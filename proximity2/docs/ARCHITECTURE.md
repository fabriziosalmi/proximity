# Proximity 2.0 - Architecture & Design

## Overview

Proximity 2.0 is a complete architectural rewrite of the Proximity platform, built from the ground up with modern best practices, scalability, and extensibility as core principles.

## Design Philosophy

### 1. Divertimento (Fun by Design)
Infrastructure management should be engaging, not tedious. We achieve this through:
- Gamified UI elements (progress bars, achievements, visual feedback)
- The "Rack" visualization concept
- Smooth animations and transitions
- Instant feedback on all actions

### 2. Casa Digitale (Digital Home)
Proximity is not just a tool - it's a unified personal environment:
- Single command center for all infrastructure
- Consistent UX across all features
- Personalization (themes, preferences)
- Both work and personal use cases supported

### 3. Tranquillità by Default (Peace of Mind)
Security and reliability are built-in, not bolted on:
- Automatic backups
- Built-in monitoring
- Secure by default configuration
- GitOps for auditability and rollback

## Architecture Stack

### Backend: Django + Django Ninja

**Why Django?**
- Battle-tested ORM with migrations
- Built-in admin panel for operations
- Robust authentication system
- Mature ecosystem

**Why Django Ninja?**
- FastAPI-like performance within Django
- Pydantic integration for validation
- Automatic OpenAPI documentation
- Type safety throughout

**Structure:**
```
backend/
├── proximity/          # Django project
│   ├── settings.py    # Configuration
│   ├── urls.py        # URL routing
│   └── celery.py      # Celery configuration
└── apps/              # Modular Django apps
    ├── core/          # Auth, users, system
    ├── proxmox/       # Proxmox integration
    ├── applications/  # App lifecycle
    ├── backups/       # Backup management
    └── monitoring/    # Metrics & logs
```

### Frontend: SvelteKit + Tailwind

**Why SvelteKit?**
- Compiler-first approach = smaller bundles
- Excellent performance
- Simple, readable component syntax
- Built-in routing and SSR

**Why Tailwind CSS?**
- Utility-first = rapid development
- Consistent design system
- Easy theming via CSS variables
- Production-ready optimizations

**Structure:**
```
frontend/
├── src/
│   ├── routes/        # File-based routing
│   │   ├── +page.svelte
│   │   ├── dashboard/
│   │   ├── apps/
│   │   └── settings/
│   ├── lib/           # Reusable components
│   │   ├── components/
│   │   ├── stores/
│   │   └── api/
│   └── app.css        # Global styles + themes
└── static/            # Static assets
```

### Background Tasks: Celery + Redis

**Why Celery?**
- Industry standard for Python async tasks
- Reliable task queue with retries
- Built-in scheduling (Celery Beat)
- Django integration

**Use Cases:**
- LXC container provisioning
- Application deployment
- Backup creation/restoration
- Node synchronization
- Scheduled maintenance tasks

### Real-time: Django Channels

**Why Channels?**
- WebSocket support for Django
- Real-time console access
- Live deployment logs
- Push notifications

**Use Cases:**
- Integrated terminal/console
- Live log streaming
- Real-time status updates
- Chat/collaboration features

## Data Models

### Core Models

