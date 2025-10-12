#!/usr/bin/env python3
"""
Debug script per verificare che il Router funzioni correttamente con window.ProximityRouter
"""

from playwright.sync_api import sync_playwright
import time

def login(page):
    """Helper per fare login"""
    page.goto("http://localhost:8765")
    page.wait_for_selector("#authModal[style*='flex']", timeout=10000)
    page.fill("#loginUsername", "fab")
    page.fill("#loginPassword", "invaders")
    page.click("#loginForm button[type='submit']")
    page.wait_for_selector("#dashboardView:not(.hidden)", timeout=5000)
    print("✅ Login completato")

def test_router_and_navigation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Login
            login(page)
            time.sleep(1)
            
            # Test 1: Verificare che ProximityRouter esista
            print("\n=== Test 1: ProximityRouter ===")
            router_exists = page.evaluate("() => typeof window.ProximityRouter !== 'undefined'")
            print(f"window.ProximityRouter exists: {router_exists}")
            
            if router_exists:
                current_view = page.evaluate("() => window.ProximityRouter.getCurrentView()")
                print(f"Current view: {current_view}")
            
            # Test 2: Navigazione su Apps
            print("\n=== Test 2: Apps Navigation ===")
            apps_nav = page.locator('[data-view="apps"]').first
            
            # Stato PRIMA del click
            before_class = apps_nav.get_attribute("class")
            print(f"Before click - Apps nav class: '{before_class}'")
            
            # Click
            apps_nav.click()
            
            # ATTENDI che la navigazione sia completa
            page.wait_for_selector("#appsView:not(.hidden)", timeout=3000)
            time.sleep(0.5)  # Attesa extra per asincronia
            
            # Stato DOPO il click
            after_class = apps_nav.get_attribute("class")
            print(f"After click - Apps nav class: '{after_class}'")
            
            # Verifica che Apps sia montato
            apps_visible = page.locator("#appsView:not(.hidden)").count() > 0
            print(f"Apps view visible: {apps_visible}")
            
            if router_exists:
                current_view = page.evaluate("() => window.ProximityRouter.getCurrentView()")
                print(f"Router current view: {current_view}")
                
            # Verifica che 'active' sia presente
            has_active = "active" in after_class
            print(f"Apps has 'active' class: {has_active}")
            
            # Test 3: Navigazione su UILab
            print("\n=== Test 3: UILab Navigation ===")
            uilab_nav = page.locator('[data-view="uilab"]').first
            
            # Stato PRIMA del click
            before_class = uilab_nav.get_attribute("class")
            print(f"Before click - UILab nav class: '{before_class}'")
            
            # Click
            uilab_nav.click()
            
            # ATTENDI che la navigazione sia completa
            page.wait_for_selector("#uilabView:not(.hidden)", timeout=3000)
            time.sleep(0.5)  # Attesa extra per asincronia
            
            # Stato DOPO il click
            after_class = uilab_nav.get_attribute("class")
            print(f"After click - UILab nav class: '{after_class}'")
            
            # Verifica che UILab sia montato
            uilab_visible = page.locator("#uilabView:not(.hidden)").count() > 0
            print(f"UILab view visible: {uilab_visible}")
            
            if router_exists:
                current_view = page.evaluate("() => window.ProximityRouter.getCurrentView()")
                print(f"Router current view: {current_view}")
                
            # Verifica che 'active' sia presente
            has_active = "active" in after_class
            print(f"UILab has 'active' class: {has_active}")
            
            # Test 4: Verificare che la funzione _updateNavigationUI venga chiamata
            print("\n=== Test 4: Navigation UI Update ===")
            dashboard_nav = page.locator('[data-view="dashboard"]').first
            dashboard_nav.click()
            time.sleep(1)
            
            dashboard_class = dashboard_nav.get_attribute("class")
            apps_class_final = apps_nav.get_attribute("class")
            
            print(f"Dashboard nav class: '{dashboard_class}'")
            print(f"Apps nav class (should not be active): '{apps_class_final}'")
            
            has_active = "active" in dashboard_class
            print(f"Dashboard has 'active' class: {has_active}")
            
            # Test 5: Verificare console logs
            print("\n=== Test 5: Console Logs ===")
            console_logs = []
            
            def handle_console(msg):
                if "Router" in msg.text or "Navigation" in msg.text or "Mounting" in msg.text:
                    console_logs.append(msg.text)
            
            page.on("console", handle_console)
            
            # Navigazione finale per catturare logs
            page.locator('[data-view="nodes"]').first.click()
            time.sleep(1)
            
            print("Recent console logs:")
            for log in console_logs[-5:]:
                print(f"  {log}")
            
            print("\n=== Summary ===")
            print(f"✅ ProximityRouter: {router_exists}")
            print(f"✅ Navigation working: {apps_visible and uilab_visible}")
            print(f"✅ Active class management: {has_active}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_router_and_navigation()
