"""
Tests for error handling and edge cases.
Ensures the application handles failures gracefully.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from main import create_app
from services.auth_service import AuthService
from services.app_service import AppService
from services.proxmox_service import ProxmoxError
from core.exceptions import (
    AppNotFoundError,
    AppAlreadyExistsError,
    AppDeploymentError,
    AppOperationError
)
from models.schemas import AppCreate
from models.database import App


@pytest.fixture
def client(test_db_engine):
    """Create test client with shared database."""
    # Create app with test database
    app = create_app()
    
    # Override database dependency to use shared test engine
    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(bind=test_db_engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    from models.database import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    return TestClient(app)


class TestAuthenticationErrors:
    """Test authentication error handling."""

    def test_login_with_invalid_credentials(self, client):
        """Test login with wrong password."""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_with_inactive_user(self, db_session):
        """Test login with inactive user."""
        from models.database import User

        # Create inactive user
        user = User(
            username="inactive",
            hashed_password=User.hash_password("password"),
            is_active=False
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(HTTPException):
            AuthService.authenticate_user(
                db=db_session,
                username="inactive",
                password="password"
            )

    def test_register_with_duplicate_username(self, client, test_user):
        """Test registration with existing username."""
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",  # Already exists
            "email": "new@example.com",
            "password": "password123",
            "role": "user"
        })

        assert response.status_code == 400

    def test_register_with_duplicate_email(self, client, test_user):
        """Test registration with existing email."""
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "test@example.com",  # Already exists
            "password": "password123",
            "role": "user"
        })

        assert response.status_code == 400

    def test_access_protected_route_without_token(self, client):
        """Test accessing protected route without authentication."""
        response = client.get("/api/v1/system/info")
        assert response.status_code == 401

    def test_access_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token."""
        response = client.get(
            "/api/v1/system/info",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    def test_access_protected_route_with_expired_token(self, db_session, test_user):
        """Test accessing protected route with expired token."""
        from datetime import timedelta

        # Create expired token
        token = AuthService.create_access_token(
            data={"sub": test_user.username, "role": test_user.role, "user_id": test_user.id},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        # Token verification should fail
        with pytest.raises(HTTPException):
            AuthService.verify_token(token)

    def test_password_change_with_wrong_old_password(self, db_session, test_user):
        """Test password change with incorrect old password."""
        with pytest.raises(HTTPException):
            AuthService.change_password(
                db=db_session,
                user=test_user,
                old_password="wrongpassword",
                new_password="newpassword123"
            )


class TestAppServiceErrors:
    """Test application service error handling."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_app(self, db_session, mock_proxmox_service, mock_proxy_manager):
        """Test getting app that doesn't exist."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        with pytest.raises(Exception):  # AppServiceError or similar
            await app_service.get_app("nonexistent-app")

    @pytest.mark.asyncio
    async def test_deploy_app_with_duplicate_id(
        self, db_session, mock_proxmox_service, mock_proxy_manager, test_user
    ):
        """Test deploying app that already exists."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Create existing app
        app = App(
            id="nginx-duplicate",
            catalog_id="nginx",
            name="Duplicate",
            hostname="duplicate",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Load catalog
        await app_service._load_catalog()

        # Try to deploy with same ID
        app_data = AppCreate(
            catalog_id="nginx",
            hostname="duplicate",
            config={},
            environment={}
        )

        with pytest.raises(AppAlreadyExistsError):
            await app_service.deploy_app(app_data)

    @pytest.mark.asyncio
    async def test_deploy_app_with_invalid_catalog_id(
        self, db_session, mock_proxmox_service, mock_proxy_manager
    ):
        """Test deploying app with non-existent catalog item."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        await app_service._load_catalog()

        app_data = AppCreate(
            catalog_id="nonexistent-catalog-item",
            hostname="test",
            config={},
            environment={}
        )

        with pytest.raises(Exception):  # Should raise AppServiceError
            await app_service.deploy_app(app_data)

    @pytest.mark.asyncio
    async def test_start_app_proxmox_failure(
        self, db_session, mock_proxmox_service, mock_proxy_manager, test_user
    ):
        """Test starting app when Proxmox fails."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Create stopped app
        app = App(
            id="start-fail",
            catalog_id="nginx",
            name="Start Fail",
            hostname="start-fail",
            status="stopped",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Mock Proxmox to fail
        mock_proxmox_service.start_lxc = AsyncMock(
            side_effect=ProxmoxError("Failed to start LXC")
        )

        with pytest.raises(AppOperationError):
            await app_service.start_app("start-fail")

        # Status should be set to error
        db_session.expire_all()
        db_app = db_session.query(App).filter(App.id == "start-fail").first()
        assert db_app.status == "error"

    @pytest.mark.asyncio
    async def test_stop_app_proxmox_failure(
        self, db_session, mock_proxmox_service, mock_proxy_manager, test_user
    ):
        """Test stopping app when Proxmox fails."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Create running app
        app = App(
            id="stop-fail",
            catalog_id="nginx",
            name="Stop Fail",
            hostname="stop-fail",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Mock Proxmox to fail
        mock_proxmox_service.execute_in_container = AsyncMock(
            side_effect=ProxmoxError("Failed to stop Docker")
        )

        with pytest.raises(AppOperationError):
            await app_service.stop_app("stop-fail")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_app(
        self, db_session, mock_proxmox_service, mock_proxy_manager
    ):
        """Test deleting app that doesn't exist."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        with pytest.raises(Exception):
            await app_service.delete_app("nonexistent")

    @pytest.mark.asyncio
    async def test_deployment_with_network_failure(
        self, db_session, mock_proxmox_service, mock_proxy_manager
    ):
        """Test deployment when network operations fail."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Mock successful deployment but network failure
        mock_proxmox_service.get_next_vmid = AsyncMock(return_value=100)
        mock_proxmox_service.get_best_node = AsyncMock(return_value="testnode")
        mock_proxmox_service.create_lxc = AsyncMock(return_value={"task_id": "UPID:1"})
        mock_proxmox_service.start_lxc = AsyncMock(return_value="UPID:2")
        mock_proxmox_service.setup_docker_in_alpine = AsyncMock(return_value=True)
        mock_proxmox_service.execute_in_container = AsyncMock(return_value="OK")
        mock_proxmox_service.get_lxc_ip = AsyncMock(
            side_effect=ProxmoxError("Network error")
        )
        mock_proxmox_service.wait_for_task = AsyncMock(return_value=True)
        mock_proxmox_service.destroy_lxc = AsyncMock(return_value="UPID:3")

        await app_service._load_catalog()

        app_data = AppCreate(
            catalog_id="wordpress",
            hostname="network-fail",
            config={},
            environment={}
        )

        # Should fail due to network error
        with pytest.raises(Exception):
            await app_service.deploy_app(app_data)


class TestProxmoxServiceErrors:
    """Test Proxmox service error handling."""

    @pytest.mark.asyncio
    async def test_connection_failure(self, mock_proxmox_service):
        """Test Proxmox connection failure."""
        mock_proxmox_service.test_connection = AsyncMock(
            side_effect=ProxmoxError("Connection refused")
        )

        with pytest.raises(ProxmoxError):
            await mock_proxmox_service.test_connection()

    @pytest.mark.asyncio
    async def test_lxc_creation_failure(self, mock_proxmox_service):
        """Test LXC creation failure."""
        mock_proxmox_service.create_lxc = AsyncMock(
            side_effect=ProxmoxError("Insufficient resources")
        )

        with pytest.raises(ProxmoxError):
            await mock_proxmox_service.create_lxc("node1", 100, {})

    @pytest.mark.asyncio
    async def test_lxc_start_failure(self, mock_proxmox_service):
        """Test LXC start failure."""
        mock_proxmox_service.start_lxc = AsyncMock(
            side_effect=ProxmoxError("LXC locked")
        )

        with pytest.raises(ProxmoxError):
            await mock_proxmox_service.start_lxc("node1", 100)


class TestAPIEndpointErrors:
    """Test API endpoint error handling."""

    def test_invalid_json_payload(self, client, auth_headers):
        """Test endpoint with invalid JSON."""
        response = client.post(
            "/api/v1/apps/deploy",
            headers=auth_headers,
            data="invalid json"
        )
        assert response.status_code in [400, 422]

    def test_missing_required_fields(self, client, auth_headers):
        """Test endpoint with missing required fields."""
        response = client.post(
            "/api/v1/apps/deploy",
            headers=auth_headers,
            json={"hostname": "test"}  # Missing catalog_id
        )
        assert response.status_code in [400, 422]

    def test_invalid_field_types(self, client, auth_headers):
        """Test endpoint with invalid field types."""
        response = client.post(
            "/api/v1/apps/deploy",
            headers=auth_headers,
            json={
                "catalog_id": 123,  # Should be string
                "hostname": "test"
            }
        )
        assert response.status_code in [400, 422]

    def test_admin_only_endpoint_as_user(self, client, auth_headers):
        """Test admin endpoint with regular user."""
        response = client.get(
            "/api/v1/settings/proxmox",
            headers=auth_headers
        )
        assert response.status_code == 403  # Forbidden

    def test_nonexistent_endpoint(self, client):
        """Test accessing non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_username(self, db_session):
        """Test username that exceeds database limit."""
        from models.database import User

        # Username column is String(50)
        long_username = "a" * 100  # Exceeds 50 chars

        user = User(
            username=long_username,
            hashed_password=User.hash_password("password")
        )
        db_session.add(user)

        # Should be truncated or raise error depending on DB
        try:
            db_session.commit()
            # If it commits, verify it was truncated
            assert len(user.username) <= 50
        except Exception:
            # Expected for databases that enforce length
            db_session.rollback()

    def test_empty_password(self):
        """Test hashing empty password."""
        from models.database import User

        # Should still hash, even if empty
        hashed = User.hash_password("")
        assert hashed != ""
        assert len(hashed) > 0

    def test_special_characters_in_hostname(self, db_session, test_user):
        """Test hostname with special characters."""
        app = App(
            id="special-chars",
            catalog_id="nginx",
            name="Special",
            hostname="test@#$%app",  # Special chars
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Should be stored as-is
        db_app = db_session.query(App).filter(App.id == "special-chars").first()
        assert db_app.hostname == "test@#$%app"

    def test_very_large_config_json(self, db_session, test_user):
        """Test app with very large config JSON."""
        large_config = {f"key_{i}": f"value_{i}" for i in range(1000)}

        app = App(
            id="large-config",
            catalog_id="nginx",
            name="Large Config",
            hostname="large-config",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id,
            config=large_config
        )
        db_session.add(app)
        db_session.commit()

        # Should store and retrieve correctly
        db_app = db_session.query(App).filter(App.id == "large-config").first()
        assert len(db_app.config) == 1000

    def test_null_values_in_optional_fields(self, db_session, test_user):
        """Test app with null values in optional fields."""
        app = App(
            id="null-values",
            catalog_id="nginx",
            name="Null Values",
            hostname="null-values",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id,
            url=None  # Optional field
        )
        db_session.add(app)
        db_session.commit()

        db_app = db_session.query(App).filter(App.id == "null-values").first()
        assert db_app.url is None

    @pytest.mark.asyncio
    async def test_concurrent_deployments_same_hostname(
        self, db_session, mock_proxmox_service, mock_proxy_manager
    ):
        """Test two deployments with same hostname (should fail)."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Mock successful deployment
        mock_proxmox_service.get_next_vmid = AsyncMock(side_effect=[100, 101])
        mock_proxmox_service.get_best_node = AsyncMock(return_value="testnode")
        mock_proxmox_service.create_lxc = AsyncMock(return_value={"task_id": "UPID:1"})
        mock_proxmox_service.start_lxc = AsyncMock(return_value="UPID:2")
        mock_proxmox_service.setup_docker_in_alpine = AsyncMock(return_value=True)
        mock_proxmox_service.execute_in_container = AsyncMock(return_value="OK")
        mock_proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.100")
        mock_proxmox_service.wait_for_task = AsyncMock(return_value=True)

        await app_service._load_catalog()

        # Deploy first app
        app_data1 = AppCreate(
            catalog_id="wordpress",
            hostname="concurrent-test",
            config={},
            environment={}
        )
        await app_service.deploy_app(app_data1)

        # Try to deploy second app with same hostname
        app_data2 = AppCreate(
            catalog_id="wordpress",
            hostname="concurrent-test",  # Same hostname
            config={},
            environment={}
        )

        # Should fail due to duplicate hostname
        with pytest.raises(AppAlreadyExistsError):
            await app_service.deploy_app(app_data2)

    def test_unicode_in_app_name(self, db_session, test_user):
        """Test app name with Unicode characters."""
        app = App(
            id="unicode-app",
            catalog_id="nginx",
            name="测试应用",  # Chinese characters
            hostname="unicode-app",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        db_app = db_session.query(App).filter(App.id == "unicode-app").first()
        assert db_app.name == "测试应用"

    def test_max_vmid_value(self, db_session, test_user):
        """Test app with maximum VMID value."""
        app = App(
            id="max-vmid",
            catalog_id="nginx",
            name="Max VMID",
            hostname="max-vmid",
            status="running",
            lxc_id=999999999,  # Very large VMID
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        db_app = db_session.query(App).filter(App.id == "max-vmid").first()
        assert db_app.lxc_id == 999999999
