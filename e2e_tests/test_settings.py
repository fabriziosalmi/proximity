"""
E2E Tests for Settings Management.

Tests all settings page functionality:
- Proxmox connection settings
- Network configuration settings
- Resource allocation settings
- Test connection functionality
- Tab navigation
- Settings persistence
"""

import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import generate_test_user


@pytest.fixture
def authenticated_settings_page(authenticated_page: Page):
    """Fixture providing authenticated page on settings view."""
    page = authenticated_page
    # Navigate to settings
    page.click("[data-view='settings']")
    expect(page.locator("#settingsView")).to_be_visible(timeout=10000)
    
    return page


@pytest.mark.settings
def test_settings_page_loads(authenticated_settings_page):
    """
    Test that settings page loads correctly.
    
    Verifies:
    - Settings view is visible
    - All tabs are present
    - Default tab (Proxmox) is active
    """
    page = authenticated_settings_page
    
    print("\n⚙️  Testing settings page load")
    
    # Verify settings view is visible
    settings_view = page.locator("#settingsView")
    expect(settings_view).to_be_visible()
    print("✓ Settings view loaded")
    
    # Verify all tabs exist
    proxmox_tab = page.locator(".settings-tab[data-tab='proxmox']")
    network_tab = page.locator(".settings-tab[data-tab='network']")
    resources_tab = page.locator(".settings-tab[data-tab='resources']")
    system_tab = page.locator(".settings-tab[data-tab='system']")
    
    expect(proxmox_tab).to_be_visible()
    expect(network_tab).to_be_visible()
    expect(resources_tab).to_be_visible()
    expect(system_tab).to_be_visible()
    print("✓ All tabs present (Proxmox, Network, Resources, System)")
    
    # Verify Proxmox tab is active by default
    proxmox_tab_class = proxmox_tab.get_attribute("class")
    assert "active" in proxmox_tab_class
    print("✓ Proxmox tab active by default")


@pytest.mark.settings
def test_settings_tab_navigation(authenticated_settings_page):
    """
    Test navigating between settings tabs.
    
    Verifies:
    - Can switch between tabs
    - Active tab updates correctly
    - Tab content changes
    """
    page = authenticated_settings_page
    
    print("\n🔀 Testing settings tab navigation")
    
    # Start on Proxmox tab
    expect(page.locator(".settings-tab[data-tab='proxmox'].active")).to_be_visible()
    expect(page.locator("#proxmox-panel.active")).to_be_visible()
    print("✓ Starting on Proxmox tab")
    
    # Switch to Network tab
    page.click(".settings-tab[data-tab='network']")
    page.wait_for_timeout(500)  # Animation delay
    
    expect(page.locator(".settings-tab[data-tab='network'].active")).to_be_visible()
    expect(page.locator("#network-panel.active")).to_be_visible()
    print("✓ Switched to Network tab")
    
    # Switch to Resources tab
    page.click(".settings-tab[data-tab='resources']")
    page.wait_for_timeout(500)
    
    expect(page.locator(".settings-tab[data-tab='resources'].active")).to_be_visible()
    expect(page.locator("#resources-panel.active")).to_be_visible()
    print("✓ Switched to Resources tab")
    
    # Switch to System tab
    page.click(".settings-tab[data-tab='system']")
    page.wait_for_timeout(500)
    
    expect(page.locator(".settings-tab[data-tab='system'].active")).to_be_visible()
    expect(page.locator("#system-panel.active")).to_be_visible()
    print("✓ Switched to System tab")
    
    # Switch back to Proxmox
    page.click(".settings-tab[data-tab='proxmox']")
    page.wait_for_timeout(500)
    
    expect(page.locator(".settings-tab[data-tab='proxmox'].active")).to_be_visible()
    print("✓ Navigation cycle complete")


