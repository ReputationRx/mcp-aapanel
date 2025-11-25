# Distribution Guide

## Package Contents

The `mcp-aapanel` package includes:

- `aapanel-mcp-server.py` - Main MCP server
- `install.sh` - Automated installation script
- `setup.sh` - Quick setup script
- `package.sh` - Package creation script
- `config.example.json` - Example configuration
- `README.md` - Main documentation
- `LICENSE` - MIT License
- `.gitignore` - Git ignore rules
- `docs/` - Additional documentation
  - `API.md` - Complete API reference
  - `EXAMPLES.md` - Usage examples
  - `TROUBLESHOOTING.md` - Troubleshooting guide

## Creating Distribution Package

```bash
cd mcp-aapanel
./package.sh
```

This creates: `mcp-aapanel-v1.0.0.tar.gz`

## Distribution Methods

### 1. GitHub Release

1. Create a new release on GitHub
2. Upload the `.tar.gz` file
3. Add release notes

### 2. Direct Download

Host the package on your server or CDN:
- Provide download link
- Include checksums (SHA256)
- Provide installation instructions

### 3. Package Managers

Consider creating packages for:
- **npm** - For Node.js integration
- **pip** - For Python package management
- **Homebrew** - For macOS users

## Installation Instructions for Users

### Quick Install

```bash
# Download and extract
wget https://example.com/mcp-aapanel-v1.0.0.tar.gz
tar -xzf mcp-aapanel-v1.0.0.tar.gz
cd mcp-aapanel

# Install
./install.sh

# Configure
./setup.sh
```

### Manual Install

See `README.md` for detailed manual installation steps.

## Versioning

Follow semantic versioning:
- **MAJOR** - Breaking changes
- **MINOR** - New features, backward compatible
- **PATCH** - Bug fixes

## Changelog

Maintain a `CHANGELOG.md` with:
- Version number
- Release date
- New features
- Bug fixes
- Breaking changes

## Testing Before Distribution

1. Test installation on clean system
2. Verify all methods work
3. Test with different Python versions
4. Test on different operating systems
5. Verify documentation is accurate
6. Check for security issues

## Security Checklist

- [ ] No hardcoded credentials
- [ ] API keys not in code
- [ ] Sensitive files in .gitignore
- [ ] Dependencies are secure
- [ ] No security vulnerabilities
- [ ] Proper file permissions

## Support

Provide support through:
- GitHub Issues
- Documentation
- Examples
- Troubleshooting guide

## License

Distribute under MIT License (included in package).
