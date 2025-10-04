# Proximity E2E Test Suite

Comprehensive end-to-end test suite for the Proximity platform using **Playwright** and **Pytest**. This suite validates the entire user journey from authentication to application deployment and management.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Page Object Model](#page-object-model)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The E2E test suite covers:

- ✅ **Authentication**: Registration, login, logout, error handling
- ✅ **Application Lifecycle**: Full deploy → manage → verify → delete workflow
- ✅ **Settings Management**: Configuration persistence and validation
- ✅ **Infrastructure Monitoring**: Network appliance and Proxmox node status
- ✅ **Integration Validation**: Frontend ↔ Backend ↔ Proxmox ↔ Database

### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| **Smoke** | 5 | Quick sanity checks for critical paths |
| **Auth** | 4 | Authentication flows and session management |
| **Lifecycle** | 1 | Complete app deployment and deletion |
| **Settings** | 3 | Configuration management |
| **Infrastructure** | 2 | System monitoring and status |

---

## 🏗️ Architecture

### Test Framework Stack

```
┌─────────────────────────────────────────────────┐
│               Pytest Test Runner                │
├─────────────────────────────────────────────────┤
│           Playwright Browser Automation         │
├─────────────────────────────────────────────────┤
│         Page Object Model (POM) Layer           │
├─────────────────────────────────────────────────┤
│    Proximity UI (Frontend) → FastAPI (Backend)  │
│              ↓                     ↓             │
│      Browser Actions         SQLite + Proxmox   │
└─────────────────────────────────────────────────┘
```

### Directory Structure

```
e2e_tests/
├── conftest.py                 # Pytest fixtures and configuration
├── pytest.ini                  # Pytest settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── pages/                      # Page Object Model
│   ├── base_page.py            # Base page class with common methods
│   ├── login_page.py           # Authentication modal
│   ├── dashboard_page.py       # Dashboard and navigation
│   ├── app_store_page.py       # Application catalog
│   └── settings_page.py        # Settings management
│
├── utils/                      # Utilities and helpers
│   ├── test_data.py            # Random data generation
│   └── api_helpers.py          # Direct API calls (optional)
│
├── test_auth_flow.py           # Authentication test suite
├── test_app_lifecycle.py       # Application lifecycle tests
└── test_settings_infra.py      # Settings and infrastructure tests
```

---

## 🚀 Setup

### Prerequisites

1. **Python 3.11+**
2. **Proximity Backend Running** on http://127.0.0.1:8765 (or configure `PROXIMITY_E2E_URL`)
3. **Proxmox VE** configured and accessible
4. **Node.js** (for Playwright browser binaries)

### Installation

#### 1. Install Python Dependencies

```bash
cd e2e_tests
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Install Playwright Browsers

```bash
playwright install chromium
```

Or install all browsers:

```bash
playwright install
```

#### 3. Configure Environment (Optional)

Create a `.env` file in the `e2e_tests/` directory:

```ini
# Proximity instance URL
PROXIMITY_E2E_URL=http://127.0.0.1:8765

# Browser settings
HEADLESS=false
SLOW_MO=0
TIMEOUT=30000

# Admin credentials (for admin-only tests)
E2E_ADMIN_USERNAME=admin
E2E_ADMIN_PASSWORD=admin123
```

---

## 🧪 Running Tests

### Run All Tests

```bash
pytest
```

### Run with Headless Browser (CI Mode)

```bash
pytest --headed=false
# Or set environment variable:
HEADLESS=true pytest
```

### Run Specific Test File

```bash
pytest test_auth_flow.py
```

### Run Specific Test Function

```bash
pytest test_auth_flow.py::test_registration_and_login
```

### Run by Marker/Category

```bash
# Run only smoke tests
pytest -m smoke

# Run authentication tests
pytest -m auth

# Run slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Parallel Execution

```bash
# Run tests in parallel (4 workers)
pytest -n 4
```

### Retry Flaky Tests

```bash
# Retry failed tests up to 3 times
pytest --reruns 3
```

### Slow Motion for Debugging

```bash
# Slow down operations by 1 second
SLOW_MO=1000 pytest
```

### Generate HTML Report

```bash
pytest --html=report.html --self-contained-html
```

---

## 📁 Test Structure

### Test Files

#### `test_auth_flow.py`

Tests authentication and session management:

- `test_registration_and_login()` - New user registration and automatic login
- `test_logout()` - User logout and session cleanup
- `test_invalid_login()` - Failed login with incorrect credentials
- `test_session_persistence()` - Token persistence across page reloads

#### `test_app_lifecycle.py`

**THE MOST CRITICAL TEST** - Full application lifecycle:

- `test_full_app_deploy_manage_delete_workflow()` - Complete E2E workflow:
  1. Login as test user
  2. Navigate to App Store
  3. Deploy Nginx with unique hostname
  4. Monitor deployment progress (real-time logs)
  5. Verify app appears in "My Apps" with RUNNING status
  6. **Integration Check**: HTTP GET request to app URL (verify reverse proxy)
  7. Stop the app → verify STOPPED status
  8. Start the app → verify RUNNING status
  9. Delete the app → confirm deletion
  10. **Cleanup Verification**: HTTP request fails (app removed)

#### `test_settings_infra.py`

Settings and infrastructure validation:

- `test_settings_page_loads_data()` - Settings form populated with API data
- `test_update_setting()` - Modify and persist configuration
- `test_infrastructure_page_loads_data()` - Network appliance and nodes display

---

## 🎭 Page Object Model

The POM pattern abstracts UI components into reusable classes, making tests more maintainable.

### Example: Using LoginPage

```python
from pages.login_page import LoginPage
from utils.test_data import generate_test_user

def test_login_example(page):
    login_page = LoginPage(page)
    user = generate_test_user()
    
    # High-level API
    login_page.register(user["username"], user["password"])
    
    # Or low-level API
    login_page.switch_to_register_mode()
    login_page.fill_username(user["username"])
    login_page.fill_password(user["password"])
    login_page.click_register_button()
    login_page.wait_for_modal_close()
```

### Available Page Objects

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `BasePage` | Base class | `click()`, `fill()`, `wait_for_selector()`, `assert_visible()` |
| `LoginPage` | Authentication | `login()`, `register()`, `logout()` |
| `DashboardPage` | Dashboard | `navigate_to_app_store()`, `find_app_card_by_name()` |
| `AppStorePage` | App catalog | `deploy_app()`, `wait_for_deployment_complete()` |
| `SettingsPage` | Settings | `navigate_to_tab()`, `save_settings()` |

---

## ✍️ Writing Tests

### Basic Test Template

```python
import pytest
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import generate_test_user

@pytest.mark.smoke
def test_my_feature(page):
    """
    Test description goes here.
    
    Steps:
    1. Login
    2. Perform action
    3. Verify result
    """
    # Arrange
    user = generate_test_user()
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    # Act
    login_page.register(user["username"], user["password"])
    dashboard_page.wait_for_dashboard_load()
    
    # Assert
    dashboard_page.assert_on_dashboard()
```

### Using Authenticated Fixture

```python
def test_requires_auth(authenticated_page):
    """This test starts with user already logged in."""
    dashboard_page = DashboardPage(authenticated_page)
    dashboard_page.assert_on_dashboard()
```

### Best Practices

1. **Use Page Objects**: Never interact with selectors directly in tests
2. **Unique Test Data**: Use `generate_test_user()`, `generate_hostname()` for unique values
3. **Wait, Don't Sleep**: Use `wait_for_selector()` instead of `time.sleep()`
4. **Cleanup**: Always delete resources created during tests
5. **Descriptive Names**: Test names should describe what's being tested
6. **AAA Pattern**: Arrange → Act → Assert
7. **Single Responsibility**: One test should verify one behavior
8. **Screenshots**: Automatically captured on failure

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd e2e_tests
          pip install -r requirements.txt
          playwright install --with-deps chromium
      
      - name: Start Proximity backend
        run: |
          cd backend
          python main.py &
          sleep 10  # Wait for startup
      
      - name: Run E2E tests
        run: |
          cd e2e_tests
          HEADLESS=true pytest --html=report.html
      
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-report
          path: e2e_tests/report.html
      
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: failure-screenshots
          path: e2e_tests/screenshots/
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Timeout while waiting for selector"

**Cause**: Element not appearing or wrong selector

**Solutions**:
- Increase timeout: `TIMEOUT=60000 pytest`
- Verify selector in browser DevTools
- Check if element is in shadow DOM or iframe
- Ensure page has loaded: `page.wait_for_load_state("networkidle")`

#### 2. "Browser not installed"

**Cause**: Playwright browsers not installed

**Solution**:
```bash
playwright install chromium
```

#### 3. "Connection refused"

**Cause**: Proximity backend not running

**Solution**:
```bash
cd backend
python main.py &
```

#### 4. Tests Pass Locally but Fail in CI

**Causes**: 
- Timing issues (CI is slower)
- Headless vs headed mode differences
- Missing dependencies

**Solutions**:
- Increase timeouts for CI
- Use `wait_for_load_state("networkidle")`
- Install system dependencies: `playwright install --with-deps`

#### 5. Flaky Tests

**Causes**:
- Race conditions
- Hard-coded waits
- Network issues

**Solutions**:
- Replace `time.sleep()` with `wait_for_selector()`
- Add retry logic: `pytest --reruns 2`
- Check for animations completing
- Verify data cleanup between tests

### Debug Mode

```bash
# Run with visible browser and slow motion
HEADLESS=false SLOW_MO=1000 pytest test_auth_flow.py -v -s

# Run single test with debugging
pytest test_auth_flow.py::test_registration_and_login --pdb

# Capture screenshots manually
page.screenshot(path="debug_screenshot.png", full_page=True)
```

### Logs and Artifacts

- **Test logs**: Console output with timestamps
- **Screenshots**: Automatically captured on failure in `screenshots/`
- **Videos**: Enable with `video="on"` in browser context
- **Trace files**: Enable with `context.tracing.start()`

---

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Page Object Model Pattern](https://playwright.dev/python/docs/pom)
- [Proximity Documentation](../docs/)

---

## 🤝 Contributing

When adding new E2E tests:

1. Create page objects for new UI components
2. Use the POM pattern consistently
3. Add appropriate pytest markers
4. Include docstrings with test steps
5. Ensure tests clean up after themselves
6. Update this README with new test coverage

---

## 📊 Test Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **Total Tests** | 15+ | 10 |
| **Success Rate** | >95% | TBD |
| **Avg Duration** | <5 min | TBD |
| **Coverage** | Critical paths | 100% |

**Last Updated**: October 4, 2025
