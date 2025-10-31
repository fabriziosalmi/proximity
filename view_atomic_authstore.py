#!/usr/bin/env python3
"""
Simple script to open the Proximity app in a browser with console visible.
This demonstrates the atomic authStore refactoring in action.
"""

import subprocess
import sys

print("""
╔═══════════════════════════════════════════════════════════════════╗
║   ATOMIC AUTHSTORE - VISUAL VERIFICATION                         ║
╚═══════════════════════════════════════════════════════════════════╝

This will open your default browser to: https://localhost:5173

TO VERIFY THE ATOMIC REFACTORING:
1. Open Browser DevTools (F12 or Cmd+Option+I)
2. Go to the Console tab
3. Look for these logs on page load:

   ✅ EXPECTED (Atomic State):
   [AuthStore] init() called
   [myAppsStore] Checked authStore state: { 
     isInitialized: true, 
     hasUser: false 
   }

   ❌ SHOULD NEVER SEE (Old Race Condition):
   { isAuthenticated: true, hasToken: false }

4. Now login and watch the atomic state update
5. After login, you should see:
   { isInitialized: true, hasUser: true }

Press Enter to open the browser (Ctrl+C to cancel)...
""")

try:
    input()
except KeyboardInterrupt:
    print("\n\nCancelled.")
    sys.exit(0)

# Open browser
print("\n🚀 Opening browser...")
try:
    subprocess.run(['open', 'https://localhost:5173'], check=True)
    print("✅ Browser opened!")
    print("\n💡 Remember to open DevTools Console (F12 or Cmd+Option+I)")
    print("   and watch the auth logs as you navigate and login.\n")
except Exception as e:
    print(f"❌ Error opening browser: {e}")
    print("\nManually open: https://localhost:5173")
