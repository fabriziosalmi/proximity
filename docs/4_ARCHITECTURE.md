# Proximity Architecture Deep-Dive

Technical overview of Proximity's backend, frontend, networking, and infrastructure architecture.

---

## Table of Contents

- [System Overview](#system-overview)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Networking Architecture](#networking-architecture)
- [Data Flow](#data-flow)
- [Security Architecture](#security-architecture)
- [Deployment Pipeline](#deployment-pipeline)

---

## System Overview

Proximity is a **three-tier architecture**:

```
┌─────────────────────────────────────────────────────────┐
│                   Browser (Client)                       │
│          Vanilla JS • Router • Components                │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST (JSON)
┌────────────────────┴────────────────────────────────────┐
│                Proximity Backend (API)                   │
│        FastAPI • SQLAlchemy • Service Layer              │
└────────────────────┬────────────────────────────────────┘
                     │ API Calls (HTTPS/SSH)
┌────────────────────┴────────────────────────────────────┐
│              Proxmox VE Infrastructure                   │
│         LXC Containers • Docker • Networking             │
└─────────────────────────────────────────────────────────┘
```

**Key Technologies:**
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vanilla JavaScript (ES6), No frameworks
- **Infrastructure**: Proxmox VE 7+, LXC, Docker, Alpine Linux
- **Networking**: Linux bridges, iptables, dnsmasq, Caddy

---

## Backend Architecture

### Service-Oriented Design

Proximity uses a **clean service layer** separating concerns:

```
api/endpoints/          # REST API routes
    apps.py            # Application management
    auth.py            # Authentication
    backups.py         # Backup operations
    settings.py        # Configuration
    system.py          # System info

services/              # Business logic
    app_service.py     # App lifecycle management
    proxmox_service.py # Proxmox API client
    backup_service.py  # Backup/restore logic
    network_manager.py # Network configuration
    port_manager.py    # Port allocation
    scheduler_service.py  # AUTO mode scheduling
    monitoring_service.py  # Resource metrics
    template_service.py    # LXC template management

models/                # Data layer
    database.py        # SQLAlchemy models
    schemas.py         # Pydantic schemas

core/                  # Core utilities
    config.py          # Settings management
    security.py        # Encryption, hashing
    exceptions.py      # Custom exceptions
```

### Key Services

#### 1. **ProxmoxService**

**Purpose**: Abstraction layer for Proxmox VE API

**Responsibilities:**
- Connect to Proxmox using `proxmoxer` library
- Manage LXC containers (create, start, stop, delete)
- Execute commands in containers via SSH (`pct exec`)
- Query cluster resources (nodes, storage, templates)
- Handle Proxmox API errors gracefully

**Key Methods:**
```python
async def create_lxc(node, vmid, config)  # Create container
async def get_lxc_status(node, vmid)     # Query status
async def execute_command(node, vmid, cmd)  # Run command
async def get_nodes()                     # List cluster nodes
async def test_connection()               # Verify connectivity
```

#### 2. **AppService**

**Purpose**: Core application lifecycle management

**Responsibilities:**
- Load application catalog (JSON/YAML)
- Deploy apps (provision LXC, install Docker, deploy compose)
- Manage app state (start, stop, restart)
- Track deployment progress
- Handle updates and clones (PRO mode)

**Deployment Flow:**
```python
1. Validate request (catalog_id, hostname, resources)
2. Allocate ports (public + internal)
3. Create LXC container on selected node
4. Install Docker + Docker Compose
5. Write docker-compose.yml
6. Start Docker Compose
7. Configure networking (port forwards or proxy)
8. Update database with app record
9. Return success
```

#### 3. **BackupService**

**Purpose**: Backup and restore management

**Responsibilities:**
- Create vzdump backups via Proxmox API
- List available backups from storage
- Restore containers from backups
- Schedule automated backups (AUTO mode)
- Handle backup compression and storage selection

**Backup Types:**
- **Snapshot**: Fast, uses LVM snapshots (requires supported storage)
- **Stop**: Stops container, creates consistent backup

#### 4. **SchedulerService**

**Purpose**: AUTO mode automation

**Responsibilities:**
- Schedule daily backups (2:00 AM default)
- Schedule weekly update checks (Sunday 3:00 AM)
- Use APScheduler for cron-like scheduling
- Run jobs in background threads

**Configuration:**
```python
# Daily backups
scheduler.add_job(
    backup_all_apps,
    trigger='cron',
    hour=2, minute=0
)

# Weekly updates
scheduler.add_job(
    check_for_updates,
    trigger='cron',
    day_of_week='sun',
    hour=3, minute=0
)
```

#### 5. **PortManager**

**Purpose**: Dynamic port allocation

**Responsibilities:**
- Allocate unique ports from defined ranges
- Track used/free ports in database
- Release ports on app deletion
- Prevent conflicts

**Port Ranges:**
- **Public**: 30000-30999 (external app access)
- **Internal**: 40000-40999 (In-App Canvas iframe)

### Database Schema

**SQLite** database with SQLAlchemy ORM:

```sql
-- Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);

-- Applications
CREATE TABLE apps (
    id TEXT PRIMARY KEY,  -- UUID
    catalog_id TEXT NOT NULL,
    name TEXT NOT NULL,
    hostname TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL,  -- deploying, running, stopped, error
    lxc_id INTEGER NOT NULL,
    node TEXT NOT NULL,
    url TEXT,
    iframe_url TEXT,
    public_port INTEGER,
    internal_port INTEGER,
    config JSON,  -- App configuration
    environment JSON,  -- Environment variables
    ports JSON,  -- Port mappings
    volumes JSON,  -- Volume definitions
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Backups
CREATE TABLE backups (
    id INTEGER PRIMARY KEY,
    app_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    storage_name TEXT,
    backup_type TEXT,  -- vzdump
    status TEXT,  -- creating, completed, failed
    size_bytes INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (app_id) REFERENCES apps(id)
);

-- Settings (encrypted)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,  -- Encrypted with Fernet
    category TEXT,
    updated_at TIMESTAMP
);

-- Audit Log
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    action TEXT,
    resource_type TEXT,
    resource_id TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP
);
```

### API Endpoints

**Authentication:**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT
- `GET /api/v1/auth/me` - Get current user info

**Applications:**
- `GET /api/v1/apps` - List deployed apps
- `POST /api/v1/apps` - Deploy new app
- `GET /api/v1/apps/{id}` - Get app details
- `POST /api/v1/apps/{id}/action` - Control app (start/stop/restart)
- `DELETE /api/v1/apps/{id}` - Delete app
- `POST /api/v1/apps/{id}/clone` - Clone app (PRO mode)
- `POST /api/v1/apps/{id}/update` - Update app

**Catalog:**
- `GET /api/v1/apps/catalog` - List available apps

**Backups:**
- `GET /api/v1/backups` - List all backups
- `POST /api/v1/backups` - Create backup
- `POST /api/v1/backups/{id}/restore` - Restore backup
- `DELETE /api/v1/backups/{id}` - Delete backup

**System:**
- `GET /api/v1/system/info` - System information
- `GET /api/v1/system/nodes` - Proxmox nodes
- `GET /api/v1/system/health` - Health check

**Settings:**
- `GET /api/v1/settings` - Get settings
- `PUT /api/v1/settings` - Update settings

---

## Frontend Architecture

### No-Framework Approach

Proximity's frontend uses **Vanilla JavaScript** with:
- ES6 Modules (native `import/export`)
- Custom Router for view lifecycle
- Observer pattern for reactive state
- Event delegation for performance

**Why No Framework?**
- ⚡ Instant load times (no bundle)
- 🐛 Easier debugging (no transpilation)
- 🎓 Lower learning curve
- 🔧 Complete control

### Modular Structure

```
frontend/js/
    main.js                 # Application entry point

    core/                   # Core abstractions
        Router.js          # View lifecycle management
        Component.js       # Base component class

    state/                  # State management
        appState.js        # Global application state (Observer)

    views/                  # Page views
        DashboardView.js
        AppsView.js
        CatalogView.js
        SettingsView.js
        NodesView.js

    components/             # Reusable UI components
        app-card.js        # App card with metrics
        auth-ui.js         # Authentication UI

    modals/                 # Modal dialogs
        DeployModal.js     # App deployment
        CanvasModal.js     # In-App Canvas
        ConsoleModal.js    # Web terminal
        BackupModal.js     # Backup management
        MonitoringModal.js # Resource metrics

    services/               # Business logic
        api.js             # REST API client
        dataService.js     # Data fetching/caching
        appOperations.js   # App control functions
        soundService.js    # UI sound effects

    utils/                  # Utilities
        dom.js             # DOM manipulation
        auth.js            # JWT management
        notifications.js   # Toast notifications
        formatters.js      # Data formatting
        icons.js           # Icon rendering
```

### Router & Lifecycle

**Router.js** manages view transitions:

```javascript
class Router {
    registerView(name, component)  // Register view
    navigateTo(viewName)           // Switch to view

    // Lifecycle:
    // 1. Call previous view's unmount()
    // 2. Call new view's mount(container, state)
    // 3. Update URL hash
    // 4. Fire callbacks
}
```

**View Lifecycle:**

```javascript
class MyView extends Component {
    mount(container, state) {
        // 1. Render HTML
        container.innerHTML = this.generateHTML(state);

        // 2. Attach event listeners
        container.querySelector('.btn').onclick = ...;

        // 3. Start polling (if needed)
        this.intervalId = setInterval(...);

        // 4. Return unmount function
        return () => this.cleanup();
    }

    unmount() {
        // Clean up resources (intervals, listeners)
        clearInterval(this.intervalId);
    }
}
```

### State Management (Observer Pattern)

**appState.js** implements reactive state:

```javascript
let state = {
    isAuthenticated: false,
    currentUser: null,
    deployedApps: [],
    catalog: [],
    currentView: 'dashboard'
};

const observers = [];

function setState(updates) {
    state = { ...state, ...updates };
    notifyObservers();  // Trigger re-render
}

function subscribe(callback) {
    observers.push(callback);
}
```

**Usage:**

```javascript
// Subscribe to state changes
AppState.subscribe((state) => {
    render(state);  // Re-render UI
});

// Update state
AppState.setState({ deployedApps: newApps });
// Automatically triggers render()
```

### Event Delegation

Single event listener for entire app:

```javascript
document.body.addEventListener('click', (event) => {
    const target = event.target;

    // Navigation
    if (target.closest('[data-view]')) {
        const viewName = target.dataset.view;
        router.navigateTo(viewName);
    }

    // Actions
    if (target.closest('[data-action]')) {
        const action = target.dataset.action;
        const appId = target.dataset.appId;
        handleAction(action, appId);
    }
});
```

**Benefits:**
- Single listener instead of thousands
- Works with dynamically added elements
- Excellent performance

---

## Networking Architecture

Proximity supports two modes:

### 1. Simple Mode (Default)

**Recommended for most users.**

```
┌────────────────────────────────────────────┐
│          Proxmox Host (vmbr0)              │
│          192.168.1.0/24                    │
│                   │                         │
│  ┌────────────────┼────────────────┐       │
│  │  LXC (DHCP)    │  LXC (DHCP)    │       │
│  │  192.168.1.101 │  192.168.1.102 │       │
│  │                │                 │       │
│  │  Docker        │  Docker         │       │
│  │  (host net)    │  (host net)     │       │
│  └────────────────┴─────────────────┘       │
└────────────────────────────────────────────┘

Access: http://192.168.1.101:30001
```

**Configuration:**
- Each LXC gets DHCP IP on vmbr0
- Docker uses host networking
- Apps accessible at `<lxc-ip>:<port>`
- Ports allocated from 30000-30999

**Pros:** Simple, reliable, no extra setup  
**Cons:** IP:PORT URLs, no custom domains

### 2. Advanced Mode (Platinum Edition)

**For custom domains and unified access.**

```
┌──────────────────────────────────────────────────┐
│               Proxmox Host                        │
│                                                  │
│  vmbr0 (Management)    proximity-lan (Apps)      │
│  192.168.1.0/24        10.20.0.0/24             │
│         │                       │                 │
│         │      ┌────────────────┤                │
│         │      │  Network       │                 │
│         └──────┤  Appliance     │                │
│                │  (VMID 9999)   │                 │
│                │                 │                │
│                │  eth0: DHCP     │                 │
│                │  eth1: 10.20.0.1│                │
│                │                 │                │
│                │  Services:      │                │
│                │  - NAT/Routing  │                │
│                │  - DHCP         │                │
│                │  - DNS          │                │
│                │  - Caddy        │                │
│                └─────────────────┘                │
│                         │                          │
│              10.20.0.0/24 network                │
│              ┌──────────┴──────────┐             │
│              │                     │              │
│         ┌────────┐           ┌────────┐          │
│         │ nginx  │           │wordpress│          │
│         │10.20.0.│           │10.20.0. │          │
│         │  101   │           │  102    │          │
│         └────────┘           └────────┘          │
└──────────────────────────────────────────────────┘

Access: https://wordpress.prox.local
```

**Network Appliance Services:**

1. **NAT/Routing**: Forwards traffic between vmbr0 and proximity-lan
2. **DHCP Server** (dnsmasq): Assigns IPs in range 10.20.0.100-250
3. **DNS Server** (dnsmasq): Resolves `.prox.local` domains
4. **Caddy Proxy**: Reverse proxy with automatic SSL

**Configuration:**
- Each app LXC gets IP from DHCP (10.20.0.100+)
- Caddy proxies: `app.prox.local` → `10.20.0.101:port`
- Automatic DNS registration
- SSL with Caddy's ACME

**Pros:** Custom domains, automatic SSL, network isolation  
**Cons:** Complex setup, resource overhead

---

## Data Flow

### Deployment Flow

```
User clicks "Deploy" in UI
    ↓
Frontend sends POST /api/v1/apps
    ↓
AppService validates request
    ↓
PortManager allocates ports
    ↓
ProxmoxService creates LXC
    ↓
ProxmoxService starts LXC
    ↓
ProxmoxService installs Docker via SSH
    ↓
AppService writes docker-compose.yml
    ↓
ProxmoxService starts Docker Compose
    ↓
NetworkManager configures access
    ↓
Database saves app record
    ↓
Response returned to frontend
    ↓
UI updates with new app card
```

### Monitoring Flow

```
Frontend renders app card
    ↓
startCPUPolling() called every 10s
    ↓
GET /api/v1/apps/{id}/metrics
    ↓
MonitoringService queries Proxmox
    ↓
Proxmox returns container stats
    ↓
Stats returned to frontend
    ↓
App card updates CPU/RAM bars
    ↓
Loop continues...
```

---

## Security Architecture

### Authentication & Authorization

**JWT-Based Authentication:**

1. User logs in with username/password
2. Backend verifies credentials
3. JWT token issued (expires in 60 min)
4. Token stored in `localStorage`
5. Token sent in `Authorization: Bearer <token>` header
6. Backend validates token on each request

**Password Storage:**
- Hashed with `bcrypt` (cost factor: 12)
- Never stored in plaintext
- Never logged or transmitted unencrypted

**Credential Encryption:**
- Proxmox passwords encrypted with Fernet (AES-256)
- Encryption key derived from `JWT_SECRET_KEY`
- Stored encrypted in database

### Container Security

**Unprivileged LXC:**
- Containers run as unprivileged (no root on host)
- UID/GID mapping prevents privilege escalation
- `lxc.idmap` configured automatically

**Network Isolation:**
- Each app in separate LXC
- Optional isolated network (Advanced Mode)
- Firewall rules between networks

**Resource Limits:**
- CPU, RAM, and disk limits enforced
- Prevents resource exhaustion
- Configurable per-app

### API Security

**Rate Limiting** (planned):
- Limit requests per IP/user
- Prevent abuse

**CORS:**
- Configured for same-origin by default
- Adjustable for custom domains

**Input Validation:**
- Pydantic schemas validate all inputs
- SQL injection prevented by ORM
- Command injection prevented by parameterized execution

---

## Deployment Pipeline

### App Deployment Steps

1. **Validation**: Check catalog_id, hostname uniqueness, resources
2. **Port Allocation**: Reserve public + internal ports
3. **LXC Creation**: Create container with specified resources
4. **Container Start**: Boot LXC
5. **Docker Installation**: Install Docker + Docker Compose
6. **Compose File**: Write `docker-compose.yml` with app definition
7. **Docker Start**: Run `docker-compose up -d`
8. **Networking**: Configure port forwards or proxy
9. **Database**: Save app record
10. **Success**: Return app details

**Total Time**: ~60-90 seconds for first deployment (faster with cached template)

---

## Next Steps

✅ **You now understand Proximity's internals!**

Continue to:
- **[Development Guide](5_DEVELOPMENT.md)** - Contribute code to the project

---

<div align="center">

[← Back: Usage Guide](3_USAGE_GUIDE.md) • [Next: Development →](5_DEVELOPMENT.md)

</div>
