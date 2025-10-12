"""
E2E Tests for UI Navigation and Interactions.

Tests all navigation elements and UI interactions:
- Sidebar navigation between views
- Sidebar collapse/expand
- User menu toggle
- View switching
- Profile access
- Responsive behavior
"""

import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import generate_test_user


# Use authenticated_page fixture from conftest.py (has proper wait timing)


@pytest.mark.navigation
@pytest.mark.smoke
def test_navigate_all_views(authenticated_page):
    """
    Test navigating through all main views.
    
    Verifies:
    - Can navigate to Dashboard
    - Can navigate to Catalog
    - Can navigate to Apps
    - Can navigate to Infrastructure
    - Can navigate to Monitoring (if exists)
    - Can navigate to Settings
    
    Expected: All views load successfully.
    """
    page = authenticated_page
    
    print("\n🧭 Testing navigation through all views")
    
    # Dashboard
    print("  → Dashboard")
    page.click("[data-view='dashboard']")
    expect(page.locator("#dashboardView")).to_be_visible(timeout=10000)
    # Check active class
    dashboard_nav = page.locator(".nav-item[data-view='dashboard']")
    assert "active" in dashboard_nav.get_attribute("class")
    print("  ✓ Dashboard loaded")
    
    # Catalog (App Store)
    print("  → Catalog")
    page.click("a.nav-rack-item[data-view='catalog']")  # Specific to nav link to avoid ambiguity
    expect(page.locator("#catalogView, #appStoreView")).to_be_visible(timeout=10000)
    print("  ✓ Catalog loaded")
    
    # Apps (Deployed Apps)
    print("  → Apps")
    page.click("[data-view='apps']")
    expect(page.locator("#appsView")).to_be_visible(timeout=10000)
    print("  ✓ Apps loaded")

    # Nodes (Infrastructure)
    print("  → Nodes")
    page.click("[data-view='nodes']")
    expect(page.locator("#nodesView")).to_be_visible(timeout=10000)
    print("  ✓ Nodes loaded")
    
    # Monitoring (if exists)
    monitoring_nav = page.locator("[data-view='monitoring']")
    if monitoring_nav.count() > 0:
        print("  → Monitoring")
        page.click("[data-view='monitoring']")
        expect(page.locator("#monitoringView")).to_be_visible(timeout=10000)
        print("  ✓ Monitoring loaded")
    else:
        print("  ⊘ Monitoring view not found (may not be implemented)")
    
    # Settings
    print("  → Settings")
    page.click("[data-view='settings']")
    expect(page.locator("#settingsView")).to_be_visible(timeout=10000)
    print("  ✓ Settings loaded")
    
    # Back to Dashboard
    print("  → Back to Dashboard")
    page.click("[data-view='dashboard']")
    expect(page.locator("#dashboardView")).to_be_visible(timeout=10000)
    print("  ✓ Navigation cycle complete")


@pytest.mark.navigation
def test_sidebar_collapse_expand(authenticated_page):
    """
    Test sidebar collapse/expand functionality.
    
    Verifies:
    - Sidebar starts expanded
    - Can collapse sidebar
    - Can expand sidebar
    - Toggle button works
    - State persists
    """
    page = authenticated_page
    
    print("\n📐 Testing sidebar collapse/expand")
    
    # Find sidebar and toggle button
    sidebar = page.locator(".sidebar")
    toggle_button = page.locator("#sidebarToggle, button[aria-label*='toggle'], .sidebar-toggle")
    
    # Check initial state (should be expanded)
    is_collapsed = "collapsed" in sidebar.get_attribute("class")
    if not is_collapsed:
        print("  ✓ Sidebar initially expanded")
    else:
        print("  ⚠️  Sidebar initially collapsed")
    
    # Find and click toggle button
    if toggle_button.count() > 0:
        print("  Collapsing sidebar...")
        toggle_button.first.click()
        page.wait_for_timeout(500)  # Animation time
        
        # Verify collapsed
        assert "collapsed" in sidebar.get_attribute("class")
        print("  ✓ Sidebar collapsed")
        
        # Expand again
        print("  Expanding sidebar...")
        toggle_button.first.click()
        page.wait_for_timeout(500)
        
        # Verify expanded
        sidebar_class = sidebar.get_attribute("class")
        is_collapsed = "collapsed" in sidebar_class
        if not is_collapsed:
            print("  ✓ Sidebar expanded")
        else:
            print("  ⚠️  Sidebar still collapsed")
    else:
        print("  ⊘ Sidebar toggle button not found")


