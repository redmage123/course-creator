# Course Creator Platform - Test Framework

## Overview

This is a comprehensive, modular test framework built following SOLID principles for the Course Creator Platform. The framework provides automated testing for all layers of the application including unit tests, integration tests, frontend tests, and end-to-end tests.

## Architecture

### SOLID Principles Implementation

The test framework follows all five SOLID principles:

1. **Single Responsibility Principle (SRP)**: Each test class and module has a single, focused responsibility
2. **Open/Closed Principle (OCP)**: The framework is extensible through configuration and plugins without modifying core code
3. **Liskov Substitution Principle (LSP)**: Test interfaces can be substituted with different implementations
4. **Interface Segregation Principle (ISP)**: Clean, focused interfaces for different test concerns
5. **Dependency Inversion Principle (DIP)**: Framework depends on abstractions, not concrete implementations

### Framework Components

```
tests/
├── framework/                     # Core test framework (SOLID architecture)
│   ├── __init__.py
│   ├── test_config.py            # Configuration management
│   ├── test_suite.py             # Test suite abstractions and implementations
│   ├── test_runner.py            # Test execution orchestration
│   ├── test_reporter.py          # Result reporting and metrics
│   └── test_factory.py           # Object creation factories
├── unit/                         # Unit tests for domain entities
│   ├── user_management/
│   ├── course_management/
│   ├── content_management/
│   ├── analytics/
│   └── rbac/                      # Enhanced RBAC System unit tests
├── integration/                  # Integration tests for service interactions
│   └── services/
├── frontend/                     # Frontend JavaScript module tests
│   └── components/
├── e2e/                         # End-to-end workflow tests
├── main.py          # Main test execution entry point
├── conftest.py                  # Pytest configuration and fixtures
└── README.md                    # This documentation
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend tests)
- PostgreSQL (for integration tests)
- Redis (for session/cache tests)

### Installation

1. Install Python dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov
pip install aiohttp fastapi httpx
```

2. Install Node.js dependencies:
```bash
npm install jest @testing-library/jest-dom
```

### Basic Usage

#### Run All Tests
```bash
python tests/main.py
```

#### Run Specific Test Types
```bash
# Unit tests only
python tests/main.py --type unit

# Integration tests only
python tests/main.py --type integration

# Frontend tests only
python tests/main.py --type frontend

# End-to-end tests only
python tests/main.py --type e2e
```

#### Run by Priority
```bash
# High priority tests only
python tests/main.py --priority high

# Medium priority tests only
python tests/main.py --priority medium
```

#### Run Specific Test Suites
```bash
# Single suite
python tests/main.py --suite user_management_unit

# Multiple suites
python tests/main.py --suites user_management_unit course_management_unit
```

#### CI/CD Mode
```bash
# Run in CI/CD mode with fail-fast
python tests/main.py --ci --fail-fast

# Generate coverage reports
python tests/main.py --coverage
```

### Advanced Usage

#### Verbose Output
```bash
python tests/main.py --verbose
```

#### Parallel Execution
```bash
# Use 8 parallel workers
python tests/main.py --parallel 8

# Disable parallel execution
python tests/main.py --no-parallel
```

#### Custom Configuration
```bash
python tests/main.py --config-file path/to/config.yaml
```

## Test Categories

### Unit Tests

Test individual domain entities and business logic in isolation.

**Location**: `tests/unit/`

**Coverage**:
- User Management domain entities (User, Session, PasswordPolicy)
- **Student Login System** (GDPR-compliant authentication, consent management)
- Course Management domain entities (Course, Enrollment, Feedback)
- Content Management domain entities (Syllabus, Slide, Lab, Quiz)
- Analytics domain entities (StudentActivity, LearningAnalytics)
- **Enhanced RBAC System** (Organization, Membership, Track, MeetingRoom, Permission entities)

**Example**:
```bash
python tests/main.py --type unit --suite user_management_unit
```

### Integration Tests

Test interactions between services and components.

**Location**: `tests/integration/`

**Coverage**:
- Service-to-service communication
- **Student Login GDPR Compliance** (cross-service privacy validation)
- Database integration
- API endpoint integration
- Event-driven communication
- Error handling across service boundaries

**Example**:
```bash
python tests/main.py --type integration
```

### Frontend Tests

Test JavaScript modules and UI components.

