# Proximity Smart Network Architecture V2

## Overview

Proximity V2 introduces **intelligent network bridge management** with a **dedicated proximity-lan bridge** for isolated app networking. The system automatically detects existing Proxmox bridges, creates a purpose-built `proximity-lan` bridge for apps, and deploys a router LXC for secure connectivity.

## Key Innovation: Dedicated Bridge Naming

Instead of auto-detecting random vmbr1/vmbr2 bridges, Proximity creates a **consistently named `proximity-lan` bridge** across all installations. This provides:

✅ **Consistent naming** - Same bridge name on every Proxmox host  
✅ **Clear purpose** - Immediately obvious which bridge is for Proximity  
✅ **Easy documentation** - "Use proximity-lan" instead of "find available vmbr"  
✅ **Production ready** - Explicit creation rather than auto-detection guessing

## Architecture Comparison

### V1: Simple Networking (Current - Fallback Mode)
```
┌─────────────────────────────────────────────────────────┐
│                    Proxmox Host                          │
│                                                          │
│  ┌──────────────────────────────────────────────┐      │
│  │           vmbr0 (Management LAN)              │      │
│  │           192.168.1.0/24                      │      │
│  │                                                │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │      │
│  │  │ Proxmox  │  │ Proximity│  │   App    │   │      │
│  │  │   UI     │  │   API    │  │ Container│   │      │
│  │  │ :8006    │  │  :8765   │  │  :80     │   │      │
│  │  └──────────┘  └──────────┘  └──────────┘   │      │
│  └──────────────────────────────────────────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘

Issues:
- All containers on same LAN as management
- Apps exposed to local network
- No isolation between apps
- IP conflicts possible
```

### V2: Isolated Network with proximity-lan (Secure Mode - Default)
```
┌─────────────────────────────────────────────────────────────────────┐
│                         Proxmox Host                                 │
│                                                                       │
│  ┌──────────────────────────────────────────────┐                   │
│  │        vmbr0 (Management LAN)                 │                   │
│  │        192.168.1.0/24                         │                   │
│  │                                                │                   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐ │                   │
│  │  │ Proxmox  │  │ Proximity│  │   Router   │ │                   │
│  │  │   UI     │  │   API    │  │    LXC     │─┼──┐                │
│  │  │ :8006    │  │  :8765   │  │ (VMID 100) │ │  │                │
│  │  └──────────┘  └──────────┘  └────────────┘ │  │                │
│  └───────────────────────────────────────────────┘  │                │
│                                                      │                │
│                                                      │ NAT/Routing    │
│  ┌───────────────────────────────────────────────┐  │                │
│  │        proximity-lan (Isolated Network)       │◄─┘                │
│  │        10.10.0.0/24                           │                   │
│  │        DHCP: 10.10.0.100-250                  │                   │
│  │        DNS: *.prox.local                      │                   │
│  │                                                │                   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │                   │
│  │  │  nginx   │  │wordpress │  │  nextcloud│   │                   │
│  │  │10.10.0.101│  │10.10.0.102│ │10.10.0.103│   │                   │
│  │  └──────────┘  └──────────┘  └──────────┘   │                   │
│  └───────────────────────────────────────────────┘                   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

Benefits:
✅ Apps isolated from management network
✅ No IP conflicts with LAN
✅ Private DNS (.prox.local)
✅ Automatic DHCP
✅ NAT routing through router LXC
✅ Reverse proxy ready
✅ Consistent "proximity-lan" naming
```

## Smart Bridge Management

### Initialization Process

The NetworkManagerV2 automatically:

1. **Scans for all bridges** on Proxmox host (vmbr0, vmbr1, proximity-lan, etc.)
2. **Identifies management bridge** (where Proxmox UI runs)
3. **Checks if proximity-lan exists** - creates if missing
4. **Configures DHCP/DNS** on proximity-lan
5. **Deploys router LXC** to connect networks

### Bridge Classification

**Management Bridge:**
- Has active IP address
- On same subnet as Proxmox UI (`:8006`) and Proximity API (`:8765`)
- Used for management traffic
- Typically `vmbr0`

**App Bridge (proximity-lan):**
- Dedicated bridge created by Proximity
- Isolated subnet (10.10.0.0/24)
- Not on LAN
- Used exclusively for app containers
- Consistently named across all installations

### Example Initialization Output

