#!/usr/bin/env python3
"""
Detailed error diagnostics - captures full error stack traces.
"""
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Inject error tracking before page loads
    page.add_init_script("""
        window.errorDetails = [];
        window.addEventListener('error', (event) => {
            window.errorDetails.push({
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error ? event.error.stack : null
            });
        });
    """)
    
    print('\n📍 Loading page...')
    page.goto('http://localhost:8765')
    page.wait_for_timeout(2000)
    
    # Get captured errors
    error_details = page.evaluate('window.errorDetails')
    
    print('\n' + '='*80)
    print('📊 DETAILED ERROR INFORMATION')
    print('='*80 + '\n')
    
    if error_details:
        for i, error in enumerate(error_details, 1):
            print(f'Error #{i}:')
            print(f'  Message: {error["message"]}')
            print(f'  File: {error["filename"]}')
            print(f'  Line: {error["lineno"]}, Column: {error["colno"]}')
            if error["error"]:
                print(f'  Stack:\n{error["error"]}')
            print()
    else:
        print('✅ No detailed errors captured')
    
    print('='*80)
    input('\nPress Enter to close...')
    browser.close()