**Location**: `tests/frontend/`

**Coverage**:
- Authentication module
- Navigation module
- Notification system
- Form validation
- API client
- UI components
- Event bus
- **Student Login UI & GDPR Compliance** (privacy controls, consent management)
- **Comprehensive Platform Validation (NEW)**:
  - All microservice health checks via HTTPS
  - Organization registration API functionality
  - Country dropdown default selection (US vs Canada)
  - Keyboard navigation in country dropdowns
  - Frontend HTTPS accessibility
  - Cross-service API integration

**Key Tests**:
- `test_student_login_ui.py` - Student login interface and GDPR compliance
- `test_platform_comprehensive.py` - Complete platform validation
- `test_platform_comprehensive.html` - Interactive browser test suite

**Example**:
```bash
python tests/main.py --type frontend

# Run comprehensive platform test specifically
python -m pytest tests/frontend/test_platform_comprehensive.py -v

# Open interactive browser test
firefox tests/frontend/test_platform_comprehensive.html
```

### End-to-End Tests

Test complete user workflows and system interactions.

**Location**: `tests/e2e/`

**Coverage**:
- User registration and login flows
- **Student Login Complete Workflows** (authentication, consent, privacy)
- Course creation and management workflows
- Student enrollment and learning flows
- Content upload and management
- Analytics and reporting workflows

**Example**:
```bash
python tests/main.py --type e2e
```

### Login Redirect E2E Tests (New in v3.3.1)

Comprehensive E2E tests for role-based login redirects with localStorage and URL parameter validation.

**Location**: `tests/e2e/test_login_redirect_proof.py`

**Coverage**:
- **Site Admin Login**: Validates redirect to `site-admin-dashboard.html`
- **Org Admin Login**: Validates redirect to `org-admin-dashboard.html?org_id={organization_id}`
- **localStorage Validation**: Verifies all required session data is stored
- **URL Parameter Validation**: Ensures org_id parameter is included for org-admins

**Test Features**:
- Browser automation with Selenium WebDriver
- localStorage session data verification
- URL parameter validation for org-admin redirects
- Screenshot capture for debugging
- Privacy modal handling
- Clean session state between tests

**Running Tests**:
```bash
# Run all login redirect tests
HEADLESS=true TEST_BASE_URL=https://localhost:3000 pytest tests/e2e/test_login_redirect_proof.py -v

# Run specific role test
pytest tests/e2e/test_login_redirect_proof.py::TestLoginRedirectProof::test_admin_login_redirects_to_site_admin_dashboard -v
pytest tests/e2e/test_login_redirect_proof.py::TestLoginRedirectProof::test_org_admin_login_redirects_to_org_admin_dashboard -v

# Run with visible browser (non-headless)
TEST_BASE_URL=https://localhost:3000 pytest tests/e2e/test_login_redirect_proof.py -v
```

**Test Credentials**:
- **Admin**: username=`admin`, password=`admin123!`
- **Org Admin**: username=`bbrelin`, password=`f00bar123!`

**Validated Requirements**:
1. ✅ Login stores complete user object in localStorage as `currentUser`
2. ✅ Login stores session timestamps (`sessionStart`, `lastActivity`)
3. ✅ Org-admin redirect includes `org_id` URL parameter
4. ✅ Site admin redirect includes `is_site_admin` field
5. ✅ No redirect loops or 10-12 second delays
6. ✅ Dashboard validation passes without redirecting back to homepage

**Related Documentation**:
- Troubleshooting: `claude.md/10-troubleshooting.md` - "Login Redirect Issues (Fixed v3.3.1)"
- Implementation: `frontend/html/index.html:513-620` - Login handler
- Validation: `frontend/js/modules/org-admin-core.js:44-126` - Dashboard validation

### Enhanced RBAC System Tests (New in v2.3)

Comprehensive test suite for the Enhanced Role-Based Access Control system with 102 tests achieving 100% success rate.

**Location**: `tests/runners/run_rbac_tests.py`

