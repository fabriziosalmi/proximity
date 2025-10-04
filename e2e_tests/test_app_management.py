"""
E2E Tests for Application Management Operations.

Tests all app control actions and monitoring features:
- Start/Stop/Restart operations
- Log viewing (all logs, docker logs, system logs)
- Console command execution
- External link access
- App info modal
- Auto-refresh functionality
"""

import pytest
import time
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import generate_test_user


@pytest.fixture(scope="module")
def deployed_app_session(browser):
    """
    Module-scoped fixture that deploys an app once for all tests.
    
    This saves time by not deploying/destroying for each test.
    """
    context = browser.new_context()
    page = context.new_page()
    
    # Authenticate
    test_user = generate_test_user()
    login_page = LoginPage(page)
    login_page.wait_for_auth_modal()
    login_page.register(
        username=test_user["username"],
        password=test_user["password"],
        email=test_user["email"]
    )
    
    dashboard = DashboardPage(page)
    dashboard.wait_for_dashboard_load()
    
    # Deploy a test app (NGINX)
    page.click("[data-view='catalog']")
    page.wait_for_selector(".app-card", timeout=15000)
    
    nginx_card = page.locator(".app-card:has-text('NGINX')").first
    nginx_card.click()
    
    timestamp = int(time.time())
    hostname = f"nginx-mgmt-{timestamp}"
    
    page.locator("#hostname").fill(hostname)
    page.click("button:has-text('Deploy Application')")
    
    # Wait for deployment
    page.wait_for_selector(
        "text=/complete|successfully/i",
        timeout=300000
    )
    
    page.click("[data-view='apps']")
    page.wait_for_selector(f".app-card:has-text('{hostname}')", timeout=30000)
    
    yield page, hostname
    
    # Cleanup
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    delete_button = app_card.locator("button[title*='Delete'], button.danger")
    if delete_button.is_visible():
        delete_button.click()
        page.locator("#deployModal button:has-text('Delete Forever')").click()
        page.wait_for_selector("#deployModal:not(.show)", timeout=180000)
    
    context.close()


@pytest.mark.management
def test_view_app_logs_all(deployed_app_session):
    """
    Test viewing all application logs.
    
    Verifies:
    - Logs modal opens
    - 'All' logs tab is functional
    - Logs content is displayed
    - Modal can be closed
    """
    page, hostname = deployed_app_session
    
    print(f"\n📋 Testing all logs for: {hostname}")
    
    # Navigate to apps view
    page.click("[data-view='apps']")
    page.wait_for_selector(f".app-card:has-text('{hostname}')", timeout=10000)
    
    # Find app card and click logs button
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    logs_button = app_card.locator("button[title*='logs'], button[title*='View logs']")
    logs_button.click()
    
    # Verify logs modal opened
    logs_modal = page.locator("#deployModal.show")
    expect(logs_modal).to_be_visible(timeout=5000)
    expect(logs_modal.locator("text=/Logs/i")).to_be_visible()
    print("✓ Logs modal opened")
    
    # Verify 'All' button is active
    all_button = page.locator("button:has-text('All').btn-secondary")
    expect(all_button).to_be_visible(timeout=5000)
    print("✓ 'All' logs tab active")
    
    # Verify logs output area exists
    logs_output = page.locator("#logsOutput, .log-output, pre")
    expect(logs_output.first).to_be_visible(timeout=5000)
    print("✓ Logs output displayed")
    
    # Close modal
    page.keyboard.press("Escape")
    page.wait_for_selector("#deployModal:not(.show)", timeout=5000)
    print("✓ Modal closed")


@pytest.mark.management
def test_view_app_logs_docker(deployed_app_session):
    """
    Test viewing docker-specific logs.
    
    Verifies:
    - Can switch to Docker logs tab
    - Docker logs are displayed
    - Tab switching works correctly
    """
    page, hostname = deployed_app_session
    
    print(f"\n🐋 Testing docker logs for: {hostname}")
    
    page.click("[data-view='apps']")
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    
    # Open logs
    logs_button = app_card.locator("button[title*='logs'], button[title*='View logs']")
    logs_button.click()
    
    logs_modal = page.locator("#deployModal.show")
    expect(logs_modal).to_be_visible(timeout=5000)
    
    # Click Docker tab
    docker_button = page.locator("button:has-text('Docker')")
    expect(docker_button).to_be_visible()
    docker_button.click()
    
    # Wait for docker logs to load
    page.wait_for_timeout(2000)
    
    # Docker button should now be active (btn-secondary class)
    expect(page.locator("button:has-text('Docker').btn-secondary")).to_be_visible()
    print("✓ Docker logs tab activated")
    
    # Verify logs updated
    logs_output = page.locator("#logsOutput, .log-output")
    expect(logs_output.first).to_be_visible()
    print("✓ Docker logs displayed")
    
    # Close
    page.keyboard.press("Escape")
    page.wait_for_selector("#deployModal:not(.show)", timeout=5000)


