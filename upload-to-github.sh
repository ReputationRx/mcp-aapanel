#!/bin/bash
# Upload MCP aaPanel package to GitHub ReputationRx repository

set -e

REPO_NAME="ReputationRx"
PACKAGE_DIR="/Users/waqar/Downloads/slideindm_site_blog_backup/mcp-aapanel"
cd "$PACKAGE_DIR"

echo "=========================================="
echo "Uploading to GitHub: $REPO_NAME"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git branch -M main
fi

# Check if remote exists
if ! git remote get-url origin &>/dev/null; then
    echo "Setting up remote repository..."
    read -p "Enter GitHub username/organization [default: your-username]: " GITHUB_USER
    GITHUB_USER=${GITHUB_USER:-your-username}
    
    git remote add origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git" || \
    git remote set-url origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
    
    echo "Remote set to: https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
fi

# Add all files
echo ""
echo "Adding files to git..."
git add .

# Check if there are changes
if git diff --staged --quiet; then
    echo "No changes to commit"
else
    echo "Committing changes..."
    git commit -m "Initial release: aaPanel MCP Server v1.0.0

- Complete MCP server for aaPanel/BT Panel management
- Docker, PM2, SSL, Database management
- Comprehensive documentation
- Installation and setup scripts
- Ready for distribution"
fi

# Push to GitHub
echo ""
echo "Pushing to GitHub..."
echo "You may be prompted for GitHub credentials"
git push -u origin main

echo ""
echo "=========================================="
echo "✅ Upload complete!"
echo "=========================================="
echo ""
echo "Repository: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\([^/]*\/[^/]*\)\.git/\1/')"
echo ""
echo "Next steps:"
echo "  1. Create a release on GitHub"
echo "  2. Upload mcp-aapanel-v1.0.0.tar.gz as a release asset"
echo "  3. Add release notes from CHANGELOG.md"
echo ""