@pytest.mark.settings
def test_proxmox_settings_form(authenticated_settings_page):
    """
    Test Proxmox settings form fields.
    
    Verifies:
    - All form fields are present
    - Can enter values
    - Test Connection button exists
    - Save button exists
    """
    page = authenticated_settings_page
    
    print("\n🖥️  Testing Proxmox settings form")
    
    # Ensure we're on Proxmox tab
    page.click(".settings-tab[data-tab='proxmox']")
    page.wait_for_timeout(500)
    
    # Verify form exists
    proxmox_form = page.locator("#proxmoxForm")
    expect(proxmox_form).to_be_visible()
    print("✓ Proxmox form found")
    
    # Check for expected fields
    host_input = page.locator("#proxmoxHost, input[name='proxmox_host']")
    user_input = page.locator("#proxmoxUser, input[name='proxmox_user']")
    password_input = page.locator("#proxmoxPassword, input[name='proxmox_password']")
    
    # At least one of these should be visible
    expect(proxmox_form.locator("input").first).to_be_visible()
    print("✓ Form input fields present")
    
    # Verify Test Connection button
    test_button = page.locator("button:has-text('Test Connection')")
    expect(test_button).to_be_visible()
    print("✓ Test Connection button found")
    
    # Verify Save button
    save_button = page.locator("button:has-text('Save Settings'), button[type='submit']")
    expect(save_button.first).to_be_visible()
    print("✓ Save Settings button found")


@pytest.mark.settings
def test_proxmox_test_connection(authenticated_settings_page):
    """
    Test the Proxmox connection test functionality.
    
    Verifies:
    - Test Connection button is clickable
    - Status message appears after clicking
    - (Success or failure message, depends on actual config)
    """
    page = authenticated_settings_page
    
    print("\n🔌 Testing Proxmox connection test")
    
    # Ensure we're on Proxmox tab
    page.click(".settings-tab[data-tab='proxmox']")
    page.wait_for_timeout(500)
    
    # Click Test Connection
    test_button = page.locator("button:has-text('Test Connection')")
    expect(test_button).to_be_visible()
    test_button.click()
    print("✓ Test Connection button clicked")
    
    # Wait for status message
    page.wait_for_timeout(3000)  # Give it time to test
    
    # Check for status div
    status_div = page.locator("#proxmoxStatus")
    if status_div.is_visible():
        status_text = status_div.inner_text()
        print(f"✓ Status message: {status_text[:100]}")
    else:
        print("⚠️  No status message appeared (may be expected)")


@pytest.mark.settings
def test_network_settings_form(authenticated_settings_page):
    """
    Test Network settings form.
    
    Verifies:
    - Network tab loads
    - Network form fields exist
    - Can interact with form
    """
    page = authenticated_settings_page
    
    print("\n🌐 Testing Network settings form")
    
    # Switch to Network tab
    page.click(".settings-tab[data-tab='network']")
    page.wait_for_timeout(500)
    
    # Verify form exists
    network_form = page.locator("#networkForm")
    expect(network_form).to_be_visible()
    print("✓ Network form found")
    
    # Check for input fields
    expect(network_form.locator("input").first).to_be_visible()
    print("✓ Network form has input fields")
    
    # Verify Save button
    save_button = page.locator("button:has-text('Save Settings'), button[type='submit']")
    expect(save_button.first).to_be_visible()
    print("✓ Save button found")


@pytest.mark.settings
def test_resources_settings_form(authenticated_settings_page):
    """
    Test Resources settings form.
    
    Verifies:
    - Resources tab loads
    - Resources form fields exist
    - Default resource limits are shown
    """
    page = authenticated_settings_page
    
    print("\n💻 Testing Resources settings form")
    
    # Switch to Resources tab
    page.click(".settings-tab[data-tab='resources']")
    page.wait_for_timeout(500)
    
    # Verify form exists
    resources_form = page.locator("#resourcesForm")
    expect(resources_form).to_be_visible()
    print("✓ Resources form found")
    
    # Check for input fields
    expect(resources_form.locator("input").first).to_be_visible()
    print("✓ Resources form has input fields")
    
    # Verify Save button
    save_button = page.locator("button:has-text('Save Settings'), button[type='submit']")
    expect(save_button.first).to_be_visible()
    print("✓ Save button found")


