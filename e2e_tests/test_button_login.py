"""
Test login with correct button selector
"""



def test_button_selector(page):
    """Test that we can find the login button"""
    base_url = "https://localhost:5173"

    # Capture console and errors
    messages = []
    page.on("console", lambda msg: messages.append(f"{msg.type}: {msg.text}"))
    page.on("pageerror", lambda exc: messages.append(f"ERROR: {exc}"))

    print("\n🔍 Navigate and login")
    page.goto(f"{base_url}/login")

    # Fill credentials
    page.fill('input[name="username"]', "testuser_real")
    page.fill('input[name="password"]', "TestPass123!")

    # Click the Sign In button (type="button" now)
    page.click('button:has-text("Sign In")')

    # Wait and check
    page.wait_for_timeout(4000)

    print(f"  URL after click: {page.url}")
    print("\n📋 Recent messages:")
    for msg in messages[-15:]:
        print(f"  {msg}")

    print("\n✅ Test completed")
