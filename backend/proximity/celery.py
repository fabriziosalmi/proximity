"""
Celery configuration for Proximity 2.0.

This module sets up Celery for background task processing.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proximity.settings')

app = Celery('proximity')

# Load configuration from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Reconciliation task - runs every hour to clean up orphan applications
    'reconcile-applications-every-hour': {
        'task': 'apps.applications.tasks.reconciliation_task',
        'schedule': 3600.0,  # Every 3600 seconds (1 hour)
        'options': {
            'expires': 3000,  # Task expires after 50 minutes if not executed
        }
    },
    # Janitor task - runs every 6 hours to clean up stuck applications
    'cleanup-stuck-applications-every-6-hours': {
        'task': 'apps.applications.tasks.janitor_task',
        'schedule': 21600.0,  # Every 21600 seconds (6 hours)
        'options': {
            'expires': 20000,  # Task expires after ~5.5 hours if not executed
        }
    },
}

# Optional: Set timezone for beat scheduler
app.conf.timezone = 'UTC'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
