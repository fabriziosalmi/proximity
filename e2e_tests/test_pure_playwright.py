"""
Pure Playwright test - NO custom fixtures at all!
"""
import pytest


def test_pure_playwright_only(page):
    """Test using ONLY pytest-playwright's page fixture."""
    print("\n🔍 PURE TEST: Only pytest-playwright page fixture")
    print(f"   Page type: {type(page)}")
    print(f"   Page: {page}")
    
    # Navigate
    print("   Navigating to login...")
    page.goto("https://localhost:5173/login")
    
    print("   ✅ Navigation successful!")
    
    # Wait
    print("   Waiting for page load...")
    page.wait_for_load_state("domcontentloaded")
    
    print("   ✅ Page loaded!")
    
    # Check title
    title = page.title()
    print(f"   Page title: {title}")
    
    # Try to fill username
    print("   Trying to fill username...")
    page.fill('input[name="username"]', "testuser")
    print("   ✅ Username filled!")
    
    # Try to fill password
    print("   Trying to fill password...")
    page.fill('input[name="password"]', "testpass123")
    print("   ✅ Password filled!")
    
    print("✅ Pure test completed successfully")
