#!/bin/bash
# Simple E2E test runner for Proximity

set -e

echo "🧪 Proximity E2E Test Runner"
echo ""

# Check if services are running
if ! curl -k -s https://localhost:5173 > /dev/null 2>&1 || ! curl -k -s https://localhost:8000/api/health/ > /dev/null 2>&1; then
    echo "⚠️  Warning: Services may not be running"
    echo "   Run: docker-compose up --build"
    echo ""
fi

# Activate venv if not already active
if [[ -z "${VIRTUAL_ENV}" ]]; then
    source venv/bin/activate
fi

# Run tests based on argument
case "${1:-all}" in
    quick)
        echo "🚀 Running quick tests (minimal, no fixtures)..."
        pytest e2e_tests/ -v -k "minimal_without"
        ;;
    minimal)
        echo "🚀 Running minimal test suite..."
        pytest e2e_tests/test_minimal.py -v
        ;;
    smoke)
        echo "🚀 Running smoke tests..."
        pytest e2e_tests/ -v -m smoke
        ;;
    all)
        echo "🚀 Running all E2E tests..."
        pytest e2e_tests/ -v
        ;;
    *)
        echo "🚀 Running specific test: $1"
        pytest e2e_tests/ -v -k "$1"
        ;;
esac

echo ""
echo "✅ Test run complete!"
