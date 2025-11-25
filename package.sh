#!/bin/bash
# Package the MCP aaPanel server for distribution

set -e

PACKAGE_NAME="mcp-aapanel"
VERSION="1.0.0"
ARCHIVE_NAME="${PACKAGE_NAME}-v${VERSION}.tar.gz"

echo "=========================================="
echo "Packaging aaPanel MCP Server"
echo "=========================================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create archive
echo "Creating archive..."
tar -czf "../${ARCHIVE_NAME}" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='config.json' \
    --exclude='*.log' \
    .

echo ""
echo "=========================================="
echo "✅ Package created: ${ARCHIVE_NAME}"
echo "=========================================="
echo ""
echo "Package contents:"
tar -tzf "../${ARCHIVE_NAME}" | head -20
echo "..."
echo ""
echo "To extract:"
echo "  tar -xzf ${ARCHIVE_NAME}"
echo ""
echo "To install:"
echo "  cd ${PACKAGE_NAME}"
echo "  ./install.sh"
echo ""
