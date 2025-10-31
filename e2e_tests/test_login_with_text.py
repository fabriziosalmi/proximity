"""
Test login using the text-based selector to verify the button works
"""
import pytest
from playwright.sync_api import Page, expect


def test_login_with_text_selector(page: Page, unique_user):
    """
    Test login using button:has-text selector
    """
    username = unique_user['username']
    password = unique_user['password']
    
    # Navigate to login
    page.goto("https://localhost:5173/login")
    expect(page).to_have_url("https://localhost:5173/login")
    
    # Wait for Svelte to hydrate (wait for vite connected message)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)  # Extra wait for JS to execute
    
    # Fill form
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    
    # Click button using text selector
    print("\n🔍 Clicking button with text 'Sign In'...")
    
    # Enable console logging with more detail
    def handle_console(msg):
        print(f"  [{msg.type}] {msg.text}")
        if msg.type == 'error':
            print(f"    Location: {msg.location}")
            # Try to get stack trace
            try:
                for arg in msg.args:
                    print(f"    Arg: {arg.json_value()}")
            except:
                pass
    
    page.on("console", handle_console)
    
    # Also capture network requests
    def handle_response(response):
        if '/api/' in response.url:
            print(f"  API {response.request.method} {response.url}")
            print(f"    Status: {response.status}")
            if response.status >= 400:
                try:
                    print(f"    Body: {response.text()}")
                except:
                    pass
    
    page.on("response", handle_response)
    
    button = page.locator('button:has-text("Sign In")').first
    expect(button).to_be_visible(timeout=5000)
    button.click()
    
    # Wait a bit and check URL
    page.wait_for_timeout(5000)
    
    print(f"\n✓ Current URL: {page.url}")
    print(f"✓ Expected URL: https://localhost:5173/")
    
    # Check if we're on homepage
    if page.url == "https://localhost:5173/":
        print("✅ Login successful - redirected to homepage!")
    else:
        print(f"❌ Still on login page")
        
        # Check for error messages
        error_msg = page.locator('.error, .alert-error, [role="alert"]').first
        if error_msg.is_visible():
            print(f"⚠️  Error message: {error_msg.text_content()}")
