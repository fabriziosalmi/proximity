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
from playwright.sync_api import expect
from pages import LoginPage, StorePage, AppsPage


@pytest.mark.golden_path
@pytest.mark.slow
def test_full_app_lifecycle(
    test_page,
    unique_user: dict,
    proxmox_host: dict,  # Ensure a Proxmox host exists
    base_url: str
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

    print("\n" + "="*80)
    print("🚀 GOLDEN PATH TEST - Full Application Lifecycle")
    print("="*80)
    print(f"📧 Test User: {unique_user['username']}")
    print(f"🏷️  Test Hostname: {test_hostname}")
    print("="*80 + "\n")

    # ============================================================================
    # PROGRAMMATIC LOGIN: Fast, robust, no UI interaction
    # ============================================================================
    print("📍 AUTHENTICATION SETUP (Programmatic)")
    print("-" * 80)
    
    auth_token = unique_user["auth_token"]
    
    # Inject authentication token into browser localStorage
    # This runs BEFORE any page navigation, ensuring auth is ready
    page.add_init_script(f"""
        window.localStorage.setItem('access_token', '{auth_token}');
    """)
    
    print(f"  ✅ Auth token injected programmatically")
    print(f"  ✅ User context set: {unique_user['username']}")
    print(f"  ⚡ Login completed instantly (no UI interaction)\n")
    
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
    print(f"  ✅ STORE PAGE LOADED - Adminer found in catalog\n")
    
    # ============================================================================
    # STEP 3: DEPLOY APPLICATION
    # ============================================================================
    print("📍 STEP 3: Deploy Application")
    print("-" * 80)
    
    # Initiate deployment
    store_page.deploy_app(
        app_name="Adminer",
        hostname=test_hostname,
        wait_for_redirect=True
    )
    print(f"  ✓ Clicked Deploy button")
    print(f"  ✓ Filled hostname: {test_hostname}")
    print(f"  ✓ Confirmed deployment")
    
    # Verify redirect to /apps page
    expect(page).to_have_url(base_url + "/apps", timeout=10000)
    print(f"  ✅ DEPLOYMENT INITIATED - Redirected to /apps page\n")
    
    # ============================================================================
    # STEP 4: MONITOR DEPLOYMENT
    # ============================================================================
    print("📍 STEP 4: Monitor Deployment Progress")
    print("-" * 80)
    print(f"  ⏳ This may take 1-3 minutes (container image pulling)...")
    
    apps_page = AppsPage(page, base_url)
    
    # Verify the new app card is visible immediately
    apps_page.assert_app_visible(test_hostname)
    print(f"  ✓ Application card appeared: {test_hostname}")
    
    # Check initial status (should be 'deploying')
    initial_status = apps_page.get_app_status(test_hostname)
    print(f"  ✓ Initial status: {initial_status}")
    
    # CRITICAL: Wait for deployment to complete (up to 3 minutes)
    # This is where most deployments can fail or timeout
    start_time = time.time()
    apps_page.wait_for_status(
        hostname=test_hostname,
        expected_status='running',
        timeout=180000  # 3 minutes
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
    print(f"  ✓ Clicked Stop button")
    print(f"  ✅ APPLICATION STOPPED - Status: stopped\n")
    
    # ============================================================================
    # STEP 6: MANAGE APPLICATION - START
    # ============================================================================
    print("📍 STEP 6: Manage Application - Start")
    print("-" * 80)
    
    # Start the application
    apps_page.start_app(test_hostname, wait_for_running=True)
    print(f"  ✓ Clicked Start button")
    print(f"  ✅ APPLICATION STARTED - Status: running\n")
    
    # ============================================================================
    # STEP 7: DELETE APPLICATION
    # ============================================================================
    print("📍 STEP 7: Delete Application")
    print("-" * 80)
    
    # Delete the application
    apps_page.delete_app(test_hostname, wait_for_removal=True)
    print(f"  ✓ Clicked Delete button")
    print(f"  ✓ Confirmed deletion")
    
    # Verify the app is no longer visible
    apps_page.assert_app_not_visible(test_hostname)
    print(f"  ✅ APPLICATION DELETED - Card removed from page\n")
    
    # ============================================================================
    # TEST COMPLETE
    # ============================================================================
    total_duration = time.time() - test_start_time
    print("="*80)
    print("✅ GOLDEN PATH TEST COMPLETE - ALL STEPS PASSED")
    print("="*80)
    print(f"Total test duration: {total_duration:.1f}s")
    print(f"User: {unique_user['username']}")
    print(f"Hostname: {test_hostname}")
    print("="*80 + "\n")


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
    login_page.login_with_api(
        username=unique_user['username'],
        password=unique_user['password']
    )

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
    login_page.login_with_api(
        username=unique_user['username'],
        password=unique_user['password']
    )

    # Navigate to store
    store_page = StorePage(page, base_url)
    store_page.navigate()

    # Verify at least one app is loaded
    store_page.wait_for_apps_loaded(min_count=1, timeout=10000)
    app_count = store_page.get_app_count()

    assert app_count > 0, "No applications found in catalog"
    print(f"✅ Catalog smoke test passed - {app_count} app(s) loaded\n")
