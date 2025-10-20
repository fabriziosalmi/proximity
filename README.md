# Proximity 2.0

**The Definitive Rewrite**

Proximity 2.0 is a complete architectural rewrite of the Proximity platform, built with modern best practices and designed for massive scalability.

## Architecture Stack

### Backend
- **Django 5.x** - Robust ORM, migrations, admin panel
- **Django Ninja** - Fast, Pydantic-driven REST API
- **Celery + Redis** - Asynchronous task processing
- **Django Channels** - WebSocket support for real-time features
- **PostgreSQL** - Production-grade database (SQLite for dev)

### Frontend
- **SvelteKit** - Blazingly fast, compiler-first framework
- **Tailwind CSS** - Utility-first styling
- **shadcn-svelte** - Beautiful, accessible component primitives

### DevOps
- **Docker Compose** - Single-command development environment
- **pytest + pytest-django** - Backend testing
- **Vitest + Playwright** - Frontend testing
- **GitHub Actions** - CI/CD pipeline

## Quick Start

```bash
# Start the entire stack
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# Django Admin: http://localhost:8000/admin
```

## Project Philosophy

### "Divertimento"
We transform tedious infrastructure management into an engaging, almost gamified experience.

### "Casa Digitale"
Proximity is not a tool; it's a personal digital environment - your unified command center.

### "Tranquillità by Default"
Advanced features like security, backups, and reliability are built-in, not optional.

## Development

See the `/docs` directory for detailed documentation on:
- Architecture & Design Decisions
- Development Workflow
- Testing Strategy
- Deployment Guide

## License

MIT License - See LICENSE file for details