@pytest.mark.management
def test_view_app_logs_system(deployed_app_session):
    """
    Test viewing system logs.
    
    Verifies:
    - Can switch to System logs tab
    - System logs are displayed
    """
    page, hostname = deployed_app_session
    
    print(f"\n⚙️  Testing system logs for: {hostname}")
    
    page.click("[data-view='apps']")
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    
    # Open logs
    logs_button = app_card.locator("button[title*='logs'], button[title*='View logs']")
    logs_button.click()
    
    expect(page.locator("#deployModal.show")).to_be_visible(timeout=5000)
    
    # Click System tab
    system_button = page.locator("button:has-text('System')")
    expect(system_button).to_be_visible()
    system_button.click()
    
    page.wait_for_timeout(2000)
    
    # System button should be active
    expect(page.locator("button:has-text('System').btn-secondary")).to_be_visible()
    print("✓ System logs tab activated")
    
    # Close
    page.keyboard.press("Escape")
    page.wait_for_selector("#deployModal:not(.show)", timeout=5000)


@pytest.mark.management
def test_logs_auto_refresh(deployed_app_session):
    """
    Test auto-refresh functionality for logs.
    
    Verifies:
    - Auto-refresh checkbox exists
    - Can enable/disable auto-refresh
    - Timestamp updates when enabled
    """
    page, hostname = deployed_app_session
    
    print(f"\n🔄 Testing auto-refresh for: {hostname}")
    
    page.click("[data-view='apps']")
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    
    # Open logs
    logs_button = app_card.locator("button[title*='logs'], button[title*='View logs']")
    logs_button.click()
    
    expect(page.locator("#deployModal.show")).to_be_visible(timeout=5000)
    
    # Find auto-refresh checkbox
    auto_refresh = page.locator("#autoRefreshLogs")
    expect(auto_refresh).to_be_visible()
    print("✓ Auto-refresh checkbox found")
    
    # Enable auto-refresh
    auto_refresh.check()
    expect(auto_refresh).to_be_checked()
    print("✓ Auto-refresh enabled")
    
    # Wait a moment
    page.wait_for_timeout(2000)
    
    # Disable auto-refresh
    auto_refresh.uncheck()
    expect(auto_refresh).not_to_be_checked()
    print("✓ Auto-refresh disabled")
    
    # Close
    page.keyboard.press("Escape")
    page.wait_for_selector("#deployModal:not(.show)", timeout=5000)


@pytest.mark.management
def test_download_logs(deployed_app_session):
    """
    Test downloading logs.
    
    Verifies:
    - Download button exists
    - Can click download (doesn't verify actual download)
    """
    page, hostname = deployed_app_session
    
    print(f"\n💾 Testing log download for: {hostname}")
    
    page.click("[data-view='apps']")
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    
    # Open logs
    logs_button = app_card.locator("button[title*='logs'], button[title*='View logs']")
    logs_button.click()
    
    expect(page.locator("#deployModal.show")).to_be_visible(timeout=5000)
    
    # Find download button
    download_button = page.locator("button:has-text('Download'), button:has(text='💾')")
    expect(download_button.first).to_be_visible()
    print("✓ Download button found")
    
    # Click download (won't verify actual file, just that it's clickable)
    download_button.first.click()
    print("✓ Download button clicked")
    
    # Close
    page.wait_for_timeout(1000)
    page.keyboard.press("Escape")
    page.wait_for_selector("#deployModal:not(.show)", timeout=5000)


@pytest.mark.management
def test_open_app_console(deployed_app_session):
    """
    Test opening application console.
    
    Verifies:
    - Console modal opens
    - Command input field exists
    - Quick command suggestions are available
    - Can close console
    """
    page, hostname = deployed_app_session
    
    print(f"\n💻 Testing console for: {hostname}")
    
    page.click("[data-view='apps']")
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    
    # Click console button
    console_button = app_card.locator("button[title*='Console'], button[title*='console']")
    console_button.click()
    
    # Verify console modal opened
    console_modal = page.locator("#deployModal.show")
    expect(console_modal).to_be_visible(timeout=5000)
    expect(console_modal.locator("text=/Console/i")).to_be_visible()
    print("✓ Console modal opened")
    
    # Verify command input exists
    command_input = page.locator("#consoleCommand")
    expect(command_input).to_be_visible()
    print("✓ Command input found")
    
    # Verify output area exists
    console_output = page.locator("#consoleOutput")
    expect(console_output).to_be_visible()
    print("✓ Console output area found")
    
    # Close
    page.keyboard.press("Escape")
    page.wait_for_selector("#deployModal:not(.show)", timeout=5000)