```
Step 1/5: Discovering Proxmox network bridges...
Found 2 existing bridges: ['vmbr0', 'vmbr1']

Step 2/5: Identifying management bridge...
Management bridge: vmbr0

Step 3/5: Setting up proximity-lan bridge...
Creating dedicated proximity-lan bridge...
✓ Created proximity-lan bridge successfully

Step 4/5: Configuring DHCP/DNS on proximity-lan...
Configured DHCP range: 10.10.0.100-250
Configured DNS domain: .prox.local

Step 5/5: Deploying router LXC...
Router LXC (VMID 100) deployed successfully

✅ Proximity isolated network initialized successfully
   Apps will use: proximity-lan (10.10.0.0/24)
```

## Router LXC (VMID 100)

### Purpose

The router LXC is a lightweight Alpine Linux container that:

1. **Bridges networks**: Connects vmbr0 (management) to proximity-lan (apps)
2. **Provides NAT**: Allows apps to reach internet via management network
3. **Runs reverse proxy**: Optional Caddy/nginx for unified access
4. **Enables DNS**: Forwards DNS queries for app discovery

### Configuration

**Network Interfaces:**
- `eth0`: Connected to vmbr0 (management) - DHCP
- `eth1`: Connected to proximity-lan (apps) - Static 10.10.0.1/24

**Services:**
- IP forwarding enabled
- iptables NAT rules
- Optional: Caddy reverse proxy
- Optional: DNS forwarding

**Resource Requirements:**
- CPU: 1 core
- Memory: 512 MB
- Storage: 4 GB
- Privileged: No (unprivileged container)

### Automatic Deployment

```python
# Router is automatically deployed during network initialization
network_manager = NetworkManagerV2(proxmox_service)
await network_manager.initialize()

# Router LXC (VMID 100) created and configured automatically
# - IP forwarding enabled
# - NAT rules configured
# - Ready to route traffic
```

## Network Modes

### Mode 1: Development (macOS/Windows)

**When:** Running on non-Linux development machine

**Behavior:**
- Network setup skipped
- Uses default Proxmox networking (vmbr0)
- Containers get DHCP from LAN
- No isolation

**Use Case:** Development and testing

### Mode 2: Simple (Single Bridge)

**When:** Only one bridge available (vmbr0)

**Behavior:**
- Uses vmbr0 for all containers
- DHCP from LAN
- No isolation
- Fallback mode

**Use Case:** Simple deployments, testing

### Mode 3: Isolated (proximity-lan) ⭐ **RECOMMENDED**

**When:** Running on Linux/Proxmox (automatic)

**Behavior:**
- Management on vmbr0
- Apps on proximity-lan (isolated)
- Private DHCP/DNS (10.10.0.0/24)
- Router LXC provides connectivity
- Full isolation

**Use Case:** Production deployments, security-focused setups

## DHCP/DNS Service

### Configuration

**Network:** 10.10.0.0/24  
**Gateway:** 10.10.0.1 (Router LXC)  
**DHCP Range:** 10.10.0.100 - 10.10.0.250  
**DNS Domain:** prox.local  
**Lease Time:** 12 hours

### DNS Resolution

Apps can reach each other by hostname:

```bash
# Inside a container
ping nginx-01.prox.local
curl http://wordpress-02.prox.local
```

### dnsmasq Configuration

Located at: `/etc/proximity/dnsmasq.conf`

```ini
# Interface
interface=proximity-lan

# DHCP
dhcp-range=10.10.0.100,10.10.0.250,12h

# DNS
domain=prox.local
local=/prox.local/

# Upstream
server=1.1.1.1
server=8.8.8.8

# Options
dhcp-option=option:router,10.10.0.1
dhcp-option=option:dns-server,10.10.0.1
```

## API Integration

### Network Status Endpoint

```http
GET /api/v1/system/network/status

Response:
{
  "management_bridge": "vmbr0",
  "app_bridge": "proximity-lan",
  "isolated_network": true,
  "router_deployed": true,
  "app_network_subnet": "10.10.0.0/24",
  "app_network_gateway": "10.10.0.1",
  "dhcp_range": "10.10.0.100-10.10.0.250",
  "dns_domain": "prox.local"
}
```

### Container Provisioning

```python
# Automatic network selection based on detected configuration
net_config = await network_manager.get_container_network_config("nginx-01")
# Returns: "name=eth0,bridge=proximity-lan,ip=dhcp,firewall=1"

# Container automatically:
# - Gets IP via DHCP (e.g., 10.10.0.105)
# - Registers hostname in DNS (nginx-01.prox.local)
# - Can reach other apps and internet
```

## Migration Guide

### From V1 (Simple) to V2 (Isolated)

**Prerequisites:**
1. Proxmox host running on Linux
2. Root access to Proxmox host
3. NetworkManagerV2 enabled

**Migration Steps:**

