# Comprehensive Testing Guide

## Overview

This guide explains the improved testing strategy implemented after the analysis in `TEST_FAILURE_ANALYSIS.md`. All tests now follow a layered validation approach to catch errors early.

---

## Test Hierarchy

Tests run in this order (enforced by pytest markers):

1. **Syntax Validation** (order=1) - Validates all Python files compile
2. **Import Validation** (order=2) - Validates modules can be imported
3. **Service Health** (order=3) - Validates services are running
4. **Import Tests** (order=4) - Module-specific import validation
5. **Unit Tests** (order=5) - Isolated component tests
6. **Integration Tests** (order=6) - Service interaction tests
7. **E2E UI Tests** (order=7) - UI tests with mocked backend
8. **E2E Full Tests** (order=8) - Full stack E2E tests

---

## Running Tests

### Quick Start

```bash
# Run pre-test validation (ALWAYS do this first)
./tests/validate_before_tests.sh

# Run all tests
pytest

# Run specific test levels
pytest tests/smoke/           # Syntax, import, health checks
pytest tests/unit/            # Unit tests
pytest tests/integration/     # Integration tests (requires services)
pytest tests/e2e/             # E2E tests
```

### Test Markers

```bash
# Run only smoke tests
pytest -m "smoke"

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests (requires --run-integration flag)
pytest tests/integration/ --run-integration

# Run UI tests with mocked backend
pytest -m "e2e_ui"

# Run full E2E tests with real backend
pytest -m "e2e_full" --run-e2e-full
```

### Environment-Specific Testing

```bash
# Development (services running locally)
pytest --run-integration

# CI/CD (no services)
pytest tests/smoke/ tests/unit/

# Full validation (everything)
./tests/validate_before_tests.sh && pytest --run-integration --run-e2e-full
```

---

## Test Types Explained

### 1. Smoke Tests (`tests/smoke/`)

**Purpose**: Foundational validation before any other tests

**Files**:
- `test_syntax_validation.py` - Validates all Python files compile
- `test_import_validation.py` - Validates critical modules import
- `test_service_health.py` - Validates services are running

**When to run**: ALWAYS, before any other tests

**Requirements**: None (only Python and optionally Docker)

**Example**:
```bash
pytest tests/smoke/ -v
```

### 2. Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation

**Structure**:
```
tests/unit/
├── service_name/
│   ├── test_module_imports.py      # Import validation first
│   ├── test_module_functionality.py # Then functionality
```

**Requirements**:
- Inherit from `BaseUnitTest`
- Mock all external dependencies
- Validate imports in test class
- Fast execution (<100ms per test)

**Example**:
```python
from tests.base_test import BaseUnitTest

class TestMyService(BaseUnitTest):
    @classmethod
    def _validate_imports(cls):
        from services.my_service import MyClass

    def test_something(self):
        from services.my_service import MyClass
        # Test here
```

### 3. Integration Tests (`tests/integration/`)

**Purpose**: Test interaction between components

**Structure**:
```
tests/integration/
├── test_service_integration.py     # Service-to-service
├── test_database_integration.py    # Service-to-database
```

**Requirements**:
- Inherit from `BaseIntegrationTest`
- Services must be running
- Use `--run-integration` flag
- Verify service health before tests

**Example**:
```python
from tests.base_test import BaseIntegrationTest

class TestMyIntegration(BaseIntegrationTest):
    service_url = "https://localhost:8000"
    requires_docker = True

    def test_integration(self):
        response = self.make_request("GET", "/api/endpoint")
        assert response.status_code == 200
```

### 4. E2E Tests (`tests/e2e/`)

**Purpose**: Test complete user workflows

**Two Types**:

#### 4a. UI Tests with Mocked Backend (Fast)
- Use `@pytest.mark.e2e_ui`
- Mock API responses with CDP injection
- Test UI functionality in isolation
- Don't require backend services

**Example**:
```python
@pytest.mark.e2e_ui
def test_ui_functionality(self):
    # CDP injection with mocks
    # Test UI interactions
```

#### 4b. Full E2E Tests (Comprehensive)
- Use `@pytest.mark.e2e_full`
- Require all services running
- Test complete data flow
- Use `--run-e2e-full` flag

**Example**:
```python
@pytest.mark.e2e_full
def test_complete_workflow(self):
    # Real login
    # Real backend calls
    # Verify real data
```

---

## Test Base Classes

All tests should inherit from appropriate base classes:

### BaseTest
- Parent of all test classes
- Adds project root to Python path
- Provides common utilities

### BaseUnitTest
- For unit tests
- Validates imports before running
- Provides mock utilities

### BaseIntegrationTest
- For integration tests
- Verifies services are running
- Provides HTTP request utilities

### BaseE2ETest
- For E2E tests
- Manages browser sessions
- Provides Selenium utilities

---

## Writing New Tests

### 1. Unit Test Template

```python
"""
Module Description

BUSINESS CONTEXT:
Why this module exists

TECHNICAL IMPLEMENTATION:
How it works

TEST COVERAGE:
What we're testing
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base_test import BaseUnitTest


class TestModuleImports(BaseUnitTest):
    """Import validation - runs first"""

    @pytest.mark.order(4)
    def test_module_imports(self):
        try:
            from services.my_service import MyClass
            assert MyClass is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestModuleFunctionality(BaseUnitTest):
    """Functionality tests - run after imports"""

    @classmethod
    def _validate_imports(cls):
        from services.my_service import MyClass

    @pytest.mark.order(5)
    def test_something(self):
        from services.my_service import MyClass
        # Your test here
```

