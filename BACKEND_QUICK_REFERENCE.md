# Proximity Backend - Quick Reference Guide

## Core Fact Sheet

| Aspect | Details |
|--------|---------|
| **Framework** | Django 5.0 + Django Ninja API |
| **Authentication** | JWT (dj-rest-auth + simple-jwt) in HttpOnly cookies |
| **Task Queue** | Celery with Redis broker |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **Container Runtime** | Proxmox LXC |
| **Monitoring** | Sentry + custom logging |

## Django Apps Overview

```
core/       → Users, system settings, health checks
proxmox/    → Proxmox host/node management
applications/ → App deployment & lifecycle
backups/    → Backup/restore operations
catalog/    → Application catalog (JSON-based)
monitoring/ → Placeholder for future features
```

## API Endpoints at a Glance

### Authentication (dj-rest-auth)
```
POST   /api/auth/login/              # Login → JWT tokens
POST   /api/auth/logout/
POST   /api/auth/registration/
GET    /api/auth/user/
POST   /api/auth/token/refresh/
```

### Core System
```
GET    /api/core/health              # Public health check
GET    /api/core/system/info
GET    /api/core/settings/resources  # Get defaults
POST   /api/core/settings/resources  # Update (admin)
GET    /api/core/settings/network
POST   /api/core/settings/network
```

### Proxmox
```
GET    /api/proxmox/hosts
POST   /api/proxmox/hosts
POST   /api/proxmox/hosts/{id}/test
POST   /api/proxmox/hosts/{id}/sync-nodes
GET    /api/proxmox/nodes
```

### Applications (Main)
```
GET    /api/apps/                    # List (paginated, filterable)
POST   /api/apps/                    # Deploy new app
GET    /api/apps/{id}
POST   /api/apps/{id}/action         # start|stop|restart|delete
POST   /api/apps/{id}/clone
GET    /api/apps/discover            # Find unmanaged containers
POST   /api/apps/adopt               # Import existing container
GET    /api/apps/{id}/logs           # Deployment logs
```

### Backups
```
GET    /api/apps/{app_id}/backups
POST   /api/apps/{app_id}/backups    # Create (202 async)
GET    /api/apps/{app_id}/backups/{id}
POST   /api/apps/{app_id}/backups/{id}/restore  # 202 async
DELETE /api/apps/{app_id}/backups/{id}          # 202 async
GET    /api/apps/{app_id}/backups/stats
```

### Catalog
```
GET    /api/catalog/
GET    /api/catalog/{app_id}
GET    /api/catalog/search?q=query
GET    /api/catalog/category/{category}
GET    /api/catalog/categories
POST   /api/catalog/reload           # Admin only
```

## Database Models (Quick Map)

### Core
- **User**: Extended Django User with avatar, bio, theme
- **SystemSettings**: Singleton (pk=1) with resource/network defaults

### Proxmox
- **ProxmoxHost**: Host config (name, IP, port, credentials)
- **ProxmoxNode**: Node info (status, CPU, memory, storage)

### Applications
- **Application**: Deployed app instance with status, ports, LXC ID
- **DeploymentLog**: Audit trail (step, level, message, timestamp)

### Backups
- **Backup**: Backup record (file, type, compression, status)

## Response Codes

| Code | Meaning |
|------|---------|
| 200  | OK (sync response) |
| 201  | Created (new resource) |
| 202  | Accepted (async task queued) |
| 400  | Bad request (validation) |
| 403  | Forbidden (insufficient privileges) |
| 404  | Not found |
| 409  | Conflict (duplicate, already exists) |
| 500  | Server error |
| 503  | Service unavailable |

## Deployment Flow

```
1. POST /api/apps/
   ↓
2. API creates Application record, allocates ports
   ↓
3. Queues Celery task (deploy_app_task.delay(...))
   ↓
4. Returns 201 with app details (status='deploying')
   ↓
5. Task executes:
   - Get next VMID
   - Create LXC container
   - Configure Docker
   - Start container
   - Update Application.lxc_id, status='running'
   ↓
6. Client polls GET /api/apps/{id} → sees status='running'
```

## Backup Flow

```
Create Backup:
  POST → Celery task → creates snapshot via Proxmox → Backup.status='completed'

Restore Backup (DESTRUCTIVE):
  POST → Celery task → restores from snapshot → overwrites container

Delete Backup:
  DELETE → Celery task → deletes snapshot file
```

## Important Patterns

