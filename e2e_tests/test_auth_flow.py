"""
E2E Tests for Authentication Flows.

Tests user registration, login, logout, and error handling.
Validates JWT token management and session persistence.
"""

import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import generate_test_user


@pytest.mark.smoke
@pytest.mark.auth
def test_registration_and_login(page: Page):
    """
    Test complete registration and login flow.
    
    Steps:
    1. Navigate to Proximity UI
    2. Fill registration form with unique credentials
    3. Submit registration
    4. Verify automatic login (modal closes)
    5. Verify dashboard is visible
    6. Verify user is authenticated
    
    Expected: User successfully registered and logged in,
              dashboard loads, auth modal is hidden.
    """
    # Arrange
    test_user = generate_test_user()
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    # Act - Register new user
    login_page.wait_for_auth_modal()
    login_page.register(
        username=test_user["username"],
        password=test_user["password"],
        email=test_user["email"]
    )
    
    # Assert - Verify successful login
    login_page.assert_auth_modal_hidden()
    dashboard_page.wait_for_dashboard_load()
    dashboard_page.assert_on_dashboard()
    
    # Additional verification - User menu visible
    assert dashboard_page.is_visible(dashboard_page.USER_MENU), \
        "User menu should be visible after login"


@pytest.mark.auth
def test_logout(authenticated_page: Page):
    """
    Test logout functionality.
    
    Steps:
    1. Start with authenticated session
    2. Click logout button
    3. Verify auth modal reappears
    4. Verify access to protected pages redirects to login
    
    Expected: User logged out, auth modal visible,
              protected content inaccessible.
    """
    # Arrange
    dashboard_page = DashboardPage(authenticated_page)
    login_page = LoginPage(authenticated_page)
    
    # Verify we start authenticated
    dashboard_page.assert_on_dashboard()
    
    # Act - Logout
    dashboard_page.logout()
    
    # Assert - Auth modal reappears
    login_page.assert_auth_modal_visible()
    
    # Verify we can't access protected content
    # Try to navigate to dashboard
    dashboard_page.navigate_to("/")
    
    # Should still see auth modal (not authenticated)
    login_page.assert_auth_modal_visible()


@pytest.mark.auth
def test_invalid_login(page: Page):
    """
    Test login with incorrect credentials.
    
    Steps:
    1. Attempt login with invalid credentials
    2. Verify error message is displayed
    3. Verify user remains on login modal
    4. Verify dashboard is NOT accessible
    
    Expected: Login fails with error message,
              modal remains visible, no access granted.
    """
    # Arrange
    login_page = LoginPage(page)
    
    # Act - Attempt login with bad credentials
    error_message = login_page.login_with_error_check(
        username="nonexistent_user",
        password="wrong_password_123"
    )
    
    # Assert - Error displayed
    assert error_message != "", "Expected error message for invalid login"
    assert any(keyword in error_message.lower() for keyword in ["invalid", "incorrect", "failed", "error"]), \
        f"Error message should indicate failure: {error_message}"
    
    # Verify modal still visible
    login_page.assert_auth_modal_visible()
    
    # Verify dashboard not accessible
    assert not page.locator("#dashboardView").is_visible(), \
        "Dashboard should not be visible after failed login"


@pytest.mark.auth
def test_session_persistence(page: Page, base_url: str):
    """
    Test that authentication token persists across page reloads.
    
    Steps:
    1. Register and login
    2. Reload the page
    3. Verify user still authenticated (no login modal)
    4. Verify dashboard loads automatically
    
    Expected: JWT token persists in localStorage,
              user remains logged in after reload.
    """
    # Arrange
    test_user = generate_test_user()
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    # Act - Register and login
    login_page.register(test_user["username"], test_user["password"])
    dashboard_page.wait_for_dashboard_load()
    
    # Verify token stored in localStorage
    token = page.evaluate("localStorage.getItem('proximity_token')")
    assert token is not None, "JWT token should be stored in localStorage"
    assert len(token) > 20, "JWT token should be a valid length"
    
    # Reload page
    page.reload()
    
    # Assert - Still authenticated
    # Should NOT see auth modal
    page.wait_for_timeout(2000)  # Give time for auth check
    assert not login_page.is_visible(login_page.AUTH_MODAL), \
        "Auth modal should not appear after reload if token valid"
    
    # Dashboard should load automatically
    dashboard_page.wait_for_dashboard_load()
    dashboard_page.assert_on_dashboard()


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
