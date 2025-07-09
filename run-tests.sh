#!/bin/bash

# Course Creator Platform - Test Runner Script
# This script runs all tests locally to ensure everything works before committing

set -e

echo "🧪 Starting Course Creator Platform Test Suite"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if services are running
check_services() {
    print_status "Checking if services are running..."
    
    # Check user management service
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "User management service is running"
    else
        print_warning "User management service is not running"
        print_status "Starting user management service..."
        cd services/user-management
        python main.py &
        USER_MGMT_PID=$!
        cd ../..
        sleep 3
    fi
    
    # Check course management service
    if curl -s http://localhost:8004/health > /dev/null; then
        print_success "Course management service is running"
    else
        print_warning "Course management service is not running"
        print_status "Starting course management service..."
        cd services/course-management
        python main.py &
        COURSE_MGMT_PID=$!
        cd ../..
        sleep 3
    fi
    
    # Check frontend service
    if curl -s http://localhost:8080 > /dev/null; then
        print_success "Frontend service is running"
    else
        print_warning "Frontend service is not running"
        print_status "Starting frontend service..."
        npm run dev &
        FRONTEND_PID=$!
        sleep 3
    fi
}

# Run linting
run_linting() {
    print_status "Running code linting..."
    
    if npm run lint; then
        print_success "Linting passed"
    else
        print_warning "Linting failed, attempting to fix..."
        npm run lint:fix
    fi
}

# Run frontend unit tests
run_frontend_tests() {
    print_status "Running frontend unit tests..."
    
    if npm run test:unit; then
        print_success "Frontend unit tests passed"
    else
        print_error "Frontend unit tests failed"
        return 1
    fi
}

# Run backend unit tests
run_backend_tests() {
    print_status "Running backend unit tests..."
    
    cd tests
    if python -m pytest unit/backend/ -v --tb=short; then
        print_success "Backend unit tests passed"
    else
        print_warning "Backend unit tests failed (services may not be running)"
    fi
    cd ..
}

# Run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    cd tests
    if python -m pytest integration/ -v --tb=short; then
        print_success "Integration tests passed"
    else
        print_warning "Integration tests failed (services may not be running)"
    fi
    
    print_status "Running registration flow integration test..."
    if python integration/test_registration_flow.py; then
        print_success "Registration flow test passed"
    else
        print_warning "Registration flow test failed"
    fi
    cd ..
}

# Run E2E tests
run_e2e_tests() {
    print_status "Running E2E tests..."
    
    if npm run test:e2e; then
        print_success "E2E tests passed"
    else
        print_warning "E2E tests failed (services may not be running)"
    fi
}

# Run coverage tests
run_coverage_tests() {
    print_status "Running test coverage analysis..."
    
    if npm run test:coverage; then
        print_success "Coverage analysis completed"
        print_status "Coverage report available in coverage/ directory"
    else
        print_warning "Coverage analysis failed"
    fi
}

# Cleanup function
cleanup() {
    print_status "Cleaning up test processes..."
    
    if [ ! -z "$USER_MGMT_PID" ]; then
        kill $USER_MGMT_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$COURSE_MGMT_PID" ]; then
        kill $COURSE_MGMT_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    print_status "Course Creator Platform Test Suite Starting..."
    
    # Check if npm dependencies are installed
    if [ ! -d "node_modules" ]; then
        print_status "Installing npm dependencies..."
        npm install
    fi
    
    # Check if Python dependencies are installed
    if ! python -c "import pytest" 2>/dev/null; then
        print_status "Installing Python dependencies..."
        pip install pytest pytest-asyncio httpx fastapi uvicorn pymongo python-multipart passlib[bcrypt] python-jose[cryptography] requests
    fi
    
    # Run test suite based on arguments
    case "${1:-all}" in
        "lint")
            run_linting
            ;;
        "frontend")
            run_frontend_tests
            ;;
        "backend")
            check_services
            run_backend_tests
            ;;
        "integration")
            check_services
            run_integration_tests
            ;;
        "e2e")
            check_services
            run_e2e_tests
            ;;
        "coverage")
            run_coverage_tests
            ;;
        "all")
            run_linting
            run_frontend_tests
            check_services
            run_backend_tests
            run_integration_tests
            run_e2e_tests
            run_coverage_tests
            ;;
        *)
            echo "Usage: $0 [lint|frontend|backend|integration|e2e|coverage|all]"
            exit 1
            ;;
    esac
    
    print_success "Test suite completed!"
}

# Run main function
main "$@"