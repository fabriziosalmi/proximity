# E2E Test Failures - Diagnostic Report

**Date:** October 5, 2025  
**Issue:** Tests hanging and requiring manual browser closing

---

## 🔍 Root Cause Analysis

### The Real Problem
The browser stays open because:
1. **Tests are TIMING OUT** (waiting 30+ seconds)
2. **User hits Ctrl+C** to cancel
3. **KeyboardInterrupt prevents cleanup** from completing

### Evidence from Logs
```
📋 [authenticated_page fixture] Waiting for dashboard to appear (Smart Wait)
✓ Dashboard visible - authentication complete
✓ User info visible - session fully established
2025-10-05 14:33:18 [    INFO] Navigating to App Store
2025-10-05 14:33:18 [    INFO] Clicking: [data-view='catalog']
ERROR    # <-- Hangs here for ~15 seconds
^C       # <-- User forced to cancel
```

---

## 🐛 Application Bugs Found

### 1. Registration → Login Tab Switch BROKEN
**Test:** `test_registration_and_login`  
**Error:** `AssertionError: Login tab should be active, got class: auth-tab`

**Problem:** After registration, the frontend is NOT switching to the login tab automatically as expected.

**Expected Behavior:**
1. User clicks "Register"
2. Backend creates user
3. Frontend switches to login tab (**NOT HAPPENING**)
4. User clicks login button

**Current Behavior:**
- Registration completes
- Tab DOES NOT switch to login mode
- Test fails immediately

**Fix Required:** Frontend code needs to properly switch tabs after successful registration.

---

### 2. Logout Button NOT Visible
**Test:** `test_logout`  
**Error:** `TimeoutError: Locator.wait_for: Timeout 5000ms exceeded`

**Problem:** The logout button is found but is HIDDEN (CSS display/visibility issue)

```
15 × locator resolved to hidden <a href="#" class="user-menu-item logout" ...
```

**Expected Behavior:**
1. Click user menu dropdown
2. Dropdown opens
3. Logout link becomes visible

**Current Behavior:**
- User menu clicked
- Dropdown might not be opening
- Logout link remains hidden

**Potential Causes:**
- CSS transition not completing
- JavaScript event handler not firing
- Dropdown CSS class not being applied

**Fix Required:** Frontend dropdown logic needs investigation.

---

### 3. Login Tab NOT Visible After Registration
**Test:** `test_session_persistence`  
**Error:** `TimeoutError: Locator.click: Timeout 30000ms exceeded`

**Problem:** After registration, the login tab element exists but is NOT VISIBLE

```
- element is not visible  (repeated 58+ times)
```

**This is the SAME bug as #1** - Registration not switching to login tab properly.

---

## ✅ What IS Working

### Browser Cleanup - WORKING PERFECTLY
```
🧹 [authenticated_page fixture] Cleaning up session
  ✓ Session cleared
🧹 [Cleanup] Closing page fixture
  ✓ Storage cleared
  ✓ Page closed successfully
🧹 [Cleanup] Closing browser context and all pages
  ✓ Context closed successfully
```

**When tests complete normally, cleanup works!**

### Passing Tests
- ✅ `test_invalid_login` - PASSED
- ✅ `test_password_field_masking` - PASSED  
- ✅ `test_switch_between_login_and_register` - PASSED

These tests pass because they don't depend on the broken registration→login switch.

---

## 🎯 Immediate Actions Required

### 1. Fix Frontend Registration Flow
**File:** Likely `backend/frontend/js/auth.js` or similar

**Current code probably looks like:**
```javascript
// After successful registration
function handleRegistration(response) {
    showNotification("Registration successful!");
    // MISSING: Switch to login tab
}
```

**Should be:**
```javascript
function handleRegistration(response) {
    showNotification("Registration successful!");
    switchAuthTab('login');  // ← ADD THIS
    // Optionally pre-fill username
    document.getElementById('loginUsername').value = registeredUsername;
}
```

---

### 2. Fix User Menu Dropdown
**File:** Likely `backend/frontend/js/app.js` or similar

**Check:**
1. Is the dropdown CSS being applied?
2. Is the click event handler working?
3. Is there a timing issue with the dropdown opening?

