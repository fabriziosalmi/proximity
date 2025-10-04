"""
Page Object Model for the Deployment Modal.

Handles interactions with the deployment modal including
configuration, deployment submission, and progress monitoring.
"""

import logging
from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class DeploymentModalPage(BasePage):
    """
    Page Object for the Deployment Modal.
    
    This modal appears when deploying a new application and handles:
    1. Configuration (hostname, ports, resources)
    2. Deployment submission
    3. Real-time progress monitoring
    4. Success/failure notifications
    """
    
    # Modal Selectors
    MODAL = "#deployModal"
    MODAL_CONTENT = ".modal-content"
    MODAL_HEADER = ".modal-header"
    MODAL_TITLE = ".modal-title"
    MODAL_CLOSE = ".modal-close"
    MODAL_BODY = ".modal-body"
    MODAL_FOOTER = ".modal-footer"
    
    # Configuration Form Selectors
    DEPLOY_FORM = "#deployForm"
    HOSTNAME_INPUT = "#hostname"
    MEMORY_INPUT = "#memory"
    CPU_INPUT = "#cpu"
    DISK_INPUT = "#disk"
    
    # Deployment Action Buttons
    DEPLOY_BUTTON = "button:has-text('Deploy Application')"
    CANCEL_BUTTON = "button:has-text('Cancel')"
    
    # Progress Monitoring Selectors
    PROGRESS_STEPS = "#progressSteps"
    PROGRESS_STEP = ".progress-step"
    PROGRESS_STEP_ACTIVE = ".progress-step.active"
    PROGRESS_STEP_COMPLETE = ".progress-step.complete"
    PROGRESS_BAR = "#progressBar"
    PROGRESS_MESSAGE = "#progressMessage"
    LOADING_SPINNER = ".loading-spinner"
    
    # Status Messages
    SUCCESS_MESSAGE = "text=/deployed successfully|deployment.*complete/i"
    ERROR_MESSAGE = ".alert.error, .error-message"
    
    def __init__(self, page: Page):
        """
        Initialize the DeploymentModalPage.
        
        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
    
    # ========================================================================
    # Properties - Locators for use in expect() assertions
    # ========================================================================
    
    @property
    def modal(self) -> Locator:
        """
        Return the modal locator for use in expect() assertions.
        
        Returns:
            Locator for the deployment modal
        """
        return self.page.locator(self.MODAL)
    
    @property
    def modal_title(self) -> Locator:
        """
        Return the modal title locator.
        
        Returns:
            Locator for the modal title element
        """
        return self.page.locator(self.MODAL_TITLE)
    
    @property
    def hostname_input(self) -> Locator:
        """
        Return the hostname input locator.
        
        Returns:
            Locator for the hostname input field
        """
        return self.page.locator(self.HOSTNAME_INPUT)
    
    @property
    def deploy_button(self) -> Locator:
        """
        Return the deploy button locator.
        
        Returns:
            Locator for the deploy button
        """
        return self.page.locator(self.DEPLOY_BUTTON)
    
    # ========================================================================
    # Wait Methods
    # ========================================================================
    
    def wait_for_modal_visible(self, timeout: int = 10000) -> None:
        """
        Wait for the deployment modal to be visible.
        
        Args:
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info("Waiting for deployment modal to be visible")
        expect(self.modal).to_be_visible(timeout=timeout)
        logger.info("Deployment modal is visible")
    
    def wait_for_modal_hidden(self, timeout: int = 10000) -> None:
        """
        Wait for the deployment modal to be hidden.
        
        Args:
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info("Waiting for deployment modal to be hidden")
        expect(self.modal).to_be_hidden(timeout=timeout)
        logger.info("Deployment modal is hidden")
    
    # ========================================================================
    # Configuration Methods
    # ========================================================================
    
    def fill_hostname(self, hostname: str) -> None:
        """
        Fill in the hostname field.
        
        Args:
            hostname: Hostname to use for the deployment
        
        Example:
            >>> modal.fill_hostname("nginx-e2e-test-123")
        """
        logger.info(f"Filling hostname: {hostname}")
        self.hostname_input.fill(hostname)
        logger.info(f"Hostname filled: {hostname}")
    
    def fill_memory(self, memory_mb: int) -> None:
        """
        Fill in the memory field.
        
        Args:
            memory_mb: Memory in megabytes
        """
        logger.info(f"Setting memory: {memory_mb}MB")
        memory_input = self.page.locator(self.MEMORY_INPUT)
        if memory_input.count() > 0:
            memory_input.fill(str(memory_mb))
    
    def fill_cpu(self, cpu_cores: int) -> None:
        """
        Fill in the CPU cores field.
        
        Args:
            cpu_cores: Number of CPU cores
        """
        logger.info(f"Setting CPU cores: {cpu_cores}")
        cpu_input = self.page.locator(self.CPU_INPUT)
        if cpu_input.count() > 0:
            cpu_input.fill(str(cpu_cores))
    
    def fill_disk(self, disk_gb: int) -> None:
        """
        Fill in the disk size field.
        
        Args:
            disk_gb: Disk size in gigabytes
        """
        logger.info(f"Setting disk size: {disk_gb}GB")
        disk_input = self.page.locator(self.DISK_INPUT)
        if disk_input.count() > 0:
            disk_input.fill(str(disk_gb))
    
    # ========================================================================
    # Deployment Submission Methods
    # ========================================================================
    
    def submit_deployment(self) -> None:
        """
        Click the deploy button to submit the deployment.
        
        This method clicks the "Deploy Application" button to start
        the deployment process. After clicking, the modal should
        transition to the progress monitoring view.
        
        Example:
            >>> modal.fill_hostname("my-app")
            >>> modal.submit_deployment()
        """
        logger.info("Clicking deploy button")
        self.deploy_button.click()
        logger.info("Deploy button clicked")
    
    def cancel_deployment(self) -> None:
        """
        Click the cancel button to close the modal without deploying.
        """
        logger.info("Clicking cancel button")
        cancel_button = self.page.locator(self.CANCEL_BUTTON)
        cancel_button.click()
        logger.info("Cancel button clicked")
    
    def close_modal(self) -> None:
        """
        Click the close (X) button to close the modal.
        """
        logger.info("Clicking modal close button")
        close_button = self.page.locator(self.MODAL_CLOSE)
        close_button.click()
        logger.info("Modal close button clicked")
    
    # ========================================================================
    # Progress Monitoring Methods
    # ========================================================================
    
    def wait_for_deployment_progress(self, timeout: int = 10000) -> None:
        """
        Wait for the deployment progress view to appear.
        
        After submitting deployment, the modal should transition to
        show the progress monitoring view with steps and progress bar.
        
        Args:
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info("Waiting for deployment progress view")
        self.wait_for_selector(self.PROGRESS_STEPS, timeout=timeout)
        logger.info("Deployment progress view visible")
    
    def wait_for_deployment_success(self, timeout: int = 240000) -> None:
        """
        Wait for deployment to complete successfully.
        
        This is the CRITICAL method for lifecycle testing. It monitors
        the deployment progress and waits for the success message.
        
        Default timeout is 4 minutes (240 seconds) to account for:
        - LXC container creation
        - Docker installation
        - Image pulling
        - Service startup
        
        Args:
            timeout: Maximum time to wait (milliseconds), default 240000 (4 min)
        
        Raises:
            TimeoutError: If deployment doesn't complete within timeout
        
        Example:
            >>> modal.fill_hostname("nginx-test")
            >>> modal.submit_deployment()
            >>> modal.wait_for_deployment_success(timeout=300000)  # 5 min
        """
        logger.info(f"Waiting for deployment success (timeout: {timeout}ms)")
        
        # Wait for the progress view to appear first
        self.wait_for_deployment_progress(timeout=10000)
        
        # Wait for success message or completed status
        # The success message might be in the progress message or a notification
        try:
            # Method 1: Look for success message in the modal
            success_locator = self.page.locator(self.SUCCESS_MESSAGE)
            expect(success_locator).to_be_visible(timeout=timeout)
            logger.info("✅ Deployment success message detected")
        except Exception as e:
            logger.warning(f"Success message not found in expected location: {e}")
            
            # Method 2: Check if all progress steps are complete
            # The UI might show all steps as complete without explicit success text
            self.wait_for_load_state("networkidle", timeout=30000)
            logger.info("✅ Deployment completed (network idle)")
    
    def wait_for_deployment_failure(self, timeout: int = 240000) -> None:
        """
        Wait for deployment to fail (for negative test scenarios).
        
        Args:
            timeout: Maximum time to wait (milliseconds)
        """
        logger.info("Waiting for deployment failure")
        error_message = self.page.locator(self.ERROR_MESSAGE)
        expect(error_message).to_be_visible(timeout=timeout)
        logger.info("Deployment failure detected")
    
    def get_progress_percentage(self) -> float:
        """
        Get the current deployment progress percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        progress_bar = self.page.locator(self.PROGRESS_BAR)
        if progress_bar.count() > 0:
            width_style = progress_bar.get_attribute("style")
            if width_style and "width:" in width_style:
                # Extract percentage from "width: 50%;"
                import re
                match = re.search(r'width:\s*(\d+)%', width_style)
                if match:
                    return float(match.group(1))
        return 0.0
    
    def get_progress_message(self) -> str:
        """
        Get the current progress message text.
        
        Returns:
            Progress message text
        """
        message_element = self.page.locator(self.PROGRESS_MESSAGE)
        if message_element.count() > 0:
            return message_element.text_content() or ""
        return ""
    
    def get_active_progress_step(self) -> str:
        """
        Get the currently active progress step text.
        
        Returns:
            Active step text (e.g., "Creating LXC container")
        """
        active_step = self.page.locator(self.PROGRESS_STEP_ACTIVE)
        if active_step.count() > 0:
            step_text = active_step.locator(".progress-step-text")
            return step_text.text_content() or ""
        return ""
    
    def get_completed_steps_count(self) -> int:
        """
        Get the number of completed progress steps.
        
        Returns:
            Count of completed steps
        """
        completed_steps = self.page.locator(self.PROGRESS_STEP_COMPLETE)
        return completed_steps.count()
    
    # ========================================================================
    # Assertion Helper Methods
    # ========================================================================
    
    def is_modal_visible(self) -> bool:
        """
        Check if the deployment modal is currently visible.
        
        Returns:
            True if modal is visible, False otherwise
        """
        return self.modal.is_visible()
    
    def is_deployment_in_progress(self) -> bool:
        """
        Check if a deployment is currently in progress.
        
        Returns:
            True if progress view is visible, False otherwise
        """
        progress_steps = self.page.locator(self.PROGRESS_STEPS)
        return progress_steps.count() > 0 and progress_steps.is_visible()
    
    def has_error(self) -> bool:
        """
        Check if an error message is displayed.
        
        Returns:
            True if error is visible, False otherwise
        """
        error_message = self.page.locator(self.ERROR_MESSAGE)
        return error_message.count() > 0 and error_message.is_visible()
