"""
Debug test to understand login page behavior
"""
import pytest
from playwright.sync_api import Page, expect


def test_login_debug(page: Page):
    """Debug login page behavior"""
    base_url = "http://localhost:5173"
    
    # Capture console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
    
    # Capture network errors
    page.on("pageerror", lambda exc: print(f"  ✗ Page Error: {exc}"))
    
    print("\n🔍 Step 1: Navigate to login page")
    page.goto(f"{base_url}/login")
    page.screenshot(path="debug_step1_login_page.png")
    print(f"  ✓ URL: {page.url}")
    
    print("\n🔍 Step 2: Check if username input exists")
    username_selectors = [
        'input[name="username"]',
        'input[type="text"]',
        'input[placeholder*="username" i]'
    ]
    
    for selector in username_selectors:
        count = page.locator(selector).count()
        print(f"  Selector '{selector}': {count} elements")
        if count > 0:
            is_visible = page.locator(selector).first.is_visible()
            print(f"    First element visible: {is_visible}")
    
    print("\n🔍 Step 3: Check if password input exists")
    password_selectors = [
        'input[name="password"]',
        'input[type="password"]'
    ]
    
    for selector in password_selectors:
        count = page.locator(selector).count()
        print(f"  Selector '{selector}': {count} elements")
        if count > 0:
            is_visible = page.locator(selector).first.is_visible()
            print(f"    First element visible: {is_visible}")
    
    print("\n🔍 Step 4: Check if submit button exists")
    button_selectors = [
        'button[type="submit"]',
        'button:has-text("Sign in")',
        'button:has-text("Log in")'
    ]
    
    for selector in button_selectors:
        count = page.locator(selector).count()
        print(f"  Selector '{selector}': {count} elements")
        if count > 0:
            is_visible = page.locator(selector).first.is_visible()
            print(f"    First element visible: {is_visible}")
    
    print("\n🔍 Step 5: Try to fill and submit")
    try:
        page.locator('input[name="username"]').first.fill("testuser")
        print("  ✓ Filled username")
        page.screenshot(path="debug_step5_filled_username.png")
        
        page.locator('input[name="password"]').first.fill("testpassword")
        print("  ✓ Filled password")
        page.screenshot(path="debug_step5_filled_password.png")
        
        page.locator('button[type="submit"]').first.click()
        print("  ✓ Clicked submit")
        
        page.wait_for_timeout(3000)
        page.screenshot(path="debug_step5_after_submit.png")
        print(f"  URL after submit: {page.url}")
        
        print("\n📋 Console Messages:")
        for msg in console_messages[-10:]:  # Last 10 messages
            print(f"  {msg}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        page.screenshot(path="debug_error.png")
        print("\n📋 Console Messages on Error:")
        for msg in console_messages:
            print(f"  {msg}")
    
    print("\n✅ Debug test completed")
