#!/usr/bin/env python3
"""
Quick test for fixed issues
"""
from playwright.sync_api import sync_playwright
import time

print("\n" + "="*80)
print("🧪 TESTING FIXES: Monitoring & Nodes Views")
print("="*80 + "\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=200)
    page = browser.new_page()
    
    js_errors = []
    
    def handle_error(error):
        js_errors.append(str(error))
        print(f'[JS ERROR] {error}')
    
    page.on('pageerror', handle_error)
    
    # Load and login
    print('1. Loading page...')
    page.goto('http://localhost:8765')
    time.sleep(2)
    
    print('2. Logging in...')
    page.fill('#loginUsername', 'fab')
    page.fill('#loginPassword', 'invaders')
    page.click('button[type="submit"]')
    time.sleep(3)
    
    print('3. Testing Monitoring view...')
    monitoring_btn = page.query_selector('[data-view="monitoring"]')
    if monitoring_btn:
        monitoring_btn.click()
        time.sleep(2)
        
        # Check for errors
        if 'monitoring' in [str(e).lower() for e in js_errors]:
            print('   ❌ MonitoringView has errors')
        else:
            print('   ✅ MonitoringView loads without errors')
        
        # Check if content rendered
        container = page.query_selector('#monitoringView')
        has_content = container and container.inner_text().strip() != ''
        print(f'   {"✅" if has_content else "❌"} MonitoringView has content')
    
    print('4. Testing Nodes view...')
    nodes_btn = page.query_selector('[data-view="nodes"]')
    if nodes_btn:
        nodes_btn.click()
        time.sleep(2)
        
        # Check for errors
        nodes_errors = [e for e in js_errors if 'nodes' in str(e).lower() or 'map' in str(e).lower()]
        if nodes_errors:
            print(f'   ❌ NodesView has errors: {len(nodes_errors)}')
            for err in nodes_errors[:2]:
                print(f'      • {err[:100]}')
        else:
            print('   ✅ NodesView loads without errors')
        
        # Check if content rendered
        container = page.query_selector('#nodesView')
        has_content = container and container.inner_text().strip() != ''
        print(f'   {"✅" if has_content else "❌"} NodesView has content')
    
    print('5. Testing Apps view...')
    apps_btn = page.query_selector('[data-view="apps"]')
    if apps_btn:
        apps_btn.click()
        time.sleep(2)
        
        container = page.query_selector('#appsView')
        has_content = container and container.inner_text().strip() != ''
        print(f'   {"✅" if has_content else "❌"} AppsView has content')
    
    print('6. Testing Catalog view...')
    catalog_btn = page.query_selector('[data-view="catalog"]')
    if catalog_btn:
        catalog_btn.click()
        time.sleep(2)
        
        # Count catalog items
        items = page.query_selector_all('.catalog-item, .app-card')
        print(f'   ✅ Catalog has {len(items)} items')
    
    print('\n' + "="*80)
    print(f'📊 TOTAL JAVASCRIPT ERRORS: {len(js_errors)}')
    print("="*80 + "\n")
    
    if js_errors:
        print('Errors found:')
        for i, err in enumerate(js_errors[:5], 1):
            print(f'  {i}. {err[:150]}')
    else:
        print('✅ No JavaScript errors!')
    
    input('\nPress Enter to close...')
    browser.close()
