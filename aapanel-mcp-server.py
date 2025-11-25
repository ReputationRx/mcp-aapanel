#!/usr/bin/env python3
"""
aaPanel MCP Server
Provides Model Context Protocol interface for managing aaPanel server
"""

import json
import sys
import subprocess
import requests
from typing import Dict, Any, List, Optional
import base64
import os
import time

class AAPanelMCPServer:
    def __init__(self):
        self.api_url = None
        self.api_key = None
        self.load_config()
    
    def load_config(self):
        """Load aaPanel API configuration"""
        try:
            # Try to read from environment or config file
            import os
            self.api_url = os.getenv('AAPANEL_URL', 'http://localhost:7800')
            self.api_key = os.getenv('AAPANEL_API_KEY', '')
            
            # Try to read from config file (try user home first, then /root)
            config_paths = [
                os.path.expanduser('~/.aapanel/config.json'),
                '/root/.aapanel/config.json'
            ]
            for config_path in config_paths:
                try:
                    if os.path.exists(config_path):
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                            self.api_url = config.get('url', self.api_url)
                            self.api_key = config.get('api_key', self.api_key)
                        break
                except:
                    pass
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr)
    
    def make_request(self, action: str, params: Dict = None) -> Dict:
        """Make request to aaPanel API"""
        if not self.api_key:
            return {"error": "API key not configured"}
        
        url = f"{self.api_url}/api"
        data = {
            "request_token": self._get_token(),
            "request_time": self._get_time(),
            "action": action
        }
        if params:
            data.update(params)
        
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def _get_token(self) -> str:
        """Generate request token"""
        import hashlib
        import time
        timestamp = int(time.time())
        token_string = f"{self.api_key}{timestamp}"
        return hashlib.md5(token_string.encode()).hexdigest()
    
    def _get_time(self) -> int:
        """Get current timestamp"""
        import time
        return int(time.time())
    
    def handle_request(self, request: Dict) -> Dict:
        """Handle MCP request"""
        method = request.get('method')
        params = request.get('params', {})
        
        # System & Resource Methods
        if method == 'aapanel/get_system_info':
            return self.get_system_info()
        elif method == 'aapanel/get_resource_usage':
            return self.get_resource_usage()
        elif method == 'aapanel/get_dashboard':
            return self.get_dashboard()
        
        # Docker Methods
        elif method == 'aapanel/get_docker_status':
            return self.get_docker_status()
        elif method == 'aapanel/stop_container':
            return self.stop_container(params.get('container_name'))
        elif method == 'aapanel/start_container':
            return self.start_container(params.get('container_name'))
        elif method == 'aapanel/restart_container':
            return self.restart_container(params.get('container_name'))
        
        # PM2 Methods
        elif method == 'aapanel/get_pm2_status':
            return self.get_pm2_status()
        elif method == 'aapanel/pm2_start':
            return self.pm2_start(params.get('app_name'))
        elif method == 'aapanel/pm2_stop':
            return self.pm2_stop(params.get('app_name'))
        elif method == 'aapanel/pm2_restart':
            return self.pm2_restart(params.get('app_name'))
        elif method == 'aapanel/pm2_logs':
            return self.pm2_logs(params.get('app_name'), params.get('lines', 50))
        
        # SSL Methods
        elif method == 'aapanel/get_ssl_list':
            return self.get_ssl_list()
        elif method == 'aapanel/get_ssl_status':
            return self.get_ssl_status(params.get('domain'))
        elif method == 'aapanel/renew_ssl':
            return self.renew_ssl(params.get('domain'))
        
        # System Service Methods
        elif method == 'aapanel/get_sites':
            return self.get_sites()
        elif method == 'aapanel/restart_service':
            return self.restart_service(params.get('service_name'))
        elif method == 'aapanel/get_logs':
            return self.get_logs(params.get('service_name'), params.get('lines', 50))
        elif method == 'aapanel/get_all_services_status':
            return self.get_all_services_status()
        
        # Unified Management Methods
        elif method == 'aapanel/service_manager':
            return self.service_manager(params.get('service_type'), params.get('action'), params.get('service_name'))
        
        # Database Methods
        elif method == 'aapanel/create_database':
            return self.create_database(
                params.get('db_name'),
                params.get('db_user'),
                params.get('db_pass')
            )
        elif method == 'aapanel/list_databases':
            return self.list_databases()
        elif method == 'aapanel/setup_drupal_database':
            return self.setup_drupal_database()
        else:
            return {"error": f"Unknown method: {method}"}
    
    def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            result = subprocess.run(
                ['free', '-h'],
                capture_output=True,
                text=True,
                timeout=5
            )
            memory = result.stdout
            
            result = subprocess.run(
                ['df', '-h'],
                capture_output=True,
                text=True,
                timeout=5
            )
            disk = result.stdout
            
            result = subprocess.run(
                ['uptime'],
                capture_output=True,
                text=True,
                timeout=5
            )
            uptime = result.stdout.strip()
            
            return {
                "memory": memory,
                "disk": disk,
                "uptime": uptime
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_sites(self) -> Dict:
        """Get list of websites from aaPanel"""
        return self.make_request("GetSiteList")
    
    def get_docker_status(self) -> Dict:
        """Get Docker container status"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))
            
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            stats = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    stats.append(json.loads(line))
            
            return {
                "containers": containers,
                "stats": stats
            }
        except Exception as e:
            return {"error": str(e)}
    
    def stop_container(self, container_name: str) -> Dict:
        """Stop a Docker container"""
        try:
            result = subprocess.run(
                ['docker', 'stop', container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def start_container(self, container_name: str) -> Dict:
        """Start a Docker container"""
        try:
            result = subprocess.run(
                ['docker', 'start', container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_resource_usage(self) -> Dict:
        """Get current resource usage"""
        try:
            # CPU usage
            result = subprocess.run(
                ['top', '-bn1'],
                capture_output=True,
                text=True,
                timeout=5
            )
            top_output = result.stdout
            
            # Memory
            result = subprocess.run(
                ['free', '-h'],
                capture_output=True,
                text=True,
                timeout=5
            )
            memory = result.stdout
            
            # Disk
            result = subprocess.run(
                ['df', '-h'],
                capture_output=True,
                text=True,
                timeout=5
            )
            disk = result.stdout
            
            # Docker stats
            result = subprocess.run(
                ['docker', 'stats', '--no-stream'],
                capture_output=True,
                text=True,
                timeout=10
            )
            docker_stats = result.stdout
            
            return {
                "cpu": top_output,
                "memory": memory,
                "disk": disk,
                "docker": docker_stats
            }
        except Exception as e:
            return {"error": str(e)}
    
    def restart_service(self, service_name: str) -> Dict:
        """Restart a system service"""
        try:
            result = subprocess.run(
                ['systemctl', 'restart', service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_logs(self, service_name: str, lines: int = 50) -> Dict:
        """Get logs from a service"""
        try:
            # Try systemd first
            result = subprocess.run(
                ['journalctl', '-u', service_name, '-n', str(lines), '--no-pager'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return {"logs": result.stdout}
            
            # Try Docker container
            result = subprocess.run(
                ['docker', 'logs', '--tail', str(lines), service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {"logs": result.stdout}
        except Exception as e:
            return {"error": str(e)}
    
    def get_dashboard(self) -> Dict:
        """Get comprehensive dashboard information"""
        try:
            result = subprocess.run(
                ['/www/server/panel/script/dashboard.sh'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {"dashboard": result.stdout}
        except Exception as e:
            # Fallback if script doesn't exist
            return {
                "docker": self.get_docker_status(),
                "pm2": self.get_pm2_status(),
                "resources": self.get_resource_usage(),
                "error": str(e) if str(e) else None
            }
    
    def get_pm2_status(self) -> Dict:
        """Get PM2 application status"""
        try:
            result = subprocess.run(
                ['pm2', 'jlist'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return {"pm2": json.loads(result.stdout)}
            else:
                # Fallback to pm2 list
                result = subprocess.run(
                    ['pm2', 'list'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return {"pm2": result.stdout}
        except Exception as e:
            return {"error": str(e)}
    
    def pm2_start(self, app_name: str = None) -> Dict:
        """Start PM2 application"""
        try:
            if app_name:
                result = subprocess.run(
                    ['pm2', 'start', app_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ['pm2', 'resurrect'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def pm2_stop(self, app_name: str = None) -> Dict:
        """Stop PM2 application"""
        try:
            if app_name:
                result = subprocess.run(
                    ['pm2', 'stop', app_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ['pm2', 'stop', 'all'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def pm2_restart(self, app_name: str = None) -> Dict:
        """Restart PM2 application"""
        try:
            if app_name:
                result = subprocess.run(
                    ['pm2', 'restart', app_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ['pm2', 'restart', 'all'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def pm2_logs(self, app_name: str, lines: int = 50) -> Dict:
        """Get PM2 application logs"""
        try:
            result = subprocess.run(
                ['pm2', 'logs', app_name, '--lines', str(lines), '--nostream'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {"logs": result.stdout}
        except Exception as e:
            return {"error": str(e)}
    
    def get_ssl_list(self) -> Dict:
        """Get list of SSL certificates"""
        try:
            result = subprocess.run(
                ['/www/server/panel/script/ssl/ssl-manager.sh', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {"ssl_list": result.stdout}
        except Exception as e:
            # Fallback
            try:
                certs = subprocess.run(
                    ['ls', '-d', '/www/server/panel/vhost/cert/*/'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return {"ssl_list": certs.stdout}
            except:
                return {"error": str(e)}
    
    def get_ssl_status(self, domain: str) -> Dict:
        """Get SSL certificate status for a domain"""
        try:
            result = subprocess.run(
                ['/www/server/panel/script/ssl/ssl-manager.sh', 'status', domain],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {"ssl_status": result.stdout}
        except Exception as e:
            return {"error": str(e)}
    
    def renew_ssl(self, domain: str = None) -> Dict:
        """Renew SSL certificate"""
        try:
            if domain:
                result = subprocess.run(
                    ['bt', 'ssl', domain],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            else:
                result = subprocess.run(
                    ['bt', 'ssl'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def restart_container(self, container_name: str) -> Dict:
        """Restart a Docker container"""
        try:
            result = subprocess.run(
                ['docker', 'restart', container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_services_status(self) -> Dict:
        """Get status of all services"""
        try:
            result = subprocess.run(
                ['/www/server/panel/script/service-manager.sh', 'all', 'status'],
                capture_output=True,
                text=True,
                timeout=15
            )
            return {"all_services": result.stdout}
        except Exception as e:
            # Fallback
            return {
                "docker": self.get_docker_status(),
                "pm2": self.get_pm2_status(),
                "system": "Use get_resource_usage for system info"
            }
    
    def service_manager(self, service_type: str, action: str, service_name: str = None) -> Dict:
        """Unified service manager"""
        try:
            cmd = ['/www/server/panel/script/service-manager.sh', service_type, action]
            if service_name:
                cmd.append(service_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def create_database(self, db_name: str, db_user: str = None, db_pass: str = None) -> Dict:
        """Create MySQL database and user"""
        try:
            import secrets
            import string
            
            if not db_name:
                return {"error": "Database name is required"}
            
            if not db_user:
                db_user = db_name.replace('-', '_').replace('.', '_')
            
            if not db_pass:
                # Generate secure password
                alphabet = string.ascii_letters + string.digits
                db_pass = ''.join(secrets.choice(alphabet) for i in range(25))
            
            # Try aaPanel bt command first
            try:
                result = subprocess.run(
                    ['bt', 'database', 'add', db_name, db_user, db_pass],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return {
                        "success": True,
                        "method": "aapanel",
                        "database": db_name,
                        "username": db_user,
                        "password": db_pass,
                        "output": result.stdout
                    }
            except:
                pass
            
            # Fallback to direct MySQL
            # Try to get MySQL root password
            mysql_root_pass = ""
            try:
                if os.path.exists('/www/server/panel/default.pl'):
                    with open('/www/server/panel/default.pl', 'r') as f:
                        content = f.read()
                        import re
                        match = re.search(r"mysql_root.*?'([^']+)'", content)
                        if match:
                            mysql_root_pass = match.group(1)
            except:
                pass
            
            mysql_cmd = ['mysql', '-u', 'root']
            if mysql_root_pass:
                mysql_cmd.extend(['-p' + mysql_root_pass])
            
            # Create database
            create_db_sql = f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            result = subprocess.run(
                mysql_cmd + ['-e', create_db_sql],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {"error": f"Failed to create database: {result.stderr}"}
            
            # Create user
            create_user_sql = f"CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_pass}';"
            grant_sql = f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'localhost'; FLUSH PRIVILEGES;"
            
            result = subprocess.run(
                mysql_cmd + ['-e', create_user_sql + grant_sql],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "method": "mysql",
                    "database": db_name,
                    "username": db_user,
                    "password": db_pass
                }
            else:
                return {"error": f"Failed to create user: {result.stderr}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def list_databases(self) -> Dict:
        """List all MySQL databases"""
        try:
            # Try aaPanel
            try:
                result = subprocess.run(
                    ['bt', 'database', 'list'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return {"databases": result.stdout, "method": "aapanel"}
            except:
                pass
            
            # Fallback to MySQL
            mysql_root_pass = ""
            try:
                if os.path.exists('/www/server/panel/default.pl'):
                    with open('/www/server/panel/default.pl', 'r') as f:
                        content = f.read()
                        import re
                        match = re.search(r"mysql_root.*?'([^']+)'", content)
                        if match:
                            mysql_root_pass = match.group(1)
            except:
                pass
            
            mysql_cmd = ['mysql', '-u', 'root', '-e', 'SHOW DATABASES;']
            if mysql_root_pass:
                mysql_cmd = ['mysql', '-u', 'root', '-p' + mysql_root_pass, '-e', 'SHOW DATABASES;']
            
            result = subprocess.run(
                mysql_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                databases = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('Database')]
                return {"databases": databases, "method": "mysql"}
            else:
                return {"error": result.stderr}
                
        except Exception as e:
            return {"error": str(e)}
    
    def setup_drupal_database(self) -> Dict:
        """Complete Drupal database setup"""
        try:
            import secrets
            import string
            
            db_name = "drupal_slideindm"
            db_user = "drupal_user"
            alphabet = string.ascii_letters + string.digits
            db_pass = ''.join(secrets.choice(alphabet) for i in range(25))
            
            drupal_path = "/www/wwwroot/drupal.slideindm.com"
            settings_file = f"{drupal_path}/sites/default/settings.php"
            
            # Create database
            db_result = self.create_database(db_name, db_user, db_pass)
            if not db_result.get("success"):
                return {"error": f"Failed to create database: {db_result.get('error')}"}
            
            # Update settings.php
            if not os.path.exists(settings_file):
                return {"error": f"Settings file not found: {settings_file}"}
            
            # Backup
            import shutil
            shutil.copy(settings_file, f"{settings_file}.backup.{int(time.time())}")
            
            # Read current settings
            with open(settings_file, 'r') as f:
                content = f.read()
            
            # Remove old database config
            import re
            content = re.sub(r"\$databases\['default'\]\['default'\].*?];", "", content, flags=re.DOTALL)
            
            # Add new config
            db_config = f"""
// Database configuration - Auto-generated
$databases['default']['default'] = [
  'database' => '{db_name}',
  'username' => '{db_user}',
  'password' => '{db_pass}',
  'host' => 'localhost',
  'port' => '3306',
  'driver' => 'mysql',
  'prefix' => '',
  'collation' => 'utf8mb4_unicode_ci',
];
"""
            content += db_config
            
            # Write back
            with open(settings_file, 'w') as f:
                f.write(content)
            
            # Set permissions
            subprocess.run(['chown', 'www:www', settings_file], timeout=5)
            subprocess.run(['chmod', '644', settings_file], timeout=5)
            
            return {
                "success": True,
                "database": db_name,
                "username": db_user,
                "password": db_pass,
                "settings_file": settings_file,
                "message": "Drupal database setup complete. Visit https://drupal.slideindm.com/core/install.php"
            }
            
        except Exception as e:
            return {"error": str(e)}


def main():
    """Main MCP server loop"""
    server = AAPanelMCPServer()
    
    # Read from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {"error": "Invalid JSON"}
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {"error": str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == '__main__':
    main()

