"""
Debug test - Step by step login
"""

from playwright.sync_api import Page


def test_debug_login_flow(page: Page, unique_user: dict, base_url: str):
    """Debug login step by step to see where it fails."""
    print("\n🔍 DEBUG LOGIN TEST")
    print(f"User: {unique_user['username']}")
    print(f"Password: {unique_user['password']}")

    # Step 1: Navigate to login
    print("\n1️⃣ Navigating to /login...")
    page.goto(f"{base_url}/login")
    page.wait_for_load_state("networkidle")
    print(f"   URL: {page.url}")

    # Step 2: Take screenshot
    page.screenshot(path="/tmp/login_page.png")
    print("   Screenshot saved: /tmp/login_page.png")

    # Step 3: Check if form exists
    print("\n2️⃣ Checking form elements...")
    username_input = page.locator('input[name="username"], input[type="text"]').first
    password_input = page.locator('input[name="password"], input[type="password"]').first
    submit_button = page.locator(
        'button[type="submit"], button:has-text("Login"), button:has-text("Sign in")'
    ).first

    print(f"   Username input visible: {username_input.is_visible()}")
    print(f"   Password input visible: {password_input.is_visible()}")
    print(f"   Submit button visible: {submit_button.is_visible()}")

    # Step 4: Fill form
    print("\n3️⃣ Filling form...")
    username_input.fill(unique_user["username"])
    password_input.fill(unique_user["password"])
    print("   Form filled")

    # Step 5: Click submit
    print("\n4️⃣ Clicking submit...")
    submit_button.click()
    print("   Clicked!")

    # Step 6: Wait a bit and check what happens
    print("\n5️⃣ Waiting for response...")
    page.wait_for_timeout(3000)

    current_url = page.url
    print(f"   Current URL after login: {current_url}")

    # Check for error messages
    error_messages = page.locator('.error, .alert-error, [role="alert"]').all()
    if error_messages:
        print(f"   ⚠️ Found {len(error_messages)} error messages:")
        for msg in error_messages:
            if msg.is_visible():
                print(f"      - {msg.text_content()}")

    # Check for success indicators
    apps_link = page.locator('a[href="/apps"]')
    store_link = page.locator('a[href="/store"]')

    print("\n6️⃣ Checking navigation elements...")
    print(f"   Apps link exists: {apps_link.count() > 0}")
    print(f"   Store link exists: {store_link.count() > 0}")

    if apps_link.count() > 0:
        print(f"   Apps link visible: {apps_link.first.is_visible()}")
    if store_link.count() > 0:
        print(f"   Store link visible: {store_link.first.is_visible()}")

    # Final screenshot
    page.screenshot(path="/tmp/after_login.png")
    print("\n   Screenshot saved: /tmp/after_login.png")

    print("\n✅ Debug test completed - check screenshots and output above")
