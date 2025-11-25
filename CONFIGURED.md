# MCP Server Configuration Complete

## ✅ API Key Configured

Your aaPanel API key has been configured:
- **API Key:** `CoBeH3LH14XAN2jrKXxCzy51dxE0dLfP`
- **URL:** `http://localhost:7800`
- **Config Location:** `~/.aapanel/config.json`

## Test Connection

### On Server

```bash
# Test the connection
echo '{"method": "aapanel/get_system_info"}' | python3 aapanel-mcp-server.py
```

Or use the test script:

```bash
cd /path/to/mcp-aapanel
./test-connection.sh
```

### From Local Machine (via SSH)

If you want to use the MCP server from your local machine, you'll need to:

1. **SSH Tunnel** (recommended):
   ```bash
   ssh -L 7800:localhost:7800 root@144.202.17.221
   ```

2. **Update config** on local machine:
   ```json
   {
     "url": "http://localhost:7800",
     "api_key": "CoBeH3LH14XAN2jrKXxCzy51dxE0dLfP"
   }
   ```

## Available Methods

Now you can use all MCP methods:

### System Info
```bash
echo '{"method": "aapanel/get_system_info"}' | python3 aapanel-mcp-server.py
```

### Docker Status
```bash
echo '{"method": "aapanel/get_docker_status"}' | python3 aapanel-mcp-server.py
```

### PM2 Status
```bash
echo '{"method": "aapanel/get_pm2_status"}' | python3 aapanel-mcp-server.py
```

### Create Database
```bash
echo '{"method": "aapanel/create_database", "params": {"db_name": "test_db"}}' | python3 aapanel-mcp-server.py
```

### Setup Drupal Database
```bash
echo '{"method": "aapanel/setup_drupal_database"}' | python3 aapanel-mcp-server.py
```

## Integration with Cursor/Claude

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "aapanel": {
      "command": "ssh",
      "args": [
        "root@144.202.17.221",
        "python3",
        "/root/mcp-aapanel/aapanel-mcp-server.py"
      ],
      "env": {
        "AAPANEL_URL": "http://localhost:7800",
        "AAPANEL_API_KEY": "CoBeH3LH14XAN2jrKXxCzy51dxE0dLfP"
      }
    }
  }
}
```

Or if running locally with SSH tunnel:

```json
{
  "mcpServers": {
    "aapanel": {
      "command": "python3",
      "args": ["/path/to/mcp-aapanel/aapanel-mcp-server.py"]
    }
  }
}
```

## Security Notes

⚠️ **Important:**
- Keep your API key secure
- Don't commit `config.json` to version control
- The API key is stored in `~/.aapanel/config.json` with permissions `600`
- Consider rotating the key periodically

## Next Steps

1. **Test the connection** using the test script
2. **Try some methods** to verify everything works
3. **Set up MCP integration** in your IDE (Cursor/Claude)
4. **Start managing your server** through MCP!

---

**Status:** ✅ Configured and ready to use!
