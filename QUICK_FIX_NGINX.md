# 🚀 Quick Fix: Redeploy Nginx with Host Networking

**Issue**: Nginx not accessible at http://192.168.100.2/  
**Cause**: Docker using bridge networking instead of host networking  
**Solution**: Redeploy nginx from UI with updated catalog template

---

## ✅ What's Been Fixed

1. ✅ **Catalog Updated**: All 106 app templates now use `network_mode: host`
2. ✅ **nginx.json**: Updated to use host networking (no port mapping needed)
3. ✅ **Documentation**: Created comprehensive guide in `docs/DOCKER_HOST_NETWORKING.md`

---

## 📋 Steps to Fix Nginx

### Option 1: Redeploy from UI (Recommended)

1. **Open Proximity UI** → http://localhost:8765

2. **Navigate to Apps**
   - Click on "Apps" in navigation

3. **Delete Old Nginx**
   - Find nginx app (VMID 102 at 192.168.100.2)
   - Click "Delete" or "Stop & Destroy"
   - Confirm deletion

4. **Deploy New Nginx**
   - Click "Deploy New App"
   - Select "nginx" from catalog
   - Click "Deploy"
   - Wait for deployment to complete

5. **Verify New Configuration**
   - New container will use host networking
   - Should be accessible at http://<new-container-ip>/

---

### Option 2: Manual Fix (Advanced)

If you prefer to fix the existing container:

```bash
# SSH into Proxmox host
ssh root@192.168.100.102

# Start container if stopped
pct start 102

# Enter container
pct exec 102 -- sh

# Stop Docker containers
cd /root
docker-compose down

# Edit docker-compose.yml
vi docker-compose.yml

# Add this to the nginx service:
#   network_mode: host
# Remove this from the nginx service:
#   ports:
#     - "80:80"
#     - "443:443"

# Start containers with new config
docker-compose up -d

# Verify nginx is listening on eth0
netstat -tlnp | grep :80

# Exit container
exit

# Test from Proxmox host
curl http://192.168.100.2/
```

---

## 🔍 Verification Steps

### 1. Check Container IP

```bash
# From Proxmox host
pct exec <vmid> -- ip -4 addr show eth0 | grep inet

# Example output:
# inet 192.168.100.2/24 brd 192.168.100.255 scope global dynamic eth0
```

### 2. Check Nginx is Listening

```bash
# From Proxmox host
pct exec <vmid> -- netstat -tlnp | grep :80

# Should show nginx listening on 0.0.0.0:80 or :::80
# NOT on 172.x.x.x (that's Docker bridge)
```

### 3. Test Connectivity

```bash
# From Proxmox host
curl -v http://<container-ip>/

# Should return HTTP 200 and HTML content
```

### 4. Test from Your Machine

```bash
# From your Mac
curl http://192.168.100.2/

# Or open in browser:
open http://192.168.100.2/
```

---

## 📊 What Changed

### Old Configuration (Bridge Mode)
```yaml
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    # ... other config
```

**Problem**: nginx listens on Docker bridge IP (172.18.0.2), not accessible from network

### New Configuration (Host Mode)
```yaml
services:
  nginx:
    image: nginx:latest
    network_mode: host
    # ... other config
    # NO ports mapping needed!
```

**Solution**: nginx listens directly on container IP (192.168.100.2), accessible from network ✅

---

## 💡 Important Notes

### After Redeploy

1. **New IP**: Container may get a different DHCP IP
2. **Check IP**: Use `pct list` or check in UI
3. **Update Bookmarks**: If you had http://192.168.100.2/ bookmarked

### Port Conflicts

With host networking:
- ✅ ONE app per port per container
- ❌ Cannot run nginx + apache (both use port 80) in same container
- ✅ Can run multiple containers each with nginx (different IPs)

---

## 🆘 Troubleshooting

### Still Can't Access?

1. **Check container is running**:
   ```bash
   pct status 102
   ```

2. **Check Docker is running inside**:
   ```bash
   pct exec 102 -- docker ps
   ```

3. **Check firewall** (should be OK but verify):
   ```bash
   pct exec 102 -- iptables -L -n
   ```

4. **Check from Proxmox host first**:
   ```bash
   ssh root@192.168.100.102
   curl http://192.168.100.2/
   ```

5. **If works from Proxmox but not from your Mac**:
   - Check network routing
   - Verify Mac can ping 192.168.100.2
   - Check any firewalls on your network

---

## 📞 Need Help?

- Check: `docs/DOCKER_HOST_NETWORKING.md` for detailed explanation
- Check: `docs/troubleshooting.md` for common issues
- Check: Backend logs in Proximity UI

---

## ✅ Success Criteria

After redeploying, you should be able to:

1. ✅ Access nginx at http://<container-ip>/
2. ✅ See nginx welcome page
3. ✅ No "Connection refused" errors
4. ✅ Container accessible from any device on network

---

**Status**: Ready to redeploy 🚀  
**Next Step**: Redeploy nginx from Proximity UI  
**Expected Time**: < 5 minutes

---

**Last Updated**: October 8, 2025  
**Tested On**: Proxmox VE 8.x with vmbr0 + DHCP networking
