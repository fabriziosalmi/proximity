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

# Install/update all dependencies from requirements.txt
# This ensures the test environment is always in sync.
echo "⚙️ Installing dependencies from requirements.txt..."
pip install -r requirements.txt

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
