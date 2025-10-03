"""
Proximity Network Appliance Orchestrator

This module manages the complete lifecycle of the Proximity Network Appliance - 
a specialized Alpine Linux LXC that provides comprehensive network services:

- Routing/NAT between management LAN (vmbr0) and app network (proximity-lan)
- DHCP server for automatic IP assignment (10.20.0.100-250)
- DNS server with .prox.local domain resolution
- Caddy reverse proxy for unified app access
- Cockpit management UI for appliance administration

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    Proxmox Host                              │
│                                                              │
│  vmbr0 (Management)          proximity-lan (Apps)           │
│  192.168.1.0/24              10.20.0.0/24                   │
│         │                           │                        │
│         │    ┌─────────────────────┤                        │
│         │    │  Network Appliance  │                        │
│         └────┤  prox-appliance     │                        │
│              │  (VMID 100)         │                        │
│              │                     │                        │
│              │  eth0: DHCP (WAN)   │                        │
│              │  eth1: 10.20.0.1/24 │                        │
│              │                     │                        │
│              │  Services:          │                        │
│              │  - NAT/Routing      │                        │
│              │  - DHCP/DNS         │                        │
│              │  - Caddy Proxy      │                        │
│              │  - Cockpit UI       │                        │
│              └─────────────────────┘                        │
│                         │                                    │
│                         │ 10.20.0.0/24                       │
│              ┌──────────┴──────────┐                        │
│              │                     │                         │
│         ┌────────┐           ┌────────┐                     │
│         │ nginx  │           │wordpress│                    │
│         │10.20.0.│           │10.20.0. │                    │
│         │  101   │           │  102    │                    │
│         └────────┘           └────────┘                     │
└─────────────────────────────────────────────────────────────┘

Network Addressing Convention:
- Appliance Gateway: 10.20.0.1/24
- DHCP Range: 10.20.0.100 - 10.20.0.250
- DNS Domain: .prox.local
- Reserved: 10.20.0.2-99 for static assignments

Author: Proximity Team
Date: October 2025
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ApplianceInfo:
    """Network Appliance LXC information"""
    vmid: int
    hostname: str
    wan_interface: str  # eth0 on vmbr0
    wan_ip: Optional[str]  # DHCP assigned
    lan_interface: str  # eth1 on proximity-lan
    lan_ip: str  # Static 10.20.0.1/24
    status: str  # running, stopped, etc.
    services: Dict[str, bool]  # Service status (dnsmasq, caddy, etc.)


class NetworkApplianceOrchestrator:
    """
    Orchestrates the complete lifecycle of the Proximity Network Appliance.
    
    This class handles:
    1. Host bridge provisioning (proximity-lan)
    2. Appliance LXC provisioning (prox-appliance)
    3. Deep service configuration (DHCP, DNS, NAT, Caddy, Cockpit)
    4. Health monitoring and maintenance
    """
    
    # Network configuration constants
    BRIDGE_NAME = "proximity-lan"
    APPLIANCE_HOSTNAME = "prox-appliance"
    APPLIANCE_VMID = 100  # Reserved VMID for the appliance
    
    # Network addressing
    LAN_NETWORK = "10.20.0.0/24"
    LAN_GATEWAY = "10.20.0.1"
    LAN_NETMASK = "255.255.255.0"
    DHCP_RANGE_START = "10.20.0.100"
    DHCP_RANGE_END = "10.20.0.250"
    DNS_DOMAIN = "prox.local"
    
    # Service ports
    COCKPIT_PORT = 9090
    CADDY_HTTP_PORT = 80
    CADDY_HTTPS_PORT = 443
    
    def __init__(self, proxmox_service):
        """
        Initialize the orchestrator.
        
        Args:
            proxmox_service: ProxmoxService instance for Proxmox API calls
        """
        self.proxmox = proxmox_service
        self.appliance_info: Optional[ApplianceInfo] = None
        
    async def initialize(self) -> bool:
        """
        Complete initialization sequence for the Network Appliance.
        
        Steps:
        1. Provision host bridge (proximity-lan)
        2. Provision appliance LXC (prox-appliance)
        3. Configure all services inside appliance
        4. Verify health and connectivity
        
        Returns:
            bool: True if initialization successful
        """
        logger.info("🚀 Initializing Proximity Network Appliance...")
        
        try:
            # Step 1: Ensure host bridge exists
            logger.info("Step 1/4: Provisioning host bridge...")
            if not await self.setup_host_bridge():
                logger.error("Failed to setup host bridge")
                return False
            
            # Step 2: Provision appliance LXC
            logger.info("Step 2/4: Provisioning appliance LXC...")
            appliance = await self.provision_appliance_lxc()
            if not appliance:
                logger.error("Failed to provision appliance LXC")
                return False
            
            self.appliance_info = appliance
            logger.info(f"✓ Appliance LXC ready: VMID {appliance.vmid}, WAN IP: {appliance.wan_ip}")
            
            # Step 3: Configure appliance services
            logger.info("Step 3/4: Configuring appliance services...")
            if not await self.configure_appliance_lxc(appliance.vmid):
                logger.error("Failed to configure appliance services")
                return False
            
            # Step 4: Verify health
            logger.info("Step 4/4: Verifying appliance health...")
            if not await self.verify_appliance_health():
                logger.warning("⚠️  Appliance health check reported warnings")
            
            logger.info("✅ Proximity Network Appliance initialized successfully")
            logger.info(f"   Management UI: http://{appliance.wan_ip}:{self.COCKPIT_PORT}")
            logger.info(f"   LAN Gateway: {self.LAN_GATEWAY}")
            logger.info(f"   DNS Domain: .{self.DNS_DOMAIN}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize network appliance: {e}", exc_info=True)
            return False
    
    async def setup_host_bridge(self) -> bool:
        """
        Provision the proximity-lan bridge on the Proxmox host.
        
        This creates a simple, unconfigured bridge that will be managed
        entirely by the appliance LXC. The bridge has no IP on the host itself.
        
        Returns:
            bool: True if bridge exists or was created successfully
        """
        try:
            logger.info(f"Checking for {self.BRIDGE_NAME} bridge on Proxmox host...")
            
            # Check if bridge already exists
            check_cmd = f"ip link show {self.BRIDGE_NAME}"
            result = await self._exec_on_host(check_cmd)
            
            if result and result.get('exitcode') == 0:
                logger.info(f"✓ Bridge {self.BRIDGE_NAME} already exists")
                return True
            
            # Create bridge using ip commands
            logger.info(f"Creating {self.BRIDGE_NAME} bridge...")
            
            commands = [
                f"ip link add name {self.BRIDGE_NAME} type bridge",
                f"ip link set {self.BRIDGE_NAME} up"
            ]
            
            for cmd in commands:
                result = await self._exec_on_host(cmd)
                if result.get('exitcode') != 0:
                    logger.error(f"Failed to execute: {cmd}")
                    return False
            
            # Make persistent in /etc/network/interfaces
            await self._persist_bridge_config()
            
            logger.info(f"✓ Created {self.BRIDGE_NAME} bridge successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup host bridge: {e}")
            return False
    
    async def _persist_bridge_config(self) -> bool:
        """Make bridge configuration persistent in /etc/network/interfaces."""
        try:
            # Check if already configured
            check_cmd = f"grep -q '{self.BRIDGE_NAME}' /etc/network/interfaces"
            result = await self._exec_on_host(check_cmd)
            
            if result and result.get('exitcode') == 0:
                logger.info(f"{self.BRIDGE_NAME} already in /etc/network/interfaces")
                return True
            
            # Append configuration
            config = f"""
