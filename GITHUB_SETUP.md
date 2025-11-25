# GitHub Repository Setup Guide

## Quick Upload

### Option 1: Automated Script

```bash
cd /Users/waqar/Downloads/slideindm_site_blog_backup/mcp-aapanel
./upload-to-github.sh
```

This will:
1. Initialize git repository (if needed)
2. Set up remote to ReputationRx
3. Add all files
4. Commit changes
5. Push to GitHub

### Option 2: Manual Steps

#### 1. Initialize Repository

```bash
cd /Users/waqar/Downloads/slideindm_site_blog_backup/mcp-aapanel
git init
git branch -M main
```

#### 2. Add Remote

```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/ReputationRx.git
```

Or if repository already exists:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/ReputationRx.git
```

#### 3. Add Files

```bash
git add .
git commit -m "Initial release: aaPanel MCP Server v1.0.0"
```

#### 4. Push to GitHub

```bash
git push -u origin main
```

## Create GitHub Release

### Via GitHub Web Interface

1. Go to your repository: `https://github.com/YOUR_USERNAME/ReputationRx`
2. Click **Releases** → **Create a new release**
3. **Tag version:** `v1.0.0`
4. **Release title:** `aaPanel MCP Server v1.0.0`
5. **Description:** Copy from `CHANGELOG.md`
6. **Attach files:** Upload `mcp-aapanel-v1.0.0.tar.gz`
7. Click **Publish release**

### Via GitHub CLI

```bash
# Install GitHub CLI if needed
# brew install gh  # macOS
# apt install gh   # Linux

# Authenticate
gh auth login

# Create release
cd /Users/waqar/Downloads/slideindm_site_blog_backup
gh release create v1.0.0 \
  --title "aaPanel MCP Server v1.0.0" \
  --notes-file mcp-aapanel/CHANGELOG.md \
  mcp-aapanel-v1.0.0.tar.gz
```

## Repository Structure

Your repository should have:

```
ReputationRx/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── aapanel-mcp-server.py
├── install.sh
├── setup.sh
├── package.sh
├── config.example.json
├── .gitignore
├── docs/
│   ├── API.md
│   ├── EXAMPLES.md
│   └── TROUBLESHOOTING.md
└── .github/
    └── workflows/
        └── release.yml
```

## Release Assets

For each release, include:
- ✅ Source code (automatically included)
- ✅ `mcp-aapanel-v1.0.0.tar.gz` (package file)
- ✅ Release notes from `CHANGELOG.md`

## GitHub Pages (Optional)

To create documentation site:

1. Go to **Settings** → **Pages**
2. Select **Source:** `main` branch, `/docs` folder
3. Documentation will be available at:
   `https://YOUR_USERNAME.github.io/ReputationRx/`

## Repository Settings

Recommended settings:
- ✅ **Description:** "Model Context Protocol server for managing aaPanel/BT Panel servers"
- ✅ **Topics:** `mcp`, `aapanel`, `server-management`, `docker`, `automation`
- ✅ **Website:** (if you have one)
- ✅ **License:** MIT (already included)

## Security

- ✅ `.gitignore` excludes sensitive files (`config.json`)
- ✅ API keys should never be committed
- ✅ Use GitHub Secrets for CI/CD if needed

## Next Steps After Upload

1. ✅ Create initial release
2. ✅ Add repository description and topics
3. ✅ Set up GitHub Pages (optional)
4. ✅ Share the repository link
5. ✅ Update package with repository URL in README

---

**Ready to upload!** Run `./upload-to-github.sh` or follow manual steps above.
