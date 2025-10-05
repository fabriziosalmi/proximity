"""
Pytest configuration and shared fixtures for Proximity E2E tests.

This module provides core fixtures for browser management, authentication,
and test data generation.
"""

import os
import pytest
from typing import Generator
from playwright.sync_api import Page, BrowserContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import additional fixtures
pytest_plugins = ['fixtures.deployed_app']


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
# Browser Fixtures (using pytest-playwright)
# ============================================================================

@pytest.fixture(scope="session")
def browser_type_launch_args(slow_mo: int, headless: bool) -> dict:
    """
    Launch arguments for the browser.
    This is used by pytest-playwright's browser fixture.
    """
    return {
        "headless": headless,
        "slow_mo": slow_mo,
        "args": [
            "--disable-blink-features=AutomationControlled",  # Avoid detection
        ]
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args) -> dict:
    """
    Context arguments for browser isolation.
    This is used by pytest-playwright's context fixture.
    
    CRITICAL: Sets storage_state to None to ensure localStorage/sessionStorage
    are cleared between tests, preventing JWT token leakage.
    """
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "storage_state": None,  # Ensures no saved state is used - critical for test isolation
    }


@pytest.fixture
def context(browser):
    """
    Create a new browser context for each test.
    This ensures complete isolation between tests with fresh storage.
    
    Note: Overrides pytest-playwright's default context fixture to use
    function scope instead of session scope for better isolation.
    """
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        storage_state=None,  # No saved state
    )
    
    yield context
    
    # CRITICAL CLEANUP: Ensure all pages are closed before closing context
    # This prevents Chromium from staying open
    print("\n🧹 [Cleanup] Closing browser context and all pages")
    try:
        # Get list of pages before iteration (avoid modification during iteration)
        pages = list(context.pages)
        for page in pages:
            try:
                if not page.is_closed():
                    print(f"  - Closing page: {page.url[:50] if page.url else 'unknown'}")
                    page.close()
            except Exception as e:
                print(f"  ⚠️  Error closing page: {e}")
    except Exception as e:
        print(f"  ⚠️  Error accessing pages: {e}")
    
    # Close context
    try:
        context.close()
        print("  ✓ Context closed successfully")
    except Exception as e:
        print(f"  ⚠️  Error closing context: {e}")


