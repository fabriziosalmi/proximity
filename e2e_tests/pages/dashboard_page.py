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
    NAV_APP_STORE = "[data-view='appStore']"
    NAV_SETTINGS = "[data-view='settings']"
    NAV_INFRASTRUCTURE = "[data-view='infrastructure']"
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
        self.wait_for_selector("#appStoreView")
    
    def navigate_to_settings(self) -> None:
        """Navigate to the Settings page."""
        logger.info("Navigating to Settings")
        self.click(self.NAV_SETTINGS)
        self.wait_for_selector("#settingsView")
    
    def navigate_to_infrastructure(self) -> None:
        """Navigate to the Infrastructure page."""
        logger.info("Navigating to Infrastructure")
        self.click(self.NAV_INFRASTRUCTURE)
        self.wait_for_selector("#infrastructureView")
    
    def logout(self) -> None:
        """Perform logout action."""
        logger.info("Logging out")
        
        # Click user menu if it's a dropdown
        if self.is_visible(self.USER_MENU):
            self.click(self.USER_MENU)
            self.wait_for_timeout(500)
        
        # Click logout button
        self.click(self.LOGOUT_BUTTON)
        
        # Wait for auth modal to reappear
        self.wait_for_selector("#authModal", timeout=10000)
        logger.info("Logout successful")
    
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
