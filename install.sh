#!/bin/bash
# Installation script for aaPanel MCP Server

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "aaPanel MCP Server Installation"
echo "=========================================="
echo ""

# Check Python
echo "Step 1: Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"

# Check pip
echo ""
echo "Step 2: Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  pip3 not found, installing...${NC}"
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        yum install -y python3-pip
    else
        echo -e "${RED}❌ Cannot install pip3 automatically${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ pip3 found${NC}"

# Install dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
pip3 install requests --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create config directory
echo ""
echo "Step 4: Creating configuration directory..."
mkdir -p ~/.aapanel
echo -e "${GREEN}✅ Config directory created${NC}"

# Copy example config if it doesn't exist
if [ ! -f ~/.aapanel/config.json ]; then
    if [ -f config.example.json ]; then
        cp config.example.json ~/.aapanel/config.json
        echo -e "${YELLOW}⚠️  Example config copied. Please update with your API key!${NC}"
    else
        cat > ~/.aapanel/config.json <<EOF
{
  "url": "http://localhost:7800",
  "api_key": "YOUR_AAPANEL_API_KEY_HERE"
}
EOF
        echo -e "${YELLOW}⚠️  Config file created. Please update with your API key!${NC}"
    fi
else
    echo -e "${GREEN}✅ Config file already exists${NC}"
fi

# Make server executable
echo ""
echo "Step 5: Setting permissions..."
chmod +x aapanel-mcp-server.py
echo -e "${GREEN}✅ Server is executable${NC}"

# Test installation
echo ""
echo "Step 6: Testing installation..."
if python3 -c "import requests" 2>/dev/null; then
    echo -e "${GREEN}✅ Installation test passed${NC}"
else
    echo -e "${RED}❌ Installation test failed${NC}"
    exit 1
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Get your aaPanel API key:"
echo "     - Log into aaPanel"
echo "     - Go to Settings → API"
echo "     - Generate or copy your API key"
echo ""
echo "  2. Update configuration:"
echo "     nano ~/.aapanel/config.json"
echo ""
echo "  3. Test the server:"
echo "     echo '{\"method\": \"aapanel/get_system_info\"}' | python3 aapanel-mcp-server.py"
echo ""
echo "  4. Configure in your MCP client (Cursor/Claude):"
echo "     See README.md for configuration details"
echo ""
