"""Debug test to check localStorage token storage."""

import pytest
from playwright.sync_api import Page


@pytest.mark.fixture_test
def test_check_token_storage_with_manual_login(page: Page, base_url: str):
    """
    Check localStorage at each step of login to see where token is lost.

    This bypasses authenticated_page fixture to debug the login flow.
    """
    from pages.login_page import LoginPage
    from pages.dashboard_page import DashboardPage
    from utils.test_data import generate_test_user
    from playwright.sync_api import expect

    print("\n🔍 Manual login test with localStorage debugging")

    # DEBUG: Enable console logging
    page.on("console", lambda msg: print(f"  [BROWSER] {msg.type}: {msg.text}"))

    # Step 1: Navigate and clear storage
    print("\n1️⃣ Navigating and clearing storage")
    page.goto(base_url)
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    page.reload()

    storage = page.evaluate("Object.keys(localStorage)")
    print(f"  → After clear: {storage}")

    # Step 2: Register
    print("\n2️⃣ Registering user")
    test_user = generate_test_user()
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)

    login_page.wait_for_auth_modal()
    login_page.switch_to_register_mode()
    login_page.fill_username(test_user["username"], mode="register")
    login_page.fill_password(test_user["password"], mode="register")
    if login_page.is_visible(login_page.REGISTER_EMAIL_INPUT):
        login_page.fill_email(test_user.get("email", f"{test_user['username']}@test.com"))

    login_page.click_register_button()
    page.wait_for_timeout(1000)

    storage = page.evaluate("Object.keys(localStorage)")
    token = page.evaluate("Auth.getToken()")
    print(f"  → After register: {storage}")
    print(f"  → Token after register: {token[:50] if token else 'NOT FOUND'}")

    # Step 3: Login
    print("\n3️⃣ Logging in")
    login_page.switch_to_login_mode()
    login_page.click_login_button()

    # Wait a bit for login to complete
    page.wait_for_timeout(2000)

    storage = page.evaluate("Object.keys(localStorage)")
    token = page.evaluate("Auth.getToken()")
    is_auth = page.evaluate("Auth.isAuthenticated()")
    print(f"  → After login click: {storage}")
    print(f"  → Token after login: {token[:50] if token else 'NOT FOUND'}")
    print(f"  → Auth.isAuthenticated(): {is_auth}")

    # Step 4: Wait for dashboard
    print("\n4️⃣ Waiting for dashboard")
    expect(dashboard_page.dashboard_container).to_be_visible(timeout=15000)

    storage = page.evaluate("Object.keys(localStorage)")
    token = page.evaluate("Auth.getToken()")
    is_auth = page.evaluate("Auth.isAuthenticated()")
    print(f"  → After dashboard visible: {storage}")
    print(f"  → Token after dashboard: {token[:50] if token else 'NOT FOUND'}")
    print(f"  → Auth.isAuthenticated(): {is_auth}")

    print("\n✅ Manual login test complete")
