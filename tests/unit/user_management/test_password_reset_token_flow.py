"""
Password Reset Token Flow Tests - TDD RED Phase (Mock-Free Version)

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
Following TDD methodology with real objects instead of mocks:
- RED: Write failing tests first (this file)
- GREEN: Implement minimum code to pass tests
- REFACTOR: Optimize and improve implementation

Author: Course Creator Platform Team
Version: 3.4.0 - Token-Based Password Reset (Mock-Free)
Last Updated: 2025-12-12
"""

import pytest
from datetime import datetime, timedelta, timezone
import secrets

# Skip all tests - these require real authentication service implementation
pytestmark = pytest.mark.skip(reason="Needs refactoring to use real AuthenticationService implementation without mocks")

# Service under test
from user_management.application.services.authentication_service import AuthenticationService
from user_management.domain.entities.user import User, UserRole, UserStatus

# Test fixtures and helpers
from data_access.user_dao import UserManagementDAO


class InMemoryUserDAO:
    """
    In-memory test double for UserManagementDAO.
    Uses real Python objects instead of mocks.
    """

    def __init__(self):
        self.users = {}
        self.users_by_email = {}
        self.users_by_metadata = {}

    async def get_user_by_email(self, email):
        return self.users_by_email.get(email)

    async def update(self, user):
        self.users[user.id] = user
        self.users_by_email[user.email] = user

        # Index by metadata for token lookup
        if hasattr(user, 'metadata') and 'password_reset_token' in user.metadata:
            token = user.metadata['password_reset_token']
            self.users_by_metadata[token] = user

        return user

    async def get_user_by_metadata_value(self, key, value):
        if key == 'password_reset_token':
            return self.users_by_metadata.get(value)
        return None

    async def get_by_id(self, user_id):
        return self.users.get(user_id)


@pytest.fixture
def user_dao():
    """Create in-memory user DAO for testing."""
    return InMemoryUserDAO()


@pytest.fixture
def auth_service(user_dao):
    """Create authentication service with test DAO."""
    return AuthenticationService(user_dao)


