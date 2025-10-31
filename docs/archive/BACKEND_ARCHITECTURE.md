# Proximity Backend - Comprehensive Architecture Map

## Executive Summary

Proximity is a modern, application-centric delivery platform for Proxmox built with Django, Django Ninja (async-first API framework), Celery (async task queue), and Redis. The backend is structured as a multi-app Django project with clear separation of concerns.

**Technology Stack:**
- Framework: Django 5.0
- API: Django Ninja (typed, async-ready)
- Authentication: JWT via dj-rest-auth + simple-jwt
- Task Queue: Celery with Redis broker
- Database: SQLite (dev), PostgreSQL (production)
- Monitoring: Sentry integration
- Proxmox Integration: ProxmoxAPI + SSH for container management

---

## 1. Backend Directory Structure

```
/Users/fab/GitHub/proximity/backend/
├── proximity/                    # Django project settings & config
│   ├── settings.py              # Django & app configuration
│   ├── urls.py                  # URL routing (API endpoints)
│   ├── auth.py                  # Custom JWT authentication
│   ├── celery.py                # Celery task scheduling
│   ├── asgi.py / wsgi.py        # Application servers
│   └── __init__.py
├── apps/                        # Django apps (business logic)
│   ├── core/                    # User, system settings, health checks
│   ├── proxmox/                 # Proxmox host/node management
│   ├── applications/            # Application deployment lifecycle
│   ├── backups/                 # Backup/restore operations
│   ├── catalog/                 # Application catalog (JSON-based)
│   └── monitoring/              # Placeholder for monitoring features
├── api/                         # Legacy API structure (mostly empty)
│   ├── endpoints/               # Endpoint organization
│   └── middleware/              # Custom middleware
├── tests/                       # Test suite
├── manage.py                    # Django management
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Container orchestration
├── db.sqlite3                   # Development database
└── celerybeat-schedule          # Celery scheduler state
```

---

## 2. Django Apps & Their Purposes

### 2.1 Core App (`apps/core/`)
**Purpose:** User authentication, system configuration, health checks

**Key Files:**
- `models.py` - User (custom), SystemSettings (singleton)
- `api.py` - Health check, system info, settings endpoints
- `schemas.py` - Pydantic models for request/response
- `middleware.py` - Sentry user context enrichment
- `auth.py` - Empty (auth delegated to dj-rest-auth)

**Database Models:**
```python
User (extends AbstractUser)
  - avatar, bio, preferred_theme

SystemSettings (singleton)
  - Resource defaults: cpu_cores, memory_mb, disk_gb, swap_mb
  - Network defaults: subnet, gateway, dns_primary/secondary, bridge
  - Feature flags: enable_ai_agent, enable_community_chat, enable_multi_host
  - GitOps config: git_repo_path, git_auto_commit
```

---

### 2.2 Proxmox App (`apps/proxmox/`)
**Purpose:** Proxmox host discovery, node management, resource monitoring

**Key Files:**
- `models.py` - ProxmoxHost, ProxmoxNode
- `api.py` - CRUD endpoints for hosts/nodes, connection testing
- `services.py` - ProxmoxAPI wrapper, connection pooling, SSH exec
- `schemas.py` - Host/node request/response models

**Database Models:**
```python
ProxmoxHost
  - name, host (IP/hostname), port, ssh_port, user, password
  - verify_ssl, is_active, is_default
  - last_seen, total_cpu, total_memory, total_storage
  - created_at/updated_at, created_by

ProxmoxNode
  - host (FK), name, status (online/offline)
  - cpu_count, cpu_usage, memory_total/used, storage_total/used
  - uptime, ip_address, pve_version, lxc_count
```

---

### 2.3 Applications App (`apps/applications/`)
**Purpose:** Application deployment, lifecycle management, configuration

**Key Files:**
- `models.py` - Application, DeploymentLog
- `api.py` - Full CRUD + lifecycle endpoints
- `tasks.py` - Celery tasks for deployment/cloning/adoption
- `services.py` - Business logic for app operations
- `port_manager.py` - Port allocation service
- `schemas.py` - Request/response models

