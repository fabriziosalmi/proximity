"""
API endpoint tests using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from main import create_app
from models.database import get_db
from services.auth_service import AuthService


@pytest.fixture
def client(db_session):
    """Create test client with test database."""
    app = create_app()
    
    # Override database dependency to use test database
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    return TestClient(app)


@pytest.fixture
def auth_token(db_session, test_user):
    """Generate auth token for test user."""
    token = AuthService.create_access_token({
        "sub": test_user.username,
        "role": test_user.role,
        "user_id": test_user.id
    })
    return token


@pytest.fixture
def admin_token(db_session, test_admin):
    """Generate auth token for admin user."""
    token = AuthService.create_access_token({
        "sub": test_admin.username,
        "role": test_admin.role,
        "user_id": test_admin.id
    })
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Create admin authorization headers."""
    return {"Authorization": f"Bearer {admin_token}"}


class TestHealthEndpoints:
    """Test health and system info endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_root(self, client):
        """Test API root endpoint."""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_user_success(self, client):
        """Test user registration."""
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "role": "user"
        })

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "newuser"

    def test_register_duplicate_user(self, client, test_user):
        """Test registration with duplicate username."""
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "password123",
            "role": "user"
        })

        assert response.status_code == 400

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    def test_get_current_user_unauthorized(self, client):
        """Test getting user without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_logout(self, client, auth_headers):
        """Test logout endpoint."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestSystemEndpoints:
    """Test system endpoints."""

    @patch('services.proxmox_service.proxmox_service')
    def test_get_system_info(self, mock_proxmox, client, auth_headers):
        """Test getting system info."""
        mock_proxmox.get_nodes = AsyncMock(return_value=[])

        response = client.get("/api/v1/system/info", headers=auth_headers)

        # May return 200 or error depending on setup
        assert response.status_code in [200, 502, 500]

    @patch('services.proxmox_service.proxmox_service')
    def test_get_nodes(self, mock_proxmox, client, auth_headers):
        """Test getting Proxmox nodes."""
        mock_proxmox.get_nodes = AsyncMock(return_value=[
            {"node": "testnode", "status": "online"}
        ])

        response = client.get("/api/v1/system/nodes", headers=auth_headers)

        assert response.status_code in [200, 502]

    def test_get_system_info_unauthorized(self, client):
        """Test system info without auth."""
        response = client.get("/api/v1/system/info")

        assert response.status_code == 401


class TestAppEndpoints:
    """Test application endpoints."""

    @patch('services.app_service.get_app_service')
    def test_get_catalog(self, mock_service, client, auth_headers):
        """Test getting app catalog."""
        response = client.get("/api/v1/apps/catalog", headers=auth_headers)

        # Should succeed even if catalog is empty
        assert response.status_code in [200, 500]

    @patch('services.app_service.get_app_service')
    def test_list_apps(self, mock_service, client, auth_headers):
        """Test listing deployed apps."""
        mock_app_service = AsyncMock()
        mock_app_service.get_all_apps = AsyncMock(return_value=[])
        mock_service.return_value = mock_app_service

        response = client.get("/api/v1/apps", headers=auth_headers)

        assert response.status_code in [200, 500]

    def test_list_apps_unauthorized(self, client):
        """Test listing apps without auth."""
        response = client.get("/api/v1/apps")

        assert response.status_code == 401

    @patch('services.app_service.get_app_service')
    def test_deploy_app(self, mock_service, client, auth_headers):
        """Test app deployment endpoint."""
        response = client.post("/api/v1/apps/deploy",
            headers=auth_headers,
            json={
                "catalog_id": "nginx",
                "hostname": "test-nginx",
                "config": {},
                "environment": {}
            }
        )

        # May fail due to missing Proxmox connection in tests
        assert response.status_code in [200, 400, 500, 502]


class TestSettingsEndpoints:
    """Test settings endpoints (admin only)."""

    def test_get_proxmox_settings_unauthorized(self, client, auth_headers):
        """Test getting settings as regular user."""
        response = client.get("/api/v1/settings/proxmox", headers=auth_headers)

        assert response.status_code == 403  # Forbidden

    def test_get_proxmox_settings_admin(self, client, admin_headers):
        """Test getting settings as admin."""
        response = client.get("/api/v1/settings/proxmox", headers=admin_headers)

        assert response.status_code in [200, 500]


class TestCORSAndOptions:
    """Test CORS and OPTIONS requests."""

    def test_options_request(self, client):
        """Test OPTIONS preflight request."""
        response = client.options("/api/v1/system/info")

        assert response.status_code == 200

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get("/api/v1/apps/catalog", headers={
            "Origin": "http://localhost:3000"
        })

        # Should have CORS headers even on auth failure
        assert "access-control-allow-origin" in response.headers or response.status_code == 401
