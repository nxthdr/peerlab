#!/bin/sh

# Start tailscaled in the background
echo "Starting tailscaled..."
tailscaled --state=${TS_STATE_DIR}/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &
TAILSCALED_PID=$!

# Wait for tailscaled to be ready
sleep 3

# Check if already authenticated (ignore errors)
if tailscale status 2>/dev/null | grep -q "100\."; then
    echo "✅ Already authenticated to Headscale"
else
    echo ""
    echo "=========================================="
    echo "⚠️  Not authenticated to Headscale"
    echo "=========================================="
    echo ""
    echo "To authenticate, run:"
    echo "  make auth"
    echo ""
    echo "Or manually:"
    echo "  docker exec -it peerlab-tailscale tailscale up --login-server=${TS_LOGIN_SERVER} --accept-routes --reset"
    echo ""
    echo "Then open the URL in your browser and authenticate."
    echo "=========================================="
    echo ""
    echo "Tailscaled is running and waiting for authentication..."
fi

# Keep the container running
wait $TAILSCALED_PID
