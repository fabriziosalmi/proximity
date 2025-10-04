"""
Page Object Model for the Dashboard page.

Handles interactions with the main dashboard including
navigation, app list viewing, and basic actions.
"""

import logging
from playwright.sync_api import Page
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class DashboardPage(BasePage):
    """
    Page Object for the Proximity Dashboard.
    
    The dashboard is the main landing page after authentication,
    showing deployed apps and system statistics.
    """
    
    # Selectors
    DASHBOARD_VIEW = "#dashboardView"
    NAV_DASHBOARD = "[data-view='dashboard']"
    NAV_APP_STORE = "[data-view='catalog']"  # The catalog IS the app store
    NAV_SETTINGS = "[data-view='settings']"
    NAV_INFRASTRUCTURE = "[data-view='nodes']"  # Infrastructure view
    USER_MENU = ".user-menu"
    LOGOUT_BUTTON = "text=Logout"
    
    # Dashboard content
    STATS_TOTAL_APPS = ".stat-card:has-text('Total Apps') .stat-value"
    STATS_RUNNING_APPS = ".stat-card:has-text('Running') .stat-value"
    DEPLOYED_APPS_LIST = "#deployedAppsList"
    APP_CARD = ".app-card"
    EMPTY_STATE = ".empty-state"
    
    def __init__(self, page: Page):
        """
        Initialize the DashboardPage.
        
        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
    
    # ========================================================================
    # Properties - Locators for use in expect() assertions
    # ========================================================================
    
    @property
    def dashboard_container(self):
        """
        Return the dashboard view locator for use in expect() assertions.
        
        This property allows tests to use Playwright's auto-retrying assertions
        like: expect(dashboard_page.dashboard_container).to_be_visible()
        
        Returns:
            Locator for the main dashboard container element
        """
        return self.page.locator(self.DASHBOARD_VIEW)
    
    # ========================================================================
    # Wait Methods
    # ========================================================================
    
    def wait_for_dashboard_load(self, timeout: int = 30000) -> None:
        """
        Wait for the dashboard to fully load.
        
        Args:
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info("Waiting for dashboard to load")
        self.wait_for_selector(self.DASHBOARD_VIEW, timeout=timeout)
        self.wait_for_load_state("networkidle", timeout=timeout)
    
    # ========================================================================
    # Navigation Methods
    # ========================================================================
    
    def navigate_to_dashboard(self) -> None:
        """Navigate to the Dashboard page."""
        logger.info("Navigating to Dashboard")
        self.click(self.NAV_DASHBOARD)
        self.wait_for_dashboard_load()
    
    def navigate_to_app_store(self) -> None:
        """Navigate to the App Store page."""
        logger.info("Navigating to App Store")
        self.click(self.NAV_APP_STORE)
        # Wait for view to be visible and CSS transition to complete
        self.page.wait_for_function("""
            () => {
                const el = document.getElementById('catalogView');
                if (!el) return false;
                const style = window.getComputedStyle(el);
                return !el.classList.contains('hidden') && 
                       style.display !== 'none' &&
                       parseFloat(style.opacity) > 0.5;
            }
        """, timeout=15000)
    
    def navigate_to_settings(self) -> None:
        """Navigate to the Settings page."""
        logger.info("Navigating to Settings")
        self.click(self.NAV_SETTINGS)
        self.wait_for_selector("#settingsView")
    
    def navigate_to_infrastructure(self) -> None:
        """Navigate to the Infrastructure page."""
        logger.info("Navigating to Infrastructure")
        self.click(self.NAV_INFRASTRUCTURE)
        self.wait_for_selector("#nodesView", timeout=10000)
    
    def logout(self) -> None:
        """Perform logout action."""
        logger.info("Logging out")
        
        # The logout button is inside a dropdown menu, so we need to open it first
        # Wait for the user menu toggle to be visible and click it
        logger.info("Opening user menu dropdown")
        user_info = self.page.locator(".user-info")
        user_info.wait_for(state="visible", timeout=10000)
        user_info.click()
        
        # Wait for the dropdown menu to appear
        self.wait_for_timeout(500)
        
        # Now click the logout button (it should be visible in the dropdown)
        logger.info("Clicking logout button")
        logout_link = self.page.locator(".user-menu-item.logout")
        logout_link.wait_for(state="visible", timeout=5000)
        logout_link.click()
        
        logger.info("Logout action completed")
    
    # ========================================================================
    # Dashboard Content Methods
    # ========================================================================
    
    def get_total_apps_count(self) -> int:
        """
        Get the total number of apps from the stats card.
        
        Returns:
            Total apps count
        """
        count_text = self.get_text(self.STATS_TOTAL_APPS)
        return int(count_text)
    
    def get_running_apps_count(self) -> int:
        """
        Get the number of running apps from the stats card.
        
        Returns:
            Running apps count
        """
        count_text = self.get_text(self.STATS_RUNNING_APPS)
        return int(count_text)
    
    def get_deployed_apps(self) -> list:
        """
        Get a list of all deployed apps visible on the dashboard.
        
        Returns:
            List of app dictionaries with name, status, and element reference
        """
        apps = []
        app_cards = self.page.locator(self.APP_CARD).all()
        
        for card in app_cards:
            app_name = card.locator(".app-name").text_content()
            app_status = card.locator(".app-status").text_content() if card.locator(".app-status").count() > 0 else "unknown"
            
            apps.append({
                "name": app_name,
                "status": app_status,
                "element": card
            })
        
        logger.info(f"Found {len(apps)} deployed apps")
        return apps
    
    def find_app_card_by_name(self, app_name: str):
        """
        Find a specific app card by name.
        
        Args:
            app_name: Name or hostname of the app
        
        Returns:
            Locator for the app card, or None if not found
        """
        logger.info(f"Finding app card: {app_name}")
        card = self.page.locator(f"{self.APP_CARD}:has-text('{app_name}')").first
        
        if card.count() > 0:
            return card
        return None
    
    def has_deployed_apps(self) -> bool:
        """
        Check if any apps are deployed.
        
        Returns:
            True if apps exist, False otherwise
        """
        return self.count(self.APP_CARD) > 0
    
    # ========================================================================
    # Assertion Helpers
    # ========================================================================
    
    def assert_on_dashboard(self) -> None:
        """Assert that we're on the dashboard page."""
        logger.info("Asserting on dashboard page")
        self.assert_visible(self.DASHBOARD_VIEW)
    
    def assert_app_exists(self, app_name: str) -> None:
        """
        Assert that a specific app exists in the dashboard.
        
        Args:
            app_name: Name or hostname of the app
        """
        logger.info(f"Asserting app exists: {app_name}")
        self.assert_visible(f"{self.APP_CARD}:has-text('{app_name}')")
    
    def assert_app_not_exists(self, app_name: str, timeout: int = 5000) -> None:
        """
        Assert that a specific app does NOT exist in the dashboard.
        
        Args:
            app_name: Name or hostname of the app
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info(f"Asserting app does not exist: {app_name}")
        self.assert_hidden(f"{self.APP_CARD}:has-text('{app_name}')", timeout=timeout)
    
    def assert_empty_state(self) -> None:
        """Assert that the empty state message is visible (no apps deployed)."""
        logger.info("Asserting empty state")
        self.assert_visible(self.EMPTY_STATE)
    
    # ========================================================================
    # App Management Methods (for Lifecycle Testing)
    # ========================================================================
    
    def get_app_card_by_hostname(self, hostname: str):
        """
        Find a specific deployed app card by its hostname.
        
        This is the primary method for locating app cards during lifecycle tests.
        The hostname is unique and reliably identifies the app.
        
        Args:
            hostname: Hostname of the deployed app (e.g., 'nginx-e2e-test-123')
        
        Returns:
            Locator for the app card
        
        Example:
            >>> app_card = dashboard_page.get_app_card_by_hostname("nginx-e2e-123")
            >>> expect(app_card).to_be_visible()
        """
        logger.info(f"Finding app card by hostname: {hostname}")
        # The hostname appears in the app card's connection info or app name
        return self.page.locator(f"{self.APP_CARD}:has-text('{hostname}')")
    
    def get_app_status(self, hostname: str) -> str:
        """
        Get the current status of an app by hostname.
        
        Args:
            hostname: Hostname of the app
        
        Returns:
            Status text (e.g., 'running', 'stopped', 'starting')
        """
        logger.info(f"Getting status for app: {hostname}")
        app_card = self.get_app_card_by_hostname(hostname)
        status_badge = app_card.locator(".status-badge")
        
        if status_badge.count() > 0:
            status_text = status_badge.text_content().strip().lower()
            logger.info(f"App {hostname} status: {status_text}")
            return status_text
        
        logger.warning(f"Status not found for app: {hostname}")
        return "unknown"
    
    def get_app_url(self, hostname: str) -> str:
        """
        Get the access URL for a deployed app.
        
        Args:
            hostname: Hostname of the app
        
        Returns:
            Access URL string
        """
        logger.info(f"Getting URL for app: {hostname}")
        app_card = self.get_app_card_by_hostname(hostname)
        url_link = app_card.locator(".connection-link")
        
        if url_link.count() > 0:
            url = url_link.get_attribute("href") or url_link.text_content()
            logger.info(f"App {hostname} URL: {url}")
            return url
        
        logger.warning(f"URL not found for app: {hostname}")
        return ""
    
    def click_app_action(self, hostname: str, action: str) -> None:
        """
        Click an action button on an app card.
        
        This is the PRIMARY method for controlling apps in lifecycle tests.
        
        Args:
            hostname: Hostname of the app
            action: Action to perform ('start', 'stop', 'restart', 'delete', 'logs', 'console')
        
        Raises:
            ValueError: If action is not recognized
        
        Example:
            >>> dashboard_page.click_app_action("nginx-test", "stop")
            >>> dashboard_page.wait_for_app_status("nginx-test", "stopped")
        """
        logger.info(f"Clicking '{action}' action for app: {hostname}")
        
        # Map actions to their icon names or titles
        action_map = {
            "start": "play",
            "stop": "pause",
            "restart": "refresh-cw",
            "delete": "trash-2",
            "logs": "file-text",
            "console": "terminal",
            "open": "external-link"
        }
        
        if action.lower() not in action_map:
            raise ValueError(f"Unknown action: {action}. Valid actions: {list(action_map.keys())}")
        
        icon_name = action_map[action.lower()]
        
        # Find the app card and then the action button within it
        app_card = self.get_app_card_by_hostname(hostname)
        
        # For delete, it's specifically the trash icon button
        if action.lower() == "delete":
            delete_button = app_card.locator(f"button[title*='Delete'], button.danger:has([data-lucide='{icon_name}'])")
            delete_button.click()
            logger.info(f"Clicked delete button for app: {hostname}")
        else:
            # For other actions, find the button with the matching icon
            action_button = app_card.locator(f"button:has([data-lucide='{icon_name}'])")
            action_button.first.click()
            logger.info(f"Clicked {action} button for app: {hostname}")
    
    def confirm_delete_app(self) -> None:
        """
        Confirm app deletion in the confirmation dialog.
        
        After clicking delete on an app card, a confirmation dialog appears.
        This method clicks the confirm button to proceed with deletion.
        
        Example:
            >>> dashboard_page.click_app_action("nginx-test", "delete")
            >>> dashboard_page.confirm_delete_app()
        """
        logger.info("Confirming app deletion")
        
        # The confirmation might be in a modal or inline
        # Look for common confirmation patterns
        confirm_selectors = [
            "button:has-text('Confirm')",
            "button:has-text('Delete')",
            "button:has-text('Yes')",
            "button.btn-danger:has-text('Delete')",
            ".modal button:has-text('Confirm')"
        ]
        
        for selector in confirm_selectors:
            confirm_button = self.page.locator(selector)
            if confirm_button.count() > 0 and confirm_button.is_visible():
                confirm_button.click()
                logger.info("Delete confirmation clicked")
                return
        
        logger.warning("Delete confirmation button not found")
    
    def wait_for_app_status(self, hostname: str, expected_status: str, timeout: int = 60000) -> None:
        """
        Wait for an app to reach a specific status.
        
        This is a CRITICAL method for lifecycle testing that waits for
        state transitions (e.g., starting -> running, running -> stopped).
        
        Args:
            hostname: Hostname of the app
            expected_status: Expected status text (case-insensitive)
            timeout: Maximum time to wait (milliseconds)
        
        Example:
            >>> dashboard_page.click_app_action("nginx-test", "stop")
            >>> dashboard_page.wait_for_app_status("nginx-test", "stopped", timeout=30000)
        """
        logger.info(f"Waiting for app {hostname} to reach status: {expected_status}")
        
        app_card = self.get_app_card_by_hostname(hostname)
        status_badge = app_card.locator(".status-badge")
        
        # Use Playwright's auto-retrying expect with regex for case-insensitive match
        from playwright.sync_api import expect
        expect(status_badge).to_contain_text(expected_status, timeout=timeout, ignore_case=True)
        
        logger.info(f"✅ App {hostname} reached status: {expected_status}")
    
    def wait_for_app_visible(self, hostname: str, timeout: int = 30000) -> None:
        """
        Wait for an app card to become visible on the dashboard.
        
        Args:
            hostname: Hostname of the app
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info(f"Waiting for app to be visible: {hostname}")
        app_card = self.get_app_card_by_hostname(hostname)
        
        from playwright.sync_api import expect
        expect(app_card).to_be_visible(timeout=timeout)
        
        logger.info(f"✅ App {hostname} is visible")
    
    def wait_for_app_hidden(self, hostname: str, timeout: int = 30000) -> None:
        """
        Wait for an app card to be removed from the dashboard.
        
        This is used after deletion to confirm cleanup.
        
        Args:
            hostname: Hostname of the app
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info(f"Waiting for app to be hidden: {hostname}")
        app_card = self.get_app_card_by_hostname(hostname)
        
        from playwright.sync_api import expect
        expect(app_card).to_be_hidden(timeout=timeout)
        
        logger.info(f"✅ App {hostname} is no longer visible")
    
    def is_app_running(self, hostname: str) -> bool:
        """
        Check if an app is in running status.
        
        Args:
            hostname: Hostname of the app
        
        Returns:
            True if status is 'running', False otherwise
        """
        status = self.get_app_status(hostname)
        return "running" in status.lower()
