"""
Page Objects Package

This package contains Page Object Models for the Proximity 2.0 E2E tests.
"""

from .login_page import LoginPage
from .store_page import StorePage
from .apps_page import AppsPage

__all__ = ["LoginPage", "StorePage", "AppsPage"]
