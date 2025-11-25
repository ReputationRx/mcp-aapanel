# aaPanel MCP Server

Model Context Protocol (MCP) server for managing aaPanel/BT Panel servers through AI assistants.

## Features

- 🐳 **Docker Management** - Start, stop, restart, and monitor containers
- 📦 **PM2 Management** - Manage Node.js applications
- 🔒 **SSL Certificate Management** - List, check status, and renew certificates
- 💾 **Database Management** - Create databases, list databases, setup Drupal
- 📊 **System Monitoring** - Resource usage, system info, service status
- 🔧 **Service Management** - Unified control for all services
- 🌐 **Website Management** - List and manage websites

## Installation

### Prerequisites

- Python 3.7+
- aaPanel or BT Panel installed
- Docker (optional, for container management)
- PM2 (optional, for Node.js app management)

### Quick Install

```bash
# Clone or download this package
cd mcp-aapanel

# Run installer
chmod +x install.sh
./install.sh
```

### Manual Install

```bash
# 1. Install Python dependencies
pip3 install requests

# 2. Create config directory
mkdir -p ~/.aapanel

# 3. Configure API access
cat > ~/.aapanel/config.json <<EOF
{
  "url": "http://localhost:7800",
  "api_key": "YOUR_AAPANEL_API_KEY"
}
EOF

# 4. Get API key from aaPanel
# Settings → API → Generate/Copy API Key

# 5. Make server executable
chmod +x aapanel-mcp-server.py
```

## Configuration

### Get aaPanel API Key

1. Log into aaPanel web interface
2. Go to **Settings** → **API**
3. Generate or copy your API key
4. Add it to `~/.aapanel/config.json`

### Environment Variables (Alternative)

Instead of config file, you can use environment variables:

```bash
export AAPANEL_URL="http://localhost:7800"
export AAPANEL_API_KEY="your_api_key_here"
```

## Usage

### With Cursor/Claude

Add to your MCP configuration (usually `~/.cursor/mcp.json` or similar):

```json
{
  "mcpServers": {
    "aapanel": {
      "command": "python3",
      "args": ["/path/to/mcp-aapanel/aapanel-mcp-server.py"],
      "env": {
        "AAPANEL_URL": "http://localhost:7800",
        "AAPANEL_API_KEY": "your_api_key"
      }
    }
  }
}
```

### Direct Usage

```bash
# Test the server
echo '{"method": "aapanel/get_system_info"}' | python3 aapanel-mcp-server.py

# Get resource usage
echo '{"method": "aapanel/get_resource_usage"}' | python3 aapanel-mcp-server.py

# List Docker containers
echo '{"method": "aapanel/get_docker_status"}' | python3 aapanel-mcp-server.py
```

## Available Methods

### System & Resources

- `aapanel/get_system_info` - Get system information (memory, disk, uptime)
- `aapanel/get_resource_usage` - Get current resource usage (CPU, memory, disk, Docker)
- `aapanel/get_dashboard` - Get comprehensive dashboard information

### Docker Management

- `aapanel/get_docker_status` - Get Docker container status
- `aapanel/stop_container` - Stop a Docker container
- `aapanel/start_container` - Start a Docker container
- `aapanel/restart_container` - Restart a Docker container

### PM2 Management

- `aapanel/get_pm2_status` - Get PM2 application status
- `aapanel/pm2_start` - Start PM2 application
- `aapanel/pm2_stop` - Stop PM2 application
- `aapanel/pm2_restart` - Restart PM2 application
- `aapanel/pm2_logs` - Get PM2 application logs

### SSL Management

- `aapanel/get_ssl_list` - Get list of SSL certificates
- `aapanel/get_ssl_status` - Get SSL certificate status for a domain
- `aapanel/renew_ssl` - Renew SSL certificate

### Database Management

- `aapanel/create_database` - Create MySQL database and user
- `aapanel/list_databases` - List all MySQL databases
- `aapanel/setup_drupal_database` - Complete Drupal database setup

### Service Management

- `aapanel/get_sites` - Get list of websites
- `aapanel/restart_service` - Restart a system service
- `aapanel/get_logs` - Get logs from a service
- `aapanel/get_all_services_status` - Get status of all services
- `aapanel/service_manager` - Unified service manager

## Examples

### Create Database

```json
{
  "method": "aapanel/create_database",
  "params": {
    "db_name": "my_database",
    "db_user": "my_user",
    "db_pass": "secure_password"
  }
}
```

### Setup Drupal Database

```json
{
  "method": "aapanel/setup_drupal_database"
}
```

This automatically:
- Creates database `drupal_slideindm`
- Creates user `drupal_user`
- Configures Drupal's `settings.php`
- Returns credentials

### Manage Docker Container

```json
{
  "method": "aapanel/stop_container",
  "params": {
    "container_name": "my-container"
  }
}
```

### Get PM2 Status

```json
{
  "method": "aapanel/get_pm2_status"
}
```

## File Structure

```
mcp-aapanel/
├── README.md                 # This file
├── aapanel-mcp-server.py     # Main MCP server
├── install.sh                # Installation script
├── config.example.json       # Example configuration
├── setup.sh                  # Setup script
├── LICENSE                   # License file
└── docs/                     # Additional documentation
    ├── API.md               # API reference
    ├── EXAMPLES.md          # Usage examples
    └── TROUBLESHOOTING.md   # Troubleshooting guide
```

## Troubleshooting

### "API key not configured"

Make sure you've set the API key in `~/.aapanel/config.json` or as an environment variable.

### "Connection refused"

Check that aaPanel is running and accessible at the configured URL.

### "Permission denied"

Make sure the script is executable: `chmod +x aapanel-mcp-server.py`

### Docker commands fail

Ensure Docker is installed and the user has permissions to run Docker commands.

## Security Notes

- Keep your API key secure
- Don't commit `config.json` to version control
- Use environment variables in production
- Restrict API key permissions in aaPanel if possible

## License

See LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting guide
2. Review the API documentation
3. Check aaPanel logs: `/www/server/panel/logs/`

## Contributing

Contributions welcome! Please ensure:
- Code follows Python PEP 8 style
- All methods are documented
- Error handling is comprehensive
- Tests are included for new features

---

**Version:** 1.0.0  
**Last Updated:** November 2025
