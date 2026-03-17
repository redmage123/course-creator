# Testing Guide - Unit vs Integration Tests

## Quick Reference

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Dependencies**: None (use mocks/stubs for external dependencies)
- **Speed**: Fast (milliseconds)
- **Database**: No database access
- **When to use**: Testing business logic, algorithms, pure functions

### Integration Tests (`tests/integration/`)
- **Purpose**: Test components working together with real dependencies
- **Dependencies**: Real database, real services, real APIs
- **Speed**: Slower (seconds to minutes)
- **Database**: Real database connections
- **When to use**: Testing DAOs, API endpoints, service integrations

## Running Tests

### Run All Unit Tests
```bash
pytest tests/unit/ -v
```

### Run All Integration Tests
```bash
# Requires database and services running
pytest tests/integration/ -v
```

### Run Specific Test Categories
```bash
# Unit tests by category
pytest tests/unit/course_management/ -v
pytest tests/unit/analytics/ -v

# Integration tests by category
pytest tests/integration/dao/ -v
pytest tests/integration/course_management/ -v
pytest tests/integration/organization_management/ -v
```

### Run Tests by Marker
```bash
# Unit tests only
pytest -m unit -v

# Integration tests only
pytest -m integration -v
```

## Test Organization

### Unit Test Structure
```
tests/unit/
├── course_management/      # Course domain logic
├── analytics/              # Analytics domain logic
├── organization_management/# Organization domain logic
├── user_management/        # User domain logic
└── [service]/             # Service-specific unit tests
```

### Integration Test Structure
```
tests/integration/
├── dao/                    # Database access tests
├── course_management/      # Course service integration
├── organization_management/# Organization service integration
├── backend/               # Backend API integration
├── services/              # Service-to-service integration
└── [service]/            # Service-specific integration tests
```

## Writing New Tests

### Unit Test Template
```python
"""
Unit Test for [Component Name]

BUSINESS REQUIREMENT:
Describe what business need this component fulfills

TECHNICAL IMPLEMENTATION:
Describe the technical approach
"""

import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestComponentName:
    """
    Test Suite: [Component] Functionality
    
    Tests the core logic without external dependencies
    """
    
    def test_specific_behavior(self):
        """
        TEST: Describe what is being tested
        
        VALIDATES:
        - Expected behavior 1
        - Expected behavior 2
        """
        # Arrange
        component = ComponentName()
        
        # Act
        result = component.method()
        
        # Assert
        assert result == expected
```

### Integration Test Template
```python
"""
Integration Test for [Component Name]

BUSINESS REQUIREMENT:
Describe what business need this component fulfills

TECHNICAL IMPLEMENTATION:
Tests with real database and service dependencies
"""

import pytest

@pytest.mark.integration
class TestComponentIntegration:
    """
    Test Suite: [Component] Integration
    
    Tests the component with real dependencies
    """
    
    def test_database_operation(self, db_session):
        """
        TEST: Describe what is being tested
        
        VALIDATES:
        - Database interaction works correctly
        - Data persists properly
        """
        # Arrange
        dao = ComponentDAO(db_session)
        
        # Act
        result = dao.create_entity(data)
        
        # Assert
        assert result.id is not None
        stored = dao.get_by_id(result.id)
        assert stored == result
```

## Migration Notes (Dec 2025)

36 database-dependent tests were migrated from `tests/unit/` to `tests/integration/`:
- All skip markers removed
- Tests now run with real dependencies
- See `DATABASE_TESTS_MIGRATION_SUMMARY.md` for details

## Troubleshooting

### "Database not found" errors
```bash
# Ensure PostgreSQL is running
docker-compose up -d postgres

# Run database migrations
alembic upgrade head
```

### "Service connection refused" errors
```bash
# Ensure all services are running
docker-compose up -d

# Check service health
docker-compose ps
```

### Slow integration tests
```bash
# Run integration tests in parallel
pytest tests/integration/ -v -n auto

# Run specific subset
pytest tests/integration/dao/ -v
```

## Best Practices

1. **Keep unit tests fast**: No database, no file I/O, no network calls
2. **Use fixtures for integration tests**: Share database setup across tests
3. **Clean up after integration tests**: Use teardown fixtures
4. **Mark tests appropriately**: Use `@pytest.mark.unit` and `@pytest.mark.integration`
5. **Document test intent**: Explain the "why" not just the "what"
6. **Test edge cases**: Include error conditions and boundary cases

## CI/CD Integration

Integration tests may run separately in CI/CD:
- Unit tests: Run on every commit (fast feedback)
- Integration tests: Run on merge to main (comprehensive validation)

Check `.github/workflows/` for specific CI/CD configuration.
