# Troubleshooting Guide

## Common Issues and Solutions

### "API key not configured"

**Problem:** The MCP server cannot find your API key.

**Solutions:**
1. Check that `~/.aapanel/config.json` exists and contains your API key
2. Verify the API key is correct (get it from aaPanel: Settings → API)
3. Try using environment variables instead:
   ```bash
   export AAPANEL_API_KEY="your_api_key"
   export AAPANEL_URL="http://localhost:7800"
   ```

### "Connection refused" or "Cannot connect to aaPanel"

**Problem:** Cannot reach aaPanel API.

**Solutions:**
1. Verify aaPanel is running:
   ```bash
   systemctl status bt
   ```
2. Check the URL is correct (default: `http://localhost:7800`)
3. If accessing remotely, ensure:
   - Firewall allows the port
   - Use SSH tunneling: `ssh -L 7800:localhost:7800 user@server`
   - Or update URL to use server IP/domain

### "Permission denied" errors

**Problem:** Insufficient permissions to run commands.

**Solutions:**
1. Ensure user has permissions for Docker:
   ```bash
   sudo usermod -aG docker $USER
   ```
2. Check file permissions:
   ```bash
   chmod +x aapanel-mcp-server.py
   chmod 600 ~/.aapanel/config.json
   ```
3. For system services, may need sudo or run as root

### Docker commands fail

**Problem:** Docker-related methods return errors.

**Solutions:**
1. Verify Docker is installed and running:
   ```bash
   systemctl status docker
   docker ps
   ```
2. Check user is in docker group:
   ```bash
   groups
   # Should include 'docker'
   ```
3. Try running Docker command manually to see specific error

### Image transfer fails or memory does not drop

**Problem:** `transfer_docker_images` errors, or RAM stays high after a copy.

**Solutions:**
1. Confirm key login from this host. A password prompt will fail:
   ```bash
   ssh -o BatchMode=yes -i /root/.ssh/id_ed25519 root@OTHER_HOST docker version
   ```
2. Copying an image moves layers to the other machine's disk. RAM on this machine drops when containers that use those images are stopped (`stop_containers`). Disk used by the layers drops when the local image is removed (`remove_local`). A stopped container still references its image, so remove that container first (`remove_containers`) or `docker rmi` will fail.
3. Volumes are not deleted. A large volume still uses disk after the image is gone.
4. The other aaPanel must be able to run `docker load`. Set `use_sudo` when that user needs `sudo -n docker`.
5. Use `dry_run` to see which containers would be affected before stopping them.

### PM2 commands fail

**Problem:** PM2 methods return errors.

**Solutions:**
1. Verify PM2 is installed:
   ```bash
   pm2 --version
   ```
2. Check PM2 is in PATH:
   ```bash
   which pm2
   ```
3. Try running PM2 command manually:
   ```bash
   pm2 list
   ```

### "Invalid JSON" error

**Problem:** Request format is incorrect.

**Solutions:**
1. Verify JSON is valid:
   ```bash
   echo '{"method": "aapanel/get_system_info"}' | python3 -m json.tool
   ```
2. Check for trailing commas or syntax errors
3. Ensure proper escaping of special characters

### Database creation fails

**Problem:** Cannot create databases.

**Solutions:**
1. Verify MySQL/MariaDB is running:
   ```bash
   systemctl status mysql
   # or
   systemctl status mariadb
   ```
2. Check MySQL root password is accessible
3. Try using aaPanel bt command manually:
   ```bash
   bt database add test_db test_user test_pass
   ```
4. Verify user has MySQL permissions

### SSL certificate methods fail

**Problem:** SSL-related methods return errors.

**Solutions:**
1. Check SSL scripts exist:
   ```bash
   ls -la /www/server/panel/script/ssl/
   ```
2. Verify aaPanel SSL functionality works in web interface
3. Check file permissions on SSL scripts

### Timeout errors

**Problem:** Methods timeout before completing.

**Solutions:**
1. Increase timeout in code (if modifying source)
2. Check system resources (CPU, memory, disk)
3. Verify network connectivity
4. Check for stuck processes:
   ```bash
   ps aux | grep docker
   ps aux | grep python
   ```

### Configuration file not found

**Problem:** Config file is not being read.

**Solutions:**
1. Check file exists:
   ```bash
   ls -la ~/.aapanel/config.json
   ```
2. Verify file permissions:
   ```bash
   chmod 600 ~/.aapanel/config.json
   ```
3. Check JSON syntax:
   ```bash
   python3 -m json.tool ~/.aapanel/config.json
   ```
4. Try using absolute path in code

## Debugging

### Enable verbose output

Add debug logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test individual components

```bash
# Test Python
python3 --version

# Test requests library
python3 -c "import requests; print(requests.__version__)"

# Test Docker
docker --version
docker ps

# Test PM2
pm2 --version
pm2 list

# Test MySQL
mysql --version
mysql -u root -e "SHOW DATABASES;"
```

### Check logs

```bash
# System logs
journalctl -xe

# Docker logs
docker logs <container-name>

# PM2 logs
pm2 logs

# aaPanel logs
tail -f /www/server/panel/logs/error.log
```

## Getting Help

1. Check the API documentation: `docs/API.md`
2. Review examples: `docs/EXAMPLES.md`
3. Check aaPanel documentation
4. Review error messages carefully
5. Test components individually

## Reporting Issues

When reporting issues, include:
- Error message
- Method being called
- System information (OS, Python version, etc.)
- Relevant logs
- Steps to reproduce
