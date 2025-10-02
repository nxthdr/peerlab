.PHONY: help up down restart logs status bird birdc tailscale shell-bird shell-tailscale

# Default target
help:
	@echo "PeerLab - Available Commands"
	@echo "============================"
	@echo ""
	@echo "Container Management:"
	@echo "  make up              - Start all containers"
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
	@echo "  make tailscale CMD='ping 100.102.32.36'"

# Container management
up:
	docker-compose up -d

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
	@docker exec peerlab-tailscale tailscale status 2>/dev/null || echo "Tailscale not ready"
	@echo ""
	@echo "=== BIRD Protocols ==="
	@docker exec peerlab-bird birdc show protocols 2>/dev/null || echo "BIRD not ready"

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
	@docker exec peerlab-tailscale ping -c 4 100.102.32.36

shell-tailscale:
	@docker exec -ti peerlab-tailscale /bin/sh
