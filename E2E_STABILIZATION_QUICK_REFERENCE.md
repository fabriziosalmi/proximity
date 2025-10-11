# Quick Reference: E2E Test Stabilization Patterns

## When to Use Clean Slate Pattern

Use this pattern at the **beginning** of any test that must start in an unauthenticated state:

```python
def test_my_unauthenticated_feature(page: Page, base_url: str):
    """Test that requires starting logged out."""
    
    # --- CRITICAL ISOLATION STEP: Clean Slate Pattern ---
    page.goto(base_url)
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    page.reload()
    # --- END OF ISOLATION STEP ---
    
    # Now proceed with test...
```

**Why?** Prevents JWT token leakage from previous tests that could cause false passes.

## When to Use Smart Waits

Replace any `page.wait_for_timeout()` with Smart Waits that check for actual UI state:

### ❌ Bad (Fragile):
```python
page.click("#loginButton")
page.wait_for_timeout(2000)  # Hope it's done in 2 seconds
assert dashboard_visible()
```

### ✅ Good (Robust):
```python
page.click("#loginButton")
expect(dashboard_page.dashboard_container).to_be_visible(timeout=15000)
# Now we KNOW the async login completed
```

**Why?** Waits exactly as long as needed (faster on fast systems, more patient on slow systems).

## Common Smart Wait Patterns

### After Login:
```python
login_page.click_login_button()
expect(dashboard_page.dashboard_container).to_be_visible(timeout=15000)
```

### After Logout:
```python
dashboard_page.logout()
expect(login_page.modal).to_be_visible(timeout=10000)
```

### After Error:
```python
login_page.click_login_button()
expect(login_page.login_error).to_be_visible(timeout=10000)
```

## authenticated_page Fixture

Use this fixture when your test needs a logged-in user:

```python
def test_my_authenticated_feature(authenticated_page: Page):
    """Test that requires authentication."""
    
    dashboard_page = DashboardPage(authenticated_page)
    
    # User is already logged in, dashboard is visible
    # No need for manual login or waiting
    dashboard_page.navigate_to_settings()
    # ... rest of test
```

**What it does**:
1. Creates user via API (fast)
2. Clears all storage (clean slate)
3. Logs in via UI (tests real UX)
4. Waits for dashboard (smart wait)
5. Yields stable, authenticated page
6. Cleans up after test

## Troubleshooting

### Test fails with TargetClosedError?
→ Add Clean Slate pattern at test start

### Test has intermittent timeouts?
→ Replace `wait_for_timeout()` with Smart Wait

### Tests pass individually but fail in suite?
→ JWT token leaking between tests, add Clean Slate

### authenticated_page fixture fails?
→ Check API endpoint availability and credentials

## Best Practices

1. **Always use base_url parameter** instead of hardcoded URLs
2. **Never use sleep()** or `wait_for_timeout()` - use Smart Waits
3. **Clear storage** before tests that need unauthenticated state
4. **Wait for visible elements** not arbitrary time periods
5. **Use fixtures** for common setup (authenticated_page, etc.)

---

**Remember**: Race conditions come from **not waiting** for async operations to complete. Smart Waits solve this!
