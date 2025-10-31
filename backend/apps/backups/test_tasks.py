"""
Unit tests for backup Celery tasks.

These tests mock Proxmox API calls to test task logic in isolation.
"""

import pytest
from unittest.mock import patch

from apps.backups.models import Backup
from apps.backups.tasks import create_backup_task, restore_backup_task, delete_backup_task


@pytest.mark.django_db
class TestCreateBackupTask:
    """Tests for create_backup_task."""

    def test_create_backup_success(self, sample_application):
        """Test successful backup creation."""
        with patch("apps.backups.tasks.ProxmoxService") as MockProxmox:
            # Mock Proxmox service
            mock_service = MockProxmox.return_value
            mock_service.create_lxc_backup.return_value = {
                "file_name": "vzdump-lxc-101-2025_10_18-10_30_00.tar.zst",
                "size": 524288000,  # 500 MB
                "storage": "local",
            }

            # Execute task
            result = create_backup_task(
                application_id=sample_application.id, backup_type="snapshot", compression="zstd"
            )

            # Verify result
            assert result["success"] is True
            assert "backup_id" in result
            assert result["file_name"] == "vzdump-lxc-101-2025_10_18-10_30_00.tar.zst"

            # Verify backup record created
            backup = Backup.objects.get(id=result["backup_id"])
            assert backup.status == "completed"
            assert backup.file_name == "vzdump-lxc-101-2025_10_18-10_30_00.tar.zst"
            assert backup.size == 524288000
            assert backup.completed_at is not None

            # Verify Proxmox service was called correctly
            mock_service.create_lxc_backup.assert_called_once_with(
                node_name=sample_application.node,
                vmid=sample_application.lxc_id,
                storage="local",
                mode="snapshot",
                compress="zstd",
            )

    def test_create_backup_application_not_found(self):
        """Test backup creation with non-existent application."""
        result = create_backup_task(
            application_id="non-existent-id", backup_type="snapshot", compression="zstd"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_create_backup_proxmox_error(self, sample_application):
        """Test backup creation when Proxmox returns an error."""
        with patch("apps.backups.tasks.ProxmoxService") as MockProxmox:
            # Mock Proxmox service to raise error
            mock_service = MockProxmox.return_value
            mock_service.create_lxc_backup.side_effect = Exception("Backup failed")

            # Execute task
            result = create_backup_task(
                application_id=sample_application.id, backup_type="snapshot", compression="zstd"
            )

            # Verify result
            assert result["success"] is False
            assert "backup failed" in result["error"].lower()

            # Verify backup record marked as failed
            backup = Backup.objects.filter(application=sample_application, status="failed").first()
            assert backup is not None
            assert backup.error_message is not None


@pytest.mark.django_db
class TestRestoreBackupTask:
    """Tests for restore_backup_task."""

    def test_restore_backup_success(self, sample_application, sample_backup):
        """Test successful backup restore."""
        with patch("apps.backups.tasks.ProxmoxService") as MockProxmox:
            # Mock Proxmox service
            mock_service = MockProxmox.return_value
            mock_service.get_lxc_status.return_value = {"status": "running"}
            mock_service.stop_lxc.return_value = {"success": True}
            mock_service.restore_lxc_backup.return_value = {
                "task": {"status": "completed"},
                "vmid": sample_application.lxc_id,
            }

            # Execute task
            result = restore_backup_task(backup_id=sample_backup.id)

            # Verify result
            assert result["success"] is True
            assert result["backup_id"] == sample_backup.id
            assert result["application_id"] == sample_application.id

            # Verify backup status
            sample_backup.refresh_from_db()
            assert sample_backup.status == "completed"

            # Verify application status
            sample_application.refresh_from_db()
            assert sample_application.status == "stopped"

            # Verify Proxmox calls
            mock_service.stop_lxc.assert_called_once()
            mock_service.restore_lxc_backup.assert_called_once_with(
                node_name=sample_application.node,
                vmid=sample_application.lxc_id,
                backup_file=sample_backup.file_name,
                storage=sample_backup.storage_name,
                force=True,
            )

    def test_restore_backup_not_found(self):
        """Test restore with non-existent backup."""
        result = restore_backup_task(backup_id=99999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_restore_backup_not_completed(self, sample_application):
        """Test restore when backup is not in completed state."""
        # Create backup in creating state
        backup = Backup.objects.create(
            application=sample_application, file_name="test.tar.zst", status="creating"
        )

        result = restore_backup_task(backup_id=backup.id)

        assert result["success"] is False
        assert "not in completed state" in result["error"].lower()

    def test_restore_backup_proxmox_error(self, sample_application, sample_backup):
        """Test restore when Proxmox returns an error."""
        with patch("apps.backups.tasks.ProxmoxService") as MockProxmox:
            # Mock Proxmox service to raise error
            mock_service = MockProxmox.return_value
            mock_service.get_lxc_status.return_value = {"status": "stopped"}
            mock_service.restore_lxc_backup.side_effect = Exception("Restore failed")

            # Execute task
            result = restore_backup_task(backup_id=sample_backup.id)

            # Verify result
            assert result["success"] is False
            assert "restore failed" in result["error"].lower()

            # Verify statuses reverted
            sample_backup.refresh_from_db()
            assert sample_backup.status == "completed"

            sample_application.refresh_from_db()
            assert sample_application.status == "error"


@pytest.mark.django_db
class TestDeleteBackupTask:
    """Tests for delete_backup_task."""

    def test_delete_backup_success(self, sample_application, sample_backup):
        """Test successful backup deletion."""
        backup_id = sample_backup.id

        with patch("apps.backups.tasks.ProxmoxService") as MockProxmox:
            # Mock Proxmox service
            mock_service = MockProxmox.return_value
            mock_service.delete_backup_file.return_value = True

            # Execute task
            result = delete_backup_task(backup_id=backup_id)

            # Verify result
            assert result["success"] is True
            assert result["backup_id"] == backup_id

            # Verify backup was deleted
            assert not Backup.objects.filter(id=backup_id).exists()

            # Verify Proxmox was called
            mock_service.delete_backup_file.assert_called_once_with(
                node_name=sample_application.node,
                storage=sample_backup.storage_name,
                backup_file=sample_backup.file_name,
            )

    def test_delete_backup_not_found(self):
        """Test delete with non-existent backup."""
        result = delete_backup_task(backup_id=99999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_delete_backup_file_not_found(self, sample_application, sample_backup):
        """Test delete when backup file doesn't exist in storage."""
        backup_id = sample_backup.id

        with patch("apps.backups.tasks.ProxmoxService") as MockProxmox:
            # Mock Proxmox service to raise "not found" error
            mock_service = MockProxmox.return_value
            mock_service.delete_backup_file.side_effect = Exception("File not found")

            # Execute task - should succeed anyway
            result = delete_backup_task(backup_id=backup_id)

            # Verify result
            assert result["success"] is True

            # Verify backup was deleted from database
            assert not Backup.objects.filter(id=backup_id).exists()

    def test_delete_backup_proxmox_error(self, sample_application, sample_backup):
        """Test delete when Proxmox returns a non-"not found" error."""
        with patch("apps.backups.tasks.ProxmoxService") as MockProxmox:
            # Mock Proxmox service to raise error
            mock_service = MockProxmox.return_value
            mock_service.delete_backup_file.side_effect = Exception("Connection error")

            # Execute task
            result = delete_backup_task(backup_id=sample_backup.id)

            # Verify result
            assert result["success"] is False
            assert "error" in result["error"].lower()

            # Verify backup still exists
            assert Backup.objects.filter(id=sample_backup.id).exists()
