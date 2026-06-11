"""
Test login using the text-based selector to verify the button works
"""

from playwright.sync_api import Page, expect


def test_login_with_text_selector(page: Page, unique_user):
    """
    Test login using button:has-text selector
    """
    username = unique_user["username"]
    password = unique_user["password"]

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

    # Define and attach handlers
    console_messages = []
    def handle_console(msg):
        console_messages.append((msg.type, msg.text))
        print(f"  [{msg.type}] {msg.text}")
        if msg.type == "error":
            print(f"    Location: {msg.location}")
            try:
                for arg in msg.args:
                    print(f"    Arg: {arg.json_value()}")
            except:
                pass

    api_responses = []
    def handle_response(response):
        if "/api/" in response.url:
            api_responses.append((response.request.method, response.url, response.status))
            print(f"  API {response.request.method} {response.url}")
            print(f"    Status: {response.status}")
            if response.status >= 400:
                try:
                    print(f"    Body: {response.text()}")
                except:
                    pass

    page.on("console", handle_console)
    page.on("response", handle_response)

    try:
        button = page.locator('button:has-text("Sign In")').first
        expect(button).to_be_visible(timeout=5000)
        button.click()

        # Wait for navigation or timeout
        page.wait_for_timeout(5000)

        print(f"\n✓ Current URL: {page.url}")
        print("✓ Expected URL: https://localhost:5173/")

        # Explicit assertions for success/failure
        expect(page).to_have_url("https://localhost:5173/", timeout=10000)

        # Verify no critical errors were logged
        error_logs = [msg for msg in console_messages if msg[0] == "error"]
        assert len(error_logs) == 0, f"Unexpected console errors: {error_logs}"

        # Verify no failed API calls (4xx/5xx)
        failed_api_calls = [r for r in api_responses if r[2] >= 400]
        assert len(failed_api_calls) == 0, f"Failed API calls: {failed_api_calls}"

        print("✅ Login successful - redirected to homepage!")

    finally:
        # Clean up handlers to avoid accumulation
        page.remove_listener("console", handle_console)
        page.remove_listener("response", handle_response)
