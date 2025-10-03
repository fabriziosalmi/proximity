# Proximity Network Architecture

## Overview

Proximity uses a multi-layer architecture for application deployment and access:

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Local Network)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ http://caddy-ip:8080/app-name
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              CADDY REVERSE PROXY (LXC)                      │
│              IP: 192.168.x.x                                │
│              Port: 8080 (HTTP)                              │
│              Role: Path-based routing                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Forwards to backend LXC IPs
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         APPLICATION LXC CONTAINERS                          │
│         ┌────────────────┐  ┌────────────────┐             │
│         │  nginx-01      │  │  wordpress-01  │             │
│         │  192.168.1.100 │  │  192.168.1.101 │             │
│         │  Port: 80      │  │  Port: 80      │             │
│         └────────┬───────┘  └────────┬───────┘             │
│                  │                    │                     │
│         ┌────────▼────────┐  ┌────────▼────────┐           │
│         │  Docker Engine  │  │  Docker Engine  │           │
│         │  ┌───────────┐  │  │  ┌───────────┐  │           │
│         │  │   Nginx   │  │  │  │WordPress  │  │           │
│         │  │Container  │  │  │  │Container  │  │           │
│         │  │ Port:80   │  │  │  │ Port:80   │  │           │
│         │  └───────────┘  │  │  └───────────┘  │           │
│         └─────────────────┘  └─────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Network Layers

### Layer 1: User Access (Browser)
- Users access applications via Caddy reverse proxy
- URL Format: `http://<caddy-ip>:8080/<app-name>`
- Example: `http://192.168.1.107:8080/nginx-01`

### Layer 2: Caddy Reverse Proxy (LXC Container)
- **Purpose**: Path-based routing to applications
- **LXC Container**: Alpine Linux with Caddy installed
- **Network**: Proxmox bridge network (vmbr0)
- **Ports**: 
  - 8080: HTTP proxy (main entry point)
  - 2019: Caddy admin API
  - 2020: Health check endpoint
- **Routing**: `/app-name/*` → `http://app-lxc-ip:port`

### Layer 3: Application LXC Containers
- **Purpose**: Isolated environments for each application
- **OS**: Alpine Linux (lightweight)
- **Docker Engine**: Runs Docker Compose inside LXC
- **Network**: Proxmox bridge network (vmbr0)
- **Ports**: Exposed on LXC network interface

### Layer 4: Docker Containers (Inside LXC)
- **Purpose**: Application containers
- **Ports**: Exposed to LXC host via port mapping
- **Example**: `ports: ["80:80"]` in docker-compose.yml

## Port Mapping Flow

For an Nginx application:

```
User Request: http://192.168.1.107:8080/nginx-01
                        ↓
Caddy (LXC 107):       :8080/nginx-01/*  →  192.168.1.100:80
                        ↓
Nginx LXC (106):       :80 (listening)
                        ↓
Docker Container:      :80 (inside LXC, mapped to LXC:80)
```

## Critical Requirements

### ✅ Docker Port Exposure

**IMPORTANT**: Docker containers MUST expose ports on the LXC host network!

**Correct Configuration** (in docker-compose.yml):
```yaml
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"      # ✅ Exposes container port 80 on LXC port 80
      - "443:443"    # ✅ Exposes container port 443 on LXC port 443
```

**Wrong Configuration**:
```yaml
services:
  nginx:
    image: nginx:latest
    expose:
      - "80"         # ❌ Only exposes within Docker network (not accessible from LXC)
```

### ✅ LXC Network Configuration

LXC containers must be on the same network as the Proxmox host:

- **Network Interface**: `net0` configured with bridge `vmbr0`
- **IP Assignment**: DHCP or static on local network
- **Accessibility**: LXC IPs must be reachable from Caddy LXC

### ✅ Caddy Configuration

Caddy uses path-based routing:

```caddyfile
:8080 {
    # Route for nginx-01
    handle_path /nginx-01/* {
        reverse_proxy 192.168.1.100:80
    }
    
    # Route for wordpress-01
    handle_path /wordpress-01/* {
        reverse_proxy 192.168.1.101:80
    }
}
```

## Access Methods

### Method 1: Via Caddy Reverse Proxy (Recommended)
- **URL**: `http://<caddy-ip>:8080/<app-name>`
- **Pros**: 
  - Single entry point for all apps
  - Path-based organization
  - Easy to remember
  - Works from local network
- **Example**: `http://192.168.1.107:8080/nginx-01`

### Method 2: Direct Access (Fallback)
- **URL**: `http://<lxc-ip>:<port>`
- **Pros**: Direct connection (no proxy overhead)
- **Cons**: 
  - Need to remember each LXC IP
  - No unified access point
- **Example**: `http://192.168.1.100:80`

