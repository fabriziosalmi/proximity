#!/bin/bash

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
if ! curl -s http://localhost:8000/api/core/health > /dev/null 2>&1; then
    echo "⚠️  Backend not responding at http://localhost:8000"
    echo "   Starting Docker stack..."
    cd ..
    docker-compose up -d
    cd e2e_tests
    echo "   Waiting 30 seconds for services to start..."
    sleep 30
else
    echo "✅ Backend is running"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing/updating dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Install Playwright browsers if not already installed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "🎭 Installing Playwright browsers (this may take a few minutes)..."
    playwright install
else
    echo "✅ Playwright browsers already installed"
fi

# Create test-results directory if it doesn't exist
mkdir -p test-results/videos

echo ""
echo "=============================================="
echo "✅ Setup complete! Running tests..."
echo "=============================================="
echo ""

# Run tests with pytest
pytest -v "$@"

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
