#!/bin/bash

# SOTA standard: Make the script robust by changing to its own directory first.
cd "$(dirname "$0")"

# Quick Start Script for E2E Tests
# This script sets up the environment and runs the tests

set -e

echo "🧪 Proximity 2.0 - E2E Test Suite Setup & Run"
echo "=============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the e2e_tests directory"
    exit 1
fi

# Check if Docker stack is running
echo "🔍 Checking if Docker stack is running..."
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "⚠️  Backend not responding at http://localhost:8000"
    echo "   Starting Docker stack..."
    # Go to project root to run docker-compose
    (cd .. && docker-compose up -d)
    echo "   Waiting 30 seconds for services to start..."
    sleep 30
else
    echo "✅ Backend is running"
fi

# Define venv executable paths for robustness
VENV_DIR="venv"

# SOTA standard: Always start with a fresh virtual environment
echo "🔥 Removing old virtual environment to ensure a clean state..."
rm -rf "$VENV_DIR"

echo "📦 Creating fresh virtual environment..."
python3 -m venv "$VENV_DIR"

PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"
PYTEST="$VENV_DIR/bin/pytest"
PLAYWRIGHT="$VENV_DIR/bin/playwright"

# Install dependencies using the venv pip
echo "📦 Installing/updating dependencies into venv..."
"$PIP" install -q --upgrade pip
"$PIP" install -q -r requirements.txt

# Install Playwright browsers if not already installed
echo "🎭 Installing Playwright browsers..."
"$PLAYWRIGHT" install

# Create test-results directory if it doesn't exist
mkdir -p test-results/videos

echo ""
echo "=============================================="
echo "✅ Setup complete! Running tests..."
echo "=============================================="
echo ""

# Run tests with the venv pytest
"$PYTEST" -v "$@"

TEST_EXIT_CODE=$?

echo ""
echo "=============================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Check output above."
    echo "   Tip: Run with --headed to see the browser"
    echo "   Tip: Run with --slowmo 1000 to slow down actions"
fi
echo "=============================================="

exit $TEST_EXIT_CODE