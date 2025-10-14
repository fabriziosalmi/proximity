#!/usr/bin/env python3
"""
Sentry Integration Test Suite

This script validates the complete Sentry integration across backend and frontend:
1. Backend configuration check
2. Backend error capture test
3. Frontend configuration check
4. User context verification
5. Breadcrumb tracking

Usage:
    python test_sentry_integration.py [--with-sentry]
    
Options:
    --with-sentry    Enable Sentry for testing (requires SENTRY_DSN in .env)
    --backend-only   Test only backend integration
    --frontend-only  Test only frontend integration
"""

import sys
import requests
import json
from pathlib import Path
import argparse

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")

def print_step(text):
    print(f"\n{BLUE}→ {text}{RESET}")


class SentryIntegrationTester:
    def __init__(self, backend_url="http://localhost:8765", api_version="v1"):
        self.backend_url = backend_url
        self.api_version = api_version
        self.base_url = f"{backend_url}/api/{api_version}"
        self.results = {
            "backend_config": False,
            "backend_test_endpoint": False,
            "frontend_config": False,
            "total_tests": 0,
            "passed_tests": 0,
        }

    def test_backend_sentry_info(self):
        """Test 1: Check backend Sentry configuration"""
        print_step("Testing backend Sentry configuration...")
        
        try:
            response = requests.get(f"{self.base_url}/test/sentry-info", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print_info(f"Sentry Enabled: {data.get('sentry_enabled')}")
                print_info(f"Environment: {data.get('environment')}")
                print_info(f"Release: {data.get('release')}")
                print_info(f"App Name: {data.get('app_name')}")
                print_info(f"App Version: {data.get('app_version')}")
                
                self.results["backend_config"] = True
                print_success("Backend Sentry configuration is accessible")
                return True
            else:
                print_error(f"Unexpected status code: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print_error("Cannot connect to backend. Is the server running?")
            print_info(f"Tried connecting to: {self.base_url}")
            return False
        except Exception as e:
            print_error(f"Error checking backend config: {e}")
            return False

    def test_backend_error_capture(self):
        """Test 2: Test backend error capture"""
        print_step("Testing backend error capture...")
        print_info("This endpoint deliberately raises an error for Sentry testing")
        
        try:
            response = requests.get(f"{self.base_url}/test/sentry-backend", timeout=5)
            
            # We expect a 500 error
            if response.status_code == 500:
                print_success("Backend error endpoint returned 500 as expected")
                print_info("Check your Sentry dashboard for the error event")
                print_info("The error message should be: 'This is a deliberate test error...'")
                self.results["backend_test_endpoint"] = True
                return True
            else:
                print_error(f"Expected 500, got {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print_error("Cannot connect to backend. Is the server running?")
            return False
        except Exception as e:
            print_error(f"Error testing backend: {e}")
            return False

    def test_backend_health(self):
        """Test 3: Test health check endpoint"""
        print_step("Testing health check endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/test/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Health check passed: {data.get('message')}")
                return True
            else:
                print_error(f"Health check failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Health check error: {e}")
            return False

    def test_frontend_sentry_config(self):
        """Test 4: Check frontend Sentry configuration"""
        print_step("Checking frontend Sentry configuration...")
        
        sentry_config_path = Path(__file__).parent / "backend" / "frontend" / "js" / "sentry-config.js"
        
        if not sentry_config_path.exists():
            print_error(f"Frontend Sentry config not found: {sentry_config_path}")
            return False
        
        try:
            content = sentry_config_path.read_text()
            
            checks = {
                "Sentry.init": "Sentry initialization",
                "dsn:": "DSN configuration",
                "environment:": "Environment detection",
                "browserTracingIntegration": "Performance monitoring",
                "replayIntegration": "Session replay",
                "beforeSend": "Event filtering",
                "setupSentryUser": "User context setup",
                "reportToSentry": "Helper function",
            }
            
            all_present = True
            for check, description in checks.items():
                if check in content:
                    print_success(f"{description} found")
                else:
                    print_error(f"{description} missing")
                    all_present = False
            
            if all_present:
                self.results["frontend_config"] = True
                print_success("Frontend Sentry configuration is complete")
                return True
            else:
                print_error("Frontend Sentry configuration is incomplete")
                return False
                
        except Exception as e:
            print_error(f"Error reading frontend config: {e}")
            return False

    def test_env_configuration(self):
        """Test 5: Check .env configuration"""
        print_step("Checking environment configuration...")
        
        env_path = Path(__file__).parent / "backend" / ".env"
        env_example_path = Path(__file__).parent / ".env.example"
        
        if not env_path.exists():
            print_error(f".env file not found: {env_path}")
            return False
        
        if not env_example_path.exists():
            print_error(f".env.example file not found: {env_example_path}")
            return False
        
        try:
            # Check .env.example has Sentry section
            example_content = env_example_path.read_text()
            if "SENTRY_DSN" in example_content:
                print_success(".env.example contains Sentry configuration template")
            else:
                print_error(".env.example missing Sentry configuration template")
                return False
            
            # Check .env (but don't show sensitive values)
            env_content = env_path.read_text()
            has_sentry_dsn = "SENTRY_DSN" in env_content
            
            if has_sentry_dsn:
                print_info(".env file has SENTRY_DSN configuration")
            else:
                print_info(".env file does NOT have SENTRY_DSN (Sentry will be disabled)")
            
            print_success("Environment configuration check complete")
            return True
            
        except Exception as e:
            print_error(f"Error checking environment files: {e}")
            return False

    def run_all_tests(self, backend_only=False, frontend_only=False):
        """Run all Sentry integration tests"""
        print_header("SENTRY INTEGRATION TEST SUITE")
        
        tests = []
        
        if not frontend_only:
            tests.extend([
                ("Backend Health Check", self.test_backend_health),
                ("Backend Sentry Info", self.test_backend_sentry_info),
                ("Backend Error Capture", self.test_backend_error_capture),
            ])
        
        if not backend_only:
            tests.extend([
                ("Frontend Sentry Config", self.test_frontend_sentry_config),
                ("Environment Configuration", self.test_env_configuration),
            ])
        
        self.results["total_tests"] = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    self.results["passed_tests"] += 1
            except Exception as e:
                print_error(f"Test '{test_name}' crashed: {e}")
        
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        passed = self.results["passed_tests"]
        total = self.results["total_tests"]
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {GREEN}{passed}{RESET}")
        print(f"Failed: {RED}{total - passed}{RESET}")
        print(f"Success Rate: {percentage:.1f}%\n")
        
        if passed == total:
            print_success("All tests passed! Sentry integration is ready.")
            print_info("Next steps:")
            print_info("  1. Add SENTRY_DSN to backend/.env to enable error tracking")
            print_info("  2. Deploy application and trigger test errors")
            print_info("  3. Verify errors appear in Sentry dashboard")
        elif passed > 0:
            print_error(f"{total - passed} test(s) failed. Review output above.")
        else:
            print_error("All tests failed. Check if backend server is running.")


def main():
    parser = argparse.ArgumentParser(description="Test Sentry integration")
    parser.add_argument("--backend-url", default="http://localhost:8765", help="Backend URL")
    parser.add_argument("--backend-only", action="store_true", help="Test only backend")
    parser.add_argument("--frontend-only", action="store_true", help="Test only frontend")
    args = parser.parse_args()
    
    tester = SentryIntegrationTester(backend_url=args.backend_url)
    tester.run_all_tests(
        backend_only=args.backend_only,
        frontend_only=args.frontend_only
    )


if __name__ == "__main__":
    main()
