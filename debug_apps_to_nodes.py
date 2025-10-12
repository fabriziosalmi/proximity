#!/usr/bin/env python3
"""
Debug script per testare la navigazione Apps → Nodes
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

def test_apps_to_nodes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        
        # Collect console logs
        console_logs = []
        def handle_console(msg):
            console_logs.append(msg.text)
            if "Router" in msg.text or "Navigation" in msg.text or "Mounting" in msg.text:
                print(f"  📝 {msg.text}")
        page.on("console", handle_console)
        
        try:
            # Login
            login(page)
            time.sleep(1)
            
            # Navigazione Dashboard → Apps
            print("\n=== Step 1: Dashboard → Apps ===")
            apps_nav = page.locator('[data-view="apps"]').first
            apps_nav.click()
            page.wait_for_selector("#appsView:not(.hidden)", timeout=5000)
            time.sleep(1)
            
            apps_class = apps_nav.get_attribute("class")
            print(f"Apps nav class: {apps_class}")
            print(f"Apps view hidden: {page.locator('#appsView.hidden').count() > 0}")
            print(f"Apps view visible: {page.locator('#appsView:not(.hidden)').count() > 0}")
            
            router_view = page.evaluate("() => window.ProximityRouter.getCurrentView()")
            print(f"Router current view: {router_view}")
            
            # Verifica lo stato di tutte le views
            print("\n=== View States After Apps Navigation ===")
            views = ["dashboard", "apps", "nodes"]
            for view_name in views:
                view_id = f"{view_name}View"
                has_hidden = page.evaluate(f"() => document.getElementById('{view_id}')?.classList.contains('hidden')")
                print(f"  {view_id}: {'hidden' if has_hidden else 'visible'}")
            
            # Navigazione Apps → Nodes
            print("\n=== Step 2: Apps → Nodes ===")
            nodes_nav = page.locator('[data-view="nodes"]').first
            
            # Cattura lo stato PRIMA del click
            print("Before click:")
            nodes_hidden_before = page.evaluate("() => document.getElementById('nodesView')?.classList.contains('hidden')")
            print(f"  nodesView hidden: {nodes_hidden_before}")
            
            nodes_nav.click()
            print("Clicked on Nodes nav")
            
            # Aspetta un po' e controlla lo stato
            time.sleep(0.5)
            print("\nAfter 500ms:")
            nodes_hidden_after = page.evaluate("() => document.getElementById('nodesView')?.classList.contains('hidden')")
            apps_hidden_after = page.evaluate("() => document.getElementById('appsView')?.classList.contains('hidden')")
            router_view_after = page.evaluate("() => window.ProximityRouter.getCurrentView()")
            print(f"  nodesView hidden: {nodes_hidden_after}")
            print(f"  appsView hidden: {apps_hidden_after}")
            print(f"  Router view: {router_view_after}")
            
            # Aspetta più a lungo
            time.sleep(1.5)
            print("\nAfter 2000ms total:")
            nodes_hidden_final = page.evaluate("() => document.getElementById('nodesView')?.classList.contains('hidden')")
            apps_hidden_final = page.evaluate("() => document.getElementById('appsView')?.classList.contains('hidden')")
            router_view_final = page.evaluate("() => window.ProximityRouter.getCurrentView()")
            print(f"  nodesView hidden: {nodes_hidden_final}")
            print(f"  appsView hidden: {apps_hidden_final}")
            print(f"  Router view: {router_view_final}")
            
            # Verifica classi nav
            nodes_class = nodes_nav.get_attribute("class")
            apps_class = apps_nav.get_attribute("class")
            print(f"\nNav classes:")
            print(f"  Nodes: {nodes_class}")
            print(f"  Apps: {apps_class}")
            
            # Verifica lo stato FINALE di tutte le views
            print("\n=== Final View States ===")
            views = ["dashboard", "apps", "nodes", "monitoring"]
            for view_name in views:
                view_id = f"{view_name}View"
                has_hidden = page.evaluate(f"() => document.getElementById('{view_id}')?.classList.contains('hidden')")
                print(f"  {view_id}: {'hidden' if has_hidden else 'visible'}")
            
            # Prova a forzare la navigazione
            print("\n=== Force Navigation (direct Router call) ===")
            page.evaluate("() => window.ProximityRouter.navigateTo('nodes')")
            time.sleep(1)
            
            nodes_hidden_forced = page.evaluate("() => document.getElementById('nodesView')?.classList.contains('hidden')")
            router_view_forced = page.evaluate("() => window.ProximityRouter.getCurrentView()")
            print(f"After forced navigation:")
            print(f"  nodesView hidden: {nodes_hidden_forced}")
            print(f"  Router view: {router_view_forced}")
            
            # Aspetta ancora un po' per vedere i console logs
            time.sleep(2)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_apps_to_nodes()
