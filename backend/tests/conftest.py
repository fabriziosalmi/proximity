"""
Pytest configuration and fixtures for unit tests.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.proxmox.models import ProxmoxHost, ProxmoxNode
from apps.applications.models import Application
from apps.backups.models import Backup
from apps.core.models import SystemSettings

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def proxmox_host(db):
    """Create a test Proxmox host."""
    return ProxmoxHost.objects.create(
        name='test-host',
        host='192.168.1.100',
        port=8006,
        user='root@pam',
        password='testpassword',
        verify_ssl=False,
        is_active=True
    )


@pytest.fixture
def proxmox_node(db, proxmox_host):
    """Create a test Proxmox node."""
    return ProxmoxNode.objects.create(
        host=proxmox_host,
        name='pve',
        status='online',
        cpu_count=8,
        cpu_usage=25.5,
        memory_total=16000000000,
        memory_used=8000000000,
        storage_total=500000000000,
        storage_used=250000000000
    )


@pytest.fixture
def test_application(db, test_user, proxmox_host):
    """Create a test application."""
    return Application.objects.create(
        id='test-app-001',
        catalog_id='nginx',
        name='Test Nginx',
        hostname='test-nginx.local',
        status='running',
        url='http://192.168.1.100:8080',
        iframe_url='http://192.168.1.100:8080',
        public_port=8080,
        internal_port=80,
        lxc_id=100,
        host=proxmox_host,
        node='pve',
        owner=test_user,
        config={'image': 'nginx:latest'},
        environment={'ENV': 'test'}
    )


@pytest.fixture
def test_backup(db, test_application):
    """Create a test backup."""
    return Backup.objects.create(
        application=test_application,
        file_name='test-nginx-backup-001.tar.gz',
        storage_name='local',
        size=1024000,
        status='completed',
        backup_type='snapshot',
        compression='zstd'
    )


@pytest.fixture
def system_settings(db):
    """Create or get system settings."""
    settings, _ = SystemSettings.objects.get_or_create(
        id=1,
        defaults={
            'default_theme': 'rack_proximity',
            'enable_ai_agent': False,
            'enable_community_chat': False,
            'enable_multi_host': True,
            'default_cpu_cores': 2,
            'default_memory_mb': 2048,
            'default_disk_gb': 20
        }
    )
    return settings


@pytest.fixture
def mock_proxmox_api(mocker):
    """Mock ProxmoxAPI for testing without real Proxmox server."""
    mock = mocker.patch('apps.proxmox.services.ProxmoxAPI')
    mock_instance = mock.return_value
    
    # Mock common API calls
    mock_instance.nodes.get.return_value = [
        {'node': 'pve', 'status': 'online', 'cpu': 0.25, 'maxcpu': 8}
    ]
    mock_instance.nodes().lxc.get.return_value = []
    
    return mock_instance


@pytest.fixture
def mock_celery_task(mocker):
    """Mock Celery tasks to run synchronously."""
    def mock_delay(*args, **kwargs):
        """Mock delay method that returns a mock result."""
        result = mocker.Mock()
        result.id = 'test-task-id'
        result.state = 'SUCCESS'
        return result
    
    return mock_delay
