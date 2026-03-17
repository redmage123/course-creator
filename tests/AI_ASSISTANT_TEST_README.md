# AI Assistant Test Suite

Comprehensive testing framework for the AI Assistant feature in Course Creator Platform.

## Overview

The AI Assistant allows administrators and instructors to manage their organizations using natural language instead of traditional forms. This test suite ensures the AI assistant works correctly across all layers:

- **Unit Tests**: Individual function testing
- **Integration Tests**: Component interaction testing
- **E2E Tests**: Complete user workflow testing
- **Lint Tests**: Code quality and syntax validation

## Test Structure

```
tests/
├── unit/
│   ├── frontend/
│   │   └── test_ai_assistant.test.js          # JavaScript unit tests (Jest)
│   └── scripts/
│       └── test_generate_slide5.py            # Python unit tests (pytest)
├── integration/
│   └── test_ai_assistant_integration.py       # Integration tests (pytest + Selenium)
└── e2e/
    └── test_ai_assistant_e2e.py               # E2E tests (pytest + Selenium)
```

## Quick Start

### Run All Tests

```bash
npm run test:ai-assistant
```

### Run Specific Test Types

```bash
# Unit tests only
npm run test:ai-assistant:unit

# Integration tests only
npm run test:ai-assistant:integration

# E2E tests only
npm run test:ai-assistant:e2e

# Lint checks only
npm run test:ai-assistant:lint
```

### Run Tests Manually

```bash
# All tests
./run_ai_assistant_tests.sh --all

# With verbose output
./run_ai_assistant_tests.sh --all --verbose

# Specific test types
./run_ai_assistant_tests.sh --unit
./run_ai_assistant_tests.sh --integration
./run_ai_assistant_tests.sh --e2e
./run_ai_assistant_tests.sh --lint
```

## Test Categories

### 1. Unit Tests (Jest + pytest)

**Location**: `tests/unit/frontend/test_ai_assistant.test.js`, `tests/unit/scripts/test_generate_slide5.py`

**Purpose**: Test individual functions and methods in isolation

**Coverage**:
- AIAssistant class initialization
- Message handling (add, send, clear)
- Intent recognition algorithms
- Conversation history management
- XSS prevention (HTML escaping)
- Panel open/close operations
- Event listener attachment
- Error handling
- Edge cases (empty messages, long messages, special characters)

**Run**:
```bash
npm run test:ai-assistant:unit
```

**Technologies**: Jest (JavaScript), pytest (Python)

### 2. Integration Tests (pytest + Selenium)

**Location**: `tests/integration/test_ai_assistant_integration.py`

**Purpose**: Test how AI assistant components work together in a real browser

**Coverage**:
- AI button visibility and clickability
- Panel open/close animations
- Message sending via button and Enter key
- Intent recognition in browser context
- Multiple message conversations
- Empty message prevention
- Input focus behavior

**Run**:
```bash
npm run test:ai-assistant:integration
```

**Technologies**: pytest, Selenium WebDriver (headless Chrome)

### 3. E2E Tests (pytest + Selenium)

**Location**: `tests/e2e/test_ai_assistant_e2e.py`

**Purpose**: Test complete user workflows from discovery to task completion

**Coverage**:

**User Journey Tests**:
- Admin discovers AI assistant button
- Admin opens AI assistant for first time
- Admin creates project via AI
- Admin creates track with full details
- Admin onboards instructor
- Admin completes multiple tasks in sequence
- Admin closes and reopens panel
- Keyboard navigation (Enter key)
- AI assistant accessible from all dashboard tabs

**Performance Tests**:
- Rapid message handling
- Long message handling

**Run**:
```bash
npm run test:ai-assistant:e2e
```

**Technologies**: pytest, Selenium WebDriver (configurable headless/headed)

### 4. Lint Tests (ESLint + flake8)

**Purpose**: Ensure code quality and consistency

**Coverage**:
- JavaScript style (ESLint)
- Python style (flake8)
- Syntax validation
- Best practices enforcement

**Run**:
```bash
npm run test:ai-assistant:lint
```

**Technologies**: ESLint, flake8, node -c, py_compile

## Test Configuration

### JavaScript Tests (Jest)

Configuration: `package.json` (jest section) and `.eslintrc.json`

Key settings:
- Test environment: jsdom (simulated browser)
- Coverage threshold: 80%
- Test match: `**/*.test.js`
- Transform: babel-jest

### Python Tests (pytest)

Configuration: `pytest.ini` or inline in tests

Key settings:
- Markers: unit, integration, e2e
- Selenium WebDriver: Chrome headless
- Fixtures: browser, mock_driver

### Linting

Configuration: `.eslintrc.json`, `.flake8` (if exists)

Key rules:
- Indent: 4 spaces
- Quotes: single (JavaScript)
- Semi: required (JavaScript)
- Max line length: 120 characters

## Test Data

### Mock Data

Unit tests use mocked DOM elements and WebDriver instances:

