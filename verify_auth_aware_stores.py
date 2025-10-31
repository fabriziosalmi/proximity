#!/usr/bin/env python3
"""
Verification script for auth-aware stores implementation.
"""
import sys
import os

# Change to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_auth_aware_implementation():
    """Verify that auth-aware store pattern is correctly implemented."""
    print("=" * 60)
    print("🔐 Auth-Aware Stores Verification")
    print("=" * 60)
    print()
    
    checks = {
        "authStore has isInitialized": {
            "file": "frontend/src/lib/stores/auth.ts",
            "pattern": "isInitialized: boolean",
            "should_exist": True
        },
        "authStore init() sets isInitialized": {
            "file": "frontend/src/lib/stores/auth.ts",
            "pattern": "isInitialized: true",
            "should_exist": True
        },
        "myAppsStore imports authStore": {
            "file": "frontend/src/lib/stores/apps.ts",
            "pattern": "import { authStore }",
            "should_exist": True
        },
        "myAppsStore imports get from svelte/store": {
            "file": "frontend/src/lib/stores/apps.ts",
            "pattern": "import { writable, derived, get }",
            "should_exist": True
        },
        "startPolling checks isInitialized": {
            "file": "frontend/src/lib/stores/apps.ts",
            "pattern": "currentAuthState.isInitialized",
            "should_exist": True
        },
        "fetchApps has auth guard": {
            "file": "frontend/src/lib/stores/apps.ts",
            "pattern": "if (!currentAuthState.isInitialized)",
            "should_exist": True
        },
        "startPolling waits for auth": {
            "file": "frontend/src/lib/stores/apps.ts",
            "pattern": "Waiting for authStore",
            "should_exist": True
        },
        "stopPolling cleans up subscription": {
            "file": "frontend/src/lib/stores/apps.ts",
            "pattern": "authUnsubscribe",
            "should_exist": True
        }
    }
    
    passed = 0
    failed = 0
    
    for check_name, check_info in checks.items():
        try:
            with open(check_info["file"], 'r') as f:
                content = f.read()
                found = check_info["pattern"] in content
                
                if found == check_info["should_exist"]:
                    print(f"  ✅ {check_name}")
                    passed += 1
                else:
                    if check_info["should_exist"]:
                        print(f"  ❌ {check_name} - Pattern NOT found (expected to exist)")
                    else:
                        print(f"  ❌ {check_name} - Pattern FOUND (expected to NOT exist)")
                    failed += 1
        except FileNotFoundError:
            print(f"  ❌ {check_name} - File not found: {check_info['file']}")
            failed += 1
    
    print()
    print(f"📊 Results: {passed} passed, {failed} failed")
    return failed == 0

def main():
    if check_auth_aware_implementation():
        print()
        print("✅ All checks passed! Auth-aware stores are correctly implemented.")
        print()
        print("📋 Next Steps:")
        print("  1. Restart Docker services: docker-compose restart")
        print("  2. Run E2E tests: cd e2e_tests && pytest test_golden_path.py -v -s")
        print("  3. Check for apps appearing on /apps page")
        print("  4. Verify no 401 errors in backend logs")
        return 0
    else:
        print()
        print("❌ Some checks failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
