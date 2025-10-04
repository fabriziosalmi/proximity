"""
App Canvas Page Object Model for E2E tests.

Provides methods for interacting with the in-app canvas modal,
including opening apps, closing canvas, refreshing, and error handling.
"""

import logging
from typing import Optional
from playwright.sync_api import Page, Locator, expect, FrameLocator

from .base_page import BasePage

logger = logging.getLogger(__name__)


class AppCanvasPage(BasePage):
    """
    Page Object Model for the In-App Canvas modal.
    
    This page object handles interactions with the canvas modal
    that displays applications in an embedded iframe.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the App Canvas page.
        
        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
        
        # Canvas Modal Selectors
        self.canvas_modal = "#canvasModal"
        self.canvas_modal_content = ".canvas-modal-content"
        self.canvas_app_name = "#canvasAppName"
        self.canvas_iframe = "#canvasIframe"
        self.canvas_loading = "#canvasLoading"
        self.canvas_error = "#canvasError"
        self.canvas_error_message = "#canvasErrorMessage"
        
        # Canvas Action Buttons
        self.open_in_new_tab_btn = "button[onclick='openInNewTab()']"
        self.refresh_btn = "button[onclick='refreshCanvas()']"
        self.close_btn = "button[onclick='closeCanvas()']"
        
        # App Card Selectors
        self.app_card = ".app-card.deployed"
        self.canvas_button = "button[title='Open in Canvas']"
    
    # ========================================================================
    # Canvas Modal Interaction Methods
    # ========================================================================
    
    def open_app_canvas(self, app_name: str, timeout: int = 10000) -> None:
        """
        Open an application in the canvas modal by clicking its canvas button.
        
        Args:
            app_name: Name of the application to open
            timeout: Max time to wait for canvas to open (ms)
        """
        logger.info(f"Opening app canvas for: {app_name}")
        
        # Find the app card containing the app name
        app_card = self.page.locator(self.app_card).filter(has_text=app_name).first
        
        # Click the canvas button in that app card
        canvas_btn = app_card.locator(self.canvas_button)
        expect(canvas_btn).to_be_visible(timeout=timeout)
        canvas_btn.click()
        
        # Wait for modal to appear
        self.wait_for_canvas_modal_visible(timeout=timeout)
    
    def open_app_canvas_by_index(self, index: int = 0, timeout: int = 10000) -> None:
        """
        Open an application canvas by index (useful when app name is unknown).
        
        Args:
            index: Index of the app card (0-based)
            timeout: Max time to wait for canvas to open (ms)
        """
        logger.info(f"Opening app canvas by index: {index}")
        
        # Get all app cards with canvas buttons
        app_cards = self.page.locator(self.app_card).filter(has=self.page.locator(self.canvas_button))
        
        # Click the canvas button in the specified card
        canvas_btn = app_cards.nth(index).locator(self.canvas_button)
        expect(canvas_btn).to_be_visible(timeout=timeout)
        canvas_btn.click()
        
        # Wait for modal to appear
        self.wait_for_canvas_modal_visible(timeout=timeout)
    
    def close_canvas(self, timeout: int = 5000) -> None:
        """
        Close the canvas modal using the close button.
        
        Args:
            timeout: Max time to wait for modal to close (ms)
        """
        logger.info("Closing canvas modal")
        
        # Click close button
        close_button = self.page.locator(self.close_btn)
        expect(close_button).to_be_visible(timeout=timeout)
        close_button.click()
        
        # Wait for modal to disappear
        self.wait_for_canvas_modal_hidden(timeout=timeout)
    
    def close_canvas_by_escape(self, timeout: int = 5000) -> None:
        """
        Close the canvas modal by pressing Escape key.
        
        Args:
            timeout: Max time to wait for modal to close (ms)
        """
        logger.info("Closing canvas modal with Escape key")
        
        # Press Escape
        self.page.keyboard.press("Escape")
        
        # Wait for modal to disappear
        self.wait_for_canvas_modal_hidden(timeout=timeout)
    
    def close_canvas_by_clicking_outside(self, timeout: int = 5000) -> None:
        """
        Close the canvas modal by clicking outside the content area.
        
        Args:
            timeout: Max time to wait for modal to close (ms)
        """
        logger.info("Closing canvas modal by clicking outside")
        
        # Click on the modal backdrop (not the content)
        modal = self.page.locator(self.canvas_modal)
        modal.click(position={"x": 10, "y": 10})  # Click top-left corner
        
        # Wait for modal to disappear
        self.wait_for_canvas_modal_hidden(timeout=timeout)
    
    def refresh_canvas(self, timeout: int = 10000) -> None:
        """
        Refresh the canvas iframe.
        
        Args:
            timeout: Max time to wait for refresh to complete (ms)
        """
        logger.info("Refreshing canvas")
        
        # Click refresh button
        refresh_button = self.page.locator(self.refresh_btn)
        expect(refresh_button).to_be_visible(timeout=timeout)
        refresh_button.click()
        
        # Wait for loading state to appear and disappear
        self.wait_for_canvas_loading()
        self.wait_for_canvas_loaded(timeout=timeout)
    
    def open_in_new_tab(self) -> None:
        """
        Click the 'Open in New Tab' button.
        
        Note: This will open a new browser tab. Tests should handle
        the new context appropriately.
        """
        logger.info("Opening app in new tab")
        
        open_tab_button = self.page.locator(self.open_in_new_tab_btn)
        expect(open_tab_button).to_be_visible()
        open_tab_button.click()
    
    # ========================================================================
    # Canvas State Checking Methods
    # ========================================================================
    
    def is_canvas_modal_visible(self) -> bool:
        """
        Check if the canvas modal is currently visible.
        
        Returns:
            True if modal is visible, False otherwise
        """
        modal = self.page.locator(self.canvas_modal)
        return modal.evaluate("el => el.classList.contains('show')")
    
    def is_canvas_loading(self) -> bool:
        """
        Check if the canvas is in loading state.
        
        Returns:
            True if loading, False otherwise
        """
        loading = self.page.locator(self.canvas_loading)
        return loading.is_visible()
    
    def is_canvas_error_visible(self) -> bool:
        """
        Check if the canvas error state is visible.
        
        Returns:
            True if error is visible, False otherwise
        """
        error = self.page.locator(self.canvas_error)
        return error.is_visible() and not error.evaluate("el => el.classList.contains('hidden')")
    
    def is_canvas_iframe_visible(self) -> bool:
        """
        Check if the canvas iframe is visible and loaded.
        
        Returns:
            True if iframe is visible, False otherwise
        """
        iframe = self.page.locator(self.canvas_iframe)
        return iframe.is_visible() and not iframe.evaluate("el => el.classList.contains('hidden')")
    
    # ========================================================================
    # Canvas Content Methods
    # ========================================================================
    
    def get_canvas_app_name(self) -> str:
        """
        Get the displayed app name in the canvas header.
        
        Returns:
            App name as displayed in canvas header
        """
        app_name_element = self.page.locator(self.canvas_app_name)
        expect(app_name_element).to_be_visible()
        return app_name_element.text_content()
    
    def get_canvas_error_message(self) -> str:
        """
        Get the error message displayed in the canvas error state.
        
        Returns:
            Error message text
        """
        error_message = self.page.locator(self.canvas_error_message)
        expect(error_message).to_be_visible()
        return error_message.text_content()
    
    def get_canvas_iframe_src(self) -> str:
        """
        Get the src attribute of the canvas iframe.
        
        Returns:
            iframe src URL
        """
        iframe = self.page.locator(self.canvas_iframe)
        expect(iframe).to_be_visible()
        return iframe.get_attribute("src")
    
    def get_canvas_iframe(self) -> FrameLocator:
        """
        Get the canvas iframe as a FrameLocator for interactions.
        
        Returns:
            FrameLocator for the canvas iframe
        """
        return self.page.frame_locator(self.canvas_iframe)
    
    # ========================================================================
    # Wait Methods
    # ========================================================================
    
    def wait_for_canvas_modal_visible(self, timeout: int = 10000) -> None:
        """
        Wait for the canvas modal to become visible.
        
        Args:
            timeout: Max time to wait (ms)
        """
        logger.info("Waiting for canvas modal to be visible")
        modal = self.page.locator(self.canvas_modal)
        modal.wait_for(state="visible", timeout=timeout)
        expect(modal).to_have_class("modal canvas-modal show", timeout=timeout)
    
    def wait_for_canvas_modal_hidden(self, timeout: int = 5000) -> None:
        """
        Wait for the canvas modal to be hidden.
        
        Args:
            timeout: Max time to wait (ms)
        """
        logger.info("Waiting for canvas modal to be hidden")
        modal = self.page.locator(self.canvas_modal)
        
        # Wait for 'show' class to be removed
        self.page.wait_for_function(
            "() => !document.getElementById('canvasModal').classList.contains('show')",
            timeout=timeout
        )
    
    def wait_for_canvas_loading(self, timeout: int = 2000) -> None:
        """
        Wait for the canvas loading state to appear.
        
        Args:
            timeout: Max time to wait (ms)
        """
        logger.info("Waiting for canvas loading state")
        loading = self.page.locator(self.canvas_loading)
        loading.wait_for(state="visible", timeout=timeout)
    
    def wait_for_canvas_loaded(self, timeout: int = 15000) -> None:
        """
        Wait for the canvas to finish loading (iframe visible or error shown).
        
        Args:
            timeout: Max time to wait (ms)
        """
        logger.info("Waiting for canvas to load")
        
        # Wait for either iframe to be visible or error to be shown
        self.page.wait_for_function(
            """() => {
                const iframe = document.getElementById('canvasIframe');
                const error = document.getElementById('canvasError');
                return (!iframe.classList.contains('hidden')) || 
                       (!error.classList.contains('hidden'));
            }""",
            timeout=timeout
        )
    
    def wait_for_canvas_error(self, timeout: int = 15000) -> None:
        """
        Wait for the canvas error state to appear.
        
        Args:
            timeout: Max time to wait (ms)
        """
        logger.info("Waiting for canvas error state")
        error = self.page.locator(self.canvas_error)
        
        # Wait for error to be visible and not have 'hidden' class
        self.page.wait_for_function(
            """() => {
                const error = document.getElementById('canvasError');
                return error && !error.classList.contains('hidden');
            }""",
            timeout=timeout
        )
    
    # ========================================================================
    # Assertion Helpers
    # ========================================================================
    
    def assert_canvas_modal_open(self) -> None:
        """Assert that the canvas modal is open and visible."""
        logger.info("Asserting canvas modal is open")
        modal = self.page.locator(self.canvas_modal)
        expect(modal).to_have_class("modal canvas-modal show")
    
    def assert_canvas_modal_closed(self) -> None:
        """Assert that the canvas modal is closed."""
        logger.info("Asserting canvas modal is closed")
        modal = self.page.locator(self.canvas_modal)
        expect(modal).not_to_have_class("show")
    
    def assert_canvas_app_name(self, expected_name: str) -> None:
        """
        Assert that the canvas displays the correct app name.
        
        Args:
            expected_name: Expected app name to be displayed
        """
        logger.info(f"Asserting canvas app name is: {expected_name}")
        app_name = self.get_canvas_app_name()
        assert app_name == expected_name, f"Expected '{expected_name}', got '{app_name}'"
    
    def assert_canvas_loaded(self) -> None:
        """Assert that the canvas iframe has loaded successfully."""
        logger.info("Asserting canvas has loaded")
        assert self.is_canvas_iframe_visible(), "Canvas iframe should be visible"
        assert not self.is_canvas_loading(), "Canvas should not be in loading state"
        assert not self.is_canvas_error_visible(), "Canvas should not show error"
    
    def assert_canvas_error_shown(self) -> None:
        """Assert that the canvas is showing an error state."""
        logger.info("Asserting canvas is showing error")
        assert self.is_canvas_error_visible(), "Canvas error should be visible"
        assert not self.is_canvas_iframe_visible(), "Canvas iframe should not be visible"
    
    def assert_canvas_button_exists(self, app_name: str) -> None:
        """
        Assert that a canvas button exists for the specified app.
        
        Args:
            app_name: Name of the app to check
        """
        logger.info(f"Asserting canvas button exists for: {app_name}")
        app_card = self.page.locator(self.app_card).filter(has_text=app_name).first
        canvas_btn = app_card.locator(self.canvas_button)
        expect(canvas_btn).to_be_visible()
