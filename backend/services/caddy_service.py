"""
Caddy Reverse Proxy Service
Manages automatic reverse proxy and load balancing for deployed applications.

Note: Alpine Linux uses OpenRC init system with these exit codes:
- Exit 0: Service is running
- Exit 3: Service is stopped (normal state, not an error)
- Exit 1/2: Service error or not found

When checking service status, exit code 3 should be handled as normal.
"""

import asyncio
import logging
import json
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class CaddyConfig:
    """Caddy configuration generator"""
    
    def __init__(self, admin_port: int = 2019, proxy_port: int = 8080):
        self.admin_port = admin_port
        self.proxy_port = proxy_port
        self.apps: Dict[str, Dict] = {}
    
    def add_app(self, app_id: str, path_prefix: str, backend_url: str):
        """
        Add application to Caddy configuration with path-based routing
        
        Args:
            app_id: Application ID
            path_prefix: URL path prefix (e.g., /wordpress-01)
            backend_url: Backend URL (e.g., http://192.168.1.100:80)
        """
        self.apps[app_id] = {
            "path": path_prefix,
            "backend": backend_url
        }
        
        logger.info(f"Added Caddy route: {path_prefix} -> {backend_url}")
    
    def remove_app(self, app_id: str):
        """Remove application from Caddy configuration"""
        if app_id in self.apps:
            path = self.apps[app_id]["path"]
            del self.apps[app_id]
            logger.info(f"Removed Caddy route for {path}")
    
    def generate_caddyfile(self) -> str:
        """
        Generate Caddyfile configuration with path-based routing
        
        Returns:
            Caddyfile content as string
        """
        lines = [
            "# Proximity Auto-Generated Caddy Configuration",
            "# DO NOT EDIT MANUALLY - Managed by Proximity",
            "",
            "# Global options",
            "{",
            "    admin 0.0.0.0:2019",
            "    auto_https off  # Disable for LAN",
            "}",
            "",
            "# Health check endpoint on separate port",
            ":2020 {",
            "    respond /health 200",
            "    respond / \"Proximity Caddy Proxy\" 200",
            "}",
            "",
            f"# Main reverse proxy on port {self.proxy_port}",
            f":{self.proxy_port} {{",
            ""
        ]
        
        # Add routes for each app with path-based routing
        if self.apps:
            lines.append("    # Application routes")
            for app_id, config in self.apps.items():
                path = config["path"]
                backend = config["backend"]
                
                lines.extend([
                    f"    # Application: {app_id}",
                    f"    handle_path {path}/* {{",
                    f"        reverse_proxy {backend} {{",
                    "            header_up Host {upstream_hostport}",
                    "            header_up X-Real-IP {{remote_host}}",
                    "            header_up X-Forwarded-For {{remote_host}}",
                    "            header_up X-Forwarded-Proto {{scheme}}",
                    "        }}",
                    "    }}",
                    f"    handle {path} {{",
                    f"        redir {path}/ permanent",
                    "    }}",
                    ""
                ])
        
        # Default response for undefined routes
        lines.extend([
            "    # Default response",
            "    handle {",
            "        respond \"Proximity - Available apps: " + ", ".join([cfg["path"] for cfg in self.apps.values()]) + "\" 200",
            "    }",
            "}",
            ""
        ])
        
        return "\n".join(lines)
    
    def generate_json_config(self) -> Dict:
        """
        Generate Caddy JSON configuration for API
        
        Returns:
            Caddy JSON config dict
        """
        config = {
            "admin": {
                "listen": f"0.0.0.0:{self.admin_port}"
            },
            "apps": {
                "http": {
                    "servers": {
                        "proximity": {
                            "listen": [":80", ":443"],
                            "routes": []
                        }
                    }
                }
            }
        }
        
        # Add routes for each app
        for app_id, app_config in self.apps.items():
            for host in app_config["hosts"]:
                route = {
                    "match": [{"host": [host]}],
                    "handle": [{
                        "handler": "reverse_proxy",
                        "upstreams": [{"dial": app_config["backend"].replace("http://", "")}],
                        "headers": {
                            "request": {
                                "set": {
                                    "X-Real-IP": ["{http.request.remote.host}"],
                                    "X-Forwarded-For": ["{http.request.remote.host}"],
                                    "X-Forwarded-Proto": ["{http.request.scheme}"]
                                }
                            }
                        }
                    }],
                    "terminal": True
                }
                config["apps"]["http"]["servers"]["proximity"]["routes"].append(route)
        
        return config


