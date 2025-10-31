"""
Manual Test: Atomic AuthStore Verification

This script opens a browser to the login page so you can:
1. Open the browser console (F12 or Cmd+Option+I)
2. Watch the authentication flow logs
3. Verify that the atomic state updates work correctly

Expected Console Logs (CORRECT):
✅ [AuthStore] init() called
✅ [AuthStore] Session is valid or invalid
✅ [myAppsStore] Checked authStore state: { isInitialized: true, hasUser: true/false }

Should NEVER see (OLD BUG - now impossible):
❌ { isAuthenticated: true, hasToken: false }
"""

import asyncio
from playwright.async_api import async_playwright


async def manual_test_atomic_authstore():
    """
    Opens a browser to manually verify the atomic authStore refactoring.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500,  # Slow down for visibility
            args=["--ignore-certificate-errors"],  # Accept self-signed certs
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, ignore_https_errors=True
        )

        page = await context.new_page()

        print("\n" + "=" * 70)
        print("🔍 ATOMIC AUTHSTORE MANUAL VERIFICATION TEST")
        print("=" * 70)
        print("\nInstructions:")
        print("1. A browser window will open to the Proximity login page")
        print("2. Open the browser console (F12 or Cmd+Option+I)")
        print("3. Watch the console logs as the page loads")
        print("4. Look for auth initialization logs")
        print("\n✅ EXPECTED (Atomic State):")
        print("   - [AuthStore] init() called")
        print("   - [myAppsStore] Checked authStore state: { isInitialized: true, hasUser: false }")
        print("\n❌ SHOULD NEVER SEE (Old Race Condition):")
        print("   - { isAuthenticated: true, hasToken: false }")
        print("\n5. Now log in and watch the atomic state update")
        print("6. After login, you should see: { isInitialized: true, hasUser: true }")
        print("\n7. Press Ctrl+C in this terminal when done")
        print("=" * 70 + "\n")

        # Navigate to login page
        await page.goto("https://localhost:5173/auth/login")

        print("✅ Browser opened! Check the console logs...")
        print("   The page is now at: https://localhost:5173/auth/login")
        print("\n   Press Ctrl+C when you're done verifying\n")

        # Keep the browser open until user presses Ctrl+C
        try:
            await asyncio.sleep(3600)  # Wait for 1 hour (or until Ctrl+C)
        except KeyboardInterrupt:
            print("\n\n✅ Test completed!")
        finally:
            await browser.close()


if __name__ == "__main__":
    print("\n🚀 Starting manual verification test...")
    asyncio.run(manual_test_atomic_authstore())
