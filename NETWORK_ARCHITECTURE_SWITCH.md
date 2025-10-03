# Network Architecture Switch - Basic to Platinum Edition

## Overview

Switched the default networking mode from **basic vmbr0 networking** to **Platinum Edition isolated networking with proximity-lan bridge and network appliance**.

---

## Changes Made

### 1. ✅ Updated main.py Startup Sequence

**File:** `backend/main.py`

**Before (Basic Networking):**
```python
# Step 1: Initialize Network Infrastructure
from services.network_manager import NetworkManager
network_manager = NetworkManager()
network_init_success = await network_manager.initialize()
proxmox_service.network_manager = network_manager

# Step 4: Deploy Caddy proxy in background
# Separate Caddy LXC deployment...
```

**After (Platinum Edition):**
```python
# Step 1: Initialize Proxmox Connection
from services.proxmox_service import proxmox_service
is_connected = await proxmox_service.test_connection()

# Step 2: Initialize Network Appliance (Platinum Edition with proximity-lan)
from services.network_appliance_orchestrator import NetworkApplianceOrchestrator
orchestrator = NetworkApplianceOrchestrator(proxmox_service)
network_init_success = await orchestrator.initialize()

# Inject orchestrator into ProxmoxService for network config
proxmox_service.network_manager = orchestrator

# Step 4: Initialize Reverse Proxy Manager (integrated with Network Appliance)
from services.reverse_proxy_manager import ReverseProxyManager
proxy_manager = ReverseProxyManager(
    proxmox_service=proxmox_service,
    appliance_vmid=orchestrator.appliance_info.vmid
)
```

**Benefits:**
- ✅ Single network appliance LXC (VMID 100) instead of multiple separate LXCs
- ✅ Integrated Caddy reverse proxy running inside the appliance
- ✅ DHCP/DNS services provided by appliance
- ✅ NAT routing through appliance
- ✅ Optional Cockpit management UI on port 9090

---

### 2. ✅ Added Network Config Method to Orchestrator

**File:** `backend/services/network_appliance_orchestrator.py`

**New Method:**
```python
async def get_container_network_config(self, hostname: str) -> str:
    """
    Get network configuration string for a container to be deployed.
    
    This method provides compatibility with ProxmoxService's network_manager interface.
    Returns a network configuration string that connects the container to proximity-lan bridge.
    
    Args:
        hostname: Hostname for the container (used for logging)
        
    Returns:
        str: Network configuration string (e.g., "name=eth0,bridge=proximity-lan,ip=dhcp")
    """
    if not self.appliance_info:
        logger.warning(f"Network appliance not initialized for {hostname}, using default bridge")
        return "name=eth0,bridge=vmbr0,ip=dhcp,firewall=1"
    
    # Container connects to proximity-lan bridge with DHCP
    # The appliance's dnsmasq will assign IP addresses from 10.20.0.100-250
    net_config = f"name=eth0,bridge={self.bridge_name},ip=dhcp,firewall=1"
    
    logger.info(f"Container {hostname} will use proximity-lan network (DHCP-managed)")
    
    return net_config
```

**Purpose:**
- Provides interface compatibility with ProxmoxService
- Returns network config string for deployed containers
- Connects containers to proximity-lan bridge
- DHCP assigns IPs from 10.20.0.100-250

---

### 3. ✅ ProxmoxService Integration

**File:** `backend/services/proxmox_service.py`

**Existing Code (No changes needed):**
```python
# In create_lxc():
if self.network_manager:
    net_config = await self.network_manager.get_container_network_config(hostname)
    logger.info(f"Using managed network config: {net_config}")
else:
    # Fallback to default bridge (vmbr0) with DHCP
    net_config = "name=eth0,bridge=vmbr0,ip=dhcp,firewall=1"
    logger.warning(f"NetworkManager not available - using default bridge (vmbr0)")
```

**Behavior:**
- ProxmoxService calls `network_manager.get_container_network_config()`
- With orchestrator injected, it gets proximity-lan config
- Without orchestrator, falls back to vmbr0

---

## Network Architecture

### Platinum Edition (NEW DEFAULT)

