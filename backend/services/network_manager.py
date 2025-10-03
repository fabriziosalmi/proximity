"""
Proximity Network Manager Service

Manages the isolated network infrastructure for application containers:
- Dedicated Linux bridge (prox-net) with NAT
- Integrated DHCP/DNS service via dnsmasq
- Automated network configuration on Proxmox host

This service provides a fully isolated, managed network environment with:
- Private subnet: 10.10.0.0/24
- DHCP range: 10.10.0.100-250
- DNS domain: prox.local
- NAT to external network via host's default interface
"""

import asyncio
import logging
import re
import shutil
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class NetworkManager:
    """
    Manages network infrastructure for Proximity application containers.
    
    Provides idempotent configuration of:
    - Linux bridge (prox-net)
    - NAT routing
    - DHCP/DNS services
    """
    
    # Network configuration constants
    BRIDGE_NAME = "prox-net"
    BRIDGE_IP = "10.10.0.1"
    SUBNET = "10.10.0.0/24"
    DHCP_RANGE_START = "10.10.0.100"
    DHCP_RANGE_END = "10.10.0.250"
    DNS_DOMAIN = "prox.local"
    
    # File paths
    NETWORK_INTERFACES = "/etc/network/interfaces"
    NETWORK_INTERFACES_BACKUP = "/etc/network/interfaces.proximity.backup"
    DNSMASQ_CONFIG_DIR = "/etc/proximity"
    DNSMASQ_CONFIG_FILE = "/etc/proximity/dnsmasq.conf"
    DNSMASQ_SERVICE_FILE = "/etc/systemd/system/proximity-dns.service"
    
    def __init__(self):
        """Initialize the Network Manager."""
        self.outgoing_interface: Optional[str] = None
    
    async def initialize(self) -> bool:
        """
        Initialize the complete network infrastructure.
        
        This is the main entry point that orchestrates all network setup.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        logger.info("🌐 Initializing Proximity Network Infrastructure...")
        
        try:
            # Step 1: Configure host bridge and NAT
            logger.info("Step 1/3: Configuring host bridge and NAT...")
            await self.configure_host_bridge()
            
            # Step 2: Verify network state
            logger.info("Step 2/3: Verifying network configuration...")
            if not await self.verify_host_network_state():
                logger.error("Network state verification failed")
                return False
            
            # Step 3: Setup DHCP/DNS service
            logger.info("Step 3/3: Setting up DHCP/DNS service...")
            await self.setup_dhcp_service()
            
            logger.info("✅ Network infrastructure initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize network infrastructure: {e}", exc_info=True)
            return False
    
    async def _get_default_interface(self) -> str:
        """
        Detect the Proxmox host's default outgoing network interface.
        
        Uses 'ip route get 1.1.1.1' to determine the interface used for
        external connectivity.
        
        Returns:
            str: Interface name (e.g., 'vmbr0', 'eth0')
            
        Raises:
            RuntimeError: If interface cannot be determined
        """
        try:
            proc = await asyncio.create_subprocess_shell(
                "ip route get 1.1.1.1 | awk '{print $5}' | head -n1",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to detect interface: {stderr.decode()}")
            
            interface = stdout.decode().strip()
            
            if not interface:
                raise RuntimeError("No default interface detected")
            
            logger.info(f"Detected default outgoing interface: {interface}")
            return interface
            
        except Exception as e:
            logger.error(f"Error detecting default interface: {e}")
            raise RuntimeError(f"Cannot determine default network interface: {e}")
    
    async def _read_network_interfaces(self) -> str:
        """
        Read the current /etc/network/interfaces file.
        
        Returns:
            str: Contents of the interfaces file
            
        Raises:
            RuntimeError: If file cannot be read
        """
        try:
            interfaces_path = Path(self.NETWORK_INTERFACES)
            
            if not interfaces_path.exists():
                logger.warning(f"{self.NETWORK_INTERFACES} does not exist, will create it")
                return ""
            
            content = interfaces_path.read_text()
            logger.debug(f"Read {len(content)} bytes from {self.NETWORK_INTERFACES}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to read {self.NETWORK_INTERFACES}: {e}")
            raise RuntimeError(f"Cannot read network interfaces file: {e}")
    
    async def _backup_network_interfaces(self) -> None:
        """
        Create a backup of /etc/network/interfaces.
        
        Raises:
            RuntimeError: If backup fails
        """
        try:
            source = Path(self.NETWORK_INTERFACES)
            backup = Path(self.NETWORK_INTERFACES_BACKUP)
            
            if source.exists():
                shutil.copy2(source, backup)
                logger.info(f"Created backup: {self.NETWORK_INTERFACES_BACKUP}")
            else:
                logger.warning(f"Source file {source} does not exist, skipping backup")
                
        except Exception as e:
            logger.error(f"Failed to backup network interfaces: {e}")
            raise RuntimeError(f"Cannot create backup: {e}")
    
    async def _restore_network_interfaces(self) -> None:
        """
        Restore /etc/network/interfaces from backup.
        
        Used for rollback on configuration failure.
        """
        try:
            backup = Path(self.NETWORK_INTERFACES_BACKUP)
            target = Path(self.NETWORK_INTERFACES)
            
            if backup.exists():
                shutil.copy2(backup, target)
                logger.info(f"Restored network interfaces from backup")
            else:
                logger.warning("No backup file found to restore")
                
        except Exception as e:
            logger.error(f"Failed to restore network interfaces: {e}")
    
    def _is_bridge_configured(self, content: str) -> bool:
        """
        Check if prox-net bridge is already configured.
        
        Args:
            content: Content of /etc/network/interfaces
            
        Returns:
            bool: True if bridge configuration exists
        """
        # Look for the bridge configuration block
        pattern = rf"^\s*auto\s+{self.BRIDGE_NAME}\s*$"
        
        if re.search(pattern, content, re.MULTILINE):
            logger.info(f"Bridge {self.BRIDGE_NAME} configuration found")
            return True
        
        logger.info(f"Bridge {self.BRIDGE_NAME} configuration not found")
        return False
    
    async def configure_host_bridge(self) -> None:
        """
        Configure the prox-net bridge with NAT on the Proxmox host.
        
        This method is idempotent - it will only make changes if the
        configuration doesn't already exist.
        
        Process:
        1. Detect default outgoing interface
        2. Read current network configuration
        3. Check if bridge already configured
        4. If not, backup and append bridge configuration
        5. Apply configuration with ifreload
        
        Raises:
            RuntimeError: If configuration fails
        """
        try:
            # Get outgoing interface
            self.outgoing_interface = await self._get_default_interface()
            
            # Read current configuration
            current_config = await self._read_network_interfaces()
            
            # Check if already configured
            if self._is_bridge_configured(current_config):
                logger.info(f"✓ Bridge {self.BRIDGE_NAME} already configured, skipping")
                return
            
            logger.info(f"Bridge {self.BRIDGE_NAME} not configured, adding configuration...")
            
            # Create backup before modification
            await self._backup_network_interfaces()
            
            # Generate bridge configuration
            bridge_config = self._generate_bridge_config()
            
            # Append configuration
            try:
                interfaces_path = Path(self.NETWORK_INTERFACES)
                
                # Ensure file exists
                interfaces_path.touch(exist_ok=True)
                
                # Append configuration (ensure newline before and after)
                with interfaces_path.open('a') as f:
                    f.write(f"\n{bridge_config}\n")
                
                logger.info(f"Appended bridge configuration to {self.NETWORK_INTERFACES}")
                
            except Exception as e:
                logger.error(f"Failed to write configuration: {e}")
                await self._restore_network_interfaces()
                raise RuntimeError(f"Configuration write failed: {e}")
            
            # Apply configuration
            await self._apply_network_config()
            
            logger.info(f"✅ Bridge {self.BRIDGE_NAME} configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to configure host bridge: {e}")
            raise
    
    def _generate_bridge_config(self) -> str:
        """
        Generate the bridge configuration block.
        
        Returns:
            str: Complete bridge configuration
        """
        config = f"""# --- Proximity Managed Network ---
