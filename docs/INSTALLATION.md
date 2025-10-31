# Installation Guide

## System Requirements

### Minimum Requirements
- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disk:** 20 GB SSD
- **OS:** Linux (Ubuntu 20.04+ or Debian 11+)
- **Proxmox:** 7.0+ (for container management)

### Recommended Requirements
- **CPU:** 4+ cores
- **RAM:** 8+ GB
- **Disk:** 50+ GB SSD
- **Network:** 1 Gbps connection

## Prerequisites

### Required Software
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Verify installations
docker --version
docker compose version
```

### Required Services
- **PostgreSQL** 13+ (for data storage)
- **Redis** 6.0+ (for caching and task queue)
- **Proxmox** 7.0+ (infrastructure)

## Deployment Methods

### Option 1: Docker Compose (Recommended)

#### 1. Clone Repository

```bash
git clone https://github.com/your-repo/proximity.git
cd proximity
```

#### 2. Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit environment file
nano backend/.env
```

**Key variables to set:**
```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=proximity.example.com,localhost

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/proximity

# Redis
REDIS_URL=redis://redis:6379/0

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587

# Sentry (optional)
SENTRY_DSN=https://key@sentry.io/project

# Proxmox (optional for initial setup)
PROXMOX_DEFAULT_HOST=your-proxmox-host
PROXMOX_DEFAULT_USER=root@pam
PROXMOX_DEFAULT_PASSWORD=your-password
```

#### 3. Start Services

```bash
# Pull latest images
docker compose pull

# Start services (in background)
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f backend
```

**Services started:**
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend (port 8000)
- Frontend (port 3000)

#### 4. Initialize Database

```bash
# Run migrations
docker compose exec backend python manage.py migrate

# Create superuser
docker compose exec backend python manage.py createsuperuser

# Load catalog data (optional)
docker compose exec backend python manage.py shell < scripts/load_catalog.py
```

#### 5. Access Application

- **Web UI:** http://localhost:3000
- **API:** http://localhost:8000/api/
- **Admin Panel:** http://localhost:8000/admin/

### Option 2: Manual Installation

#### 1. System Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and dependencies
sudo apt-get install python3.12 python3.12-venv python3-pip \
  postgresql postgresql-contrib redis-server \
  git curl wget

# Create application user
sudo useradd -m -s /bin/bash proximity
sudo su - proximity
```

#### 2. Backend Setup

```bash
# Clone repository
git clone https://github.com/your-repo/proximity.git
cd proximity/backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure settings
cp .env.example .env
nano .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

#### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Build for production
npm run build

# Output in build/ directory
```

#### 4. Web Server (Nginx)

Create `/etc/nginx/sites-available/proximity`:

```nginx
upstream django {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name proximity.example.com;

    client_max_body_size 100M;

    location /api/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/proximity \
           /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. Systemd Services

Create `/etc/systemd/system/proximity-backend.service`:

```ini
[Unit]
Description=Proximity Backend
After=network.target postgresql.service redis.service

[Service]
User=proximity
WorkingDirectory=/home/proximity/proximity/backend
ExecStart=/home/proximity/proximity/backend/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    proximity.wsgi

Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable proximity-backend
sudo systemctl start proximity-backend
sudo systemctl status proximity-backend
```

### Option 3: Kubernetes

For production Kubernetes deployments, use the provided Helm charts:

```bash
# Add Proximity Helm repository
helm repo add proximity https://charts.proximity.io

# Install Proximity
helm install proximity proximity/proximity \
  --namespace proximity \
  --create-namespace \
  -f values.yaml

# Wait for deployment
kubectl rollout status deployment/proximity-backend \
  -n proximity
```

## Post-Installation

### 1. Add Proxmox Host

```bash
# Via Django admin
# Go to http://localhost:8000/admin/
# Add ProxmoxHost with your details
```

Or via API:

```bash
curl -X POST http://localhost:8000/api/proxmox/hosts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pve",
    "host": "192.168.1.100",
    "port": 8006,
    "user": "root@pam",
    "password": "your-password",
    "is_active": true
  }'
```

### 2. Load Catalog

```bash
# Download or create catalog JSON files
mkdir -p catalog_data/
# Place application definitions in catalog_data/

# Backend automatically loads from this directory
```

### 3. Configure Email (Optional)

Edit `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@proximity.local
```

### 4. Set Up HTTPS (Recommended)

Using Let's Encrypt with Certbot:

```bash
sudo apt-get install certbot python3-certbot-nginx

sudo certbot --nginx -d proximity.example.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

Or manually:

```nginx
# /etc/nginx/sites-available/proximity
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of config ...
}

server {
    listen 80;
    return 301 https://$server_name$request_uri;
}
```

### 5. Configure Backups

Create backup directory:

```bash
mkdir -p /var/lib/proximity/backups
chown -R proximity:proximity /var/lib/proximity/backups
chmod 755 /var/lib/proximity/backups
```

Update settings:

```python
# backend/proximity/settings.py
BACKUP_PATH = '/var/lib/proximity/backups'
```

### 6. Test Installation

```bash
# Check backend health
curl http://localhost:8000/api/health/

# Check Proxmox connectivity
curl http://localhost:8000/api/proxmox/hosts/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test application deployment
curl -X POST http://localhost:8000/api/apps/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_id": "adminer",
    "hostname": "test-app"
  }'
```

## Troubleshooting Installation

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 PID
```

### Database Connection Error

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Connect to database
psql -U proximity -d proximity -h localhost
```

### Permission Denied Errors

```bash
# Fix permissions
sudo chown -R proximity:proximity /home/proximity/proximity
sudo chmod -R 755 /home/proximity/proximity
```

### Proxmox Connection Failed

```bash
# Test Proxmox connectivity
curl -k https://PROXMOX_HOST:8006/api2/json/nodes

# Check firewall
sudo ufw allow 8006/tcp
```

## Uninstallation

### Docker Compose

```bash
# Stop and remove containers
docker compose down -v

# Remove data volumes
docker volume prune
```

### Manual Installation

```bash
# Stop services
sudo systemctl stop proximity-backend
sudo systemctl disable proximity-backend

# Remove installation
sudo rm -rf /home/proximity/proximity
sudo userdel -r proximity

# Clean up
sudo apt-get autoremove
```

## Upgrades

### Docker Compose

```bash
# Pull latest version
git pull origin main

# Update images
docker compose pull

# Restart services
docker compose down
docker compose up -d

# Run migrations
docker compose exec backend python manage.py migrate
```

### Manual Installation

```bash
cd /home/proximity/proximity
git pull origin main

cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
python manage.py migrate

cd ../frontend
npm install
npm run build
```

## Next Steps

1. **[First Steps Guide](./FIRST_STEPS.md)** - Deploy your first application
2. **[API Documentation](./API.md)** - Explore the API
3. **[Deployment Guide](./DEPLOYMENT.md)** - Production setup
4. **[Development Guide](./DEVELOPMENT.md)** - Start contributing

---

**Installation Version:** 2.0
**Last Updated:** October 31, 2025
**Status:** ✅ Current and Tested
