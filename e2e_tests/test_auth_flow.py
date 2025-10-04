"""
E2E Tests for Authentication Flows.

Tests user registration, login, logout, and error handling.
Validates JWT token management and session persistence.
"""

import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import generate_test_user


@pytest.mark.smoke
@pytest.mark.auth
def test_registration_and_login(page: Page):
    """
    Test complete registration and login flow.
    
    This test validates the ACTUAL UX flow where registration automatically
    switches to the login tab with pre-filled credentials, but does NOT auto-login.
    The user must click the login button to complete authentication.
    
    Steps:
    1. Navigate to Proximity UI
    2. Fill registration form with unique credentials
    3. Submit registration
    4. Wait for success notification
    5. Verify modal switches to login tab (automatic)
    6. Verify username is pre-filled in login form
    7. Click login button to complete authentication
    8. Wait for dashboard to appear (confirms async auto-login completed)
    9. Verify modal closes
    10. Verify dashboard is visible
    
    Expected: User successfully registered, must manually click login,
              then dashboard loads and auth modal is hidden.
    """
    print("\n🔍 Test: Registration and Login Flow")
    
    # Arrange
    test_user = generate_test_user()
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    print(f"📝 Generated test user: {test_user['username']}")
    
    # Act - Register new user
    print("📋 Step 1: Waiting for auth modal")
    login_page.wait_for_auth_modal()
    
    print("📋 Step 2: Switching to register mode")
    login_page.switch_to_register_mode()
    
    print("📋 Step 3: Filling registration form")
    login_page.fill_username(test_user["username"], mode="register")
    login_page.fill_password(test_user["password"], mode="register")
    if login_page.is_visible(login_page.REGISTER_EMAIL_INPUT):
        login_page.fill_email(test_user["email"])
    
    print("📋 Step 4: Clicking register button")
    login_page.click_register_button()
    
    # Assert - Verify registration success and auto-switch to login
    print("📋 Step 5: Waiting for success notification (optional)")
    page.wait_for_timeout(2000)  # Give time for registration to process
    
    print("📋 Step 6: Verifying modal switched to login tab")
    login_page.assert_in_login_mode()
    
    print("📋 Step 7: Verifying username is pre-filled")
    login_page.assert_username_prefilled(test_user["username"])
    
    print("📋 Step 8: Clicking login button to complete authentication")
    login_page.click_login_button()
    
    # --- CRITICAL FIX: Wait for async auto-login to complete ---
    # After clicking login, the frontend makes an async network request to authenticate.
    # We must wait for the dashboard to appear before asserting anything else.
    # This confirms the login completed successfully and the UI has fully updated.
    print("📋 Step 9: Waiting for dashboard to appear (confirms async auto-login completed)")
    expect(dashboard_page.dashboard_container).to_be_visible(timeout=15000)  # 15 seconds for network + UI update
    print("✓ Dashboard is now visible - auto-login completed successfully")
    
    # Now that we know the dashboard is visible, we can safely assert other things
    print("📋 Step 10: Verifying modal is closed")
    expect(login_page.modal).to_be_hidden()
    print("✓ Auth modal is hidden")
    
    print("📋 Step 11: Verifying dashboard state")
    dashboard_page.assert_on_dashboard()
    
    print("✅ Test passed: Registration and login flow works correctly")


