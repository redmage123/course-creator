"""
Password Reset Token Flow Tests - TDD RED Phase

BUSINESS CONTEXT:
Secure password reset implementation using time-limited tokens instead of
returning passwords directly. Follows industry security best practices for
password reset workflows.

SECURITY REQUIREMENTS:
- Tokens must be cryptographically secure (secrets.token_urlsafe)
- Tokens must expire after configurable time (default: 1 hour)
- Used tokens must be invalidated after successful password reset
- No user enumeration (same response for valid/invalid emails)
- Rate limiting to prevent abuse (future enhancement)

TEST COVERAGE:
1. Password reset request generation
2. Token validation (valid, expired, invalid tokens)
3. Password reset completion with token
4. Error handling and security edge cases

TESTING STRATEGY:
Following TDD methodology:
- RED: Write failing tests first (this file)
- GREEN: Implement minimum code to pass tests
- REFACTOR: Optimize and improve implementation

Author: Course Creator Platform Team
Version: 3.4.0 - Token-Based Password Reset
Last Updated: 2025-10-10
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch
import secrets

# Service under test
from user_management.application.services.authentication_service import AuthenticationService
from user_management.domain.entities.user import User, UserRole, UserStatus

# Test fixtures and helpers
from data_access.user_dao import UserManagementDAO


class TestPasswordResetTokenGeneration:
    """
    Test suite for password reset token generation.

    Business Logic:
    When a user requests password reset via email:
    1. Generate cryptographically secure random token
    2. Store token with user ID and expiration timestamp
    3. Return token for email delivery (in production, send email)
    4. No error if email doesn't exist (prevent user enumeration)
    """

    @pytest.mark.asyncio
    async def test_request_password_reset_generates_secure_token(self):
        """
        Test that password reset request generates cryptographically secure token.

        Security Requirement:
        Tokens must use secrets.token_urlsafe() for cryptographic randomness.
        Minimum token length: 32 characters (192 bits of entropy).

        Expected Behavior:
        - Token is URL-safe base64 string
        - Token length >= 32 characters
        - Token is unique per request
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user_dao.get_user_by_email = AsyncMock(return_value=user)
        user_dao.update = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act
        reset_token = await auth_service.request_password_reset("user@example.com")

        # Assert
        assert reset_token is not None, "Password reset should return token"
        assert isinstance(reset_token, str), "Token must be string"
        assert len(reset_token) >= 32, f"Token too short ({len(reset_token)} chars). Security requirement: >= 32"
        # URL-safe base64 uses only: A-Z, a-z, 0-9, -, _
        assert all(c.isalnum() or c in '-_' for c in reset_token), "Token must be URL-safe"

    @pytest.mark.asyncio
    async def test_request_password_reset_stores_token_with_expiration(self):
        """
        Test that password reset token is stored with expiration timestamp.

        Business Rule:
        Tokens expire after 1 hour to limit attack window.

        Expected Storage:
        user.metadata['password_reset_token'] = token
        user.metadata['password_reset_expires'] = timestamp (1 hour from now)
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user_dao.get_user_by_email = AsyncMock(return_value=user)
        user_dao.update = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act
        before_request = datetime.now(timezone.utc)
        reset_token = await auth_service.request_password_reset("user@example.com")
        after_request = datetime.now(timezone.utc)

        # Assert - verify DAO.update was called with token metadata
        user_dao.update.assert_called_once()
        updated_user = user_dao.update.call_args[0][0]

        assert 'password_reset_token' in updated_user.metadata, "Token must be stored in metadata"
        assert updated_user.metadata['password_reset_token'] == reset_token, "Stored token must match returned token"

        assert 'password_reset_expires' in updated_user.metadata, "Token expiration must be stored"
        expiration = updated_user.metadata['password_reset_expires']

        # Verify expiration is approximately 1 hour from now
        expected_expiration_min = before_request + timedelta(hours=1)
        expected_expiration_max = after_request + timedelta(hours=1)

        assert expected_expiration_min <= expiration <= expected_expiration_max, \
            f"Token should expire in 1 hour. Expected between {expected_expiration_min} and {expected_expiration_max}, got {expiration}"

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_email_succeeds_no_enumeration(self):
        """
        Test that password reset for nonexistent email returns success.

        Security Requirement:
        Prevent user enumeration attacks by not revealing whether email exists.
        Always return success message regardless of email validity.

        Expected Behavior:
        - Returns success message (not token)
        - Does not throw error for invalid email
        - Response time similar to valid email (timing attack prevention)
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        user_dao.get_user_by_email = AsyncMock(return_value=None)  # Email not found

        auth_service = AuthenticationService(user_dao)

        # Act - should not raise exception
        result = await auth_service.request_password_reset("nonexistent@example.com")

        # Assert
        assert result is not None, "Should return success message even for invalid email"
        assert user_dao.update.call_count == 0, "Should not update database for nonexistent email"

    @pytest.mark.asyncio
    async def test_request_password_reset_generates_unique_tokens(self):
        """
        Test that multiple password reset requests generate unique tokens.

        Security Requirement:
        Each reset request must generate a unique token to prevent token reuse attacks.
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user_dao.get_user_by_email = AsyncMock(return_value=user)
        user_dao.update = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act - request reset twice
        token1 = await auth_service.request_password_reset("user@example.com")
        token2 = await auth_service.request_password_reset("user@example.com")

        # Assert
        assert token1 != token2, "Each reset request must generate unique token"


class TestPasswordResetTokenValidation:
    """
    Test suite for password reset token validation.

    Business Logic:
    Before allowing password reset, validate that:
    1. Token exists in system
    2. Token matches user's stored token
    3. Token has not expired
    4. Token has not been used (invalidated)
    """

    @pytest.mark.asyncio
    async def test_validate_reset_token_valid_token_returns_user_id(self):
        """
        Test that valid unexpired token returns associated user ID.

        Expected Behavior:
        - Token exists and matches stored value
        - Token expiration is in future
        - Returns user ID for password reset
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        reset_token = "valid-token-abc123"
        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user.add_metadata('password_reset_token', reset_token)
        user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))

        user_dao.get_user_by_metadata = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act
        user_id = await auth_service.validate_password_reset_token(reset_token)

        # Assert
        assert user_id == "user-123", "Valid token should return user ID"

    @pytest.mark.asyncio
    async def test_validate_reset_token_expired_token_raises_error(self):
        """
        Test that expired token raises appropriate error.

        Security Requirement:
        Expired tokens must be rejected to limit attack window.

        Expected Behavior:
        - Raises ValueError with "expired" message
        - Does not return user ID
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        reset_token = "expired-token-xyz789"
        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user.add_metadata('password_reset_token', reset_token)
        user.add_metadata('password_reset_expires', datetime.now(timezone.utc) - timedelta(minutes=5))  # Expired 5 min ago

        user_dao.get_user_by_metadata = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await auth_service.validate_password_reset_token(reset_token)

        assert "expired" in str(exc_info.value).lower(), "Error message should indicate token expired"

    @pytest.mark.asyncio
    async def test_validate_reset_token_invalid_token_raises_error(self):
        """
        Test that nonexistent token raises appropriate error.

        Security Requirement:
        Invalid tokens must be rejected without revealing whether token existed.

        Expected Behavior:
        - Raises ValueError with generic "invalid" message
        - Does not reveal whether token never existed vs already used
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        user_dao.get_user_by_metadata = AsyncMock(return_value=None)  # Token not found

        auth_service = AuthenticationService(user_dao)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await auth_service.validate_password_reset_token("nonexistent-token-123")

        assert "invalid" in str(exc_info.value).lower(), "Error message should indicate invalid token"


