# 🎯 EPIC 0: OPERAZIONE STABILITÀ TOTALE - Master Plan

**Status:** 🔴 IN PROGRESS  
**Priority:** 🔥 CRITICAL - BLOCCA TUTTO  
**Completion Target:** Before any new feature development  
**Current Date:** October 16, 2025

---

## 📋 Executive Summary

**Mission:** Achieve 150% confidence in the codebase before building new features.  
**Rationale:** You don't build skyscrapers on sand. Complete stability is non-negotiable.

**Success Criteria:**
- ✅ 100% backend test pass rate (259 tests)
- ✅ 100% E2E test pass rate (all critical flows)
- ✅ Zero RuntimeWarnings
- ✅ Zero TargetClosedErrors
- ✅ Real Proxmox integration tests passing
- ✅ Complete test coverage documentation

---

## 🗺️ The Four Pillars of Stability

### **PILLAR 1: Backend Test Perfection** 
### **PILLAR 2: E2E Test Reliability**
### **PILLAR 3: Critical Flow Coverage**
### **PILLAR 4: Real Integration Validation**

---

## 📊 Current Status Baseline

### Backend Tests (pytest tests/)
```
Total Tests:     259
Status:          ⚠️  NEEDS VERIFICATION
Known Issues:    - Clone/Config test failures
                 - RuntimeWarning: coroutine never awaited
                 - AsyncMock fixture issues
Priority:        🔥 P0 - CRITICAL
```

### E2E Tests (Playwright)
```
Total Tests:     ~120+ (needs verification)
Status:          ⚠️  PARTIALLY STABLE
Known Issues:    - TargetClosedError intermittent
                 - Auth fixture flakiness (partially fixed)
                 - Navigation timeout issues (FIXED)
Recent Wins:     ✅ Apps view navigation fixed
                 ✅ 5-layer auth fixture implemented
Priority:        🔥 P0 - CRITICAL
```

### Integration Tests
```
Status:          ❌ NON-EXISTENT
Impact:          Cannot validate ProxmoxService
Priority:        🟡 P1 - HIGH
```

---

## 🎯 PILLAR 1: Backend Test Perfection

### Task 1.1: Fix Clone/Config Test Suite ✅
**File:** `tests/test_app_clone_config.py`  
**Status:** 🔴 FAILING

#### Issues Identified:
1. **Async/Await Issues**
   - `RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited`
   - Mock returns not properly awaited
   - Fixture lifecycle problems

2. **Mock Configuration Problems**
   - `ProxmoxService` mocks incomplete
   - `network_manager` not properly mocked
   - Port allocation mocks failing

3. **Test Data Issues**
   - Source app fixture incomplete
   - Test user fixture missing fields
   - Database session rollback issues

#### Action Items:
- [ ] **1.1.1** Audit all AsyncMock usage in `test_app_clone_config.py`
  - Verify all async mocks are properly configured
  - Ensure return values are coroutines where needed
  - Fix mock call assertions

- [ ] **1.1.2** Fix ProxmoxService Mock Configuration
  ```python
  # Ensure all async methods return proper coroutines
  mock.clone_lxc = AsyncMock(return_value={"task_id": "...", "newid": 101})
  mock.network_manager = MagicMock()
  mock.network_manager.appliance_info.wan_ip = "192.168.1.100"
  ```

- [ ] **1.1.3** Strengthen Test Fixtures
  - Ensure `source_app` fixture has all required fields
  - Verify `test_user` fixture is complete
  - Add explicit session.commit() and session.refresh()

- [ ] **1.1.4** Run Individual Clone Tests
  ```bash
  cd tests
  pytest test_app_clone_config.py::TestCloneApp -v
  pytest test_app_clone_config.py::TestUpdateAppConfig -v
  ```

- [ ] **1.1.5** Fix Each Failing Test One by One
  - `test_clone_app_success`
  - `test_clone_app_source_not_found`
  - `test_clone_app_duplicate_hostname`
  - `test_clone_app_proxmox_failure_cleanup`
  - `test_clone_app_copies_all_properties`

**Success Criteria:**
```bash
pytest tests/test_app_clone_config.py -v
# Output: 100% PASS (0 failures, 0 warnings)
```

---

### Task 1.2: Eliminate All RuntimeWarnings ⚠️
**Priority:** 🔥 P0

