"""
Store Page Object Model

Encapsulates all interactions with the App Store/Catalog page.
"""
from playwright.sync_api import Page, expect, Locator
from typing import Optional
import time
import re


class StorePage:
    """
    Page Object for the App Store page (/store).
    
    This page displays the catalog of available applications
    and provides deployment functionality.
    """
    
    # Locators
    SEARCH_INPUT = 'input[type="search"], input[placeholder*="Search" i]'
    CATEGORY_FILTER = '.category-filter, [data-testid="category-filter"]'
    # Use data-testid pattern for catalog cards (format: catalog-card-{app.id})
    APP_CARD = '[data-testid^="catalog-card-"]'
    APP_CARD_TITLE = '.app-title, h3, h4'
    DEPLOY_BUTTON = 'button:has-text("Deploy"), button:has-text("🚀 Deploy"), button:has-text("Install")'
    
    # Deployment Modal
    MODAL = '.modal, [role="dialog"], .deployment-modal'
    HOSTNAME_INPUT = 'input[name="hostname"], input[placeholder*="hostname" i]'
    MODAL_DEPLOY_BUTTON = '.modal button:has-text("Deploy"), [role="dialog"] button:has-text("Deploy")'
    MODAL_CANCEL_BUTTON = '.modal button:has-text("Cancel"), [role="dialog"] button:has-text("Cancel")'
    MODAL_CLOSE_BUTTON = '.modal-close, button[aria-label="Close"]'
    
    # Loading states
    LOADING_INDICATOR = '.loading, .spinner, [data-loading="true"]'
    TOAST_NOTIFICATION = '.toast, .notification, [role="alert"]'
    
    def __init__(self, page: Page, base_url: str):
        """
        Initialize the StorePage.
        
        Args:
            page: Playwright Page object
            base_url: Base URL of the application
        """
        self.page = page
        self.base_url = base_url
    
    def navigate(self) -> 'StorePage':
        """Navigate to the store page."""
        self.page.goto(f"{self.base_url}/store")
        # Wait for page to be fully loaded
        self.page.wait_for_load_state("networkidle")
        return self
    
    def search(self, query: str) -> 'StorePage':
        """
        Search for applications.
        
        Args:
            query: Search query string
        
        Returns:
            self for chaining
        """
        search_input = self.page.locator(self.SEARCH_INPUT).first
        search_input.fill(query)
        # Wait a moment for client-side filtering
        self.page.wait_for_timeout(500)
        return self
    
    def get_app_card(self, app_name: str) -> Locator:
        """
        Get the card element for a specific application.
        
        Args:
            app_name: Name of the application (case-insensitive)
        
        Returns:
            Locator for the app card
        """
        # Find the card that contains the app name
        all_cards = self.page.locator(self.APP_CARD)
        
        # Iterate through cards to find the one with matching title
        for i in range(all_cards.count()):
            card = all_cards.nth(i)
            title = card.locator(self.APP_CARD_TITLE).first
            if title.count() > 0:
                title_text = title.inner_text().strip()
                if app_name.lower() in title_text.lower():
                    return card
        
        # If not found, return a generic locator that will fail gracefully
        return self.page.locator(f'{self.APP_CARD}:has-text("{app_name}")').first
    
    def click_deploy(self, app_name: str) -> 'StorePage':
        """
        Click the deploy button for a specific application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            self for chaining
        """
        app_card = self.get_app_card(app_name)
        deploy_button = app_card.locator(self.DEPLOY_BUTTON).first
        
        expect(deploy_button).to_be_visible(timeout=5000)
        deploy_button.click()
        
        # Wait for modal to appear
        expect(self.page.locator(self.MODAL).first).to_be_visible(timeout=5000)
        
        return self
    
    def fill_hostname(self, hostname: str) -> 'StorePage':
        """
        Fill in the hostname field in the deployment modal.
        
        Args:
            hostname: Hostname to use for the deployment
        
        Returns:
            self for chaining
        """
        hostname_input = self.page.locator(self.HOSTNAME_INPUT).first
        expect(hostname_input).to_be_visible(timeout=5000)
        hostname_input.clear()  # Clear existing value first
        hostname_input.fill(hostname)
        return self
    
    def confirm_deployment(self, wait_for_redirect: bool = True) -> 'StorePage':
        """
        Click the deploy button in the modal to confirm deployment.
        
        Args:
            wait_for_redirect: Whether to wait for redirect to /apps page
        
        Returns:
            self for chaining
        """
        modal_deploy_button = self.page.locator(self.MODAL_DEPLOY_BUTTON).first
        expect(modal_deploy_button).to_be_visible(timeout=5000)
        
        # Click the button (deployment is async, navigation happens after API call)
        modal_deploy_button.click()
        
        if wait_for_redirect:
            # Wait for navigation to /apps page after successful deployment
            # This happens asynchronously after the API call completes
            expect(self.page).to_have_url(re.compile(r".*/apps/?$"), timeout=30000)
        
        return self
    
    def deploy_app(
        self,
        app_name: str,
        hostname: str,
        wait_for_redirect: bool = True
    ) -> 'StorePage':
        """
        Complete the full deployment flow for an application.
        
        Args:
            app_name: Name of the application to deploy
            hostname: Hostname to use for the deployment
            wait_for_redirect: Whether to wait for redirect to /apps page
        
        Returns:
            self for chaining
        """
        self.click_deploy(app_name)
        self.fill_hostname(hostname)
        self.confirm_deployment(wait_for_redirect)
        return self
    
    def assert_app_visible(self, app_name: str) -> 'StorePage':
        """
        Assert that an application is visible in the catalog.
        
        Args:
            app_name: Name of the application
        
        Returns:
            self for chaining
        """
        app_card = self.get_app_card(app_name)
        expect(app_card).to_be_visible(timeout=10000)
        return self
    
    def assert_modal_open(self) -> 'StorePage':
        """
        Assert that the deployment modal is open.
        
        Returns:
            self for chaining
        """
        modal = self.page.locator(self.MODAL).first
        expect(modal).to_be_visible(timeout=5000)
        return self
    
    def assert_toast_visible(self, message: Optional[str] = None) -> 'StorePage':
        """
        Assert that a toast notification is visible.
        
        Args:
            message: Optional specific message to match
        
        Returns:
            self for chaining
        """
        toast = self.page.locator(self.TOAST_NOTIFICATION).first
        expect(toast).to_be_visible(timeout=5000)
        
        if message:
            expect(toast).to_contain_text(message)
        
        return self
    
    def get_app_count(self) -> int:
        """
        Get the number of applications visible in the catalog.
        
        Returns:
            Number of app cards visible
        """
        return self.page.locator(self.APP_CARD).count()
    
    def wait_for_apps_loaded(self, min_count: int = 1, timeout: int = 10000) -> 'StorePage':
        """
        Wait for applications to be loaded and visible.
        
        Args:
            min_count: Minimum number of apps expected
            timeout: Maximum time to wait in milliseconds
        
        Returns:
            self for chaining
        """
        # Wait for at least one catalog card with specific data-testid pattern
        # This is more reliable than document.querySelectorAll
        self.page.locator('[data-testid^="catalog-card-"]').first.wait_for(
            state="visible",
            timeout=timeout
        )
        
        # Verify we have at least min_count apps
        actual_count = self.page.locator('[data-testid^="catalog-card-"]').count()
        if actual_count < min_count:
            raise AssertionError(
                f"Expected at least {min_count} apps, but found {actual_count}"
            )
        
        return self