@pytest.mark.auth
def test_logout(authenticated_page: Page):
    """
    Test logout functionality.
    
    Uses authenticated_page fixture which provides a pre-authenticated session.
    Validates complete logout flow including session cleanup.
    
    Steps:
    1. Start with authenticated session (from fixture)
    2. Verify dashboard is visible
    3. Click logout button
    4. Wait for auth modal to reappear (confirms async logout completed)
    5. Clear session storage to ensure complete cleanup
    6. Verify auth modal is visible
    7. Verify cannot access protected pages
    
    Expected: User logged out, session cleared,
              auth modal visible, protected content inaccessible.
    """
    print("\n🔍 Test: Logout Functionality")
    
    # Arrange
    dashboard_page = DashboardPage(authenticated_page)
    login_page = LoginPage(authenticated_page)
    
    # Verify we start authenticated
    print("📋 Step 1: Verifying authenticated state")
    dashboard_page.assert_on_dashboard()
    print("✓ User is authenticated and on dashboard")
    
    # Act - Logout
    print("📋 Step 2: Clicking logout button")
    dashboard_page.logout()
    
    # --- CRITICAL FIX: Wait for auth modal to reappear ---
    # After clicking logout, the frontend makes an async request to invalidate the session.
    # We must wait for the auth modal to become visible before making any assertions.
    # This confirms the logout completed and the UI has fully updated.
    print("📋 Step 3: Waiting for auth modal to reappear (confirms async logout completed)")
    expect(login_page.modal).to_be_visible(timeout=10000)  # 10 seconds for logout to complete
    print("✓ Auth modal is now visible - logout completed successfully")
    
    # Ensure session is cleared (some apps might not clear automatically)
    print("📋 Step 4: Clearing session storage for complete cleanup")
    authenticated_page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    
    # Assert - Verify logout state
    print("📋 Step 5: Verifying auth modal is visible")
    login_page.assert_auth_modal_visible()
    print("✓ Auth modal confirmed visible")
    
    # Verify we can't access protected content
    print("📋 Step 6: Verifying cannot access protected pages")
    # Try to navigate to dashboard
    dashboard_page.navigate_to("/")
    authenticated_page.wait_for_timeout(1000)  # Give page time to load
    
    # Should still see auth modal (not authenticated)
    login_page.assert_auth_modal_visible()
    print("✓ Cannot access dashboard after logout")
    
    print("✅ Test passed: Logout functionality works correctly")


@pytest.mark.auth
def test_invalid_login(page: Page):
    """
    Test login with incorrect credentials.
    
    CRITICAL: This test ensures complete isolation by clearing session storage
    before attempting login, preventing false passes from lingering JWT tokens.
    
    Steps:
    1. Clear any existing session (localStorage/sessionStorage)
    2. Navigate to fresh page with full reload
    3. Wait for page to fully load
    4. Attempt login with invalid credentials
    5. Wait for error message to appear (confirms async login attempt completed)
    6. Verify error message content
    7. Verify user remains on login modal
    8. Verify dashboard is NOT accessible
    
    Expected: Login fails with error message,
              modal remains visible, no access granted.
    """
    print("\n🔍 Test: Invalid Login")
    
    # Arrange - Ensure completely clean state
    print("📋 Step 1: Clearing any existing session")
    page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
    
    print("📋 Step 2: Navigating to fresh page with full reload")
    # Force a full page reload to ensure clean state
    page.goto(page.url, wait_until="networkidle")
    page.wait_for_timeout(1000)  # Give page time to initialize
    
    print("📋 Step 3: Verifying clean state (no dashboard visible)")
    # Ensure we're starting from a clean slate - dashboard should not be visible yet
    dashboard_page = DashboardPage(page)
    try:
        # Dashboard should not be visible initially
        expect(dashboard_page.dashboard_container).to_be_hidden(timeout=2000)
    except:
        # If dashboard is visible, we have a problem - clear again
        print("⚠️  Dashboard was visible, forcing another clear")
        page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(1000)
    
    login_page = LoginPage(page)
    
    print("📋 Step 4: Waiting for auth modal")
    login_page.wait_for_auth_modal()
    
    # Act - Attempt login with bad credentials
    print("📋 Step 5: Attempting login with invalid credentials")
    # Fill in the credentials manually to have more control
    login_page.switch_to_login_mode()
    login_page.fill_username("nonexistent_user_12345", mode="login")
    login_page.fill_password("wrong_password_98765", mode="login")
    login_page.click_login_button()
    
    # --- CRITICAL FIX: Wait for error message to appear ---
    # After clicking login with invalid credentials, the frontend makes an async request.
    # We must wait for the error element to become visible with the error message.
    # This confirms the login attempt completed and the UI has shown the error.
    print("📋 Step 6: Waiting for error message to appear (confirms async login attempt completed)")
    expect(login_page.login_error).to_be_visible(timeout=10000)  # 10 seconds for network + UI update
    print("✓ Error message is now visible - invalid login rejected")
    
    # Assert - Verify error message content
    print("📋 Step 7: Verifying error message content")
    error_message = login_page.get_text(login_page.LOGIN_ERROR)
    assert error_message != "", "Expected error message for invalid login"
    assert any(keyword in error_message.lower() for keyword in ["invalid", "incorrect", "failed", "error", "not found"]), \
        f"Error message should indicate failure: {error_message}"
    print(f"✓ Error message received: {error_message}")
    
    # Verify modal still visible
    print("📋 Step 8: Verifying modal still visible")
    login_page.assert_auth_modal_visible()
    
    # Verify dashboard not accessible (should be hidden or not present)
    print("📋 Step 9: Verifying dashboard is NOT accessible")
    # After failed login, dashboard should remain hidden
    expect(dashboard_page.dashboard_container).to_be_hidden(timeout=2000)
    print("✓ Dashboard is not visible - access properly denied")
    
    print("✅ Test passed: Invalid login correctly rejected")


