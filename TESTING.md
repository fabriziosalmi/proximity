# 🧪 Proximity - Local Development & Testing Guide

## Quick Start

### 1. Setup Python Environment

```bash
cd /Users/fab/GitHub/proximity/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure Environment

Edit `backend/.env` with your Proxmox credentials:

```env
# Proxmox Configuration
PROXMOX_HOST=192.168.100.102
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=invaders
PROXMOX_VERIFY_SSL=false

# API Configuration
API_PORT=8765
API_HOST=0.0.0.0
DEBUG=true
```

### 3. Start Development Server

```bash
cd backend
python3 main.py
```

The server will start on:
- **UI**: http://localhost:8765
- **API**: http://localhost:8765/api/v1
- **API Docs (Swagger)**: http://localhost:8765/docs
- **API Docs (ReDoc)**: http://localhost:8765/redoc

### 4. Open UI in Browser

```bash
open http://localhost:8765
```

Or manually navigate to `http://localhost:8765` in your browser.

## Testing Features

### UI Testing

The web interface provides:

1. **Dashboard**
   - System statistics
   - Recent applications
   - Resource overview

2. **Application Catalog**
   - Browse available applications
   - Filter by category
   - One-click deployment wizard

3. **My Applications**
   - View all deployed apps
   - Start/stop containers
   - Monitor app status

4. **Infrastructure**
   - Proxmox nodes overview
   - Resource utilization
   - Container statistics

### API Testing

Test API endpoints with curl:

```bash
# Health check
curl http://localhost:8765/health

# System information
curl http://localhost:8765/api/v1/system/info

# List Proxmox nodes
curl http://localhost:8765/api/v1/system/nodes

# Get application catalog
curl http://localhost:8765/api/v1/apps/catalog

# List deployed applications
curl http://localhost:8765/api/v1/apps
```

### Deploy Test Application

#### Via UI:
1. Navigate to "Application Catalog"
2. Select an app (e.g., WordPress)
3. Click "🚀 Deploy"
4. Fill in the form:
   - **Hostname**: `wordpress-test`
   - **Node**: Leave "Auto-select" (or choose manually)
5. Click "Deploy Application"

#### Via API:
```bash
curl -X POST http://localhost:8765/api/v1/apps/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_id": "wordpress",
    "hostname": "wp-test-01",
    "config": {},
    "environment": {}
  }'
```

### Verify Deployment on Proxmox

Connect to Proxmox via SSH:

```bash
ssh root@192.168.100.102

# List all LXC containers
pct list

# Enter a container (replace 100 with actual VMID)
pct enter 100

# Check Docker containers
docker ps
docker-compose ps

# View Docker logs
docker-compose logs

# Exit container
exit
```

## Proxmox Test Environment

### Current Setup

- **Host**: 192.168.100.102
- **User**: root@pam
- **Password**: invaders
- **Access**: SSH and Web UI (https://192.168.100.102:8006)

### Container Configuration

Proximity creates unprivileged Alpine LXC containers with:
- **OS**: Alpine Linux 3.19
- **Features**: `nesting=1, keyctl=1`
- **Docker**: Automatically installed and configured
- **Ulimits**: Pre-configured to avoid permission errors

## Troubleshooting

### Backend Won't Start

```bash
# Check Python version (must be 3.13+)
python3 --version

# Reinstall dependencies
cd backend
pip install --upgrade -r requirements.txt

# Check Proxmox connectivity
ping 192.168.100.102
curl -k https://192.168.100.102:8006
```

### UI Not Loading

1. Verify backend is running: `curl http://localhost:8765/health`
2. Check browser console for errors (F12 → Console)
3. Clear browser cache
4. Try incognito/private mode

### Deployment Failures

```bash
# Check backend logs (terminal output)
# Look for error messages

# Verify Proxmox storage
ssh root@192.168.100.102 "pvesm status"

# Check LXC templates
ssh root@192.168.100.102 "pveam list local"

# View Proxmox logs
ssh root@192.168.100.102 "tail -f /var/log/pve/tasks/active"
```

### Container Issues

```bash
# List containers with status
ssh root@192.168.100.102 "pct list"

# Start a stopped container
ssh root@192.168.100.102 "pct start <VMID>"

# View container logs
ssh root@192.168.100.102 "pct enter <VMID>"
# Inside container:
journalctl -xe
docker logs <container_name>
```

### Database/Persistence Issues

```bash
# Check apps.json file
cat backend/data/apps.json

# Backup apps database
cp backend/data/apps.json backend/data/apps.json.backup

# Reset apps database (WARNING: deletes all app records)
echo '{"apps": []}' > backend/data/apps.json
```

## Development Tips

### Hot Reload

The development server auto-reloads on file changes. Just save your files and the server will restart automatically.

### API Documentation

Visit http://localhost:8765/docs for interactive API documentation with Swagger UI. You can test all endpoints directly from the browser.

### Debugging

Enable debug logging by setting in `.env`:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

Then watch the terminal for detailed logs.

### Testing Without Proxmox

If Proxmox is unavailable, the API will still start but show warnings. The UI will display connection errors gracefully.

## Next Steps

- Read [README.md](./README.md) for project overview
- Check [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines
- Deploy to production using [scripts/install.sh](./scripts/install.sh)

## Support

For issues or questions:
- Check existing GitHub Issues
- Review logs in terminal output
- Verify Proxmox is accessible and healthy
