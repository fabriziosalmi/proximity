"""
Apps Page Object Model

Encapsulates all interactions with the My Apps page where users manage
their deployed applications.
"""
from playwright.sync_api import Page, expect, Locator
from typing import Optional, List
import time


class AppsPage:
    """
    Page Object for the My Apps page (/apps).
    
    This page displays deployed applications and provides management
    functionality (start, stop, restart, delete).
    """
    
    # Locators
    APP_CARD = '.rack-card, [data-testid="app-card"], .app-card'
    APP_CARD_TITLE = '.app-title, h3, h4'
    APP_HOSTNAME = '[data-testid="hostname"], .hostname'
    
    # Status indicators (adjust based on your actual implementation)
    STATUS_DEPLOYING = '.status-deploying, [data-status="deploying"], .deploying'
    STATUS_CLONING = '.status-cloning, [data-status="cloning"], .cloning'
    STATUS_RUNNING = '.status-running, [data-status="running"], .running'
    STATUS_STOPPED = '.status-stopped, [data-status="stopped"], .stopped'
    STATUS_ERROR = '.status-error, [data-status="error"], .error, .failed'
    
    # Action buttons
    START_BUTTON = 'button:has-text("Start")'
    STOP_BUTTON = 'button:has-text("Stop")'
    RESTART_BUTTON = 'button:has-text("Restart")'
    DELETE_BUTTON = '[data-testid="delete-button"]'
    
    # Confirmation dialog
    CONFIRM_DIALOG = '[role="dialog"], .modal, .confirm-dialog'
    CONFIRM_YES_BUTTON = 'button:has-text("Yes"), button:has-text("Confirm"), button:has-text("Delete")'
    CONFIRM_NO_BUTTON = 'button:has-text("No"), button:has-text("Cancel")'
    
    # Other elements
    EMPTY_STATE = '.empty-state, [data-testid="no-apps"]'
    LOADING_INDICATOR = '.loading, .spinner, [data-loading="true"]'
    TOAST_NOTIFICATION = '.toast, .notification, [role="alert"]'
    
    def __init__(self, page: Page, base_url: str):
        """
        Initialize the AppsPage.
        
        Args:
            page: Playwright Page object
            base_url: Base URL of the application
        """
        self.page = page
        self.base_url = base_url
    
    def navigate(self) -> 'AppsPage':
        """
        Navigate to the apps page with intelligent API synchronization.
        
        Waits for the initial /api/apps call to complete before proceeding,
        eliminating race conditions with frontend data polling.
        
        Returns:
            Self for method chaining
        """
        print(f"  🔄 Navigating to /apps and waiting for initial data load...")
        
        # Intercept the /api/apps call to ensure data is loaded before we interact
        with self.page.expect_response(
            lambda res: "/api/apps" in res.url and res.status == 200,
            timeout=15000
        ) as response_info:
            self.page.goto(f"{self.base_url}/apps")
        
        response = response_info.value
        print(f"  ✅ Initial /api/apps call intercepted (Status: {response.status})")
        print(f"  ✅ UI is now populated with data")
        
        # Additional wait for page stability
        self.page.wait_for_load_state("networkidle")
        
        return self
    
    def get_app_card_by_hostname(self, hostname: str) -> Locator:
        """
        Get the card element for a specific application by hostname.
        
        Uses the most robust selector strategy: data-testid with hostname.
        This is the primary strategy as it's immune to CSS changes and
        provides unique identification.
        
        Args:
            hostname: Hostname of the deployed application
        
        Returns:
            Locator for the app card
        """
        # STRATEGY 1 (PRIMARY & MOST ROBUST): Use data-testid with hostname
        # This is set in RackCard.svelte as: data-testid="rack-card-{hostname}"
        primary_selector = f'[data-testid="rack-card-{hostname}"]'
        card = self.page.locator(primary_selector)
        
        # Return the primary selector - it's the most reliable
        return card.first
    
    def get_app_status(self, hostname: str) -> str:
        """
        Get the current status of an application.
        
        Uses the data-status attribute for robust, CSS-independent status detection.
        
        Args:
            hostname: Hostname of the application
        
        Returns:
            Status string: 'deploying', 'cloning', 'running', 'stopped', 'error', 'deleting', or 'unknown'
        """
        card = self.get_app_card_by_hostname(hostname)
        
        # PRIMARY STRATEGY: Use data-status attribute (most robust)
        # This is set in RackCard.svelte as: data-status={app.status}
        status_attr = card.get_attribute('data-status')
        
        if status_attr:
            return status_attr
        
        # FALLBACK: Check for status indicators via CSS classes (legacy support)
        if card.locator(self.STATUS_DEPLOYING).count() > 0:
            return 'deploying'
        elif card.locator(self.STATUS_CLONING).count() > 0:
            return 'cloning'
        elif card.locator(self.STATUS_RUNNING).count() > 0:
            return 'running'
        elif card.locator(self.STATUS_STOPPED).count() > 0:
            return 'stopped'
        elif card.locator(self.STATUS_ERROR).count() > 0:
            return 'error'
        else:
            return 'unknown'
    
    def wait_for_status(
        self,
        hostname: str,
        expected_status: str,
        timeout: int = 180000
    ) -> 'AppsPage':
        """
        Wait for an application to reach a specific status.
        
        This is the CRITICAL method for the Golden Path test.
        
        Args:
            hostname: Hostname of the application
            expected_status: Expected status ('running', 'stopped', etc.)
            timeout: Maximum time to wait in milliseconds (default 3 minutes)
        
        Returns:
            self for chaining
        """
        print(f"⏳ Waiting for {hostname} to reach status: {expected_status} (timeout: {timeout}ms)")
        
        card = self.get_app_card_by_hostname(hostname)
        
        # Map status to locator
        status_locators = {
            'deploying': self.STATUS_DEPLOYING,
            'cloning': self.STATUS_CLONING,
            'running': self.STATUS_RUNNING,
            'stopped': self.STATUS_STOPPED,
            'error': self.STATUS_ERROR,
        }
        
        status_locator = status_locators.get(expected_status)
        if not status_locator:
            raise ValueError(f"Unknown status: {expected_status}")
        
        # Wait for the status indicator to appear within the card
        status_element = card.locator(status_locator).first
        expect(status_element).to_be_visible(timeout=timeout)
        
        print(f"✅ {hostname} reached status: {expected_status}")
        return self
    
    def click_start(self, hostname: str) -> 'AppsPage':
        """
        Click the Start button for an application.
        
        Args:
            hostname: Hostname of the application
        
        Returns:
            self for chaining
        """
        card = self.get_app_card_by_hostname(hostname)
        start_button = card.locator(self.START_BUTTON).first
        expect(start_button).to_be_visible(timeout=5000)
        start_button.click()
        return self
    
    def click_stop(self, hostname: str) -> 'AppsPage':
        """
        Click the Stop button for an application.
        
        Args:
            hostname: Hostname of the application
        
        Returns:
            self for chaining
        """
        card = self.get_app_card_by_hostname(hostname)
        stop_button = card.locator(self.STOP_BUTTON).first
        expect(stop_button).to_be_visible(timeout=5000)
        stop_button.click()
        return self
    
    def click_restart(self, hostname: str) -> 'AppsPage':
        """
        Click the Restart button for an application.
        
        Args:
            hostname: Hostname of the application
        
        Returns:
            self for chaining
        """
        card = self.get_app_card_by_hostname(hostname)
        restart_button = card.locator(self.RESTART_BUTTON).first
        expect(restart_button).to_be_visible(timeout=5000)
        restart_button.click()
        return self
    
    def click_delete(self, hostname: str, confirm: bool = True) -> 'AppsPage':
        """
        Click the Delete button for an application.
        
        Args:
            hostname: Hostname of the application
            confirm: Whether to confirm the deletion in the browser's native confirm dialog
        
        Returns:
            self for chaining
        """
        card = self.get_app_card_by_hostname(hostname)
        delete_button = card.locator(self.DELETE_BUTTON).first
        expect(delete_button).to_be_visible(timeout=5000)
        
        if confirm:
            # Handle the browser's native confirm() dialog
            self.page.on("dialog", lambda dialog: dialog.accept())
        else:
            # Dismiss the dialog
            self.page.on("dialog", lambda dialog: dialog.dismiss())
        
        delete_button.click()
        
        # Wait a moment for the deletion to process
        self.page.wait_for_timeout(1000)
        
        return self
    
    def start_app(self, hostname: str, wait_for_running: bool = True) -> 'AppsPage':
        """
        Start an application and optionally wait for it to be running.
        
        Args:
            hostname: Hostname of the application
            wait_for_running: Whether to wait for 'running' status
        
        Returns:
            self for chaining
        """
        self.click_start(hostname)
        if wait_for_running:
            self.wait_for_status(hostname, 'running', timeout=60000)
        return self
    
    def stop_app(self, hostname: str, wait_for_stopped: bool = True) -> 'AppsPage':
        """
        Stop an application and optionally wait for it to be stopped.
        
        Args:
            hostname: Hostname of the application
            wait_for_stopped: Whether to wait for 'stopped' status
        
        Returns:
            self for chaining
        """
        self.click_stop(hostname)
        if wait_for_stopped:
            self.wait_for_status(hostname, 'stopped', timeout=60000)
        return self
    
    def delete_app(self, hostname: str, wait_for_removal: bool = True) -> 'AppsPage':
        """
        Delete an application and optionally wait for it to be removed.
        
        Args:
            hostname: Hostname of the application
            wait_for_removal: Whether to wait for card to disappear
        
        Returns:
            self for chaining
        """
        card = self.get_app_card_by_hostname(hostname)
        self.click_delete(hostname, confirm=True)
        
        if wait_for_removal:
            # Wait for the card to disappear
            expect(card).not_to_be_visible(timeout=30000)
        
        return self
    
    def assert_app_visible(self, hostname: str) -> 'AppsPage':
        """
        Assert that an application card is visible.
        
        Args:
            hostname: Hostname of the application
        
        Returns:
            self for chaining
        """
        card = self.get_app_card_by_hostname(hostname)
        expect(card).to_be_visible(timeout=10000)
        return self
    
    def assert_app_not_visible(self, hostname: str) -> 'AppsPage':
        """
        Assert that an application card is NOT visible.
        
        Args:
            hostname: Hostname of the application
        
        Returns:
            self for chaining
        """
        card = self.get_app_card_by_hostname(hostname)
        expect(card).not_to_be_visible(timeout=10000)
        return self
    
    def assert_status(self, hostname: str, expected_status: str) -> 'AppsPage':
        """
        Assert that an application has a specific status.
        
        Args:
            hostname: Hostname of the application
            expected_status: Expected status
        
        Returns:
            self for chaining
        """
        actual_status = self.get_app_status(hostname)
        assert actual_status == expected_status, \
            f"Expected status '{expected_status}' but got '{actual_status}'"
        return self
    
    def get_app_count(self) -> int:
        """
        Get the number of application cards visible.
        
        Returns:
            Number of app cards
        """
        return self.page.locator(self.APP_CARD).count()
    
    def assert_empty_state(self) -> 'AppsPage':
        """
        Assert that the empty state is visible (no apps deployed).

        Returns:
            self for chaining
        """
        empty_state = self.page.locator(self.EMPTY_STATE).first
        expect(empty_state).to_be_visible(timeout=5000)
        return self

    def flip_card(self, hostname: str) -> 'AppsPage':
        """
        Flip the application card to reveal technical details (3D flip animation).

        This method triggers the 3D flip animation by clicking the info button
        on the rack card. This is part of the "Living Interface" features.

        Args:
            hostname: Hostname of the application

        Returns:
            self for chaining
        """
        card = self.get_app_card_by_hostname(hostname)
        flip_button = card.locator('[data-testid="flip-button"]')
        expect(flip_button).to_be_visible(timeout=5000)
        flip_button.click()

        # Give the animation a moment to start
        self.page.wait_for_timeout(100)

        return self

    def assert_card_is_flipped(self, hostname: str) -> 'AppsPage':
        """
        Assert that the application card is in the flipped state.

        This verifies that the 'is-flipped' CSS class has been applied to the
        card container, which triggers the 3D flip animation. This doesn't test
        the animation itself, but confirms the state management is working.

        Args:
            hostname: Hostname of the application

        Returns:
            self for chaining
        """
        import re

        # Get the card container directly using the data-testid
        # Structure: .card-container[data-testid="rack-card-{hostname}"]
        card_container = self.page.locator(f'[data-testid="rack-card-{hostname}"]')
        
        # Wait for the element to exist
        expect(card_container).to_be_visible(timeout=5000)

        # Assert that the container has the 'is-flipped' class
        expect(card_container).to_have_class(re.compile(r'is-flipped'))

        return self
