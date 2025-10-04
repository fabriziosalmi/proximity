# Proximity

**Self-hosted Application Delivery Platform for Proxmox VE**

Proximity is a cloud-native application delivery platform that abstracts the complexity of Proxmox VE, providing a simple, web-based interface for deploying and managing containerized applications. Think Heroku or Cloudron, but for your own Proxmox infrastructure.

## 🌟 Features

- **One-Click App Deployment**: Deploy applications from a curated catalog with a single click
- **Fully Automated Setup**: Docker installation, networking, and proxy configuration—all automatic
- **Isolated Network Architecture**: Dedicated `proximity-lan` network with automatic DHCP/DNS
- **Reverse Proxy Integration**: Automatic Caddy vhost configuration for web applications
- **Web-Based Management**: Modern, responsive UI with real-time status monitoring
- **REST API**: Full API access for automation and integration
- **Secure by Default**: Unprivileged containers, network isolation, JWT authentication
- **Self-Hosted**: Complete control over your data and applications

## 🏗️ Architecture

### Platinum Edition Network

Proximity uses a **fully isolated network architecture** powered by a dedicated network appliance:

- **`proximity-lan` Bridge**: Isolated 10.20.0.0/24 network for all containers
- **Network Appliance** (VMID 9999):
  - DHCP server for automatic IP allocation (10.20.0.100-250)
  - DNS server with `.prox.local` domain resolution
  - NAT gateway for internet access
  - Caddy reverse proxy for HTTP/HTTPS routing
  - Management UI via Cockpit on port 9090

**[Read more →](docs/architecture.md)**

### Core Components

- **FastAPI Backend**: High-performance async API built with Python 3.13+
- **Proxmox Integration**: Direct API integration + SSH for container management
- **Network Orchestrator**: Automated network infrastructure provisioning
- **App Service**: Application lifecycle management with Docker Compose
- **Reverse Proxy Manager**: Dynamic Caddy vhost configuration
- **Authentication**: JWT-based with role-based access control

## 🚀 Quick Start

### Prerequisites

- Proxmox VE 8.x or later
- Root access to Proxmox host(s)
- Python 3.13+
- SSH access configured

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/proximity.git
   cd proximity/backend
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Proxmox credentials
   ```

4. **Initialize database:**
   ```bash
   python -c "from models.database import init_db; init_db()"
   ```

5. **Start the server:**
   ```bash
   python main.py
   ```

6. **Access the UI:**
   Open http://localhost:8765 in your browser

**[Detailed setup guide →](docs/deployment.md)**

## 📖 Documentation

- **[Architecture Guide](docs/architecture.md)** - System design, network topology, and technical details
- **[Deployment Guide](docs/deployment.md)** - Installation, configuration, operations, and troubleshooting
- **[Development Guide](docs/development.md)** - Contributing, code structure, and adding features
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues, fixes, and debugging techniques
- **[Changelog](docs/CHANGELOG.md)** - Version history and release notes
- **[Security Refactoring](docs/SECURITY_REFACTORING_SAFE_COMMANDS.md)** - Safe command system documentation
- **[Safe Commands Reference](docs/SAFE_COMMANDS_REFERENCE.md)** - Quick reference for secure container commands

## 🔒 Security

Proximity is built with security as a top priority:

- ✅ **JWT Authentication**: Secure token-based authentication with role-based access control
- ✅ **Safe Command System**: Predefined, read-only commands prevent arbitrary code execution
- ✅ **Audit Logging**: All command executions and critical actions are logged
- ✅ **Network Isolation**: Dedicated `proximity-lan` network separates containers
- ✅ **Unprivileged Containers**: All LXC containers run unprivileged by default
- ✅ **Input Validation**: Comprehensive parameter validation using Pydantic
- ✅ **No Command Injection**: All commands are hardcoded; user input never interpolated into shell commands

**October 2025 Security Update:**  
We've completely eliminated the dangerous arbitrary command execution endpoint (`/exec`) and replaced it with a secure, predefined command system. See [Security Refactoring Documentation](docs/SECURITY_REFACTORING_SAFE_COMMANDS.md) for details.

**Available Safe Commands:**
- 📋 logs, ✅ status, 💾 disk, ⚙️ processes, 🧠 memory, 🌐 network, 🐳 images, 📦 volumes, ⚙️ config, 💻 system

All commands are read-only, audited, and fully documented in the [Safe Commands Reference](docs/SAFE_COMMANDS_REFERENCE.md).

## 🔧 Configuration

Edit `.env` with your settings:

```ini
# Proxmox Connection
PROXMOX_HOST=192.168.1.100
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your_password
PROXMOX_VERIFY_SSL=false

# SSH Settings (for container management)
PROXMOX_SSH_HOST=192.168.1.100
PROXMOX_SSH_PORT=22
PROXMOX_SSH_USER=root
PROXMOX_SSH_PASSWORD=your_password

