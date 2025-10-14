# Development Guide

This guide covers contributing to Proximity, understanding the codebase, and implementing new features.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Adding Features](#adding-features)
- [Code Style](#code-style)
- [Testing](#testing)
- [Contributing](#contributing)

---

## Getting Started

### Development Environment Setup

1. **Fork and clone:**
   ```bash
   git clone https://github.com/yourfork/proximity.git
   cd proximity
   ```

2. **Create development environment:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up development configuration:**
   ```bash
   cp .env.example .env
   # Edit .env for your local Proxmox setup
   ```

4. **Initialize database:**
   ```bash
   python -c "from models.database import init_db; init_db()"
   ```

5. **Run in development mode:**
   ```bash
   python main.py
   # Server runs with auto-reload on file changes
   ```

### Development Tools

**Recommended IDE:** VS Code with Python extension

**Useful VS Code Extensions:**
- Python
- Pylance (type checking)
- SQLite Viewer
- REST Client
- Better Comments

**Browser Dev Tools:**
- Chrome/Firefox DevTools for frontend debugging
- Network tab for API request inspection
- Console for JavaScript debugging

---

## Project Structure

```
proximity/
├── backend/
│   ├── api/                    # API layer
│   │   ├── endpoints/          # Route handlers
│   │   │   ├── apps.py         # Application management
│   │   │   ├── auth.py         # Authentication
│   │   │   ├── settings.py     # Settings management
│   │   │   └── system.py       # System information
│   │   └── middleware/         # Middleware
│   │       └── auth.py         # Authentication middleware
│   ├── catalog/                # Application catalog
│   │   ├── nginx.json
│   │   ├── wordpress.json
│   │   └── ...
│   ├── core/                   # Core utilities
│   │   ├── config.py           # Configuration management
│   │   ├── encryption.py       # Encryption utilities
│   │   └── exceptions.py       # Custom exceptions
│   ├── models/                 # Data models
│   │   ├── database.py         # Database models
│   │   └── schemas.py          # Pydantic schemas
│   ├── services/               # Business logic
│   │   ├── app_service.py      # Application management
│   │   ├── auth_service.py     # Authentication
│   │   ├── command_service.py  # Safe command execution
│   │   ├── network_appliance_orchestrator.py  # Network management
│   │   ├── proxmox_service.py  # Proxmox API client
│   │   └── reverse_proxy_manager.py  # Caddy management
│   ├── main.py                 # Application entry point
│   ├── app.js                  # Frontend JavaScript
│   ├── index.html              # Frontend HTML
│   ├── styles.css              # Frontend styles
│   └── proximity.db            # SQLite database
├── docs/                       # Documentation
│   ├── architecture.md
│   ├── deployment.md
│   ├── development.md (this file)
│   └── troubleshooting.md
└── README.md                   # Main README
```

### Key Components

#### Backend Services

**ProxmoxService** (`services/proxmox_service.py`):
- Proxmox API client wrapper
- LXC container lifecycle management
- Template management and caching
- SSH-based command execution

**AppService** (`services/app_service.py`):
- Application catalog management
- Deployment orchestration
- Application state management
- Docker Compose integration

**NetworkApplianceOrchestrator** (`services/network_appliance_orchestrator.py`):
- Network bridge provisioning
- Appliance LXC management
- DNS/DHCP/NAT configuration
- Service health monitoring

**ReverseProxyManager** (`services/reverse_proxy_manager.py`):
- Caddy configuration management
- Vhost creation for deployed apps
- Dynamic proxy updates

**AuthService** (`services/auth_service.py`):
- JWT token generation/validation
- User authentication
- Password hashing
- Audit logging

#### Frontend

**App.js**:
- Single-page application logic
- API client with authentication
- Real-time UI updates
- Deployment wizard
- Application management UI

**Styles.css**:
- Modern dark theme
- Responsive grid layouts
- Component styling
- Animations and transitions

---

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/feature-name`: New features
- `fix/issue-description`: Bug fixes

### Workflow Steps

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make changes and test:**
   ```bash
   # Edit code
   python main.py  # Test locally
   pytest tests/   # Run tests
   ```

3. **Commit with meaningful messages:**
   ```bash
   git add .
   git commit -m "feat: Add support for PostgreSQL catalog items"
   ```

4. **Push and create pull request:**
   ```bash
   git push origin feature/my-new-feature
   # Create PR on GitHub
   ```

### Commit Message Convention

Follow conventional commits:

```
feat: Add new feature
fix: Bug fix
docs: Documentation changes
style: Code style changes (formatting)
refactor: Code refactoring
test: Test additions or changes
chore: Build process or auxiliary tool changes
```

**Examples:**
```
feat: Implement automatic SSL certificate generation
fix: Resolve race condition in container startup
docs: Add deployment troubleshooting guide
refactor: Extract network config into separate service
```

---

## Adding Features

### Adding a New Catalog Item

1. **Create catalog file:**
   ```bash
   touch backend/catalog/myapp.json
   ```

2. **Define application:**
   ```json
   {
     "id": "myapp",
     "name": "My Application",
     "description": "Description of my app",
     "category": "web",
     "icon": "package",
     "version": "1.0",
     "tags": ["web", "nodejs"],
     "resources": {
       "cpu": 2,
       "memory": 2048,
       "disk": 20
     },
     "compose": {
       "version": "3.8",
       "services": {
         "app": {
           "image": "myapp:latest",
           "ports": ["3000:3000"],
           "environment": {
             "NODE_ENV": "production"
           },
           "volumes": ["./data:/data"],
           "restart": "unless-stopped"
         }
       }
     }
   }
   ```

3. **Test deployment:**
   - Restart Proximity
   - Deploy via UI
   - Verify functionality

### Adding a New API Endpoint

1. **Define route in appropriate endpoint file:**
   ```python
   # backend/api/endpoints/apps.py

   @router.get("/{app_id}/metrics")
   async def get_app_metrics(
       app_id: str,
       current_user: TokenData = Depends(get_current_user),
       service: AppService = Depends(get_app_service)
   ):
       """Get application metrics"""
       metrics = await service.get_metrics(app_id)
       return metrics
   ```

2. **Implement service method:**
   ```python
   # backend/services/app_service.py

   async def get_metrics(self, app_id: str):
       """Get application metrics"""
       app = await self.get_app(app_id)
       # Fetch metrics from container
       result = await self.proxmox.execute_in_container(
           app.node,
           app.vmid,
           "docker stats --no-stream --format json"
       )
       return json.loads(result)
   ```

3. **Update frontend:**
   ```javascript
   // backend/app.js

   async function loadAppMetrics(appId) {
       const response = await authFetch(`${API_BASE}/apps/${appId}/metrics`);
       if (!response.ok) throw new Error('Failed to load metrics');
       return await response.json();
   }
   ```

### Adding a New Service

1. **Create service file:**
   ```python
   # backend/services/monitoring_service.py

   class MonitoringService:
       def __init__(self, proxmox: ProxmoxService):
           self.proxmox = proxmox

       async def get_system_metrics(self):
           """Get system-wide metrics"""
           # Implementation
           pass
   ```

2. **Add dependency injection:**
   ```python
   # backend/api/endpoints/system.py

   def get_monitoring_service(
       proxmox: ProxmoxService = Depends(lambda: proxmox_service)
   ) -> MonitoringService:
       return MonitoringService(proxmox)
   ```

3. **Create endpoints using service:**
   ```python
   @router.get("/metrics")
   async def get_metrics(
       monitoring: MonitoringService = Depends(get_monitoring_service)
   ):
       return await monitoring.get_system_metrics()
   ```

---

## Code Style

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these additions:

**Imports:**
```python
# Standard library
import os
import sys
from typing import Optional, List

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Local
from models.database import get_db
from services.proxmox_service import ProxmoxService
```

**Type Hints:**
```python
def create_app(
    catalog_id: str,
    hostname: str,
    config: dict = None
) -> App:
    """Create application with type hints"""
    pass
```

**Docstrings:**
```python
def deploy_app(self, app_data: AppCreate) -> App:
    """
    Deploy application to Proxmox.

    Args:
        app_data: Application deployment configuration

    Returns:
        Deployed application instance

    Raises:
        AppDeploymentError: If deployment fails
    """
    pass
```

**Error Handling:**
```python
try:
    result = await proxmox.create_lxc(node, vmid, config)
except ProxmoxError as e:
    logger.error(f"Failed to create container: {e}")
    raise AppDeploymentError(f"Container creation failed: {e}")
```

### JavaScript Style Guide

**Modern ES6+ Syntax:**
```javascript
// Use const/let, not var
const apiBase = 'http://localhost:8765/api/v1';
let currentView = 'dashboard';

// Arrow functions
const fetchApps = async () => {
    const response = await authFetch(`${apiBase}/apps`);
    return await response.json();
};

// Destructuring
const { name, status, node } = app;

// Template literals
const url = `${apiBase}/apps/${appId}/logs`;
```

**Async/Await:**
```javascript
async function deployApp(catalogId) {
    try {
        const response = await authFetch(`${API_BASE}/apps/deploy`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('Deployment failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Deploy error:', error);
        showNotification(error.message, 'error');
    }
}
```

---

## Testing

Proximity has a comprehensive test suite with **250+ tests** covering all critical functionality.

### Test Suite Overview

| Test File | Tests | Focus Area |
|-----------|-------|------------|
| `test_database_models.py` | 60+ | Database models, constraints, relationships |
| `test_database_transactions.py` | 25+ | ACID properties, transaction safety, rollback |
| `test_auth_service.py` | 15+ | Authentication, JWT, password management |
| `test_app_service.py` | 20+ | App deployment, lifecycle, catalog |
| `test_proxmox_service.py` | 15+ | Proxmox integration, LXC operations |
| `test_api_endpoints.py` | 25+ | API endpoints, CORS, authentication |
| `test_integration.py` | 30+ | End-to-end workflows, data consistency |
| `test_error_handling.py` | 40+ | Error scenarios, edge cases, boundaries |
| `test_catalog_service.py` | 20+ | Catalog loading, filtering, validation |

### Running Tests

```bash
# Run ALL tests (backend + E2E) in one command - RECOMMENDED
./run_all_tests.sh

# Or use Python version (cross-platform including Windows)
python run_all_tests.py

# With headed browser for E2E tests
./run_all_tests.sh --headed

# Backend tests only
pytest tests/ -v
# OR
./run_all_tests.sh --backend-only

# E2E tests only (requires backend running)
pytest e2e_tests/ --browser chromium -v
# OR
./run_all_tests.sh --e2e-only --headed

# With coverage report (backend tests)
pytest tests/ --cov=services --cov=models --cov=api --cov-report=html

# Specific test file
pytest tests/test_app_service.py -v

# Specific test function
pytest tests/test_app_service.py::test_deploy_app -v

# Integration tests only
pytest -m integration

# Skip integration tests (faster)
pytest -m "not integration"

# Failed tests only (after a run)
pytest --lf

# Show print statements
pytest -s

# Parallel execution (faster)
pytest -n auto
```

### Pre-commit Hooks - Automated Quality Gates 🔒

**Proximity uses the `pre-commit` framework to automatically enforce code quality and run tests before every commit.**

#### Quick Setup

After setting up your development environment:

```bash
# Install pre-commit (included in root requirements.txt)
pip install -r requirements.txt

# Install Git hooks (one-time per repository clone)
pre-commit install

# ✅ Hooks are now active!
```

#### What Happens on Every Commit?

**Phase 1: Code Quality Checks (ACTIVE NOW)** - ~2-5 seconds ⚡

These hooks run automatically and fix most issues:

| Hook | Purpose | Auto-fix |
|------|---------|----------|
| `check-yaml` | Validates YAML syntax | ❌ |
| `check-json` | Validates JSON syntax | ❌ |
| `end-of-file-fixer` | Ensures newline at end of files | ✅ |
| `trailing-whitespace` | Removes trailing spaces | ✅ |
| `check-added-large-files` | Blocks files >500KB | ❌ |
| `check-merge-conflict` | Detects `<<<<<<` markers | ❌ |
| `mixed-line-ending` | Enforces LF line endings | ✅ |
| `black` | Python code formatter | ✅ |
| `ruff` | Python linter (flake8/isort/etc.) | ✅ |

**Phase 2: Backend Test Guardian (READY TO ACTIVATE)** - ~10-30 seconds 🐍

Once activated, this hook runs `pytest tests/` before every commit:

```yaml
# To activate: Edit .pre-commit-config.yaml and uncomment this section
- id: pytest-backend
  name: 🔒 Backend Test Guardian
  entry: bash -c 'cd tests && pytest --tb=short -q'
```

**Phase 3: E2E Test Guardian (READY TO ACTIVATE)** - ~5-10 minutes 🎭

Once activated, this hook runs the full Playwright E2E suite:

```yaml
# To activate: Edit .pre-commit-config.yaml and uncomment this section
- id: pytest-e2e
  name: 🔒 E2E Test Guardian (SLOW)
  entry: bash -c 'cd e2e_tests && pytest --browser chromium --tb=short -q'
```

#### Running Hooks Manually

```bash
# Run all hooks on all files (do this after activation)
pre-commit run --all-files

# Run all hooks on staged files
pre-commit run

# Run specific hook
pre-commit run black --all-files
pre-commit run pytest-backend --all-files

# Update hook versions
pre-commit autoupdate
```

#### Bypassing Hooks (Emergency Only!)

For trivial commits (typos, doc fixes), you can skip hooks:

```bash
git commit -m "docs: Fix typo" --no-verify
```

**⚠️ Use sparingly!** CI/CD will still run all tests.

#### Gradual Activation Strategy

The `.pre-commit-config.yaml` file uses a **3-phase rollout**:

**✅ Phase 1 (Active Now)**: Code quality hooks
- Already running on every commit
- Fast (~2-5 seconds)
- Auto-fixes most issues

**🚧 Phase 2 (Activate When Ready)**: Backend test guardian
1. Ensure `pytest tests/` passes 100%: `pytest tests/ -v`
2. Edit `.pre-commit-config.yaml`
3. Uncomment the entire `pytest-backend` hook block
4. Test: `pre-commit run pytest-backend --all-files`
5. Commit: `git add .pre-commit-config.yaml && git commit -m "chore: Activate backend test guardian"`

**📋 Phase 3 (Activate When Ready)**: E2E test guardian
1. Ensure `pytest e2e_tests/` passes 100%
2. Ensure backend can be auto-started
3. Edit `.pre-commit-config.yaml`
4. Uncomment the `pytest-e2e` hook block
5. Test: `pre-commit run pytest-e2e --all-files`
6. Commit the activation

#### Best Practices

✅ **DO:**
- Let hooks run for all significant code changes
- Fix issues immediately when hooks fail
- Run `pre-commit run --all-files` after pulling changes
- Use `--no-verify` only for documentation fixes

❌ **DON'T:**
- Use `--no-verify` to bypass failing tests
- Commit broken code just because "CI will catch it"
- Disable hooks permanently

#### Performance Optimization

**For active development:**
```bash
# Commit frequently to feature branch WITHOUT E2E tests
git commit -m "feat: WIP - Add user profile page"

# Before pushing, run full suite manually
./run_all_tests.sh

# Let CI/CD validate everything
git push origin feature/user-profile
```

**For quick iterations:**
```bash
# Temporarily deactivate E2E hook (comment it out in .pre-commit-config.yaml)
# Work on your feature
# Before final push, reactivate and run full suite
```

#### Troubleshooting

**Hook fails with `ModuleNotFoundError`:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
pip install -r tests/requirements.txt
pip install -r e2e_tests/requirements.txt
```

**E2E tests fail - backend not running:**
```bash
# The E2E hook expects backend at http://localhost:8765
# Start backend in another terminal:
cd backend && python main.py

# Or use the unified test runner which auto-starts backend:
./run_all_tests.sh --e2e-only
```

**Hook takes too long:**
```bash
# Skip for this commit
git commit -m "message" --no-verify

# Or consider moving slow hooks to pre-push instead
# Edit .git/hooks/pre-push (advanced)
```

**Want to clean hook cache:**
```bash
pre-commit clean
```

**Want to uninstall all hooks:**
```bash
pre-commit uninstall
```

#### Hook Configuration Reference

All hooks are defined in `.pre-commit-config.yaml` at the repository root. Key configuration options:

```yaml
hooks:
  - id: hook-name
    name: Display name
    entry: Command to run
    language: python | system | script
    types: [python, javascript, css]  # File types to trigger on
    pass_filenames: false  # Pass filenames as arguments
    always_run: true       # Run even if no matching files changed
    verbose: true          # Show command output
    stages: [commit, push] # When to run (default: commit)
```

#### Integration with CI/CD

Pre-commit hooks are your **first line of defense**:

1. **Pre-commit hooks** → Catch issues locally before push
2. **CI/CD pipeline** → Validate everything on server
3. **Code review** → Human validation

Even if you use `--no-verify`, CI/CD will **always** run the full test suite.

#### Additional Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Supported Hooks](https://pre-commit.com/hooks.html)
- [Writing Custom Hooks](https://pre-commit.com/#creating-new-hooks)

**Remember: Pre-commit hooks save you time by catching issues early! 🚀**

### Test Categories

#### Unit Tests - Database Models
Tests for `User`, `App`, and `AuditLog` models:
- ✅ Field validation and constraints
- ✅ Unique constraints (username, email, hostname, lxc_id)
- ✅ Foreign key relationships
- ✅ Password hashing and verification
- ✅ Default values and nullable fields
- ✅ Cascade delete behavior

#### Unit Tests - Database Transactions
Tests for transaction safety and ACID properties:
- ✅ Transaction rollback on errors
- ✅ Commit verification
- ✅ Concurrent access patterns
- ✅ Deadlock prevention
- ✅ Session isolation

#### Unit Tests - Services
Tests for business logic in services:
- ✅ App deployment workflows
- ✅ Authentication and JWT handling
- ✅ Proxmox API interactions
- ✅ Network appliance orchestration
- ✅ Reverse proxy configuration

#### Integration Tests
End-to-end tests requiring database and (optionally) Proxmox:
- ✅ Complete deployment workflows
- ✅ User registration and app ownership
- ✅ Multi-container scenarios
- ✅ Network appliance integration
- ✅ Audit log generation

#### Error Handling Tests
Tests for edge cases and error conditions:
- ✅ Invalid input validation
- ✅ Database constraint violations
- ✅ Proxmox connection failures
- ✅ Resource exhaustion scenarios
- ✅ Concurrent operation conflicts

### Writing Tests

#### Unit Test Example

```python
# tests/test_app_service.py

import pytest
from services.app_service import AppService

@pytest.mark.asyncio
async def test_deploy_app(mock_proxmox, mock_db):
    """Test application deployment"""
    service = AppService(mock_db, mock_proxmox)

    result = await service.deploy_app(
        catalog_id="nginx",
        hostname="test-nginx",
        config={},
        environment={}
    )

    assert result.name == "nginx"
    assert result.hostname == "test-nginx"
    assert result.status == "running"
```

#### Database Model Test Example

```python
# tests/test_database_models.py

def test_user_creation(db_session):
    """Test creating a user with all fields"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$...",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.created_at is not None
```

#### Integration Test Example

```python
# tests/test_integration.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_deployment_workflow(app_service, admin_user):
    """Test complete deployment workflow from catalog to running app"""
    # Deploy app
    app = await app_service.deploy_app(
        catalog_id="nginx",
        hostname="integration-test-nginx",
        user_id=admin_user.id
    )
    
    assert app.lxc_id is not None
    assert app.status == "running"
    
    # Verify app is accessible
    apps = await app_service.get_all_apps()
    assert any(a.hostname == "integration-test-nginx" for a in apps)
    
    # Cleanup
    await app_service.delete_app(app.id)
```

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
@pytest.fixture
def db_session():
    """Provide a clean database session for each test"""
    # Creates temporary database
    yield session
    # Cleanup after test

@pytest.fixture
def admin_user(db_session):
    """Provide an admin user for tests"""
    user = User(username="admin", role="admin")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
async def app_service(db_session, mock_proxmox):
    """Provide configured AppService"""
    return AppService(db_session, mock_proxmox)
```

### Coverage Goals

- **Target:** 80%+ overall coverage
- **Critical paths:** 95%+ coverage (auth, deployment, data access)
- **Current status:** Check with `pytest --cov --cov-report=term-missing`

### CI/CD Integration

Tests run automatically on:
- Every push to `main` branch
- Every pull request
- Before deployments

**GitHub Actions workflow:**
```yaml
- name: Run tests
  run: |
    cd backend
    pytest --cov --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

---

## Contributing

### Pull Request Process

1. **Fork the repository**
2. **Create feature branch**
3. **Make changes with tests**
4. **Ensure all tests pass**
5. **Update documentation**
6. **Submit pull request**

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Added tests for new features
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts

### Code Review Guidelines

**For Reviewers:**
- Check code quality and style
- Verify tests are comprehensive
- Ensure documentation is updated
- Test functionality locally
- Provide constructive feedback

**For Contributors:**
- Address all review comments
- Update PR based on feedback
- Keep PR focused on single feature
- Respond to questions promptly

---

## Implementation Notes

### Smart Cleanup Integration

Proximity automatically cleans up failed deployments:

```python
# Successful deployment creates app record
app = App(...)
db.add(app)
db.commit()

# Failed deployment triggers cleanup
try:
    await deploy_steps()
except Exception as e:
    await cleanup_container(vmid)
    raise
```

### Template Caching

Templates are cached per-node for faster deployments:

```python
# Check cache first
cached = await check_template_cache(node)
if cached:
    use_cached_template()
else:
    download_and_cache_template()
```

### Network Management Refactoring

The network architecture evolved through several iterations. See `docs/architecture.md` for details.

**Key Learnings:**
- Isolated networks improve security
- Centralized DHCP/DNS simplifies management
- Fallback modes ensure reliability

---

## Debugging

### Enable Debug Logging

```python
# main.py
logging.basicConfig(level=logging.DEBUG)
```

### Common Debug Scenarios

**Container Won't Start:**
```bash
# Check Proxmox logs
pct config <vmid>
tail -f /var/log/pve/tasks/UPID*
```

**Docker Install Fails:**
```bash
# Test SSH connectivity
ssh root@proxmox-host 'pct exec <vmid> -- apk --version'
```

**API Errors:**
- Check browser console
- Inspect Network tab
- Verify authentication token
- Check CORS headers

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Proxmox VE API](https://pve.proxmox.com/pve-docs/api-viewer/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Docker Compose Spec](https://docs.docker.com/compose/compose-file/)
- [Alpine Linux Packages](https://pkgs.alpinelinux.org/)

---

## Getting Help

- **Issues**: https://github.com/yourusername/proximity/issues
- **Discussions**: https://github.com/yourusername/proximity/discussions
- **Documentation**: https://github.com/yourusername/proximity/docs
