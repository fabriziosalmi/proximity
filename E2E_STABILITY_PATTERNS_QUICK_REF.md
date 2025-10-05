# E2E Test Stability Patterns - Quick Reference

## 🎯 Two Core Patterns

### 1. Clean Slate Pattern
**Use when:** Test should start "logged out" or with no session

```python
def test_something(page: Page):
    # --- CRITICAL ISOLATION STEP ---
    page.goto(page.url)
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    page.reload()
    # --- END ---
    
    # Now test can safely assume clean state
```

### 2. Smart Wait Pattern
**Use after:** Any async operation (login, logout, form submit)

```python
# ✅ CORRECT - Wait for visible outcome
expect(element_locator).to_be_visible(timeout=10000)

# ❌ WRONG - Never use arbitrary timeouts
page.wait_for_timeout(2000)  # Race condition!
```

---

## 📋 Common Scenarios

### Starting a Test in Logged Out State
```python
@pytest.mark.auth
def test_something(page: Page):
    # Clean Slate Pattern
    page.goto(page.url)
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    page.reload()
    
    # Now safe to test login flow
    login_page = LoginPage(page)
    login_page.wait_for_auth_modal()
```

### After Login/Registration
```python
# Click login button
login_page.click_login_button()

# ✅ Smart Wait - Wait for dashboard
expect(dashboard_page.dashboard_container).to_be_visible(timeout=15000)

# Now safe to assert
dashboard_page.assert_on_dashboard()
```

### After Logout
```python
# Click logout
dashboard_page.logout()

# ✅ Smart Wait - Wait for auth modal
expect(login_page.modal).to_be_visible(timeout=10000)

# Now safe to assert
login_page.assert_auth_modal_visible()
```

### In Fixtures
```python
@pytest.fixture
def authenticated_page(page: Page, base_url: str):
    # Clean Slate at start
    page.goto(base_url)
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    page.reload()
    
    # ... authentication logic ...
    
    # Smart Wait before yielding
    expect(dashboard_page.dashboard_container).to_be_visible(timeout=15000)
    expect(dashboard_page.get_user_display_locator).to_be_visible(timeout=10000)
    
    yield page
    
    # Cleanup
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
```

---

## ⚠️ Anti-Patterns to Avoid

### ❌ Arbitrary Timeouts
```python
# BAD
page.wait_for_timeout(2000)  # What if it takes 3 seconds?
page.wait_for_timeout(1000)  # Race condition!
```

### ❌ Manual DOM Manipulation
```python
# BAD - Don't force modals open/closed
page.evaluate("modal.classList.remove('show')")
```

### ❌ No Session Cleanup
```python
# BAD - Tokens leak to next test
def test_something(authenticated_page):
    # ... test logic ...
    # Missing cleanup!
```

---

## 🎯 Page Object Helpers

### Dashboard Page
```python
# Use these locators for Smart Waits
dashboard_page.dashboard_container  # Main dashboard
dashboard_page.get_user_display_locator  # User info (logged in indicator)
```

### Login Page
```python
# Use these locators for Smart Waits
login_page.modal  # Auth modal
login_page.login_error  # Error message
login_page.register_error  # Register error
```

---

## 🚀 Checklist for New Tests

- [ ] Does test need logged-out state? → Add Clean Slate Pattern
- [ ] Does test click login/logout? → Add Smart Wait after
- [ ] Does test use `wait_for_timeout()`? → Replace with Smart Wait
- [ ] Does fixture yield a page? → Add Smart Wait before yield
- [ ] Does fixture cleanup? → Clear storage in teardown

---

## 💡 Why These Patterns Work

**Clean Slate Pattern:**
- Prevents JWT token leakage
- Forces known initial state
- Eliminates test interference

**Smart Wait Pattern:**
- Waits for actual async completion
- Auto-retries until success or timeout
- Prevents assertions before UI updates

**Result:** 0 TargetClosedError exceptions! 🎉
