# Proximity Architecture

This document provides a comprehensive overview of Proximity's architecture, including the evolution of the network infrastructure.

## Table of Contents

- [System Architecture](#system-architecture)
- [Network Architecture](#network-architecture)
- [Network Evolution](#network-evolution)
- [Platinum Edition Features](#platinum-edition-features)

---

## System Architecture

Proximity is a self-hosted application delivery platform built on Proxmox VE that enables automated deployment and management of containerized applications.

### Core Components

#### 1. Backend API (FastAPI)
- RESTful API for application management
- JWT-based authentication with role-based access control
- Real-time deployment status tracking
- Proxmox VE integration via proxmoxer

**Key Services:**
- `ProxmoxService`: Manages LXC container lifecycle, networking, and Proxmox API interactions
- `AppService`: Handles application catalog, deployment, and state management
- `NetworkApplianceOrchestrator`: Manages network appliance and bridge provisioning
- `ReverseProxyManager`: Configures Caddy reverse proxy for deployed applications
- `SafeCommandService`: Executes pre-configured safe commands in containers

#### 2. Frontend UI
- Modern, responsive web interface built with vanilla JavaScript
- Real-time application monitoring
- Interactive deployment wizard
- System health dashboard

#### 3. Database (SQLite)
- Application registry and deployment metadata
- User authentication and authorization
- Audit logging for security compliance
- Configuration settings

### Technology Stack

**Backend:**
- FastAPI (Python 3.13+)
- Proxmoxer (Proxmox API client)
- SQLAlchemy (ORM)
- JWT authentication
- Paramiko (SSH operations)

**Frontend:**
- Vanilla JavaScript (ES6+)
- Lucide Icons
- CSS Grid/Flexbox

**Infrastructure:**
- Proxmox VE 8.x
- LXC Containers (Alpine Linux base)
- Caddy (reverse proxy)
- Linux Bridge networking

---

## Network Architecture

Proximity uses an isolated network architecture to provide secure, managed networking for deployed applications.

### Overview

The platform implements a **Platinum Edition** network architecture featuring:

1. **Isolated Bridge Network** (`proximity-lan`)
   - Dedicated Layer 2 bridge for container networking
   - Subnet: `10.20.0.0/24`
   - No direct internet access (controlled through appliance)

2. **Network Appliance** (LXC Container)
   - Dual-NIC configuration for routing
   - Built-in DHCP server for container IP allocation
   - DNS server with `.prox.local` domain
   - Caddy reverse proxy for HTTP/HTTPS routing
   - NAT gateway for outbound connectivity

3. **Deployed Containers**
   - Single NIC connected to `proximity-lan`
   - DHCP-assigned IPs from appliance
   - DNS resolution via appliance
   - Reverse proxy access for web applications

### Network Topology

```
Internet
   ↓
[Proxmox Node: vmbr0 - WAN Interface]
   ↓
[Network Appliance Container VMID 9999]
   ├─ eth0: vmbr0 (WAN) - DHCP from network
   └─ eth1: proximity-lan (10.20.0.1/24) - Gateway
        ↓
   [proximity-lan Bridge]
        ↓
   ┌────────┴────────┬────────────┬─────────┐
   ↓                 ↓            ↓         ↓
[App 1]          [App 2]      [App 3]   [App N]
eth0: 10.20.0.100 10.20.0.101 10.20.0.102 ...
(DHCP from appliance)
```

### Network Appliance Configuration

The network appliance (VMID 9999) provides:

**Services:**
- **dnsmasq**: DHCP (10.20.0.100-250) + DNS server
- **Caddy**: Reverse proxy with automatic HTTPS
- **iptables**: NAT for outbound traffic
- **Management UI**: Cockpit on port 9090

**Network Interfaces:**
- `eth0` (WAN): Connected to `vmbr0`, DHCP-assigned public IP
- `eth1` (LAN): Connected to `proximity-lan`, static IP `10.20.0.1/24`

**Routing:**
```bash
# NAT for containers to access internet
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# IP forwarding enabled
sysctl net.ipv4.ip_forward=1
```

---

## Network Evolution

Proximity's network architecture has evolved through several iterations:

### Phase 1: Basic vmbr0 Networking
- All containers directly on `vmbr0`
- DHCP from external network
- No isolation or centralized management

### Phase 2: proximity-lan Bridge
- Introduced dedicated bridge for container isolation
- Manual DHCP configuration per container
- Improved security through network segregation

### Phase 3: Network Appliance v1
- First attempt at centralized network management
- Basic DHCP and DNS services
- Manual configuration required

### Phase 4: Platinum Edition (Current)
- Fully automated network appliance provisioning
- Integrated reverse proxy management
- Automatic DNS with `.prox.local` domain
- Seamless NAT and routing
- Management UI via Cockpit

**Key Improvements in Platinum:**
1. **Zero-Touch Networking**: Containers automatically get IP, DNS, and internet access
2. **Automatic Proxy Configuration**: Web apps automatically receive reverse proxy vhosts
3. **Persistent Configuration**: Bridge and appliance survive Proxmox reboots
4. **Fallback Mode**: Gracefully falls back to vmbr0 if appliance provisioning fails

---

## Platinum Edition Features

### Automated Appliance Provisioning

The `NetworkApplianceOrchestrator` handles:

1. **Bridge Creation**
   - Creates `proximity-lan` bridge on target Proxmox node
   - Persists configuration in `/etc/network/interfaces`
   - Automatically reloads network configuration

2. **Appliance Deployment**
   - Provisions Alpine Linux LXC container (VMID 9999)
   - Dual-NIC configuration (WAN + LAN)
   - Installs and configures dnsmasq, Caddy, iptables
   - Sets up NAT, DNS, DHCP automatically

3. **Service Management**
   - Health monitoring of appliance services
   - Automatic restart capabilities
   - Log aggregation for troubleshooting

### Reverse Proxy Integration

The `ReverseProxyManager` provides:

- **Automatic Vhost Creation**: When deploying web apps, Caddy vhosts are auto-configured
- **Domain Naming**: Apps are accessible at `{hostname}.prox.local`
- **Health Checks**: Monitors backend container availability
- **Dynamic Reconfiguration**: Updates proxy config on app deployment/removal

**Example Caddyfile:**
```
nginx-01.prox.local {
    reverse_proxy 10.20.0.100:80
}

wordpress-prod.prox.local {
    reverse_proxy 10.20.0.101:80
}
```

### Container Deployment Flow

When deploying an application:

1. **Template Download**: Alpine template cached on Proxmox node
2. **Container Creation**: LXC created with single NIC on `proximity-lan`
3. **Network Bootstrap**: Container receives IP via DHCP from appliance
4. **DNS Registration**: dnsmasq assigns `{hostname}.prox.local` DNS entry
5. **Proxy Configuration**: If web app, Caddy vhost created
6. **Health Check**: System verifies container and services are running

### Management & Monitoring

**Cockpit Management UI** (Port 9090):
- Real-time system metrics
- Service status monitoring
- Log viewing
- Terminal access

**API Endpoints:**
- `GET /api/v1/system/infrastructure/status` - Network appliance status
- `POST /api/v1/system/infrastructure/appliance/restart` - Restart services
- `GET /api/v1/system/infrastructure/appliance/logs` - View appliance logs
- `POST /api/v1/system/infrastructure/test-nat` - Test NAT connectivity
- `GET /api/v1/system/proxy/status` - Reverse proxy status

---

## Security Considerations

### Network Isolation
- Containers cannot directly access Proxmox management network
- All internet traffic goes through NAT gateway
- No inbound access unless via reverse proxy

### Authentication
- JWT-based API authentication
- Role-based access control (admin/user)
- Audit logging for all operations

### Container Security
- Unprivileged LXC containers
- AppArmor profiles
- Limited capabilities
- Resource quotas (CPU, RAM, disk)

---

## Troubleshooting

### Common Issues

**Appliance Not Starting:**
- Check if VMID 9999 already exists: `pct list | grep 9999`
- Verify bridge exists: `ip link show proximity-lan`
- Check appliance logs: `GET /api/v1/system/infrastructure/appliance/logs`

**Containers Not Getting IPs:**
- Verify dnsmasq is running: `pct exec 9999 -- rc-status`
- Check DHCP range: `pct exec 9999 -- cat /etc/dnsmasq.conf`
- Test from container: `pct exec <vmid> -- ip addr`

**Reverse Proxy Not Working:**
- Check Caddy status: `pct exec 9999 -- rc-status | grep caddy`
- Verify Caddyfile: `pct exec 9999 -- cat /etc/caddy/Caddyfile`
- Test proxy: `curl -H "Host: app.prox.local" http://10.20.0.1`

**Fallback to vmbr0:**
- If appliance provisioning fails, containers use `vmbr0` with DHCP
- Check logs for specific error: `journalctl -u proximity-api`

---

## Future Enhancements

- **IPv6 Support**: Dual-stack networking with DHCPv6
- **VLAN Segmentation**: Multiple isolated networks per project
- **VPN Integration**: WireGuard for remote access
- **Load Balancing**: HAProxy for multi-container apps
- **Certificate Management**: Automatic Let's Encrypt SSL
- **Network Policies**: Firewall rules per container
- **Monitoring**: Prometheus metrics and Grafana dashboards
