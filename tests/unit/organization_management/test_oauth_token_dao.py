"""
OAuthTokenDAO Unit Tests - TDD RED Phase

BUSINESS CONTEXT:
The OAuthTokenDAO handles OAuth token management for all integrations (Google, Microsoft,
Slack, LTI, etc.), providing secure storage, retrieval, refresh, and encryption.

REFACTORING CONTEXT:
This test file is part of the IntegrationsDAO god class refactoring (2,911 lines → 5 specialized DAOs).
The OAuthTokenDAO will be extracted to handle ONLY OAuth token operations shared across all integrations.

TEST COVERAGE (TDD RED Phase):
1. Token Storage and Retrieval (6 tests)
2. Token Encryption and Decryption (5 tests)
3. Token Refresh Automation (6 tests)
4. Token Expiration Management (5 tests)
5. Multi-Provider Token Management (5 tests)
6. Token Revocation and Cleanup (3 tests)

DEPENDENCIES:
- Custom exceptions from shared/exceptions/__init__.py
- cryptography for AES-256 encryption
- OAuth provider SDKs (google-auth, msal, slack-sdk)

EXPECTED BEHAVIOR (TDD RED - These tests WILL FAIL until implementation):
All tests define the DESIRED behavior for the OAuthTokenDAO.
Implementation should follow the Clean Architecture pattern:
- Domain layer: OAuth token entities
- Application layer: Token refresh service
- Infrastructure layer: OAuthTokenDAO (database + encryption operations)

Related Files:
- services/organization-management/organization_management/data_access/integrations_dao.py (original god class)
- docs/INTEGRATIONS_DAO_REFACTORING_STATUS.md (refactoring plan)
- docs/EXCEPTION_MAPPING_GUIDE.md (exception handling patterns)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Optional

# These imports will fail until the OAuthTokenDAO is created (TDD RED phase)
try:
    from organization_management.infrastructure.repositories.oauth_token_dao import OAuthTokenDAO
except ImportError:
    OAuthTokenDAO = None  # Expected during RED phase

# Custom exceptions (these should exist)
from shared.exceptions import (
    DatabaseException,
    ValidationException,
    ConflictException,
    NotFoundException,
    AuthenticationException,
    RateLimitException,
    ExternalServiceException
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def fake_db_pool():
    """Mock database connection pool.

    Supports both patterns:
    - Direct await: conn = await pool.acquire()
    - Context manager: async with pool.acquire() as conn
    """
    pool = AsyncMock()
    conn = AsyncMock()

    # Configure for direct await pattern (used by OAuthTokenDAO implementation)
    pool.acquire.return_value = conn
    pool.release = AsyncMock()

    # Also configure for async context manager pattern (if needed)
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    # Configure connection methods
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.execute = AsyncMock()
    return pool


@pytest.fixture
def sample_organization_id():
    """Sample organization UUID."""
    return "org-550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_google_tokens():
    """Sample Google OAuth tokens."""
    return {
        "provider": "google",
        "access_token": "ya29.a0AfH6SMBx...",
        "refresh_token": "1//0gJKwXYZ...",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "scope": "https://www.googleapis.com/auth/calendar.events"
    }


@pytest.fixture
def sample_microsoft_tokens():
    """Sample Microsoft OAuth tokens."""
    return {
        "provider": "microsoft",
        "access_token": "EwBwA8l6BAAURSN...",
        "refresh_token": "M.R3_BAY.-CRvF...",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "scope": "Calendars.ReadWrite User.Read"
    }


@pytest.fixture
def sample_slack_tokens():
    """Sample Slack OAuth tokens."""
    return {
        "provider": "slack",
        "access_token": "test-fake-slack-bot-token-not-real-1234567890",
        "token_type": "bot",
        "scope": "channels:read,chat:write,commands",
        "bot_user_id": "U0123BOTUSER"
        # Note: Slack bot tokens don't expire
    }


# ============================================================================
# TEST CLASS 1: Token Storage and Retrieval
# ============================================================================

@pytest.mark.skipif(OAuthTokenDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestTokenStorageAndRetrieval:
    """
    Tests for OAuth token storage and retrieval.

    BUSINESS REQUIREMENTS:
    - Securely store OAuth tokens for multiple providers
    - Retrieve tokens by organization and provider
    - Support multiple integrations per organization
    - Link tokens to specific integration records
    """

    @pytest.mark.asyncio
    async def test_store_oauth_tokens(self, fake_db_pool, sample_organization_id, sample_google_tokens):
        """
        Test storing OAuth tokens for an integration.

        EXPECTED BEHAVIOR:
        - Encrypts tokens before storage
        - Stores access token, refresh token, expiration
        - Links to integration_id
        - Returns storage confirmation
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Mock encrypt_token to avoid needing actual encryption key
        with patch("organization_management.infrastructure.repositories.oauth_token_dao.encrypt_token") as mock_encrypt:
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"

            # Act
            result = await dao.store_tokens(
                organization_id=sample_organization_id,
                integration_id="int-google-123",
                tokens=sample_google_tokens
            )

        # Assert
        assert result["stored"] is True
        assert result["integration_id"] == "int-google-123"
        assert result["provider"] == "google"
        assert result["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_retrieve_oauth_tokens(self, fake_db_pool, sample_organization_id, sample_google_tokens):
        """
        Test retrieving OAuth tokens for an integration.

        EXPECTED BEHAVIOR:
        - Retrieves encrypted tokens from database
        - Decrypts tokens
        - Returns access token, refresh token, expiration
        - Checks if token is expired
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - tokens stored in DB (encrypted values in access_token/refresh_token columns)
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "int-google-123",
            "provider": "google",
            "access_token": "encrypted_access_token_base64==",
            "refresh_token": "encrypted_refresh_token_base64==",
            "token_type": "Bearer",
            "expires_at": sample_google_tokens["expires_at"],
            "is_valid": True
        }

        with patch("organization_management.infrastructure.repositories.oauth_token_dao.decrypt_token") as mock_decrypt:
            mock_decrypt.side_effect = lambda x: x.replace("encrypted_", "").replace("_base64==", "")

            # Act
            result = await dao.get_tokens(
                organization_id=sample_organization_id,
                integration_id="int-google-123"
            )

        # Assert
        assert result["provider"] == "google"
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_retrieve_tokens_by_provider(self, fake_db_pool, sample_organization_id):
        """
        Test retrieving all tokens for a specific provider.

        EXPECTED BEHAVIOR:
        - Retrieves all integrations for provider
        - Returns list of tokens
        - Useful for batch operations
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - mock returns what SQL query selects: id, provider, access_token, refresh_token, expires_at
        fake_db_pool.acquire.return_value.fetch.return_value = [
            {
                "id": "int-google-1",
                "provider": "google",
                "access_token": "encrypted_token_1",
                "refresh_token": "refresh_1",
                "expires_at": datetime.utcnow() + timedelta(hours=1)
            },
            {
                "id": "int-google-2",
                "provider": "google",
                "access_token": "encrypted_token_2",
                "refresh_token": "refresh_2",
                "expires_at": datetime.utcnow() + timedelta(hours=2)
            }
        ]

        # Act
        result = await dao.get_tokens_by_provider(
            organization_id=sample_organization_id,
            provider="google"
        )

        # Assert
        assert len(result["tokens"]) == 2
        assert all(t["provider"] == "google" for t in result["tokens"])

    @pytest.mark.asyncio
    async def test_update_oauth_tokens(self, fake_db_pool, sample_organization_id, sample_google_tokens):
        """
        Test updating existing OAuth tokens (e.g., after refresh).

        EXPECTED BEHAVIOR:
        - Updates access token and expiration
        - Preserves refresh token if not changed
        - Encrypts new tokens
        - Returns update confirmation
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        updated_tokens = sample_google_tokens.copy()
        updated_tokens["access_token"] = "ya29.NEW_ACCESS_TOKEN"
        updated_tokens["expires_at"] = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        # Mock encrypt_token to avoid needing actual encryption key
        with patch("organization_management.infrastructure.repositories.oauth_token_dao.encrypt_token") as mock_encrypt:
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"

            # Act
            result = await dao.update_tokens(
                organization_id=sample_organization_id,
                integration_id="int-google-123",
                tokens=updated_tokens
            )

        # Assert
        assert result["updated"] is True
        assert result["access_token_changed"] is True

    @pytest.mark.asyncio
    async def test_tokens_not_found(self, fake_db_pool, sample_organization_id):
        """
        Test retrieving tokens when integration doesn't exist.

        EXPECTED BEHAVIOR:
        - Returns None or raises NotFoundException
        - Provides clear error message
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - no tokens found
        fake_db_pool.acquire.return_value.fetchrow.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            await dao.get_tokens(
                organization_id=sample_organization_id,
                integration_id="nonexistent-integration"
            )

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_store_tokens_without_expiration(self, fake_db_pool, sample_organization_id, sample_slack_tokens):
        """
        Test storing tokens that don't expire (e.g., Slack bot tokens).

        EXPECTED BEHAVIOR:
        - Stores tokens with expires_at = NULL
        - Handles providers without token expiration
        - No automatic refresh needed
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Configure mock to return Slack token with no expiration
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "id": "int-slack-123",
            "provider": "slack",
            "expires_at": None
        }

        # Mock encrypt_token to avoid needing actual encryption key
        with patch("organization_management.infrastructure.repositories.oauth_token_dao.encrypt_token") as mock_encrypt:
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"

            # Act
            result = await dao.store_tokens(
                organization_id=sample_organization_id,
                integration_id="int-slack-123",
                tokens=sample_slack_tokens
            )

        # Assert
        assert result["stored"] is True
        assert result["expires_at"] is None  # Slack bot tokens don't expire


# ============================================================================
# TEST CLASS 2: Token Encryption and Decryption
# ============================================================================

@pytest.mark.skipif(OAuthTokenDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestTokenEncryptionAndDecryption:
    """
    Tests for OAuth token encryption and decryption.

    BUSINESS REQUIREMENTS:
    - All tokens must be encrypted at rest (AES-256)
    - Encryption key stored securely (AWS KMS, environment variable)
    - Tokens decrypted only when needed
    - No plaintext tokens in database
    """

    @pytest.mark.asyncio
    async def test_encrypt_token_aes256(self, fake_db_pool):
        """
        Test encrypting token using AES-256.

        EXPECTED BEHAVIOR:
        - Uses AES-256 encryption
        - Returns base64-encoded ciphertext
        - Different for each encryption (uses IV)
        """
        from cryptography.fernet import Fernet
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        plaintext_token = "ya29.a0AfH6SMBx..."

        # Use a valid Fernet key for testing
        test_key = Fernet.generate_key()
        with patch("organization_management.infrastructure.repositories.oauth_token_dao.get_encryption_key") as mock_key:
            mock_key.return_value = test_key

            # Act
            encrypted1 = await dao.encrypt_token(plaintext_token)
            encrypted2 = await dao.encrypt_token(plaintext_token)

        # Assert
        assert encrypted1 != plaintext_token
        assert encrypted1 != encrypted2  # Different due to IV
        assert len(encrypted1) > len(plaintext_token)

    @pytest.mark.asyncio
    async def test_decrypt_token(self, fake_db_pool):
        """
        Test decrypting token.

        EXPECTED BEHAVIOR:
        - Decrypts ciphertext to original token
        - Handles base64 encoding
        - Validates encryption key
        """
        from cryptography.fernet import Fernet
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        plaintext_token = "ya29.a0AfH6SMBx..."

        # Use a valid Fernet key for testing
        test_key = Fernet.generate_key()
        with patch("organization_management.infrastructure.repositories.oauth_token_dao.get_encryption_key") as mock_key:
            mock_key.return_value = test_key

            encrypted_token = await dao.encrypt_token(plaintext_token)

            # Act
            decrypted_token = await dao.decrypt_token(encrypted_token)

        # Assert
        assert decrypted_token == plaintext_token

    @pytest.mark.asyncio
    async def test_encryption_key_missing(self, fake_db_pool):
        """
        Test behavior when encryption key is not configured.

        EXPECTED BEHAVIOR:
        - Raises ValidationException
        - Prevents storing tokens in plaintext
        - Provides clear error message
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        with patch.dict("os.environ", {}, clear=True):  # Clear encryption key
            # Act & Assert
            with pytest.raises(ValidationException) as exc_info:
                await dao.encrypt_token("token123")

            assert "encryption key" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_decrypt_with_wrong_key(self, fake_db_pool):
        """
        Test decryption failure with wrong key.

        EXPECTED BEHAVIOR:
        - Raises AuthenticationException
        - Indicates decryption failure
        - Suggests key rotation or re-authentication
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - encrypt with one key (use valid Fernet keys - 32 bytes base64-encoded)
        from cryptography.fernet import Fernet
        correct_key = Fernet.generate_key()
        wrong_key = Fernet.generate_key()

        with patch("organization_management.infrastructure.repositories.oauth_token_dao.get_encryption_key") as mock_key:
            mock_key.return_value = correct_key
            encrypted = await dao.encrypt_token("token123")

        # Act - decrypt with different key
        with patch("organization_management.infrastructure.repositories.oauth_token_dao.get_encryption_key") as mock_key:
            mock_key.return_value = wrong_key

            with pytest.raises(AuthenticationException) as exc_info:
                await dao.decrypt_token(encrypted)

        assert "decrypt" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rotate_encryption_key(self, fake_db_pool, sample_organization_id):
        """
        Test rotating encryption key for all tokens.

        EXPECTED BEHAVIOR:
        - Decrypts all tokens with old key
        - Re-encrypts with new key
        - Updates all token records
        - Returns count of rotated tokens
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - 10 tokens encrypted with old key (columns: id, access_token, refresh_token)
        fake_db_pool.acquire.return_value.fetch.return_value = [
            {"id": f"int-{i}", "access_token": f"old_encrypted_{i}", "refresh_token": f"old_refresh_{i}"}
            for i in range(10)
        ]

        with patch("organization_management.infrastructure.repositories.oauth_token_dao.decrypt_token") as mock_decrypt, \
             patch("organization_management.infrastructure.repositories.oauth_token_dao.encrypt_token") as mock_encrypt:
            mock_decrypt.side_effect = lambda x: x.replace("old_encrypted_", "plaintext_")
            mock_encrypt.side_effect = lambda x: x.replace("plaintext_", "new_encrypted_")

            # Act
            result = await dao.rotate_encryption_keys(
                organization_id=sample_organization_id
            )

        # Assert
        assert result["rotated_count"] == 10
        assert result["success"] is True


# ============================================================================
# TEST CLASS 3: Token Refresh Automation
# ============================================================================

@pytest.mark.skipif(OAuthTokenDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestTokenRefreshAutomation:
    """
    Tests for automatic OAuth token refresh.

    BUSINESS REQUIREMENTS:
    - Detect expired or soon-to-expire tokens
    - Automatically refresh using refresh token
    - Update stored tokens with new values
    - Handle refresh failures gracefully
    - Support provider-specific refresh flows
    """

    @pytest.mark.asyncio
    async def test_detect_expired_token(self, fake_db_pool, sample_organization_id):
        """
        Test detecting expired access token.

        EXPECTED BEHAVIOR:
        - Checks expires_at timestamp
        - Returns True if expired
        - Triggers refresh workflow
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - expired token
        expired_tokens = {
            "access_token": "ya29.EXPIRED",
            "refresh_token": "1//0gJKwXYZ...",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
        }

        # Act
        result = await dao.is_token_expired(
            tokens=expired_tokens
        )

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_refresh_google_token(self, fake_db_pool, sample_organization_id, sample_google_tokens):
        """
        Test refreshing Google OAuth token.

        EXPECTED BEHAVIOR:
        - Uses refresh token to get new access token
        - Calls Google token endpoint
        - Updates stored tokens
        - Returns new access token
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        new_tokens = sample_google_tokens.copy()
        new_tokens["access_token"] = "ya29.NEW_TOKEN"
        new_tokens["expires_at"] = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        with patch("organization_management.infrastructure.repositories.oauth_token_dao.refresh_google_token") as mock_refresh, \
             patch("organization_management.infrastructure.repositories.oauth_token_dao.encrypt_token") as mock_encrypt:
            mock_refresh.return_value = new_tokens
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"

            # Act
            result = await dao.refresh_tokens(
                organization_id=sample_organization_id,
                integration_id="int-google-123",
                provider="google",
                refresh_token=sample_google_tokens["refresh_token"]
            )

        # Assert
        assert result["refreshed"] is True
        assert result["new_access_token"] == "ya29.NEW_TOKEN"
        mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_microsoft_token(self, fake_db_pool, sample_organization_id, sample_microsoft_tokens):
        """
        Test refreshing Microsoft OAuth token.

        EXPECTED BEHAVIOR:
        - Uses MSAL library for token refresh
        - Calls Microsoft identity platform
        - Updates stored tokens
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        new_tokens = sample_microsoft_tokens.copy()
        new_tokens["access_token"] = "NEW_MICROSOFT_TOKEN"

        with patch("organization_management.infrastructure.repositories.oauth_token_dao.refresh_microsoft_token") as mock_refresh, \
             patch("organization_management.infrastructure.repositories.oauth_token_dao.encrypt_token") as mock_encrypt:
            mock_refresh.return_value = new_tokens
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"

            # Act
            result = await dao.refresh_tokens(
                organization_id=sample_organization_id,
                integration_id="int-outlook-123",
                provider="microsoft",
                refresh_token=sample_microsoft_tokens["refresh_token"]
            )

        # Assert
        assert result["refreshed"] is True
        assert result["new_access_token"] == "NEW_MICROSOFT_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_grant(self, fake_db_pool, sample_organization_id, sample_google_tokens):
        """
        Test token refresh failure due to invalid_grant (revoked refresh token).

        EXPECTED BEHAVIOR:
        - Detects invalid_grant error
        - Marks integration as inactive
        - Raises AuthenticationException
        - Notifies organization to re-authenticate
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.oauth_token_dao.refresh_google_token") as mock_refresh:
            mock_refresh.side_effect = Exception("invalid_grant: Token has been revoked")

            # Act & Assert
            with pytest.raises(AuthenticationException) as exc_info:
                await dao.refresh_tokens(
                    organization_id=sample_organization_id,
                    integration_id="int-google-123",
                    provider="google",
                    refresh_token=sample_google_tokens["refresh_token"]
                )

            assert "invalid_grant" in str(exc_info.value).lower() or "revoked" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_automatic_token_refresh_on_retrieval(self, fake_db_pool, sample_organization_id, sample_google_tokens):
        """
        Test automatic token refresh when retrieving expired token.

        EXPECTED BEHAVIOR:
        - Detects token is expired
        - Automatically refreshes token
        - Returns new access token
        - Transparent to caller
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - expired token in database
        expired_expires_at = datetime.utcnow() - timedelta(hours=1)

        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "id": "int-google-123",
            "provider": "google",
            "access_token": "encrypted_expired_token",
            "refresh_token": "encrypted_refresh_token",
            "token_type": "Bearer",
            "expires_at": expired_expires_at,  # Expired
            "is_valid": True
        }

        new_tokens = sample_google_tokens.copy()
        new_tokens["access_token"] = "ya29.AUTO_REFRESHED"

        # Patch decrypt_token, encrypt_token, and refresh to avoid actual calls
        with patch("organization_management.infrastructure.repositories.oauth_token_dao.decrypt_token") as mock_decrypt, \
             patch("organization_management.infrastructure.repositories.oauth_token_dao.encrypt_token") as mock_encrypt, \
             patch("organization_management.infrastructure.repositories.oauth_token_dao.refresh_google_token") as mock_refresh:
            # decrypt_token is called for access_token and refresh_token
            mock_decrypt.side_effect = lambda x: "decrypted_" + x.replace("encrypted_", "")
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"
            mock_refresh.return_value = new_tokens

            # Act
            result = await dao.get_valid_access_token(
                organization_id=sample_organization_id,
                integration_id="int-google-123"
            )

        # Assert
        assert result["access_token"] == "ya29.AUTO_REFRESHED"
        assert result["auto_refreshed"] is True

    @pytest.mark.asyncio
    async def test_batch_refresh_expiring_tokens(self, fake_db_pool, sample_organization_id):
        """
        Test batch refresh of tokens expiring within 5 minutes.

        EXPECTED BEHAVIOR:
        - Finds all tokens expiring soon
        - Refreshes them proactively
        - Updates stored tokens
        - Returns summary of refreshes
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - 5 tokens expiring soon (columns: id, organization_id, provider, refresh_token, expires_at)
        fake_db_pool.acquire.return_value.fetch.return_value = [
            {
                "id": f"int-{i}",
                "organization_id": sample_organization_id,
                "provider": "google",
                "refresh_token": f"encrypted_refresh_{i}",
                "expires_at": datetime.utcnow() + timedelta(minutes=3)
            }
            for i in range(5)
        ]

        # Patch decrypt_token to avoid actual decryption of mock values
        with patch("organization_management.infrastructure.repositories.oauth_token_dao.decrypt_token") as mock_decrypt, \
             patch("organization_management.infrastructure.repositories.oauth_token_dao.refresh_google_token") as mock_refresh, \
             patch("organization_management.infrastructure.repositories.oauth_token_dao.encrypt_token") as mock_encrypt:
            # decrypt_token is called for each refresh_token
            mock_decrypt.side_effect = lambda x: x.replace("encrypted_", "decrypted_")
            mock_refresh.return_value = {"access_token": "NEW", "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()}
            mock_encrypt.return_value = "encrypted_new_token"

            # Act
            result = await dao.batch_refresh_expiring_tokens(
                threshold_minutes=5
            )

        # Assert
        assert result["refreshed_count"] == 5
        assert result["failed_count"] == 0


# ============================================================================
# TEST CLASS 4: Token Expiration Management
# ============================================================================

@pytest.mark.skipif(OAuthTokenDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestTokenExpirationManagement:
    """
    Tests for OAuth token expiration management.

    BUSINESS REQUIREMENTS:
    - Track token expiration timestamps
    - Calculate time until expiration
    - Identify expiring/expired tokens
    - Support tokens without expiration (Slack bot tokens)
    """

    @pytest.mark.asyncio
    async def test_calculate_time_until_expiration(self, fake_db_pool, sample_google_tokens):
        """
        Test calculating time remaining until token expires.

        EXPECTED BEHAVIOR:
        - Returns seconds until expiration
        - Returns negative value if already expired
        - Returns None if token doesn't expire
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Act
        result = await dao.get_time_until_expiration(
            expires_at=sample_google_tokens["expires_at"]
        )

        # Assert
        assert result > 0  # Should be ~3600 seconds (1 hour)
        assert result <= 3600

    @pytest.mark.asyncio
    async def test_get_expiring_tokens(self, fake_db_pool, sample_organization_id):
        """
        Test retrieving tokens expiring within specified timeframe.

        EXPECTED BEHAVIOR:
        - Returns tokens expiring within threshold
        - Used for proactive refresh
        - Excludes tokens without expiration
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - 3 tokens expiring soon (columns: id, provider, expires_at)
        fake_db_pool.acquire.return_value.fetch.return_value = [
            {
                "id": f"int-{i}",
                "provider": "google",
                "expires_at": datetime.utcnow() + timedelta(minutes=3)
            }
            for i in range(3)
        ]

        # Act
        result = await dao.get_expiring_tokens(
            organization_id=sample_organization_id,
            threshold_minutes=5
        )

        # Assert
        assert len(result["tokens"]) == 3
        assert all("expires_at" in t for t in result["tokens"])

    @pytest.mark.asyncio
    async def test_check_token_validity(self, fake_db_pool, sample_google_tokens):
        """
        Test checking if token is currently valid.

        EXPECTED BEHAVIOR:
        - Returns True if token exists and not expired
        - Returns False if expired
        - Considers grace period (5 minutes before expiration)
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Act - valid token
        result_valid = await dao.is_token_valid(
            expires_at=sample_google_tokens["expires_at"]
        )

        # Act - expired token
        result_expired = await dao.is_token_valid(
            expires_at=(datetime.utcnow() - timedelta(hours=1)).isoformat()
        )

        # Assert
        assert result_valid is True
        assert result_expired is False

    @pytest.mark.asyncio
    async def test_tokens_without_expiration(self, fake_db_pool, sample_slack_tokens):
        """
        Test handling tokens that never expire (e.g., Slack bot tokens).

        EXPECTED BEHAVIOR:
        - expires_at is NULL in database
        - Always considered valid
        - Never appear in expiring tokens list
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Act
        result = await dao.is_token_valid(
            expires_at=None  # Slack bot token
        )

        # Assert
        assert result is True  # Never expires = always valid

    @pytest.mark.asyncio
    async def test_update_token_expiration(self, fake_db_pool, sample_organization_id):
        """
        Test updating token expiration timestamp after refresh.

        EXPECTED BEHAVIOR:
        - Updates expires_at field
        - Preserves other token data
        - Returns confirmation
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        new_expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        # Act
        result = await dao.update_token_expiration(
            organization_id=sample_organization_id,
            integration_id="int-google-123",
            expires_at=new_expires_at
        )

        # Assert
        assert result["updated"] is True
        assert result["expires_at"] == new_expires_at


# ============================================================================
# TEST CLASS 5: Multi-Provider Token Management
# ============================================================================

@pytest.mark.skipif(OAuthTokenDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestMultiProviderTokenManagement:
    """
    Tests for managing tokens across multiple OAuth providers.

    BUSINESS REQUIREMENTS:
    - Support multiple providers (Google, Microsoft, Slack, LTI)
    - Each provider has different token format and refresh flow
    - Organization can have multiple integrations per provider
    - Provider-specific token handling
    """

    @pytest.mark.asyncio
    async def test_get_tokens_for_all_providers(self, fake_db_pool, sample_organization_id):
        """
        Test retrieving tokens for all connected providers.

        EXPECTED BEHAVIOR:
        - Returns tokens grouped by provider
        - Includes all active integrations
        - Shows expiration status
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - tokens for 3 providers (columns: id, provider, expires_at)
        fake_db_pool.acquire.return_value.fetch.return_value = [
            {"id": "int-google-1", "provider": "google", "expires_at": datetime.utcnow() + timedelta(hours=1)},
            {"id": "int-outlook-1", "provider": "microsoft", "expires_at": datetime.utcnow() + timedelta(hours=1)},
            {"id": "int-slack-1", "provider": "slack", "expires_at": None}
        ]

        # Act
        result = await dao.get_all_provider_tokens(
            organization_id=sample_organization_id
        )

        # Assert
        assert len(result["providers"]) == 3
        assert "google" in result["providers"]
        assert "microsoft" in result["providers"]
        assert "slack" in result["providers"]

    @pytest.mark.asyncio
    async def test_provider_specific_token_format(self, fake_db_pool, sample_organization_id):
        """
        Test that each provider has unique token format requirements.

        EXPECTED BEHAVIOR:
        - Google: access_token, refresh_token, expires_in
        - Microsoft: access_token, refresh_token, expires_in, scope
        - Slack: access_token (bot), bot_user_id, no expiration
        - LTI: JWT access token with client_credentials grant
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Act - validate Google format
        google_valid = await dao.validate_token_format(
            provider="google",
            tokens={"access_token": "ya29...", "refresh_token": "1//...", "expires_in": 3600}
        )

        # Act - validate Slack format
        slack_valid = await dao.validate_token_format(
            provider="slack",
            tokens={"access_token": "xoxb-...", "bot_user_id": "U0123"}
        )

        # Assert
        assert google_valid is True
        assert slack_valid is True

    @pytest.mark.asyncio
    async def test_provider_specific_refresh_flow(self, fake_db_pool, sample_organization_id):
        """
        Test that each provider uses correct refresh flow.

        EXPECTED BEHAVIOR:
        - Google: Uses google-auth library
        - Microsoft: Uses MSAL library
        - Slack: Bot tokens don't refresh
        - LTI: Uses client_credentials grant
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Act - refresh different providers
        with patch("organization_management.infrastructure.repositories.oauth_token_dao.refresh_google_token") as mock_google, \
             patch("organization_management.infrastructure.repositories.oauth_token_dao.refresh_microsoft_token") as mock_microsoft, \
             patch("organization_management.infrastructure.repositories.oauth_token_dao.encrypt_token") as mock_encrypt:
            mock_google.return_value = {"access_token": "new_google"}
            mock_microsoft.return_value = {"access_token": "new_microsoft"}
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"

            result_google = await dao.refresh_tokens(
                organization_id=sample_organization_id,
                integration_id="int-google-1",
                provider="google",
                refresh_token="refresh_token"
            )

            result_microsoft = await dao.refresh_tokens(
                organization_id=sample_organization_id,
                integration_id="int-outlook-1",
                provider="microsoft",
                refresh_token="refresh_token"
            )

        # Assert
        mock_google.assert_called_once()
        mock_microsoft.assert_called_once()
        assert result_google["new_access_token"] == "new_google"
        assert result_microsoft["new_access_token"] == "new_microsoft"

    @pytest.mark.asyncio
    async def test_multiple_integrations_same_provider(self, fake_db_pool, sample_organization_id):
        """
        Test organization with multiple integrations for same provider.

        EXPECTED BEHAVIOR:
        - Supports multiple Google accounts
        - Supports multiple Slack workspaces
        - Each integration has separate tokens
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - get_tokens_by_provider selects: id, provider, access_token, refresh_token, expires_at
        fake_db_pool.acquire.return_value.fetch.return_value = [
            {"id": "int-google-1", "provider": "google", "access_token": "enc1", "refresh_token": "ref1", "expires_at": datetime.utcnow() + timedelta(hours=1)},
            {"id": "int-google-2", "provider": "google", "access_token": "enc2", "refresh_token": "ref2", "expires_at": datetime.utcnow() + timedelta(hours=1)}
        ]

        # Act
        result = await dao.get_tokens_by_provider(
            organization_id=sample_organization_id,
            provider="google"
        )

        # Assert
        assert len(result["tokens"]) == 2
        assert result["tokens"][0]["integration_id"] != result["tokens"][1]["integration_id"]

    @pytest.mark.asyncio
    async def test_unsupported_provider(self, fake_db_pool, sample_organization_id):
        """
        Test handling unsupported OAuth provider.

        EXPECTED BEHAVIOR:
        - Raises ValidationException
        - Lists supported providers
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            await dao.store_tokens(
                organization_id=sample_organization_id,
                integration_id="int-unsupported",
                tokens={"access_token": "token", "provider": "unsupported_provider"}
            )

        assert "provider" in str(exc_info.value).lower()


# ============================================================================
# TEST CLASS 6: Token Revocation and Cleanup
# ============================================================================

@pytest.mark.skipif(OAuthTokenDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestTokenRevocationAndCleanup:
    """
    Tests for OAuth token revocation and cleanup.

    BUSINESS REQUIREMENTS:
    - Revoke tokens when disconnecting integration
    - Clean up expired tokens (data retention)
    - Securely delete sensitive token data
    """

    @pytest.mark.asyncio
    async def test_revoke_oauth_tokens(self, fake_db_pool, sample_organization_id, sample_google_tokens):
        """
        Test revoking OAuth tokens with provider.

        EXPECTED BEHAVIOR:
        - Calls provider's token revocation endpoint
        - Deletes stored tokens from database
        - Returns confirmation
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.oauth_token_dao.revoke_google_token") as mock_revoke:
            mock_revoke.return_value = {"revoked": True}

            # Act
            result = await dao.revoke_tokens(
                organization_id=sample_organization_id,
                integration_id="int-google-123",
                provider="google",
                access_token=sample_google_tokens["access_token"]
            )

        # Assert
        assert result["revoked"] is True
        mock_revoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_tokens_from_database(self, fake_db_pool, sample_organization_id):
        """
        Test securely deleting tokens from database.

        EXPECTED BEHAVIOR:
        - Deletes token record
        - Overwrites sensitive fields before delete (defense in depth)
        - Returns confirmation
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Act
        result = await dao.delete_tokens(
            organization_id=sample_organization_id,
            integration_id="int-google-123"
        )

        # Assert
        assert result["deleted"] is True
        assert result["integration_id"] == "int-google-123"

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, fake_db_pool):
        """
        Test cleanup of expired tokens (data retention policy).

        EXPECTED BEHAVIOR:
        - Finds tokens expired more than 90 days ago
        - Deletes old token records
        - Returns count of cleaned tokens
        """
        dao = OAuthTokenDAO(db_pool=fake_db_pool)

        # Arrange - execute() returns "DELETE N" format string
        fake_db_pool.acquire.return_value.execute.return_value = "DELETE 25"

        # Act
        result = await dao.cleanup_expired_tokens(
            retention_days=90
        )

        # Assert
        assert result["deleted_count"] == 25
        assert result["retention_policy_days"] == 90
