# Quick Start Guide

## ✅ Your MCP Server is Configured!

Your aaPanel API key has been set up and the MCP server is ready to use.

## Test It Now

### On Your Server

```bash
# Test system info
echo '{"method": "aapanel/get_system_info"}' | python3 /root/mcp-aapanel/aapanel-mcp-server.py

# Test Docker status
echo '{"method": "aapanel/get_docker_status"}' | python3 /root/mcp-aapanel/aapanel-mcp-server.py

# Test PM2 status
echo '{"method": "aapanel/get_pm2_status"}' | python3 /root/mcp-aapanel/aapanel-mcp-server.py
```

## Common Commands

### Get System Resources
```bash
echo '{"method": "aapanel/get_resource_usage"}' | python3 /root/mcp-aapanel/aapanel-mcp-server.py
```

### List All Databases
```bash
echo '{"method": "aapanel/list_databases"}' | python3 /root/mcp-aapanel/aapanel-mcp-server.py
```

### Setup Drupal Database
```bash
echo '{"method": "aapanel/setup_drupal_database"}' | python3 /root/mcp-aapanel/aapanel-mcp-server.py
```

### Stop Docker Container
```bash
echo '{"method": "aapanel/stop_container", "params": {"container_name": "my-container"}}' | python3 /root/mcp-aapanel/aapanel-mcp-server.py
```

### List image sizes
```bash
echo '{"method": "aapanel/list_docker_images"}' | python3 /root/mcp-aapanel/aapanel-mcp-server.py
```

### Copy an image to another aaPanel
```bash
echo '{"method": "aapanel/transfer_docker_images", "params": {"images": ["nginx:1.27"], "target": "secondary", "dry_run": true}}' | python3 /root/mcp-aapanel/aapanel-mcp-server.py
```

## Configuration

Your API key is stored at:
- **Location:** `/root/.aapanel/config.json`
- **Permissions:** `600` (secure)
- **API Key:** `CoBeH3LH14XAN2jrKXxCzy51dxE0dLfP`
- **URL:** `http://localhost:7800`

## Using with AI Assistants

The MCP server is now ready to be used with:
- **Cursor** - Add to MCP configuration
- **Claude** - Add to MCP configuration
- **Any MCP-compatible tool**

## Next Steps

1. ✅ API key configured
2. ✅ MCP server ready
3. 🔄 Test some methods
4. 🔄 Set up MCP integration in your IDE
5. 🔄 Start managing your server!

---

**Status:** ✅ Ready to use!
