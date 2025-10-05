# Test Baseline Report - October 5, 2025

## Executive Summary

Complete test baseline captured for both unit/integration tests and E2E tests to establish current quality state before any fixes.

### Overall Statistics

- **Unit/Integration Tests**: 246 passed, 13 failed (95.0% pass rate)
- **E2E Tests**: 7 passed, 13 failed, 3 skipped, 51 errors (10.0% pass rate)
- **Total Test Coverage**: 259 tests

---

## Unit/Integration Test Results (tests/)

**Duration**: 302.61s (5 minutes 2 seconds)  
**Pass Rate**: 95.0% (246/259)

### ✅ Passing Test Suites (246 tests)

1. **API Endpoints** (9/9) - 100% pass
   - System info, app listing, deployment, settings, CORS headers

2. **App Service** (36/36) - 100% pass
   - Catalog management, deployment, lifecycle operations, updates

3. **Authentication Service** (22/22) - 100% pass
   - Token creation/verification, user authentication, password management, audit logging

4. **Backup System** (43/43) - 100% pass
   - Backup API (14/14), Backup Model (16/16), Backup Service (13/13)
   - Creation, listing, restoration, deletion, polling

5. **Catalog Service** (18/18) - 100% pass
   - Catalog loading, filtering, environment variables, versioning

6. **Database Models** (26/26) - 100% pass
   - User, App, DeploymentLog, AuditLog models
   - Constraints, relationships, cascade operations

7. **Database Transactions** (13/13) - 100% pass
   - Atomicity, isolation, consistency, durability
   - Rollback scenarios

8. **Monitoring Service** (9/9) - 100% pass
   - Stats caching, cache expiration, concurrent requests

9. **Port Manager** (9/9) - 100% pass
   - Port allocation, release, usage tracking, exhaustion handling

10. **Proxmox Service** (16/17) - 94% pass
    - Connection, LXC management, SSH operations, network configuration

11. **Reverse Proxy Manager** (7/7) - 100% pass
    - Caddy config generation, port-based routing, header management

12. **Error Handling** (27/29) - 93% pass
    - Authentication errors, app service errors, API endpoint errors, edge cases

13. **Integration Tests** (10/10) - 100% pass
    - Full deployment workflow, auth flow, catalog browsing, CORS, data consistency

### ❌ Failing Tests (13 failures)

#### 1. App Clone & Config Tests (10 failures)

**test_app_clone_config.py**:
- `test_clone_app_success` - Volume format mismatch (string vs dict)
- `test_clone_app_source_not_found` - Wrong exception type raised
- `test_clone_app_duplicate_hostname` - Wrong exception type raised
- `test_clone_app_copies_all_properties` - Ports format mismatch (int vs string keys)
- `test_update_cpu_cores` - stop_app not called
- `test_update_memory` - Missing 'config' key in call args
- `test_update_disk_size` - Disk size not updated (10 != 20)
- `test_update_multiple_resources` - CPU cores not updated (1 != 4)
- `test_update_app_not_found` - Wrong exception type raised
- `test_update_failure_attempts_restart` - start_app not called

**Root Causes**:
- Data format inconsistencies (volumes stored as strings vs dicts)
- Exception handling not matching test expectations
- Update operations not properly invoking lifecycle methods
- Config updates not persisting to database

#### 2. Authentication Error Tests (2 failures)

**test_error_handling.py**:
- `test_register_with_duplicate_username` - Returns 201 instead of 400
- `test_register_with_duplicate_email` - Returns 201 instead of 400

**Root Cause**: Duplicate username/email validation not enforced at API level

#### 3. Proxmox Service Test (1 failure)

**test_proxmox_service.py**:
- `test_get_nodes` - Mock object issue, expects 'testnode' string

**Root Cause**: Mock setup issue in test configuration

### ⚠️ Warnings (838 warnings)

1. **SQLAlchemy Deprecations** (635 warnings)
   - `declarative_base()` → `sqlalchemy.orm.declarative_base()`
   - `datetime.utcnow()` → `datetime.now(datetime.UTC)`

2. **SSL Warnings** (28 warnings)
   - Unverified HTTPS requests to Proxmox API (192.168.100.102)

3. **Runtime Warnings** (3 warnings)
   - Unawaited coroutines in backup service tests

---

## E2E Test Results (e2e_tests/)

**Duration**: 587.51s (9 minutes 47 seconds)  
**Pass Rate**: 10.0% (7/72)

### ✅ Passing E2E Tests (7 tests)

