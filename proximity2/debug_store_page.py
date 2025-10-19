"""
Quick debug test to verify Store page loads apps
"""
from playwright.sync_api import sync_playwright
import time

def test_store_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to store
        print("🔧 Navigating to store page...")
        page.goto("http://localhost:5173/store")
        
        # Wait a bit for page to load
        print("⏳ Waiting 5 seconds for page to load...")
        time.sleep(5)
        
        # Check what elements are on the page
        print("\n📊 Checking page content...")
        
        # Take screenshot
        page.screenshot(path="/tmp/store_page.png")
        print("✅ Screenshot saved to /tmp/store_page.png")
        
        # Try different selectors
        selectors = [
            '.rack-card',
            '[data-testid="app-card"]',
            '.app-card',
            'div[class*="card"]',
            'article',
            '[role="article"]'
        ]
        
        for selector in selectors:
            count = page.locator(selector).count()
            print(f"  - {selector}: {count} elements found")
        
        # Get page HTML
        html = page.content()
        if 'Adminer' in html:
            print("✅ 'Adminer' text found in page HTML")
        else:
            print("❌ 'Adminer' text NOT found in page HTML")
        
        # Check network requests
        print("\n🌐 Checking if catalog API was called...")
        print("   (Check browser DevTools Network tab)")
        
        input("Press Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    test_store_page()
