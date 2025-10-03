# Proximity

**Self-hosted Application Delivery Platform for Proxmox VE**

Proximity is a cloud-native application delivery platform that abstracts the complexity of Proxmox VE, providing a simple, web-based interface for deploying and managing containerized applications. Think Heroku or Cloudron, but for your own Proxmox infrastructure.

## 🌟 Features

- **One-Click App Deployment**: Deploy applications from a curated catalog with a single click
- **Application-Centric Approach**: Focus on apps, not infrastructure
- **Docker-Based**: All applications run in LXC containers with Docker for maximum efficiency
- **Web-Based Management**: Modern, responsive web interface
- **REST API**: Full API access for automation and integration
- **Resource Monitoring**: Real-time monitoring of application resources
- **Secure by Default**: Proper isolation and security practices
- **Self-Hosted**: Complete control over your data and applications

## 🏗️ Architecture

### Native Cloud Architecture
- **FastAPI Backend**: High-performance async API built with Python
- **Direct Proxmox Integration**: Native API integration for maximum performance
- **LXC + Docker**: Efficient containerization with LXC containers running Docker
- **Microservices Design**: Clean separation of concerns with service layers

### Core Components
- **Proxmox Service**: Direct integration with Proxmox VE API
- **App Service**: Business logic for application lifecycle management
- **REST API**: RESTful endpoints for all operations
- **Web Interface**: Modern web UI (SvelteKit/Vue - coming soon)

## 🚀 Quick Start

### Prerequisites
- Proxmox VE 7.x or 8.x
- Root access to Proxmox host
- Internet connection for downloading templates

### Installation

1. **Download and run the installer on your Proxmox host:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/yourusername/proximity/main/scripts/install.sh | bash
   ```

2. **Configure Proxmox credentials:**
   ```bash
   sudo nano /opt/proximity/.env
   # Update PROXMOX_PASSWORD with your root password
   ```

3. **Restart the service:**
   ```bash
   sudo systemctl restart proximity
   ```

4. **Access the web interface:**
   ```
   https://your-proxmox-ip
   ```

## 📁 Project Structure

```
proximity/
├── backend/                    # FastAPI backend
│   ├── api/
│   │   └── endpoints/
│   │       ├── apps.py        # Application endpoints
│   │       └── system.py      # System endpoints
│   ├── core/
│   │   └── config.py          # Configuration management
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── app_service.py     # Business logic
│   │   └── proxmox_service.py # Proxmox API wrapper
│   ├── main.py                # FastAPI application
│   └── requirements.txt
├── frontend/                   # Web interface (coming soon)
├── scripts/
│   └── install.sh             # Installation script
└── README.md
```

## 🔧 Configuration

The main configuration is in `/opt/proximity/.env`:

```env
# Proxmox Configuration
PROXMOX_HOST=localhost
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your_password_here
PROXMOX_VERIFY_SSL=false

# API Configuration
API_PORT=8765
DEBUG=false

# LXC Configuration
LXC_MEMORY=2048
LXC_CORES=2
LXC_DISK_SIZE=8G
```

## 🌐 API Documentation

Once installed, access the interactive API documentation at:
- **Swagger UI**: https://your-proxmox-ip/docs
- **ReDoc**: https://your-proxmox-ip/redoc

### Key Endpoints

#### Applications
- `GET /api/v1/apps` - List all applications
- `POST /api/v1/apps/deploy` - Deploy new application
- `GET /api/v1/apps/{app_id}` - Get application details
- `POST /api/v1/apps/{app_id}/actions` - Control application (start/stop/restart)
- `DELETE /api/v1/apps/{app_id}` - Delete application

#### System
- `GET /api/v1/system/info` - System information
- `GET /api/v1/system/nodes` - Proxmox nodes
- `GET /api/v1/system/health` - Health check

#### Catalog
- `GET /api/v1/apps/catalog` - Available applications

## 📱 Application Catalog

Proximity comes with a curated catalog of popular applications:

### Content Management
- **WordPress** - Popular CMS and blogging platform
- **Nextcloud** - Self-hosted file sync and share

### DevOps
- **Portainer** - Container management platform

### Adding Custom Applications

Applications are defined in `/opt/proximity/catalog/catalog.json`. Each application includes:

```json
{
  "id": "my-app",
  "name": "My Application",
  "description": "Description of the app",
  "category": "Category",
  "docker_compose": {
    "version": "3.8",
    "services": {
      "app": {
        "image": "my-app:latest",
        "ports": ["80:80"]
      }
    }
  },
  "ports": [80],
  "min_memory": 1024,
  "min_cpu": 1
}
```

## 🛡️ Security

- **Isolated Containers**: Each application runs in its own LXC container
- **Unprivileged Containers**: All containers run unprivileged for security
- **Nginx Reverse Proxy**: SSL termination and security headers
- **Firewall Integration**: Automatic firewall configuration
- **Credential Management**: Secure storage of sensitive configuration

## 📊 Monitoring

### Service Logs
```bash
# View service logs
sudo journalctl -u proximity -f

# View application logs
sudo journalctl -u proximity --since "1 hour ago"
```

### Application Metrics
- CPU and memory usage
- Network I/O statistics
- Container status and uptime
- Application-specific logs

## 🔄 Development

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/proximity.git
   cd proximity
   ```

2. **Set up Python environment:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Proxmox details
   ```

4. **Run the development server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8765
   ```

### Testing

```bash
# Run tests (when available)
pytest

# Check code style
black backend/
flake8 backend/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Principles
- **Async First**: All I/O operations must be asynchronous
- **Type Safety**: Full type hints with Pydantic models
- **Clean Architecture**: Clear separation between API, business logic, and data layers
- **Security**: Security-first design with proper input validation
- **Documentation**: Comprehensive documentation for all APIs

## 📋 Roadmap

### Phase 1 - Core Platform ✅
- [x] Direct Proxmox API integration
- [x] LXC container management
- [x] Docker-ready template creation
- [x] REST API with FastAPI
- [x] Application deployment pipeline
- [x] Basic application catalog

### Phase 2 - Web Interface 🚧
- [ ] SvelteKit/Vue.js web interface
- [ ] Application deployment wizard
- [ ] Real-time monitoring dashboard
- [ ] Application management interface

### Phase 3 - Advanced Features 📋
- [ ] Multi-node deployment
- [ ] Application scaling
- [ ] Backup and restore
- [ ] Custom application builder
- [ ] Marketplace integration
- [ ] Team collaboration features

### Phase 4 - AI Integration 🔮
- [ ] AI-powered application recommendations
- [ ] Automated optimization suggestions
- [ ] Intelligent resource allocation
- [ ] Predictive scaling

## 📞 Support

- **Documentation**: [docs.proximity.dev](https://docs.proximity.dev) (coming soon)
- **Issues**: [GitHub Issues](https://github.com/yourusername/proximity/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/proximity/discussions)
- **Discord**: [Community Discord](https://discord.gg/proximity) (coming soon)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Proxmox VE** - The incredible virtualization platform
- **FastAPI** - Modern, fast web framework for APIs
- **Docker** - Containerization platform
- **Community** - All the amazing contributors and users

---

**Made with ❤️ for the self-hosting community**