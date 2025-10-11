#!/bin/bash

###############################################################################
# Master Test Runner for Course Creator Platform
#
# BUSINESS CONTEXT:
# Orchestrates execution of all test suites including unit, integration,
# E2E, linting, and coverage reporting for comprehensive quality assurance.
#
# TECHNICAL IMPLEMENTATION:
# - Runs Python tests with pytest
# - Runs JavaScript tests with Jest
# - Executes linting checks
# - Generates consolidated coverage reports
# - Supports selective test execution
# - CI/CD friendly with exit codes
###############################################################################

set -e  # Exit on error

# Configure Python path for all services
export PYTHONPATH="services/analytics:services/content-management:services/content-storage:services/course-generator:services/course-management:services/demo-service:services/knowledge-graph-service:services/lab-manager:services/local-llm-service:services/metadata-service:services/nlp-preprocessing:services/organization-management:services/rag-service:services/user-management:$PYTHONPATH"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
UNIT_TESTS_PASSED=0
INTEGRATION_TESTS_PASSED=0
E2E_TESTS_PASSED=0
FRONTEND_TESTS_PASSED=0
LINT_PASSED=0

# Configuration
HEADLESS=${HEADLESS:-true}
COVERAGE=${COVERAGE:-true}
PARALLEL=${PARALLEL:-true}
VERBOSE=${VERBOSE:-false}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║    Course Creator Platform - Test Suite Runner       ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print section header
print_section() {
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Print info message
print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -u, --unit              Run unit tests only"
    echo "  -i, --integration       Run integration tests only"
    echo "  -e, --e2e               Run E2E tests only"
    echo "  -f, --frontend          Run frontend tests only"
    echo "  -l, --lint              Run linting only"
    echo "  -c, --coverage          Generate coverage reports (default: true)"
    echo "  --no-coverage           Skip coverage reporting"
    echo "  --headless              Run E2E tests in headless mode (default: true)"
    echo "  --headed                Run E2E tests in headed mode (see browser)"
    echo "  -v, --verbose           Verbose output"
    echo "  --parallel              Run tests in parallel (default: true)"
    echo "  --sequential            Run tests sequentially"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run all tests"
    echo "  $0 --unit               # Run only unit tests"
    echo "  $0 --e2e --headed       # Run E2E tests with visible browser"
    echo "  $0 --lint --no-coverage # Run linting without coverage"
}

# Parse command line arguments
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_E2E=false
RUN_FRONTEND=false
RUN_LINT=false
RUN_ALL=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -u|--unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        -i|--integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        -e|--e2e)
            RUN_E2E=true
            RUN_ALL=false
            shift
            ;;
        -f|--frontend)
            RUN_FRONTEND=true
            RUN_ALL=false
            shift
            ;;
        -l|--lint)
            RUN_LINT=true
            RUN_ALL=false
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --headed)
            HEADLESS=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --sequential)
            PARALLEL=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# If RUN_ALL, enable all test types
if [ "$RUN_ALL" = true ]; then
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_E2E=true
    RUN_FRONTEND=true
    RUN_LINT=true
fi

# Start time
START_TIME=$(date +%s)

print_banner

# Create reports directory
mkdir -p tests/reports
mkdir -p tests/reports/coverage
mkdir -p tests/reports/screenshots

print_info "Configuration:"
print_info "  - Coverage: $COVERAGE"
print_info "  - Headless: $HEADLESS"
print_info "  - Parallel: $PARALLEL"
print_info "  - Verbose: $VERBOSE"

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    print_info "Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    print_info "Activating virtual environment..."
    source venv/bin/activate
fi

