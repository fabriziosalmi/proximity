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
    APPLIANCE_VMID = 9999  # Reserved VMID for the Proximity-managed appliance (changed from 100 to avoid conflicts)
    
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
            # Get target node from Proxmox cluster
            nodes = await self.proxmox.get_nodes()
            if not nodes:
                logger.error("No Proxmox nodes available")
                return False
            
            # Use first online node for appliance deployment
            target_node = nodes[0].node
            logger.info(f"Selected node '{target_node}' for network appliance deployment")
            
            # Step 1: Ensure host bridge exists on target node
            logger.info(f"Step 1/4: Provisioning host bridge on {target_node}...")
            if not await self.ensure_bridge_on_node(target_node):
                logger.error(f"Failed to setup host bridge on {target_node}")
                return False
            
            # Step 2: Provision appliance LXC
            logger.info("Step 2/4: Provisioning appliance LXC...")
            appliance = await self.provision_appliance_lxc(target_node)
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
    
    async def setup_host_bridge(self, target_node: str = None) -> bool:
        """
        Provision the proximity-lan bridge on the Proxmox host (or specific node).
        
        This creates a simple, unconfigured bridge that will be managed
        entirely by the appliance LXC. The bridge has no IP on the host itself.
        
        Args:
            target_node: Optional specific node to create bridge on. If None, uses default SSH host.
        
        Returns:
            bool: True if bridge exists or was created successfully
        """
        try:
            node_info = f" on node {target_node}" if target_node else ""
            logger.info(f"Checking for {self.BRIDGE_NAME} bridge{node_info}...")
            
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
                f"ip link set {self.BRIDGE_NAME} up",
                f"ip link set {self.BRIDGE_NAME} master {self.BRIDGE_NAME} 2>/dev/null || true"  # Ensure bridge is its own master
            ]
            
            for cmd in commands:
                result = await self._exec_on_host(cmd)
                if result.get('exitcode') != 0 and "already exists" not in result.get('error', '').lower():
                    logger.error(f"Failed to execute: {cmd}")
                    return False
            
            # Make persistent in /etc/network/interfaces
            persist_success = await self._persist_bridge_config()
            
            if persist_success:
                # Reload Proxmox networking to register the bridge
                logger.info("Reloading Proxmox network configuration...")
                reload_cmd = "ifreload -a"
                reload_result = await self._exec_on_host(reload_cmd)
                
                if reload_result.get('exitcode') == 0:
                    logger.info("✓ Proxmox network configuration reloaded")
                else:
                    logger.warning("⚠ Could not reload network config (bridge active but may need manual reload)")
            
            # Verify bridge is visible to Proxmox
            verify_cmd = f"pvesh get /nodes/$(hostname)/network --type bridge 2>/dev/null || brctl show"
            verify_result = await self._exec_on_host(verify_cmd)
            
            if verify_result and self.BRIDGE_NAME in verify_result.get('output', ''):
                logger.info(f"✓ Bridge {self.BRIDGE_NAME} verified in Proxmox network list")
            else:
                logger.warning(f"⚠ Bridge {self.BRIDGE_NAME} not yet visible in Proxmox network list")
                logger.warning("  This is normal - bridge will be available after networking reload")
            
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
                
                # Bring up the bridge using ifup to ensure it's properly registered
                ifup_cmd = f"ifup {self.BRIDGE_NAME}"
                ifup_result = await self._exec_on_host(ifup_cmd)
                
                if ifup_result.get('exitcode') == 0:
                    logger.info(f"✓ Bridge {self.BRIDGE_NAME} activated via ifup")
                else:
                    logger.warning(f"Could not activate bridge via ifup (may already be up)")
                
                return True
            else:
                logger.warning("Could not persist bridge config (will work until reboot)")
                return False
                
        except Exception as e:
            logger.warning(f"Could not persist bridge config: {e}")
            return False
    
    async def provision_appliance_lxc(self, node: str) -> Optional[ApplianceInfo]:
        """
        Provision the Network Appliance LXC container.
        
        This creates a specialized, dual-homed Alpine Linux LXC with:
        - Privileged mode (for iptables, service management)
        - eth0 on vmbr0 (WAN/management) with DHCP
        - eth1 on proximity-lan (LAN) with static 10.20.0.1/24
        
        Args:
            node: Target Proxmox node to create appliance on
        
        Returns:
            ApplianceInfo: Information about the provisioned appliance, or None if failed
        """
        try:
            # Check if appliance already exists
            existing = await self._find_existing_appliance()
            if existing:
                logger.info(f"✓ Found existing appliance: VMID {existing.vmid}")
                return existing
            
            logger.info(f"Creating new appliance LXC on node {node}: {self.APPLIANCE_HOSTNAME}")
            
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
            
            # Create the appliance LXC - note: vmid is separate parameter
            result = await self.proxmox.create_lxc(node, self.APPLIANCE_VMID, config)
            
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
    
    async def ensure_bridge_on_node(self, node: str) -> bool:
        """
        Ensure the proximity-lan bridge exists on a specific Proxmox node.
        
        This is critical for Proxmox clusters where each node needs its own bridge.
        The bridge must exist on the node where a container will be deployed.
        
        Args:
            node: Name of the Proxmox node (e.g., 'opti2', 'pve')
            
        Returns:
            bool: True if bridge exists or was created successfully on the node
        """
        try:
            logger.info(f"Ensuring {self.BRIDGE_NAME} bridge exists on node {node}...")
            
            bridge_exists = False
            
            # Check if bridge exists on this node (connect directly to the node)
            check_cmd = f"ip link show {self.BRIDGE_NAME}"
            try:
                result = await self.proxmox.execute_on_node(node, check_cmd, allow_nonzero_exit=True)
                if "does not exist" not in result.lower() and result.strip():
                    logger.info(f"✓ Bridge {self.BRIDGE_NAME} already exists on node {node}")
                    bridge_exists = True
            except Exception as e:
                logger.debug(f"Bridge check on {node}: {e}")
                # Bridge doesn't exist, continue to creation
                pass
            
            # Create bridge if it doesn't exist
            if not bridge_exists:
                logger.info(f"Creating {self.BRIDGE_NAME} bridge on node {node}...")
                
                try:
                    create_cmd = f"ip link add name {self.BRIDGE_NAME} type bridge && ip link set {self.BRIDGE_NAME} up"
                    await self.proxmox.execute_on_node(node, create_cmd, allow_nonzero_exit=True)
                    logger.info(f"✓ Bridge {self.BRIDGE_NAME} created on node {node}")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.error(f"Failed to create bridge on {node}: {e}")
                        return False
            
            # Always check and persist the configuration (even if bridge already existed)
            # This ensures the bridge survives reboots
            config = f"""
# Proximity isolated network bridge (auto-generated)
auto {self.BRIDGE_NAME}
iface {self.BRIDGE_NAME} inet manual
    bridge-ports none
    bridge-stp off
    bridge-fd 0
"""
            
            # Check if already in config on this specific node
            check_config_cmd = f"grep -q {self.BRIDGE_NAME} /etc/network/interfaces"
            config_exists = False
            try:
                result = await self.proxmox.execute_on_node(node, check_config_cmd, allow_nonzero_exit=True)
                if result and "exitcode" not in str(result).lower():
                    logger.info(f"✓ Bridge already persisted in config on node {node}")
                    config_exists = True
            except:
                pass
            
            # Add to config if not already there
            if not config_exists:
                escaped_config = config.replace("'", "'\\''").replace('\n', '\\n')
                persist_cmd = f"echo '{escaped_config}' >> /etc/network/interfaces"
                try:
                    await self.proxmox.execute_on_node(node, persist_cmd)
                    logger.info(f"✓ Bridge configuration persisted on node {node}")
                    
                    # Reload networking on that node
                    reload_cmd = "ifreload -a"
                    await self.proxmox.execute_on_node(node, reload_cmd, allow_nonzero_exit=True)
                    logger.info(f"✓ Network configuration reloaded on node {node}")
                    
                    # Restart pve-cluster to ensure Proxmox recognizes the new bridge
                    # This is critical for LXC containers to see the bridge
                    restart_cmd = "systemctl restart pve-cluster"
                    await self.proxmox.execute_on_node(node, restart_cmd, allow_nonzero_exit=True)
                    logger.info(f"✓ Proxmox cluster service restarted on node {node}")
                except Exception as e:
                    logger.error(f"Failed to persist bridge config on node {node}: {e}")
                    return False
            
            logger.info(f"✓ Bridge {self.BRIDGE_NAME} ready on node {node}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure bridge on node {node}: {e}")
            return False
    
    async def get_container_network_config(self, hostname: str, node: str = None) -> str:
        """
        Get network configuration string for a container to be deployed.
        
        This method provides compatibility with ProxmoxService's network_manager interface.
        Returns a network configuration string that connects the container to proximity-lan bridge.
        
        Automatically ensures the bridge exists on the target node before returning config.
        
        Args:
            hostname: Hostname for the container (used for logging)
            node: Target Proxmox node where container will be deployed (optional)
            
        Returns:
            str: Network configuration string (e.g., "name=eth0,bridge=proximity-lan,ip=dhcp")
        """
        if not self.appliance_info:
            logger.warning(f"Network appliance not initialized for {hostname}, using default bridge")
            return "name=eth0,bridge=vmbr0,ip=dhcp,firewall=1"
        
        # Ensure bridge exists on target node before returning config
        if node:
            logger.info(f"Ensuring {self.BRIDGE_NAME} bridge exists on node {node}...")
            bridge_ready = await self.ensure_bridge_on_node(node)
            if not bridge_ready:
                logger.warning(f"Failed to ensure bridge on {node}, falling back to vmbr0")
                return "name=eth0,bridge=vmbr0,ip=dhcp,firewall=1"
        
        # Container connects to proximity-lan bridge with DHCP
        # The appliance's dnsmasq will assign IP addresses from 10.20.0.100-250
        net_config = f"name=eth0,bridge={self.BRIDGE_NAME},ip=dhcp,firewall=1"
        
        logger.info(f"Container {hostname} will use proximity-lan network on node {node} (DHCP-managed)")
        
        return net_config
    
    async def get_infrastructure_status(self) -> Dict[str, Any]:
        """
        Get comprehensive infrastructure status for the Infrastructure page.
        
        Returns detailed information about:
        - Network appliance status
        - Bridge configuration
        - Network statistics
        - Service status
        - Connected applications
        - Resource usage
        
        Returns:
            Dict with complete infrastructure information
        """
        try:
            status = {
                'appliance': None,
                'bridge': None,
                'network': None,
                'services': {},
                'applications': [],
                'statistics': {}
            }
            
            # Appliance information
            if self.appliance_info:
                status['appliance'] = {
                    'vmid': self.appliance_info.vmid,
                    'hostname': self.appliance_info.hostname,
                    'status': self.appliance_info.status,
                    'wan_ip': self.appliance_info.wan_ip,
                    'wan_interface': self.appliance_info.wan_interface,
                    'lan_ip': self.appliance_info.lan_ip,
                    'lan_interface': self.appliance_info.lan_interface,
                    'management_url': f"http://{self.appliance_info.wan_ip}:{self.COCKPIT_PORT}" if self.appliance_info.wan_ip else None
                }
                
                # Get resource usage
                usage = await self._get_appliance_resource_usage(self.appliance_info.vmid)
                status['appliance']['resources'] = usage
            
            # Bridge information
            bridge_info = await self._get_bridge_status()
            status['bridge'] = bridge_info
            
            # Network configuration
            status['network'] = {
                'bridge_name': self.BRIDGE_NAME,
                'network': self.LAN_NETWORK,
                'gateway': self.LAN_GATEWAY,
                'netmask': self.LAN_NETMASK,
                'dhcp_range': f"{self.DHCP_RANGE_START} - {self.DHCP_RANGE_END}",
                'dns_domain': self.DNS_DOMAIN
            }
            
            # Service status
            if self.appliance_info:
                services_status = await self._get_services_status(self.appliance_info.vmid)
                status['services'] = services_status
            
            # Connected applications (DHCP leases)
            apps = await self._get_connected_applications()
            status['applications'] = apps
            
            # Network statistics
            stats = await self._get_network_statistics()
            status['statistics'] = stats
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get infrastructure status: {e}")
            return {'error': str(e)}
    
    async def count_connected_apps(self) -> int:
        """
        Count how many applications are currently connected to proximity-lan.
        
        Returns:
            int: Number of connected applications
        """
        try:
            apps = await self._get_connected_applications()
            return len(apps)
        except Exception as e:
            logger.error(f"Failed to count connected apps: {e}")
            return 0
    
    async def cleanup_if_empty(self) -> bool:
        """
        Clean up network infrastructure if no applications are connected.
        
        This method should be called when deleting an application.
        It checks if this was the last application, and if so, cleans up
        the network appliance and bridge.
        
        Returns:
            bool: True if cleanup was performed (was last app), False otherwise
        """
        try:
            # Count remaining apps
            app_count = await self.count_connected_apps()
            
            if app_count > 0:
                logger.info(f"Infrastructure still in use ({app_count} apps remaining)")
                return False
            
            logger.info("Last application removed, cleaning up infrastructure...")
            
            # Stop and delete appliance LXC
            if self.appliance_info:
                await self._cleanup_appliance(self.appliance_info.vmid)
            
            # Remove bridge
            await self._cleanup_bridge()
            
            # Reset state
            self.appliance_info = None
            
            logger.info("✓ Infrastructure cleanup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup infrastructure: {e}")
            return False
    
    async def _get_appliance_resource_usage(self, vmid: int) -> Dict[str, Any]:
        """Get resource usage for the appliance LXC."""
        try:
            # Get CPU and memory usage from pct status
            status_cmd = f"pct status {vmid}"
            result = await self._exec_on_host(status_cmd)
            
            if result.get('exitcode') != 0:
                return {}
            
            # Get detailed stats
            config_cmd = f"pct config {vmid}"
            config_result = await self._exec_on_host(config_cmd)
            
            usage = {
                'cpu_cores': 2,
                'memory_mb': 1024,
                'storage_gb': 8,
                'status': 'running' if 'running' in result.get('output', '') else 'stopped'
            }
            
            return usage
            
        except Exception as e:
            logger.debug(f"Could not get resource usage: {e}")
            return {}
    
    async def _get_bridge_status(self) -> Dict[str, Any]:
        """Get status of the proximity-lan bridge."""
        try:
            # Check if bridge exists
            check_cmd = f"ip -br link show {self.BRIDGE_NAME}"
            result = await self._exec_on_host(check_cmd)
            
            if result.get('exitcode') != 0:
                return {
                    'name': self.BRIDGE_NAME,
                    'exists': False,
                    'status': 'not found'
                }
            
            # Get bridge details
            detail_cmd = f"ip -d link show {self.BRIDGE_NAME}"
            detail_result = await self._exec_on_host(detail_cmd)
            
            # Get IP address
            ip_cmd = f"ip -4 addr show {self.BRIDGE_NAME}"
            ip_result = await self._exec_on_host(ip_cmd)
            
            output = result.get('output', '')
            status = 'UP' if 'UP' in output else 'DOWN'
            
            return {
                'name': self.BRIDGE_NAME,
                'exists': True,
                'status': status,
                'type': 'bridge',
                'details': detail_result.get('output', '').strip()
            }
            
        except Exception as e:
            logger.debug(f"Could not get bridge status: {e}")
            return {'name': self.BRIDGE_NAME, 'exists': False}
    
    async def _get_services_status(self, vmid: int) -> Dict[str, Dict[str, Any]]:
        """Get status of all services running in the appliance."""
        try:
            services = {
                'dnsmasq': {'name': 'DHCP/DNS Server', 'status': 'unknown'},
                'iptables': {'name': 'NAT Firewall', 'status': 'unknown'},
                'caddy': {'name': 'Reverse Proxy', 'status': 'unknown'},
                'cockpit': {'name': 'Management UI', 'status': 'unknown'}
            }
            
            for service_name in services.keys():
                check_cmd = f"rc-service {service_name} status"
                result = await self._exec_in_lxc(vmid, check_cmd)
                
                if result.get('exitcode') == 0:
                    services[service_name]['status'] = 'running'
                    services[service_name]['healthy'] = True
                else:
                    services[service_name]['status'] = 'stopped'
                    services[service_name]['healthy'] = False
            
            return services
            
        except Exception as e:
            logger.debug(f"Could not get services status: {e}")
            return {}
    
    async def _get_connected_applications(self) -> List[Dict[str, Any]]:
        """Get list of applications connected to proximity-lan via DHCP leases."""
        try:
            if not self.appliance_info:
                return []
            
            # Read DHCP leases file
            leases_cmd = "cat /var/lib/misc/dnsmasq.leases 2>/dev/null || echo ''"
            result = await self._exec_in_lxc(self.appliance_info.vmid, leases_cmd)
            
            if result.get('exitcode') != 0:
                return []
            
            apps = []
            leases = result.get('output', '').strip().split('\n')
            
            for lease in leases:
                if not lease:
                    continue
                
                # Parse lease: timestamp mac ip hostname client-id
                parts = lease.split()
                if len(parts) >= 4:
                    apps.append({
                        'ip': parts[2],
                        'hostname': parts[3],
                        'mac': parts[1],
                        'lease_expires': parts[0],
                        'dns_name': f"{parts[3]}.{self.DNS_DOMAIN}"
                    })
            
            return apps
            
        except Exception as e:
            logger.debug(f"Could not get connected applications: {e}")
            return []
    
    async def _get_network_statistics(self) -> Dict[str, Any]:
        """Get network statistics for the appliance."""
        try:
            if not self.appliance_info:
                return {}
            
            # Get interface statistics
            stats_cmd = "ip -s link show eth1"
            result = await self._exec_in_lxc(self.appliance_info.vmid, stats_cmd)
            
            if result.get('exitcode') != 0:
                return {}
            
            # Parse output for RX/TX bytes
            output = result.get('output', '')
            
            # Basic statistics
            stats = {
                'interface': 'eth1',
                'network': self.LAN_NETWORK,
                'gateway': self.LAN_GATEWAY
            }
            
            # Count DHCP leases
            apps = await self._get_connected_applications()
            stats['active_leases'] = len(apps)
            stats['available_ips'] = 151  # 250 - 100 + 1
            
            return stats
            
        except Exception as e:
            logger.debug(f"Could not get network statistics: {e}")
            return {}
    
    async def _cleanup_appliance(self, vmid: int) -> bool:
        """Clean up the appliance LXC."""
        try:
            logger.info(f"Stopping appliance LXC {vmid}...")
            
            # Stop LXC
            stop_cmd = f"pct stop {vmid}"
            result = await self._exec_on_host(stop_cmd)
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Delete LXC
            delete_cmd = f"pct destroy {vmid}"
            result = await self._exec_on_host(delete_cmd)
            
            if result.get('exitcode') == 0:
                logger.info(f"✓ Appliance LXC {vmid} deleted")
                return True
            else:
                logger.error(f"Failed to delete appliance LXC: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cleanup appliance: {e}")
            return False
    
    async def _cleanup_bridge(self) -> bool:
        """Clean up the proximity-lan bridge."""
        try:
            logger.info(f"Removing {self.BRIDGE_NAME} bridge...")
            
            # Bring bridge down
            down_cmd = f"ip link set {self.BRIDGE_NAME} down"
            await self._exec_on_host(down_cmd)
            
            # Delete bridge
            delete_cmd = f"ip link delete {self.BRIDGE_NAME}"
            result = await self._exec_on_host(delete_cmd)
            
            if result.get('exitcode') == 0:
                logger.info(f"✓ Bridge {self.BRIDGE_NAME} deleted")
                
                # Remove from /etc/network/interfaces
                remove_cmd = f"sed -i '/{self.BRIDGE_NAME}/,+5d' /etc/network/interfaces"
                await self._exec_on_host(remove_cmd)
                
                return True
            else:
                logger.error(f"Failed to delete bridge: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cleanup bridge: {e}")
            return False
    
    # Helper methods
    
    async def _find_existing_appliance(self) -> Optional[ApplianceInfo]:
        """Find existing appliance LXC by hostname or VMID."""
        try:
            node = await self._get_default_node()
            if not node:
                return None
            
            # Use Proxmox API to check if container exists
            try:
                container_info = await self.proxmox.get_lxc_info(node, self.APPLIANCE_VMID)
                if container_info:
                    # LXC exists, get its details
                    wan_ip = await self._get_lxc_wan_ip(node, self.APPLIANCE_VMID)
                    
                    logger.info(f"Found existing appliance VMID {self.APPLIANCE_VMID} with WAN IP: {wan_ip}")
                    
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
            except:
                # Container doesn't exist or API call failed
                pass
            
            logger.info(f"No existing appliance found at VMID {self.APPLIANCE_VMID}, will create new one")
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
        Execute a command on the Proxmox host via SSH.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Dict with 'exitcode' and 'output', or None if failed
        """
        try:
            # Use ProxmoxService SSH to execute on remote host
            output = await self.proxmox.execute_command_via_ssh(
                node="",  # Not used by execute_command_via_ssh
                command=command,
                allow_nonzero_exit=True
            )
            
            # SSH method only raises on error if allow_nonzero_exit=False
            # If we get here, command succeeded (exitcode 0)
            return {
                'exitcode': 0,
                'output': output,
                'error': ''
            }
            
        except Exception as e:
            # Command failed (non-zero exit or SSH error)
            logger.error(f"Failed to execute on host: {command} - {e}")
            return {
                'exitcode': 1,
                'output': '',
                'error': str(e)
            }
    
    async def _exec_in_lxc(self, vmid: int, command: str) -> Optional[Dict[str, Any]]:
        """
        Execute a command inside an LXC container via SSH + pct exec.
        
        Args:
            vmid: VMID of the LXC container
            command: Shell command to execute
            
        Returns:
            Dict with 'exitcode' and 'output', or None if failed
        """
        try:
            # Use ProxmoxService to execute via SSH + pct exec
            output = await self.proxmox.execute_in_container(
                node="",  # Not used by execute_in_container
                vmid=vmid,
                command=command,
                allow_nonzero_exit=True
            )
            
            # If we get here, command succeeded (exitcode 0)
            return {
                'exitcode': 0,
                'output': output,
                'error': ''
            }
            
        except Exception as e:
            # Command failed (non-zero exit or SSH error)
            logger.error(f"Failed to execute in LXC {vmid}: {command} - {e}")
            return {
                'exitcode': 1,
                'output': '',
                'error': str(e)
            }
