#!/usr/bin/env python3
"""
PeerLab Bootstrap
Automatically generates BIRD configuration from Jinja2 template based on Tailscale network
"""

import ipaddress
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


def parse_user_prefixes(prefixes_str):
    """Parse and validate user-provided IPv6 prefixes"""
    if not prefixes_str or not prefixes_str.strip():
        return []

    prefixes = []
    raw_prefixes = [p.strip() for p in prefixes_str.split(",") if p.strip()]

    for prefix_str in raw_prefixes:
        try:
            # Parse and validate IPv6 prefix
            network = ipaddress.IPv6Network(prefix_str, strict=False)
            prefixes.append(str(network))
        except (ipaddress.AddressValueError, ValueError) as e:
            print(f"⚠️  Warning: Invalid IPv6 prefix '{prefix_str}': {e}")
            print("   Skipping this prefix")

    return prefixes


def render_bird_config(
    local_ip, local_asn, ixp_servers, user_prefixes, template_path, output_path
):
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
        user_prefixes=user_prefixes,
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Write output
    with open(output_path, "w") as f:
        f.write(config)

    return config


def render_caddy_config(user_prefixes, user_asn, template_path, output_path):
    """Render Caddy configuration from Jinja2 template"""

    # Read template
    with open(template_path, "r") as f:
        template_content = f.read()

    template = Template(template_content)

    # Get the first prefix for the web server address
    ipv6_address = "::1"  # Default fallback
    if user_prefixes:
        # Use the first prefix and add ::face as the host address
        prefix = user_prefixes[0]
        # Remove the /48 or other prefix length
        prefix_base = prefix.split("/")[0]
        # Add ::face to the prefix
        ipv6_address = f"{prefix_base.rstrip(':')}::face"

    # Render template
    config = template.render(
        user_asn=user_asn,
        ipv6_address=ipv6_address,
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Write output
    with open(output_path, "w") as f:
        f.write(config)

    return ipv6_address


def generate_ixp_mapping(status_data, output_path):
    """Generate JavaScript file with IXP Tailscale IP to hostname mapping"""

    # Get peers from status
    peers = status_data.get("Peer", {})
    mapping = {}

    for peer_id, peer_info in peers.items():
        hostname = peer_info.get("HostName", "")

        # Check if this is an IXP server (hostname starts with "ixp")
        if hostname.startswith("ixp"):
            # Get both IPv4 and IPv6 TailscaleIPs
            tailscale_ips = peer_info.get("TailscaleIPs", [])

            # Add all IPs to mapping
            for ip in tailscale_ips:
                mapping[ip] = hostname

    # Generate JavaScript file
    js_content = f"""// Auto-generated IXP mapping from Tailscale status
// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

const ixpMapping = {json.dumps(mapping, indent=4)};
"""

    # Write output
    with open(output_path, "w") as f:
        f.write(js_content)


def main():
    print("🔧 PeerLab Bootstrap")
    print("====================")
    print()

    # Get configuration from environment
    local_asn = os.environ.get("USER_ASN", "64512")
    tailscale_container = os.environ.get("TAILSCALE_CONTAINER", "peerlab-tailscale")
    user_prefixes_str = os.environ.get("USER_PREFIXES", "")

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

    # Parse user prefixes
    user_prefixes = parse_user_prefixes(user_prefixes_str)
    if user_prefixes:
        print(f"✅ Advertising {len(user_prefixes)} IPv6 prefix(es):")
        for prefix in user_prefixes:
            print(f"   - {prefix}")
    else:
        print("ℹ️  No prefixes configured - receive-only mode")
    print()

    # Render configuration
    print("🔧 Rendering BIRD configuration from template...")
    template_path = Path("/config/bird.conf.j2")
    output_path = Path("/output/bird.conf")

    if not template_path.exists():
        print(f"❌ Template not found at {template_path}")
        sys.exit(1)

    render_bird_config(
        local_ip, local_asn, ixp_servers, user_prefixes, template_path, output_path
    )

    print(f"✅ Configuration written to {output_path}")
    print()
    print("📋 Generated BGP sessions:")
    for ixp in ixp_servers:
        print(f"   - protocol bgp {ixp['name']}")
    print()
    if user_prefixes:
        print(f"📡 Advertising {len(user_prefixes)} prefix(es) to all IXP peers")
    else:
        print("📡 Receive-only mode (no prefixes advertised)")
    print()

    # Render Caddy configuration
    print("🔧 Rendering Caddy configuration from template...")
    caddy_template_path = Path("/templates/Caddyfile.j2")
    caddy_output_path = Path("/output/Caddyfile")

    if caddy_template_path.exists():
        ipv6_address = render_caddy_config(
            user_prefixes, local_asn, caddy_template_path, caddy_output_path
        )
        print(f"✅ Caddy configuration written to {caddy_output_path}")
        print(f"🌐 Web server listening on [{ipv6_address}]:80")
        print()
    else:
        print(f"⚠️  Caddy template not found at {caddy_template_path}, skipping")
        print()

    # Generate IXP mapping for webpage
    print("🔧 Generating IXP mapping for webpage...")
    generate_ixp_mapping(status, Path("/output/ixp-mapping.js"))
    print("✅ IXP mapping written to /output/ixp-mapping.js")
    print()

    print("✅ Bootstrap complete!")


if __name__ == "__main__":
    main()
