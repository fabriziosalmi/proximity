# Docker Host Networking for Container Apps

**Date**: October 8, 2025  
**Status**: ✅ IMPLEMENTED

---

## 🎯 Problem Statement

When deploying applications with Docker inside LXC containers on Proxmox using the simplified vmbr0 + DHCP networking:

**Issue**: Applications running in Docker containers were NOT accessible from the network because Docker uses bridge networking by default, creating an isolated network (172.x.x.x) inside the LXC container.

**Example**:
- LXC Container IP: `192.168.100.2` (assigned by DHCP)
- Docker Bridge IP: `172.18.0.2` (internal to container)
- Nginx listening on: `172.18.0.2:80` (NOT accessible from outside)
- Result: `curl http://192.168.100.2/` → **Connection refused** ❌

---

## ✅ Solution: Docker Host Networking

Use `network_mode: host` in docker-compose files to make Docker containers use the LXC container's network interface directly.

### Before (Bridge Mode)
```yaml
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    restart: always
```

**Network Flow**:
```
External Client → 192.168.100.2:80 (LXC eth0)
                  ❌ Connection refused
                  (nginx is on 172.18.0.2:80)
```

### After (Host Mode)
```yaml
services:
  nginx:
    image: nginx:latest
    network_mode: "host"
    restart: always
```

**Network Flow**:
```
External Client → 192.168.100.2:80 (LXC eth0)
                  ✅ nginx listening directly on eth0
                  → nginx container responds
```

---

## 🔧 Implementation

### 1. Update Catalog Templates

Modified all catalog JSON files to use `network_mode: host`:

```python
# Script: update_catalog_networking.py
# Updates 106 catalog files automatically

# Changes made:
# - Remove "ports" mapping (not needed with host mode)
# - Add "network_mode": "host" to all services
```

### 2. Updated Files

All catalog templates in `backend/catalog/apps/*.json` now include:
- ✅ `network_mode: host` in all services
- ❌ Removed `ports` mapping (incompatible with host mode)

**Example files updated**:
- nginx.json
- wordpress.json
- ghost.json
- gitea.json
- ... (all 106 apps)

---

## 📋 How It Works

### With network_mode: host

1. **Container Deployment**:
   - LXC container created on vmbr0 with DHCP
   - Gets IP from network (e.g., 192.168.100.2)

2. **Docker Container**:
   - Uses `network_mode: host`
   - Binds directly to LXC's eth0 interface
   - No port mapping needed

3. **Network Access**:
   - Application listens on LXC container's IP
   - Accessible from any device on the network
   - No NAT, no port forwarding, simple and direct

### Network Stack

```
External Network (192.168.100.0/24)
         ↓
    Proxmox vmbr0
         ↓
  LXC Container (192.168.100.2)
    Interface: eth0
         ↓
  Docker Container (network_mode: host)
    Binds to: eth0 (same as LXC)
         ↓
  Application (nginx)
    Listening on: 192.168.100.2:80 ✅
```

---

## 🚀 Benefits

### Simplicity
- ✅ No port mapping configuration needed
- ✅ Application binds directly to container IP
- ✅ Standard network troubleshooting works

### Performance
- ✅ No Docker bridge overhead
- ✅ No NAT translation
- ✅ Direct packet routing

### Compatibility
- ✅ Works with vmbr0 + DHCP architecture
- ✅ No need for complex network appliance
- ✅ Standard Proxmox networking patterns

---

## 📝 Usage Instructions

### For New Deployments

1. Deploy app from catalog via Proximity UI
2. App automatically uses `network_mode: host`
3. Access via container's DHCP IP (e.g., `http://192.168.100.2/`)

### For Existing Deployments

**Option 1: Redeploy** (Recommended)
1. Delete old app deployment
2. Redeploy from updated catalog
3. New deployment will use host networking

**Option 2: Manual Update**
1. SSH into LXC container
2. Edit `/root/docker-compose.yml`
3. Add `network_mode: host` to services
4. Remove `ports` section
5. Run `docker-compose down && docker-compose up -d`

---

## 🔍 Troubleshooting

### Check if Container Uses Host Networking

```bash
# SSH into LXC container
pct exec <vmid> -- sh

# Check docker-compose.yml
cat /root/docker-compose.yml | grep network_mode

# Should show:
# network_mode: host
```

### Verify Application is Listening

```bash
# Inside container
netstat -tlnp | grep :80

# Should show process listening on 0.0.0.0:80
# NOT on 127.0.0.1 or 172.x.x.x
```

### Test Connectivity

```bash
# From Proxmox host
curl http://<container-ip>/

# Should return application response
```

---

## ⚠️ Important Notes

### Port Conflicts

With `network_mode: host`, applications bind directly to the container's network interface:

**Implication**: Cannot run multiple apps on the same port on the same LXC container.

**Example**:
- ❌ CANNOT: nginx (port 80) + apache (port 80) in same container
- ✅ CAN: nginx (port 80) + app (port 3000) in same container
- ✅ CAN: nginx on container A + nginx on container B (different IPs)

### Environment Variables

Some applications may need host/port environment variables:

```yaml
services:
  app:
    image: myapp:latest
    network_mode: host
    environment:
      - HOST=0.0.0.0      # Bind to all interfaces
      - PORT=8080          # Listen on specific port
```

### DNS Resolution

With host networking, containers use the LXC container's DNS settings:

```bash
# Check DNS in container
cat /etc/resolv.conf
```

---

## 📊 Catalog Update Summary

**Script**: `update_catalog_networking.py`

**Changes**:
- Total files: 106
- Modified: 106 (100%)
- Changes per file:
  - Added `network_mode: host`
  - Removed `ports` mapping

**Affected Categories**:
- Web Servers (nginx, caddy, apache)
- CMS (wordpress, ghost, wikijs)
- Development (gitea, gitlab, code-server)
- Monitoring (grafana, prometheus, uptime-kuma)
- Media (plex, jellyfin, sonarr, radarr)
- All other applications

---

## 🎓 Technical Details

### Docker Network Modes

1. **bridge** (default): Isolated network, requires port mapping
2. **host** (our choice): Use host's network directly, no isolation
3. **none**: No networking
4. **container**: Share another container's network

### Why Host Mode for Proximity

Given our architecture:
- ✅ LXC containers already provide isolation
- ✅ Each app in separate LXC container
- ✅ No need for double network isolation (LXC + Docker)
- ✅ Simpler networking = easier troubleshooting
- ✅ Better performance (no bridge overhead)

---

## 📚 References

- [Docker Network Mode Documentation](https://docs.docker.com/network/)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
- [LXC Networking](https://pve.proxmox.com/wiki/Linux_Container#pct_container_network)
- [Proximity Architecture](4_ARCHITECTURE.md)

---

## ✅ Validation

To verify host networking is working:

```bash
# 1. Check catalog template
cat backend/catalog/apps/nginx.json | grep network_mode
# Expected: "network_mode": "host"

# 2. Deploy app via UI

# 3. Get container IP
pct exec <vmid> -- ip -4 addr show eth0

# 4. Test from external machine
curl http://<container-ip>/
# Expected: HTTP 200 response ✅
```

---

**Status**: ✅ **PRODUCTION READY**

All catalog applications now use Docker host networking for seamless network access with the simplified vmbr0 + DHCP architecture.

---

**Last Updated**: October 8, 2025  
**Implemented By**: System Update  
**Tested On**: Proxmox VE 8.x + Docker 24.x
