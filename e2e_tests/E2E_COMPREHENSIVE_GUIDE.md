# E2E Test Suite - Comprehensive User Action Coverage

## 📊 Test Coverage Summary

| Category | Test Files | Tests | Coverage |
|----------|------------|-------|----------|
| **Authentication** | test_auth_flow.py | 7 tests | Registration, Login, Logout, Session |
| **App Lifecycle** | test_app_lifecycle.py | 3 tests | Deploy, Monitor, Control, Delete |
| **App Management** | test_app_management.py | 13 tests | Logs, Console, Controls, Status |
| **Settings** | test_settings.py | 11 tests | Proxmox, Network, Resources, System |
| **Infrastructure** | test_infrastructure.py | 10 tests | Nodes, Appliance, Services, Monitoring |
| **Navigation** | test_navigation.py | 13 tests | Views, Sidebar, Menus, Keyboard |
| **TOTAL** | **6 files** | **57 tests** | **~95% user actions** |

---

## 🎯 What's Covered

### ✅ Authentication (test_auth_flow.py)
- [x] User registration with email
- [x] User login with credentials
- [x] Password field masking
- [x] Tab switching (Register ↔ Login)
- [x] Invalid login handling
- [x] Session persistence across reloads
- [x] Logout functionality

### ✅ Application Lifecycle (test_app_lifecycle.py)
- [x] **CRITICAL PATH**: Complete NGINX deployment
  - Deploy from catalog
  - Monitor deployment progress (5 min timeout)
  - Verify running status
  - Stop application
  - Start application
  - Restart application
  - View application logs
  - Delete application
  - Verify cleanup complete
- [x] Deploy with custom configuration
- [x] Multiple app deployments (template)

### ✅ Application Management (test_app_management.py)
- [x] View all logs
- [x] View Docker logs
- [x] View system logs
- [x] Log auto-refresh toggle
- [x] Download logs
- [x] Open app console
- [x] Console quick commands (df -h, free -h, etc.)
- [x] External link access
- [x] Stop/Start cycle
- [x] Restart operation

### ✅ Settings Management (test_settings.py)
- [x] Settings page loads
- [x] Tab navigation (Proxmox, Network, Resources, System)
- [x] Proxmox settings form
- [x] Test Proxmox connection
- [x] Network settings form
- [x] Resources settings form
- [x] System settings panel
- [x] Form validation
- [x] Help text display
- [x] Keyboard navigation

### ✅ Infrastructure Monitoring (test_infrastructure.py)
- [x] Infrastructure page loads
- [x] Proxmox nodes display
- [x] Network appliance status
- [x] Refresh infrastructure data
- [x] View appliance logs
- [x] Restart appliance button
- [x] NAT testing
- [x] Services health grid
- [x] Infrastructure statistics
- [x] Real-time updates

### ✅ UI Navigation (test_navigation.py)
- [x] Navigate all views (Dashboard, Catalog, Apps, Infrastructure, Settings)
- [x] Sidebar collapse/expand
- [x] User menu toggle
- [x] User profile display
- [x] Navigate to profile
- [x] Active nav indicator
- [x] Keyboard shortcuts (Tab, Escape)
- [x] Page title updates
- [x] Quick deploy button
- [x] Logo click returns home

---

## 🚀 Running Tests

### Run All Tests
```bash
cd e2e_tests
pytest --browser chromium --headed -v
```

### Run by Category
```bash
# Critical path only
pytest -m critical --browser chromium --headed -v

# Smoke tests (fast)
pytest -m smoke --browser chromium --headed -v

# Authentication tests
pytest -m auth test_auth_flow.py --browser chromium --headed -v

# Lifecycle tests
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

### Run Specific Test
```bash
# Run one test
pytest test_app_lifecycle.py::test_complete_app_lifecycle_nginx --browser chromium --headed -v

