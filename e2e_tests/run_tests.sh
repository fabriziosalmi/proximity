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

# Check if Docker stack is running and wait for it if necessary
HEALTH_URL="http://localhost:8000/api/health"
if ! curl -s --fail "$HEALTH_URL" > /dev/null 2>&1; then
    echo "⚠️  Backend not responding at $HEALTH_URL"
    echo "   Starting Docker stack..."
    (cd .. && docker-compose up -d --build --remove-orphans)
    
    echo "   Waiting for backend to become healthy..."
    WAIT_LIMIT=90 # 90 seconds timeout
    WAIT_INTERVAL=5
    ELAPSED=0
    
    while ! curl -s --fail "$HEALTH_URL" > /dev/null 2>&1; do
        if [ $ELAPSED -ge $WAIT_LIMIT ]; then
            echo "❌ Timeout: Backend did not become healthy within $WAIT_LIMIT seconds."
            docker-compose logs backend
            exit 1
        fi
        echo "   ... still waiting ($ELAPSED/$WAIT_LIMIT seconds)"
        sleep $WAIT_INTERVAL
        ELAPSED=$((ELAPSED + WAIT_INTERVAL))
    done
fi
echo "✅ Backend is healthy and running at $HEALTH_URL"


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

# Install Playwright browsers
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