**Database Models:**
```python
Application
  - id (app_id, custom PK), catalog_id, name, hostname
  - status (deploying/cloning/running/stopped/error/updating/removing)
  - urls: url, iframe_url
  - ports: public_port, internal_port
  - lxc_id, lxc_root_password
  - host (FK ProxmoxHost), node
  - config (JSON), ports (JSON), volumes (JSON), environment (JSON)
  - owner (FK User), created_at/updated_at, state_changed_at

DeploymentLog
  - application (FK), timestamp, level (info/warning/error)
  - message, step (named stage of deployment)
```

---

### 2.4 Backups App (`apps/backups/`)
**Purpose:** LXC container backup/restore lifecycle

**Key Files:**
- `models.py` - Backup model
- `api.py` - Backup CRUD endpoints (nested under /apps/{app_id}/backups)
- `tasks.py` - Async backup/restore/delete operations
- `schemas.py` - Backup request/response models

**Database Models:**
```python
Backup
  - application (FK), file_name, storage_name (e.g., 'local')
  - size (bytes), backup_type (snapshot/suspend/stop)
  - compression (zstd/gzip/lzo)
  - status (creating/completed/failed/restoring/deleting)
  - error_message, created_at/updated_at, completed_at
  - Properties: size_mb, size_gb, is_completed, is_in_progress
```

---

### 2.5 Catalog App (`apps/catalog/`)
**Purpose:** Application catalog from JSON files (no DB models)

**Key Files:**
- `models.py` - Empty (catalog is file-based)
- `api.py` - Catalog search/filter endpoints
- `services.py` - CatalogService (load, search, filter JSON)
- `schemas.py` - CatalogAppSchema, catalog responses

**No database models** - Catalog loaded from `/catalog_data/` JSON files

---

### 2.6 Monitoring App (`apps/monitoring/`)
**Purpose:** Placeholder for future monitoring features

**Status:** Not fully implemented yet

---

## 3. Complete API Endpoint Map

### Authentication Endpoints (dj-rest-auth)
```
POST   /api/auth/login/                    # Login, returns JWT tokens in HttpOnly cookies
POST   /api/auth/logout/                   # Logout
POST   /api/auth/registration/             # User registration
POST   /api/auth/token/refresh/            # Refresh access token
GET    /api/auth/user/                     # Get authenticated user
```

### Health & System Endpoints (Core)
```
GET    /api/core/health                    # Health check (public, no auth)
GET    /api/core/system/info               # System configuration
GET    /api/core/sentry-debug/             # Sentry test error (dev only)

GET    /api/core/settings/resources        # Get resource defaults
POST   /api/core/settings/resources        # Update (admin only)
GET    /api/core/settings/network          # Get network defaults
POST   /api/core/settings/network          # Update (admin only)
```

### Proxmox Management (Proxmox)
```
GET    /api/proxmox/hosts                  # List all Proxmox hosts
POST   /api/proxmox/hosts                  # Create new host
GET    /api/proxmox/hosts/{host_id}        # Get host details
PUT    /api/proxmox/hosts/{host_id}        # Update host
DELETE /api/proxmox/hosts/{host_id}        # Delete host

POST   /api/proxmox/hosts/{host_id}/test   # Test connection
POST   /api/proxmox/hosts/{host_id}/sync-nodes  # Sync nodes from Proxmox

GET    /api/proxmox/nodes                  # List nodes (optional host_id filter)
```

### Application Management (Applications)
```
GET    /api/apps/                          # List apps (paginated, searchable)
POST   /api/apps/                          # Create & deploy new app
GET    /api/apps/{app_id}                  # Get app details
POST   /api/apps/{app_id}/action           # Perform action: start/stop/restart/delete

GET    /api/apps/discover                  # Discover unmanaged containers
POST   /api/apps/adopt                     # Adopt existing container

POST   /api/apps/{app_id}/clone            # Clone application
GET    /api/apps/{app_id}/logs             # Get deployment logs (paginated)
```

