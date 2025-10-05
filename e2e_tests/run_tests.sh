#!/bin/bash
# E2E Test Runner Script
# Uses virtual environment for isolation

set -e  # Exit on error

# Activate virtual environment
source "$(dirname "$0")/venv/bin/activate"

# Run pytest with provided arguments
# If no arguments, run all tests
if [ $# -eq 0 ]; then
    echo "Running all E2E tests..."
    pytest -v
else
    echo "Running tests with args: $@"
    pytest "$@"
fi
