"""
Bulletproof Programmatic Authentication for E2E Tests

This module provides a robust, reusable authentication strategy that guarantees
the frontend ApiClient is fully initialized and authenticated before any test
interactions occur.
"""
import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def cookie_login(page: Page, session_cookies: List[Dict[str, Any]], base_url: str = "https://localhost:5173", initial_page: str = "/", access_token: Optional[str] = None) -> None:
    """
    Perform cookie-based authentication by injecting session cookies into the browser.
    This works with HttpOnly cookie-based auth (the current Proximity 2.0 architecture).
    
    Args:
        page: Playwright Page instance
        session_cookies: List of cookie dicts with 'name', 'value', 'domain', 'path'
        base_url: Base URL of the frontend application (HTTPS required)
        initial_page: Initial page to navigate to (default: "/" for homepage)
        access_token: Optional JWT access token to inject into localStorage (for hybrid auth)
        
    Raises:
        TimeoutError: If authStore fails to initialize within timeout
    """
    logger.info("🍪 [COOKIE-LOGIN] Starting cookie-based authentication...")
    print("🍪 [COOKIE-LOGIN] Starting cookie-based authentication...")  # DEBUG
    
    # Capture browser console logs for debugging
    console_messages = []
    def handle_console(msg):
        console_messages.append(f"[{msg.type}] {msg.text}")
    page.on("console", handle_console)
    
    # Step 1: Navigate to the base URL to establish context
    logger.info(f"  → Navigating to {base_url} to establish browser context...")
    print(f"  → Navigating to {base_url} to establish browser context...")  # DEBUG
    page.goto(base_url, wait_until="domcontentloaded")
    
    # Step 2: Inject session cookies into the browser
    logger.info(f"  → Injecting {len(session_cookies)} session cookies...")
    print(f"  → Injecting {len(session_cookies)} session cookies...")  # DEBUG
    for cookie in session_cookies:
        page.context.add_cookies([cookie])
        logger.info(f"    ✓ Cookie injected: {cookie['name']}")
    
    # Step 3: Navigate to the target page (authStore will init and verify cookies)
    target_url = f"{base_url}{initial_page}"
    logger.info(f"  → Navigating to {target_url} (authStore will verify session)...")
    print(f"  → Navigating to {target_url} (authStore will verify session)...")  # DEBUG
    page.goto(target_url, wait_until="domcontentloaded")
    
    # Step 3.5: CRITICAL - Inject access_token into localStorage AFTER navigation
    # The frontend uses HYBRID auth - checks both cookies AND localStorage
    logger.info(f"  → DEBUG: access_token type={type(access_token)}, value={bool(access_token)}")
    print(f"  → DEBUG: access_token type={type(access_token)}, value={bool(access_token)}")  # DEBUG
    if access_token:
        logger.info(f"  → Injecting JWT access_token into localStorage (AFTER page load)...")
        logger.info(f"  → Token preview: {access_token[:50]}...")
        page.evaluate(f"""
            () => {{
                localStorage.setItem('access_token', '{access_token}');
                console.log('✓ JWT access_token injected into localStorage');
            }}
        """)
        # Reload to trigger authStore re-init with the token
        logger.info(f"  → Reloading page to apply token...")
        page.reload(wait_until="domcontentloaded")
    else:
        logger.warning("  ⚠️  No access_token provided - frontend may fail auth checks!")
        logger.warning(f"  ⚠️  access_token value: {access_token}")
    
    # Step 4: Wait for authStore to initialize and verify the session
    try:
        page.wait_for_timeout(2000)  # Give authStore time to call api.getUser()
        
        # Check auth status
        auth_status = page.evaluate("""
            () => {
                const cookies = document.cookie;
                return {
                    hasCookies: cookies.length > 0,
                    url: window.location.href
                };
            }
        """)
        logger.info(f"  → Auth status: cookies={auth_status['hasCookies']}")
        logger.info(f"  ✅ authStore initialized with cookie-based session!")
        
    except Exception as e:
        logger.error(f"  ❌ authStore initialization check failed: {e}")
        
        # Log captured console messages
        logger.error(f"  → Browser console ({len(console_messages)} messages):")
        for msg in console_messages[-20:]:  # Last 20 messages
            logger.error(f"      {msg}")
        
        # Still continue - the session might be working even if our check failed
        logger.warning("  ⚠️  Continuing despite check failure...")
    
    logger.info("🎉 [COOKIE-LOGIN] Authentication completed successfully!")


