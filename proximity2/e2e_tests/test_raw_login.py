"""
Raw Playwright test - NO LoginPage, NO fixtures except basic Playwright ones.
"""
import pytest


@pytest.mark.asyncio
async def test_raw_login_no_fixtures(page):
    """Test login using only raw Playwright page fixture."""
    print("\n🔍 RAW TEST: Pure Playwright page fixture")
    
    # Navigate
    print("   Navigating to login...")
    await page.goto("http://localhost:5173/login")
    
    # Wait
    print("   Waiting for page load...")
    await page.wait_for_load_state("networkidle")
    
    # Fill form
    print("   Filling username...")
    await page.fill('input[name="username"]', "testuser")
    
    print("   Filling password...")
    await page.fill('input[type="password"]', "testpass123")
    
    print("   Clicking submit...")
    await page.click('button[type="submit"]')
    
    # Wait
    await page.wait_for_timeout(2000)
    
    print("✅ Raw test completed successfully")


def test_raw_login_sync(page):
    """Test login using sync Playwright (like our current tests)."""
    print("\n🔍 SYNC TEST: Sync Playwright page fixture")
    
    # Navigate
    print("   Navigating to login...")
    page.goto("http://localhost:5173/login")
    
    # Wait
    print("   Waiting for page load...")
    page.wait_for_load_state("domcontentloaded")  # Changed from networkidle
    
    # Fill form
    print("   Filling username...")
    page.fill('input[name="username"]', "testuser")
    
    print("   Filling password...")
    page.fill('input[name="password"]', "testpass123")
    
    print("   Clicking submit button (type=button with on:click)...")
    # The button is type="button" with on:click handler, not type="submit"
    submit_btn = page.locator('button:has-text("Sign In")').first
    submit_btn.wait_for(state='visible', timeout=5000)
    submit_btn.click()
    
    # Wait
    page.wait_for_timeout(2000)
    
    print("✅ Sync test completed successfully")
