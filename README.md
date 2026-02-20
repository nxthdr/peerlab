# PeerLab

Learn BGP by connecting to a real Internet Exchange Point (IXP) and receiving the full IPv6 routing table.

> [!WARNING]
> Currently in early-stage development.

## Requirements

You'll need Docker and Docker Compose installed. PeerLab uses Headscale (a self-hosted Tailscale control server) for secure connectivity to the IXP.

You also need a valid **nxthdr** account to authenticate with Headscale. Please register at [nxthdr.dev](https://nxthdr.dev).

## Quick Start

1. **Configure your environment:**
   ```bash
   cp .env.example .env
   # Edit .env and configure:
   # - USER_ASN: Your private ASN (e.g., 64512)
   # - USER_PREFIXES: IPv6 prefixes to advertise (optional)
   ```

   **Example configurations:**
   ```bash
   # Receive-only mode (no prefix advertisement)
   USER_ASN=64512
   USER_PREFIXES=

   # Advertise a single prefix
   USER_ASN=64512
   USER_PREFIXES=2001:db8:1234::/48

   # Advertise multiple prefixes
   USER_ASN=64512
   USER_PREFIXES=2001:db8:1234::/48,2001:db8:5678::/48
   ```

2. **Start Tailscale:**
   ```bash
   make setup
   ```

   This will start the Tailscale container and display authentication instructions.

3. **Authenticate with Headscale:**

   In a new terminal, run:
   ```bash
   make auth
   ```

   This will output a URL like:
   ```
   To authenticate, visit:
   https://headscale.nxthdr.dev/register/<key>
   ```

   Open this URL in your browser and authenticate with your nxthdr.dev account.

4. **Start PeerLab:**

   Once authenticated, start the full stack:
   ```bash
   make up
   ```

   This will configure BIRD and establish BGP sessions with the IXP.

5. **Check status:**
   ```bash
   make status
   ```

   After a while, you should see BGP sessions in "Established" state.

## Prefix Advertisement

PeerLab supports advertising one or multiple IPv6 prefixes to the IXP. This is configured via the `USER_PREFIXES` environment variable.

### Configuration

Edit your `.env` file and set `USER_PREFIXES` to a comma-separated list of IPv6 prefixes:

```bash
# Single prefix
USER_PREFIXES=2001:db8:1234::/48

# Multiple prefixes
USER_PREFIXES=2001:db8:1234::/48,2001:db8:5678::/48,2001:db8:abcd::/48
```

**Important notes:**
- Only IPv6 prefixes are supported
- Prefixes must be in CIDR notation (e.g., `2001:db8::/48`)
- Invalid prefixes will be skipped with a warning during bootstrap
- Leave empty for receive-only mode (no advertisement)

### Viewing Advertised Routes

After starting PeerLab with prefixes configured, you can verify they're being advertised:

```bash
# View all exported routes to all IXP peers
make bird-exports

# View routes advertised to a specific peer
make bird CMD='show route export ixpfra01'

# View the static routes table (your configured prefixes)
make bird-prefixes
```

### How It Works

1. **Static Routes**: Your prefixes are configured as static blackhole routes in BIRD
2. **Export Filter**: The `ExportToIXP` filter advertises these static routes to all BGP peers
3. **BGP Advertisement**: Each IXP peer receives your prefixes via BGP

### Updating Prefixes

To change advertised prefixes:

1. Update `USER_PREFIXES` in your `.env` file
2. Restart PeerLab:
   ```bash
   make down
   make up
   ```

The bootstrap process will regenerate the BIRD configuration with your new prefixes.

## Updating BIRD Configuration

1. Update BIRD configuration in `workspace/` directory
2. Reload BIRD with:
   ```bash
   make bird-config
   ```
