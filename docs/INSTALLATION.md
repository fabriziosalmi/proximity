# Installation Guide

## System Requirements

### Minimum Requirements
- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disk:** 20 GB
- **OS:** Linux (Ubuntu 20.04+ or Debian 11+)
- **Proxmox:** 7.0+ (for container management)

### Recommended Requirements
- **CPU:** 4+ cores
- **RAM:** 8+ GB
- **Disk:** 50+ GB

## Prerequisites

### Required Software
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt-get install docker-compose-plugin

# Verify installations
docker --version
docker compose version
```

## Deployment Methods

### Option 1: Docker Compose (Recommended)

#### 1. Clone Repository

```bash
git clone https://github.com/fabriziosalmi/proximity.git
cd proximity
```

#### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Key variables to set:**
```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=proximity.example.com,localhost

# Database (SQLite is used by default; for production use PostgreSQL)
# DATABASE_URL=postgresql://user:password@postgres:5432/proximity

# Proxmox
PROXMOX_HOST=your-proxmox-host
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your-password
PROXMOX_PORT=8006
PROXMOX_VERIFY_SSL=False

# Sentry (optional)
SENTRY_DSN=https://key@sentry.io/project
```

#### 3. Start Services

```bash
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
- Celery worker
- Celery beat scheduler
- Frontend (port 5173)

#### 4. Initialize Database

```bash
# Run migrations
docker compose exec backend python manage.py migrate
```

The first registered user automatically receives admin privileges. No `createsuperuser` step is required.

#### 5. Access Application

- **Web UI:** http://localhost:5173
- **API:** http://localhost:8000/api/
- **API Docs:** http://localhost:8000/api/docs
- **Django Admin:** http://localhost:8000/admin/

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
git clone https://github.com/fabriziosalmi/proximity.git
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

## Post-Installation

### 1. Add Proxmox Host

Via API:

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

Or via Settings in the web UI.

### 2. Load Catalog

The catalog is loaded from JSON files in the `catalog_data/` directory. The backend loads catalog data automatically on startup.

### 3. Set Up HTTPS (Recommended)

Using Let's Encrypt with Certbot:

```bash
sudo apt-get install certbot python3-certbot-nginx

sudo certbot --nginx -d proximity.example.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 4. Test Installation

```bash
# Check backend health
curl http://localhost:8000/api/health/

# Check Proxmox connectivity
curl http://localhost:8000/api/proxmox/hosts/ \
  -H "Authorization: Bearer YOUR_TOKEN"
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

