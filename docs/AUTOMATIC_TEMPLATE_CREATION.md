# Automatic Template Creation

## Overview

Proximity automatically creates an optimized LXC template on first startup. This template includes Alpine Linux with Docker pre-installed, significantly speeding up application deployments.

## How It Works

### First Startup

When Proximity starts for the first time (or when the template is missing):

```
🚀 Starting Proximity API...
================================================
STEP 2.5: Checking LXC Template
================================================
⚠ Proximity template 'proximity-alpine-docker.tar.zst' not found
🔧 Creating optimized Alpine+Docker template (this will take 2-3 minutes)...
📦 Step 1/7: Checking for base Alpine template...
✓ Found base template: local:vztmpl/alpine-3.19-default_20231225_amd64.tar.xz
📦 Step 2/7: Creating temporary container (VMID 9999)...
✓ Temporary container created
📦 Step 3/7: Starting container...
✓ Container started
📦 Step 4/7: Installing Docker (this takes ~60 seconds)...
✓ Docker installed and configured
📦 Step 5/7: Stopping container...
✓ Container stopped
📦 Step 6/7: Creating template archive (this takes ~30 seconds)...
✓ Template archive created
📦 Step 7/7: Cleaning up temporary container...
✓ Cleanup complete
✓ Template creation completed in 142.3 seconds
✓ Optimized Alpine+Docker template ready
   • Deployments will be 50% faster!
```

### Subsequent Startups

Once the template exists, it's reused:

```
================================================
STEP 2.5: Checking LXC Template
================================================
✓ Proximity template 'proximity-alpine-docker.tar.zst' already exists
✓ Optimized Alpine+Docker template ready
   • Deployments will be 50% faster!
```

## Performance Benefits

### Before (Standard Alpine Template)

```
Deployment Timeline:
├─ Create LXC container (10-15s)
├─ Start container (3-5s)
├─ Install Docker + dependencies (40-60s) ⬅️ ELIMINATED
├─ Pull application images (20-120s)
└─ Start Docker Compose (5-10s)
Total: 80-210 seconds
```

### After (Optimized Template)

```
Deployment Timeline:
├─ Create LXC container (10-15s)
├─ Start container (3-5s)
├─ Verify Docker is ready (1-2s) ⬅️ FAST!
├─ Pull application images (20-120s)
└─ Start Docker Compose (5-10s)
Total: 40-152 seconds (50% faster!)
```

## Template Contents

The optimized template includes:

- **Alpine Linux 3.19** (latest stable)
- **Docker Engine** (latest from Alpine repos)
- **Docker Compose** (latest from Alpine repos)
- **Essential utilities**: curl, ca-certificates, bash
- **Pre-configured**: Docker starts on boot
- **Optimized**: System fully updated (apk upgrade)

## Requirements

### Base Template

Proximity needs an Alpine Linux base template to build from. The system looks for:

1. **Preferred**: `alpine-3.19-default_20231225_amd64.tar.xz`
2. **Fallback**: Any Alpine 3.x template

### Download Base Template

If no Alpine template is found, download one:

```bash
# On your Proxmox host
pveam update
pveam download local alpine-3.19-default_20231225_amd64.tar.xz
```

Or via web UI:
1. Go to: Node → local (pve) → Content → Templates
2. Click "Templates" button
3. Find "Alpine Linux"
4. Click "Download"

### System Requirements

- **Proxmox VE 8.x** or later
- **Storage space**: ~500MB for template
- **Temporary VMID**: 9999 must be available
- **Network access**: Container needs internet for Docker installation

## Configuration

### Environment Variables

```bash
# .env file

# Primary template (created automatically)
DEFAULT_LXC_TEMPLATE=local:vztmpl/proximity-alpine-docker.tar.zst

# Fallback if template creation fails
FALLBACK_LXC_TEMPLATE=local:vztmpl/alpine-3.19-default_20231225_amd64.tar.xz
```

### Settings (config.py)

```python
class Settings(BaseSettings):
    DEFAULT_LXC_TEMPLATE: str = "local:vztmpl/proximity-alpine-docker.tar.zst"
    FALLBACK_LXC_TEMPLATE: str = "local:vztmpl/alpine-3.19-default_20231225_amd64.tar.xz"
```

