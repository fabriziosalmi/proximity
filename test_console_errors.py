#!/usr/bin/env python3
"""
Capture and analyze console errors
"""
from playwright.sync_api import sync_playwright
import time

print("\n" + "="*80)
print("🐛 CONSOLE ERROR ANALYSIS")
print("="*80 + "\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    console_messages = []
    errors = []
    warnings = []
    
    def handle_console(msg):
        text = msg.text
        msg_type = msg.type
        
        entry = {
            'type': msg_type,
            'text': text,
            'location': msg.location
        }
        
        console_messages.append(entry)
        
        if msg_type == 'error' or '❌' in text:
            errors.append(entry)
            print(f'[ERROR] {text}')
        elif msg_type == 'warning':
            warnings.append(entry)
    
    page.on('console', handle_console)
    
    print('Loading page and performing login...\n')
    page.goto('http://localhost:8765')
    time.sleep(2)
    
    # Login
    try:
        page.fill('#loginUsername', 'fab')
        page.fill('#loginPassword', 'invaders')
        page.click('button[type="submit"]')
        time.sleep(3)
    except:
        pass
    
    # Navigate through views
    print('Navigating through all views...\n')
    views = ['apps', 'catalog', 'settings', 'monitoring', 'nodes', 'dashboard']
    for view in views:
        try:
            btn = page.query_selector(f'[data-view="{view}"]')
            if btn:
                btn.click()
                time.sleep(1.5)
        except:
            pass
    
    print('\n' + "="*80)
    print('📊 ERROR SUMMARY')
    print("="*80)
    print(f'Total console messages: {len(console_messages)}')
    print(f'Errors: {len(errors)}')
    print(f'Warnings: {len(warnings)}')
    
    if errors:
        print(f'\n❌ ERRORS ({len(errors)}):')
        
        # Group errors by type
        error_groups = {}
        for error in errors:
            key = error['text'][:100]  # Group by first 100 chars
            if key not in error_groups:
                error_groups[key] = []
            error_groups[key].append(error)
        
        for i, (key, group) in enumerate(error_groups.items(), 1):
            print(f'\n[{i}] {key}')
            print(f'    Count: {len(group)}')
            if group[0]['location']:
                loc = group[0]['location']
                print(f'    Location: {loc.get("url", "unknown")}:{loc.get("lineNumber", "?")}')
    
    if warnings:
        print(f'\n⚠️  WARNINGS ({len(warnings)}):')
        warning_groups = {}
        for warning in warnings:
            key = warning['text'][:80]
            if key not in warning_groups:
                warning_groups[key] = []
            warning_groups[key].append(warning)
        
        for key, group in warning_groups.items():
            if len(group) > 2:  # Only show warnings that appear multiple times
                print(f'   • {key} (x{len(group)})')
    
    print('\n' + "="*80)
    input('\nPress Enter to close...')
    browser.close()