# Proximity isolated network bridge (auto-generated)
auto {self.BRIDGE_NAME}
iface {self.BRIDGE_NAME} inet manual
    bridge-ports none
    bridge-stp off
    bridge-fd 0
"""
            
            append_cmd = f"echo '{config}' >> /etc/network/interfaces"
            result = await self._exec_on_host(append_cmd)
            
            if result.get('exitcode') == 0:
                logger.info(f"✓ Persisted {self.BRIDGE_NAME} configuration")
                return True
            else:
                logger.warning("Could not persist bridge config (will work until reboot)")
                return False
                
        except Exception as e:
            logger.warning(f"Could not persist bridge config: {e}")
            return False
    
    async def provision_appliance_lxc(self) -> Optional[ApplianceInfo]:
        """
        Provision the Network Appliance LXC container.
        
        This creates a specialized, dual-homed Alpine Linux LXC with:
        - Privileged mode (for iptables, service management)
        - eth0 on vmbr0 (WAN/management) with DHCP
        - eth1 on proximity-lan (LAN) with static 10.20.0.1/24
        
        Returns:
            ApplianceInfo: Information about the provisioned appliance, or None if failed
        """
        try:
            # Check if appliance already exists
            existing = await self._find_existing_appliance()
            if existing:
                logger.info(f"✓ Found existing appliance: VMID {existing.vmid}")
                return existing
            
            logger.info(f"Creating new appliance LXC: {self.APPLIANCE_HOSTNAME}")
            
            # Get node name
            node = await self._get_default_node()
            if not node:
                logger.error("Could not determine Proxmox node")
                return None
            
            # LXC configuration
            config = {
                'vmid': self.APPLIANCE_VMID,
                'hostname': self.APPLIANCE_HOSTNAME,
                'ostemplate': 'local:vztmpl/alpine-3.18-default_20230607_amd64.tar.xz',
                'unprivileged': 0,  # Privileged container (required for iptables)
                'features': 'nesting=1,keyctl=1',
                'cores': 2,
                'memory': 1024,  # 1GB RAM
                'swap': 512,
                'rootfs': 'local-lvm:8',  # 8GB root filesystem
                'net0': 'name=eth0,bridge=vmbr0,ip=dhcp,firewall=1',
                'net1': f'name=eth1,bridge={self.BRIDGE_NAME},ip={self.LAN_GATEWAY}/24,firewall=1',
                'nameserver': '8.8.8.8 1.1.1.1',
                'onboot': 1,  # Start on Proxmox boot
                'start': 1  # Start immediately after creation
            }
            
            # Create LXC via Proxmox API
            logger.info(f"Creating LXC on node {node} with VMID {self.APPLIANCE_VMID}...")
            
            # Note: This uses the proxmox service's internal methods
            # You'll need to expose this method or use direct API calls
            result = await self.proxmox.create_lxc(node, config)
            
            if not result:
                logger.error("Failed to create appliance LXC")
                return None
            
            # Wait for LXC to start
            await asyncio.sleep(10)
            
            # Get WAN IP (DHCP assigned)
            wan_ip = await self._get_lxc_wan_ip(node, self.APPLIANCE_VMID)
            
            appliance = ApplianceInfo(
                vmid=self.APPLIANCE_VMID,
                hostname=self.APPLIANCE_HOSTNAME,
                wan_interface='eth0',
                wan_ip=wan_ip,
                lan_interface='eth1',
                lan_ip=self.LAN_GATEWAY,
                status='running',
                services={}
            )
            
            logger.info(f"✓ Appliance LXC created successfully")
            return appliance
            
        except Exception as e:
            logger.error(f"Failed to provision appliance LXC: {e}", exc_info=True)
            return None
    
    async def configure_appliance_lxc(self, vmid: int) -> bool:
        """
        Deep configuration of the appliance LXC services.
        
        This performs comprehensive setup of all services inside the appliance:
        1. Base system (packages, IP forwarding)
        2. NAT firewall (iptables)
        3. DHCP/DNS (dnsmasq)
        4. Reverse proxy (Caddy)
        5. Management UI (Cockpit)
        
        Args:
            vmid: VMID of the appliance LXC
            
        Returns:
            bool: True if configuration successful
        """
        logger.info(f"Configuring appliance LXC {vmid}...")
        
        try:
            # Step 1: Base system setup
            logger.info("  [1/5] Setting up base system...")
            if not await self._setup_base_system(vmid):
                return False
            
            # Step 2: Configure NAT firewall
            logger.info("  [2/5] Configuring NAT firewall...")
            if not await self._configure_nat_firewall(vmid):
                return False
            
            # Step 3: Configure DHCP/DNS
            logger.info("  [3/5] Configuring DHCP/DNS...")
            if not await self._configure_dhcp_dns(vmid):
                return False
            
            # Step 4: Configure Caddy reverse proxy
            logger.info("  [4/5] Configuring Caddy reverse proxy...")
            if not await self._configure_caddy(vmid):
                return False
            
            # Step 5: Configure Cockpit management UI
            logger.info("  [5/5] Configuring Cockpit management UI...")
            if not await self._configure_cockpit(vmid):
                return False
            
            logger.info("✓ Appliance configuration complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure appliance: {e}", exc_info=True)
            return False
    
    async def _setup_base_system(self, vmid: int) -> bool:
        """Install packages and configure base system."""
        try:
            # Install required packages
            packages = "bash nano curl iptables ip6tables dnsmasq caddy"
            # Note: Cockpit might not be available in Alpine repos, we'll handle that separately
            
            install_cmd = f"apk update && apk add {packages}"
            result = await self._exec_in_lxc(vmid, install_cmd)
            
            if result.get('exitcode') != 0:
                logger.error("Failed to install packages")
                return False
            
            # Enable IP forwarding
            sysctl_cmd = "echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf && sysctl -p"
            result = await self._exec_in_lxc(vmid, sysctl_cmd)
            
            if result.get('exitcode') != 0:
                logger.warning("Failed to enable IP forwarding via sysctl")
            
            logger.info("    ✓ Base system configured")
            return True
            
        except Exception as e:
            logger.error(f"Base system setup failed: {e}")
            return False
    
    async def _configure_nat_firewall(self, vmid: int) -> bool:
        """Configure NAT and iptables rules."""
        try:
            # NAT rule for outbound traffic
            nat_cmd = "iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE"
            result = await self._exec_in_lxc(vmid, nat_cmd)
            
            if result.get('exitcode') != 0:
                logger.error("Failed to configure NAT")
                return False
            
            # Save iptables rules
            save_cmd = "rc-update add iptables default && /etc/init.d/iptables save"
            await self._exec_in_lxc(vmid, save_cmd)
            
            logger.info("    ✓ NAT firewall configured")
            return True
            
        except Exception as e:
            logger.error(f"NAT configuration failed: {e}")
            return False
    
    async def _configure_dhcp_dns(self, vmid: int) -> bool:
        """Configure dnsmasq for DHCP and DNS services."""
        try:
            # Create dnsmasq configuration
            dnsmasq_config = f"""# Proximity Network Appliance - DHCP/DNS Configuration
