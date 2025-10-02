# PeerLab

Learn BGP by connecting to a real Internet Exchange Point (IXP) and receiving the full IPv6 routing table.

> [!WARNING]
> Currently in early-stage development.

## Requirements

You'll need Docker and Docker Compose installed, along with a [Tailscale](https://tailscale.com/) account to generate an OAuth token for authentication.

## Quick Start

1. **Configure your environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your ASN and Tailscale auth key
   ```

2. **Start PeerLab:**
   ```bash
   ./setup.sh
   ```

3. **Check status:**
   ```bash
   make status
   ```

## Useful Commands

```bash
make help
```

```bash
PeerLab - Available Commands
============================

Container Management:
  make up              - Start all containers
  make down            - Stop and remove all containers
  make restart         - Restart all containers
  make logs            - Show logs from all containers
  make status          - Show container status

BIRD Commands:
  make bird            - Run any BIRD command (usage: make bird CMD='show protocols')
  make bird-status     - Show BIRD status
  make bird-protocols  - Show BGP protocols
  make bird-routes     - Show all received routes
  make bird-routes-count - Count received routes
  make bird-config     - Reload BIRD configuration
  make shell-bird      - Open shell in BIRD container

Tailscale Commands:
  make tailscale       - Run any Tailscale command (usage: make tailscale CMD='status')
  make ts-status       - Show Tailscale connection status
  make ts-ip           - Show Tailscale IP address
  make ts-ping         - Ping ixpfra01 via Tailscale
  make shell-tailscale - Open shell in Tailscale container

Examples:
  make bird CMD='show route protocol ixpfra01'
  make tailscale CMD='ping 100.102.32.36'
```




