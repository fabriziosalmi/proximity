"""
Proximity Network Manager V2 - Smart Bridge Detection

Intelligent network infrastructure management that:
1. Detects available Proxmox bridges (vmbr0, vmbr1, vmbr2, etc.)
2. Identifies which bridges are on the management LAN vs isolated
3. Uses an isolated bridge for app network with DHCP/DNS
4. Deploys an Alpine LXC router/proxy between management and app networks

Architecture:
- vmbr0 (or primary): Management network (Proxmox UI, Proximity API)
- vmbr1 (or available): Isolated app network (10.10.0.0/24)
- Router LXC: Bridges between networks, provides reverse proxy
"""

import asyncio
import ipaddress
import logging
import platform
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BridgeInfo:
    """Information about a Proxmox network bridge."""
    
    def __init__(self, name: str, ip: Optional[str] = None, subnet: Optional[str] = None, 
                 is_active: bool = False, is_management: bool = False):
        self.name = name
        self.ip = ip
        self.subnet = subnet
        self.is_active = is_active
        self.is_management = is_management
    
    def __repr__(self):
        status = "MGMT" if self.is_management else "ISOLATED"
        return f"BridgeInfo({self.name}, {self.ip}/{self.subnet}, {status})"


class NetworkManagerV2:
    """
    Smart network infrastructure manager for Proximity.
    
    Creates and manages a dedicated 'proximity-lan' bridge for isolated app networks.
    Falls back to management LAN only if bridge creation fails.
    """
    
    # Dedicated Proximity bridge
    PROXIMITY_BRIDGE = "proximity-lan"
    
    # Network configuration for isolated app network
    APP_NETWORK_SUBNET = "10.10.0.0/24"
    APP_NETWORK_GATEWAY = "10.10.0.1"
    DHCP_RANGE_START = "10.10.0.100"
    DHCP_RANGE_END = "10.10.0.250"
    DNS_DOMAIN = "prox.local"
    
    # Router LXC configuration
    ROUTER_VMID = 100  # Reserved VMID for router
    ROUTER_HOSTNAME = "proximity-router"
    
    def __init__(self, proxmox_service=None):
        """
        Initialize the Network Manager V2.
        
        Args:
            proxmox_service: ProxmoxService instance for API access
        """
        self.proxmox = proxmox_service
        self.management_bridge: Optional[BridgeInfo] = None
        self.app_bridge: Optional[BridgeInfo] = None
        self.router_deployed = False
    
    async def initialize(self) -> bool:
        """
        Initialize smart network infrastructure.
        
        Steps:
        1. Detect platform (skip if not Linux/Proxmox)
        2. Discover available bridges
        3. Check if proximity-lan exists, create if not
        4. Configure DHCP/DNS on proximity-lan
        5. Deploy router LXC for connectivity
        
        Returns:
            bool: True if initialization successful
        """
        logger.info("🌐 Initializing Proximity Smart Network Infrastructure...")
        
        # Check if running on Linux
        if platform.system() != "Linux":
            logger.warning(f"⚠️  Network infrastructure skipped: Not running on Linux (detected: {platform.system()})")
            logger.warning("⚠️  This is expected for development environments")
            logger.info("ℹ️  Containers will use default Proxmox networking")
            return False
        
        try:
            # Step 1: Discover available bridges
            logger.info("Step 1/5: Discovering Proxmox network bridges...")
            bridges = await self.discover_bridges()
            
            if not bridges:
                logger.error("No network bridges found on Proxmox host")
                return False
            
            logger.info(f"Found {len(bridges)} existing bridges: {[b.name for b in bridges]}")
            
            # Step 2: Identify management bridge
            logger.info("Step 2/5: Identifying management bridge...")
            await self.classify_bridges(bridges)
            
            if not self.management_bridge:
                logger.error("Could not identify management bridge")
                return False
            
            logger.info(f"Management bridge: {self.management_bridge.name}")
            
            # Step 3: Check if proximity-lan exists, create if not
            logger.info(f"Step 3/5: Setting up {self.PROXIMITY_BRIDGE} bridge...")
            proximity_bridge = next((b for b in bridges if b.name == self.PROXIMITY_BRIDGE), None)
            
            if proximity_bridge:
                logger.info(f"✓ Found existing {self.PROXIMITY_BRIDGE} bridge")
                self.app_bridge = proximity_bridge
            else:
                logger.info(f"Creating dedicated {self.PROXIMITY_BRIDGE} bridge...")
                if await self.create_proximity_bridge():
                    # Refresh bridge list
                    bridges = await self.discover_bridges()
                    self.app_bridge = next((b for b in bridges if b.name == self.PROXIMITY_BRIDGE), None)
                    logger.info(f"✓ Created {self.PROXIMITY_BRIDGE} bridge successfully")
                else:
                    logger.warning(f"⚠️  Failed to create {self.PROXIMITY_BRIDGE}, falling back to management bridge")
                    self.app_bridge = self.management_bridge
            
            # Step 4: Configure DHCP/DNS if using isolated bridge
            if self.app_bridge.name != self.management_bridge.name:
                logger.info(f"Step 4/5: Configuring DHCP/DNS on {self.PROXIMITY_BRIDGE}...")
                await self.configure_dhcp_dns()
            else:
                logger.warning("Step 4/5: Using management bridge (fallback mode - no isolation)")
            
            # Step 5: Deploy router LXC if needed
            if self.app_bridge.name != self.management_bridge.name and self.proxmox:
                logger.info("Step 5/5: Deploying router LXC...")
                await self.ensure_router_deployed()
            else:
                logger.info("Step 5/5: Router not needed (using management bridge)")
            
            # Verify configuration
            is_healthy = await self.verify_network_health()
            
            if is_healthy:
                if self.app_bridge.name == self.PROXIMITY_BRIDGE:
                    logger.info("✅ Proximity isolated network initialized successfully")
                    logger.info(f"   Apps will use: {self.PROXIMITY_BRIDGE} ({self.APP_NETWORK_SUBNET})")
                else:
                    logger.info("✅ Network initialized in fallback mode")
                    logger.info(f"   Apps will use: {self.app_bridge.name} (management LAN)")
                return True
            else:
                logger.warning("⚠️  Network infrastructure initialized with warnings")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize network infrastructure: {e}", exc_info=True)
            return False
    
    async def discover_bridges(self) -> List[BridgeInfo]:
        """
        Discover all network bridges on the Proxmox host.
        
        Uses 'ip' command to detect bridges and their configurations.
        
        Returns:
            List of BridgeInfo objects
        """
        bridges = []
        
        try:
            # Get all network interfaces
            proc = await asyncio.create_subprocess_exec(
                'ip', '-br', 'link', 'show', 'type', 'bridge',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.warning(f"Failed to list bridges: {stderr.decode()}")
                return bridges
            
            # Parse bridge names
            for line in stdout.decode().strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    bridge_name = parts[0]
                    state = parts[1]  # UP or DOWN
                    
                    # Get IP address for this bridge
                    ip_addr, subnet = await self._get_bridge_ip(bridge_name)
                    
                    bridge = BridgeInfo(
                        name=bridge_name,
                        ip=ip_addr,
                        subnet=subnet,
                        is_active=(state == 'UP')
                    )
                    bridges.append(bridge)
                    
                    logger.debug(f"Discovered bridge: {bridge}")
            
            return bridges
            
        except Exception as e:
            logger.error(f"Failed to discover bridges: {e}")
            return []
    
    async def _get_bridge_ip(self, bridge_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get IP address and subnet for a bridge.
        
        Args:
            bridge_name: Name of the bridge
            
        Returns:
            Tuple of (ip_address, subnet_mask)
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                'ip', '-4', 'addr', 'show', bridge_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return None, None
            
            # Parse output for IP address
            # Example: inet 192.168.1.100/24 brd 192.168.1.255 scope global vmbr0
            for line in stdout.decode().split('\n'):
                if 'inet ' in line:
                    match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)', line)
                    if match:
                        ip = match.group(1)
                        cidr = match.group(2)
                        return ip, cidr
            
            return None, None
            
        except Exception as e:
            logger.debug(f"Failed to get IP for {bridge_name}: {e}")
            return None, None
    
    async def create_proximity_bridge(self) -> bool:
        """
        Create the dedicated proximity-lan bridge for isolated app networking.
        
        This method creates a new Linux bridge interface named 'proximity-lan'
        and configures it with the app network subnet (10.10.0.0/24 by default).
        
        Steps:
        1. Check if bridge already exists
        2. Create bridge using 'ip link add'
        3. Assign IP address (10.10.0.1/24)
        4. Bring bridge up
        5. Make configuration persistent in /etc/network/interfaces
        
        Returns:
            bool: True if created successfully, False otherwise
        """
        try:
            logger.info(f"Creating {self.PROXIMITY_BRIDGE} bridge...")
            
            # Extract network info from APP_NETWORK_SUBNET (e.g., "10.10.0.0/24")
            network = ipaddress.ip_network(self.APP_NETWORK_SUBNET)
            bridge_ip = str(network.network_address + 1)  # 10.10.0.1
            bridge_cidr = str(network.prefixlen)  # 24
            
            # Step 1: Check if bridge already exists
            check_proc = await asyncio.create_subprocess_exec(
                'ip', 'link', 'show', self.PROXIMITY_BRIDGE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await check_proc.communicate()
            
            if check_proc.returncode == 0:
                logger.info(f"Bridge {self.PROXIMITY_BRIDGE} already exists")
                return True
            
            # Step 2: Create bridge
            logger.info(f"Creating bridge interface {self.PROXIMITY_BRIDGE}...")
            proc = await asyncio.create_subprocess_exec(
                'ip', 'link', 'add', 'name', self.PROXIMITY_BRIDGE, 'type', 'bridge',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"Failed to create bridge: {stderr.decode()}")
                return False
            
            # Step 3: Assign IP address
            logger.info(f"Assigning IP {bridge_ip}/{bridge_cidr} to {self.PROXIMITY_BRIDGE}...")
            proc = await asyncio.create_subprocess_exec(
                'ip', 'addr', 'add', f'{bridge_ip}/{bridge_cidr}', 'dev', self.PROXIMITY_BRIDGE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.warning(f"Failed to assign IP: {stderr.decode()}")
            
            # Step 4: Bring bridge up
            logger.info(f"Bringing up {self.PROXIMITY_BRIDGE}...")
            proc = await asyncio.create_subprocess_exec(
                'ip', 'link', 'set', self.PROXIMITY_BRIDGE, 'up',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"Failed to bring up bridge: {stderr.decode()}")
                return False
            
            # Step 5: Make configuration persistent
            logger.info(f"Making {self.PROXIMITY_BRIDGE} configuration persistent...")
            await self._persist_bridge_config(bridge_ip, bridge_cidr)
            
            logger.info(f"✓ Successfully created {self.PROXIMITY_BRIDGE} ({bridge_ip}/{bridge_cidr})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create proximity bridge: {e}")
            return False
    
    async def _persist_bridge_config(self, bridge_ip: str, bridge_cidr: str) -> bool:
        """
        Make bridge configuration persistent in /etc/network/interfaces.
        
        Args:
            bridge_ip: IP address for the bridge (e.g., "10.10.0.1")
            bridge_cidr: CIDR prefix (e.g., "24")
            
        Returns:
            bool: True if successful
        """
        try:
            interfaces_file = '/etc/network/interfaces'
            
            # Check if bridge already configured
            try:
                with open(interfaces_file, 'r') as f:
                    content = f.read()
                    if self.PROXIMITY_BRIDGE in content:
                        logger.info(f"{self.PROXIMITY_BRIDGE} already in {interfaces_file}")
                        return True
            except Exception as e:
                logger.debug(f"Could not read {interfaces_file}: {e}")
            
            # Append bridge configuration
            config = f"""
# Proximity isolated network bridge (auto-generated)
auto {self.PROXIMITY_BRIDGE}
iface {self.PROXIMITY_BRIDGE} inet static
    address {bridge_ip}/{bridge_cidr}
    bridge-ports none
    bridge-stp off
    bridge-fd 0
"""
            
            with open(interfaces_file, 'a') as f:
                f.write(config)
            
            logger.info(f"✓ Added {self.PROXIMITY_BRIDGE} to {interfaces_file}")
            return True
            
        except Exception as e:
            logger.warning(f"Could not persist bridge config: {e}")
            logger.warning("Bridge will work but won't survive reboot")
            return False
    
    async def classify_bridges(self, bridges: List[BridgeInfo]) -> None:
        """
        Classify bridges as management or isolated.
        
        Management bridge:
        - Has an IP address (active)
        - On the same subnet as Proxmox management interface
        
        Isolated bridge:
        - Either has no IP or on a different subnet
        - Available for isolated app network
        
        Args:
            bridges: List of discovered bridges
        """
        # Get Proxmox management IP from config or environment
        management_ip = None
        try:
            if self.proxmox and hasattr(self.proxmox, '_proxmox'):
                # Try to get from proxmox config
                from core.config import settings
                management_ip = settings.PROXMOX_HOST
        except Exception:
            pass
        
        # Classify bridges
        for bridge in bridges:
            if bridge.ip and management_ip:
                # Check if bridge IP is in same subnet as management
                try:
                    bridge_network = ipaddress.ip_network(f"{bridge.ip}/{bridge.subnet}", strict=False)
                    mgmt_ip_obj = ipaddress.ip_address(management_ip)
                    
                    if mgmt_ip_obj in bridge_network:
                        bridge.is_management = True
                        if not self.management_bridge:
                            self.management_bridge = bridge
                            logger.info(f"Identified management bridge: {bridge.name} ({bridge.ip}/{bridge.subnet})")
                except Exception as e:
                    logger.debug(f"Could not classify {bridge.name}: {e}")
        
        # If no management bridge found, use vmbr0 as default
        if not self.management_bridge:
            vmbr0 = next((b for b in bridges if b.name == 'vmbr0'), None)
            if vmbr0:
                vmbr0.is_management = True
                self.management_bridge = vmbr0
                logger.info(f"Using default management bridge: vmbr0")
        
        # Find first available isolated bridge
        for bridge in bridges:
            if not bridge.is_management and bridge.is_active:
                self.app_bridge = bridge
                logger.info(f"Found isolated bridge for apps: {bridge.name}")
                break
        
        # If no isolated bridge, look for any non-management bridge
        if not self.app_bridge:
            for bridge in bridges:
                if not bridge.is_management:
                    self.app_bridge = bridge
                    logger.info(f"Found available bridge for apps: {bridge.name} (will configure)")
                    break
    
    async def configure_dhcp_dns(self) -> bool:
        """
        Configure DHCP/DNS service on the isolated app bridge.
        
        Sets up dnsmasq to provide:
        - DHCP: Automatic IP assignment
        - DNS: Hostname resolution for containers
        
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Configuring DHCP/DNS on {self.app_bridge.name}...")
            
            # Configure bridge with static IP if not already configured
            if not self.app_bridge.ip:
                await self._configure_bridge_ip()
            
            # Generate dnsmasq configuration
            config = self._generate_dnsmasq_config()
            
            # Write configuration (would need root/sudo in production)
            logger.info("DHCP/DNS configuration ready (manual deployment required on production)")
            logger.debug(f"Config:\n{config}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure DHCP/DNS: {e}")
            return False
    
    async def _configure_bridge_ip(self) -> None:
        """Configure static IP on the app bridge."""
        logger.info(f"Configuring {self.app_bridge.name} with IP {self.APP_NETWORK_GATEWAY}/{self.APP_NETWORK_SUBNET.split('/')[1]}")
        # In production, this would execute:
        # ip addr add 10.10.0.1/24 dev vmbr1
        # This requires root privileges
    
    def _generate_dnsmasq_config(self) -> str:
        """Generate dnsmasq configuration for app network."""
        return f"""# Proximity App Network DHCP/DNS Configuration
# Auto-generated for {self.app_bridge.name}

# Interface to listen on
interface={self.app_bridge.name}

# DHCP range
dhcp-range={self.DHCP_RANGE_START},{self.DHCP_RANGE_END},12h

# DNS domain
domain={self.DNS_DOMAIN}
local=/{self.DNS_DOMAIN}/

# DNS servers (upstream)
server=1.1.1.1
server=8.8.8.8

# DHCP options
dhcp-option=option:router,{self.APP_NETWORK_GATEWAY}
dhcp-option=option:dns-server,{self.APP_NETWORK_GATEWAY}

# Logging
log-queries
log-dhcp
"""
    
    async def ensure_router_deployed(self) -> bool:
        """
        Ensure router LXC is deployed between management and app networks.
        
        The router LXC:
        - Has two network interfaces (vmbr0 and vmbr1)
        - Runs Caddy or nginx for reverse proxy
        - Provides NAT/routing between networks
        
        Returns:
            bool: True if router is deployed and healthy
        """
        if not self.proxmox:
            logger.warning("Cannot deploy router: ProxmoxService not available")
            return False
        
        try:
            # Check if router already exists
            logger.info(f"Checking for router LXC (VMID {self.ROUTER_VMID})...")
            
            nodes = await self.proxmox.get_nodes()
            if not nodes:
                logger.error("No Proxmox nodes available")
                return False
            
            target_node = nodes[0].node
            
            # Check if router exists
            try:
                router_status = await self.proxmox.get_lxc_status(target_node, self.ROUTER_VMID)
                logger.info(f"Router LXC found: {router_status.status}")
                self.router_deployed = True
                return True
            except Exception:
                logger.info("Router LXC not found, will deploy...")
            
            # Deploy router LXC
            logger.info(f"Deploying router LXC on node {target_node}...")
            
            router_config = {
                'hostname': self.ROUTER_HOSTNAME,
                'cores': 1,
                'memory': 512,
                'rootfs': 'local-lvm:4',
                # Two network interfaces
                'net0': f'name=eth0,bridge={self.management_bridge.name},ip=dhcp,firewall=1',
                'net1': f'name=eth1,bridge={self.app_bridge.name},ip={self.APP_NETWORK_GATEWAY}/24,firewall=1',
                'features': 'nesting=1',
                'unprivileged': 1,
                'onboot': 1
            }
            
            # Create router container
            result = await self.proxmox.create_lxc(target_node, self.ROUTER_VMID, router_config)
            task_id = result['task_id']
            
            # Wait for creation
            await self.proxmox.wait_for_task(target_node, task_id, timeout=300)
            logger.info("✓ Router LXC created successfully")
            
            # Start router
            start_task = await self.proxmox.start_lxc(target_node, self.ROUTER_VMID)
            await self.proxmox.wait_for_task(target_node, start_task, timeout=120)
            logger.info("✓ Router LXC started successfully")
            
            # Configure router (install routing/proxy software)
            await self._configure_router(target_node)
            
            self.router_deployed = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy router LXC: {e}")
            return False
    
    async def _configure_router(self, node: str) -> None:
        """
        Configure router LXC with routing and reverse proxy.
        
        Args:
            node: Proxmox node name
        """
        try:
            logger.info("Configuring router LXC...")
            
            # Wait for container to be ready
            await asyncio.sleep(10)
            
            # Enable IP forwarding
            await self.proxmox.execute_in_container(
                node, self.ROUTER_VMID,
                "sysctl -w net.ipv4.ip_forward=1"
            )
            
            # Make it persistent
            await self.proxmox.execute_in_container(
                node, self.ROUTER_VMID,
                "echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf"
            )
            
            # Install iptables for NAT
            await self.proxmox.execute_in_container(
                node, self.ROUTER_VMID,
                "apk add --no-cache iptables ip6tables"
            )
            
            # Configure NAT from app network to management network
            await self.proxmox.execute_in_container(
                node, self.ROUTER_VMID,
                f"iptables -t nat -A POSTROUTING -s {self.APP_NETWORK_SUBNET} -o eth0 -j MASQUERADE"
            )
            
            logger.info("✓ Router LXC configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to configure router: {e}")
            raise
    
    async def verify_network_health(self) -> bool:
        """
        Verify network infrastructure health.
        
        Returns:
            bool: True if healthy
        """
        try:
            # Check bridges exist
            if not self.management_bridge or not self.app_bridge:
                return False
            
            # If using isolated network, check router
            if self.app_bridge.name != self.management_bridge.name:
                if not self.router_deployed:
                    logger.warning("Router not deployed for isolated network")
                    return False
            
            logger.info("Network infrastructure health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def get_container_network_config(self, hostname: str) -> str:
        """
        Get network configuration for a new container.
        
        Args:
            hostname: Container hostname
            
        Returns:
            Network configuration string for Proxmox
        """
        if self.app_bridge:
            return f"name=eth0,bridge={self.app_bridge.name},ip=dhcp,firewall=1"
        else:
            # Fallback to vmbr0
            return "name=eth0,bridge=vmbr0,ip=dhcp,firewall=1"
    
    def get_network_status(self) -> Dict:
        """
        Get current network infrastructure status.
        
        Returns:
            Dict with status information
        """
        return {
            "management_bridge": self.management_bridge.name if self.management_bridge else None,
            "app_bridge": self.app_bridge.name if self.app_bridge else None,
            "isolated_network": self.app_bridge.name != self.management_bridge.name if (self.app_bridge and self.management_bridge) else False,
            "router_deployed": self.router_deployed,
            "app_network_subnet": self.APP_NETWORK_SUBNET,
            "app_network_gateway": self.APP_NETWORK_GATEWAY,
            "dhcp_range": f"{self.DHCP_RANGE_START}-{self.DHCP_RANGE_END}",
            "dns_domain": self.DNS_DOMAIN
        }
