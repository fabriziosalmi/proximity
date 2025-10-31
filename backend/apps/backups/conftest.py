"""
Pytest fixtures for backup tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.proxmox.models import ProxmoxHost
from apps.applications.models import Application
from apps.backups.models import Backup

User = get_user_model()


@pytest.fixture
def sample_user():
    """Create a test user."""
    user, _ = User.objects.get_or_create(
        username="testuser",
        defaults={
            "email": "test@example.com",
        },
    )
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def other_user():
    """Create another test user."""
    user, _ = User.objects.get_or_create(
        username="otheruser",
        defaults={
            "email": "other@example.com",
        },
    )
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def sample_host():
    """Create a test Proxmox host."""
    host, _ = ProxmoxHost.objects.get_or_create(
        name="Test Host",
        defaults={
            "host": "192.168.1.100",
            "port": 8006,
            "user": "root@pam",
            "password": "testpassword",
            "is_active": True,
            "is_default": True,
        },
    )
    return host


@pytest.fixture
def sample_application(sample_user, sample_host):
    """Create a test application."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    lxc_id = 100 + int(unique_id[:2], 16) % 900

    app, _ = Application.objects.get_or_create(
        id=f"test-app-{unique_id}",
        defaults={
            "catalog_id": "adminer",
            "name": "Test Adminer",
            "hostname": f"test-adminer-{unique_id}",
            "status": "running",
            "lxc_id": lxc_id,
            "host": sample_host,
            "node": "pve",
            "owner": sample_user,
        },
    )
    return app


@pytest.fixture
def other_user_application(other_user, sample_host):
    """Create an application owned by another user."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    lxc_id = 200 + int(unique_id[:2], 16) % 700

    app, _ = Application.objects.get_or_create(
        id=f"other-app-{unique_id}",
        defaults={
            "catalog_id": "adminer",
            "name": "Other Adminer",
            "hostname": f"other-adminer-{unique_id}",
            "status": "running",
            "lxc_id": lxc_id,
            "host": sample_host,
            "node": "pve",
            "owner": other_user,
        },
    )
    return app


@pytest.fixture
def sample_backup(sample_application):
    """Create a test backup."""
    return Backup.objects.create(
        application=sample_application,
        file_name="vzdump-lxc-101-2025_10_18-10_00_00.tar.zst",
        storage_name="local",
        size=524288000,  # 500 MB
        backup_type="snapshot",
        compression="zstd",
        status="completed",
    )


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def auth_client(client, sample_user):
    """Authenticated Django test client."""
    # For Django Ninja with AuthBearer, we need to add the token header
    # This is a simplified version - adjust based on your auth implementation
    from rest_framework.authtoken.models import Token

    # Try to get or create token
    try:
        token, _ = Token.objects.get_or_create(user=sample_user)
        client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token.key}"
    except Exception:
        # If Token model doesn't exist, mock the user directly
        client.force_login(sample_user)

    # Store user reference for permission checks
    client.user = sample_user
    return client