#### Current Warnings:
```
RuntimeWarning: coroutine was never awaited
RuntimeWarning: Enable tracemalloc to get object allocation traceback
```

#### Strategy:
1. **Enable Strict Async Mode**
   ```python
   # pytest.ini
   asyncio_mode = strict
   ```

2. **Audit All Async Code**
   - Search for patterns: `async def` without `await`
   - Find mocks returning sync values instead of coroutines
   - Identify fixture teardown issues

3. **Fix Patterns**
   ```python
   # WRONG ❌
   mock.method = AsyncMock(return_value="value")
   result = mock.method()  # Missing await!
   
   # CORRECT ✅
   mock.method = AsyncMock(return_value="value")
   result = await mock.method()
   ```

**Action Items:**
- [ ] **1.2.1** Run pytest with `-W error::RuntimeWarning` to catch all warnings
- [ ] **1.2.2** Create grep search for all async functions
  ```bash
  grep -r "async def" tests/ | grep -v "__pycache__"
  ```
- [ ] **1.2.3** Review each file with async code for proper await usage
- [ ] **1.2.4** Fix all identified issues
- [ ] **1.2.5** Verify zero warnings remain

**Success Criteria:**
```bash
pytest tests/ -v -W error::RuntimeWarning
# Output: 259 passed, 0 warnings
```

---

### Task 1.3: Achieve 100% Backend Pass Rate 🎯
**Target:** 259/259 tests passing

#### Process:
1. **Baseline Assessment**
   ```bash
   cd tests
   pytest -v --tb=short > test_baseline_report.txt 2>&1
   ```

2. **Categorize Failures**
   - Parse output for FAILED/ERROR/WARNING
   - Group by test file and failure type
   - Prioritize by impact (blocking tests first)

3. **Fix in Order**
   - P0: Tests that block other tests
   - P1: Core functionality tests
   - P2: Edge cases and validation tests

4. **Continuous Validation**
   ```bash
   # After each fix
   pytest tests/ -v --tb=short
   ```

**Action Items:**
- [ ] **1.3.1** Generate current test status report
- [ ] **1.3.2** Create failure categorization spreadsheet
- [ ] **1.3.3** Fix P0 failures (Clone/Config)
- [ ] **1.3.4** Fix P1 failures (remaining core tests)
- [ ] **1.3.5** Fix P2 failures (edge cases)
- [ ] **1.3.6** Generate final PILLAR 1 completion report

**Success Criteria:**
```bash
pytest tests/ -v --tb=short
# Output: ========================= 259 passed in XXs =========================
```

---

## 🎯 PILLAR 2: E2E Test Reliability

### Task 2.1: Eliminate TargetClosedError 🐛
**Priority:** 🔥 P0 - CRITICAL

#### Root Causes:
1. **Page Lifecycle Issues**
   - Page closed prematurely by Playwright
   - Navigation occurring on closed page
   - Fixture cleanup racing with test execution

2. **Timeout Cascades**
   - One timeout causes downstream page closure
   - No graceful degradation
   - Missing error recovery

#### Strategy:
1. **Implement Robust Page Guards**
   ```python
   def safe_navigate(page, url):
       if page.is_closed():
           raise RuntimeError("Cannot navigate: page is closed")
       page.goto(url, wait_until="domcontentloaded")
   ```

2. **Add Page Health Checks**
   ```python
   @pytest.fixture
   def page(context):
       page = context.new_page()
       yield page
       if not page.is_closed():
           page.close()
   ```

3. **Improve Error Messages**
   - Catch TargetClosedError early
   - Provide context about what failed
   - Log page state before closure

**Action Items:**
- [ ] **2.1.1** Create page health check utility
  ```python
  # e2e_tests/utils/page_guard.py
  def ensure_page_alive(page):
      if page.is_closed():
          raise PageClosedError("Page was closed unexpectedly")
  ```

- [ ] **2.1.2** Wrap all page interactions with health checks
- [ ] **2.1.3** Add explicit page lifecycle logging
  ```python
  print(f"Page alive: {not page.is_closed()}")
  ```

- [ ] **2.1.4** Review fixture teardown order
  - Ensure page cleaned up after test completes
  - Add try/finally blocks for cleanup

- [ ] **2.1.5** Run full navigation suite
  ```bash
  pytest e2e_tests/test_navigation.py -v
  ```

**Success Criteria:**
```
pytest e2e_tests/ -v -k navigation
# Output: 0 TargetClosedError exceptions
```

