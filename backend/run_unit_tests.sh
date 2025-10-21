#!/bin/bash
# Script per eseguire i test unitari del backend

set -e

echo "🧪 Running Backend Unit Tests"
echo "================================"

# Change to backend directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-django pytest-cov
fi

# Run tests
if [ $# -eq 0 ]; then
    echo "🚀 Running all unit tests..."
    python -m pytest tests/ -v
else
    echo "🚀 Running specific tests: $@"
    python -m pytest "$@" -v
fi

echo ""
echo "✅ Tests completed!"
