#!/bin/bash
# Quick script to run System Configuration E2E Tests
# TDD RED Phase - Expected: 25/25 FAIL initially

set -e

echo "=========================================="
echo "System Configuration E2E Test Suite"
echo "TDD RED Phase - Tests should FAIL initially"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi
echo "✅ Docker installed"

# Check Docker daemon
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running. Please start Docker."
    exit 1
fi
echo "✅ Docker daemon running"

# Check Python packages
echo "Checking Python packages..."
python3 -c "import pytest, docker, httpx, redis, psycopg2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing Python packages. Installing..."
    pip install pytest docker httpx redis psycopg2-binary cryptography
fi
echo "✅ Python packages installed"

echo ""
echo "=========================================="
echo "Running tests..."
echo "=========================================="
echo ""

# Run tests with verbose output
pytest tests/e2e/test_system_configuration.py -v --tb=short

echo ""
echo "=========================================="
echo "Test run complete!"
echo "=========================================="
echo ""
echo "Expected in RED phase: 25/25 FAIL"
echo "Next step: Implement system configuration to make tests pass (GREEN phase)"
