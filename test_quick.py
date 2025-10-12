#!/usr/bin/env python3
"""
Quick test to verify icons, navigation, and error handling.
"""
from playwright.sync_api import sync_playwright
import time

print("\n" + "="*80)
print("🧪 QUICK TEST: Icons, Navigation & Error Handling")
print("="*80 + "\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Track console messages
    console_msgs = []
    def handle_console(msg):
        text = f'[{msg.type}] {msg.text}'
        console_msgs.append(text)
        if 'error' in msg.type.lower() or '❌' in msg.text:
            print(text)
    
    page.on('console', handle_console)
    
    print('📍 Step 1: Loading page...')
    page.goto('http://localhost:8765')
    time.sleep(2)
    
    # Check icons
    print('\n🔍 Step 2: Checking icons...')
    svg_count = len(page.query_selector_all('svg'))
    print(f'   SVG icons rendered: {svg_count}')
    
    # Check navigation buttons
    print('\n🔍 Step 3: Checking navigation...')
    nav_buttons = page.query_selector_all('.nav-rack-item[data-view]')
    print(f'   Navigation buttons found: {len(nav_buttons)}')
    
    # Test navigation to Apps view
    print('\n🖱️  Step 4: Navigating to Apps view...')
    apps_btn = page.query_selector('[data-view="apps"]')
    if apps_btn:
        apps_btn.click()
        time.sleep(2)
        
        # Check if error message is shown
        error_state = page.query_selector('.empty-state')
        if error_state:
            icon = error_state.query_selector('.empty-state-icon')
            title = error_state.query_selector('h2')
            if icon and title:
                print(f'   Error state shown: {icon.inner_text()} {title.inner_text()}')
        else:
            apps_count = len(page.query_selector_all('.app-card'))
            print(f'   Apps loaded: {apps_count} apps')
    
    # Test navigation to Catalog
    print('\n🖱️  Step 5: Navigating to Catalog view...')
    catalog_btn = page.query_selector('[data-view="catalog"]')
    if catalog_btn:
        catalog_btn.click()
        time.sleep(2)
        print('   ✅ Catalog view loaded')
    
    # Test navigation back to Dashboard
    print('\n🖱️  Step 6: Navigating back to Dashboard...')
    dashboard_btn = page.query_selector('[data-view="dashboard"]')
    if dashboard_btn:
        dashboard_btn.click()
        time.sleep(1)
        print('   ✅ Dashboard view loaded')
    
    # Check for errors
    error_count = sum(1 for msg in console_msgs if '❌' in msg or 'error' in msg.lower())
    
    print('\n' + "="*80)
    print('📊 SUMMARY')
    print("="*80)
    print(f'SVG Icons: {svg_count}')
    print(f'Navigation Buttons: {len(nav_buttons)}')
    print(f'Console Errors: {error_count}')
    print(f'Navigation: {"✅ Working" if len(nav_buttons) > 0 else "❌ Not working"}')
    print("="*80 + "\n")
    
    input('Press Enter to close...')
    browser.close()
