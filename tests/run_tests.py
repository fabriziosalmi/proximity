#!/usr/bin/env python3
"""
Main test runner for Proximity test suite.
Executes all tests and provides detailed reporting.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def print_banner(text: str, char: str = "="):
    """Print a banner with text."""
    width = 80
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}\n")


def run_tests():
    """Run the complete test suite."""

    print_banner("PROXIMITY TEST SUITE", "=")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Get the tests directory
    tests_dir = Path(__file__).parent

    # Test configuration
    pytest_args = [
        "pytest",
        str(tests_dir),
        "-v",                          # Verbose output
        "--tb=short",                  # Shorter traceback format
        "--color=yes",                 # Colored output
        "-W", "ignore::DeprecationWarning",  # Ignore deprecation warnings
        "--strict-markers",            # Strict marker checking
        "-ra",                         # Show summary of all test outcomes
    ]

    print("Running pytest with configuration:")
    print(f"  Test directory: {tests_dir}")
    print(f"  Arguments: {' '.join(pytest_args[2:])}\n")

    # Count test files
    test_files = list(tests_dir.glob("test_*.py"))
    print(f"Found {len(test_files)} test files:")
    for test_file in sorted(test_files):
        print(f"  • {test_file.name}")
    print()

    print_banner("TEST EXECUTION", "-")

    try:
        # Run pytest
        result = subprocess.run(
            pytest_args,
            cwd=tests_dir.parent,
            capture_output=False,
            text=True
        )

        print_banner("TEST RESULTS", "-")

        if result.returncode == 0:
            print("✅ ALL TESTS PASSED!")
            print("\nTest suite completed successfully.")
            return 0
        elif result.returncode == 1:
            print("❌ SOME TESTS FAILED")
            print("\nPlease review the output above for details.")
            return 1
        elif result.returncode == 2:
            print("⚠️  TEST EXECUTION INTERRUPTED")
            print("\nTest execution was interrupted or had errors.")
            return 2
        elif result.returncode == 3:
            print("⚠️  INTERNAL ERROR")
            print("\nPytest encountered an internal error.")
            return 3
        elif result.returncode == 4:
            print("⚠️  USAGE ERROR")
            print("\nPytest was invoked incorrectly.")
            return 4
        elif result.returncode == 5:
            print("⚠️  NO TESTS COLLECTED")
            print("\nNo tests were found to execute.")
            return 5
        else:
            print(f"⚠️  UNKNOWN EXIT CODE: {result.returncode}")
            return result.returncode

    except FileNotFoundError:
        print("❌ ERROR: pytest not found!")
        print("\nPlease install pytest:")
        print("  pip install pytest pytest-asyncio")
        return 1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 1
    finally:
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_banner("", "=")


def run_specific_test(test_file: str):
    """Run a specific test file."""

    print_banner(f"RUNNING: {test_file}", "=")

    tests_dir = Path(__file__).parent
    test_path = tests_dir / test_file

    if not test_path.exists():
        print(f"❌ ERROR: Test file not found: {test_path}")
        return 1

    pytest_args = [
        "pytest",
        str(test_path),
        "-v",
        "--tb=short",
        "--color=yes",
    ]

    try:
        result = subprocess.run(
            pytest_args,
            cwd=tests_dir.parent,
            capture_output=False,
            text=True
        )
        return result.returncode
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 1


def show_coverage():
    """Run tests with coverage reporting."""

    print_banner("TEST COVERAGE REPORT", "=")

    tests_dir = Path(__file__).parent

    pytest_args = [
        "pytest",
        str(tests_dir),
        "--cov=backend",
        "--cov-report=html",
        "--cov-report=term",
        "-v",
    ]

    print("Running tests with coverage analysis...\n")

    try:
        result = subprocess.run(
            pytest_args,
            cwd=tests_dir.parent,
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print("\n✅ Coverage report generated!")
            print("   HTML report: htmlcov/index.html")

        return result.returncode
    except FileNotFoundError:
        print("❌ ERROR: pytest-cov not found!")
        print("\nPlease install pytest-cov:")
        print("  pip install pytest-cov")
        return 1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 1


def list_tests():
    """List all available tests."""

    print_banner("AVAILABLE TESTS", "=")

    tests_dir = Path(__file__).parent

    pytest_args = [
        "pytest",
        str(tests_dir),
        "--collect-only",
        "-q",
    ]

    try:
        subprocess.run(
            pytest_args,
            cwd=tests_dir.parent,
            capture_output=False,
            text=True
        )
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 1

    return 0


def show_help():
    """Show help message."""

    help_text = """
PROXIMITY TEST RUNNER
=====================

Usage:
  python run_tests.py [OPTIONS]

Options:
  (no args)         Run all tests
  --file <name>     Run specific test file
  --coverage        Run tests with coverage report
  --list            List all available tests
  --help, -h        Show this help message

Examples:
  python run_tests.py
  python run_tests.py --file test_auth_service.py
  python run_tests.py --coverage
  python run_tests.py --list

Test Files:
  - test_database_models.py        Database model tests (User, App, Logs)
  - test_database_transactions.py  Transaction safety and ACID tests
  - test_auth_service.py           Authentication and user management tests
  - test_app_service.py            Application service tests
  - test_proxmox_service.py        Proxmox integration tests
  - test_api_endpoints.py          API endpoint tests
  - test_integration.py            Integration and workflow tests
  - test_error_handling.py         Error handling and edge cases
  - test_catalog_service.py        Catalog management tests

Requirements:
  pip install pytest pytest-asyncio pytest-cov
"""

    print(help_text)


def main():
    """Main entry point."""

    args = sys.argv[1:]

    if not args:
        # Run all tests
        return run_tests()

    if args[0] in ["--help", "-h"]:
        show_help()
        return 0

    if args[0] == "--list":
        return list_tests()

    if args[0] == "--coverage":
        return show_coverage()

    if args[0] == "--file":
        if len(args) < 2:
            print("❌ ERROR: --file requires a test file name")
            print("Example: python run_tests.py --file test_auth_service.py")
            return 1
        return run_specific_test(args[1])

    print(f"❌ ERROR: Unknown option: {args[0]}")
    print("Run with --help for usage information")
    return 1


if __name__ == "__main__":
    sys.exit(main())
