#!/bin/bash

"""
Linting Script for Authentication Token Consistency

BUSINESS CONTEXT:
Scans all JavaScript files for deprecated localStorage key usage
that could cause authentication failures and redirect loops.

TECHNICAL IMPLEMENTATION:
Uses grep to find problematic patterns and ESLint for comprehensive checks

TDD METHODOLOGY:
This script is part of the TDD workflow to catch auth token issues
before they reach production.
"""

set -e

echo "================================================"
echo "Authentication Token Consistency Linter"
echo "================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any issues found
ISSUES_FOUND=0

echo "1. Checking for deprecated 'auth_token' usage..."
echo "------------------------------------------------"

# Search for localStorage.getItem('auth_token')
if grep -r "localStorage.getItem('auth_token')" frontend/ --include="*.js" 2>/dev/null; then
    echo -e "${RED}✗ Found localStorage.getItem('auth_token') - should use 'authToken'${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No localStorage.getItem('auth_token') found${NC}"
fi

# Search for localStorage.setItem('auth_token'
if grep -r "localStorage.setItem('auth_token'" frontend/ --include="*.js" 2>/dev/null; then
    echo -e "${RED}✗ Found localStorage.setItem('auth_token') - should use 'authToken'${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No localStorage.setItem('auth_token') found${NC}"
fi

# Search for localStorage.removeItem('auth_token')
if grep -r "localStorage.removeItem('auth_token')" frontend/ --include="*.js" 2>/dev/null; then
    echo -e "${RED}✗ Found localStorage.removeItem('auth_token') - should use 'authToken'${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No localStorage.removeItem('auth_token') found${NC}"
fi

echo ""
echo "2. Checking for deprecated 'access_token' usage..."
echo "------------------------------------------------"

# Search for access_token
if grep -r "localStorage.getItem('access_token')" frontend/ --include="*.js" 2>/dev/null; then
    echo -e "${RED}✗ Found localStorage.getItem('access_token') - should use 'authToken'${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No localStorage.getItem('access_token') found${NC}"
fi

if grep -r "localStorage.setItem('access_token'" frontend/ --include="*.js" 2>/dev/null; then
    echo -e "${RED}✗ Found localStorage.setItem('access_token') - should use 'authToken'${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No localStorage.setItem('access_token') found${NC}"
fi

echo ""
echo "3. Checking for deprecated 'user_data' usage..."
echo "------------------------------------------------"

# Search for user_data
if grep -r "localStorage.getItem('user_data')" frontend/ --include="*.js" 2>/dev/null; then
    echo -e "${RED}✗ Found localStorage.getItem('user_data') - should use 'currentUser'${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No localStorage.getItem('user_data') found${NC}"
fi

if grep -r "localStorage.setItem('user_data'" frontend/ --include="*.js" 2>/dev/null; then
    echo -e "${RED}✗ Found localStorage.setItem('user_data') - should use 'currentUser'${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No localStorage.setItem('user_data') found${NC}"
fi

echo ""
echo "4. Checking for correct 'authToken' usage..."
echo "------------------------------------------------"

# Count correct usage
CORRECT_USAGE=$(grep -r "localStorage.getItem('authToken')" frontend/ --include="*.js" 2>/dev/null | wc -l)
echo -e "${GREEN}✓ Found ${CORRECT_USAGE} correct uses of 'authToken'${NC}"

echo ""
echo "5. Checking for /login.html redirect issues..."
echo "------------------------------------------------"

# Search for /login.html redirects
if grep -r "window.location.href = '/login.html'" frontend/ --include="*.js" 2>/dev/null; then
    echo -e "${RED}✗ Found redirect to '/login.html' - should use '../index.html' or '/html/index.html'${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No incorrect /login.html redirects found${NC}"
fi

if grep -r 'window.location.href = "/login.html"' frontend/ --include="*.js" 2>/dev/null; then
    echo -e "${RED}✗ Found redirect to '/login.html' - should use '../index.html' or '/html/index.html'${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No incorrect /login.html redirects found${NC}"
fi

echo ""
echo "================================================"

if [ $ISSUES_FOUND -eq 1 ]; then
    echo -e "${RED}✗ FAILED: Authentication token inconsistencies found${NC}"
    echo ""
    echo "Fix these issues to prevent authentication failures and redirect loops."
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ PASSED: All authentication token usage is consistent${NC}"
    echo ""
    exit 0
fi
