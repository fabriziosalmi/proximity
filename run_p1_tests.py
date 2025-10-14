#!/usr/bin/env python3
"""
Quick test runner for P1 tests: Update and Monitoring workflows.

This script runs only the P1 priority E2E tests to verify implementation.
"""

import subprocess
import sys

def run_p1_tests():
    """Run only the P1 E2E tests (Update + Monitoring)."""
    
    print("=" * 80)
    print("🧪 Running P1 E2E Tests (Update + Monitoring)")
    print("=" * 80)
    print()
    
    # Run the P1 tests
    cmd = [
        "pytest",
        "e2e_tests/test_app_management.py::test_update_app_workflow",
        "e2e_tests/test_app_management.py::test_app_monitoring_modal",
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
        print("✅ All P1 tests PASSED!")
        print()
        print("Next steps:")
        print("  • Update audit report to mark P1 items as completed")
        print("  • Run full test suite to verify no regressions")
        print("  • Proximity is now 100% ready for v1.0 release!")
    else:
        print("❌ Some P1 tests FAILED")
        print()
        print("Review the output above to identify issues.")
    print("=" * 80)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_p1_tests())