auto {self.BRIDGE_NAME}
iface {self.BRIDGE_NAME} inet static
        address {self.BRIDGE_IP}/24
        bridge-ports none
        bridge-stp off
        bridge-fd 0
        post-up echo 1 > /proc/sys/net/ipv4/ip_forward
        post-up iptables -t nat -A POSTROUTING -s '{self.SUBNET}' -o {self.outgoing_interface} -j MASQUERADE
        post-down iptables -t nat -D POSTROUTING -s '{self.SUBNET}' -o {self.outgoing_interface} -j MASQUERADE"""
        
        return config
    
    async def _apply_network_config(self) -> None:
        """
        Apply network configuration using ifreload.
        
        Raises:
            RuntimeError: If ifreload fails
        """
        try:
            logger.info("Applying network configuration with ifreload...")
            
            proc = await asyncio.create_subprocess_shell(
                "ifreload -a",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"ifreload failed: {error_msg}")
                await self._restore_network_interfaces()
                raise RuntimeError(f"ifreload failed: {error_msg}")
            
            logger.info("Network configuration applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply network configuration: {e}")
            raise
    
    async def verify_host_network_state(self) -> bool:
        """
        Verify that the network infrastructure is correctly configured.
        
        Checks:
        1. Bridge interface is up and has correct IP
        2. NAT iptables rule is present
        3. IP forwarding is enabled
        
        Returns:
            bool: True if all checks pass, False otherwise
        """
        logger.info("Verifying network state...")
        
        try:
            # Check 1: Bridge interface exists and is up
            bridge_ok = await self._verify_bridge_state()
            if not bridge_ok:
                logger.error(f"✗ Bridge {self.BRIDGE_NAME} verification failed")
                return False
            
            logger.info(f"✓ Bridge {self.BRIDGE_NAME} is up")
            
            # Check 2: NAT rule exists
            nat_ok = await self._verify_nat_rule()
            if not nat_ok:
                logger.error("✗ NAT rule verification failed")
                return False
            
            logger.info("✓ NAT rule is present")
            
            # Check 3: IP forwarding enabled
            forwarding_ok = await self._verify_ip_forwarding()
            if not forwarding_ok:
                logger.error("✗ IP forwarding verification failed")
                return False
            
            logger.info("✓ IP forwarding is enabled")
            
            logger.info("✅ All network state checks passed")
            return True
            
        except Exception as e:
            logger.error(f"Network state verification error: {e}")
            return False
    
    async def _verify_bridge_state(self) -> bool:
        """
        Verify bridge interface is up with correct configuration.
        
        Returns:
            bool: True if bridge is correctly configured
        """
        try:
            proc = await asyncio.create_subprocess_shell(
                f"ip addr show {self.BRIDGE_NAME}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"Bridge {self.BRIDGE_NAME} not found")
                return False
            
            output = stdout.decode()
            
            # Check if interface is UP
            if "state UP" not in output and "state UNKNOWN" not in output:
                logger.error(f"Bridge {self.BRIDGE_NAME} is not UP")
                return False
            
            # Check if IP is assigned
            if self.BRIDGE_IP not in output:
                logger.error(f"Bridge {self.BRIDGE_NAME} does not have IP {self.BRIDGE_IP}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying bridge state: {e}")
            return False
    
    async def _verify_nat_rule(self) -> bool:
        """
        Verify NAT iptables rule exists.
        
        Returns:
            bool: True if NAT rule is present
        """
        try:
            proc = await asyncio.create_subprocess_shell(
                "iptables-save | grep -E 'MASQUERADE.*10\\.10\\.0\\.0/24'",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            # grep returns 0 if pattern found, 1 if not found
            if proc.returncode == 0:
                logger.debug(f"NAT rule found: {stdout.decode().strip()}")
                return True
            else:
                logger.error("NAT rule not found in iptables")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying NAT rule: {e}")
            return False
    
    async def _verify_ip_forwarding(self) -> bool:
        """
        Verify IP forwarding is enabled.
        
        Returns:
            bool: True if IP forwarding is enabled
        """
        try:
            forwarding_path = Path("/proc/sys/net/ipv4/ip_forward")
            value = forwarding_path.read_text().strip()
            
            if value == "1":
                return True
            else:
                logger.error(f"IP forwarding disabled (value: {value})")
                return False
                
        except Exception as e:
            logger.error(f"Error checking IP forwarding: {e}")
            return False
    
    async def setup_dhcp_service(self) -> None:
        """
        Setup and start the dnsmasq DHCP/DNS service.
        
        This method is idempotent - it will only make changes if the
        service isn't already correctly configured.
        
        Process:
        1. Create configuration directory
        2. Generate dnsmasq configuration
        3. Create systemd service file
        4. Enable and start service
        
        Raises:
            RuntimeError: If service setup fails
        """
        try:
            logger.info("Setting up DHCP/DNS service...")
            
            # Create configuration directory
            config_dir = Path(self.DNSMASQ_CONFIG_DIR)
            config_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Configuration directory: {config_dir}")
            
            # Generate and write dnsmasq configuration
            config_changed = await self._write_dnsmasq_config()
            
            # Generate and write systemd service file
            service_changed = await self._write_systemd_service()
            
            # Reload systemd if service file changed
            if service_changed:
                await self._reload_systemd()
            
            # Start/restart service if configuration changed
            if config_changed or service_changed:
                await self._restart_dnsmasq_service()
            else:
                # Just ensure it's running
                await self._ensure_dnsmasq_running()
            
            logger.info("✅ DHCP/DNS service setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup DHCP/DNS service: {e}")
            raise RuntimeError(f"DHCP/DNS service setup failed: {e}")
    
    def _generate_dnsmasq_config(self) -> str:
        """
        Generate dnsmasq configuration content.
        
        Returns:
            str: Complete dnsmasq configuration
        """
        config = f"""# Proximity Managed DNS/DHCP