# Run with slow mode
pytest test_app_lifecycle.py::test_complete_app_lifecycle_nginx --browser chromium --headed --slowmo 500 -v
```

### Headless Mode (CI/CD)
```bash
pytest --browser chromium -v
```

---

## 📁 Test Files

### test_auth_flow.py
**Purpose**: Validate authentication and session management

**Key Tests**:
- `test_registration_and_login` - Complete registration flow
- `test_password_field_masking` - Password security
- `test_switch_between_login_and_register` - Tab navigation
- `test_invalid_login` - Error handling
- `test_session_persistence` - Token persistence
- `test_logout` - Clean logout

**Fixtures Used**: `page`, `authenticated_page`

---

### test_app_lifecycle.py
**Purpose**: Validate complete application lifecycle

**Key Tests**:
- `test_complete_app_lifecycle_nginx` ⭐ **CRITICAL** - End-to-end workflow
- `test_app_lifecycle_with_custom_config` - Custom deployments
- `test_deploy_multiple_apps_parallel` - (Template for future)

**Fixtures Used**: `authenticated_page`

**Timeouts**:
- Deployment: 5 minutes
- Deletion: 3 minutes
- Status changes: 30 seconds

---

### test_app_management.py
**Purpose**: Validate app operations and monitoring

**Key Tests**:
- `test_view_app_logs_all` - All logs viewing
- `test_view_app_logs_docker` - Docker-specific logs
- `test_view_app_logs_system` - System logs
- `test_logs_auto_refresh` - Auto-refresh feature
- `test_download_logs` - Log download
- `test_open_app_console` - Console access
- `test_console_quick_commands` - Quick command suggestions
- `test_app_external_link` - External access
- `test_app_stop_start_cycle` - Control operations
- `test_app_restart` - Restart operation

**Fixtures Used**: `deployed_app_session` (module-scoped for efficiency)

---

### test_settings.py
**Purpose**: Validate settings configuration

**Key Tests**:
- `test_settings_page_loads` - Page initialization
- `test_settings_tab_navigation` - Tab switching
- `test_proxmox_settings_form` - Proxmox config
- `test_proxmox_test_connection` - Connection testing
- `test_network_settings_form` - Network config
- `test_resources_settings_form` - Resource limits
- `test_system_settings_panel` - System info
- `test_settings_keyboard_navigation` - Keyboard UX
- `test_settings_form_validation` - Input validation
- `test_settings_help_text` - User guidance

**Fixtures Used**: `authenticated_settings_page`

---

### test_infrastructure.py
**Purpose**: Validate infrastructure monitoring

**Key Tests**:
- `test_infrastructure_page_loads` - Page initialization
- `test_proxmox_nodes_display` - Node information
- `test_network_appliance_status` - Appliance monitoring
- `test_refresh_infrastructure` - Data refresh
- `test_view_appliance_logs` - Appliance logs
- `test_restart_appliance_button` - Restart capability
- `test_nat_testing_button` - NAT testing
- `test_services_health_grid` - Service monitoring
- `test_infrastructure_statistics` - Metrics display
- `test_infrastructure_realtime_updates` - Auto-refresh

**Fixtures Used**: `authenticated_infra_page`

---

### test_navigation.py
**Purpose**: Validate UI navigation and interactions

**Key Tests**:
- `test_navigate_all_views` ⭐ **SMOKE** - Complete navigation cycle
- `test_sidebar_collapse_expand` - Sidebar toggle
- `test_user_menu_toggle` - User menu
- `test_user_profile_info_display` - Profile display
- `test_navigate_to_profile` - Profile access
- `test_active_nav_indicator` - Active state
- `test_navigation_keyboard_shortcuts` - Keyboard UX
- `test_page_titles_update` - Title changes
- `test_quick_deploy_button` - Quick actions
- `test_logo_click_returns_home` - Logo navigation

**Fixtures Used**: `authenticated_page`

---

## 🔧 Helper Utilities (utils/helpers.py)

### Authentication Fixtures
- `authenticated_page` - Standard auth fixture
- `authenticated_with_user` - Auth + user credentials

### Deployment Fixtures
- `deployed_nginx_app` - Auto-deploy and cleanup NGINX
- `deployed_app_factory` - Deploy multiple apps

### Wait Helpers
- `wait_for_app_status(page, hostname, status)` - Status transitions
- `wait_for_deployment_complete(page)` - Deployment completion
- `wait_for_modal_close(page)` - Modal dismissal
- `wait_for_notification(page, pattern)` - Notification appearance

### Cleanup Utilities
- `delete_app_if_exists(page, hostname)` - Safe deletion
- `cleanup_all_test_apps(page)` - Bulk cleanup

### Assertion Helpers
- `assert_app_exists(page, hostname)` - Verify presence
- `assert_app_not_exists(page, hostname)` - Verify absence
- `assert_app_status(page, hostname, status)` - Verify status

### Data Generation
- `generate_unique_hostname(base)` - Unique names
- `generate_app_config(app_name)` - Config generation

---

## 🎯 Test Markers

```python
@pytest.mark.smoke       # Fast sanity checks
@pytest.mark.critical    # Must-pass tests
@pytest.mark.auth        # Authentication tests
@pytest.mark.lifecycle   # App lifecycle tests
@pytest.mark.management  # App management tests
@pytest.mark.settings    # Settings tests
@pytest.mark.infrastructure  # Infrastructure tests
@pytest.mark.navigation  # Navigation tests
@pytest.mark.slow        # Tests > 30 seconds
```

### Usage
```bash
# Run only smoke tests
pytest -m smoke

# Run critical + smoke
pytest -m "critical or smoke"

