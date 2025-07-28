# Quiz Management Tests

This directory contains comprehensive tests for the quiz management system.

## Test Files

### API Testing
- `test_quiz_api_functionality.py` - Tests API endpoints for quiz management
- `test_comprehensive_quiz_management.py` - Complete database workflow testing
- `test_quiz_management_simple.py` - Simplified database schema testing

### Frontend Testing
- `test_frontend_quiz_management.py` - JavaScript functionality validation
- `test_quiz_management_frontend.html` - Interactive browser-based testing

## Running Tests

```bash
# Run all quiz management tests
python -m pytest tests/quiz-management/

# Run specific test files
python tests/quiz-management/test_quiz_api_functionality.py
python tests/quiz-management/test_frontend_quiz_management.py

# Run frontend tests in browser
open tests/quiz-management/test_quiz_management_frontend.html
```

## Test Coverage

- ✅ API endpoint validation
- ✅ Database schema validation  
- ✅ JavaScript function testing
- ✅ UI component generation
- ✅ Interactive element testing
- ✅ Mock data processing
- ✅ Complete workflow testing