---

### Task 2.2: Strengthen Auth Fixture 🔐
**Priority:** 🔥 P0

#### Current Status:
- ✅ 5-layer wait strategy implemented
- ⚠️ Still seeing intermittent failures
- ❌ Not all tests use the fixture correctly

#### Remaining Issues:
1. **Race Conditions in Token Storage**
   - localStorage.setItem() not synchronous
   - Token set but not yet persisted
   - Tests reading stale tokens

2. **Modal Close Timing**
   - Modal closes before JWT fully processed
   - Dashboard loads before auth complete
   - No validation of "truly logged in" state

#### Enhancement Plan:
```python
# conftest.py - Enhanced auth fixture

@pytest.fixture
def authenticated_page(page: Page, base_url: str):
    """
    BULLETPROOF authentication fixture.
    Guarantees user is logged in AND app is ready.
    """
    # ... existing 5-layer wait ...
    
    # LAYER 6: Verify API readiness
    page.wait_for_function("""
        () => {
            // Check if app is truly ready to make API calls
            return window.AppManager && 
                   window.AppManager.isInitialized &&
                   window.Auth.isAuthenticated();
        }
    """, timeout=5000)
    
    # LAYER 7: Health check API call
    response = page.evaluate("""
        async () => {
            const response = await fetch('/api/v1/apps/health');
            return response.ok;
        }
    """)
    assert response, "API health check failed"
    
    yield page
    
    # Teardown with guaranteed cleanup
    if not page.is_closed():
        page.evaluate("localStorage.clear(); sessionStorage.clear();")
```

**Action Items:**
- [ ] **2.2.1** Implement Layer 6: App initialization check
- [ ] **2.2.2** Implement Layer 7: API health verification
- [ ] **2.2.3** Add fixture debug mode with detailed logging
- [ ] **2.2.4** Run auth flow tests 10 times consecutively
  ```bash
  for i in {1..10}; do
    pytest e2e_tests/test_auth_flow.py -v || break
  done
  ```
- [ ] **2.2.5** Document fixture usage best practices

**Success Criteria:**
```
10 consecutive runs of auth tests with 0 failures
pytest e2e_tests/test_auth_flow.py -v (x10) = 100% pass rate
```

---

### Task 2.3: Fix Navigation Test Stability 🧭
**Status:** ✅ PARTIALLY COMPLETE

#### Recent Fixes:
- ✅ Apps view timeout fixed (two-phase rendering)
- ✅ Navigation speed improved 45%
- ✅ Basic navigation tests passing

#### Remaining Work:
1. **Verify All Views**
   - Dashboard ✅
   - Apps ✅
   - Catalog ⚠️ (needs verification)
   - Nodes ⚠️
   - Monitoring ⚠️
   - Settings ⚠️

2. **Test Edge Cases**
   - Rapid navigation (clicking multiple nav items quickly)
   - Back/forward browser buttons
   - Direct URL navigation
   - Navigation while operations in progress

**Action Items:**
- [ ] **2.3.1** Create comprehensive navigation matrix
  ```
  From → To    | Dashboard | Apps | Catalog | Nodes | Monitoring | Settings
  -------------|-----------|------|---------|-------|------------|----------
  Dashboard    |     -     |  ✅  |   ⚠️    |  ⚠️   |     ⚠️     |    ⚠️
  Apps         |     ⚠️    |  -   |   ⚠️    |  ⚠️   |     ⚠️     |    ⚠️
  ...
  ```

- [ ] **2.3.2** Test each navigation path
  ```bash
  pytest e2e_tests/test_navigation.py::test_navigate_all_views -v
  ```

- [ ] **2.3.3** Implement rapid navigation stress test
  ```python
  def test_rapid_navigation(authenticated_page):
      """Test clicking nav items rapidly doesn't break app"""
      views = ['dashboard', 'apps', 'catalog', 'nodes']
      for _ in range(5):  # 5 cycles
          for view in views:
              page.click(f'[data-view="{view}"]')
              page.wait_for_timeout(100)  # Minimal wait
  ```

- [ ] **2.3.4** Fix any failures found
- [ ] **2.3.5** Document navigation best practices

**Success Criteria:**
```
All navigation tests pass with 0 failures
Rapid navigation stress test passes
Navigation time < 1s per view switch
```

---

## 🎯 PILLAR 3: Critical Flow Coverage

