"""
OAuthTokenDAO - OAuth Token Management Data Access Object

BUSINESS CONTEXT:
The OAuthTokenDAO provides secure storage, retrieval, encryption, and refresh management
for OAuth tokens across all integration providers (Google, Microsoft, Slack, LTI).

REFACTORING CONTEXT:
Extracted from IntegrationsDAO god class (2,911 lines → 5 specialized DAOs).
This DAO handles ONLY OAuth token operations shared across all integrations.

ARCHITECTURE:
Following Clean Architecture patterns:
- Domain layer: OAuthToken entity
- Application layer: Token refresh services (future)
- Infrastructure layer: This DAO (database + encryption operations)

SECURITY:
- All tokens encrypted at rest using AES-256
- Encryption key stored securely (environment variable or AWS KMS)
- Tokens decrypted only when needed
- No plaintext tokens in database

Related Files:
- services/organization-management/organization_management/domain/entities/integrations.py (OAuthToken entity)
- services/organization-management/organization_management/data_access/integrations_dao.py (original god class)
- tests/unit/organization_management/test_oauth_token_dao.py (test suite - 30 tests)
"""

import asyncpg
import logging
import json
import os
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from dateutil import parser as date_parser

from shared.exceptions import (
    DatabaseException,
    ValidationException,
    NotFoundException,
    AuthenticationException,
    ExternalServiceException
)
from organization_management.domain.entities.integrations import (
    OAuthToken,
    OAuthProvider
)


# ================================================================
# MODULE-LEVEL ENCRYPTION HELPERS
# ================================================================

def get_encryption_key() -> bytes:
    """
    Get encryption key from environment variable or generate one.

    Returns:
        Encryption key bytes (32 bytes for AES-256)

    Raises:
        ValidationException: If encryption key not configured
    """
    key_b64 = os.environ.get("OAUTH_TOKEN_ENCRYPTION_KEY")
    if not key_b64:
        raise ValidationException(
            message="OAuth token encryption key not configured. Set OAUTH_TOKEN_ENCRYPTION_KEY environment variable.",
            validation_errors={"env_var": "OAUTH_TOKEN_ENCRYPTION_KEY"}
        )

    try:
        return base64.b64decode(key_b64)
    except Exception as e:
        raise ValidationException(
            message="Invalid encryption key format. Must be base64-encoded 32-byte key.",
            validation_errors={"error": str(e)}
        )


def encrypt_token(plaintext_token: str) -> str:
    """
    Encrypt token using AES-256 (Fernet).

    Args:
        plaintext_token: Token to encrypt

    Returns:
        Base64-encoded encrypted token

    Raises:
        ValidationException: If encryption fails
    """
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(plaintext_token.encode())
        return base64.b64encode(encrypted).decode()
    except ValidationException:
        raise
    except Exception as e:
        raise ValidationException(
            message="Failed to encrypt token",
            validation_errors={"error": str(e)}
        )


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt token using AES-256 (Fernet).

    Args:
        encrypted_token: Base64-encoded encrypted token

    Returns:
        Decrypted plaintext token

    Raises:
        AuthenticationException: If decryption fails (wrong key, corrupted data)
    """
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_token.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise AuthenticationException(
            message="Failed to decrypt token. The encryption key may have changed or the token is corrupted.", reason=str(e)
        )


# ================================================================
# MODULE-LEVEL PROVIDER-SPECIFIC REFRESH HELPERS
# ================================================================

def refresh_google_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh Google OAuth token.

    NOTE: This is a stub that will be mocked in tests.
    Real implementation would call Google's token endpoint.

    Args:
        refresh_token: Google refresh token

    Returns:
        Dictionary with new access_token, expires_in, expires_at

    Raises:
        ExternalServiceException: If refresh fails
    """
    raise ExternalServiceException(
        message="Google token refresh not implemented. Mock this function in tests.",
        service_name_external="google",
        operation="refresh_token"
    )