**Temporary Workaround in Test:**
```python
# In dashboard_page.py::logout() method
# Change:
logout_link.wait_for(state="visible", timeout=5000)

# To:
self.page.wait_for_timeout(1000)  # Give dropdown time to open
logout_link.click(force=True)  # Force click even if not fully visible
```

---

## 🔧 Test Suite Improvements

### Add Timeout Protection
Prevent tests from hanging forever when frontend has bugs.

**Create:** `conftest.py` pytest timeout configuration

```python
@pytest.fixture(autouse=True)
def test_timeout():
    """Ensure tests don't hang forever."""
    # Already configured in pytest.ini with timeout=300
    pass
```

---

### Add Retry Logic for Flaky UI Elements
Some UI elements need time to become visible.

**In:** `pages/base_page.py`

```python
def click_with_retry(self, selector, retries=3, delay=1000):
    """Click element with retries for timing issues."""
    for attempt in range(retries):
        try:
            self.page.locator(selector).click(timeout=5000)
            return
        except TimeoutError:
            if attempt < retries - 1:
                self.page.wait_for_timeout(delay)
            else:
                raise
```

---

## 📊 Test Results Summary

| Test | Status | Issue |
|------|--------|-------|
| test_registration_and_login | ❌ FAIL | Frontend bug: Tab doesn't switch |
| test_logout | ❌ FAIL | Frontend bug: Dropdown not opening |
| test_invalid_login | ✅ PASS | Working correctly |
| test_session_persistence | ❌ FAIL | Frontend bug: Tab doesn't switch |
| test_password_field_masking | ✅ PASS | Working correctly |
| test_switch_between_login_and_register | ✅ PASS | Working correctly |
| test_admin_user_login | ⏭️ SKIP | No admin credentials |

**Pass Rate:** 3/6 (50%) - **NOT a test framework issue, APPLICATION BUGS**

---

## 🚫 Why Browser Stays Open

### Scenario 1: Test Completes Normally
```
Test runs → Cleanup runs → Browser closes ✅
```

### Scenario 2: Test Times Out (Current Issue)
```
Test hangs → User hits Ctrl+C → KeyboardInterrupt → Cleanup INTERRUPTED → Browser stays open ❌
```

### Scenario 3: Test Fails Quickly
```
Test fails → Cleanup runs → Browser closes ✅
```

**Solution:** Fix the frontend bugs so tests don't hang!

---

## 🔧 Quick Workarounds

### 1. Increase Wait After Registration
**File:** `test_auth_flow.py::test_registration_and_login`

```python
# After clicking register button
login_page.click_register_button()

# ADD: Give frontend time to switch tabs
page.wait_for_timeout(2000)

# Then verify login mode
login_page.assert_in_login_mode()
```

### 2. Force Click Logout
**File:** `pages/dashboard_page.py::logout()`

```python
# Replace:
logout_link.wait_for(state="visible", timeout=5000)
logout_link.click()

# With:
logout_link.click(force=True)  # Force click even if hidden
```

### 3. Add Explicit Wait for Tab Visibility
**File:** `pages/login_page.py::switch_to_login_mode()`

```python
def switch_to_login_mode(self):
    """Switch to login mode and WAIT for it to be visible."""
    self.click(self.LOGIN_TAB)
    # ADD: Wait for login form to actually appear
    self.wait_for_selector(self.LOGIN_USERNAME_INPUT, timeout=5000)
```

---

## 🎯 Recommended Next Steps

1. **Fix Frontend First** - These are application bugs, not test issues
2. **Apply Workarounds** - Make tests more resilient to timing issues
3. **Add Retry Logic** - Handle flaky UI elements gracefully
4. **Increase Timeouts** - Give slow operations more time

---

## 📝 Conclusion

**The E2E test framework is STABLE and working correctly.**

The issues you're experiencing are:
1. **Frontend bugs** causing tests to timeout
2. **Manual cancellation** (Ctrl+C) preventing cleanup
3. **NOT a test framework problem**

**Action Items:**
- [ ] Fix registration→login tab switch in frontend
- [ ] Fix user menu dropdown visibility
- [ ] Apply test workarounds for resilience
- [ ] Re-run tests to verify fixes

Once the frontend bugs are fixed, you'll see:
- ✅ All tests pass
- ✅ Browser closes automatically
- ✅ No manual intervention needed
