"""
Pytest configuration and shared fixtures for Proximity E2E tests.

This module provides core fixtures for browser management, authentication,
and test data generation.
"""

import os
import pytest
from typing import Generator
from playwright.sync_api import Page, Browser, BrowserContext, Playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def base_url() -> str:
    """
    Base URL for the Proximity instance under test.
    Can be overridden with PROXIMITY_E2E_URL environment variable.
    """
    return os.getenv("PROXIMITY_E2E_URL", "http://127.0.0.1:8765")


@pytest.fixture(scope="session")
def slow_mo() -> int:
    """
    Milliseconds to slow down Playwright operations for debugging.
    Set SLOW_MO=1000 to see tests run in slow motion.
    """
    return int(os.getenv("SLOW_MO", "0"))


@pytest.fixture(scope="session")
def headless() -> bool:
    """
    Whether to run browser in headless mode.
    Set HEADLESS=true for CI environments.
    """
    return os.getenv("HEADLESS", "false").lower() == "true"


@pytest.fixture(scope="session")
def timeout() -> int:
    """
    Default timeout in milliseconds for Playwright operations.
    """
    return int(os.getenv("TIMEOUT", "30000"))


# ============================================================================
# Browser Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def browser_type_launch_args(slow_mo: int, headless: bool) -> dict:
    """
    Launch arguments for the browser.
    """
    return {
        "headless": headless,
        "slow_mo": slow_mo,
        "args": [
            "--disable-blink-features=AutomationControlled",  # Avoid detection
        ]
    }


@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    """
    Context arguments for browser isolation.
    """
    return {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }


@pytest.fixture(scope="function")
def context(browser: Browser, browser_context_args: dict, base_url: str, timeout: int) -> Generator[BrowserContext, None, None]:
    """
    Create a new browser context for each test (isolation).
    Automatically sets default timeout and navigation timeout.
    """
    ctx = browser.new_context(**browser_context_args)
    ctx.set_default_timeout(timeout)
    ctx.set_default_navigation_timeout(timeout)
    
    yield ctx
    
    # Cleanup: Close context and all pages
    ctx.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext, base_url: str) -> Generator[Page, None, None]:
    """
    Create a new page for each test.
    Automatically navigates to base URL.
    """
    page = context.new_page()
    page.goto(base_url)
    
    yield page
    
    # Take screenshot on failure (captured by pytest)
    if hasattr(page, "_test_failed"):
        page.screenshot(path=f"screenshots/failure_{page._test_name}.png")
    
    page.close()


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def authenticated_page(page: Page, base_url: str) -> Page:
    """
    Provides a page with an authenticated user session.
    
    This fixture:
    1. Registers a new test user (if not exists)
    2. Logs in
    3. Waits for dashboard to load
    4. Returns authenticated page
    
    Use this when tests require a logged-in user.
    """
    from pages.login_page import LoginPage
    from pages.dashboard_page import DashboardPage
    from utils.test_data import generate_test_user
    
    # Generate unique test user
    test_user = generate_test_user()
    
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    # Navigate to app
    page.goto(base_url)
    
    # Register and login
    login_page.register(test_user["username"], test_user["password"])
    
    # Verify we're on the dashboard
    dashboard_page.wait_for_dashboard_load()
    
    return page


@pytest.fixture(scope="function")
def admin_authenticated_page(page: Page, base_url: str) -> Page:
    """
    Provides a page with an authenticated admin user session.
    
    Useful for tests that require admin privileges.
    """
    from pages.login_page import LoginPage
    from pages.dashboard_page import DashboardPage
    
    # Use a consistent admin user (assuming it exists)
    # In production, you might want to create this via API or migration
    admin_username = os.getenv("E2E_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("E2E_ADMIN_PASSWORD", "admin123")
    
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    # Navigate to app
    page.goto(base_url)
    
    # Login as admin
    login_page.login(admin_username, admin_password)
    
    # Verify we're on the dashboard
    dashboard_page.wait_for_dashboard_load()
    
    return page


# ============================================================================
# Hooks for Enhanced Reporting
# ============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test failure status for screenshot capture.
    """
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        # Mark the page object to trigger screenshot
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            page._test_failed = True
            page._test_name = item.name


@pytest.fixture(autouse=True)
def log_test_info(request):
    """
    Automatically log test start and end.
    """
    test_name = request.node.name
    print(f"\n{'='*80}")
    print(f"Starting test: {test_name}")
    print(f"{'='*80}")
    
    yield
    
    print(f"\n{'='*80}")
    print(f"Finished test: {test_name}")
    print(f"{'='*80}\n")
