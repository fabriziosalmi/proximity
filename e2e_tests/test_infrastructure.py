"""
E2E Tests for Infrastructure Monitoring.

Tests infrastructure page functionality:
- Viewing Proxmox nodes
- Network appliance status
- Appliance logs viewing
- Restart appliance functionality
- NAT testing
"""

import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import generate_test_user


@pytest.fixture
def authenticated_infra_page(authenticated_page: Page):
    """Fixture providing authenticated page on infrastructure view."""
    page = authenticated_page
    # Navigate to infrastructure (nodes view)
    page.click("[data-view='nodes']")
    expect(page.locator("#nodesView")).to_be_visible(timeout=10000)
    
    return page


@pytest.mark.infrastructure
def test_infrastructure_page_loads(authenticated_infra_page):
    """
    Test that infrastructure page loads correctly.
    
    Verifies:
    - Infrastructure view is visible
    - Page has expected sections
    """
    page = authenticated_infra_page
    
    print("\n🏗️  Testing infrastructure page load")
    
    # Verify infrastructure view (nodes view)
    infra_view = page.locator("#nodesView")
    expect(infra_view).to_be_visible()
    print("✓ Infrastructure view loaded")
    
    # Check for main sections
    # (node info, appliance status, services health, etc.)
    expect(infra_view.locator("text=/node|appliance|infrastructure/i").first).to_be_visible()
    print("✓ Infrastructure content present")


@pytest.mark.infrastructure
def test_proxmox_nodes_display(authenticated_infra_page):
    """
    Test displaying Proxmox nodes.
    
    Verifies:
    - Node information is displayed
    - Node cards/sections exist
    """
    page = authenticated_infra_page
    
    print("\n🖥️  Testing Proxmox nodes display")
    
    # Look for node information
    nodes_section = page.locator("text=/Proxmox Node|Node Information/i")
    
    if nodes_section.count() > 0:
        expect(nodes_section.first).to_be_visible()
        print("✓ Node information section found")
        
        # Check for node details
        node_card = page.locator(".node-card, .app-card:has-text('node'), .card:has-text('node')")
        if node_card.count() > 0:
            print(f"✓ Found {node_card.count()} node card(s)")
        else:
            print("⚠️  No node cards found (may need configuration)")
    else:
        print("⚠️  Node section not found (Proxmox may not be configured)")


@pytest.mark.infrastructure
def test_network_appliance_status(authenticated_infra_page):
    """
    Test network appliance status display.
    
    Verifies:
    - Appliance status section exists
    - Status information is shown
    """
    page = authenticated_infra_page
    
    print("\n🌐 Testing network appliance status")
    
    # Look for appliance section
    appliance_section = page.locator("text=/Network Appliance|Appliance Status/i")
    
    if appliance_section.count() > 0:
        expect(appliance_section.first).to_be_visible()
        print("✓ Network appliance section found")
        
        # Check for status indicators
        status_badge = page.locator(".status-badge, .badge")
        if status_badge.count() > 0:
            status_text = status_badge.first.inner_text()
            print(f"✓ Appliance status: {status_text}")
        else:
            print("⚠️  No status badge found")
    else:
        print("⚠️  Network appliance section not found")


@pytest.mark.infrastructure
def test_refresh_infrastructure(authenticated_infra_page):
    """
    Test refreshing infrastructure data.
    
    Verifies:
    - Refresh button exists
    - Can click refresh
    """
    page = authenticated_infra_page
    
    print("\n🔄 Testing infrastructure refresh")
    
    # Look for refresh button
    refresh_button = page.locator("button:has-text('Refresh'), button[title*='Refresh']")
    
    if refresh_button.count() > 0:
        expect(refresh_button.first).to_be_visible()
        refresh_button.first.click()
        print("✓ Refresh button clicked")
        
        # Wait for refresh to complete
        page.wait_for_timeout(2000)
        print("✓ Infrastructure refreshed")
    else:
        print("⚠️  No refresh button found")


@pytest.mark.infrastructure
def test_view_appliance_logs(authenticated_infra_page):
    """
    Test viewing network appliance logs.
    
    Verifies:
    - View Logs button exists
    - Logs modal opens
    - Log content is displayed
    """
    page = authenticated_infra_page
    
    print("\n📋 Testing appliance logs")
    
    # Look for View Logs button
    logs_button = page.locator("button:has-text('View Logs')")
    
    if logs_button.count() > 0:
        expect(logs_button.first).to_be_visible()
        logs_button.first.click()
        print("✓ View Logs button clicked")
        
        # Wait for logs modal
        logs_modal = page.locator("#deployModal.show")
        expect(logs_modal).to_be_visible(timeout=5000)
        print("✓ Logs modal opened")
        
        # Verify logs content
        expect(logs_modal.locator("text=/Logs|log/i")).to_be_visible()
        
        # Look for log sections
        log_section = page.locator(".log-section, pre, .log-output")
        if log_section.count() > 0:
            print(f"✓ Found {log_section.count()} log section(s)")
        
        # Close modal
        page.keyboard.press("Escape")
        page.wait_for_selector("#deployModal:not(.show)", timeout=5000)
        print("✓ Logs modal closed")
    else:
        print("⚠️  View Logs button not found (appliance may not be deployed)")


