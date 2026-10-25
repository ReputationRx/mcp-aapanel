# aaPanel MCP Server API Reference

## Overview

The aaPanel MCP Server provides a comprehensive API for managing aaPanel/BT Panel servers through the Model Context Protocol.

## Request Format

All requests are JSON objects with the following structure:

```json
{
  "method": "aapanel/method_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

## Response Format

All responses are JSON objects:

```json
{
  "success": true,
  "data": {...},
  "error": null
}
```

Or on error:

```json
{
  "error": "Error message"
}
```

## System & Resource Methods

### get_system_info

Get system information (memory, disk, uptime).

**Request:**
```json
{
  "method": "aapanel/get_system_info"
}
```

**Response:**
```json
{
  "memory": "Mem: 7.7Gi 4.3Gi 3.5Gi...",
  "disk": "Filesystem Size Used Avail...",
  "uptime": "23:36:47 up 2 days..."
}
```

### get_resource_usage

Get current resource usage (CPU, memory, disk, Docker).

**Request:**
```json
{
  "method": "aapanel/get_resource_usage"
}
```

### get_dashboard

Get comprehensive dashboard information.

**Request:**
```json
{
  "method": "aapanel/get_dashboard"
}
```

## Docker Management

### get_docker_status

Get Docker container status and statistics.

**Request:**
```json
{
  "method": "aapanel/get_docker_status"
}
```

**Response:**
```json
{
  "containers": [...],
  "stats": [...]
}
```

### stop_container

Stop a Docker container.

**Request:**
```json
{
  "method": "aapanel/stop_container",
  "params": {
    "container_name": "my-container"
  }
}
```

### start_container

Start a Docker container.

**Request:**
```json
{
  "method": "aapanel/start_container",
  "params": {
    "container_name": "my-container"
  }
}
```

### restart_container

Restart a Docker container.

**Request:**
```json
{
  "method": "aapanel/restart_container",
  "params": {
    "container_name": "my-container"
  }
}
```

### list_docker_images

List local images sorted by size, plus current RAM, Docker disk usage, and running container stats.

**Request:**
```json
{
  "method": "aapanel/list_docker_images"
}
```

**Response:**
```json
{
  "images": [
    {"id": "sha256:...", "tags": ["nginx:1.27"], "size_bytes": 180000000, "size": "171.7 MB"}
  ],
  "count": 1,
  "running_containers": [],
  "memory": "Mem: ...",
  "disk": "TYPE ..."
}
```

### transfer_docker_images

Stream one or more local images to Docker on another aaPanel host. The destination panel reads its local Docker engine, so a loaded image shows up under Docker → Images.

The transfer is `docker save` piped over SSH into `docker load`. Nothing is written to a tar on the source, which matters when disk is already tight. Compression uses `gzip -1` unless `compress` is false.

Only image layers are copied. Container configuration, volumes, bind mounts, networks, and environment variables stay on the source. Recreate the container on the destination after the image is there.

SSH must accept key authentication. The command runs with `BatchMode=yes`, so a password prompt fails instead of hanging. The first connection stores the host key (`StrictHostKeyChecking=accept-new`).

`stop_containers`, `remove_containers`, and `remove_local` default to false. Local cleanup runs only after the destination reports the image id. A failed copy leaves this machine unchanged.

**Request:**
```json
{
  "method": "aapanel/transfer_docker_images",
  "params": {
    "images": ["nginx:1.27", "redis:7"],
    "target": "secondary",
    "dry_run": false,
    "compress": true,
    "stop_containers": false,
    "remove_containers": false,
    "remove_local": false,
    "timeout_seconds": 3600
  }
}
```

`target` names an entry in `docker_targets` in `~/.aapanel/config.json`. You can pass `host`, `user`, `port`, `ssh_key`, and `use_sudo` instead of, or as overrides on, a saved target.

| Param | Default | Effect |
| --- | --- | --- |
| `images` | required | Image name, tag, or id. One string or a list of up to 20. |
| `dry_run` | false | Report the plan and do not connect. |
| `stop_containers` | false | Stop running containers that use these images. This releases their RAM. |
| `remove_containers` | false | Remove those containers after they are stopped. Required before a local image delete if a container still references it. Does not delete volumes. |
| `remove_local` | false | `docker rmi` on this machine after the destination has the image. This releases image-layer disk. |
| `use_sudo` | false | Run `sudo -n docker` on the destination. |
| `timeout_seconds` | 3600 | Limit for the stream. 30–86400. |

**Response (success):**
```json
{
  "success": true,
  "transferred": true,
  "verified": [{"name": "nginx:1.27", "id": "sha256:..."}],
  "memory_note": "Copied the images. Containers using them are still running...",
  "not_transferred": ["container configuration", "volumes and bind mounts", "networks", "environment variables"]
}
```

## PM2 Management

### get_pm2_status

Get PM2 application status.

**Request:**
```json
{
  "method": "aapanel/get_pm2_status"
}
```

### pm2_start

Start a PM2 application.

**Request:**
```json
{
  "method": "aapanel/pm2_start",
  "params": {
    "app_name": "my-app"
  }
}
```

### pm2_stop

Stop a PM2 application.

**Request:**
```json
{
  "method": "aapanel/pm2_stop",
  "params": {
    "app_name": "my-app"
  }
}
```

### pm2_restart

Restart a PM2 application.

**Request:**
```json
{
  "method": "aapanel/pm2_restart",
  "params": {
    "app_name": "my-app"
  }
}
```

### pm2_logs

Get PM2 application logs.

**Request:**
```json
{
  "method": "aapanel/pm2_logs",
  "params": {
    "app_name": "my-app",
    "lines": 50
  }
}
```

## SSL Management

### get_ssl_list

Get list of SSL certificates.

**Request:**
```json
{
  "method": "aapanel/get_ssl_list"
}
```

### get_ssl_status

Get SSL certificate status for a domain.

**Request:**
```json
{
  "method": "aapanel/get_ssl_status",
  "params": {
    "domain": "example.com"
  }
}
```

### renew_ssl

Renew SSL certificate.

**Request:**
```json
{
  "method": "aapanel/renew_ssl",
  "params": {
    "domain": "example.com"
  }
}
```

## Database Management

### create_database

Create MySQL database and user.

**Request:**
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

**Note:** If `db_user` or `db_pass` are not provided, they will be auto-generated.

### list_databases

List all MySQL databases.

**Request:**
```json
{
  "method": "aapanel/list_databases"
}
```

### setup_drupal_database

Complete Drupal database setup (creates database, user, and configures settings.php).

**Request:**
```json
{
  "method": "aapanel/setup_drupal_database"
}
```

**Response:**
```json
{
  "success": true,
  "database": "drupal_slideindm",
  "username": "drupal_user",
  "password": "generated_password",
  "settings_file": "/www/wwwroot/drupal.slideindm.com/sites/default/settings.php",
  "message": "Drupal database setup complete..."
}
```

## Service Management

### get_sites

Get list of websites from aaPanel.

**Request:**
```json
{
  "method": "aapanel/get_sites"
}
```

### restart_service

Restart a system service.

**Request:**
```json
{
  "method": "aapanel/restart_service",
  "params": {
    "service_name": "nginx"
  }
}
```

### get_logs

Get logs from a service.

**Request:**
```json
{
  "method": "aapanel/get_logs",
  "params": {
    "service_name": "nginx",
    "lines": 100
  }
}
```

### get_all_services_status

Get status of all services.

**Request:**
```json
{
  "method": "aapanel/get_all_services_status"
}
```

### service_manager

Unified service manager.

**Request:**
```json
{
  "method": "aapanel/service_manager",
  "params": {
    "service_type": "docker",
    "action": "status",
    "service_name": "my-container"
  }
}
```

## Error Handling

All methods return error responses in the following format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common errors:
- `"API key not configured"` - API key is missing
- `"Unknown method: method_name"` - Method doesn't exist
- `"Connection refused"` - Cannot connect to aaPanel
- `"Permission denied"` - Insufficient permissions

## Rate Limiting

No rate limiting is implemented. However, be mindful of:
- System resource usage
- aaPanel API rate limits
- Network bandwidth

## Security Considerations

1. **API Key Security**: Keep your API key secure and never commit it to version control
2. **Network Security**: Use HTTPS when possible, or SSH tunneling for remote access
3. **Permissions**: Run the MCP server with appropriate user permissions
4. **Firewall**: Restrict access to the MCP server if exposed

## Best Practices

1. Always check for errors in responses
2. Use appropriate timeouts for long-running operations
3. Cache system information when possible
4. Handle connection errors gracefully
5. Log operations for debugging