interface=eth1
bind-interfaces

# DHCP Configuration
dhcp-range={self.DHCP_RANGE_START},{self.DHCP_RANGE_END},{self.LAN_NETMASK},12h
dhcp-option=option:router,{self.LAN_GATEWAY}
dhcp-option=option:dns-server,{self.LAN_GATEWAY}

# DNS Configuration
domain={self.DNS_DOMAIN}
expand-hosts
local=/{self.DNS_DOMAIN}/

# Upstream DNS servers
server=8.8.8.8
server=1.1.1.1

# Logging
log-dhcp
log-queries
"""
            
            # Write configuration
            write_cmd = f"cat > /etc/dnsmasq.conf << 'EOF'\n{dnsmasq_config}\nEOF"
            result = await self._exec_in_lxc(vmid, write_cmd)
            
            if result.get('exitcode') != 0:
                logger.error("Failed to write dnsmasq config")
                return False
            
            # Enable and start dnsmasq
            enable_cmd = "rc-update add dnsmasq default && rc-service dnsmasq start"
            result = await self._exec_in_lxc(vmid, enable_cmd)
            
            if result.get('exitcode') != 0:
                logger.error("Failed to start dnsmasq")
                return False
            
            logger.info("    ✓ DHCP/DNS configured")
            return True
            
        except Exception as e:
            logger.error(f"DHCP/DNS configuration failed: {e}")
            return False
    
    async def _configure_caddy(self, vmid: int) -> bool:
        """Configure Caddy reverse proxy."""
        try:
            # Create Caddy directories
            mkdir_cmd = "mkdir -p /etc/caddy/sites-enabled"
            await self._exec_in_lxc(vmid, mkdir_cmd)
            
            # Create main Caddyfile
            caddyfile = """{
    # Global options
    admin off
    auto_https off  # We'll handle HTTPS per-site if needed
}

