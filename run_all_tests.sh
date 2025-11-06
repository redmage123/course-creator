#!/bin/bash
# Parallel Test Runner for Course Creator Platform
#
# BUSINESS CONTEXT:
# Executes entire test suite across Python backend (16 services) and React frontend
# in parallel for maximum efficiency. Provides comprehensive test results and coverage reports.
#
# TECHNICAL IMPLEMENTATION:
# - Parallel execution using GNU parallel or background jobs
# - Separate process groups for Python, React, Regression, and E2E tests
# - Real-time progress tracking with spinners
# - Colored output for easy status identification
# - Detailed failure reporting
# - Coverage aggregation across all test types
#
# USAGE:
#     ./run_all_tests.sh [OPTIONS]
#
# OPTIONS:
#     --python-only       Run only Python tests
#     --react-only        Run only React tests
#     --regression-only   Run only regression tests
#     --e2e-only          Run only E2E tests
#     --no-coverage       Skip coverage reporting
#     --fast              Skip E2E tests (fastest execution)
#     --parallel N        Set parallelism level (default: 4)
#     --verbose           Show detailed output
#     --help              Show this help message
#
# EXAMPLES:
#     ./run_all_tests.sh                    # Run all tests with coverage
#     ./run_all_tests.sh --fast             # Skip E2E tests
#     ./run_all_tests.sh --python-only      # Python tests only
#     ./run_all_tests.sh --parallel 8       # Use 8 parallel jobs

set -e  # Exit on error (disable for test execution)
set +e  # Allow tests to fail without stopping script

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Test result tracking
PYTHON_UNIT_RESULT=0
PYTHON_INTEGRATION_RESULT=0
PYTHON_REGRESSION_RESULT=0
REACT_UNIT_RESULT=0
REACT_INTEGRATION_RESULT=0
REACT_E2E_RESULT=0