1. **Backup current state:**
   ```bash
   # Backup container list
   pct list > /root/proximity-containers-backup.txt
   ```

2. **Enable V2 Network Manager:**
   ```python
   # In main.py
   from services.network_manager_v2 import NetworkManagerV2
   
   network_manager = NetworkManagerV2(proxmox_service)
   await network_manager.initialize()
   ```

3. **Let Proximity detect bridges:**
   - Start Proximity API
   - Check logs for bridge detection
   - Verify router LXC deployment

4. **Deploy new apps:**
   - New apps automatically use isolated network
   - Get IPs in 10.10.0.0/24 range

5. **Migrate existing apps (optional):**
   ```bash
   # Stop container
   pct stop 106
   
   # Change network to proximity-lan
   pct set 106 -net0 name=eth0,bridge=proximity-lan,ip=dhcp,firewall=1
   
   # Start container
   pct start 106
   ```

## Troubleshooting

### Bridge Detection Issues

**Problem:** proximity-lan bridge not created

**Solution:**
```bash
# Check if proximity-lan exists
ip link show proximity-lan

# If not, check logs
tail -f /var/log/proximity/network.log

# Manual creation (if needed):
ip link add name proximity-lan type bridge
ip addr add 10.10.0.1/24 dev proximity-lan
ip link set proximity-lan up

# Make persistent:
nano /etc/network/interfaces

# Add:
auto proximity-lan
iface proximity-lan inet static
        address 10.10.0.1/24
        bridge-ports none
        bridge-stp off
        bridge-fd 0

# Apply
ifreload -a
```

### Router LXC Issues

**Problem:** Router not routing traffic

**Check IP forwarding:**
```bash
pct exec 100 -- sysctl net.ipv4.ip_forward
# Should return: net.ipv4.ip_forward = 1
```

**Check NAT rules:**
```bash
pct exec 100 -- iptables -t nat -L -n -v
# Should see MASQUERADE rule
```

**Check connectivity:**
```bash
# From router
pct exec 100 -- ping 8.8.8.8

# From app container
pct exec 106 -- ping 8.8.8.8
```

### DHCP Issues

**Problem:** Containers not getting IP

**Check dnsmasq:**
```bash
systemctl status proximity-dns
journalctl -u proximity-dns -f
```

**Check DHCP leases:**
```bash
cat /var/lib/proximity/dnsmasq.leases
```

**Manual DHCP request:**
```bash
pct exec 106 -- dhclient -v eth0
```

## Security Benefits

### Network Isolation

✅ **Apps not exposed to LAN**
- Apps only accessible via router LXC
- No direct LAN connectivity
- Reduced attack surface

✅ **Firewall ready**
- Each bridge can have iptables rules
- Container firewall enabled (`firewall=1`)
- Fine-grained access control

✅ **Private DNS**
- App hostnames not in LAN DNS
- Internal service discovery
- No DNS leakage

### Best Practices

1. **Use proximity-lan bridge** for all app containers
2. **Keep router LXC minimal** - only essential services
3. **Enable firewall** on all network interfaces
4. **Monitor router logs** for suspicious traffic
5. **Regular security updates** for router LXC

## Performance Considerations

### Router LXC Overhead

- **CPU:** < 1% idle, ~5% under load
- **Memory:** ~50 MB used
- **Network:** Near line-rate (minimal overhead)
- **Latency:** +1-2ms compared to direct

### Scaling

- **Containers:** 150+ (DHCP pool size)
- **Throughput:** Limited by bridge, not router
- **Concurrent connections:** Thousands

### Optimization Tips

1. Pin router LXC to dedicated CPU core
2. Use virtio network drivers
3. Enable jumbo frames if needed
4. Monitor router resource usage

## Future Enhancements

### Planned Features

- [ ] Multiple isolated networks (dev/staging/prod)
- [ ] IPv6 support with DHCPv6
- [ ] Built-in reverse proxy in router
- [ ] Load balancing across app instances
- [ ] VPN access to isolated network
- [ ] Network traffic analytics
- [ ] Automatic backup network configuration
- [ ] GUI for network topology visualization

## References

- [Proxmox Network Configuration](https://pve.proxmox.com/wiki/Network_Configuration)
- [Linux Bridge Documentation](https://wiki.linuxfoundation.org/networking/bridge)
- [dnsmasq Manual](https://thekelleys.org.uk/dnsmasq/docs/dnsmasq-man.html)
- [iptables NAT](https://www.netfilter.org/documentation/HOWTO/NAT-HOWTO.html)

---

**Proximity Network Architecture V2** - Intelligent, Secure, Automated
