.PHONY: help setup auth up down restart logs status bird birdc tailscale shell-bird shell-tailscale

# Default target
help:
	@echo "PeerLab - Available Commands"
	@echo "============================"
	@echo ""
	@echo "Setup:"
	@echo "  make setup           - Start Tailscale container (first step)"
	@echo "  make auth            - Authenticate with Headscale (second step)"
	@echo "  make up              - Start full stack after authentication (third step)"
	@echo ""
	@echo "Container Management:"
	@echo "  make down            - Stop and remove all containers"
	@echo "  make restart         - Restart all containers"
	@echo "  make logs            - Show logs from all containers"
	@echo "  make status          - Show container status"
	@echo ""
	@echo "BIRD Commands:"
	@echo "  make bird            - Run any BIRD command (usage: make bird CMD='show protocols')"
	@echo "  make bird-status     - Show BIRD status"
	@echo "  make bird-protocols  - Show BGP protocols"
	@echo "  make bird-routes     - Show all received routes"
	@echo "  make bird-routes-count - Count received routes"
	@echo "  make bird-config     - Reload BIRD configuration"
	@echo "  make shell-bird      - Open shell in BIRD container"
	@echo ""
	@echo "Tailscale Commands:"
	@echo "  make tailscale       - Run any Tailscale command (usage: make tailscale CMD='status')"
	@echo "  make ts-status       - Show Tailscale connection status"
	@echo "  make ts-ip           - Show Tailscale IP address"
	@echo "  make ts-ping         - Ping ixpfra01 via Tailscale"
	@echo "  make shell-tailscale - Open shell in Tailscale container"
	@echo ""
	@echo "Examples:"
	@echo "  make bird CMD='show route protocol ixpfra01'"
	@echo "  make tailscale CMD='ping 100.64.0.2'"

# Setup workflow
setup:
	@echo "Starting Tailscale container..."
	@docker-compose up -d tailscale
	@echo ""
	@echo "✅ Tailscale container started"
	@echo ""
	@echo "Next step: Authenticate with Headscale"
	@echo "Run: make auth"

auth:
	@echo "Starting Headscale authentication..."
	@echo ""
	@docker exec -it peerlab-tailscale tailscale up --login-server=https://headscale.nxthdr.dev --accept-routes --reset
	@echo ""
	@echo "✅ Authentication complete"
	@echo ""
	@echo "Next step: Start the full stack"
	@echo "Run: make up"

# Container management
up:
	@echo "Starting PeerLab..."
	@docker-compose up -d
	@echo ""
	@echo "✅ PeerLab is starting up"
	@echo ""
	@echo "Check status with: make status"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

status:
	@echo "=== Container Status ==="
	@docker-compose ps
	@echo ""
	@echo "=== Tailscale Status ==="
	@docker exec peerlab-tailscale tailscale status 2>/dev/null || echo "Tailscale not ready. Run 'make setup' then 'make auth'"
	@echo ""
	@echo "=== BIRD Protocols ==="
	@docker exec peerlab-bird birdc show protocols 2>/dev/null || echo "BIRD not ready. Run 'make up' after authentication"

# BIRD commands
bird:
	@docker exec -ti peerlab-bird birdc $(CMD)

bird-status:
	@docker exec peerlab-bird birdc show status

bird-protocols:
	@docker exec peerlab-bird birdc show protocols

bird-routes:
	@docker exec peerlab-bird birdc show route

bird-routes-count:
	@docker exec peerlab-bird birdc show route count

bird-config:
	@docker exec peerlab-bird birdc configure

shell-bird:
	@docker exec -ti peerlab-bird /bin/bash

# Tailscale commands
tailscale:
	@docker exec -ti peerlab-tailscale tailscale $(CMD)

ts-status:
	@docker exec peerlab-tailscale tailscale status

ts-ip:
	@docker exec peerlab-tailscale tailscale ip -4

ts-ping:
	@docker exec peerlab-tailscale ping -c 4 100.64.0.2

shell-tailscale:
	@docker exec -ti peerlab-tailscale /bin/sh
