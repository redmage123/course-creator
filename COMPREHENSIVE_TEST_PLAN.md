# Comprehensive Test Plan for Course Creator Platform

## Overview
This document outlines the complete testing strategy for all 16 microservices and the React frontend.

## Test Structure

```
course-creator/
├── tests/
│   ├── unit/                    # Unit tests for all services
│   │   ├── analytics/
│   │   ├── content_management/
│   │   ├── course_generator/
│   │   ├── course_management/
│   │   ├── demo_service/
│   │   ├── knowledge_graph/
│   │   ├── organization_management/
│   │   ├── user_management/
│   │   ├── ai_assistant_service/    # TODO: Add comprehensive tests
│   │   ├── content_storage/          # TODO: Add comprehensive tests
│   │   ├── lab_containers/           # TODO: Add comprehensive tests
│   │   ├── lab_manager/              # TODO: Add comprehensive tests
│   │   ├── local_llm_service/        # TODO: Add comprehensive tests
│   │   ├── metadata_service/         # TODO: Add comprehensive tests
│   │   ├── nlp_preprocessing/        # TODO: Add comprehensive tests
│   │   └── rag_service/              # TODO: Add comprehensive tests
│   ├── integration/             # Integration tests
│   ├── e2e/                     # End-to-end Selenium tests
│   └── regression/              # Regression tests
└── frontend-react/
    └── src/
        └── test/
            ├── setup.ts         # ✅ COMPLETED
            ├── utils.tsx        # ✅ COMPLETED
            ├── unit/
            │   ├── store/       # ✅ COMPLETED - 131 tests
            │   ├── services/    # ✅ COMPLETED - 6 service tests
            │   ├── components/  # TODO: Consolidate from co-located tests
            │   └── pages/       # TODO: Consolidate from co-located tests
            ├── integration/     # TODO: Create React integration tests
            ├── e2e/            # TODO: Create Cypress tests
            └── regression/      # TODO: Create regression tests
```

## 16 Microservices Test Requirements

### 1. ai-assistant-service
**Port**: 8009
**Purpose**: RAG-enhanced AI chatbot with NLP
**Test Requirements**:
- Unit tests for AI response generation
- Unit tests for context management
- Unit tests for conversation history
- Integration tests for RAG retrieval
- Integration tests for API endpoints

### 2. analytics
**Port**: 8001
**Purpose**: Analytics and reporting
**Test Requirements**:
- ✅ 6 unit tests exist
- TODO: Add tests for materialized views
- TODO: Add tests for PDF generation
- TODO: Add tests for time-series data

### 3. content-management
**Port**: 8003
**Purpose**: Course content management
**Test Requirements**:
- Unit tests for content validation
- Unit tests for syllabus generation
- Unit tests for content search
- Integration tests for file uploads

### 4. content-storage
**Port**: 8011
**Purpose**: File storage and backup
**Test Requirements**:
- Unit tests for storage operations
- Unit tests for backup/restore
- Integration tests for S3/local storage
- Integration tests for CDN

### 5. course-generator
**Port**: 8002
**Purpose**: AI-powered course generation
**Test Requirements**:
- Unit tests for syllabus generation
- Unit tests for slide generation
- Unit tests for quiz generation
- Integration tests for AI client
- Integration tests for fallback generators

### 6. course-management
**Port**: 8004
**Purpose**: Course CRUD and enrollment
**Test Requirements**:
- Unit tests for course operations
- Unit tests for enrollment service
- Unit tests for feedback system
- Integration tests for course publishing

### 7. demo-service
**Port**: 8010
**Purpose**: Demo data generation
**Test Requirements**:
- Unit tests for data generators
- Unit tests for PostgreSQL session storage
- Integration tests for demo workflows
- Integration tests for privacy compliance

### 8. knowledge-graph-service
**Port**: 8007
**Purpose**: Course prerequisite graph
**Test Requirements**:
- Unit tests for graph operations
- Unit tests for path finding algorithms
- Integration tests for Neo4j
- Integration tests for prerequisite chains

