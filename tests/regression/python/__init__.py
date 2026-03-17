"""
Regression Test Suite - Python Backend

BUSINESS CONTEXT:
Prevents known bugs in Python backend services from recurring.
Documents historical issues and their fixes with comprehensive tests.

PURPOSE:
- Ensure fixed bugs don't reappear in future releases
- Provide documentation of historical issues
- Enable confident refactoring with safety net
- Reduce time spent debugging known issues

TEST CATEGORIES:
1. Authentication bugs (login, tokens, sessions)
2. API routing bugs (nginx, endpoints)
3. Exception handling bugs (error types)
4. Race condition bugs (async, TOCTOU)
5. Enrollment bugs (validation, duplicates)
6. Course generation bugs (AI, validation)
7. Analytics bugs (aggregation, PDFs)
8. RBAC bugs (permissions, roles)

Each test documents:
- Bug ID and title
- Original symptoms
- Root cause analysis
- Fix implementation details
- Git commit reference
- Prevention strategy

See BUG_CATALOG.md for complete bug documentation.
"""

__version__ = "1.0.0"
__all__ = [
    "test_auth_bugs",
    "test_api_routing_bugs",
    "test_exception_handling_bugs",
    "test_race_condition_bugs",
]
