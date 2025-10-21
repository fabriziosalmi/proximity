"""
Bulletproof Programmatic Authentication for E2E Tests

This module provides a robust, reusable authentication strategy that guarantees
the frontend ApiClient is fully initialized and authenticated before any test
interactions occur.
"""
import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def programmatic_login(page: Page, auth_token: str, base_url: str = "http://localhost:5173", initial_page: str = "/") -> None:
    """
    Perform bulletproof programmatic login by:
    1. Injecting the auth token into localStorage before any page loads
    2. Navigating to the specified initial page
    3. Waiting for explicit confirmation that the ApiClient is ready
    
    This eliminates race conditions and ensures all subsequent API calls
    will be authenticated.
    
    Args:
        page: Playwright Page instance
        auth_token: JWT authentication token from user fixture
        base_url: Base URL of the frontend application
        initial_page: Initial page to navigate to (default: "/" for homepage)
        
    Raises:
        TimeoutError: If ApiClient doesn't signal readiness within 10 seconds
    """
    logger.info("🔐 [AUTH] Starting bulletproof programmatic login...")
    
    # Step 1: Inject token into localStorage BEFORE any navigation
    # This ensures the token is available when the ApiClient initializes
    page.add_init_script(f"""
        // Store auth token in localStorage
        window.localStorage.setItem('access_token', '{auth_token}');
        console.log('🔑 [E2E] Auth token injected into localStorage');
    """)
    logger.info(f"  ✓ Token injection script registered")
    
    # Step 2: Navigate to the initial page
    # The add_init_script will execute before the page loads
    target_url = f"{base_url}{initial_page}"
    logger.info(f"  → Navigating to {target_url}")
    page.goto(target_url, wait_until="domcontentloaded")
    
    # Step 3: Wait for the ApiClient to signal it's ready
    # This is the critical step that ensures authentication is complete
    try:
        # Wait a moment for the ApiClient module to load and initialize
        page.wait_for_timeout(500)
        
        # Check the current auth state
        auth_status = page.evaluate("""
            () => {
                return {
                    hasToken: !!localStorage.getItem('access_token'),
                    tokenPrefix: (localStorage.getItem('access_token') || '').substring(0, 20),
                    apiReady: document.body.getAttribute('data-api-client-ready'),
                    url: window.location.href
                };
            }
        """)
        logger.info(f"  → Auth status: token={auth_status['hasToken']}, ready={auth_status['apiReady']}")
        
        # Wait for the ready signal with a reasonable timeout
        page.wait_for_selector(
            'body[data-api-client-ready="true"]',
            timeout=10000,
            state="attached"
        )
        logger.info("  ✅ ApiClient confirmed ready for authenticated requests")
        
        # Verify the token is actually in localStorage
        has_token = page.evaluate('!!localStorage.getItem("access_token")')
        if not has_token:
            raise RuntimeError("Token was lost from localStorage!")
            
    except Exception as e:
        logger.error(f"  ❌ ApiClient failed to become ready: {e}")
        # Log detailed page state for debugging
        logger.error(f"  → Current URL: {page.url}")
        ready_attr = page.evaluate('document.body.getAttribute("data-api-client-ready")')
        logger.error(f"  → Body attribute: {ready_attr}")
        token_exists = page.evaluate('!!localStorage.getItem("access_token")')
        logger.error(f"  → Has token in localStorage: {token_exists}")
        
        # Get console logs
        console_logs = page.evaluate("""
            () => {
                // Try to get any ApiClient logs
                return window.__e2e_logs || 'No logs captured';
            }
        """)
        logger.error(f"  → Console context: {console_logs}")
        
        raise TimeoutError(
            f"ApiClient did not signal readiness within 10 seconds. "
            f"Ready attribute: {ready_attr}, Has token: {token_exists}"
        ) from e
    
    logger.info("🎉 [AUTH] Programmatic login completed successfully!")


def wait_for_auth_ready(page: Page, timeout: int = 5000) -> None:
    """
    Wait for the ApiClient to be ready for authenticated requests.
    
    Use this if you need to re-verify auth state after navigation
    or when auth token might have been refreshed.
    
    Args:
        page: Playwright Page instance
        timeout: Maximum time to wait in milliseconds (default: 5000)
    """
    try:
        page.wait_for_selector(
            'body[data-api-client-ready="true"]',
            timeout=timeout,
            state="attached"
        )
        logger.debug("✅ [AUTH] ApiClient auth state verified")
    except Exception as e:
        logger.warning(f"⚠️  [AUTH] Could not verify ApiClient auth state: {e}")
        raise


def get_auth_status(page: Page) -> dict:
    """
    Get the current authentication status from the browser.
    
    Useful for debugging auth issues in tests.
    
    Args:
        page: Playwright Page instance
        
    Returns:
        Dictionary with auth status information
    """
    return page.evaluate("""
        () => {
            const token = localStorage.getItem('access_token');
            const isReady = document.body.getAttribute('data-api-client-ready') === 'true';
            
            return {
                hasToken: !!token,
                tokenPrefix: token ? token.substring(0, 20) + '...' : null,
                apiClientReady: isReady,
                url: window.location.href
            };
        }
    """)