```
┌─────────────────────────────────────────────────────────────┐
│ Proxmox Host (192.168.1.x)                                   │
│                                                               │
│  ┌──────────────┐                     ┌──────────────┐      │
│  │ vmbr0        │◄────────────────────┤ WAN Router   │      │
│  │ (Management) │                     │ (Internet)   │      │
│  └──────┬───────┘                     └──────────────┘      │
│         │                                                    │
│         │                                                    │
│  ┌──────▼────────────────────────────────────────────┐      │
│  │ Network Appliance LXC (VMID 100)                  │      │
│  │                                                    │      │
│  │  • Hostname: prox-appliance                       │      │
│  │  • eth0: vmbr0 (192.168.1.x) - WAN/Management    │      │
│  │  • eth1: proximity-lan (10.20.0.1) - LAN Gateway │      │
│  │                                                    │      │
│  │  Services Running:                                │      │
│  │  ✓ dnsmasq (DHCP 10.20.0.100-250, DNS .prox.local) │  │
│  │  ✓ iptables NAT (MASQUERADE to WAN)              │      │
│  │  ✓ Caddy Reverse Proxy (port 8080)               │      │
│  │  ✓ Cockpit Management UI (port 9090)             │      │
│  └──────┬─────────────────────────────────────────────┘      │
│         │ eth1 (10.20.0.1/24)                               │
│         │                                                    │
│  ┌──────▼───────┐                                           │
│  │ proximity-lan│  (10.20.0.0/24 Isolated Network)         │
│  │ Bridge       │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│    ┌────┴───────────────────────────────────┐              │
│    │                                         │              │
│  ┌─▼──────────────┐  ┌──────────────┐  ┌───▼───────────┐  │
│  │ App LXC 1      │  │ App LXC 2    │  │ App LXC N     │  │
│  │ nginx-01       │  │ wordpress    │  │ portainer     │  │
│  │ 10.20.0.101    │  │ 10.20.0.102  │  │ 10.20.0.103   │  │
│  │ eth0: DHCP     │  │ eth0: DHCP   │  │ eth0: DHCP    │  │
│  └────────────────┘  └──────────────┘  └───────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Traffic Flow:
1. Internet → vmbr0 → Appliance eth0 (WAN)
2. Appliance NAT → Appliance eth1 (LAN Gateway 10.20.0.1)
3. App containers get IPs via DHCP (10.20.0.100-250)
4. Apps access Internet through Appliance NAT
5. External access via Caddy reverse proxy on Appliance
```

---

## Startup Sequence

### New Startup Flow:

```
1. Connect to Proxmox API
   ↓
2. Initialize Network Appliance Orchestrator
   ├── Create proximity-lan bridge on host
   ├── Provision Network Appliance LXC (VMID 100)
   │   ├── Dual NICs: eth0 (vmbr0), eth1 (proximity-lan)
   │   ├── Install dnsmasq (DHCP/DNS)
   │   ├── Configure iptables NAT
   │   ├── Install Caddy reverse proxy
   │   └── Install Cockpit management UI
   ├── Verify health
   └── Inject orchestrator into proxmox_service
   ↓
3. Load Application Catalog
   ↓
4. Initialize Reverse Proxy Manager
   └── Configure for Caddy on appliance VMID 100
```

---

## Container Deployment Flow

### When deploying a new app:

1. **ProxmoxService.create_lxc()** is called
2. Calls `orchestrator.get_container_network_config(hostname)`
3. Gets: `"name=eth0,bridge=proximity-lan,ip=dhcp,firewall=1"`
4. Creates LXC with this network config
5. Container boots and gets IP from appliance's DHCP (10.20.0.100-250)
6. Container automatically gets DNS name: `<hostname>.prox.local`
7. **ReverseProxyManager** creates Caddy vhost on appliance
8. App becomes accessible via: `http://<appliance-ip>/<app-name>`

---

## Network Details

| Component | Value |
|-----------|-------|
| **Bridge Name** | proximity-lan |
| **Network CIDR** | 10.20.0.0/24 |
| **Gateway IP** | 10.20.0.1 |
| **DHCP Range** | 10.20.0.100 - 10.20.0.250 |
| **Available IPs** | 151 addresses |
| **DNS Domain** | .prox.local |
| **Appliance VMID** | 100 |
| **Appliance Hostname** | prox-appliance |
| **Reverse Proxy Port** | 8080 |
| **Management UI Port** | 9090 |

---

## Benefits of Platinum Edition

### Security:
- ✅ **Isolated Network**: Apps run on separate network (10.20.0.0/24)
- ✅ **NAT Firewall**: All traffic filtered through appliance
- ✅ **Controlled Access**: Apps can't directly access management network

### Networking:
- ✅ **Automatic DHCP**: IP addresses auto-assigned
- ✅ **DNS Resolution**: Apps accessible by hostname.prox.local
- ✅ **Unified Proxy**: Single Caddy instance for all apps
- ✅ **Dynamic Vhosts**: Reverse proxy config auto-updated

