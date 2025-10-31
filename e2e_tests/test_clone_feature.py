"""
Clone Feature E2E Test - Application Cloning Workflow

This test validates the complete clone feature in Proximity 2.0 using two approaches:

1. test_clone_application_workflow: Full UI-driven test (deploys via UI)
2. test_clone_application_lifecycle: Faster API-based test (uses deployed_app fixture)

Both tests ensure the EPIC 2 "Clone Application" feature works end-to-end.
"""
import pytest
import time
import re
from playwright.sync_api import expect, Page
from pages import LoginPage, StorePage, AppsPage
from utils.auth import cookie_login  # Use cookie-based auth instead of JWT


@pytest.mark.clone
@pytest.mark.fast
def test_clone_application_lifecycle(
    page: Page,  # ← Standard page fixture (no pre-auth)
    deployed_app: dict,  # ← Backend setup (includes token)
    base_url: str
):
    """
    FAST Clone Test: Uses deployed_app fixture (API-based deployment).
    
    This test demonstrates the ROBUST architectural pattern:
    1. Backend setup via API (deployed_app fixture - takes ~60s)
    2. Browser authentication via token injection (instant, no race condition)
    3. UI interaction testing (clone workflow)
    
    This pattern eliminates the TargetClosedError by ensuring the browser
    is only involved AFTER the slow backend setup completes.
    
    Steps:
    1. ✅ Start with deployed app from API (no browser yet)
    2. ✅ Inject auth token into browser (programmatic login)
    3. ✅ Navigate to /apps
    4. ✅ Verify source app is visible and running
    5. ✅ Click Clone button
    6. ✅ Fill clone modal with new hostname
    7. ✅ Submit clone request
    8. ✅ Verify clone appears with 'cloning' status
    9. ✅ Wait for clone to reach 'running' status
    10. ✅ Verify both apps are running
    11. ✅ Cleanup handled by fixtures
    
    Args:
        page: Standard Playwright Page (no pre-authentication)
        deployed_app: Pre-deployed source app with auth token (from fixture)
        base_url: Frontend base URL
    """
    # ============================================================================
    # BULLETPROOF COOKIE-BASED LOGIN:
    # Injects session cookies + JWT token + waits for ApiClient readiness signal
    # ============================================================================
    print(f"\n🔐 Performing hybrid authentication (cookies + JWT)...")
    print(f"DEBUG: auth_token = {deployed_app.get('auth_token', 'NOT FOUND')[:50] if deployed_app.get('auth_token') else 'NONE'}")
    cookie_login(page, deployed_app["session_cookies"], base_url, access_token=deployed_app["auth_token"])
    print(f"  ✅ ApiClient confirmed ready for authenticated requests")
    
    # ============================================================================
    # NOW THE PAGE IS READY FOR AUTHENTICATED NAVIGATION
    # ============================================================================
    apps_page = AppsPage(page, base_url)
    
    # Extract source app details
    source_hostname = deployed_app["hostname"]
    source_id = deployed_app["id"]
    
    # Generate unique hostname for clone
    timestamp = int(time.time() * 1000)
    clone_hostname = f"e2e-clone-copy-{timestamp}"
    
    # Track test duration
    test_start_time = time.time()
    
    print("\n" + "="*80)
    print("🧬 CLONE LIFECYCLE TEST (API-Based) - Fast Clone Workflow")
    print("="*80)
    print(f"🏷️  Source: {source_hostname} (ID: {source_id})")
    print(f"🏷️  Clone: {clone_hostname}")
    print("="*80 + "\n")
    
    # ============================================================================
    # STEP 1: NAVIGATE TO /APPS
    # ============================================================================
    print("📍 STEP 1: Navigate to Apps Page")
    print("-" * 80)
    
    apps_page.navigate()
    page.wait_for_load_state("networkidle")
    print(f"  ✅ Navigated to: {base_url}/apps\n")
    
    # ============================================================================
    # STEP 2: VERIFY SOURCE APP IS VISIBLE AND RUNNING
    # ============================================================================
    print(f"📍 STEP 2: Verify Source App '{source_hostname}' Exists")
    print("-" * 80)
    
    source_card = apps_page.get_app_card_by_hostname(source_hostname)
    expect(source_card).to_be_visible(timeout=10000)
    print(f"  ✓ Source app card visible")
    
    source_status = apps_page.get_app_status(source_hostname)
    assert source_status == "running", \
        f"Expected source to be 'running', got '{source_status}'"
    print(f"  ✅ Source app status: {source_status}\n")
    
    # ============================================================================
    # STEP 3: CLICK CLONE BUTTON
    # ============================================================================
    print("📍 STEP 3: Initiate Clone")
    print("-" * 80)
    
    clone_button = source_card.locator('[data-testid="clone-button"]')
    expect(clone_button).to_be_visible(timeout=5000)
    expect(clone_button).to_be_enabled(timeout=5000)
    print(f"  ✓ Clone button found and enabled")
    
    clone_button.click()
    print(f"  ✓ Clicked Clone button")
    
    # Wait for clone modal
    clone_modal = page.locator('text=Clone Application').first
    expect(clone_modal).to_be_visible(timeout=5000)
    print(f"  ✅ Clone modal appeared\n")
    
    # ============================================================================
    # STEP 4: FILL CLONE MODAL
    # ============================================================================
    print(f"📍 STEP 4: Fill Clone Modal")
    print("-" * 80)
    
    hostname_input = page.locator('input#new-hostname').first
    expect(hostname_input).to_be_visible(timeout=5000)
    
    # Clear and enter new hostname
    hostname_input.click()
    hostname_input.fill('')
    hostname_input.type(clone_hostname)
    print(f"  ✓ Entered new hostname: {clone_hostname}")
    
    # Submit clone
    submit_button = page.locator('button:has-text("Clone Application")').first
    expect(submit_button).to_be_enabled(timeout=5000)
    submit_button.click()
    print(f"  ✓ Clicked 'Clone Application' button")
    
    # Wait for modal to close
    expect(clone_modal).to_be_hidden(timeout=5000)
    print(f"  ✅ Clone request submitted\n")
    
    # ============================================================================
    # STEP 5: VERIFY CLONE APPEARS WITH CLONING STATUS
    # ============================================================================
    print("📍 STEP 5: Verify Clone Appears")
    print("-" * 80)
    
    # Wait for clone card to appear using our fortified selector
    clone_card = apps_page.get_app_card_by_hostname(clone_hostname)
    expect(clone_card).to_be_visible(timeout=10000)
    print(f"  ✓ Clone card appeared: {clone_hostname}")
    
    # Check initial status using our fortified status reader
    clone_initial_status = apps_page.get_app_status(clone_hostname)
    print(f"  ✓ Clone initial status: {clone_initial_status}")
    assert clone_initial_status in ['cloning', 'running'], \
        f"Expected 'cloning' or 'running', got '{clone_initial_status}'"
    print(f"  ✅ Clone visible with valid status\n")
    
    # ============================================================================
    # STEP 6: MONITOR CLONE UNTIL RUNNING
    # ============================================================================
    print("📍 STEP 6: Monitor Clone Progress")
    print("-" * 80)
    print(f"  ⏳ Waiting for clone to reach 'running' status...")
    print(f"  ⏳ Timeout: 10 minutes (LXC cloning can be slow)...")
    
    clone_start_time = time.time()
    clone_timeout = 600000  # 10 minutes
    
    apps_page.wait_for_status(clone_hostname, 'running', timeout=clone_timeout)
    
    clone_duration = time.time() - clone_start_time
    print(f"  ✅ Clone reached 'running' status (took {clone_duration:.1f}s)\n")
    
    # ============================================================================
    # STEP 7: VERIFY BOTH APPS ARE RUNNING
    # ============================================================================
    print("📍 STEP 7: Final Verification")
    print("-" * 80)
    
    # Verify source still running
    source_status_final = apps_page.get_app_status(source_hostname)
    assert source_status_final == 'running', \
        f"Source should still be running, got '{source_status_final}'"
    print(f"  ✓ Source: {source_hostname} - Status: {source_status_final}")
    
    # Verify clone running
    clone_status_final = apps_page.get_app_status(clone_hostname)
    assert clone_status_final == 'running', \
        f"Clone should be running, got '{clone_status_final}'"
    print(f"  ✓ Clone: {clone_hostname} - Status: {clone_status_final}")
    
    # Both cards visible
    expect(source_card).to_be_visible()
    expect(apps_page.get_app_card_by_hostname(clone_hostname)).to_be_visible()
    print(f"  ✅ Both apps visible and running\n")

    # ============================================================================
    # STEP 8: VERIFY 3D FLIP ANIMATION (LIVING INTERFACE)
    # ============================================================================
    print("📍 STEP 8: Verify 3D Flip Animation")
    print("-" * 80)
    print(f"  🎨 Testing 'Living Interface' features...")

    # Flip the clone card to reveal technical details
    apps_page.flip_card(clone_hostname)
    print(f"  ✓ Triggered flip animation on: {clone_hostname}")

    # Verify the is-flipped class was applied (confirms state management)
    apps_page.assert_card_is_flipped(clone_hostname)
    print(f"  ✓ 'is-flipped' class applied successfully")
    print(f"  ✅ Flip animation mechanism verified\n")

    # ============================================================================
    # TEST SUMMARY
    # ============================================================================
    total_duration = time.time() - test_start_time
    
    print("="*80)
    print("✅ CLONE LIFECYCLE TEST COMPLETE")
    print("="*80)
    print(f"Total duration: {total_duration:.1f}s")
    print(f"Source: {source_hostname}")
    print(f"Clone: {clone_hostname}")
    print(f"Note: Cleanup handled by fixtures (deployed_app & unique_user)")
    print("="*80 + "\n")


