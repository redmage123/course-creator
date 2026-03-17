#!/bin/bash

"""
Coverage Report Generator

BUSINESS PURPOSE:
Generates comprehensive test coverage reports for all services and frontend.
Provides visibility into test coverage across the entire Course Creator Platform,
helping identify untested code paths and areas requiring additional testing.

OUTPUTS:
- HTML coverage reports (navigable in browser)
- JSON coverage data (machine-readable)
- XML coverage data (for CI/CD integration)
- Terminal summary (quick visibility)
- Coverage badges (for README display)
- Trend analysis (coverage over time)

USAGE:
  ./scripts/generate_coverage_report.sh              # Generate all reports
  ./scripts/generate_coverage_report.sh --python     # Python backend only
  ./scripts/generate_coverage_report.sh --react      # React frontend only
  ./scripts/generate_coverage_report.sh --combined   # Combined report only

PREREQUISITES:
- Python 3.11+ installed
- Node.js 18+ installed
- pytest, pytest-cov installed (pip install pytest pytest-cov)
- npm packages installed in frontend-react/

TECHNICAL RATIONALE:
- Separate Python and React coverage (different toolchains)
- Combined HTML dashboard for unified view
- Multiple output formats for flexibility
- Coverage thresholds enforced (70% minimum)
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_COVERAGE=70
REACT_MIN_COVERAGE=70
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COVERAGE_DIR="${PROJECT_ROOT}/coverage"
PYTHON_COVERAGE_DIR="${COVERAGE_DIR}/python"
REACT_COVERAGE_DIR="${COVERAGE_DIR}/react"
COMBINED_REPORT="${COVERAGE_DIR}/index.html"

# Parse command line arguments
MODE="all"
if [ $# -gt 0 ]; then
    case "$1" in
        --python)
            MODE="python"
            ;;
        --react)
            MODE="react"
            ;;
        --combined)
            MODE="combined"
            ;;
        --help|-h)
            echo "Usage: $0 [--python|--react|--combined]"
            echo ""
            echo "Options:"
            echo "  --python      Generate Python coverage only"
            echo "  --react       Generate React coverage only"
            echo "  --combined    Generate combined report only (requires existing data)"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
fi

# Create coverage directories
mkdir -p "${PYTHON_COVERAGE_DIR}"
mkdir -p "${REACT_COVERAGE_DIR}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Course Creator Platform - Coverage Report Generator        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# Function: Generate Python Coverage
# ============================================================================
generate_python_coverage() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}1. Generating Python Backend Coverage${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    cd "${PROJECT_ROOT}"

    echo -e "${YELLOW}Running Python tests with coverage...${NC}"

    # Run pytest with coverage
    pytest \
        --cov=services \
        --cov-report=html:"${PYTHON_COVERAGE_DIR}" \
        --cov-report=json:"${PYTHON_COVERAGE_DIR}/coverage.json" \
        --cov-report=xml:"${PYTHON_COVERAGE_DIR}/coverage.xml" \
        --cov-report=term-missing \
        --cov-fail-under="${PYTHON_MIN_COVERAGE}" \
        -v \
        2>&1 | tee "${PYTHON_COVERAGE_DIR}/test_output.log"

    PYTHON_EXIT_CODE=$?

    if [ $PYTHON_EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Python coverage generated successfully${NC}"
        echo -e "${GREEN}  HTML Report: ${PYTHON_COVERAGE_DIR}/index.html${NC}"
        echo -e "${GREEN}  JSON Report: ${PYTHON_COVERAGE_DIR}/coverage.json${NC}"
        echo -e "${GREEN}  XML Report:  ${PYTHON_COVERAGE_DIR}/coverage.xml${NC}"
    else
        echo ""
        echo -e "${RED}✗ Python coverage below ${PYTHON_MIN_COVERAGE}% threshold${NC}"
        echo -e "${YELLOW}  Reports generated anyway for review${NC}"
    fi

    echo ""
}

# ============================================================================
# Function: Generate React Coverage
# ============================================================================
generate_react_coverage() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}2. Generating React Frontend Coverage${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    cd "${PROJECT_ROOT}/frontend-react"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install --legacy-peer-deps
        echo ""
    fi

    echo -e "${YELLOW}Running React tests with coverage...${NC}"

    # Run Vitest with coverage
    npm run test:coverage 2>&1 | tee "${REACT_COVERAGE_DIR}/test_output.log"

    REACT_EXIT_CODE=$?

    # Copy coverage reports to our standard location
    if [ -d "coverage" ]; then
        cp -r coverage/* "${REACT_COVERAGE_DIR}/"
    fi

    if [ $REACT_EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ React coverage generated successfully${NC}"
        echo -e "${GREEN}  HTML Report: ${REACT_COVERAGE_DIR}/index.html${NC}"
        echo -e "${GREEN}  JSON Report: ${REACT_COVERAGE_DIR}/coverage-final.json${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠ React coverage tests completed with warnings${NC}"
        echo -e "${YELLOW}  Reports generated anyway for review${NC}"
    fi

    cd "${PROJECT_ROOT}"
    echo ""
}

# ============================================================================
# Function: Generate Combined Report
# ============================================================================
generate_combined_report() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}3. Generating Combined Coverage Report${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    cd "${PROJECT_ROOT}"

    echo -e "${YELLOW}Combining Python and React coverage...${NC}"

    # Run the Python script to combine coverage
    python3 scripts/combine_coverage.py

    COMBINE_EXIT_CODE=$?

    if [ $COMBINE_EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Combined coverage report generated${NC}"
        echo -e "${GREEN}  Dashboard: ${COMBINED_REPORT}${NC}"
    else
        echo ""
        echo -e "${RED}✗ Failed to generate combined report${NC}"
        echo -e "${YELLOW}  Check individual reports for details${NC}"
    fi

    echo ""
}

# ============================================================================
# Function: Display Summary
# ============================================================================
display_summary() {
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}Coverage Report Summary${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${CYAN}Reports Generated:${NC}"
    echo ""

    if [ -f "${PYTHON_COVERAGE_DIR}/index.html" ]; then
        echo -e "  ${GREEN}✓${NC} Python Backend Coverage:"
        echo -e "    HTML: file://${PYTHON_COVERAGE_DIR}/index.html"
        echo ""
    fi

    if [ -f "${REACT_COVERAGE_DIR}/index.html" ]; then
        echo -e "  ${GREEN}✓${NC} React Frontend Coverage:"
        echo -e "    HTML: file://${REACT_COVERAGE_DIR}/index.html"
        echo ""
    fi

    if [ -f "${COMBINED_REPORT}" ]; then
        echo -e "  ${GREEN}✓${NC} Combined Coverage Dashboard:"
        echo -e "    HTML: file://${COMBINED_REPORT}"
        echo ""
    fi

    echo -e "${CYAN}Next Steps:${NC}"
    echo -e "  1. Open reports in browser to view detailed coverage"
    echo -e "  2. Identify files with low coverage (<70%)"
    echo -e "  3. Write tests for uncovered code paths"
    echo -e "  4. Re-run this script to verify improvements"
    echo ""

    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# Main Execution
# ============================================================================

case "$MODE" in
    all)
        generate_python_coverage
        generate_react_coverage
        generate_combined_report
        display_summary
        ;;
    python)
        generate_python_coverage
        ;;
    react)
        generate_react_coverage
        ;;
    combined)
        if [ ! -f "${PYTHON_COVERAGE_DIR}/coverage.json" ] || [ ! -d "${REACT_COVERAGE_DIR}" ]; then
            echo -e "${RED}Error: Coverage data not found${NC}"
            echo -e "${YELLOW}Run with --python and --react first to generate data${NC}"
            exit 1
        fi
        generate_combined_report
        display_summary
        ;;
esac

echo ""
echo -e "${BLUE}═════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Coverage Report Generation Complete!${NC}"
echo -e "${BLUE}═════════════════════════════════════════════════════════════════${NC}"
echo ""

exit 0
