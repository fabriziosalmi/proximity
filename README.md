# Proximity
Proximity is an open-source web UI and REST API for managing LXC containers on Proxmox VE hosts.

> [!WARNING]
> This project is in beta. Some features are incomplete. Contributions and bug reports are welcome.

> See [STATUS.md](STATUS.md) for detailed project status and progress.

## Key Features

*   **Application Catalog:** Deploy pre-configured LXC-based applications from a curated catalog.
*   **Container Adoption:** Discover and import existing LXC containers running on your Proxmox host.
*   **Backup & Restore:** Create and restore backups of deployed containers via the Proxmox API.
*   **Container Lifecycle:** Start, stop, restart, clone, and delete containers from the web UI.
*   **Multi-host Support:** Connect and manage multiple Proxmox VE hosts.
*   **Notification System:** Status and error notifications displayed in the Master Control Rack UI component.
*   **REST API:** Full API with JWT authentication and auto-generated Swagger docs.

## Quick Start

Get Proximity up and running in a few minutes.

### Prerequisites

*   Docker & Docker Compose
*   Git
*   A running Proxmox VE host (v7.0+)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/fabriziosalmi/proximity.git
    cd proximity
    ```

2.  **Configure your environment:**
    ```bash
    cp .env.example .env
    # Edit .env with your Proxmox host credentials and a new SECRET_KEY
    ```
    Update the `.env` file with:
    - Proxmox host IP/hostname and credentials
    - A new `SECRET_KEY` (generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
    - Database URL (defaults to SQLite; PostgreSQL is supported for production)

3.  **Launch the stack:**
    ```bash
    docker-compose up -d --build
    ```

4.  **Initialize the database:**
    ```bash
    docker-compose exec backend python manage.py migrate
    ```

    **Note**: The first user registered automatically becomes admin (staff + superuser) to ease initial setup. You can create additional regular users through the UI or API.

5.  **Access Proximity:**
    *   **Frontend:** `http://localhost:5173` (SvelteKit dev server)
    *   **Backend API:** `http://localhost:8000/api/` (Django backend)
    *   **API Docs:** `http://localhost:8000/api/docs` (Swagger UI)

For more detailed instructions, see the [Installation Guide](docs/INSTALLATION.md).

## Documentation

*   [**Project Status**](STATUS.md): Current progress, test results, known limitations
*   [**Installation Guide**](docs/INSTALLATION.md): Detailed setup and deployment instructions
*   [**Architecture**](docs/ARCHITECTURE.md): System design and technical architecture
*   [**API Reference**](docs/API.md): Backend API endpoints and usage
*   [**First Steps**](docs/FIRST_STEPS.md): Getting started after installation
*   [**Testing Guide**](docs/TESTING.md): How to run tests and verify functionality
*   [**Security Summary**](SECURITY_SUMMARY.md): Security audit and fixes applied

### Documentation Index

See [docs/INDEX.md](docs/INDEX.md) for a complete documentation map organized by category.

## Testing

Proximity has a backend test suite covering models, services, API endpoints, and security features.

### Running Tests Locally

#### Backend Tests

```bash
# Install test dependencies
cd backend
pip install -r requirements-test.txt

# Run all tests with pytest (REQUIRED - not python manage.py test)
env USE_MOCK_PROXMOX=1 pytest

# Run with verbose output
env USE_MOCK_PROXMOX=1 pytest -v

# Run specific test file
env USE_MOCK_PROXMOX=1 pytest tests/test_models.py

# Run with coverage report
env USE_MOCK_PROXMOX=1 pytest --cov=apps --cov=tests
```

**Important**: Always use `pytest` (not `python manage.py test`) for the full test suite. Django's test runner only discovers a subset of tests.

#### Frontend Tests

```bash
# Install dependencies
cd frontend
npm install

# Run Playwright E2E tests (requires running backend)
npm run test:e2e

# Build frontend
npm run build
```

### Test Status

- **Backend**: 102/102 tests passing
- **E2E Tests**: Require a running backend

For more details, see [TESTING.md](docs/TESTING.md).

## Development

### Local Development Setup

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-test.txt

# Run development server with mock Proxmox
env USE_MOCK_PROXMOX=1 python manage.py runserver

# Frontend development
cd frontend
npm install
npm run dev
```

### Project Structure

```
proximity/
├── backend/              # Django REST API
│   ├── apps/            # Feature apps (proxmox, applications, backups, catalog, etc.)
│   ├── tests/           # Unit tests
│   ├── proximity/       # Django settings
│   └── requirements.txt # Python dependencies
├── frontend/            # SvelteKit web application
│   ├── src/
│   │   ├── lib/        # Utilities and components
│   │   ├── routes/     # Page components
│   │   └── styles/     # Global styling
│   └── package.json    # JavaScript dependencies
├── docs/               # Documentation
├── docker-compose.yml  # Full stack orchestration
└── STATUS.md          # Project status and progress
```

## Notification System

All notifications are displayed in the Master Control Rack component at the top of the interface instead of floating toast boxes. Status is indicated by color-coded LED:
- Green = Success
- Red = Error
- Blue = Info
- Yellow = Warning or deployment in progress

```javascript
// These calls display on the Master Control Rack LCD
toasts.success('Application deployed successfully');
toasts.error('Failed to connect to Proxmox');
toasts.info('System maintenance scheduled');
toasts.warning('Low disk space detected');
```

## User Management

### Automatic Admin on First Registration
The first user registered in Proximity automatically becomes an admin (staff + superuser). This ensures the initial setup does not require manual command line operations.

### Managing Users with make_admin Command
Promote existing users to staff or superuser status using the `make_admin` management command:

```bash
# Promote a user to staff (can access admin panel)
python manage.py make_admin <username>

# Promote a user to staff + superuser (full admin access)
python manage.py make_admin <username> --superuser

# Docker usage
docker-compose exec backend python manage.py make_admin <username> --superuser
```

**Examples:**
```bash
# Promote user 'john' to staff
docker-compose exec backend python manage.py make_admin john

# Promote user 'jane' to superuser (full admin)
docker-compose exec backend python manage.py make_admin jane --superuser
```

## Contributing

Contributions are welcome. Before contributing, please:
1. Read our [Contributing Guide](CONTRIBUTING.md)
2. Check the [STATUS.md](STATUS.md) for current project state
3. Review the [Security Summary](SECURITY_SUMMARY.md) for security guidelines

## Security

This project has undergone a security audit with fixes for:
- Command injection prevention (SSH escaping)
- Authentication hardening (JWT + session-based)
- Encryption (Fernet for sensitive data)
- CORS hardening and authorization checks
- Input validation and rate limiting

See [SECURITY_SUMMARY.md](SECURITY_SUMMARY.md) for detailed security information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