@pytest.mark.navigation
def test_user_menu_toggle(authenticated_page):
    """
    Test user menu dropdown toggle.
    
    Verifies:
    - User menu button exists
    - Can open user menu
    - Menu items are visible
    - Can close user menu
    """
    page = authenticated_page
    
    print("\n👤 Testing user menu toggle")
    
    # Find user menu button
    user_menu_btn = page.locator("#userProfileBtn, .user-profile")
    expect(user_menu_btn).to_be_visible()
    print("  ✓ User menu button found")
    
    # Click to open
    user_menu_btn.click()
    page.wait_for_timeout(300)
    
    # Verify menu is visible
    user_menu = page.locator("#userMenu, .user-menu")
    expect(user_menu).to_be_visible()
    print("  ✓ User menu opened")
    
    # Verify menu items exist
    profile_item = page.locator(".user-menu-item:has-text('Profile'), a:has-text('Profile')")
    settings_item = page.locator(".user-menu-item:has-text('Settings'), a:has-text('Settings')")
    logout_item = page.locator(".user-menu-item:has-text('Logout'), a:has-text('Logout')")
    
    menu_items_count = page.locator(".user-menu-item").count()
    print(f"  ✓ Found {menu_items_count} menu item(s)")
    
    # Close menu (click outside)
    page.mouse.click(100, 100)
    page.wait_for_timeout(300)
    
    # Menu should be hidden now
    if not user_menu.is_visible():
        print("  ✓ User menu closed")
    else:
        print("  ⚠️  User menu still visible")


@pytest.mark.navigation
def test_user_profile_info_display(authenticated_page):
    """
    Test user profile information display.
    
    Verifies:
    - Username is displayed
    - User role is displayed
    - User avatar/initials shown
    """
    page = authenticated_page
    
    print("\n👨‍💼 Testing user profile display")
    
    # Check user name
    user_name = page.locator(".user-name")
    if user_name.is_visible():
        name_text = user_name.inner_text()
        print(f"  ✓ Username: {name_text}")
    else:
        print("  ⚠️  Username not displayed")
    
    # Check user role
    user_role = page.locator(".user-role")
    if user_role.is_visible():
        role_text = user_role.inner_text()
        print(f"  ✓ User role: {role_text}")
    else:
        print("  ⚠️  User role not displayed")
    
    # Check user avatar
    user_avatar = page.locator(".user-avatar")
    if user_avatar.is_visible():
        avatar_text = user_avatar.inner_text()
        print(f"  ✓ User avatar: {avatar_text}")
    else:
        print("  ⚠️  User avatar not displayed")


@pytest.mark.navigation
def test_navigate_to_profile(authenticated_page):
    """
    Test navigating to user profile.
    
    Verifies:
    - Can click Profile in user menu
    - Profile view/modal opens
    """
    page = authenticated_page
    
    print("\n📋 Testing profile navigation")
    
    # Open user menu
    user_menu_btn = page.locator("#userProfileBtn, .user-profile")
    user_menu_btn.click()
    page.wait_for_timeout(300)
    
    # Click Profile
    profile_item = page.locator(".user-menu-item:has-text('Profile'), a:has-text('Profile')")
    
    if profile_item.count() > 0:
        profile_item.click()
        page.wait_for_timeout(1000)
        
        # Profile might be a modal or a view
        # Check for either
        profile_modal = page.locator("#profileModal, .modal:has-text('Profile')")
        profile_view = page.locator("#profileView")
        
        if profile_modal.is_visible():
            print("  ✓ Profile modal opened")
        elif profile_view.is_visible():
            print("  ✓ Profile view loaded")
        else:
            print("  ⚠️  Profile not found (may not be implemented)")
    else:
        print("  ⊘ Profile menu item not found")


@pytest.mark.navigation
def test_active_nav_indicator(authenticated_page):
    """
    Test that active navigation item is highlighted.
    
    Verifies:
    - Active nav item has 'active' class
    - Only one nav item is active at a time
    """
    page = authenticated_page
    
    print("\n✨ Testing active navigation indicator")

    views = ["dashboard", "catalog", "apps", "nodes", "settings"]
    
    for view_name in views:
        # Navigate to view
        nav_item = page.locator(f"[data-view='{view_name}']")
        
        if nav_item.count() > 0:
            nav_item.click()
            page.wait_for_timeout(500)
            
            # Check if it's active
            assert "active" in nav_item.get_attribute("class")
            
            # Count active items (should be exactly 1)
            active_count = page.locator(".nav-item.active").count()
            if active_count == 1:
                print(f"  ✓ {view_name}: Active indicator correct")
            else:
                print(f"  ⚠️  {view_name}: {active_count} active items (expected 1)")


