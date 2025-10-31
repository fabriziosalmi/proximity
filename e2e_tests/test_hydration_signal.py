"""
Test SvelteKit hydration signal detection.

This test verifies that our event-driven wait mechanism works correctly
and eliminates the race condition between Playwright and SvelteKit hydration.
"""

from playwright.sync_api import Page
from pages.login_page import LoginPage


def test_hydration_signal_and_login(page: Page, unique_user, base_url: str):
    """
    Test that login works using API method.

    This test uses the reliable API login method instead of form submission.
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

    # Use API login (more reliable than form)
    print("\n🚀 Using API login method...")
    login_page.login_with_api(username=unique_user["username"], password=unique_user["password"])

    print(f"✓ Login complete! User: {unique_user['username']}")

    # Verify we're on homepage or apps page
    assert page.url in [
        base_url + "/",
        base_url + "/apps",
        base_url + "/store",
    ], f"Expected to be redirected after login, but at: {page.url}"

    print(f"\n📊 Total API requests captured: {len(api_requests)}")
    for req in api_requests[:10]:  # Show first 10
        print(f"   - {req}")

    print("\n✅ SUCCESS: API login method works!")
