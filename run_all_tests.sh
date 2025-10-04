#!/bin/bash

################################################################################
# Proximity - Unified Test Runner
# 
# Runs both backend unit tests AND E2E tests in sequence
# Usage: ./run_all_tests.sh [options]
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_BACKEND=true
RUN_E2E=true
HEADED=false
VERBOSE=false
BACKEND_RUNNING=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            RUN_E2E=false
            shift
            ;;
        --e2e-only)
            RUN_BACKEND=false
            shift
            ;;
        --headed)
            HEADED=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --backend-running)
            BACKEND_RUNNING=true
            shift
            ;;
        -h|--help)
            echo "Usage: ./run_all_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --backend-only        Run only backend unit tests"
            echo "  --e2e-only           Run only E2E tests"
            echo "  --headed             Run E2E tests with visible browser"
            echo "  -v, --verbose        Verbose output"
            echo "  --backend-running    Skip starting backend (already running)"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_all_tests.sh                    # Run all tests"
            echo "  ./run_all_tests.sh --backend-only     # Only unit tests"
            echo "  ./run_all_tests.sh --e2e-only --headed # Only E2E with browser"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

################################################################################
# Main Script
################################################################################

print_header "Proximity Unified Test Suite"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

BACKEND_PID=""
TESTS_FAILED=false

# Cleanup function
cleanup() {
    if [[ -n "$BACKEND_PID" ]]; then
        print_info "Stopping backend server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
        print_success "Backend stopped"
    fi
}

trap cleanup EXIT INT TERM

################################################################################
# 1. Backend Unit Tests
################################################################################

if [[ "$RUN_BACKEND" == true ]]; then
    print_header "Running Backend Unit Tests"
    
    cd tests
    
    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Please install: pip install pytest"
        exit 1
    fi
    
    # Run backend tests
    print_info "Executing backend test suite..."
    
    if [[ "$VERBOSE" == true ]]; then
        pytest -v --tb=short || TESTS_FAILED=true
    else
        pytest --tb=short || TESTS_FAILED=true
    fi
    
    if [[ "$TESTS_FAILED" == false ]]; then
        print_success "Backend unit tests PASSED"
    else
        print_error "Backend unit tests FAILED"
    fi
    
    cd "$SCRIPT_DIR"
fi

################################################################################
# 2. E2E Tests
################################################################################

if [[ "$RUN_E2E" == true ]]; then
    print_header "Running E2E Tests"
    
    # Start backend if not already running
    if [[ "$BACKEND_RUNNING" == false ]]; then
        print_info "Starting backend server..."
        cd backend
        python3 main.py > ../backend.log 2>&1 &
        BACKEND_PID=$!
        cd "$SCRIPT_DIR"
        
        # Wait for backend to be ready
        print_info "Waiting for backend to be ready..."
        for i in {1..30}; do
            if curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then
                print_success "Backend is ready (PID: $BACKEND_PID)"
                break
            fi
            if [[ $i -eq 30 ]]; then
                print_error "Backend failed to start after 30 seconds"
                print_info "Check backend.log for details"
                exit 1
            fi
            sleep 1
        done
    else
        print_info "Using already running backend server"
    fi
    
    cd e2e_tests
    
    # Check if playwright is installed
    if ! command -v playwright &> /dev/null; then
        print_error "playwright not found. Please install: pip install playwright && playwright install chromium"
        exit 1
    fi
    
    # Build pytest command
    PYTEST_CMD="pytest"
    
    if [[ "$HEADED" == true ]]; then
        PYTEST_CMD="$PYTEST_CMD --browser chromium --headed"
    else
        PYTEST_CMD="$PYTEST_CMD --browser chromium"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        PYTEST_CMD="$PYTEST_CMD -v"
    fi
    
    # Run E2E tests
    print_info "Executing E2E test suite..."
    print_info "Command: $PYTEST_CMD"
    
    eval "$PYTEST_CMD" || TESTS_FAILED=true
    
    if [[ "$TESTS_FAILED" == false ]]; then
        print_success "E2E tests PASSED"
    else
        print_error "E2E tests FAILED"
    fi
    
    cd "$SCRIPT_DIR"
fi

################################################################################
# Summary
################################################################################

print_header "Test Results Summary"

if [[ "$TESTS_FAILED" == false ]]; then
    print_success "ALL TESTS PASSED ✓"
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                   ║${NC}"
    echo -e "${GREEN}║        ✓ Test Suite Completed Successfully       ║${NC}"
    echo -e "${GREEN}║                                                   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 0
else
    print_error "SOME TESTS FAILED ✗"
    echo ""
    echo -e "${RED}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                   ║${NC}"
    echo -e "${RED}║           ✗ Test Suite Failed                     ║${NC}"
    echo -e "${RED}║                                                   ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 1
fi