### Backup Management (Backups)
```
GET    /api/apps/{app_id}/backups          # List backups for app
POST   /api/apps/{app_id}/backups          # Create backup (202 async)
GET    /api/apps/{app_id}/backups/{backup_id}     # Get backup details
POST   /api/apps/{app_id}/backups/{backup_id}/restore  # Restore (202 async)
DELETE /api/apps/{app_id}/backups/{backup_id}     # Delete backup (202 async)
GET    /api/apps/{app_id}/backups/stats    # Get backup statistics
```

### Catalog (Catalog)
```
GET    /api/catalog/                       # List all catalog apps
GET    /api/catalog/categories             # List all categories
GET    /api/catalog/search                 # Search by query
GET    /api/catalog/category/{category}    # Filter by category
GET    /api/catalog/stats                  # Catalog statistics
POST   /api/catalog/reload                 # Reload from disk (admin)
GET    /api/catalog/{app_id}               # Get single app
```

---

## 4. API Request/Response Schemas

### Authentication Requests/Responses
```python
# LOGIN
POST /api/auth/login/
{
    "username": "string",
    "password": "string"
}
Response:
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "preferred_theme": "rack_proximity"
    }
}

# REGISTRATION
POST /api/auth/registration/
{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepass123"
}
```

### Application Deployment
```python
# CREATE APPLICATION
POST /api/apps/
{
    "catalog_id": "nginx",
    "hostname": "my-nginx-01",
    "config": {
        "image": "nginx:latest"
    },
    "environment": {
        "NGINX_PORT": "80"
    },
    "node": null  # Optional, auto-selected if null
}
Response (201):
{
    "id": "nginx-a1b2c3d4",
    "catalog_id": "nginx",
    "name": "nginx",
    "hostname": "my-nginx-01",
    "status": "deploying",
    "url": null,
    "iframe_url": null,
    "public_port": 8080,
    "internal_port": 80,
    "lxc_id": null,
    "node": "pve-node-1",
    "host_id": 1,
    "created_at": "2024-10-29T12:00:00Z",
    "updated_at": "2024-10-29T12:00:00Z",
    "config": {"image": "nginx:latest"},
    "environment": {"NGINX_PORT": "80"}
}

# APP ACTION
POST /api/apps/{app_id}/action
{
    "action": "start"  # start, stop, restart, delete
}
Response:
{
    "success": true,
    "message": "Starting my-nginx-01"
}

# CLONE APPLICATION
POST /api/apps/{app_id}/clone
{
    "new_hostname": "my-nginx-clone-01"
}
Response (202):
{
    "success": true,
    "message": "Cloning my-nginx-01 to my-nginx-clone-01...",
    "source_app_id": "nginx-a1b2c3d4",
    "new_hostname": "my-nginx-clone-01"
}

# ADOPT CONTAINER
POST /api/apps/adopt
{
    "vmid": 105,
    "node_name": "pve-node-1",
    "suggested_type": "nginx",
    "port_to_expose": 80
}
Response (202):
{
    "success": true,
    "message": "Adoption of container 105 started...",
    "vmid": 105,
    "node": "pve-node-1",
    "type": "nginx",
    "port_detection": "manual:80"
}
```

### List Applications
```python
GET /api/apps/?page=1&per_page=20&status=running&search=nginx

Response:
{
    "apps": [
        {
            "id": "nginx-a1b2c3d4",
            "catalog_id": "nginx",
            "name": "nginx",
            "hostname": "my-nginx-01",
            "status": "running",
            "url": "http://10.0.0.105:80",
            "public_port": 8080,
            "internal_port": 80,
            "lxc_id": 105,
            "node": "pve-node-1",
            "host_id": 1,
            "created_at": "2024-10-29T12:00:00Z",
            "updated_at": "2024-10-29T12:00:00Z",
            "config": {},
            "environment": {},
            "cpu_usage": 5.2,
            "memory_used": 512000000,
            "memory_total": 2147483648,
            "disk_used": 1073741824,
            "disk_total": 21474836480
        }
    ],
    "total": 42,
    "page": 1,
    "per_page": 20
}
```

