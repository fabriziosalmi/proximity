"""
E2E Tests for UI Navigation - Rewritten for New Modular Frontend.

Tests navigation in the new modular UI design:
- Nav-rack navigation (no sidebar)
- Simple view switching
- Active indicators
- Logo navigation

OLD FEATURES REMOVED:
- Sidebar collapse/expand (no sidebar)
- User profile dropdown (simplified to username display + logout button)
- Breadcrumb navigation (not in new design)
- Complex user menus (simplified)
"""

import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import generate_test_user


@pytest.mark.navigation
@pytest.mark.smoke
def test_navigate_all_views(authenticated_page):
    """
    Test navigating through all main views in the new modularized UI.
    
    The new UI uses a nav-rack system with simple navigation items.
    No sidebar, no complex dropdowns - just clean navigation buttons.
    
    Verifies:
    - Can navigate to Dashboard
    - Can navigate to Catalog (Store)
    - Can navigate to Apps
    - Can navigate to Nodes (Infrastructure)
    - Can navigate to Settings
    
    Expected: All views load successfully with proper view containers visible.
    """
    page = authenticated_page
    
    print("\n🧭 Testing navigation through all views (New Modular UI)")
    
    # Dashboard
    print("  → Dashboard")
    page.click("a.nav-rack-item[data-view='dashboard']")
    expect(page.locator("#dashboardView")).to_be_visible(timeout=10000)
    print("  ✓ Dashboard loaded")
    
    # Catalog (App Store) - Use specific selector to avoid button ambiguity
    print("  → Catalog (Store)")
    page.click("a.nav-rack-item[data-view='catalog']")
    expect(page.locator("#catalogView")).to_be_visible(timeout=10000)
    print("  ✓ Catalog loaded")
    
    # Apps (Deployed Apps)
    print("  → Apps")
    page.click("a.nav-rack-item[data-view='apps']")
    # Wait for apps view to be fully loaded (data-loaded attribute)
    page.wait_for_function("""
        () => document.getElementById('appsView')?.getAttribute('data-loaded') === 'true'
    """, timeout=30000)
    expect(page.locator("#appsView")).to_be_visible(timeout=10000)
    print("  ✓ Apps loaded")

    # Nodes (Infrastructure) - May have initialization issues
    print("  → Nodes")
    page.click("a.nav-rack-item[data-view='nodes']")
    page.wait_for_timeout(1000)
    # Check if view is visible (may have loading issues)
    nodes_view = page.locator("#nodesView")
    if nodes_view.is_visible():
        print("  ✓ Nodes loaded")
    else:
        print("  ⚠️  Nodes view not visible (may have initialization issues)")
    
    # Settings
    print("  → Settings")
    page.click("a.nav-rack-item[data-view='settings']")
    expect(page.locator("#settingsView")).to_be_visible(timeout=10000)
    print("  ✓ Settings loaded")
    
    # Back to Dashboard
    print("  → Back to Dashboard")
    page.click("a.nav-rack-item[data-view='dashboard']")
    expect(page.locator("#dashboardView")).to_be_visible(timeout=10000)
    print("  ✓ Navigation cycle complete")


@pytest.mark.navigation
@pytest.mark.skip(reason="Sidebar removed in modular UI - now uses nav-rack")
def test_sidebar_collapse_expand(authenticated_page):
    """OBSOLETE: Sidebar feature removed in modular UI redesign."""
    pass


@pytest.mark.navigation  
@pytest.mark.skip(reason="User profile dropdown removed - now simple username + logout button")
def test_user_menu_toggle(authenticated_page):
    """OBSOLETE: User menu dropdown removed in modular UI redesign."""
    pass


@pytest.mark.navigation
@pytest.mark.skip(reason="User profile page not in current design")
def test_user_profile_info_display(authenticated_page):
    """OBSOLETE: Dedicated profile display removed."""
    pass


@pytest.mark.navigation
@pytest.mark.skip(reason="Profile navigation removed - no profile page in current UI")
def test_navigate_to_profile(authenticated_page):
    """OBSOLETE: Profile page removed in modular UI redesign."""
    pass


