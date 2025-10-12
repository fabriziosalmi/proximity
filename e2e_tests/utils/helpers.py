"""
Helper utilities for E2E tests.

Provides reusable fixtures, wait helpers, and cleanup utilities.
"""

import pytest
import time
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import generate_test_user


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
def authenticated_page(page: Page):
    """
    Fixture that provides an authenticated page with a logged-in user.
    
    Usage:
        def test_something(authenticated_page):
            page = authenticated_page
            # User is already logged in, on dashboard
    
    Returns:
        Page: Playwright page with authenticated session
    """
    test_user = generate_test_user()
    login_page = LoginPage(page)
    
    login_page.wait_for_auth_modal()
    login_page.register(
        username=test_user["username"],
        password=test_user["password"],
        email=test_user["email"]
    )
    
    dashboard = DashboardPage(page)
    dashboard.wait_for_dashboard_load()
    
    return page


@pytest.fixture
def authenticated_with_user(page: Page):
    """
    Fixture that provides both authenticated page AND user credentials.
    
    Usage:
        def test_something(authenticated_with_user):
            page, user = authenticated_with_user
            # Can access user['username'], user['password'], etc.
    
    Returns:
        tuple: (Page, dict) - Page object and user credentials
    """
    test_user = generate_test_user()
    login_page = LoginPage(page)
    
    login_page.wait_for_auth_modal()
    login_page.register(
        username=test_user["username"],
        password=test_user["password"],
        email=test_user["email"]
    )
    
    dashboard = DashboardPage(page)
    dashboard.wait_for_dashboard_load()
    
    return page, test_user


# ============================================================================
# APP DEPLOYMENT FIXTURES
# ============================================================================

@pytest.fixture
def deployed_nginx_app(authenticated_page):
    """
    Fixture that deploys an NGINX app and provides the page + hostname.
    
    Automatically cleans up the app after test completes.
    
    Usage:
        def test_something(deployed_nginx_app):
            page, hostname = deployed_nginx_app
            # NGINX app is already deployed and running
    
    Returns:
        tuple: (Page, str) - Page object and deployed app hostname
    """
    page = authenticated_page
    
    # Deploy NGINX
    page.click("a.nav-rack-item[data-view='catalog']")  # Specific to nav link to avoid ambiguity
    page.wait_for_selector(".app-card", timeout=15000)
    
    nginx_card = page.locator(".app-card:has-text('NGINX')").first
    nginx_card.click()
    
    timestamp = int(time.time())
    hostname = f"nginx-test-{timestamp}"
    
    page.locator("#hostname").fill(hostname)
    page.click("button:has-text('Deploy Application')")
    
    # Wait for deployment to complete
    page.wait_for_selector(
        "text=/complete|successfully/i",
        timeout=300000
    )
    
    # Navigate to apps view
    page.click("[data-view='apps']")
    page.wait_for_selector(f".app-card:has-text('{hostname}')", timeout=30000)
    
    yield page, hostname
    
    # Cleanup - delete the app
    try:
        page.click("[data-view='apps']")
        page.wait_for_selector(f".app-card:has-text('{hostname}')", timeout=10000)
        
        app_card = page.locator(f".app-card:has-text('{hostname}')")
        delete_button = app_card.locator("button[title*='Delete'], button.danger")
        
        if delete_button.is_visible():
            delete_button.click()
            page.locator("#deployModal button:has-text('Delete Forever')").click()
            page.wait_for_selector("#deployModal:not(.show)", timeout=180000)
    except Exception as e:
        print(f"Warning: Cleanup failed for {hostname}: {e}")


@pytest.fixture
def deployed_app_factory(authenticated_page):
    """
    Factory fixture for deploying multiple apps.
    
    Usage:
        def test_something(deployed_app_factory):
            page = authenticated_page
            
            # Deploy multiple apps
            nginx = deployed_app_factory(page, 'NGINX')
            portainer = deployed_app_factory(page, 'Portainer')
            
            # Use the apps
            # ...
            
    Returns:
        function: Factory function to deploy apps
    """
    deployed_apps = []
    
    def deploy_app(page: Page, app_name: str):
        """Deploy an app and track it for cleanup."""
        page.click("a.nav-rack-item[data-view='catalog']")  # Specific to nav link to avoid ambiguity
        page.wait_for_selector(".app-card", timeout=15000)
        
        app_card = page.locator(f".app-card:has-text('{app_name}')").first
        app_card.click()
        
        timestamp = int(time.time())
        hostname = f"{app_name.lower()}-test-{timestamp}"
        
        page.locator("#hostname").fill(hostname)
        page.click("button:has-text('Deploy Application')")
        
        page.wait_for_selector(
            "text=/complete|successfully/i",
            timeout=300000
        )
        
        deployed_apps.append(hostname)
        return hostname
    
    yield deploy_app
    
    # Cleanup all deployed apps
    for hostname in deployed_apps:
        try:
            page = authenticated_page
            page.click("[data-view='apps']")
            page.wait_for_selector(f".app-card:has-text('{hostname}')", timeout=10000)
            
            app_card = page.locator(f".app-card:has-text('{hostname}')")
            delete_button = app_card.locator("button[title*='Delete'], button.danger")
            
            if delete_button.is_visible():
                delete_button.click()
                page.locator("#deployModal button:has-text('Delete Forever')").click()
                page.wait_for_selector("#deployModal:not(.show)", timeout=180000)
        except Exception as e:
            print(f"Warning: Cleanup failed for {hostname}: {e}")