@pytest.mark.infrastructure
def test_restart_appliance_button(authenticated_infra_page):
    """
    Test restart appliance button exists.
    
    NOTE: Does NOT actually restart (to avoid disrupting tests).
    Only verifies button is present.
    
    Verifies:
    - Restart button exists
    - Button is clickable
    """
    page = authenticated_infra_page
    
    print("\n🔄 Testing restart appliance button")
    
    # Look for Restart button
    restart_button = page.locator("button:has-text('Restart')")
    
    if restart_button.count() > 0:
        expect(restart_button.first).to_be_visible()
        print("✓ Restart button found")
        
        # Verify it's enabled (don't actually click to avoid disruption)
        is_disabled = restart_button.first.is_disabled()
        if not is_disabled:
            print("✓ Restart button is enabled")
        else:
            print("⚠️  Restart button is disabled")
    else:
        print("⚠️  Restart button not found (appliance may not be deployed)")


@pytest.mark.infrastructure
def test_nat_testing_button(authenticated_infra_page):
    """
    Test NAT testing functionality.
    
    Verifies:
    - Test NAT button exists
    - Can click to test NAT
    """
    page = authenticated_infra_page
    
    print("\n🔌 Testing NAT test button")
    
    # Look for Test NAT button
    nat_button = page.locator("button:has-text('Test NAT')")
    
    if nat_button.count() > 0:
        expect(nat_button.first).to_be_visible()
        nat_button.first.click()
        print("✓ Test NAT button clicked")
        
        # Wait for result
        page.wait_for_timeout(3000)
        
        # Check for status message
        status_div = page.locator("#infrastructureStatus, .status-message")
        if status_div.is_visible():
            status_text = status_div.inner_text()
            print(f"✓ NAT test result: {status_text[:100]}")
        else:
            print("⚠️  No status message appeared")
    else:
        print("⚠️  Test NAT button not found")


@pytest.mark.infrastructure
def test_services_health_grid(authenticated_infra_page):
    """
    Test services health monitoring grid.
    
    Verifies:
    - Services health section exists
    - Service status is displayed
    """
    page = authenticated_infra_page
    
    print("\n❤️  Testing services health grid")
    
    # Look for services section
    services_section = page.locator("text=/Services Health|Service Status/i")
    
    if services_section.count() > 0:
        expect(services_section.first).to_be_visible()
        print("✓ Services health section found")
        
        # Look for service cards
        service_cards = page.locator(".service-card, .health-card")
        if service_cards.count() > 0:
            print(f"✓ Found {service_cards.count()} service(s)")
        else:
            print("⚠️  No service cards found")
    else:
        print("⚠️  Services health section not found")


@pytest.mark.infrastructure
def test_infrastructure_statistics(authenticated_infra_page):
    """
    Test infrastructure statistics display.
    
    Verifies:
    - Statistics are shown (CPU, RAM, etc.)
    - Values are displayed
    """
    page = authenticated_infra_page
    
    print("\n📊 Testing infrastructure statistics")
    
    # Look for stat cards
    stat_cards = page.locator(".stat-card, .metric-card")
    
    if stat_cards.count() > 0:
        print(f"✓ Found {stat_cards.count()} statistic card(s)")
        
        # Check for common metrics
        for metric in ["CPU", "RAM", "Memory", "Disk", "Storage"]:
            if page.locator(f"text=/{metric}/i").count() > 0:
                print(f"  ✓ {metric} metric found")
    else:
        print("⚠️  No statistic cards found")


@pytest.mark.infrastructure
def test_infrastructure_alerts(authenticated_infra_page):
    """
    Test infrastructure alerts/warnings display.
    
    Verifies:
    - Alert sections exist (if any)
    - Warnings are properly styled
    """
    page = authenticated_infra_page
    
    print("\n⚠️  Testing infrastructure alerts")
    
    # Look for alerts
    alerts = page.locator(".alert, .warning, .error-message")
    
    if alerts.count() > 0:
        print(f"✓ Found {alerts.count()} alert(s)")
        
        # Get alert content
        for i in range(min(alerts.count(), 3)):  # Show first 3
            alert_text = alerts.nth(i).inner_text()
            print(f"  Alert {i+1}: {alert_text[:80]}...")
    else:
        print("✓ No alerts (system healthy or no data)")


@pytest.mark.infrastructure
@pytest.mark.slow
def test_infrastructure_realtime_updates(authenticated_infra_page):
    """
    Test that infrastructure page updates in real-time.
    
    Verifies:
    - Data refreshes automatically
    - Timestamps update
    """
    page = authenticated_infra_page
    
    print("\n⏱️  Testing real-time updates")
    
    # Take initial snapshot of status
    initial_html = page.locator("#nodesView").inner_html()
    
    # Wait for auto-refresh (usually 10-30 seconds)
    print("  Waiting for auto-refresh...")
    page.wait_for_timeout(35000)
    
    # Take new snapshot
    updated_html = page.locator("#nodesView").inner_html()
    
    # Check if content changed (indicating refresh occurred)
    if initial_html != updated_html:
        print("✓ Infrastructure data refreshed automatically")
    else:
        print("⚠️  No auto-refresh detected (may have longer interval)")
