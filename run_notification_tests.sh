#!/bin/bash

#
# Comprehensive Test Runner for Notification and Bulk Room Management Features
#
# BUSINESS CONTEXT:
# Runs complete test suite covering unit, integration, and E2E tests
# for notification system and bulk meeting room management.
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "==========================================="
echo "Notification & Bulk Room Management Tests"
echo "==========================================="
echo ""

# Test result tracking
UNIT_TESTS_PASSED=0
INTEGRATION_TESTS_PASSED=0
E2E_TESTS_PASSED=0
FAILED_TESTS=""

# Function to run tests and track results
run_test_suite() {
    local suite_name=$1
    local test_path=$2
    local result_var=$3

    echo -e "${YELLOW}Running $suite_name...${NC}"
    # Add service root to PYTHONPATH for data_access imports
    if PYTHONPATH=services/organization-management:$PWD:$PYTHONPATH pytest "$test_path" -v --tb=short --no-cov -q; then
        echo -e "${GREEN}✓ $suite_name PASSED${NC}"
        eval "$result_var=1"
    else
        echo -e "${RED}✗ $suite_name FAILED${NC}"
        FAILED_TESTS="$FAILED_TESTS\n  - $suite_name"
    fi
    echo ""
}

# =============================================================================
# UNIT TESTS
# =============================================================================

echo "================================================"
echo "UNIT TESTS"
echo "================================================"
echo ""

run_test_suite \
    "Notification Domain Entities" \
    "tests/unit/organization_management/test_notification_entities.py" \
    "UNIT_ENTITIES"

run_test_suite \
    "Notification Service" \
    "tests/unit/organization_management/test_notification_service.py" \
    "UNIT_SERVICE"

run_test_suite \
    "Bulk Room Creation" \
    "tests/unit/organization_management/test_bulk_room_creation.py" \
    "UNIT_BULK"

# Calculate unit test results
if [ "$UNIT_ENTITIES" == "1" ] && [ "$UNIT_SERVICE" == "1" ] && [ "$UNIT_BULK" == "1" ]; then
    UNIT_TESTS_PASSED=1
fi

# =============================================================================
# INTEGRATION TESTS
# =============================================================================

echo "================================================"
echo "INTEGRATION TESTS"
echo "================================================"
echo ""

run_test_suite \
    "Notification Integration" \
    "tests/integration/test_notification_integration.py" \
    "INTEGRATION_NOTIF"

if [ "$INTEGRATION_NOTIF" == "1" ]; then
    INTEGRATION_TESTS_PASSED=1
fi

# =============================================================================
# E2E TESTS
# =============================================================================

echo "================================================"
echo "E2E TESTS"
echo "================================================"
echo ""

echo -e "${YELLOW}NOTE: E2E tests require the platform to be running${NC}"
echo -e "${YELLOW}Run: ./scripts/app-control.sh start${NC}"
echo ""

read -p "Platform is running? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    run_test_suite \
        "Org Admin Notification E2E" \
        "tests/e2e/test_org_admin_notifications_e2e.py" \
        "E2E_NOTIF"

    if [ "$E2E_NOTIF" == "1" ]; then
        E2E_TESTS_PASSED=1
    fi
else
    echo -e "${YELLOW}Skipping E2E tests${NC}"
fi

# =============================================================================
# RESULTS SUMMARY
# =============================================================================

echo ""
echo "==========================================="
echo "TEST RESULTS SUMMARY"
echo "==========================================="
echo ""

if [ "$UNIT_TESTS_PASSED" == "1" ]; then
    echo -e "${GREEN}✓ Unit Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Unit Tests: FAILED${NC}"
fi

if [ "$INTEGRATION_TESTS_PASSED" == "1" ]; then
    echo -e "${GREEN}✓ Integration Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Integration Tests: FAILED${NC}"
fi

if [ "$E2E_TESTS_PASSED" == "1" ]; then
    echo -e "${GREEN}✓ E2E Tests: PASSED${NC}"
elif [ -z "$E2E_NOTIF" ]; then
    echo -e "${YELLOW}⊘ E2E Tests: SKIPPED${NC}"
else
    echo -e "${RED}✗ E2E Tests: FAILED${NC}"
fi

echo ""

if [ -n "$FAILED_TESTS" ]; then
    echo -e "${RED}Failed test suites:${NC}"
    echo -e "$FAILED_TESTS"
    echo ""
    exit 1
else
    echo -e "${GREEN}All executed tests passed successfully!${NC}"
    echo ""
    exit 0
fi
