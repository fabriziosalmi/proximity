# Running Tests - Quick Commands

## 🚀 E2E Tests

### Run All E2E Tests
```bash
cd e2e_tests
pytest -v
```

### Run Specific Categories

#### Backup Tests Only
```bash
pytest -v -m backup
```

#### Volume Tests Only
```bash
pytest -v -m volume
```

#### Fast Tests Only (skip slow)
```bash
pytest -v -m "e2e and not slow"
```

#### Critical Path Tests
```bash
pytest -v -m critical
```

### Run Specific Test Files

#### Backup/Restore Tests
```bash
pytest -v e2e_tests/test_backup_restore_flow.py
```

#### Volume Management Tests
```bash
pytest -v e2e_tests/test_volume_management.py
```

#### App Lifecycle Tests
```bash
pytest -v e2e_tests/test_app_lifecycle.py
```

### Run Single Test
```bash
pytest -v e2e_tests/test_backup_restore_flow.py::test_backup_creation_and_listing
```

## 🔧 Backend/Unit Tests

### Run All Backend Tests
```bash
pytest tests/ -v
```

### Run Integration Tests Only
```bash
pytest tests/test_integration.py -v
```

### Run API Endpoint Tests
```bash
pytest tests/test_api_endpoints.py -v
```

### Run Service Tests
```bash
pytest tests/test_app_service.py -v
pytest tests/test_auth_service.py -v
pytest tests/test_backup_api.py -v
```

## 🎯 Run Tests by Priority

### High Priority (uses new fixtures)
```bash
# E2E: Backup tests with new fixtures
pytest -v -m backup e2e_tests/

# E2E: Volume tests with new fixtures
pytest -v -m volume e2e_tests/
```

### Medium Priority (backend with timeouts)
```bash
# Integration tests with timeout protection
pytest -v tests/test_integration.py
```

## 🐛 Debug Mode

### Show Browser (Not Headless)
```bash
HEADLESS=false pytest -v -m backup
```

### Slow Motion (1 second per action)
```bash
SLOW_MO=1000 pytest -v -m backup
```

### Full Output (no capture)
```bash
pytest -v --capture=no -m backup
```

### Stop on First Failure
```bash
pytest -v -x -m backup
```

### Show Local Variables on Failure
```bash
pytest -v -l -m backup
```

## 📊 Coverage Reports

### Run with Coverage
```bash
pytest --cov=backend --cov-report=html tests/
```

### View Coverage Report
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔄 Continuous Testing

### Watch Mode (re-run on change)
```bash
# Install pytest-watch first
pip install pytest-watch

# Run in watch mode
ptw e2e_tests/ -v -m backup
```

## 🚦 Exit Codes

- `0` - All tests passed
- `1` - Some tests failed
- `2` - Test execution interrupted
- `3` - Internal error
- `4` - Usage error

## 💡 Useful Combinations

### Quick Smoke Test
```bash
pytest -v -m smoke --maxfail=3
```

### Full Test Suite with Coverage
```bash
pytest -v --cov=backend --cov-report=term-missing tests/ e2e_tests/
```

### Parallel Execution (requires pytest-xdist)
```bash
pytest -v -n auto tests/  # Auto-detect CPU count
pytest -v -n 4 tests/     # Use 4 workers
```

### Generate Test Report
```bash
pytest -v --html=report.html --self-contained-html
```

## 🎨 Pretty Output

### Colors
```bash
pytest -v --color=yes
```

### Detailed Failures
```bash
pytest -v --tb=long  # Long traceback
pytest -v --tb=short # Short traceback
pytest -v --tb=line  # One line per failure
```

## 🔍 Test Discovery

### List All Tests (don't run)
```bash
pytest --collect-only
```

### List Tests Matching Pattern
```bash
pytest --collect-only -k backup
```

### Show Available Markers
```bash
pytest --markers
```

## ⚡ Performance

### Show Slowest Tests
```bash
pytest -v --durations=10  # Show 10 slowest tests
```

### Show All Test Durations
```bash
pytest -v --durations=0
```

## 🧹 Cleanup

### Clear Cache
```bash
pytest --cache-clear
```

### Remove Pytest Cache
```bash
rm -rf .pytest_cache
rm -rf e2e_tests/.pytest_cache
rm -rf tests/.pytest_cache
```

## 📝 Test Selection by Name

### Run Tests Containing "backup"
```bash
pytest -v -k backup
```

### Run Tests Containing "volume" or "backup"
```bash
pytest -v -k "volume or backup"
```

### Run Tests NOT containing "slow"
```bash
pytest -v -k "not slow"
```

## 🎯 Examples by Use Case

### "I want to test backup functionality"
```bash
pytest -v -m backup e2e_tests/test_backup_restore_flow.py
```

### "I want to test volume management"
```bash
pytest -v -m volume e2e_tests/test_volume_management.py
```

### "I want to run fast tests only"
```bash
pytest -v -m "e2e and not slow"
```

### "I want to debug a failing test"
```bash
HEADLESS=false SLOW_MO=500 pytest -v --capture=no -k test_name
```

### "I want to run backend tests with timeouts"
```bash
pytest -v tests/test_integration.py
```

### "I want to see what's taking so long"
```bash
pytest -v --durations=20 --tb=short
```

## 🚨 CI/CD Usage

### Run in CI Mode
```bash
HEADLESS=true pytest -v --maxfail=5 --tb=short
```

### Generate XML Report for CI
```bash
pytest -v --junitxml=test-results.xml
```

### Run with Retries (requires pytest-rerunfailures)
```bash
pytest -v --reruns 2 --reruns-delay 5
```

## 📚 More Information

- Test fixtures guide: `/TEST_FIXTURES_QUICK_REFERENCE.md`
- Full improvements: `/TEST_INFRASTRUCTURE_IMPROVEMENTS.md`
- E2E test directory: `/e2e_tests/`
- Backend test directory: `/tests/`
