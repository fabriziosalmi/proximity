# Network Appliance Architecture

**Date:** 8 October 2025  
**Component:** Network Appliance (prox-appliance)  
**Purpose:** Dual-homed network gateway for application isolation and management

## Overview

The Proximity Network Appliance is a specialized Alpine Linux LXC container that provides:
- **Network isolation** for deployed applications
- **DHCP/DNS services** for automatic IP assignment
- **NAT gateway** for internet access
- **Reverse proxy** (Caddy) for unified application access

## Network Interfaces

### 🌍 WAN Interface (eth0)

**Purpose:** External network connectivity and management access

```
Interface:     eth0
Bridge:        vmbr0 (Proxmox default bridge)
IP Address:    DHCP assigned (e.g., 192.168.100.2)
Network:       External/Management network
Configuration: Dynamic (DHCP client)
Access:        SSH, management, internet gateway
```

**Key Features:**
- ✅ DHCP client - automatically gets IP from your router/DHCP server
- ✅ Connected to the same network as Proxmox host
- ✅ Provides internet access for NAT gateway functionality
- ✅ SSH access for management: `ssh root@<WAN_IP>`

### 🔌 LAN Interface (eth1)

**Purpose:** Gateway for isolated application network

```
Interface:     eth1
Bridge:        proximity-lan (isolated virtual bridge)
IP Address:    10.20.0.1/24 (static)
Network:       Internal application network
Configuration: Static (gateway)
Services:      DHCP server, DNS server, NAT gateway
```

**Key Features:**
- ✅ Static IP - always 10.20.0.1
- ✅ Acts as gateway for all deployed applications
- ✅ Provides DHCP range: 10.20.0.100 - 10.20.0.250
- ✅ DNS domain: .prox.local
- ✅ NAT masquerading to WAN interface

## Network Flow

### Application Internet Access

```
Application Container (10.20.0.x)
    ↓
    eth0 → proximity-lan bridge
    ↓
Appliance eth1 (10.20.0.1) - receives packet
    ↓
    NAT (iptables MASQUERADE)
    ↓
Appliance eth0 (192.168.100.2) - sends to WAN
    ↓
    vmbr0 → External Network → Internet
```

### Management Access

```
Your Computer
    ↓
External Network (e.g., 192.168.100.0/24)
    ↓
Proxmox vmbr0
    ↓
Appliance eth0 (192.168.100.2)
    ↓
SSH/HTTP access to appliance
```

### Application Deployment

When you deploy an application:

1. **Container Creation**
   ```
   App Container: nginx-001
   Network: name=eth0,bridge=proximity-lan,ip=dhcp
   ```

2. **DHCP Assignment**
   ```
   Appliance dnsmasq assigns:
   - IP: 10.20.0.130
   - Gateway: 10.20.0.1
   - DNS: 10.20.0.1
   - Domain: nginx-001.prox.local
   ```

3. **DNS Registration**
   ```
   Appliance DNS resolves:
   nginx-001.prox.local → 10.20.0.130
   ```

4. **Reverse Proxy**
   ```
   Caddy on appliance creates vhost:
   http://<appliance-wan-ip>/nginx-001 → http://10.20.0.130:80
   ```

## Configuration Details

### Proxmox LXC Config

```bash
# View appliance network config
pct config 9999 | grep net

# Output:
net0: name=eth0,bridge=vmbr0,firewall=1,hwaddr=XX:XX:XX:XX:XX:XX,ip=dhcp,type=veth
net1: name=eth1,bridge=proximity-lan,firewall=1,hwaddr=XX:XX:XX:XX:XX:XX,ip=10.20.0.1/24,type=veth
```

### Inside Appliance

```bash
# SSH into appliance
ssh root@192.168.100.2  # Use your WAN IP

# Check interfaces
ip addr show

# Output:
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    inet 127.0.0.1/8

2: eth0@if57: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 192.168.100.2/24 brd 192.168.100.255 scope global dynamic eth0

3: eth1@if58: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 10.20.0.1/24 brd 10.20.0.255 scope global eth1
```

