# Proximity Development Guide

Complete guide for developers who want to contribute to Proximity.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Code Style & Conventions](#code-style--conventions)
- [Contribution Workflow](#contribution-workflow)
- [Adding New Features](#adding-new-features)
- [Troubleshooting Development Issues](#troubleshooting-development-issues)

---

## Development Setup

### Prerequisites

- **Python 3.9+** with pip
- **Node.js 16+** (for frontend tooling, optional)
- **Git**
- **Access to a Proxmox VE instance** (for integration testing)
- **Playwright** (for E2E tests)

### Step 1: Fork & Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/proximity.git
cd proximity
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
cd backend
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black flake8 mypy
```

### Step 3: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit with your Proxmox test instance
nano .env
```

**Development Configuration:**

```bash
# Proxmox (use test/dev instance)
PROXMOX_HOST=192.168.1.100
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your-password
PROXMOX_VERIFY_SSL=false

# Enable debug mode
DEBUG=true

# JWT secret (generate new for dev)
JWT_SECRET_KEY=dev-secret-key-not-for-production

# Database (separate from production)
DATABASE_URL=sqlite:///./proximity_dev.db
```

### Step 4: Install E2E Test Dependencies

```bash
cd ../e2e_tests

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Optional: Install all browsers
playwright install
```

### Step 5: Run Development Server

```bash
cd ../backend
python main.py
```

Server starts on `http://localhost:8765`

---

## Project Structure

```
proximity/
├── backend/                  # Python backend
│   ├── main.py              # Application entry point
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Configuration (not in git)
│   │
│   ├── api/                 # REST API layer
│   │   ├── endpoints/       # API route handlers
│   │   └── middleware/      # Auth middleware
│   │
│   ├── services/            # Business logic layer
│   │   ├── app_service.py   # App lifecycle
│   │   ├── proxmox_service.py  # Proxmox API
│   │   └── ...
│   │
│   ├── models/              # Data layer
│   │   ├── database.py      # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas
│   │
│   ├── core/                # Core utilities
│   │   ├── config.py        # Settings
│   │   ├── security.py      # Crypto/auth
│   │   └── exceptions.py    # Custom exceptions
│   │
│   ├── frontend/            # Frontend assets
│   │   ├── index.html       # Main HTML
│   │   ├── css/             # Stylesheets
│   │   └── js/              # JavaScript modules
│   │       ├── main.js      # Entry point
│   │       ├── core/        # Router, Component
│   │       ├── views/       # Page views
│   │       ├── components/  # UI components
│   │       ├── modals/      # Modal dialogs
│   │       ├── services/    # Business logic
│   │       └── utils/       # Utilities
│   │
│   ├── catalog/             # App catalog definitions
│   │   └── apps.json        # Available applications
│   │
│   └── tests/               # Backend unit tests
│       ├── conftest.py      # pytest fixtures
│       └── test_*.py        # Test modules
│
├── e2e_tests/               # End-to-end tests
│   ├── conftest.py          # Playwright fixtures
│   ├── test_*.py            # E2E test cases
│   └── fixtures/            # Shared fixtures
│
├── docs/                    # Documentation
│   ├── 1_INTRODUCTION.md
│   ├── 2_DEPLOYMENT.md
│   ├── 3_USAGE_GUIDE.md
│   ├── 4_ARCHITECTURE.md
│   └── 5_DEVELOPMENT.md  (this file)
│
├── README.md                # Project README
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # MIT License
└── .gitignore              # Git ignore rules
```

---

## Running Tests

### Backend Unit Tests (pytest)

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_app_service.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest tests/ -m "not slow"

# Run in parallel (requires pytest-xdist)
pytest tests/ -n auto
```

**Test Structure:**

```python
# tests/test_app_service.py
import pytest
from services.app_service import AppService

@pytest.fixture
def app_service(db_session):
    """Fixture providing AppService instance"""
    return AppService(proxmox_service, db_session)

async def test_deploy_app(app_service):
    """Test app deployment"""
    result = await app_service.deploy_app(...)
    assert result.status == "running"
```

### E2E Tests (Playwright + pytest)

```bash
cd e2e_tests

# Run all E2E tests (headless)
pytest -v

# Run with visible browser (for debugging)
pytest -v --headed

# Run specific test
pytest test_app_lifecycle.py -v

# Run in slow motion (see what's happening)
SLOW_MO=1000 pytest -v --headed

# Generate HTML report
pytest -v --html=report.html --self-contained-html
```

**E2E Test Structure:**

```python
# e2e_tests/test_app_lifecycle.py
def test_deploy_app(page, authenticated_user):
    """Test complete app deployment flow"""
    
    # Navigate to catalog
    page.click('[data-view="catalog"]')
    
    # Deploy nginx
    page.click('text=nginx >> ../.. >> button:has-text("Deploy")')
    
    # Wait for modal
    page.wait_for_selector('.deploy-modal')
    
    # Submit deployment
    page.click('button:has-text("Deploy Application")')
    
    # Wait for completion
    page.wait_for_selector('.deployment-success', timeout=120000)
    
    # Verify app appears in My Apps
    page.click('[data-view="apps"]')
    assert page.is_visible('text=nginx')
```

### Test Coverage Goals

- **Backend**: Aim for >80% coverage
- **E2E**: Cover all critical user journeys
- **Integration**: Test key service interactions

---

## Code Style & Conventions

### Python (Backend)

**Follow PEP 8** with these specifics:

```python
# Imports: standard, third-party, local
import os
import sys

from fastapi import FastAPI
from sqlalchemy.orm import Session

from services.app_service import AppService
from models.schemas import App

# Line length: 100 characters max
# Indentation: 4 spaces
# Quotes: Double quotes for strings

# Type hints
def deploy_app(app_id: str, config: Dict[str, Any]) -> App:
    """Deploy application with given configuration."""
    pass

# Docstrings: Google style
def complex_function(param1: str, param2: int) -> bool:
    """
    Brief one-line description.

    Longer description explaining the function's purpose,
    behavior, and any important notes.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

**Tools:**

```bash
# Format code with Black
black backend/

# Lint with flake8
flake8 backend/ --max-line-length=100

# Type check with mypy
mypy backend/
```

### JavaScript (Frontend)

**Modern ES6+ with modules:**

```javascript
// Use const/let, never var
const apiUrl = '/api/v1';
let currentUser = null;

// Arrow functions for callbacks
apps.map(app => app.name);

// Template literals
const message = `Hello ${username}!`;

// Destructuring
const { name, version } = app;

// Async/await
async function fetchApps() {
    const response = await fetch('/api/v1/apps');
    const data = await response.json();
    return data.apps;
}

// JSDoc comments
/**
 * Deploy an application from the catalog.
 * @param {string} catalogId - Application catalog ID
 * @param {object} config - Deployment configuration
 * @returns {Promise<object>} Deployed app object
 */
async function deployApp(catalogId, config) {
    // ...
}

// Module exports
export { deployApp, deleteApp };
```

**Naming Conventions:**

- **Components**: PascalCase (`MyComponent.js`)
- **Functions**: camelCase (`fetchUserData()`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **Files**: kebab-case (`app-card.js`)

### Commit Messages

Follow **Conventional Commits**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
feat(app-service): add app cloning functionality

Implemented app cloning feature for PRO mode users.
Includes volume copying and configuration inheritance.

Closes #123

fix(auth): resolve JWT expiration handling

Fixed issue where expired tokens caused infinite loops.
Now properly redirects to login on token expiration.

Fixes #456

docs(readme): update deployment instructions

Added systemd service setup guide.
```

---

## Contribution Workflow

### 1. Create Feature Branch

```bash
# Sync with upstream
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-awesome-feature

# Or for bug fixes
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write code following style guidelines
- Add tests for new functionality
- Update documentation if needed
- Commit frequently with clear messages

```bash
git add .
git commit -m "feat(catalog): add search functionality"
```

### 3. Test Your Changes

```bash
# Run backend tests
cd backend
pytest tests/ -v

# Run E2E tests
cd ../e2e_tests
pytest -v

# Ensure no linting errors
flake8 backend/
```

### 4. Push to Your Fork

```bash
git push origin feature/my-awesome-feature
```

### 5. Open Pull Request

1. Go to https://github.com/fabriziosalmi/proximity
2. Click **"New Pull Request"**
3. Select your fork and branch
4. Fill out PR template:
   - **Description**: What does this PR do?
   - **Motivation**: Why is this change needed?
   - **Testing**: How was it tested?
   - **Screenshots**: For UI changes
5. Submit PR

### 6. Code Review

- Respond to feedback promptly
- Make requested changes
- Push updates to same branch (auto-updates PR)
- Be patient and respectful

### 7. Merge

Once approved, maintainers will merge your PR. Congratulations! 🎉

---

## Adding New Features

### Adding a New Catalog App

1. **Create App Definition** (`backend/catalog/apps.json`):

```json
{
  "id": "myapp",
  "name": "My App",
  "description": "Description of my app",
  "version": "1.0.0",
  "category": "web",
  "icon": "https://example.com/icon.png",
  "docker_compose": {
    "version": "3",
    "services": {
      "myapp": {
        "image": "myapp:latest",
        "ports": ["8080:8080"],
        "environment": {
          "APP_KEY": "${APP_KEY}"
        }
      }
    }
  },
  "config_schema": {
    "APP_KEY": {
      "type": "string",
      "description": "Application API key",
      "default": "changeme"
    }
  },
  "ports": [8080],
  "min_memory": 1024,
  "min_cpu": 1
}
```

2. **Test Deployment**:

```bash
# Restart backend
python backend/main.py

# Deploy via UI
# Verify app works
```

### Adding a New API Endpoint

1. **Define Schema** (`backend/models/schemas.py`):

```python
class MyRequest(BaseModel):
    field1: str
    field2: int

class MyResponse(BaseModel):
    result: str
    data: Dict[str, Any]
```

2. **Create Endpoint** (`backend/api/endpoints/mymodule.py`):

```python
from fastapi import APIRouter, Depends
from models.schemas import MyRequest, MyResponse

router = APIRouter()

@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    """My endpoint description."""
    # Implementation
    return MyResponse(result="success", data={})
```

3. **Register Router** (`backend/main.py`):

```python
from api.endpoints import mymodule

app.include_router(
    mymodule.router,
    prefix="/api/v1/mymodule",
    tags=["mymodule"]
)
```

4. **Add Tests** (`backend/tests/test_mymodule.py`):

```python
async def test_my_endpoint(client):
    response = await client.post("/api/v1/mymodule/my-endpoint", json={
        "field1": "value",
        "field2": 42
    })
    assert response.status_code == 200
    assert response.json()["result"] == "success"
```

### Adding a New Frontend View

1. **Create View** (`backend/frontend/js/views/MyView.js`):

```javascript
import { Component } from '../core/Component.js';

export class MyView extends Component {
    constructor() {
        super();
    }

    mount(container, state) {
        console.log('Mounting MyView');
        
        container.innerHTML = this.generateHTML(state);
        
        // Attach listeners
        container.querySelector('.my-button').onclick = () => {
            this.handleClick();
        };
        
        return super.mount(container, state);
    }

    generateHTML(state) {
        return `
            <div class="my-view">
                <h1>My View</h1>
                <button class="my-button">Click Me</button>
            </div>
        `;
    }

    handleClick() {
        console.log('Button clicked!');
    }
}

export const myView = new MyView();
```

2. **Register View** (`backend/frontend/js/main.js`):

```javascript
import { myView } from './views/MyView.js';

router.registerViews({
    'dashboard': dashboardView,
    'apps': appsView,
    'catalog': catalogView,
    'settings': settingsView,
    'nodes': nodesView,
    'myview': myView  // Add new view
});
```

3. **Add Navigation** (`backend/frontend/index.html`):

```html
<li class="nav-item">
    <a href="#" data-view="myview" class="nav-link">
        <i data-lucide="star"></i>
        <span>My View</span>
    </a>
</li>
```

---

## Troubleshooting Development Issues

### "Module not found" errors

```bash
# Ensure you're in venv
source venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Database locked errors

```bash
# Stop all Proximity instances
pkill -f "python.*main.py"

# Remove lock file
rm backend/proximity.db-journal

# Restart
python backend/main.py
```

### E2E tests timing out

```bash
# Increase timeout
TIMEOUT=60000 pytest e2e_tests/ -v

# Run with browser visible
pytest e2e_tests/ --headed
```

### Frontend changes not appearing

```bash
# Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
# Or disable cache in DevTools

# Check browser console for errors
# Verify correct files are being served
```

### Port conflicts

```bash
# Check what's using port 8765
lsof -ti:8765

# Kill process
kill $(lsof -ti:8765)

# Or change port in .env
API_PORT=8766
```

---

## Development Best Practices

### 1. **Write Tests First** (TDD)

Before implementing a feature, write the test:

```python
def test_feature_x():
    # Arrange
    setup_data()
    
    # Act
    result = feature_x()
    
    # Assert
    assert result == expected_value
```

Then implement until tests pass.

### 2. **Keep PRs Small**

- Focus on one feature/fix per PR
- Easier to review
- Faster to merge

### 3. **Document As You Go**

- Update docs when adding features
- Add code comments for complex logic
- Write clear commit messages

### 4. **Test Locally First**

Before pushing:
- Run all tests
- Test in browser
- Check for console errors
- Verify no regressions

### 5. **Ask for Help**

- Open a Discussion for design questions
- Draft PRs for early feedback
- Reach out in Issues

---

## Resources

### Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **Playwright**: https://playwright.dev/python/
- **Proxmox API**: https://pve.proxmox.com/pve-docs/api-viewer/
- **pytest**: https://docs.pytest.org/

### Tools
- **Black** (formatter): https://black.readthedocs.io/
- **flake8** (linter): https://flake8.pycqa.org/
- **mypy** (type checker): http://mypy-lang.org/

### Community
- **GitHub Discussions**: Ask questions
- **GitHub Issues**: Report bugs
- **Pull Requests**: Submit contributions

---

## Thank You!

Thank you for contributing to Proximity! Every contribution—whether code, documentation, testing, or feedback—makes this project better for everyone.

**Happy coding!** 🚀

---

<div align="center">

[← Back: Architecture](4_ARCHITECTURE.md) • [Home: README](../README.md)

</div>
