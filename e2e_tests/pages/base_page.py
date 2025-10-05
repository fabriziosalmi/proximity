"""
Base Page Object Model class for Proximity E2E tests.

Provides common functionality for all page objects including
navigation, waiting, screenshots, and element interactions.
"""

import logging
from typing import Optional
from playwright.sync_api import Page, Locator, expect

logger = logging.getLogger(__name__)


class BasePage:
    """
    Base class for all Page Objects.
    
    Provides common methods for interacting with pages,
    including navigation, waiting, and element interactions.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the base page.

        Args:
            page: Playwright Page instance
        """
        self.page = page
        # Extract base URL from current page URL
        import os
        self.base_url = os.getenv("PROXIMITY_E2E_URL", "http://127.0.0.1:8765")
    
    # ========================================================================
    # Navigation Methods
    # ========================================================================
    
    def navigate_to(self, path: str) -> None:
        """
        Navigate to a specific path relative to base URL.

        Args:
            path: Relative path (e.g., '/dashboard', '/apps') or full URL
        """
        # If path is relative, prepend base_url
        if path.startswith('/'):
            full_url = f"{self.base_url}{path}"
        else:
            full_url = path

        logger.info(f"Navigating to: {full_url}")
        self.page.goto(full_url)
    
    def reload(self) -> None:
        """Reload the current page."""
        logger.info("Reloading page")
        self.page.reload()
    
    def go_back(self) -> None:
        """Navigate back in browser history."""
        logger.info("Going back")
        self.page.go_back()
    
    def clear_session(self) -> None:
        """
        Clear localStorage and sessionStorage to reset authentication state.
        
        CRITICAL for test isolation - prevents JWT token leakage between tests.
        Use this at the beginning of tests that require a clean, unauthenticated state.
        """
        logger.info("Clearing session storage (localStorage + sessionStorage)")
        self.page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
        logger.info("Session storage cleared successfully")
    
    # ========================================================================
    # Element Interaction Methods
    # ========================================================================
    
    def click(self, selector: str, timeout: int = 30000) -> None:
        """
        Click an element.
        
        Args:
            selector: CSS selector or text selector
            timeout: Maximum time to wait for element (milliseconds)
        """
        logger.info(f"Clicking: {selector}")
        self.page.locator(selector).click(timeout=timeout)
    
    def fill(self, selector: str, value: str, timeout: int = 30000) -> None:
        """
        Fill an input field.
        
        Args:
            selector: CSS selector
            value: Value to fill
            timeout: Maximum time to wait for element (milliseconds)
        """
        logger.info(f"Filling {selector} with: {value[:20]}...")
        self.page.locator(selector).fill(value, timeout=timeout)
    
    def type_slowly(self, selector: str, value: str, delay: int = 100) -> None:
        """
        Type text slowly (character by character).
        
        Useful for inputs with event listeners.
        
        Args:
            selector: CSS selector
            value: Text to type
            delay: Delay between keystrokes (milliseconds)
        """
        logger.info(f"Typing slowly into {selector}: {value[:20]}...")
        self.page.locator(selector).press_sequentially(value, delay=delay)
    
    def select_option(self, selector: str, value: str) -> None:
        """
        Select an option from a dropdown.
        
        Args:
            selector: CSS selector for the select element
            value: Value to select
        """
        logger.info(f"Selecting option '{value}' in {selector}")
        self.page.locator(selector).select_option(value)
    
    def check(self, selector: str) -> None:
        """
        Check a checkbox or radio button.
        
        Args:
            selector: CSS selector
        """
        logger.info(f"Checking: {selector}")
        self.page.locator(selector).check()
    
    def uncheck(self, selector: str) -> None:
        """
        Uncheck a checkbox.
        
        Args:
            selector: CSS selector
        """
        logger.info(f"Unchecking: {selector}")
        self.page.locator(selector).uncheck()
    
    # ========================================================================
    # Wait Methods
    # ========================================================================
    
    def wait_for_selector(self, selector: str, timeout: int = 30000, state: str = "visible") -> Locator:
        """
        Wait for an element to reach a specific state.
        
        Args:
            selector: CSS selector
            timeout: Maximum time to wait (milliseconds)
            state: Element state ('visible', 'hidden', 'attached', 'detached')
        
        Returns:
            Locator for the element
        """
        logger.info(f"Waiting for {selector} to be {state}")
        return self.page.wait_for_selector(selector, timeout=timeout, state=state)
    
    def wait_for_text(self, text: str, timeout: int = 30000) -> None:
        """
        Wait for specific text to appear on the page.
        
        Args:
            text: Text to wait for
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info(f"Waiting for text: {text}")
        self.page.wait_for_selector(f"text={text}", timeout=timeout)
    
    def wait_for_url(self, url_pattern: str, timeout: int = 30000) -> None:
        """
        Wait for URL to match a pattern.
        
        Args:
            url_pattern: URL pattern (can include wildcards)
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info(f"Waiting for URL: {url_pattern}")
        self.page.wait_for_url(url_pattern, timeout=timeout)
    
    def wait_for_load_state(self, state: str = "load", timeout: int = 30000) -> None:
        """
        Wait for a specific page load state.
        
        Args:
            state: Load state ('load', 'domcontentloaded', 'networkidle')
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info(f"Waiting for load state: {state}")
        self.page.wait_for_load_state(state, timeout=timeout)
    
    def wait_for_timeout(self, timeout: int) -> None:
        """
        Hard wait for a specific duration.
        
        Use sparingly - prefer wait_for_selector or wait_for_load_state.
        
        Args:
            timeout: Time to wait (milliseconds)
        """
        logger.warning(f"Hard wait for {timeout}ms")
        self.page.wait_for_timeout(timeout)
    
    # ========================================================================
    # Assertion Helpers
    # ========================================================================
    
    def assert_visible(self, selector: str, timeout: int = 5000) -> None:
        """
        Assert that an element is visible.
        
        Args:
            selector: CSS selector
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info(f"Asserting visible: {selector}")
        expect(self.page.locator(selector)).to_be_visible(timeout=timeout)
    
    def assert_hidden(self, selector: str, timeout: int = 5000) -> None:
        """
        Assert that an element is hidden or doesn't exist.
        
        Args:
            selector: CSS selector
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info(f"Asserting hidden: {selector}")
        expect(self.page.locator(selector)).to_be_hidden(timeout=timeout)
    
    def assert_text_present(self, text: str, timeout: int = 5000) -> None:
        """
        Assert that specific text is present on the page.
        
        Args:
            text: Text to find
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info(f"Asserting text present: {text}")
        expect(self.page.locator(f"text={text}")).to_be_visible(timeout=timeout)
    
    def assert_url_contains(self, url_fragment: str) -> None:
        """
        Assert that current URL contains a specific fragment.
        
        Args:
            url_fragment: Fragment to find in URL
        """
        logger.info(f"Asserting URL contains: {url_fragment}")
        expect(self.page).to_have_url_containing(url_fragment)
    
    # ========================================================================
    # Element Query Methods
    # ========================================================================
    
    def get_text(self, selector: str) -> str:
        """
        Get the text content of an element.
        
        Args:
            selector: CSS selector
        
        Returns:
            Text content of the element
        """
        return self.page.locator(selector).text_content()
    
    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        Get an attribute value from an element.
        
        Args:
            selector: CSS selector
            attribute: Attribute name
        
        Returns:
            Attribute value or None
        """
        return self.page.locator(selector).get_attribute(attribute)
    
    def get_value(self, selector: str) -> str:
        """
        Get the value of an input element.
        
        Args:
            selector: CSS selector
        
        Returns:
            Input value
        """
        return self.page.locator(selector).input_value()
    
    def is_visible(self, selector: str) -> bool:
        """
        Check if an element is visible.
        
        Args:
            selector: CSS selector
        
        Returns:
            True if visible, False otherwise
        """
        try:
            return self.page.locator(selector).is_visible(timeout=1000)
        except Exception:
            return False
    
    def is_enabled(self, selector: str) -> bool:
        """
        Check if an element is enabled.
        
        Args:
            selector: CSS selector
        
        Returns:
            True if enabled, False otherwise
        """
        return self.page.locator(selector).is_enabled()
    
    def count(self, selector: str) -> int:
        """
        Count elements matching a selector.
        
        Args:
            selector: CSS selector
        
        Returns:
            Number of matching elements
        """
        return self.page.locator(selector).count()
    
    # ========================================================================
    # Screenshot and Debugging
    # ========================================================================
    
    def screenshot(self, path: str) -> None:
        """
        Take a screenshot of the entire page.
        
        Args:
            path: Path to save screenshot
        """
        logger.info(f"Taking screenshot: {path}")
        self.page.screenshot(path=path, full_page=True)
    
    def screenshot_element(self, selector: str, path: str) -> None:
        """
        Take a screenshot of a specific element.
        
        Args:
            selector: CSS selector
            path: Path to save screenshot
        """
        logger.info(f"Taking screenshot of {selector}: {path}")
        self.page.locator(selector).screenshot(path=path)
    
    def console_log(self, message: str) -> None:
        """
        Log a message to the browser console (for debugging).
        
        Args:
            message: Message to log
        """
        self.page.evaluate(f"console.log('{message}')")
    
    # ========================================================================
    # Common UI Patterns
    # ========================================================================
    
    def wait_for_notification(self, expected_text: Optional[str] = None, timeout: int = 10000) -> str:
        """
        Wait for a notification/toast message to appear.
        
        Args:
            expected_text: Expected notification text (optional)
            timeout: Maximum time to wait (milliseconds)
        
        Returns:
            The notification text
        """
        logger.info("Waiting for notification")
        notification = self.wait_for_selector(".notification, .toast, .alert", timeout=timeout)
        text = notification.text_content()
        
        if expected_text:
            assert expected_text in text, f"Expected '{expected_text}' in notification, got: {text}"
        
        return text
    
    def dismiss_notification(self) -> None:
        """Dismiss any visible notifications."""
        if self.is_visible(".notification .close, .toast .close"):
            self.click(".notification .close, .toast .close")
            self.wait_for_timeout(500)  # Brief pause for animation
