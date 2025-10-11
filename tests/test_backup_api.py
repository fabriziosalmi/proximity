"""
API tests for backup endpoints.
Tests backup creation, listing, restoration, and deletion via REST API.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from models.database import Backup, App, User
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class TestBackupAPICreate:
    """Test backup creation API."""

    def test_create_backup_success(self, client_with_mock_proxmox, auth_headers, db_session, test_user):
        """Test successful backup creation via API."""
        # Create app
        app = App(
            id="api-test-app",
            catalog_id="nginx",
            name="API Test App",
            hostname="api-test-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Create backup
        response = client_with_mock_proxmox.post(
            "/api/v1/apps/api-test-app/backups",
            headers=auth_headers,
            json={
                "storage": "local",
                "compress": "zstd",
                "mode": "snapshot"
            }
        )

        assert response.status_code == 202  # Accepted (async operation)
        data = response.json()
        assert data["status"] == "creating"
        assert data["app_id"] == "api-test-app"
        assert "backup_id" in data

    def test_create_backup_unauthorized(self, client, db_session, test_user):
        """Test backup creation without authentication."""
        app = App(
            id="unauth-app",
            catalog_id="nginx",
            name="Unauth App",
            hostname="unauth-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        response = client.post(
            "/api/v1/apps/unauth-app/backups",
            json={"storage": "local"}
        )

        assert response.status_code == 401

    def test_create_backup_app_not_found(self, client, auth_headers):
        """Test backup creation for non-existent app."""
        response = client.post(
            "/api/v1/apps/nonexistent-app/backups",
            headers=auth_headers,
            json={"storage": "local"}
        )

        assert response.status_code == 404

    def test_create_backup_invalid_compression(self, client_with_mock_proxmox, auth_headers, db_session, test_user):
        """Test backup creation with invalid compression type."""
        app = App(
            id="compress-app",
            catalog_id="nginx",
            name="Compress App",
            hostname="compress-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        response = client_with_mock_proxmox.post(
            "/api/v1/apps/compress-app/backups",
            headers=auth_headers,
            json={"compress": "invalid"}
        )

        assert response.status_code == 422  # Validation error



class TestBackupAPIList:
    """Test backup listing API."""

    def test_list_backups_success(self, client, auth_headers, db_session, test_user):
        """Test listing backups for an app."""
        # Create app
        app = App(
            id="list-api-app",
            catalog_id="nginx",
            name="List API App",
            hostname="list-api-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Create backups
        for i in range(3):
            backup = Backup(
                app_id="list-api-app",
                filename=f"backup-{i}.tar.zst",
                storage_name="local",
                status="available",
                size_bytes=1000000 * (i + 1)
            )
            db_session.add(backup)
        db_session.commit()

        response = client.get(
            "/api/v1/apps/list-api-app/backups",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "backups" in data
        assert len(data["backups"]) == 3
        assert data["total"] == 3

    def test_list_backups_empty(self, client, auth_headers, db_session, test_user):
        """Test listing backups when none exist."""
        app = App(
            id="empty-api-app",
            catalog_id="nginx",
            name="Empty API App",
            hostname="empty-api-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        response = client.get(
            "/api/v1/apps/empty-api-app/backups",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["backups"]) == 0
        assert data["total"] == 0

    def test_list_backups_app_not_found(self, client, auth_headers):
        """Test listing backups for non-existent app."""
        response = client.get(
            "/api/v1/apps/nonexistent-app/backups",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestBackupAPIGet:
    """Test getting individual backup."""

    def test_get_backup_success(self, client, auth_headers, db_session, test_user):
        """Test getting a specific backup."""
        app = App(
            id="get-api-app",
            catalog_id="nginx",
            name="Get API App",
            hostname="get-api-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="get-api-app",
            filename="specific-backup.tar.zst",
            storage_name="local",
            status="available",
            size_bytes=5000000
        )
        db_session.add(backup)
        db_session.commit()

        response = client.get(
            f"/api/v1/apps/get-api-app/backups/{backup.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == backup.id
        assert data["filename"] == "specific-backup.tar.zst"
        assert data["size_bytes"] == 5000000

    def test_get_backup_not_found(self, client, auth_headers, db_session, test_user):
        """Test getting non-existent backup."""
        app = App(
            id="notfound-app",
            catalog_id="nginx",
            name="Not Found App",
            hostname="notfound-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        response = client.get(
            "/api/v1/apps/notfound-app/backups/99999",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestBackupAPIRestore:
    """Test backup restoration API."""

    def test_restore_backup_success(self, client_with_mock_proxmox, auth_headers, db_session, test_user):
        """Test successful backup restoration."""
        app = App(
            id="restore-api-app",
            catalog_id="nginx",
            name="Restore API App",
            hostname="restore-api-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="restore-api-app",
            filename="restore.tar.zst",
            storage_name="local",
            status="available"
        )
        db_session.add(backup)
        db_session.commit()

        response = client_with_mock_proxmox.post(
            f"/api/v1/apps/restore-api-app/backups/{backup.id}/restore",
            headers=auth_headers
        )

        assert response.status_code == 202  # Accepted
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_restore_backup_not_available(self, client, auth_headers, db_session, test_user):
        """Test restoring backup with wrong status."""
        app = App(
            id="restore-fail-app",
            catalog_id="nginx",
            name="Restore Fail App",
            hostname="restore-fail-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="restore-fail-app",
            filename="restore.tar.zst",
            storage_name="local",
            status="creating"  # Not available
        )
        db_session.add(backup)
        db_session.commit()

        response = client.post(
            f"/api/v1/apps/restore-fail-app/backups/{backup.id}/restore",
            headers=auth_headers
        )

        assert response.status_code in [400, 422]


class TestBackupAPIDelete:
    """Test backup deletion API."""

    def test_delete_backup_success(self, client_with_mock_proxmox, auth_headers, db_session, test_user):
        """Test successful backup deletion."""
        app = App(
            id="delete-api-app",
            catalog_id="nginx",
            name="Delete API App",
            hostname="delete-api-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="delete-api-app",
            filename="delete.tar.zst",
            storage_name="local",
            status="available"
        )
        db_session.add(backup)
        db_session.commit()
        backup_id = backup.id

        response = client_with_mock_proxmox.delete(
            f"/api/v1/apps/delete-api-app/backups/{backup_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_backup_not_found(self, client, auth_headers, db_session, test_user):
        """Test deleting non-existent backup."""
        app = App(
            id="delete-notfound-app",
            catalog_id="nginx",
            name="Delete Not Found App",
            hostname="delete-notfound-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        response = client.delete(
            "/api/v1/apps/delete-notfound-app/backups/99999",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestBackupAPIPermissions:
    """Test backup API permissions and ownership."""

    def test_user_can_only_access_own_backups(self, client, db_session):
        """Test users can only access their own app backups."""
        # Create two users
        user1 = User(
            username="user1",
            email="user1@example.com",
            hashed_password=User.hash_password("password123"),
            role="user"
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            hashed_password=User.hash_password("password123"),
            role="user"
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # Create app for user1
        app = App(
            id="user1-app",
            catalog_id="nginx",
            name="User1 App",
            hostname="user1-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=user1.id
        )
        db_session.add(app)
        db_session.commit()

        # Create backup
        backup = Backup(
            app_id="user1-app",
            filename="user1-backup.tar.zst",
            storage_name="local",
            status="available"
        )
        db_session.add(backup)
        db_session.commit()

        # Login as user2
        login_response = client.post("/api/v1/auth/login", json={
            "username": "user2",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access user1's backups
        response = client.get(
            "/api/v1/apps/user1-app/backups",
            headers=headers
        )

        # Should be forbidden (user2 doesn't own the app)
        assert response.status_code in [403, 404]
