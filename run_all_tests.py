#!/usr/bin/env python3
"""
Proximity - Unified Test Runner (Python version)

Cross-platform script to run both backend unit tests and E2E tests.
Usage: python run_all_tests.py [options]
"""

import sys
import os
import time
import subprocess
import argparse
import signal
from pathlib import Path


# ANSI color codes
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_header(text):
    """Print a formatted header."""
    print()
    print(f"{Colors.BLUE}{'═' * 63}{Colors.NC}")
    print(f"{Colors.BLUE}  {text}{Colors.NC}")
    print(f"{Colors.BLUE}{'═' * 63}{Colors.NC}")
    print()


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.NC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.NC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.NC}")


def run_command(cmd, cwd=None, verbose=False):
    """Run a shell command and return success status."""
    try:
        if verbose:
            result = subprocess.run(cmd, cwd=cwd, shell=True, check=True, text=True)
        else:
            result = subprocess.run(
                cmd, cwd=cwd, shell=True, check=True, text=True, capture_output=True
            )
        return True
    except subprocess.CalledProcessError as e:
        if not verbose:
            print(e.stdout)
            print(e.stderr)
        return False


def check_backend_ready(max_attempts=30):
    """Check if backend is responding."""
    import urllib.request
    import urllib.error

    for i in range(max_attempts):
        try:
            urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=1)
            return True
        except (urllib.error.URLError, TimeoutError):
            if i < max_attempts - 1:
                time.sleep(1)
            else:
                return False
    return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Run Proximity test suites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                    # Run all tests
  python run_all_tests.py --backend-only     # Only unit tests
  python run_all_tests.py --e2e-only --headed # Only E2E with browser
        """,
    )

    parser.add_argument("--backend-only", action="store_true", help="Run only backend unit tests")
    parser.add_argument("--e2e-only", action="store_true", help="Run only E2E tests")
    parser.add_argument("--headed", action="store_true", help="Run E2E tests with visible browser")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--backend-running", action="store_true", help="Skip starting backend (already running)"
    )

    args = parser.parse_args()

    # Determine what to run
    run_backend = not args.e2e_only
    run_e2e = not args.backend_only

    # Setup paths
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)

    backend_pid = None
    tests_failed = False

    def cleanup(signum=None, frame=None):
        """Cleanup function to stop backend."""
        nonlocal backend_pid
        if backend_pid:
            print_info(f"Stopping backend server (PID: {backend_pid})...")
            try:
                os.kill(backend_pid, signal.SIGTERM)
                print_success("Backend stopped")
            except ProcessLookupError:
                pass
        if signum:
            sys.exit(1)

    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        print_header("Proximity Unified Test Suite")

        # ========================================================================
        # 1. Backend Unit Tests
        # ========================================================================

        if run_backend:
            print_header("Running Backend Unit Tests")

            tests_dir = script_dir / "tests"

            # Check if pytest is available
            if not run_command("pytest --version", verbose=False):
                print_error("pytest not found. Please install: pip install pytest")
                return 1

            # Run backend tests
            print_info("Executing backend test suite...")

            cmd = "pytest -v --tb=short" if args.verbose else "pytest --tb=short"

            if not run_command(cmd, cwd=tests_dir, verbose=args.verbose):
                tests_failed = True
                print_error("Backend unit tests FAILED")
            else:
                print_success("Backend unit tests PASSED")

        # ========================================================================
        # 2. E2E Tests
        # ========================================================================

        if run_e2e:
            print_header("Running E2E Tests")

            # Start backend if not already running
            if not args.backend_running:
                print_info("Starting backend server...")
                backend_dir = script_dir / "backend"

                # Start backend in background
                with open(script_dir / "backend.log", "w") as log_file:
                    backend_process = subprocess.Popen(
                        [sys.executable, "main.py"],
                        cwd=backend_dir,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                    )
                    backend_pid = backend_process.pid

                # Wait for backend to be ready
                print_info("Waiting for backend to be ready...")
                if check_backend_ready():
                    print_success(f"Backend is ready (PID: {backend_pid})")
                else:
                    print_error("Backend failed to start after 30 seconds")
                    print_info("Check backend.log for details")
                    cleanup()
                    return 1
            else:
                print_info("Using already running backend server")

            e2e_dir = script_dir / "e2e_tests"

            # Check if playwright is installed
            if not run_command("playwright --version", verbose=False):
                print_error(
                    "playwright not found. Please install: pip install playwright && playwright install chromium"
                )
                cleanup()
                return 1

            # Build pytest command
            pytest_cmd = "pytest"

            if args.headed:
                pytest_cmd += " --browser chromium --headed"
            else:
                pytest_cmd += " --browser chromium"

            if args.verbose:
                pytest_cmd += " -v"

            # Run E2E tests
            print_info("Executing E2E test suite...")
            print_info(f"Command: {pytest_cmd}")

            if not run_command(pytest_cmd, cwd=e2e_dir, verbose=args.verbose):
                tests_failed = True
                print_error("E2E tests FAILED")
            else:
                print_success("E2E tests PASSED")

        # ========================================================================
        # Summary
        # ========================================================================

        print_header("Test Results Summary")

        if not tests_failed:
            print_success("ALL TESTS PASSED ✓")
            print()
            print(f"{Colors.GREEN}╔═══════════════════════════════════════════════════╗{Colors.NC}")
            print(f"{Colors.GREEN}║                                                   ║{Colors.NC}")
            print(f"{Colors.GREEN}║        ✓ Test Suite Completed Successfully       ║{Colors.NC}")
            print(f"{Colors.GREEN}║                                                   ║{Colors.NC}")
            print(f"{Colors.GREEN}╚═══════════════════════════════════════════════════╝{Colors.NC}")
            print()
            return 0
        else:
            print_error("SOME TESTS FAILED ✗")
            print()
            print(f"{Colors.RED}╔═══════════════════════════════════════════════════╗{Colors.NC}")
            print(f"{Colors.RED}║                                                   ║{Colors.NC}")
            print(f"{Colors.RED}║           ✗ Test Suite Failed                     ║{Colors.NC}")
            print(f"{Colors.RED}║                                                   ║{Colors.NC}")
            print(f"{Colors.RED}╚═══════════════════════════════════════════════════╝{Colors.NC}")
            print()
            return 1

    finally:
        cleanup()


if __name__ == "__main__":
    sys.exit(main())