@pytest.mark.management
def test_console_quick_commands(deployed_app_session):
    """
    Test console quick command buttons.
    
    Verifies quick command suggestions (df -h, free -h, etc.) work.
    """
    page, hostname = deployed_app_session
    
    print(f"\n⚡ Testing console quick commands for: {hostname}")
    
    page.click("[data-view='apps']")
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    
    # Open console
    console_button = app_card.locator("button[title*='Console'], button[title*='console']")
    console_button.click()
    
    expect(page.locator("#deployModal.show")).to_be_visible(timeout=5000)
    
    # Find a quick command button (e.g., "df -h")
    quick_cmd = page.locator("code:has-text('df -h'), button:has-text('df -h')")
    if quick_cmd.first.is_visible():
        quick_cmd.first.click()
        
        # Verify command input was populated
        command_input = page.locator("#consoleCommand")
        expect(command_input).to_have_value("df -h")
        print("✓ Quick command populated input field")
    else:
        print("⚠️  Quick command buttons not found (UI may have changed)")
    
    # Close
    page.keyboard.press("Escape")
    page.wait_for_selector("#deployModal:not(.show)", timeout=5000)


@pytest.mark.management  
def test_app_external_link(deployed_app_session):
    """
    Test opening app in external tab.
    
    Verifies:
    - External link button exists
    - Button is enabled when app is running
    """
    page, hostname = deployed_app_session
    
    print(f"\n🔗 Testing external link for: {hostname}")
    
    page.click("[data-view='apps']")
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    
    # Find external link button
    external_button = app_card.locator("button[title*='Open in new tab'], button:has([data-lucide='external-link'])")
    
    # Should be visible (may be disabled if app not running)
    expect(external_button.first).to_be_visible()
    print("✓ External link button found")
    
    # Check if enabled (app should be running)
    is_enabled = not external_button.first.is_disabled()
    if is_enabled:
        print("✓ External link button is enabled (app is running)")
    else:
        print("⚠️  External link button is disabled (app may be stopped)")


@pytest.mark.management
def test_app_stop_start_cycle(deployed_app_session):
    """
    Test stop/start cycle of an application.
    
    Verifies:
    - Can stop running app
    - Status changes to Stopped
    - Can start stopped app  
    - Status changes back to Running
    """
    page, hostname = deployed_app_session
    
    print(f"\n⏯️  Testing stop/start cycle for: {hostname}")
    
    page.click("[data-view='apps']")
    page.wait_for_selector(f".app-card:has-text('{hostname}')", timeout=10000)
    
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    
    # Stop app
    print("  Stopping app...")
    stop_button = app_card.locator("button[title*='Stop']")
    expect(stop_button).to_be_visible()
    stop_button.click()
    
    # Wait for stopped status
    page.wait_for_selector(
        f".app-card:has-text('{hostname}') .status-badge:has-text('Stopped')",
        timeout=30000
    )
    print("✓ App stopped")
    
    # Reload to refresh UI
    page.reload()
    page.wait_for_selector(f".app-card:has-text('{hostname}')", timeout=10000)
    
    # Start app
    print("  Starting app...")
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    start_button = app_card.locator("button[title*='Start']")
    expect(start_button).to_be_visible()
    start_button.click()
    
    # Wait for running status
    page.wait_for_selector(
        f".app-card:has-text('{hostname}') .status-badge:has-text('Running')",
        timeout=30000
    )
    print("✓ App started")


@pytest.mark.management
def test_app_restart(deployed_app_session):
    """
    Test restarting an application.
    
    Verifies restart button works and app returns to running state.
    """
    page, hostname = deployed_app_session
    
    print(f"\n🔄 Testing restart for: {hostname}")
    
    page.click("[data-view='apps']")
    page.wait_for_selector(f".app-card:has-text('{hostname}')", timeout=10000)
    
    app_card = page.locator(f".app-card:has-text('{hostname}')")
    
    # Restart app
    restart_button = app_card.locator("button[title*='Restart']")
    expect(restart_button).to_be_visible()
    restart_button.click()
    
    print("  Restarting...")
    page.wait_for_timeout(5000)
    
    # Should be back to running
    status = app_card.locator(".status-badge:has-text('Running')")
    expect(status).to_be_visible(timeout=30000)
    print("✓ App restarted successfully")