### 9. lab-containers
**Port**: N/A (Docker management)
**Purpose**: Student IDE containers
**Test Requirements**:
- Unit tests for container lifecycle
- Unit tests for IDE configuration
- Integration tests for Docker API
- Integration tests for resource limits

### 10. lab-manager
**Port**: 8008
**Purpose**: Lab environment orchestration
**Test Requirements**:
- Unit tests for lab creation
- Unit tests for resource allocation
- Integration tests for container deployment
- Integration tests for student access

### 11. local-llm-service
**Port**: 8012
**Purpose**: Local LLM integration
**Test Requirements**:
- Unit tests for Ollama integration
- Unit tests for model loading
- Integration tests for prompt generation
- Integration tests for response handling

### 12. metadata-service
**Port**: 8005
**Purpose**: Entity metadata and tagging
**Test Requirements**:
- Unit tests for metadata DAO
- Unit tests for fuzzy search
- Integration tests for PostgreSQL
- Integration tests for search indexing

### 13. nlp-preprocessing
**Port**: 8013
**Purpose**: NLP text processing
**Test Requirements**:
- Unit tests for text cleaning
- Unit tests for entity extraction
- Unit tests for query expansion
- Integration tests for similarity algorithms

### 14. organization-management
**Port**: 8006
**Purpose**: Multi-tenant organization management
**Test Requirements**:
- Unit tests for organization CRUD
- Unit tests for notification service
- Unit tests for bulk operations
- Integration tests for Slack/Teams

### 15. rag-service
**Port**: 8014
**Purpose**: RAG document retrieval
**Test Requirements**:
- Unit tests for document chunking
- Unit tests for vector embedding
- Unit tests for semantic search
- Integration tests for vector database

### 16. user-management
**Port**: 8000
**Purpose**: Authentication and RBAC
**Test Requirements**:
- Unit tests for password management
- Unit tests for JWT token handling
- Unit tests for RBAC enforcement
- Integration tests for login flow

## Python Test Standards

### Unit Test Template
```python
"""
{Service Name} Unit Tests

BUSINESS CONTEXT:
{Business purpose of the service}

TECHNICAL IMPLEMENTATION:
- Uses pytest for test execution
- Uses pytest-mock for mocking
- Uses pytest-cov for coverage
- Follows TDD red-green-refactor cycle

COVERAGE REQUIREMENTS:
- 80%+ line coverage
- 75%+ function coverage
- 75%+ branch coverage
- All public APIs tested
"""

import pytest
from unittest.mock import Mock, patch
from {service}.{module} import {Class}

class Test{ClassName}:
    """
    TEST SUITE: {Class Name}

    WHY THESE TESTS:
    {Rationale for test coverage}
    """

    @pytest.fixture
    def {fixture_name}(self):
        """
        FIXTURE: {Fixture Description}

        BUSINESS REQUIREMENT:
        {Why this fixture is needed}

        RETURNS:
        {What the fixture provides}
        """
        return {fixture_value}

    def test_{scenario}(self, {fixture_name}):
        """
        TEST: {Test Description}

        BUSINESS SCENARIO:
        {Real-world scenario being tested}

        TECHNICAL VALIDATION:
        {What is being validated}

        EXPECTED OUTCOME:
        {What should happen}
        """
        # Arrange
        {setup_code}

        # Act
        result = {action}

        # Assert
        assert {expectation}
```

