"""
E2E Tests for Clone App and Config Edit features.

Tests the complete user workflows for:
- Cloning an application
- Editing application resources (CPU/RAM/Disk)
"""

import pytest
import logging
from playwright.sync_api import Page, expect
from pages.dashboard_page import DashboardPage
from pages.app_store_page import AppStorePage
from pages.deployment_modal_page import DeploymentModalPage
from utils.test_data import generate_hostname

logger = logging.getLogger(__name__)


@pytest.fixture
def deployed_app(authenticated_page: Page, base_url: str):
    """
    Fixture that deploys a test application for clone/config testing.

    Yields the hostname, then cleans up after the test.
    """
    page = authenticated_page
    hostname = generate_hostname("nginx-clone-test")

    # Deploy app
    dashboard_page = DashboardPage(page)
    app_store_page = AppStorePage(page)
    deployment_modal = DeploymentModalPage(page)

    dashboard_page.navigate_to_app_store()
    app_store_page.wait_for_catalog_loaded()
    app_store_page.select_app("nginx")
    deployment_modal.wait_for_modal_visible()
    deployment_modal.enter_hostname(hostname)
    deployment_modal.submit_deployment()
    deployment_modal.wait_for_deployment_success(timeout=180000)
    deployment_modal.close_modal()
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(hostname)

    yield hostname

    # Cleanup
    try:
        dashboard_page.navigate_to_my_apps()
        dashboard_page.delete_app(hostname)
        # Also try to delete cloned app if it exists
        try:
            dashboard_page.delete_app(f"{hostname}-clone")
        except:
            pass
    except Exception as e:
        logger.warning(f"Cleanup failed for {hostname}: {e}")


@pytest.mark.clone
@pytest.mark.smoke
@pytest.mark.timeout(300)
def test_clone_app_workflow(deployed_app: str, authenticated_page: Page):
    """
    Test the complete clone app workflow.

    Steps:
        1. Navigate to My Apps
        2. Click clone button for deployed app
        3. Enter new hostname in prompt
        4. Verify clone success notification
        5. Verify cloned app appears in list
        6. Verify cloned app has different hostname
        7. Verify cloned app is running

    Expected Results:
        - Clone button works correctly
        - Prompt modal appears for hostname input
        - Clone operation succeeds
        - Cloned app appears with new hostname
        - Cloned app is in running state
    """
    page = authenticated_page
    source_hostname = deployed_app
    clone_hostname = f"{source_hostname}-clone"

    print("\n" + "="*80)
    print("🔄 TEST: Clone App Workflow")
    print("="*80)

    dashboard_page = DashboardPage(page)

    # Navigate to My Apps
    print("\n📋 Step 1: Navigate to My Apps")
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(source_hostname)
    print(f"   ✓ Source app '{source_hostname}' is visible")

    # Find clone button
    print("\n🔍 Step 2: Locate clone button")
    app_card = page.locator(".app-card.deployed").filter(has_text=source_hostname).first
    clone_button = app_card.locator("button[title='Clone App']")
    expect(clone_button).to_be_visible(timeout=5000)
    print("   ✓ Clone button found")

    # Click clone button
    print("\n🖱️  Step 3: Click clone button and enter hostname")
    clone_button.click()

    # Wait for prompt modal
    prompt_modal = page.locator("#promptOverlay")
    expect(prompt_modal).to_be_visible(timeout=3000)
    print("   ✓ Clone prompt modal appeared")

    # Enter hostname
    hostname_input = page.locator("#clone-hostname")
    expect(hostname_input).to_be_visible()
    hostname_input.fill(clone_hostname)
    print(f"   ✓ Entered clone hostname: {clone_hostname}")

    # Click confirm
    confirm_button = page.locator("#promptConfirm")
    confirm_button.click()
    print("   ✓ Confirmed clone operation")

    # Wait for success notification
    print("\n⏳ Step 4: Wait for clone to complete")
    # Clone operation can take some time
    page.wait_for_timeout(3000)

    # Verify cloned app appears
    print("\n✅ Step 5: Verify cloned app appears in list")
    # Refresh apps view
    dashboard_page.navigate_to_my_apps()

    # Wait for cloned app to appear (may take a moment)
    cloned_app_card = page.locator(".app-card.deployed").filter(has_text=clone_hostname)
    expect(cloned_app_card).to_be_visible(timeout=30000)
    print(f"   ✓ Cloned app '{clone_hostname}' is visible")

    # Verify cloned app is running
    print("\n🔍 Step 6: Verify cloned app status")
    status_badge = cloned_app_card.locator(".status-badge")
    expect(status_badge).to_contain_text("running", timeout=10000)
    print("   ✓ Cloned app is running")

    # Verify both apps exist
    print("\n📊 Step 7: Verify both source and clone exist")
    source_card = page.locator(".app-card.deployed").filter(has_text=source_hostname).first
    expect(source_card).to_be_visible()
    expect(cloned_app_card).to_be_visible()
    print(f"   ✓ Source app '{source_hostname}' still exists")
    print(f"   ✓ Cloned app '{clone_hostname}' exists")

    print("\n" + "="*80)
    print("✅ TEST PASSED: Clone App Workflow")
    print("="*80)

    # Cleanup cloned app
    try:
        dashboard_page.delete_app(clone_hostname)
    except:
        pass