### Task 3.1: Full App Lifecycle Test 🔄
**Priority:** 🔥 P0 - HIGHEST

#### Scope:
Complete end-to-end test covering:
1. Deploy app from catalog
2. Wait for "running" status
3. Open app in canvas
4. Stop app
5. Verify "stopped" status
6. Start app again
7. Verify "running" status
8. Restart app
9. Delete app
10. Verify app removed

#### Implementation:
```python
# e2e_tests/test_full_lifecycle.py

@pytest.mark.lifecycle
@pytest.mark.critical
@pytest.mark.timeout(600)
def test_full_app_deploy_manage_delete_workflow(authenticated_page: Page):
    """
    🎯 CRITICAL TEST: Full application lifecycle
    
    This test validates EVERY major app operation:
    - Deploy from catalog
    - Lifecycle management (start/stop/restart)
    - Canvas interaction
    - Deletion and cleanup
    """
    page = authenticated_page
    hostname = generate_hostname("lifecycle-test")
    
    # Phase 1: Deploy
    print("\n📦 PHASE 1: Deploy Application")
    dashboard = DashboardPage(page)
    app_store = AppStorePage(page)
    deployment = DeploymentModalPage(page)
    
    dashboard.navigate_to_app_store()
    app_store.click_app_card("Nginx")
    deployment.fill_hostname(hostname)
    deployment.submit_deployment()
    deployment.wait_for_deployment_success(timeout=180000)
    deployment.close_modal()
    
    # Phase 2: Verify Running
    print("\n✅ PHASE 2: Verify App Running")
    dashboard.navigate_to_my_apps()
    dashboard.wait_for_app_visible(hostname)
    status = dashboard.get_app_status(hostname)
    assert status == "running", f"Expected running, got {status}"
    
    # Phase 3: Stop App
    print("\n🛑 PHASE 3: Stop Application")
    dashboard.stop_app(hostname)
    page.wait_for_timeout(5000)
    status = dashboard.get_app_status(hostname)
    assert status == "stopped", f"Expected stopped, got {status}"
    
    # Phase 4: Start App
    print("\n▶️ PHASE 4: Start Application")
    dashboard.start_app(hostname)
    page.wait_for_timeout(5000)
    status = dashboard.get_app_status(hostname)
    assert status == "running", f"Expected running, got {status}"
    
    # Phase 5: Restart App
    print("\n🔄 PHASE 5: Restart Application")
    dashboard.restart_app(hostname)
    page.wait_for_timeout(8000)
    status = dashboard.get_app_status(hostname)
    assert status == "running", f"Expected running, got {status}"
    
    # Phase 6: Open in Canvas
    print("\n🎨 PHASE 6: Open in Canvas")
    canvas = AppCanvasPage(page)
    dashboard.open_app_canvas(hostname)
    canvas.wait_for_canvas_visible()
    canvas.wait_for_iframe_load()
    canvas.close_canvas()
    
    # Phase 7: Delete App
    print("\n🗑️ PHASE 7: Delete Application")
    dashboard.delete_app(hostname)
    page.wait_for_timeout(5000)
    
    # Verify app removed
    assert not dashboard.is_app_visible(hostname), \
        f"App {hostname} should be removed"
    
    print("\n" + "="*80)
    print("✅ LIFECYCLE TEST COMPLETE: ALL PHASES PASSED")
    print("="*80)
```

**Action Items:**
- [ ] **3.1.1** Create `test_full_lifecycle.py`
- [ ] **3.1.2** Implement helper methods in DashboardPage
  - `stop_app(hostname)`
  - `start_app(hostname)`
  - `restart_app(hostname)`
  - `get_app_status(hostname)`
  - `is_app_visible(hostname)`
- [ ] **3.1.3** Add robust waits for state transitions
- [ ] **3.1.4** Run test 5 times to verify reliability
- [ ] **3.1.5** Add to critical smoke test suite

**Success Criteria:**
```
pytest e2e_tests/test_full_lifecycle.py -v
# Output: 1 passed, 0 failures
# Time: < 10 minutes
# Reliability: 5/5 consecutive runs pass
```

---

### Task 3.2: Backup/Restore Flow Tests 💾
**Priority:** 🟡 P1

#### Scope:
1. **Create Backup**
   - Trigger manual backup
   - Wait for completion
   - Verify backup appears in list

2. **List Backups**
   - Fetch backup list via API
   - Verify backup metadata
   - Check backup file exists