###############################################################################
# Python Unit Tests
###############################################################################
if [ "$RUN_UNIT" = true ]; then
    print_section "Running Python Unit Tests"

    PYTEST_ARGS="-v tests/unit"

    if [ "$COVERAGE" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS --cov=services --cov-report=html:tests/reports/coverage/python --cov-report=term"
    fi

    if [ "$PARALLEL" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS -n auto"
    fi

    if [ "$VERBOSE" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS -vv"
    fi

    if pytest $PYTEST_ARGS; then
        UNIT_TESTS_PASSED=1
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
        UNIT_TESTS_PASSED=0
    fi
fi

###############################################################################
# Integration Tests
###############################################################################
if [ "$RUN_INTEGRATION" = true ]; then
    print_section "Running Integration Tests"

    PYTEST_ARGS="-v tests/integration -m integration"

    if [ "$COVERAGE" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS --cov=services --cov-append --cov-report=term"
    fi

    if pytest $PYTEST_ARGS; then
        INTEGRATION_TESTS_PASSED=1
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        INTEGRATION_TESTS_PASSED=0
    fi
fi

###############################################################################
# E2E Tests (Selenium)
###############################################################################
if [ "$RUN_E2E" = true ]; then
    print_section "Running E2E Tests (Selenium)"

    export HEADLESS=$HEADLESS

    PYTEST_ARGS="-v tests/e2e -m e2e --asyncio-mode=auto"

    if [ "$VERBOSE" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS -vv -s"
    fi

    if pytest $PYTEST_ARGS; then
        E2E_TESTS_PASSED=1
        print_success "E2E tests passed"
    else
        print_error "E2E tests failed"
        E2E_TESTS_PASSED=0
        print_info "Screenshots saved to: tests/reports/screenshots/"
    fi
fi

###############################################################################
# Frontend JavaScript Tests (Jest)
###############################################################################
if [ "$RUN_FRONTEND" = true ]; then
    print_section "Running Frontend JavaScript Tests"

    if command_exists npm; then
        JEST_ARGS=""

        if [ "$COVERAGE" = true ]; then
            JEST_ARGS="$JEST_ARGS --coverage"
        fi

        if [ "$VERBOSE" = true ]; then
            JEST_ARGS="$JEST_ARGS --verbose"
        fi

        if npm test -- $JEST_ARGS; then
            FRONTEND_TESTS_PASSED=1
            print_success "Frontend tests passed"
        else
            print_error "Frontend tests failed"
            FRONTEND_TESTS_PASSED=0
        fi
    else
        print_error "npm not found. Skipping frontend tests."
        print_info "Install Node.js and npm to run frontend tests"
    fi
fi

###############################################################################
# Linting
###############################################################################
if [ "$RUN_LINT" = true ]; then
    print_section "Running Linting Checks"

    # Python linting with flake8
    print_info "Running flake8..."
    if flake8 services/ --config=.flake8 --output-file=tests/reports/flake8-report.txt; then
        print_success "flake8 passed"
    else
        print_error "flake8 found issues"
        LINT_PASSED=0
    fi

    # Python linting with pylint (less strict)
    print_info "Running pylint..."
    if pylint services/ --rcfile=.pylintrc --output=tests/reports/pylint-report.txt || [ $? -le 4 ]; then
        print_success "pylint passed (or minor warnings only)"
    else
        print_error "pylint found critical issues"
        LINT_PASSED=0
    fi

    # JavaScript linting with eslint
    if command_exists eslint; then
        print_info "Running eslint..."
        if eslint frontend/js/ --config .eslintrc.json; then
            print_success "eslint passed"
        else
            print_error "eslint found issues"
            LINT_PASSED=0
        fi
    fi

    if [ $LINT_PASSED -eq 0 ]; then
        print_info "Linting completed with warnings"
    else
        print_success "All linting checks passed"
        LINT_PASSED=1
    fi
fi

###############################################################################
# Summary
###############################################################################
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

print_section "Test Summary"

echo "Results:"
[ "$RUN_UNIT" = true ] && [ $UNIT_TESTS_PASSED -eq 1 ] && print_success "Unit Tests: PASSED" || [ "$RUN_UNIT" = true ] && print_error "Unit Tests: FAILED"
[ "$RUN_INTEGRATION" = true ] && [ $INTEGRATION_TESTS_PASSED -eq 1 ] && print_success "Integration Tests: PASSED" || [ "$RUN_INTEGRATION" = true ] && print_error "Integration Tests: FAILED"
[ "$RUN_E2E" = true ] && [ $E2E_TESTS_PASSED -eq 1 ] && print_success "E2E Tests: PASSED" || [ "$RUN_E2E" = true ] && print_error "E2E Tests: FAILED"
[ "$RUN_FRONTEND" = true ] && [ $FRONTEND_TESTS_PASSED -eq 1 ] && print_success "Frontend Tests: PASSED" || [ "$RUN_FRONTEND" = true ] && print_error "Frontend Tests: FAILED"
[ "$RUN_LINT" = true ] && [ $LINT_PASSED -eq 1 ] && print_success "Linting: PASSED" || [ "$RUN_LINT" = true ] && print_error "Linting: WARNINGS"

echo ""
print_info "Total execution time: ${DURATION}s"

if [ "$COVERAGE" = true ]; then
    echo ""
    print_info "Coverage reports:"
    [ -f "tests/reports/coverage/python/index.html" ] && print_info "  Python: tests/reports/coverage/python/index.html"
    [ -f "tests/reports/coverage/frontend/index.html" ] && print_info "  Frontend: tests/reports/coverage/frontend/index.html"
fi

# Exit code
if [ "$RUN_UNIT" = true ] && [ $UNIT_TESTS_PASSED -eq 0 ]; then
    exit 1
fi
if [ "$RUN_INTEGRATION" = true ] && [ $INTEGRATION_TESTS_PASSED -eq 0 ]; then
    exit 1
fi
if [ "$RUN_E2E" = true ] && [ $E2E_TESTS_PASSED -eq 0 ]; then
    exit 1
fi
if [ "$RUN_FRONTEND" = true ] && [ $FRONTEND_TESTS_PASSED -eq 0 ]; then
    exit 1
fi

print_success "All selected tests passed!"
exit 0
