#!/bin/bash
# EPIC 0: Quick Start Execution Script
# This script provides quick commands for each phase of EPIC 0

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to run backend tests
run_backend_tests() {
    print_header "PILLAR 1: Running Backend Tests"
    cd tests
    
    echo "Running full test suite..."
    if pytest -v --tb=short; then
        print_success "All backend tests passed!"
        pytest --co -q | tail -1
    else
        print_error "Some backend tests failed. Check output above."
        return 1
    fi
    
    cd ..
}

# Function to run specific clone/config tests
run_clone_tests() {
    print_header "PILLAR 1: Running Clone/Config Tests"
    cd tests
    
    echo "Testing clone functionality..."
    pytest test_app_clone_config.py::TestCloneApp -v --tb=short
    
    echo -e "\nTesting config update functionality..."
    pytest test_app_clone_config.py::TestUpdateAppConfig -v --tb=short
    
    cd ..
}

# Function to check for warnings
check_warnings() {
    print_header "PILLAR 1: Checking for RuntimeWarnings"
    cd tests
    
    echo "Running tests with warning escalation..."
    if pytest -v --tb=short -W error::RuntimeWarning 2>&1 | tee warning_check.log; then
        print_success "No RuntimeWarnings found!"
    else
        print_warning "RuntimeWarnings detected. Check warning_check.log"
        return 1
    fi
    
    cd ..
}

# Function to run E2E tests
run_e2e_tests() {
    print_header "PILLAR 2: Running E2E Tests"
    cd e2e_tests
    
    echo "Running auth flow tests..."
    pytest test_auth_flow.py -v --tb=short
    
    echo -e "\nRunning navigation tests..."
    pytest test_navigation.py -v --tb=short
    
    echo -e "\nRunning core flow test..."
    pytest test_complete_core_flow.py -v --tb=short
    
    cd ..
}

# Function to run E2E auth tests multiple times
stress_test_auth() {
    print_header "PILLAR 2: Auth Fixture Stress Test"
    cd e2e_tests
    
    echo "Running auth tests 10 times to check for flakiness..."
    PASS_COUNT=0
    FAIL_COUNT=0
    
    for i in {1..10}; do
        echo -e "\n${BLUE}Run $i/10${NC}"
        if pytest test_auth_flow.py -v --tb=line -q; then
            PASS_COUNT=$((PASS_COUNT + 1))
            print_success "Run $i: PASSED"
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
            print_error "Run $i: FAILED"
        fi
    done
    
    echo -e "\n${BLUE}Stress Test Results:${NC}"
    echo -e "  Passed: ${GREEN}$PASS_COUNT/10${NC}"
    echo -e "  Failed: ${RED}$FAIL_COUNT/10${NC}"
    
    if [ $FAIL_COUNT -eq 0 ]; then
        print_success "Auth fixture is stable!"
    else
        print_warning "Auth fixture needs improvement (flaky)"
    fi
    
    cd ..
}

# Function to generate test report
generate_report() {
    print_header "Generating Test Status Report"
    
    REPORT_FILE="EPIC_0_STATUS_REPORT_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# EPIC 0 Status Report
**Generated:** $(date)

## Backend Tests Status
\`\`\`
$(cd tests && pytest --co -q 2>&1)
\`\`\`

## Backend Test Execution
\`\`\`
$(cd tests && pytest -v --tb=line 2>&1 | tail -30)
\`\`\`

## E2E Tests Status
\`\`\`
$(cd e2e_tests && pytest --co -q 2>&1)
\`\`\`

## Known Issues
- [ ] List issues found during testing
- [ ] Document blockers
- [ ] Note warnings

## Next Steps
1. [ ] Fix identified issues
2. [ ] Re-run test suite
3. [ ] Update this report
EOF

    print_success "Report generated: $REPORT_FILE"
}

# Function to show progress
show_progress() {
    print_header "EPIC 0 Progress Dashboard"
    
    echo -e "${BLUE}PILLAR 1: Backend Test Perfection${NC}"
    cd tests
    TOTAL_TESTS=$(pytest --co -q 2>&1 | grep "test" | wc -l | xargs)
    echo "  Total Tests: $TOTAL_TESTS"
    
    # Quick pass/fail count
    if pytest --co -q > /dev/null 2>&1; then
        echo -e "  ${GREEN}Collection: OK${NC}"
    else
        echo -e "  ${RED}Collection: FAILED${NC}"
    fi
    cd ..
    
    echo -e "\n${BLUE}PILLAR 2: E2E Test Reliability${NC}"
    cd e2e_tests
    E2E_TESTS=$(pytest --co -q 2>&1 | grep "test" | wc -l | xargs)
    echo "  Total Tests: $E2E_TESTS"
    cd ..
    
    echo -e "\n${BLUE}Quick Actions:${NC}"
    echo "  1. Run backend tests:        ./epic0_quick_start.sh backend"
    echo "  2. Run clone tests:          ./epic0_quick_start.sh clone"
    echo "  3. Check warnings:           ./epic0_quick_start.sh warnings"
    echo "  4. Run E2E tests:            ./epic0_quick_start.sh e2e"
    echo "  5. Stress test auth:         ./epic0_quick_start.sh stress"
    echo "  6. Generate report:          ./epic0_quick_start.sh report"
    echo "  7. Show this menu:           ./epic0_quick_start.sh progress"
}

# Main menu
case "${1:-help}" in
    backend)
        run_backend_tests
        ;;
    clone)
        run_clone_tests
        ;;
    warnings)
        check_warnings
        ;;
    e2e)
        run_e2e_tests
        ;;
    stress)
        stress_test_auth
        ;;
    report)
        generate_report
        ;;
    progress)
        show_progress
        ;;
    all)
        print_header "EPIC 0: Full Test Suite"
        run_backend_tests
        run_e2e_tests
        generate_report
        ;;
    help|*)
        echo -e "${BLUE}EPIC 0 Quick Start Script${NC}"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  backend   - Run all backend tests (pytest tests/)"
        echo "  clone     - Run clone/config tests specifically"
        echo "  warnings  - Check for RuntimeWarnings"
        echo "  e2e       - Run E2E test suite"
        echo "  stress    - Stress test auth fixture (10 runs)"
        echo "  report    - Generate test status report"
        echo "  progress  - Show EPIC 0 progress dashboard"
        echo "  all       - Run everything and generate report"
        echo ""
        echo "Examples:"
        echo "  $0 backend        # Run backend tests"
        echo "  $0 stress         # Check auth fixture stability"
        echo "  $0 progress       # Show current status"
        echo ""
        ;;
esac