3. **Restore from Backup**
   - Delete original app
   - Restore from backup
   - Verify app recreated
   - Verify data intact

#### Implementation Plan:
```python
# e2e_tests/test_backup_restore.py

@pytest.mark.backup
@pytest.mark.critical
def test_backup_and_restore_workflow(authenticated_page: Page):
    """Test complete backup/restore cycle"""
    
    # 1. Deploy test app
    hostname = deploy_test_app(authenticated_page, "nginx")
    
    # 2. Create backup
    dashboard = DashboardPage(authenticated_page)
    dashboard.navigate_to_my_apps()
    dashboard.create_backup(hostname)
    dashboard.wait_for_backup_complete(hostname, timeout=120000)
    
    # 3. Verify backup exists
    backups = dashboard.get_app_backups(hostname)
    assert len(backups) > 0, "No backups found"
    backup_id = backups[0]['id']
    
    # 4. Delete app
    dashboard.delete_app(hostname)
    assert not dashboard.is_app_visible(hostname)
    
    # 5. Restore from backup
    dashboard.navigate_to_backups()
    dashboard.restore_backup(backup_id)
    dashboard.wait_for_restore_complete(timeout=180000)
    
    # 6. Verify app restored
    dashboard.navigate_to_my_apps()
    assert dashboard.is_app_visible(hostname)
    assert dashboard.get_app_status(hostname) == "running"
```

**Action Items:**
- [ ] **3.2.1** Verify backup API endpoints work
- [ ] **3.2.2** Implement backup UI interactions in DashboardPage
- [ ] **3.2.3** Create test_backup_restore.py
- [ ] **3.2.4** Test manual backup creation
- [ ] **3.2.5** Test restore operation
- [ ] **3.2.6** Test restore with existing app (should fail gracefully)

**Success Criteria:**
```
pytest e2e_tests/test_backup_restore.py -v
# All backup/restore tests pass
# Backups created successfully
# Restore recreates app correctly
```

---

### Task 3.3: App Update Flow Tests 🔄
**Priority:** 🟡 P1

#### Scope:
1. **Check for Updates**
   - Query update endpoint
   - Display available updates
   - Show version information

2. **Execute Update**
   - Trigger update operation
   - Monitor progress
   - Handle failures gracefully

3. **Verify Update**
   - Check new version deployed
   - Verify app still running
   - Validate no data loss

4. **Rollback Scenario**
   - Simulate failed update
   - Trigger rollback
   - Verify previous version restored

#### Implementation:
```python
# e2e_tests/test_app_update.py

@pytest.mark.update
@pytest.mark.critical
def test_app_update_workflow(authenticated_page: Page):
    """Test application update process"""
    
    # Setup: Deploy app with "old" version
    hostname = deploy_app_version(authenticated_page, "nginx", version="1.0")
    
    # Check for updates
    dashboard = DashboardPage(authenticated_page)
    dashboard.navigate_to_my_apps()
    
    has_update = dashboard.check_for_updates(hostname)
    assert has_update, "Should detect available update"
    
    # Execute update
    dashboard.update_app(hostname)
    dashboard.wait_for_update_complete(hostname, timeout=120000)
    
    # Verify update
    new_version = dashboard.get_app_version(hostname)
    assert new_version == "2.0", f"Expected v2.0, got {new_version}"
    
    status = dashboard.get_app_status(hostname)
    assert status == "running", "App should be running after update"
```

**Action Items:**
- [ ] **3.3.1** Implement update check API endpoint
- [ ] **3.3.2** Create update UI in dashboard
- [ ] **3.3.3** Implement update operation in AppService
- [ ] **3.3.4** Create test_app_update.py
- [ ] **3.3.5** Test successful update path
- [ ] **3.3.6** Test failed update + rollback

**Success Criteria:**
```
Update feature implemented and tested
Rollback mechanism works
Zero data loss during updates
```

---

## 🎯 PILLAR 4: Real Integration Validation

### Task 4.1: Proxmox Integration Test Suite 🖥️
**Priority:** 🟡 P1 - HIGH

#### Why This Matters:
Currently, ALL ProxmoxService tests use mocks. We have ZERO validation that our code actually works against a real Proxmox VE instance.

#### Scope:
Create a mini test suite that:
1. Connects to real Proxmox instance
2. Creates a test LXC container
3. Starts/stops the container
4. Clones the container
5. Destroys test containers
6. Validates error handling

