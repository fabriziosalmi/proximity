"""
Pytest configuration for Proximity 2.0 backend tests.
"""

import os
import django
import pytest

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proximity.settings")
django.setup()


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """Configure test database and apply migrations."""
    from django.conf import settings
    from django.core.management import call_command

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

    # Apply migrations to the test database
    with django_db_blocker.unblock():
        call_command("migrate", "--run-syncdb", verbosity=0)


@pytest.fixture(autouse=True)
def enable_db_access(db):
    """Enable database access for all tests."""
    pass


@pytest.fixture(scope="session")
def celery_config():
    """Configure Celery for synchronous execution in tests."""
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,
        "task_eager_propagates": True,
    }
