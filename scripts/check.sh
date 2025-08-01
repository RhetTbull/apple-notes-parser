#!/bin/bash
# Simple shell script version of code quality checks
# Usage: ./scripts/check.sh [--with-tests]

set -e  # Exit on any error

echo "🚀 Running code quality checks for apple-notes-parser"

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "📦 Using uv for command execution"
    UV_RUN="uv run"
else
    echo "📦 Using direct python execution (uv not found)"
    UV_RUN=""
fi

echo ""
echo "🔍 Running Ruff linting with auto-fixes..."
$UV_RUN ruff check src/ --fix

echo ""
echo "🎨 Running Ruff formatting..."
$UV_RUN ruff format src/

echo ""
echo "🔍 Verifying Ruff linting (after fixes)..."
$UV_RUN ruff check src/

echo ""
echo "🔬 Running MyPy type checking..."
$UV_RUN mypy src/apple_notes_parser/

# Optional: Run tests if --with-tests is passed
if [[ "$1" == "--with-tests" ]]; then
    echo ""
    echo "🧪 Running test suite..."
    $UV_RUN pytest tests/ -v
fi

echo ""
echo "✅ All code quality checks completed successfully!"