#### Requirements:
- Optional execution (pytest marker)
- Cleanup guaranteed even on failure
- Safe for production Proxmox (uses test VMID range)
- Clear documentation for setup

#### Implementation:
```python
# tests/integration/test_proxmox_real.py

import pytest
import os

# Only run if PROXMOX_HOST is set
pytestmark = pytest.mark.skipif(
    not os.getenv("PROXMOX_HOST"),
    reason="Real Proxmox integration tests require PROXMOX_HOST env var"
)

@pytest.fixture(scope="module")
def proxmox_config():
    """Real Proxmox connection config"""
    return {
        "host": os.getenv("PROXMOX_HOST"),
        "user": os.getenv("PROXMOX_USER", "root@pam"),
        "password": os.getenv("PROXMOX_PASSWORD"),
        "verify_ssl": False
    }

@pytest.fixture(scope="module")
def proxmox_service(proxmox_config):
    """Real ProxmoxService instance"""
    service = ProxmoxService()
    service.connect(**proxmox_config)
    yield service
    # Cleanup any test containers left behind
    service.cleanup_test_containers()

@pytest.mark.integration
@pytest.mark.real_proxmox
async def test_create_lxc_real(proxmox_service):
    """Test creating a real LXC container"""
    
    # Use test VMID range (9000-9999)
    vmid = 9001
    
    try:
        # Create container
        result = await proxmox_service.create_lxc(
            node="pve",
            vmid=vmid,
            hostname="test-lxc",
            template="local:vztmpl/alpine-3.18-default_20230607_amd64.tar.xz",
            storage="local-lvm",
            cores=1,
            memory=512,
            disk=8
        )
        
        assert result["status"] == "success"
        assert result["vmid"] == vmid
        
        # Verify container exists
        status = await proxmox_service.get_lxc_status("pve", vmid)
        assert status is not None
        
    finally:
        # Always cleanup
        await proxmox_service.destroy_lxc("pve", vmid)

@pytest.mark.integration
@pytest.mark.real_proxmox
async def test_clone_lxc_real(proxmox_service):
    """Test cloning a real LXC container"""
    
    source_vmid = 9001
    clone_vmid = 9002
    
    try:
        # Create source container
        await proxmox_service.create_lxc(
            node="pve",
            vmid=source_vmid,
            hostname="test-source",
            template="local:vztmpl/alpine-3.18-default_20230607_amd64.tar.xz"
        )
        
        # Clone it
        result = await proxmox_service.clone_lxc(
            node="pve",
            vmid=source_vmid,
            newid=clone_vmid,
            name="test-clone",
            full=True
        )
        
        assert result["newid"] == clone_vmid
        
        # Verify clone exists
        status = await proxmox_service.get_lxc_status("pve", clone_vmid)
        assert status is not None
        
    finally:
        # Cleanup both containers
        await proxmox_service.destroy_lxc("pve", source_vmid)
        await proxmox_service.destroy_lxc("pve", clone_vmid)
```

#### Setup Guide:
```bash
# .env.test (DO NOT COMMIT!)
PROXMOX_HOST=192.168.1.100
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your_password_here
PROXMOX_NODE=pve

# Run integration tests
cd tests
pytest integration/test_proxmox_real.py -v -m real_proxmox
```

**Action Items:**
- [ ] **4.1.1** Create tests/integration/ directory
- [ ] **4.1.2** Implement test_proxmox_real.py
- [ ] **4.1.3** Add pytest marker configuration
  ```python
  # pytest.ini
  markers =
      integration: Integration tests (may require external services)
      real_proxmox: Tests requiring real Proxmox VE instance
  ```
- [ ] **4.1.4** Write setup documentation
- [ ] **4.1.5** Test against dev Proxmox instance
- [ ] **4.1.6** Add to CI (optional execution)

**Success Criteria:**
```
Integration tests pass against real Proxmox
Cleanup always executes (even on failure)
Zero leftover test containers
Documentation complete
```

---

## 📈 Progress Tracking

### Daily Checklist Template
```
Date: YYYY-MM-DD
Engineer: [Your Name]

PILLAR 1 - Backend Tests:
- [ ] Task completed: _____________
- [ ] Current pass rate: ___/259
- [ ] Blockers identified: _____________

PILLAR 2 - E2E Tests:
- [ ] Task completed: _____________
- [ ] Tests passing: ___/___
- [ ] Issues found: _____________

PILLAR 3 - Critical Flows:
- [ ] Test implemented: _____________
- [ ] Status: PASS/FAIL
- [ ] Notes: _____________

PILLAR 4 - Integration:
- [ ] Progress: _____________
- [ ] Blockers: _____________

Blockers for Tomorrow:
1. _____________
2. _____________
```