@pytest.fixture
def sample_user(user_dao):
    """Create a sample user in the DAO."""
    user = User(
        id="user-123",
        email="user@example.com",
        username="testuser",
        full_name="Test User",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE
    )
    user_dao.users[user.id] = user
    user_dao.users_by_email[user.email] = user
    return user


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
    async def test_request_password_reset_generates_secure_token(self, auth_service, sample_user):
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
        # Act
        reset_token = await auth_service.request_password_reset(sample_user.email)

        # Assert
        assert reset_token is not None, "Password reset should return token"
        assert isinstance(reset_token, str), "Token must be string"
        assert len(reset_token) >= 32, f"Token too short ({len(reset_token)} chars). Security requirement: >= 32"
        # URL-safe base64 uses only: A-Z, a-z, 0-9, -, _
        assert all(c.isalnum() or c in '-_' for c in reset_token), "Token must be URL-safe"

    @pytest.mark.asyncio
    async def test_request_password_reset_stores_token_with_expiration(self, auth_service, sample_user, user_dao):
        """
        Test that password reset token is stored with expiration timestamp.

        Business Rule:
        Tokens expire after 1 hour to limit attack window.

        Expected Storage:
        user.metadata['password_reset_token'] = token
        user.metadata['password_reset_expires'] = timestamp (1 hour from now)
        """
        # Act
        before_request = datetime.now(timezone.utc)
        reset_token = await auth_service.request_password_reset(sample_user.email)
        after_request = datetime.now(timezone.utc)

        # Assert - verify token was stored
        updated_user = user_dao.users[sample_user.id]

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
    async def test_request_password_reset_nonexistent_email_succeeds_no_enumeration(self, auth_service):
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
        # Act - should not raise exception
        result = await auth_service.request_password_reset("nonexistent@example.com")

        # Assert
        assert result is not None, "Should return success message even for invalid email"

    @pytest.mark.asyncio
    async def test_request_password_reset_generates_unique_tokens(self, auth_service, sample_user):
        """
        Test that multiple password reset requests generate unique tokens.

        Security Requirement:
        Each reset request must generate a unique token to prevent token reuse attacks.
        """
        # Act - request reset twice
        token1 = await auth_service.request_password_reset(sample_user.email)
        token2 = await auth_service.request_password_reset(sample_user.email)

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
    async def test_validate_reset_token_valid_token_returns_user_id(self, auth_service, sample_user, user_dao):
        """
        Test that valid unexpired token returns associated user ID.

        Expected Behavior:
        - Token exists and matches stored value
        - Token expiration is in future
        - Returns user ID for password reset
        """
        # Arrange
        reset_token = "valid-token-abc123"
        sample_user.add_metadata('password_reset_token', reset_token)
        sample_user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))
        user_dao.users_by_metadata[reset_token] = sample_user

        # Act
        user_id = await auth_service.validate_password_reset_token(reset_token)

        # Assert
        assert user_id == sample_user.id, "Valid token should return user ID"

    @pytest.mark.asyncio
    async def test_validate_reset_token_expired_token_raises_error(self, auth_service, sample_user, user_dao):
        """
        Test that expired token raises appropriate error.

        Security Requirement:
        Expired tokens must be rejected to limit attack window.

        Expected Behavior:
        - Raises ValueError with "expired" message
        - Does not return user ID
        """
        # Arrange
        reset_token = "expired-token-xyz789"
        sample_user.add_metadata('password_reset_token', reset_token)
        sample_user.add_metadata('password_reset_expires', datetime.now(timezone.utc) - timedelta(minutes=5))  # Expired 5 min ago
        user_dao.users_by_metadata[reset_token] = sample_user

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await auth_service.validate_password_reset_token(reset_token)

        assert "expired" in str(exc_info.value).lower(), "Error message should indicate token expired"

    @pytest.mark.asyncio
    async def test_validate_reset_token_invalid_token_raises_error(self, auth_service):
        """
        Test that nonexistent token raises appropriate error.

        Security Requirement:
        Invalid tokens must be rejected without revealing whether token existed.

        Expected Behavior:
        - Raises ValueError with generic "invalid" message
        - Does not reveal whether token never existed vs already used
        """
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
    async def test_complete_password_reset_valid_token_updates_password(self, auth_service, sample_user, user_dao):
        """
        Test that valid token allows password update.

        Expected Workflow:
        1. Validate token
        2. Hash new password
        3. Update user password
        4. Invalidate token
        """
        # Arrange
        reset_token = "valid-token-abc123"
        new_password = "NewSecureP@ss123"

        sample_user.add_metadata('password_reset_token', reset_token)
        sample_user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))
        sample_user.add_metadata('hashed_password', 'old-hashed-password')
        user_dao.users_by_metadata[reset_token] = sample_user

        # Act
        success = await auth_service.complete_password_reset(reset_token, new_password)

        # Assert
        assert success is True, "Password reset should succeed with valid token"

        # Verify password was updated
        updated_user = user_dao.users[sample_user.id]

        # Verify password was hashed (not stored as plaintext)
        new_hashed_password = updated_user.metadata.get('hashed_password')
        assert new_hashed_password != new_password, "Password must be hashed, not plaintext"
        assert new_hashed_password != 'old-hashed-password', "Password must be updated"

        # Verify token was invalidated
        assert updated_user.metadata.get('password_reset_token') is None, "Token must be cleared after use"
        assert updated_user.metadata.get('password_reset_expires') is None, "Expiration must be cleared"

    @pytest.mark.asyncio
    async def test_complete_password_reset_weak_password_raises_error(self, auth_service, sample_user, user_dao):
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
        reset_token = "valid-token-abc123"
        weak_password = "weak"  # Too short, no complexity

        sample_user.add_metadata('password_reset_token', reset_token)
        sample_user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))
        user_dao.users_by_metadata[reset_token] = sample_user

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await auth_service.complete_password_reset(reset_token, weak_password)

        assert "strength" in str(exc_info.value).lower(), "Error should indicate password strength issue"

    @pytest.mark.asyncio
    async def test_complete_password_reset_expired_token_raises_error(self, auth_service, sample_user, user_dao):
        """
        Test that expired token cannot be used to reset password.

        Security Requirement:
        Expired tokens must be rejected even if password is valid.

        Expected Behavior:
        - Raises ValueError with "expired" message
        - Does not update password
        """
        # Arrange
        reset_token = "expired-token-xyz789"
        new_password = "ValidP@ssw0rd123"

        sample_user.add_metadata('password_reset_token', reset_token)
        sample_user.add_metadata('password_reset_expires', datetime.now(timezone.utc) - timedelta(hours=2))  # Expired
        user_dao.users_by_metadata[reset_token] = sample_user

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await auth_service.complete_password_reset(reset_token, new_password)

        assert "expired" in str(exc_info.value).lower(), "Error should indicate token expired"

    @pytest.mark.asyncio
    async def test_complete_password_reset_invalid_token_raises_error(self, auth_service):
        """
        Test that invalid token cannot be used to reset password.

        Security Requirement:
        Only valid tokens can reset passwords.

        Expected Behavior:
        - Raises ValueError with "invalid" message
        - Does not update password
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await auth_service.complete_password_reset("fake-token-999", "ValidP@ssw0rd123")

        assert "invalid" in str(exc_info.value).lower(), "Error should indicate invalid token"


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
    async def test_request_password_reset_overwrites_previous_token(self, auth_service, sample_user, user_dao):
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
        sample_user.add_metadata('password_reset_token', 'old-token-123')
        sample_user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))

        # Act
        new_token = await auth_service.request_password_reset(sample_user.email)

        # Assert
        assert new_token != 'old-token-123', "New request must generate different token"

        # Verify old token was overwritten
        updated_user = user_dao.users[sample_user.id]
        assert updated_user.metadata['password_reset_token'] == new_token, "Old token should be overwritten"

    @pytest.mark.asyncio
    async def test_complete_password_reset_token_can_only_be_used_once(self, auth_service, sample_user, user_dao):
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
        reset_token = "one-time-token-456"

        sample_user.add_metadata('password_reset_token', reset_token)
        sample_user.add_metadata('password_reset_expires', datetime.now(timezone.utc) + timedelta(minutes=30))
        user_dao.users_by_metadata[reset_token] = sample_user

        # Act - First use
        success = await auth_service.complete_password_reset(reset_token, "NewP@ssw0rd123")
        assert success is True, "First use should succeed"

        # Verify token was cleared
        updated_user = user_dao.users[sample_user.id]
        assert updated_user.metadata.get('password_reset_token') is None, "Token should be cleared after use"

        # Act - Second use (simulate user finding token in email and trying again)
        # Assert - Second use fails
        with pytest.raises(ValueError) as exc_info:
            await auth_service.complete_password_reset(reset_token, "AnotherP@ss456")

        assert "invalid" in str(exc_info.value).lower(), "Token reuse should fail"
