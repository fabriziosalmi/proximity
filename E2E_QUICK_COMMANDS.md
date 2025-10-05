# E2E Tests - Quick Command Reference

## 🚀 Running Tests

```bash
# Activate venv first (ALWAYS!)
cd e2e_tests && source venv/bin/activate

# Run all tests
./run_tests.sh

# Run specific file
./run_tests.sh test_auth_flow.py -v

# Run specific test
./run_tests.sh test_auth_flow.py::test_registration_and_login -v

# Run with visible browser
./run_tests.sh test_auth_flow.py --headed

# Run with slow motion (debugging)
SLOW_MO=1000 ./run_tests.sh test_auth_flow.py --headed

# Run and show print statements
./run_tests.sh test_auth_flow.py -s

# Stop on first failure
./run_tests.sh test_auth_flow.py -x
```

---

## 🔧 Before Running Tests

```bash
# 1. Start backend (separate terminal)
cd backend && python main.py

# 2. Verify backend is up
curl http://127.0.0.1:8765

# 3. Run tests
cd e2e_tests && source venv/bin/activate && ./run_tests.sh
```

---

## 📝 Test Patterns

### Logged-Out Test Template
```python
def test_something(page: Page):
    # Clean Slate
    page.goto(page.url)
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    page.reload()
    
    # Test logic
    login_page = LoginPage(page)
    
    # Smart Wait
    expect(element).to_be_visible(timeout=10000)
```

### Authenticated Test Template
```python
def test_something(authenticated_page: Page):
    # Already authenticated
    dashboard_page = DashboardPage(authenticated_page)
    
    # Test logic + Smart Waits
    expect(element).to_be_visible(timeout=10000)
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend not running | `cd backend && python main.py` |
| Module not found | `source venv/bin/activate` |
| Browser won't close | Check cleanup logs with `-s` flag |
| Tests timeout | Check backend is running and responsive |
| Flaky tests | Verify Clean Slate + Smart Wait patterns used |

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `E2E_REFACTORING_COMPLETE_SUMMARY.md` | Full overview |
| `E2E_STABILITY_PATTERNS_QUICK_REF.md` | Pattern examples |
| `E2E_SETUP_AND_EXECUTION_GUIDE.md` | Setup instructions |
| `BROWSER_CLEANUP_FIX.md` | Cleanup details |

---

## ✅ Pre-Commit

```bash
# Run these before committing
cd e2e_tests && source venv/bin/activate
pytest test_auth_flow.py -v
# All should pass ✅
```

---

**Key Rules:**
1. Always use venv
2. Clean Slate for logged-out tests
3. Smart Waits after async actions
4. Never use `wait_for_timeout()`