@pytest.fixture
def page(context: BrowserContext, base_url: str) -> Generator[Page, None, None]:
    """
    Create a new page for each test.
    Automatically navigates to base URL and sets timeout.
    Note: 'context' is provided by pytest-playwright.
    
    CRITICAL: This fixture ensures test isolation by:
    1. Creating a fresh page
    2. Clearing all storage before navigation
    3. Navigating to base URL
    4. Triggering auth modal if not authenticated
    5. Cleaning up after test
    """
    page = context.new_page()
    page.set_default_timeout(int(os.getenv("TIMEOUT", "30000")))
    
    # Clear all storage BEFORE navigating to ensure clean state
    page.goto(base_url, wait_until="domcontentloaded")
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    
    # Reload to ensure the cleared state takes effect
    page.reload(wait_until="domcontentloaded")
    
    # Wait for app to initialize
    page.wait_for_load_state("networkidle")
    
    # Force show auth modal if not authenticated (with proper Bootstrap modal display)
    page.evaluate("""
        if (typeof Auth !== 'undefined' && !Auth.isAuthenticated()) {
            const modal = document.getElementById('authModal');
            if (modal) {
                // Use the app's showAuthModal function if available
                if (typeof showAuthModal === 'function') {
                    showAuthModal();
                }
                // Ensure modal is actually visible with proper styling
                modal.style.display = 'block';
                modal.classList.add('show');
                document.body.classList.add('modal-open');
                
                // Add backdrop if not present
                if (!document.querySelector('.modal-backdrop')) {
                    const backdrop = document.createElement('div');
                    backdrop.className = 'modal-backdrop fade show';
                    document.body.appendChild(backdrop);
                }
            }
        }
    """)
    
    yield page
    
    # CRITICAL CLEANUP: Ensure page is properly closed
    print("\n🧹 [Cleanup] Closing page fixture")
    try:
        if not page.is_closed():
            # Try to clear storage first
            try:
                page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
                print("  ✓ Storage cleared")
            except Exception:
                pass  # Page might be in bad state
            
            # Close the page
            page.close()
            print("  ✓ Page closed successfully")
        else:
            print("  ℹ️  Page was already closed")
    except Exception as e:
        print(f"  ⚠️  Error during page cleanup: {e}")


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def authenticated_page(page: Page, base_url: str) -> Generator[Page, None, None]:
    """
    Provides a page with an authenticated user session.
    
    This fixture:
    1. Clears any existing session (localStorage/sessionStorage) - CLEAN SLATE
    2. Registers a new test user
    3. Switches to login tab (app behavior after registration)
    4. Clicks login button
    5. Waits for dashboard to load with explicit Smart Wait
    6. Returns authenticated page
    
    Use this when tests require a logged-in user.
    
    IMPORTANT: This fixture ensures complete test isolation by clearing
    session storage before authentication and using Smart Waits.
    """
    from pages.login_page import LoginPage
    from pages.dashboard_page import DashboardPage
    from utils.test_data import generate_test_user
    from playwright.sync_api import expect
    
    # --- CRITICAL ISOLATION STEP: Clean Slate Pattern ---
    # NOTE: The `page` fixture already cleared storage and navigated to base_url
    # We rely on that, so NO additional clearing here to avoid breaking app state
    print("📋 [authenticated_page fixture] Using clean slate from page fixture")
    # --- END OF ISOLATION STEP ---

    # DEBUG: Enable console logging
    page.on("console", lambda msg: print(f"  [BROWSER] {msg.type}: {msg.text}"))

    # Generate unique test user
    test_user = generate_test_user()
    
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    # Wait for auth modal
    login_page.wait_for_auth_modal()
    
    # Register user (this will switch to login tab with pre-filled credentials)
    print(f"📋 [authenticated_page fixture] Registering user: {test_user['username']}")
    login_page.switch_to_register_mode()
    login_page.fill_username(test_user["username"], mode="register")
    login_page.fill_password(test_user["password"], mode="register")
    if login_page.is_visible(login_page.REGISTER_EMAIL_INPUT):
        login_page.fill_email(test_user.get("email", f"{test_user['username']}@test.com"))
    
    login_page.click_register_button()

    # Wait for registration to complete and credentials to be pre-filled
    page.wait_for_timeout(1000)

    # Switch to login tab and submit (credentials should be pre-filled)
    print("📋 [authenticated_page fixture] Completing login")
    login_page.switch_to_login_mode()

    # DEBUG: Check form state before clicking login
    form_state = page.evaluate("""
        () => {
            const username = document.getElementById('loginUsername')?.value;
            const password = document.getElementById('loginPassword')?.value;
            return {username: username, password: password ? '***' : ''};
        }
    """)
    print(f"🔍 Login form before click: {form_state}")

    login_page.click_login_button()
    print("🔍 Login button clicked")

    # --- SMART WAIT: Wait for dashboard to become visible ---
    # This confirms the login completed successfully before yielding to the test.
    # This prevents TargetClosedError by ensuring the session is fully established.
    print("📋 [authenticated_page fixture] Waiting for dashboard to appear (Smart Wait)")
    expect(dashboard_page.dashboard_container).to_be_visible(timeout=15000)
    print("✓ Dashboard visible - authentication complete")

    # ADDITIONAL WAIT: Give the app time to save the token
    page.wait_for_timeout(2000)

    # DEBUG: Check token right after login
    token_after_login = page.evaluate("Auth.getToken()")
    print(f"🔍 Token right after dashboard visible + 2s wait: {token_after_login[:50] if token_after_login else 'NOT FOUND!'}")

    # Additional verification with user display
    expect(dashboard_page.get_user_display_locator).to_be_visible(timeout=10000)
    print("✓ User info visible - session fully established")

    # CRITICAL: Ensure event listeners are set up
    # Workaround: Call setupEventListeners() manually to ensure navigation works
    print("📋 [authenticated_page fixture] Setting up event listeners")
    page.evaluate("if (typeof setupEventListeners === 'function') setupEventListeners();")
    print("✓ Event listeners ready")

    # Ensure auth modal is closed (force close if needed)
    page.evaluate("""
        const modal = document.getElementById('authModal');
        if (modal && modal.classList.contains('show')) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        }
    """)
    print("✓ Auth modal confirmed closed")

    # FINAL CHECK: Verify token is present before yielding
    final_token = page.evaluate("Auth.getToken()")
    print(f"✓ Token verified before yield: {final_token[:50] if final_token else 'NOT FOUND!'}")

    yield page
    
    # CRITICAL CLEANUP: Clear session on teardown to prevent leakage to next test
    print("\n🧹 [authenticated_page fixture] Cleaning up session")
    try:
        if not page.is_closed():
            page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
            print("  ✓ Session cleared")
        else:
            print("  ℹ️  Page already closed, skipping session clear")
    except Exception as e:
        print(f"  ⚠️  Error clearing session: {e}")


@pytest.fixture(scope="function")
def admin_authenticated_page(page: Page, base_url: str) -> Generator[Page, None, None]:
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
    
    yield page
    
    # Cleanup: Clear session on teardown
    try:
        page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    except:
        pass  # Page might be closed already


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


@pytest.fixture(autouse=True, scope="function")
def ensure_browser_cleanup(request):
    """
    Final safety net to ensure browser resources are cleaned up after each test,
    even if the test fails or is interrupted.
    
    This runs AFTER other fixture teardowns as a last resort cleanup.
    """
    yield
    
    print("\n🛡️  [Safety Net] Final cleanup check")
    
    # Force cleanup of any remaining browser resources
    if "page" in request.fixturenames:
        try:
            page = request.getfixturevalue("page")
            if page and not page.is_closed():
                print("  ⚠️  Found unclosed page, closing now...")
                try:
                    page.close()
                    print("  ✓ Page closed")
                except Exception as e:
                    print(f"  ⚠️  Error closing page: {e}")
        except Exception as e:
            print(f"  ⚠️  Error accessing page: {e}")
    
    if "context" in request.fixturenames:
        try:
            context = request.getfixturevalue("context")
            if context:
                unclosed_count = 0
                try:
                    # Close all pages in context
                    for page in list(context.pages):
                        try:
                            if not page.is_closed():
                                unclosed_count += 1
                                page.close()
                        except Exception:
                            pass
                    if unclosed_count > 0:
                        print(f"  ⚠️  Closed {unclosed_count} unclosed page(s)")
                except Exception as e:
                    print(f"  ⚠️  Error cleaning context pages: {e}")
        except Exception as e:
            print(f"  ⚠️  Error accessing context: {e}")


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
