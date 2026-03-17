# Regression Test Suite

## Purpose

This regression test suite documents and prevents known bugs from recurring in the Course Creator Platform. Each test corresponds to a specific historical bug fix with complete documentation of the issue, root cause, fix, and prevention strategy.

## Structure

```
tests/regression/
├── README.md                          # This file
├── BUG_CATALOG.md                     # Complete catalog of all tested bugs
├── GUIDELINES.md                      # How to add new regression tests
├── python/                            # Python backend regression tests
│   ├── __init__.py
│   ├── test_auth_bugs.py              # Authentication bug fixes
│   ├── test_api_routing_bugs.py       # API routing and nginx config bugs
│   ├── test_exception_handling_bugs.py # Exception handling improvements
│   ├── test_race_condition_bugs.py    # Race condition fixes
│   ├── test_enrollment_bugs.py        # Enrollment system bugs
│   ├── test_course_generation_bugs.py # Course generation bugs
│   ├── test_analytics_bugs.py         # Analytics service bugs
│   └── test_rbac_bugs.py              # RBAC permission bugs
└── react/                             # React frontend regression tests
    ├── test_navigation_bugs.test.tsx  # Navigation and routing bugs
    ├── test_form_bugs.test.tsx        # Form validation and state bugs
    ├── test_authentication_bugs.test.tsx # Frontend auth bugs
    ├── test_ui_rendering_bugs.test.tsx # UI rendering issues
    └── test_state_management_bugs.test.tsx # State management bugs
```

## Test Categories

### Python Backend Bugs (8 categories)

1. **Authentication Bugs** - Login redirects, token management, session handling
2. **API Routing Bugs** - nginx configuration, endpoint path mismatches
3. **Exception Handling Bugs** - Generic exception replacement with custom exceptions
4. **Race Condition Bugs** - TOCTOU issues, async/await missing, fire-and-forget tasks
5. **Enrollment Bugs** - Duplicate enrollments, validation errors
6. **Course Generation Bugs** - AI timeouts, content validation
7. **Analytics Bugs** - Data aggregation, PDF generation
8. **RBAC Bugs** - Permission bypasses, role escalation

### React Frontend Bugs (5 categories)

1. **Navigation Bugs** - Login redirect paths, dashboard routing
2. **Form Bugs** - Password visibility, validation, state
3. **Authentication Bugs** - Token storage, logout sync, session management
4. **UI Rendering Bugs** - DOMPurify integrity, z-index stacking, element visibility
5. **State Management Bugs** - localStorage sync, Redux state

## Running Regression Tests

### Run All Regression Tests
```bash
# Python backend regression tests
pytest tests/regression/python/ -v

# React frontend regression tests (when implemented)
npm test tests/regression/react/
```

### Run Specific Bug Category
```bash
# Test authentication bugs only
pytest tests/regression/python/test_auth_bugs.py -v

# Test a specific bug fix
pytest tests/regression/python/test_auth_bugs.py::TestAuthenticationBugs::test_bug_001_login_redirect_org_admin -v
```

### CI/CD Integration
Regression tests run automatically on:
- Every commit (pre-commit hook)
- Every pull request (GitHub Actions)
- Nightly builds (full regression suite)

## Test Documentation Format

Every regression test MUST include:

1. **Bug ID** - Unique identifier (BUG-001, BUG-002, etc.)
2. **Bug Title** - Clear, descriptive title
3. **Original Issue** - What went wrong from user perspective
4. **Symptoms** - Observable behavior, error messages
5. **Root Cause** - Technical explanation of why it happened
6. **Fix Implementation** - How it was fixed, with file/line references
7. **Git Commit** - SHA of the commit that fixed the bug
8. **Regression Prevention** - Explanation of test strategy

## Bug Tracking

All bugs are tracked in `BUG_CATALOG.md` with:
- Bug ID and severity (Critical, High, Medium, Low)
- Date discovered and fixed
- Version introduced and fixed
- Services affected
- Test coverage status
- Related bugs (if any)

## Guidelines for New Tests

See `GUIDELINES.md` for detailed instructions on:
- How to identify bugs worth testing
- How to write regression tests
- How to document bug fixes
- How to integrate with CI/CD

## Metrics

Track regression test coverage:
- Total bugs documented: TBD
- Total regression tests: TBD
- Coverage by service: TBD
- Critical bugs covered: TBD

## Related Documentation

- `/tests/COMPREHENSIVE_E2E_TEST_PLAN.md` - E2E testing strategy
- `/tests/README.md` - Overall testing documentation
- `/claude.md/08-testing-strategy.md` - Testing standards
- Git commit history - Source of bug fixes