# Auto-generated configuration for container network

# Bind to prox-net bridge only
interface={self.BRIDGE_NAME}
bind-interfaces

# DHCP configuration
dhcp-range={self.DHCP_RANGE_START},{self.DHCP_RANGE_END},255.255.255.0,12h
dhcp-option=option:router,{self.BRIDGE_IP}
dhcp-option=option:dns-server,{self.BRIDGE_IP}

# Authoritative DHCP server
dhcp-authoritative

# DNS configuration
domain-needed
bogus-priv
expand-hosts
domain={self.DNS_DOMAIN}

# Logging
log-queries
log-dhcp

# No DNS resolution from /etc/resolv.conf
no-resolv
# Use upstream DNS servers
server=1.1.1.1
server=8.8.8.8

# Enable DHCP lease file
dhcp-leasefile=/var/lib/proximity/dnsmasq.leases
"""
        return config
    
    async def _write_dnsmasq_config(self) -> bool:
        """
        Write dnsmasq configuration file.
        
        Returns:
            bool: True if configuration was changed
        """
        try:
            config_path = Path(self.DNSMASQ_CONFIG_FILE)
            new_config = self._generate_dnsmasq_config()
            
            # Check if config already exists and is identical
            if config_path.exists():
                current_config = config_path.read_text()
                if current_config == new_config:
                    logger.info("dnsmasq configuration unchanged")
                    return False
            
            # Write new configuration
            config_path.write_text(new_config)
            logger.info(f"Written dnsmasq configuration to {config_path}")
            
            # Create lease file directory
            lease_dir = Path("/var/lib/proximity")
            lease_dir.mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write dnsmasq configuration: {e}")
            raise
    
    def _generate_systemd_service(self) -> str:
        """
        Generate systemd service file content.
        
        Returns:
            str: Complete systemd service unit
        """
        service = f"""[Unit]
