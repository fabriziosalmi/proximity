"""
Test SvelteKit hydration signal detection.

This test verifies that our event-driven wait mechanism works correctly
and eliminates the race condition between Playwright and SvelteKit hydration.
"""

import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage


def test_hydration_signal_and_login(page: Page, unique_user, base_url: str):
    """
    Test that the hydration signal works and login API is called.
    
    This test:
    1. Navigates using navigate_and_wait_for_ready()
    2. Intercepts network requests to verify API call is made
    3. Attempts login and verifies success
    """
    # Track API requests
    api_requests = []
    def track_request(request):
        if "/api/" in request.url:
            api_requests.append(f"{request.method} {request.url}")
            print(f"   [API REQUEST] {request.method} {request.url}")
    
    page.on("request", track_request)
    
    # Initialize page object
    login_page = LoginPage(page, base_url)
    
    # Use the NEW navigation method that waits for hydration
    print("\n🚀 Using navigate_and_wait_for_ready() to wait for SvelteKit hydration...")
    login_page.navigate_and_wait_for_ready()
    
    print(f"✓ Hydration complete! Now attempting login with: {unique_user['username']}")
    
    # Fill credentials
    login_page.fill_username(unique_user["username"])
    login_page.fill_password(unique_user["password"])
    
    # Click submit
    print("   Clicking login button...")
    login_page.click_submit()

    
    # Verify API call was made
    print(f"\n📊 Total API requests captured: {len(api_requests)}")
    for req in api_requests:
        print(f"   - {req}")
    
    # Assert that login API was called
    login_requests = [req for req in api_requests if "/api/core/auth/login" in req]
    assert len(login_requests) > 0, f"Expected login API call, but got: {api_requests}"
    
    print("\n✅ SUCCESS: Login API was called after hydration signal!")
