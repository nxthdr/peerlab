#!/bin/bash
# Setup script for PeerLab environment

set -e

echo "🎓 PeerLab - User Environment Setup"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  Please edit .env and configure:"
    echo "   - USER_ASN: Your assigned ASN"
    echo "   - TS_AUTHKEY: Your Tailscale auth key"
    echo ""
    read -p "Press Enter when you've configured .env..."
fi

# Load environment variables
source .env

# Validate configuration
if [ -z "$USER_ASN" ] || [ "$USER_ASN" = "64512" ]; then
    echo "⚠️  Warning: USER_ASN is not configured or using default"
fi

if [ -z "$TS_AUTHKEY" ] || [[ "$TS_AUTHKEY" == *"xxxxx"* ]]; then
    echo "❌ Error: TS_AUTHKEY is not configured in .env"
    echo "   Get your auth key from: https://login.tailscale.com/admin/settings/keys"
    exit 1
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p tailscale/state
echo "✅ Directories created"
echo ""

# Check if ixpfra01 IP is configured
if grep -q "100.x.x.x" bird/bird.conf; then
    echo "⚠️  Warning: ixpfra01 Tailscale IP not configured in bird/bird.conf"
    echo "   You need to replace '100.x.x.x' with the actual Tailscale IP of ixpfra01"
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update BIRD config with user ASN
echo "🔧 Updating BIRD configuration with your ASN..."
sed -i.bak "s/local as 64512/local as $USER_ASN/" bird/bird.conf
rm bird/bird.conf.bak
echo "✅ BIRD configuration updated"
echo ""

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d
echo "✅ Containers started"
echo ""

# Wait a bit for services to start
echo "⏳ Waiting for services to initialize..."
sleep 5

# Check Tailscale status
echo "🔍 Checking Tailscale connection..."
if docker exec peerlab-tailscale tailscale status &> /dev/null; then
    echo "✅ Tailscale is connected"
    docker exec peerlab-tailscale tailscale status
else
    echo "⚠️  Tailscale status check failed (this might be normal during initial setup)"
fi
echo ""

# Check BIRD status
echo "🔍 Checking BIRD status..."
if docker exec peerlab-bird birdc show status &> /dev/null; then
    echo "✅ BIRD is running"
    docker exec peerlab-bird birdc show protocols
else
    echo "❌ BIRD is not responding"
    echo "   Check logs with: docker logs peerlab-bird"
fi
echo ""

echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Verify Tailscale connection: docker exec peerlab-tailscale tailscale status"
echo "   2. Check BGP session: docker exec peerlab-bird birdc show protocols"
echo "   3. View received routes: docker exec peerlab-bird birdc show route"
echo ""
echo "📖 For more information, see README.md"