class TestPasswordResetCompletion:
    """
    Test suite for password reset completion with token.

    Business Logic:
    When user submits new password with valid token:
    1. Validate token (existence, expiration)
    2. Validate new password strength
    3. Hash new password securely
    4. Update user password
    5. Invalidate reset token
    6. Clear password reset metadata
    """

    @pytest.mark.asyncio
    async def test_complete_password_reset_valid_token_updates_password(self):
        """
        Test that valid token allows password update.

        Expected Workflow:
        1. Validate token
        2. Hash new password
        3. Update user password
        4. Invalidate token
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        reset_token = "valid-token-abc123"
        new_password = "NewSecureP@ss123"

        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user.add_metadata('password_reset_token', reset_token)
        user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))
        user.add_metadata('hashed_password', 'old-hashed-password')

        user_dao.get_user_by_metadata = AsyncMock(return_value=user)
        user_dao.update = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act
        success = await auth_service.complete_password_reset(reset_token, new_password)

        # Assert
        assert success is True, "Password reset should succeed with valid token"

        # Verify password was updated
        user_dao.update.assert_called_once()
        updated_user = user_dao.update.call_args[0][0]

        # Verify password was hashed (not stored as plaintext)
        new_hashed_password = updated_user.metadata.get('hashed_password')
        assert new_hashed_password != new_password, "Password must be hashed, not plaintext"
        assert new_hashed_password != 'old-hashed-password', "Password must be updated"

        # Verify token was invalidated
        assert updated_user.metadata.get('password_reset_token') is None, "Token must be cleared after use"
        assert updated_user.metadata.get('password_reset_expires') is None, "Expiration must be cleared"

    @pytest.mark.asyncio
    async def test_complete_password_reset_weak_password_raises_error(self):
        """
        Test that weak password is rejected even with valid token.

        Security Requirement:
        Password strength requirements apply to reset passwords too.

        Expected Behavior:
        - Raises ValueError for weak password
        - Does not update password
        - Does not invalidate token (user can retry)
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        reset_token = "valid-token-abc123"
        weak_password = "weak"  # Too short, no complexity

        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user.add_metadata('password_reset_token', reset_token)
        user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))

        user_dao.get_user_by_metadata = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await auth_service.complete_password_reset(reset_token, weak_password)

        assert "strength" in str(exc_info.value).lower(), "Error should indicate password strength issue"

        # Verify password was not updated
        assert user_dao.update.call_count == 0, "Weak password should not trigger update"

    @pytest.mark.asyncio
    async def test_complete_password_reset_expired_token_raises_error(self):
        """
        Test that expired token cannot be used to reset password.

        Security Requirement:
        Expired tokens must be rejected even if password is valid.

        Expected Behavior:
        - Raises ValueError with "expired" message
        - Does not update password
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        reset_token = "expired-token-xyz789"
        new_password = "ValidP@ssw0rd123"

        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user.add_metadata('password_reset_token', reset_token)
        user.add_metadata('password_reset_expires', datetime.now(timezone.utc) - timedelta(hours=2))  # Expired

        user_dao.get_user_by_metadata = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await auth_service.complete_password_reset(reset_token, new_password)

        assert "expired" in str(exc_info.value).lower(), "Error should indicate token expired"
        assert user_dao.update.call_count == 0, "Expired token should not trigger password update"

    @pytest.mark.asyncio
    async def test_complete_password_reset_invalid_token_raises_error(self):
        """
        Test that invalid token cannot be used to reset password.

        Security Requirement:
        Only valid tokens can reset passwords.

        Expected Behavior:
        - Raises ValueError with "invalid" message
        - Does not update password
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        user_dao.get_user_by_metadata = AsyncMock(return_value=None)  # Token not found

        auth_service = AuthenticationService(user_dao)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await auth_service.complete_password_reset("fake-token-999", "ValidP@ssw0rd123")

        assert "invalid" in str(exc_info.value).lower(), "Error should indicate invalid token"
        assert user_dao.update.call_count == 0, "Invalid token should not trigger password update"