### Backup Operations
```python
# CREATE BACKUP
POST /api/apps/{app_id}/backups
{
    "backup_type": "snapshot",    # snapshot, suspend, stop
    "compression": "zstd"         # zstd, gzip, lzo
}
Response (202):
{
    "id": 1,
    "status": "creating",
    "message": "Backup creation started for my-app"
}

# LIST BACKUPS
GET /api/apps/{app_id}/backups
Response:
{
    "backups": [
        {
            "id": 1,
            "application_id": "app-123",
            "file_name": "vzdump-lxc-105-2024_10_29-120000.tar.zst",
            "storage_name": "local",
            "size": 1073741824,
            "backup_type": "snapshot",
            "compression": "zstd",
            "status": "completed",
            "error_message": null,
            "created_at": "2024-10-29T12:00:00Z",
            "completed_at": "2024-10-29T12:05:00Z"
        }
    ],
    "total": 1
}

# RESTORE BACKUP
POST /api/apps/{app_id}/backups/{backup_id}/restore
Response (202):
{
    "backup_id": 1,
    "application_id": "app-123",
    "status": "restoring",
    "message": "Restore operation started..."
}

# BACKUP STATISTICS
GET /api/apps/{app_id}/backups/stats
Response:
{
    "total_backups": 5,
    "completed_backups": 4,
    "failed_backups": 0,
    "in_progress_backups": 1,
    "total_size_gb": 5.25,
    "average_size_mb": 1280.5
}
```

### Catalog
```python
# LIST ALL APPS
GET /api/catalog/
Response:
{
    "total": 42,
    "applications": [
        {
            "id": "nginx",
            "name": "Nginx",
            "description": "Lightweight web server",
            "version": "1.24",
            "category": "web",
            "tags": ["web", "proxy", "reverse-proxy"],
            "icon": "icon.png",
            "documentation": "https://...",
            "homepage": "https://nginx.org",
            "repository": "https://github.com/...",
            "env_vars": {...},
            "ports": {...}
        }
    ]
}

# SEARCH
GET /api/catalog/search?q=nginx
GET /api/catalog/category/web
GET /api/catalog/{app_id}
GET /api/catalog/categories
GET /api/catalog/stats
```

---

## 5. Database Models

### Core App Models
```python
User (extends Django AbstractUser)
  Fields:
  - username, password, email, first_name, last_name
  - avatar (ImageField), bio, preferred_theme
  - is_staff, is_active, is_superuser, last_login, date_joined

SystemSettings (singleton, pk=1)
  Fields:
  - Resource: default_cpu_cores, default_memory_mb, default_disk_gb, default_swap_mb
  - Network: default_subnet, default_gateway, default_dns_primary, default_dns_secondary, default_bridge
  - Features: enable_ai_agent, enable_community_chat, enable_multi_host
  - Git: git_repo_path, git_auto_commit
  - Metadata: updated_at, updated_by (FK User)
```

### Proxmox App Models
```python
ProxmoxHost
  Fields:
  - name (unique), host, port, ssh_port, user, password
  - verify_ssl, is_active, is_default
  - last_seen, total_cpu, total_memory, total_storage
  - created_at, updated_at, created_by (FK User)

ProxmoxNode
  Fields:
  - host (FK ProxmoxHost), name, status, node_type
  - cpu_count, cpu_usage, memory_total, memory_used
  - storage_total, storage_used, uptime, ip_address
  - pve_version, lxc_count, last_updated
  - Unique: (host, name)
```