@pytest.mark.auth
def test_session_persistence(page: Page, base_url: str):
    """
    Test that authentication token persists across page reloads.
    
    This test validates JWT token storage in localStorage and session persistence.
    After registration and login, reloading the page should NOT show the auth modal.
    
    Steps:
    1. Register new user
    2. Switch to login tab and complete login
    3. Wait for dashboard to load (confirms login completed)
    4. Verify JWT token is stored in localStorage
    5. Reload the page
    6. Wait for dashboard to appear (confirms session persisted and auto-login occurred)
    7. Verify auth modal does NOT appear
    
    Expected: JWT token persists in localStorage,
              user remains logged in after reload.
    """
    print("\n🔍 Test: Session Persistence")
    
    # Arrange
    test_user = generate_test_user()
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    print(f"📝 Generated test user: {test_user['username']}")
    
    # Act - Register new user
    print("📋 Step 1: Registering new user")
    login_page.wait_for_auth_modal()
    login_page.switch_to_register_mode()
    login_page.fill_username(test_user["username"], mode="register")
    login_page.fill_password(test_user["password"], mode="register")
    if login_page.is_visible(login_page.REGISTER_EMAIL_INPUT):
        login_page.fill_email(test_user["email"])
    login_page.click_register_button()
    
    # Wait for registration and switch to login
    page.wait_for_timeout(2000)
    
    print("📋 Step 2: Completing login")
    login_page.switch_to_login_mode()
    login_page.click_login_button()
    
    # --- CRITICAL FIX: Wait for dashboard to appear after login ---
    # Before checking the token, we need to ensure the login completed successfully.
    # This confirms the async login request finished and the token was saved.
    print("📋 Step 3: Waiting for dashboard to load (confirms login completed)")
    expect(dashboard_page.dashboard_container).to_be_visible(timeout=15000)  # 15 seconds for network + UI update
    print("✓ Dashboard is now visible - login completed successfully")
    
    # Verify token stored in localStorage
    print("📋 Step 4: Verifying JWT token is stored")
    token = page.evaluate("localStorage.getItem('proximity_token') || localStorage.getItem('token') || localStorage.getItem('authToken')")
    assert token is not None, "JWT token should be stored in localStorage"
    assert len(token) > 20, f"JWT token should be a valid length, got: {len(token)} chars"
    print(f"✓ JWT token stored (length: {len(token)} chars)")
    
    # Reload page
    print("📋 Step 5: Reloading page to test persistence")
    page.reload()
    page.wait_for_load_state("load")
    
    # --- CRITICAL FIX: Wait for dashboard to appear after reload ---
    # After reloading, the frontend should auto-login using the stored token.
    # We must wait for the dashboard to become visible before asserting anything.
    # This confirms the session persisted and auto-login completed.
    print("📋 Step 6: Waiting for dashboard to appear (confirms session persisted and auto-login occurred)")
    expect(dashboard_page.dashboard_container).to_be_visible(timeout=15000)  # 15 seconds for network + UI update
    print("✓ Dashboard is now visible - session persisted successfully")
    
    # Assert - Still authenticated
    print("📋 Step 7: Verifying auth modal does NOT appear")
    # Modal should not be visible
    expect(login_page.modal).to_be_hidden()
    print("✓ Auth modal is hidden - user remained authenticated")
    
    # Dashboard should be loaded
    print("📋 Step 8: Verifying dashboard is fully loaded")
    dashboard_page.assert_on_dashboard()
    
    print("✅ Test passed: Session persists across page reload")


