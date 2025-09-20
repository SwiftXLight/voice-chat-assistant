#!/bin/bash

# Simple test runner script for the backend

echo "🧪 Running Backend Tests..."
echo "=========================="

# Run tests with coverage if available
if poetry run python -c "import pytest_cov" 2>/dev/null; then
    echo "Running tests with coverage..."
    poetry run pytest --cov=main --cov-report=term-missing -v
else
    echo "Running tests without coverage..."
    poetry run pytest -v
fi

echo ""
echo "✅ Tests completed!"
