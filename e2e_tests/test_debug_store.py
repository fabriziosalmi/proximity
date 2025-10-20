"""
Debug test - Store page loading
"""
import pytest
from playwright.sync_api import Page
from pages import LoginPage, StorePage


def test_debug_store_page(page: Page, unique_user: dict, proxmox_host: dict, base_url: str):
    """Test just the store page loading after login."""
    print("\n🔍 DEBUG STORE PAGE TEST")
    
    # Step 1: Login
    print("\n1️⃣ Logging in...")
    login_page = LoginPage(page, base_url)
    login_page.navigate()
    login_page.login(
        username=unique_user['username'],
        password=unique_user['password'],
        wait_for_navigation=True
    )
    print(f"   ✅ Logged in as {unique_user['username']}")
    
    # Step 2: Navigate to store
    print("\n2️⃣ Navigating to /store...")
    store_page = StorePage(page, base_url)
    store_page.navigate()
    print(f"   URL: {page.url}")
    
    # Step 3: Wait for apps to load
    print("\n3️⃣ Waiting for apps to load...")
    page.screenshot(path="/tmp/store_before_wait.png")
    
    try:
        store_page.wait_for_apps_loaded(min_count=1, timeout=30000)
        app_count = store_page.get_app_count()
        print(f"   ✅ Found {app_count} apps")
    except Exception as e:
        print(f"   ❌ Error waiting for apps: {e}")
        app_count = 0
    
    # Step 4: Screenshot and inspect
    page.screenshot(path="/tmp/store_after_wait.png")
    print(f"   Screenshot saved: /tmp/store_after_wait.png")
    
    # Check for app cards
    app_cards = page.locator('[data-testid^="app-card-"]').all()
    print(f"\n4️⃣ App cards found: {len(app_cards)}")
    
    if len(app_cards) > 0:
        print("   First 3 app cards:")
        for i, card in enumerate(app_cards[:3]):
            if card.is_visible():
                text = card.text_content()[:100]  # First 100 chars
                print(f"      {i+1}. {text}")
    else:
        print("   ⚠️ No app cards found!")
        print("   Checking page content:")
        body_text = page.locator('body').text_content()
        print(f"      Body text (first 300 chars): {body_text[:300]}")
    
    print("\n✅ Debug store test completed")
    assert app_count > 0, f"Expected at least 1 app, found {app_count}"
