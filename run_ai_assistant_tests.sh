#!/bin/bash
# AI Assistant Test Runner
#
# BUSINESS PURPOSE:
# Comprehensive test suite runner for AI assistant functionality.
# Runs unit, integration, lint, and E2E tests in sequence.
#
# USAGE:
#     ./run_ai_assistant_tests.sh [--unit] [--integration] [--e2e] [--lint] [--all]
#
# OPTIONS:
#     --unit          Run only unit tests
#     --integration   Run only integration tests
#     --e2e           Run only E2E tests
#     --lint          Run only lint checks
#     --all           Run all tests (default)
#     --verbose       Verbose output
#     --help          Show this help

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test flags
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_E2E=false
RUN_LINT=false
RUN_ALL=true
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        --e2e)
            RUN_E2E=true
            RUN_ALL=false
            shift
            ;;
        --lint)
            RUN_LINT=true
            RUN_ALL=false
            shift
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            head -n 20 "$0" | tail -n +2 | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# If --all is set, enable all tests
if [ "$RUN_ALL" = true ]; then
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_E2E=true
    RUN_LINT=true
fi

# Test results
UNIT_RESULT=0
INTEGRATION_RESULT=0
E2E_RESULT=0
LINT_RESULT=0

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          AI ASSISTANT COMPREHENSIVE TEST SUITE               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for required dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found. Please install Node.js${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

#############
# LINT TESTS
#############
if [ "$RUN_LINT" = true ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  RUNNING LINT CHECKS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # JavaScript lint
    echo -e "${YELLOW}Running ESLint on AI assistant module...${NC}"
    if npx eslint frontend/static/js/ai-assistant.js; then
        echo -e "${GREEN}✓ ESLint passed${NC}"
    else
        LINT_RESULT=1
        echo -e "${RED}✗ ESLint failed${NC}"
    fi
    echo ""

    # Python lint (flake8)
    if command -v flake8 &> /dev/null; then
        echo -e "${YELLOW}Running flake8 on Python scripts...${NC}"
        if flake8 scripts/generate_slide5_ai_assistant.py --max-line-length=120; then
            echo -e "${GREEN}✓ flake8 passed${NC}"
        else
            LINT_RESULT=1
            echo -e "${RED}✗ flake8 failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ flake8 not found, skipping Python lint${NC}"
    fi
    echo ""

    # Check for syntax errors
    echo -e "${YELLOW}Checking JavaScript syntax...${NC}"
    if node -c frontend/static/js/ai-assistant.js; then
        echo -e "${GREEN}✓ JavaScript syntax OK${NC}"
    else
        LINT_RESULT=1
        echo -e "${RED}✗ JavaScript syntax error${NC}"
    fi
    echo ""

    echo -e "${YELLOW}Checking Python syntax...${NC}"
    if python3 -m py_compile scripts/generate_slide5_ai_assistant.py; then
        echo -e "${GREEN}✓ Python syntax OK${NC}"
    else
        LINT_RESULT=1
        echo -e "${RED}✗ Python syntax error${NC}"
    fi
    echo ""
fi

##############
# UNIT TESTS
##############
if [ "$RUN_UNIT" = true ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  RUNNING UNIT TESTS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # JavaScript unit tests (Jest)
    echo -e "${YELLOW}Running Jest unit tests...${NC}"
    if [ "$VERBOSE" = true ]; then
        npx jest tests/unit/frontend/test_ai_assistant.test.js --verbose --no-coverage
    else
        npx jest tests/unit/frontend/test_ai_assistant.test.js --no-coverage
    fi
    UNIT_RESULT=$?

    if [ $UNIT_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ JavaScript unit tests passed${NC}"
    else
        echo -e "${RED}✗ JavaScript unit tests failed${NC}"
    fi
    echo ""

    # Python unit tests (pytest)
    echo -e "${YELLOW}Running Python unit tests...${NC}"
    if [ "$VERBOSE" = true ]; then
        python3 -m pytest tests/unit/scripts/test_generate_slide5.py -v
    else
        python3 -m pytest tests/unit/scripts/test_generate_slide5.py
    fi
    PYTHON_UNIT_RESULT=$?

    if [ $PYTHON_UNIT_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Python unit tests passed${NC}"
    else
        echo -e "${RED}✗ Python unit tests failed${NC}"
        UNIT_RESULT=$PYTHON_UNIT_RESULT
    fi
    echo ""
fi

######################
# INTEGRATION TESTS
######################
if [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  RUNNING INTEGRATION TESTS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    echo -e "${YELLOW}Running AI assistant integration tests...${NC}"
    if [ "$VERBOSE" = true ]; then
        HEADLESS=true pytest tests/integration/test_ai_assistant_integration.py -v
    else
        HEADLESS=true pytest tests/integration/test_ai_assistant_integration.py
    fi
    INTEGRATION_RESULT=$?

    if [ $INTEGRATION_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Integration tests passed${NC}"
    else
        echo -e "${RED}✗ Integration tests failed${NC}"
    fi
    echo ""
fi

##############
# E2E TESTS
##############
if [ "$RUN_E2E" = true ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  RUNNING E2E TESTS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    echo -e "${YELLOW}Running AI assistant E2E tests...${NC}"
    if [ "$VERBOSE" = true ]; then
        HEADLESS=true TEST_BASE_URL=https://localhost:3000 pytest tests/e2e/test_ai_assistant_e2e.py -v
    else
        HEADLESS=true TEST_BASE_URL=https://localhost:3000 pytest tests/e2e/test_ai_assistant_e2e.py
    fi
    E2E_RESULT=$?

    if [ $E2E_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ E2E tests passed${NC}"
    else
        echo -e "${RED}✗ E2E tests failed${NC}"
    fi
    echo ""
fi

##############
# SUMMARY
##############
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  TEST SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

TOTAL_FAILURES=0

if [ "$RUN_LINT" = true ]; then
    if [ $LINT_RESULT -eq 0 ]; then
        echo -e "Lint:        ${GREEN}✓ PASSED${NC}"
    else
        echo -e "Lint:        ${RED}✗ FAILED${NC}"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
fi

if [ "$RUN_UNIT" = true ]; then
    if [ $UNIT_RESULT -eq 0 ]; then
        echo -e "Unit:        ${GREEN}✓ PASSED${NC}"
    else
        echo -e "Unit:        ${RED}✗ FAILED${NC}"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
fi

if [ "$RUN_INTEGRATION" = true ]; then
    if [ $INTEGRATION_RESULT -eq 0 ]; then
        echo -e "Integration: ${GREEN}✓ PASSED${NC}"
    else
        echo -e "Integration: ${RED}✗ FAILED${NC}"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
fi

if [ "$RUN_E2E" = true ]; then
    if [ $E2E_RESULT -eq 0 ]; then
        echo -e "E2E:         ${GREEN}✓ PASSED${NC}"
    else
        echo -e "E2E:         ${RED}✗ FAILED${NC}"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
fi

echo ""

if [ $TOTAL_FAILURES -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                 ALL TESTS PASSED! ✓                          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              $TOTAL_FAILURES TEST SUITE(S) FAILED ✗                      ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