1. `test_registration_flow[chromium]` - User registration works
2. `test_registration_and_login[chromium]` - Auth flow completes
3. `test_login_with_invalid_credentials[chromium]` - Error handling works
4. `test_dashboard_loads_after_login[chromium]` - Dashboard accessible
5. `test_catalog_page_displays_apps[chromium]` - Catalog displays
6. `test_search_catalog_functionality[chromium]` - Search works
7. `test_filter_catalog_by_category[chromium]` - Filtering works

### ❌ Failing E2E Tests (13 failures)

#### 1. App Lifecycle Tests (4 failures)

**Pattern**: Strict mode violation - locator finds 2 "Nginx" elements
- `test_full_app_deploy_manage_delete_workflow[chromium]`
- `test_app_update_workflow_with_pre_update_backup[chromium]`
- `test_app_volumes_display[chromium]`
- `test_monitoring_tab_displays_data[chromium]`

**Root Cause**: Both deployed app card AND catalog card match "Nginx" selector

#### 2. Auth Flow Tests (1 failure)

**test_auth_flow.py**:
- `test_logout[chromium]` - Cannot navigate to invalid URL "/"

**Root Cause**: Base URL not properly configured in navigation

#### 3. Backup & Restore Tests (6 failures)

**Pattern**: No deployed apps found or timeout waiting for backup button
- `test_backup_creation_and_listing[chromium]` - No deployed app cards visible
- `test_backup_completion_polling[chromium]` - 30s timeout waiting for backup button
- `test_backup_restore_workflow[chromium]` - 30s timeout waiting for backup button
- `test_backup_deletion[chromium]` - 30s timeout waiting for backup button
- `test_backup_ui_feedback[chromium]` - 30s timeout waiting for backup button
- `test_backup_security_ownership[chromium]` - Target page closed

**Root Cause**: Tests depend on deployed apps, but no apps are deployed

#### 4. Dual Mode Tests (2 failures)

**test_dual_mode_experience.py**:
- `test_switching_to_pro_mode_reveals_features[chromium]` - Mode toggle hidden
- `test_mode_toggle_ui_behavior[chromium]` - Mode toggle hidden

**Root Cause**: Mode toggle element has visibility:hidden CSS property

### 🚫 E2E Test Errors (51 errors)

#### 1. Auth Modal Issues (51 errors)

**Pattern**: "Registration may have failed - no token found"
- All settings tests (10 errors)
- All infrastructure tests (11 errors)
- All navigation tests (11 errors)
- All app management tests (10 errors)
- Clone/config tests (2 errors)
- App canvas tests (7 errors)

**Root Cause**: Auth modal doesn't close after registration, no token stored

**Evidence from logs**:
```
WARNING  Modal didn't close automatically, checking auth state: 
Page.wait_for_selector: Timeout 5000ms exceeded.
Call log:
  - waiting for locator("#authModal") to be hidden
  -     15 × locator resolved to visible <div id="authModal" class="modal show">
```

---

## Critical Issues Blocking E2E Tests

### 🔴 Priority 1: Auth Modal Won't Close (Blocks 51 tests)

**Impact**: 70.8% of E2E tests cannot authenticate

**Symptoms**:
- Registration appears to succeed (API returns 201)
- Auth modal remains visible with class "modal show"
- No JWT token found in localStorage
- Tests fail at setup stage

**Affected Test Files**:
- `test_settings.py` - 10 tests
- `test_infrastructure.py` - 11 tests
- `test_navigation.py` - 11 tests
- `test_app_management.py` - 10 tests
- `test_clone_and_config.py` - 2 tests
- `test_app_canvas.py` - 7 tests

**Expected Behavior**:
1. User fills registration form
2. Clicks Register button
3. API returns 201 with JWT token
4. Frontend stores token in localStorage
5. Modal closes automatically
6. User lands on dashboard

**Actual Behavior**:
1. User fills registration form
2. Clicks Register button
3. API returns 201 with JWT token
4. Token NOT stored in localStorage
5. Modal stays visible
6. Tests timeout waiting for modal to close

### 🔴 Priority 2: Duplicate Selector Issue (Blocks 4 tests)

**Impact**: Cannot click specific app cards when catalog and deployed apps show same app

**Error**: `strict mode violation: locator(".app-card:has(.app-name:text-is('Nginx'))") resolved to 2 elements`