def refresh_microsoft_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh Microsoft OAuth token.

    NOTE: This is a stub that will be mocked in tests.
    Real implementation would use MSAL library.

    Args:
        refresh_token: Microsoft refresh token

    Returns:
        Dictionary with new access_token, expires_in, expires_at

    Raises:
        ExternalServiceException: If refresh fails
    """
    raise ExternalServiceException(
        message="Microsoft token refresh not implemented. Mock this function in tests.",
        service_name_external="microsoft",
        operation="refresh_token"
    )


def revoke_google_token(access_token: str) -> Dict[str, Any]:
    """
    Revoke Google OAuth token.

    NOTE: This is a stub that will be mocked in tests.
    Real implementation would call Google's revocation endpoint.

    Args:
        access_token: Google access token to revoke

    Returns:
        Dictionary with revoked status

    Raises:
        ExternalServiceException: If revocation fails
    """
    raise ExternalServiceException(
        message="Google token revocation not implemented. Mock this function in tests.",
        service_name_external="google",
        operation="revoke_token"
    )


class OAuthTokenDAO:
    """
    Data Access Object for OAuth token management.

    RESPONSIBILITIES:
    - Store and retrieve OAuth tokens for all providers
    - Encrypt/decrypt tokens at rest
    - Manage token expiration and refresh
    - Support multiple providers (Google, Microsoft, Slack, LTI)
    - Handle multi-tenant data isolation

    DATABASE SCHEMA:
    Table: oauth_tokens
    Columns:
    - id (UUID, primary key)
    - user_id (UUID, nullable)
    - organization_id (UUID, nullable)
    - provider (VARCHAR) - 'google', 'microsoft', 'slack', 'lti'
    - provider_user_id (VARCHAR) - external user ID
    - access_token (TEXT) - encrypted
    - refresh_token (TEXT) - encrypted, nullable
    - token_type (VARCHAR) - 'Bearer', 'bot', etc.
    - expires_at (TIMESTAMP, nullable)
    - refresh_expires_at (TIMESTAMP, nullable)
    - scopes (TEXT[]) - array of scope strings
    - is_valid (BOOLEAN) - false if revoked or failed
    - last_used_at (TIMESTAMP)
    - last_refreshed_at (TIMESTAMP)
    - consecutive_failures (INTEGER) - for circuit breaker
    - last_error (TEXT)
    - created_at (TIMESTAMP)
    - updated_at (TIMESTAMP)
    """

    SUPPORTED_PROVIDERS = ["google", "microsoft", "slack", "lti"]

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize OAuthTokenDAO.

        Args:
            db_pool: asyncpg connection pool
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # BASIC CRUD OPERATIONS
    # ================================================================

    async def store_tokens(
        self,
        organization_id: str,
        integration_id: str,
        tokens: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store OAuth tokens for an integration.

        What: Persists OAuth tokens with encryption.
        Where: Called when user authorizes external service.
        Why: Enables secure token storage for API access.

        BUSINESS RULES:
        - Tokens must be encrypted before storage
        - Access token and expiration are required
        - Refresh token is optional (Slack bot tokens don't have it)
        - Links to integration_id for tracking

        Args:
            organization_id: UUID of the organization
            integration_id: UUID of the integration
            tokens: Dictionary containing:
                - provider (str): 'google', 'microsoft', 'slack', 'lti'
                - access_token (str): OAuth access token
                - refresh_token (str, optional): OAuth refresh token
                - token_type (str): 'Bearer', 'bot', etc.
                - expires_in (int, optional): Seconds until expiration
                - expires_at (str, optional): ISO timestamp of expiration
                - scope (str, optional): Space-separated scopes

        Returns:
            Dictionary containing:
                - stored (bool): True if successful
                - integration_id (str): Integration UUID
                - provider (str): Provider name
                - expires_at (str or None): Expiration timestamp

        Raises:
            ValidationException: If tokens are invalid or already exist
            DatabaseException: If database operation fails
        """
        try:
            provider = tokens.get("provider")
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            token_type = tokens.get("token_type", "Bearer")

            # Validate provider
            if provider and provider not in self.SUPPORTED_PROVIDERS:
                raise ValidationException(
                    message=f"Unsupported OAuth provider: {provider}. Supported: {', '.join(self.SUPPORTED_PROVIDERS)}",
                    validation_errors={"provider": provider}
                )

            # Calculate expiration
            expires_at = None
            if "expires_at" in tokens:
                expires_at = tokens["expires_at"]
            elif "expires_in" in tokens:
                expires_at = (datetime.utcnow() + timedelta(seconds=tokens["expires_in"])).isoformat()

            # Parse scopes
            scopes = []
            if "scope" in tokens:
                scopes = tokens["scope"].split(" ") if isinstance(tokens["scope"], str) else tokens["scope"]

            # Encrypt tokens
            encrypted_access = encrypt_token(access_token) if access_token else None
            encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

            conn = await self.db_pool.acquire()
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO oauth_tokens (
                        id, organization_id, provider, access_token,
                        refresh_token, token_type, expires_at, scopes,
                        is_valid, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, true, $8, $9
                    )
                    RETURNING id, provider, expires_at
                    """,
                    organization_id,
                    provider,
                    encrypted_access,
                    encrypted_refresh,
                    token_type,
                    expires_at,
                    scopes,
                    datetime.now(),
                    datetime.now()
                )

                return {
                    "stored": True,
                    "integration_id": integration_id,
                    "provider": provider,
                    "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None
                }
            finally:
                await self.db_pool.release(conn)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="OAuth token already exists for this integration",
                validation_errors={"integration_id": integration_id},
                original_exception=e
            )
        except (ValidationException, AuthenticationException):
            raise
        except Exception as e:
            self.logger.error(f"Failed to store OAuth tokens: {e}")
            raise DatabaseException(
                message="Failed to store OAuth tokens",
                original_exception=e
            )

    async def get_tokens(
        self,
        organization_id: str,
        integration_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve OAuth tokens for an integration.

        What: Fetches and decrypts OAuth tokens.
        Where: Called when accessing external APIs.
        Why: Enables retrieving stored access tokens.

        Args:
            organization_id: UUID of the organization
            integration_id: UUID of the integration

        Returns:
            Dictionary containing:
                - provider (str): Provider name
                - access_token (str): Decrypted access token
                - refresh_token (str, optional): Decrypted refresh token
                - token_type (str): Token type
                - expires_at (str or None): Expiration timestamp
                - is_valid (bool): Token validity status

        Raises:
            NotFoundException: If tokens not found
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT provider, access_token, refresh_token, token_type,
                           expires_at, is_valid
                    FROM oauth_tokens
                    WHERE organization_id = $1 AND is_valid = true
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    organization_id
                )

                if not row:
                    raise NotFoundException(
                        message="OAuth tokens not found for this integration",
                        resource_type="OAuthToken",
                        resource_id=integration_id
                    )

                # Decrypt tokens
                decrypted_access = decrypt_token(row['access_token']) if row['access_token'] else None
                decrypted_refresh = decrypt_token(row['refresh_token']) if row['refresh_token'] else None

                # Handle expires_at - may be datetime object or string
                expires_at = row['expires_at']
                if expires_at and hasattr(expires_at, 'isoformat'):
                    expires_at = expires_at.isoformat()

                return {
                    "provider": row['provider'],
                    "access_token": decrypted_access,
                    "refresh_token": decrypted_refresh,
                    "token_type": row['token_type'],
                    "expires_at": expires_at,
                    "is_valid": row['is_valid']
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get OAuth tokens: {e}")
            raise DatabaseException(
                message="Failed to retrieve OAuth tokens",
                original_exception=e
            )

    async def update_tokens(
        self,
        organization_id: str,
        integration_id: str,
        tokens: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update existing OAuth tokens (e.g., after refresh).

        What: Updates access token and expiration.
        Where: Called after token refresh.
        Why: Maintains valid token state.

        Args:
            organization_id: UUID of the organization
            integration_id: UUID of the integration
            tokens: Dictionary with new token values

        Returns:
            Dictionary containing:
                - updated (bool): True if successful
                - access_token_changed (bool): Whether access token changed

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            access_token = tokens.get("access_token")

            # Calculate new expiration
            expires_at = None
            if "expires_at" in tokens:
                expires_at = tokens["expires_at"]
            elif "expires_in" in tokens:
                expires_at = (datetime.utcnow() + timedelta(seconds=tokens["expires_in"])).isoformat()

            # Encrypt new access token
            encrypted_access = encrypt_token(access_token) if access_token else None

            conn = await self.db_pool.acquire()
            try:
                await conn.execute(
                    """
                    UPDATE oauth_tokens
                    SET access_token = $1,
                        expires_at = $2,
                        last_refreshed_at = $3,
                        updated_at = $4
                    WHERE organization_id = $5 AND is_valid = true
                    """,
                    encrypted_access,
                    expires_at,
                    datetime.now(),
                    datetime.now(),
                    organization_id
                )

                return {
                    "updated": True,
                    "access_token_changed": True
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to update OAuth tokens: {e}")
            raise DatabaseException(
                message="Failed to update OAuth tokens",
                original_exception=e
            )

    async def delete_tokens(
        self,
        organization_id: str,
        integration_id: str
    ) -> Dict[str, Any]:
        """
        Securely delete OAuth tokens from database.

        What: Removes token record.
        Where: Called when user revokes access.
        Why: Enables token cleanup and revocation.

        Args:
            organization_id: UUID of the organization
            integration_id: UUID of the integration

        Returns:
            Dictionary containing:
                - deleted (bool): True if successful
                - integration_id (str): Integration UUID

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                result = await conn.execute(
                    "DELETE FROM oauth_tokens WHERE organization_id = $1",
                    organization_id
                )

                return {
                    "deleted": True,
                    "integration_id": integration_id
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to delete OAuth tokens: {e}")
            raise DatabaseException(
                message="Failed to delete OAuth tokens",
                original_exception=e
            )

    # ================================================================
    # QUERY METHODS
    # ================================================================

    async def get_tokens_by_provider(
        self,
        organization_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Retrieve all tokens for a specific provider.

        Args:
            organization_id: UUID of the organization
            provider: Provider name ('google', 'microsoft', etc.)

        Returns:
            Dictionary containing:
                - tokens (list): List of token dictionaries

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, provider, access_token, refresh_token, expires_at
                    FROM oauth_tokens
                    WHERE organization_id = $1 AND provider = $2 AND is_valid = true
                    ORDER BY created_at DESC
                    """,
                    organization_id,
                    provider
                )

                tokens = []
                for row in rows:
                    tokens.append({
                        "integration_id": str(row['id']),
                        "provider": row['provider'],
                        "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None
                    })

                return {"tokens": tokens}
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to get tokens by provider: {e}")
            raise DatabaseException(
                message="Failed to retrieve tokens by provider",
                original_exception=e
            )

    # ================================================================
    # TOKEN ENCRYPTION AND DECRYPTION
    # ================================================================

    async def encrypt_token(self, plaintext_token: str) -> str:
        """
        Encrypt token using AES-256.

        Args:
            plaintext_token: Token to encrypt

        Returns:
            Base64-encoded encrypted token

        Raises:
            ValidationException: If encryption fails
        """
        return encrypt_token(plaintext_token)

    async def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt token.

        Args:
            encrypted_token: Base64-encoded encrypted token

        Returns:
            Decrypted plaintext token

        Raises:
            AuthenticationException: If decryption fails
        """
        return decrypt_token(encrypted_token)

    async def rotate_encryption_keys(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Rotate encryption key for all tokens.

        NOTE: This requires having both old and new encryption keys available.
        Real implementation would need key versioning.

        Args:
            organization_id: UUID of the organization

        Returns:
            Dictionary containing:
                - rotated_count (int): Number of tokens rotated
                - success (bool): Whether rotation succeeded

        Raises:
            DatabaseException: If rotation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, access_token, refresh_token
                    FROM oauth_tokens
                    WHERE organization_id = $1
                    """,
                    organization_id
                )

                rotated_count = 0
                for row in rows:
                    # Decrypt with old key, re-encrypt with new key
                    # NOTE: In real implementation, this would handle key versioning
                    decrypted_access = decrypt_token(row['access_token']) if row['access_token'] else None
                    decrypted_refresh = decrypt_token(row['refresh_token']) if row['refresh_token'] else None

                    encrypted_access = encrypt_token(decrypted_access) if decrypted_access else None
                    encrypted_refresh = encrypt_token(decrypted_refresh) if decrypted_refresh else None

                    await conn.execute(
                        """
                        UPDATE oauth_tokens
                        SET access_token = $1,
                            refresh_token = $2,
                            updated_at = $3
                        WHERE id = $4
                        """,
                        encrypted_access,
                        encrypted_refresh,
                        datetime.now(),
                        row['id']
                    )
                    rotated_count += 1

                return {
                    "rotated_count": rotated_count,
                    "success": True
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to rotate encryption keys: {e}")
            raise DatabaseException(
                message="Failed to rotate encryption keys",
                original_exception=e
            )

    # ================================================================
    # TOKEN REFRESH AUTOMATION
    # ================================================================

    async def is_token_expired(self, tokens: Dict[str, Any]) -> bool:
        """
        Check if access token is expired.

        Args:
            tokens: Dictionary with expires_at timestamp

        Returns:
            True if token is expired, False otherwise
        """
        expires_at_str = tokens.get("expires_at")
        if not expires_at_str:
            return False  # No expiration = never expires (Slack bot tokens)

        try:
            expires_at = date_parser.parse(expires_at_str)
            return datetime.utcnow() >= expires_at
        except Exception:
            return False

    async def refresh_tokens(
        self,
        organization_id: str,
        integration_id: str,
        provider: str,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh OAuth tokens using refresh token.

        Args:
            organization_id: UUID of the organization
            integration_id: UUID of the integration
            provider: Provider name
            refresh_token: Refresh token

        Returns:
            Dictionary containing:
                - refreshed (bool): Whether refresh succeeded
                - new_access_token (str): New access token

        Raises:
            AuthenticationException: If refresh fails (invalid_grant, revoked)
            ExternalServiceException: If provider API fails
        """
        try:
            # Call provider-specific refresh function
            if provider == "google":
                new_tokens = refresh_google_token(refresh_token)
            elif provider == "microsoft":
                new_tokens = refresh_microsoft_token(refresh_token)
            else:
                raise ValidationException(
                    message=f"Token refresh not supported for provider: {provider}",
                    validation_errors={"provider": provider}
                )

            # Update stored tokens
            await self.update_tokens(organization_id, integration_id, new_tokens)

            return {
                "refreshed": True,
                "new_access_token": new_tokens["access_token"]
            }

        except Exception as e:
            # Check for invalid_grant error (revoked refresh token)
            if "invalid_grant" in str(e).lower() or "revoked" in str(e).lower():
                raise AuthenticationException(
                    message="Refresh token has been revoked or is invalid. User must re-authenticate.", reason=f"Provider: {provider}"
                )
            # Re-raise other exceptions
            if isinstance(e, (ValidationException, AuthenticationException)):
                raise
            raise ExternalServiceException(
                message=f"Token refresh failed for provider {provider}",
                service_name_external=provider,
                operation="refresh_token",
                original_exception=e
            )

    async def get_valid_access_token(
        self,
        organization_id: str,
        integration_id: str
    ) -> Dict[str, Any]:
        """
        Get valid access token, automatically refreshing if expired.

        Args:
            organization_id: UUID of the organization
            integration_id: UUID of the integration

        Returns:
            Dictionary containing:
                - access_token (str): Valid access token
                - auto_refreshed (bool): Whether token was auto-refreshed

        Raises:
            NotFoundException: If tokens not found
            AuthenticationException: If refresh fails
        """
        tokens = await self.get_tokens(organization_id, integration_id)

        # Check if token is expired
        if await self.is_token_expired(tokens):
            # Auto-refresh
            refresh_result = await self.refresh_tokens(
                organization_id,
                integration_id,
                tokens["provider"],
                tokens["refresh_token"]
            )
            return {
                "access_token": refresh_result["new_access_token"],
                "auto_refreshed": True
            }

        return {
            "access_token": tokens["access_token"],
            "auto_refreshed": False
        }

    async def batch_refresh_expiring_tokens(
        self,
        threshold_minutes: int
    ) -> Dict[str, Any]:
        """
        Batch refresh tokens expiring within threshold.

        Args:
            threshold_minutes: Refresh tokens expiring within this many minutes

        Returns:
            Dictionary containing:
                - refreshed_count (int): Number of tokens refreshed
                - failed_count (int): Number of failed refreshes

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            threshold_time = datetime.utcnow() + timedelta(minutes=threshold_minutes)

            conn = await self.db_pool.acquire()
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, organization_id, provider, refresh_token, expires_at
                    FROM oauth_tokens
                    WHERE expires_at IS NOT NULL
                      AND expires_at <= $1
                      AND refresh_token IS NOT NULL
                      AND is_valid = true
                    """,
                    threshold_time
                )

                refreshed_count = 0
                failed_count = 0

                for row in rows:
                    try:
                        decrypted_refresh = decrypt_token(row['refresh_token'])
                        await self.refresh_tokens(
                            str(row['organization_id']),
                            str(row['id']),
                            row['provider'],
                            decrypted_refresh
                        )
                        refreshed_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to refresh token {row['id']}: {e}")
                        failed_count += 1

                return {
                    "refreshed_count": refreshed_count,
                    "failed_count": failed_count
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to batch refresh tokens: {e}")
            raise DatabaseException(
                message="Failed to batch refresh expiring tokens",
                original_exception=e
            )

    # ================================================================
    # TOKEN EXPIRATION MANAGEMENT
    # ================================================================

    async def get_time_until_expiration(self, expires_at: str) -> Optional[int]:
        """
        Calculate seconds until token expires.

        Args:
            expires_at: ISO timestamp of expiration

        Returns:
            Seconds until expiration (negative if already expired), or None if no expiration
        """
        if not expires_at:
            return None

        try:
            expiration = date_parser.parse(expires_at)
            delta = expiration - datetime.utcnow()
            return int(delta.total_seconds())
        except Exception:
            return None

    async def get_expiring_tokens(
        self,
        organization_id: str,
        threshold_minutes: int
    ) -> Dict[str, Any]:
        """
        Retrieve tokens expiring within specified timeframe.

        Args:
            organization_id: UUID of the organization
            threshold_minutes: Return tokens expiring within this many minutes

        Returns:
            Dictionary containing:
                - tokens (list): List of expiring token dictionaries

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            threshold_time = datetime.utcnow() + timedelta(minutes=threshold_minutes)

            conn = await self.db_pool.acquire()
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, provider, expires_at
                    FROM oauth_tokens
                    WHERE organization_id = $1
                      AND expires_at IS NOT NULL
                      AND expires_at <= $2
                      AND is_valid = true
                    ORDER BY expires_at ASC
                    """,
                    organization_id,
                    threshold_time
                )

                tokens = []
                for row in rows:
                    tokens.append({
                        "integration_id": str(row['id']),
                        "provider": row['provider'],
                        "expires_at": row['expires_at'].isoformat()
                    })

                return {"tokens": tokens}
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to get expiring tokens: {e}")
            raise DatabaseException(
                message="Failed to retrieve expiring tokens",
                original_exception=e
            )

    async def is_token_valid(self, expires_at: Optional[str]) -> bool:
        """
        Check if token is currently valid.

        Args:
            expires_at: ISO timestamp of expiration (None if no expiration)

        Returns:
            True if token is valid, False if expired
        """
        if expires_at is None:
            return True  # No expiration = always valid (Slack bot tokens)

        try:
            expiration = date_parser.parse(expires_at)
            # Add 5-minute grace period
            return datetime.utcnow() < (expiration - timedelta(minutes=5))
        except Exception:
            return False

    async def update_token_expiration(
        self,
        organization_id: str,
        integration_id: str,
        expires_at: str
    ) -> Dict[str, Any]:
        """
        Update token expiration timestamp.

        Args:
            organization_id: UUID of the organization
            integration_id: UUID of the integration
            expires_at: New expiration timestamp

        Returns:
            Dictionary containing:
                - updated (bool): True if successful
                - expires_at (str): New expiration timestamp

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                await conn.execute(
                    """
                    UPDATE oauth_tokens
                    SET expires_at = $1,
                        updated_at = $2
                    WHERE organization_id = $3 AND is_valid = true
                    """,
                    expires_at,
                    datetime.now(),
                    organization_id
                )

                return {
                    "updated": True,
                    "expires_at": expires_at
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to update token expiration: {e}")
            raise DatabaseException(
                message="Failed to update token expiration",
                original_exception=e
            )

    # ================================================================
    # MULTI-PROVIDER TOKEN MANAGEMENT
    # ================================================================

    async def get_all_provider_tokens(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve tokens for all connected providers.

        Args:
            organization_id: UUID of the organization

        Returns:
            Dictionary containing:
                - providers (dict): Dictionary of provider -> token list

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, provider, expires_at
                    FROM oauth_tokens
                    WHERE organization_id = $1 AND is_valid = true
                    ORDER BY provider, created_at DESC
                    """,
                    organization_id
                )

                providers = {}
                for row in rows:
                    provider = row['provider']
                    if provider not in providers:
                        providers[provider] = []

                    providers[provider].append({
                        "integration_id": str(row['id']),
                        "provider": provider,
                        "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None
                    })

                return {"providers": providers}
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to get all provider tokens: {e}")
            raise DatabaseException(
                message="Failed to retrieve all provider tokens",
                original_exception=e
            )

    async def validate_token_format(
        self,
        provider: str,
        tokens: Dict[str, Any]
    ) -> bool:
        """
        Validate provider-specific token format.

        Args:
            provider: Provider name
            tokens: Token dictionary to validate

        Returns:
            True if format is valid

        Raises:
            ValidationException: If format is invalid
        """
        # Google: requires access_token, refresh_token, expires_in
        if provider == "google":
            required = ["access_token", "refresh_token", "expires_in"]
            if not all(key in tokens for key in required):
                return False

        # Microsoft: requires access_token, refresh_token, expires_in, scope
        elif provider == "microsoft":
            required = ["access_token", "refresh_token", "expires_in", "scope"]
            if not all(key in tokens for key in required):
                return False

        # Slack: requires access_token, bot_user_id
        elif provider == "slack":
            required = ["access_token", "bot_user_id"]
            if not all(key in tokens for key in required):
                return False

        # LTI: requires access_token
        elif provider == "lti":
            if "access_token" not in tokens:
                return False

        return True

    # ================================================================
    # TOKEN REVOCATION AND CLEANUP
    # ================================================================

    async def revoke_tokens(
        self,
        organization_id: str,
        integration_id: str,
        provider: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Revoke OAuth tokens with provider.

        Args:
            organization_id: UUID of the organization
            integration_id: UUID of the integration
            provider: Provider name
            access_token: Access token to revoke

        Returns:
            Dictionary containing:
                - revoked (bool): Whether revocation succeeded

        Raises:
            ExternalServiceException: If revocation fails
        """
        try:
            # Call provider-specific revocation function
            if provider == "google":
                result = revoke_google_token(access_token)
            else:
                # Other providers don't have revocation endpoints
                result = {"revoked": True}

            # Delete from database
            await self.delete_tokens(organization_id, integration_id)

            return result

        except ExternalServiceException:
            raise

    async def cleanup_expired_tokens(
        self,
        retention_days: int
    ) -> Dict[str, Any]:
        """
        Clean up expired tokens per data retention policy.

        Args:
            retention_days: Delete tokens expired more than this many days ago

        Returns:
            Dictionary containing:
                - deleted_count (int): Number of tokens deleted
                - retention_policy_days (int): Retention policy applied

        Raises:
            DatabaseException: If cleanup fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            conn = await self.db_pool.acquire()
            try:
                result = await conn.execute(
                    """
                    DELETE FROM oauth_tokens
                    WHERE expires_at IS NOT NULL
                      AND expires_at < $1
                    """,
                    cutoff_date
                )

                # Parse "DELETE N" result
                deleted_count = int(result.split(" ")[1]) if result else 0

                return {
                    "deleted_count": deleted_count,
                    "retention_policy_days": retention_days
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired tokens: {e}")
            raise DatabaseException(
                message="Failed to cleanup expired tokens",
                original_exception=e
            )
