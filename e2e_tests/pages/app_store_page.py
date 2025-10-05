"""
Page Object Model for the App Store (Catalog) page.

Handles interactions with the application catalog including
browsing apps and initiating deployments.
"""

import logging
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class AppStorePage(BasePage):
    """
    Page Object for the Proximity App Store (Catalog).
    
    The App Store displays available applications from the catalog
    that can be deployed to the infrastructure.
    """
    
    # Selectors
    CATALOG_VIEW = "#catalogView"
    NAV_CATALOG = "[data-view='catalog']"
    APP_GRID = ".apps-grid"
    APP_CARD = ".app-card"
    APP_NAME = ".app-name"
    APP_CATEGORY = ".app-category"
    APP_DESCRIPTION = ".app-description"
    EMPTY_STATE = ".empty-state"
    SEARCH_INPUT = "#catalogSearch"
    CATEGORY_FILTER = "#categoryFilter"
    
    def __init__(self, page: Page):
        """
        Initialize the AppStorePage.
        
        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
    
    # ========================================================================
    # Properties - Locators for use in expect() assertions
    # ========================================================================
    
    @property
    def catalog_container(self) -> Locator:
        """
        Return the catalog view locator for use in expect() assertions.
        
        Returns:
            Locator for the catalog view container element
        """
        return self.page.locator(self.CATALOG_VIEW)
    
    @property
    def app_grid(self) -> Locator:
        """
        Return the app grid locator.
        
        Returns:
            Locator for the apps grid container
        """
        return self.page.locator(self.APP_GRID)
    
    # ========================================================================
    # Wait Methods
    # ========================================================================
    
    def wait_for_catalog_load(self, timeout: int = 30000) -> None:
        """
        Wait for the catalog view to fully load.
        
        Args:
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info("Waiting for catalog to load")
        self.wait_for_selector(self.CATALOG_VIEW, timeout=timeout)
        self.wait_for_load_state("networkidle", timeout=timeout)
    
    # ========================================================================
    # App Search and Selection Methods
    # ========================================================================
    
    def get_app_card(self, app_name: str) -> Locator:
        """
        Find a specific app card by application name IN THE CATALOG (not deployed apps).
        
        This method returns a Locator for the app card that contains
        the specified app name. The locator specifically targets catalog
        app cards (without .deployed class) to avoid ambiguity with
        deployed apps that may have the same name.
        
        Args:
            app_name: Name of the application (e.g., 'Nginx', 'WordPress')
        
        Returns:
            Locator for the catalog app card containing the app name
        
        Example:
            >>> app_card = app_store_page.get_app_card("Nginx")
            >>> expect(app_card).to_be_visible()
        
        Note:
            Uses :not(.deployed) to exclude deployed app cards from the selection.
            This prevents strict mode violations when multiple apps with the same
            name exist (one in catalog, one or more deployed).
        """
        logger.info(f"Finding catalog app card for: {app_name}")
        # CRITICAL FIX: Use :not(.deployed) to target ONLY catalog cards
        # Catalog cards: <div class="app-card">
        # Deployed cards: <div class="app-card deployed">
        return self.page.locator(f"{self.APP_CARD}:not(.deployed):has({self.APP_NAME}:text-is('{app_name}'))")
    
    def get_all_app_cards(self) -> Locator:
        """
        Get locator for all app cards in the catalog (excludes deployed apps).
        
        Returns:
            Locator for all catalog app cards (can be used with count(), all(), etc.)
        
        Note:
            Uses :not(.deployed) to exclude deployed app cards.
            Only returns catalog app cards without the .deployed class.
        """
        return self.page.locator(f"{self.APP_CARD}:not(.deployed)")
    
    def get_app_card_by_category(self, category: str) -> Locator:
        """
        Find app cards by category IN THE CATALOG (excludes deployed apps).
        
        Args:
            category: Category name (e.g., 'Web Server', 'Database')
        
        Returns:
            Locator for catalog app cards in the specified category
        
        Note:
            Uses :not(.deployed) to target only catalog cards.
        """
        logger.info(f"Finding catalog apps in category: {category}")
        return self.page.locator(f"{self.APP_CARD}:not(.deployed):has({self.APP_CATEGORY}:text-is('{category}'))")
    
    # ========================================================================
    # Deployment Initiation Methods
    # ========================================================================
    
    def click_app_card(self, app_name: str) -> None:
        """
        Click on an app card to open the deployment modal.
        
        This simulates the user clicking on an app card in the catalog,
        which triggers the deployment modal to appear.
        
        Args:
            app_name: Name of the application to deploy
        
        Raises:
            TimeoutError: If the app card is not found or clickable
        """
        logger.info(f"Clicking app card: {app_name}")
        app_card = self.get_app_card(app_name)
        app_card.click()
        logger.info(f"Clicked app card: {app_name}")
    
    def click_deploy_on_app(self, app_name: str) -> None:
        """
        Convenience method to initiate deployment for an app.
        
        This is an alias for click_app_card() since clicking the card
        is what initiates the deployment flow in the UI.
        
        Args:
            app_name: Name of the application to deploy
        """
        self.click_app_card(app_name)
    
    # ========================================================================
    # Search and Filter Methods
    # ========================================================================
    
    def search_apps(self, search_term: str) -> None:
        """
        Search for applications using the search input.
        
        Args:
            search_term: Text to search for
        """
        logger.info(f"Searching for apps: {search_term}")
        search_input = self.page.locator(self.SEARCH_INPUT)
        if search_input.count() > 0:
            search_input.fill(search_term)
            logger.info(f"Entered search term: {search_term}")
        else:
            logger.warning("Search input not found in catalog")
    
    def filter_by_category(self, category: str) -> None:
        """
        Filter apps by category using the category filter.
        
        Args:
            category: Category to filter by
        """
        logger.info(f"Filtering by category: {category}")
        category_filter = self.page.locator(self.CATEGORY_FILTER)
        if category_filter.count() > 0:
            category_filter.select_option(category)
            logger.info(f"Selected category: {category}")
        else:
            logger.warning("Category filter not found in catalog")
    
    # ========================================================================
    # Assertion Helper Methods
    # ========================================================================
    
    def is_app_available(self, app_name: str) -> bool:
        """
        Check if an app is available in the catalog.
        
        Args:
            app_name: Name of the application
        
        Returns:
            True if the app is found, False otherwise
        """
        app_card = self.get_app_card(app_name)
        return app_card.count() > 0
    
    def get_app_count(self) -> int:
        """
        Get the total number of apps in the catalog.
        
        Returns:
            Number of app cards visible
        """
        return self.get_all_app_cards().count()
    
    def is_catalog_empty(self) -> bool:
        """
        Check if the catalog is empty (shows empty state).
        
        Returns:
            True if empty state is visible, False otherwise
        """
        empty_state = self.page.locator(self.EMPTY_STATE)
        return empty_state.count() > 0 and empty_state.is_visible()