**Affected Tests**:
- `test_full_app_deploy_manage_delete_workflow`
- `test_app_update_workflow_with_pre_update_backup`
- `test_app_volumes_display`
- `test_monitoring_tab_displays_data`

**Fix Required**: More specific selectors that differentiate catalog cards from deployed cards

### 🟡 Priority 3: Mode Toggle Hidden (Blocks 2 tests)

**Impact**: Cannot test dual mode feature

**Issue**: `#modeToggleInput` has CSS `visibility: hidden`

**Affected Tests**:
- `test_switching_to_pro_mode_reveals_features`
- `test_mode_toggle_ui_behavior`

### 🟡 Priority 4: Missing App Dependencies (Blocks 6 tests)

**Impact**: Backup/restore tests need deployed apps

**Issue**: Tests assume apps are deployed, but none exist

**Affected Tests**: All backup/restore workflow tests

---

## Test Infrastructure Health

### ✅ Working Components

1. **Test Isolation**: Clean database between tests
2. **Browser Management**: Playwright properly initializes browsers
3. **Page Objects**: Well-structured page object model
4. **Fixtures**: Proper setup/teardown with conftest.py
5. **Backend Server**: Responds correctly to API calls
6. **Database**: SQLite schema correct, migrations applied

### ⚠️ Known Issues

1. **Deprecated APIs**: 838 deprecation warnings to address
2. **SSL Verification**: Proxmox connections bypass SSL verification
3. **Mock Setup**: One proxmox test has mock configuration issue
4. **Coroutine Warnings**: 3 unawaited coroutines in backup tests

---

## Test Coverage Analysis

### Well-Covered Areas (>90% pass rate)

- ✅ Authentication & Authorization (100%)
- ✅ Database Operations (100%)
- ✅ Backup System (100%)
- ✅ Catalog Management (100%)
- ✅ Monitoring & Stats (100%)
- ✅ Port Management (100%)
- ✅ Reverse Proxy Config (100%)

### Areas Needing Attention (<50% pass rate)

- ❌ App Cloning & Config Updates (0%)
- ❌ E2E Authentication Flow (0% - blocks 70% of E2E tests)
- ❌ Duplicate Entry Validation (0%)

---

## Recommendations

### Immediate Actions

1. **Fix Auth Modal Closure** (Critical)
   - Debug JavaScript event handling for registration success
   - Verify token storage logic
   - Test modal close mechanisms (both manual and automatic)

2. **Fix Duplicate Selectors** (High)
   - Add distinguishing classes/attributes to catalog vs deployed cards
   - Update E2E selectors to be more specific

3. **Fix Clone/Config Tests** (Medium)
   - Standardize data formats (volumes, ports)
   - Implement proper exception handling
   - Ensure config updates persist

4. **Fix Duplicate Validation** (Medium)
   - Add uniqueness validation at API layer
   - Return proper 400 errors for duplicates

### Long-term Improvements

1. **Address Deprecation Warnings**
   - Migrate to `sqlalchemy.orm.declarative_base()`
   - Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)`

2. **SSL Configuration**
   - Add proper SSL certificate verification for Proxmox
   - Configure test environment with valid certs

3. **Test Reliability**
   - Fix mock setup in proxmox tests
   - Resolve unawaited coroutines
   - Add retry logic for flaky network operations

4. **E2E Test Dependencies**
   - Create fixtures that deploy test apps
   - Ensure consistent test data state

---

## Test Execution Commands

### Run All Unit Tests
```bash
cd /Users/fab/GitHub/proximity
python3 -m pytest tests/ -v --tb=short
```

### Run All E2E Tests
```bash
cd /Users/fab/GitHub/proximity
python3 -m pytest e2e_tests/ -v --tb=short
```

### Run Specific Test File
```bash
python3 -m pytest tests/test_app_clone_config.py -v
python3 -m pytest e2e_tests/test_auth_flow.py -v
```

### Run Single Test
```bash
python3 -m pytest tests/test_app_clone_config.py::TestCloneApp::test_clone_app_success -v
```

---

## Files Generated

1. `test_run_results.txt` - Full unit/integration test output
2. `e2e_test_run_results.txt` - Full E2E test output
3. `TEST_BASELINE_REPORT.md` - This comprehensive report

---

## Next Steps

This baseline establishes the current state. The directive is **DO NOT FIX** at this stage. This data will be used to:

1. Prioritize bug fixes based on impact
2. Track regression during refactoring
3. Measure improvement over time
4. Identify architectural issues

**Status**: ✅ **BASELINE CAPTURE COMPLETE**
