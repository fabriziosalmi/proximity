"""
Debug navigation clicks for apps and uilab
"""

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8765"
TEST_USER = {"username": "fab", "password": "invaders"}

def debug_specific_nav():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        console_msgs = []
        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))
        
        # Login
        page.goto(BASE_URL)
        page.wait_for_selector("#authModal", timeout=5000)
        page.wait_for_selector('#loginForm', timeout=3000)
        page.fill('#loginUsername', TEST_USER["username"])
        page.fill('#loginPassword', TEST_USER["password"])
        page.click('#loginForm button[type="submit"]')
        page.wait_for_selector("#authModal", state="hidden", timeout=5000)
        page.wait_for_timeout(1000)
        
        print("✅ Logged in")
        
        # Test apps navigation
        print("\n🔍 Testing Apps navigation...")
        apps_nav = page.locator('.nav-rack-item[data-view="apps"]')
        print(f"   Before click - class: {apps_nav.get_attribute('class')}")
        
        apps_nav.click()
        print(f"   Clicked!")
        
        page.wait_for_timeout(500)
        print(f"   After 500ms - class: {apps_nav.get_attribute('class')}")
        
        page.wait_for_timeout(500)
        print(f"   After 1000ms - class: {apps_nav.get_attribute('class')}")
        
        # Check what JavaScript sees
        active_view = page.evaluate("window.router ? window.router._currentViewName : 'no router'")
        print(f"   Router current view: {active_view}")
        
        # Test uilab navigation
        print("\n🔍 Testing UILab navigation...")
        uilab_nav = page.locator('.nav-rack-item[data-view="uilab"]')
        print(f"   Before click - class: {uilab_nav.get_attribute('class')}")
        
        uilab_nav.click()
        print(f"   Clicked!")
        
        page.wait_for_timeout(500)
        print(f"   After 500ms - class: {uilab_nav.get_attribute('class')}")
        
        page.wait_for_timeout(500)
        print(f"   After 1000ms - class: {uilab_nav.get_attribute('class')}")
        
        active_view = page.evaluate("window.router ? window.router._currentViewName : 'no router'")
        print(f"   Router current view: {active_view}")
        
        # Check console for errors
        print("\n📊 Recent console messages:")
        for msg in console_msgs[-15:]:
            print(f"   {msg}")
        
        input("\nPress Enter to close...")
        browser.close()

if __name__ == "__main__":
    debug_specific_nav()
