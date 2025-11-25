#!/bin/bash
# Test MCP server connection with configured API key

set -e

echo "=========================================="
echo "Testing aaPanel MCP Server Connection"
echo "=========================================="
echo ""

# Check if config exists
if [ ! -f ~/.aapanel/config.json ]; then
    echo "❌ Config file not found: ~/.aapanel/config.json"
    echo "Run ./setup.sh first"
    exit 1
fi

echo "✅ Config file found"
echo ""

# Test system info
echo "Testing: get_system_info"
echo '{"method": "aapanel/get_system_info"}' | python3 aapanel-mcp-server.py | python3 -m json.tool | head -20

echo ""
echo "=========================================="
echo "✅ Connection test complete!"
echo "=========================================="