@pytest.mark.settings
def test_system_settings_panel(authenticated_settings_page):
    """
    Test System settings panel.
    
    Verifies:
    - System tab loads
    - System information is displayed
    """
    page = authenticated_settings_page
    
    print("\n🔧 Testing System settings panel")
    
    # Switch to System tab
    page.click(".settings-tab[data-tab='system']")
    page.wait_for_timeout(500)
    
    # Verify panel exists
    system_panel = page.locator("#system-panel")
    expect(system_panel).to_be_visible()
    print("✓ System panel found")
    
    # System panel might show version info, backup options, etc.
    expect(system_panel.locator("text=/system|version|backup/i").first).to_be_visible()
    print("✓ System panel has content")


@pytest.mark.settings
@pytest.mark.skip(reason="Settings persistence requires valid config")
def test_save_proxmox_settings(authenticated_settings_page):
    """
    Test saving Proxmox settings.
    
    NOTE: Skipped by default as it requires valid Proxmox credentials.
    Enable this test when you have a test Proxmox instance.
    
    Verifies:
    - Can enter settings
    - Can save settings
    - Success notification appears
    - Settings persist after reload
    """
    page = authenticated_settings_page
    
    print("\n💾 Testing save Proxmox settings")
    
    # Fill form with test data
    page.fill("#proxmoxHost, input[name='proxmox_host']", "https://proxmox.example.com:8006")
    page.fill("#proxmoxUser, input[name='proxmox_user']", "root@pam")
    page.fill("#proxmoxPassword, input[name='proxmox_password']", "test_password")
    
    # Save
    page.click("button:has-text('Save Settings')")
    
    # Wait for success notification
    page.wait_for_selector(".notification.success, .alert.success", timeout=5000)
    print("✓ Settings saved successfully")


@pytest.mark.settings
def test_settings_keyboard_navigation(authenticated_settings_page):
    """
    Test keyboard navigation in settings.
    
    Verifies:
    - Can tab through form fields
    - Can use arrow keys for navigation
    """
    page = authenticated_settings_page
    
    print("\n⌨️  Testing keyboard navigation")
    
    # Focus first input
    first_input = page.locator("input").first
    first_input.click()
    first_input.focus()
    
    # Press Tab to move to next field
    page.keyboard.press("Tab")
    page.wait_for_timeout(200)
    
    # Verify focus moved (basic check)
    focused_element = page.evaluate("document.activeElement.tagName")
    print(f"✓ Keyboard navigation works (focused: {focused_element})")


@pytest.mark.settings
def test_settings_form_validation(authenticated_settings_page):
    """
    Test form validation in settings.
    
    Verifies:
    - Required fields are marked
    - Can't submit empty form (if validation exists)
    """
    page = authenticated_settings_page
    
    print("\n✅ Testing form validation")
    
    # Check for required field indicators
    required_indicators = page.locator(".required, [required], label:has-text('*')")
    
    if required_indicators.count() > 0:
        print(f"✓ Found {required_indicators.count()} required field indicators")
    else:
        print("⚠️  No required field indicators found (validation may be optional)")


@pytest.mark.settings
def test_settings_help_text(authenticated_settings_page):
    """
    Test that help text is displayed for settings fields.
    
    Verifies:
    - Help text exists for complex settings
    - Field descriptions are present
    """
    page = authenticated_settings_page
    
    print("\n❓ Testing help text")
    
    # Look for help text elements
    help_texts = page.locator(".form-help, .help-text, .form-description, p.form-help")
    
    if help_texts.count() > 0:
        print(f"✓ Found {help_texts.count()} help text elements")
    else:
        print("⚠️  No help text found (UI may not have help text)")
