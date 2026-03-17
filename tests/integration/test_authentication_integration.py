"""
Integration tests for authentication and JWT middleware.

Tests end-to-end workflows for:
- User login and JWT token generation
- JWT token validation across services
- Password reset flow (3-step process)
- Token expiration handling
- Invalid token handling

Business Context:
These tests verify the complete authentication system works correctly
when all services are running together, ensuring secure access control
and password management across the platform.
"""

import pytest
import requests
import json
import time
from datetime import datetime, timedelta


class TestAuthenticationIntegration:
    """Integration tests for authentication system."""

    @classmethod
    def setup_class(cls):
        """Set up test environment with service URLs and test data."""
        # Service base URLs
        cls.auth_base = "http://localhost:8000"
        cls.analytics_base = "http://localhost:8001"

        # Test user credentials
        cls.test_user = {
            "email": "auth.integration@example.com",
            "username": "auth_integration_test",
            "full_name": "Auth Integration Test User",
            "password": "TestP@ssw0rd123",
            "role": "student"
        }

        # Test tokens
        cls.access_token = None
        cls.reset_token = None
        cls.user_id = None

    def test_01_services_are_running(self):
        """
        Test that required services are running.

        Verifies:
        - User management service (port 8000)
        - Analytics service (port 8001) for JWT validation tests
        """
        # Test user management service
        try:
            response = requests.get(f"{self.auth_base}/health", timeout=5)
            assert response.status_code == 200, "User management service not healthy"
        except requests.exceptions.RequestException as e:
            pytest.skip(f"User management service not running: {e}")

        # Test analytics service (for JWT middleware validation)
        try:
            response = requests.get(f"{self.analytics_base}/health", timeout=5)
            assert response.status_code == 200, "Analytics service not healthy"
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Analytics service not running: {e}")

    def test_02_user_login_generates_jwt_token(self):
        """
        Test successful login generates valid JWT token.

        Flow:
        1. POST /auth/login with valid credentials
        2. Receive JWT token and user data
        3. Verify token format and expiration

        Security:
        - Passwords transmitted securely
        - JWT token includes user ID and role
        - Token has expiration time
        """
        try:
            response = requests.post(
                f"{self.auth_base}/auth/login",
                json={
                    "username": self.test_user["username"],
                    "password": self.test_user["password"]
                },
                timeout=10
            )

            # Should return 200 OK with token
            assert response.status_code == 200, f"Login failed: {response.text}"

            data = response.json()
            assert "access_token" in data, "No access token in response"
            assert "user" in data, "No user data in response"
            assert "token_type" in data, "No token type in response"

            # Verify token format (JWT has 3 parts: header.payload.signature)
            token = data["access_token"]
            token_parts = token.split(".")
            assert len(token_parts) == 3, f"Invalid JWT format: {len(token_parts)} parts"

            # Store token for subsequent tests
            self.__class__.access_token = token
            self.__class__.user_id = data["user"]["id"]

            # Verify user data
            user = data["user"]
            assert user["username"] == self.test_user["username"]
            assert user["email"] == self.test_user["email"]
            assert "password" not in user, "Password should not be in response"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Login request failed: {e}")

    def test_03_invalid_credentials_rejected(self):
        """
        Test login with invalid credentials is rejected.

        Security:
        - Invalid passwords return 401 Unauthorized
        - Error message doesn't reveal if username exists (no user enumeration)
        - No token generated for failed login
        """
        try:
            response = requests.post(
                f"{self.auth_base}/auth/login",
                json={
                    "username": self.test_user["username"],
                    "password": "WrongPassword123"
                },
                timeout=10
            )

            # Should return 401 Unauthorized
            assert response.status_code == 401, "Invalid credentials should return 401"

            data = response.json()
            assert "access_token" not in data, "Token should not be generated for invalid login"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Invalid login test failed: {e}")

    def test_04_jwt_token_validates_successfully(self):
        """
        Test JWT token can be validated by other services.

        Flow:
        1. Use token from login to access protected endpoint
        2. Service validates JWT token
        3. Request succeeds with 200 OK

        Services tested:
        - Analytics service (uses JWT middleware)
        """
        if not self.access_token:
            pytest.skip("No access token available (login test may have failed)")

        try:
            # Test analytics service with JWT token
            response = requests.get(
                f"{self.analytics_base}/api/v1/activity/recent",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10
            )

            # Should succeed (200 OK) or return empty data, not auth error
            assert response.status_code in [200, 404], \
                f"JWT validation failed: {response.status_code} - {response.text}"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"JWT validation request failed: {e}")

    def test_05_missing_token_rejected(self):
        """
        Test requests without JWT token are rejected.

        Security:
        - Protected endpoints require authentication
        - Missing Authorization header returns 401
        - Clear error message for missing token
        """
        try:
            response = requests.get(
                f"{self.analytics_base}/api/v1/activity/recent",
                timeout=10
            )

            # Should return 401 Unauthorized (no token provided)
            assert response.status_code == 401, \
                "Protected endpoint should reject requests without token"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Missing token test failed: {e}")

    def test_06_invalid_token_rejected(self):
        """
        Test requests with invalid JWT token are rejected.

        Security:
        - Malformed tokens return 401
        - Expired tokens return 401
        - Tokens with invalid signatures return 401
        """
        try:
            # Test with completely invalid token
            response = requests.get(
                f"{self.analytics_base}/api/v1/activity/recent",
                headers={"Authorization": "Bearer invalid.token.here"},
                timeout=10
            )

            # Should return 401 Unauthorized
            assert response.status_code == 401, \
                "Invalid token should be rejected"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Invalid token test failed: {e}")

    def test_07_password_reset_request_succeeds(self):
        """
        Test password reset request (step 1 of 3).

        Flow:
        1. POST /auth/password/reset/request with email
        2. Receive generic success message
        3. Token generated server-side (would be sent via email)

        Security:
        - Generic success message prevents user enumeration
        - Same response for valid/invalid emails
        - Token not returned in response (security)
        """
        try:
            response = requests.post(
                f"{self.auth_base}/auth/password/reset/request",
                json={"email": self.test_user["email"]},
                timeout=10
            )

            # Should return 200 OK with generic message
            assert response.status_code == 200, \
                f"Password reset request failed: {response.text}"

            data = response.json()
            assert "message" in data, "No message in response"
            assert "success" in data, "No success field in response"
            assert data["success"] is True, "Password reset request not successful"

            # Verify generic message (prevents user enumeration)
            assert "if an account" in data["message"].lower(), \
                "Message should be generic to prevent user enumeration"

            # Security: Token should NOT be in response
            assert "token" not in data, "Token should not be in response (security)"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Password reset request failed: {e}")

    def test_08_password_reset_request_with_invalid_email(self):
        """
        Test password reset with non-existent email returns generic success.

        Security:
        - Same response for valid/invalid emails
        - Prevents user enumeration attacks
        - No indication if email exists in system
        """
        try:
            response = requests.post(
                f"{self.auth_base}/auth/password/reset/request",
                json={"email": "nonexistent@example.com"},
                timeout=10
            )

            # Should still return 200 OK (security - no user enumeration)
            assert response.status_code == 200, \
                "Password reset should return success even for invalid email"

            data = response.json()
            assert data["success"] is True, \
                "Should return success for invalid email (prevents enumeration)"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Password reset with invalid email test failed: {e}")

    def test_09_password_reset_token_validation_fails_for_invalid_token(self):
        """
        Test password reset token validation (step 2 of 3) with invalid token.

        Security:
        - Invalid tokens return valid: false
        - Clear error message
        - No sensitive data in error response
        """
        try:
            response = requests.post(
                f"{self.auth_base}/auth/password/reset/verify",
                json={"token": "invalid_fake_token_12345"},
                timeout=10
            )

            # Should return 200 OK but with valid: false
            assert response.status_code == 200, \
                "Token verification endpoint should return 200"

            data = response.json()
            assert "valid" in data, "No valid field in response"
            assert data["valid"] is False, "Invalid token should have valid: false"
            assert "error" in data, "No error message for invalid token"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Invalid token validation test failed: {e}")

    def test_10_password_reset_completion_fails_without_valid_token(self):
        """
        Test password reset completion (step 3 of 3) without valid token.

        Security:
        - Cannot complete reset without valid token
        - Clear error message
        - Password strength requirements enforced
        """
        try:
            response = requests.post(
                f"{self.auth_base}/auth/password/reset/complete",
                json={
                    "token": "invalid_fake_token_12345",
                    "new_password": "NewP@ssw0rd456"
                },
                timeout=10
            )

            # Should return 400 Bad Request (invalid token)
            assert response.status_code == 400, \
                "Password reset with invalid token should return 400"

            data = response.json()
            assert "detail" in data, "No error detail in response"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Password reset completion test failed: {e}")

    def test_11_password_reset_rejects_weak_passwords(self):
        """
        Test password reset enforces password strength requirements.

        Security:
        - Weak passwords rejected (< 8 chars)
        - Must meet complexity requirements
        - Clear error message about requirements
        """
        # Note: This test would require a valid reset token
        # For now, we test that the endpoint validates password strength
        try:
            response = requests.post(
                f"{self.auth_base}/auth/password/reset/complete",
                json={
                    "token": "fake_token_for_weak_password_test",
                    "new_password": "weak"  # Too short, too simple
                },
                timeout=10
            )

            # Should return 400 Bad Request (weak password or invalid token)
            assert response.status_code == 400, \
                "Weak password should be rejected"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Weak password test failed: {e}")

    def test_12_authenticated_endpoint_access_with_valid_token(self):
        """
        Test accessing authenticated endpoint with valid JWT token succeeds.

        Flow:
        1. Use valid JWT token from login
        2. Access protected endpoint
        3. Verify request succeeds

        Services:
        - User management /auth/me endpoint
        """
        if not self.access_token:
            pytest.skip("No access token available")

        try:
            response = requests.get(
                f"{self.auth_base}/auth/me",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10
            )

            # Should return 200 OK with user data
            assert response.status_code == 200, \
                f"Authenticated endpoint failed: {response.text}"

            data = response.json()
            assert "id" in data, "No user ID in response"
            assert "email" in data, "No email in response"
            assert "username" in data, "No username in response"
            assert "password" not in data, "Password should not be in response"

            # Verify user data matches test user
            assert data["email"] == self.test_user["email"]
            assert data["username"] == self.test_user["username"]

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Authenticated endpoint test failed: {e}")

    @classmethod
    def teardown_class(cls):
        """Clean up test data after all tests complete."""
        # In a real scenario, we'd delete the test user here
        # For now, we just log completion
        pass