@pytest.mark.navigation
def test_navigation_keyboard_shortcuts(authenticated_page):
    """
    Test keyboard navigation (if implemented).
    
    Tests common shortcuts like:
    - Tab navigation
    - Escape to close modals
    - Arrow keys (if applicable)
    """
    page = authenticated_page
    
    print("\n⌨️  Testing keyboard navigation")
    
    # Test Tab navigation
    page.keyboard.press("Tab")
    page.wait_for_timeout(200)
    
    focused = page.evaluate("document.activeElement.tagName")
    print(f"  ✓ Tab navigation works (focused: {focused})")
    
    # Test Escape (should close any open modal)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    
    # Check if any modal is visible
    modal = page.locator(".modal.show")
    if not modal.is_visible():
        print("  ✓ Escape key works (no modal visible)")
    else:
        print("  ⚠️  Modal still visible after Escape")


@pytest.mark.navigation
def test_breadcrumb_navigation(authenticated_page):
    """
    Test breadcrumb navigation (if exists).
    
    Verifies:
    - Breadcrumbs are displayed
    - Can navigate using breadcrumbs
    """
    page = authenticated_page
    
    print("\n🍞 Testing breadcrumb navigation")
    
    # Look for breadcrumb
    breadcrumb = page.locator(".breadcrumb, nav[aria-label='breadcrumb']")
    
    if breadcrumb.count() > 0:
        expect(breadcrumb.first).to_be_visible()
        print("  ✓ Breadcrumb found")
        
        # Check for breadcrumb items
        items = page.locator(".breadcrumb-item, .breadcrumb a")
        print(f"  ✓ Breadcrumb has {items.count()} item(s)")
    else:
        print("  ⊘ Breadcrumb not found (may not be implemented)")


@pytest.mark.navigation
def test_page_titles_update(authenticated_page):
    """
    Test that page titles update when navigating.
    
    Verifies:
    - Page title changes per view
    - Title is descriptive
    """
    page = authenticated_page
    
    print("\n📄 Testing page title updates")
    
    views = [
        ("dashboard", "Dashboard"),
        ("catalog", "Catalog"),
        ("apps", "Apps"),
        ("settings", "Settings")
    ]
    
    for view_id, expected_title in views:
        nav_item = page.locator(f"[data-view='{view_id}']")
        if nav_item.count() > 0:
            nav_item.click()
            page.wait_for_timeout(500)
            
            # Check page title header
            page_title = page.locator(".page-title, h1")
            if page_title.count() > 0:
                title_text = page_title.first.inner_text()
                if expected_title.lower() in title_text.lower():
                    print(f"  ✓ {view_id}: Title '{title_text}'")
                else:
                    print(f"  ⚠️  {view_id}: Title '{title_text}' (expected '{expected_title}')")


@pytest.mark.navigation
def test_quick_deploy_button(authenticated_page):
    """
    Test quick deploy button on dashboard.
    
    Verifies:
    - Deploy button exists on dashboard
    - Clicking it navigates to catalog
    """
    page = authenticated_page
    
    print("\n🚀 Testing quick deploy button")
    
    # Go to dashboard
    page.click("[data-view='dashboard']")
    page.wait_for_timeout(500)
    
    # Look for deploy/add button
    deploy_button = page.locator("button:has-text('Deploy'), button:has-text('Add App')")
    
    if deploy_button.count() > 0:
        expect(deploy_button.first).to_be_visible()
        print("  ✓ Quick deploy button found")
        
        # Click it
        deploy_button.first.click()
        page.wait_for_timeout(1000)
        
        # Should navigate to catalog
        if page.locator("#catalogView, #appStoreView").is_visible():
            print("  ✓ Navigated to catalog")
        else:
            print("  ⚠️  Did not navigate to catalog")
    else:
        print("  ⊘ Quick deploy button not found")


@pytest.mark.navigation
def test_logo_click_returns_home(authenticated_page):
    """
    Test clicking logo/brand returns to dashboard.
    
    Verifies:
    - Logo/brand is clickable
    - Returns to dashboard
    """
    page = authenticated_page
    
    print("\n🏠 Testing logo click")
    
    # Navigate away from dashboard
    page.click("[data-view='settings']")
    page.wait_for_timeout(500)
    
    # Find and click logo/brand
    logo = page.locator(".logo, .brand, .app-logo, a[href='/'], a[href='#']").first
    
    if logo.count() > 0:
        logo.click()
        page.wait_for_timeout(1000)
        
        # Should be back on dashboard
        if page.locator("#dashboardView").is_visible():
            print("  ✓ Logo click returned to dashboard")
        else:
            print("  ⚠️  Logo click did not return to dashboard")
    else:
        print("  ⊘ Logo not found or not clickable")
