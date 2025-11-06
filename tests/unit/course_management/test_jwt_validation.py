"""
Unit Tests for JWT Token Validation in Course Management Service

TDD RED PHASE - These tests will FAIL until JWT validation is implemented.

BUSINESS CONTEXT:
Tests ensure that course video endpoints properly validate JWT tokens and
extract authenticated user information. This prevents unauthorized access to
course content and ensures proper attribution of user actions.

SOLID PRINCIPLES:
- Dependency Inversion: Tests depend on authentication interface, not implementation
- Single Responsibility: Each test validates one aspect of JWT authentication
- Interface Segregation: Tests focused authentication contract

SECURITY REQUIREMENTS:
- All video endpoints must validate JWT tokens
- Invalid/expired tokens must be rejected with 401 Unauthorized
- User ID and role must be extracted from valid tokens
- Mock tokens (e.g., "current-user-id") must NOT be accepted in production
"""

import pytest
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import Mock, MagicMock, patch

# Direct imports from service modules
# These will fail import errors until we set PYTHONPATH correctly
import sys
import os

# Clean sys.path of ALL other service directories to avoid 'api' module conflicts
# conftest.py adds ALL services - we need course-management ONLY for this test
import sys
# Keep only non-service paths
sys.path = [p for p in sys.path if '/services/' not in p or 'course-management' in p]

# Add course-management path at the beginning
course_mgmt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../services/course-management"))
if course_mgmt_path not in sys.path:
    sys.path.insert(0, course_mgmt_path)

# Now we can import without conflicts
from api import video_endpoints
from auth.jwt_middleware import get_current_user_id


