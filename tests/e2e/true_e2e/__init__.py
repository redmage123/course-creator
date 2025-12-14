"""
True End-to-End Test Suite

This package contains E2E tests that validate the complete flow:
Browser → React Components → Service Layer → API Client → Backend → Database

CRITICAL DESIGN PRINCIPLE:
These tests NEVER bypass the frontend code. They interact with the application
exactly as a real user would, ensuring bugs in the React service layer are caught.

Anti-patterns that are FORBIDDEN in this suite:
1. Direct API calls via execute_script("fetch(...)") - bypasses React services
2. Token injection via localStorage.setItem('authToken', ...) - bypasses login flow
3. Mock API responses via window.fetch = ... - bypasses real backend
4. Direct database manipulation for test assertions (use for seeding only)

Structure:
- base/: Base test classes with anti-pattern detection
- data/: Test data seeding and database verification
- pages/: Page Object Model classes for UI interaction
- journeys/: Complete user journey tests (one per role)
- regression/: Tests for specific bugs that should never recur
- utils/: Helper utilities
"""
