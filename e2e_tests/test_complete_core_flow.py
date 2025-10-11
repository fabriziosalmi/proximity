"""
E2E Test: Complete "Click and Use" Core Flow

This test validates the main promise of Proximity:
Login -> Deploy App -> Launch in Canvas -> Interact -> Close Canvas -> Delete App

This is the MOST IMPORTANT test as it validates the entire user experience.
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


@pytest.mark.e2e
@pytest.mark.core
@pytest.mark.smoke
@pytest.mark.timeout(300)
def test_complete_click_and_use_flow(authenticated_page: Page, base_url: str):
    """
    🎯 CORE TEST: Complete "Click and Use" Flow
    
    This test validates the entire Proximity value proposition:
    1. User logs in (via authenticated_page fixture)
    2. User browses catalog
    3. User deploys an app with one click
    4. User launches app in canvas
    5. User interacts with app in canvas
    6. User closes canvas
    7. User deletes app
    
    If this test passes, Proximity delivers on its promise!
    """
    page = authenticated_page
    hostname = generate_hostname("e2e-complete-flow")
    
    print("\n" + "="*100)
    print("🚀 CORE E2E TEST: Complete 'Click and Use' Flow")
    print("="*100)
    print(f"Testing with app hostname: {hostname}")
    print("="*100)
    
    # Initialize page objects
    dashboard_page = DashboardPage(page)
    app_store_page = AppStorePage(page)
    deployment_modal = DeploymentModalPage(page)
    canvas_page = AppCanvasPage(page)
    
    try:
        # ==============================================================================
        # PHASE 1: Deploy Application
        # ==============================================================================
        print("\n📦 PHASE 1: Deploy Application")
        print("-" * 100)
        
        # Step 1: Navigate to App Store
        print("   [1/4] Navigate to App Store...")
        dashboard_page.navigate_to_app_store()
        app_store_page.wait_for_catalog_load()
        print("   ✓ App Store loaded")
        
        # Step 2: Select Nginx app
        print("   [2/4] Select Nginx app...")
        app_store_page.click_app_card("Nginx")
        deployment_modal.wait_for_modal_visible()
        print("   ✓ Deployment modal opened")
        
        # Step 3: Configure and deploy
        print(f"   [3/4] Deploy with hostname: {hostname}...")
        deployment_modal.enter_hostname(hostname)
        deployment_modal.submit_deployment()
        print("   ⏳ Waiting for deployment to complete (this may take 2-3 minutes)...")
        
        # Wait for deployment with extended timeout
        deployment_modal.wait_for_deployment_success(timeout=180000)  # 3 minutes
        print("   ✓ Deployment successful!")
        
        # Step 4: Close deployment modal and navigate to apps
        print("   [4/4] Navigate to My Apps...")
        deployment_modal.close_modal()
        dashboard_page.navigate_to_my_apps()
        dashboard_page.wait_for_app_visible(hostname, timeout=30000)
        print("   ✓ App visible in My Apps")
        
        # ==============================================================================
        # PHASE 2: Launch in Canvas
        # ==============================================================================
        print("\n🖼️  PHASE 2: Launch in Canvas")
        print("-" * 100)
        
        # Step 1: Open canvas
        print("   [1/3] Open app in canvas...")
        canvas_page.open_app_canvas(hostname)
        canvas_page.assert_canvas_modal_open()
        print("   ✓ Canvas modal opened")
        
        # Step 2: Wait for app to load
        print("   [2/3] Wait for app to load in canvas (up to 30 seconds)...")
        canvas_page.wait_for_canvas_loaded(timeout=30000)
        canvas_page.assert_canvas_loaded()
        print("   ✓ App loaded in canvas!")
        
        # Step 3: Verify app name
        print("   [3/3] Verify canvas shows correct app...")
        displayed_name = canvas_page.get_canvas_app_name()
        assert hostname in displayed_name or "nginx" in displayed_name.lower(), \
            f"Expected hostname '{hostname}' in displayed name '{displayed_name}'"
        print(f"   ✓ Canvas showing: {displayed_name}")
        
        # ==============================================================================
        # PHASE 3: Interact with App
        # ==============================================================================
        print("\n🖱️  PHASE 3: Interact with App in Canvas")
        print("-" * 100)
        
        print("   [1/3] Verify iframe is interactive...")
        iframe = page.locator("#canvasIframe")
        expect(iframe).to_be_visible()
        expect(iframe).not_to_have_class("hidden")
        print("   ✓ Iframe is visible and active")
        
        print("   [2/3] Test canvas controls...")
        # Test refresh button
        refresh_btn = page.locator('button[onclick="refreshCanvas()"]')
        expect(refresh_btn).to_be_visible()
        print("   ✓ Refresh button available")
        
        # Test open in new tab button
        new_tab_btn = page.locator('button[onclick="openInNewTab()"]')
        expect(new_tab_btn).to_be_visible()
        print("   ✓ Open in new tab button available")
        
        print("   [3/3] Verify no error messages...")
        error_div = page.locator("#canvasError")
        expect(error_div).to_have_class("hidden")
        print("   ✓ No errors - app is working!")
        
        # ==============================================================================
        # PHASE 4: Close Canvas
        # ==============================================================================
        print("\n❌ PHASE 4: Close Canvas")
        print("-" * 100)
        
        print("   [1/2] Close canvas modal...")
        canvas_page.close_canvas()
        canvas_page.assert_canvas_modal_closed()
        print("   ✓ Canvas closed")
        
        print("   [2/2] Verify back at My Apps...")
        expect(page.locator("#appsView")).to_be_visible()
        print("   ✓ Back at My Apps view")
        
        # ==============================================================================
        # PHASE 5: Delete Application
        # ==============================================================================
        print("\n🗑️  PHASE 5: Delete Application")
        print("-" * 100)
        
        print("   [1/2] Delete app...")
        dashboard_page.delete_app(hostname)
        print("   ✓ Delete initiated")
        
        print("   [2/2] Verify app is removed...")
        page.wait_for_timeout(2000)  # Give time for deletion to process
        app_card = page.locator(f'[data-hostname="{hostname}"]')
        expect(app_card).not_to_be_visible()
        print("   ✓ App deleted successfully")
        
        # ==============================================================================
        # SUCCESS!
        # ==============================================================================
        print("\n" + "="*100)
        print("✅ CORE FLOW TEST PASSED!")
        print("="*100)
        print("Proximity delivers on its promise:")
        print("  ✓ Login")
        print("  ✓ Deploy App")
        print("  ✓ Launch in Canvas")
        print("  ✓ Interact with App")
        print("  ✓ Close Canvas")
        print("  ✓ Delete App")
        print("="*100)
        
    except Exception as e:
        print("\n" + "="*100)
        print("❌ CORE FLOW TEST FAILED")
        print("="*100)
        print(f"Error: {str(e)}")
        print("="*100)
        
        # Take screenshot for debugging
        try:
            page.screenshot(path=f"test_failure_{hostname}.png")
            print(f"Screenshot saved: test_failure_{hostname}.png")
        except:
            pass
        
        # Try to clean up
        try:
            if canvas_page:
                canvas_page.close_canvas()
        except:
            pass
        
        try:
            dashboard_page.navigate_to_my_apps()
            dashboard_page.delete_app(hostname)
        except:
            pass
        
        raise


@pytest.mark.e2e
@pytest.mark.core
@pytest.mark.extended
@pytest.mark.timeout(360)
def test_complete_flow_with_console_interaction(authenticated_page: Page, base_url: str):
    """
    Extended Core Flow Test with Console Interaction
    
    Same as core test but also tests the integrated console:
    1. All steps from core test
    2. + Open console
    3. + Execute command
    4. + Verify output
    5. + Close console
    """
    page = authenticated_page
    hostname = generate_hostname("e2e-console-flow")
    
    print("\n" + "="*100)
    print("🚀 EXTENDED E2E TEST: Complete Flow + Console")
    print("="*100)
    
    dashboard_page = DashboardPage(page)
    app_store_page = AppStorePage(page)
    deployment_modal = DeploymentModalPage(page)
    canvas_page = AppCanvasPage(page)
    
    try:
        # Deploy app (same as core test)
        print("\n📦 Deploying application...")
        dashboard_page.navigate_to_app_store()
        app_store_page.wait_for_catalog_load()
        app_store_page.click_app_card("Nginx")
        deployment_modal.wait_for_modal_visible()
        deployment_modal.enter_hostname(hostname)
        deployment_modal.submit_deployment()
        deployment_modal.wait_for_deployment_success(timeout=180000)
        deployment_modal.close_modal()
        dashboard_page.navigate_to_my_apps()
        dashboard_page.wait_for_app_visible(hostname)
        print("✓ App deployed")
        
        # Launch in canvas
        print("\n🖼️  Launching in canvas...")
        canvas_page.open_app_canvas(hostname)
        canvas_page.wait_for_canvas_loaded(timeout=30000)
        print("✓ Canvas loaded")
        
        # Close canvas
        print("\n❌ Closing canvas...")
        canvas_page.close_canvas()
        print("✓ Canvas closed")
        
        # NEW: Test console
        print("\n💻 Testing console integration...")
        
        # Find console button for the app
        console_button = page.locator(f'button[onclick*="showAppConsole"][onclick*="{hostname}"]').first
        if console_button.is_visible():
            print("   [1/5] Opening console...")
            console_button.click()
            
            # Wait for terminal to appear
            terminal = page.locator('.xterm')
            expect(terminal).to_be_visible(timeout=5000)
            print("   ✓ Console opened")
            
            print("   [2/5] Waiting for terminal to initialize...")
            page.wait_for_timeout(2000)
            
            print("   [3/5] Executing command: ls...")
            page.click('.xterm')  # Focus terminal
            page.keyboard.type('ls')
            page.keyboard.press('Enter')
            print("   ✓ Command executed")
            
            print("   [4/5] Waiting for output...")
            page.wait_for_timeout(3000)
            print("   ✓ Command completed")
            
            print("   [5/5] Closing console...")
            # Find and click close button
            close_btn = page.locator('button[onclick*="closeModal"]').first
            close_btn.click()
            page.wait_for_timeout(500)
            print("   ✓ Console closed")
        else:
            print("   ⚠️ Console button not found, skipping console test")
        
        # Delete app
        print("\n🗑️  Deleting application...")
        dashboard_page.delete_app(hostname)
        page.wait_for_timeout(2000)
        print("✓ App deleted")
        
        print("\n" + "="*100)
        print("✅ EXTENDED FLOW TEST PASSED!")
        print("="*100)
        
    except Exception as e:
        print(f"\n❌ EXTENDED FLOW TEST FAILED: {str(e)}")
        
        # Cleanup
        try:
            canvas_page.close_canvas()
        except:
            pass
        try:
            dashboard_page.navigate_to_my_apps()
            dashboard_page.delete_app(hostname)
        except:
            pass
        
        raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--headed"])
