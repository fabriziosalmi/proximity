"""
Unit tests for BackupService.
Tests backup creation, listing, restoration, and deletion with TDD approach.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from models.database import Backup, App, User
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class TestBackupServiceCreate:
    """Test backup creation functionality."""

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_create_backup_success(self, mock_proxmox_class, db_session, test_user):
        """Test successful backup creation."""
        from services.backup_service import BackupService

        # Create app
        app = App(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Mock Proxmox service
        mock_proxmox = AsyncMock()
        mock_proxmox.create_vzdump.return_value = "UPID:testnode:00001234:00000000:00000000:vzdump:100:user@pam:"
        mock_proxmox_class.return_value = mock_proxmox

        # Create backup service
        backup_service = BackupService(db_session, mock_proxmox)

        # Create backup
        backup = await backup_service.create_backup(
            app_id="test-app",
            storage="local",
            compress="zstd",
            mode="snapshot"
        )

        # Verify backup record created
        assert backup.id is not None
        assert backup.app_id == "test-app"
        assert backup.storage_name == "local"
        assert backup.status == "creating"
        assert backup.filename.startswith("vzdump-lxc-100-")
        assert backup.filename.endswith(".tar.zst")

        # Verify Proxmox API called
        mock_proxmox.create_vzdump.assert_called_once_with(
            node="testnode",
            vmid=100,
            storage="local",
            compress="zstd",
            mode="snapshot"
        )

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_create_backup_app_not_found(self, mock_proxmox_class, db_session):
        """Test backup creation fails when app doesn't exist."""
        from services.backup_service import BackupService

        mock_proxmox = AsyncMock()
        mock_proxmox_class.return_value = mock_proxmox
        backup_service = BackupService(db_session, mock_proxmox)

        with pytest.raises(ValueError, match="App.*not found"):
            await backup_service.create_backup(
                app_id="nonexistent-app",
                storage="local"
            )

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_create_backup_proxmox_failure(self, mock_proxmox_class, db_session, test_user):
        """Test backup creation handles Proxmox failures."""
        from services.backup_service import BackupService

        # Create app
        app = App(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Mock Proxmox failure
        mock_proxmox = AsyncMock()
        mock_proxmox.create_vzdump.side_effect = Exception("Proxmox API error")
        mock_proxmox_class.return_value = mock_proxmox

        backup_service = BackupService(db_session, mock_proxmox)

        with pytest.raises(Exception, match="Proxmox API error"):
            await backup_service.create_backup(app_id="test-app", storage="local")

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_create_backup_with_custom_compression(self, mock_proxmox_class, db_session, test_user):
        """Test backup creation with different compression types."""
        from services.backup_service import BackupService

        app = App(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        mock_proxmox = AsyncMock()
        mock_proxmox.create_vzdump.return_value = "UPID:task"
        mock_proxmox_class.return_value = mock_proxmox

        backup_service = BackupService(db_session, mock_proxmox)

        # Test gzip compression
        backup = await backup_service.create_backup(
            app_id="test-app",
            storage="local",
            compress="gzip"
        )
        assert backup.filename.endswith(".tar.gz")


class TestBackupServiceList:
    """Test backup listing functionality."""

    @pytest.mark.asyncio
    async def test_list_backups_for_app(self, db_session, test_user):
        """Test listing all backups for an app."""
        from services.backup_service import BackupService

        # Create app
        app = App(
            id="list-app",
            catalog_id="nginx",
            name="List App",
            hostname="list-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Create multiple backups
        for i in range(3):
            backup = Backup(
                app_id="list-app",
                filename=f"backup-{i}.tar.zst",
                storage_name="local",
                status="available",
                size_bytes=1000000 * (i + 1)
            )
            db_session.add(backup)
        db_session.commit()

        backup_service = BackupService(db_session)

        # List backups
        backups = await backup_service.list_backups_for_app("list-app")

        assert len(backups) == 3
        assert all(b.app_id == "list-app" for b in backups)

    @pytest.mark.asyncio
    async def test_list_backups_empty(self, db_session, test_user):
        """Test listing backups when none exist."""
        from services.backup_service import BackupService

        app = App(
            id="empty-app",
            catalog_id="nginx",
            name="Empty App",
            hostname="empty-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup_service = BackupService(db_session)
        backups = await backup_service.list_backups_for_app("empty-app")

        assert len(backups) == 0

    @pytest.mark.asyncio
    async def test_list_backups_ordered_by_created_at(self, db_session, test_user):
        """Test backups are returned in reverse chronological order."""
        from services.backup_service import BackupService
        import time

        app = App(
            id="order-app",
            catalog_id="nginx",
            name="Order App",
            hostname="order-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Create backups with delays
        for i in range(3):
            backup = Backup(
                app_id="order-app",
                filename=f"backup-{i}.tar.zst",
                storage_name="local",
                status="available"
            )
            db_session.add(backup)
            db_session.commit()
            time.sleep(0.01)

        backup_service = BackupService(db_session)
        backups = await backup_service.list_backups_for_app("order-app")

        # Most recent first
        assert "backup-2" in backups[0].filename
        assert "backup-0" in backups[2].filename


class TestBackupServiceGet:
    """Test getting individual backups."""

    @pytest.mark.asyncio
    async def test_get_backup_success(self, db_session, test_user):
        """Test getting a specific backup."""
        from services.backup_service import BackupService

        app = App(
            id="get-app",
            catalog_id="nginx",
            name="Get App",
            hostname="get-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="get-app",
            filename="specific-backup.tar.zst",
            storage_name="local",
            status="available",
            size_bytes=5000000
        )
        db_session.add(backup)
        db_session.commit()

        backup_service = BackupService(db_session)
        retrieved = await backup_service.get_backup(backup.id)

        assert retrieved.id == backup.id
        assert retrieved.filename == "specific-backup.tar.zst"
        assert retrieved.size_bytes == 5000000

    @pytest.mark.asyncio
    async def test_get_backup_not_found(self, db_session):
        """Test getting non-existent backup."""
        from services.backup_service import BackupService

        backup_service = BackupService(db_session)

        with pytest.raises(ValueError, match="Backup.*not found"):
            await backup_service.get_backup(99999)


class TestBackupServiceRestore:
    """Test backup restoration functionality."""

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_restore_backup_success(self, mock_proxmox_class, db_session, test_user):
        """Test successful backup restoration."""
        from services.backup_service import BackupService

        # Create app
        app = App(
            id="restore-app",
            catalog_id="nginx",
            name="Restore App",
            hostname="restore-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Create backup
        backup = Backup(
            app_id="restore-app",
            filename="vzdump-lxc-100-2025_10_04-12_00_00.tar.zst",
            storage_name="local",
            status="available",
            size_bytes=1000000
        )
        db_session.add(backup)
        db_session.commit()

        # Mock Proxmox service
        mock_proxmox = AsyncMock()
        mock_proxmox.stop_lxc.return_value = "UPID:stop"
        mock_proxmox.restore_backup.return_value = "UPID:restore"
        mock_proxmox.start_lxc.return_value = "UPID:start"
        mock_proxmox_class.return_value = mock_proxmox

        backup_service = BackupService(db_session, mock_proxmox)

        # Restore backup
        result = await backup_service.restore_from_backup(backup.id)

        # Verify backup status returned to available after restore
        db_session.refresh(backup)
        assert backup.status == "available"

        # Verify Proxmox calls
        mock_proxmox.stop_lxc.assert_called_once_with("testnode", 100)
        mock_proxmox.restore_backup.assert_called_once_with(
            node="testnode",
            vmid=100,
            backup_file="vzdump-lxc-100-2025_10_04-12_00_00.tar.zst",
            storage="local"
        )
        mock_proxmox.start_lxc.assert_called_once_with("testnode", 100)

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_restore_backup_not_available(self, mock_proxmox_class, db_session, test_user):
        """Test restoration fails for non-available backups."""
        from services.backup_service import BackupService

        app = App(
            id="restore-app",
            catalog_id="nginx",
            name="Restore App",
            hostname="restore-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="restore-app",
            filename="backup.tar.zst",
            storage_name="local",
            status="creating"  # Not available yet
        )
        db_session.add(backup)
        db_session.commit()

        mock_proxmox = AsyncMock()
        mock_proxmox_class.return_value = mock_proxmox

        backup_service = BackupService(db_session, mock_proxmox)

        with pytest.raises(ValueError, match="Backup is not available"):
            await backup_service.restore_from_backup(backup.id)

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_restore_failure_restarts_container(self, mock_proxmox_class, db_session, test_user):
        """Test that container is restarted when restore fails."""
        from services.backup_service import BackupService

        app = App(
            id="restore-fail-app",
            catalog_id="nginx",
            name="Restore Fail App",
            hostname="restore-fail-app",
            status="running",
            lxc_id=101,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="restore-fail-app",
            filename="backup.tar.zst",
            storage_name="local",
            status="available"
        )
        db_session.add(backup)
        db_session.commit()

        # Mock Proxmox - restore will fail
        mock_proxmox = AsyncMock()
        mock_proxmox.stop_lxc.return_value = "UPID:stop"
        mock_proxmox.restore_backup.side_effect = Exception("Restore failed")
        mock_proxmox.start_lxc.return_value = "UPID:start"
        mock_proxmox_class.return_value = mock_proxmox

        backup_service = BackupService(db_session, mock_proxmox)

        # Restore should fail but attempt container restart
        with pytest.raises(Exception, match="Restore failed"):
            await backup_service.restore_from_backup(backup.id)

        # Verify stop was called
        mock_proxmox.stop_lxc.assert_called_once_with("testnode", 101)

        # Verify restore was attempted
        mock_proxmox.restore_backup.assert_called_once()

        # CRITICAL: Verify container restart was attempted after failure
        mock_proxmox.start_lxc.assert_called_once_with("testnode", 101)

        # Verify backup status returned to available
        db_session.refresh(backup)
        assert backup.status == "available"
        assert "Restore failed" in backup.error_message


class TestBackupServiceDelete:
    """Test backup deletion functionality."""

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_delete_backup_success(self, mock_proxmox_class, db_session, test_user):
        """Test successful backup deletion."""
        from services.backup_service import BackupService

        app = App(
            id="delete-app",
            catalog_id="nginx",
            name="Delete App",
            hostname="delete-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="delete-app",
            filename="vzdump-lxc-100-2025_10_04.tar.zst",
            storage_name="local",
            status="available"
        )
        db_session.add(backup)
        db_session.commit()
        backup_id = backup.id

        # Mock Proxmox
        mock_proxmox = AsyncMock()
        mock_proxmox.delete_backup.return_value = True
        mock_proxmox_class.return_value = mock_proxmox

        backup_service = BackupService(db_session, mock_proxmox)

        # Delete backup
        await backup_service.delete_backup(backup_id)

        # Verify Proxmox call
        mock_proxmox.delete_backup.assert_called_once_with(
            node="testnode",
            storage="local",
            backup_file="vzdump-lxc-100-2025_10_04.tar.zst"
        )

        # Verify backup deleted from DB
        deleted = db_session.query(Backup).filter(Backup.id == backup_id).first()
        assert deleted is None

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_delete_backup_not_found(self, mock_proxmox_class, db_session):
        """Test deleting non-existent backup."""
        from services.backup_service import BackupService

        mock_proxmox = AsyncMock()
        mock_proxmox_class.return_value = mock_proxmox

        backup_service = BackupService(db_session, mock_proxmox)

        with pytest.raises(ValueError, match="Backup.*not found"):
            await backup_service.delete_backup(99999)


class TestBackupServicePolling:
    """Test backup completion polling."""

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_poll_backup_completion_success(self, mock_proxmox_class, db_session, test_user):
        """Test backup completion polling updates status."""
        from services.backup_service import BackupService

        app = App(
            id="poll-app",
            catalog_id="nginx",
            name="Poll App",
            hostname="poll-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="poll-app",
            filename="vzdump-lxc-100-2025_10_04.tar.zst",
            storage_name="local",
            status="creating"
        )
        db_session.add(backup)
        db_session.commit()

        # Mock Proxmox - backup is complete
        mock_proxmox = AsyncMock()
        mock_proxmox.get_backup_list.return_value = [{
            "volid": "local:backup/vzdump-lxc-100-2025_10_04.tar.zst",
            "size": 5000000,
            "ctime": datetime.utcnow().timestamp()
        }]
        mock_proxmox_class.return_value = mock_proxmox

        backup_service = BackupService(db_session, mock_proxmox)

        # Poll completion
        await backup_service._poll_backup_completion(backup.id)

        # Verify status updated
        db_session.refresh(backup)
        assert backup.status == "available"
        assert backup.size_bytes == 5000000
        assert backup.completed_at is not None

    @pytest.mark.asyncio
    @patch('services.backup_service.ProxmoxService')
    async def test_poll_backup_completion_failed(self, mock_proxmox_class, db_session, test_user):
        """Test backup failure detection."""
        from services.backup_service import BackupService

        app = App(
            id="poll-app",
            catalog_id="nginx",
            name="Poll App",
            hostname="poll-app",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        backup = Backup(
            app_id="poll-app",
            filename="vzdump-lxc-100-2025_10_04.tar.zst",
            storage_name="local",
            status="creating"
        )
        db_session.add(backup)
        db_session.commit()

        # Mock Proxmox - backup not found (failed)
        mock_proxmox = AsyncMock()
        mock_proxmox.get_backup_list.return_value = []
        mock_proxmox_class.return_value = mock_proxmox

        backup_service = BackupService(db_session, mock_proxmox)

        # Poll with a very short timeout to trigger failure quickly
        await backup_service._poll_backup_completion(backup.id, timeout=0)

        # Verify marked as failed
        db_session.refresh(backup)
        assert backup.status == "failed"
        assert "timeout" in backup.error_message.lower()
