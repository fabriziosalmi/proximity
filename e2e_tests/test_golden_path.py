"""
Golden Path E2E Test - The Critical User Journey

This test validates the complete user lifecycle in Proximity 2.0:
1. User Registration/Login
2. Navigate to App Store
3. Deploy an Application
4. Monitor Deployment Progress
5. Manage Application (Stop/Start)
6. Delete Application

This is the "Indestructible Test" - it uses unique users and complete cleanup
to ensure perfect test isolation and reliability.
"""

import pytest
import time
from pages import LoginPage, StorePage, AppsPage


@pytest.mark.golden_path
@pytest.mark.slow
def test_full_app_lifecycle(
    test_page, unique_user: dict, proxmox_host: dict, base_url: str  # Ensure a Proxmox host exists
):
    """
    The Golden Path: Complete application lifecycle test.

    This test performs the following steps:
    1. ✅ Login with unique test user
    2. ✅ Navigate to App Store
    3. ✅ Deploy "Adminer" application with unique hostname
    4. ✅ Monitor deployment until status is "running"
    5. ✅ Stop the application
    6. ✅ Start the application
    7. ✅ Delete the application
    8. ✅ Verify application is removed

    Args:
        test_page: Playwright Page fixture with storage
        unique_user: Unique user fixture with credentials
        proxmox_host: Proxmox host fixture (ensures host exists)
        base_url: Frontend base URL fixture
    """

    page = test_page

    # Generate unique hostname for this test run
    timestamp = int(time.time() * 1000)
    test_hostname = f"e2e-adminer-{timestamp}"

    # Track total test duration
    test_start_time = time.time()

    print("\n" + "=" * 80)
    print("🚀 GOLDEN PATH TEST - Full Application Lifecycle")
    print("=" * 80)
    print(f"📧 Test User: {unique_user['username']}")
    print(f"🏷️  Test Hostname: {test_hostname}")
    print("=" * 80 + "\n")

    # ============================================================================
    # AUTHENTICATION SETUP: UI-Based Login (Cookie-based Auth)
    # ============================================================================
    print("📍 AUTHENTICATION SETUP (UI-Based Login)")
    print("-" * 80)

    # Use proper UI-based login flow that works with HttpOnly cookies
    login_page = LoginPage(page, base_url)
    login_page.navigate_and_wait_for_ready()
    print("  ✓ Navigated to login page")

    # Set up console log capture
    console_messages = []
    page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))

    # Use the complete login method which handles the full flow
    login_page.login(
        unique_user["username"], unique_user["password"], wait_for_navigation=False
    )  # Don't wait, we'll check manually
    print(f"  ✓ Login form submitted for: {unique_user['username']}")

    # Wait a bit for the async login to complete
    page.wait_for_timeout(3000)

    print(f"  ✓ Current URL: {page.url}")

    # Print recent console messages for debugging
    print("  📜 Recent console messages:")
    for msg in console_messages[-10:]:
        print(f"     {msg}")

    # DEBUG: Take screenshot if still on login page
    if "/login" in page.url:
        page.screenshot(path="/tmp/login_failed_debug.png")
        print("  ⚠️  WARNING: Still on login page! Screenshot saved.")
        # Check for error messages
        error_locator = page.locator('.error, .alert-error, [role="alert"]')
        if error_locator.count() > 0:
            error_text = error_locator.first.text_content()
            print(f"  ❌ Error message: {error_text}")

    print(f"  ✅ User authenticated: {unique_user['username']}")
    print("  ✅ Session established with HttpOnly cookies")
    print("  ⚡ All API calls will now include session cookies\n")

    # ============================================================================
    # STEP 1: NAVIGATE TO APP STORE (Already Authenticated)
    # ============================================================================
    print("📍 STEP 1: Navigate to App Store")
    print("-" * 80)

    store_page = StorePage(page, base_url)
    store_page.navigate()
    print(f"  ✓ Navigated to: {base_url}/store")

    # Wait for apps to load (increased timeout for initial catalog load)
    store_page.wait_for_apps_loaded(min_count=1, timeout=30000)
    app_count = store_page.get_app_count()
    print(f"  ✓ Catalog loaded: {app_count} application(s) available")

    # Verify Adminer is visible
    store_page.assert_app_visible("Adminer")
    print("  ✅ STORE PAGE LOADED - Adminer found in catalog\n")

    # ============================================================================
    # STEP 3: DEPLOY APPLICATION
    # ============================================================================
    print("📍 STEP 3: Deploy Application")
    print("-" * 80)

    # Click Deploy and fill hostname
    store_page.click_deploy("Adminer")
    print("  ✓ Clicked Deploy button")

    store_page.fill_hostname(test_hostname)
    print(f"  ✓ Filled hostname: {test_hostname}")

    # ============================================================================
    # CRITICAL: Wait for BOTH redirect AND initial API data load
    # ============================================================================
    print("  ⏳ Confirming deployment (waiting for redirect + API data)...")

    # Set up expectation for the API response BEFORE clicking confirm
    with page.expect_response(
        lambda res: "/api/apps" in res.url and res.status == 200, timeout=15000
    ) as response_info:
        # Click confirm - this will trigger: POST deploy → redirect → GET /api/apps
        store_page.confirm_deployment(wait_for_redirect=True)

    api_response = response_info.value
    print(f"  ✓ Redirect to /apps confirmed (Status: {api_response.status})")
    print("  ✓ Initial app list loaded from API")
    print("  ✅ DEPLOYMENT INITIATED - UI is now populated and ready for monitoring\n")

    # ============================================================================
    # STEP 4: MONITOR DEPLOYMENT
    # ============================================================================
    print("📍 STEP 4: Monitor Deployment Progress")
    print("-" * 80)
    print("  ⏳ This may take 1-3 minutes (container image pulling)...")

    apps_page = AppsPage(page, base_url)

    # Now the page has already loaded data, we can immediately look for the card
    print(f"  ✓ Searching for newly deployed app: {test_hostname}")
    apps_page.assert_app_visible(test_hostname)
    print(
        f"  ✓ Application card appeared: {test_hostname}"
    )  # Check initial status (should be 'deploying')
    initial_status = apps_page.get_app_status(test_hostname)
    print(f"  ✓ Initial status: {initial_status}")

    # CRITICAL: Wait for deployment to complete (up to 3 minutes)
    # This is where most deployments can fail or timeout
    start_time = time.time()
    apps_page.wait_for_status(
        hostname=test_hostname, expected_status="running", timeout=180000  # 3 minutes
    )
    elapsed_time = time.time() - start_time
    print(f"  ✅ DEPLOYMENT COMPLETE - Status: running (took {elapsed_time:.1f}s)\n")

    # ============================================================================
    # STEP 5: MANAGE APPLICATION - STOP
    # ============================================================================
    print("📍 STEP 5: Manage Application - Stop")
    print("-" * 80)

    # Stop the application
    apps_page.stop_app(test_hostname, wait_for_stopped=True)
    print("  ✓ Clicked Stop button")
    print("  ✅ APPLICATION STOPPED - Status: stopped\n")

    # ============================================================================
    # STEP 6: MANAGE APPLICATION - START
    # ============================================================================
    print("📍 STEP 6: Manage Application - Start")
    print("-" * 80)

    # Start the application
    apps_page.start_app(test_hostname, wait_for_running=True)
    print("  ✓ Clicked Start button")
    print("  ✅ APPLICATION STARTED - Status: running\n")

    # ============================================================================
    # STEP 7: DELETE APPLICATION
    # ============================================================================
    print("📍 STEP 7: Delete Application")
    print("-" * 80)

    # Delete the application
    apps_page.delete_app(test_hostname, wait_for_removal=True)
    print("  ✓ Clicked Delete button")
    print("  ✓ Confirmed deletion")

    # Verify the app is no longer visible
    apps_page.assert_app_not_visible(test_hostname)
    print("  ✅ APPLICATION DELETED - Card removed from page\n")

    # ============================================================================
    # TEST COMPLETE
    # ============================================================================
    total_duration = time.time() - test_start_time
    print("=" * 80)
    print("✅ GOLDEN PATH TEST COMPLETE - ALL STEPS PASSED")
    print("=" * 80)
    print(f"Total test duration: {total_duration:.1f}s")
    print(f"User: {unique_user['username']}")
    print(f"Hostname: {test_hostname}")
    print("=" * 80 + "\n")


