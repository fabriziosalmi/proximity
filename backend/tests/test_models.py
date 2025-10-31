"""
Unit tests for Django models.
"""

import pytest
from django.db import IntegrityError

from apps.applications.models import Application, DeploymentLog
from apps.backups.models import Backup
from apps.core.models import User, SystemSettings
from apps.proxmox.models import ProxmoxHost, ProxmoxNode


@pytest.mark.django_db
class TestUserModel:
    """Test User model."""

    def test_create_user(self):
        """Test creating a basic user."""
        user = User.objects.create_user(
            username="john", email="john@example.com", password="secure123"
        )
        assert user.username == "john"
        assert user.email == "john@example.com"
        assert user.check_password("secure123")
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123"
        )
        assert admin.is_staff
        assert admin.is_superuser

    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(username="john", password="test")
        assert str(user) == "john"

    def test_user_default_theme(self):
        """Test user default theme preference."""
        user = User.objects.create_user(username="john", password="test")
        assert user.preferred_theme == "rack_proximity"


@pytest.mark.django_db
class TestProxmoxHostModel:
    """Test ProxmoxHost model."""

    def test_create_proxmox_host(self):
        """Test creating a Proxmox host."""
        host = ProxmoxHost.objects.create(
            name="proxmox-01",
            host="192.168.1.100",
            port=8006,
            user="root@pam",
            password="secret",
            verify_ssl=False,
        )
        assert host.name == "proxmox-01"
        assert host.host == "192.168.1.100"
        assert host.port == 8006
        assert host.is_active

    def test_host_unique_name(self):
        """Test that host names must be unique."""
        ProxmoxHost.objects.create(
            name="host1", host="192.168.1.100", user="root@pam", password="secret"
        )
        with pytest.raises(IntegrityError):
            ProxmoxHost.objects.create(
                name="host1", host="192.168.1.101", user="root@pam", password="secret"
            )

    def test_host_str_representation(self):
        """Test host string representation."""
        host = ProxmoxHost.objects.create(
            name="proxmox-01", host="192.168.1.100", user="root@pam", password="secret"
        )
        assert str(host) == "proxmox-01 (192.168.1.100)"


@pytest.mark.django_db
class TestProxmoxNodeModel:
    """Test ProxmoxNode model."""

    def test_create_node(self, proxmox_host):
        """Test creating a Proxmox node."""
        node = ProxmoxNode.objects.create(
            host=proxmox_host,
            name="pve",
            status="online",
            cpu_count=16,
            cpu_usage=45.5,
            memory_total=64000000000,
            memory_used=32000000000,
        )
        assert node.name == "pve"
        assert node.status == "online"
        assert node.cpu_count == 16
        assert node.host == proxmox_host

    def test_node_memory_percentage(self, proxmox_host):
        """Test memory usage percentage calculation."""
        node = ProxmoxNode.objects.create(
            host=proxmox_host,
            name="pve",
            status="online",
            memory_total=10000000000,
            memory_used=5000000000,
        )
        # Calculate memory percentage manually
        memory_percent = (node.memory_used / node.memory_total) * 100
        assert round(memory_percent, 2) == 50.0

    def test_node_str_representation(self, proxmox_node):
        """Test node string representation."""
        assert "pve" in str(proxmox_node)


@pytest.mark.django_db
class TestApplicationModel:
    """Test Application model."""

    def test_create_application(self, test_user, proxmox_host):
        """Test creating an application."""
        app = Application.objects.create(
            id="app-001",
            catalog_id="nginx",
            name="My Nginx",
            hostname="nginx-001.local",
            host=proxmox_host,
            node="pve",
            owner=test_user,
            status="deploying",
        )
        assert app.id == "app-001"
        assert app.name == "My Nginx"
        assert app.status == "deploying"
        assert app.owner == test_user

    def test_unique_hostname(self, test_user, proxmox_host):
        """Test that hostnames must be unique."""
        Application.objects.create(
            id="app-001",
            catalog_id="nginx",
            name="App 1",
            hostname="test.local",
            host=proxmox_host,
            node="pve",
            owner=test_user,
        )
        with pytest.raises(IntegrityError):
            Application.objects.create(
                id="app-002",
                catalog_id="mysql",
                name="App 2",
                hostname="test.local",
                host=proxmox_host,
                node="pve",
                owner=test_user,
            )

    def test_unique_ports(self, test_user, proxmox_host):
        """Test that public and internal ports must be unique."""
        Application.objects.create(
            id="app-001",
            catalog_id="nginx",
            name="App 1",
            hostname="app1.local",
            host=proxmox_host,
            node="pve",
            owner=test_user,
            public_port=8080,
        )
        with pytest.raises(IntegrityError):
            Application.objects.create(
                id="app-002",
                catalog_id="mysql",
                name="App 2",
                hostname="app2.local",
                host=proxmox_host,
                node="pve",
                owner=test_user,
                public_port=8080,
            )

    def test_state_changed_on_status_update(self, test_application):
        """Test that state_changed_at updates when status changes."""
        original_time = test_application.state_changed_at

        # Wait a moment to ensure time difference
        import time

        time.sleep(0.1)

        # Change status
        test_application.status = "stopped"
        test_application.save()

        # Reload from database
        test_application.refresh_from_db()

        assert test_application.state_changed_at > original_time

    def test_application_str_representation(self, test_application):
        """Test application string representation."""
        assert "Test Nginx" in str(test_application)
        assert "running" in str(test_application)

    def test_application_default_status(self, test_user, proxmox_host):
        """Test default application status."""
        app = Application.objects.create(
            id="app-test",
            catalog_id="test",
            name="Test",
            hostname="test.local",
            host=proxmox_host,
            node="pve",
            owner=test_user,
        )
        assert app.status == "deploying"

    def test_application_json_fields(self, test_application):
        """Test JSON field defaults."""
        assert isinstance(test_application.config, dict)
        assert isinstance(test_application.ports, dict)
        assert isinstance(test_application.volumes, list)
        assert isinstance(test_application.environment, dict)


