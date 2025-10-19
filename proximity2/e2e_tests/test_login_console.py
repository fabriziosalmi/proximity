"""
Test login con cattura console logs
"""
import pytest


def test_login_with_console_logs(page, unique_user):
    """Test login e cattura tutti i console.log del browser."""
    print(f"\n🧪 Testing login with console capture")
    print(f"   Username: {unique_user['username']}")
    print(f"   Password: {unique_user['password']}")
    
    # Capture console messages
    console_messages = []
    
    def handle_console(msg):
        console_messages.append({
            'type': msg.type,
            'text': msg.text
        })
        print(f"   [BROWSER {msg.type.upper()}] {msg.text}")
    
    page.on("console", handle_console)
    
    # Capture network requests
    api_requests = []
    
    def handle_request(request):
        if '/api/' in request.url:
            api_requests.append({
                'method': request.method,
                'url': request.url,
                'headers': dict(request.headers)
            })
            print(f"   [API REQUEST] {request.method} {request.url}")
    
    def handle_response(response):
        if '/api/' in response.url:
            print(f"   [API RESPONSE] {response.status} {response.url}")
            try:
                print(f"   [API BODY] {response.json()}")
            except:
                pass
    
    page.on("request", handle_request)
    page.on("response", handle_response)
    
    # Navigate to login
    print("\n📍 Navigating to login page...")
    page.goto("http://localhost:5173/login")
    page.wait_for_load_state("domcontentloaded")
    
    # Fill form
    print("📝 Filling login form...")
    page.fill('input[name="username"]', unique_user['username'])
    page.fill('input[type="password"]', unique_user['password'])
    
    # Wait for Svelte hydration
    print("⏳ Waiting for Svelte hydration...")
    page.wait_for_timeout(2000)
    
    # Click login
    print("🖱️  Clicking login button...")
    login_button = page.locator('button:has-text("Sign In")').first
    login_button.wait_for(state='attached', timeout=5000)
    login_button.click()
    
    # Wait a bit for API call
    print("⏳ Waiting for API call...")
    page.wait_for_timeout(8000)
    
    # Check for error messages in the page
    print("\n🔍 Checking for error messages...")
    error_selectors = [
        '.error',
        '.alert-error',
        '[role="alert"]',
        'text=/error/i',
        'text=/fail/i',
        'text=/invalid/i'
    ]
    
    for selector in error_selectors:
        try:
            error_elem = page.locator(selector).first
            if error_elem.is_visible(timeout=1000):
                error_text = error_elem.text_content()
                print(f"   ⚠️  Found error: {error_text}")
        except:
            pass
    
    # Check URL
    current_url = page.url
    print(f"\n🌐 Current URL: {current_url}")
    
    # Print all console messages
    print(f"\n📜 Total console messages: {len(console_messages)}")
    
    # Check if redirected
    if current_url == "http://localhost:5173/":
        print("✅ Successfully redirected to home!")
    else:
        print(f"❌ Still on login page or elsewhere: {current_url}")
        
        # Take screenshot for debugging
        page.screenshot(path="/tmp/login_failed.png")
        print("📸 Screenshot saved to /tmp/login_failed.png")