class CaddyService:
    """Manages Caddy reverse proxy lifecycle"""
    
    def __init__(self, proxmox_service, config_dir: str = "/etc/proximity/caddy"):
        self.proxmox = proxmox_service
        self.config_dir = Path(config_dir)
        self.config = CaddyConfig()
        
        # Caddy container details
        self.caddy_node = None
        self.caddy_lxc_id = None
        self.is_deployed = False
    
    async def ensure_caddy_deployed(self, node: str) -> bool:
        """
        Ensure Caddy proxy is deployed and running
        
        Args:
            node: Proxmox node to deploy Caddy on
            
        Returns:
            True if Caddy is ready, False otherwise
        """
        try:
            # Check if Caddy LXC exists
            containers = await self.proxmox.get_lxc_containers(node)
            
            for container in containers:
                # LXCInfo is a Pydantic model, use dot notation
                if container.name == "proximity-caddy":
                    self.caddy_node = node
                    self.caddy_lxc_id = container.vmid
                    self.is_deployed = True
                    
                    # Check if running
                    status = container.status.value if hasattr(container.status, 'value') else str(container.status)
                    if status != "running":
                        logger.info("Starting Caddy container...")
                        await self.proxmox.start_lxc(node, self.caddy_lxc_id)
                    
                    logger.info(f"Caddy proxy ready on {node} (LXC {self.caddy_lxc_id})")
                    return True
            
            # Deploy new Caddy container
            logger.info(f"Deploying Caddy proxy on {node}...")
            await self._deploy_caddy(node)
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure Caddy deployment: {e}")
            return False
    
    async def _deploy_caddy(self, node: str):
        """Deploy Caddy LXC container with network access"""
        try:
            # Create Alpine LXC for Caddy
            self.caddy_lxc_id = await self.proxmox.get_next_vmid()
            
            logger.info(f"Creating Caddy container (LXC {self.caddy_lxc_id})...")
            
            # Create container with config dict
            # Note: Caddy will listen on port 8080 inside the container
            # Users on local network access via: http://<caddy-container-ip>:8080/app-name
            # For production, set up port forwarding on Proxmox host:
            #   iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 8080 -j DNAT --to <caddy-ip>:8080
            lxc_config = {
                "hostname": "proximity-caddy",
                "cores": 2,
                "memory": 512,
                "description": "Proximity Caddy Reverse Proxy - Access on port 8080"
            }
            
            create_result = await self.proxmox.create_lxc(
                node=node,
                vmid=self.caddy_lxc_id,
                config=lxc_config
            )
            
            # Wait for creation task
            await self.proxmox.wait_for_task(node, create_result["task_id"])
            
            logger.info("Starting Caddy container...")
            await self.proxmox.start_lxc(node, self.caddy_lxc_id)
            
            # Wait for container to be ready
            import asyncio
            await asyncio.sleep(5)
            
            # Install Caddy
            logger.info("Installing Caddy in container...")
            await self._install_caddy(node, self.caddy_lxc_id)
            
            self.caddy_node = node
            self.is_deployed = True
            
            logger.info(f"✓ Caddy proxy deployed successfully on {node}")
            
        except Exception as e:
            logger.error(f"Failed to deploy Caddy: {e}")
            raise
    
    async def _install_caddy(self, node: str, lxc_id: int):
        """Install Caddy inside the container"""
        commands = [
            # Update package index
            "apk update",
            
            # Install Caddy from Alpine community repo
            "apk add caddy",
            
            # Create directories
            "mkdir -p /etc/caddy /var/log/caddy /var/lib/caddy",
            
            # Set permissions (if caddy user exists, otherwise skip)
            "id caddy && chown -R caddy:caddy /var/log/caddy /var/lib/caddy || true",
        ]
        
        for cmd in commands:
            result = await self.proxmox.execute_in_container(node, lxc_id, cmd)
            logger.debug(f"Caddy setup: {cmd} -> {result[:100] if result else 'OK'}")
        
        # Create OpenRC init script for Caddy
        init_script = """#!/sbin/openrc-run

description="Caddy web server"
command="/usr/sbin/caddy"
command_args="run --config /etc/caddy/Caddyfile --adapter caddyfile"
command_background="yes"
pidfile="/run/caddy.pid"
output_log="/var/log/caddy/caddy.log"
error_log="/var/log/caddy/caddy.err"

depend() {
    need net
    after firewall
}

start_pre() {
    checkpath --directory --owner root:root --mode 0755 /var/log/caddy
    checkpath --directory --owner root:root --mode 0755 /var/lib/caddy
}
"""
        
        # Write init script
        init_script_cmd = f"cat > /etc/init.d/caddy << 'EOFSCRIPT'\n{init_script}\nEOFSCRIPT"
        await self.proxmox.execute_in_container(node, lxc_id, init_script_cmd)
        
        # Make init script executable
        await self.proxmox.execute_in_container(node, lxc_id, "chmod +x /etc/init.d/caddy")
        
        # Create initial Caddyfile
        await self.proxmox.execute_in_container(node, lxc_id, "echo ':2020 { respond /health 200 }' > /etc/caddy/Caddyfile")
        
        # Enable and start Caddy service
        await self.proxmox.execute_in_container(node, lxc_id, "rc-update add caddy default")
        await self.proxmox.execute_in_container(node, lxc_id, "rc-service caddy start")
    
    async def add_application(self, app_id: str, path_prefix: str, 
                             backend_ip: str, backend_port: int = 80):
        """
        Add application to reverse proxy with path-based routing
        
        Args:
            app_id: Application ID
            path_prefix: URL path prefix (e.g., /wordpress-01)
            backend_ip: Backend container IP address (LXC IP)
            backend_port: Backend port (exposed on LXC, e.g., 80)
            
        Note: backend_ip should be the LXC container IP, not the Docker container IP.
              Docker containers must expose ports on the LXC network (e.g., "80:80" in docker-compose).
        """
        if not self.is_deployed:
            raise RuntimeError("Caddy is not deployed")
        
        backend_url = f"{backend_ip}:{backend_port}"
        
        # Add to configuration
        self.config.add_app(
            app_id=app_id,
            path_prefix=path_prefix,
            backend_url=backend_url
        )
        
        # Update Caddy configuration
        await self._update_caddy_config()
        
        # Ensure Caddy is running
        is_running = await self.is_caddy_running()
        if not is_running:
            logger.info("Starting Caddy service...")
            try:
                await self.proxmox.execute_in_container(
                    self.caddy_node,
                    self.caddy_lxc_id,
                    "rc-service caddy start",
                    allow_nonzero_exit=True
                )
                await asyncio.sleep(2)  # Wait for Caddy to start
                logger.info("✓ Caddy service started")
            except Exception as e:
                logger.warning(f"Failed to start Caddy: {e}")
        
        logger.info(f"Added {path_prefix} -> {backend_url} to Caddy proxy")
    
    async def remove_application(self, app_id: str):
        """Remove application from reverse proxy"""
        if not self.is_deployed:
            return
        
        self.config.remove_app(app_id)
        await self._update_caddy_config()
    
    async def _update_caddy_config(self):
        """Update Caddy configuration file and reload"""
        if not self.is_deployed:
            return
        
        try:
            # Generate Caddyfile
            caddyfile = self.config.generate_caddyfile()
            
            # Write to container
            # Escape single quotes and newlines for shell
            escaped_config = caddyfile.replace("'", "'\\''")
            
            write_cmd = f"cat > /etc/caddy/Caddyfile << 'PROXIMITY_EOF'\n{caddyfile}\nPROXIMITY_EOF"
            
            await self.proxmox.execute_in_container(
                self.caddy_node,
                self.caddy_lxc_id,
                write_cmd
            )
            
            # Reload Caddy (or start if not running)
            await self.proxmox.execute_in_container(
                self.caddy_node,
                self.caddy_lxc_id,
                "rc-service caddy reload || rc-service caddy start",
                allow_nonzero_exit=True
            )
            
            logger.info("Caddy configuration updated and reloaded")
            
        except Exception as e:
            logger.error(f"Failed to update Caddy config: {e}")
            raise
    
    async def get_caddy_ip(self) -> Optional[str]:
        """Get Caddy proxy IP address"""
        if not self.is_deployed:
            return None
        
        try:
            # Get container network info
            result = await self.proxmox.execute_in_container(
                self.caddy_node,
                self.caddy_lxc_id,
                "ip -4 addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1"
            )
            
            ip = result.strip()
            return ip if ip else None
            
        except Exception as e:
            logger.error(f"Failed to get Caddy IP: {e}")
            return None
    
    async def is_caddy_running(self) -> bool:
        """Check if Caddy is running"""
        if not self.is_deployed:
            return False
        
        try:
            # Check LXC status
            lxc_status = await self.proxmox.get_lxc_status(self.caddy_node, self.caddy_lxc_id)
            if lxc_status.status.value != "running":
                return False
            
            # Check if Caddy service is running
            # Note: OpenRC returns exit code 3 when service is stopped (not an error)
            result = await self.proxmox.execute_in_container(
                self.caddy_node,
                self.caddy_lxc_id,
                "rc-service caddy status",
                allow_nonzero_exit=True  # Exit code 3 = stopped (normal)
            )
            
            # OpenRC status output contains "started" when running, "stopped" when not
            return "started" in result.lower()
            
        except Exception as e:
            logger.error(f"Failed to check Caddy status: {e}")
            return False
    
    async def get_status(self) -> Dict:
        """Get Caddy proxy status"""
        if not self.is_deployed:
            return {
                "deployed": False,
                "status": "not_deployed"
            }
        
        try:
            # Check if Caddy is running
            # Note: OpenRC returns exit code 3 when service is stopped (not an error)
            result = await self.proxmox.execute_in_container(
                self.caddy_node,
                self.caddy_lxc_id,
                "rc-service caddy status",
                allow_nonzero_exit=True  # Exit code 3 = stopped (normal)
            )
            
            # OpenRC status output contains "started" when running, "stopped" when not
            is_running = "started" in result.lower()
            
            caddy_ip = await self.get_caddy_ip()
            
            return {
                "deployed": True,
                "status": "running" if is_running else "stopped",
                "node": self.caddy_node,
                "lxc_id": self.caddy_lxc_id,
                "ip": caddy_ip,
                "routes": len(self.config.apps),
                "apps": list(self.config.apps.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to get Caddy status: {e}")
            return {
                "deployed": True,
                "status": "error",
                "error": str(e)
            }


# Singleton instance
_caddy_service: Optional[CaddyService] = None


def get_caddy_service(proxmox_service=None) -> CaddyService:
    """Get Caddy service singleton"""
    global _caddy_service
    
    if _caddy_service is None:
        if proxmox_service is None:
            from services.proxmox_service import proxmox_service as px_service
            proxmox_service = px_service
        
        _caddy_service = CaddyService(proxmox_service)
    
    return _caddy_service
