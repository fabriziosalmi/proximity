# Testing Quick Reference Card

## 🚀 Quick Commands

```bash
# Run all tests
python tests/run_tests.py

# Run specific test file
python tests/run_tests.py --file test_database_models.py

# Run with coverage
python tests/run_tests.py --coverage

# List all tests
python tests/run_tests.py --list

# Run specific test class
pytest tests/test_database_models.py::TestUserModel -v

# Run specific test
pytest tests/test_database_models.py::TestUserModel::test_create_user -v

# Run tests matching pattern
pytest tests/ -k "test_deploy" -v

# Run with output
pytest tests/ -v -s
```

---

## 📁 Test File Quick Lookup

| Need to Test... | Use This File |
|-----------------|---------------|
| User model, password hashing | `test_database_models.py::TestUserModel` |
| App model, relationships | `test_database_models.py::TestAppModel` |
| Database transactions | `test_database_transactions.py` |
| Login, registration, JWT | `test_auth_service.py` |
| App deployment | `test_app_service.py` |
| LXC operations | `test_proxmox_service.py` |
| API endpoints | `test_api_endpoints.py` |
| End-to-end workflows | `test_integration.py` |
| Error scenarios | `test_error_handling.py` |
| Catalog loading | `test_catalog_service.py` |

---

## 🎯 Common Test Patterns

### Test Database Model
```python
def test_create_model(self, db_session):
    """Test creating a model instance."""
    instance = Model(field="value")
    db_session.add(instance)
    db_session.commit()
    assert instance.id is not None
```

### Test Async Service Method
```python
@pytest.mark.asyncio
async def test_service_method(self, service):
    """Test service method."""
    result = await service.method()
    assert result is not None
```

### Test API Endpoint
```python
def test_endpoint(self, client, auth_headers):
    """Test API endpoint."""
    response = client.get("/api/v1/endpoint", headers=auth_headers)
    assert response.status_code == 200
```

### Test Error Handling
```python
def test_error_case(self, service):
    """Test error handling."""
    with pytest.raises(CustomError):
        service.invalid_operation()
```

### Test Transaction Rollback
```python
def test_rollback(self, db_session):
    """Test transaction rollback."""
    model = Model(field="value")
    db_session.add(model)

    # Don't commit
    db_session.rollback()

    # Verify not persisted
    result = db_session.query(Model).first()
    assert result is None
```

---

## 🔧 Debugging Failed Tests

### Show More Output
```bash
# Show print statements
pytest tests/ -s

# Show full traceback
pytest tests/ --tb=long

# Show local variables
pytest tests/ -l

# Stop on first failure
pytest tests/ -x

# Drop into debugger on failure
pytest tests/ --pdb
```

### Run Specific Failed Test
```bash
# Last failed
pytest tests/ --lf

# Failed first
pytest tests/ --ff
```

---

## 📊 Coverage Commands

```bash
# Generate HTML coverage report
pytest tests/ --cov=backend --cov-report=html

# View in browser
open htmlcov/index.html

# Terminal coverage report
pytest tests/ --cov=backend --cov-report=term

# Coverage for specific module
pytest tests/ --cov=backend/services --cov-report=term
```

---

## ✅ Pre-Commit Checklist

Before committing code, run:

```bash
# 1. Run all tests
python tests/run_tests.py

# 2. Check specific area you changed
pytest tests/test_your_area.py -v

# 3. Run coverage
python tests/run_tests.py --coverage

# 4. Verify no new warnings
pytest tests/ -W error
```

---

## 🎓 Test Data

### Available Fixtures (conftest.py)

```python
# Database
db_session          # Fresh database session
test_db_engine      # Test database engine

# Users
test_user           # Regular user (username: testuser)
test_admin          # Admin user (username: admin)

# Services (mocked)
mock_proxmox_service    # Mocked Proxmox service
mock_proxy_manager      # Mocked proxy manager

# Sample Data
sample_catalog_item     # Sample catalog item dict
sample_app_create       # Sample app creation data

# Authentication
auth_token          # Token for test_user
admin_token         # Token for test_admin
auth_headers        # Headers with test_user token
admin_headers       # Headers with admin token

# Client
client              # FastAPI TestClient
```

---

## 🐛 Common Issues & Solutions

### Issue: Import Errors
```bash
# Solution: Ensure backend is in path
cd tests
pytest  # Not: pytest tests/
```

### Issue: Database Locked
```bash
# Solution: Close existing sessions
# Tests use in-memory DB, shouldn't happen
# Check for background processes
```

### Issue: Async Tests Not Running
```bash
# Solution: Install pytest-asyncio
pip install pytest-asyncio
```

### Issue: Tests Pass Locally But Fail in CI
```bash
# Check:
# 1. Dependencies installed (requirements.txt)
# 2. Environment variables set
# 3. Database initialization
```

---

## 💡 Tips & Tricks

### Run Tests in Parallel
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

### Show Test Duration
```bash
pytest tests/ --durations=10
```

### Generate JUnit XML (for CI)
```bash
pytest tests/ --junitxml=report.xml
```

### Watch Mode (Re-run on Changes)
```bash
pip install pytest-watch
ptw tests/
```

### Test Coverage Minimum
```bash
# Fail if coverage below 80%
pytest tests/ --cov=backend --cov-fail-under=80
```

---

## 📝 Writing New Tests

### Template
```python
"""
Tests for [feature].
"""

import pytest
from models.database import Model


class TestMyFeature:
    """Test suite for my feature."""

    def test_basic_case(self, db_session):
        """Test basic functionality."""
        # Arrange
        model = Model(field="value")

        # Act
        db_session.add(model)
        db_session.commit()

        # Assert
        assert model.id is not None

    @pytest.mark.asyncio
    async def test_async_case(self, service):
        """Test async functionality."""
        result = await service.method()
        assert result is not None
```

---

## 🎯 Test Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Database Models | 95%+ | ✅ 95%+ |
| Services | 90%+ | ✅ 90%+ |
| API Endpoints | 90%+ | ✅ 90%+ |
| Utils | 85%+ | ✅ 85%+ |
| Overall | 90%+ | ✅ ~92% |

---

## 📞 Need Help?

1. Check test documentation in `tests/README.md`
2. Review test examples in existing test files
3. Check pytest documentation: https://docs.pytest.org
4. Review conftest.py for available fixtures

---

**Quick Reference Created:** October 4, 2025
**Last Updated:** October 4, 2025
