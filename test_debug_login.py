"""
Test di debug per capire cosa succede con il login
"""

import pytest
from playwright.sync_api import Page
import time

BASE_URL = "http://localhost:8765"
TEST_USERNAME = "fab"
TEST_PASSWORD = "invaders"

def test_debug_login(page: Page):
    """Debug del processo di login"""
    print("\n" + "="*80)
    print("DEBUG: Login Process")
    print("="*80)
    
    # Vai alla homepage
    print(f"1. Going to {BASE_URL}...")
    page.goto(BASE_URL, timeout=30000)
    time.sleep(2)
    
    # Screenshot homepage
    page.screenshot(path="debug_01_homepage.png")
    print("   Screenshot saved: debug_01_homepage.png")
    
    # HTML della pagina
    html = page.content()
    print(f"   Page title: {page.title()}")
    print(f"   URL: {page.url}")
    
    # Cerca form di login
    print("\n2. Looking for login form...")
    login_form = page.locator('form, #loginForm, .login-form')
    if login_form.count() > 0:
        print(f"   ✅ Found {login_form.count()} form(s)")
    else:
        print("   ⚠️ No form found")
    
    # Cerca input fields
    text_inputs = page.locator('input[type="text"], input[name="username"]')
    password_inputs = page.locator('input[type="password"], input[name="password"]')
    submit_buttons = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")')
    
    print(f"   Text inputs found: {text_inputs.count()}")
    print(f"   Password inputs found: {password_inputs.count()}")
    print(f"   Submit buttons found: {submit_buttons.count()}")
    
    if text_inputs.count() == 0 or password_inputs.count() == 0:
        print("   ❌ Login form elements not found!")
        print("   Saving full HTML...")
        with open("debug_page_html.html", "w") as f:
            f.write(html)
        print("   HTML saved: debug_page_html.html")
        return
    
    # Prova il login
    print("\n3. Attempting login...")
    text_inputs.first.fill(TEST_USERNAME)
    print(f"   Username filled: {TEST_USERNAME}")
    
    password_inputs.first.fill(TEST_PASSWORD)
    print("   Password filled: ***")
    
    page.screenshot(path="debug_02_before_submit.png")
    print("   Screenshot saved: debug_02_before_submit.png")
    
    submit_buttons.first.click()
    print("   Submit clicked")
    
    # Attendi navigazione/cambio
    time.sleep(3)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    page.screenshot(path="debug_03_after_submit.png")
    print("   Screenshot saved: debug_03_after_submit.png")
    
    print(f"\n4. After login:")
    print(f"   URL: {page.url}")
    print(f"   Title: {page.title()}")
    
    # Cerca elementi del dashboard
    print("\n5. Looking for dashboard elements...")
    sidebar = page.locator('.sidebar, #sidebar, nav.sidebar')
    print(f"   Sidebar found: {sidebar.count()}")
    
    header = page.locator('header, .header, .navbar')
    print(f"   Header found: {header.count()}")
    
    main_content = page.locator('main, .main-content, #main')
    print(f"   Main content found: {main_content.count()}")
    
    # Cerca link My Apps
    my_apps_links = page.locator('a[href="#apps"], a:has-text("My Apps"), a:has-text("Apps")')
    print(f"   My Apps links found: {my_apps_links.count()}")
    
    # Elenca tutti i link visibili
    print("\n6. All visible links:")
    all_links = page.locator('a').all()
    for i, link in enumerate(all_links[:20]):  # primi 20
        try:
            href = link.get_attribute('href')
            text = link.text_content()
            if text and text.strip():
                print(f"   [{i}] {text.strip()[:30]} -> {href}")
        except:
            pass
    
    # Salva HTML finale
    with open("debug_after_login.html", "w") as f:
        f.write(page.content())
    print("\n   Full HTML saved: debug_after_login.html")
    
    print("\n" + "="*80)
    print("DEBUG COMPLETE - Check the screenshots and HTML files")
    print("="*80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