# API Settings
API_HOST=0.0.0.0
API_PORT=8765
DEBUG=true

# Security
JWT_SECRET_KEY=generate-a-secure-random-key
ENCRYPTION_KEY=generate-another-secure-key
```

## 📱 Application Catalog

Proximity includes pre-configured applications:

### Web Servers & Proxies
- **Nginx** - High-performance web server
- **Caddy** - Modern web server with automatic HTTPS
- **Traefik** - Cloud-native reverse proxy

### Content Management
- **WordPress** - Popular CMS and blogging platform
- **Ghost** - Modern publishing platform

### Development
- **VS Code Server** - Web-based VS Code editor
- **Gitea** - Self-hosted Git service

### And more...

**[Add custom apps →](docs/development.md#adding-a-new-catalog-item)**

## 🌐 API Documentation

Access interactive API docs at:
- **Swagger UI**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc

### Key Endpoints

**Applications:**
- `GET /api/v1/apps` - List deployed applications
- `POST /api/v1/apps/deploy` - Deploy new application
- `POST /api/v1/apps/{app_id}/actions` - Start/stop/restart
- `GET /api/v1/apps/{app_id}/logs` - View application logs
- `DELETE /api/v1/apps/{app_id}` - Delete application

**System:**
- `GET /api/v1/system/info` - System information
- `GET /api/v1/system/nodes` - Proxmox nodes
- `GET /api/v1/system/infrastructure/status` - Network appliance status
- `GET /api/v1/system/proxy/status` - Reverse proxy status

**Authentication:**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/logout` - Logout (audit logging)
- `GET /api/v1/auth/me` - Get current user info

## 🛡️ Security

- **Network Isolation**: All containers on isolated `proximity-lan` bridge
- **Unprivileged Containers**: LXC containers run unprivileged for security
- **JWT Authentication**: Secure API access with token-based auth
- **Role-Based Access**: Admin and user roles with different permissions
- **NAT Protection**: Containers not directly accessible from external network
- **Audit Logging**: All user actions logged for compliance
- **SSH Security**: Secure container management via SSH with key authentication

## 📊 Monitoring

**Dashboard Features:**
- Total and running application count
- Infrastructure nodes status
- Resource utilization metrics
- Reverse proxy status
- Real-time deployment tracking

**Application Management:**
- Start/stop/restart applications
- View logs in real-time
- Monitor resource usage
- Access via reverse proxy URLs

## 🔄 Development

### Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/proximity.git
cd proximity/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure and run
cp .env.example .env
python main.py
```

### Contributing

We welcome contributions! Please see:
- **[Development Guide](docs/development.md)** for code structure and workflow
- **[Contributing](CONTRIBUTING.md)** for contribution guidelines

### Project Structure

```
proximity/
├── backend/
│   ├── api/endpoints/       # REST API routes
│   ├── services/            # Business logic
│   ├── models/              # Database models
│   ├── catalog/             # Application catalog
│   ├── core/                # Core utilities
│   ├── main.py              # Application entry point
│   ├── app.js               # Frontend JavaScript
│   └── index.html           # Web UI
├── docs/                    # Documentation
│   ├── architecture.md
│   ├── deployment.md
│   ├── development.md
│   └── troubleshooting.md
└── README.md
```

## 📋 Roadmap

### ✅ Completed
- [x] Direct Proxmox API integration
- [x] LXC container management
- [x] Automated Docker installation via SSH
- [x] Isolated network infrastructure (`proximity-lan`)
- [x] Network appliance with DHCP/DNS/NAT
- [x] Caddy reverse proxy integration
- [x] Modern web interface
- [x] JWT authentication with RBAC
- [x] Application catalog system
- [x] Template caching for fast deployments
- [x] **Safe Command System** - Secure, predefined command execution (Oct 2025)
- [x] **Audit Logging** - Complete command execution tracking (Oct 2025)
- [x] **Command Injection Prevention** - Eliminated arbitrary command execution (Oct 2025)

### 🚧 In Progress
- [ ] Advanced dashboard with real-time metrics
- [ ] Application health monitoring
- [ ] Log aggregation and search

### 📋 Planned
- [ ] Multi-node deployment and load balancing
- [ ] Application scaling (horizontal/vertical)
- [ ] Backup and restore functionality
- [ ] Custom application builder UI
- [ ] Team collaboration features
- [ ] Marketplace integration
- [ ] IPv6 support
- [ ] Advanced firewall and network policies

## 📞 Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/proximity/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/proximity/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Proxmox VE** - The incredible virtualization platform
- **FastAPI** - Modern, fast web framework for APIs
- **Docker** - Containerization platform
- **Caddy** - Modern reverse proxy with automatic HTTPS
- **Alpine Linux** - Lightweight container base
- **Lucide Icons** - Beautiful icon library
- **Community** - All contributors and users

---

**Made with ❤️ for the self-hosting community**