**Coverage**:
- **Unit Tests (48 tests)**: Organization, Membership, Track, MeetingRoom services with complete business logic validation
- **Integration Tests (22 tests)**: API endpoints, authentication flows, cross-service integration, and audit logging
- **Frontend Tests (15 tests)**: Dashboard components, user interactions, modal management, and responsive design
- **E2E Tests (8 tests)**: Complete workflows for organization management, member lifecycle, and meeting room creation
- **Security Tests (6 tests)**: Authentication, authorization, permission checks, and JWT token validation
- **Code Quality Tests (3 tests)**: Python (Flake8), JavaScript (ESLint), and CSS (Stylelint) linting with 391 fixed errors

**Specialized Test Runner**:
```bash
# Complete RBAC test suite (102/102 tests passing)
python tests/runners/run_rbac_tests.py

# Run specific test categories
python tests/runners/run_rbac_tests.py --suite unit               # Unit tests (48/48)
python tests/runners/run_rbac_tests.py --suite integration        # Integration tests (22/22)
python tests/runners/run_rbac_tests.py --suite frontend           # Frontend tests (15/15)
python tests/runners/run_rbac_tests.py --suite e2e                # E2E tests (8/8)
python tests/runners/run_rbac_tests.py --suite security           # Security tests (6/6)
python tests/runners/run_rbac_tests.py --suite lint               # Code quality tests (3/3)

# Performance and coverage reporting
python tests/runners/run_rbac_tests.py --coverage                 # With coverage analysis
python tests/runners/run_rbac_tests.py --verbose                  # Detailed output
```

**Key RBAC Test Features**:
- **Multi-tenant Organization Management**: Complete organization lifecycle testing with member management
- **Granular Permission System**: Role-based access control with project-specific permissions
- **Teams/Zoom Integration**: Meeting room creation and management with real-time status validation  
- **JWT Authentication**: Secure token-based authentication with expiration and validation testing
- **Comprehensive Audit Logging**: Complete audit trail validation for all RBAC operations
- **Email Integration**: Hydra-configured email service testing for notifications
- **Code Quality Enforcement**: Automated linting with 391 Python/JavaScript/CSS errors fixed
- **100% Success Rate**: All 102 tests consistently passing with comprehensive error handling

### Student Login System Tests (New in v3.0)

Comprehensive GDPR-compliant test suite for the student login system with privacy-by-design testing.

**Location**: Multiple test directories

**Coverage**:
- **Unit Tests (50+ tests)**: Authentication endpoints, consent management, data minimization, privacy controls
- **Integration Tests (25+ tests)**: Cross-service privacy compliance, analytics consent, instructor notifications
- **Frontend Tests (40+ tests)**: UI/UX validation, accessibility, responsive design, JavaScript functionality
- **E2E Tests (20+ tests)**: Complete login workflows, error handling, performance testing
- **Lint Tests (15+ tests)**: Code quality, security patterns, GDPR compliance validation

**Test Files**:
- `tests/unit/user_management/test_student_login.py` - Core authentication and privacy unit tests
- `tests/integration/test_student_login_gdpr.py` - Cross-service GDPR compliance validation
- `tests/frontend/test_student_login_ui.py` - UI/UX and accessibility testing
- `tests/e2e/test_student_login_e2e.py` - Complete workflow validation
- `tests/lint/test_student_login_lint.py` - Code quality and security testing

**Specialized Test Features**:
- **GDPR Articles 5, 6, 7, 13, 25 Compliance**: Comprehensive privacy regulation testing
- **Data Minimization Validation**: Ensures only necessary data is collected and processed
- **Explicit Consent Management**: Validates opt-in requirements and consent withdrawal
- **Cross-Service Privacy Boundaries**: Tests data protection across microservices
- **Anonymized Device Fingerprinting**: Security testing with privacy protection
- **Analytics Consent Validation**: Conditional data processing based on user consent
- **Instructor Notification Controls**: Privacy-compliant educational engagement tracking

**Specialized Test Runner**:
```bash
# Complete student login test suite (all tests)
python tests/runners/run_student_login_tests.py

# Run specific test categories
python tests/runners/run_student_login_tests.py --suite unit           # Unit tests (50+ tests)
python tests/runners/run_student_login_tests.py --suite integration   # GDPR compliance tests (25+ tests)
python tests/runners/run_student_login_tests.py --suite frontend      # UI/UX tests (40+ tests)
python tests/runners/run_student_login_tests.py --suite e2e           # E2E workflow tests (20+ tests)
python tests/runners/run_student_login_tests.py --suite lint          # Code quality tests (15+ tests)
python tests/runners/run_student_login_tests.py --suite security      # Security & privacy tests

# Performance and coverage reporting
python tests/runners/run_student_login_tests.py --coverage            # With coverage analysis
python tests/runners/run_student_login_tests.py --verbose             # Detailed output
```

