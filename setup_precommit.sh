#!/bin/bash

# Pre-commit Hooks Setup Script for Proximity Project
# 
# This script helps you install and configure pre-commit hooks
# with a gradual activation strategy.
#
# Usage:
#   ./setup_precommit.sh            # Install and activate Phase 1
#   ./setup_precommit.sh --phase2   # Activate backend test guardian
#   ./setup_precommit.sh --phase3   # Activate E2E test guardian
#   ./setup_precommit.sh --check    # Check current status

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if we're in the repository root
if [ ! -f ".pre-commit-config.yaml" ]; then
    print_error "Error: .pre-commit-config.yaml not found!"
    echo "Please run this script from the repository root."
    exit 1
fi

# Function to check Python/pip availability
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python not found! Please install Python 3.7+"
        exit 1
    fi
    
    print_success "Found Python: $($PYTHON_CMD --version)"
}

# Function to install pre-commit
install_precommit() {
    print_header "Phase 1: Installing Pre-commit Framework"
    
    print_info "Installing pre-commit from requirements.txt..."
    $PYTHON_CMD -m pip install -r requirements.txt
    
    print_success "Pre-commit installed successfully"
    
    print_info "Installing Git hooks..."
    pre-commit install
    
    print_success "Git hooks installed successfully"
    
    print_header "Phase 1: Running Code Quality Hooks"
    
    print_info "Running all hooks on all files (this may take a moment)..."
    if pre-commit run --all-files; then
        print_success "All code quality hooks passed!"
    else
        print_warning "Some files were auto-fixed by hooks"
        print_info "Review changes with: git diff"
        print_info "Commit changes with: git add . && git commit -m 'chore: Apply code quality fixes'"
    fi
    
    print_header "✅ Phase 1 Complete: Code Quality Hooks Active"
    
    echo "What's active now:"
    echo "  - YAML/JSON validation"
    echo "  - Black code formatter"
    echo "  - Ruff linter"
    echo "  - Whitespace cleanup"
    echo "  - Large file detection"
    echo ""
    echo "Next steps:"
    echo "  - Phase 2: Activate backend tests when ready"
    echo "  - Run: ./setup_precommit.sh --phase2"
}

# Function to check test status
check_tests() {
    local test_dir=$1
    local test_name=$2
    
    print_info "Checking $test_name..."
    
    cd "$test_dir"
    if pytest -v --tb=short -q 2>&1 | tee /tmp/pytest_output.txt; then
        cd - > /dev/null
        print_success "$test_name: ALL PASSING ✅"
        return 0
    else
        cd - > /dev/null
        print_error "$test_name: SOME FAILING ❌"
        echo ""
        echo "Please fix failing tests before activating this hook."
        echo "Run tests manually: cd $test_dir && pytest -v"
        return 1
    fi
}

# Function to activate Phase 2 (backend tests)
activate_phase2() {
    print_header "Phase 2: Activating Backend Test Guardian"
    
    # Check if already activated
    if grep -q "^[[:space:]]*-[[:space:]]*repo:[[:space:]]*local" .pre-commit-config.yaml && \
       ! grep -q "^#.*pytest-backend" .pre-commit-config.yaml; then
        print_warning "Backend test guardian is already active!"
        return 0
    fi
    
    # Check backend tests
    if ! check_tests "tests" "Backend Tests"; then
        return 1
    fi
    
    print_info "Uncommenting backend test hook in .pre-commit-config.yaml..."
    
    # Uncomment the local repo section for pytest-backend
    sed -i.bak '/^#.*repo: local/,/^#.*always_run: true/ s/^#[[:space:]]*//' .pre-commit-config.yaml
    
    print_success "Backend test hook activated"
    
    print_info "Testing the hook..."
    if pre-commit run pytest-backend --all-files; then
        print_success "Backend test hook works correctly!"
    else
        print_error "Backend test hook failed!"
        print_warning "Reverting changes..."
        mv .pre-commit-config.yaml.bak .pre-commit-config.yaml
        return 1
    fi
    
    rm -f .pre-commit-config.yaml.bak
    
    print_header "✅ Phase 2 Complete: Backend Test Guardian Active"
    
    echo "What's active now:"
    echo "  - All Phase 1 hooks (code quality)"
    echo "  - Backend test suite (pytest tests/)"
    echo ""
    echo "Your commits are now protected against backend test failures!"
    echo ""
    echo "Next steps:"
    echo "  - Commit this change: git add .pre-commit-config.yaml"
    echo "  - Run: git commit -m 'chore: Activate backend test guardian'"
    echo "  - Phase 3: Activate E2E tests when ready"
    echo "  - Run: ./setup_precommit.sh --phase3"
}