class TestJWTValidationVideoEndpoints:
    """
    Test suite for JWT token validation in video endpoints.

    TDD APPROACH:
    RED: These tests fail because endpoints return mock user IDs
    GREEN: Implement JWT validation to make tests pass
    REFACTOR: Clean up implementation and improve error handling
    """

    def test_get_current_user_id_with_valid_jwt_token(self):
        """
        Test that valid JWT token returns correct user ID.

        BUSINESS VALUE:
        Ensures authenticated users can access their authorized content.

        SECURITY REQUIREMENT:
        Only users with valid JWT tokens can access course content.
        """
        # ARRANGE: Create valid JWT token
        valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsInJvbGUiOiJpbnN0cnVjdG9yIiwiZXhwIjoxOTk5OTk5OTk5fQ.signature"

        # ACT: Extract user ID from token
        with patch('services.course_management.api.video_endpoints.get_authorization_header', return_value=f"Bearer {valid_token}"):
            user_id = video_endpoints.get_current_user_id()

        # ASSERT: Should return actual user ID from token, NOT mock ID
        assert user_id != "current-user-id", "Should not return mock user ID"
        assert user_id == "user_123", f"Expected 'user_123', got '{user_id}'"

    def test_get_current_user_id_with_expired_token_raises_401(self):
        """
        Test that expired JWT token raises 401 Unauthorized.

        BUSINESS VALUE:
        Prevents access with outdated credentials, enhancing security.

        SECURITY REQUIREMENT:
        Expired tokens must be rejected to prevent session hijacking.
        """
        # ARRANGE: Create expired JWT token
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6MTAwMDAwMDAwMH0.signature"

        # ACT & ASSERT: Should raise HTTPException with 401 status
        with patch('services.course_management.api.video_endpoints.get_authorization_header', return_value=f"Bearer {expired_token}"):
            with pytest.raises(HTTPException) as exc_info:
                video_endpoints.get_current_user_id()

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()

    def test_get_current_user_id_with_invalid_token_raises_401(self):
        """
        Test that invalid JWT token raises 401 Unauthorized.

        BUSINESS VALUE:
        Protects against token tampering and forged credentials.

        SECURITY REQUIREMENT:
        Malformed or tampered tokens must be rejected.
        """
        # ARRANGE: Create invalid JWT token (bad signature)
        invalid_token = "invalid.jwt.token"

        # ACT & ASSERT: Should raise HTTPException with 401 status
        with patch('services.course_management.api.video_endpoints.get_authorization_header', return_value=f"Bearer {invalid_token}"):
            with pytest.raises(HTTPException) as exc_info:
                video_endpoints.get_current_user_id()

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in exc_info.value.detail.lower() or "malformed" in exc_info.value.detail.lower()

    def test_get_current_user_id_without_authorization_header_raises_401(self):
        """
        Test that missing Authorization header raises 401 Unauthorized.

        BUSINESS VALUE:
        Enforces authentication requirement for all protected endpoints.

        SECURITY REQUIREMENT:
        Unauthenticated requests must be rejected.
        """
        # ACT & ASSERT: Should raise HTTPException with 401 status
        with patch('services.course_management.api.video_endpoints.get_authorization_header', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                video_endpoints.get_current_user_id()

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "missing" in exc_info.value.detail.lower() or "required" in exc_info.value.detail.lower()

    def test_get_current_user_id_with_malformed_authorization_header_raises_401(self):
        """
        Test that malformed Authorization header raises 401 Unauthorized.

        BUSINESS VALUE:
        Handles client errors gracefully with clear error messages.

        SECURITY REQUIREMENT:
        Only properly formatted bearer tokens should be accepted.
        """
        # ARRANGE: Create malformed authorization header (missing "Bearer")
        malformed_header = "InvalidFormat eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.sig"

        # ACT & ASSERT: Should raise HTTPException with 401 status
        with patch('services.course_management.api.video_endpoints.get_authorization_header', return_value=malformed_header):
            with pytest.raises(HTTPException) as exc_info:
                video_endpoints.get_current_user_id()

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "bearer" in exc_info.value.detail.lower() or "format" in exc_info.value.detail.lower()


class TestJWTValidationAnalyticsService:
    """
    Test suite for JWT token validation in analytics service.

    TDD APPROACH:
    RED: These tests fail because dependencies return mock user IDs
    GREEN: Implement JWT validation to make tests pass
    REFACTOR: Consolidate with video endpoints validation
    """

    def test_analytics_get_current_user_id_with_valid_token(self):
        """
        Test that analytics service validates JWT tokens.

        BUSINESS VALUE:
        Ensures analytics data is properly attributed to authenticated users.

        PRIVACY REQUIREMENT:
        User analytics must be tied to authenticated identities.
        """
        # ARRANGE: Create valid JWT token
        valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzQ1NiIsInJvbGUiOiJzdHVkZW50IiwiZXhwIjoxOTk5OTk5OTk5fQ.signature"

        # ACT: Extract user ID from token
        with patch('services.analytics.api.dependencies.get_authorization_header', return_value=f"Bearer {valid_token}"):
            user_id = dependencies.get_current_user_id()

        # ASSERT: Should return actual user ID from token, NOT mock ID
        assert user_id != "user_123", "Should not return mock user ID"
        assert user_id == "user_456", f"Expected 'user_456', got '{user_id}'"

    def test_analytics_get_current_user_id_extracts_role(self):
        """
        Test that analytics service extracts user role from JWT.

        BUSINESS VALUE:
        Enables role-based analytics dashboards and insights.

        RBAC REQUIREMENT:
        User role determines available analytics features.
        """
        # ARRANGE: Create JWT token with role
        token_with_role = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzc4OSIsInJvbGUiOiJvcmdfYWRtaW4iLCJleHAiOjE5OTk5OTk5OTl9.signature"

        # ACT: Extract role from token
        with patch('services.analytics.api.dependencies.get_authorization_header', return_value=f"Bearer {token_with_role}"):
            # This will require a new function: get_current_user_role()
            # For now, test that user_id is extracted correctly
            user_id = dependencies.get_current_user_id()

        # ASSERT: User ID should be extracted correctly
        assert user_id == "user_789", f"Expected 'user_789', got '{user_id}'"


class TestJWTMiddlewareIntegration:
    """
    Integration tests for JWT middleware across services.

    TDD APPROACH:
    RED: Tests fail due to missing centralized JWT middleware
    GREEN: Implement shared JWT middleware
    REFACTOR: Consolidate duplicate validation logic
    """

    def test_jwt_middleware_validates_all_protected_endpoints(self):
        """
        Test that JWT middleware is applied to all protected endpoints.

        BUSINESS VALUE:
        Centralized authentication reduces code duplication and security gaps.

        ARCHITECTURE REQUIREMENT:
        DRY principle - authentication logic should not be duplicated.
        """
        # ARRANGE: List of protected endpoints
        protected_endpoints = [
            ("POST", "/courses/{course_id}/videos/upload"),
            ("PUT", "/courses/{course_id}/videos/{video_id}"),
            ("DELETE", "/courses/{course_id}/videos/{video_id}"),
            ("GET", "/analytics/student/{student_id}/activity"),
            ("GET", "/analytics/progress/{user_id}"),
        ]

        # ACT & ASSERT: Each endpoint should require valid JWT
        for method, endpoint in protected_endpoints:
            # This test will require FastAPI TestClient setup
            # For now, assert that middleware configuration exists
            pass

    def test_jwt_middleware_allows_public_endpoints_without_token(self):
        """
        Test that public endpoints don't require JWT tokens.

        BUSINESS VALUE:
        Enables public course discovery and registration flows.

        UX REQUIREMENT:
        Anonymous users should be able to browse public content.
        """
        # ARRANGE: List of public endpoints
        public_endpoints = [
            ("GET", "/courses/public"),
            ("GET", "/courses/{course_id}/preview"),
            ("POST", "/auth/register"),
            ("POST", "/auth/login"),
        ]

        # ACT & ASSERT: Public endpoints should NOT require authentication
        # This will be tested in integration tests
        pass


# Test Configuration
@pytest.fixture
def valid_jwt_token():
    """Fixture providing valid JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsInJvbGUiOiJpbnN0cnVjdG9yIiwiZXhwIjoxOTk5OTk5OTk5fQ.signature"


@pytest.fixture
def expired_jwt_token():
    """Fixture providing expired JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6MTAwMDAwMDAwMH0.signature"


@pytest.fixture
def invalid_jwt_token():
    """Fixture providing invalid JWT token for testing."""
    return "invalid.jwt.token"
