#!/bin/bash

###############################################################################
# Pre-Test Validation Script
#
# BUSINESS CONTEXT:
# This script runs all foundational validation before any tests execute.
# It ensures the codebase is in a testable state.
#
# TECHNICAL IMPLEMENTATION:
# 1. Syntax validation (Python compilation)
# 2. Import validation (module imports)
# 3. Service health checks (Docker containers)
#
# USAGE:
#   ./tests/validate_before_tests.sh
#
# EXIT CODES:
#   0 - All validations passed
#   1 - Syntax errors found
#   2 - Import errors found
#   3 - Service health check failed
###############################################################################

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "Pre-Test Validation"
echo "============================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

###############################################################################
# 1. SYNTAX VALIDATION
###############################################################################

echo "1. Validating Python syntax..."
echo "-------------------------------------------"

syntax_errors=0

# Find all Python files (excluding venv and cache)
while IFS= read -r py_file; do
    if ! python3 -m py_compile "$py_file" 2>/dev/null; then
        echo -e "${RED}✗ Syntax error in: $py_file${NC}"
        python3 -m py_compile "$py_file" 2>&1 | head -5
        syntax_errors=$((syntax_errors + 1))
    fi
done < <(find "$PROJECT_ROOT/services" "$PROJECT_ROOT/shared" "$PROJECT_ROOT/tests" -name "*.py" -type f ! -path "*/.venv/*" ! -path "*/__pycache__/*" 2>/dev/null)

if [ $syntax_errors -gt 0 ]; then
    echo ""
    echo -e "${RED}✗ Found $syntax_errors file(s) with syntax errors${NC}"
    echo "Fix syntax errors before running tests"
    exit 1
else
    echo -e "${GREEN}✓ All Python files have valid syntax${NC}"
fi

echo ""

###############################################################################
# 2. IMPORT VALIDATION
###############################################################################

echo "2. Validating critical imports..."
echo "-------------------------------------------"

cd "$PROJECT_ROOT"

# Run import validation smoke tests
if python3 -m pytest tests/smoke/test_import_validation.py -v --tb=short -q 2>&1 | tee /tmp/import_validation.log; then
    echo -e "${GREEN}✓ All critical imports successful${NC}"
else
    echo -e "${RED}✗ Import validation failed${NC}"
    echo "Check /tmp/import_validation.log for details"
    exit 2
fi

echo ""

###############################################################################
# 3. SERVICE HEALTH CHECKS
###############################################################################

echo "3. Checking service health..."
echo "-------------------------------------------"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Docker is not running${NC}"
    echo "  Skipping service health checks"
    echo "  Integration tests will be skipped"
else
    # Run service health smoke tests
    if python3 -m pytest tests/smoke/test_service_health.py -v --tb=short -q 2>&1 | tee /tmp/service_health.log; then
        echo -e "${GREEN}✓ All services are healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Some services are not healthy${NC}"
        echo "  Check /tmp/service_health.log for details"
        echo "  Integration tests may be skipped"
        # Don't exit - let tests handle this
    fi
fi

echo ""

###############################################################################
# 4. SUMMARY
###############################################################################

echo "============================================"
echo "Pre-Test Validation Complete"
echo "============================================"
echo ""
echo -e "${GREEN}✓ Syntax validation: PASSED${NC}"
echo -e "${GREEN}✓ Import validation: PASSED${NC}"

if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Service health: CHECKED${NC}"
else
    echo -e "${YELLOW}⚠ Service health: SKIPPED (Docker not running)${NC}"
fi

echo ""
echo "You can now run tests with:"
echo "  pytest tests/unit/"
echo "  pytest tests/integration/"
echo "  pytest tests/e2e/"
echo ""

exit 0
