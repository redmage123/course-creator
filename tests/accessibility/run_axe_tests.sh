#!/bin/bash

# Accessibility Testing with axe-core
# Tests all key pages for WCAG 2.1 AA compliance

echo "==================================="
echo "Running axe-core Accessibility Tests"
echo "==================================="

# Check if axe is installed
if ! command -v axe &> /dev/null; then
    echo "❌ axe-core not installed. Installing..."
    npm install -g @axe-core/cli
fi

# Base URL
BASE_URL="https://localhost:3000"

# Array of pages to test
declare -a pages=(
    ""  # Landing page
    "/html/register.html"
    "/html/student-login.html"
    "/html/org-admin-dashboard.html?org_id=1"
    "/html/instructor-dashboard.html"
    "/html/student-dashboard.html"
    "/html/site-admin-dashboard.html"
    "/html/password-change.html"
    "/html/organization-registration.html"
    "/html/quiz.html"
    "/html/lab.html"
    "/html/lab-multi-ide.html"
    "/html/admin.html"
    "/html/project-dashboard.html"
)

# Create results directory
mkdir -p tests/accessibility/results
RESULTS_DIR="tests/accessibility/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Summary variables
total_pages=0
passed_pages=0
failed_pages=0

echo ""
echo "Testing ${#pages[@]} pages..."
echo ""

# Test each page
for page in "${pages[@]}"; do
    total_pages=$((total_pages + 1))
    page_name=$(echo "$page" | sed 's/[\/\?=]/_/g' | sed 's/__*/_/g' | sed 's/^_//' | sed 's/_$//')
    if [ -z "$page_name" ]; then
        page_name="index"
    fi

    echo "[$total_pages/${#pages[@]}] Testing: ${BASE_URL}${page}"

    # Run axe test
    axe "${BASE_URL}${page}" \
        --disable=certificate-error \
        --reporter=json \
        --save="${RESULTS_DIR}/${page_name}_${TIMESTAMP}.json" \
        > /dev/null 2>&1

    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "    ✅ PASS - No critical violations"
        passed_pages=$((passed_pages + 1))
    else
        echo "    ❌ FAIL - Violations found"
        failed_pages=$((failed_pages + 1))

        # Show violation count
        violations=$(grep -o '"violations":\[' "${RESULTS_DIR}/${page_name}_${TIMESTAMP}.json" | wc -l)
        echo "    📋 Check results: ${RESULTS_DIR}/${page_name}_${TIMESTAMP}.json"
    fi
    echo ""
done

# Summary
echo "==================================="
echo "Test Summary"
echo "==================================="
echo "Total Pages:  $total_pages"
echo "Passed:       $passed_pages ($(echo "scale=1; $passed_pages * 100 / $total_pages" | bc)%)"
echo "Failed:       $failed_pages ($(echo "scale=1; $failed_pages * 100 / $total_pages" | bc)%)"
echo ""
echo "Detailed results saved to: $RESULTS_DIR"
echo "==================================="

# Exit with failure if any tests failed
if [ $failed_pages -gt 0 ]; then
    exit 1
fi

exit 0
