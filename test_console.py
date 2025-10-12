#!/usr/bin/env python3
"""
Check browser console for exact error messages.
"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    errors = []
    console_messages = []
    
    def handle_console(msg):
        text = msg.text
        console_messages.append(f'[{msg.type}] {text}')
        print(f'[{msg.type}] {text}')
    
    def handle_error(error):
        errors.append(str(error))
        print(f'[ERROR] {error}')
    
    page.on('console', handle_console)
    page.on('pageerror', handle_error)
    
    print('\n📍 Loading page...\n')
    page.goto('http://localhost:8765')
    
    print('\n⏳ Waiting for page to settle...\n')
    time.sleep(3)
    
    print('\n' + '='*80)
    print('📊 CONSOLE OUTPUT')
    print('='*80)
    for msg in console_messages:
        print(msg)
    
    print('\n' + '='*80)
    print('❌ ERRORS')
    print('='*80)
    if errors:
        for error in errors:
            print(error)
    else:
        print('No errors detected')
    
    print('\n' + '='*80)
    input('\nPress Enter to close...')
    browser.close()