# ============================================================================
# WAIT HELPERS
# ============================================================================

def wait_for_app_status(page: Page, hostname: str, status: str, timeout: int = 30000):
    """
    Wait for an app to reach a specific status.
    
    Args:
        page: Playwright Page object
        hostname: App hostname to wait for
        status: Expected status ('Running', 'Stopped', etc.)
        timeout: Maximum wait time in milliseconds
    """
    page.wait_for_selector(
        f".app-card:has-text('{hostname}') .status-badge:has-text('{status}')",
        timeout=timeout
    )


def wait_for_deployment_complete(page: Page, timeout: int = 300000):
    """
    Wait for deployment progress to complete.
    
    Args:
        page: Playwright Page object
        timeout: Maximum wait time in milliseconds (default 5 minutes)
    """
    try:
        page.wait_for_selector(
            "text=/complete|successfully deployed/i",
            timeout=timeout
        )
    except Exception:
        # Modal might close without explicit success message
        page.wait_for_selector("#deployModal:not(.show)", timeout=10000)


def wait_for_modal_close(page: Page, timeout: int = 10000):
    """
    Wait for any modal to close.
    
    Args:
        page: Playwright Page object
        timeout: Maximum wait time in milliseconds
    """
    page.wait_for_selector("#deployModal:not(.show)", timeout=timeout)


def wait_for_notification(page: Page, message_pattern: str = None, timeout: int = 5000):
    """
    Wait for a notification to appear.
    
    Args:
        page: Playwright Page object
        message_pattern: Optional regex pattern to match notification text
        timeout: Maximum wait time in milliseconds
    """
    if message_pattern:
        page.wait_for_selector(
            f".notification:has-text('{message_pattern}'), .alert:has-text('{message_pattern}')",
            timeout=timeout
        )
    else:
        page.wait_for_selector(".notification, .alert", timeout=timeout)


# ============================================================================
# CLEANUP UTILITIES
# ============================================================================

def delete_app_if_exists(page: Page, hostname: str):
    """
    Delete an app if it exists, otherwise do nothing.
    
    Args:
        page: Playwright Page object
        hostname: Hostname of app to delete
    """
    try:
        # Navigate to apps view
        page.click("[data-view='apps']")
        page.wait_for_timeout(2000)
        
        # Find app
        app_card = page.locator(f".app-card:has-text('{hostname}')")
        
        if app_card.count() > 0 and app_card.is_visible():
            # Click delete
            delete_button = app_card.locator("button[title*='Delete'], button.danger")
            delete_button.click()
            
            # Confirm
            page.locator("#deployModal button:has-text('Delete Forever')").click()
            
            # Wait for deletion
            page.wait_for_selector("#deployModal:not(.show)", timeout=180000)
            
            return True
    except Exception as e:
        print(f"Warning: Could not delete {hostname}: {e}")
    
    return False


def cleanup_all_test_apps(page: Page):
    """
    Clean up all apps with 'test' in their hostname.
    
    Args:
        page: Playwright Page object
    """
    try:
        page.click("[data-view='apps']")
        page.wait_for_timeout(2000)
        
        # Find all test apps
        test_apps = page.locator(".app-card:has-text('test')").all()
        
        for app_card in test_apps:
            try:
                hostname = app_card.locator(".app-name, h3").inner_text()
                delete_app_if_exists(page, hostname)
            except Exception as e:
                print(f"Warning: Could not delete app: {e}")
    except Exception as e:
        print(f"Warning: Cleanup failed: {e}")


# ============================================================================
# ASSERTION HELPERS
# ============================================================================

def assert_app_exists(page: Page, hostname: str):
    """Assert that an app exists in the dashboard."""
    page.click("[data-view='apps']")
    page.wait_for_selector(".app-card", timeout=10000)
    
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    expect(app_card).to_be_visible()


def assert_app_not_exists(page: Page, hostname: str):
    """Assert that an app does NOT exist in the dashboard."""
    page.click("[data-view='apps']")
    page.wait_for_timeout(2000)
    
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    expect(app_card).not_to_be_visible()


def assert_app_status(page: Page, hostname: str, expected_status: str):
    """Assert that an app has a specific status."""
    page.click("[data-view='apps']")
    page.wait_for_selector(f".app-card:has-text('{hostname}')", timeout=10000)
    
    status_badge = page.locator(
        f".app-card:has-text('{hostname}') .status-badge:has-text('{expected_status}')"
    )
    expect(status_badge).to_be_visible()


# ============================================================================
# DATA GENERATION HELPERS
# ============================================================================

def generate_unique_hostname(base_name: str = "test"):
    """Generate a unique hostname with timestamp."""
    timestamp = int(time.time())
    return f"{base_name}-{timestamp}"


def generate_app_config(app_name: str):
    """
    Generate deployment configuration for an app.
    
    Args:
        app_name: Base name for the app
        
    Returns:
        dict: Configuration dictionary
    """
    return {
        "hostname": generate_unique_hostname(app_name.lower()),
        "cpu": 1,
        "memory": 512,
        "storage": 8
    }
