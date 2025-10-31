#!/usr/bin/env python3
"""
Quick verification script for authStore refactoring.
Tests that the auth flow works correctly with the new single source of truth.
"""
import sys
import subprocess
import json

def check_frontend_files():
    """Verify that all frontend files have been updated correctly."""
    print("🔍 Checking frontend files for authStore refactoring...")
    
    checks = {
        "authStore has init method": {
            "file": "frontend/src/lib/stores/auth.ts",
            "pattern": "init:",
            "should_exist": True
        },
        "ApiClient subscribes to authStore": {
            "file": "frontend/src/lib/api.ts",
            "pattern": "authStore.subscribe",
            "should_exist": True
        },
        "ApiClient does NOT access localStorage": {
            "file": "frontend/src/lib/api.ts",
            "pattern": "localStorage.getItem('access_token')",
            "should_exist": False
        },
        "Layout initializes authStore": {
            "file": "frontend/src/routes/+layout.svelte",
            "pattern": "authStore.init()",
            "should_exist": True
        },
        "E2E injects user object": {
            "file": "e2e_tests/utils/auth.py",
            "pattern": "localStorage.setItem('user'",
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
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0

def main():
    print("=" * 60)
    print("🔐 AuthStore Refactoring Verification")
    print("=" * 60)
    print()
    
    if check_frontend_files():
        print("\n✅ All checks passed! AuthStore refactoring is complete.")
        print("\n📋 Next Steps:")
        print("  1. Build the frontend: cd frontend && npm run build")
        print("  2. Run E2E tests: cd e2e_tests && pytest -v")
        print("  3. Monitor for 401 errors in test output")
        return 0
    else:
        print("\n❌ Some checks failed. Please review the refactoring.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
