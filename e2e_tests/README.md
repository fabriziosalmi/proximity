# Proximity E2E Test Suite

Comprehensive end-to-end test suite for the Proximity platform using **Playwright** and **Pytest**. This suite validates the entire user journey from authentication to application deployment and management.

## � Quick Stats

- **Total Tests**: 57
- **Test Categories**: 6 (Auth, Lifecycle, Management, Settings, Infrastructure, Navigation)
- **Coverage**: ~95% of all user actions
- **Execution Time**: 30-40 minutes (full suite)
- **Smoke Tests**: 2 minutes
- **Critical Path**: 6-8 minutes

## 🎯 What's Tested

| Category | Tests | Key Coverage |
|----------|-------|--------------|
| **Authentication** | 7 | Register, Login, Logout, Session Management |
| **App Lifecycle** | 3 | Deploy, Monitor, Control, Delete (Complete E2E) |
| **App Management** | 13 | Logs, Console, Start/Stop/Restart, External Access |
| **Settings** | 11 | Proxmox, Network, Resources, System Configuration |
| **Infrastructure** | 10 | Nodes, Appliance, Services, NAT Testing |
| **Navigation** | 13 | Views, Sidebar, Menus, Keyboard Navigation |

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## 🎯 Overview

The E2E test suite covers:

- ✅ **Authentication**: Registration, login, logout, session management, error handling
- ✅ **Application Lifecycle**: Complete deploy → manage → monitor → delete workflow
- ✅ **Application Management**: Logs, console, controls (start/stop/restart)
- ✅ **Settings Management**: Proxmox, network, resources, system configuration
- ✅ **Infrastructure Monitoring**: Nodes, appliance status, services health
- ✅ **UI Navigation**: Sidebar, views, menus, keyboard shortcuts
- ✅ **Integration Validation**: Frontend ↔ Backend ↔ Proxmox ↔ Database

### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| **Smoke** | 5 | Quick sanity checks for critical paths |
| **Auth** | 7 | Authentication flows and session management |
| **Lifecycle** | 3 | Complete app deployment and deletion |
| **Management** | 13 | App controls, logs, console, monitoring |
| **Settings** | 11 | Configuration management and validation |
| **Infrastructure** | 10 | System monitoring, nodes, appliance |
| **Navigation** | 13 | UI navigation, sidebar, menus, keyboard |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd e2e_tests
pip install -r requirements.txt
playwright install chromium
```

### 2. Start Backend

```bash
# In another terminal
cd backend
python main.py
```

### 3. Run Tests

```bash
# Run smoke tests (fastest)
pytest -m smoke --browser chromium --headed -v

# Run critical path test
pytest -m critical test_app_lifecycle.py::test_complete_app_lifecycle_nginx --browser chromium --headed -v

# Run full suite
pytest --browser chromium --headed -v
```

---

## 📁 Test Structure

```
e2e_tests/
├── test_auth_flow.py           # Authentication tests (7 tests)
├── test_app_lifecycle.py       # App lifecycle tests (3 tests)
├── test_app_management.py      # App management tests (13 tests)
├── test_settings.py            # Settings tests (11 tests)
├── test_infrastructure.py      # Infrastructure tests (10 tests)
├── test_navigation.py          # Navigation tests (13 tests)
│
├── pages/                      # Page Object Model
│   ├── base_page.py            # Base page class
│   ├── login_page.py           # Authentication modal
│   ├── dashboard_page.py       # Dashboard and navigation
│   └── ...
│
├── utils/                      # Utilities and helpers
│   ├── test_data.py            # Random data generation
│   ├── helpers.py              # Fixtures, waits, cleanup
│   └── ...
│
├── conftest.py                 # Pytest configuration
├── pytest.ini                  # Pytest settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── E2E_COMPREHENSIVE_GUIDE.md  # Detailed documentation
```

---

## 🧪 Running Tests

### By Category

```bash
# Authentication tests
pytest -m auth test_auth_flow.py --browser chromium --headed -v

# Lifecycle tests (includes deployment)
pytest -m lifecycle test_app_lifecycle.py --browser chromium --headed -v

# Management tests
pytest -m management test_app_management.py --browser chromium --headed -v

# Settings tests
pytest -m settings test_settings.py --browser chromium --headed -v

# Infrastructure tests
pytest -m infrastructure test_infrastructure.py --browser chromium --headed -v

# Navigation tests
pytest -m navigation test_navigation.py --browser chromium --headed -v
```

### By Marker

```bash
# Smoke tests only (fast)
pytest -m smoke --browser chromium --headed -v

# Critical tests only
pytest -m critical --browser chromium --headed -v

# Exclude slow tests
pytest -m "not slow" --browser chromium --headed -v
```

### Single Test

```bash
# Run one specific test
pytest test_app_lifecycle.py::test_complete_app_lifecycle_nginx --browser chromium --headed -v

# With slow motion
pytest test_app_lifecycle.py::test_complete_app_lifecycle_nginx --browser chromium --headed --slowmo 500 -v
```

### Headless (CI/CD)

```bash
# Run in headless mode
pytest --browser chromium -v

