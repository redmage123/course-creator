#!/bin/bash

#
# Codebase Cleanup Script
#
# PURPOSE: Remove unnecessary files, temporary data, and redundant documentation
# CATEGORIES:
# 1. Python cache files (__pycache__, *.pyc, *.pyo)
# 2. Log files (*.log)
# 3. Temporary test outputs
# 4. Duplicate/redundant summary documents
# 5. Old test scripts in root directory
# 6. Test lab storage data
#

echo "=========================================="
echo "Course Creator Platform - Codebase Cleanup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Counters
total_removed=0
total_size=0

# Function to remove files and track statistics
remove_files() {
    local pattern=$1
    local description=$2
    local count=0
    local size=0

    echo -e "${YELLOW}Removing: $description${NC}"

    while IFS= read -r file; do
        if [ -f "$file" ]; then
            fsize=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
            size=$((size + fsize))
            rm -f "$file"
            count=$((count + 1))
        elif [ -d "$file" ]; then
            dsize=$(du -sb "$file" 2>/dev/null | awk '{print $1}' || echo 0)
            size=$((size + dsize))
            rm -rf "$file"
            count=$((count + 1))
        fi
    done < <(eval "$pattern")

    if [ $count -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} Removed $count items (~$(( size / 1024 )) KB)"
        total_removed=$((total_removed + count))
        total_size=$((total_size + size))
    else
        echo -e "  ${GREEN}✓${NC} No files to remove"
    fi
    echo ""
}

# 1. Python cache files
echo "=== Cleaning Python Cache Files ==="
remove_files "find . -type d -name '__pycache__' -not -path './.venv/*' -not -path './node_modules/*'" "Python __pycache__ directories"
remove_files "find . -type f -name '*.pyc' -not -path './.venv/*' -not -path './node_modules/*'" "Python bytecode files (*.pyc)"
remove_files "find . -type f -name '*.pyo' -not -path './.venv/*' -not -path './node_modules/*'" "Python optimized bytecode (*.pyo)"

