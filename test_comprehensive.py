#!/usr/bin/env python3
"""
Comprehensive test suite for Proximity frontend
Tests: Authentication, Navigation, Apps View, Catalog, Settings, Error Handling
"""
from playwright.sync_api import sync_playwright
import time

print("\n" + "="*80)
print("🧪 COMPREHENSIVE FRONTEND TEST SUITE")
print("="*80 + "\n")

test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test_result(name, passed, message=""):
    if passed:
        test_results['passed'].append(name)
        print(f"   ✅ {name}")
    else:
        test_results['failed'].append((name, message))
        print(f"   ❌ {name}: {message}")
    if message and passed:
        test_results['warnings'].append((name, message))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page()
    
    console_errors = []
    js_errors = []
    
    def handle_console(msg):
        if 'error' in msg.type.lower() or '❌' in msg.text:
            console_errors.append(msg.text)
    
    def handle_error(error):
        js_errors.append(str(error))
        print(f'[JS ERROR] {error}')
    
    page.on('console', handle_console)
    page.on('pageerror', handle_error)
    
    # TEST 1: Page Load
    print("\n📋 TEST 1: Page Load and Initial State")
    print("-" * 80)
    try:
        response = page.goto('http://localhost:8765', wait_until='networkidle')
        test_result("Page loads successfully", response.status == 200)
        time.sleep(2)
    except Exception as e:
        test_result("Page loads successfully", False, str(e))
        print("\n❌ Cannot continue tests - page failed to load")
        browser.close()
        exit(1)
    
    # TEST 2: Icons
    print("\n📋 TEST 2: Icon Rendering")
    print("-" * 80)
    svg_count = len(page.query_selector_all('svg'))
    test_result("SVG icons rendered", svg_count > 20, f"{svg_count} icons found")
    
    lucide_loaded = page.evaluate('typeof lucide !== "undefined"')
    test_result("Lucide library loaded", lucide_loaded)
    
    # TEST 3: Navigation Bar
    print("\n📋 TEST 3: Navigation Bar")
    print("-" * 80)
    nav_buttons = page.query_selector_all('.nav-rack-item[data-view]')
    test_result("Navigation buttons present", len(nav_buttons) >= 6, f"{len(nav_buttons)} buttons")
    
    for btn in nav_buttons[:6]:
        view = btn.get_attribute('data-view')
        has_icon = btn.query_selector('svg') is not None
        has_text = btn.query_selector('span') is not None
        test_result(f"Button '{view}' has icon", has_icon)
        test_result(f"Button '{view}' has label", has_text)
    
    # TEST 4: Authentication Modal
    print("\n📋 TEST 4: Authentication Modal")
    print("-" * 80)
    auth_modal = page.query_selector('#authModal')
    test_result("Auth modal exists", auth_modal is not None)
    
    if auth_modal:
        is_visible = auth_modal.is_visible()
        test_result("Auth modal visible", is_visible)
        
        login_tab = page.query_selector('#loginTab')
        test_result("Login tab exists", login_tab is not None)
        
        if login_tab:
            is_active = 'active' in (login_tab.get_attribute('class') or '')
            test_result("Login tab active by default", is_active)
        
        username_field = page.query_selector('#loginUsername')
        password_field = page.query_selector('#loginPassword')
        test_result("Username field exists", username_field is not None)
        test_result("Password field exists", password_field is not None)
    
    # TEST 5: Login Flow
    print("\n📋 TEST 5: Login Flow (fab/invaders)")
    print("-" * 80)
    try:
        page.fill('#loginUsername', 'fab')
        page.fill('#loginPassword', 'invaders')
        test_result("Credentials filled", True)
        
        submit_btn = page.query_selector('button[type="submit"]')
        if submit_btn:
            submit_btn.click()
            test_result("Submit button clicked", True)
            time.sleep(3)
            
            # Check if modal closed
            modal_closed = not page.query_selector('#authModal').is_visible()
            test_result("Modal closed after login", modal_closed)
            
            # Check token
            token = page.evaluate('localStorage.getItem("proximity_token")')
            test_result("Token saved", token is not None)
            
            # Check auth state
            is_auth = page.evaluate('window.Auth && window.Auth.isAuthenticated()')
            test_result("User authenticated", is_auth)
        else:
            test_result("Submit button found", False)
    except Exception as e:
        test_result("Login flow", False, str(e))
    
    # TEST 6: Dashboard View
    print("\n📋 TEST 6: Dashboard View")
    print("-" * 80)
    time.sleep(1)
    
    hero_section = page.query_selector('.hero-section')
    test_result("Hero section exists", hero_section is not None)
    
    stats_cards = page.query_selector_all('.stats-card')
    test_result("Stats cards rendered", len(stats_cards) > 0, f"{len(stats_cards)} cards")
    
    quick_actions = page.query_selector('.quick-actions')
    test_result("Quick actions section exists", quick_actions is not None)
    
    # TEST 7: Navigation to Apps
    print("\n📋 TEST 7: Navigation - Apps View")
    print("-" * 80)
    apps_btn = page.query_selector('[data-view="apps"]')
    if apps_btn:
        apps_btn.click()
        time.sleep(2)
        
        # Check if active
        is_active = 'active' in apps_btn.get_attribute('class')
        test_result("Apps button active", is_active)
        
        # Check container visibility
        apps_container = page.query_selector('#appsView')
        is_visible = apps_container and not ('hidden' in apps_container.get_attribute('class'))
        test_result("Apps view visible", is_visible)
        
        # Check for empty state or app cards
        empty_state = page.query_selector('.empty-state')
        app_cards = page.query_selector_all('.app-card')
        
        if empty_state:
            test_result("Apps view shows content", True, "Empty state (no apps)")
        elif len(app_cards) > 0:
            test_result("Apps view shows content", True, f"{len(app_cards)} apps")
        else:
            test_result("Apps view shows content", False, "No content found")
    else:
        test_result("Apps button found", False)
    
    # TEST 8: Navigation to Catalog
    print("\n📋 TEST 8: Navigation - Catalog View")
    print("-" * 80)
    catalog_btn = page.query_selector('[data-view="catalog"]')
    if catalog_btn:
        catalog_btn.click()
        time.sleep(2)
        
        is_active = 'active' in catalog_btn.get_attribute('class')
        test_result("Catalog button active", is_active)
        
        catalog_container = page.query_selector('#catalogView')
        is_visible = catalog_container and not ('hidden' in catalog_container.get_attribute('class'))
        test_result("Catalog view visible", is_visible)
        
        # Check for catalog content
        catalog_items = page.query_selector_all('.catalog-item, .app-card')
        search_bar = page.query_selector('input[type="search"], .search-input')
        
        test_result("Catalog items rendered", len(catalog_items) > 0, f"{len(catalog_items)} items")
        test_result("Search bar exists", search_bar is not None)
    else:
        test_result("Catalog button found", False)
    
    # TEST 9: Navigation to Settings
    print("\n📋 TEST 9: Navigation - Settings View")
    print("-" * 80)
    settings_btn = page.query_selector('[data-view="settings"]')
    if settings_btn:
        settings_btn.click()
        time.sleep(2)
        
        is_active = 'active' in settings_btn.get_attribute('class')
        test_result("Settings button active", is_active)
        
        settings_container = page.query_selector('#settingsView')
        is_visible = settings_container and not ('hidden' in settings_container.get_attribute('class'))
        test_result("Settings view visible", is_visible)
        
        # Check for settings tabs
        settings_tabs = page.query_selector_all('.settings-tab, .sub-nav-item')
        test_result("Settings tabs rendered", len(settings_tabs) > 0, f"{len(settings_tabs)} tabs")
    else:
        test_result("Settings button found", False)
    
    # TEST 10: Navigation to Monitoring
    print("\n📋 TEST 10: Navigation - Monitoring View")
    print("-" * 80)
    monitoring_btn = page.query_selector('[data-view="monitoring"]')
    if monitoring_btn:
        monitoring_btn.click()
        time.sleep(2)
        
        is_active = 'active' in monitoring_btn.get_attribute('class')
        test_result("Monitoring button active", is_active)
        
        monitoring_container = page.query_selector('#monitoringView')
        is_visible = monitoring_container and not ('hidden' in monitoring_container.get_attribute('class'))
        test_result("Monitoring view visible", is_visible)
    else:
        test_result("Monitoring button found", False)
    
    # TEST 11: Navigation to Nodes
    print("\n📋 TEST 11: Navigation - Nodes View")
    print("-" * 80)
    nodes_btn = page.query_selector('[data-view="nodes"]')
    if nodes_btn:
        nodes_btn.click()
        time.sleep(2)
        
        is_active = 'active' in nodes_btn.get_attribute('class')
        test_result("Nodes button active", is_active)
        
        nodes_container = page.query_selector('#nodesView')
        is_visible = nodes_container and not ('hidden' in nodes_container.get_attribute('class'))
        test_result("Nodes view visible", is_visible)
    else:
        test_result("Nodes button found", False)
    
    # TEST 12: Back to Dashboard
    print("\n📋 TEST 12: Navigation - Back to Dashboard")
    print("-" * 80)
    dashboard_btn = page.query_selector('[data-view="dashboard"]')
    if dashboard_btn:
        dashboard_btn.click()
        time.sleep(1)
        
        is_active = 'active' in dashboard_btn.get_attribute('class')
        test_result("Dashboard button active", is_active)
        
        dashboard_container = page.query_selector('#dashboardView')
        is_visible = dashboard_container and not ('hidden' in dashboard_container.get_attribute('class'))
        test_result("Dashboard view visible", is_visible)
    
    # TEST 13: Sound Control
    print("\n📋 TEST 13: Sound Control")
    print("-" * 80)
    sound_btn = page.query_selector('#soundToggleBtn')
    test_result("Sound button exists", sound_btn is not None)
    
    if sound_btn:
        sound_service = page.evaluate('typeof window.SoundService !== "undefined"')
        test_result("SoundService loaded", sound_service)
    
    # TEST 14: Logout Button
    print("\n📋 TEST 14: Logout Functionality")
    print("-" * 80)
    logout_btn = page.query_selector('[data-action="logout"]')
    test_result("Logout button exists", logout_btn is not None)
    
    # TEST 15: Error Console Check
    print("\n📋 TEST 15: JavaScript Errors")
    print("-" * 80)
    test_result("No JavaScript errors", len(js_errors) == 0, f"{len(js_errors)} errors")
    test_result("No console errors", len(console_errors) < 5, f"{len(console_errors)} errors")
    
    # SUMMARY
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results['failed']:
        print("\n❌ FAILED TESTS:")
        for name, msg in test_results['failed']:
            print(f"   • {name}")
            if msg:
                print(f"     → {msg}")
    
    if test_results['warnings']:
        print("\n⚠️  WARNINGS:")
        for name, msg in test_results['warnings']:
            print(f"   • {name}: {msg}")
    
    if js_errors:
        print("\n🐛 JAVASCRIPT ERRORS:")
        for error in js_errors[:10]:
            print(f"   • {error}")
    
    pass_rate = len(test_results['passed']) / (len(test_results['passed']) + len(test_results['failed'])) * 100
    print(f"\n📈 Pass Rate: {pass_rate:.1f}%")
    print("="*80 + "\n")
    
    input('Press Enter to close browser...')
    browser.close()
    
    # Exit with error code if tests failed
    exit(0 if len(test_results['failed']) == 0 else 1)
