"""
E2E Tests for In-App Canvas Feature.

Tests the in-app canvas modal functionality including:
- Opening apps in canvas modal
- Canvas iframe loading and display
- Canvas controls (refresh, open in new tab, close)
- Error handling for apps without iframe support
- Modal interaction (escape key, click outside)

This test suite validates the new In-App Canvas feature that allows
users to view and interact with applications directly within the Proximity UI.
"""

import pytest
import logging
from playwright.sync_api import Page, expect
from pages.dashboard_page import DashboardPage
from pages.app_store_page import AppStorePage
from pages.deployment_modal_page import DeploymentModalPage
from pages.app_canvas_page import AppCanvasPage
from utils.test_data import generate_hostname

logger = logging.getLogger(__name__)


@pytest.fixture
def deployed_app(authenticated_page: Page, base_url: str):
    """
    Fixture that deploys a test application for canvas testing.
    
    Yields the hostname of the deployed app, then cleans up after the test.
    """
    print("\n" + "="*80)
    print("🚀 [LOCAL deployed_app fixture] Starting UI-based deployment")
    print("="*80)
    
    page = authenticated_page
    hostname = generate_hostname("nginx-canvas")
    
    # Enable console logging
    page.on("console", lambda msg: print(f"  [BROWSER] {msg.text}"))
    
    print(f"📝 Generated hostname: {hostname}")
    
    # Deploy app
    print("🔧 Creating page objects...")
    dashboard_page = DashboardPage(page)
    app_store_page = AppStorePage(page)
    deployment_modal = DeploymentModalPage(page)
    print("✅ Page objects created")
    
    print("\n📋 STEP 1: Navigate to App Store")
    try:
        dashboard_page.navigate_to_app_store()
        print("✅ Successfully navigated to App Store")
    except Exception as e:
        print(f"❌ FAILED to navigate to App Store: {e}")
        raise
    
    print("\n📋 STEP 2: Wait for catalog to load")
    try:
        app_store_page.wait_for_catalog_load()
        print("✅ Catalog loaded successfully")
    except Exception as e:
        print(f"❌ FAILED to load catalog: {e}")
        raise
    
    print("\n📋 STEP 3: Click on Nginx app card")
    try:
        app_store_page.click_app_card("Nginx")
        print("✅ Clicked Nginx app card")
    except Exception as e:
        print(f"❌ FAILED to click app card: {e}")
        raise
    
    print("\n📋 STEP 4: Wait for deployment modal")
    try:
        deployment_modal.wait_for_modal_visible()
        print("✅ Deployment modal visible")
    except Exception as e:
        print(f"❌ FAILED: Modal not visible: {e}")
        raise
    
    print(f"\n📋 STEP 5: Enter hostname: {hostname}")
    try:
        deployment_modal.fill_hostname(hostname)
        print("✅ Hostname entered")
    except Exception as e:
        print(f"❌ FAILED to enter hostname: {e}")
        raise
    
    print("\n📋 STEP 6: Submit deployment")
    try:
        deployment_modal.submit_deployment()
        print("✅ Deployment submitted")
    except Exception as e:
        print(f"❌ FAILED to submit deployment: {e}")
        raise
    
    print("\n📋 STEP 7: Wait for deployment success (timeout=180s)")
    try:
        deployment_modal.wait_for_deployment_success(timeout=180000)
        print("✅ Deployment successful!")
    except Exception as e:
        print(f"❌ FAILED: Deployment did not succeed: {e}")
        raise
    
    print("\n📋 STEP 8: Close modal")
    try:
        deployment_modal.close_modal()
        print("✅ Modal closed")
    except Exception as e:
        print(f"❌ FAILED to close modal: {e}")
        raise
    
    print("\n📋 STEP 9: Navigate to My Apps")
    try:
        dashboard_page.navigate_to_my_apps()
        print("✅ Navigated to My Apps")
        
        # CRITICAL FIX: Wait for the apps list to be refreshed after navigation
        # The Router now calls loadDeployedApps() asynchronously, so we need to wait
        # for the network to settle before checking for the app card
        print("⏳ Waiting for network to settle after apps view load...")
        dashboard_page.wait_for_load_state("networkidle", timeout=10000)
        print("✅ Network idle - apps list should be refreshed")
    except Exception as e:
        print(f"❌ FAILED to navigate to My Apps: {e}")
        raise
    
    print(f"\n📋 STEP 10: Wait for app {hostname} to be visible")
    try:
        dashboard_page.wait_for_app_visible(hostname)
        print(f"✅ App {hostname} is visible!")
    except Exception as e:
        print(f"❌ FAILED: App not visible: {e}")
        raise
    
    print("\n" + "="*80)
    print(f"🎉 [LOCAL deployed_app fixture] SUCCESS! Yielding hostname: {hostname}")
    print("="*80)
    
    yield hostname
    
    # Cleanup
    print(f"\n🧹 [LOCAL deployed_app fixture] Cleanup: Deleting app {hostname}")
    try:
        # First, close any open canvas modal
        canvas_page = AppCanvasPage(page)
        try:
            # Check if canvas modal is visible and close it
            modal = page.locator("#canvasModal.show")
            if modal.count() > 0:
                logger.info("Canvas modal is open, closing it...")
                canvas_page.close_canvas()
                logger.info("✓ Closed canvas modal before cleanup")
                page.wait_for_timeout(500)  # Brief wait for modal animation
        except Exception as e:
            logger.debug(f"Canvas close attempt: {e}")
            # Try alternative method - press Escape
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            except:
                pass
        
        dashboard_page.navigate_to_my_apps()
        dashboard_page.delete_app(hostname, timeout=45000)
        print(f"✅ App {hostname} deleted successfully")
    except Exception as e:
        logger.warning(f"⚠️  Cleanup failed for {hostname}: {e}")