**Manual Test Execution**:
```bash
# Individual test files
python -m pytest tests/unit/user_management/test_student_login.py -v
python -m pytest tests/integration/test_student_login_gdpr.py -v
python -m pytest tests/frontend/test_student_login_ui.py -v
python -m pytest tests/e2e/test_student_login_e2e.py -v -s
python -m pytest tests/lint/test_student_login_lint.py -v

# Using the comprehensive test runner
python tests/run_all_tests.py --suite unit              # Includes student login unit tests
python tests/run_all_tests.py --suite integration      # Includes GDPR compliance tests
python tests/run_all_tests.py --suite frontend         # Includes UI/UX tests
python tests/run_all_tests.py --suite e2e              # Includes workflow tests
python tests/run_all_tests.py --suite lint             # Includes code quality tests
python tests/run_all_tests.py --suite student_login    # Run specialized runner

# Run all student login related tests
python tests/run_all_tests.py | grep -i "student\|login\|gdpr"
```

**Key GDPR Compliance Features**:
- **Privacy by Design**: All tests validate privacy-first implementation
- **Consent Granularity**: Separate consent for analytics and notifications
- **Data Retention Policies**: Validates proper data lifecycle management
- **Error Privacy Protection**: Ensures no sensitive data in error messages
- **Cross-Service Data Minimization**: Validates minimal data sharing between services
- **Regulatory Compliance**: EU GDPR and AI Act compliance validation

## Test Framework Features

### Modular Architecture

The test framework follows SOLID principles with clean separation of concerns:

- **TestConfig**: Manages configuration for different test environments
- **TestSuite**: Abstract base classes and concrete implementations for different test types
- **TestRunner**: Orchestrates test execution with dependency management
- **TestReporter**: Generates comprehensive reports in multiple formats
- **TestFactory**: Creates test objects and utilities following factory pattern

### Advanced Features

- **Dependency Management**: Tests run in correct order based on dependencies
- **Parallel Execution**: Configurable parallel test execution for faster results
- **Multiple Report Formats**: JSON, HTML, JUnit XML, and console output
- **Coverage Integration**: Built-in code coverage reporting
- **CI/CD Optimization**: Special modes for continuous integration
- **Filtering and Selection**: Run tests by type, priority, or specific suites
- **Plugin System**: Extensible through custom plugins and hooks

## Writing Tests

### Unit Test Example

```python
# tests/unit/user_management/test_domain_entities.py
import pytest
from domain.entities.user import User, Role

class TestUser:
    def test_user_creation_with_valid_data(self):
        """Test creating a user with valid data"""
        # Arrange
        email = "test@example.com"
        username = "testuser"
        
        # Act
        user = User(
            email=email,
            username=username,
            full_name="Test User",
            password_hash="hashed_password",
            role=Role.STUDENT
        )
        
        # Assert
        assert user.email == email
        assert user.username == username
        assert user.role == Role.STUDENT
        assert user.is_active()
```

### Integration Test Example

```python
# tests/integration/services/test_service_integration.py
import pytest
from unittest.mock import AsyncMock

class TestUserCourseIntegration:
    @pytest.mark.integration
    async def test_instructor_can_create_course(self, mock_user_service, mock_course_service):
        """Test that an instructor can create a course"""
        # Arrange
        instructor_id = "instructor_123"
        mock_user_service.get_user_by_id.return_value = {
            "id": instructor_id,
            "role": "instructor"
        }
        
        # Act
        user = await mock_user_service.get_user_by_id(instructor_id)
        course = await mock_course_service.create_course({
            "title": "Python Programming",
            "instructor_id": instructor_id
        })
        
        # Assert
        assert user["role"] == "instructor"
        assert course["instructor_id"] == instructor_id
```

### Frontend Test Example

