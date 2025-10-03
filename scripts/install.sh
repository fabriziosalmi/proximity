#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Proximity Installer for Proxmox VE
# This script installs Proximity on a Proxmox VE host
SCRIPT_VERSION="1.0.0"
PROXIMITY_VERSION="0.1.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROXIMITY_USER="proximity"
PROXIMITY_HOME="/opt/proximity"
PROXIMITY_REPO="https://github.com/yourusername/proximity.git"  # Update with actual repo
PROXIMITY_SERVICE="proximity"
PROXIMITY_PORT="8765"
PYTHON_VERSION="3.11"

# Logging
LOG_FILE="/var/log/proximity-install.log"

log() {
    echo -e "${1}" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

print_header() {
    log ""
    log "${BLUE}=================================================="
    log "           Proximity Installer v${SCRIPT_VERSION}"
    log "   Self-hosted App Delivery for Proxmox VE"
    log "==================================================${NC}"
    log ""
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
    log_success "Running as root"
}

check_proxmox() {
    if [[ ! -f /etc/pve/local/pve-ssl.pem ]]; then
        log_error "This doesn't appear to be a Proxmox VE installation"
        log_error "Please run this script on a Proxmox VE host"
        exit 1
    fi
    
    # Check Proxmox version
    if command -v pveversion >/dev/null 2>&1; then
        PVE_VERSION=$(pveversion | head -n1)
        log_success "Detected Proxmox VE: $PVE_VERSION"
    else
        log_warning "Could not detect Proxmox version"
    fi
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3 \
        python3-venv \
        python3-pip \
        git \
        curl \
        wget \
        unzip \
        build-essential \
        python3-dev \
        libssl-dev \
        libffi-dev \
        nginx \
        supervisor
    
    log_success "System dependencies installed"
}

create_user() {
    log_info "Creating proximity user..."
    
    if id "$PROXIMITY_USER" &>/dev/null; then
        log_info "User $PROXIMITY_USER already exists"
    else
        useradd --system --home "$PROXIMITY_HOME" --create-home --shell /bin/bash "$PROXIMITY_USER"
        log_success "Created user $PROXIMITY_USER"
    fi
    
    # Add proximity user to necessary groups
    usermod -a -G www-data "$PROXIMITY_USER"
}

setup_directories() {
    log_info "Setting up directories..."
    
    # Create main directory
    mkdir -p "$PROXIMITY_HOME"
    mkdir -p "$PROXIMITY_HOME/logs"
    mkdir -p "$PROXIMITY_HOME/catalog"
    mkdir -p "$PROXIMITY_HOME/data"
    
    # Set ownership
    chown -R "$PROXIMITY_USER:$PROXIMITY_USER" "$PROXIMITY_HOME"
    
    log_success "Directories created"
}

clone_repository() {
    log_info "Cloning Proximity repository..."
    
    if [[ -d "$PROXIMITY_HOME/.git" ]]; then
        log_info "Repository already exists, pulling latest changes..."
        cd "$PROXIMITY_HOME"
        sudo -u "$PROXIMITY_USER" git pull
    else
        # For now, we'll create the structure manually since we don't have a repo yet
        log_info "Creating application structure..."
        
        # Copy the backend files (in production, this would be a git clone)
        # For now, we'll create a minimal structure
        sudo -u "$PROXIMITY_USER" mkdir -p "$PROXIMITY_HOME/backend"
        sudo -u "$PROXIMITY_USER" mkdir -p "$PROXIMITY_HOME/frontend"
        sudo -u "$PROXIMITY_USER" mkdir -p "$PROXIMITY_HOME/scripts"
        
        # Create requirements.txt
        cat > "$PROXIMITY_HOME/backend/requirements.txt" << 'EOF'
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
proxmoxer>=2.0.1
pydantic>=2.4.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
httpx>=0.25.0
aiofiles>=23.2.1
python-multipart>=0.0.6
jinja2>=3.1.2
PyYAML>=6.0.1
EOF
    fi
    
    log_success "Application code ready"
}

setup_python_environment() {
    log_info "Setting up Python virtual environment..."
    
    cd "$PROXIMITY_HOME"
    
    # Create virtual environment
    sudo -u "$PROXIMITY_USER" python3 -m venv venv
    
    # Activate and install dependencies
    sudo -u "$PROXIMITY_USER" bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r backend/requirements.txt
    "
    
    log_success "Python environment configured"
}

create_lxc_template() {
    log_info "Creating Docker-ready LXC template..."
    
    # Template configuration
    TEMPLATE_ID=9999
    TEMPLATE_NAME="proximity-docker-template"
    TEMPLATE_HOSTNAME="docker-template"
    
    # Check if template already exists
    if [[ -f "/var/lib/vz/template/cache/${TEMPLATE_NAME}.tar.zst" ]]; then
        log_info "Docker template already exists"
        return 0
    fi
    
    # Download base template if not exists
    log_info "Downloading base Debian template..."
    pveam update
    
    # Get latest Debian template
    DEBIAN_TEMPLATE=$(pveam available | grep debian-12-standard | head -n1 | awk '{print $2}')
    if [[ -z "$DEBIAN_TEMPLATE" ]]; then
        log_error "Could not find Debian 12 template"
        exit 1
    fi
    
    # Download template if not already downloaded
    if ! pveam list local | grep -q "$DEBIAN_TEMPLATE"; then
        pveam download local "$DEBIAN_TEMPLATE"
    fi
    
    log_info "Creating template container..."
    
    # Destroy existing template container if exists
    if pct list | grep -q "^$TEMPLATE_ID"; then
        pct stop "$TEMPLATE_ID" || true
        pct destroy "$TEMPLATE_ID"
    fi
    
    # Create template container
    pct create "$TEMPLATE_ID" \
        "local:vztmpl/$DEBIAN_TEMPLATE" \
        --hostname "$TEMPLATE_HOSTNAME" \
        --memory 2048 \
        --cores 2 \
        --rootfs local-lvm:8 \
        --net0 name=eth0,bridge=vmbr0,ip=dhcp \
        --features nesting=1,keyctl=1 \
        --unprivileged 1 \
        --password proxmox123
    
    log_info "Starting template container..."
    pct start "$TEMPLATE_ID"
    
    # Wait for container to be ready
    sleep 15
    
    log_info "Installing Docker in template..."
    
    # Install Docker and Docker Compose
    pct exec "$TEMPLATE_ID" -- bash -c "
        apt-get update
        apt-get install -y ca-certificates curl gnupg lsb-release
        
        # Add Docker's official GPG key
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg
        
        # Add Docker repository
        echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \$(. /etc/os-release && echo \"\$VERSION_CODENAME\") stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # Enable Docker service
        systemctl enable docker
        systemctl start docker
        
        # Test Docker installation
        docker --version
        docker compose version
        
        # Clean up
        apt-get clean
        rm -rf /var/lib/apt/lists/*
    "
    
    log_info "Stopping template container..."
    pct stop "$TEMPLATE_ID"
    
    log_info "Creating template archive..."
    
    # Create template
    vzdump "$TEMPLATE_ID" \
        --dumpdir /var/lib/vz/template/cache \
        --compress zstd \
        --mode snapshot
    
    # Find the created backup file
    BACKUP_FILE=$(ls -t /var/lib/vz/template/cache/vzdump-lxc-${TEMPLATE_ID}-*.tar.zst | head -n1)
    
    if [[ -f "$BACKUP_FILE" ]]; then
        # Move to template directory with proper name
        mv "$BACKUP_FILE" "/var/lib/vz/template/cache/${TEMPLATE_NAME}.tar.zst"
        log_success "Template created: ${TEMPLATE_NAME}.tar.zst"
    else
        log_error "Failed to create template backup"
        exit 1
    fi
    
    # Clean up template container
    pct destroy "$TEMPLATE_ID"
    
    log_success "Docker-ready LXC template created successfully"
}

create_configuration() {
    log_info "Creating configuration files..."
    
    # Create environment file
    cat > "$PROXIMITY_HOME/.env" << EOF
# Proxmox Configuration
PROXMOX_HOST=localhost
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=
PROXMOX_VERIFY_SSL=false
PROXMOX_PORT=8006

# API Configuration
API_HOST=0.0.0.0
API_PORT=$PROXIMITY_PORT
DEBUG=false

# Application Configuration
APP_NAME=Proximity
APP_VERSION=$PROXIMITY_VERSION
LOG_LEVEL=INFO

# LXC Configuration
DEFAULT_LXC_TEMPLATE=local:vztmpl/proximity-docker-template.tar.zst
LXC_STORAGE=local-lvm
LXC_MEMORY=2048
LXC_CORES=2
LXC_DISK_SIZE=8G
LXC_BRIDGE=vmbr0

# Paths
APP_CATALOG_PATH=$PROXIMITY_HOME/catalog
EOF
    
    chown "$PROXIMITY_USER:$PROXIMITY_USER" "$PROXIMITY_HOME/.env"
    chmod 600 "$PROXIMITY_HOME/.env"
    
    log_success "Configuration files created"
}

create_systemd_service() {
    log_info "Creating systemd service..."
    
    cat > "/etc/systemd/system/${PROXIMITY_SERVICE}.service" << EOF
[Unit]
Description=Proximity - Self-hosted App Delivery Platform
After=network.target multi-user.target
Wants=network.target

[Service]
Type=exec
User=$PROXIMITY_USER
Group=$PROXIMITY_USER
WorkingDirectory=$PROXIMITY_HOME/backend
Environment=PATH=$PROXIMITY_HOME/venv/bin
ExecStart=$PROXIMITY_HOME/venv/bin/uvicorn main:app --host 0.0.0.0 --port $PROXIMITY_PORT
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=10

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROXIMITY_HOME
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$PROXIMITY_SERVICE"
    
    log_success "Systemd service created and enabled"
}

configure_nginx() {
    log_info "Configuring Nginx reverse proxy..."
    
    # Create Nginx configuration
    cat > "/etc/nginx/sites-available/proximity" << EOF
server {
    listen 80;
    server_name _;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;
    
    # SSL configuration (using Proxmox certificates)
    ssl_certificate /etc/pve/local/pve-ssl.pem;
    ssl_certificate_key /etc/pve/local/pve-ssl.key;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:$PROXIMITY_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Static files (for future frontend)
    location /static/ {
        alias $PROXIMITY_HOME/frontend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/proximity /etc/nginx/sites-enabled/
    
    # Test Nginx configuration
    nginx -t
    
    # Reload Nginx
    systemctl reload nginx
    
    log_success "Nginx reverse proxy configured"
}

setup_firewall() {
    log_info "Configuring firewall..."
    
    # Check if ufw is available
    if command -v ufw >/dev/null 2>&1; then
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow "$PROXIMITY_PORT/tcp"
        log_success "UFW rules added"
    elif command -v iptables >/dev/null 2>&1; then
        # Basic iptables rules
        iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        iptables -A INPUT -p tcp --dport 443 -j ACCEPT
        iptables -A INPUT -p tcp --dport "$PROXIMITY_PORT" -j ACCEPT
        log_success "Iptables rules added"
    else
        log_warning "No firewall detected. Please ensure ports 80, 443, and $PROXIMITY_PORT are accessible"
    fi
}

create_default_catalog() {
    log_info "Creating default application catalog..."
    
    cat > "$PROXIMITY_HOME/catalog/catalog.json" << 'EOF'
{
  "items": [
    {
      "id": "wordpress",
      "name": "WordPress",
      "description": "Popular content management system and blogging platform",
      "version": "latest",
      "icon": "https://s.w.org/style/images/about/WordPress-logotype-wmark.png",
      "category": "CMS",
      "docker_compose": {
        "version": "3.8",
        "services": {
          "wordpress": {
            "image": "wordpress:latest",
            "ports": ["80:80"],
            "environment": {
              "WORDPRESS_DB_HOST": "db",
              "WORDPRESS_DB_USER": "wordpress",
              "WORDPRESS_DB_PASSWORD": "wordpress_password",
              "WORDPRESS_DB_NAME": "wordpress"
            },
            "volumes": ["wordpress_data:/var/www/html"],
            "depends_on": ["db"]
          },
          "db": {
            "image": "mysql:8.0",
            "environment": {
              "MYSQL_DATABASE": "wordpress",
              "MYSQL_USER": "wordpress",
              "MYSQL_PASSWORD": "wordpress_password",
              "MYSQL_ROOT_PASSWORD": "root_password"
            },
            "volumes": ["db_data:/var/lib/mysql"]
          }
        },
        "volumes": {
          "wordpress_data": {},
          "db_data": {}
        }
      },
      "ports": [80],
      "volumes": ["wordpress_data", "db_data"],
      "environment": {
        "WORDPRESS_DB_PASSWORD": "wordpress_password",
        "MYSQL_ROOT_PASSWORD": "root_password"
      },
      "min_memory": 1024,
      "min_cpu": 1
    },
    {
      "id": "nextcloud",
      "name": "Nextcloud",
      "description": "Self-hosted file sync and share platform",
      "version": "latest",
      "icon": "https://nextcloud.com/wp-content/themes/next/assets/img/common/nextcloud-square-logo.png",
      "category": "Storage",
      "docker_compose": {
        "version": "3.8",
        "services": {
          "nextcloud": {
            "image": "nextcloud:latest",
            "ports": ["80:80"],
            "environment": {
              "MYSQL_HOST": "db",
              "MYSQL_USER": "nextcloud",
              "MYSQL_PASSWORD": "nextcloud_password",
              "MYSQL_DATABASE": "nextcloud"
            },
            "volumes": ["nextcloud_data:/var/www/html"],
            "depends_on": ["db"]
          },
          "db": {
            "image": "mysql:8.0",
            "environment": {
              "MYSQL_DATABASE": "nextcloud",
              "MYSQL_USER": "nextcloud",
              "MYSQL_PASSWORD": "nextcloud_password",
              "MYSQL_ROOT_PASSWORD": "root_password"
            },
            "volumes": ["db_data:/var/lib/mysql"]
          }
        },
        "volumes": {
          "nextcloud_data": {},
          "db_data": {}
        }
      },
      "ports": [80],
      "volumes": ["nextcloud_data", "db_data"],
      "environment": {
        "MYSQL_PASSWORD": "nextcloud_password",
        "MYSQL_ROOT_PASSWORD": "root_password"
      },
      "min_memory": 2048,
      "min_cpu": 2
    },
    {
      "id": "portainer",
      "name": "Portainer",
      "description": "Container management platform",
      "version": "latest",
      "category": "DevOps",
      "docker_compose": {
        "version": "3.8",
        "services": {
          "portainer": {
            "image": "portainer/portainer-ce:latest",
            "ports": ["9000:9000"],
            "volumes": [
              "/var/run/docker.sock:/var/run/docker.sock",
              "portainer_data:/data"
            ],
            "restart": "always"
          }
        },
        "volumes": {
          "portainer_data": {}
        }
      },
      "ports": [9000],
      "volumes": ["portainer_data"],
      "environment": {},
      "min_memory": 512,
      "min_cpu": 1
    }
  ]
}
EOF
    
    chown "$PROXIMITY_USER:$PROXIMITY_USER" "$PROXIMITY_HOME/catalog/catalog.json"
    
    log_success "Default catalog created"
}

start_services() {
    log_info "Starting Proximity services..."
    
    # Start and enable Proximity service
    systemctl start "$PROXIMITY_SERVICE"
    
    # Check if service started successfully
    sleep 5
    
    if systemctl is-active --quiet "$PROXIMITY_SERVICE"; then
        log_success "Proximity service started successfully"
    else
        log_error "Failed to start Proximity service"
        systemctl status "$PROXIMITY_SERVICE"
        exit 1
    fi
}

display_completion_info() {
    log ""
    log_success "🎉 Proximity installation completed successfully!"
    log ""
    log "${GREEN}Access Information:${NC}"
    
    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    log "  • Web Interface: https://$SERVER_IP"
    log "  • API Documentation: https://$SERVER_IP/docs"
    log "  • Direct API: https://$SERVER_IP:$PROXIMITY_PORT"
    log ""
    log "${YELLOW}Important Notes:${NC}"
    log "  • Default Proxmox credentials are used (root@pam)"
    log "  • Please update the password in: $PROXIMITY_HOME/.env"
    log "  • Service logs: journalctl -u $PROXIMITY_SERVICE -f"
    log "  • Installation log: $LOG_FILE"
    log ""
    log "${BLUE}Next Steps:${NC}"
    log "  1. Update Proxmox credentials in the configuration"
    log "  2. Access the web interface to deploy your first app"
    log "  3. Check the documentation for advanced configuration"
    log ""
}

main() {
    print_header
    
    log_info "Starting Proximity installation..."
    
    # Pre-installation checks
    check_root
    check_proxmox
    
    # Installation steps
    install_dependencies
    create_user
    setup_directories
    clone_repository
    setup_python_environment
    create_lxc_template
    create_configuration
    create_default_catalog
    create_systemd_service
    configure_nginx
    setup_firewall
    start_services
    
    # Post-installation
    display_completion_info
    
    log_success "Installation completed in $(date)"
}

# Trap errors and cleanup
trap 'log_error "Installation failed at line $LINENO. Check $LOG_FILE for details."' ERR

# Create log file
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

# Run main installation
main "$@"