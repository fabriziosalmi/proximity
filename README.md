# Proximity

**Self-hosted Application Delivery Platform for Proxmox VE**

Proximity is a cloud-native application delivery platform that abstracts the complexity of Proxmox VE, providing a simple, web-based interface for deploying and managing containerized applications. Think Heroku or Cloudron, but for your own Proxmox infrastructure.

---

[![Tests](https://img.shields.io/badge/tests-250%2B%20passing-success)](tests/)
[![E2E Tests](https://img.shields.io/badge/E2E-Playwright%20%2B%20Pytest-blue)](e2e_tests/)
[![Network](https://img.shields.io/badge/network-simple%20vmbr0%2BDHCP-brightgreen)](#-architecture)
[![Dual Mode](https://img.shields.io/badge/mode-AUTO%20%7C%20PRO-purple)](#-dual-mode-operation-new)
[![Security](https://img.shields.io/badge/security-hardened-green)](#-security)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## 🌟 Features

### Core Platform
- **One-Click App Deployment**: Deploy applications from a curated catalog with a single click
- **Fully Automated Setup**: Docker installation and container configuration—all automatic
- **Standard Proxmox Networking**: Uses vmbr0 with DHCP + Docker host networking for direct access
- **Web-Based Management**: Modern, responsive UI with real-time status monitoring
- **REST API**: Full API access for automation and integration
- **Secure by Default**: Unprivileged containers, network isolation, JWT authentication
- **Self-Hosted**: Complete control over your data and applications

### 🤖 Dual-Mode Operation (NEW!)
**Proximity now offers two distinct operating modes to match your workflow:**

#### AUTO Mode 🤖
Perfect for hands-free operation and peace of mind:
- ✅ **Daily Automated Backups** - All running apps backed up automatically at 2:00 AM
- ✅ **Weekly Update Checks** - System checks for application updates every Sunday
- ✅ **Simplified Interface** - Clean UI focused on essential features
- ✅ **Hands-Free Operation** - Set it and forget it

#### PRO Mode 🛠️
Full professional control for power users:
- ✅ **Manual Backup Control** - Create backups on-demand whenever needed
- ✅ **Clone Applications** - Duplicate running apps with one click
- ✅ **Edit Resources** - Adjust CPU, RAM, and disk allocations on the fly
- ✅ **Advanced Features** - Access all professional-grade tools
- ✅ **Complete Control** - You decide when and how things happen

**Switch modes anytime** from Settings → System → Proximity Mode

## 🏗️ Architecture

### Simplified Network Architecture

Proximity uses **standard Proxmox networking** for simplicity and reliability:

- **`vmbr0` Bridge**: All containers connect to the default Proxmox bridge
- **DHCP Configuration**: Containers automatically receive IP addresses from your network's DHCP server
- **Direct Network Access**: No NAT overhead, containers are directly accessible on your network
- **Standard Proxmox Patterns**: Uses conventional Proxmox networking for easy troubleshooting

**Benefits of Simple Architecture:**
- ✅ Less complexity = fewer failure points
- ✅ Standard networking tools work directly
- ✅ No custom network appliance to maintain
- ✅ Better performance with direct access
- ✅ Easier troubleshooting and debugging

**[Read more →](docs/architecture.md)** | **[Network Simplification Details →](docs/NETWORK_SIMPLIFICATION.md)**

### Core Components

- **FastAPI Backend**: High-performance async API built with Python 3.13+
- **Proxmox Integration**: Direct API integration + SSH for container management
- **App Service**: Application lifecycle management with Docker Compose
- **Authentication**: JWT-based with role-based access control
- **Scheduler Service**: Automated backup and maintenance tasks (AUTO mode)
- **Modular Frontend**: ES6 modules with state management and component architecture

**Network Simplification (October 2025):**  
Proximity now uses standard Proxmox networking (vmbr0 + DHCP) instead of a complex custom network appliance. This significantly reduces complexity while maintaining full functionality. See [Network Simplification Documentation](docs/NETWORK_SIMPLIFICATION.md) for migration details.

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

### Core Guides
- **[Architecture Guide](docs/architecture.md)** - System design, network topology, and technical details
- **[Deployment Guide](docs/deployment.md)** - Installation, configuration, operations, and troubleshooting
- **[Development Guide](docs/development.md)** - Contributing, code structure, and adding features
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues, fixes, and debugging techniques
- **[Changelog](docs/CHANGELOG.md)** - Version history and release notes

### Security & Testing
- **[Security Refactoring](docs/SECURITY_REFACTORING_SAFE_COMMANDS.md)** - Safe command system documentation
- **[Safe Commands Reference](docs/SAFE_COMMANDS_REFERENCE.md)** - Quick reference for secure container commands
- **[E2E Testing Guide](e2e_tests/README.md)** - End-to-end testing with Playwright and Pytest

### Feature Documentation
- **[Dual-Mode Operation](#-dual-mode-operation-new)** - AUTO vs PRO mode comparison (see Features section above)
- **[Frontend Architecture](#modular-frontend-architecture-new)** - ES6 modules and component structure (see below)

## 🔒 Security

Proximity is built with security as a top priority:

- ✅ **JWT Authentication**: Secure token-based authentication with role-based access control
- ✅ **Safe Command System**: Predefined, read-only commands prevent arbitrary code execution
- ✅ **Audit Logging**: All command executions and critical actions are logged
- ✅ **Standard Networking**: Containers on vmbr0 with firewall enabled by default
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

### Running Tests

**Unit and Integration Tests (250+ tests):**
```bash
cd tests/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

**End-to-End Tests (Playwright):**
```bash
cd e2e_tests/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Run all E2E tests
pytest -v

# Run specific test suite
pytest test_auth_flow.py -v

# Run with headed browser (watch tests run)
pytest --headed -v

# Run smoke tests only
pytest -m smoke -v
```

See [E2E Testing Guide](e2e_tests/README.md) for comprehensive testing documentation.

### Contributing

We welcome contributions! Please see:
- **[Development Guide](docs/development.md)** for code structure and workflow
- **[Contributing Guide](CONTRIBUTING.md)** for contribution guidelines
- **[Pre-commit Quick Start](PRE_COMMIT_QUICK_START.md)** for automated quality gates

**Testing:**
- **Run All Tests**: Use `./run_all_tests.sh` or `python run_all_tests.py`
- **Backend Unit Tests**: 250+ tests in `tests/` directory - `pytest tests/`
- **E2E Tests**: Playwright-based browser tests in `e2e_tests/` - `pytest e2e_tests/`
- **Pre-commit Hooks**: Automated code quality and test execution before commits
- See [E2E Testing Guide](e2e_tests/README.md) for comprehensive testing documentation

**Quality Assurance:**

Proximity uses **automated pre-commit hooks** to ensure code quality:

```bash
# One-time setup (after cloning)
./setup_precommit.sh

# Hooks now run automatically on every commit!
```

**What's protected:**
- ✅ Code formatting (Black, Ruff)
- ✅ Syntax validation (YAML, JSON)
- ✅ Whitespace cleanup
- ✅ Backend tests (optional - activate when ready)
- ✅ E2E tests (optional - activate when ready)

See [PRE_COMMIT_QUICK_START.md](PRE_COMMIT_QUICK_START.md) for details.

### Project Structure

```
proximity/
├── backend/
│   ├── api/endpoints/       # REST API routes
│   ├── services/            # Business logic
│   │   ├── app_service.py
│   │   ├── backup_service.py
│   │   ├── scheduler_service.py  # NEW: AUTO mode automation
│   │   └── ...
│   ├── models/              # Database models
│   ├── catalog/             # Application catalog
│   ├── core/                # Core utilities
│   ├── main.py              # Application entry point
│   └── frontend/            # NEW: Modular frontend
│       ├── index.html       # Entry point
│       ├── app.js           # Legacy (compatibility)
│       ├── css/
│       │   └── styles.css   # Global styles + dual-mode CSS
│       ├── js/
│       │   ├── main.js      # ES6 module entry point
│       │   ├── state/
│       │   │   └── appState.js      # State management
│       │   ├── services/
│       │   │   └── api.js           # API service layer
│       │   ├── utils/
│       │   │   ├── auth.js          # Authentication
│       │   │   ├── dom.js           # DOM utilities
│       │   │   ├── notifications.js # Toast system
│       │   │   └── ui.js            # UI mode control
│       │   └── components/          # Future: React-like components
│       └── assets/          # Images, icons, etc.
├── docs/                    # Documentation
│   ├── architecture.md
│   ├── deployment.md
│   ├── development.md
│   └── troubleshooting.md
├── e2e_tests/               # End-to-end tests
│   ├── pages/               # Page Object Model
│   ├── utils/               # Test utilities
│   ├── conftest.py          # Pytest fixtures
│   ├── test_dual_mode_experience.py  # NEW: Dual-mode tests
│   └── test_*.py            # Test suites
├── tests/                   # Unit and integration tests
└── README.md
```

## 🎨 Modular Frontend Architecture (NEW!)

Proximity's frontend has been completely refactored into a modern, maintainable ES6 module system:

### Architecture Highlights

**Before**: 4,200+ lines monolithic `app.js`
**After**: Clean, modular structure with separation of concerns

```
frontend/js/
├── main.js              ← Entry point (bootstraps everything)
├── state/
│   └── appState.js      ← Centralized state management
├── services/
│   └── api.js           ← API abstraction (40+ endpoints)
├── utils/
│   ├── auth.js          ← JWT token management
│   ├── dom.js           ← DOM manipulation helpers
│   ├── notifications.js ← Toast notification system
│   └── ui.js            ← Dual-mode visibility control
└── components/          ← Future: Component modules
```

### Key Features

- ✅ **ES6 Modules**: Clean import/export syntax
- ✅ **State Management**: Centralized state with getters/setters
- ✅ **API Layer**: All backend calls abstracted to `api.js`
- ✅ **Utility Functions**: Reusable helpers for DOM, auth, notifications
- ✅ **Backward Compatible**: Legacy code still works during transition
- ✅ **Dual-Mode Control**: CSS-based visibility system for AUTO/PRO modes

### Usage Example

```javascript
// Import modules
import { getState, setState } from './state/appState.js';
import { getApps, deployApp } from './services/api.js';
import { showNotification } from './utils/notifications.js';
import { switchProximityMode } from './utils/ui.js';

// Use state management
const currentMode = getState('proximityMode');
setState('proximityMode', 'PRO');

// Call APIs
const apps = await getApps();
await deployApp({ catalog_id: 'nginx', hostname: 'my-app' });

// Show notifications
showNotification('App deployed successfully!', 'success');

// Switch modes
switchProximityMode('AUTO');
```

## 📋 Roadmap

### ✅ Completed

#### Core Platform (v1.0)
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

#### Security & Testing (Oct 2025)
- [x] **Safe Command System** - Secure, predefined command execution
- [x] **Audit Logging** - Complete command execution tracking
- [x] **Command Injection Prevention** - Eliminated arbitrary command execution
- [x] **Comprehensive Test Suite** - 250+ unit/integration tests + E2E tests with Playwright
- [x] **E2E Testing Framework** - Page Object Model pattern with Pytest and Playwright

#### Phase 2: Dual-Mode & Modularization (Oct 2025)
- [x] **🤖 AUTO/PRO Mode System** - Dual operating modes for different workflows
- [x] **Automated Backups** - Daily scheduled backups in AUTO mode (2:00 AM)
- [x] **Weekly Update Checks** - Automatic update notifications (Sunday 3:00 AM)
- [x] **Clone Applications** - One-click app duplication (PRO mode)
- [x] **Edit Resources** - Dynamic CPU/RAM/Disk configuration (PRO mode)
- [x] **Scheduler Service** - APScheduler integration for automated tasks
- [x] **Modular Frontend** - ES6 modules with state management
- [x] **Component Architecture** - Separation of concerns (state, services, utils)
- [x] **Dual-Mode E2E Tests** - Complete test coverage for AUTO/PRO modes

### 🚧 In Progress
- [ ] Complete E2E test coverage (all edge cases)
- [ ] Advanced dashboard with real-time metrics
- [ ] Application health monitoring
- [ ] Log aggregation and search

### 📋 Planned
- [ ] Multi-node deployment and load balancing
- [ ] Application scaling (horizontal/vertical)
- [ ] Backup retention policies and cleanup
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
