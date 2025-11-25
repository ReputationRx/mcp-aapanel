# Usage Examples

## Basic Examples

### Get System Information

```bash
echo '{"method": "aapanel/get_system_info"}' | python3 aapanel-mcp-server.py
```

### Get Docker Status

```bash
echo '{"method": "aapanel/get_docker_status"}' | python3 aapanel-mcp-server.py
```

### Stop a Container

```bash
echo '{"method": "aapanel/stop_container", "params": {"container_name": "my-container"}}' | python3 aapanel-mcp-server.py
```

## Advanced Examples

### Create Database for Application

```bash
cat <<EOF | python3 aapanel-mcp-server.py
{
  "method": "aapanel/create_database",
  "params": {
    "db_name": "myapp_db",
    "db_user": "myapp_user",
    "db_pass": "SecurePassword123!"
  }
}
EOF
```

### Setup Drupal Database

```bash
echo '{"method": "aapanel/setup_drupal_database"}' | python3 aapanel-mcp-server.py
```

### Get PM2 Application Logs

```bash
cat <<EOF | python3 aapanel-mcp-server.py
{
  "method": "aapanel/pm2_logs",
  "params": {
    "app_name": "my-app",
    "lines": 100
  }
}
EOF
```

### Restart Service

```bash
echo '{"method": "aapanel/restart_service", "params": {"service_name": "nginx"}}' | python3 aapanel-mcp-server.py
```

## Python Script Examples

### Monitor Resources

```python
import json
import subprocess

request = {"method": "aapanel/get_resource_usage"}
result = subprocess.run(
    ['python3', 'aapanel-mcp-server.py'],
    input=json.dumps(request),
    text=True,
    capture_output=True
)
data = json.loads(result.stdout)
print(data)
```

### Manage Container

```python
import json
import subprocess

def manage_container(action, container_name):
    request = {
        "method": f"aapanel/{action}_container",
        "params": {"container_name": container_name}
    }
    result = subprocess.run(
        ['python3', 'aapanel-mcp-server.py'],
        input=json.dumps(request),
        text=True,
        capture_output=True
    )
    return json.loads(result.stdout)

# Stop container
result = manage_container("stop", "my-container")
print(result)
```

## Shell Script Examples

### Check All Services

```bash
#!/bin/bash

methods=(
    "get_system_info"
    "get_docker_status"
    "get_pm2_status"
    "get_all_services_status"
)

for method in "${methods[@]}"; do
    echo "=== $method ==="
    echo "{\"method\": \"aapanel/$method\"}" | python3 aapanel-mcp-server.py
    echo ""
done
```

### Monitor Container

```bash
#!/bin/bash

CONTAINER_NAME="my-container"

# Get status
echo "Checking container status..."
echo "{\"method\": \"aapanel/get_docker_status\"}" | python3 aapanel-mcp-server.py | jq ".containers[] | select(.Names==\"$CONTAINER_NAME\")"

# Restart if needed
echo "{\"method\": \"aapanel/restart_container\", \"params\": {\"container_name\": \"$CONTAINER_NAME\"}}" | python3 aapanel-mcp-server.py
```

## Integration Examples

### With Cursor/Claude

Add to your MCP configuration:

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

Then use in your AI assistant:

```
User: "Check Docker container status"
Assistant: [Calls aapanel/get_docker_status]
```

### With Node.js

```javascript
const { spawn } = require('child_process');

function callMCP(method, params = {}) {
  return new Promise((resolve, reject) => {
    const request = JSON.stringify({ method, params });
    const mcp = spawn('python3', ['aapanel-mcp-server.py']);
    
    let output = '';
    mcp.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    mcp.on('close', (code) => {
      if (code === 0) {
        resolve(JSON.parse(output));
      } else {
        reject(new Error(`Process exited with code ${code}`));
      }
    });
    
    mcp.stdin.write(request);
    mcp.stdin.end();
  });
}

// Usage
callMCP('aapanel/get_docker_status')
  .then(result => console.log(result))
  .catch(err => console.error(err));
```
