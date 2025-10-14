#!/usr/bin/env python3
"""
Quick test runner for the new delete app workflow test.

This script runs only the delete app tests to verify the implementation.
"""

import subprocess
import sys

def run_delete_tests():
    """Run only the delete app E2E tests."""
    
    print("=" * 80)
    print("🧪 Running Delete App E2E Tests (P0 - Critical)")
    print("=" * 80)
    print()
    
    # Run the delete workflow tests
    cmd = [
        "pytest",
        "e2e_tests/test_app_management.py::test_delete_app_workflow",
        "e2e_tests/test_app_management.py::test_delete_app_cancellation",
        "-v",  # Verbose
        "-s",  # Show print statements
        "--tb=short",  # Shorter traceback format
        "--color=yes"  # Colored output
    ]
    
    print("Running command:")
    print(" ".join(cmd))
    print()
    
    result = subprocess.run(cmd, cwd="/Users/fab/GitHub/proximity")
    
    print()
    print("=" * 80)
    if result.returncode == 0:
        print("✅ All delete app tests PASSED!")
    else:
        print("❌ Some delete app tests FAILED")
    print("=" * 80)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_delete_tests())
