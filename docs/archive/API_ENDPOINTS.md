# Proximity API Endpoints

Base URL: `http://localhost:8765/api/v1`

## 📋 Table of Contents
- [Authentication](#authentication)
- [Apps Management](#apps-management)
- [Backups](#backups)
- [System](#system)
- [Settings](#settings)
- [Test & Health](#test--health)

---

## 🔐 Authentication
**Base Path:** `/auth`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user |
| POST | `/login` | User login (returns JWT token) |
| POST | `/logout` | User logout |
| GET | `/me` | Get current user info |
| POST | `/change-password` | Change user password |
| POST | `/refresh` | Refresh JWT token |

---

## 📦 Apps Management
**Base Path:** `/apps`

### Catalog
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog` | Get all available apps in catalog |
| GET | `/catalog/{catalog_id}` | Get specific catalog item |

### App CRUD
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` or `` | List all deployed apps |
| GET | `/{app_id}` | Get specific app details |
| POST | `/deploy` | Deploy new app from catalog |
| PUT | `/{app_id}` | Update app configuration |
| DELETE | `/{app_id}` | Delete app and container |

### App Actions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/{app_id}/actions` | Control app (start/stop/restart/rebuild) |
| POST | `/{app_id}/update` | Update app to newer version |
| POST | `/{app_id}/clone` | Clone existing app |
| PUT | `/{app_id}/config` | Update app configuration |

### App Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{app_id}/status` | **[UNIFIED]** Get app status (simple for running/stopped, rich with progress for deploying/updating) |
| GET | `/{app_id}/logs` | Get app container logs |
| GET | `/{app_id}/stats` | Get app resource statistics |
| GET | `/{app_id}/stats/current` | Get current app stats |

### App Commands
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/{app_id}/exec` | Execute command in container |
| GET | `/{app_id}/commands` | List available commands |
| GET | `/{app_id}/command/{command_name}` | Get specific command details |

---

## 💾 Backups
**Base Path:** `/backups`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/apps/{app_id}/backups` | Create new backup |
| GET | `/apps/{app_id}/backups` | List all backups for app |
| GET | `/apps/{app_id}/backups/{backup_id}` | Get backup details |
| POST | `/apps/{app_id}/backups/{backup_id}/restore` | Restore backup |
| DELETE | `/apps/{app_id}/backups/{backup_id}` | Delete backup |

---

## 🖥️ System
**Base Path:** `/system`

### Health & Info
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/status/initial` | Initial system status |
| GET | `/info` | System information |
| GET | `/metrics` | System metrics |
| GET | `/config` | System configuration |

### Nodes & Containers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/nodes` | List all Proxmox nodes |
| GET | `/nodes/{node_name}` | Get specific node info |
| GET | `/containers` | List all LXC containers |

### Network
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/network/metrics` | Network metrics |
| GET | `/network/public-info` | Public IP and geolocation |
| GET | `/network/status` | Network status |
| POST | `/test-connection` | Test Proxmox connection |

### Proxy
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/proxy/status` | Proxy service status |

### Templates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/templates/cache` | Get cached LXC templates |

### Cleanup
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cleanup/stats` | Get cleanup statistics |
| POST | `/cleanup/run` | Run cleanup operation |

### Infrastructure
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/infrastructure/test-nat` | Test NAT configuration |
| POST | `/infrastructure/rebuild-bridge` | Rebuild network bridge |

---

## ⚙️ Settings
**Base Path:** `/settings`

### Proxmox Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/proxmox` | Get Proxmox settings |
| POST | `/proxmox` | Update Proxmox settings |

### Network Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/network` | Get network settings |
| POST | `/network` | Update network settings |

### Resource Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/resources` | Get resource limits |
| POST | `/resources` | Update resource limits |

### General Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/all` | Get all settings |
| POST | `/` | Create/update setting |
| DELETE | `/{key}` | Delete setting |

---

## 🧪 Test & Health
**Base Path:** `/test`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sentry-backend` | Test Sentry backend integration |
| GET | `/health` | Health check endpoint |
| GET | `/sentry-info` | Get Sentry configuration info |

---

## 📝 Request/Response Examples

### Authentication
```bash
# Login
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "your_password"
}

# Response
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Deploy App
```bash
POST /api/v1/apps/deploy
{
  "catalog_id": "nginx",
  "hostname": "my-nginx",
  "node": "pve"
}
```

### Control App
```bash
POST /api/v1/apps/{app_id}/actions
{
  "action": "start"  # or "stop", "restart", "rebuild"
}
```

### Get Nodes
```bash
GET /api/v1/system/nodes

# Response
[
  {
    "node": "pve",
    "status": "online",
    "type": "node",
    "uptime": 123456,
    "cpu": 0.25,
    "maxcpu": 8,
    "mem": 4294967296,
    "maxmem": 16777216000
  }
]
```

### Get App Status
```bash
GET /api/v1/apps/{app_id}/status

# Simple Response (running/stopped apps)
{
  "status": "running",
  "app_id": "nginx-prod"
}

# Rich Response (deploying/updating apps)
{
  "status": "deploying",
  "app_id": "nginx-prod",
  "progress": 65,
  "current_step": "Configuring network",
  "total_steps": 5,
  "current_step_number": 3
}
```

---

## 🔒 Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer {your_jwt_token}
```

## 📊 HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 500 | Internal Server Error |

---

**Total Endpoints:** 65 *(unified from 67)*
**Last Updated:** October 15, 2025

## 🔄 Changelog

### v2.0 - API Unification (October 15, 2025)
- ✅ **Unified App Status**: Consolidated duplicate endpoints into single `/apps/{app_id}/status`
  - **Removed:** `GET /apps/deploy/{app_id}/status`
  - **Removed:** `GET /apps/{app_id}/deployment-status`
  - **Added:** `GET /apps/{app_id}/status` (single source of truth)
- ✅ **Backup Endpoints**: Already properly nested under `/apps/{app_id}/backups` (no changes needed)
- 📉 Reduced endpoint count from 67 to 65 by eliminating redundancy
