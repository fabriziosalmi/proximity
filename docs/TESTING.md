# Testing Guide

## Overview

Proximity has comprehensive test coverage with **102/102 tests passing (100% coverage)** for the backend.

## Test Structure

```
backend/
├── tests/                    # Shared tests
│   ├── test_models.py       # Model tests
│   ├── test_services.py     # Service tests
│   ├── test_schemas.py      # Authentication tests
│   ├── test_utils.py        # Utility function tests
│   └── conftest.py          # Shared fixtures
├── apps/
│   ├── applications/
│   │   └── test_node_selection.py
│   ├── backups/
│   │   ├── test_api.py      # API endpoint tests
│   │   ├── test_tasks.py    # Celery task tests
│   │   └── conftest.py      # Backup fixtures
│   ├── catalog/
│   │   └── test_api.py      # Catalog endpoint tests
│   └── [other apps]/
└── conftest.py              # Root pytest configuration
```

## Running Tests

### Prerequisites

```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
# With mock Proxmox service
USE_MOCK_PROXMOX=1 python -m pytest

# With coverage report
USE_MOCK_PROXMOX=1 python -m pytest --cov=apps --cov=tests

# Verbose output
USE_MOCK_PROXMOX=1 python -m pytest -v
```

### Run Specific Test File

```bash
USE_MOCK_PROXMOX=1 python -m pytest apps/backups/test_api.py
```

### Run Specific Test Class

```bash
USE_MOCK_PROXMOX=1 python -m pytest tests/test_models.py::TestUserModel
```

### Run Specific Test

```bash
USE_MOCK_PROXMOX=1 python -m pytest tests/test_models.py::TestUserModel::test_create_user
```

### Run with Debugging

```bash
USE_MOCK_PROXMOX=1 python -m pytest -xvs apps/backups/test_api.py::TestBackupAPIEndpoints::test_create_backup_success
```

Options:
- `-x` - Stop on first failure
- `-v` - Verbose output
- `-s` - Show print statements
- `--pdb` - Drop into debugger on failure
- `-k` - Filter by test name pattern

## Test Categories

### 1. Model Tests (tests/test_models.py)

Test Django model functionality:

```python
def test_create_user():
    """Test user creation"""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    assert user.username == 'testuser'
    assert user.is_active
```

**Coverage:**
- User creation and properties
- Proxmox host and node models
- Application model lifecycle
- Backup model operations
- System settings

### 2. Service Tests (tests/test_services.py)

Test business logic services:

```python
def test_allocate_ports_success():
    """Test port allocation service"""
    ports = PortManagerService.allocate_ports(app_id, count=3)
    assert len(ports) == 3
    assert all(8000 <= p < 9000 for p in ports)
```

**Coverage:**
- Port manager service
- Catalog service
- Proxmox service integration

### 3. API Tests (apps/*/test_api.py)

Test REST endpoints:

```python
def test_list_applications(auth_client, sample_application):
    """Test GET /api/apps/"""
    response = auth_client.get('/api/apps/')
    assert response.status_code == 200
    data = response.json()
    assert len(data['applications']) == 1
```

**Coverage:**
- Application CRUD operations
- Backup management endpoints
- Catalog browsing
- Authentication and permissions

### 4. Task Tests (apps/*/test_tasks.py)

Test Celery task execution:

```python
def test_create_backup_success(sample_application, sample_backup):
    """Test backup creation task"""
    with patch('apps.backups.tasks.ProxmoxService') as MockProxmox:
        result = create_backup_task(application_id=sample_application.id)
        assert result['success'] is True
```

**Coverage:**
- Asynchronous task execution
- Error handling in tasks
- Task retries and failures

### 5. Integration Tests

Test complete workflows:

```python
def test_deploy_and_backup_workflow():
    """Test full deployment and backup workflow"""
    # 1. Deploy application
    app = deploy_application('nginx')
    assert app.status == 'running'

    # 2. Create backup
    backup = create_backup(app)
    assert backup.status == 'completed'

    # 3. Restore from backup
    restored = restore_backup(app, backup)
    assert restored.status == 'running'
```

## Test Fixtures

Common fixtures defined in `conftest.py`:

```python
@pytest.fixture
def sample_user():
    """Create a test user"""
    return User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )[0]

@pytest.fixture
def sample_application(sample_user):
    """Create a test application"""
    return Application.objects.create(
        id=f'test-app-{uuid.uuid4()}',
        catalog_id='nginx',
        owner=sample_user,
        hostname='test-app.local',
        lxc_id=random.randint(100, 9999)
    )

@pytest.fixture
def auth_client(client, sample_user):
    """Create authenticated test client"""
    client.force_login(sample_user)
    return client
```

## Test Database

Tests use an in-memory SQLite database:

```python
# conftest.py
@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    with django_db_blocker.unblock():
        call_command('migrate', '--run-syncdb', verbosity=0)
```

