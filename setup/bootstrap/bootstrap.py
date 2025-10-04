#!/usr/bin/env python3
"""
PeerLab Bootstrap
Automatically generates BIRD configuration from Jinja2 template based on Tailscale network
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from jinja2 import Template
except ImportError:
    print("❌ Error: jinja2 not installed")
    sys.exit(1)


def wait_for_tailscale(container_name, timeout=300):
    """Wait for Tailscale daemon to start and verify authentication"""
    print("⏳ Waiting for Tailscale daemon to start...")

    # First, wait for tailscaled to be running
    for i in range(30):
        try:
            result = subprocess.run(
                ["docker", "exec", container_name, "tailscale", "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Daemon is running if we get any response
            break
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass

        time.sleep(1)
    else:
        print("❌ Tailscale daemon failed to start")
        return False

    print("✅ Tailscale daemon is running")
    print()

    # Check if authenticated
    print("🔍 Checking Tailscale authentication status...")
    try:
        result = subprocess.run(
            ["docker", "exec", container_name, "tailscale", "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and "100." in result.stdout:
            print("✅ Authenticated to Headscale")
            return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass

    # Not authenticated - this shouldn't happen with the new workflow
    print("❌ Tailscale is not authenticated")
    print()
    print("Please authenticate first by running:")
    print("  make auth")
    print()
    print("Or manually:")
    print(f"  docker exec -it {container_name} tailscale up \\")
    print("    --login-server=https://headscale.nxthdr.dev \\")
    print("    --accept-routes --reset")
    print()
    return False


def get_tailscale_status(container_name):
    """Get Tailscale status and parse peer information"""
    try:
        result = subprocess.run(
            ["docker", "exec", container_name, "tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting Tailscale status: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing Tailscale JSON: {e}")
        sys.exit(1)


def get_local_ip(container_name):
    """Get local Tailscale IP"""
    try:
        result = subprocess.run(
            ["docker", "exec", container_name, "tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting local IP: {e}")
        sys.exit(1)


def parse_ixp_servers(status_data):
    """Parse ALL IXP servers from Tailscale status"""
    ixp_servers = []

    # Default ASN mapping for known IXPs
    # If not in this map, we'll use 215011 as default
    asn_map = {
        "ixpfra01": 215011,
        "ixpams01": 215011,
        "ixpams02": 215011,
    }

    # Get peers from status
    peers = status_data.get("Peer", {})

    for peer_id, peer_info in peers.items():
        hostname = peer_info.get("HostName", "")
        dns_name = peer_info.get("DNSName", "")

        # Check if this is an IXP server (hostname starts with "ixp")
        if hostname.startswith("ixp"):
            # Get the first TailscaleIP (IPv4)
            tailscale_ips = peer_info.get("TailscaleIPs", [])
            if not tailscale_ips:
                continue

            ip = tailscale_ips[0]
            asn = asn_map.get(hostname, 215011)  # Default to 215011

            ixp_servers.append(
                {"name": hostname, "ip": ip, "asn": asn, "dns_name": dns_name}
            )

    return ixp_servers


def render_bird_config(local_ip, local_asn, ixp_servers, template_path, output_path):
    """Render BIRD configuration from Jinja2 template"""

    # Read template
    with open(template_path, "r") as f:
        template_content = f.read()

    template = Template(template_content)

    # Render template
    config = template.render(
        local_ip=local_ip,
        local_asn=local_asn,
        ixp_servers=ixp_servers,
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Write output
    with open(output_path, "w") as f:
        f.write(config)

    return config


def main():
    print("🔧 PeerLab Bootstrap")
    print("====================")
    print()

    # Get configuration from environment
    local_asn = os.environ.get("USER_ASN", "64512")
    tailscale_container = os.environ.get("TAILSCALE_CONTAINER", "peerlab-tailscale")

    if local_asn == "64512":
        print("⚠️  Warning: Using default ASN 64512")
        print("   Consider setting a unique ASN in your .env file")

    print(f"📋 Local ASN: AS{local_asn}")
    print()

    # Wait for Tailscale
    if not wait_for_tailscale(tailscale_container):
        sys.exit(1)
    print()

    # Get Tailscale status
    print("🔍 Getting Tailscale network information...")
    status = get_tailscale_status(tailscale_container)

    # Get local IP
    local_ip = get_local_ip(tailscale_container)
    print(f"✅ Local IP: {local_ip}")

    # Parse IXP servers
    ixp_servers = parse_ixp_servers(status)

    if not ixp_servers:
        print("❌ No IXP servers found in Tailscale network")
        print("   Make sure you're connected to a Tailscale network with IXP servers")
        sys.exit(1)

    print(f"✅ Found {len(ixp_servers)} IXP server(s):")
    for ixp in ixp_servers:
        print(f"   - {ixp['name']}: {ixp['ip']} (AS{ixp['asn']})")
    print()

    # Render configuration
    print("🔧 Rendering BIRD configuration from template...")
    template_path = Path("/config/bird.conf.j2")
    output_path = Path("/output/bird.conf")

    if not template_path.exists():
        print(f"❌ Template not found at {template_path}")
        sys.exit(1)

    render_bird_config(local_ip, local_asn, ixp_servers, template_path, output_path)

    print(f"✅ Configuration written to {output_path}")
    print()
    print("📋 Generated BGP sessions:")
    for ixp in ixp_servers:
        print(f"   - protocol bgp {ixp['name']}")
    print()
    print("✅ Bootstrap complete!")


if __name__ == "__main__":
    main()
