# 🧪 Proximity 2.0 - E2E Test Suite

## Overview

This directory contains the End-to-End (E2E) test suite for Proximity 2.0, built using **Playwright** and **pytest**. The tests follow the **"Indestructible Test Pattern"**, ensuring complete test isolation through unique user creation and automatic cleanup.

## 🎯 Test Philosophy

The E2E tests are designed to be:

- **Self-Contained**: Each test creates its own unique user and resources
- **Reliable**: Robust waiting strategies prevent flaky tests
- **Clean**: Automatic cleanup ensures no test pollution
- **Maintainable**: Page Object Model keeps tests DRY and readable
- **Fast Feedback**: Clear logging and assertions pinpoint failures

## 📁 Directory Structure

```
e2e_tests/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── conftest.py                 # Test fixtures and configuration
├── test_golden_path.py         # Main Golden Path test
├── pages/                      # Page Object Models
│   ├── __init__.py
│   ├── login_page.py          # Login/Auth page interactions
│   ├── store_page.py          # App Store/Catalog page interactions
│   └── apps_page.py           # My Apps management page interactions
└── test-results/              # Generated test artifacts (videos, screenshots)
```

## 🚀 Quick Start

### Prerequisites

1. **Running Application Stack**:
   ```bash
   cd /path/to/proximity2
   docker-compose up -d
   ```

2. **Python 3.9+** installed

### Installation

1. **Navigate to the e2e_tests directory**:
   ```bash
   cd e2e_tests
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install
   ```

### Running Tests

#### Run All Tests
```bash
pytest
```

#### Run Only the Golden Path Test
```bash
pytest -m golden_path
```

#### Run Smoke Tests Only
```bash
pytest -m smoke
```

#### Run with Headed Browser (See the Browser)
```bash
pytest --headed
```

#### Run with Slow Motion (Debugging)
```bash
pytest --headed --slowmo 1000
```

#### Run with Video Recording
```bash
RECORD_VIDEO=1 pytest
```

#### Run with Verbose Output
```bash
pytest -vv -s
```

### Environment Variables

You can customize the test environment using these variables:

```bash
# Frontend URL (default: http://localhost:5173)
export BASE_URL=http://localhost:5173

# Backend API URL (default: http://localhost:8000)
export API_URL=http://localhost:8000

# Enable video recording
export RECORD_VIDEO=1
```

## 🧩 Test Architecture

### The "Indestructible Test Pattern"

Our tests follow a unique pattern that ensures perfect isolation:

1. **Before Test**: 
   - Create a unique user via API (e.g., `testuser_1697654321000@e2etest.local`)
   - User gets unique credentials
   
2. **During Test**: 
   - Use the unique user to perform all operations
   - Deploy apps with unique hostnames (e.g., `e2e-adminer-1697654321000`)
   
3. **After Test**: 
   - Automatically delete all apps created by the user
   - Automatically delete the user account
   - Leave the system in a clean state

### Page Object Model (POM)

We use the Page Object Model pattern to:
- Encapsulate page-specific locators and interactions
- Make tests more readable and maintainable
- Reduce code duplication
- Enable easy updates when UI changes

Example:
```python
# Instead of this:
page.fill('input[name="username"]', username)
page.fill('input[name="password"]', password)
page.click('button[type="submit"]')

# We do this:
login_page = LoginPage(page, base_url)
login_page.login(username, password)
```

## 📝 Test Cases

### Golden Path Test (`test_full_app_lifecycle`)

**Duration**: ~3-5 minutes  
**Marks**: `@pytest.mark.golden_path`, `@pytest.mark.slow`

This is the CRITICAL test that validates the entire user journey:

1. **Login**: Authenticate with unique test user
2. **Navigate**: Go to App Store (/store)
3. **Deploy**: Deploy "Adminer" application with unique hostname
4. **Monitor**: Wait for deployment to complete (status: deploying → running)
5. **Stop**: Stop the running application
6. **Start**: Start the stopped application
7. **Delete**: Delete the application and verify removal

**Why It's Critical**: This test exercises the complete application lifecycle and validates all major features working together.

### Smoke Tests

#### `test_login_only`
**Duration**: ~5 seconds  
Quick validation that authentication works.

#### `test_catalog_loads`
**Duration**: ~10 seconds  
Validates that the catalog service loads applications.

