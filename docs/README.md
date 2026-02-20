# Proximity Documentation

Welcome to the Proximity documentation. This covers the main aspects of the project.

## Documentation Structure

### Getting Started
- **[Quick Start Guide](./guides/QUICK_START.md)** - Set up Proximity with Docker Compose
- **[Installation Guide](./INSTALLATION.md)** - Detailed installation instructions
- **[First Steps](./FIRST_STEPS.md)** - Your first deployment

### Architecture & Design
- **[System Architecture](./ARCHITECTURE.md)** - Overall system design and component overview

### API Reference
- **[REST API Documentation](./API.md)** - Complete endpoint reference

### Development
- **[Testing Guide](./TESTING.md)** - Running and writing tests
- **[Contributing Guide](../CONTRIBUTING.md)** - Contribution guidelines

### Security
- **[Security Summary](../SECURITY_SUMMARY.md)** - Security audit findings and fixes applied
- **[Backend Security Audit](./security/BACKEND_SECURITY_AUDIT_REPORT.md)** - Backend security findings
- **[Frontend Security Audit](./security/FRONTEND_SECURITY_AUDIT_REPORT.md)** - Frontend security findings

## Key Features

- **Proxmox Integration** - Deploy and manage LXC containers via the Proxmox API
- **Application Catalog** - Pre-configured applications ready to deploy
- **Backup Management** - On-demand backup creation and restoration
- **Container Adoption** - Discover and import unmanaged LXC containers
- **Web UI** - SvelteKit-based interface
- **REST API** - Full API with JWT authentication
- **Async Tasks** - Celery-based background task processing

## Getting Help

- **[API Documentation](./API.md)** - API reference
- **[GitHub Issues](https://github.com/fabriziosalmi/proximity/issues)** - Report bugs or request features

## Known Limitations

- No admin panel UI (user management requires CLI or Django admin)
- No built-in monitoring dashboard (Proxmox metrics are polled per request)
- Scheduled automatic backups are not yet implemented (backups are on-demand)
- Some pages use mock data placeholders (noted in FEATURE_MAPPING_AUDIT.md)

