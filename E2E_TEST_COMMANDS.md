# E2E Test Commands - Quick Guide

## 🚀 Running Tests

### Run all E2E tests (excluding skipped)
```bash
pytest e2e_tests/ -v
```

### Run only passing tests (exclude volumes and known failures)
```bash
pytest e2e_tests/ -v -m "e2e and not volume"
```

### Run specific test file
```bash
pytest e2e_tests/test_app_lifecycle.py -v
```

### Run specific test function
```bash
pytest e2e_tests/test_app_lifecycle.py::test_full_app_deploy_manage_delete_workflow -v
```

### Run with detailed output (including print statements)
```bash
pytest e2e_tests/ -v -s
```

### Run with short traceback
```bash
pytest e2e_tests/ -v --tb=short
```

### Run with line-level traceback
```bash
pytest e2e_tests/ -v --tb=line
```

---

## 🔍 Filtering and Collection

### See what tests would run (don't execute)
```bash
pytest e2e_tests/ --collect-only
```

### See test collection in quiet mode
```bash
pytest e2e_tests/ --collect-only -q
```

### Count total tests
```bash
pytest e2e_tests/ --collect-only -q | grep "test session" | tail -1
```

### Show only skipped tests
```bash
pytest e2e_tests/ -v | grep SKIP
```

### Show test markers
```bash
pytest e2e_tests/ --markers
```

---

## 🎯 Running by Markers

### Run only critical tests
```bash
pytest e2e_tests/ -v -m critical
```

### Run only smoke tests
```bash
pytest e2e_tests/ -v -m smoke
```

### Run lifecycle tests
```bash
pytest e2e_tests/ -v -m lifecycle
```

### Exclude volume tests
```bash
pytest e2e_tests/ -v -m "not volume"
```

### Run multiple markers
```bash
pytest e2e_tests/ -v -m "critical or smoke"
```

---

## ⏱️ Timeout Management

### Run with custom timeout (useful for deployment tests)
```bash
timeout 240 pytest e2e_tests/test_app_lifecycle.py -v
```

### Run with pytest timeout plugin
```bash
pytest e2e_tests/ -v --timeout=120
```

---

## 📊 Output Formatting

### Show only summary
```bash
pytest e2e_tests/ -v --tb=no
```

### Show first 50 lines of output
```bash
pytest e2e_tests/ -v 2>&1 | head -50
```

### Show last 50 lines (useful for summary)
```bash
pytest e2e_tests/ -v 2>&1 | tail -50
```

### Show only pass/fail/skip status
```bash
pytest e2e_tests/ -v 2>&1 | grep -E "(PASSED|FAILED|SKIPPED)"
```

### Count test results
```bash
pytest e2e_tests/ -v 2>&1 | grep -c PASSED
pytest e2e_tests/ -v 2>&1 | grep -c FAILED
pytest e2e_tests/ -v 2>&1 | grep -c SKIPPED
```

---

## 🐛 Debugging

### Run with maximum verbosity
```bash
pytest e2e_tests/ -vv -s --tb=long
```

### Run and stop on first failure
```bash
pytest e2e_tests/ -v -x
```

### Run and stop after N failures
```bash
pytest e2e_tests/ -v --maxfail=3
```

### Show local variables on failure
```bash
pytest e2e_tests/ -v -l
```

### Run last failed tests only
```bash
pytest e2e_tests/ -v --lf
```

### Run failed tests first, then remaining
```bash
pytest e2e_tests/ -v --ff
```

---

## 🔄 Re-running Flaky Tests

### Re-run failures up to 3 times
```bash
pytest e2e_tests/ -v --reruns 3
```

### Re-run failures with delay
```bash
pytest e2e_tests/ -v --reruns 3 --reruns-delay 5
```

---

## 📸 Screenshots and Videos (Playwright)

### Take screenshots on failure
```bash
pytest e2e_tests/ -v --screenshot on-failure
```

### Record videos
```bash
pytest e2e_tests/ -v --video on
```

### Keep videos only on failure
```bash
pytest e2e_tests/ -v --video retain-on-failure
```

---

## 🎭 Browser Selection

### Run in specific browser
```bash
pytest e2e_tests/ -v --browser chromium
pytest e2e_tests/ -v --browser firefox
pytest e2e_tests/ -v --browser webkit
```

### Run in headed mode (see browser)
```bash
pytest e2e_tests/ -v --headed
```