```javascript
// Mock DOM element
class MockElement {
    constructor(id) {
        this.id = id;
        this.classList = new Set();
        this.value = '';
        this.eventListeners = {};
    }
}
```

### Test Messages

Integration and E2E tests use realistic messages:

```javascript
"create a new project"
"Create an intermediate track called Machine Learning Basics for the Data Science project"
"add a new instructor to my organization"
```

## Test Results

### Success Criteria

- **Unit tests**: 90%+ coverage
- **Integration tests**: All 15+ scenarios pass
- **E2E tests**: All 12+ user journeys pass
- **Lint tests**: Zero errors, warnings acceptable

### Failure Handling

If tests fail:

1. Check the test output for specific failure
2. Review the relevant code section
3. Run specific test with `--verbose` flag
4. Use `--headed` for E2E tests to see browser
5. Check browser console logs

### CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run AI Assistant Tests
  run: npm run test:ai-assistant
```

## Development Workflow

### Adding New Tests

1. **Unit Test**: Add to `test_ai_assistant.test.js` or `test_generate_slide5.py`
2. **Integration Test**: Add to `test_ai_assistant_integration.py`
3. **E2E Test**: Add to `test_ai_assistant_e2e.py`
4. Run tests to verify: `npm run test:ai-assistant`

### Writing Tests

**JavaScript Unit Test Example**:
```javascript
test('should recognize create project intent', () => {
    const response = assistant.getAIResponse('create a new project');
    expect(response).toContain('project');
    expect(response.toLowerCase()).toContain('name');
});
```

**Python E2E Test Example**:
```python
def test_01_admin_discovers_ai_assistant(self, browser):
    """Test: Admin user logs in and discovers AI assistant button"""
    browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
    wait = WebDriverWait(browser, 10)

    ai_button = wait.until(
        EC.visibility_of_element_located((By.ID, "aiAssistantBtn"))
    )

    assert ai_button.is_displayed()
```

### Test Naming Convention

- **Unit tests**: `test_<function_name>_<scenario>`
- **Integration tests**: `test_<feature>_<interaction>`
- **E2E tests**: `test_<step_number>_<user_action>`

## Debugging Tests

### Enable Verbose Output

```bash
./run_ai_assistant_tests.sh --all --verbose
```

### Run in Headed Mode (E2E)

```bash
HEADLESS=false pytest tests/e2e/test_ai_assistant_e2e.py -v
```

### Run Single Test

```bash
# JavaScript
npm test -- tests/unit/frontend/test_ai_assistant.test.js -t "should open panel"

# Python
pytest tests/e2e/test_ai_assistant_e2e.py::TestAIAssistantCompleteJourney::test_01_admin_discovers_ai_assistant -v
```

### Check Coverage

```bash
npm run test:coverage
```

## Dependencies

### JavaScript
- jest
- @testing-library/jest-dom
- eslint

### Python
- pytest
- selenium
- webdriver-manager (optional)
- flake8 (optional)

### Install

```bash
# JavaScript
npm install --save-dev jest eslint

# Python
pip install pytest selenium flake8
```

## Environment Variables

- `HEADLESS`: Set to "false" to run E2E tests in headed mode
- `TEST_BASE_URL`: Base URL for tests (default: https://localhost:3000)
- `CI`: Set to "true" for CI/CD environments

## Continuous Integration

### GitHub Actions Example

```yaml
name: AI Assistant Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: npm install
      - run: pip install -r requirements.txt
      - run: npm run test:ai-assistant
```

## Troubleshooting

### Common Issues

**Issue**: "Element not found"
**Solution**: Increase wait timeout or check element selector

**Issue**: "Tests pass locally but fail in CI"
**Solution**: Ensure same browser version, check for race conditions

**Issue**: "Import error in Jest tests"
**Solution**: Check `moduleNameMapper` in jest.config.js

**Issue**: "Selenium WebDriver not found"
**Solution**: Install webdriver-manager or specify chromedriver path

### Getting Help

- Check test output for specific error
- Review test code for assertions
- Check browser console (for E2E tests)
- Verify element IDs match HTML

## Performance

### Test Execution Times (Approximate)

- **Unit tests**: 2-5 seconds
- **Integration tests**: 15-30 seconds
- **E2E tests**: 60-120 seconds
- **Lint tests**: 5-10 seconds
- **Total (all tests)**: 2-3 minutes

### Optimization

- Run unit tests during development (fastest feedback)
- Run integration tests before committing
- Run E2E tests before merging to main
- Run all tests in CI/CD pipeline

## Contributing

When adding new AI assistant features:

1. Write unit tests first (TDD)
2. Add integration tests for interactions
3. Add E2E tests for user workflows
4. Ensure lint checks pass
5. Run full test suite before submitting PR

## License

Part of Course Creator Platform - MIT License

## Contact

For issues or questions about AI assistant tests:
- Open an issue in the repository
- Contact the development team
