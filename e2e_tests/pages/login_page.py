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
    MODAL_TITLE = "#modalTitle"
    USERNAME_INPUT = "#authUsername"
    PASSWORD_INPUT = "#authPassword"
    EMAIL_INPUT = "#authEmail"
    LOGIN_BUTTON = "button:has-text('Login')"
    REGISTER_BUTTON = "button:has-text('Register')"
    SWITCH_TO_REGISTER_LINK = "text=Don't have an account? Register"
    SWITCH_TO_LOGIN_LINK = "text=Already have an account? Login"
    ERROR_MESSAGE = ".error-message, .notification.error"
    SUCCESS_MESSAGE = ".success-message, .notification.success"
    
    def __init__(self, page: Page):
        """
        Initialize the LoginPage.
        
        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
    
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
        
        # Check if we're already in register mode
        modal_title = self.get_text(self.MODAL_TITLE)
        if "Register" in modal_title:
            logger.info("Already in register mode")
            return
        
        # Click the "Don't have an account?" link
        self.click(self.SWITCH_TO_REGISTER_LINK)
        self.wait_for_text("Register")
    
    def switch_to_login_mode(self) -> None:
        """Switch from register mode to login mode."""
        logger.info("Switching to login mode")
        
        # Check if we're already in login mode
        modal_title = self.get_text(self.MODAL_TITLE)
        if "Login" in modal_title:
            logger.info("Already in login mode")
            return
        
        # Click the "Already have an account?" link
        self.click(self.SWITCH_TO_LOGIN_LINK)
        self.wait_for_text("Login")
    
    def fill_username(self, username: str) -> None:
        """
        Fill the username field.
        
        Args:
            username: Username to enter
        """
        logger.info(f"Filling username: {username}")
        self.fill(self.USERNAME_INPUT, username)
    
    def fill_password(self, password: str) -> None:
        """
        Fill the password field.
        
        Args:
            password: Password to enter
        """
        logger.info("Filling password")
        self.fill(self.PASSWORD_INPUT, password)
    
    def fill_email(self, email: str) -> None:
        """
        Fill the email field (registration only).
        
        Args:
            email: Email address to enter
        """
        logger.info(f"Filling email: {email}")
        self.fill(self.EMAIL_INPUT, email)
    
    def click_login_button(self) -> None:
        """Click the Login button."""
        logger.info("Clicking Login button")
        self.click(self.LOGIN_BUTTON)
    
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
        self.fill_username(username)
        self.fill_password(password)
        
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
        self.fill_username(username)
        self.fill_password(password)
        
        # Fill email if provided
        if email and self.is_visible(self.EMAIL_INPUT):
            self.fill_email(email)
        
        # Submit
        self.click_register_button()
        
        # Wait for modal to close (indicates success)
        if wait_for_success:
            self.wait_for_modal_close(timeout=10000)
            logger.info("Registration successful - modal closed")
    
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
        
        # Check for error message
        if self.is_visible(self.ERROR_MESSAGE):
            error_text = self.get_text(self.ERROR_MESSAGE)
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
        modal_title = self.get_text(self.MODAL_TITLE)
        assert "Login" in modal_title, f"Expected 'Login' in title, got: {modal_title}"
    
    def assert_in_register_mode(self) -> None:
        """Assert that the modal is in register mode."""
        logger.info("Asserting register mode")
        modal_title = self.get_text(self.MODAL_TITLE)
        assert "Register" in modal_title, f"Expected 'Register' in title, got: {modal_title}"