### Operations:
- ✅ **Centralized Management**: Cockpit UI for appliance monitoring
- ✅ **Smart Cleanup**: Infrastructure removed when last app deleted
- ✅ **Auto-Reinit**: Infrastructure recreated on first deployment
- ✅ **Health Monitoring**: Service status tracking via API

### Scalability:
- ✅ **150+ Apps**: Support for 151 simultaneous apps
- ✅ **Resource Efficient**: Single appliance LXC vs multiple LXCs
- ✅ **Easy Expansion**: Just deploy more apps

---

## Fallback Behavior

If network appliance initialization fails:

```python
if not network_init_success:
    logger.warning("⚠️  Network appliance initialization failed")
    logger.info("ℹ️  Containers will use default Proxmox networking (vmbr0)")
    orchestrator = None
```

**Result:**
- ProxmoxService detects `network_manager == None`
- Falls back to: `"name=eth0,bridge=vmbr0,ip=dhcp,firewall=1"`
- Apps get deployed on default vmbr0 bridge
- Direct network access (no isolation)
- No reverse proxy integration

---

## API Changes

### New Endpoint Available:

**GET** `/api/v1/system/infrastructure/status`

Returns comprehensive infrastructure status:
```json
{
  "appliance": {
    "vmid": 100,
    "hostname": "prox-appliance",
    "status": "running",
    "wan_ip": "192.168.1.150",
    "lan_ip": "10.20.0.1",
    "management_url": "http://192.168.1.150:9090"
  },
  "bridge": {
    "name": "proximity-lan",
    "exists": true,
    "status": "UP"
  },
  "network": {
    "network": "10.20.0.0/24",
    "gateway": "10.20.0.1",
    "dhcp_range": "10.20.0.100 - 10.20.0.250"
  },
  "services": {
    "dnsmasq": {"status": "running", "healthy": true},
    "iptables": {"status": "running", "healthy": true},
    "caddy": {"status": "running", "healthy": true},
    "cockpit": {"status": "stopped", "healthy": false}
  },
  "applications": [
    {"ip": "10.20.0.101", "hostname": "nginx-01", "dns_name": "nginx-01.prox.local"}
  ],
  "health_status": "healthy"
}
```

---

## Migration from Basic to Platinum

**No migration needed!**

- Old deployments on vmbr0 continue to work
- New deployments automatically use proximity-lan
- Both modes can coexist
- Clean slate on next fresh deployment

---

## Testing Checklist

- [ ] Backend starts successfully
- [ ] Network appliance initialized
- [ ] proximity-lan bridge created
- [ ] Appliance LXC (VMID 100) running
- [ ] All 4 services running in appliance
- [ ] New app deployments use proximity-lan
- [ ] Apps get DHCP addresses (10.20.0.100-250)
- [ ] DNS resolution works (hostname.prox.local)
- [ ] Reverse proxy vhosts created automatically
- [ ] Apps accessible via proxy URL
- [ ] Infrastructure status API works
- [ ] Smart cleanup works on last app deletion
- [ ] Auto-reinit works on next deployment

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/main.py` | • Replaced NetworkManager with NetworkApplianceOrchestrator<br>• Updated startup sequence<br>• Replaced Caddy service with ReverseProxyManager<br>• Added orchestrator injection into proxmox_service |
| `backend/services/network_appliance_orchestrator.py` | • Added get_container_network_config() method<br>• Provides ProxmoxService compatibility |

---

## Environment Variables

**No changes needed to .env file!**

The system automatically:
- Detects best Proxmox node
- Creates proximity-lan bridge
- Provisions appliance
- Configures all services

---

**Status:** ✅ Platinum Edition networking is now the default mode

**Date:** October 3, 2025

---

## Troubleshooting

### If appliance initialization fails:

1. Check Proxmox connection
2. Verify Alpine template available
3. Check bridge creation permissions
4. Review logs for specific errors
5. System falls back to vmbr0 automatically

### Manual cleanup if needed:

```bash
# SSH to Proxmox host
ssh root@<proxmox-host>

# Check appliance status
pct status 100

# Check bridge
ip link show proximity-lan

# Check services in appliance
pct exec 100 -- rc-service dnsmasq status
pct exec 100 -- rc-service iptables status
pct exec 100 -- rc-service caddy status
pct exec 100 -- rc-service cockpit status

# View DHCP leases
pct exec 100 -- cat /var/lib/misc/dnsmasq.leases
```
