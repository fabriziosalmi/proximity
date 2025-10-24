"""
Login Page Object Model

Encapsulates all interactions with the login/authentication pages.
"""
from playwright.sync_api import Page, expect
from typing import Optional
import requests


class LoginPage:
    """
    Page Object for the login page.
    
    Locators are defined as class constants for easy maintenance.
    Actions are implemented as methods that return self for chaining.
    """
    
    # Locators
    USERNAME_INPUT = 'input[name="username"], input[type="email"], input[placeholder*="username" i], input[placeholder*="email" i]'
    PASSWORD_INPUT = 'input[name="password"], input[type="password"]'
    SUBMIT_BUTTON = 'button:has-text("Sign In"), button[type="submit"], button:has-text("Log in"), button:has-text("Sign in")'
    ERROR_MESSAGE = '.error, .alert-error, [role="alert"]'
    SUCCESS_MESSAGE = '.success, .alert-success'
    
    # Registration-specific locators
    REGISTER_LINK = 'a[href*="register"], a:has-text("Register"), a:has-text("Sign up")'
    FIRST_NAME_INPUT = 'input[name="first_name"], input[name="firstName"]'
    LAST_NAME_INPUT = 'input[name="last_name"], input[name="lastName"]'
    EMAIL_INPUT = 'input[name="email"], input[type="email"]'
    REGISTER_USERNAME_INPUT = 'input[name="username"]'
    REGISTER_PASSWORD_INPUT = 'input[name="password"]'
    REGISTER_SUBMIT_BUTTON = 'button[type="submit"]:has-text("Register"), button[type="submit"]:has-text("Sign up")'
    
    def __init__(self, page: Page, base_url: str):
        """
        Initialize the LoginPage.
        
        Args:
            page: Playwright Page object
            base_url: Base URL of the application
        """
        self.page = page
        self.base_url = base_url
    
    def navigate_and_wait_for_ready(self) -> 'LoginPage':
        """
        Navigate to the login page and wait for SvelteKit hydration to complete.
        
        This method ensures that SvelteKit has fully hydrated the page and
        attached all event handlers before proceeding. This prevents race
        conditions where Playwright might click elements before their event
        handlers are attached.
        
        Returns:
            Self for method chaining
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Navigating to {self.base_url}/login and waiting for SvelteKit hydration")
        
        # Navigate to the page
        self.page.goto(f"{self.base_url}/login")
        
        # Wait for the page to load (DOM content ready)
        self.page.wait_for_load_state("domcontentloaded")
        
        # Wait for SvelteKit to complete hydration by checking for interactive elements
        # Instead of waiting for data-sveltekit-interactive (which doesn't exist in this version),
        # we wait for the login form to be ready
        logger.info("Waiting for login form to be interactive")
        try:
            # Wait for both username and password fields to be visible and enabled
            self.page.wait_for_selector(self.USERNAME_INPUT, state="visible", timeout=30000)
            self.page.wait_for_selector(self.PASSWORD_INPUT, state="visible", timeout=5000)
            logger.info("✓ Login form is ready and interactive")
        except Exception as e:
            # Debug: Check what's actually on the page
            body_attrs = self.page.evaluate("() => { const attrs = {}; for (const attr of document.body.attributes) { attrs[attr.name] = attr.value; } return attrs; }")
            logger.error(f"Login form NOT ready! Body attributes: {body_attrs}")
            logger.error(f"Page URL: {self.page.url}")
            logger.error(f"Page title: {self.page.title()}")
            raise
        return self
    
    def navigate(self) -> 'LoginPage':
        """Navigate to the login page."""
        self.page.goto(f"{self.base_url}/login")
        return self
    
    def fill_username(self, username: str) -> 'LoginPage':
        """Fill in the username field."""
        self.page.fill(self.USERNAME_INPUT, username)
        return self
    
    def fill_password(self, password: str) -> 'LoginPage':
        """Fill in the password field."""
        self.page.fill(self.PASSWORD_INPUT, password)
        return self
    
    def click_submit(self) -> 'LoginPage':
        """Click the login submit button."""
        self.page.click(self.SUBMIT_BUTTON)
        return self
    
    def login(self, username: str, password: str, wait_for_navigation: bool = True) -> 'LoginPage':
        """
        Complete login flow.
        
        Args:
            username: Username or email
            password: Password
            wait_for_navigation: Whether to wait for successful login
        
        Returns:
            self for chaining
        """
        # Wait for page to be fully loaded
        self.page.wait_for_load_state("domcontentloaded")
        
        # Wait for form to be ready - use locators with auto-waiting
        username_input = self.page.locator(self.USERNAME_INPUT).first
        password_input = self.page.locator(self.PASSWORD_INPUT).first
        submit_button = self.page.locator(self.SUBMIT_BUTTON).first
        
        # Ensure elements are visible (Playwright auto-waits)
        expect(username_input).to_be_visible(timeout=10000)
        expect(password_input).to_be_visible(timeout=10000)
        expect(submit_button).to_be_visible(timeout=10000)
        
        # Fill fields
        username_input.fill(username)
        password_input.fill(password)
        
        # Click submit
        submit_button.click()
        
        if wait_for_navigation:
            # Wait for successful login by checking for homepage elements
            # SvelteKit uses client-side navigation, so we look for content change
            try:
                # Wait for either Apps or Store link to be visible (homepage elements)
                self.page.locator('a[href="/apps"], a[href="/store"]').first.wait_for(
                    state='visible',
                    timeout=10000
                )
            except Exception:
                # Fallback: just wait a bit for the page to settle
                self.page.wait_for_timeout(2000)
        
        return self
    
    def navigate_to_register(self) -> 'LoginPage':
        """Navigate to the registration page."""
        self.page.goto(f"{self.base_url}/register")
        return self
    
    def register(
        self,
        email: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str
    ) -> 'LoginPage':
        """
        Complete registration flow.
        
        Args:
            email: User email
            username: Username
            password: Password
            first_name: First name
            last_name: Last name
        
        Returns:
            self for chaining
        """
        self.navigate_to_register()
        
        self.page.fill(self.EMAIL_INPUT, email)
        self.page.fill(self.REGISTER_USERNAME_INPUT, username)
        self.page.fill(self.PASSWORD_INPUT, password)
        self.page.fill(self.FIRST_NAME_INPUT, first_name)
        self.page.fill(self.LAST_NAME_INPUT, last_name)
        
        with self.page.expect_navigation():
            self.page.click(self.REGISTER_SUBMIT_BUTTON)
        
        return self
    
    def assert_login_success(self, expected_url: Optional[str] = None) -> 'LoginPage':
        """
        Assert that login was successful.
        
        Args:
            expected_url: Optional URL to expect after login
        
        Returns:
            self for chaining
        """
        if expected_url:
            expect(self.page).to_have_url(expected_url, timeout=10000)
        else:
            # Default: Expect to be redirected away from /login
            expect(self.page).not_to_have_url(f"{self.base_url}/login", timeout=10000)
        
        return self
    
    def assert_error_visible(self, error_text: Optional[str] = None) -> 'LoginPage':
        """
        Assert that an error message is visible.
        
        Args:
            error_text: Optional specific error text to match
        
        Returns:
            self for chaining
        """
        error_locator = self.page.locator(self.ERROR_MESSAGE).first
        expect(error_locator).to_be_visible(timeout=5000)
        
        if error_text:
            expect(error_locator).to_contain_text(error_text)
        
        return self
    
    def is_logged_in(self) -> bool:
        """
        Check if the user is logged in by looking for common indicators.
        
        Returns:
            True if user appears to be logged in
        """
        # Check for common logged-in indicators
        indicators = [
            'button:has-text("Logout")',
            'button:has-text("Log out")',
            '.user-avatar',
            '[data-testid="user-menu"]',
            'nav a[href="/apps"]',
        ]
        
        for indicator in indicators:
            if self.page.locator(indicator).count() > 0:
                return True
        
        return False
    
    def login_with_api(self, username: str, password: str, api_base_url: str = "http://localhost:8000") -> 'LoginPage':
        """
        Login using direct API call and set the token/cookie in browser.
        This bypasses the frontend form and is more reliable for E2E tests.
        
        Args:
            username: Username to login with
            password: Password
            api_base_url: Base URL of the API (default: http://localhost:8000)
        
        Returns:
            self for chaining
        """
        import requests
        
        # Call the correct dj-rest-auth login endpoint
        response = requests.post(
            f"{api_base_url}/api/auth/login/",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
            verify=False  # Accept self-signed certificates for local development
        )
        
        if not response.ok:
            raise Exception(f"API login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        token = data.get('access_token') or data.get('access')  # Try both formats
        
        if not token:
            raise Exception(f"No access token in response: {data}")
        
        # Navigate to any page first (needed to set localStorage)
        self.page.goto(f"{self.base_url}/login")
        self.page.wait_for_load_state("domcontentloaded")
        
        # Set the token in localStorage via JavaScript
        self.page.evaluate(f"""
            localStorage.setItem('access_token', '{token}');
            localStorage.setItem('user', JSON.stringify({{ username: '{username}' }}));
        """)
        
        # Navigate to home to trigger auth check
        self.page.goto(self.base_url + "/")
        self.page.wait_for_load_state("networkidle")
        
        return self