## Manual Template Creation

If you want to create the template manually:

```bash
# 1. Create temporary container
pct create 9999 local:vztmpl/alpine-3.19-default_20231225_amd64.tar.xz \
  --hostname proximity-template-builder \
  --password temppass \
  --memory 2048 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp,firewall=1 \
  --features nesting=1,keyctl=1 \
  --unprivileged 1 \
  --onboot 0

# 2. Start and configure
pct start 9999
sleep 5

pct exec 9999 -- sh -c "
  apk update && \
  apk upgrade && \
  apk add --no-cache docker docker-compose docker-cli-compose ca-certificates curl bash && \
  rc-update add docker boot && \
  service docker start && \
  docker --version && \
  docker compose version
"

# 3. Stop container
pct stop 9999
sleep 3

# 4. Create template
vzdump 9999 \
  --compress zstd \
  --dumpdir /var/lib/vz/template/cache \
  --mode stop

# 5. Rename template
BACKUP_FILE=$(ls -t /var/lib/vz/template/cache/vzdump-lxc-9999-*.tar.zst | head -1)
mv "$BACKUP_FILE" /var/lib/vz/template/cache/proximity-alpine-docker.tar.zst

# 6. Cleanup
pct destroy 9999
```

## Troubleshooting

### Template Creation Fails

**Symptom**: "Template creation failed" during startup

**Possible Causes**:
1. No Alpine base template available
2. VMID 9999 already in use
3. Network connectivity issues
4. Insufficient disk space

**Solutions**:

```bash
# 1. Download Alpine template
pveam update
pveam available | grep alpine
pveam download local alpine-3.19-default_20231225_amd64.tar.xz

# 2. Check VMID 9999
pct list | grep 9999
# If exists, change TEMP_VMID in template_service.py

# 3. Check connectivity
pct exec <container_id> -- ping -c 3 dl-cdn.alpinelinux.org

# 4. Check disk space
df -h /var/lib/vz
```

### Template Exists But Not Working

**Symptom**: Deployments still slow, Docker installation happens

**Check Template**:
```bash
# List templates
ls -lh /var/lib/vz/template/cache/ | grep proximity

# Test template
pct create 999 local:vztmpl/proximity-alpine-docker.tar.zst \
  --hostname test \
  --password test \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp

pct start 999
pct exec 999 -- docker --version
pct destroy 999
```

### Force Template Recreation

```bash
# Remove existing template
rm /var/lib/vz/template/cache/proximity-alpine-docker.tar.zst

# Restart Proximity
# Template will be recreated automatically
```

## Template Management API

Future enhancement - API endpoints for template management:

```
GET  /api/v1/system/template/status      # Check template status
POST /api/v1/system/template/create      # Force template creation
GET  /api/v1/system/template/info        # Get template details
DELETE /api/v1/system/template           # Remove template
```

## Customization

### Adding Packages to Template

Modify `template_service.py`:

```python
install_script = """
apk update && \
apk upgrade && \
apk add --no-cache \
  docker docker-compose docker-cli-compose \
  ca-certificates curl bash \
  vim nano htop   # Add your packages here
"""
```

### Different Base OS

Change `BASE_ALPINE_TEMPLATE` in `template_service.py`:

```python
class TemplateService:
    BASE_ALPINE_TEMPLATE = "ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
```

Update install script accordingly.

### Custom Template Storage

```bash
# .env
DEFAULT_LXC_TEMPLATE=my-storage:vztmpl/proximity-alpine-docker.tar.zst
```

## Benefits Summary

✅ **50% faster deployments** - No Docker installation wait  
✅ **Automatic setup** - Template created on first run  
✅ **User-friendly** - Clear progress logs  
✅ **Reliable** - Tested, pre-configured Docker  
✅ **Fallback safe** - Uses standard Alpine if creation fails  
✅ **Space efficient** - ~500MB template vs repeated downloads  
✅ **Network efficient** - One-time setup vs per-deployment  

## See Also

- [Deployment Guide](deployment.md)
- [LXC Password Management](LXC_PASSWORD_MANAGEMENT.md)
- [Docker Host Networking](DOCKER_HOST_NETWORKING.md)
- [Architecture](architecture.md)