**User** (extends Django's AbstractUser)
- Authentication and authorization
- Profile information
- Theme preferences
- API tokens

**SystemSettings** (singleton)
- Global configuration
- Feature flags
- GitOps settings
- Default values

### Proxmox Models

**ProxmoxHost**
- Multi-host support
- Connection configuration
- Resource tracking
- Health monitoring

**ProxmoxNode** (cached)
- Node information
- Resource utilization
- LXC container counts

### Application Models

**Application**
- Deployed app instances
- Status and lifecycle
- Port mappings
- Volume mounts
- Environment variables

**DeploymentLog**
- Audit trail
- Deployment steps
- Error tracking

### Backup Models

**Backup**
- Backup metadata
- Storage location
- Restore history

## API Design

### RESTful Endpoints

All API endpoints follow REST conventions:

```
GET    /api/apps/           # List apps
POST   /api/apps/           # Create app
GET    /api/apps/{id}       # Get app
PUT    /api/apps/{id}       # Update app
DELETE /api/apps/{id}       # Delete app
POST   /api/apps/{id}/start # Action endpoint
```

### Authentication

JWT-based authentication:
1. Client sends credentials to `/api/core/auth/login`
2. Server returns access token + refresh token
3. Client includes token in `Authorization: Bearer <token>` header
4. Tokens expire and can be refreshed

### Error Handling

Consistent error responses:
```json
{
  "success": false,
  "error": "Error message",
  "details": {
    "field": "Validation error"
  }
}
```

## Database Strategy

### Development
- SQLite for simplicity
- Quick setup, no external dependencies

### Production
- PostgreSQL for robustness
- JSONB fields for flexible configuration
- Proper indexing on foreign keys and lookups

### Migrations
- All schema changes via Django migrations
- Version-controlled
- Reversible when possible

## Scaling Considerations

### Horizontal Scaling
- Stateless backend servers (scale with load balancer)
- Celery workers (scale independently)
- Redis cluster for high availability

### Vertical Scaling
- Database connection pooling
- Celery concurrency settings
- Redis memory limits

### Caching Strategy
- Redis for session storage
- API response caching
- Proxmox API connection pooling

## Security

### Authentication & Authorization
- JWT tokens with expiration
- Role-based access control (RBAC)
- API rate limiting

### Data Protection
- Encrypted passwords (bcrypt)
- Encrypted Proxmox credentials
- HTTPS enforcement in production
- CSRF protection

### Container Security
- Non-root containers
- Minimal base images
- Regular security updates

## Future Architecture (EPIC 3)

### GitOps Integration
- Internal Git repository for state
- All changes as commits
- Reconciliation service
- Full audit trail

### AI Agent
- Local LLM (Qwen) service
- Model-Control-Plane (MCP) tools
- Conversational interface
- Proactive monitoring

### Multi-Host Orchestration
- Host selection algorithms
- Load distribution
- Failover capabilities
- Cross-host networking

### Skinning Engine
- CSS variable-based theming
- Multiple built-in themes
- Custom theme support
- Dark/light mode variants

## Monitoring & Observability

### Logging
- Structured logging (JSON)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Centralized collection (optional ELK stack)

### Metrics
- Application metrics (requests, errors, latency)
- Celery task metrics
- Resource utilization
- Business metrics (deployments, apps)

### Tracing (Optional)
- Sentry for error tracking
- Request tracing across services
- Performance profiling

## Development Workflow

### Local Development
1. Clone repository
2. Run `docker-compose up`
3. Access services on localhost

### Testing
- Backend: pytest + pytest-django
- Frontend: Vitest (unit) + Playwright (E2E)
- Run tests in CI/CD pipeline

### Code Quality
- Backend: black, isort, flake8
- Frontend: ESLint, Prettier
- Pre-commit hooks

### Deployment
- Docker images for all services
- Docker Compose for simple deployments
- Kubernetes manifests for production (future)

## Comparison: v1.0 vs v2.0

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| Backend | FastAPI | Django + Django Ninja |
| Database | SQLite + SQLAlchemy | PostgreSQL + Django ORM |
| Frontend | React | SvelteKit |
| Async Tasks | Custom implementation | Celery |
| Real-time | Custom WebSocket | Django Channels |
| Multi-host | No | Yes |
| Testing | Manual | pytest + Playwright |
| CI/CD | No | GitHub Actions |

## Key Improvements

1. **Robustness**: Django's mature ecosystem vs custom FastAPI patterns
2. **Scalability**: Celery for proven task queue vs custom async
3. **Maintainability**: Modular app structure vs monolithic code
4. **Developer Experience**: Hot reload, type safety, auto documentation
5. **Operations**: Built-in admin panel, migrations, management commands
