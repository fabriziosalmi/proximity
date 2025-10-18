"""
Debug test for deployment flow - captures console logs and API calls
"""
import pytest
from playwright.sync_api import Page, expect


def test_deploy_debug(page: Page, unique_user, proxmox_host):
    """
    Debug test to understand deployment flow and API errors
    """
    username = unique_user['username']
    password = unique_user['password']
    
    # Capture console messages
    console_messages = []
    def handle_console(msg):
        console_messages.append(f"[{msg.type}] {msg.text}")
    
    page.on("console", handle_console)
    
    # Capture network requests
    api_calls = []
    def handle_response(response):
        if '/api/' in response.url:
            status = response.status
            method = response.request.method
            url = response.url
            api_calls.append({
                'method': method,
                'url': url,
                'status': status
            })
            
            # Try to get response body for failed requests
            if status >= 400:
                try:
                    body = response.text()
                    api_calls[-1]['error_body'] = body
                except:
                    pass
    
    page.on("response", handle_response)
    
    # Navigate to login
    print("\n🔍 STEP 1: Login")
    page.goto("http://localhost:5173/login")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.locator('button:has-text("Sign In")').click()
    
    # Wait for login to complete
    expect(page).to_have_url("http://localhost:5173/", timeout=10000)
    print("✅ Login successful")
    
    # Navigate to store
    print("\n🔍 STEP 2: Navigate to Store")
    page.goto("http://localhost:5173/store")
    expect(page).to_have_url("http://localhost:5173/store")
    
    # Wait for catalog to load
    page.wait_for_selector('.rack-card', timeout=10000)
    print("✅ Store loaded")
    
    # Click deploy on first app
    print("\n🔍 STEP 3: Open Deploy Modal")
    deploy_button = page.locator('button:has-text("Deploy")').first
    deploy_button.click()
    
    # Wait for modal (using role="dialog")
    page.wait_for_selector('[role="dialog"]', state='visible', timeout=5000)
    print("✅ Modal opened")
    
    # Check hostname field
    hostname_input = page.locator('input[name="hostname"]').first
    hostname = hostname_input.input_value()
    print(f"📝 Hostname: {hostname}")
    
    # Check host selection
    host_select = page.locator('select#host').first
    if host_select.is_visible():
        selected_value = host_select.input_value()
        print(f"📝 Selected host ID: {selected_value}")
    else:
        print("⚠️  Host select not visible")
    
    # Check if deploy button is enabled
    modal_deploy_button = page.locator('[role="dialog"] button:has-text("Deploy")').first
    is_disabled = modal_deploy_button.get_attribute('disabled')
    print(f"📝 Deploy button disabled: {is_disabled}")
    
    # Check localStorage for auth token
    token = page.evaluate("() => localStorage.getItem('access_token')")
    print(f"📝 Auth token present: {'Yes' if token else 'No'}")
    if token:
        print(f"📝 Token (first 20 chars): {token[:20]}...")
    
    print("\n🔍 STEP 4: Click Deploy Button")
    modal_deploy_button.click()
    
    # Wait a bit for API call
    page.wait_for_timeout(3000)
    
    # Check current URL
    current_url = page.url
    print(f"📝 Current URL: {current_url}")
    
    # Print all console messages
    print("\n📋 Console Messages:")
    for msg in console_messages:
        print(f"  {msg}")
    
    # Print all API calls
    print("\n📋 API Calls:")
    for call in api_calls:
        print(f"  {call['method']} {call['url']} → {call['status']}")
        if 'error_body' in call:
            print(f"    Error: {call['error_body']}")
    
    # Check if we're on /apps page
    if current_url.endswith('/apps') or current_url.endswith('/apps/'):
        print("\n✅ Successfully navigated to /apps")
    else:
        print(f"\n❌ Still on {current_url}, expected /apps")