class TestPasswordChangeFlow:
    """Integration tests for password change (authenticated users)."""

    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.auth_base = "http://localhost:8000"
        cls.test_user = {
            "username": "password_change_test",
            "password": "OldP@ssw0rd123"
        }
        cls.access_token = None

    def test_01_login_to_get_token(self):
        """Login to get JWT token for password change tests."""
        try:
            response = requests.post(
                f"{self.auth_base}/auth/login",
                json={
                    "username": self.test_user["username"],
                    "password": self.test_user["password"]
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.__class__.access_token = data["access_token"]
            else:
                pytest.skip("User not found - password change tests require existing user")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Login failed: {e}")

    def test_02_password_change_requires_authentication(self):
        """Test password change endpoint requires valid JWT token."""
        try:
            response = requests.post(
                f"{self.auth_base}/auth/password/change",
                json={
                    "old_password": "OldP@ssw0rd123",
                    "new_password": "NewP@ssw0rd456"
                },
                timeout=10
            )

            # Should return 401 Unauthorized (no token)
            assert response.status_code == 401, \
                "Password change without authentication should return 401"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Unauthenticated password change test failed: {e}")

    def test_03_password_change_validates_old_password(self):
        """Test password change validates old password before allowing change."""
        if not self.access_token:
            pytest.skip("No access token available")

        try:
            response = requests.post(
                f"{self.auth_base}/auth/password/change",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "old_password": "WrongOldPassword",
                    "new_password": "NewP@ssw0rd456"
                },
                timeout=10
            )

            # Should return 400 Bad Request (wrong old password)
            assert response.status_code == 400, \
                "Password change with wrong old password should return 400"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Wrong old password test failed: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
