#!/bin/bash

# Course Creator Platform Test Runner
# This script runs comprehensive tests on the software engineering agent

set -e

echo "🧪 Course Creator Platform Test Suite"
echo "======================================"

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY environment variable not set"
    echo "   Some tests may fail without a valid API key"
    echo ""
fi

# Default values
TEST_DIR=""
KEEP_FILES=false
OUTPUT_REPORT=""
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --test-dir)
            TEST_DIR="$2"
            shift 2
            ;;
        --keep-files)
            KEEP_FILES=true
            shift
            ;;
        --output-report)
            OUTPUT_REPORT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --test-dir DIR       Use specific test directory"
            echo "  --keep-files         Keep test files after completion"
            echo "  --output-report FILE Save test report to file"
            echo "  --verbose            Enable verbose output"
            echo "  --help               Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  ANTHROPIC_API_KEY    Required for full agent testing"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
CMD="python3 tools/code-generation/test_agent.py"

if [ ! -z "$TEST_DIR" ]; then
    CMD="$CMD --test-dir $TEST_DIR"
fi

if [ "$KEEP_FILES" = true ]; then
    CMD="$CMD --keep-files"
fi

if [ ! -z "$OUTPUT_REPORT" ]; then
    CMD="$CMD --output-report $OUTPUT_REPORT"
fi

# Run tests
echo "🚀 Running test suite..."
echo "Command: $CMD"
echo ""

if $VERBOSE; then
    $CMD
else
    $CMD 2>&1
fi

TEST_EXIT_CODE=$?

echo ""
echo "======================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed successfully!"
else
    echo "❌ Some tests failed. Check the output above for details."
fi

if [ ! -z "$OUTPUT_REPORT" ]; then
    echo "📄 Test report saved to: $OUTPUT_REPORT"
fi

echo ""
echo "💡 Tips:"
echo "  - Use --keep-files to inspect generated files"
echo "  - Use --output-report to save detailed results"
echo "  - Set ANTHROPIC_API_KEY for full agent testing"

exit $TEST_EXIT_CODE