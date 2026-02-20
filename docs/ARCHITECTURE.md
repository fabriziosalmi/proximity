# Proximity System Architecture

## Overview

Proximity is a full-stack application deployment platform that simplifies container management across multiple Proxmox hosts. It provides a web-based interface and REST API for deploying, managing, and monitoring containerized applications.

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser / Client                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Frontend (SvelteKit)                        │
│  - Modern Web UI                                             │
│  - Real-time updates                                         │
│  - Responsive design                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────▼──────────────────────────────────┐
│              Backend API (Django Ninja)                      │
│  - REST Endpoints                                            │
│  - Authentication (JWT)                                      │
│  - Business Logic                                            │
│  - Database ORM                                              │
└──────────────────────────┬──────────────────────────────────┘
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐      ┌────▼────┐      ┌──▼──────┐
    │PostgreSQL│      │  Redis  │      │ Celery  │
    │ Database │      │ Cache   │      │ Queue   │
    └──────────┘      └─────────┘      └──┬──────┘
                                           │
         ┌─────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │  Proxmox Integration (API)             │
    │  - Node management                     │
    │  - Container deployment                │
    │  - Resource allocation                 │
    │  - Backup management                   │
    └────┬──────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │  Proxmox Infrastructure                │
    │  - pve (Host 1)                        │
    │  - opti2 (Host 2)                      │
    │  - Additional nodes                    │
    └────────────────────────────────────────┘
```

## Technology Stack

### Frontend
- **Framework:** SvelteKit
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **UI Components:** Custom SvelteKit components
- **State Management:** Svelte stores
- **HTTP Client:** Fetch API

### Backend
- **Framework:** Django 5.1
- **API:** Django Ninja (REST)
- **ORM:** Django ORM
- **Task Queue:** Celery
- **Database:** PostgreSQL
- **Cache:** Redis
- **Auth:** JWT via djangorestframework-simplejwt

### Infrastructure
- **Deployment:** Docker / Docker Compose
- **Containerization:** LXC (via Proxmox)
- **Proxmox API:** Version 2.0+
- **Monitoring:** Sentry
- **Logging:** Django logging

## Core Components

### 1. Frontend Application (SvelteKit)
Located: `/frontend`

**Responsibilities:**
- User interface for application management
- Real-time status updates
- Application deployment interface
- Backup and restore management
- System monitoring dashboard

**Key Routes:**
```
/ → Dashboard
/apps → Application listing
/apps/[id] → Application details
/deploy → Deployment wizard
/backups → Backup management
/settings → System settings
```

### 2. Backend API (Django)
Located: `/backend`

**Core Apps:**
```
proximity/
├── apps/
│   ├── applications/     # App deployment & management
│   ├── backups/          # Backup operations
│   ├── catalog/          # Application catalog
│   ├── proxmox/          # Proxmox integration
│   ├── core/             # Authentication & user management
│   └── [other apps]/
└── proximity/
    ├── settings.py       # Django configuration
    └── urls.py           # URL routing
```

### 3. Database Schema
Located: `/backend/apps/*/migrations`

**Key Models:**
```python
User
  ├─ Applications (1:N)
  │  ├─ Backups (1:N)
  │  └─ DeploymentLogs (1:N)
  └─ Tokens (1:N)

ProxmoxHost
  ├─ ProxmoxNodes (1:N)
  └─ Applications (1:N)

Application
  ├─ Backups (1:N)
  ├─ DeploymentLogs (1:N)
  └─ ProxmoxHost (N:1)

Backup
  ├─ Application (N:1)
  └─ [Snapshots/Files]
```

### 4. Proxmox Integration
Located: `/backend/apps/proxmox`

**Service Architecture:**
```
ProxmoxService
├─ get_host()
├─ get_nodes()
├─ deploy_container()
├─ create_backup()
├─ restore_backup()
└─ delete_backup()
```

**Integration Pattern:**
```
API Request
  ↓
Authentication & Authorization
  ↓
Business Logic (Django)
  ↓
ProxmoxService Call
  ↓
Proxmox API HTTP Request
  ↓
Container Operation
  ↓
Database Update
  ↓
Response to Client
```

### 5. Task Queue (Celery)
Located: `/backend/apps/*/tasks.py`

**Async Operations:**
- Container deployment
- Backup creation
- Backup restoration
- Cleanup operations

## Data Flow

### Application Deployment
```
1. User submits deployment form
   ↓
2. Frontend calls POST /api/apps/
   ↓
3. Backend validates request
   ↓
4. Backend creates Application record (status: "deploying")
   ↓
5. Celery task triggered: create_deployment_task
   ↓
6. ProxmoxService connects to Proxmox host
   ↓
7. Container created via Proxmox API
   ↓
8. Application status updated to "running"
   ↓
