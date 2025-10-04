# Troubleshooting Guide

This guide covers common issues, debugging techniques, and solutions for problems you might encounter with Proximity.

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [Deployment Failures](#deployment-failures)
- [Network Issues](#network-issues)
- [Container Problems](#container-problems)
- [Performance Issues](#performance-issues)
- [Bug Fixes & Patches](#bug-fixes--patches)

---

## Authentication Issues

### 401 Unauthorized After Login

**Problem**: API requests return 401 even after successful login.

**Symptoms:**
```
GET /api/v1/system/nodes HTTP/1.1 401 Unauthorized
Authentication required: No token provided
```

**Causes:**
1. Browser caching old JavaScript without `authFetch`
2. OPTIONS requests not handled properly (CORS preflight)
3. Token not being sent in request headers

**Solution:**

**Fixed in:** `api/middleware/auth.py:43-44`

Added OPTIONS request handling:
```python
async def get_current_user(request: Request, ...):
    # Allow OPTIONS requests for CORS preflight
    if request.method == "OPTIONS":
        return None

    if credentials is None:
        raise HTTPException(status_code=401, ...)
```

**Additional Fixes:**
- Replaced all `fetch()` with `authFetch()` in `app.js`
- Added cache-busting headers for static files in `main.py`:

```python
response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
response.headers["Pragma"] = "no-cache"
response.headers["Expires"] = "0"
```

**Resolution Steps:**
1. Hard refresh browser: `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows/Linux)
2. Clear browser cache
3. Restart backend server

### Token Expiration

**Problem**: User gets logged out unexpectedly.

**Solution:**
- Tokens expire after 60 minutes (default)
- Configure in `.env`:
  ```ini
  ACCESS_TOKEN_EXPIRE_MINUTES=120
  ```
- Implement token refresh endpoint (already available at `/api/v1/auth/refresh`)

---

## Deployment Failures

### Docker Installation Fails

**Problem**: Container created but Docker installation fails during deployment.

**Symptoms:**
```
[nginx-nginx-01] Setting up Docker
ERROR: SSH command failed: Connection timeout
```

**Causes:**
1. SSH connection to Proxmox host not working
2. Container doesn't have internet access
3. Alpine repositories unreachable

**Solution:**

1. **Verify SSH Access:**
   ```bash
   # Test SSH from Proximity host to Proxmox
   ssh root@{proxmox_host} 'echo OK'
   ```

2. **Check Container Network:**
   ```bash
   # Test from container
   pct exec <vmid> -- ping -c 3 8.8.8.8
   pct exec <vmid> -- ping -c 3 dl-cdn.alpinelinux.org
   ```

3. **Verify .env Configuration:**
   ```ini
   PROXMOX_SSH_HOST=192.168.1.100
   PROXMOX_SSH_PORT=22
   PROXMOX_SSH_USER=root
   PROXMOX_SSH_PASSWORD=your_password
   ```

4. **Manual Docker Installation:**
   ```bash
   pct exec <vmid> -- sh -c 'apk update && apk add docker docker-cli-compose'
   pct exec <vmid> -- rc-update add docker default
   pct exec <vmid> -- service docker start
   ```

### Container Creation Fails

**Problem**: LXC container fails to create.

**Symptoms:**
```
ProxmoxError: LXC 106 already exists on node opti2
```

**Solutions:**

1. **VMID Already Exists:**
   ```bash
   # Check if VMID is in use
   pct list | grep 106

   # Destroy old container
   pct stop 106
   pct destroy 106
   ```

2. **Storage Full:**
   ```bash
   # Check storage on Proxmox node
   pvesm status

   # Clean up old backups
   rm /var/lib/vz/dump/old-backups/*
   ```

3. **Template Missing:**
   ```bash
   # Download Alpine template manually
   pveam update
   pveam download local alpine-3.22-default_20250617_amd64.tar.xz
   ```

### Deployment Stuck/Hanging

**Problem**: Deployment progress shows "Deploying..." but never completes.

**Symptoms:**
- UI shows spinning loader indefinitely
- No errors in console
- Container exists but isn't fully configured

**Solution:**

1. **Check Backend Logs:**
   ```bash
   # Look for errors
   tail -f /path/to/proximity/backend/logs/app.log
   ```

2. **Check Container Status:**
   ```bash
   pct status <vmid>
   pct exec <vmid> -- docker ps
   ```

3. **Manual Cleanup:**
   ```bash
   # Stop deployment
   pct stop <vmid>
   pct destroy <vmid>

   # Retry deployment from UI
   ```

4. **Increase Timeouts:**
   Edit `services/app_service.py`:
   ```python
   # Increase timeout for large images
   await self.proxmox.execute_in_container(
       ...,
       timeout=600  # 10 minutes instead of default
   )
   ```

---

## Network Issues

### Network Appliance Fails to Start

**Problem**: Network appliance (VMID 9999) fails during initialization.

**Symptoms:**
```
⚠️ Network appliance initialization failed
ℹ️  Containers will use default Proxmox networking (vmbr0)
```

**Common Causes:**

**1. VMID 9999 Already Exists:**
```bash
# Check and clean up
pct status 9999
pct stop 9999
pct destroy 9999

# Restart Proximity to re-provision
```

**2. Bridge Creation Fails:**
```bash
# Check if bridge exists
ip link show proximity-lan

# Manually create bridge (if needed)
cat >> /etc/network/interfaces <<EOF
auto proximity-lan
iface proximity-lan inet static
    address 10.20.0.1
    netmask 255.255.255.0
    bridge_ports none
    bridge_stp off
    bridge_fd 0
EOF

ifup proximity-lan
```

**3. SSH Connection Issues:**
```bash
# Test SSH to node
ssh root@{node} 'echo Connected'

# Check SSH config in .env
PROXMOX_SSH_HOST=192.168.1.100
PROXMOX_SSH_USER=root
```

### Containers Can't Access Internet

**Problem**: Deployed containers cannot reach internet.

**Symptoms:**
```bash
pct exec <vmid> -- ping 8.8.8.8
# Result: Network unreachable
```

**Solutions:**

**1. Check NAT on Appliance:**
```bash
# Verify iptables NAT rule
pct exec 9999 -- iptables -t nat -L -n | grep MASQUERADE

# Re-add if missing
pct exec 9999 -- iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

**2. Verify IP Forwarding:**
```bash
pct exec 9999 -- sysctl net.ipv4.ip_forward
# Should return: net.ipv4.ip_forward = 1

# Enable if disabled
pct exec 9999 -- sysctl -w net.ipv4.ip_forward=1
```

**3. Check Container Gateway:**
```bash
pct exec <vmid> -- ip route
# Should show: default via 10.20.0.1 dev eth0
```

**4. Fallback to vmbr0:**
If appliance is unavailable, manually switch container to vmbr0:
```bash
pct set <vmid> -net0 name=eth0,bridge=vmbr0,ip=dhcp
pct reboot <vmid>
```

### DNS Resolution Fails

**Problem**: Containers can ping IPs but not domain names.

**Symptoms:**
```bash
pct exec <vmid> -- ping 8.8.8.8    # Works
pct exec <vmid> -- ping google.com # Fails: Name resolution failed
```

**Solutions:**

**1. Check dnsmasq on Appliance:**
```bash
pct exec 9999 -- rc-status | grep dnsmasq
# Should show: dnsmasq [started]

# Restart if needed
pct exec 9999 -- rc-service dnsmasq restart
```

**2. Verify DNS Config in Container:**
```bash
pct exec <vmid> -- cat /etc/resolv.conf
# Should show: nameserver 10.20.0.1
```

**3. Test DNS from Appliance:**
```bash
pct exec 9999 -- nslookup google.com
```

---

## Container Problems

### Container Won't Start

**Problem**: Container status shows "stopped" and won't start.

**Symptoms:**
```bash
pct start <vmid>
# Error: CT <vmid> unable to start
```

**Solutions:**

**1. Check Container Config:**
```bash
pct config <vmid>
# Look for invalid settings
```

**2. Check Resource Availability:**
```bash
# Verify node has resources
pvesh get /nodes/{node}/status
```

**3. Review Logs:**
```bash
# Proxmox task log
tail -f /var/log/pve/tasks/active
```

**4. Rebuild Container:**
```bash
pct stop <vmid>
pct destroy <vmid>
# Redeploy from Proximity UI
```

### Docker Not Running in Container

**Problem**: Docker commands fail inside container.

**Symptoms:**
```bash
pct exec <vmid> -- docker ps
# Error: Cannot connect to Docker daemon
```

**Solutions:**

**1. Check Docker Service:**
```bash
pct exec <vmid> -- rc-status | grep docker
# If not started:
pct exec <vmid> -- rc-service docker start
```

**2. Verify Container Features:**
```bash
pct config <vmid> | grep features
# Should include: features: keyctl=1,nesting=1
```

**3. Reinstall Docker:**
```bash
pct exec <vmid> -- apk add --no-cache docker docker-cli-compose
pct exec <vmid> -- rc-update add docker default
pct exec <vmid> -- rc-service docker start
```

### Application Not Accessible

**Problem**: Application deployed but not accessible via URL.

**Symptoms:**
- Container running
- Docker container shows as "Up"
- URL returns connection refused

**Solutions:**

**1. Check Reverse Proxy:**
```bash
# Verify Caddy is running
pct exec 9999 -- rc-status | grep caddy

# Check vhost configuration
pct exec 9999 -- cat /etc/caddy/Caddyfile | grep {hostname}
```

**2. Verify Port Mapping:**
```bash
pct exec <vmid> -- docker ps
# Check PORTS column shows correct mapping
```

**3. Test Direct Access:**
```bash
# From appliance, curl container
pct exec 9999 -- curl http://10.20.0.100:80
```

**4. Check Firewall:**
```bash
# Disable container firewall temporarily
pct set <vmid> -firewall 0
```

---

## Performance Issues

### Slow Deployments

**Problem**: Application deployments take longer than expected.

**Causes:**
1. Slow internet for image downloads
2. Template not cached
3. Limited node resources

**Solutions:**

**1. Pre-cache Templates:**
```bash
# Download Alpine template on all nodes
pveam download local alpine-3.22-default_20250617_amd64.tar.xz
```

**2. Increase Resources:**
Edit catalog item to use more CPU during deployment:
```json
"resources": {
  "cpu": 4,  // More CPU = faster setup
  "memory": 4096
}
```

**3. Local Docker Registry:**
Set up local registry for faster image pulls:
```bash
# Deploy registry container
docker run -d -p 5000:5000 --name registry registry:2
```

### High CPU Usage

**Problem**: Proxmox node shows high CPU usage.

**Solutions:**

**1. Check Container Resources:**
```bash
pct exec <vmid> -- docker stats
```

**2. Limit Container CPU:**
```bash
pct set <vmid> -cores 2 -cpulimit 2
```

**3. Review Application Config:**
Check `docker-compose.yml` for resource limits:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## Bug Fixes & Patches

### Event Loop Fixes

**Issue**: Async event loop errors during initialization.

**Fixed in**: `services/network_appliance_orchestrator.py`

**Problem**: SSH operations blocking event loop.

**Solution**: Wrapped SSH calls in `asyncio.to_thread()`:
```python
# Before (blocking)
channel.exec_command(command)

# After (non-blocking)
result = await asyncio.to_thread(
    lambda: self._execute_ssh_command(node, command)
)
```

### SSH Connection Fixes

**Issue**: SSH authentication failures.

**Fixed in**: `services/network_appliance_orchestrator.py`

**Problem**: Paramiko SSH client not properly initialized.

**Solution**: Improved connection handling:
```python
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname=node,
    username='root',
    password=settings.PROXMOX_PASSWORD,
    timeout=30
)
```

### Initialization Sequence Fixes

**Issue**: Services starting in wrong order causing failures.

**Fixed in**: `main.py` startup sequence

**Problem**: App catalog loaded before network appliance ready.

**Solution**: Reorganized startup steps:
1. Database init
2. Proxmox connection
3. Network appliance (with fallback)
4. App catalog
5. Reverse proxy

### UI Refresh Issues

**Issue**: UI not updating after actions.

**Fixed in**: `app.js`

**Problem**: State not refreshing after deployment/actions.

**Solution**: Added reload calls:
```javascript
// After deployment
await loadDeployedApps();
await loadSystemInfo();
await loadProxyStatus();
updateUI();
```

### Template Caching Issues

**Issue**: Templates downloaded on every deployment.

**Fixed in**: `services/proxmox_service.py`

**Problem**: Cache check not working properly.

**Solution**: Improved cache detection:
```python
# Check local storage first
templates = await self.proxmox.nodes(node).storage('local').content.get()
for tmpl in templates:
    if 'alpine-3.22' in tmpl['volid']:
        logger.info(f"✓ CACHE HIT: Using {tmpl['volid']}")
        return tmpl['volid']
```

---

## Diagnostic Commands

### System Health Check

```bash
# Proxmox status
pvesh get /cluster/resources

# Node status
pvesh get /nodes/{node}/status

# Storage status
pvesm status

# Network interfaces
ip addr show
```

### Container Diagnostics

```bash
# Container info
pct config <vmid>
pct status <vmid>

# Resource usage
pct exec <vmid> -- top -b -n 1

# Network config
pct exec <vmid> -- ip addr
pct exec <vmid> -- ip route

# Docker status
pct exec <vmid> -- docker info
pct exec <vmid> -- docker ps -a
pct exec <vmid> -- docker compose ls
```

### Network Diagnostics

```bash
# Bridge status
ip link show proximity-lan
brctl show proximity-lan

# Appliance status
pct status 9999
pct exec 9999 -- rc-status

# Routing
pct exec 9999 -- ip route
pct exec 9999 -- iptables -t nat -L -n -v

# DNS/DHCP
pct exec 9999 -- cat /etc/dnsmasq.conf
pct exec 9999 -- ps aux | grep dnsmasq
```

### Application Diagnostics

```bash
# App logs
curl http://localhost:8765/api/v1/apps/{app_id}/logs

# Docker logs
pct exec <vmid> -- docker compose logs

# Service status
pct exec <vmid> -- docker compose ps
```

---

## Getting Additional Help

If you're still experiencing issues:

1. **Check GitHub Issues**: https://github.com/yourusername/proximity/issues
2. **Enable Debug Logging**: Set `DEBUG=true` in `.env`
3. **Collect Logs**:
   ```bash
   # Proximity logs
   cat /path/to/proximity/backend/logs/*.log

   # Proxmox logs
   tail -100 /var/log/pve/tasks/active

   # Container logs
   pct exec <vmid> -- dmesg
   ```

4. **Create Issue**: Include:
   - Proximity version
   - Proxmox version
   - Error messages
   - Steps to reproduce
   - Relevant logs
