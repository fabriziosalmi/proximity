# Deployment & Operations Guide

This guide covers deploying Proximity, deploying applications, and operational procedures.

## Table of Contents

- [Installing Proximity](#installing-proximity)
- [Deploying Applications](#deploying-applications)
- [Template Management](#template-management)
- [Testing](#testing)
- [Operations](#operations)

---

## Installing Proximity

### Prerequisites

- Proxmox VE 8.x or later
- Python 3.13+
- SSH access to Proxmox host(s)
- Sufficient storage for LXC containers

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/proximity.git
   cd proximity/backend
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Proxmox credentials
   ```

5. **Initialize database:**
   ```bash
   python -c "from models.database import init_db; init_db()"
   ```

6. **Start the server:**
   ```bash
   python main.py
   ```

7. **Access the UI:**
   Open http://localhost:8765 in your browser

### Configuration

Edit `.env` file with your settings:

```ini
# Proxmox Connection
PROXMOX_HOST=192.168.1.100
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your_password
PROXMOX_VERIFY_SSL=false

# SSH Settings (for container management)
PROXMOX_SSH_HOST=192.168.1.100  # Defaults to PROXMOX_HOST
PROXMOX_SSH_PORT=22
PROXMOX_SSH_USER=root
PROXMOX_SSH_PASSWORD=your_password  # Defaults to PROXMOX_PASSWORD

# API Settings
API_HOST=0.0.0.0
API_PORT=8765
DEBUG=true

# Security
JWT_SECRET_KEY=generate-a-secure-random-key
ENCRYPTION_KEY=generate-another-secure-key
```

### First-Time Setup

1. **Create admin user:**
   - Navigate to http://localhost:8765
   - Click "Register" on the auth modal
   - Create your admin account

2. **Verify Proxmox connection:**
   - Check the dashboard for node information
   - Verify "Infrastructure" page shows your Proxmox nodes

3. **Check network appliance:**
   - Go to Infrastructure > Network Status
   - Verify the appliance is running or deploying

---

## Deploying Applications

Proximity supports fully automated application deployment with zero manual intervention.

### Deployment Methods

#### 1. Via Web UI (Recommended)

1. Navigate to "App Store" in the sidebar
2. Browse available applications
3. Click "Deploy" on your chosen app
4. Fill in deployment form:
   - **Hostname**: Unique name for the container (e.g., `nginx-01`)
   - **Node** (optional): Target Proxmox node
5. Click "Deploy Application"
6. Monitor deployment progress in real-time

#### 2. Via API

```bash
curl -X POST http://localhost:8765/api/v1/apps/deploy \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_id": "nginx",
    "hostname": "nginx-01",
    "config": {},
    "environment": {}
  }'
```

### Deployment Process

When you deploy an application, Proximity:

1. **Selects Target Node**: Automatically chooses node with most available resources
2. **Downloads Template**: Alpine Linux template cached on the node
3. **Creates LXC Container**: With appropriate resources and networking
4. **Installs Docker**: Fully automated via SSH
5. **Deploys Application**: Using Docker Compose
6. **Configures Reverse Proxy**: Automatic vhost creation (if web app)
7. **Registers DNS**: Adds `.prox.local` DNS entry
8. **Health Checks**: Verifies services are running

**Timeline:** Typical deployment takes 2-5 minutes depending on image size.

### Automated Docker Installation

Proximity automatically installs Docker in new containers via SSH:

```bash
# Executed automatically during deployment
apk update
apk add --no-cache docker docker-cli-compose
rc-update add docker default
service docker start
docker info  # Verification
```

**Requirements:**
- SSH access to Proxmox host (configured in `.env`)
- Proxmox host has `pct` command available
- Container has network connectivity for package downloads

### Deployment Configuration

Each catalog item includes deployment configuration:

**Example: `catalog/nginx.json`**
```json
{
  "id": "nginx",
  "name": "Nginx",
  "description": "High-performance web server",
  "category": "web",
  "icon": "server",
  "version": "1.25",
  "resources": {
    "cpu": 1,
    "memory": 512,
    "disk": 8
  },
  "compose": {
    "version": "3.8",
    "services": {
      "nginx": {
        "image": "nginx:alpine",
        "ports": ["80:80"],
        "restart": "unless-stopped"
      }
    }
  }
}
```

### Post-Deployment

After deployment, your application is:
- ✅ Accessible via `{hostname}.prox.local` (if web app)
- ✅ Listed in "My Apps" with status monitoring
- ✅ Manageable via UI (start/stop/restart)
- ✅ Accessible via SSH: `pct enter <vmid>` on Proxmox host

---

## Template Management

Proximity uses Alpine Linux as the base template for all containers.

### Template Caching

Templates are automatically cached on Proxmox nodes during first deployment:

```
Location: /var/lib/vz/template/cache/
Example: alpine-3.22-default_20250617_amd64.tar.xz
```

**Cache Benefits:**
- ⚡ Faster subsequent deployments (no re-download)
- 💾 Reduced bandwidth usage
- 📦 Consistent base images across deployments

### Template Selection Process

1. **Check Local Cache**: Look for Alpine 3.22 template in node's cache
2. **Download if Missing**: Fetch from official Alpine repository
3. **Cache for Reuse**: Store in `/var/lib/vz/template/cache/`
4. **Verify Integrity**: Check template is usable

**Logging:**
```
✓ CACHE HIT: Using cached template from local: local:vztmpl/alpine-3.22-default_20250617_amd64.tar.xz
```

### Custom Templates (Advanced)

To create custom templates with pre-installed software:

1. **Create base container:**
   ```bash
   pct create 9998 local:vztmpl/alpine-3.22-default_20250617_amd64.tar.xz \
     --hostname custom-template \
     --memory 2048 \
     --cores 2 \
     --net0 name=eth0,bridge=vmbr0,ip=dhcp \
     --rootfs local-lvm:8
   ```

2. **Install software:**
   ```bash
   pct start 9998
   pct exec 9998 -- apk update
   pct exec 9998 -- apk add docker docker-cli-compose python3 nodejs
   pct exec 9998 -- rc-update add docker default
   pct stop 9998
   ```

3. **Create template:**
   ```bash
   vzdump 9998 --dumpdir /var/lib/vz/template/cache --compress gzip
   mv /var/lib/vz/template/cache/vzdump-lxc-9998-*.tar.gz \
      /var/lib/vz/template/cache/alpine-custom.tar.gz
   pct destroy 9998
   ```

4. **Update catalog to use custom template** (modify `proxmox_service.py` template selection logic)

---

## Testing

Proximity includes comprehensive testing facilities.

### Running Tests

```bash
# Unit tests
python -m pytest tests/

# Integration tests (requires Proxmox)
python -m pytest tests/integration/

# Specific test
python -m pytest tests/test_proxmox_service.py -v
```

### Test Categories

**Unit Tests:**
- Service layer logic
- Data validation
- Authentication/authorization
- API endpoints

**Integration Tests:**
- Proxmox API connectivity
- Container lifecycle
- Network appliance provisioning
- Deployment workflows

### Testing Deployment

To test app deployment without the UI:

```python
import asyncio
from services.app_service import AppService
from models.database import get_db

async def test_deploy():
    db = next(get_db())
    app_service = AppService(db)

    result = await app_service.deploy_app(
        catalog_id="nginx",
        hostname="test-nginx",
        config={},
        environment={}
    )

    print(f"Deployed: {result.name} on {result.node}")
    print(f"VMID: {result.vmid}")
    print(f"Status: {result.status}")

asyncio.run(test_deploy())
```

### Debugging Deployments

Enable debug logging:

```python
# In main.py or config
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs for deployment steps:
```
[nginx-nginx-01] Selecting target node
[nginx-nginx-01] Getting next VMID
[nginx-nginx-01] Creating LXC container 106 on node opti2
[nginx-nginx-01] Starting container
[nginx-nginx-01] Setting up Docker
[nginx-nginx-01] Deploying application
```

---

## Operations

### Application Management

#### Start/Stop/Restart Applications

**Via UI:**
1. Go to "My Apps"
2. Click app card dropdown menu (⋮)
3. Select action: Start, Stop, Restart, or Delete

**Via API:**
```bash
# Start
curl -X POST http://localhost:8765/api/v1/apps/{app_id}/actions \
  -H "Authorization: Bearer TOKEN" \
  -d '{"action": "start"}'

# Stop
curl -X POST http://localhost:8765/api/v1/apps/{app_id}/actions \
  -d '{"action": "stop"}'

# Restart
curl -X POST http://localhost:8765/api/v1/apps/{app_id}/actions \
  -d '{"action": "restart"}'
```

#### View Application Logs

**Via UI:**
- Click app card → "View Logs" button
- Real-time log streaming

**Via API:**
```bash
curl http://localhost:8765/api/v1/apps/{app_id}/logs?lines=100
```

**Via SSH:**
```bash
# Access container
pct enter <vmid>

# View Docker logs
docker compose logs -f
```

### Network Appliance Management

#### Check Appliance Status

```bash
GET /api/v1/system/infrastructure/status
```

**Response:**
```json
{
  "appliance": {
    "vmid": 9999,
    "hostname": "prox-appliance",
    "status": "running",
    "wan_ip": "192.168.1.50",
    "lan_ip": "10.20.0.1"
  },
  "services": {
    "dnsmasq": "started",
    "caddy": "started",
    "cockpit": "started"
  }
}
```

#### Restart Appliance Services

```bash
POST /api/v1/system/infrastructure/appliance/restart
```

#### View Appliance Logs

```bash
GET /api/v1/system/infrastructure/appliance/logs?lines=100
```

#### Access Cockpit Management UI

SSH access: `ssh root@{appliance_wan_ip}` (password: invaders)

Default credentials: `root` / Your Proxmox password

### Monitoring

#### System Health

**Dashboard Metrics:**
- Total applications deployed
- Running applications count
- Infrastructure nodes status
- Resource utilization
- Reverse proxy status

**API Endpoint:**
```bash
GET /api/v1/system/info
```

#### Application Health

Each app card shows:
- Status (running/stopped/error)
- Uptime
- Resource usage (if available)
- Access URL

### Backup & Recovery

#### Backup Containers

Proxmox automatically supports container backups:

```bash
# Manual backup
vzdump <vmid> --dumpdir /var/lib/vz/dump

# Automated backup (configure in Proxmox)
# Datacenter → Backup → Add
```

#### Restore Containers

```bash
pct restore <vmid> /var/lib/vz/dump/vzdump-lxc-<vmid>-YYYY_MM_DD-HH_MM_SS.tar.gz
```

#### Backup Proximity Data

**Database:**
```bash
cp /path/to/proximity/backend/proximity.db /backup/location/
```

**Configuration:**
```bash
cp /path/to/proximity/backend/.env /backup/location/
```

### Scaling

#### Add More Proxmox Nodes

1. Add node to Proxmox cluster
2. Proximity automatically discovers it
3. New deployments will distribute across all nodes

#### Resource Limits

Modify catalog item resource requirements:

```json
"resources": {
  "cpu": 2,      // CPU cores
  "memory": 2048, // RAM in MB
  "disk": 20      // Disk in GB
}
```

---

## Common Operations

### Finding Container VMIDs

```bash
# List all containers
pct list

# Find by hostname
pct list | grep nginx-01
```

### Accessing Container Shell

```bash
# Via Proxmox
pct enter <vmid>

# Via SSH
ssh root@{container_ip}
```

### Checking Docker Status

```bash
pct exec <vmid> -- docker ps
pct exec <vmid> -- docker compose ls
```

### Viewing Container Logs

```bash
pct exec <vmid> -- docker compose logs -f
```

### Network Troubleshooting

```bash
# Check container IP
pct exec <vmid> -- ip addr show eth0

# Test internet connectivity
pct exec <vmid> -- ping -c 3 8.8.8.8

# Test DNS resolution
pct exec <vmid> -- nslookup google.com

# Check appliance routing
pct exec 9999 -- iptables -t nat -L -n -v
```

---

## Maintenance

### Update Alpine Packages

```bash
pct exec <vmid> -- apk update
pct exec <vmid> -- apk upgrade
```

### Update Docker Images

```bash
pct exec <vmid> -- docker compose pull
pct exec <vmid> -- docker compose up -d
```

### Clean Up Unused Resources

```bash
# Remove stopped containers
docker system prune -a

# Clean up Proxmox templates
rm /var/lib/vz/template/cache/old-template.tar.xz
```

### Database Maintenance

```bash
# Vacuum database
sqlite3 proximity.db "VACUUM;"

# Check integrity
sqlite3 proximity.db "PRAGMA integrity_check;"
```

### Upgrading from JSON-based Versions

If you're upgrading from an older Proximity version that used `data/apps.json`, follow these steps:

#### 1. Backup Everything
```bash
cd backend

# Backup current database (if exists)
cp proximity.db proximity_backup_$(date +%Y%m%d_%H%M%S).db

# Backup JSON file
cp data/apps.json data/apps.json.backup
```

#### 2. Verify Admin User Exists
```bash
# Check for admin user
sqlite3 proximity.db "SELECT username, role FROM users WHERE role='admin';"

# If no admin exists, register one through the UI:
# http://localhost:8765 → Register → Create admin account
```

#### 3. Run Migration Script
```bash
python scripts/migrate_json_to_sqlite.py
```

**Expected Output:**
```
============================================================
PROXIMITY: JSON to SQLite Migration
============================================================
Found 5 apps in JSON file
Found admin user: admin (ID: 1)
All migrated apps will be assigned to this user

  ✓ Created: WordPress (ID: wordpress-prod) (Owner: admin)
  ✓ Created: Nextcloud (ID: nextcloud-storage) (Owner: admin)
  ...
------------------------------------------------------------
✅ Migration completed successfully!
📦 JSON file backed up to: data/apps.json.backup
```

#### 4. Verify Migration
```bash
# Check migrated apps
sqlite3 proximity.db "SELECT catalog_id, hostname, status, owner_id FROM apps;"

# Verify app count matches
wc -l data/apps.json.backup
sqlite3 proximity.db "SELECT COUNT(*) FROM apps;"
```

#### 5. Test Application Access
- Navigate to the Dashboard
- Verify all apps show correct status
- Test starting/stopping containers
- Check reverse proxy access

#### Migration Notes

**What Gets Migrated:**
- ✅ All app configurations (catalog_id, hostname, resources)
- ✅ Container metadata (lxc_id, ip_address, node)
- ✅ Status information (running, stopped, etc.)
- ✅ Network configuration (vlan_id, ports)

**What Changes:**
- 📝 All apps assigned to first admin user
- 📝 Audit timestamps set to migration time
- 📝 Original JSON backed up automatically

**Rollback (if needed):**
```bash
# Stop the server
# Restore backup database
cp proximity_backup_YYYYMMDD_HHMMSS.db proximity.db
# Restart server
```

---

## Best Practices

1. **Resource Planning**: Ensure adequate CPU/RAM/disk on Proxmox nodes
2. **Regular Backups**: Schedule automated container backups
3. **Monitor Logs**: Check appliance and application logs regularly
4. **Update Templates**: Keep base templates updated for security
5. **Network Isolation**: Use `proximity-lan` for application isolation
6. **Access Control**: Use strong passwords and limit API access
7. **Documentation**: Document custom catalog items and configurations

---

## Performance Tuning

### Container Resources

Adjust per-app resources in catalog:
```json
"resources": {
  "cpu": 2,
  "memory": 4096,
  "disk": 50,
  "swap": 512
}
```

### Network Performance

- Use `vmbr0` for WAN-facing apps (bypasses appliance NAT)
- Enable jumbo frames for better throughput
- Monitor bandwidth with Proxmox graphs

### Storage Performance

- Use `local-lvm` for better disk I/O
- Consider NVMe storage for database containers
- Enable discard/TRIM for SSD optimization