### Global JWT Auth
- All endpoints protected by JWT cookie (`proximity-auth-cookie`)
- Exception: `/health`, `/auth/*` endpoints
- Token lifetime: 60 minutes (access), 7 days (refresh)

### Admin Checks
```python
if not request.auth or not request.auth.is_staff:
    return 403, {"error": "Admin privileges required"}
```

### User Ownership
```python
# Non-admin users see only their own apps
queryset = queryset.filter(owner=request.user)
```

### Smart Node Selection
- If node not specified, auto-select online node with most available memory
- Falls back to any online node if memory info unavailable

### Transaction Safety
```python
# Create app first, then queue task after commit
with transaction.atomic():
    app = Application.objects.create(...)
transaction.on_commit(lambda: deploy_task.delay(...))
```

## Error Handling Summary

### ProxmoxError Exception
Raised by ProxmoxService for:
- Authentication failures
- Connection errors
- Container lifecycle failures
- Snapshot operation failures

### API Error Responses
```python
400 → Validation/conflict errors
403 → Missing admin privileges
404 → Resource not found
409 → Duplicate hostname, already adopted
500 → Unexpected server error
503 → No online nodes available
```

### Task Retries
- Celery tasks retry up to 3 times with exponential backoff
- Failed tasks set app.status='error' and log error message

## Celery Periodic Tasks

| Task | Schedule | Purpose |
|------|----------|---------|
| reconciliation_task | Every 1 hour | Clean up orphan apps |
| janitor_task | Every 6 hours | Remove stuck deployments |

## Configuration Checklist

Essential environment variables for production:
```
□ DEBUG=False
□ SECRET_KEY=<strong-random-key>
□ DATABASE_URL=postgresql://user:pass@host:5432/db
□ PROXMOX_HOST=<proxmox-ip-or-hostname>
□ PROXMOX_USER=root@pam
□ PROXMOX_PASSWORD=<encrypted-password>
□ CELERY_BROKER_URL=redis://redis:6379/0
□ REDIS_URL=redis://redis:6379/0
□ SENTRY_DSN=https://...
□ CORS_ALLOWED_ORIGINS=https://app.example.com
```

## Common Tasks

### View Running Apps
```bash
GET /api/apps/?status=running
```

### Get App Logs
```bash
GET /api/apps/{app_id}/logs?limit=100
```

### Stop an App
```bash
POST /api/apps/{app_id}/action
{"action": "stop"}
```

### Create Backup
```bash
POST /api/apps/{app_id}/backups
{"backup_type": "snapshot", "compression": "zstd"}
```

### Adopt Unmanaged Container
```bash
1. GET /api/apps/discover  # Find it
2. POST /api/apps/adopt {vmid, node_name}
```

### Update System Settings (Admin)
```bash
POST /api/core/settings/resources
{
    "default_cpu_cores": 4,
    "default_memory_mb": 4096,
    "default_disk_gb": 50,
    "default_swap_mb": 1024
}
```

## File Locations

| Purpose | Path |
|---------|------|
| Settings | `/backend/proximity/settings.py` |
| URL Routes | `/backend/proximity/urls.py` |
| Models | `/backend/apps/*/models.py` |
| API Endpoints | `/backend/apps/*/api.py` |
| Celery Tasks | `/backend/apps/*/tasks.py` |
| Services | `/backend/apps/*/services.py` |
| Schemas | `/backend/apps/*/schemas.py` |

## Security Notes

1. **Passwords**: Currently stored plaintext in DB (TODO: encrypt)
2. **SSL**: Self-signed cert support for development
3. **CORS**: Restrict to frontend origin in production
4. **CSRF**: Trusted origins required for HTTPS
5. **Sentry**: Filters noisy events to manage quota

## Monitoring

### Health Check
```bash
GET /api/core/health
# Returns: {status, database, cache, service, version}
```

### Logging
```
Level: DEBUG (dev) | INFO (prod)
Output: Console/stdout
Loggers: django.*, apps.*
```

### Sentry Integration
- Tracks errors automatically
- Enriches with user context
- Filters out noisy events
- Samples transactions to manage quota

## Testing Mode

Enable fake Proxmox responses:
```bash
# Method 1
TESTING_MODE=True python manage.py runserver

# Method 2
USE_MOCK_PROXMOX=1 python manage.py runserver
```

- Generates fake VMIDs (9000+)
- Skips real Proxmox API calls
- Useful for E2E tests

---

**See `/backend/BACKEND_ARCHITECTURE.md` for comprehensive documentation**