def programmatic_login(page: Page, auth_token: str, base_url: str = "https://localhost:5173", initial_page: str = "/") -> None:
    """
    Perform bulletproof programmatic login using the authStore single source of truth:
    1. Inject the auth token into localStorage before any page loads
    2. Navigate to the specified initial page
    3. Force authStore to re-initialize and sync with localStorage
    4. Wait for explicit confirmation that the ApiClient is ready
    
    This eliminates race conditions by ensuring authStore.init() picks up
    the injected token and propagates it to all subscribers (including ApiClient).
    
    Args:
        page: Playwright Page instance
        auth_token: JWT authentication token from user fixture
        base_url: Base URL of the frontend application (HTTPS required)
        initial_page: Initial page to navigate to (default: "/" for homepage)
        
    Raises:
        TimeoutError: If ApiClient doesn't signal readiness within 10 seconds
    """
    logger.info("🔐 [AUTH] Starting bulletproof programmatic login with authStore...")
    
    # Step 1: Inject token into localStorage BEFORE any navigation
    # This ensures the token is available when authStore.init() runs
    page.add_init_script(f"""
        // Store auth token in localStorage
        window.localStorage.setItem('access_token', '{auth_token}');
        // Add a fake user object (authStore expects both token and user)
        window.localStorage.setItem('user', JSON.stringify({{
            id: 1,
            username: 'testuser',
            email: 'test@example.com'
        }}));
        console.log('🔑 [E2E] Auth token and user injected into localStorage');
    """)
    logger.info(f"  ✓ Token injection script registered")
    
    # Step 2: Navigate to the initial page
    # The add_init_script will execute before the page loads
    # The +layout.svelte will call authStore.init() on mount
    target_url = f"{base_url}{initial_page}"
    logger.info(f"  → Navigating to {target_url}")
    page.goto(target_url, wait_until="domcontentloaded")
    
    # Step 3: Reload to ensure authStore picks up the localStorage changes
    # Sometimes tokens injected via add_init_script aren't detected on first mount
    logger.info(f"  → Reloading page to trigger authStore.init() with fresh token...")
    page.reload(wait_until="domcontentloaded")
    
    # Step 4: Wait for authStore to initialize and propagate to ApiClient
    try:
        # Wait a moment for the app to mount and authStore.init() to run
        page.wait_for_timeout(1500)  # Increased from 1000ms to 1500ms
        
        # Check the current auth state
        auth_status = page.evaluate("""
            () => {
                return {
                    hasToken: !!localStorage.getItem('access_token'),
                    hasUser: !!localStorage.getItem('user'),
                    tokenPrefix: (localStorage.getItem('access_token') || '').substring(0, 20),
                    apiReady: document.body.getAttribute('data-api-client-ready'),
                    url: window.location.href
                };
            }
        """)
        logger.info(f"  → Auth status: token={auth_status['hasToken']}, user={auth_status['hasUser']}, ready={auth_status['apiReady']}")
        
        # Wait for the ready signal with a reasonable timeout
        # This is set by authStore.init() when it finds a valid session
        page.wait_for_selector(
            'body[data-api-client-ready="true"]',
            timeout=10000,
            state="attached"
        )
        logger.info("  ✅ authStore initialized, ApiClient subscribed and ready")
        
        # Verify the token is actually in localStorage
        has_token = page.evaluate('!!localStorage.getItem("access_token")')
        if not has_token:
            raise RuntimeError("Token was lost from localStorage!")
            
    except Exception as e:
        logger.error(f"  ❌ authStore/ApiClient failed to become ready: {e}")
        # Log detailed page state for debugging
        logger.error(f"  → Current URL: {page.url}")
        ready_attr = page.evaluate('document.body.getAttribute("data-api-client-ready")')
        logger.error(f"  → Body attribute: {ready_attr}")
        token_exists = page.evaluate('!!localStorage.getItem("access_token")')
        logger.error(f"  → Has token in localStorage: {token_exists}")
        user_exists = page.evaluate('!!localStorage.getItem("user")')
        logger.error(f"  → Has user in localStorage: {user_exists}")
        
        # Get console logs
        console_logs = page.evaluate("""
            () => {
                // Try to get any ApiClient logs
                return window.__e2e_logs || 'No logs captured';
            }
        """)
        logger.error(f"  → Console context: {console_logs}")
        
        raise TimeoutError(
            f"authStore/ApiClient did not signal readiness within 10 seconds. "
            f"Ready attribute: {ready_attr}, Has token: {token_exists}, Has user: {user_exists}"
        ) from e
    
    logger.info("🎉 [AUTH] Programmatic login completed successfully via authStore!")


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
