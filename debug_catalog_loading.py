#!/usr/bin/env python3
"""
Debug script per verificare il caricamento del Catalog
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

def test_catalog_loading():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        
        # Collect console logs
        console_logs = []
        def handle_console(msg):
            text = msg.text
            console_logs.append(text)
            if any(keyword in text for keyword in ['Catalog', 'catalog', 'loadCatalog', 'renderCatalog']):
                print(f"  📝 {text}")
        page.on("console", handle_console)
        
        try:
            # Login
            login(page)
            time.sleep(1)
            
            # Navigazione a Catalog
            print("\n=== Navigating to Catalog ===")
            catalog_nav = page.locator('[data-view="catalog"]').first
            catalog_nav.click()
            
            # Wait for catalog view to be visible
            page.wait_for_selector("#catalogView:not(.hidden)", timeout=5000)
            print("✓ Catalog view is visible")
            time.sleep(2)  # Wait for async loading
            
            # Check catalog state
            print("\n=== Catalog State ===")
            has_loading = page.locator(".loading-spinner").count() > 0
            print(f"Loading spinner present: {has_loading}")
            
            has_empty = page.locator(".empty-state").count() > 0
            print(f"Empty state present: {has_empty}")
            
            has_items = page.locator(".catalog-item, .app-template-card").count() > 0
            item_count = page.locator(".catalog-item, .app-template-card").count()
            print(f"Catalog items present: {has_items}")
            print(f"Item count: {item_count}")
            
            # Check if there's a search bar
            has_search = page.locator("#catalogSearchInput").count() > 0
            print(f"Search bar present: {has_search}")
            
            # Get the HTML content of catalogView
            print("\n=== Catalog View HTML (first 500 chars) ===")
            catalog_html = page.evaluate("() => document.getElementById('catalogView')?.innerHTML?.substring(0, 500)")
            print(catalog_html)
            
            # Check AppState
            print("\n=== AppState Catalog ===")
            app_state_catalog = page.evaluate("""() => {
                const state = window.getState ? window.getState() : null;
                if (!state) return 'getState not available';
                if (!state.catalog) return 'catalog not in state';
                return {
                    items_count: state.catalog.items?.length || 0,
                    categories: state.catalog.categories?.length || 0,
                    total: state.catalog.total || 0
                };
            }""")
            print(f"AppState catalog: {app_state_catalog}")
            
            # Wait a bit more
            print("\n=== Waiting 3 more seconds ===")
            time.sleep(3)
            
            item_count_final = page.locator(".catalog-item, .app-template-card").count()
            print(f"Final item count: {item_count_final}")
            
            # Check relevant console logs
            print("\n=== Relevant Console Logs ===")
            catalog_logs = [log for log in console_logs if any(keyword in log for keyword in ['Catalog', 'catalog', 'load', 'render', 'items'])]
            for log in catalog_logs[-20:]:
                print(f"  {log}")
            
            # Keep browser open
            print("\n=== Press Enter to close ===")
            input()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            input("Press Enter to close...")
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_catalog_loading()