## Troubleshooting

### Application shows "Access URL: IP not available"

**Causes**:
1. LXC doesn't have an IP (DHCP failed or network not started)
2. Container is still starting up
3. Network interface not ready

**Solutions**:
```bash
# Check LXC network status
pct exec <vmid> -- ip addr show

# Restart LXC networking
pct exec <vmid> -- rc-service networking restart

# Check if Docker is running
pct exec <vmid> -- docker ps
```

### Caddy shows "Offline" but is deployed

**Causes**:
1. Caddy service not started
2. LXC container stopped

**Solutions**:
```bash
# Check Caddy LXC status
pct status <vmid>

# Start Caddy service
pct exec <vmid> -- rc-service caddy start

# Check Caddy status
pct exec <vmid> -- rc-service caddy status
```

### Cannot access app via Caddy proxy

**Causes**:
1. Docker container not exposing ports on LXC network
2. Backend LXC IP changed
3. Caddy configuration not reloaded

**Solutions**:
```bash
# Check if port is listening on LXC
pct exec <lxc-vmid> -- netstat -tlnp | grep :<port>

# Check Docker port mapping
pct exec <lxc-vmid> -- docker compose ps

# Test direct access to backend
curl http://<lxc-ip>:<port>

# Check Caddy configuration
pct exec <caddy-vmid> -- cat /etc/caddy/Caddyfile

# Reload Caddy
pct exec <caddy-vmid> -- rc-service caddy reload
```

### Docker container not exposing ports

**Verify docker-compose.yml**:
```bash
# Check docker-compose file
pct exec <vmid> -- cat /root/docker-compose.yml

# Look for ports section
# Should have: ports: ["80:80"]  ✅
# NOT just:    expose: ["80"]    ❌
```

**Fix**:
1. Update catalog JSON with correct port mappings
2. Redeploy the application
3. Or manually edit docker-compose.yml and restart:
```bash
pct exec <vmid> -- cd /root && docker compose down
pct exec <vmid> -- cd /root && docker compose up -d
```

## Testing Connectivity

### Test 1: Check LXC IP
```bash
# From Proxmox host
pct exec <vmid> -- ip addr show eth0
```

### Test 2: Test Docker Port Exposure
```bash
# From Proxmox host - should respond
curl http://<lxc-ip>:<port>
```

### Test 3: Test Caddy Routing
```bash
# From local network - should respond
curl http://<caddy-ip>:8080/<app-name>/
```

### Test 4: Check Caddy Backend Configuration
```bash
# From Proxmox host
pct exec <caddy-vmid> -- cat /etc/caddy/Caddyfile
```

## Network Diagram (Detailed)

```
Proxmox Host (192.168.1.10)
├── vmbr0 (Bridge Network)
│   ├── Caddy LXC (107): 192.168.1.107
│   │   ├── eth0: 192.168.1.107
│   │   ├── Caddy Service: :8080, :2019, :2020
│   │   └── Routes: /nginx-01 → 192.168.1.100:80
│   │
│   ├── Nginx LXC (106): 192.168.1.100
│   │   ├── eth0: 192.168.1.100
│   │   ├── Port 80: Listening (Docker mapped)
│   │   └── Docker Container: nginx:latest
│   │       └── Internal Port 80 → LXC Port 80
│   │
│   └── WordPress LXC (108): 192.168.1.101
│       ├── eth0: 192.168.1.101
│       ├── Port 80: Listening (Docker mapped)
│       └── Docker Containers:
│           ├── wordpress:latest (80 → 80)
│           └── mysql:8.0 (3306 → 3306)
│
└── Local Network Router (192.168.1.1)
    └── User Devices
        └── Browser: http://192.168.1.107:8080/nginx-01
```

## Best Practices

1. **Always use port mappings** in docker-compose.yml:
   ```yaml
   ports: ["host:container"]  # ✅ Correct
   ```

2. **Use consistent naming** for applications:
   - Hostname: `appname-##` (e.g., `nginx-01`)
   - Path: `/appname-##` (e.g., `/nginx-01`)

3. **Monitor Caddy status** to ensure proxy is running

4. **Test direct access** before testing via Caddy

5. **Use static IPs** for critical services (optional but recommended)

## Summary

- 🐳 **Docker containers** run inside Alpine LXC containers
- 🌐 **Ports MUST be exposed** on LXC network (e.g., "80:80")
- 🔀 **Caddy** provides path-based reverse proxy
- 🔗 **Access**: Users → Caddy → LXC → Docker
- ✅ **Automatic**: Caddy starts when first app is registered
- 📍 **Local Network**: All accessible from same network segment

The architecture ensures isolation, scalability, and easy access to all deployed applications through a unified reverse proxy entry point.
