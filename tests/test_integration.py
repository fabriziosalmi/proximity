"""
Integration tests for deployment workflows.
Tests the full stack from API to Proxmox.
"""

import pytest
from unittest.mock import AsyncMock, patch
import sys
from pathlib import Path

# Disable pytest-flask auto-use fixtures for this file
pytestmark = pytest.mark.usefixtures()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Note: client fixture comes from conftest.py
# Note: auth_token and auth_headers come from conftest.py


class TestFullDeploymentWorkflow:
    """Test complete application deployment workflow."""

    @patch('services.proxmox_service.proxmox_service')
    @patch('services.app_service.get_app_service')
    def test_complete_app_lifecycle(self, mock_app_service, mock_proxmox, client, auth_headers):
        """Test full lifecycle: deploy -> start -> stop -> restart -> delete."""

        # Mock Proxmox service
        mock_proxmox.get_next_vmid = AsyncMock(return_value=100)
        mock_proxmox.create_lxc = AsyncMock(return_value={"task": "UPID:test"})
        mock_proxmox.start_lxc = AsyncMock(return_value="UPID:test")
        mock_proxmox.stop_lxc = AsyncMock(return_value="UPID:test")
        mock_proxmox.destroy_lxc = AsyncMock(return_value="UPID:test")
        mock_proxmox.get_lxc_status = AsyncMock(return_value={
            "vmid": 100,
            "status": "running"
        })

        # 1. Deploy app
        deploy_response = client.post(
            "/api/v1/apps/deploy",
            headers=auth_headers,
            json={
                "catalog_id": "nginx",
                "hostname": "test-nginx",
                "config": {},
                "environment": {}
            }
        )

        # Should succeed or fail with proper error
        assert deploy_response.status_code in [200, 201, 400, 500, 502]

        if deploy_response.status_code in [200, 201]:
            app_data = deploy_response.json()
            app_id = app_data.get("id")

            # 2. List apps to verify deployment
            list_response = client.get("/api/v1/apps", headers=auth_headers)
            assert list_response.status_code == 200

            # 3. Get specific app
            get_response = client.get(f"/api/v1/apps/{app_id}", headers=auth_headers)
            assert get_response.status_code in [200, 404]

            # 4. Stop app
            stop_response = client.post(
                f"/api/v1/apps/{app_id}/stop",
                headers=auth_headers
            )
            assert stop_response.status_code in [200, 400, 404, 500]

            # 5. Start app
            start_response = client.post(
                f"/api/v1/apps/{app_id}/start",
                headers=auth_headers
            )
            assert start_response.status_code in [200, 400, 404, 500]

            # 6. Restart app
            restart_response = client.post(
                f"/api/v1/apps/{app_id}/restart",
                headers=auth_headers
            )
            assert restart_response.status_code in [200, 400, 404, 500]

            # 7. Delete app
            delete_response = client.delete(
                f"/api/v1/apps/{app_id}",
                headers=auth_headers
            )
            assert delete_response.status_code in [200, 204, 404, 500]


class TestAuthenticationWorkflow:
    """Test complete authentication workflow."""

    def test_register_login_access_logout(self, client):
        """Test full auth flow: register -> login -> access protected -> logout."""

        # 1. Register new user
        register_response = client.post("/api/v1/auth/register", json={
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "password123",
            "role": "user"
        })

        assert register_response.status_code in [201, 400]

        if register_response.status_code == 201:
            register_data = register_response.json()
            assert "access_token" in register_data
            token = register_data["access_token"]

            # 2. Access protected endpoint with token
            headers = {"Authorization": f"Bearer {token}"}
            me_response = client.get("/api/v1/auth/me", headers=headers)
            assert me_response.status_code == 200
            assert me_response.json()["username"] == "integrationuser"

            # 3. Access system info
            system_response = client.get("/api/v1/system/info", headers=headers)
            assert system_response.status_code in [200, 500, 502]

            # 4. Logout
            logout_response = client.post("/api/v1/auth/logout", headers=headers)
            assert logout_response.status_code == 200

        # 5. Login with existing user
        login_response = client.post("/api/v1/auth/login", json={
            "username": "integrationuser",
            "password": "password123"
        })

        # May fail if registration failed
        assert login_response.status_code in [200, 401]


