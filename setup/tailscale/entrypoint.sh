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

    # Configure IPv6 address for announced prefix if USER_PREFIXES is set
    if [ -n "$USER_PREFIXES" ]; then
        # Extract first prefix and add ::face address
        FIRST_PREFIX=$(echo "$USER_PREFIXES" | cut -d',' -f1 | tr -d ' ')
        if [ -n "$FIRST_PREFIX" ]; then
            # Extract network part and add ::face
            IPV6_ADDR=$(echo "$FIRST_PREFIX" | sed 's|/[0-9]*$||')::face
            echo "🌐 Configuring IPv6 address: $IPV6_ADDR"

            # Wait for tailscale0 interface to be ready
            sleep 2

            # Add IPv6 address to tailscale0 interface
            if ip -6 addr add "$IPV6_ADDR/128" dev tailscale0 2>/dev/null; then
                echo "✅ IPv6 address configured on tailscale0"
            else
                echo "⚠️  IPv6 address may already be configured"
            fi

            # Update default route to use tailscale0
            ip -6 route del default 2>/dev/null || true
            ip -6 route add default dev tailscale0
            echo "✅ Default IPv6 route set to tailscale0"
        fi
    fi
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