9. Frontend polls status and updates UI
```

### Backup Operation
```
1. User requests backup
   ↓
2. POST /api/apps/{id}/backups/
   ↓
3. Backup record created (status: "creating")
   ↓
4. Celery task: create_backup_task
   ↓
5. ProxmoxService.create_backup_file()
   ↓
6. Backup stored in Proxmox storage
   ↓
7. Backup record updated (status: "completed")
   ↓
8. User can restore from this backup
```

## Authentication Flow

```
1. User logs in with credentials
   ↓
2. POST /api/auth/login/
   ↓
3. Backend validates credentials
   ↓
4. JWT token generated
   ↓
5. Token stored in HTTP-only cookie
   ↓
6. Subsequent requests include JWT in Authorization header
   ↓
7. Middleware validates JWT
   ↓
8. Request processed with user context
```

## Database Relationships

### User & Applications
```
User (1) ──── (*) Application
- Each user can own multiple applications
- User authentication verified per request
- Applications filtered by owner
```

### Application & Proxmox
```
Application ──→ ProxmoxHost
Application ──→ ProxmoxNode
- Application deployed to specific node
- Resources allocated from host
- Status synchronized with Proxmox
```

### Application & Backups
```
Application (1) ──── (*) Backup
- Each application can have multiple backups
- Backups linked to specific application
- Restore operation creates new application state
```

## API Architecture

### REST Endpoints
```
Authentication
  POST   /api/auth/login/
  POST   /api/auth/logout/
  GET    /api/auth/user/

Applications
  GET    /api/apps/                      # List
  POST   /api/apps/                      # Create
  GET    /api/apps/{id}/                 # Detail
  PATCH  /api/apps/{id}/                 # Update
  DELETE /api/apps/{id}/                 # Delete

Backups
  GET    /api/apps/{app_id}/backups/
  POST   /api/apps/{app_id}/backups/
  GET    /api/apps/{app_id}/backups/{id}/
  POST   /api/apps/{app_id}/backups/{id}/restore/
  DELETE /api/apps/{app_id}/backups/{id}/

Catalog
  GET    /api/catalog/
  GET    /api/catalog/{id}/
  GET    /api/catalog/categories/
  GET    /api/catalog/search/
```

### Response Format
```json
{
  "data": { /* ... */ },
  "status": "success|error",
  "message": "Human-readable message",
  "timestamp": "2025-10-31T10:00:00Z"
}
```

## Deployment Patterns

### Single Host
```
Frontend (SvelteKit)
  ↓
Backend API (Django)
  ↓
PostgreSQL
  ↓
Proxmox Host (Single)
```

### Multi-Host
```
Frontend (SvelteKit)
  ↓
Backend API (Django)
  ↓
PostgreSQL
  ↓
┌─────────────────────┬──────────────────┐
│ Proxmox Host 1      │ Proxmox Host 2   │
│ (pve)               │ (opti2)          │
└─────────────────────┴──────────────────┘
```

## Scalability Considerations

### Horizontal Scaling
- **Stateless API:** Multiple backend instances via load balancer
- **Shared Database:** PostgreSQL for persistence
- **Celery Workers:** Multiple workers for task processing
- **Redis:** Distributed cache and broker

### Vertical Scaling
- Increase resources on single host
- Database optimization (indexing, query optimization)
- Caching strategies (Redis)
- Connection pooling

## Error Handling

```
Request
  ↓
Validation Error? → 400 Bad Request
  ↓
Authentication Error? → 401 Unauthorized
  ↓
Permission Error? → 403 Forbidden
  ↓
Resource Not Found? → 404 Not Found
  ↓
Proxmox Error? → 502 Bad Gateway
  ↓
Internal Error? → 500 Internal Server Error
```

## Monitoring & Observability

### Sentry Integration
- Error tracking and alerting
- Performance monitoring
- Release tracking

### Logging
- Request/response logging
- Task execution logging
- Error stack traces

### Metrics
- Application deployment success rate
- Task queue depth
- Response times
- Database connection pool usage

## Security Architecture

### Authentication
- JWT tokens with expiration
- HTTP-only cookies for token storage
- CSRF protection
- Token refresh mechanism

### Authorization
- Permission-based access control
- User ownership verification
- Admin-only operations

### Data Protection
- Database passwords encrypted in config
- API request/response validation
- SQL injection prevention (ORM)
- XSS protection (Frontend framework)

## Development Considerations

### State Management
- **Frontend:** Svelte stores for local state
- **Backend:** Django models as source of truth
- **Cache:** Redis for session and temporary data

### Testing
- **Unit Tests:** Model and service tests
- **Integration Tests:** API endpoint tests
- **E2E Tests:** Full workflow tests
- **Test Coverage:** 102/102 backend tests passing (see STATUS.md)

### Version Control
- Git for source control
- Feature branches for development
- Pull requests for code review
