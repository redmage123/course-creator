#!/bin/bash
# Run Demo Player E2E Tests
#
# Usage:
#   ./run_demo_player_tests.sh              # Run all tests
#   ./run_demo_player_tests.sh -k "video"   # Run tests matching "video"
#   HEADLESS=true ./run_demo_player_tests.sh # Run in headless mode

echo "========================================================================"
echo "🧪 DEMO PLAYER E2E TESTS"
echo "========================================================================"
echo ""

# Set default base URL
export TEST_BASE_URL=${TEST_BASE_URL:-"https://localhost:3000"}

# Set headless mode
export HEADLESS=${HEADLESS:-"false"}

echo "Configuration:"
echo "  - Base URL: $TEST_BASE_URL"
echo "  - Headless: $HEADLESS"
echo ""

# Check if services are running
echo "Checking if services are running..."
if curl -k -s "${TEST_BASE_URL}/demo-player.html" > /dev/null 2>&1; then
    echo "✓ Frontend is accessible"
else
    echo "❌ Frontend is not accessible at $TEST_BASE_URL"
    echo ""
    echo "Please start the services first:"
    echo "  docker-compose up -d"
    echo ""
    exit 1
fi

echo ""
echo "========================================================================"
echo "Running tests..."
echo "========================================================================"
echo ""

# Run pytest with provided arguments
cd /home/bbrelin/course-creator
pytest tests/e2e/test_demo_player.py -v --tb=short "$@"

# Capture exit code
EXIT_CODE=$?

echo ""
echo "========================================================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
else
    echo "❌ SOME TESTS FAILED"
fi

echo "========================================================================"
echo ""

exit $EXIT_CODE