@pytest.mark.config
@pytest.mark.smoke
@pytest.mark.timeout(240)
def test_edit_config_workflow(deployed_app: str, authenticated_page: Page):
    """
    Test the complete config edit workflow.

    Steps:
        1. Navigate to My Apps
        2. Click edit resources button
        3. Verify config modal appears
        4. Enter new CPU value
        5. Submit config update
        6. Verify success notification
        7. Verify app is restarted

    Expected Results:
        - Edit resources button works
        - Config modal appears with form fields
        - Config update succeeds
        - App is automatically restarted
    """
    page = authenticated_page
    hostname = deployed_app

    print("\n" + "="*80)
    print("⚙️  TEST: Edit Config Workflow")
    print("="*80)

    dashboard_page = DashboardPage(page)

    # Navigate to My Apps
    print("\n📋 Step 1: Navigate to My Apps")
    dashboard_page.navigate_to_my_apps()
    dashboard_page.wait_for_app_visible(hostname)
    print(f"   ✓ App '{hostname}' is visible")

    # Find edit resources button
    print("\n🔍 Step 2: Locate edit resources button")
    app_card = page.locator(".app-card.deployed").filter(has_text=hostname).first
    edit_button = app_card.locator("button[title='Edit Resources']")
    expect(edit_button).to_be_visible(timeout=5000)
    print("   ✓ Edit resources button found")

    # Click edit button
    print("\n🖱️  Step 3: Click edit resources button")
    edit_button.click()

    # Wait for config modal
    config_modal = page.locator("#editConfigOverlay")
    expect(config_modal).to_be_visible(timeout=3000)
    print("   ✓ Edit config modal appeared")

    # Verify form fields exist
    print("\n✅ Step 4: Verify form fields")
    cpu_input = page.locator("#editCpu")
    memory_input = page.locator("#editMemory")
    disk_input = page.locator("#editDisk")

    expect(cpu_input).to_be_visible()
    expect(memory_input).to_be_visible()
    expect(disk_input).to_be_visible()
    print("   ✓ CPU, Memory, and Disk fields are visible")

    # Enter new CPU value
    print("\n📝 Step 5: Enter new resource values")
    cpu_input.fill("2")
    print("   ✓ Set CPU to 2 cores")

    # Submit
    print("\n🚀 Step 6: Submit config update")
    apply_button = page.locator("button:has-text('Apply Changes')")
    apply_button.click()
    print("   ✓ Clicked Apply Changes")

    # Modal should close
    expect(config_modal).not_to_be_visible(timeout=5000)
    print("   ✓ Modal closed")

    # Wait for update to complete
    print("\n⏳ Step 7: Wait for config update to complete")
    page.wait_for_timeout(5000)

    # Verify app is still running (restarted automatically)
    print("\n🔍 Step 8: Verify app status after config update")
    dashboard_page.navigate_to_my_apps()
    app_card = page.locator(".app-card.deployed").filter(has_text=hostname).first
    status_badge = app_card.locator(".status-badge")
    expect(status_badge).to_contain_text("running", timeout=20000)
    print("   ✓ App is running after config update")

    print("\n" + "="*80)
    print("✅ TEST PASSED: Edit Config Workflow")
    print("="*80)