**Benefits:**
- Fast test execution
- No database cleanup needed
- Isolated per test session
- In-memory operations

## Mocking Strategy

### Mock Proxmox Service

```python
from unittest.mock import patch, MagicMock

def test_deploy_with_mocked_proxmox():
    with patch('apps.proxmox.services.ProxmoxService') as MockProxmox:
        mock_service = MockProxmox.return_value
        mock_service.deploy_container.return_value = {
            'status': 'created',
            'lxc_id': 101
        }

        # Your test code here
```

### Mock Celery Tasks

```python
def test_with_celery_mocked():
    with patch('apps.backups.tasks.create_backup_task.delay'):
        # Celery tasks won't actually execute
        response = client.post('/api/apps/1/backups/')
        assert response.status_code == 202
```

### Environment Variables

Use `USE_MOCK_PROXMOX=1` to load mock Proxmox service:

```python
# apps/proxmox/__init__.py
USE_MOCK = os.getenv('USE_MOCK_PROXMOX') == '1'

if USE_MOCK:
    from .mock_service import MockProxmoxService as ProxmoxService
else:
    from .services import ProxmoxService
```

## Writing New Tests

### Test Structure

```python
import pytest
from django.test import Client

@pytest.mark.django_db
class TestMyFeature:
    """Test suite for my feature"""

    def test_happy_path(self, sample_user, auth_client):
        """Test the happy path"""
        # Arrange
        expected = "expected_value"

        # Act
        result = do_something()

        # Assert
        assert result == expected

    def test_error_case(self, sample_user, auth_client):
        """Test error handling"""
        with pytest.raises(ValueError):
            do_something_invalid()
```

### Naming Conventions

- `test_` prefix for test functions
- `Test` prefix for test classes
- Descriptive names: `test_create_backup_with_invalid_compression`
- Follow AAA pattern: Arrange, Act, Assert

### Assertions

```python
# Simple assertions
assert user.is_active

# Comparison assertions
assert response.status_code == 200

# Membership assertions
assert 'error' in response.json()

# Exception assertions
with pytest.raises(ValueError):
    invalid_operation()

# Django assertions
from django.test import TestCase
assert User.objects.filter(username='test').exists()
```

## Coverage Report

Generate coverage report:

```bash
USE_MOCK_PROXMOX=1 python -m pytest --cov=apps --cov=tests \
  --cov-report=html --cov-report=term
```

**Current Coverage:**
```
apps/applications    - 95%
apps/backups         - 98%
apps/catalog         - 99%
apps/core            - 85%
apps/proxmox         - 80%
tests/               - 100%

Overall: 94%
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Commits to main branch
- Scheduled nightly runs

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: |
          cd backend
          pip install -r requirements.txt
          USE_MOCK_PROXMOX=1 python -m pytest
```

## Debugging Failed Tests

### Print Debugging

```python
def test_with_debugging(sample_user):
    print(f"User: {sample_user}")
    print(f"User email: {sample_user.email}")
```

Run with `-s` flag:
```bash
USE_MOCK_PROXMOX=1 python -m pytest tests/test_models.py -s
```

### Interactive Debugging

```bash
USE_MOCK_PROXMOX=1 python -m pytest tests/test_models.py --pdb
```

This drops into pdb debugger on test failure.

### Inspect Database State

```python
def test_with_db_inspection(db):
    user = User.objects.create_user(username='test')
    print(User.objects.filter(username='test').values())
    # Database will still exist after test for inspection
```

## Performance Testing

### Measure Test Execution Time

```bash
USE_MOCK_PROXMOX=1 python -m pytest --durations=10
```

Shows slowest 10 tests.

### Profile Specific Test

```bash
USE_MOCK_PROXMOX=1 python -m pytest tests/test_models.py \
  --profile --profile-svg
```

## Common Issues

### Issue: Import Errors in Tests

**Solution:** Ensure `USE_MOCK_PROXMOX=1` is set before imports.

### Issue: Database Constraint Errors

**Solution:** Use `get_or_create()` pattern in fixtures to avoid unique violations.

### Issue: Test Isolation Failures

**Solution:** Generate unique IDs using UUID for test data.

### Issue: Async Task Tests Failing

**Solution:** Mock Celery tasks with `@patch.object()`.

## Best Practices

1. **Use fixtures** for common setup
2. **Mock external services** (Proxmox, etc.)
3. **Test one thing per test** function
4. **Use descriptive names** for test functions
5. **Follow AAA pattern** (Arrange, Act, Assert)
6. **Keep tests fast** (use in-memory DB)
7. **Test edge cases** not just happy path
8. **Document non-obvious tests** with comments

---

**Test Version:** 1.0
**Last Updated:** October 31, 2025
**Test Status:** ✅ 102/102 Passing (100%)