## 🔍 Debugging Failed Tests

### 1. Run with Headed Browser
```bash
pytest --headed
```
This shows you the browser as the test runs.

### 2. Run with Slow Motion
```bash
pytest --headed --slowmo 1000
```
Slows down actions by 1000ms each for easier observation.

### 3. Enable Video Recording
```bash
RECORD_VIDEO=1 pytest
```
Videos will be saved in `test-results/videos/`.

### 4. Check Test Output
Tests provide detailed console output showing each step:
```
📍 STEP 1: Login
--------------------------------------------------------------------------------
  ✓ Navigated to login page
  ✓ Submitted login credentials
  ✅ LOGIN SUCCESS - Redirected to dashboard
```

### 5. Use Playwright Inspector
```bash
PWDEBUG=1 pytest
```
Opens Playwright Inspector for step-by-step debugging.

## 🎭 Common Issues & Solutions

### Issue: Tests timeout during deployment

**Symptom**: Test fails at "Monitor Deployment Progress" step

**Solution**:
- Increase timeout in `apps_page.wait_for_status()` (default is 180s)
- Check that Proxmox is running and accessible
- Verify Docker images can be pulled
- Check Celery worker logs: `docker-compose logs celery_worker`

### Issue: Login fails

**Symptom**: `assert_login_success` fails

**Solution**:
- Verify backend is running: `curl http://localhost:8000/api/core/health`
- Check if registration endpoint works: Check backend logs
- Verify frontend is accessible: `curl http://localhost:5173`

### Issue: App card not found

**Symptom**: `get_app_card_by_hostname()` fails to find the app

**Solution**:
- Check if the app was actually deployed: Look at backend/celery logs
- Verify the hostname matches exactly
- Check frontend console for errors: Run with `--headed`
- Ensure polling is working in the frontend

### Issue: Cleanup fails

**Symptom**: Warning messages during teardown

**Solution**:
- This is usually non-critical (user deletion endpoint might not exist yet)
- Cleanup failures don't fail the test
- You may need to manually clean test data periodically

## 📊 CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start Application Stack
        run: |
          docker-compose up -d
          sleep 30  # Wait for services to be ready
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd e2e_tests
          pip install -r requirements.txt
          playwright install --with-deps
      
      - name: Run E2E Tests
        run: |
          cd e2e_tests
          pytest -v
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: e2e_tests/test-results/
```

## 🏗️ Extending the Test Suite

### Adding a New Test

1. **Create a test function** in `test_golden_path.py` or a new file:
   ```python
   def test_my_feature(page: Page, unique_user: dict, base_url: str):
       # Your test code here
       pass
   ```

2. **Use Page Objects** for interactions:
   ```python
   login_page = LoginPage(page, base_url)
   store_page = StorePage(page, base_url)
   apps_page = AppsPage(page, base_url)
   ```

3. **Add appropriate markers**:
   ```python
   @pytest.mark.smoke  # For quick tests
   @pytest.mark.slow   # For tests >60 seconds
   ```

### Adding a New Page Object

1. **Create a new file** in `pages/`:
   ```python
   # pages/settings_page.py
   from playwright.sync_api import Page, expect
   
   class SettingsPage:
       def __init__(self, page: Page, base_url: str):
           self.page = page
           self.base_url = base_url
       
       # Add your methods here
   ```

2. **Export it** in `pages/__init__.py`:
   ```python
   from .settings_page import SettingsPage
   __all__ = ['LoginPage', 'StorePage', 'AppsPage', 'SettingsPage']
   ```

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Page Object Model Pattern](https://playwright.dev/python/docs/pom)
- [Proximity 2.0 API Documentation](http://localhost:8000/api/docs)

## 🤝 Contributing

When adding new tests:
1. Follow the existing patterns (POM, fixtures, assertions)
2. Add clear docstrings
3. Use descriptive test names
4. Include appropriate markers
5. Test your tests locally before committing
6. Update this README if you add new features

## 📞 Support

For issues with the E2E tests:
1. Check the "Common Issues" section above
2. Review test output for specific error messages
3. Run with `--headed` and `--slowmo` to observe behavior
4. Check application logs: `docker-compose logs`

---

**Happy Testing! 🧪✨**