### Applications App Models
```python
Application
  Fields:
  - id (CharField, custom PK), catalog_id, name, hostname (unique)
  - status (CharField, choices), url, iframe_url
  - public_port (unique), internal_port (unique)
  - lxc_id (unique), lxc_root_password
  - host (FK ProxmoxHost), node
  - config (JSONField), ports (JSONField), volumes (JSONField)
  - environment (JSONField)
  - owner (FK User), created_at, updated_at, state_changed_at

DeploymentLog
  Fields:
  - application (FK), timestamp, level, message, step
  - Ordering: ['-timestamp']
```

### Backups App Models
```python
Backup
  Fields:
  - application (FK), file_name, storage_name
  - size (BigInteger), backup_type, compression
  - status (CharField, choices), error_message
  - created_at, updated_at, completed_at
  - Indexes: [(application, status), (status, created_at)]
```

---

## 6. Error Handling Patterns

### Exception Hierarchy
```python
# Custom exceptions
ProxmoxError(Exception)
  - Used by ProxmoxService for Proxmox API failures
  - Categories: authentication, connection, container lifecycle, snapshot operations

# HTTP Error Responses
HttpError(status_code, message)
  - 400: Bad request (validation, conflict, etc.)
  - 403: Forbidden (insufficient permissions)
  - 404: Not found
  - 409: Conflict (duplicate hostname, container already managed)
  - 500: Internal server error
  - 503: Service unavailable (no online nodes)
```

### Error Handling Patterns

**1. API Endpoints:**
```python
# Pattern: validate -> execute -> handle exceptions
try:
    service = ProxmoxService(host_id=host_id)
    result = service.operation()
    return {success: True, ...}
except ProxmoxError as e:
    return {success: False, message: str(e)}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HttpError(500, f"Error: {str(e)}")
```

**2. Task Handling:**
```python
# Pattern: log deployment -> handle exceptions -> update status
@shared_task(bind=True, max_retries=3)
def deploy_app_task(self, ...):
    try:
        log_deployment(app_id, 'info', 'Starting...', 'init')
        # ... perform operations ...
    except ProxmoxError as e:
        log_deployment(app_id, 'error', str(e), 'error')
        app.status = 'error'
        app.save()
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    except Exception as e:
        logger.error(f"Unexpected: {e}", exc_info=True)
        app.status = 'error'
        app.save()
        raise
```

**3. Middleware:**
```python
# Sentry user context enrichment
class SentryUserContextMiddleware:
    def process_request(self, request):
        if request.user.is_authenticated:
            sentry_sdk.set_user({...})
        else:
            sentry_sdk.set_user(None)
```

**4. Validation:**
```python
# Pydantic models validate request payloads
class ApplicationCreate(BaseModel):
    catalog_id: str
    hostname: str = Field(..., min_length=3, max_length=63)
    config: Dict[str, Any] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)

# CIDR validation in network settings
import ipaddress
ipaddress.IPv4Network(subnet, strict=False)  # Raises ValueError if invalid
```

---

## 7. Authentication & Authorization

### Authentication Flow
```
1. User submits login credentials to POST /api/auth/login/
2. dj-rest-auth validates credentials against User model
3. simple-jwt generates access_token (60 min) + refresh_token (7 days)
4. Tokens returned in:
   - HttpOnly cookies (proximity-auth-cookie, proximity-refresh-cookie)
   - Response body (for JS access)
5. Client includes cookie in subsequent requests
6. JWTCookieAuthenticator validates token in request.auth
```

### Authorization Levels
```python
# Global Auth: All endpoints protected by JWT (except /health, /auth/*)
@api.get("/health", auth=None)  # Public endpoint

# Admin-Only Checks
if not request.auth or not request.auth.is_staff:
    return 403, {"error": "Admin privileges required"}

# User Ownership
if request.user.is_authenticated and not request.user.is_staff:
    queryset = queryset.filter(owner=request.user)  # Users see only their apps
```

### JWT Token Details
```
ACCESS_TOKEN_LIFETIME: 60 minutes
REFRESH_TOKEN_LIFETIME: 7 days
ROTATE_REFRESH_TOKENS: True (new refresh token issued on each refresh)
BLACKLIST_AFTER_ROTATION: True
ALGORITHM: HS256
SIGNING_KEY: settings.SECRET_KEY
USER_ID_CLAIM: 'user_id'
```

