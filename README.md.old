<div align="center"># Proximity



<img src="logo.png" alt="Proximity Logo" width="200"/>**Self-hosted Application Delivery Platform for Proxmox VE**



# ProximityProximity is a cloud-native application delivery platform that abstracts the complexity of Proxmox VE, providing a simple, web-based interface for deploying and managing containerized applications. Think Heroku or Cloudron, but for your own Proxmox infrastructure.



### Your Personal Cloud's Operating System, Built on Proxmox---



**The modern, self-hosted application delivery platform that makes deploying containerized apps as easy as browsing a catalog.**[![Tests](https://img.shields.io/badge/tests-250%2B%20passing-success)](tests/)

[![E2E Tests](https://img.shields.io/badge/E2E-Playwright%20%2B%20Pytest-blue)](e2e_tests/)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/fabriziosalmi/proximity)[![Network](https://img.shields.io/badge/network-simple%20vmbr0%2BDHCP-brightgreen)](#-architecture)

[![Test Coverage](https://img.shields.io/badge/coverage-250%2B%20tests-success)](https://github.com/fabriziosalmi/proximity/tree/main/tests)[![Dual Mode](https://img.shields.io/badge/mode-AUTO%20%7C%20PRO-purple)](#-dual-mode-operation-new)

[![E2E Tests](https://img.shields.io/badge/E2E-Playwright%20%2B%20Pytest-blue)](https://github.com/fabriziosalmi/proximity/tree/main/e2e_tests)[![Security](https://img.shields.io/badge/security-hardened-green)](#-security)

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[![GitHub Stars](https://img.shields.io/github/stars/fabriziosalmi/proximity?style=social)](https://github.com/fabriziosalmi/proximity)

## 🌟 Features

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

### Core Platform

</div>- **One-Click App Deployment**: Deploy applications from a curated catalog with a single click

- **Fully Automated Setup**: Docker installation and container configuration—all automatic

---- **Standard Proxmox Networking**: Uses vmbr0 with DHCP + Docker host networking for direct access

- **Web-Based Management**: Modern, responsive UI with real-time status monitoring

## 🎯 What is Proximity?- **REST API**: Full API access for automation and integration

- **Secure by Default**: Unprivileged containers, network isolation, JWT authentication

**Proximity** transforms your Proxmox VE infrastructure into a **powerful application delivery platform**. It abstracts away the complexity of container management, networking, and deployments—giving you a **beautiful, intuitive interface** that feels like using Heroku or Cloudron, but with **complete control** over your own hardware.- **Self-Hosted**: Complete control over your data and applications



### The Problem We Solve### 🤖 Dual-Mode Operation (NEW!)

**Proximity now offers two distinct operating modes to match your workflow:**

Managing applications on Proxmox typically requires:

- 🔧 Manual LXC container creation and configuration#### AUTO Mode 🤖

- 📦 Docker installation and compose file management  Perfect for hands-free operation and peace of mind:

- 🌐 Complex networking and reverse proxy setup- ✅ **Daily Automated Backups** - All running apps backed up automatically at 2:00 AM

- 🔒 Security hardening and access control- ✅ **Weekly Update Checks** - System checks for application updates every Sunday

- 📊 Monitoring, logging, and backup management- ✅ **Simplified Interface** - Clean UI focused on essential features

- ⏰ Update tracking and maintenance scheduling- ✅ **Hands-Free Operation** - Set it and forget it



**Proximity handles all of this for you.**#### PRO Mode 🛠️

Full professional control for power users:

### How It Works- ✅ **Manual Backup Control** - Create backups on-demand whenever needed

- ✅ **Clone Applications** - Duplicate running apps with one click

```- ✅ **Edit Resources** - Adjust CPU, RAM, and disk allocations on the fly

Browse App Store → Click Deploy → Watch Progress → Use Your App- ✅ **Advanced Features** - Access all professional-grade tools

```- ✅ **Complete Control** - You decide when and how things happen



That's it. One click from browsing to running. Proximity manages the entire lifecycle:**Switch modes anytime** from Settings → System → Proximity Mode



1. **Provisions** an isolated, hardened LXC container on your Proxmox cluster## 🏗️ Architecture

2. **Installs** Docker and all required dependencies automatically

3. **Configures** networking with automatic port allocation and access URLs### Simplified Network Architecture

4. **Deploys** your application with proper resource limits and security

5. **Monitors** health, performance, and resource usage in real-timeProximity uses **standard Proxmox networking** for simplicity and reliability:

6. **Maintains** automated backups, updates, and lifecycle management

- **`vmbr0` Bridge**: All containers connect to the default Proxmox bridge

---- **DHCP Configuration**: Containers automatically receive IP addresses from your network's DHCP server

- **Direct Network Access**: No NAT overhead, containers are directly accessible on your network

## ✨ Features- **Standard Proxmox Patterns**: Uses conventional Proxmox networking for easy troubleshooting



### 🚀 **One-Click Deployment****Benefits of Simple Architecture:**

Deploy applications from a curated catalog in seconds. No Docker knowledge required. Proximity handles container provisioning, Docker installation, networking, and configuration automatically.- ✅ Less complexity = fewer failure points

- ✅ Standard networking tools work directly

### 🎨 **Beautiful "In-App Canvas" Experience**- ✅ Direct container access without NAT overhead

Access your deployed applications directly within Proximity using our integrated iframe canvas. No need to remember URLs or open new tabs—everything at your fingertips.- ✅ Better performance with host networking

- ✅ Easier troubleshooting and debugging

### 🖥️ **Integrated Web Console**

Full SSH-like terminal access to every container, right in your browser. No SSH client needed. Built-in security ensures safe remote access.**[Read more →](docs/architecture.md)** | **[Network Simplification Details →](docs/NETWORK_SIMPLIFICATION.md)**



### 🤖 **AUTO & PRO Modes**### Core Components

- **AUTO Mode**: Hands-free operation with daily automated backups and weekly update checks

- **PRO Mode**: Full manual control for power users—clone apps, edit resources, advanced configurations- **FastAPI Backend**: High-performance async API built with Python 3.13+

- **Proxmox Integration**: Direct API integration + SSH for container management

Switch between modes instantly based on your workflow.- **App Service**: Application lifecycle management with Docker Compose

- **Authentication**: JWT-based with role-based access control

### 🎯 **"Living" App Cards**- **Scheduler Service**: Automated backup and maintenance tasks (AUTO mode)

Real-time monitoring directly on each app card:- **Modular Frontend**: ES6 modules with state management and component architecture

- 📊 Live CPU and RAM usage metrics

- 🟢 Status indicators (running, stopped, deploying)**Network Simplification (October 2025):**  

- ⚡ Quick actions (start, stop, restart, backup, update, delete)Proximity uses standard Proxmox networking (vmbr0 + DHCP) for simplicity and reliability. Containers use Docker's host networking mode for direct access without NAT complexity. This architectural choice significantly reduces infrastructure overhead while maintaining full functionality. See [Network Simplification Documentation](docs/NETWORK_SIMPLIFICATION.md) for details.

- 📦 Volume management and console access

- 🔄 One-click app cloning (PRO mode)## 🚀 Quick Start



### 🔐 **Security by Default**### Prerequisites

- Unprivileged LXC containers for isolation

- JWT-based authentication with role-based access- Proxmox VE 8.x or later

- Encrypted credential storage- Root access to Proxmox host(s)

- Network segmentation and firewall rules- Python 3.13+

- Audit logging for all administrative actions- SSH access configured



### 🔧 **Advanced Network Architecture** *(Optional)*### Installation

Platinum Edition includes:

- Dedicated network appliance LXC with NAT/routing1. **Clone the repository:**

- DHCP server for automatic IP assignment     ```bash

- DNS server with `.prox.local` domain resolution   git clone https://github.com/yourusername/proximity.git

- Caddy reverse proxy for unified app access   cd proximity/backend

- Isolated app network (`10.20.0.0/24`)   ```



### 💾 **Fearless Backups & Updates**2. **Create virtual environment:**

- Automatic scheduled backups (AUTO mode)   ```bash

- On-demand backup creation (PRO mode)   python3 -m venv venv

- One-click restore from any backup   source venv/bin/activate

- Update detection and upgrade workflows   pip install -r requirements.txt

- Zero-downtime snapshot-based backups   ```



### 📡 **Comprehensive Monitoring**3. **Configure environment:**

- Real-time infrastructure health dashboard   ```bash

- Per-app resource usage tracking   cp .env.example .env

- Network activity monitoring   # Edit .env with your Proxmox credentials

- Container lifecycle event logging   ```

- Proxmox node statistics

4. **Initialize database:**

### 🔄 **Full Lifecycle Management**   ```bash

Complete control over your applications:   python -c "from models.database import init_db; init_db()"

- **Deploy** from catalog with custom configuration   ```

- **Start/Stop/Restart** with instant feedback

- **Update** to latest versions seamlessly5. **Start the server:**

- **Backup/Restore** with compression options   ```bash

- **Clone** running applications (PRO mode)   python main.py

- **Scale** resources on-the-fly (PRO mode)   ```

- **Delete** with automatic cleanup

6. **Access the UI:**

---   Open http://localhost:8765 in your browser



## 📸 Screenshots**[Detailed setup guide →](docs/deployment.md)**



> **Visual Demo Coming Soon**  ## 📖 Documentation

> We're preparing high-quality GIFs and screenshots showcasing:

> - App Store browsing and deployment flow### Core Guides

> - The "In-App Canvas" experience- **[Architecture Guide](docs/architecture.md)** - System design, network topology, and technical details

> - Real-time monitoring and "Living" app cards- **[Deployment Guide](docs/deployment.md)** - Installation, configuration, operations, and troubleshooting

> - The integrated web console- **[Development Guide](docs/development.md)** - Contributing, code structure, and adding features

> - Backup and update workflows- **[Troubleshooting](docs/troubleshooting.md)** - Common issues, fixes, and debugging techniques

- **[Changelog](docs/CHANGELOG.md)** - Version history and release notes

---

### Security & Testing

## 🚀 Quick Start- **[Security Refactoring](docs/SECURITY_REFACTORING_SAFE_COMMANDS.md)** - Safe command system documentation

- **[Safe Commands Reference](docs/SAFE_COMMANDS_REFERENCE.md)** - Quick reference for secure container commands

### Prerequisites- **[E2E Testing Guide](e2e_tests/README.md)** - End-to-end testing with Playwright and Pytest



- **Proxmox VE** 7.0 or higher### Feature Documentation

- **Python** 3.9+- **[Dual-Mode Operation](#-dual-mode-operation-new)** - AUTO vs PRO mode comparison (see Features section above)

- **SSH access** to your Proxmox host- **[Frontend Architecture](#modular-frontend-architecture-new)** - ES6 modules and component structure (see below)

- **Root privileges** on Proxmox

## 🔒 Security

### Installation (Development Mode)

Proximity is built with security as a top priority:

```bash

# 1. Clone the repository- ✅ **JWT Authentication**: Secure token-based authentication with role-based access control

git clone https://github.com/fabriziosalmi/proximity.git- ✅ **Safe Command System**: Predefined, read-only commands prevent arbitrary code execution

cd proximity/backend- ✅ **Audit Logging**: All command executions and critical actions are logged

- ✅ **Standard Networking**: Containers on vmbr0 with firewall enabled by default

# 2. Install Python dependencies- ✅ **Unprivileged Containers**: All LXC containers run unprivileged by default

pip3 install -r requirements.txt- ✅ **Input Validation**: Comprehensive parameter validation using Pydantic

- ✅ **No Command Injection**: All commands are hardcoded; user input never interpolated into shell commands

# 3. Configure environment

cp .env.example .env**October 2025 Security Update:**  

# Edit .env with your Proxmox credentialsWe've completely eliminated the dangerous arbitrary command execution endpoint (`/exec`) and replaced it with a secure, predefined command system. See [Security Refactoring Documentation](docs/SECURITY_REFACTORING_SAFE_COMMANDS.md) for details.



# 4. Start the application**Available Safe Commands:**

python3 main.py- 📋 logs, ✅ status, 💾 disk, ⚙️ processes, 🧠 memory, 🌐 network, 🐳 images, 📦 volumes, ⚙️ config, 💻 system

```

All commands are read-only, audited, and fully documented in the [Safe Commands Reference](docs/SAFE_COMMANDS_REFERENCE.md).

The Proximity UI will be available at **`http://localhost:8765`**

## 🔧 Configuration

### First Run

Edit `.env` with your settings:

1. **Navigate to** `http://localhost:8765` in your browser

2. **Power On** the application (first-time onboarding)```ini

3. **Register** your admin account# Proxmox Connection

4. **Configure** Proxmox connection settingsPROXMOX_HOST=192.168.1.100

5. **Start deploying** apps from the catalog!PROXMOX_USER=root@pam

PROXMOX_PASSWORD=your_password

### Production DeploymentPROXMOX_VERIFY_SSL=false



For production installations with systemd, Docker, or reverse proxy configurations, see:# SSH Settings (for container management)

PROXMOX_SSH_HOST=192.168.1.100

📘 **[Complete Deployment Guide →](docs/2_DEPLOYMENT.md)**PROXMOX_SSH_PORT=22

PROXMOX_SSH_USER=root

---PROXMOX_SSH_PASSWORD=your_password



## 📖 Documentation# API Settings

API_HOST=0.0.0.0

### User DocumentationAPI_PORT=8765

- 📖 **[Introduction & Philosophy](docs/1_INTRODUCTION.md)** - Learn about Proximity's vision and design principlesDEBUG=true

- 🚀 **[Deployment Guide](docs/2_DEPLOYMENT.md)** - Complete installation and configuration instructions

- 🎯 **[Usage Guide](docs/3_USAGE_GUIDE.md)** - Step-by-step guide to using every feature# Security

JWT_SECRET_KEY=generate-a-secure-random-key

### Developer Documentation  ENCRYPTION_KEY=generate-another-secure-key

- 🏗️ **[Architecture Deep-Dive](docs/4_ARCHITECTURE.md)** - Technical overview of backend, frontend, and networking```

- 🛠️ **[Development Guide](docs/5_DEVELOPMENT.md)** - Setup, testing, conventions, and contribution workflow

## 📱 Application Catalog

---

Proximity includes pre-configured applications:

## 🏗️ Architecture Overview

### Web Servers & Proxies

Proximity uses a modern, service-oriented architecture:- **Nginx** - High-performance web server

- **Caddy** - Modern web server with automatic HTTPS

```- **Traefik** - Cloud-native reverse proxy

┌─────────────────────────────────────────────────────────┐

│                   Proximity Frontend                     │### Content Management

│              (Vanilla JS + Modular Architecture)         │- **WordPress** - Popular CMS and blogging platform

│  Router • Views • Components • State Management          │- **Ghost** - Modern publishing platform

└────────────────────┬────────────────────────────────────┘

                     │ REST API (JSON)### Development

┌────────────────────┴────────────────────────────────────┐- **VS Code Server** - Web-based VS Code editor

│                   Proximity Backend                      │- **Gitea** - Self-hosted Git service

│                  (FastAPI + SQLite)                      │

│                                                          │### And more...

│  ┌─────────────────────────────────────────────────────┐   │

│  │  Services Layer                                  │   │**[Add custom apps →](docs/development.md#adding-a-new-catalog-item)**

│  │  • ProxmoxService    • AppService               │   │

│  │  • NetworkService    • BackupService            │   │## 🌐 API Documentation

│  │  • PortManager       • SchedulerService         │   │

│  │  • MonitoringService • TemplateService          │   │Access interactive API docs at:

│  └─────────────────────────────────────────────────┘   │- **Swagger UI**: http://localhost:8765/docs

└────────────────────┬────────────────────────────────────┘- **ReDoc**: http://localhost:8765/redoc

                     │ Proxmox API

┌────────────────────┴────────────────────────────────────┐### Key Endpoints

│                  Proxmox VE Cluster                      │

│                                                          │**Applications:**

│  ┌──────────────┐    ┌──────────────┐                  │- `GET /api/v1/apps` - List deployed applications

│  │   Node 1     │    │   Node 2     │                  │- `POST /api/v1/apps/deploy` - Deploy new application

│  │              │    │              │                  │- `POST /api/v1/apps/{app_id}/actions` - Start/stop/restart

│  │  ┌─────────┐ │    │  ┌─────────┐ │                  │- `GET /api/v1/apps/{app_id}/logs` - View application logs

│  │  │ App LXC │ │    │  │ App LXC │ │                  │- `DELETE /api/v1/apps/{app_id}` - Delete application

│  │  │ (Docker)│ │    │  │ (Docker)│ │                  │

│  │  └─────────┘ │    │  └─────────┘ │                  │**System:**

│  └──────────────┘    └──────────────┘                  │- `GET /api/v1/system/info` - System information

└─────────────────────────────────────────────────────────┘- `GET /api/v1/system/nodes` - Proxmox nodes and host status

```- `GET /api/v1/system/infrastructure/status` - Infrastructure health check

- `GET /api/v1/system/proxy/status` - Reverse proxy status

**Key Technologies:**

- **Backend**: FastAPI (Python), SQLite, SQLAlchemy**Authentication:**

- **Frontend**: Vanilla JavaScript (ES6 Modules), Custom Router, Observer Pattern- `POST /api/v1/auth/register` - Register new user

- **Infrastructure**: Proxmox VE, LXC Containers, Docker- `POST /api/v1/auth/login` - Login and get JWT token

- **Networking**: vmbr0 (DHCP) or Custom Bridge with Network Appliance- `POST /api/v1/auth/logout` - Logout (audit logging)

- **Testing**: pytest (backend), Playwright (E2E), 250+ test suite- `GET /api/v1/auth/me` - Get current user info



For complete architectural details, see **[docs/4_ARCHITECTURE.md](docs/4_ARCHITECTURE.md)**## 🛡️ Security



---- **Direct Network Access**: Standard vmbr0 networking with firewall enabled

- **Unprivileged Containers**: LXC containers run unprivileged for security

## 🧪 Testing- **JWT Authentication**: Secure API access with token-based auth

- **Role-Based Access**: Admin and user roles with different permissions

Proximity includes comprehensive test coverage:- **Network Security**: Firewall rules and secure container isolation

- **Audit Logging**: All user actions logged for compliance

### Backend Unit Tests (pytest)- **SSH Security**: Secure container management via SSH with key authentication

```bash

cd backend## 📊 Monitoring

pytest tests/ -v

```**Dashboard Features:**

- Total and running application count

### End-to-End Tests (Playwright + pytest)- Infrastructure nodes status

```bash- Resource utilization metrics

cd e2e_tests- Reverse proxy status

pytest -v --headed  # Run with visible browser- Real-time deployment tracking

```

**Application Management:**

**Test Coverage:**- Start/stop/restart applications

- ✅ 250+ backend unit tests- View logs in real-time

- ✅ 30+ E2E integration tests- Monitor resource usage

- ✅ Authentication flows- Access via reverse proxy URLs

- ✅ Complete app lifecycle (deploy → manage → delete)

- ✅ Backup/restore workflows## 🔄 Development

- ✅ Settings and configuration

- ✅ UI navigation and interactions### Development Setup



---```bash

# Clone and setup

## 🤝 Contributinggit clone https://github.com/yourusername/proximity.git

cd proximity/backend

We welcome contributions from the community! Whether it's:python3 -m venv venv

source venv/bin/activate

- 🐛 **Bug reports** and feature requestspip install -r requirements.txt

- 📝 **Documentation** improvements

- 🔧 **Code contributions** (features, fixes, optimizations)# Configure and run

- 🎨 **UI/UX** enhancementscp .env.example .env

- 🧪 **Test coverage** improvementspython main.py

```

### How to Contribute

### Running Tests

1. **Fork** the repository

2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)**Unit and Integration Tests (250+ tests):**

3. **Commit** your changes (`git commit -m 'Add amazing feature'`)```bash

4. **Push** to your branch (`git push origin feature/amazing-feature`)cd tests/

5. **Open** a Pull Requestpython3 -m venv venv

source venv/bin/activate

Please read our **[Development Guide](docs/5_DEVELOPMENT.md)** and **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed guidelines.pip install -r requirements.txt

pytest -v

---```



## 📜 License**End-to-End Tests (Playwright):**

```bash

Proximity is open-source software licensed under the **MIT License**.cd e2e_tests/

python3 -m venv venv

See [LICENSE](LICENSE) for full details.source venv/bin/activate

pip install -r requirements.txt

---playwright install chromium



## 🙏 Acknowledgments# Run all E2E tests

pytest -v

Proximity stands on the shoulders of giants:

# Run specific test suite

- **[Proxmox VE](https://www.proxmox.com/)** - The foundation of our platformpytest test_auth_flow.py -v

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework

- **[Alpine Linux](https://alpinelinux.org/)** - Lightweight container base# Run with headed browser (watch tests run)

- **[Docker](https://www.docker.com/)** - Container runtimepytest --headed -v

- **[Lucide Icons](https://lucide.dev/)** - Beautiful icon set

- **[Playwright](https://playwright.dev/)** - Reliable E2E testing# Run smoke tests only

pytest -m smoke -v

And to all our contributors who make Proximity better every day! 🚀```



---See [E2E Testing Guide](e2e_tests/README.md) for comprehensive testing documentation.



## 📬 Support & Community### Contributing



- 📧 **Email**: [support@proximity.dev](mailto:support@proximity.dev)We welcome contributions! Please see:

- 💬 **Discussions**: [GitHub Discussions](https://github.com/fabriziosalmi/proximity/discussions)- **[Development Guide](docs/development.md)** for code structure and workflow

- 🐛 **Issues**: [GitHub Issues](https://github.com/fabriziosalmi/proximity/issues)- **[Contributing Guide](CONTRIBUTING.md)** for contribution guidelines

- 📖 **Wiki**: [GitHub Wiki](https://github.com/fabriziosalmi/proximity/wiki)- **[Pre-commit Quick Start](PRE_COMMIT_QUICK_START.md)** for automated quality gates



---**Testing:**

- **Run All Tests**: Use `./run_all_tests.sh` or `python run_all_tests.py`

<div align="center">- **Backend Unit Tests**: 250+ tests in `tests/` directory - `pytest tests/`

- **E2E Tests**: Playwright-based browser tests in `e2e_tests/` - `pytest e2e_tests/`

**Made with ❤️ by the Proximity Team**- **Pre-commit Hooks**: Automated code quality and test execution before commits

- See [E2E Testing Guide](e2e_tests/README.md) for comprehensive testing documentation

⭐ **Star us on GitHub** if you find Proximity useful!

**Quality Assurance:**

[🏠 Homepage](https://github.com/fabriziosalmi/proximity) • [📚 Documentation](docs/) • [🐛 Report Bug](https://github.com/fabriziosalmi/proximity/issues) • [💡 Request Feature](https://github.com/fabriziosalmi/proximity/issues)

Proximity uses **automated pre-commit hooks** to ensure code quality:

</div>

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
- [x] Standard Proxmox networking (vmbr0 + DHCP)
- [x] Docker host networking for direct access
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