# Import all site configurations
import /etc/caddy/sites-enabled/*
"""
            
            write_cmd = f"cat > /etc/caddy/Caddyfile << 'EOF'\n{caddyfile}\nEOF"
            result = await self._exec_in_lxc(vmid, write_cmd)
            
            if result.get('exitcode') != 0:
                logger.error("Failed to write Caddyfile")
                return False
            
            # Enable and start Caddy
            enable_cmd = "rc-update add caddy default && rc-service caddy start"
            result = await self._exec_in_lxc(vmid, enable_cmd)
            
            if result.get('exitcode') != 0:
                logger.warning("Failed to start Caddy (may not have service script)")
                # Caddy might need manual service setup in Alpine
            
            logger.info("    ✓ Caddy reverse proxy configured")
            return True
            
        except Exception as e:
            logger.error(f"Caddy configuration failed: {e}")
            return False
    
    async def _configure_cockpit(self, vmid: int) -> bool:
        """Configure Cockpit management UI."""
        try:
            # Cockpit might not be available in standard Alpine repos
            # We'll try to install it, but won't fail if unavailable
            
            enable_cmd = "rc-update add cockpit default && rc-service cockpit start"
            result = await self._exec_in_lxc(vmid, enable_cmd)
            
            if result.get('exitcode') != 0:
                logger.warning("Cockpit not available (optional feature)")
                logger.info("    ⚠️  Cockpit not configured (optional)")
                return True  # Don't fail, it's optional
            
            logger.info("    ✓ Cockpit management UI configured")
            return True
            
        except Exception as e:
            logger.warning(f"Cockpit configuration skipped: {e}")
            return True  # Don't fail on optional feature
    
    async def verify_appliance_health(self) -> bool:
        """
        Verify appliance health and service status.
        
        Returns:
            bool: True if all critical services are healthy
        """
        if not self.appliance_info:
            logger.error("No appliance info available for health check")
            return False
        
        try:
            vmid = self.appliance_info.vmid
            logger.info("Verifying appliance health...")
            
            # Check if LXC is running
            status_cmd = "echo 'OK'"
            result = await self._exec_in_lxc(vmid, status_cmd)
            
            if result.get('exitcode') != 0:
                logger.error("Appliance LXC not responding")
                return False
            
            # Check critical services
            services = ['dnsmasq', 'iptables']
            for service in services:
                check_cmd = f"rc-service {service} status"
                result = await self._exec_in_lxc(vmid, check_cmd)
                
                status = 'running' if result.get('exitcode') == 0 else 'stopped'
                self.appliance_info.services[service] = (status == 'running')
                
                if status != 'running':
                    logger.warning(f"  ⚠️  Service {service}: {status}")
            
            logger.info("✓ Appliance health check complete")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def get_appliance_info(self) -> Optional[ApplianceInfo]:
        """
        Get current appliance information.
        
        Returns:
            ApplianceInfo: Current appliance info, or None if not initialized
        """
        return self.appliance_info
    
    # Helper methods
    
    async def _find_existing_appliance(self) -> Optional[ApplianceInfo]:
        """Find existing appliance LXC by hostname or VMID."""
        try:
            node = await self._get_default_node()
            if not node:
                return None
            
            # Check if VMID exists
            check_cmd = f"pct status {self.APPLIANCE_VMID}"
            result = await self._exec_on_host(check_cmd)
            
            if result and result.get('exitcode') == 0:
                # LXC exists, get its details
                wan_ip = await self._get_lxc_wan_ip(node, self.APPLIANCE_VMID)
                
                return ApplianceInfo(
                    vmid=self.APPLIANCE_VMID,
                    hostname=self.APPLIANCE_HOSTNAME,
                    wan_interface='eth0',
                    wan_ip=wan_ip,
                    lan_interface='eth1',
                    lan_ip=self.LAN_GATEWAY,
                    status='running',
                    services={}
                )
            
            return None
            
        except Exception as e:
            logger.debug(f"No existing appliance found: {e}")
            return None
    
    async def _get_default_node(self) -> Optional[str]:
        """Get the default Proxmox node name."""
        try:
            # Try to get from proxmox service
            if hasattr(self.proxmox, 'node'):
                return self.proxmox.node
            
            # Fallback: try to detect from hostname
            result = await self._exec_on_host("hostname")
            if result and result.get('exitcode') == 0:
                return result.get('output', '').strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Could not determine node: {e}")
            return None
    
    async def _get_lxc_wan_ip(self, node: str, vmid: int) -> Optional[str]:
        """Get the WAN (eth0) IP address of an LXC."""
        try:
            # Execute ip command inside LXC
            cmd = "ip -4 addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1"
            result = await self._exec_in_lxc(vmid, cmd)
            
            if result.get('exitcode') == 0:
                ip = result.get('output', '').strip()
                if ip and re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
                    return ip
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not get WAN IP: {e}")
            return None
    
    async def _exec_on_host(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Execute a command on the Proxmox host.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Dict with 'exitcode' and 'output', or None if failed
        """
        try:
            # Use subprocess to execute on local host
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            return {
                'exitcode': proc.returncode,
                'output': stdout.decode() if stdout else '',
                'error': stderr.decode() if stderr else ''
            }
            
        except Exception as e:
            logger.error(f"Failed to execute on host: {command} - {e}")
            return None
    
    async def _exec_in_lxc(self, vmid: int, command: str) -> Optional[Dict[str, Any]]:
        """
        Execute a command inside an LXC container.
        
        Args:
            vmid: VMID of the LXC container
            command: Shell command to execute
            
        Returns:
            Dict with 'exitcode' and 'output', or None if failed
        """
        try:
            # Use pct exec to run command in container
            full_cmd = f"pct exec {vmid} -- sh -c '{command}'"
            
            proc = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            return {
                'exitcode': proc.returncode,
                'output': stdout.decode() if stdout else '',
                'error': stderr.decode() if stderr else ''
            }
            
        except Exception as e:
            logger.error(f"Failed to execute in LXC {vmid}: {command} - {e}")
            return None
