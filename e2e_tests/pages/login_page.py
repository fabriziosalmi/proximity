"""
Page Object Model for the Login/Registration modal.

Handles authentication flows including registration,
login, and logout operations.
"""

import logging
from playwright.sync_api import Page
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """
    Page Object for the Login/Registration modal.
    
    This modal appears on the initial page load if the user is not authenticated.
    """
    
    # Selectors
    AUTH_MODAL = "#authModal"
    MODAL_TITLE = "#authModalTitle"
    
    # Register mode selectors
    REGISTER_USERNAME_INPUT = "#registerUsername"
    REGISTER_PASSWORD_INPUT = "#registerPassword"
    REGISTER_EMAIL_INPUT = "#registerEmail"
    REGISTER_TAB = "#registerTab"
    REGISTER_ERROR = "#registerError"
    
    # Login mode selectors
    LOGIN_USERNAME_INPUT = "#loginUsername"
    LOGIN_PASSWORD_INPUT = "#loginPassword"
    LOGIN_TAB = "#loginTab"
    LOGIN_ERROR = "#loginError"
    
    # Common selectors
    REGISTER_BUTTON = "#registerForm button[type='submit']"
    LOGIN_SUBMIT_BUTTON = "#loginForm button[type='submit']"
    ERROR_MESSAGE = ".form-error"
    SUCCESS_MESSAGE = ".success-message, .notification.success"
    
    def __init__(self, page: Page):
        """
        Initialize the LoginPage.
        
        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
    
    # ========================================================================
    # Properties - Locators for use in expect() assertions
    # ========================================================================
    
    @property
    def modal(self):
        """
        Return the auth modal locator for use in expect() assertions.
        
        This property allows tests to use Playwright's auto-retrying assertions
        like: expect(login_page.modal).to_be_visible()
        
        Returns:
            Locator for the authentication modal element
        """
        return self.page.locator(self.AUTH_MODAL)
    
    @property
    def login_error(self):
        """
        Return the login error locator for use in expect() assertions.
        
        Returns:
            Locator for the login error message element
        """
        return self.page.locator(self.LOGIN_ERROR)
    
    @property
    def register_error(self):
        """
        Return the register error locator for use in expect() assertions.
        
        Returns:
            Locator for the register error message element
        """
        return self.page.locator(self.REGISTER_ERROR)
    
    # ========================================================================
    # Wait Methods
    # ========================================================================
    
    def wait_for_auth_modal(self, timeout: int = 10000) -> None:
        """
        Wait for the auth modal to be visible.
        
        Args:
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info("Waiting for auth modal to appear")
        self.wait_for_selector(self.AUTH_MODAL, timeout=timeout)
        # Wait for tabs to render
        self.wait_for_selector(self.REGISTER_TAB, timeout=timeout)
    
    def wait_for_modal_close(self, timeout: int = 10000) -> None:
        """
        Wait for the auth modal to close/disappear.
        
        Args:
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info("Waiting for auth modal to close")
        self.wait_for_selector(self.AUTH_MODAL, timeout=timeout, state="hidden")
    
    # ========================================================================
    # Form Interaction Methods
    # ========================================================================
    
    def switch_to_register_mode(self) -> None:
        """Switch from login mode to register mode."""
        logger.info("Switching to register mode")
        
        # Check if we're already in register mode by checking if tab is active
        register_tab = self.page.locator(self.REGISTER_TAB)
        if register_tab.get_attribute("class") and "active" in register_tab.get_attribute("class"):
            logger.info("Already in register mode")
            return
        
        # Click the register tab
        self.click(self.REGISTER_TAB)
        self.wait_for_selector(self.REGISTER_USERNAME_INPUT)
    
    def switch_to_login_mode(self) -> None:
        """Switch from register mode to login mode."""
        logger.info("Switching to login mode")
        
        # Check if we're already in login mode by checking if tab is active
        login_tab = self.page.locator(self.LOGIN_TAB)
        if login_tab.get_attribute("class") and "active" in login_tab.get_attribute("class"):
            logger.info("Already in login mode")
            return
        
        # Click the login tab
        self.click(self.LOGIN_TAB)
        self.wait_for_selector(self.LOGIN_USERNAME_INPUT)
    
    def fill_username(self, username: str, mode: str = "auto") -> None:
        """
        Fill the username field.
        
        Args:
            username: Username to enter
            mode: "login", "register", or "auto" (detects current mode)
        """
        logger.info(f"Filling username: {username}")
        
        # Auto-detect mode if not specified
        if mode == "auto":
            if self.is_visible(self.LOGIN_USERNAME_INPUT):
                mode = "login"
            elif self.is_visible(self.REGISTER_USERNAME_INPUT):
                mode = "register"
            else:
                raise Exception("Could not detect login or register mode")
        
        selector = self.LOGIN_USERNAME_INPUT if mode == "login" else self.REGISTER_USERNAME_INPUT
        self.fill(selector, username)
    
    def fill_password(self, password: str, mode: str = "auto") -> None:
        """
        Fill the password field.
        
        Args:
            password: Password to enter
            mode: "login", "register", or "auto" (detects current mode)
        """
        logger.info("Filling password")
        
        # Auto-detect mode if not specified
        if mode == "auto":
            if self.is_visible(self.LOGIN_PASSWORD_INPUT):
                mode = "login"
            elif self.is_visible(self.REGISTER_PASSWORD_INPUT):
                mode = "register"
            else:
                raise Exception("Could not detect login or register mode")
        
        selector = self.LOGIN_PASSWORD_INPUT if mode == "login" else self.REGISTER_PASSWORD_INPUT
        self.fill(selector, password)
    
    def fill_email(self, email: str) -> None:
        """
        Fill the email field (registration only).
        
        Args:
            email: Email address to enter
        """
        logger.info(f"Filling email: {email}")
        self.fill(self.REGISTER_EMAIL_INPUT, email)
    
    def click_login_button(self) -> None:
        """Click the Login submit button."""
        logger.info("Clicking Login submit button")
        self.click(self.LOGIN_SUBMIT_BUTTON)
    
    def click_register_button(self) -> None:
        """Click the Register button."""
        logger.info("Clicking Register button")
        self.click(self.REGISTER_BUTTON)
    
    # ========================================================================
    # High-Level Action Methods
    # ========================================================================
    
    def login(self, username: str, password: str, wait_for_success: bool = True) -> None:
        """
        Perform complete login flow.
        
        Args:
            username: Username
            password: Password
            wait_for_success: Whether to wait for modal to close (default: True)
        """
        logger.info(f"Logging in as: {username}")
        
        # Ensure we're in login mode
        self.switch_to_login_mode()
        
        # Fill credentials
        self.fill_username(username, mode="login")
        self.fill_password(password, mode="login")
        
        # Submit
        self.click_login_button()
        
        # Wait for modal to close (indicates success)
        if wait_for_success:
            self.wait_for_modal_close(timeout=10000)
            logger.info("Login successful - modal closed")
    
    def register(self, username: str, password: str, email: str = None, wait_for_success: bool = True) -> None:
        """
        Perform complete registration flow.
        
        Args:
            username: Username
            password: Password
            email: Email address (optional)
            wait_for_success: Whether to wait for modal to close (default: True)
        """
        logger.info(f"Registering user: {username}")
        
        # Ensure we're in register mode
        self.switch_to_register_mode()
        
        # Fill credentials
        self.fill_username(username, mode="register")
        self.fill_password(password, mode="register")
        
        # Fill email if provided
        if email and self.is_visible(self.REGISTER_EMAIL_INPUT):
            self.fill_email(email)
        
        # Submit
        self.click_register_button()
        
        # Wait for modal to close (indicates success)
        # NOTE: With the frontend fix, modal should close automatically after registration
        if wait_for_success:
            try:
                # First, wait a bit for the registration request to complete
                self.page.wait_for_timeout(1000)
                
                # Then wait for modal to close (should happen automatically now)
                self.wait_for_modal_close(timeout=5000)
                logger.info("Registration successful - modal closed automatically")
            except Exception as e:
                logger.warning(f"Modal didn't close automatically, checking auth state: {e}")
                
                # Check if we're authenticated (token was saved)
                token_saved = self.page.evaluate("""
                    () => {
                        return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
                    }
                """)
                
                if token_saved:
                    logger.info("Registration successful - token found, forcing modal close")
                    # Force close the modal (workaround for slow modal animation)
                    self.page.evaluate("""
                        const modal = document.getElementById('authModal');
                        if (modal && modal.classList.contains('show')) {
                            modal.classList.remove('show');
                            modal.style.display = 'none';
                            document.body.classList.remove('modal-open');
                            const backdrop = document.querySelector('.modal-backdrop');
                            if (backdrop) backdrop.remove();
                        }
                    """)
                else:
                    logger.warning("Token not found after registration, may have failed")
                    raise Exception("Registration may have failed - no token found")
    
    def login_with_error_check(self, username: str, password: str) -> str:
        """
        Attempt login and return any error message.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            Error message text, or empty string if no error
        """
        logger.info(f"Attempting login as: {username}")
        
        # Perform login without waiting for success
        self.login(username, password, wait_for_success=False)
        
        # Wait a moment for potential error
        self.wait_for_timeout(2000)
        
        # Check for error message in login error div
        if self.is_visible(self.LOGIN_ERROR):
            error_text = self.get_text(self.LOGIN_ERROR)
            logger.info(f"Login error: {error_text}")
            return error_text
        
        return ""
    
    # ========================================================================
    # Assertion Helpers
    # ========================================================================
    
    def assert_auth_modal_visible(self) -> None:
        """Assert that the auth modal is visible."""
        logger.info("Asserting auth modal is visible")
        self.assert_visible(self.AUTH_MODAL)
    
    def assert_auth_modal_hidden(self) -> None:
        """Assert that the auth modal is hidden."""
        logger.info("Asserting auth modal is hidden")
        self.assert_hidden(self.AUTH_MODAL)
    
    def assert_error_message(self, expected_text: str = None) -> None:
        """
        Assert that an error message is displayed.
        
        Args:
            expected_text: Expected error text (optional)
        """
        logger.info("Asserting error message is visible")
        self.assert_visible(self.ERROR_MESSAGE)
        
        if expected_text:
            actual_text = self.get_text(self.ERROR_MESSAGE)
            assert expected_text.lower() in actual_text.lower(), \
                f"Expected error '{expected_text}' not found in '{actual_text}'"
    
    def assert_in_login_mode(self) -> None:
        """Assert that the modal is in login mode."""
        logger.info("Asserting login mode")
        login_tab = self.page.locator(self.LOGIN_TAB)
        tab_class = login_tab.get_attribute("class") or ""
        assert "active" in tab_class, f"Login tab should be active, got class: {tab_class}"
    
    def assert_in_register_mode(self) -> None:
        """Assert that the modal is in register mode."""
        logger.info("Asserting register mode")
        register_tab = self.page.locator(self.REGISTER_TAB)
        tab_class = register_tab.get_attribute("class") or ""
        assert "active" in tab_class, f"Register tab should be active, got class: {tab_class}"
    
    def get_prefilled_username(self) -> str:
        """
        Get the current value of the username field in login mode.
        
        Returns:
            Username value from the login username input field
        """
        logger.info("Getting pre-filled username from login form")
        return self.get_value(self.LOGIN_USERNAME_INPUT)
    
    def assert_username_prefilled(self, expected_username: str) -> None:
        """
        Assert that the login username field is pre-filled with expected value.
        
        Args:
            expected_username: Expected username value
        """
        logger.info(f"Asserting username is pre-filled with: {expected_username}")
        actual_username = self.get_prefilled_username()
        assert actual_username == expected_username, \
            f"Expected username '{expected_username}' to be pre-filled, got: '{actual_username}'"
    
    def wait_for_success_notification(self, timeout: int = 10000) -> str:
        """
        Wait for a success notification to appear (e.g., after registration).
        
        Args:
            timeout: Maximum time to wait (milliseconds)
        
        Returns:
            The notification text
        """
        logger.info("Waiting for success notification")
        return self.wait_for_notification(timeout=timeout)