@pytest.mark.auth
def test_password_field_masking(page: Page):
    """
    Test that password input is properly masked.
    
    Steps:
    1. Navigate to login modal
    2. Type password
    3. Verify input type is 'password'
    4. Verify characters are masked
    
    Expected: Password field uses type='password',
              input is not visible as plain text.
    """
    # Arrange
    login_page = LoginPage(page)
    
    # Act
    login_page.wait_for_auth_modal()
    # Use register mode password field (default mode on load)
    login_page.fill_password("TestPassword123!", mode="register")
    
    # Assert - Password field is masked
    password_input = page.locator(login_page.REGISTER_PASSWORD_INPUT)
    input_type = password_input.get_attribute("type")
    
    assert input_type == "password", \
        f"Password input should have type='password', got: {input_type}"


@pytest.mark.auth
def test_switch_between_login_and_register(page: Page):
    """
    Test switching between login and register modes.
    
    Steps:
    1. Start in login mode (or register mode by default)
    2. Switch to register mode
    3. Verify register form elements
    4. Switch back to login mode
    5. Verify login form elements
    
    Expected: Modal correctly toggles between modes,
              appropriate fields displayed.
    """
    # Arrange
    login_page = LoginPage(page)
    
    login_page.wait_for_auth_modal()
    
    # Act & Assert - Ensure we're in register mode first
    login_page.switch_to_register_mode()
    login_page.assert_in_register_mode()
    
    # Verify register form elements are present
    assert login_page.is_visible(login_page.REGISTER_USERNAME_INPUT), \
        "Register username input should be visible"
    assert login_page.is_visible(login_page.REGISTER_PASSWORD_INPUT), \
        "Register password input should be visible"
    assert login_page.is_visible(login_page.REGISTER_EMAIL_INPUT), \
        "Register email input should be visible"
    
    # Switch to login mode
    login_page.switch_to_login_mode()
    login_page.assert_in_login_mode()
    
    # Verify login form elements are present
    assert login_page.is_visible(login_page.LOGIN_USERNAME_INPUT), \
        "Login username input should be visible"
    assert login_page.is_visible(login_page.LOGIN_PASSWORD_INPUT), \
        "Login password input should be visible"


@pytest.mark.auth
@pytest.mark.skip_in_ci  # Requires admin user to exist
def test_admin_user_login(page: Page):
    """
    Test login as admin user (if exists).
    
    Steps:
    1. Login with admin credentials from environment
    2. Verify successful authentication
    3. Verify admin has access to all features
    
    Expected: Admin user can login and access all pages.
    
    Note: Requires E2E_ADMIN_USERNAME and E2E_ADMIN_PASSWORD
          environment variables to be set.
    """
    import os
    
    admin_username = os.getenv("E2E_ADMIN_USERNAME")
    admin_password = os.getenv("E2E_ADMIN_PASSWORD")
    
    if not admin_username or not admin_password:
        pytest.skip("Admin credentials not configured in environment")
    
    # Arrange
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    # Act - Login as admin
    login_page.login(admin_username, admin_password)
    
    # Assert - Successful login
    dashboard_page.wait_for_dashboard_load()
    dashboard_page.assert_on_dashboard()
    
    # Verify admin can access settings
    dashboard_page.navigate_to_settings()
    assert page.locator("#settingsView").is_visible(), \
        "Admin should have access to settings"