### Integration Test Template
```python
"""
{Service Name} Integration Tests

BUSINESS CONTEXT:
{Business purpose of integration tests}

TECHNICAL IMPLEMENTATION:
- Tests real database connections
- Tests real HTTP endpoints
- Uses Docker test containers
- Cleans up after each test

COVERAGE REQUIREMENTS:
- All API endpoints tested
- All DAO methods tested
- Error handling validated
- Performance benchmarks
"""

import pytest
from fastapi.testclient import TestClient
from {service}.main import app

@pytest.fixture(scope="module")
def test_client():
    """
    FIXTURE: Test HTTP Client

    PROVIDES:
    FastAPI test client for HTTP requests
    """
    return TestClient(app)

class Test{Service}Integration:
    """
    INTEGRATION TEST SUITE: {Service}

    VALIDATES:
    - HTTP endpoints
    - Database operations
    - External service calls
    """

    def test_{endpoint_name}(self, test_client):
        """
        TEST: {Endpoint Description}

        VALIDATES:
        - Request/response cycle
        - Database persistence
        - Business logic execution
        """
        # Arrange
        payload = {test_data}

        # Act
        response = test_client.post("/endpoint", json=payload)

        # Assert
        assert response.status_code == 200
        assert response.json()["key"] == expected_value
```

## React/TypeScript Test Standards

### Component Test Template
(See frontend-react/src/test/utils.tsx for renderWithProviders)

### Service Test Template
(See frontend-react/src/test/unit/services/ for examples)

## Test Execution

### Python Tests
```bash
# Run all Python tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run e2e tests
pytest tests/e2e/

# Run with coverage
pytest --cov=services --cov-report=html --cov-report=term

# Run specific service tests
pytest tests/unit/analytics/
```

### React Tests
```bash
# Run all React tests
cd frontend-react && npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm test -- --watch

# Run specific test file
npm test -- src/test/unit/store/authSlice.test.ts
```

### Lint Tests
```bash
# Python linting
flake8 services/
mypy services/
black --check services/

# React linting
cd frontend-react && npm run lint
```

## Coverage Requirements

### Python Services
- **Line Coverage**: 80%+ per service
- **Function Coverage**: 75%+ per service
- **Branch Coverage**: 75%+ per service
- **Integration Coverage**: All endpoints tested

### React Frontend
- **Line Coverage**: 80%+ overall
- **Function Coverage**: 75%+ overall
- **Branch Coverage**: 75%+ overall
- **Component Coverage**: All pages and features tested

## Regression Tests

### Purpose
Prevent known bugs from recurring

### Structure
```python
# tests/regression/test_known_bugs.py

class TestBugFixes:
    """
    REGRESSION TEST SUITE

    PURPOSE:
    Ensure fixed bugs don't reappear in future releases
    """

    def test_bug_123_login_redirect(self):
        """
        BUG #123: Login redirect broken for org admins

        ORIGINAL ISSUE:
        Org admins were redirected to student dashboard after login

        FIX:
        Updated redirect logic in authService.ts:42

        REGRESSION PREVENTION:
        This test ensures org admins always go to org dashboard
        """
        # Test implementation
        pass
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Python tests
        run: |
          pytest --cov=services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2

  react-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run React tests
        run: |
          cd frontend-react
          npm test -- --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Maintenance

### When to Update Tests
1. When adding new features
2. When fixing bugs (add regression test)
3. When refactoring code
4. When APIs change
5. When dependencies update

### Test Review Checklist
- [ ] All tests have comprehensive documentation
- [ ] Tests follow Arrange-Act-Assert pattern
- [ ] Tests are isolated (no test pollution)
- [ ] Tests are deterministic (no flaky tests)
- [ ] Coverage meets 80%+ threshold
- [ ] All edge cases covered
- [ ] Error paths tested
- [ ] Performance is reasonable (<5s per test)

## Current Status

### Completed ✅
- Frontend test infrastructure (vitest, setup, utils)
- Redux store unit tests (131 tests)
- React service unit tests (6 services)
- Python unit tests (101 tests across services)
- Python integration tests (52 tests)
- Python e2e tests (92 tests)

### In Progress 🔄
- Comprehensive tests for all 16 microservices
- React integration tests
- Cypress E2E tests
- Regression test suite

### TODO ⏳
- Complete missing service unit tests (8 services)
- Create React integration tests
- Create Cypress E2E test framework
- Create comprehensive regression suite
- Set up coverage reporting dashboard
- Integrate with CI/CD pipeline
