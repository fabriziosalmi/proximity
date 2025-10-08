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
- `PortManagerService`: Manages sequential port allocation for public and internal proxy access
- `NetworkApplianceOrchestrator`: Manages network appliance and bridge provisioning
- `ReverseProxyManager`: Configures Caddy reverse proxy with port-based architecture
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
- **Management UI**: Webmin on port 10000

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

**Port-Based Architecture (Platinum Edition v2.0)**

Proximity uses a modern **port-based reverse proxy architecture** that assigns each application two dedicated ports:

- **Public Port (30000-30999)**: Standard external access with full security headers
- **Internal Port (40000-40999)**: iframe-embeddable access with stripped frame-busting headers for In-App Canvas

#### Port Allocation

The `PortManagerService` manages sequential port allocation:

- **Sequential Assignment**: Ports assigned sequentially starting from range minimum
- **Database-Backed**: Port assignments stored in database with unique constraints
- **Automatic Recycling**: Released ports become available for reuse
- **Conflict Prevention**: Unique constraints prevent port collisions

**Port Ranges (Configurable):**
```python
PUBLIC_PORT_RANGE: 30000-30999 (1000 ports)
INTERNAL_PORT_RANGE: 40000-40999 (1000 ports)
```

#### Access Methods

Applications are accessible via:

1. **Port-Based Public Access**: `http://<appliance-ip>:<public_port>`
   - Full security headers preserved
   - Standard HTTP/HTTPS access
   - Example: `http://10.20.0.10:30001`

2. **Port-Based Canvas Access**: `http://<appliance-ip>:<internal_port>`
   - X-Frame-Options header stripped (allows iframe embedding)
   - Content-Security-Policy header stripped
   - Used by In-App Canvas feature
   - Example: `http://10.20.0.10:40001`

3. **DNS Access** (Optional): `http://{hostname}.prox.local`
   - Requires DNS/hosts file configuration
   - Maps hostname to container IP

4. **Direct Access**: `http://<container-ip>:<container-port>`
   - Bypass reverse proxy entirely
   - Useful for debugging

#### Caddy Configuration

The `ReverseProxyManager` generates port-based Caddy configurations:

**Example Generated Configuration:**
```
# Port-based virtual host for myapp
# Platinum Edition v2.0 - Port-Based Architecture

# Public Access (Port 30001)
:30001 {
    reverse_proxy http://10.20.0.100:80 {
        header_up Host {upstream_hostport}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}

# Internal Canvas Access (Port 40001)
:40001 {
    reverse_proxy http://10.20.0.100:80 {
        header_up Host {upstream_hostport}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
        
        # Strip frame-busting headers for iframe embedding
        header_down -X-Frame-Options
        header_down -Content-Security-Policy
    }
}
```

**Key Features:**
- ✅ No path-based routing (`handle_path` removed)
- ✅ No prefix stripping complexities
- ✅ Each app gets dedicated ports
- ✅ Simplified proxy configuration
- ✅ Better iframe security control
- ✅ Scalable up to 1000 concurrent apps per port range

#### In-App Canvas Integration

The **In-App Canvas** feature uses the internal port for secure iframe embedding:

```javascript
// Frontend canvas rendering
const canvasUrl = app.iframe_url; // http://10.20.0.10:40001
const iframe = document.createElement('iframe');
iframe.src = canvasUrl;
iframe.sandbox = 'allow-same-origin allow-scripts allow-forms';
```

#### Migration from Path-Based Architecture

**Legacy (Pre-v2.0):**
- Path-based routing: `http://appliance/app-name`
- Path-based canvas: `http://appliance/proxy/internal/app-name`
- Complex prefix stripping with `handle_path`

**Current (v2.0+):**
- Port-based routing: `http://appliance:30001`
- Port-based canvas: `http://appliance:40001`
- Clean, dedicated port blocks
- No path manipulation required

### Container Deployment Flow

When deploying an application:

1. **Port Assignment**: PortManagerService assigns unique public and internal ports (e.g., 30001, 40001)
2. **Template Download**: Alpine template cached on Proxmox node
3. **Container Creation**: LXC created with single NIC on `proximity-lan`
4. **Network Bootstrap**: Container receives IP via DHCP from appliance
5. **DNS Registration**: dnsmasq assigns `{hostname}.prox.local` DNS entry
6. **Proxy Configuration**: Caddy vhost created with dedicated ports for public and canvas access
7. **Health Check**: System verifies container and services are running
8. **Database Update**: App record updated with assigned ports and access URLs

### Management & Monitoring

**Webmin Management UI** (Port 10000):
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
