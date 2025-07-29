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
│   └── analytics/
├── integration/                  # Integration tests for service interactions
│   └── services/
├── frontend/                     # Frontend JavaScript module tests
│   └── components/
├── e2e/                         # End-to-end workflow tests
├── main_test_runner.py          # Main test execution entry point
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
python tests/main_test_runner.py
```

#### Run Specific Test Types
```bash
# Unit tests only
python tests/main_test_runner.py --type unit

# Integration tests only
python tests/main_test_runner.py --type integration

# Frontend tests only
python tests/main_test_runner.py --type frontend

# End-to-end tests only
python tests/main_test_runner.py --type e2e
```

#### Run by Priority
```bash
# High priority tests only
python tests/main_test_runner.py --priority high

# Medium priority tests only
python tests/main_test_runner.py --priority medium
```

#### Run Specific Test Suites
```bash
# Single suite
python tests/main_test_runner.py --suite user_management_unit

# Multiple suites
python tests/main_test_runner.py --suites user_management_unit course_management_unit
```

#### CI/CD Mode
```bash
# Run in CI/CD mode with fail-fast
python tests/main_test_runner.py --ci --fail-fast

# Generate coverage reports
python tests/main_test_runner.py --coverage
```

### Advanced Usage

#### Verbose Output
```bash
python tests/main_test_runner.py --verbose
```

#### Parallel Execution
```bash
# Use 8 parallel workers
python tests/main_test_runner.py --parallel 8

# Disable parallel execution
python tests/main_test_runner.py --no-parallel
```

#### Custom Configuration
```bash
python tests/main_test_runner.py --config-file path/to/config.yaml
```

## Test Categories

### Unit Tests

Test individual domain entities and business logic in isolation.

**Location**: `tests/unit/`

**Coverage**:
- User Management domain entities (User, Session, PasswordPolicy)
- Course Management domain entities (Course, Enrollment, Feedback)
- Content Management domain entities (Syllabus, Slide, Lab, Quiz)
- Analytics domain entities (StudentActivity, LearningAnalytics)

**Example**:
```bash
python tests/main_test_runner.py --type unit --suite user_management_unit
```

### Integration Tests

Test interactions between services and components.

**Location**: `tests/integration/`

**Coverage**:
- Service-to-service communication
- Database integration
- API endpoint integration
- Event-driven communication
- Error handling across service boundaries

**Example**:
```bash
python tests/main_test_runner.py --type integration
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

**Example**:
```bash
python tests/main_test_runner.py --type frontend
```

### End-to-End Tests

Test complete user workflows and system interactions.

**Location**: `tests/e2e/`

**Coverage**:
- User registration and login flows
- Course creation and management workflows
- Student enrollment and learning flows
- Content upload and management
- Analytics and reporting workflows

**Example**:
```bash
python tests/main_test_runner.py --type e2e
```

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
      run: python tests/main_test_runner.py --ci --coverage
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
python tests/main_test_runner.py --verbose --no-parallel
```

## License

This test framework is part of the Course Creator Platform and follows the same license terms.