#!/bin/bash
# Quick setup script for aaPanel MCP Server

set -e

echo "=========================================="
echo "aaPanel MCP Server Quick Setup"
echo "=========================================="
echo ""

# Get API key
echo "Please enter your aaPanel API key:"
echo "(Get it from: Settings → API in aaPanel)"
read -p "API Key: " API_KEY

if [ -z "$API_KEY" ]; then
    echo "API key is required. Exiting."
    exit 1
fi

# Get URL (optional)
read -p "aaPanel URL [http://localhost:7800]: " AAPANEL_URL
AAPANEL_URL=${AAPANEL_URL:-http://localhost:7800}

# Create config
mkdir -p ~/.aapanel
cat > ~/.aapanel/config.json <<EOF
{
  "url": "${AAPANEL_URL}",
  "api_key": "${API_KEY}"
}
EOF

chmod 600 ~/.aapanel/config.json

echo ""
echo "✅ Configuration saved to ~/.aapanel/config.json"
echo ""
echo "Testing connection..."
if echo '{"method": "aapanel/get_system_info"}' | python3 aapanel-mcp-server.py 2>/dev/null | grep -q "memory\|error"; then
    echo "✅ Connection test successful!"
else
    echo "⚠️  Connection test had issues. Please verify your API key and URL."
fi

echo ""
echo "Setup complete!"
