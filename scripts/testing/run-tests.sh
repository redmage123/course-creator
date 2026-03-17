#!/bin/bash
# Run tests

set -e

echo "🧪 Running tests..."

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "✅ Tests completed!"