# 2. Log files (keep structure, remove content)
echo "=== Cleaning Log Files ==="
if [ -d "./logs" ]; then
    echo -e "${YELLOW}Clearing log file contents${NC}"
    for logfile in ./logs/*.log; do
        if [ -f "$logfile" ]; then
            > "$logfile"
        fi
    done
    echo -e "  ${GREEN}✓${NC} Cleared log files (kept structure)"
    echo ""
fi

remove_files "find ./services -type f -name '*.log'" "Service log files"

# 3. Temporary test outputs
echo "=== Cleaning Test Outputs ==="
remove_files "find . -maxdepth 1 -type f -name '*_test_output*.txt'" "Test output files"
remove_files "find . -maxdepth 1 -type f -name 'verification_*.txt'" "Verification output files"
remove_files "find ./tests/reports -type f -name '*.txt' 2>/dev/null || echo ''" "Test report text files"

# 4. Redundant summary documents
echo "=== Cleaning Redundant Documentation ==="
echo -e "${YELLOW}Note: Keeping essential documentation, removing duplicates${NC}"

# List of redundant summary files to remove
redundant_docs=(
    "ANALYTICS_TEST_SUMMARY.md"
    "API_ENDPOINT_TEST_REPORT.md"
    "AUDIT_LOG_TEST_SUMMARY.md"
    "CRUD_TEST_SUMMARY.md"
    "DATABASE_TEST_REFACTORING_SUMMARY.md"
    "FINAL_TEST_REFACTORING_SUMMARY.md"
    "INSTRUCTOR_CRUD_TEST_RESULTS.md"
    "LAB_MANAGEMENT_TEST_SUMMARY.md"
    "LAB_MODULE_TEST_REPORT.md"
    "MICROSERVICES_TEST_STATUS.md"
    "PRAGMATIC_SOLUTION.md"
    "PROJECTS_MODAL_E2E_TEST_SUMMARY.md"
    "PROJECTS_MODAL_TEST_SUITE_SUMMARY.md"
    "RAG_SERVICE_TEST_SUMMARY.md"
    "STATISTICS_METRICS_TEST_REPORT.md"
    "TEST_EXECUTION_RESULTS.md"
    "TEST_FAILURE_ANALYSIS.md"
    "TEST_REFACTORING_COMPLETE.md"
    "TEST_REFACTORING_PROGRESS.md"
    "TEST_REFACTORING_SUMMARY.md"
    "TEST_SUITE_SUMMARY.md"
    "USER_MANAGEMENT_TEST_FIXES_SUMMARY.md"
    "USER_MANAGEMENT_TEST_SUMMARY.md"
    "TEST_REFACTORING_COMPLETE_SUMMARY.md"
    "AUDIT_LOG_FIXES.md"
)

count=0
for doc in "${redundant_docs[@]}"; do
    if [ -f "$doc" ]; then
        rm -f "$doc"
        count=$((count + 1))
    fi
done
echo -e "  ${GREEN}✓${NC} Removed $count redundant documentation files"
echo ""

# 5. Old test scripts in root directory
echo "=== Cleaning Root Directory Test Scripts ==="
root_test_scripts=(
    "test_admin_login.py"
    "test_api_authenticated.py"
    "test_api_endpoints.py"
    "test_browser_capture.py"
    "test_crud_simple.py"
    "test_lab_module.sh"
    "test_login_model.py"
    "test_organization_endpoints.py"
    "test_selenium_registration.py"
    "test_site_admin_endpoint.py"
    "test_statistics_metrics.sh"
    "verify_crud_with_curl.sh"
)

count=0
for script in "${root_test_scripts[@]}"; do
    if [ -f "$script" ]; then
        rm -f "$script"
        count=$((count + 1))
    fi
done
echo -e "  ${GREEN}✓${NC} Removed $count test scripts from root directory"
echo ""

# 6. Test lab storage data (keep structure, remove test data)
echo "=== Cleaning Test Lab Storage ==="
if [ -d "./lab-storage" ]; then
    test_dirs=$(find ./lab-storage -mindepth 1 -maxdepth 1 -type d | wc -l)
    if [ $test_dirs -gt 0 ]; then
        echo -e "${YELLOW}Removing test lab storage directories${NC}"
        rm -rf ./lab-storage/*
        echo -e "  ${GREEN}✓${NC} Removed $test_dirs test lab directories"
    else
        echo -e "  ${GREEN}✓${NC} No test lab directories to remove"
    fi
    echo ""
fi

# 7. Old output directories
echo "=== Cleaning Old Output Directories ==="
remove_files "find ./services -type d -name 'outputs' 2>/dev/null || echo ''" "Service output directories"

# 8. Screenshot and report files
echo "=== Cleaning Test Artifacts ==="
remove_files "find ./tests/reports -type f -name '*.png' 2>/dev/null || echo ''" "Test screenshot files"
remove_files "find ./tests/reports -type f -name '*.html' 2>/dev/null || echo ''" "Test report HTML files"

# 9. Duplicate test files
echo "=== Cleaning Duplicate Test Files ==="
remove_files "find ./tests -type f -name '*_refactored.py' 2>/dev/null || echo ''" "Refactored duplicate test files"

# Summary
echo "=========================================="
echo "Cleanup Summary"
echo "=========================================="
echo -e "${GREEN}Total items removed: $total_removed${NC}"
echo -e "${GREEN}Total space freed: ~$(( total_size / 1024 / 1024 )) MB${NC}"
echo ""

# List of important files kept
echo "Important files retained:"
echo "  - CLAUDE.md (root documentation)"
echo "  - README.md (project overview)"
echo "  - EXCEPTION_REFACTORING_COMPLETE.md (recent work)"
echo "  - ORG_ADMIN_REFACTORING_SUMMARY.md (recent work)"
echo "  - INSTRUCTOR_DASHBOARD_TEST_SUMMARY.md (recent work)"
echo "  - COMPLETE_WORKFLOW_VERIFICATION.md (recent work)"
echo "  - SYNTAX_VALIDATION_REPORT.md (recent work)"
echo "  - HOW_TO_RUN_TESTS.md (testing guide)"
echo "  - TESTING_GUIDE.md (comprehensive guide)"
echo "  - verify_complete_workflow.sh (verification tool)"
echo "  - check_syntax.py (validation tool)"
echo "  - All tests in tests/ directory"
echo "  - All source code in services/ directory"
echo ""

echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
