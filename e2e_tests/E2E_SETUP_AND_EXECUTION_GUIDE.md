# E2E Test Suite - Setup and Execution Guide

## 🎯 Quick Start

### 1. Virtual Environment Setup (First Time Only)

```bash
cd e2e_tests

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Start Backend Server

The E2E tests require the Proximity backend to be running on port 8765:

```bash
# In a separate terminal, from project root:
cd backend
python main.py
```

Verify backend is running:
```bash
curl http://127.0.0.1:8765
```

### 3. Run Tests

#### Using the Helper Script (Recommended)
```bash
cd e2e_tests
./run_tests.sh                           # Run all tests
./run_tests.sh test_auth_flow.py -v     # Run specific file
./run_tests.sh -k "test_login" -v       # Run tests matching pattern
```

#### Using pytest directly
```bash
cd e2e_tests
source venv/bin/activate
pytest test_auth_flow.py -v             # Run auth tests
pytest -v                                # Run all tests
pytest --headed                          # Run with visible browser
```

---

## 📋 Test Execution Options

### Run Specific Tests
```bash
# Single test
pytest test_auth_flow.py::test_registration_and_login -v

# All auth tests
pytest test_auth_flow.py -v

# Tests matching pattern
pytest -k "login" -v
```

### Browser Visibility
```bash
# Headless (default for CI)
pytest test_auth_flow.py

# Headed (visible browser - for debugging)
pytest test_auth_flow.py --headed

# Slow motion (for watching)
SLOW_MO=1000 pytest test_auth_flow.py --headed
```

### Parallel Execution
```bash
# Run tests in parallel (faster)
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

### Debugging Options
```bash
# Show print statements
pytest -s

# Verbose output
pytest -v

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x

# Enter debugger on failure
pytest --pdb
```

---

## 🔧 Environment Variables

Create a `.env` file in the `e2e_tests` directory:

```env
# Backend URL (default: http://127.0.0.1:8765)
PROXIMITY_E2E_URL=http://127.0.0.1:8765

# Browser settings
HEADLESS=false           # Set to true for CI
SLOW_MO=0               # Milliseconds to slow down (for debugging)
TIMEOUT=30000           # Default timeout in milliseconds

# Admin credentials (for admin tests)
E2E_ADMIN_USERNAME=admin
E2E_ADMIN_PASSWORD=admin123
```

---

## 🧪 Test Structure

### Stabilized Tests (✅ Refactored)
- `test_auth_flow.py::test_registration_and_login` - **Clean Slate + Smart Wait**
- `test_auth_flow.py::test_invalid_login` - **Clean Slate + Smart Wait**
- `test_auth_flow.py::test_logout` - **Smart Wait**
- `conftest.py::authenticated_page` fixture - **Clean Slate + Smart Wait**

### Key Patterns Implemented
1. **Clean Slate Pattern**: All tests start with cleared localStorage/sessionStorage
2. **Smart Wait Pattern**: Tests wait for visible outcomes, not arbitrary timeouts
3. **Test Isolation**: Each test is completely independent

---

## 📊 Expected Results After Refactoring

### Before Stabilization
```
49 ERRORS - All TargetClosedError
Tests randomly pass/fail
Broken test isolation
```

### After Stabilization
```
0 TargetClosedError exceptions
Consistent, deterministic test results
Complete test isolation
Reliable CI/CD indicator
```

---

## 🐛 Troubleshooting

### Backend Not Running
```
Error: Connection refused
Solution: Start backend with `python backend/main.py`
```

### Browser Not Installed
```
Error: Executable doesn't exist
Solution: Run `playwright install chromium`
```

### Module Not Found
```
Error: ModuleNotFoundError: No module named 'pytest_playwright'
Solution: Ensure venv is activated: source venv/bin/activate
```

### Tests Timing Out
```
Error: Test exceeded timeout
Solution: 
1. Check backend is running
2. Increase timeout: TIMEOUT=60000 pytest test_auth_flow.py
3. Check network connectivity
```

### Flaky Tests
```
If tests still flake:
1. Check console logs for race conditions
2. Verify Clean Slate pattern is applied
3. Verify Smart Waits are used (not timeouts)
4. Check backend is not overwhelmed (run with --headed to observe)
```

---

## 📚 Documentation References

- **Stability Patterns**: See `E2E_STABILITY_PATTERNS_QUICK_REF.md`
- **Complete Refactoring Guide**: See `E2E_TEST_SUITE_STABILIZATION.md`
- **Playwright Python Docs**: https://playwright.dev/python/

---

## ✅ Pre-Commit Checklist

Before committing E2E test changes:

- [ ] Backend is running on port 8765
- [ ] All tests pass locally: `pytest test_auth_flow.py -v`
- [ ] Used Clean Slate pattern for tests requiring logged-out state
- [ ] Used Smart Waits instead of arbitrary timeouts
- [ ] No `wait_for_timeout()` calls in new code
- [ ] Tests are isolated (don't depend on execution order)
- [ ] Added logging for debugging if needed

---

## 🎯 Common Test Scenarios

### Testing New Authentication Feature
```python
def test_new_auth_feature(page: Page):
    # Clean Slate Pattern
    page.goto(page.url)
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    page.reload()
    
    login_page = LoginPage(page)
    
    # Your test logic here
    
    # Smart Wait Pattern
    expect(some_element).to_be_visible(timeout=10000)
```

### Testing Authenticated Feature
```python
def test_authenticated_feature(authenticated_page: Page):
    # Fixture already provides authenticated state
    dashboard_page = DashboardPage(authenticated_page)
    
    # Your test logic here
```

### Testing Logout
```python
def test_logout_feature(authenticated_page: Page):
    dashboard_page = DashboardPage(authenticated_page)
    login_page = LoginPage(authenticated_page)
    
    dashboard_page.logout()
    
    # Smart Wait - wait for auth modal
    expect(login_page.modal).to_be_visible(timeout=10000)
    
    # Now safe to assert
```

---

## 🚀 CI/CD Integration

### GitHub Actions Example
```yaml
- name: Install E2E dependencies
  run: |
    cd e2e_tests
    pip install -r requirements.txt
    playwright install chromium

- name: Start backend
  run: |
    cd backend
    python main.py &
    sleep 5

- name: Run E2E tests
  env:
    HEADLESS: true
    TIMEOUT: 60000
  run: |
    cd e2e_tests
    pytest -v --junit-xml=test-results.xml
```

---

**Last Updated**: October 5, 2025  
**Status**: ✅ Test Suite Stabilized with Clean Slate + Smart Wait patterns