@pytest.mark.clone
@pytest.mark.slow
def test_clone_application_workflow(
    test_page,
    unique_user: dict,
    proxmox_host: dict,
    base_url: str
):
    """
    FULL Clone Test: Complete UI-driven workflow (deploys via UI).
    
    This is the original comprehensive test that validates the entire flow
    including manual deployment through the Store UI.

    This test performs the following steps:
    1. ✅ Login with unique test user
    2. ✅ Deploy source application (Adminer)
    3. ✅ Wait for source app to be running
    4. ✅ Click Clone button on source app
    5. ✅ Fill clone modal with new hostname
    6. ✅ Submit clone request
    7. ✅ Verify clone appears with status "cloning"
    8. ✅ Monitor clone until status is "running"
    9. ✅ Verify both apps are running
    10. ✅ Delete both applications
    11. ✅ Verify both are removed

    Args:
        test_page: Playwright Page fixture with storage
        unique_user: Unique user fixture with credentials
        proxmox_host: Proxmox host fixture (ensures host exists)
        base_url: Frontend base URL fixture
    """

    page = test_page

    # Generate unique hostnames for this test run
    timestamp = int(time.time() * 1000)
    source_hostname = f"e2e-clone-source-{timestamp}"
    clone_hostname = f"e2e-clone-copy-{timestamp}"

    # Track total test duration
    test_start_time = time.time()

    print("\n" + "="*80)
    print("🧬 CLONE FEATURE TEST - Application Cloning Workflow")
    print("="*80)
    print(f"📧 Test User: {unique_user['username']}")
    print(f"🏷️  Source Hostname: {source_hostname}")
    print(f"🏷️  Clone Hostname: {clone_hostname}")
    print("="*80 + "\n")

    # ============================================================================
    # AUTHENTICATION SETUP: UI-Based Login (Cookie-based Auth)
    # ============================================================================
    print("📍 AUTHENTICATION SETUP (UI-Based Login)")
    print("-" * 80)
    
    # Use proper UI-based login flow that works with HttpOnly cookies
    login_page = LoginPage(page, base_url)
    login_page.navigate_and_wait_for_ready()
    print(f"  ✓ Navigated to login page")
    
    # Use the complete login method which handles the full flow
    login_page.login(unique_user["username"], unique_user["password"], wait_for_navigation=True)
    print(f"  ✓ Login completed for: {unique_user['username']}")
    print(f"  ✓ Current URL: {page.url}")
    
    # Wait for authStore to initialize with the session
    page.wait_for_timeout(1000)
    
    print(f"  ✅ User authenticated: {unique_user['username']}")
    print(f"  ✅ Session established with HttpOnly cookies")
    print(f"  ⚡ All API calls will now include session cookies\n")

    # ============================================================================
    # STEP 1: DEPLOY SOURCE APPLICATION (Already Authenticated)
    # ============================================================================
    print("📍 STEP 1: Deploy Source Application")
    print("-" * 80)

    store_page = StorePage(page, base_url)
    store_page.navigate()
    print(f"  ✓ Navigated to: {base_url}/store")

    # Wait for catalog to load
    store_page.wait_for_apps_loaded()
    app_count = store_page.get_app_count()
    print(f"  ✓ Catalog loaded: {app_count} application(s) available")
    
    # Get first available app name
    # Find the first catalog card and extract its title
    first_card = page.locator('[data-testid^="catalog-card-"]').first
    expect(first_card).to_be_visible(timeout=5000)
    
    # Get the app name from the card
    app_name_locator = first_card.locator('[data-testid="app-name"]').first
    app_name = app_name_locator.inner_text().strip()
    
    print(f"  ✓ Found app in catalog: {app_name}")

    # Click Deploy button and fill hostname
    store_page.click_deploy(app_name)
    print(f"  ✓ Clicked Deploy button")
    
    store_page.fill_hostname(source_hostname)
    print(f"  ✓ Filled hostname: {source_hostname}")
    
    # ============================================================================
    # CRITICAL: Wait for BOTH redirect AND initial API data load
    # ============================================================================
    print(f"  ⏳ Confirming deployment (waiting for redirect + API data)...")
    
    # Set up expectation for the API response BEFORE clicking confirm
    # This ensures we catch the API call that happens after redirect
    with page.expect_response(
        lambda res: "/api/apps" in res.url and res.status == 200,
        timeout=15000
    ) as response_info:
        # Click confirm - this will trigger: POST deploy → redirect → GET /api/apps
        store_page.confirm_deployment(wait_for_redirect=True)
    
    # Get the intercepted response
    api_response = response_info.value
    print(f"  ✓ Redirect to /apps confirmed (Status: {api_response.status})")
    print(f"  ✓ Initial app list loaded from API")
    print(f"  ✅ DEPLOYMENT INITIATED - UI is now populated and ready for monitoring\n")

    # ============================================================================
    # STEP 2: WAIT FOR SOURCE APP TO BE RUNNING
    # ============================================================================
    print("📍 STEP 2: Monitor Source App Deployment")
    print("-" * 80)
    print(f"  ⏳ This may take 1-3 minutes (container image pulling)...")

    apps_page = AppsPage(page, base_url)
    
    # Now the page has already loaded data, we can immediately look for the card
    print(f"  ✓ Searching for newly deployed app: {source_hostname}")

    # Wait for app card to appear using page object method
    try:
        app_card = apps_page.get_app_card_by_hostname(source_hostname)
        expect(app_card).to_be_visible(timeout=15000)
        print(f"  ✓ Application card appeared: {source_hostname}")
    except Exception as e:
        # Debug: print all visible cards
        all_cards = page.locator('[data-app-hostname]').all()
        hostnames = [card.get_attribute('data-app-hostname') for card in all_cards]
        print(f"  ⚠️  Could not find card for {source_hostname}")
        print(f"  ⚠️  Available cards: {hostnames}")
        raise

    # Get initial status
    initial_status = apps_page.get_app_status(source_hostname)
    print(f"  ✓ Initial status: {initial_status}")

    # Wait for running status
    deployment_timeout = 180000  # 3 minutes
    apps_page.wait_for_status(source_hostname, 'running', timeout=deployment_timeout)

    deployment_duration = time.time() - test_start_time
    print(f"  ✅ SOURCE APP DEPLOYED - Status: running (took {deployment_duration:.1f}s)\n")

    # ============================================================================
    # STEP 3: CLONE THE APPLICATION
    # ============================================================================
    print("📍 STEP 3: Clone Application")
    print("-" * 80)

    # Click Clone button
    clone_button_selector = f'[data-app-hostname="{source_hostname}"] [data-testid="clone-button"]'
    clone_button = page.locator(clone_button_selector).first
    
    # Wait for clone button to be visible and enabled
    expect(clone_button).to_be_visible(timeout=5000)
    expect(clone_button).to_be_enabled(timeout=5000)
    print(f"  ✓ Clone button found and enabled")

    clone_button.click()
    print(f"  ✓ Clicked Clone button")

    # Wait for clone modal to appear
    clone_modal = page.locator('text=Clone Application').first
    expect(clone_modal).to_be_visible(timeout=5000)
    print(f"  ✓ Clone modal appeared")

    # Fill in new hostname
    hostname_input = page.locator('input#new-hostname').first
    expect(hostname_input).to_be_visible(timeout=5000)
    
    # Clear auto-suggested hostname and enter our test hostname
    hostname_input.click()
    hostname_input.fill('')  # Clear
    hostname_input.type(clone_hostname)
    print(f"  ✓ Filled new hostname: {clone_hostname}")

    # Submit clone request
    submit_button = page.locator('button:has-text("Clone Application")').first
    expect(submit_button).to_be_enabled(timeout=5000)
    submit_button.click()
    print(f"  ✓ Clicked 'Clone Application' button")

    # Wait for modal to close
    expect(clone_modal).to_be_hidden(timeout=5000)
    print(f"  ✅ CLONE INITIATED - Modal closed\n")

    # ============================================================================
    # STEP 4: VERIFY CLONE APPEARS WITH "CLONING" STATUS
    # ============================================================================
    print("📍 STEP 4: Verify Clone Appears")
    print("-" * 80)

    # Wait for clone card to appear (optimistic update)
    clone_card = apps_page.get_app_card_by_hostname(clone_hostname)
    expect(clone_card).to_be_visible(timeout=10000)
    print(f"  ✓ Clone application card appeared: {clone_hostname}")

    # Check initial clone status (should be 'cloning')
    clone_initial_status = apps_page.get_app_status(clone_hostname)
    print(f"  ✓ Clone initial status: {clone_initial_status}")
    
    # It might be 'cloning' or already 'running' depending on timing
    assert clone_initial_status in ['cloning', 'running'], \
        f"Expected clone status to be 'cloning' or 'running', got '{clone_initial_status}'"
    print(f"  ✅ CLONE CARD VISIBLE with valid status\n")

    # ============================================================================
    # STEP 6: MONITOR CLONE UNTIL RUNNING
    # ============================================================================
    print("📍 STEP 6: Monitor Clone Progress")
    print("-" * 80)
    print(f"  ⏳ Waiting for clone to reach 'running' status...")
    print(f"  ⏳ This may take several minutes (LXC cloning + container start)...")

    # Clone operation can take longer (up to 10 minutes for full clone)
    clone_timeout = 600000  # 10 minutes
    clone_start_time = time.time()
    
    apps_page.wait_for_status(clone_hostname, 'running', timeout=clone_timeout)

    clone_duration = time.time() - clone_start_time
    print(f"  ✅ CLONE COMPLETE - Status: running (took {clone_duration:.1f}s)\n")

    # ============================================================================
    # STEP 7: VERIFY BOTH APPS ARE RUNNING
    # ============================================================================
    print("📍 STEP 7: Verify Both Apps Running")
    print("-" * 80)

    # Verify source app is still running
    source_status = apps_page.get_app_status(source_hostname)
    assert source_status == 'running', \
        f"Source app should still be running, got '{source_status}'"
    print(f"  ✓ Source app: {source_hostname} - Status: {source_status}")

    # Verify clone app is running
    clone_status = apps_page.get_app_status(clone_hostname)
    assert clone_status == 'running', \
        f"Clone app should be running, got '{clone_status}'"
    print(f"  ✓ Clone app: {clone_hostname} - Status: {clone_status}")

    print(f"  ✅ BOTH APPS RUNNING SUCCESSFULLY\n")

    # ============================================================================
    # STEP 8: DELETE BOTH APPLICATIONS
    # ============================================================================
    print("📍 STEP 8: Cleanup - Delete Both Applications")
    print("-" * 80)

    # Setup dialog handler for delete confirmations
    page.on("dialog", lambda dialog: dialog.accept())

    # Delete source app
    print(f"  🗑️  Deleting source app: {source_hostname}...")
    apps_page.click_delete(source_hostname)
    print(f"  ✓ Source app delete initiated")

    # Delete clone app
    print(f"  🗑️  Deleting clone app: {clone_hostname}...")
    apps_page.click_delete(clone_hostname)
    print(f"  ✓ Clone app delete initiated")

    # Wait for both cards to disappear
    source_card = apps_page.get_app_card_by_hostname(source_hostname)
    expect(source_card).to_be_hidden(timeout=90000)
    print(f"  ✓ Source app removed from UI")

    clone_card = apps_page.get_app_card_by_hostname(clone_hostname)
    expect(clone_card).to_be_hidden(timeout=90000)
    print(f"  ✓ Clone app removed from UI")

    print(f"  ✅ CLEANUP COMPLETE - Both apps deleted\n")

    # ============================================================================
    # TEST SUMMARY
    # ============================================================================
    total_duration = time.time() - test_start_time

    print("="*80)
    print("✅ CLONE FEATURE TEST COMPLETE - ALL STEPS PASSED")
    print("="*80)
    print(f"Total test duration: {total_duration:.1f}s")
    print(f"User: {unique_user['username']}")
    print(f"Source: {source_hostname}")
    print(f"Clone: {clone_hostname}")
    print("="*80 + "\n")
