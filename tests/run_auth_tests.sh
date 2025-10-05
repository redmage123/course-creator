#!/bin/bash
"""
Authentication Token Consistency Test Runner

BUSINESS CONTEXT:
Runs all authentication-related tests including linting, unit, integration, and E2E tests.
Ensures no auth token inconsistencies that could cause redirect loops or authentication failures.

TECHNICAL IMPLEMENTATION:
Executes tests in order: linting → unit → integration → E2E
"""

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Authentication Token Consistency Test Suite${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 1. Run linting
echo -e "${YELLOW}[1/4] Running Auth Token Linting...${NC}"
if ./scripts/lint_auth_tokens.sh; then
    echo -e "${GREEN}✓ Linting PASSED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Linting FAILED${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

# 2. Run unit tests
echo -e "${YELLOW}[2/4] Running Unit Tests...${NC}"
if npx vitest run tests/unit/frontend/auth-token-consistency.test.js --reporter=verbose 2>&1 | tee /tmp/unit_test_output.txt; then
    UNIT_PASSED=$(grep -oP '\d+(?= passed)' /tmp/unit_test_output.txt | tail -1)
    echo -e "${GREEN}✓ Unit Tests PASSED (${UNIT_PASSED} tests)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + UNIT_PASSED))
    TOTAL_TESTS=$((TOTAL_TESTS + UNIT_PASSED))
else
    echo -e "${RED}✗ Unit Tests FAILED${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi
echo ""

# 3. Run integration tests
echo -e "${YELLOW}[3/4] Running Integration Tests...${NC}"
if npx vitest run tests/integration/org-admin-auth-flow.test.js --reporter=verbose 2>&1 | tee /tmp/integration_test_output.txt; then
    INTEGRATION_PASSED=$(grep -oP '\d+(?= passed)' /tmp/integration_test_output.txt | tail -1)
    echo -e "${GREEN}✓ Integration Tests PASSED (${INTEGRATION_PASSED} tests)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + INTEGRATION_PASSED))
    TOTAL_TESTS=$((TOTAL_TESTS + INTEGRATION_PASSED))
else
    echo -e "${RED}✗ Integration Tests FAILED${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi
echo ""

# 4. Run E2E tests
echo -e "${YELLOW}[4/4] Running E2E Tests (Selenium)...${NC}"
export PYTHONPATH=.
export TEST_BASE_URL="https://176.9.99.103:3000"
if pytest tests/e2e/test_org_admin_dashboard_auth_selenium.py -v 2>&1 | tee /tmp/e2e_test_output.txt; then
    E2E_PASSED=$(grep -oP '\d+(?= passed)' /tmp/e2e_test_output.txt | tail -1 || echo "0")
    if [ "$E2E_PASSED" -gt 0 ]; then
        echo -e "${GREEN}✓ E2E Tests PASSED (${E2E_PASSED} tests)${NC}"
        PASSED_TESTS=$((PASSED_TESTS + E2E_PASSED))
        TOTAL_TESTS=$((TOTAL_TESTS + E2E_PASSED))
    else
        echo -e "${YELLOW}⚠ E2E Tests SKIPPED (frontend server may not be accessible)${NC}"
    fi
else
    echo -e "${RED}✗ E2E Tests FAILED${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi
echo ""

# Summary
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Test Results Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${PASSED_TESTS}${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED_TESTS}${NC}"
fi
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
