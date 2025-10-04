"""
Proximity Reverse Proxy Manager

This module manages dynamic Caddy virtual host configurations in the 
Network Appliance for automatic reverse proxying of application containers.

Features:
- Automatic vhost creation when apps are deployed
- Dynamic Caddy configuration without downtime
- Hostname-based routing (app-name.prox.local)
- Health check endpoints
- Automatic cleanup on app deletion

Architecture:
┌─────────────────────────────────────────────────────────────┐
│  Network Appliance (prox-appliance)                         │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Caddy Reverse Proxy (Port 80/443)                      │ │
│  │                                                          │ │
│  │  nginx.prox.local        → http://10.20.0.101:80       │ │
│  │  wordpress.prox.local    → http://10.20.0.102:80       │ │
│  │  nextcloud.prox.local    → http://10.20.0.103:80       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  /etc/caddy/sites-enabled/                                  │
│    ├── nginx.caddy                                          │
│    ├── wordpress.caddy                                      │
│    └── nextcloud.caddy                                      │
└─────────────────────────────────────────────────────────────┘

Author: Proximity Team  
Date: October 2025
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VirtualHost:
    """Virtual host configuration"""
    app_name: str
    hostname: str  # e.g., "nginx.prox.local"
    backend_ip: str  # e.g., "10.20.0.101"
    backend_port: int  # e.g., 80
    protocol: str = "http"  # http or https
    enabled: bool = True


class ReverseProxyManager:
    """
    Manages Caddy reverse proxy configurations in the Network Appliance.
    
    This service handles:
    - Creating vhost configurations for new apps
    - Updating existing vhost configurations
    - Deleting vhost configurations
    - Reloading Caddy without downtime
    - Health checking proxy status
    """
    
    DNS_DOMAIN = "prox.local"
    CADDY_SITES_DIR = "/etc/caddy/sites-enabled"
    CADDY_CONFIG = "/etc/caddy/Caddyfile"
    
    def __init__(self, appliance_vmid: int, proxmox_service=None):
        """
        Initialize the reverse proxy manager.
        
        Args:
            appliance_vmid: VMID of the network appliance LXC
            proxmox_service: ProxmoxService instance for SSH execution (optional, will import if needed)
        """
        self.appliance_vmid = appliance_vmid
        self.proxmox_service = proxmox_service
        self.vhosts: Dict[str, VirtualHost] = {}
        
    async def create_vhost(self, app_name: str, backend_ip: str, backend_port: int = 80) -> bool:
        """
        Create a new virtual host configuration for an application.
        
        This generates a Caddy configuration file and reloads Caddy to apply it.
        
        Args:
            app_name: Name of the application (e.g., "nginx-01", "wordpress")
            backend_ip: IP address of the application container (e.g., "10.20.0.101")
            backend_port: Port the application listens on (default: 80)
            
        Returns:
            bool: True if vhost created successfully
            
        Example:
            await proxy_manager.create_vhost("nginx-01", "10.20.0.101", 80)
            # Creates: nginx-01.prox.local → http://10.20.0.101:80
        """
        try:
            # Sanitize app name (remove special chars, lowercase)
            sanitized_name = self._sanitize_app_name(app_name)
            hostname = f"{sanitized_name}.{self.DNS_DOMAIN}"
            
            logger.info(f"Creating vhost: {hostname} → {backend_ip}:{backend_port}")
            
            # Generate Caddy configuration
            caddy_config = self._generate_caddy_config(hostname, backend_ip, backend_port)
            
            # Write configuration file to appliance
            config_file = f"{self.CADDY_SITES_DIR}/{sanitized_name}.caddy"
            if not await self._write_config_file(config_file, caddy_config):
                logger.error(f"Failed to write vhost config for {app_name}")
                return False
            
            # Reload Caddy to apply changes
            if not await self._reload_caddy():
                logger.error(f"Failed to reload Caddy after creating vhost for {app_name}")
                return False
            
            # Store vhost info
            vhost = VirtualHost(
                app_name=app_name,
                hostname=hostname,
                backend_ip=backend_ip,
                backend_port=backend_port,
                protocol="http",
                enabled=True
            )
            self.vhosts[app_name] = vhost
            
            logger.info(f"✓ Created vhost: {hostname}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create vhost for {app_name}: {e}", exc_info=True)
            return False
    
    async def update_vhost(self, app_name: str, backend_ip: Optional[str] = None, 
                          backend_port: Optional[int] = None) -> bool:
        """
        Update an existing virtual host configuration.
        
        Args:
            app_name: Name of the application
            backend_ip: New backend IP (optional)
            backend_port: New backend port (optional)
            
        Returns:
            bool: True if vhost updated successfully
        """
        try:
            if app_name not in self.vhosts:
                logger.warning(f"Vhost for {app_name} not found, creating new one")
                return await self.create_vhost(app_name, backend_ip or "10.20.0.100", backend_port or 80)
            
            vhost = self.vhosts[app_name]
            
            # Update fields if provided
            if backend_ip:
                vhost.backend_ip = backend_ip
            if backend_port:
                vhost.backend_port = backend_port
            
            logger.info(f"Updating vhost: {vhost.hostname}")
            
            # Regenerate and write configuration
            sanitized_name = self._sanitize_app_name(app_name)
            caddy_config = self._generate_caddy_config(vhost.hostname, vhost.backend_ip, vhost.backend_port)
            config_file = f"{self.CADDY_SITES_DIR}/{sanitized_name}.caddy"
            
            if not await self._write_config_file(config_file, caddy_config):
                return False
            
            if not await self._reload_caddy():
                return False
            
            logger.info(f"✓ Updated vhost: {vhost.hostname}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update vhost for {app_name}: {e}")
            return False
    
    async def delete_vhost(self, app_name: str) -> bool:
        """
        Delete a virtual host configuration.
        
        Args:
            app_name: Name of the application
            
        Returns:
            bool: True if vhost deleted successfully
        """
        try:
            if app_name not in self.vhosts:
                logger.warning(f"Vhost for {app_name} not found")
                return True  # Already deleted
            
            vhost = self.vhosts[app_name]
            sanitized_name = self._sanitize_app_name(app_name)
            
            logger.info(f"Deleting vhost: {vhost.hostname}")
            
            # Remove configuration file
            config_file = f"{self.CADDY_SITES_DIR}/{sanitized_name}.caddy"
            delete_cmd = f"rm -f {config_file}"
            
            result = await self._exec_in_appliance(delete_cmd)
            if result.get('exitcode') != 0:
                logger.error(f"Failed to delete vhost config file: {config_file}")
                return False
            
            # Reload Caddy
            if not await self._reload_caddy():
                logger.warning("Failed to reload Caddy after deleting vhost")
            
            # Remove from tracking
            del self.vhosts[app_name]
            
            logger.info(f"✓ Deleted vhost: {vhost.hostname}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vhost for {app_name}: {e}")
            return False
    
    async def get_vhost_count(self) -> int:
        """
        Get the number of configured virtual hosts.
        
        Returns:
            int: Number of vhosts
        """
        return len(self.vhosts)
    
    async def list_vhosts(self) -> List[VirtualHost]:
        """
        Get list of all configured virtual hosts.
        
        Returns:
            List of VirtualHost objects
        """
        return list(self.vhosts.values())
    
    async def get_vhost(self, app_name: str) -> Optional[VirtualHost]:
        """
        Get virtual host configuration for an application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            VirtualHost object or None if not found
        """
        return self.vhosts.get(app_name)
    
    def get_vhost_urls(self, app_name: str, appliance_ip: str) -> Dict[str, str]:
        """
        Get both public and iframe URLs for an application.
        
        Args:
            app_name: Name of the application
            appliance_ip: WAN IP of the network appliance
            
        Returns:
            Dict with 'url' and 'iframe_url' keys
            
        Example:
            urls = proxy_manager.get_vhost_urls("nginx-01", "192.168.1.100")
            # Returns:
            # {
            #     'url': 'http://192.168.1.100/nginx-01',
            #     'iframe_url': 'http://192.168.1.100/proxy/internal/nginx-01'
            # }
        """
        sanitized_name = self._sanitize_app_name(app_name)
        return {
            'url': f"http://{appliance_ip}/{sanitized_name}",
            'iframe_url': f"http://{appliance_ip}/proxy/internal/{sanitized_name}"
        }
    
    async def verify_vhost_health(self, app_name: str) -> bool:
        """
        Verify that a virtual host is working correctly.
        
        Args:
            app_name: Name of the application
            
        Returns:
            bool: True if vhost is healthy
        """
        try:
            vhost = self.vhosts.get(app_name)
            if not vhost:
                return False
            
            # Try to curl the backend through the proxy
            test_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost/{app_name} || echo '000'"
            result = await self._exec_in_appliance(test_cmd)
            
            if result.get('exitcode') == 0:
                http_code = result.get('output', '').strip()
                # Accept any 2xx or 3xx as healthy
                if http_code.startswith('2') or http_code.startswith('3'):
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Health check failed for {app_name}: {e}")
            return False
    
    # Helper methods
    
    def _sanitize_app_name(self, app_name: str) -> str:
        """
        Sanitize app name for use in hostname and filenames.
        
        Args:
            app_name: Original app name
            
        Returns:
            Sanitized name (lowercase, alphanumeric and hyphens only)
        """
        import re
        # Convert to lowercase and replace non-alphanumeric with hyphens
        sanitized = re.sub(r'[^a-z0-9-]', '-', app_name.lower())
        # Remove consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        return sanitized
    
    def _generate_caddy_config(self, hostname: str, backend_ip: str, backend_port: int) -> str:
        """
        Generate Caddy configuration for a virtual host with dual-access strategy.

        v2.0 In-App Canvas Feature: Generates THREE access methods:
        1. Hostname-based: app-name.prox.local (for internal DNS)
        2. Path-based PUBLIC: /app-name (standard external access)
        3. Path-based IFRAME: /proxy/internal/app-name (for in-app embedding)

        CRITICAL SECURITY:
        - Public paths preserve security headers (X-Frame-Options, CSP)
        - Iframe path strips security headers to allow embedding
        - This dual strategy enables unified UX while maintaining security

        Args:
            hostname: Hostname for the vhost (e.g., "nginx-01.prox.local")
            backend_ip: Backend IP address
            backend_port: Backend port

        Returns:
            Caddy configuration string with public AND iframe proxy blocks
        """
        # Extract app name from hostname (e.g., "nginx-01" from "nginx-01.prox.local")
        app_name = hostname.replace(f".{self.DNS_DOMAIN}", "")

        config = f"""# Virtual host for {hostname}
