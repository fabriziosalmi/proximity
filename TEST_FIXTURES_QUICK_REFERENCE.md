# Test Fixtures Quick Reference

## 🚀 Quick Start

### Using Pre-deployed App

```python
def test_something(deployed_app: Dict):
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    # App is already deployed and running
    # Cleanup happens automatically
```

### Using App with Backup

```python
def test_restore(deployed_app_with_backup: Dict):
    app_id = deployed_app_with_backup['id']
    backup_id = deployed_app_with_backup['backup_id']
    # App has a backup ready to use
```

### Managing Backups

```python
def test_backups(deployed_app: Dict, backup_manager):
    # Create backup
    backup = backup_manager.create_backup(deployed_app['id'])
    
    # Wait for completion (max 5 minutes)
    completed = backup_manager.wait_for_completion(
        deployed_app['id'], 
        backup['id'], 
        timeout=300
    )
    
    # List backups
    backups = backup_manager.list_backups(deployed_app['id'])
    
    # Restore backup
    backup_manager.restore_backup(deployed_app['id'], backup['id'])
    
    # Delete backup
    backup_manager.delete_backup(deployed_app['id'], backup['id'])
```

### Managing Volumes

```python
def test_volumes(deployed_app: Dict, volume_manager):
    # Create volume (10GB)
    volume = volume_manager.create_volume(
        deployed_app['id'], 
        size=10,
        name="my-volume"
    )
    
    # Attach volume
    volume_manager.attach_volume(deployed_app['id'], volume['id'])
    
    # List volumes
    volumes = volume_manager.list_volumes(deployed_app['id'])
    
    # Detach volume
    volume_manager.detach_volume(deployed_app['id'], volume['id'])
    
    # Delete volume (or automatic cleanup on teardown)
    volume_manager.delete_volume(deployed_app['id'], volume['id'])
```

## 📋 Available Fixtures

### Core Fixtures (from `conftest.py`)

- `page` - Browser page instance
- `context` - Browser context (isolated)
- `authenticated_page` - Page with logged-in user
- `base_url` - Base URL for Proximity instance

### App Fixtures (from `fixtures/deployed_app.py`)

- `deployed_app` - Pre-deployed Nginx app
- `deployed_app_with_backup` - App with one backup
- `backup_manager` - Backup operations helper
- `volume_manager` - Volume operations helper

## 🏷️ Test Markers

Add markers to categorize and control test execution:

```python
@pytest.mark.e2e           # E2E integration test
@pytest.mark.backup        # Backup/restore test
@pytest.mark.volume        # Volume management test
@pytest.mark.slow          # Takes > 60 seconds
@pytest.mark.timeout(120)  # Must complete in 120 seconds
```

Run specific categories:
```bash
# Run only backup tests
pytest -m backup

# Run E2E tests except slow ones
pytest -m "e2e and not slow"

# Run with verbose output
pytest -v -m backup
```

## 🎯 Best Practices

### 1. Use Fixtures Instead of Setup Code

❌ **Don't:**
```python
def test_something(page):
    # Deploy app manually
    # Create backup manually
    # Test...
    # Cleanup manually
```

✅ **Do:**
```python
def test_something(deployed_app_with_backup, backup_manager):
    # Everything is ready
    # Test...
    # Automatic cleanup
```

### 2. Add Timeout Markers

❌ **Don't:**
```python
def test_slow_operation(deployed_app):
    # This might hang forever
```

✅ **Do:**
```python
@pytest.mark.timeout(180)  # 3 minutes max
def test_slow_operation(deployed_app):
    # Will fail fast if it hangs
```

### 3. Use Phase-Based Logging

❌ **Don't:**
```python
def test_something(deployed_app):
    backup = backup_manager.create_backup(app_id)
    # Silent operation
```

✅ **Do:**
```python
def test_something(deployed_app, backup_manager):
    print("\n" + "="*80)
    print("📦 PHASE 1: Create Backup")
    backup = backup_manager.create_backup(app_id)
    print(f"✓ Backup created: {backup['id']}")
```

### 4. Clean Test Names

✅ **Good naming:**
```python
def test_backup_creation_and_listing(...)
def test_backup_completion_polling(...)
def test_volume_attach_detach(...)
```

### 5. Mark Long-Running Tests

```python
@pytest.mark.slow  # Warn that it takes time
@pytest.mark.timeout(360)  # 6 minutes max
def test_backup_completion_polling(deployed_app, backup_manager):
    # This waits for backup to complete
```

## 🐛 Debugging Tips

### See Full Output
```bash
pytest -v --capture=no
```

### Run Single Test
```bash
pytest e2e_tests/test_backup_restore_flow.py::test_backup_creation_and_listing -v
```

### Debug Mode (show browser)
```bash
HEADLESS=false pytest -v -m backup
```

### Slow Motion (see actions)
```bash
SLOW_MO=1000 pytest -v -m backup
```

### Skip Slow Tests
```bash
pytest -m "e2e and not slow"
```

## 📊 Fixture Dependency Tree

```
authenticated_page
    ↓
deployed_app
    ├─→ deployed_app_with_backup
    ├─→ backup_manager
    └─→ volume_manager
```

## 🆘 Common Issues

### Issue: "No auth token found"
**Solution:** Make sure you're using `authenticated_page` not `page`

### Issue: "App not found"
**Solution:** Use `deployed_app` fixture to ensure app exists

### Issue: Test hangs indefinitely
**Solution:** Add `@pytest.mark.timeout(N)` decorator

### Issue: Resources not cleaned up
**Solution:** Use fixtures - they have automatic cleanup

### Issue: Flaky test results
**Solution:** 
- Use `wait_for_completion()` for async operations
- Don't use fixed sleep times
- Use Playwright's built-in waits

## 📚 More Information

- Full docs: `/TEST_INFRASTRUCTURE_IMPROVEMENTS.md`
- Fixture source: `/e2e_tests/fixtures/deployed_app.py`
- Example tests: `/e2e_tests/test_backup_restore_flow.py`
- Volume tests: `/e2e_tests/test_volume_management.py`
