"""
E2E Tests for Application Lifecycle.

Tests the complete application lifecycle including:
- Deployment from catalog
- Real-time deployment monitoring
- HTTP accessibility verification
- State management (stop/start)
- Application deletion and cleanup

This is the MOST CRITICAL test suite for the Proximity platform
as it validates the core user journey.
"""

import pytest
import logging
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.app_store_page import AppStorePage
from pages.deployment_modal_page import DeploymentModalPage
from utils.test_data import generate_test_user, generate_hostname

logger = logging.getLogger(__name__)


@pytest.fixture
def authenticated_page(page: Page):
    """
    Fixture that provides an authenticated page with a logged-in user.
    
    Returns:
        Page: Playwright page with authenticated session
    """
    # Register and login
    test_user = generate_test_user()
    login_page = LoginPage(page)
    
    login_page.wait_for_auth_modal()
    login_page.register(
        username=test_user["username"],
        password=test_user["password"],
        email=test_user["email"]
    )
    
    # Wait for dashboard to load
    dashboard = DashboardPage(page)
    dashboard.wait_for_dashboard_load()
    
    return page


@pytest.mark.lifecycle
@pytest.mark.smoke
@pytest.mark.critical
@pytest.mark.timeout(360)  # 6 minutes timeout for full workflow
def test_full_app_deploy_manage_delete_workflow(authenticated_page: Page, base_url: str):
    """
    THE MOST CRITICAL E2E TEST: Full application lifecycle workflow.
    
    This test validates the complete user journey from deployment to deletion:
    
    1. **Deploy Phase**:
       - Navigate to App Store
       - Select Nginx application
       - Configure with unique hostname
       - Submit deployment
       - Monitor real-time deployment progress
    
    2. **Verification Phase**:
       - Wait for deployment success
       - Verify app appears on dashboard
       - Verify status is "RUNNING"
       - Make HTTP request to verify accessibility
       - Validate reverse proxy is working
    
    3. **Management Phase**:
       - Stop the application
       - Verify status changes to "STOPPED"
       - Verify app is no longer accessible
       - Start the application
       - Verify status returns to "RUNNING"
       - Verify app is accessible again
    
    4. **Cleanup Phase**:
       - Delete the application
       - Confirm deletion
       - Verify app is removed from dashboard
       - Verify app is no longer in backend
    
    Expected Results:
        - All deployment steps complete successfully
        - App is accessible when running
        - App is inaccessible when stopped
        - App is completely removed after deletion
        - No orphaned resources remain
    
    Test Characteristics:
        - ✅ Atomic (performs own cleanup)
        - ✅ Reliable (handles timing and async operations)
        - ✅ Comprehensive (validates all critical paths)
        - ✅ Isolated (uses unique hostname)
    """
    page = authenticated_page
    print("\n" + "="*80)
    print("🚀 CRITICAL E2E TEST: Full Application Lifecycle Workflow")
    print("="*80)
    
    # ========================================================================
    # ARRANGE: Setup test data and page objects
    # ========================================================================
    print("\n📋 Phase 0: Setup")
    
    # Generate unique hostname for this test run
    hostname = generate_hostname("nginx")
    print(f"   ✓ Generated unique hostname: {hostname}")
    
    # Initialize page objects
    dashboard_page = DashboardPage(page)
    app_store_page = AppStorePage(page)
    deployment_modal = DeploymentModalPage(page)
    
    print(f"   ✓ Page objects initialized")
    print(f"   ✓ Base URL: {base_url}")
    
    # ========================================================================
    # PHASE 1: DEPLOYMENT
    # ========================================================================
    print("\n" + "-"*80)
    print("� Phase 1: Deploy Application")
    print("-"*80)
    
    # Step 1.1: Navigate to App Store
    print("\n   Step 1.1: Navigate to App Store")
    dashboard_page.navigate_to_app_store()
    print("   ✓ Navigated to App Store")
    
    # Wait for catalog to load
    app_store_page.wait_for_catalog_load()
    print("   ✓ Catalog loaded")
    
    # Step 1.2: Select Nginx application
    print("\n   Step 1.2: Select Nginx application")
    
    # Verify Nginx is available
    assert app_store_page.is_app_available("Nginx"), "Nginx app not found in catalog"
    print("   ✓ Nginx found in catalog")
    
    # Click to open deployment modal
    app_store_page.click_deploy_on_app("Nginx")
    print("   ✓ Clicked Nginx app card")
    
    # Step 1.3: Configure deployment
    print("\n   Step 1.3: Configure deployment")
    
    # Wait for modal to appear
    deployment_modal.wait_for_modal_visible()
    print("   ✓ Deployment modal opened")
    
    # Verify modal title
    expect(deployment_modal.modal_title).to_have_text("Deploy Application")
    print("   ✓ Modal title verified")
    
    # Fill hostname (the only required field for basic deployment)
    deployment_modal.fill_hostname(hostname)
    print(f"   ✓ Filled hostname: {hostname}")
    
    # Step 1.4: Submit deployment
    print("\n   Step 1.4: Submit deployment")
    deployment_modal.submit_deployment()
    print("   ✓ Deployment submitted")
    
    # Step 1.5: Monitor deployment progress
    print("\n   Step 1.5: Monitor deployment (this may take 3-5 minutes)")
    print("   ⏳ Waiting for deployment to complete...")
    print("   📋 Progress steps:")
    print("      - Creating LXC container")
    print("      - Starting container")
    print("      - Installing Docker")
    print("      - Pulling Docker images")
    print("      - Starting services")
    print("      - Finalizing deployment")
    
    # This is the CRITICAL wait - deployment can take several minutes
    deployment_modal.wait_for_deployment_success(timeout=300000)  # 5 minutes
    print("   ✅ Deployment completed successfully!")
    
    # ========================================================================
    # PHASE 2: VERIFICATION
    # ========================================================================
    print("\n" + "-"*80)
    print("✅ Phase 2: Verify Deployment")
    print("-"*80)
    
    # Step 2.1: Verify app appears on dashboard
    print("\n   Step 2.1: Verify app appears on dashboard")
    
    # The UI should auto-navigate back to dashboard or we navigate manually
    dashboard_page.navigate_to_dashboard()
    dashboard_page.wait_for_dashboard_load()
    print("   ✓ Navigated to dashboard")
    
    # Find the newly deployed app card
    app_card = dashboard_page.get_app_card_by_hostname(hostname)
    expect(app_card).to_be_visible(timeout=30000)
    print(f"   ✓ App card visible for: {hostname}")
    
    # Step 2.2: Verify status is RUNNING
    print("\n   Step 2.2: Verify app status is RUNNING")
    dashboard_page.wait_for_app_status(hostname, "running", timeout=60000)
    print(f"   ✅ App status: RUNNING")
    
    # Step 2.3: Get app URL
    print("\n   Step 2.3: Get application access URL")
    app_url = dashboard_page.get_app_url(hostname)
    print(f"   ✓ App URL: {app_url}")
    
    assert app_url and app_url != "IP not available", f"App URL not available: {app_url}"
    print("   ✓ URL is valid")
    
    # Step 2.4: Verify HTTP accessibility
    print("\n   Step 2.4: Verify app is accessible via HTTP")
    print(f"   🌐 Making HTTP GET request to: {app_url}")
    
    # Use Playwright's API request context for HTTP verification
    api_context = page.request
    response = api_context.get(app_url, timeout=30000)
    
    print(f"   📡 Response status: {response.status}")
    expect(response).to_be_ok()  # Asserts 2xx status code
    print("   ✅ App is accessible (2xx response)")
    
    # Optional: Verify Nginx welcome page content
    response_text = response.text()
    assert "nginx" in response_text.lower() or "welcome" in response_text.lower(), \
        "Response doesn't contain expected Nginx content"
    print("   ✅ Response contains expected Nginx content")
    
    # ========================================================================
    # PHASE 3: STATE MANAGEMENT
    # ========================================================================
    print("\n" + "-"*80)
    print("⚙️  Phase 3: Test State Management (Stop/Start)")
    print("-"*80)
    
    # Step 3.1: Stop the application
    print("\n   Step 3.1: Stop the application")
    dashboard_page.click_app_action(hostname, "stop")
    print("   ✓ Clicked stop button")
    
    # Wait for status to change to STOPPED
    dashboard_page.wait_for_app_status(hostname, "stopped", timeout=60000)
    print("   ✅ App status: STOPPED")
    
    # Step 3.2: Verify app is no longer accessible
    print("\n   Step 3.2: Verify app is NOT accessible when stopped")
    print(f"   🌐 Making HTTP GET request to: {app_url}")
    
    response_stopped = api_context.get(app_url, timeout=10000, ignore_http_errors=True)
    print(f"   📡 Response status: {response_stopped.status}")
    
    # When stopped, we expect the app to be inaccessible (not 2xx)
    # It might return 502 Bad Gateway, 503 Service Unavailable, or timeout
    assert not response_stopped.ok, "App should not be accessible when stopped"
    print("   ✅ App is inaccessible (as expected when stopped)")
    
    # Step 3.3: Start the application again
    print("\n   Step 3.3: Start the application")
    dashboard_page.click_app_action(hostname, "start")
    print("   ✓ Clicked start button")
    
    # Wait for status to change back to RUNNING
    dashboard_page.wait_for_app_status(hostname, "running", timeout=90000)
    print("   ✅ App status: RUNNING (restarted)")
    
    # Step 3.4: Verify app is accessible again
    print("\n   Step 3.4: Verify app is accessible again")
    print(f"   🌐 Making HTTP GET request to: {app_url}")
    
    # Give the service a moment to fully start
    page.wait_for_timeout(5000)
    
    response_restarted = api_context.get(app_url, timeout=30000)
    print(f"   📡 Response status: {response_restarted.status}")
    expect(response_restarted).to_be_ok()
    print("   ✅ App is accessible again (2xx response)")
    
    # ========================================================================
    # PHASE 4: CLEANUP AND DELETION
    # ========================================================================
    print("\n" + "-"*80)
    print("🗑️  Phase 4: Delete Application and Verify Cleanup")
    print("-"*80)
    
    # Step 4.1: Delete the application
    print("\n   Step 4.1: Delete the application")
    dashboard_page.click_app_action(hostname, "delete")
    print("   ✓ Clicked delete button")
    
    # Handle confirmation dialog (if present)
    print("   ⏳ Handling confirmation dialog...")
    page.wait_for_timeout(1000)  # Brief wait for dialog
    
    # Try to find and click confirmation button
    try:
        dashboard_page.confirm_delete_app()
        print("   ✓ Deletion confirmed")
    except Exception as e:
        logger.warning(f"Confirmation dialog not found (might auto-delete): {e}")
        print("   ⚠️  No confirmation dialog (auto-delete)")
    
    # Step 4.2: Verify app is removed from dashboard
    print("\n   Step 4.2: Verify app is removed from dashboard")
    dashboard_page.wait_for_app_hidden(hostname, timeout=60000)
    print(f"   ✅ App {hostname} no longer visible on dashboard")
    
    # Step 4.3: Final verification - check backend
    print("\n   Step 4.3: Verify app is removed from backend")
    
    # Make API call to verify app is not in the apps list
    response = api_context.get(f"{base_url}/api/v1/apps")
    expect(response).to_be_ok()
    
    apps_data = response.json()
    hostnames = [app.get("hostname") for app in apps_data]
    
    assert hostname not in hostnames, f"App {hostname} still exists in backend!"
    print(f"   ✅ App {hostname} removed from backend database")
    
    # ========================================================================
    # TEST COMPLETE
    # ========================================================================
    print("\n" + "="*80)
    print("🎉 TEST PASSED: Full Application Lifecycle Workflow")
    print("="*80)
    print("\n✅ Summary:")
    print(f"   • Deployed: {hostname}")
    print("   • Verified: HTTP accessibility")
    print("   • Managed: Stop/Start state transitions")
    print("   • Cleaned: Complete deletion verified")
    print("\n🏆 All phases completed successfully!")
    print("="*80 + "\n")
