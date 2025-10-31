"""
Proximity 2.0 - Django Project Package

This initializes Celery for the Django application.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
