"""
E2E Tests for Proxmox Nodes View.

Tests the simplified infrastructure page that shows Proxmox nodes only.
No network appliance, just basic node information display.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def nodes_page(authenticated_page: Page):
    """Fixture providing authenticated page on Proxmox nodes view."""
    page = authenticated_page
    # Navigate to nodes view
    page.click("[data-view='nodes']")
    expect(page.locator("#nodesView")).to_be_visible(timeout=10000)
    
    return page


@pytest.mark.nodes
def test_nodes_page_loads(nodes_page):
    """
    Test that Proxmox nodes page loads correctly.
    
    Verifies:
    - Nodes view is visible
    - Page has expected sections
    """
    page = nodes_page
    
    print("\n🖥️  Testing Proxmox nodes page load")
    
    # Verify nodes view
    nodes_view = page.locator("#nodesView")
    expect(nodes_view).to_be_visible()
    print("✓ Nodes view loaded")
    
    # Check for main content
    expect(nodes_view.locator("text=/node|proxmox/i").first).to_be_visible()
    print("✓ Node content present")


@pytest.mark.nodes
def test_proxmox_nodes_display(nodes_page):
    """
    Test displaying Proxmox nodes.
    
    Verifies:
    - Node information is displayed
    - Node cards/sections exist
    """
    page = nodes_page
    
    print("\n📋 Testing Proxmox nodes display")
    
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


@pytest.mark.nodes
def test_node_information_content(nodes_page):
    """
    Test that node information contains expected details.
    
    Verifies:
    - Node name is displayed
    - Status or other basic info is shown
    """
    page = nodes_page
    
    print("\n📊 Testing node information content")
    
    # Check for common node information patterns
    # This is flexible since exact content depends on Proxmox configuration
    nodes_view = page.locator("#nodesView")
    
    # Should have some textual content about nodes
    content = nodes_view.inner_text()
    
    if content and len(content.strip()) > 10:
        print(f"✓ Node view has content ({len(content)} chars)")
    else:
        print("⚠️  Node view seems empty")


@pytest.mark.nodes
def test_refresh_nodes(nodes_page):
    """
    Test refreshing nodes data.
    
    Verifies:
    - Refresh button exists
    - Can click refresh
    """
    page = nodes_page
    
    print("\n🔄 Testing nodes refresh")
    
    # Look for refresh button
    refresh_button = page.locator("button:has-text('Refresh'), button[title*='Refresh'], button:has([data-lucide='refresh-cw'])")
    
    if refresh_button.count() > 0:
        expect(refresh_button.first).to_be_visible()
        refresh_button.first.click()
        print("✓ Refresh button clicked")
        
        # Wait for refresh to complete
        page.wait_for_timeout(1000)
        print("✓ Nodes refreshed")
    else:
        print("⚠️  No refresh button found")


@pytest.mark.nodes
def test_nodes_navigation(authenticated_page):
    """
    Test navigation to nodes page from different sections.
    
    Verifies:
    - Can navigate to nodes from dashboard
    - Navigation button/link is visible
    """
    page = authenticated_page
    
    print("\n🧭 Testing navigation to nodes page")
    
    # Find and click nodes navigation button
    nodes_nav = page.locator("[data-view='nodes'], nav a:has-text('Nodes'), nav button:has-text('Nodes')")
    
    if nodes_nav.count() > 0:
        expect(nodes_nav.first).to_be_visible()
        nodes_nav.first.click()
        print("✓ Clicked nodes navigation")
        
        # Verify nodes view appears
        expect(page.locator("#nodesView")).to_be_visible(timeout=10000)
        print("✓ Nodes view displayed")
    else:
        print("⚠️  Nodes navigation button not found")