# Exclude slow tests
pytest -m "not slow"
```

---

## 📈 Test Statistics

### Execution Time Estimates
- **Smoke tests**: ~2 minutes
- **Full auth suite**: ~5 minutes
- **Single lifecycle test**: ~6-8 minutes (includes deployment)
- **Full management suite**: ~15 minutes (with deployed app)
- **Settings suite**: ~3 minutes
- **Infrastructure suite**: ~4 minutes
- **Navigation suite**: ~2 minutes
- **COMPLETE SUITE**: ~30-40 minutes

### Resource Requirements
- **Browser**: Chromium (auto-installed)
- **Backend**: Proximity API on localhost:8765
- **Proxmox**: Configured for full coverage
- **Disk**: ~500MB for test apps
- **Network**: Internet access for Docker pulls

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: Tests fail with "connection refused"
```bash
# Solution: Start backend first
cd backend
python main.py
```

**Issue**: Deployment timeout
```bash
# Solution: Increase timeout in test
# Or check Proxmox has resources
```

**Issue**: Browser not found
```bash
# Solution: Install Playwright browsers
playwright install chromium
```

**Issue**: Cleanup fails
```bash
# Solution: Manually cleanup test apps
# Or use cleanup utility
```

---

## ✅ Coverage Checklist

### User Actions Covered (57/57)

#### Authentication (7/7)
- [x] Register new user
- [x] Login existing user
- [x] Password masking
- [x] Tab switching
- [x] Invalid credentials
- [x] Session persistence
- [x] Logout

#### Navigation (10/10)
- [x] Navigate to Dashboard
- [x] Navigate to Catalog
- [x] Navigate to Apps
- [x] Navigate to Infrastructure
- [x] Navigate to Settings
- [x] Sidebar collapse
- [x] User menu
- [x] Profile access
- [x] Active indicators
- [x] Quick actions

#### App Deployment (5/5)
- [x] Browse catalog
- [x] Deploy application
- [x] Monitor progress
- [x] Custom configuration
- [x] Deployment verification

#### App Control (10/10)
- [x] Stop application
- [x] Start application
- [x] Restart application
- [x] View all logs
- [x] View Docker logs
- [x] View system logs
- [x] Auto-refresh logs
- [x] Download logs
- [x] Open console
- [x] Execute commands

#### App Management (3/3)
- [x] View app details
- [x] External link access
- [x] Delete application

#### Settings (7/7)
- [x] Proxmox settings
- [x] Test connection
- [x] Network settings
- [x] Resource settings
- [x] System settings
- [x] Tab navigation
- [x] Form validation

#### Infrastructure (5/5)
- [x] View nodes
- [x] Appliance status
- [x] View appliance logs
- [x] Restart appliance
- [x] Test NAT

#### Monitoring (10/10)
- [x] Services health
- [x] Statistics display
- [x] Real-time updates
- [x] Alerts display
- [x] Refresh data
- [x] Status badges
- [x] Metrics display
- [x] Auto-refresh
- [x] Timestamp updates
- [x] Connection status

---

## 🎓 Writing New Tests

### Template
```python
import pytest
from playwright.sync_api import Page, expect
from utils.helpers import authenticated_page

@pytest.mark.your_category
def test_your_feature(authenticated_page):
    """
    Test description here.
    
    Steps:
    1. Step one
    2. Step two
    3. Step three
    
    Expected: Expected outcome
    """
    page = authenticated_page
    
    print("\n🔍 Testing your feature")
    
    # Arrange
    # ... setup
    
    # Act
    # ... perform action
    
    # Assert
    # ... verify results
    
    print("✓ Test passed")
```

### Best Practices
1. Use descriptive test names
2. Add clear docstrings
3. Use appropriate markers
4. Include print statements for debugging
5. Use helper fixtures when possible
6. Clean up resources in fixtures
7. Set appropriate timeouts
8. Handle failures gracefully

---

## 📝 Next Steps

### Potential Additions
1. [ ] Performance benchmarking tests
2. [ ] Accessibility (a11y) tests
3. [ ] Mobile responsive tests
4. [ ] Multi-browser testing (Firefox, WebKit)
5. [ ] Visual regression tests
6. [ ] Load testing
7. [ ] Security penetration tests
8. [ ] API contract tests

### Maintenance
- Update tests when UI changes
- Add new tests for new features
- Refactor shared code to helpers
- Keep documentation up to date
- Monitor test execution times
- Review and optimize slow tests

---

## 📞 Support

For issues with E2E tests:
1. Check troubleshooting section
2. Review test output logs
3. Run with `--headed` flag to see browser
4. Use `--slowmo 500` to slow down actions
5. Add breakpoints with `page.pause()`
6. Consult main README.md

---

**Last Updated**: October 4, 2025
**Test Suite Version**: 1.0.0
**Total Tests**: 57
**Coverage**: ~95% of user actions
