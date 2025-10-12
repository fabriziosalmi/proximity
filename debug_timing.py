"""
Debug timing issues in E2E tests
"""

from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:8765"
TEST_USER = {"username": "fab", "password": "invaders"}

def debug_login_flow():
    """Debug the complete login flow with detailed logging"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Track console messages
        console_msgs = []
        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))
        
        # Track page errors
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        
        try:
            print("1️⃣  Loading page...")
            page.goto(BASE_URL)
            print(f"   URL: {page.url}")
            
            print("\n2️⃣  Waiting for auth modal...")
            page.wait_for_selector("#authModal", timeout=5000)
            print("   ✓ Auth modal found")
            
            print("\n3️⃣  Checking modal visibility...")
            modal = page.locator("#authModal")
            print(f"   Modal display: {modal.evaluate('el => window.getComputedStyle(el).display')}")
            print(f"   Modal visible: {modal.is_visible()}")
            
            print("\n4️⃣  Checking tabs...")
            register_tab = page.locator('#registerTab')
            login_tab = page.locator('#loginTab')
            print(f"   Register tab exists: {register_tab.count()}")
            print(f"   Login tab exists: {login_tab.count()}")
            print(f"   Login tab class: {login_tab.get_attribute('class')}")
            
            print("\n5️⃣  Checking login form...")
            login_form = page.locator('#loginForm')
            print(f"   Login form exists: {login_form.count()}")
            print(f"   Login form visible: {login_form.is_visible() if login_form.count() > 0 else 'N/A'}")
            
            print("\n6️⃣  Checking form inputs...")
            username_input = page.locator('#loginUsername')
            password_input = page.locator('#loginPassword')
            print(f"   Username input exists: {username_input.count()}")
            print(f"   Password input exists: {password_input.count()}")
            
            if username_input.count() > 0:
                print("\n7️⃣  Filling login form...")
                page.fill('#loginUsername', TEST_USER["username"])
                page.fill('#loginPassword', TEST_USER["password"])
                print(f"   Username filled: {page.input_value('#loginUsername')}")
                print(f"   Password filled: {len(page.input_value('#loginPassword'))} chars")
                
                print("\n8️⃣  Submitting form...")
                submit_btn = page.locator('#loginForm button[type="submit"]')
                print(f"   Submit button exists: {submit_btn.count()}")
                submit_btn.click()
                
                print("\n9️⃣  Waiting for modal to close...")
                page.wait_for_selector("#authModal", state="hidden", timeout=5000)
                print("   ✓ Modal closed")
                
                print("\n🔟  Waiting for app initialization...")
                page.wait_for_timeout(1000)
                
                print("\n1️⃣1️⃣  Checking views...")
                dashboard_view = page.locator('#dashboard-view')
                print(f"   Dashboard view exists: {dashboard_view.count()}")
                
                if dashboard_view.count() > 0:
                    print(f"   Dashboard display: {dashboard_view.evaluate('el => window.getComputedStyle(el).display')}")
                    print(f"   Dashboard visible: {dashboard_view.is_visible()}")
                    
                    # Check parent visibility
                    print("\n1️⃣2️⃣  Checking parent containers...")
                    main_content = page.locator('#mainContent, .main-content, main')
                    if main_content.count() > 0:
                        print(f"   Main content exists: {main_content.count()}")
                        print(f"   Main content display: {main_content.first.evaluate('el => window.getComputedStyle(el).display')}")
                else:
                    print("   ❌ Dashboard view not found!")
                    print("\n   Available views:")
                    all_views = page.locator('[id$="-view"]')
                    for i in range(all_views.count()):
                        view = all_views.nth(i)
                        view_id = view.get_attribute('id')
                        print(f"     - {view_id}")
                
                print("\n1️⃣3️⃣  Checking navigation state...")
                dashboard_nav = page.locator('.nav-rack-item[data-view="dashboard"]')
                if dashboard_nav.count() > 0:
                    print(f"   Dashboard nav class: {dashboard_nav.get_attribute('class')}")
                
                print("\n1️⃣4️⃣  DOM Structure:")
                body_html = page.evaluate('''() => {
                    const body = document.body;
                    const structure = {
                        modalOpen: body.classList.contains('modal-open'),
                        mainContent: document.querySelector('#mainContent') ? 'exists' : 'missing',
                        dashboardView: document.querySelector('#dashboard-view') ? 'exists' : 'missing',
                        allViewIds: Array.from(document.querySelectorAll('[id$="-view"]')).map(el => el.id)
                    };
                    return structure;
                }''')
                print(f"   {body_html}")
                
            else:
                print("   ❌ Login form inputs not found!")
            
            print("\n📊 Console messages:")
            for msg in console_msgs[-10:]:  # Last 10 messages
                print(f"   {msg}")
            
            if errors:
                print("\n❌ JavaScript errors:")
                for err in errors:
                    print(f"   {err}")
            else:
                print("\n✅ No JavaScript errors")
            
            print("\n⏸️  Pausing for inspection (browser will stay open)...")
            input("Press Enter to close...")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Debug Timing Issues - Login Flow")
    print("=" * 60)
    print()
    debug_login_flow()
