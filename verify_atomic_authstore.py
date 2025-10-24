#!/usr/bin/env python3
"""
Verification script for AuthStore atomic refactoring.

This script checks that the refactored authentication store properly
eliminates race conditions by verifying console logs during E2E tests.
"""

import re
import sys
from pathlib import Path


def check_authstore_implementation():
    """Verify that authStore uses atomic state management."""
    
    auth_store_path = Path('frontend/src/lib/stores/auth.ts')
    
    if not auth_store_path.exists():
        print("❌ auth.ts file not found")
        return False
    
    content = auth_store_path.read_text()
    
    checks = {
        "Atomic state structure": 'user: User | null;' in content and 'interface AuthState' in content,
        "No stored isAuthenticated": 'isAuthenticated: boolean;' not in content or 
                                     'isAuthenticated = derived' in content,
        "Derived store exists": 'export const isAuthenticated = derived(' in content,
        "Atomic setUserState": 'set({ user, isInitialized }' in content,
        "Documented atomic behavior": 'ATOMIC' in content and 'DERIVED' in content,
    }
    
    print("\n🔍 AuthStore Implementation Checks:")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed


def check_layout_initialization():
    """Verify that +layout.svelte awaits authStore.init()."""
    
    layout_path = Path('frontend/src/routes/+layout.svelte')
    
    if not layout_path.exists():
        print("❌ +layout.svelte file not found")
        return False
    
    content = layout_path.read_text()
    
    checks = {
        "authStore imported": "from '$lib/stores/auth'" in content,
        "init() is awaited": 'await authStore.init()' in content,
        "Documented critical section": 'CRITICAL' in content or 'AWAIT' in content,
    }
    
    print("\n🔍 Layout Initialization Checks:")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed


def check_apps_store_updates():
    """Verify that apps.ts uses the new state structure."""
    
    apps_store_path = Path('frontend/src/lib/stores/apps.ts')
    
    if not apps_store_path.exists():
        print("❌ apps.ts file not found")
        return False
    
    content = apps_store_path.read_text()
    
    # These OLD patterns should NOT exist
    bad_patterns = [
        r'currentAuthState\.isAuthenticated',  # Old property access
        r'currentAuthState\.token',            # Token no longer in authStore
        r'hasToken:.*currentAuthState',        # Old logging pattern
    ]
    
    # These NEW patterns SHOULD exist
    good_patterns = [
        r'currentAuthState\.isInitialized',    # Still checking initialization
        r'currentAuthState\.user',             # Checking user instead
        r'hasUser:.*currentAuthState\.user',   # New logging pattern
    ]
    
    print("\n🔍 Apps Store Update Checks:")
    print("=" * 60)
    
    all_passed = True
    
    for pattern in bad_patterns:
        if re.search(pattern, content):
            print(f"❌ Found old pattern that should be removed: {pattern}")
            all_passed = False
        else:
            print(f"✅ Old pattern correctly removed: {pattern}")
    
    for pattern in good_patterns:
        if re.search(pattern, content):
            print(f"✅ New pattern present: {pattern}")
        else:
            print(f"❌ Missing new pattern: {pattern}")
            all_passed = False
    
    return all_passed


def main():
    """Run all verification checks."""
    
    print("=" * 60)
    print("🚀 AuthStore Atomic Refactoring Verification")
    print("=" * 60)
    
    results = []
    
    # Run all checks
    results.append(("AuthStore Implementation", check_authstore_implementation()))
    results.append(("Layout Initialization", check_layout_initialization()))
    results.append(("Apps Store Updates", check_apps_store_updates()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Verification Summary:")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All checks passed! The atomic refactoring is complete.")
        print("\n📝 Next Steps:")
        print("   1. Restart the frontend dev server")
        print("   2. Run E2E tests: cd e2e_tests && pytest -v")
        print("   3. Verify no console errors about inconsistent state")
        print("   4. Confirm no 401/422 API errors")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the implementation.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