### NAT Configuration

```bash
# Check NAT rules
iptables -t nat -L POSTROUTING -n -v

# Output:
Chain POSTROUTING (policy ACCEPT)
target     prot opt source               destination
MASQUERADE all  --  0.0.0.0/0            0.0.0.0/0
```

This rule masquerades all traffic from LAN (10.20.0.0/24) to appear as coming from WAN IP (192.168.100.2).

### DHCP/DNS Configuration

```bash
# View dnsmasq config
cat /etc/dnsmasq.conf

# Key settings:
interface=eth1
bind-interfaces
dhcp-range=10.20.0.100,10.20.0.250,255.255.255.0,12h
dhcp-option=option:router,10.20.0.1
dhcp-option=option:dns-server,10.20.0.1
domain=prox.local
expand-hosts
```

## Network Isolation Benefits

### Security
- ✅ Applications isolated from management network
- ✅ Single gateway point for all application traffic
- ✅ Centralized firewall and NAT rules
- ✅ No direct external network access for apps

### Management
- ✅ Centralized DHCP/DNS for all applications
- ✅ Automatic IP assignment and DNS registration
- ✅ Easy to monitor all application network traffic
- ✅ Single reverse proxy for all applications

### Flexibility
- ✅ Easy to add new applications (just DHCP)
- ✅ No IP conflicts (DHCP managed)
- ✅ Can easily change external network without affecting apps
- ✅ Portable between different Proxmox nodes

## Troubleshooting

### Check WAN Connectivity

```bash
# From appliance
ping -c 3 8.8.8.8          # Internet connectivity
ping -c 3 google.com       # DNS resolution
ip route show              # Check default route
```

### Check LAN Connectivity

```bash
# From appliance
ip addr show eth1          # Should show 10.20.0.1/24
ip link show proximity-lan # Check bridge status
cat /var/lib/misc/dnsmasq.leases  # Check DHCP leases
```

### Check NAT

```bash
# From appliance
iptables -t nat -L -n -v   # Check NAT rules
cat /proc/sys/net/ipv4/ip_forward  # Should be 1
```

### Test from Application Container

```bash
# SSH into any app container
pct enter <vmid>

# Check network
ip addr show eth0          # Should show 10.20.0.x
ip route show              # Default via 10.20.0.1
ping -c 3 10.20.0.1       # Ping gateway
ping -c 3 8.8.8.8         # Test internet via NAT
```

## API Integration

### Get Infrastructure Status

```bash
curl http://localhost:8765/api/v1/system/infrastructure/status \
  -H "Authorization: Bearer <token>" | jq .
```

**Response includes:**
```json
{
  "appliance": {
    "wan_ip": "192.168.100.2",
    "wan_interface": "eth0",
    "lan_ip": "10.20.0.1",
    "lan_interface": "eth1"
  },
  "network": {
    "bridge_name": "proximity-lan",
    "network": "10.20.0.0/24",
    "gateway": "10.20.0.1",
    "dhcp_range": "10.20.0.100 - 10.20.0.250"
  },
  "services": {
    "dnsmasq": "running",
    "caddy": "running",
    "iptables": "running"
  }
}
```

## Summary

The Network Appliance uses a **dual-homed architecture**:

| Interface | Purpose | Network | IP Assignment | Role |
|-----------|---------|---------|---------------|------|
| **eth0 (WAN)** | External connectivity | vmbr0 | DHCP | Management, Internet |
| **eth1 (LAN)** | Application network | proximity-lan | Static 10.20.0.1 | Gateway, DHCP/DNS server |

This design provides:
- ✅ Clean separation between management and application networks
- ✅ Automatic IP assignment for applications
- ✅ Centralized network services (DHCP, DNS, NAT, Proxy)
- ✅ Easy management and troubleshooting
- ✅ Scalable architecture for many applications

---

**Related Documentation:**
- `BUGFIX_INFRASTRUCTURE_TOKEN.md` - UI token fix
- `BUGFIX_CADDY_SERVICE.md` - Reverse proxy setup
- `deployment.md` - Full deployment guide