### Weekly Status Report Template
```
Week of: YYYY-MM-DD

PILLAR 1: Backend Tests
✅ Completed: _____________
🟡 In Progress: _____________
🔴 Blocked: _____________
Progress: XX% complete

PILLAR 2: E2E Tests
✅ Completed: _____________
🟡 In Progress: _____________
🔴 Blocked: _____________
Progress: XX% complete

PILLAR 3: Critical Flows
✅ Completed: _____________
🟡 In Progress: _____________
Progress: XX% complete

PILLAR 4: Integration
✅ Completed: _____________
🟡 In Progress: _____________
Progress: XX% complete

Overall EPIC 0 Progress: XX%
Estimated Completion: YYYY-MM-DD
```

---

## 🎬 Execution Sequence

### Phase 1: Quick Wins (Days 1-2)
1. Fix Clone/Config tests (Task 1.1)
2. Eliminate RuntimeWarnings (Task 1.2)
3. Strengthen Auth fixture (Task 2.2)

**Goal:** Get backend tests to 100% and E2E auth stable

### Phase 2: Core Stability (Days 3-4)
1. Eliminate TargetClosedError (Task 2.1)
2. Verify navigation stability (Task 2.3)
3. Achieve 100% backend pass rate (Task 1.3)

**Goal:** All existing tests rock solid

### Phase 3: Critical Coverage (Days 5-7)
1. Implement full lifecycle test (Task 3.1)
2. Implement backup/restore tests (Task 3.2)
3. Implement update tests (Task 3.3)

**Goal:** All critical user flows covered

### Phase 4: Real Validation (Days 8-10)
1. Create Proxmox integration suite (Task 4.1)
2. Run full test suite 10 consecutive times
3. Generate completion report

**Goal:** Complete confidence in codebase

---

## 🏁 Definition of Done

EPIC 0 is complete when:

- ✅ **Backend Tests:** 259/259 passing, 0 warnings
- ✅ **E2E Tests:** 100% pass rate on critical flows
- ✅ **No Flakiness:** 10 consecutive full test runs with 0 failures
- ✅ **Real Integration:** Proxmox integration tests passing
- ✅ **Documentation:** Complete test coverage report generated
- ✅ **CI/CD:** All tests run automatically on push
- ✅ **Team Confidence:** Everyone agrees codebase is rock solid

---

## 📚 Deliverables

1. **Test Reports:**
   - `BACKEND_TEST_COMPLETION_REPORT.md`
   - `E2E_TEST_STABILIZATION_REPORT_V2.md`
   - `INTEGRATION_TEST_REPORT.md`

2. **Code Artifacts:**
   - Fixed test files (all passing)
   - New critical flow tests
   - Integration test suite
   - Updated CI/CD configuration

3. **Documentation:**
   - Test execution guide
   - Fixture usage patterns
   - Best practices guide
   - Troubleshooting runbook

4. **Metrics Dashboard:**
   - Test pass rate over time
   - Flakiness tracking
   - Coverage by module
   - Execution time trends

---

## 🎯 Next Steps After EPIC 0

Once stability is achieved, proceed to:

### EPIC 1: The "Genesis Release" (v1.0 Completion)
- Clone App feature (PRO mode)
- Config Edit feature (PRO mode)
- Auto Backups (AUTO mode)
- Auto Update Check (AUTO mode)
- Container Adoption Wizard

### EPIC 2: "Operation Gioiellino" (Polish & UX)
- Power-on experience
- Sound system
- Theme engine
- Rack navigation
- Card flip animations

**But not before EPIC 0 is 100% complete!**

---

## 💪 Team Commitment

**We pledge:**
- No new features until stability achieved
- Every commit includes test coverage
- All PRs require test pass before merge
- Weekly progress reviews
- Daily blockers triage

**Success Mantra:**
> "Stability first, features second. A solid foundation enables infinite innovation."

---

**Document Version:** 1.0  
**Last Updated:** October 16, 2025  
**Next Review:** End of Phase 1 (Day 2)

---

**Let's build something rock solid! 🚀**
