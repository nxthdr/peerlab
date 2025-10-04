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
   # Edit .env and set your Private ASN (e.g., USER_ASN=64512)
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
   https://headscale.nxthdr.dev/register/mkey:...
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

   You should see BGP sessions in "Established" state.