### 2. Integration Test Template

```python
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base_test import BaseIntegrationTest


class TestMyIntegration(BaseIntegrationTest):
    service_url = "https://localhost:8000"
    requires_docker = True

    @pytest.mark.order(6)
    @pytest.mark.integration
    def test_endpoint_integration(self):
        response = self.make_request(
            method="GET",
            endpoint="/api/v1/resource",
            headers={'Authorization': f'Bearer {self.get_auth_token()}'},
            expected_status=200
        )

        data = response.json()
        # Validate response
```

### 3. E2E Test Template

```python
import pytest
from tests.e2e.selenium_base import BaseTest


class TestMyE2E(BaseTest):
    @pytest.mark.order(7)
    @pytest.mark.e2e_ui
    def test_ui_with_mocks(self):
        # CDP injection
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'window.MOCK_DATA = {...};'
        })

        # Test UI
        self.driver.get(f"{self.base_url}/page.html")
        # Assertions
```

---

## pytest.ini Configuration

Add to `pytest.ini`:

```ini
[pytest]
markers =
    smoke: Foundational validation tests
    integration: Tests requiring running services
    e2e_ui: E2E UI tests with mocked backend
    e2e_full: Full E2E tests with real backend
    slow: Tests that take >5 seconds

addopts =
    -v
    --tb=short
    --strict-markers
    --order-dependencies

testpaths = tests

python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Syntax Validation
        run: |
          find . -name "*.py" ! -path "./.venv/*" -exec python -m py_compile {} \;

      - name: Run Smoke Tests
        run: |
          pytest tests/smoke/ -v

  unit-tests:
    needs: validation
    runs-on: ubuntu-latest
    steps:
      - name: Run Unit Tests
        run: |
          pytest tests/unit/ -v

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
      redis:
        image: redis:7
    steps:
      - name: Start Services
        run: docker-compose up -d

      - name: Run Integration Tests
        run: |
          pytest tests/integration/ --run-integration -v
```

---

## Troubleshooting

### Tests Won't Run

1. **Run validation first**:
   ```bash
   ./tests/validate_before_tests.sh
   ```

2. **Check for syntax errors**:
   ```bash
   find . -name "*.py" -exec python -m py_compile {} \;
   ```

3. **Check imports**:
   ```bash
   pytest tests/smoke/test_import_validation.py -v
   ```

### Integration Tests Failing

1. **Verify services are running**:
   ```bash
   docker-compose ps
   ```

2. **Check service health**:
   ```bash
   pytest tests/smoke/test_service_health.py -v
   ```

3. **View service logs**:
   ```bash
   docker-compose logs [service-name]
   ```

### E2E Tests Failing

1. **Check ChromeDriver version**:
   ```bash
   chromium --version
   chromedriver --version
   ```

2. **Run with visible browser** (remove headless):
   ```python
   # In selenium_base.py, comment out:
   # options.add_argument('--headless')
   ```

3. **Check for JavaScript errors** (browser console)

---

## Best Practices

### DO ✅

1. **Always run validation before tests**
   ```bash
   ./tests/validate_before_tests.sh && pytest
   ```

2. **Use appropriate base classes**
   - Unit tests → `BaseUnitTest`
   - Integration → `BaseIntegrationTest`
   - E2E → `BaseE2ETest`

3. **Validate imports in unit tests**
   ```python
   @classmethod
   def _validate_imports(cls):
       from module import Class
   ```

4. **Mark tests appropriately**
   ```python
   @pytest.mark.integration
   @pytest.mark.slow
   ```

5. **Document test business context**
   ```python
   """
   BUSINESS CONTEXT:
   Why this test exists
   """
   ```

### DON'T ❌

1. **Don't skip validation**
   - Always run smoke tests first

2. **Don't mix test types**
   - Unit tests shouldn't call real APIs
   - E2E tests shouldn't mock everything

3. **Don't assume services are running**
   - Always verify in integration tests

4. **Don't ignore import errors**
   - Fix them before running other tests

5. **Don't write tests without business context**
   - Always explain WHY, not just WHAT

---

## Summary

**Test Order**:
1. Syntax → 2. Imports → 3. Health → 4. Unit → 5. Integration → 6. E2E

**Key Commands**:
```bash
./tests/validate_before_tests.sh  # Always first
pytest tests/smoke/                # Validation
pytest tests/unit/                 # Isolated tests
pytest tests/integration/ --run-integration  # Service tests
pytest -m e2e_ui                   # UI tests (mocked)
pytest -m e2e_full --run-e2e-full  # Full E2E
```

**Remember**:
- Tests that don't execute the code can't catch errors in it
- Validate syntax and imports before testing functionality
- Separate UI tests from full E2E tests
- Always document business context

---

## Next Steps

1. Read `TEST_FAILURE_ANALYSIS.md` for detailed analysis
2. Review `tests/base_test.py` for base class usage
3. Check existing refactored tests as examples:
   - `tests/unit/organization_management/test_audit_endpoints_refactored.py`
   - `tests/integration/test_audit_log_integration_refactored.py`
   - `tests/e2e/test_site_admin_audit_log_refactored.py`
4. Run `./tests/validate_before_tests.sh` before any test session