# Parallel execution (if configured)
pytest -n auto --browser chromium -v
```

---

## 📚 Test Categories

### 1. Authentication Tests (test_auth_flow.py)

**Coverage**: Registration, Login, Logout, Session Management

```bash
pytest test_auth_flow.py --browser chromium --headed -v
```

**Key Tests**:
- `test_registration_and_login` - Complete registration flow
- `test_password_field_masking` - Password security ✅ PASSING
- `test_switch_between_login_and_register` - Tab navigation ✅ PASSING
- `test_invalid_login` - Error handling
- `test_session_persistence` - Token persistence
- `test_logout` - Clean logout

### 2. Application Lifecycle Tests (test_app_lifecycle.py)

**Coverage**: Complete E2E deployment workflow

```bash
pytest test_app_lifecycle.py --browser chromium --headed -v
```

**Key Tests**:
- `test_complete_app_lifecycle_nginx` ⭐ **CRITICAL** - Full workflow:
  1. Deploy NGINX from catalog
  2. Monitor deployment progress (5 min)
  3. Verify running status
  4. Stop application
  5. Start application
  6. Restart application
  7. View logs
  8. Delete application
  9. Verify cleanup

- `test_app_lifecycle_with_custom_config` - Custom deployments
- `test_deploy_multiple_apps_parallel` - Multi-app support

### 3. Application Management Tests (test_app_management.py)

**Coverage**: App controls, monitoring, logs, console

```bash
pytest test_app_management.py --browser chromium --headed -v
```

**Key Tests**:
- `test_view_app_logs_all` - All logs viewing
- `test_view_app_logs_docker` - Docker-specific logs
- `test_view_app_logs_system` - System logs
- `test_logs_auto_refresh` - Auto-refresh feature
- `test_download_logs` - Log download
- `test_open_app_console` - Console access
- `test_console_quick_commands` - Quick commands
- `test_app_external_link` - External access
- `test_app_stop_start_cycle` - Control operations
- `test_app_restart` - Restart operation

### 4. Settings Tests (test_settings.py)

**Coverage**: Configuration management

```bash
pytest test_settings.py --browser chromium --headed -v
```

**Key Tests**:
- `test_settings_page_loads` - Page initialization
- `test_settings_tab_navigation` - Tab switching
- `test_proxmox_settings_form` - Proxmox config
- `test_proxmox_test_connection` - Connection testing
- `test_network_settings_form` - Network config
- `test_resources_settings_form` - Resource limits
- `test_system_settings_panel` - System info

### 5. Infrastructure Tests (test_infrastructure.py)

**Coverage**: Monitoring, nodes, appliance, services

```bash
pytest test_infrastructure.py --browser chromium --headed -v
```

**Key Tests**:
- `test_infrastructure_page_loads` - Page initialization
- `test_proxmox_nodes_display` - Node information
- `test_network_appliance_status` - Appliance monitoring
- `test_view_appliance_logs` - Appliance logs
- `test_restart_appliance_button` - Restart capability
- `test_nat_testing_button` - NAT testing
- `test_services_health_grid` - Service monitoring

### 6. Navigation Tests (test_navigation.py)

**Coverage**: UI navigation, sidebar, menus

```bash
pytest test_navigation.py --browser chromium --headed -v
```

**Key Tests**:
- `test_navigate_all_views` ⭐ **SMOKE** - Complete navigation
- `test_sidebar_collapse_expand` - Sidebar toggle
- `test_user_menu_toggle` - User menu
- `test_active_nav_indicator` - Active states
- `test_navigation_keyboard_shortcuts` - Keyboard UX
- `test_page_titles_update` - Title changes

---

## 🛠️ Writing Tests

### Using Helper Fixtures

```python
import pytest
from utils.helpers import authenticated_page, deployed_nginx_app

def test_my_feature(authenticated_page):
    """User is already logged in."""
    page = authenticated_page
    # Your test code here

def test_with_deployed_app(deployed_nginx_app):
    """NGINX app is already deployed."""
    page, hostname = deployed_nginx_app
    # Test app operations
```

### Available Helpers

**Fixtures**:
- `authenticated_page` - Logged-in user on dashboard
- `authenticated_with_user` - Auth + user credentials
- `deployed_nginx_app` - Auto-deployed NGINX app
- `deployed_app_factory` - Deploy multiple apps

**Wait Helpers**:
- `wait_for_app_status(page, hostname, status)`
- `wait_for_deployment_complete(page)`
- `wait_for_modal_close(page)`
- `wait_for_notification(page, pattern)`

**Cleanup**:
- `delete_app_if_exists(page, hostname)`
- `cleanup_all_test_apps(page)`

**Assertions**:
- `assert_app_exists(page, hostname)`
- `assert_app_not_exists(page, hostname)`
- `assert_app_status(page, hostname, status)`

### Test Template

```python
import pytest
from playwright.sync_api import Page, expect
from utils.helpers import authenticated_page

@pytest.mark.your_category
def test_your_feature(authenticated_page):
    """
    Test description.
    
    Steps:
    1. Step one
    2. Step two
    
    Expected: Expected outcome
    """
    page = authenticated_page
    
    print("\n🔍 Testing feature")
    
    # Arrange
    # ... setup
    
    # Act
    # ... perform action
    
    # Assert
    expect(page.locator("#element")).to_be_visible()
    
    print("✓ Test passed")
```

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
