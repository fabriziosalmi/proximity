#!/usr/bin/env python3
"""
Debug authentication flow with credentials: fab / invaders
"""
from playwright.sync_api import sync_playwright
import time

print("\n" + "="*80)
print("🔐 DEBUGGING AUTHENTICATION FLOW")
print("   Username: fab")
print("   Password: invaders")
print("="*80 + "\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page()
    
    # Track all console messages and errors
    console_msgs = []
    errors = []
    
    def handle_console(msg):
        text = f'[{msg.type}] {msg.text}'
        console_msgs.append(text)
        print(text)
    
    def handle_error(error):
        errors.append(str(error))
        print(f'[PAGE ERROR] {error}')
    
    page.on('console', handle_console)
    page.on('pageerror', handle_error)
    
    print('📍 Step 1: Loading page...\n')
    page.goto('http://localhost:8765')
    time.sleep(2)
    
    print('\n📍 Step 2: Checking for auth modal...\n')
    auth_modal = page.query_selector('#authModal')
    if auth_modal:
        is_visible = auth_modal.is_visible()
        print(f'   ✅ Auth modal found, visible: {is_visible}')
        
        if not is_visible:
            print('   ⚠️  Modal exists but not visible, checking display style...')
            display = page.evaluate('document.getElementById("authModal").style.display')
            print(f'      Display style: {display}')
    else:
        print('   ❌ Auth modal NOT found in DOM')
        print('   🔍 Searching for modal-related elements...')
        
        # Check if there are any modals
        all_modals = page.query_selector_all('[class*="modal"]')
        print(f'   Found {len(all_modals)} elements with "modal" in class')
        
        for i, modal in enumerate(all_modals):
            classes = modal.get_attribute('class')
            id_attr = modal.get_attribute('id')
            print(f'      [{i+1}] id={id_attr}, class={classes}')
    
    # Wait for modal to appear
    print('\n📍 Step 3: Waiting for modal to appear (5s)...\n')
    try:
        page.wait_for_selector('#authModal', state='visible', timeout=5000)
        print('   ✅ Modal appeared')
    except Exception as e:
        print(f'   ❌ Modal did not appear: {e}')
        
        # Try to manually show the modal
        print('\n   🔧 Attempting to manually show modal...')
        try:
            page.evaluate('window.showAuthModal && window.showAuthModal()')
            time.sleep(1)
            
            modal = page.query_selector('#authModal')
            if modal and modal.is_visible():
                print('   ✅ Modal shown successfully')
            else:
                print('   ❌ Failed to show modal')
        except Exception as e2:
            print(f'   ❌ Error showing modal: {e2}')
    
    # Check if modal is now visible
    auth_modal = page.query_selector('#authModal')
    if not auth_modal or not auth_modal.is_visible():
        print('\n❌ Cannot proceed without visible auth modal')
        print('\n📊 Checking page state...')
        
        # Check if showAuthModal function exists
        has_func = page.evaluate('typeof window.showAuthModal')
        print(f'   window.showAuthModal exists: {has_func}')
        
        # Check if Auth module is loaded
        has_auth = page.evaluate('typeof window.Auth')
        print(f'   window.Auth exists: {has_auth}')
        
        input('\nPress Enter to close...')
        browser.close()
        exit(1)
    
    print('\n📍 Step 4: Checking modal tabs...\n')
    login_tab = page.query_selector('#loginTab')
    register_tab = page.query_selector('#registerTab')
    
    if login_tab:
        print(f'   ✅ Login tab found')
        is_active = 'active' in (login_tab.get_attribute('class') or '')
        print(f'      Active: {is_active}')
        
        if not is_active:
            print('\n   🔄 Switching to login tab...')
            login_tab.click()
            time.sleep(0.5)
    else:
        print('   ❌ Login tab not found')
    
    if register_tab:
        print(f'   ✅ Register tab found')
    else:
        print('   ❌ Register tab not found')
    
    print('\n📍 Step 5: Filling login form...\n')
    
    # Find username field
    username_field = page.query_selector('#loginUsername')
    if username_field:
        print('   ✅ Username field found')
        username_field.fill('fab')
        print('      Filled: fab')
    else:
        print('   ❌ Username field not found')
        # Try alternative selectors
        username_field = page.query_selector('input[name="username"]')
        if username_field:
            print('      Found via name="username"')
            username_field.fill('fab')
    
    # Find password field
    password_field = page.query_selector('#loginPassword')
    if password_field:
        print('   ✅ Password field found')
        password_field.fill('invaders')
        print('      Filled: invaders')
    else:
        print('   ❌ Password field not found')
        # Try alternative selectors
        password_field = page.query_selector('input[type="password"]')
        if password_field:
            print('      Found via type="password"')
            password_field.fill('invaders')
    
    time.sleep(0.5)
    
    print('\n📍 Step 6: Submitting login form...\n')
    
    # Find submit button
    submit_btn = page.query_selector('button[type="submit"]')
    if not submit_btn:
        submit_btn = page.query_selector('.auth-submit')
    if not submit_btn:
        submit_btn = page.query_selector('button:has-text("Login")')
    
    if submit_btn:
        print('   ✅ Submit button found')
        print('      Clicking submit...')
        submit_btn.click()
        
        print('\n   ⏳ Waiting for response (5s)...')
        time.sleep(5)
        
        # Check if modal closed (successful login)
        modal_after = page.query_selector('#authModal')
        if modal_after and modal_after.is_visible():
            print('   ⚠️  Modal still visible after submit')
            
            # Check for error messages
            error_msg = page.query_selector('.auth-error')
            if error_msg:
                error_text = error_msg.inner_text()
                print(f'   ❌ Error message: {error_text}')
        else:
            print('   ✅ Modal closed - login successful!')
            
            # Check if token was saved
            token = page.evaluate('localStorage.getItem("proximity_token")')
            if token:
                print(f'   ✅ Token saved: {token[:20]}...')
            else:
                print('   ❌ No token found in localStorage')
            
            # Check user state
            is_auth = page.evaluate('window.Auth && window.Auth.isAuthenticated && window.Auth.isAuthenticated()')
            print(f'   Auth state: {is_auth}')
    else:
        print('   ❌ Submit button not found')
    
    print('\n' + "="*80)
    print('📊 SUMMARY')
    print("="*80)
    print(f'Console messages: {len(console_msgs)}')
    print(f'Errors: {len(errors)}')
    
    if errors:
        print('\n❌ ERRORS DETECTED:')
        for error in errors[:5]:  # Show first 5 errors
            print(f'   {error}')
    
    print('\n' + "="*80)
    print('Browser left open for inspection.')
    print('Check the Network tab and Console in DevTools.')
    print("="*80 + "\n")
    
    input('Press Enter to close...')
    browser.close()