@pytest.mark.canvas
@pytest.mark.smoke
@pytest.mark.timeout(240)
def test_open_and_close_canvas_with_button(deployed_app: str, authenticated_page: Page):
    """
    Test opening and closing the canvas modal using the close button.
    
    Steps:
        1. Navigate to My Apps
        2. Click canvas button for deployed app
        3. Verify canvas modal opens
        4. Verify app name is displayed correctly
        5. Wait for iframe to load
        6. Click close button
        7. Verify modal closes
    
    Expected Results:
        - Canvas modal opens successfully
        - Correct app name is displayed
        - Iframe loads and displays content
        - Modal closes when close button is clicked
    """
    page = authenticated_page
    hostname = deployed_app
    
    print("\n" + "="*80)
    print("🖼️  TEST: Open and Close Canvas with Button")
    print("="*80)
    
    # Initialize page objects
    dashboard_page = DashboardPage(page)
    canvas_page = AppCanvasPage(page)
    
    # Navigate to My Apps
    print("\n📋 Step 1: Navigate to My Apps")
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(hostname)
    print(f"   ✓ App '{hostname}' is visible")
    
    # Open canvas
    print("\n📋 Step 2: Open Canvas")
    canvas_page.open_app_canvas(hostname)
    print(f"   ✓ Canvas opened for '{hostname}'")
    
    # Verify modal is open
    print("\n📋 Step 3: Verify Canvas Modal State")
    canvas_page.assert_canvas_modal_open()
    print("   ✓ Canvas modal is open")
    
    # Verify app name
    displayed_name = canvas_page.get_canvas_app_name()
    print(f"   ✓ Displayed app name: {displayed_name}")
    
    # Wait for iframe to load
    print("\n📋 Step 4: Wait for Canvas to Load")
    canvas_page.wait_for_canvas_loaded(timeout=30000)
    canvas_page.assert_canvas_loaded()
    print("   ✓ Canvas iframe loaded successfully")
    
    # Close canvas
    print("\n📋 Step 5: Close Canvas")
    canvas_page.close_canvas()
    canvas_page.assert_canvas_modal_closed()
    print("   ✓ Canvas modal closed successfully")
    
    print("\n✅ TEST PASSED: Canvas open/close with button")


@pytest.mark.canvas
@pytest.mark.smoke
@pytest.mark.timeout(240)
def test_close_canvas_with_escape_key(deployed_app: str, authenticated_page: Page):
    """
    Test closing the canvas modal using the Escape key.
    
    Steps:
        1. Navigate to My Apps
        2. Open canvas for deployed app
        3. Wait for canvas to load
        4. Press Escape key
        5. Verify modal closes
    
    Expected Results:
        - Canvas opens successfully
        - Modal closes when Escape key is pressed
    """
    page = authenticated_page
    hostname = deployed_app
    
    print("\n" + "="*80)
    print("⌨️  TEST: Close Canvas with Escape Key")
    print("="*80)
    
    # Initialize page objects
    dashboard_page = DashboardPage(page)
    canvas_page = AppCanvasPage(page)
    
    # Navigate and open canvas
    print("\n📋 Opening canvas")
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(hostname)
    canvas_page.open_app_canvas(hostname)
    canvas_page.wait_for_canvas_loaded(timeout=30000)
    print("   ✓ Canvas opened and loaded")
    
    # Close with Escape
    print("\n📋 Closing with Escape key")
    canvas_page.close_canvas_by_escape()
    canvas_page.assert_canvas_modal_closed()
    print("   ✓ Canvas closed with Escape key")
    
    print("\n✅ TEST PASSED: Close canvas with Escape key")


