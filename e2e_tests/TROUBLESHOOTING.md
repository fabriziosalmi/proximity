# 🔧 E2E Tests - Troubleshooting Guide

## Quick Diagnostics

Run these commands to verify your setup:

```bash
# Check backend is running
curl http://localhost:8000/api/core/health

# Check frontend is running
curl http://localhost:5173

# Check Docker containers
docker-compose ps

# Check Celery worker
docker-compose logs celery_worker --tail 50

# Check backend logs
docker-compose logs backend --tail 50
```

---

## Common Issues

### 1. Backend Not Running

**Symptom**:
```
❌ Backend not responding at http://localhost:8000
```

**Solution**:
```bash
cd /Users/fab/GitHub/proximity/proximity2
docker-compose up -d
sleep 30  # Wait for services
```

**Verify**:
```bash
curl http://localhost:8000/api/core/health
# Should return: {"status": "healthy", ...}
```

---

### 2. Playwright Browsers Not Installed

**Symptom**:
```
Error: browserType.launch: Executable doesn't exist
```

**Solution**:
```bash
cd e2e_tests
source venv/bin/activate
playwright install
```

---

### 3. Test Times Out During Deployment

**Symptom**:
```
TimeoutError: Timeout 180000ms exceeded.
  waiting for locator('.status-running')
```

**Possible Causes**:
1. Docker image is large and taking time to pull
2. Proxmox is not configured/running
3. Celery worker is stuck

**Solutions**:

**A. Check Celery Worker**:
```bash
docker-compose logs celery_worker --tail 100
```
Look for errors or stuck tasks.

**B. Check Backend Logs**:
```bash
docker-compose logs backend --tail 100
```
Look for ProxmoxError or connection issues.

**C. Increase Timeout**:
Edit `e2e_tests/.env`:
```bash
DEPLOYMENT_TIMEOUT=300  # 5 minutes instead of 3
```

**D. Test Manually**:
```bash
# Try deploying via API directly
curl -X POST http://localhost:8000/api/apps/ \
  -H "Content-Type: application/json" \
  -d '{"app_id": "adminer", "hostname": "test-manual"}'
```

---

### 4. User Registration Fails

**Symptom**:
```
Failed to create test user: 400 Bad Request
```

**Possible Causes**:
1. Backend not running
2. Database not migrated
3. Registration endpoint doesn't exist

**Solutions**:

**A. Check Registration Endpoint**:
```bash
curl -X POST http://localhost:8000/api/core/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@test.com",
    "password": "Test123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**B. Check Database Migrations**:
```bash
docker-compose exec backend python manage.py showmigrations
```

**C. Run Migrations**:
```bash
docker-compose exec backend python manage.py migrate
```

---

### 5. App Card Not Found

**Symptom**:
```
Error: Locator('.rack-card:has-text("e2e-adminer-123")') not found
```

**Possible Causes**:
1. App deployment failed silently
2. Frontend not polling correctly
3. Wrong hostname

**Solutions**:

**A. Check if App Exists in Backend**:
```bash
curl http://localhost:8000/api/apps/
```

**B. Check Frontend Console**:
Run test with headed mode:
```bash
pytest --headed
```
Open browser DevTools (F12) and check Console for errors.

**C. Verify Polling**:
Look for these in browser Network tab:
- Repeated GET requests to `/api/apps/`
- Should happen every 5 seconds

---

### 6. Login Fails (UI)

**Symptom**:
```
AssertionError: Login indicators not found after login
```

**Solutions**:

**A. Check Login UI**:
```bash
pytest --headed --slowmo 1000
```
Watch what happens during login.

**B. Check Frontend Routes**:
Verify these files exist:
- `frontend/src/routes/login/+page.svelte`
- `frontend/src/routes/+page.svelte`

**C. Check API Response**:
```bash
curl -X POST http://localhost:8000/api/core/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Test123!"}'
```

---

### 7. Cleanup Fails

**Symptom**:
```
⚠️  Could not delete user account: 404 Not Found
```

**Solution**:
This is **not critical**. The user deletion endpoint may not be implemented yet.

To manually clean up test users:
```bash
docker-compose exec backend python manage.py shell
```
```python
from django.contrib.auth.models import User
User.objects.filter(username__startswith='testuser_').delete()
```

---

### 8. Port Already in Use

**Symptom**:
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solution**:
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or stop conflicting Docker containers
docker ps | grep 8000
docker stop <container_name>
```