---

## 8. Async/Background Tasks (Celery)

### Task Configuration
```python
# Broker & Results Backend
CELERY_BROKER_URL = redis://redis:6379/0
CELERY_RESULT_BACKEND = redis://redis:6379/0
CELERY_TASK_TIME_LIMIT = 30 minutes

# Serialization
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
```

### Periodic Tasks (Celery Beat)
```python
# Reconciliation - runs hourly
'reconcile-applications-every-hour'
  Task: apps.applications.tasks.reconciliation_task
  Schedule: Every 3600 seconds
  Expires: 3000 seconds (50 min)

# Janitor - runs every 6 hours
'cleanup-stuck-applications-every-6-hours'
  Task: apps.applications.tasks.janitor_task
  Schedule: Every 21600 seconds
  Expires: 20000 seconds (5.5 hours)
```

### Application Lifecycle Tasks
```python
@shared_task(bind=True, max_retries=3)
deploy_app_task(app_id, catalog_id, hostname, host_id, node, config, environment, owner_id)
  # Returns: {success, app_id, vmid, hostname, status}
  # Failure: Updates app.status = 'error', retries with backoff

start_app_task(app_id)
  # Starts LXC container

stop_app_task(app_id)
  # Stops LXC container

restart_app_task(app_id)
  # Restarts LXC container

delete_app_task(app_id)
  # Deletes LXC container and application record

clone_app_task(source_app_id, new_hostname, owner_id)
  # Clones LXC container to new hostname

adopt_app_task(payload)
  # Imports unmanaged LXC container into Proximity management
```

### Backup Lifecycle Tasks
```python
create_backup_task(application_id, backup_type, compression)
  # Creates LXC backup via Proxmox

restore_backup_task(backup_id)
  # Restores LXC from backup (destructive)

delete_backup_task(backup_id)
  # Deletes backup file from storage
```

### Task Status Patterns
```
API Response → 202 Accepted
↓
Celery Task Queued → Processing
↓
Client polls GET /api/apps/{app_id}/logs or checks app status
↓
Task completes → Database updated → Client sees final state
```

---

## 9. Service Layer Architecture

### ProxmoxService
```python
class ProxmoxService:
    """Wraps ProxmoxAPI with connection pooling and error handling."""

    Methods:
    - get_client() → ProxmoxAPI (cached in Redis)
    - test_connection() → bool
    - sync_nodes() → int (count synced)
    - get_nodes() → List[dict]
    - get_lxc_containers(node) → List[dict]
    - get_next_vmid() → int
    - create_lxc(vmid, hostname, config) → dict
    - configure_lxc_docker(vmid, hostname) → None (SSH)
    - start_lxc(vmid) → dict
    - stop_lxc(vmid) → dict
    - restart_lxc(vmid) → dict
    - delete_lxc(vmid) → dict
    - create_backup(vmid, backup_type, compression) → str (filename)
    - restore_backup(vmid, backup_file) → None
    - get_lxc_status(vmid) → dict
    - get_lxc_config(vmid) → dict
    - discover_unmanaged_lxc() → List[dict]
```

### PortManagerService
```python
class PortManagerService:
    """Allocates unique port pairs for applications."""

    Methods:
    - allocate_ports() → Tuple[public_port, internal_port]
    - release_ports(public_port, internal_port) → None
    - is_port_available(port) → bool

    Port Ranges:
    - Public: 8000-9000 (routable to internet)
    - Internal: 80-9000 (container-internal)
```

### CatalogService
```python
class CatalogService:
    """Loads and searches application catalog from JSON files."""

    Methods:
    - get_all_apps() → List[CatalogAppSchema]
    - get_app_by_id(app_id) → Optional[CatalogAppSchema]
    - search_apps(query) → List[CatalogAppSchema]
    - filter_by_category(category) → List[CatalogAppSchema]
    - get_categories() → List[str]
    - get_stats() → dict
    - reload() → None (reload from disk)

    Source: /Users/fab/GitHub/proximity/catalog_data/
```