class TestPasswordResetEdgeCases:
    """
    Test suite for password reset edge cases and security scenarios.

    Business Logic:
    Handle edge cases like:
    - Multiple concurrent reset requests
    - Token reuse attempts
    - Timing attacks
    - Account status changes during reset
    """

    @pytest.mark.asyncio
    async def test_request_password_reset_overwrites_previous_token(self):
        """
        Test that new reset request invalidates previous token.

        Security Requirement:
        Only the most recent token should be valid. Old tokens must be invalidated.

        Expected Behavior:
        - New request generates new token
        - Old token is overwritten
        - Only new token is valid
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user.add_metadata('password_reset_token', 'old-token-123')
        user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))

        user_dao.get_user_by_email = AsyncMock(return_value=user)
        user_dao.update = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act
        new_token = await auth_service.request_password_reset("user@example.com")

        # Assert
        assert new_token != 'old-token-123', "New request must generate different token"

        # Verify old token was overwritten
        updated_user = user_dao.update.call_args[0][0]
        assert updated_user.metadata['password_reset_token'] == new_token, "Old token should be overwritten"

    @pytest.mark.asyncio
    async def test_complete_password_reset_token_can_only_be_used_once(self):
        """
        Test that reset token is invalidated after successful use.

        Security Requirement:
        Tokens are single-use. After successful password reset, token must be invalidated.

        Expected Behavior:
        - First use succeeds
        - Token is cleared from metadata
        - Second use with same token fails
        """
        # Arrange
        user_dao = Mock(spec=UserManagementDAO)
        reset_token = "one-time-token-456"

        user = User(
            id="user-123",
            email="user@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        user.add_metadata('password_reset_token', reset_token)
        user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))

        user_dao.get_user_by_metadata = AsyncMock(return_value=user)
        user_dao.update = AsyncMock(return_value=user)

        auth_service = AuthenticationService(user_dao)

        # Act - First use
        success = await auth_service.complete_password_reset(reset_token, "NewP@ssw0rd123")
        assert success is True, "First use should succeed"

        # Verify token was cleared
        updated_user = user_dao.update.call_args[0][0]
        assert updated_user.metadata.get('password_reset_token') is None, "Token should be cleared after use"

        # Act - Second use (simulate user finding token in email and trying again)
        user_dao.get_user_by_metadata = AsyncMock(return_value=None)  # Token no longer exists

        # Assert - Second use fails
        with pytest.raises(ValueError) as exc_info:
            await auth_service.complete_password_reset(reset_token, "AnotherP@ss456")

        assert "invalid" in str(exc_info.value).lower(), "Token reuse should fail"