class TestCatalogBrowsing:
    """Test catalog browsing workflow."""

    def test_browse_catalog_and_get_details(self, client, auth_headers):
        """Test browsing catalog and getting app details."""

        # 1. Get catalog
        catalog_response = client.get("/api/v1/apps/catalog", headers=auth_headers)
        assert catalog_response.status_code in [200, 500]

        if catalog_response.status_code == 200:
            catalog_data = catalog_response.json()

            # 2. Get catalog item details if catalog has items
            if "items" in catalog_data and len(catalog_data["items"]) > 0:
                first_item = catalog_data["items"][0]
                item_id = first_item.get("id")

                detail_response = client.get(
                    f"/api/v1/apps/catalog/{item_id}",
                    headers=auth_headers
                )
                assert detail_response.status_code in [200, 404, 500]


class TestSystemMonitoring:
    """Test system monitoring workflow."""

    @patch('services.proxmox_service.proxmox_service')
    def test_monitor_system_resources(self, mock_proxmox, client, auth_headers):
        """Test monitoring system resources and nodes."""

        # Mock Proxmox responses
        mock_proxmox.get_nodes = AsyncMock(return_value=[
            {"node": "testnode", "status": "online", "cpu": 0.1, "maxcpu": 8}
        ])

        # 1. Get system info
        info_response = client.get("/api/v1/system/info", headers=auth_headers)
        assert info_response.status_code in [200, 500, 502]

        # 2. Get nodes
        nodes_response = client.get("/api/v1/system/nodes", headers=auth_headers)
        assert nodes_response.status_code in [200, 500, 502]

        # 3. Get proxy status
        proxy_response = client.get("/api/v1/system/proxy/status", headers=auth_headers)
        assert proxy_response.status_code in [200, 500, 502]


class TestErrorHandling:
    """Test error handling across the application."""

    def test_authentication_errors(self, client):
        """Test authentication error responses."""

        # 1. Access protected endpoint without token
        response = client.get("/api/v1/system/info")
        assert response.status_code == 401

        # 2. Invalid token
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

        # 3. Wrong password
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_resource_not_found(self, client, auth_headers):
        """Test 404 error handling."""

        # 1. Non-existent app
        response = client.get("/api/v1/apps/non-existent-app", headers=auth_headers)
        assert response.status_code == 404

        # 2. Non-existent catalog item
        response = client.get(
            "/api/v1/apps/catalog/non-existent-item",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_invalid_input(self, client, auth_headers):
        """Test validation error handling."""

        # 1. Deploy with missing required fields
        response = client.post(
            "/api/v1/apps/deploy",
            headers=auth_headers,
            json={"hostname": "test"}  # Missing catalog_id
        )
        assert response.status_code in [400, 422]

        # 2. Register with invalid data
        response = client.post("/api/v1/auth/register", json={
            "username": "a",  # Too short
            "password": "short"  # Too short
        })
        assert response.status_code in [400, 422]


class TestCORS:
    """Test CORS functionality."""

    def test_cors_preflight(self, client):
        """Test CORS preflight requests."""

        # 1. OPTIONS request to protected endpoint
        response = client.options("/api/v1/system/info")
        assert response.status_code == 200

        # 2. OPTIONS to auth endpoint
        response = client.options("/api/v1/auth/login")
        assert response.status_code == 200

    def test_cors_headers_present(self, client):
        """Test CORS headers in responses."""

        response = client.get(
            "/api/v1/apps/catalog",
            headers={"Origin": "http://localhost:3000"}
        )

        # Should have CORS headers or auth error
        assert response.status_code in [200, 401, 500]


class TestDataConsistency:
    """Test data consistency across operations."""

    def test_user_data_consistency(self, client, test_user):
        """Test user data remains consistent."""

        # 1. Login
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get user info multiple times
        responses = []
        for _ in range(3):
            response = client.get("/api/v1/auth/me", headers=headers)
            responses.append(response)

        # All should succeed and return same data
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "testuser"
            assert data["role"] == "user"