---

## 10. Monitoring & Observability

### Sentry Integration
```python
# Configuration in settings.py
SENTRY_DSN = os.getenv('SENTRY_DSN')
SENTRY_ENVIRONMENT = 'development' | 'staging' | 'production'
SENTRY_TRACES_SAMPLE_RATE = 1.0 (default)
SENTRY_PROFILES_SAMPLE_RATE = 0.1

# Event Filtering
before_send(event) - Filters noisy events
before_send_transaction(event) - Filters health checks, static files

# User Context
Set via middleware for all authenticated requests
```

### Logging
```
Level: DEBUG (dev) | INFO (prod)
Loggers:
  - django.* → INFO
  - apps.* → DEBUG (dev) | INFO (prod)

Format: {levelname} {asctime} {module} {message}
Output: Console (stdout)
```

### Health Checks
```
GET /api/core/health (public, no auth)
  - Checks database connection
  - Checks Redis/cache connection
  - Returns: {status, database, cache, service, version}
```

---

## 11. Configuration & Deployment

### Environment Variables
```
DJANGO:
  - DEBUG (False/True)
  - SECRET_KEY
  - ALLOWED_HOSTS
  - DATABASE_URL (default: sqlite:///db.sqlite3)

PROXMOX:
  - PROXMOX_HOST, PROXMOX_USER, PROXMOX_PASSWORD
  - PROXMOX_PORT (8006), PROXMOX_VERIFY_SSL (False)

CELERY:
  - CELERY_BROKER_URL (redis://redis:6379/0)
  - CELERY_RESULT_BACKEND (redis://redis:6379/0)

REDIS:
  - REDIS_URL (redis://redis:6379/0)

CORS:
  - CORS_ALLOWED_ORIGINS (http://localhost:5173)
  - CORS_ALLOW_CREDENTIALS (True)

JWT:
  - REST_AUTH.JWT_AUTH_COOKIE = 'proximity-auth-cookie'
  - REST_AUTH.JWT_AUTH_REFRESH_COOKIE = 'proximity-refresh-cookie'

SENTRY:
  - SENTRY_DSN, SENTRY_ENVIRONMENT, SENTRY_RELEASE
  - SENTRY_TRACES_SAMPLE_RATE, SENTRY_PROFILES_SAMPLE_RATE
```

### Docker Compose Services
```
Backend: Django dev server (port 8000)
Frontend: Vite (port 5173)
Database: PostgreSQL (or SQLite)
Redis: Cache & Celery broker
Celery Worker: Task execution
Celery Beat: Scheduled tasks
```

---

## 12. Key Design Patterns

### Singleton Pattern
- **SystemSettings**: Only one instance (pk=1) via `SystemSettings.load()`

### Service Layer Pattern
- **ProxmoxService, PortManagerService, CatalogService**: Encapsulate business logic
- API endpoints delegate to services

### Async Task Pattern
- **Celery @shared_task**: Long-running operations (deploy, backup, clone)
- **202 Accepted** response: Task queued, client polls for completion
- **Deployment logs**: Track multi-step processes

### Transaction Safety
```python
# Two-phase commit for deployment creation
with transaction.atomic():
    app = Application.objects.create(...)  # 1. Create in DB
transaction.on_commit(
    lambda: deploy_app_task.delay(...)  # 2. Queue task after commit
)
# Prevents race condition where task runs before object exists
```

### Connection Pooling
- **ProxmoxAPI client**: Cached in Redis for 5 minutes
- **Cache key**: `proxmox_client_{host_id}`

### Smart Node Selection
```python
# For deployments without explicit node:
1. Get all online nodes across active hosts
2. Calculate available memory = total - used
3. Select node with maximum available memory
4. Fallback to first online node if no memory info
```

---

## 13. Testing & Validation