# v2.0 In-App Canvas: Dual-access configuration
# Accessible via:
#   - http://{hostname} (with DNS)
#   - http://<appliance-ip>/{app_name} (public path-based access)
#   - http://<appliance-ip>/proxy/internal/{app_name} (iframe-embeddable)

# Method 1: Hostname-based routing (requires DNS or /etc/hosts)
{hostname} {{
    reverse_proxy http://{backend_ip}:{backend_port} {{
        # Health checks
        health_uri /
        health_interval 30s
        health_timeout 5s

        # Headers
        header_up Host {{upstream_hostport}}
        header_up X-Real-IP {{remote_host}}
        header_up X-Forwarded-For {{remote_host}}
        header_up X-Forwarded-Proto {{scheme}}
    }}

    # Logging
    log {{
        output file /var/log/caddy/{hostname}.log
        format json
    }}
}}

# Method 2: PUBLIC path-based routing (works without DNS)
# Access via: http://<appliance-wan-ip>/{app_name}
# Security headers PRESERVED - this is the standard public access
:80 {{
    handle_path /{app_name} {{
        reverse_proxy http://{backend_ip}:{backend_port} {{
            # Headers for path-based proxy
            header_up Host {{upstream_hostport}}
            header_up X-Real-IP {{remote_host}}
            header_up X-Forwarded-For {{remote_host}}
            header_up X-Forwarded-Proto {{scheme}}
            header_up X-Forwarded-Prefix /{app_name}
        }}
    }}

    # Method 3: IFRAME-EMBEDDABLE internal proxy (In-App Canvas)
    # Access via: http://<appliance-wan-ip>/proxy/internal/{app_name}
    # CRITICAL: Security headers STRIPPED to allow iframe embedding
    # This path is ONLY for the Proximity UI canvas feature
    handle_path /proxy/internal/{app_name} {{
        reverse_proxy http://{backend_ip}:{backend_port} {{
            # Standard proxy headers
            header_up Host {{upstream_hostport}}
            header_up X-Real-IP {{remote_host}}
            header_up X-Forwarded-For {{remote_host}}
            header_up X-Forwarded-Proto {{scheme}}
            header_up X-Forwarded-Prefix /proxy/internal/{app_name}

            # CRITICAL: Strip frame-busting headers to allow iframe embedding
            # These directives make apps embeddable in the Proximity canvas
            header_down -X-Frame-Options
            header_down -Content-Security-Policy
            header_down -X-Content-Security-Policy
            header_down -X-WebKit-CSP
        }}
    }}
}}
"""
        return config
    
    async def _write_config_file(self, filepath: str, content: str) -> bool:
        """
        Write configuration file to the appliance.
        
        Args:
            filepath: Full path to the config file
            content: Configuration content
            
        Returns:
            bool: True if written successfully
        """
        try:
            # Escape single quotes in content
            content_escaped = content.replace("'", "'\\''")
            
            write_cmd = f"cat > {filepath} << 'EOF'\n{content}\nEOF"
            result = await self._exec_in_appliance(write_cmd)
            
            if result.get('exitcode') != 0:
                logger.error(f"Failed to write config file: {filepath}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write config file {filepath}: {e}")
            return False
    
    async def _reload_caddy(self) -> bool:
        """
        Reload Caddy configuration without downtime.
        
        Returns:
            bool: True if reload successful
        """
        try:
            # Try graceful reload first
            reload_cmd = f"caddy reload --config {self.CADDY_CONFIG}"
            result = await self._exec_in_appliance(reload_cmd)
            
            if result.get('exitcode') == 0:
                logger.debug("Caddy reloaded successfully")
                return True
            
            # Fallback: restart Caddy service
            logger.warning("Graceful reload failed, restarting Caddy service")
            restart_cmd = "rc-service caddy restart"
            result = await self._exec_in_appliance(restart_cmd)
            
            if result.get('exitcode') == 0:
                logger.debug("Caddy restarted successfully")
                return True
            
            logger.error("Failed to reload Caddy")
            return False
            
        except Exception as e:
            logger.error(f"Failed to reload Caddy: {e}")
            return False
    
    async def _exec_in_appliance(self, command: str) -> Dict[str, Any]:
        """
        Execute a command inside the appliance LXC.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Dict with 'exitcode' and 'output'
        """
        try:
            # Use ProxmoxService SSH execution if available
            if self.proxmox_service is None:
                # Lazy import to avoid circular dependency
                from services.proxmox_service import proxmox_service
                self.proxmox_service = proxmox_service
            
            # Execute via SSH on Proxmox host
            full_cmd = f"pct exec {self.appliance_vmid} -- sh -c '{command}'"
            result = await self.proxmox_service.execute_command_via_ssh(full_cmd)
            
            return {
                'exitcode': 0 if result.get('success') else 1,
                'output': result.get('output', ''),
                'error': result.get('error', '')
            }
            
        except Exception as e:
            logger.error(f"Failed to execute in appliance: {command} - {e}")
            return {'exitcode': 1, 'output': '', 'error': str(e)}
