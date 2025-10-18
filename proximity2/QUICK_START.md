# Proximity 2.0 - Quick Start Guide

## Prerequisites

- Docker & Docker Compose installed
- Git
- At least one Proxmox VE host (v7.0+)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd proximity2
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your Proxmox credentials
```

**Required settings to update:**
- `PROXMOX_HOST`: Your Proxmox hostname/IP
- `PROXMOX_USER`: Proxmox user (default: root@pam)
- `PROXMOX_PASSWORD`: Your Proxmox password
- `SECRET_KEY`: Generate a secure secret key

### 3. Start the Stack

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- Django backend (port 8000)
- Celery worker
- Celery beat scheduler
- SvelteKit frontend (port 5173)

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

### 5. Access Proximity

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/docs
- **Django Admin**: http://localhost:8000/admin

## Development Workflow

### Backend Development

```bash
# View logs
docker-compose logs -f backend

# Run Django commands
docker-compose exec backend python manage.py <command>

# Run tests
docker-compose exec backend pytest

# Create migrations
docker-compose exec backend python manage.py makemigrations
```

### Frontend Development

```bash
# View logs
docker-compose logs -f frontend

# Install new packages
docker-compose exec frontend npm install <package>

# Run linting
docker-compose exec frontend npm run lint
```

### Celery Tasks

```bash
# View worker logs
docker-compose logs -f celery_worker

# Monitor tasks (requires celery flower)
docker-compose exec celery_worker celery -A proximity flower
```

## Architecture Overview

```
proximity2/
├── backend/              # Django + Django Ninja
│   ├── apps/            # Django apps (modular architecture)
│   │   ├── core/       # Auth, users, system settings
│   │   ├── proxmox/    # Proxmox integration
│   │   ├── applications/ # App lifecycle management
│   │   ├── backups/    # Backup management
│   │   └── monitoring/ # Metrics & logging
│   ├── proximity/      # Django project settings
│   └── manage.py
├── frontend/            # SvelteKit
│   ├── src/
│   │   ├── routes/     # File-based routing
│   │   ├── lib/        # Reusable components
│   │   └── app.css     # Global styles
│   └── package.json
└── docker-compose.yml   # Development stack
```

## Next Steps

1. **Configure Proxmox Host**: Go to Settings → Proxmox Hosts
2. **Sync Nodes**: Click "Sync Nodes" to discover your Proxmox nodes
3. **Browse Catalog**: Explore available applications
4. **Deploy First App**: Choose an app and deploy it

## Troubleshooting

### Backend won't start
- Check logs: `docker-compose logs backend`
- Verify database connection: `docker-compose exec db psql -U proximity`

### Frontend can't connect to API
- Verify CORS settings in `.env`
- Check backend is running: `curl http://localhost:8000/api/health`

### Celery tasks not running
- Check worker logs: `docker-compose logs celery_worker`
- Verify Redis connection: `docker-compose exec redis redis-cli ping`

## Support

See full documentation in `/docs` directory or visit [project repository].