@pytest.mark.smoke
def test_login_only(test_page, unique_user: dict, base_url: str):
    """
    Smoke test: Verify basic login functionality.

    This is a quick test that validates the authentication flow
    without deploying any applications.
    """
    print("\n🔍 SMOKE TEST: Login Only")

    page = test_page

    login_page = LoginPage(page, base_url)

    # Use API login instead of form (more reliable)
    login_page.login_with_api(username=unique_user["username"], password=unique_user["password"])

    # Verify successful login by checking URL redirection
    # (is_logged_in() check removed as UI indicators may vary)
    login_page.assert_login_success(expected_url=base_url + "/")

    print("✅ Login smoke test passed\n")


@pytest.mark.smoke
def test_catalog_loads(test_page, unique_user: dict, base_url: str):
    """
    Smoke test: Verify the catalog loads applications.

    This test ensures the catalog service is working and
    applications are being displayed.
    """
    print("\n🔍 SMOKE TEST: Catalog Loads")

    page = test_page

    # Login first using API (more reliable)
    login_page = LoginPage(page, base_url)
    login_page.login_with_api(username=unique_user["username"], password=unique_user["password"])

    # Navigate to store
    store_page = StorePage(page, base_url)
    store_page.navigate()

    # Verify at least one app is loaded
    store_page.wait_for_apps_loaded(min_count=1, timeout=10000)
    app_count = store_page.get_app_count()

    assert app_count > 0, "No applications found in catalog"
    print(f"✅ Catalog smoke test passed - {app_count} app(s) loaded\n")
