"""
Debug script to check app IDs and controlApp functionality
"""
import asyncio
from playwright.async_api import async_playwright

async def test_app_id():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.type}: {msg.text}"))
        
        # Navigate to app
        await page.goto("http://localhost:8765")
        await page.wait_for_load_state("networkidle")
        
        # Login
        await page.fill('input[name="username"]', 'fab')
        await page.fill('input[name="password"]', 'invaders')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000)
        
        # Navigate to My Apps
        await page.click('.top-nav-rack a[href="#apps"]')
        await page.wait_for_timeout(2000)
        
        # Extract app data from first card
        app_data = await page.evaluate("""
            () => {
                const card = document.querySelector('.app-card.deployed');
                if (!card) return null;
                
                const stopBtn = card.querySelector('[data-action="toggle-status"]');
                const nameEl = card.querySelector('.app-name');
                
                return {
                    name: nameEl ? nameEl.textContent : 'N/A',
                    stopBtnExists: !!stopBtn,
                    cardHTML: card.outerHTML.substring(0, 500),
                    dataAttributes: Array.from(card.attributes).map(a => ({name: a.name, value: a.value}))
                };
            }
        """)
        
        print("\n=== APP DATA ===")
        print(f"App name: {app_data['name']}")
        print(f"Stop button exists: {app_data['stopBtnExists']}")
        print(f"\nData attributes:")
        for attr in app_data['dataAttributes']:
            print(f"  {attr['name']}: {attr['value']}")
        print(f"\nCard HTML preview:\n{app_data['cardHTML']}")
        
        # Try to get window.controlApp info
        control_info = await page.evaluate("""
            () => {
                return {
                    controlAppExists: typeof window.controlApp === 'function',
                    controlAppSource: window.controlApp ? window.controlApp.toString().substring(0, 200) : 'N/A'
                };
            }
        """)
        
        print("\n=== CONTROL APP INFO ===")
        print(f"window.controlApp exists: {control_info['controlAppExists']}")
        print(f"Function preview: {control_info['controlAppSource']}")
        
        await page.wait_for_timeout(3000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_app_id())