---

### 9. Permission Denied on run_tests.sh

**Symptom**:
```
bash: ./run_tests.sh: Permission denied
```

**Solution**:
```bash
chmod +x run_tests.sh
```

---

### 10. Tests Pass But App Isn't Actually Working

**Symptom**:
Test says "PASSED" but manual testing shows issues.

**Possible Causes**:
- Locators are too loose
- Waiting strategies are incorrect
- Assertions are not strict enough

**Solutions**:

**A. Add More Specific Assertions**:
```python
# Instead of just checking if card exists
apps_page.assert_app_visible(hostname)

# Also check status explicitly
assert apps_page.get_app_status(hostname) == 'running'
```

**B. Add Functional Verification**:
```python
# Try to access the deployed app
response = requests.get(f"http://{hostname}.example.com")
assert response.status_code == 200
```

---

## Advanced Debugging

### Using Playwright Trace Viewer

1. **Enable tracing in conftest.py**:
```python
@pytest.fixture
def context_with_storage(browser: Browser):
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True)
    yield context
    context.tracing.stop(path="trace.zip")
    context.close()
```

2. **View trace**:
```bash
playwright show-trace trace.zip
```

### Using Playwright Inspector

```bash
PWDEBUG=1 pytest test_golden_path.py::test_full_app_lifecycle
```

This opens an interactive debugger where you can:
- Step through each action
- Inspect DOM
- Record actions
- Generate code

### Verbose Pytest Output

```bash
pytest -vv -s --tb=long
```

- `-vv`: Very verbose
- `-s`: Show print statements
- `--tb=long`: Full tracebacks

---

## Performance Issues

### Tests Are Slow

**Normal Timing**:
- Smoke tests: 5-15 seconds
- Golden Path: 3-5 minutes (mostly waiting for deployment)

**If Slower**:

1. **Check System Resources**:
```bash
docker stats
```

2. **Reduce Timeout**:
For faster iteration during development:
```python
# In test_golden_path.py
apps_page.wait_for_status(hostname, 'running', timeout=60000)  # 1 min
```

3. **Use Headless Mode**:
```bash
# Faster than headed
pytest
```

---

## Environment-Specific Issues

### Running on CI/CD

**Additional Considerations**:

1. **Install system dependencies**:
```bash
playwright install-deps
```

2. **Use xvfb** for headless Linux:
```bash
xvfb-run pytest
```

3. **Increase timeouts** for slower CI machines:
```bash
export DEPLOYMENT_TIMEOUT=300
```

### Running on macOS

**Known Issues**:
- Sometimes Docker Desktop sleeps → restart it
- Rosetta 2 on M1 Macs may be slower

**Solutions**:
```bash
# Check Docker is running
docker ps

# Restart Docker Desktop if needed
```

### Running on Windows

**Additional Setup**:
```powershell
# Use PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install
```

---

## Getting Help

### Logs to Collect

When reporting issues, provide:

1. **Test output**:
```bash
pytest -vv -s > test_output.txt 2>&1
```

2. **Backend logs**:
```bash
docker-compose logs backend > backend.log
```

3. **Celery logs**:
```bash
docker-compose logs celery_worker > celery.log
```

4. **Frontend logs** (from browser console)

5. **Test configuration**:
```bash
cat pytest.ini
cat .env
```

### Check Prerequisites

```bash
# Python version (need 3.9+)
python3 --version

# Docker version
docker --version
docker-compose --version

# Check services
curl http://localhost:8000/api/core/health
curl http://localhost:5173
```

---

## Still Stuck?

1. ✅ Read the README.md thoroughly
2. ✅ Check all diagnostic commands above
3. ✅ Run with `--headed --slowmo 1000` to observe
4. ✅ Check application logs
5. ✅ Try the manual API test (see "Test Times Out" section)
6. ✅ Verify Proxmox configuration
7. ✅ Check if issue is test-specific or app-specific

---

**Most issues are environment-related, not test-related. Ensure your Docker stack is healthy first!** 🔍