# Function to activate Phase 3 (E2E tests)
activate_phase3() {
    print_header "Phase 3: Activating E2E Test Guardian"
    
    # Check if already activated
    if grep -q "^[[:space:]]*-[[:space:]]*id:[[:space:]]*pytest-e2e" .pre-commit-config.yaml && \
       ! grep -q "^#.*pytest-e2e" .pre-commit-config.yaml; then
        print_warning "E2E test guardian is already active!"
        return 0
    fi
    
    print_warning "⚠️  E2E tests require the backend to be running on localhost:8765"
    print_info "Make sure backend is running before proceeding..."
    
    read -p "Is the backend running? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Please start the backend first:"
        echo "  cd backend && python main.py"
        return 1
    fi
    
    # Check E2E tests
    if ! check_tests "e2e_tests" "E2E Tests"; then
        return 1
    fi
    
    print_info "Uncommenting E2E test hook in .pre-commit-config.yaml..."
    
    # Uncomment the pytest-e2e section
    sed -i.bak '/^#[[:space:]]*-[[:space:]]*id: pytest-e2e/,/^#[[:space:]]*verbose: true/ s/^#[[:space:]]*//' .pre-commit-config.yaml
    
    print_success "E2E test hook activated"
    
    print_info "Testing the hook (this will take several minutes)..."
    if pre-commit run pytest-e2e --all-files; then
        print_success "E2E test hook works correctly!"
    else
        print_error "E2E test hook failed!"
        print_warning "Reverting changes..."
        mv .pre-commit-config.yaml.bak .pre-commit-config.yaml
        return 1
    fi
    
    rm -f .pre-commit-config.yaml.bak
    
    print_header "✅ Phase 3 Complete: E2E Test Guardian Active"
    
    echo "What's active now:"
    echo "  - All Phase 1 hooks (code quality)"
    echo "  - Backend test suite (pytest tests/)"
    echo "  - E2E test suite (pytest e2e_tests/)"
    echo ""
    echo "🎉 FULL PROTECTION ACTIVE! 🎉"
    echo ""
    echo "Your commits are now protected against:"
    echo "  ✓ Code quality issues"
    echo "  ✓ Backend test failures"
    echo "  ✓ E2E test failures"
    echo ""
    echo "⚠️  Note: E2E tests can take 5-10 minutes"
    echo "For minor commits, you can use: git commit --no-verify"
    echo "(But use sparingly - CI/CD will still run all tests!)"
    echo ""
    echo "Commit this change:"
    echo "  git add .pre-commit-config.yaml"
    echo "  git commit -m 'chore: Activate E2E test guardian'"
}

# Function to check current status
check_status() {
    print_header "Pre-commit Hooks Status"
    
    # Check if pre-commit is installed
    if ! command -v pre-commit &> /dev/null; then
        print_error "Pre-commit not installed"
        echo "Run: ./setup_precommit.sh"
        return
    fi
    print_success "Pre-commit installed"
    
    # Check if hooks are installed
    if [ ! -f ".git/hooks/pre-commit" ]; then
        print_error "Git hooks not installed"
        echo "Run: pre-commit install"
        return
    fi
    print_success "Git hooks installed"
    
    # Check Phase 1 (code quality)
    if grep -q "black" .pre-commit-config.yaml; then
        print_success "Phase 1: Code Quality Hooks - ACTIVE ✅"
    else
        print_error "Phase 1: Code Quality Hooks - NOT ACTIVE ❌"
    fi
    
    # Check Phase 2 (backend tests)
    if grep -q "^[[:space:]]*-[[:space:]]*repo:[[:space:]]*local" .pre-commit-config.yaml && \
       ! grep -q "^#.*pytest-backend" .pre-commit-config.yaml; then
        print_success "Phase 2: Backend Test Guardian - ACTIVE ✅"
    else
        print_warning "Phase 2: Backend Test Guardian - READY (not activated)"
        echo "  Activate with: ./setup_precommit.sh --phase2"
    fi
    
    # Check Phase 3 (E2E tests)
    if grep -q "^[[:space:]]*-[[:space:]]*id:[[:space:]]*pytest-e2e" .pre-commit-config.yaml && \
       ! grep -q "^#.*pytest-e2e" .pre-commit-config.yaml; then
        print_success "Phase 3: E2E Test Guardian - ACTIVE ✅"
    else
        print_warning "Phase 3: E2E Test Guardian - READY (not activated)"
        echo "  Activate with: ./setup_precommit.sh --phase3"
    fi
    
    echo ""
    print_info "Manual commands:"
    echo "  Run all hooks: pre-commit run --all-files"
    echo "  Skip hooks: git commit --no-verify"
    echo "  Update hooks: pre-commit autoupdate"
    echo "  Clean cache: pre-commit clean"
}

# Main script logic
main() {
    check_python
    
    case "${1:-}" in
        --phase2)
            activate_phase2
            ;;
        --phase3)
            activate_phase3
            ;;
        --check|--status)
            check_status
            ;;
        --help|-h)
            echo "Pre-commit Hooks Setup Script"
            echo ""
            echo "Usage:"
            echo "  ./setup_precommit.sh           Install and activate Phase 1"
            echo "  ./setup_precommit.sh --phase2  Activate backend test guardian"
            echo "  ./setup_precommit.sh --phase3  Activate E2E test guardian"
            echo "  ./setup_precommit.sh --check   Check current status"
            echo "  ./setup_precommit.sh --help    Show this help"
            ;;
        *)
            install_precommit
            ;;
    esac
}

main "$@"