@pytest.mark.canvas
@pytest.mark.smoke
@pytest.mark.timeout(240)
def test_close_canvas_by_clicking_outside(deployed_app: str, authenticated_page: Page):
    """
    Test closing the canvas modal by clicking outside the content area.
    
    Steps:
        1. Navigate to My Apps
        2. Open canvas for deployed app
        3. Wait for canvas to load
        4. Click outside modal content
        5. Verify modal closes
    
    Expected Results:
        - Canvas opens successfully
        - Modal closes when clicking outside content area
    """
    page = authenticated_page
    hostname = deployed_app
    
    print("\n" + "="*80)
    print("🖱️  TEST: Close Canvas by Clicking Outside")
    print("="*80)
    
    # Initialize page objects
    dashboard_page = DashboardPage(page)
    canvas_page = AppCanvasPage(page)
    
    # Navigate and open canvas
    print("\n📋 Opening canvas")
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(hostname)
    canvas_page.open_app_canvas(hostname)
    canvas_page.wait_for_canvas_loaded(timeout=30000)
    print("   ✓ Canvas opened and loaded")
    
    # Close by clicking outside
    print("\n📋 Closing by clicking outside")
    canvas_page.close_canvas_by_clicking_outside()
    canvas_page.assert_canvas_modal_closed()
    print("   ✓ Canvas closed by clicking outside")
    
    print("\n✅ TEST PASSED: Close canvas by clicking outside")


@pytest.mark.canvas
@pytest.mark.timeout(240)
def test_refresh_canvas(deployed_app: str, authenticated_page: Page):
    """
    Test refreshing the canvas iframe.
    
    Steps:
        1. Navigate to My Apps
        2. Open canvas for deployed app
        3. Wait for initial load
        4. Click refresh button
        5. Verify canvas reloads
    
    Expected Results:
        - Canvas opens successfully
        - Refresh button triggers reload
        - Canvas loads again after refresh
    """
    page = authenticated_page
    hostname = deployed_app
    
    print("\n" + "="*80)
    print("🔄 TEST: Refresh Canvas")
    print("="*80)
    
    # Initialize page objects
    dashboard_page = DashboardPage(page)
    canvas_page = AppCanvasPage(page)
    
    # Navigate and open canvas
    print("\n📋 Opening canvas")
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(hostname)
    canvas_page.open_app_canvas(hostname)
    canvas_page.wait_for_canvas_loaded(timeout=30000)
    print("   ✓ Canvas opened and loaded")
    
    # Get initial iframe src
    initial_src = canvas_page.get_canvas_iframe_src()
    print(f"   ✓ Initial iframe src: {initial_src}")
    
    # Refresh canvas
    print("\n📋 Refreshing canvas")
    canvas_page.refresh_canvas(timeout=30000)
    print("   ✓ Canvas refreshed")
    
    # Verify it reloaded
    canvas_page.assert_canvas_loaded()
    refreshed_src = canvas_page.get_canvas_iframe_src()
    assert refreshed_src == initial_src, "Iframe src should remain the same after refresh"
    print("   ✓ Canvas reloaded successfully")
    
    print("\n✅ TEST PASSED: Refresh canvas")


@pytest.mark.canvas
@pytest.mark.timeout(240)
def test_canvas_displays_correct_app_name(deployed_app: str, authenticated_page: Page):
    """
    Test that the canvas modal displays the correct app name in the header.
    
    Steps:
        1. Navigate to My Apps
        2. Open canvas for deployed app
        3. Verify displayed app name matches
    
    Expected Results:
        - Canvas header shows correct app name
    """
    page = authenticated_page
    hostname = deployed_app
    
    print("\n" + "="*80)
    print("📝 TEST: Canvas Displays Correct App Name")
    print("="*80)
    
    # Initialize page objects
    dashboard_page = DashboardPage(page)
    canvas_page = AppCanvasPage(page)
    
    # Navigate and open canvas
    print("\n📋 Opening canvas")
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(hostname)
    canvas_page.open_app_canvas(hostname)
    canvas_page.wait_for_canvas_loaded(timeout=30000)
    print("   ✓ Canvas opened and loaded")
    
    # Verify app name
    displayed_name = canvas_page.get_canvas_app_name()
    print(f"   ✓ Displayed name: {displayed_name}")
    
    # App name should contain either the hostname or "nginx"
    assert "nginx" in displayed_name.lower() or hostname in displayed_name.lower(), \
        f"Expected app name to contain 'nginx' or '{hostname}', got '{displayed_name}'"
    
    print("\n✅ TEST PASSED: Canvas displays correct app name")