```python
# tests/frontend/components/test_javascript_modules.py
import pytest
from unittest.mock import Mock

class TestAuthModule:
    def test_auth_login_success(self, js_harness, mock_auth_module):
        """Test successful login flow"""
        # Arrange
        credentials = {"email": "test@example.com", "password": "password123"}
        mock_auth_module.login.return_value = {"access_token": "mock_token"}
        
        # Act
        result = mock_auth_module.login(credentials)
        
        # Assert
        mock_auth_module.login.assert_called_once_with(credentials)
        assert result["access_token"] == "mock_token"
```

## Configuration

### Environment Variables

```bash
# Database configuration
TEST_DATABASE_URL=postgresql://test_user:password@localhost:5432/course_creator_test
TEST_REDIS_URL=redis://localhost:6379/1

# Authentication
TEST_JWT_SECRET=test_secret_key_for_testing

# Storage
TEST_STORAGE_PATH=/tmp/test_storage

# AI Services (optional)
TEST_AI_API_KEY=your_test_api_key

# Execution settings
TEST_PARALLEL_WORKERS=4
TEST_TIMEOUT_SECONDS=600
TEST_LOG_LEVEL=INFO
```

### Custom Configuration File

Create a YAML configuration file:

```yaml
# test_config.yaml
environment:
  database_url: "postgresql://test_user:password@localhost:5432/test_db"
  redis_url: "redis://localhost:6379/1"
  jwt_secret: "test_secret"
  storage_path: "/tmp/test_storage"
  parallel_workers: 4
  timeout_seconds: 600

reporting:
  formats: ["json", "html", "junit"]
  output_dir: "test_reports"
  coverage:
    enabled: true
    threshold: 80
    report_formats: ["html", "term", "json"]

suites:
  custom_suite:
    name: "Custom Test Suite"
    test_type: "unit"
    priority: "high"
    path: "tests/custom"
    pattern: "test_*.py"
    timeout: 300
    parallel: true
    coverage: true
    markers: ["custom", "unit"]
```

## Best Practices

### Test Organization

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One Assertion Per Test**: Each test should verify one specific behavior
3. **Descriptive Test Names**: Use clear, descriptive test method names
4. **Test Isolation**: Tests should not depend on each other
5. **Mock External Dependencies**: Use mocks for external services and databases

### Domain Entity Testing

1. **Test Business Logic**: Focus on domain rules and validation
2. **Test Edge Cases**: Include boundary conditions and error cases
3. **Test Invariants**: Verify domain invariants are maintained
4. **Use Value Objects**: Test value objects separately from entities

### Service Integration Testing

1. **Test Service Boundaries**: Verify correct interaction between services
2. **Test Error Propagation**: Ensure errors are handled properly across services
3. **Test Transactional Behavior**: Verify data consistency
4. **Mock External Services**: Use mocks for third-party services

### Frontend Testing

1. **Test User Interactions**: Verify user actions trigger correct behavior
2. **Test State Management**: Ensure application state is managed correctly
3. **Test API Integration**: Verify frontend correctly calls backend APIs
4. **Test Error Handling**: Ensure UI handles errors gracefully

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: course_creator_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Set up Node.js
      uses: actions/setup-node@v2
      with:
        node-version: 16
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        npm install
    
    - name: Run tests
      run: python tests/main.py --ci --coverage
      env:
        TEST_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/course_creator_test
        TEST_REDIS_URL: redis://localhost:6379/1
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v1
      with:
        files: ./coverage.xml
```

## Test Reports

The framework generates comprehensive reports in multiple formats:

1. **JSON Report**: Machine-readable test results for CI/CD integration
2. **HTML Report**: Human-readable web interface with interactive features
3. **JUnit XML**: Standard format for CI/CD systems and IDEs
4. **Console Report**: Terminal-friendly output for local development
5. **Coverage Report**: Code coverage analysis with detailed metrics

Reports are automatically generated in the `tests/reports/` directory.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Ensure PostgreSQL is running
   - Check database URL configuration
   - Verify test database exists

2. **Redis Connection Errors**:
   - Ensure Redis is running
   - Check Redis URL configuration
   - Verify Redis is accessible

3. **Import Errors**:
   - Check Python path configuration
   - Ensure all dependencies are installed
   - Verify module structure

4. **Timeout Errors**:
   - Increase timeout configuration
   - Check for infinite loops in tests
   - Verify external service availability

### Debug Mode

Run tests with debug information:

```bash
python tests/main.py --verbose --no-parallel
```

## License

This test framework is part of the Course Creator Platform and follows the same license terms.