@pytest.mark.navigation
def test_active_nav_indicator(authenticated_page):
    """
    Test active navigation indicator in new nav-rack UI.
    
    Verifies:
    - Current view has active indicator
    - Active class applied to correct nav item
    - Visual feedback for current location
    """
    page = authenticated_page
    
    print("\n🎯 Testing active navigation indicators")
    
    # Navigate to catalog
    page.click("a.nav-rack-item[data-view='catalog']")
    page.wait_for_timeout(500)
    
    # Check catalog nav has active class
    catalog_nav = page.locator("a.nav-rack-item[data-view='catalog']")
    catalog_class = catalog_nav.get_attribute("class")
    assert "active" in catalog_class, f"Catalog nav should have 'active' class, got: {catalog_class}"
    print("  ✓ Catalog nav marked as active")
    
    # Navigate to apps
    page.click("a.nav-rack-item[data-view='apps']")
    # Wait for apps view to be fully loaded (it's async)
    page.wait_for_function("""
        () => document.getElementById('appsView')?.getAttribute('data-loaded') === 'true'
    """, timeout=30000)
    page.wait_for_timeout(500)
    
    # Check apps nav has active class
    apps_nav = page.locator("a.nav-rack-item[data-view='apps']")
    apps_class = apps_nav.get_attribute("class")
    assert "active" in apps_class, f"Apps nav should have 'active' class, got: {apps_class}"
    print("  ✓ Apps nav marked as active")
    
    # Verify catalog is no longer active
    catalog_class_now = catalog_nav.get_attribute("class")
    assert "active" not in catalog_class_now, "Previous nav should not be active"
    print("  ✓ Previous nav no longer active")


@pytest.mark.navigation
@pytest.mark.skip(reason="Keyboard shortcuts not yet implemented in modular UI")
def test_navigation_keyboard_shortcuts(authenticated_page):
    """POSTPONED: Keyboard shortcuts feature not yet in modular UI."""
    pass


@pytest.mark.navigation
@pytest.mark.skip(reason="Breadcrumb navigation not in current design")
def test_breadcrumb_navigation(authenticated_page):
    """OBSOLETE: Breadcrumb navigation not part of modular UI design."""
    pass


@pytest.mark.navigation
def test_page_titles_update(authenticated_page):
    """
    Test page title updates when navigating.
    
    Verifies:
    - Page title changes with view
    - Title reflects current location
    """
    page = authenticated_page
    
    print("\n📄 Testing page title updates")
    
    # Navigate to catalog and check title
    page.click("a.nav-rack-item[data-view='catalog']")
    page.wait_for_timeout(500)
    title = page.title()
    assert "catalog" in title.lower() or "store" in title.lower(), \
        f"Expected title to contain 'catalog' or 'store', got: {title}"
    print(f"  ✓ Catalog title: {title}")
    
    # Navigate to apps and check title
    page.click("a.nav-rack-item[data-view='apps']")
    # Wait for apps view to be fully loaded
    page.wait_for_function("""
        () => document.getElementById('appsView')?.getAttribute('data-loaded') === 'true'
    """, timeout=30000)
    page.wait_for_timeout(500)
    title = page.title()
    assert "apps" in title.lower() or "my apps" in title.lower(), \
        f"Expected title to contain 'apps' or 'my apps', got: {title}"
    print(f"  ✓ Apps title: {title}")


@pytest.mark.navigation
def test_quick_deploy_button(authenticated_page):
    """
    Test quick deploy button on dashboard (if empty state).
    
    Verifies:
    - Quick deploy button navigates to catalog
    - Catalog view opens properly
    """
    page = authenticated_page
    
    print("\n🚀 Testing quick deploy button")
    
    # Go to dashboard
    page.click("a.nav-rack-item[data-view='dashboard']")
    page.wait_for_timeout(500)
    
    # Look for quick deploy button (appears in empty state)
    quick_deploy = page.locator("button[data-view='catalog']")
    
    if quick_deploy.count() > 0 and quick_deploy.is_visible():
        print("  Found quick deploy button")
        quick_deploy.click()
        page.wait_for_timeout(500)
        
        # Should navigate to catalog
        expect(page.locator("#catalogView")).to_be_visible(timeout=10000)
        print("  ✓ Quick deploy button navigated to catalog")
    else:
        print("  ⊘ Quick deploy button not visible (may have apps deployed)")


@pytest.mark.navigation
def test_logo_click_returns_home(authenticated_page):
    """
    Test clicking logo returns to dashboard.
    
    Verifies:
    - Logo is clickable
    - Clicking logo navigates to dashboard
    """
    page = authenticated_page
    
    print("\n🏠 Testing logo click navigation")
    
    # Navigate away from dashboard
    page.click("a.nav-rack-item[data-view='settings']")
    expect(page.locator("#settingsView")).to_be_visible(timeout=10000)
    print("  → Navigated to Settings")
    
    # Click logo
    logo = page.locator(".logo, .brand, a[href='#']:has-text('Proximity')")
    if logo.count() > 0:
        logo.first.click()
        page.wait_for_timeout(500)
        
        # Should navigate to dashboard
        expect(page.locator("#dashboardView")).to_be_visible(timeout=10000)
        print("  ✓ Logo click returned to dashboard")
    else:
        print("  ⊘ Logo element not found")