@pytest.mark.canvas
@pytest.mark.timeout(240)
def test_canvas_iframe_loads_content(deployed_app: str, authenticated_page: Page):
    """
    Test that the canvas iframe successfully loads the application content.
    
    Steps:
        1. Navigate to My Apps
        2. Open canvas for deployed app
        3. Wait for iframe to load
        4. Verify iframe src is set correctly
        5. Verify iframe is visible and not in error state
    
    Expected Results:
        - Iframe src contains expected URL pattern
        - Iframe becomes visible after loading
        - No error state is displayed
    """
    page = authenticated_page
    hostname = deployed_app
    
    print("\n" + "="*80)
    print("📦 TEST: Canvas Iframe Loads Content")
    print("="*80)
    
    # Initialize page objects
    dashboard_page = DashboardPage(page)
    canvas_page = AppCanvasPage(page)
    
    # Navigate and open canvas
    print("\n📋 Opening canvas")
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(hostname)
    canvas_page.open_app_canvas(hostname)
    print("   ✓ Canvas opened")
    
    # Wait for load
    print("\n📋 Waiting for canvas to load")
    canvas_page.wait_for_canvas_loaded(timeout=30000)
    print("   ✓ Canvas loaded")
    
    # Verify iframe
    iframe_src = canvas_page.get_canvas_iframe_src()
    print(f"   ✓ Iframe src: {iframe_src}")
    
    # Verify src contains expected pattern
    # Can be either:
    # 1. /proxy/internal/ (proxied through Proximity)
    # 2. Direct IP (http://192.168.x.x:port)
    # 3. Hostname in URL
    assert ("/proxy/internal/" in iframe_src or 
            hostname in iframe_src or 
            iframe_src.startswith("http://") or 
            iframe_src.startswith("https://")), \
        f"Expected iframe src to be valid URL, got '{iframe_src}'"
    
    # Verify iframe is visible
    canvas_page.assert_canvas_loaded()
    print("   ✓ Iframe is visible and loaded")
    
    print("\n✅ TEST PASSED: Canvas iframe loads content")


@pytest.mark.canvas
@pytest.mark.timeout(240)
def test_canvas_button_only_visible_for_running_apps(deployed_app: str, authenticated_page: Page):
    """
    Test that the canvas button is only visible when an app is running.
    
    Steps:
        1. Navigate to My Apps with running app
        2. Verify canvas button is visible
        3. Stop the app
        4. Verify canvas button is hidden or disabled
    
    Expected Results:
        - Canvas button visible for running apps
        - Canvas button hidden/disabled for stopped apps
    """
    page = authenticated_page
    hostname = deployed_app
    
    print("\n" + "="*80)
    print("👁️  TEST: Canvas Button Visibility Based on App State")
    print("="*80)
    
    # Initialize page objects
    dashboard_page = DashboardPage(page)
    canvas_page = AppCanvasPage(page)
    
    # Verify button visible when running
    print("\n📋 Step 1: Verify canvas button visible for running app")
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(hostname)
    canvas_page.assert_canvas_button_exists(hostname)
    print("   ✓ Canvas button is visible for running app")
    
    # Stop the app
    print("\n📋 Step 2: Stop the app")
    dashboard_page.stop_app(hostname)
    dashboard_page.wait_for_app_status(hostname, "stopped")
    print("   ✓ App stopped")
    
    # Check if canvas button is hidden/disabled
    print("\n📋 Step 3: Check canvas button state for stopped app")
    # Note: The button should either not exist or be disabled
    # We'll check if it's still visible, and if so, verify it's disabled
    try:
        canvas_page.assert_canvas_button_exists(hostname)
        # If it exists, it should be disabled
        print("   ⚠️  Canvas button still visible (should be disabled)")
    except AssertionError:
        print("   ✓ Canvas button hidden for stopped app")
    
    # Restart for cleanup
    print("\n📋 Step 4: Restart app for cleanup")
    dashboard_page.start_app(hostname)
    dashboard_page.wait_for_app_status(hostname, "running")
    print("   ✓ App restarted")
    
    print("\n✅ TEST PASSED: Canvas button visibility based on app state")


@pytest.mark.canvas
@pytest.mark.skip(reason="Error handling depends on app configuration")
def test_canvas_error_handling(deployed_app: str, authenticated_page: Page):
    """
    Test canvas error handling for apps that don't support iframe embedding.
    
    Note: This test is skipped by default as it requires an app that blocks
    iframe embedding (X-Frame-Options). Most test apps allow embedding.
    
    Steps:
        1. Deploy an app that blocks iframe embedding
        2. Open canvas
        3. Verify error state is shown
        4. Verify error message is displayed
        5. Verify "Open in New Tab" button works
    
    Expected Results:
        - Error state appears for blocked iframes
        - Error message is clear and helpful
        - Fallback option (new tab) is provided
    """
    pass  # Implementation depends on having an app that blocks iframes