@pytest.mark.django_db
class TestBackupModel:
    """Test Backup model."""

    def test_create_backup(self, test_application):
        """Test creating a backup."""
        backup = Backup.objects.create(
            application=test_application,
            file_name="backup-001.tar.gz",
            storage_name="local",
            size=5000000,
            status="completed",
        )
        assert backup.application == test_application
        assert backup.status == "completed"
        assert backup.size == 5000000

    def test_backup_size_mb_property(self, test_backup):
        """Test size_mb property calculation."""
        # test_backup has size=1024000 bytes
        expected_mb = 1024000 / (1024 * 1024)
        assert abs(test_backup.size_mb - round(expected_mb, 2)) < 0.01

    def test_backup_size_gb_property(self, test_backup):
        """Test size_gb property calculation."""
        expected_gb = 1024000 / (1024 * 1024 * 1024)
        assert abs(test_backup.size_gb - round(expected_gb, 2)) < 0.01

    def test_backup_is_completed_property(self, test_backup):
        """Test is_completed property."""
        assert test_backup.is_completed is True

        test_backup.status = "in_progress"
        test_backup.save()
        assert test_backup.is_completed is False

    def test_backup_str_representation(self, test_backup):
        """Test backup string representation."""
        result = str(test_backup)
        assert "Test Nginx" in result
        assert "backup-001.tar.gz" in result or "test-nginx-backup-001.tar.gz" in result

    def test_backup_ordering(self, test_application):
        """Test that backups are ordered by created_at descending."""
        backup1 = Backup.objects.create(
            application=test_application, file_name="backup1.tar.gz", storage_name="local"
        )
        backup2 = Backup.objects.create(
            application=test_application, file_name="backup2.tar.gz", storage_name="local"
        )

        backups = list(Backup.objects.all())
        assert backups[0] == backup2  # Most recent first
        assert backups[1] == backup1


@pytest.mark.django_db
class TestDeploymentLogModel:
    """Test DeploymentLog model."""

    def test_create_deployment_log(self, test_application):
        """Test creating a deployment log entry."""
        log = DeploymentLog.objects.create(
            application=test_application,
            level="info",
            message="Starting deployment",
            step="initialization",
        )
        assert log.application == test_application
        assert log.level == "info"
        assert log.message == "Starting deployment"

    def test_deployment_log_ordering(self, test_application):
        """Test that logs are ordered by timestamp descending."""
        log1 = DeploymentLog.objects.create(
            application=test_application, level="info", message="First log"
        )
        log2 = DeploymentLog.objects.create(
            application=test_application, level="info", message="Second log"
        )

        logs = list(DeploymentLog.objects.all())
        assert logs[0] == log2  # Most recent first
        assert logs[1] == log1


@pytest.mark.django_db
class TestSystemSettingsModel:
    """Test SystemSettings model."""

    def test_system_settings_singleton(self, system_settings):
        """Test that SystemSettings behaves as singleton."""
        settings = SystemSettings.load()
        assert settings == system_settings

    def test_system_settings_defaults(self):
        """Test default system settings values."""
        settings = SystemSettings.load()
        assert settings.default_theme == "rack_proximity"
        assert settings.enable_multi_host is True

    def test_system_settings_update(self, system_settings):
        """Test updating system settings."""
        system_settings.enable_ai_agent = True
        system_settings.save()

        # Reload and verify
        settings = SystemSettings.load()
        assert settings.enable_ai_agent is True
