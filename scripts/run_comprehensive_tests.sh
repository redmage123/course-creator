#!/bin/bash

"""
Comprehensive Test Suite Runner

BUSINESS CONTEXT:
Runs all test suites that catch integration and visual issues missed by unit tests.
These tests verify actual API contracts, database queries, and UI rendering.

TECHNICAL IMPLEMENTATION:
- Contract tests: API response validation against Pydantic models
- E2E tests: Browser automation testing actual user flows
- Visual tests: CSS and UI rendering validation
- Database tests: Query structure and field validation
- Integration tests: Login flow and response structure

USAGE:
./scripts/run_comprehensive_tests.sh [test-type]

test-type options:
  all        - Run all comprehensive tests (default)
  contract   - API contract tests only
  e2e        - End-to-end browser tests only
  visual     - Visual/CSS validation tests only
  database   - Database query structure tests only
  integration - Integration tests only
"""

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get test type from argument (default: all)
TEST_TYPE="${1:-all}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Comprehensive Test Suite Runner${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Ensure services are running
echo -e "${YELLOW}Checking if services are running...${NC}"
if ! docker ps | grep -q "course-creator"; then
    echo -e "${RED}❌ Services not running. Start them first:${NC}"
    echo "   ./scripts/app-control.sh start"
    exit 1
fi
echo -e "${GREEN}✅ Services are running${NC}"
echo ""

# Set test environment variables
export TEST_BASE_URL="https://176.9.99.103:3000"
export PYTHONPATH="/home/bbrelin/course-creator:$PYTHONPATH"

# Function to run contract tests
run_contract_tests() {
    echo -e "${YELLOW}Running Contract Tests...${NC}"
    echo "These verify API responses match Pydantic models"
    echo ""

    pytest tests/contract/test_organization_api_contracts.py -v --tb=short

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Contract tests passed${NC}"
    else
        echo -e "${RED}❌ Contract tests failed${NC}"
        return 1
    fi
    echo ""
}

# Function to run E2E data loading tests
run_e2e_tests() {
    echo -e "${YELLOW}Running E2E Data Loading Tests...${NC}"
    echo "These verify actual dashboard tabs load data without errors"
    echo ""

    HEADLESS=true pytest tests/e2e/test_org_admin_dashboard_data_loading.py -v --tb=short

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ E2E data loading tests passed${NC}"
    else
        echo -e "${RED}❌ E2E data loading tests failed${NC}"
        return 1
    fi
    echo ""
}

# Function to run visual tests
run_visual_tests() {
    echo -e "${YELLOW}Running Visual/CSS Validation Tests...${NC}"
    echo "These verify UI elements render correctly with proper styling"
    echo ""

    HEADLESS=true pytest tests/e2e/test_org_admin_dashboard_visual.py -v --tb=short

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Visual tests passed${NC}"
    else
        echo -e "${RED}❌ Visual tests failed${NC}"
        return 1
    fi
    echo ""
}

# Function to run database tests
run_database_tests() {
    echo -e "${YELLOW}Running Database Query Structure Tests...${NC}"
    echo "These verify queries return all fields needed by Pydantic models"
    echo ""

    pytest tests/integration/test_database_query_contracts.py -v --tb=short

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database query tests passed${NC}"
    else
        echo -e "${RED}❌ Database query tests failed${NC}"
        return 1
    fi
    echo ""
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${YELLOW}Running Login Response Structure Tests...${NC}"
    echo "These verify login returns all required fields for each user role"
    echo ""

    pytest tests/integration/test_login_response_structure.py -v --tb=short

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Login integration tests passed${NC}"
    else
        echo -e "${RED}❌ Login integration tests failed${NC}"
        return 1
    fi
    echo ""
}

# Run tests based on argument
case "$TEST_TYPE" in
    contract)
        run_contract_tests
        ;;
    e2e)
        run_e2e_tests
        ;;
    visual)
        run_visual_tests
        ;;
    database)
        run_database_tests
        ;;
    integration)
        run_integration_tests
        ;;
    all)
        echo -e "${YELLOW}Running ALL comprehensive tests...${NC}"
        echo ""

        FAILED=0

        run_contract_tests || FAILED=1
        run_e2e_tests || FAILED=1
        run_visual_tests || FAILED=1
        run_database_tests || FAILED=1
        run_integration_tests || FAILED=1

        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Test Results Summary${NC}"
        echo -e "${GREEN}========================================${NC}"

        if [ $FAILED -eq 0 ]; then
            echo -e "${GREEN}✅ ALL COMPREHENSIVE TESTS PASSED${NC}"
            echo ""
            echo "These tests catch issues that unit tests miss:"
            echo "  ✓ API responses match Pydantic models"
            echo "  ✓ Dashboard tabs load data without errors"
            echo "  ✓ UI elements render with correct CSS"
            echo "  ✓ Database queries return all required fields"
            echo "  ✓ Login includes organization_id for org admins"
        else
            echo -e "${RED}❌ SOME TESTS FAILED${NC}"
            echo "Review the output above for details"
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}Invalid test type: $TEST_TYPE${NC}"
        echo "Usage: $0 [all|contract|e2e|visual|database|integration]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
