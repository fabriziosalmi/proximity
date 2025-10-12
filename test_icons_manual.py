#!/usr/bin/env python3
"""
Manual test to verify that icons are visible and navigation buttons work.
This script opens a browser and prints diagnostic information.
"""
import asyncio
import time
from playwright.sync_api import sync_playwright

def test_icons_and_navigation():
    """Test that icons are visible and navigation buttons work."""
    print("\n" + "="*80)
    print("🧪 TESTING ICON VISIBILITY AND NAVIGATION")
    print("="*80 + "\n")
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode for visual inspection
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Set up console listeners
        console_messages = []
        def handle_console(msg):
            message = f'[CONSOLE {msg.type}] {msg.text}'
            console_messages.append(message)
            print(message)
        
        # Set up error listeners
        errors = []
        def handle_error(error):
            error_msg = f'[PAGE ERROR] {error}'
            errors.append(error_msg)
            print(error_msg)
        
        page.on('console', handle_console)
        page.on('pageerror', handle_error)
        
        print('📍 Step 1: Loading page at http://localhost:8765')
        response = page.goto('http://localhost:8765', wait_until='networkidle')
        print(f'   Status: {response.status}')
        
        # Wait for the page to be fully loaded
        print('\n⏳ Step 2: Waiting for page to be ready...')
        page.wait_for_timeout(2000)
        
        # Check if Lucide is loaded
        print('\n🔍 Step 3: Checking if Lucide library is loaded...')
        lucide_loaded = page.evaluate('typeof lucide !== "undefined"')
        print(f'   Lucide loaded: {"✅ YES" if lucide_loaded else "❌ NO"}')
        
        # Count icon elements
        print('\n🔍 Step 4: Checking icon elements...')
        icon_selectors = page.query_selector_all('[data-lucide]')
        print(f'   Elements with data-lucide attribute: {len(icon_selectors)}')
        
        # Check SVG icons rendered
        svg_icons = page.query_selector_all('.nav-rack-item svg')
        print(f'   SVG icons rendered: {len(svg_icons)}')
        
        # List all navigation buttons
        print('\n🔍 Step 5: Listing navigation buttons...')
        nav_buttons = page.query_selector_all('.nav-rack-item')
        print(f'   Total navigation buttons: {len(nav_buttons)}')
        
        for i, btn in enumerate(nav_buttons):
            view = btn.get_attribute('data-view')
            title = btn.get_attribute('title')
            is_visible = btn.is_visible()
            has_icon = btn.query_selector('svg') is not None
            print(f'   [{i+1}] View: {view}, Title: {title}, Visible: {is_visible}, Has Icon: {has_icon}')
        
        # Test clicking on a navigation button
        print('\n🖱️  Step 6: Testing navigation click (Dashboard -> Apps)...')
        apps_button = page.query_selector('[data-view="apps"]')
        if apps_button:
            print('   Found Apps button, clicking...')
            apps_button.click()
            page.wait_for_timeout(1000)
            
            # Check if view changed
            active_nav = page.query_selector('.nav-rack-item.active')
            if active_nav:
                active_view = active_nav.get_attribute('data-view')
                print(f'   Active view after click: {active_view}')
                print(f'   Navigation working: {"✅ YES" if active_view == "apps" else "❌ NO"}')
            else:
                print('   ❌ No active navigation item found')
        else:
            print('   ❌ Apps button not found')
        
        # Test clicking on another button
        print('\n🖱️  Step 7: Testing navigation click (Apps -> Catalog)...')
        catalog_button = page.query_selector('[data-view="catalog"]')
        if catalog_button:
            print('   Found Catalog button, clicking...')
            catalog_button.click()
            page.wait_for_timeout(1000)
            
            # Check if view changed
            active_nav = page.query_selector('.nav-rack-item.active')
            if active_nav:
                active_view = active_nav.get_attribute('data-view')
                print(f'   Active view after click: {active_view}')
                print(f'   Navigation working: {"✅ YES" if active_view == "catalog" else "❌ NO"}')
            else:
                print('   ❌ No active navigation item found')
        else:
            print('   ❌ Catalog button not found')
        
        # Summary
        print('\n' + "="*80)
        print('📊 TEST SUMMARY')
        print("="*80)
        print(f'Lucide loaded: {"✅" if lucide_loaded else "❌"}')
        print(f'Icon elements found: {len(icon_selectors)}')
        print(f'SVG icons rendered: {len(svg_icons)}')
        print(f'Navigation buttons: {len(nav_buttons)}')
        print(f'Console messages: {len(console_messages)}')
        print(f'Errors: {len(errors)}')
        
        if errors:
            print('\n❌ ERRORS DETECTED:')
            for error in errors:
                print(f'   {error}')
        
        print('\n' + "="*80)
        print('👁️  Browser left open for manual inspection.')
        print('   Please verify that:')
        print('   1. Icons are visible in the top navigation bar')
        print('   2. Buttons are clickable and change color on hover')
        print('   3. Navigation changes when clicking buttons')
        print('   4. No console errors in the browser DevTools')
        print("="*80 + "\n")
        
        input('Press Enter to close the browser and exit...')
        browser.close()

if __name__ == '__main__':
    test_icons_and_navigation()
