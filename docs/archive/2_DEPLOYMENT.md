# Proximity Deployment Guide

Complete instructions for installing, configuring, and running Proximity in development and production environments.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Development)](#quick-start-development)
- [Production Deployment](#production-deployment)
  - [Option 1: Systemd Service](#option-1-systemd-service)
  - [Option 2: Docker Container](#option-2-docker-container)
  - [Option 3: Reverse Proxy Setup](#option-3-reverse-proxy-setup)
- [Configuration Reference](#configuration-reference)
- [First-Time Setup](#first-time-setup)
- [Network Configuration](#network-configuration)
- [Security Hardening](#security-hardening)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

**Minimum:**
- Proxmox VE 7.0 or higher
- 2 CPU cores
- 4 GB RAM
- 20 GB disk space

**Recommended:**
- Proxmox VE 8.0+
- 4+ CPU cores
- 8+ GB RAM
- 50+ GB SSD storage
- Separate disk for container storage

### Software Requirements

**On Proxmox Host:**
- Proxmox VE 7.0+ installed and configured
- Root SSH access
- At least one network bridge (typically `vmbr0`)
- Internet connectivity

**On Deployment Machine** (can be your workstation or Proxmox host):
- Python 3.9 or higher
- pip3 (Python package manager)
- Git
- curl or wget

### Network Requirements

- **Management Network**: Access to Proxmox web UI (default: port 8006)
- **Application Port**: Available port for Proximity UI (default: 8765)
- **Container Network**: Existing or ability to create network bridge

---

## Quick Start (Development)

Perfect for testing, development, or quick demos.

### Step 1: Clone the Repository

```bash
git clone https://github.com/fabriziosalmi/proximity.git
cd proximity/backend
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip3 install -r requirements.txt
```

If you encounter permission errors, use a virtual environment:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip3 install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration with your favorite editor
nano .env  # or vim, code, etc.
```

**Required Configuration:**

```bash
# Proxmox Connection
PROXMOX_HOST=192.168.1.100  # Your Proxmox host IP
PROXMOX_USER=root@pam       # Proxmox user
PROXMOX_PASSWORD=your-password-here
PROXMOX_PORT=8006
PROXMOX_VERIFY_SSL=false    # Set to true if using valid SSL cert

# SSH Access (for container management)
PROXMOX_SSH_HOST=192.168.1.100  # Usually same as PROXMOX_HOST
PROXMOX_SSH_USER=root
PROXMOX_SSH_PASSWORD=your-password-here  # Or use SSH keys

# Application Settings
API_HOST=0.0.0.0
API_PORT=8765
DEBUG=true  # Set to false in production

# Security
JWT_SECRET_KEY=change-this-to-a-random-secret-key-minimum-32-chars

# Database (default is fine for development)
DATABASE_URL=sqlite:///./proximity.db
```

### Step 4: Start Proximity

```bash
python3 main.py
```

You should see output like:

```
✓ Sentry initialized (environment=development, release=0.1.0)
====================================================================
STEP 0: Initializing Database
====================================================================
✓ Database initialized successfully
====================================================================
STEP 1: Connecting to Proxmox
====================================================================
✓ Proxmox connection successful
====================================================================
STEP 2: Network Configuration
====================================================================
✓ Using vmbr0 with DHCP (simple and reliable)
====================================================================
STEP 3: Loading Application Catalog
====================================================================
✓ Loaded catalog with 12 applications
====================================================================
STEP 4: Initializing Scheduler Service (AUTO Mode)
====================================================================
✓ Scheduler Service initialized
   • Daily backups scheduled for 2:00 AM
   • Weekly update checks scheduled for Sunday 3:00 AM
====================================================================
🚀 Proximity API started on 0.0.0.0:8765
```

### Step 5: Access the UI

Open your browser and navigate to:

```
http://localhost:8765
```

Or from another machine on your network:

```
http://<proxmox-host-ip>:8765
```

Proceed to [First-Time Setup](#first-time-setup) →

---

## Production Deployment

For production use, run Proximity as a system service with proper monitoring and automatic restarts.

### Option 1: Systemd Service

The most reliable method for Linux systems.

#### Step 1: Create Service User

```bash
# Create dedicated user (no login shell)
sudo useradd -r -s /bin/false -d /opt/proximity proximity

# Create installation directory
sudo mkdir -p /opt/proximity
sudo chown proximity:proximity /opt/proximity
```

#### Step 2: Install Proximity

```bash
# Clone repository
cd /opt/proximity
sudo -u proximity git clone https://github.com/fabriziosalmi/proximity.git .

# Install dependencies in virtual environment
sudo -u proximity python3 -m venv venv
sudo -u proximity venv/bin/pip install -r backend/requirements.txt
```

#### Step 3: Configure Environment

```bash
# Copy and edit configuration
cd /opt/proximity/backend
sudo -u proximity cp .env.example .env
sudo -u proximity nano .env
```

**Production Configuration Notes:**
- Set `DEBUG=false`
- Use strong `JWT_SECRET_KEY` (generate with: `openssl rand -hex 32`)
- Consider using PostgreSQL instead of SQLite for multi-user scenarios
- Enable Sentry for error tracking (optional)

#### Step 4: Create Systemd Service

Create `/etc/systemd/system/proximity.service`:

```ini
[Unit]
Description=Proximity Application Delivery Platform
After=network.target

[Service]
Type=simple
User=proximity
Group=proximity
WorkingDirectory=/opt/proximity/backend
Environment="PATH=/opt/proximity/venv/bin"
ExecStart=/opt/proximity/venv/bin/python3 /opt/proximity/backend/main.py
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

# Security Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/proximity
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictNamespaces=true

[Install]
WantedBy=multi-user.target
```

#### Step 5: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable proximity

# Start service
sudo systemctl start proximity

# Check status
sudo systemctl status proximity

# View logs
sudo journalctl -u proximity -f
```

### Option 2: Docker Container

Run Proximity in a Docker container (coming soon).

```dockerfile
# Dockerfile (example - to be added in future release)
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8765

CMD ["python", "main.py"]
```

```bash
# Build and run
docker build -t proximity:latest .
docker run -d \
  --name proximity \
  -p 8765:8765 \
  -v proximity-data:/app/data \
  -e PROXMOX_HOST=192.168.1.100 \
  -e PROXMOX_USER=root@pam \
  -e PROXMOX_PASSWORD=your-password \
  proximity:latest
```

### Option 3: Reverse Proxy Setup

Expose Proximity securely with Nginx or Caddy.

#### Nginx Configuration

Create `/etc/nginx/sites-available/proximity`:

```nginx
server {
    listen 80;
    server_name proximity.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name proximity.example.com;

    # SSL Configuration (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/proximity.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/proximity.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Proxy to Proximity
    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for future features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/proximity /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Caddy Configuration

Create `Caddyfile`:

```caddy
proximity.example.com {
    reverse_proxy localhost:8765

    # Automatic HTTPS with Let's Encrypt
    tls your-email@example.com
}
```

Start Caddy:

```bash
caddy run --config Caddyfile
```

---

## Configuration Reference

Complete reference for all `.env` variables:

### Proxmox Connection

```bash
# Proxmox API Endpoint
PROXMOX_HOST=192.168.1.100     # Proxmox host IP or hostname
PROXMOX_PORT=8006              # Proxmox web interface port
PROXMOX_USER=root@pam          # Proxmox user (format: user@realm)
PROXMOX_PASSWORD=password      # User password
PROXMOX_VERIFY_SSL=false       # Verify SSL certificate (true for production)
```

### SSH Access

```bash
# SSH for container management (usually same as Proxmox)
PROXMOX_SSH_HOST=192.168.1.100
PROXMOX_SSH_PORT=22
PROXMOX_SSH_USER=root
PROXMOX_SSH_PASSWORD=password  # Or use SSH keys
```

### Application Settings

```bash
# API Server
API_HOST=0.0.0.0               # Listen address (0.0.0.0 for all interfaces)
API_PORT=8765                  # API and UI port
DEBUG=false                    # Enable debug mode (verbose logging)

# Application Metadata
APP_NAME=Proximity
APP_VERSION=0.1.0
```

### LXC Container Defaults

```bash
# Default LXC Template
DEFAULT_LXC_TEMPLATE=local:vztmpl/proximity-alpine-docker.tar.zst
FALLBACK_LXC_TEMPLATE=local:vztmpl/alpine-3.19-default_20231225_amd64.tar.xz

# Default Resources
LXC_MEMORY=2048                # Default RAM (MB)
LXC_CORES=2                    # Default CPU cores
LXC_DISK_SIZE=8G               # Default disk size
LXC_STORAGE=local-lvm          # Storage backend

# Network
LXC_BRIDGE=vmbr0               # Network bridge
LXC_NET_CONFIG=name=eth0,bridge=vmbr0,ip=dhcp
```

### Security

```bash
# JWT Authentication
JWT_SECRET_KEY=your-secret-key-here  # REQUIRED: Generate with openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MINUTES=60       # Token expiration

# Container Passwords
LXC_ROOT_PASSWORD=invaders           # Default root password for containers
LXC_PASSWORD_RANDOM=false            # Generate random passwords per container
LXC_PASSWORD_LENGTH=16               # Random password length
```

### Port Allocation

```bash
# Port ranges for app access
PUBLIC_PORT_RANGE_START=30000        # Public access ports start
PUBLIC_PORT_RANGE_END=30999          # Public access ports end
INTERNAL_PORT_RANGE_START=40000      # Internal iframe ports start
INTERNAL_PORT_RANGE_END=40999        # Internal iframe ports end
```

### Database

```bash
# SQLite (default)
DATABASE_URL=sqlite:///./proximity.db

# PostgreSQL (optional, for multi-user)
# DATABASE_URL=postgresql://user:password@localhost/proximity
```

### Monitoring (Optional)

```bash
# Sentry Error Tracking
SENTRY_DSN=                          # Leave empty to disable
SENTRY_ENVIRONMENT=production        # Environment tag
SENTRY_RELEASE=0.1.0                 # Release version
```

### Application Catalog

```bash
# Custom catalog path (optional)
APP_CATALOG_PATH=./catalog           # Path to app definitions
```

---

## First-Time Setup

After starting Proximity for the first time, follow the **Power On** onboarding:

### Step 1: Power On

1. Navigate to `http://localhost:8765` (or your configured address)
2. You'll see the "Proximity is Powering On" screen
3. Click **"Power On Proximity"**

### Step 2: Register Admin Account

1. **Username**: Choose your admin username (3-30 characters)
2. **Email**: Your email address
3. **Password**: Strong password (minimum 8 characters)
4. Click **"Create Admin Account"**

### Step 3: Configure Proxmox Connection

1. **Host**: Your Proxmox server IP (e.g., `192.168.1.100`)
2. **Port**: Proxmox port (default: `8006`)
3. **User**: Proxmox username with format `user@realm` (e.g., `root@pam`)
4. **Password**: Proxmox user password
5. **Verify SSL**: Enable if using valid SSL certificate
6. Click **"Test Connection"**
7. If successful, click **"Save and Continue"**

### Step 4: Welcome to Proximity

You're now ready to deploy applications!

1. Browse the **App Store** (Catalog view)
2. Click **Deploy** on any application
3. Watch the deployment progress
4. Access your app from **My Apps**

---

## Network Configuration

Proximity supports two network architectures:

### Simple Mode (Default)

**Recommended for most users.**

- Uses existing `vmbr0` bridge with DHCP
- Docker containers use host networking
- Automatic port allocation for access
- No additional configuration required

**Pros:**
- ✅ Simple setup
- ✅ No network knowledge required
- ✅ Works out of the box

**Cons:**
- ❌ Apps accessed by IP:PORT (e.g., `192.168.1.101:30001`)
- ❌ No custom domains without external reverse proxy

### Advanced Mode (Platinum Edition)

**For advanced users who want custom domains and unified access.**

- Dedicated network appliance LXC with NAT/routing
- DHCP server for automatic IP assignment
- DNS server with `.prox.local` domain resolution
- Caddy reverse proxy for unified app access
- Isolated app network (`10.20.0.0/24`)

**Pros:**
- ✅ Custom domains (e.g., `wordpress.prox.local`)
- ✅ Automatic SSL with Caddy
- ✅ Network isolation between apps
- ✅ Unified access point

**Cons:**
- ❌ Requires manual configuration
- ❌ Additional resource overhead
- ❌ More complex troubleshooting

**Platinum Edition setup:** See [docs/DOCKER_HOST_NETWORKING.md](DOCKER_HOST_NETWORKING.md)

---

## Security Hardening

### Production Security Checklist

- [ ] **Change default passwords**: Update `LXC_ROOT_PASSWORD`
- [ ] **Use strong JWT secret**: Generate with `openssl rand -hex 32`
- [ ] **Enable SSL**: Use reverse proxy with Let's Encrypt
- [ ] **Firewall rules**: Limit access to Proximity port (8765)
- [ ] **Proxmox access**: Use dedicated Proxmox user with minimal permissions
- [ ] **SSH keys**: Replace password SSH with key-based authentication
- [ ] **Regular updates**: Keep Proxmox, Proximity, and containers updated
- [ ] **Backup strategy**: Configure automated backups
- [ ] **Audit logging**: Review logs regularly
- [ ] **Network segmentation**: Isolate app network from management network

### Creating Dedicated Proxmox User

Instead of using `root@pam`, create a dedicated user:

```bash
# On Proxmox host
pveum user add proximity@pve
pveum passwd proximity@pve

# Grant required permissions
pveum aclmod / -user proximity@pve -role Administrator
```

Update `.env`:

```bash
PROXMOX_USER=proximity@pve
PROXMOX_PASSWORD=dedicated-password
```

---

## Troubleshooting

### Cannot Connect to Proxmox

**Symptoms:** "Proxmox connection failed" on startup

**Solutions:**
1. Verify Proxmox is accessible: `curl -k https://<PROXMOX_HOST>:8006`
2. Check credentials in `.env`
3. Ensure firewall allows port 8006
4. Verify Proxmox user has sufficient permissions

### Port Already in Use

**Symptoms:** `Address already in use` error on startup

**Solutions:**
1. Check if Proximity is already running: `ps aux | grep main.py`
2. Change `API_PORT` in `.env`
3. Kill process using port: `sudo lsof -ti:8765 | xargs kill`

### Database Locked

**Symptoms:** `database is locked` errors

**Solutions:**
1. Ensure only one Proximity instance is running
2. Remove lock file: `rm proximity.db-journal`
3. Consider using PostgreSQL for multi-user scenarios

### Deployment Fails

**Symptoms:** Apps stuck in "deploying" status

**Solutions:**
1. Check Proxmox logs: `/var/log/pve/tasks/`
2. Verify SSH access to Proxmox
3. Ensure sufficient storage on Proxmox
4. Check container logs in Proximity console
5. Verify template exists: `pveam list local`

### Apps Won't Start

**Symptoms:** Apps show "error" status after deployment

**Solutions:**
1. Open **Console** from app card
2. Check Docker status: `docker ps -a`
3. View logs: `docker-compose logs`
4. Verify network connectivity: `ping google.com`
5. Check resource limits (CPU, RAM, disk)

### Backup Failures

**Symptoms:** Backup jobs fail or hang

**Solutions:**
1. Verify storage has space: `pvesm status`
2. Check backup logs in Proxmox UI
3. Try different compression: `zstd` vs `gzip` vs `none`
4. Use `stop` mode instead of `snapshot` for problematic containers

---

## Next Steps

✅ **Proximity is now deployed!**

Continue to:
- **[Usage Guide](3_USAGE_GUIDE.md)** - Learn to use every feature
- **[Architecture Guide](4_ARCHITECTURE.md)** - Understand how it works
- **[Development Guide](5_DEVELOPMENT.md)** - Contribute to the project

---

<div align="center">

[← Back to README](../README.md) • [Next: Usage Guide →](3_USAGE_GUIDE.md)

</div>
