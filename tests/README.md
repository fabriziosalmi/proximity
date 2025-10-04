# Proximity Test Suite

Comprehensive test suite for the Proximity application.

## Test Files

### Core Infrastructure Tests
- **`conftest.py`** - Pytest configuration and shared fixtures
- **`test_database_models.py`** - Database model tests (User, App, DeploymentLog, AuditLog)
- **`test_database_transactions.py`** - Transaction safety, ACID properties, rollback scenarios

### Service Layer Tests
- **`test_auth_service.py`** - Authentication and authorization tests
- **`test_app_service.py`** - Application deployment and management tests
- **`test_proxmox_service.py`** - Proxmox integration tests
- **`test_catalog_service.py`** - Catalog loading, filtering, and management tests

### API & Integration Tests
- **`test_api_endpoints.py`** - API endpoint tests
- **`test_integration.py`** - End-to-end integration tests
- **`test_error_handling.py`** - Error handling, edge cases, and boundary conditions

### Utilities
- **`run_tests.py`** - Main test runner script with coverage support

## Quick Start

### Install Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov
```

### Run All Tests

```bash
python tests/run_tests.py
```

or

```bash
cd tests
pytest
```

### Run Specific Test File

```bash
python tests/run_tests.py --file test_auth_service.py
```

### Run with Coverage

```bash
python tests/run_tests.py --coverage
```

### List All Tests

```bash
python tests/run_tests.py --list
```

## Test Coverage

The test suite covers:

### Database Models & Transactions (NEW!)
- User model (creation, constraints, password hashing)
- App model (CRUD, relationships, JSON fields)
- DeploymentLog model (logging, relationships)
- AuditLog model (audit trail)
- ACID transaction properties
- Atomicity and rollback scenarios
- Database constraints (unique, foreign keys)
- Cascade deletes
- Transaction isolation

### Authentication & Authorization
- JWT token creation and verification
- User registration and login
- Password hashing and verification
- Role-based access control
- Audit logging
- Token expiration
- Inactive user handling

### Application Management
- Catalog browsing and item retrieval
- Catalog loading from files
- Catalog caching
- Application deployment workflow
- App lifecycle (start/stop/restart/delete)
- Reverse proxy configuration
- Error handling and cleanup
- Deployment logging

### Proxmox Integration
- Connection testing
- LXC container operations
- SSH command execution
- Network configuration
- Resource management
- Error handling

### API Endpoints
- Health checks
- Authentication endpoints
- System information
- Application CRUD operations
- Settings management
- CORS handling
- Error responses

### Error Handling & Edge Cases (NEW!)
- Authentication errors (invalid credentials, inactive users, expired tokens)
- Deployment failures (Proxmox errors, network failures)
- Invalid input validation
- Boundary conditions (max values, unicode, special characters)
- Concurrent operations
- Resource conflicts

### Integration Tests
- Complete deployment workflows
- Full app lifecycle (deploy → start → stop → delete)
- Authentication flow (register → login → access → logout)
- Catalog browsing
- System monitoring
- Error handling
- Data consistency
- CORS functionality

## Fixtures

Available pytest fixtures (defined in `conftest.py`):

- `db_session` - Fresh database session for each test
- `test_user` - Standard test user
- `test_admin` - Admin test user
- `mock_proxmox_service` - Mocked ProxmoxService
- `mock_proxy_manager` - Mocked ReverseProxyManager
- `sample_catalog_item` - Sample catalog data
- `sample_app_create` - Sample app deployment data

## Test Database

Tests use an in-memory SQLite database that is created fresh for each test session. No persistent data is stored.

## Writing New Tests

### Unit Test Example

```python
import pytest
from services.my_service import MyService

class TestMyService:
    def test_my_function(self, db_session):
        service = MyService(db=db_session)
        result = service.my_function()
        assert result is not None
```

### API Test Example

```python
def test_my_endpoint(self, client, auth_headers):
    response = client.get("/api/v1/my/endpoint", headers=auth_headers)
    assert response.status_code == 200
    assert "data" in response.json()
```

### Async Test Example

```python
@pytest.mark.asyncio
async def test_async_function(self, mock_proxmox_service):
    result = await mock_proxmox_service.get_nodes()
    assert len(result) > 0
```

## CI/CD Integration

The test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install pytest pytest-asyncio pytest-cov
    python tests/run_tests.py
```

## Troubleshooting

### Import Errors

If you encounter import errors, ensure the backend path is correctly added to sys.path in the test files.

### Async Warnings

The test suite uses `pytest-asyncio` for async tests. Ensure it's installed to avoid warnings.

### Database Errors

Each test gets a fresh database session. If you see database-related errors, check that fixtures are properly used.

## Best Practices

1. **Isolation** - Each test should be independent
2. **Mocking** - Use mocks for external services (Proxmox, network calls)
3. **Cleanup** - Fixtures handle cleanup automatically
4. **Assertions** - Use clear, specific assertions
5. **Documentation** - Add docstrings to test functions

## Performance

The test suite is designed to run quickly:
- Uses in-memory database
- Mocks external services
- Parallel test execution supported with `pytest-xdist`

```bash
pip install pytest-xdist
pytest -n auto  # Run tests in parallel
```