### Run with slow motion (debug)
```bash
pytest e2e_tests/ -v --headed --slowmo 1000
```

---

## 📦 Coverage

### Run with coverage report
```bash
pytest e2e_tests/ -v --cov=e2e_tests
```

### Generate HTML coverage report
```bash
pytest e2e_tests/ -v --cov=e2e_tests --cov-report=html
```

---

## 🔧 Common Workflows

### Quick smoke test
```bash
pytest e2e_tests/ -v -m smoke --tb=short
```

### Full test run with detailed output
```bash
pytest e2e_tests/ -v -s --tb=short > test_results.txt 2>&1
```

### CI/CD pipeline command
```bash
pytest e2e_tests/ -v -m "not volume" --tb=short --maxfail=5
```

### Debug failing test
```bash
pytest e2e_tests/test_app_lifecycle.py::test_full_app_deploy_manage_delete_workflow -vv -s --tb=long
```

### Check test suite health
```bash
pytest e2e_tests/ --collect-only -q && \
pytest e2e_tests/ -v --tb=no 2>&1 | grep -E "(passed|failed|skipped)" | tail -1
```

---

## 🏗️ Maintenance Commands

### Check for syntax errors
```bash
python -m py_compile e2e_tests/test_*.py
```

### Check imports
```bash
pytest e2e_tests/ --collect-only
```

### List all fixtures
```bash
pytest e2e_tests/ --fixtures
```

### List all markers
```bash
pytest e2e_tests/ --markers
```

---

## 📝 Useful Aliases

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# E2E test aliases
alias e2e='pytest e2e_tests/ -v'
alias e2e-smoke='pytest e2e_tests/ -v -m smoke'
alias e2e-critical='pytest e2e_tests/ -v -m critical'
alias e2e-quick='pytest e2e_tests/ -v -m "smoke or critical" --tb=short'
alias e2e-lifecycle='pytest e2e_tests/test_app_lifecycle.py -v'
alias e2e-debug='pytest e2e_tests/ -vv -s --tb=long'
alias e2e-collect='pytest e2e_tests/ --collect-only -q'
alias e2e-status='pytest e2e_tests/ -v 2>&1 | grep -E "(passed|failed|skipped)" | tail -1'
```

Then use:
```bash
e2e-quick          # Run smoke + critical tests
e2e-lifecycle      # Run lifecycle tests
e2e-debug          # Debug mode
e2e-status         # Quick status check
```

---

## 🎯 Recommended Commands for Our Fixes

### Verify authentication fixture
```bash
pytest e2e_tests/ -v -k "authenticated" -s
```

### Verify selector fixes (no strict mode violations)
```bash
pytest e2e_tests/test_app_lifecycle.py -v --tb=short
```

### Verify method name fixes
```bash
pytest e2e_tests/test_clone_and_config.py e2e_tests/test_app_canvas.py -v
```

### Verify volume skip markers
```bash
pytest e2e_tests/test_volume_management.py -v
```

### Full validation run
```bash
pytest e2e_tests/ -v --tb=short 2>&1 | tee validation_results.txt
```

---

## 📊 Results Interpretation

### Good Test Run
```
========================= 83 tests collected =========================
... PASSED ...
... PASSED ...
... SKIPPED (documented reason) ...
==================== 70 passed, 7 skipped in 45.2s ====================
```

### Test Run with Known Issues
```
========================= 83 tests collected =========================
... PASSED ...
... FAILED (deployment timeout) ...
... SKIPPED (volume endpoints) ...
============ 65 passed, 10 failed, 8 skipped in 120.5s ============
```

**Note:** Failed tests due to deployment timing or missing backend features are EXPECTED and NOT related to our architectural fixes.

---

## 🆘 Troubleshooting

### Backend not running?
```bash
ps aux | grep "python.*main.py" | grep -v grep
# If nothing shows, start backend:
cd backend && python main.py
```

### Browser not closing?
```bash
pkill -f "chromium\|firefox\|webkit"
```

### Port already in use?
```bash
lsof -ti:8765 | xargs kill -9
```

### Clear pytest cache
```bash
rm -rf .pytest_cache e2e_tests/.pytest_cache
```

### Reinstall Playwright browsers
```bash
playwright install chromium
```

---

**Last Updated:** 5 October 2025  
**Related Docs:** `E2E_FIXES_QUICK_REFERENCE.md`, `E2E_FIX_SUMMARY.md`