Description=Proximity DNS/DHCP Service
Documentation=https://github.com/yourusername/proximity
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/dnsmasq -k -C {self.DNSMASQ_CONFIG_FILE}
Restart=on-failure
RestartSec=5

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/lib/proximity

[Install]
WantedBy=multi-user.target
"""
        return service
    
    async def _write_systemd_service(self) -> bool:
        """
        Write systemd service file.
        
        Returns:
            bool: True if service file was changed
        """
        try:
            service_path = Path(self.DNSMASQ_SERVICE_FILE)
            new_service = self._generate_systemd_service()
            
            # Check if service already exists and is identical
            if service_path.exists():
                current_service = service_path.read_text()
                if current_service == new_service:
                    logger.info("systemd service file unchanged")
                    return False
            
            # Write new service file
            service_path.write_text(new_service)
            logger.info(f"Written systemd service to {service_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write systemd service: {e}")
            raise
    
    async def _reload_systemd(self) -> None:
        """
        Reload systemd daemon to recognize new/changed service files.
        
        Raises:
            RuntimeError: If reload fails
        """
        try:
            logger.info("Reloading systemd daemon...")
            
            proc = await asyncio.create_subprocess_shell(
                "systemctl daemon-reload",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"systemctl daemon-reload failed: {stderr.decode()}")
            
            logger.info("systemd daemon reloaded")
            
        except Exception as e:
            logger.error(f"Failed to reload systemd: {e}")
            raise
    
    async def _restart_dnsmasq_service(self) -> None:
        """
        Restart the dnsmasq service.
        
        Raises:
            RuntimeError: If restart fails
        """
        try:
            logger.info("Restarting proximity-dns service...")
            
            # Enable service first
            proc = await asyncio.create_subprocess_shell(
                "systemctl enable proximity-dns.service",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            # Restart service
            proc = await asyncio.create_subprocess_shell(
                "systemctl restart proximity-dns.service",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"Service restart failed: {stderr.decode()}")
            
            logger.info("✓ proximity-dns service restarted successfully")
            
            # Wait a moment for service to start
            await asyncio.sleep(2)
            
            # Verify service is running
            is_running = await self._check_service_status()
            if not is_running:
                raise RuntimeError("Service started but is not running")
            
        except Exception as e:
            logger.error(f"Failed to restart dnsmasq service: {e}")
            raise
    
    async def _ensure_dnsmasq_running(self) -> None:
        """
        Ensure dnsmasq service is running, start if not.
        """
        try:
            is_running = await self._check_service_status()
            
            if is_running:
                logger.info("✓ proximity-dns service is already running")
                return
            
            logger.info("Starting proximity-dns service...")
            
            proc = await asyncio.create_subprocess_shell(
                "systemctl start proximity-dns.service",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"Service start failed: {stderr.decode()}")
            
            logger.info("✓ proximity-dns service started")
            
        except Exception as e:
            logger.error(f"Failed to ensure dnsmasq running: {e}")
            raise
    
    async def _check_service_status(self) -> bool:
        """
        Check if proximity-dns service is active.
        
        Returns:
            bool: True if service is active (running)
        """
        try:
            proc = await asyncio.create_subprocess_shell(
                "systemctl is-active proximity-dns.service",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            status = stdout.decode().strip()
            return status == "active"
            
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return False
    
    async def get_container_network_config(self, hostname: str) -> str:
        """
        Get the network configuration string for a new LXC container.
        
        Args:
            hostname: The container hostname (used for DNS resolution)
            
        Returns:
            str: Network configuration in Proxmox format
        """
        # DHCP configuration on prox-net bridge
        net_config = f"name=eth0,bridge={self.BRIDGE_NAME},ip=dhcp,firewall=1"
        
        logger.info(f"Generated network config for {hostname}: {net_config}")
        return net_config
    
    async def get_network_info(self) -> dict:
        """
        Get current network infrastructure status.
        
        Returns:
            dict: Network status information
        """
        try:
            bridge_up = await self._verify_bridge_state()
            nat_ok = await self._verify_nat_rule()
            service_running = await self._check_service_status()
            
            return {
                "bridge_name": self.BRIDGE_NAME,
                "bridge_ip": self.BRIDGE_IP,
                "subnet": self.SUBNET,
                "dhcp_range": f"{self.DHCP_RANGE_START}-{self.DHCP_RANGE_END}",
                "dns_domain": self.DNS_DOMAIN,
                "bridge_up": bridge_up,
                "nat_configured": nat_ok,
                "dhcp_service_running": service_running,
                "outgoing_interface": self.outgoing_interface or await self._get_default_interface()
            }
            
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {
                "error": str(e)
            }