# Configuration
PARALLEL_JOBS=4
RUN_PYTHON=true
RUN_REACT=true
RUN_REGRESSION=true
RUN_E2E=true
RUN_COVERAGE=true
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --python-only)
            RUN_REACT=false
            RUN_E2E=false
            shift
            ;;
        --react-only)
            RUN_PYTHON=false
            RUN_REGRESSION=false
            shift
            ;;
        --regression-only)
            RUN_PYTHON=false
            RUN_REACT=false
            RUN_E2E=false
            RUN_REGRESSION=true
            shift
            ;;
        --e2e-only)
            RUN_PYTHON=false
            RUN_REACT=false
            RUN_REGRESSION=false
            RUN_E2E=true
            shift
            ;;
        --no-coverage)
            RUN_COVERAGE=false
            shift
            ;;
        --fast)
            RUN_E2E=false
            shift
            ;;
        --parallel)
            PARALLEL_JOBS="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            grep '^"""' "$0" -A 100 | grep -B 100 '"""$' | head -n -1 | tail -n +2
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "\n${BOLD}${BLUE}=====================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}=====================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# Spinner function for background processes
spinner() {
    local pid=$1
    local message=$2
    local delay=0.1
    local spinstr='|/-\'
    echo -n "$message "
    while kill -0 $pid 2>/dev/null; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Start timer
START_TIME=$(date +%s)

print_header "Course Creator Platform - Comprehensive Test Suite"
echo -e "${CYAN}Started at: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${CYAN}Parallel Jobs: $PARALLEL_JOBS${NC}"
echo ""

# Create temp directory for logs
TEMP_DIR=$(mktemp -d)
echo -e "${CYAN}Logs directory: $TEMP_DIR${NC}\n"

# ============================================================================
# PHASE 1: Python Unit Tests (Parallel by Service)
# ============================================================================

if [ "$RUN_PYTHON" = true ]; then
    print_header "PHASE 1: Python Unit Tests (Parallel Execution)"

    # Array of services with tests
    SERVICES=(
        "ai_assistant_service"
        "knowledge_graph_service"
        "analytics"
        "content_management"
        "course_generator"
        "course_management"
        "demo_service"
        "lab_manager"
        "organization_management"
        "rag_service"
        "user_management"
    )

    echo -e "${CYAN}Running unit tests for ${#SERVICES[@]} services in parallel...${NC}\n"

    # Run tests in parallel
    PIDS=()
    for service in "${SERVICES[@]}"; do
        if [ -d "tests/unit/$service" ]; then
            (
                if [ "$VERBOSE" = true ]; then
                    python -m pytest "tests/unit/$service/" -v --tb=short 2>&1 | tee "$TEMP_DIR/unit_${service}.log"
                else
                    python -m pytest "tests/unit/$service/" -v --tb=short > "$TEMP_DIR/unit_${service}.log" 2>&1
                fi
                echo $? > "$TEMP_DIR/unit_${service}.exit"
            ) &
            PIDS+=($!)

            # Limit parallel jobs
            if [ ${#PIDS[@]} -ge $PARALLEL_JOBS ]; then
                wait -n
                PIDS=($(jobs -p))
            fi
        fi
    done

    # Wait for all to complete
    wait

    # Check results
    echo -e "\n${BOLD}Python Unit Test Results:${NC}"
    UNIT_PASS=0
    UNIT_FAIL=0
    for service in "${SERVICES[@]}"; do
        if [ -f "$TEMP_DIR/unit_${service}.exit" ]; then
            EXIT_CODE=$(cat "$TEMP_DIR/unit_${service}.exit")
            if [ $EXIT_CODE -eq 0 ]; then
                print_success "$service: PASSED"
                ((UNIT_PASS++))
            else
                print_error "$service: FAILED (exit code: $EXIT_CODE)"
                ((UNIT_FAIL++))
                PYTHON_UNIT_RESULT=1
                if [ "$VERBOSE" = true ]; then
                    echo -e "${YELLOW}Last 20 lines of log:${NC}"
                    tail -20 "$TEMP_DIR/unit_${service}.log"
                fi
            fi
        fi
    done

    echo -e "\n${BOLD}Summary: ${GREEN}$UNIT_PASS passed${NC}, ${RED}$UNIT_FAIL failed${NC}\n"
fi

# ============================================================================
# PHASE 2: Python Integration Tests
# ============================================================================

if [ "$RUN_PYTHON" = true ]; then
    print_header "PHASE 2: Python Integration Tests"

    echo -e "${CYAN}Running integration tests...${NC}\n"

    if [ "$VERBOSE" = true ]; then
        python -m pytest tests/integration/ -v --tb=short 2>&1 | tee "$TEMP_DIR/integration.log"
    else
        python -m pytest tests/integration/ -v --tb=short > "$TEMP_DIR/integration.log" 2>&1
    fi
    PYTHON_INTEGRATION_RESULT=$?

    if [ $PYTHON_INTEGRATION_RESULT -eq 0 ]; then
        print_success "Integration tests: PASSED"
    else
        print_error "Integration tests: FAILED"
        if [ "$VERBOSE" = false ]; then
            echo -e "${YELLOW}Last 30 lines of log:${NC}"
            tail -30 "$TEMP_DIR/integration.log"
        fi
    fi
    echo ""
fi

# ============================================================================
# PHASE 3: Python Regression Tests
# ============================================================================

if [ "$RUN_REGRESSION" = true ]; then
    print_header "PHASE 3: Python Regression Tests"

    echo -e "${CYAN}Running regression tests...${NC}\n"

    if [ -d "tests/regression/python" ]; then
        if [ "$VERBOSE" = true ]; then
            python -m pytest tests/regression/python/ -v --tb=short 2>&1 | tee "$TEMP_DIR/regression.log"
        else
            python -m pytest tests/regression/python/ -v --tb=short > "$TEMP_DIR/regression.log" 2>&1
        fi
        PYTHON_REGRESSION_RESULT=$?

        if [ $PYTHON_REGRESSION_RESULT -eq 0 ]; then
            print_success "Regression tests: PASSED"
        else
            print_error "Regression tests: FAILED"
            if [ "$VERBOSE" = false ]; then
                echo -e "${YELLOW}Last 30 lines of log:${NC}"
                tail -30 "$TEMP_DIR/regression.log"
            fi
        fi
    else
        print_warning "Regression tests directory not found, skipping"
    fi
    echo ""
fi

# ============================================================================
# PHASE 4: React Unit Tests
# ============================================================================

if [ "$RUN_REACT" = true ]; then
    print_header "PHASE 4: React Unit Tests"

    echo -e "${CYAN}Running React unit tests...${NC}\n"

    cd frontend-react
    if [ "$VERBOSE" = true ]; then
        npm test -- --run --reporter=verbose 2>&1 | tee "$TEMP_DIR/react_unit.log"
    else
        npm test -- --run --reporter=verbose > "$TEMP_DIR/react_unit.log" 2>&1
    fi
    REACT_UNIT_RESULT=$?
    cd ..

    if [ $REACT_UNIT_RESULT -eq 0 ]; then
        print_success "React unit tests: PASSED"
    else
        print_error "React unit tests: FAILED"
        if [ "$VERBOSE" = false ]; then
            echo -e "${YELLOW}Last 40 lines of log:${NC}"
            tail -40 "$TEMP_DIR/react_unit.log"
        fi
    fi
    echo ""
fi

# ============================================================================
# PHASE 5: React Integration Tests
# ============================================================================

if [ "$RUN_REACT" = true ]; then
    print_header "PHASE 5: React Integration Tests"

    echo -e "${CYAN}Running React integration tests...${NC}\n"

    cd frontend-react
    if [ -d "src/test/integration" ]; then
        if [ "$VERBOSE" = true ]; then
            npm test -- --run src/test/integration --reporter=verbose 2>&1 | tee "$TEMP_DIR/react_integration.log"
        else
            npm test -- --run src/test/integration --reporter=verbose > "$TEMP_DIR/react_integration.log" 2>&1
        fi
        REACT_INTEGRATION_RESULT=$?

        if [ $REACT_INTEGRATION_RESULT -eq 0 ]; then
            print_success "React integration tests: PASSED"
        else
            print_error "React integration tests: FAILED"
            if [ "$VERBOSE" = false ]; then
                echo -e "${YELLOW}Last 40 lines of log:${NC}"
                tail -40 "$TEMP_DIR/react_integration.log"
            fi
        fi
    else
        print_warning "React integration tests not found, skipping"
    fi
    cd ..
    echo ""
fi

# ============================================================================
# PHASE 6: Cypress E2E Tests (Optional)
# ============================================================================

if [ "$RUN_E2E" = true ]; then
    print_header "PHASE 6: Cypress E2E Tests"

    echo -e "${CYAN}Running Cypress E2E tests...${NC}\n"

    cd frontend-react
    if [ -d "cypress" ] && command -v cypress &> /dev/null; then
        if [ "$VERBOSE" = true ]; then
            npm run test:e2e 2>&1 | tee "$TEMP_DIR/e2e.log"
        else
            npm run test:e2e > "$TEMP_DIR/e2e.log" 2>&1
        fi
        REACT_E2E_RESULT=$?

        if [ $REACT_E2E_RESULT -eq 0 ]; then
            print_success "E2E tests: PASSED"
        else
            print_error "E2E tests: FAILED"
            if [ "$VERBOSE" = false ]; then
                echo -e "${YELLOW}Last 40 lines of log:${NC}"
                tail -40 "$TEMP_DIR/e2e.log"
            fi
        fi
    else
        print_warning "Cypress not installed or configured, skipping E2E tests"
        print_info "Install with: cd frontend-react && npm install cypress --save-dev"
    fi
    cd ..
    echo ""
fi

# ============================================================================
# PHASE 7: Coverage Report Generation
# ============================================================================

if [ "$RUN_COVERAGE" = true ]; then
    print_header "PHASE 7: Coverage Report Generation"

    echo -e "${CYAN}Generating combined coverage reports...${NC}\n"

    if [ -f "scripts/generate_coverage_report.sh" ]; then
        chmod +x scripts/generate_coverage_report.sh
        if [ "$VERBOSE" = true ]; then
            ./scripts/generate_coverage_report.sh 2>&1 | tee "$TEMP_DIR/coverage.log"
        else
            ./scripts/generate_coverage_report.sh > "$TEMP_DIR/coverage.log" 2>&1
        fi

        if [ $? -eq 0 ]; then
            print_success "Coverage reports generated"
            if [ -f "coverage/index.html" ]; then
                print_info "Combined report: coverage/index.html"
            fi
            if [ -f "coverage/python/index.html" ]; then
                print_info "Python report: coverage/python/index.html"
            fi
            if [ -f "frontend-react/coverage/index.html" ]; then
                print_info "React report: frontend-react/coverage/index.html"
            fi
        else
            print_warning "Coverage report generation had issues (see log)"
        fi
    else
        print_warning "Coverage script not found, skipping coverage generation"
    fi
    echo ""
fi

# ============================================================================
# Final Summary
# ============================================================================

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

print_header "FINAL TEST RESULTS"

echo -e "${BOLD}Test Execution Summary:${NC}\n"

# Calculate totals
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

if [ "$RUN_PYTHON" = true ]; then
    echo -e "${BOLD}Python Tests:${NC}"
    if [ $PYTHON_UNIT_RESULT -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Unit Tests: PASSED ($UNIT_PASS services)"
        ((PASSED_TESTS++))
    else
        echo -e "  ${RED}✗${NC} Unit Tests: FAILED ($UNIT_FAIL services failed)"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))

    if [ $PYTHON_INTEGRATION_RESULT -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Integration Tests: PASSED"
        ((PASSED_TESTS++))
    else
        echo -e "  ${RED}✗${NC} Integration Tests: FAILED"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    echo ""
fi

if [ "$RUN_REGRESSION" = true ]; then
    echo -e "${BOLD}Regression Tests:${NC}"
    if [ $PYTHON_REGRESSION_RESULT -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} PASSED"
        ((PASSED_TESTS++))
    else
        echo -e "  ${RED}✗${NC} FAILED"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    echo ""
fi

if [ "$RUN_REACT" = true ]; then
    echo -e "${BOLD}React Tests:${NC}"
    if [ $REACT_UNIT_RESULT -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Unit Tests: PASSED"
        ((PASSED_TESTS++))
    else
        echo -e "  ${RED}✗${NC} Unit Tests: FAILED"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))

    if [ $REACT_INTEGRATION_RESULT -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Integration Tests: PASSED"
        ((PASSED_TESTS++))
    else
        echo -e "  ${RED}✗${NC} Integration Tests: FAILED"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    echo ""
fi

if [ "$RUN_E2E" = true ]; then
    echo -e "${BOLD}E2E Tests:${NC}"
    if [ $REACT_E2E_RESULT -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Cypress: PASSED"
        ((PASSED_TESTS++))
    else
        echo -e "  ${RED}✗${NC} Cypress: FAILED"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    echo ""
fi

# Final summary
echo -e "${BOLD}Overall Results:${NC}"
echo -e "  Total Test Suites: $TOTAL_TESTS"
echo -e "  ${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "  ${RED}Failed: $FAILED_TESTS${NC}"
echo -e "  ${CYAN}Duration: ${MINUTES}m ${SECONDS}s${NC}"
echo -e "  ${CYAN}Finished at: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# Log file information
echo -e "${BOLD}Log Files:${NC}"
echo -e "  Location: $TEMP_DIR"
echo -e "  ${CYAN}View logs: ls -lh $TEMP_DIR/${NC}"
echo ""

# Exit code
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${BOLD}${GREEN}════════════════════════════════════${NC}"
    echo -e "${BOLD}${GREEN}   ALL TESTS PASSED! 🎉${NC}"
    echo -e "${BOLD}${GREEN}════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${BOLD}${RED}════════════════════════════════════${NC}"
    echo -e "${BOLD}${RED}   SOME TESTS FAILED ❌${NC}"
    echo -e "${BOLD}${RED}════════════════════════════════════${NC}"
    echo -e "\n${YELLOW}Review logs in: $TEMP_DIR${NC}"
    echo -e "${YELLOW}Rerun failed tests with --verbose flag for detailed output${NC}\n"
    exit 1
fi