### Test Mode
```python
# Simulate deployment without Proxmox
settings.TESTING_MODE = True
or
os.environ['USE_MOCK_PROXMOX'] = '1'

# Generates fake VMID (9000+) and skips real Proxmox calls
```

### Data Validation
```python
# Pydantic models for API inputs
ApplicationCreate - validates hostname length, catalog_id format
NetworkSettingsRequest - validates CIDR, IP addresses

# Django model validators
MinValueValidator, MaxValueValidator for ports
EmailValidator for email fields
```

---

## 14. Quick Reference: Common Workflows

### Deploy New Application
```
1. POST /api/apps/ {catalog_id, hostname, config, environment}
2. API validates hostname uniqueness, selects node
3. Creates Application record, allocates ports
4. Queues deploy_app_task
5. Returns 201 with app details
6. Client polls GET /api/apps/{app_id} until status != 'deploying'
7. Task creates LXC, configures, starts container
8. Updates Application.status = 'running', .lxc_id = VMID
```

### Backup and Restore
```
1. POST /api/apps/{app_id}/backups
2. Creates Backup record, queues create_backup_task
3. Returns 202 Accepted
4. Task creates snapshot via Proxmox, updates Backup.status = 'completed'
5. To restore: POST /api/apps/{app_id}/backups/{backup_id}/restore
6. Queues restore_backup_task (async, destructive)
7. Returns 202 Accepted
```

### Adopt Unmanaged Container
```
1. GET /api/apps/discover - scans Proxmox for unmanaged containers
2. POST /api/apps/adopt {vmid, node_name, suggested_type}
3. Queues adopt_app_task
4. Returns 202 Accepted
5. Task imports container as Application with original config
6. Allocates ports, creates Application record
```

### Admin Configuration
```
1. GET /api/core/settings/resources - view current defaults
2. POST /api/core/settings/resources {cpu_cores, memory_mb, disk_gb, swap_mb}
3. Requires request.auth.is_staff = True
4. Updates SystemSettings singleton
5. All future deployments use new defaults
```

---

## 15. Dependencies

**Key Python Packages:**
```
Django 5.0 - Web framework
django-ninja - Async-first API
django-cors-headers - CORS support
dj-rest-auth - JWT authentication
djangorestframework-simplejwt - Token generation
proxmoxer - Proxmox API client
paramiko - SSH for pct exec
celery - Task queue
redis - Cache & broker
psycopg2 - PostgreSQL driver
sentry-sdk - Error tracking
pydantic - Validation
```

---

## 16. Future Improvements

- [ ] Password encryption (currently stored plaintext in DB)
- [ ] Monitoring app implementation
- [ ] Kubernetes support
- [ ] Multi-region deployments
- [ ] Advanced scheduling/balancing
- [ ] Resource quotas per user
- [ ] Audit logging
- [ ] Role-based access control (RBAC)

---

## File Reference Guide

| Component | File Path |
|-----------|-----------|
| Settings | `/Users/fab/GitHub/proximity/backend/proximity/settings.py` |
| URLs | `/Users/fab/GitHub/proximity/backend/proximity/urls.py` |
| Auth | `/Users/fab/GitHub/proximity/backend/proximity/auth.py` |
| Celery Config | `/Users/fab/GitHub/proximity/backend/proximity/celery.py` |
| Core API | `/Users/fab/GitHub/proximity/backend/apps/core/api.py` |
| Proxmox API | `/Users/fab/GitHub/proximity/backend/apps/proxmox/api.py` |
| Proxmox Service | `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py` |
| Apps API | `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` |
| Apps Tasks | `/Users/fab/GitHub/proximity/backend/apps/applications/tasks.py` |
| Backups API | `/Users/fab/GitHub/proximity/backend/apps/backups/api.py` |
| Catalog API | `/Users/fab/GitHub/proximity/backend/apps/catalog/api.py` |
| Catalog Service | `/Users/fab/GitHub/proximity/backend/apps/catalog/services.py` |
