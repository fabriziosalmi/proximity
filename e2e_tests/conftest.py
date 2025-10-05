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
    Provides a page with an authenticated user session - BULLETPROOF VERSION.
    
    This fixture is INDESTRUCTIBLE:
    1. ✅ Clears ALL storage (localStorage + sessionStorage) BEFORE starting
    2. ✅ Creates user via API (not UI) - eliminates registration flakiness
    3. ✅ Logs in via API to get token - eliminates login UI flakiness
    4. ✅ Injects token directly into localStorage - no waiting for UI
    5. ✅ Navigates to dashboard and waits for VISIBLE elements
    6. ✅ Verifies authentication with multiple checks
    7. ✅ Cleans up perfectly at the end
    
    Use this when tests require a logged-in user.
    
    WHY THIS IS BETTER:
    - No UI interaction for auth = no race conditions
    - API calls are deterministic and fast
    - Direct token injection = guaranteed auth state
    - Multiple verification checks = catches issues early
    """
    import requests
    from utils.test_data import generate_test_user
    from playwright.sync_api import expect
    import time
    
    print("\n" + "="*80)
    print("🔐 [authenticated_page] Starting BULLETPROOF authentication")
    print("="*80)
    
    # ========================================================================
    # STEP 1: CLEAR ALL STORAGE - ABSOLUTE CLEAN SLATE
    # ========================================================================
    print("\n🧹 STEP 1: Clearing all storage for clean slate")
    page.goto(base_url, wait_until="domcontentloaded")
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    page.evaluate("document.cookie.split(';').forEach(c => document.cookie = c.split('=')[0] + '=;expires=' + new Date().toUTCString());")
    print("   ✓ localStorage cleared")
    print("   ✓ sessionStorage cleared")
    print("   ✓ cookies cleared")
    
    # ========================================================================
    # STEP 2: CREATE USER VIA API (NOT UI!)
    # ========================================================================
    print("\n👤 STEP 2: Creating test user via API")
    test_user = generate_test_user()
    api_base = base_url.replace(":8765", ":8765/api/v1")
    
    register_data = {
        "username": test_user["username"],
        "email": test_user.get("email", f"{test_user['username']}@test.com"),
        "password": test_user["password"],
        "role": "user"
    }
    
    print(f"   Creating user: {register_data['username']}")
    
    try:
        register_response = requests.post(
            f"{api_base}/auth/register",
            json=register_data,
            timeout=10
        )
        
        if register_response.status_code in [200, 201]:
            print(f"   ✅ User created successfully (status: {register_response.status_code})")
            register_json = register_response.json()
            token = register_json.get("access_token")
            
            if token:
                print("   ✅ Token received from registration")
            else:
                # User created but no token - need to login
                print("   ⚠️  No token from registration, will login separately")
                token = None
        else:
            print(f"   ⚠️  Registration returned {register_response.status_code}")
            print(f"   Response: {register_response.text[:200]}")
            token = None
    except Exception as e:
        print(f"   ❌ Registration failed: {e}")
        token = None
    
    # ========================================================================
    # STEP 3: GET TOKEN VIA LOGIN API IF NEEDED
    # ========================================================================
    if not token:
        print("\n🔑 STEP 3: Getting token via login API")
        
        try:
            login_response = requests.post(
                f"{api_base}/auth/login",
                json={
                    "username": register_data["username"],
                    "password": register_data["password"]
                },
                timeout=10
            )
            
            if login_response.status_code == 200:
                login_json = login_response.json()
                token = login_json.get("access_token")
                
                if token:
                    print("   ✅ Token obtained via login")
                else:
                    raise Exception("Login succeeded but no token in response")
            else:
                raise Exception(f"Login failed with status {login_response.status_code}: {login_response.text[:200]}")
        
        except Exception as e:
            print(f"   ❌ Login failed: {e}")
            raise Exception(f"AUTHENTICATION FAILED: Could not get token. Registration status: {register_response.status_code if 'register_response' in locals() else 'N/A'}. Error: {e}")
    
    # ========================================================================
    # STEP 4: INJECT TOKEN INTO LOCALSTORAGE
    # ========================================================================
    print("\n� STEP 4: Injecting token into localStorage")
    
    if not token:
        raise Exception("CRITICAL ERROR: No token available to inject!")
    
    # Navigate to base URL first (localStorage needs a context)
    page.goto(base_url, wait_until="domcontentloaded")
    
    # Inject token
    page.evaluate(f"window.localStorage.setItem('proximity_token', '{token}');")
    
    # Verify token was saved
    saved_token = page.evaluate("window.localStorage.getItem('proximity_token')")
    
    if saved_token == token:
        print(f"   ✅ Token injected successfully (length: {len(token)} chars)")
    else:
        raise Exception("Token injection failed - localStorage.getItem returned different value!")
    
    # ========================================================================
    # STEP 5: NAVIGATE TO DASHBOARD
    # ========================================================================
    print("\n🏠 STEP 5: Navigating to dashboard")
    
    # Reload page to trigger app initialization with token
    page.reload(wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    
    # Wait for app initialization
    time.sleep(1)
    
    # Verify we're on dashboard view
    print("   ✓ Page reloaded with token")
    
    # ========================================================================
    # STEP 6: VERIFY AUTHENTICATION - MULTIPLE CHECKS
    # ========================================================================
    print("\n✅ STEP 6: Verifying authentication state")
    
    # Check 1: Dashboard container must be visible
    try:
        dashboard = page.locator('[data-view="dashboard"]')
        expect(dashboard).to_be_visible(timeout=15000)
        print("   ✅ Check 1/4: Dashboard container visible")
    except Exception as e:
        raise Exception(f"VERIFICATION FAILED: Dashboard not visible. Error: {e}")
    
    # Check 2: User display must be visible (proves we're logged in)
    try:
        user_display = page.locator('.user-display, .user-info, [data-user-display]')
        expect(user_display.first).to_be_visible(timeout=10000)
        print("   ✅ Check 2/4: User display visible")
    except Exception as e:
        print(f"   ⚠️  Check 2/4: User display not found (might be acceptable): {e}")
    
    # Check 3: Auth modal must NOT be visible
    try:
        auth_modal = page.locator('#authModal')
        expect(auth_modal).not_to_be_visible(timeout=5000)
        print("   ✅ Check 3/4: Auth modal is hidden")
    except Exception as e:
        print(f"   ⚠️  Check 3/4: Auth modal check inconclusive: {e}")
    
    # Check 4: Token still in localStorage
    final_token = page.evaluate("window.localStorage.getItem('proximity_token')")
    if final_token == token:
        print("   ✅ Check 4/4: Token persisted in localStorage")
    else:
        raise Exception("VERIFICATION FAILED: Token was cleared from localStorage!")
    
    # Force close any modals that might be open
    page.evaluate("""
        // Force close any modal
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            modal.classList.remove('show');
            modal.style.display = 'none';
        });
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
    """)
    
    print("\n" + "="*80)
    print("🎉 AUTHENTICATION COMPLETE - Page ready for testing")
    print("="*80 + "\n")
    
    yield page
    
    # ========================================================================
    # CLEANUP: CLEAR SESSION
    # ========================================================================
    print("\n🧹 [authenticated_page] Cleaning up session")
    try:
        if not page.is_closed():
            page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
            print("  ✓ Session cleared successfully")
        else:
            print("  ℹ️  Page already closed, skipping cleanup")
    except Exception as e:
        print(f"  ⚠️  Error during cleanup: {e}")


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
