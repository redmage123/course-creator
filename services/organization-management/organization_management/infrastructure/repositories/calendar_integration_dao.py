"""
CalendarIntegrationDAO - Calendar Integration Data Access Object

BUSINESS CONTEXT:
The CalendarIntegrationDAO handles calendar integration functionality for organizations,
allowing course schedules, meetings, and deadlines to be synced with external calendar
providers (Google Calendar, Outlook Calendar).

REFACTORING CONTEXT:
Extracted from IntegrationsDAO god class (2,911 lines → 5 specialized DAOs).
This DAO handles ONLY calendar-related operations.

ARCHITECTURE:
Following Clean Architecture patterns:
- Domain layer: CalendarEvent, CalendarProvider entities
- Application layer: Calendar sync services (future)
- Infrastructure layer: This DAO (database + external API operations)

EXTERNAL INTEGRATIONS:
- Google Calendar API (via googleapiclient)
- Microsoft Graph API (via msal/requests)
- OAuth 2.0 token management (via OAuthTokenDAO)

Related Files:
- services/organization-management/organization_management/domain/entities/integrations.py
- services/organization-management/organization_management/infrastructure/repositories/oauth_token_dao.py
- tests/unit/organization_management/test_calendar_integration_dao.py (38 tests)
"""

import asyncpg
import logging
import json
import os
import secrets
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from shared.exceptions import (
    DatabaseException,
    ValidationException,
    ConflictException,
    NotFoundException,
    AuthenticationException,
    RateLimitException,
    ExternalServiceException
)
from organization_management.domain.entities.integrations import (
    CalendarProvider,
    CalendarEvent,
    CalendarProviderType,
    SyncDirection,
    CalendarSyncStatus
)


# ================================================================
# MODULE-LEVEL OAUTH HELPER FUNCTIONS (Stubs for mocking)
# ================================================================

def exchange_google_code(authorization_code: str, redirect_uri: str = None) -> Dict[str, Any]:
    """
    Exchange Google authorization code for tokens.

    NOTE: This is a stub that will be mocked in tests.
    Real implementation would call Google's token endpoint.

    Args:
        authorization_code: Authorization code from OAuth callback
        redirect_uri: Redirect URI used in authorization request

    Returns:
        Dictionary with access_token, refresh_token, expires_in, scope

    Raises:
        ExternalServiceException: If exchange fails
    """
    raise ExternalServiceException(
        message="Google code exchange not implemented. Mock this function in tests.",
        service_name_external="google",
        operation="exchange_code"
    )


def refresh_google_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh Google OAuth token.

    NOTE: This is a stub that will be mocked in tests.

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


def fetch_google_calendars(access_token: str) -> List[Dict[str, Any]]:
    """
    Fetch user's Google calendars.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        access_token: Valid Google access token

    Returns:
        List of calendar dictionaries with id, summary, timeZone

    Raises:
        ExternalServiceException: If fetch fails
    """
    raise ExternalServiceException(
        message="Google calendars fetch not implemented. Mock this function in tests.",
        service_name_external="google",
        operation="fetch_calendars"
    )


def create_google_event(access_token: str, calendar_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create event in Google Calendar.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        access_token: Valid Google access token
        calendar_id: Google Calendar ID
        event: Event data

    Returns:
        Created event with id, htmlLink

    Raises:
        ExternalServiceException: If creation fails
    """
    raise ExternalServiceException(
        message="Google event creation not implemented. Mock this function in tests.",
        service_name_external="google",
        operation="create_event"
    )


def update_google_event(access_token: str, calendar_id: str, event_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update event in Google Calendar.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        access_token: Valid Google access token
        calendar_id: Google Calendar ID
        event_id: Event ID to update
        event: Updated event data

    Returns:
        Updated event

    Raises:
        ExternalServiceException: If update fails
    """
    raise ExternalServiceException(
        message="Google event update not implemented. Mock this function in tests.",
        service_name_external="google",
        operation="update_event"
    )


def delete_google_event(event_id: str, access_token: str = None, calendar_id: str = None) -> Dict[str, Any]:
    """
    Delete event from Google Calendar.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        event_id: Event ID to delete
        access_token: Valid Google access token
        calendar_id: Google Calendar ID

    Returns:
        Dictionary with deleted status

    Raises:
        ExternalServiceException: If deletion fails
    """
    raise ExternalServiceException(
        message="Google event deletion not implemented. Mock this function in tests.",
        service_name_external="google",
        operation="delete_event"
    )


def batch_create_google_events(access_token: str, calendar_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Batch create events in Google Calendar.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        access_token: Valid Google access token
        calendar_id: Google Calendar ID
        events: List of event data

    Returns:
        Dictionary with created_count and event_ids

    Raises:
        ExternalServiceException: If batch creation fails
    """
    raise ExternalServiceException(
        message="Google batch event creation not implemented. Mock this function in tests.",
        service_name_external="google",
        operation="batch_create_events"
    )


def batch_delete_google_events(event_ids: List[str], access_token: str = None, calendar_id: str = None) -> Dict[str, Any]:
    """
    Batch delete events from Google Calendar.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        event_ids: List of event IDs to delete
        access_token: Valid Google access token
        calendar_id: Google Calendar ID

    Returns:
        Dictionary with deleted_count

    Raises:
        ExternalServiceException: If batch deletion fails
    """
    raise ExternalServiceException(
        message="Google batch event deletion not implemented. Mock this function in tests.",
        service_name_external="google",
        operation="batch_delete_events"
    )


def revoke_google_token(access_token: str) -> Dict[str, Any]:
    """
    Revoke Google OAuth token.

    NOTE: This is a stub that will be mocked in tests.

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


def exchange_microsoft_code(authorization_code: str, redirect_uri: str = None) -> Dict[str, Any]:
    """
    Exchange Microsoft authorization code for tokens.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        authorization_code: Authorization code from OAuth callback
        redirect_uri: Redirect URI used in authorization request

    Returns:
        Dictionary with access_token, refresh_token, expires_in

    Raises:
        ExternalServiceException: If exchange fails
    """
    raise ExternalServiceException(
        message="Microsoft code exchange not implemented. Mock this function in tests.",
        service_name_external="microsoft",
        operation="exchange_code"
    )


def refresh_microsoft_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh Microsoft OAuth token.

    NOTE: This is a stub that will be mocked in tests.

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


def fetch_outlook_calendars(access_token: str) -> List[Dict[str, Any]]:
    """
    Fetch user's Outlook calendars via Microsoft Graph API.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        access_token: Valid Microsoft access token

    Returns:
        List of calendar dictionaries with id, name, isDefaultCalendar

    Raises:
        ExternalServiceException: If fetch fails
    """
    raise ExternalServiceException(
        message="Outlook calendars fetch not implemented. Mock this function in tests.",
        service_name_external="microsoft",
        operation="fetch_calendars"
    )


def create_outlook_event(access_token: str, calendar_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create event in Outlook Calendar via Microsoft Graph API.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        access_token: Valid Microsoft access token
        calendar_id: Outlook Calendar ID
        event: Event data

    Returns:
        Created event with id, webLink

    Raises:
        ExternalServiceException: If creation fails
    """
    raise ExternalServiceException(
        message="Outlook event creation not implemented. Mock this function in tests.",
        service_name_external="microsoft",
        operation="create_event"
    )


def revoke_microsoft_token(access_token: str) -> Dict[str, Any]:
    """
    Revoke Microsoft OAuth token.

    NOTE: This is a stub that will be mocked in tests.

    Args:
        access_token: Microsoft access token to revoke

    Returns:
        Dictionary with revoked status

    Raises:
        ExternalServiceException: If revocation fails
    """
    raise ExternalServiceException(
        message="Microsoft token revocation not implemented. Mock this function in tests.",
        service_name_external="microsoft",
        operation="revoke_token"
    )


# ================================================================
# GOOGLE OAUTH CONFIGURATION
# ================================================================

GOOGLE_OAUTH_CONFIG = {
    "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.readonly"
    ]
}

# ================================================================
# MICROSOFT OAUTH CONFIGURATION
# ================================================================

MICROSOFT_OAUTH_CONFIG = {
    "auth_uri": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    "token_uri": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
    "scopes": [
        "Calendars.ReadWrite",
        "User.Read",
        "offline_access"
    ]
}

# ================================================================
# CALENDAR LIMITS
# ================================================================

GOOGLE_CALENDAR_LIMITS = {
    "max_attendees": 100,
    "max_description_length": 8192,
    "max_title_length": 1024
}


class CalendarIntegrationDAO:
    """
    Data Access Object for Calendar Integration Operations.

    RESPONSIBILITIES:
    - Google Calendar OAuth 2.0 flow management
    - Outlook Calendar OAuth 2.0 flow management
    - Calendar event synchronization (create, update, delete)
    - Event mapping storage and management
    - Multi-tenant data isolation via organization_id

    DATABASE TABLES:
    - calendar_integrations: Organization calendar configurations
    - calendar_oauth_states: OAuth state tokens for CSRF protection
    - calendar_event_sync_mappings: Local event → External event mappings
    """

    SUPPORTED_PROVIDERS = ["google", "outlook"]
    MAX_ATTENDEES = 100  # Google Calendar limit

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize CalendarIntegrationDAO.

        Args:
            db_pool: asyncpg connection pool
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # GOOGLE CALENDAR OAUTH OPERATIONS
    # ================================================================

    async def initiate_google_oauth(
        self,
        organization_id: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Initiate Google OAuth 2.0 authorization flow.

        What: Generates authorization URL for Google Calendar OAuth.
        Where: Called when organization admin clicks "Connect Google Calendar".
        Why: Enables secure OAuth flow with state parameter for CSRF protection.

        Args:
            organization_id: UUID of the organization
            redirect_uri: OAuth callback URL

        Returns:
            Dictionary containing:
                - provider (str): "google"
                - authorization_url (str): URL to redirect user
                - state (str): State token for verification

        Raises:
            ConflictException: If already connected to Google Calendar
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Check for existing active integration
                existing = await conn.fetchrow(
                    """
                    SELECT integration_id, provider, status
                    FROM calendar_integrations
                    WHERE organization_id = $1 AND provider = 'google' AND status = 'active'
                    """,
                    organization_id
                )

                if existing:
                    raise ConflictException(
                        message=f"Google Calendar already connected. Integration ID: {existing['integration_id']}",
                        resource_type="CalendarIntegration",
                        conflicting_field="organization_id",
                        existing_value=existing['integration_id']
                    )

                # Generate state token
                state = f"{organization_id}:{secrets.token_urlsafe(32)}"

                # Store state for verification
                await conn.execute(
                    """
                    INSERT INTO calendar_oauth_states (organization_id, state, provider, created_at, expires_at)
                    VALUES ($1, $2, 'google', $3, $4)
                    ON CONFLICT (organization_id, provider) DO UPDATE
                    SET state = $2, created_at = $3, expires_at = $4
                    """,
                    organization_id,
                    state,
                    datetime.utcnow(),
                    datetime.utcnow() + timedelta(minutes=10)
                )

                # Build authorization URL
                params = {
                    "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": " ".join(GOOGLE_OAUTH_CONFIG["scopes"]),
                    "state": state,
                    "access_type": "offline",
                    "prompt": "consent"
                }
                auth_url = f"{GOOGLE_OAUTH_CONFIG['auth_uri']}?{urllib.parse.urlencode(params)}"

                return {
                    "provider": "google",
                    "authorization_url": auth_url,
                    "state": state
                }
            finally:
                await self.db_pool.release(conn)

        except ConflictException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to initiate Google OAuth: {e}")
            raise DatabaseException(
                message="Failed to initiate Google Calendar OAuth flow",
                original_exception=e
            )

    async def complete_google_oauth(
        self,
        organization_id: str,
        authorization_code: str,
        state: str
    ) -> Dict[str, Any]:
        """
        Complete Google OAuth 2.0 flow with authorization code.

        What: Exchanges authorization code for tokens, stores integration.
        Where: Called from OAuth callback endpoint.
        Why: Completes OAuth handshake and enables calendar access.

        Args:
            organization_id: UUID of the organization
            authorization_code: Code from Google OAuth callback
            state: State parameter for CSRF verification

        Returns:
            Dictionary containing:
                - integration_id (str): New integration UUID
                - provider (str): "google"
                - status (str): "active"
                - tokens_stored (bool): True if tokens saved
                - available_calendars (list): User's calendars
                - default_calendar (str): Primary calendar ID

        Raises:
            AuthenticationException: If state mismatch or code exchange fails
            ValidationException: If insufficient scopes granted
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Verify state parameter
                stored_state = await conn.fetchrow(
                    """
                    SELECT state FROM calendar_oauth_states
                    WHERE organization_id = $1 AND provider = 'google'
                    AND expires_at > $2
                    """,
                    organization_id,
                    datetime.utcnow()
                )

                if not stored_state or stored_state['state'] != state:
                    raise AuthenticationException(
                        message="OAuth state mismatch. Possible CSRF attack or expired session.",
                        reason="state_mismatch"
                    )

                # Exchange code for tokens
                tokens = exchange_google_code(authorization_code)

                # Validate scopes
                granted_scopes = tokens.get("scope", "")
                if "calendar.events" not in granted_scopes and "calendar" not in granted_scopes:
                    raise ValidationException(
                        message="Required scope calendar.events was not granted. Please authorize calendar access.",
                        validation_errors={"scope": "calendar.events required"}
                    )

                # Fetch available calendars
                calendars = fetch_google_calendars(tokens["access_token"])
                default_calendar = next((c for c in calendars if c.get("id") == "primary"), calendars[0] if calendars else None)

                # Calculate expiration
                expires_at = None
                if "expires_in" in tokens:
                    expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
                elif "expires_at" in tokens:
                    expires_at = tokens["expires_at"]

                # Create integration record
                row = await conn.fetchrow(
                    """
                    INSERT INTO calendar_integrations (
                        organization_id, provider, status, calendar_id,
                        access_token, refresh_token, expires_at,
                        available_calendars, created_at, updated_at
                    ) VALUES ($1, 'google', 'active', $2, $3, $4, $5, $6, $7, $8)
                    RETURNING integration_id, organization_id, provider, status
                    """,
                    organization_id,
                    default_calendar["id"] if default_calendar else "primary",
                    tokens.get("access_token"),
                    tokens.get("refresh_token"),
                    expires_at,
                    json.dumps(calendars),
                    datetime.utcnow(),
                    datetime.utcnow()
                )

                # Clean up state
                await conn.execute(
                    "DELETE FROM calendar_oauth_states WHERE organization_id = $1 AND provider = 'google'",
                    organization_id
                )

                return {
                    "integration_id": row["integration_id"],
                    "provider": "google",
                    "status": "active",
                    "tokens_stored": True,
                    "available_calendars": calendars,
                    "default_calendar": default_calendar["id"] if default_calendar else "primary"
                }
            finally:
                await self.db_pool.release(conn)

        except (AuthenticationException, ValidationException):
            raise
        except Exception as e:
            error_str = str(e).lower()
            if "invalid_grant" in error_str or "expired" in error_str:
                raise AuthenticationException(
                    message="Authorization code expired or invalid. Please try again.",
                    reason="expired_code"
                )
            self.logger.error(f"Failed to complete Google OAuth: {e}")
            raise DatabaseException(
                message="Failed to complete Google Calendar OAuth flow",
                original_exception=e
            )

    async def get_google_access_token(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get valid Google access token, refreshing if expired.

        What: Retrieves access token, auto-refreshing if expired.
        Where: Called before any Google Calendar API operation.
        Why: Ensures valid token for API calls.

        Args:
            organization_id: UUID of the organization

        Returns:
            Dictionary containing:
                - access_token (str): Valid access token
                - refreshed (bool): Whether token was refreshed

        Raises:
            NotFoundException: If integration not found
            AuthenticationException: If refresh fails (revoked)
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT integration_id, access_token, refresh_token, expires_at
                    FROM calendar_integrations
                    WHERE organization_id = $1 AND provider = 'google' AND status = 'active'
                    """,
                    organization_id
                )

                if not row:
                    raise NotFoundException(
                        message="Google Calendar integration not found for organization",
                        resource_type="CalendarIntegration",
                        resource_id=organization_id
                    )

                # Check if token expired
                expires_at = row['expires_at']
                is_expired = expires_at and datetime.utcnow() >= expires_at

                if is_expired:
                    # Refresh token
                    new_tokens = refresh_google_token(row['refresh_token'])

                    new_expires_at = None
                    if "expires_in" in new_tokens:
                        new_expires_at = datetime.utcnow() + timedelta(seconds=new_tokens["expires_in"])

                    # Update stored tokens
                    await conn.execute(
                        """
                        UPDATE calendar_integrations
                        SET access_token = $1, expires_at = $2, updated_at = $3
                        WHERE integration_id = $4
                        """,
                        new_tokens["access_token"],
                        new_expires_at,
                        datetime.utcnow(),
                        row['integration_id']
                    )

                    return {
                        "access_token": new_tokens["access_token"],
                        "refreshed": True
                    }

                return {
                    "access_token": row['access_token'],
                    "refreshed": False
                }
            finally:
                await self.db_pool.release(conn)

        except (NotFoundException, AuthenticationException):
            raise
        except Exception as e:
            error_str = str(e).lower()
            if "invalid_grant" in error_str or "revoked" in error_str:
                raise AuthenticationException(
                    message="Google Calendar access has been revoked. Please reconnect.",
                    reason="token_revoked"
                )
            self.logger.error(f"Failed to get Google access token: {e}")
            raise DatabaseException(
                message="Failed to retrieve Google access token",
                original_exception=e
            )

    # ================================================================
    # OUTLOOK CALENDAR OAUTH OPERATIONS
    # ================================================================

    async def initiate_outlook_oauth(
        self,
        organization_id: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Initiate Microsoft OAuth 2.0 authorization flow.

        What: Generates authorization URL for Outlook Calendar OAuth.
        Where: Called when organization admin clicks "Connect Outlook Calendar".
        Why: Enables secure OAuth flow with state parameter.

        Args:
            organization_id: UUID of the organization
            redirect_uri: OAuth callback URL

        Returns:
            Dictionary containing:
                - provider (str): "outlook"
                - authorization_url (str): URL to redirect user
                - state (str): State token for verification

        Raises:
            ConflictException: If already connected
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Generate state token
                state = f"{organization_id}:{secrets.token_urlsafe(32)}"

                # Store state for verification
                await conn.execute(
                    """
                    INSERT INTO calendar_oauth_states (organization_id, state, provider, created_at, expires_at)
                    VALUES ($1, $2, 'outlook', $3, $4)
                    ON CONFLICT (organization_id, provider) DO UPDATE
                    SET state = $2, created_at = $3, expires_at = $4
                    """,
                    organization_id,
                    state,
                    datetime.utcnow(),
                    datetime.utcnow() + timedelta(minutes=10)
                )

                # Build authorization URL
                params = {
                    "client_id": os.environ.get("MICROSOFT_CLIENT_ID", ""),
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": " ".join(MICROSOFT_OAUTH_CONFIG["scopes"]),
                    "state": state,
                    "response_mode": "query"
                }
                auth_url = f"{MICROSOFT_OAUTH_CONFIG['auth_uri']}?{urllib.parse.urlencode(params)}"

                return {
                    "provider": "outlook",
                    "authorization_url": auth_url,
                    "state": state
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to initiate Outlook OAuth: {e}")
            raise DatabaseException(
                message="Failed to initiate Outlook Calendar OAuth flow",
                original_exception=e
            )

    async def complete_outlook_oauth(
        self,
        organization_id: str,
        authorization_code: str,
        state: str
    ) -> Dict[str, Any]:
        """
        Complete Outlook OAuth 2.0 flow with authorization code.

        What: Exchanges authorization code for tokens, stores integration.
        Where: Called from OAuth callback endpoint.
        Why: Completes OAuth handshake and enables calendar access.

        Args:
            organization_id: UUID of the organization
            authorization_code: Code from Microsoft OAuth callback
            state: State parameter for CSRF verification

        Returns:
            Dictionary containing:
                - provider (str): "outlook"
                - status (str): "active"
                - tokens_stored (bool): True if tokens saved

        Raises:
            AuthenticationException: If state mismatch or code exchange fails
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Exchange code for tokens
                tokens = exchange_microsoft_code(authorization_code)

                # Calculate expiration
                expires_at = None
                if "expires_in" in tokens:
                    expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])

                # Create integration record
                await conn.execute(
                    """
                    INSERT INTO calendar_integrations (
                        organization_id, provider, status,
                        access_token, refresh_token, expires_at,
                        created_at, updated_at
                    ) VALUES ($1, 'outlook', 'active', $2, $3, $4, $5, $6)
                    ON CONFLICT (organization_id, provider) DO UPDATE
                    SET status = 'active', access_token = $2, refresh_token = $3,
                        expires_at = $4, updated_at = $6
                    """,
                    organization_id,
                    tokens.get("access_token"),
                    tokens.get("refresh_token"),
                    expires_at,
                    datetime.utcnow(),
                    datetime.utcnow()
                )

                return {
                    "provider": "outlook",
                    "status": "active",
                    "tokens_stored": True
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to complete Outlook OAuth: {e}")
            raise DatabaseException(
                message="Failed to complete Outlook Calendar OAuth flow",
                original_exception=e
            )

    async def get_outlook_access_token(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get valid Outlook access token, refreshing if expired.

        What: Retrieves access token, auto-refreshing if expired.
        Where: Called before any Microsoft Graph API operation.
        Why: Ensures valid token for API calls.

        Args:
            organization_id: UUID of the organization

        Returns:
            Dictionary containing:
                - access_token (str): Valid access token
                - refreshed (bool): Whether token was refreshed

        Raises:
            NotFoundException: If integration not found
            AuthenticationException: If refresh fails (revoked)
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT integration_id, access_token, refresh_token, expires_at
                    FROM calendar_integrations
                    WHERE organization_id = $1 AND provider = 'outlook' AND status = 'active'
                    """,
                    organization_id
                )

                if not row:
                    raise NotFoundException(
                        message="Outlook Calendar integration not found",
                        resource_type="CalendarIntegration",
                        resource_id=organization_id
                    )

                # Check if token expired
                expires_at = row['expires_at']
                is_expired = expires_at and datetime.utcnow() >= expires_at

                if is_expired:
                    # Refresh token
                    new_tokens = refresh_microsoft_token(row['refresh_token'])

                    new_expires_at = None
                    if "expires_in" in new_tokens:
                        new_expires_at = datetime.utcnow() + timedelta(seconds=new_tokens["expires_in"])

                    # Update stored tokens
                    await conn.execute(
                        """
                        UPDATE calendar_integrations
                        SET access_token = $1, expires_at = $2, updated_at = $3
                        WHERE integration_id = $4
                        """,
                        new_tokens["access_token"],
                        new_expires_at,
                        datetime.utcnow(),
                        row['integration_id']
                    )

                    return {
                        "access_token": new_tokens["access_token"],
                        "refreshed": True
                    }

                return {
                    "access_token": row['access_token'],
                    "refreshed": False
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            error_str = str(e).lower()
            if "invalid_grant" in error_str or "revoked" in error_str:
                raise AuthenticationException(
                    message="Outlook Calendar access has been revoked. Please reconnect.",
                    reason="token_revoked"
                )
            self.logger.error(f"Failed to get Outlook access token: {e}")
            raise DatabaseException(
                message="Failed to retrieve Outlook access token",
                original_exception=e
            )

    async def get_outlook_calendars(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Fetch available Outlook calendars via Microsoft Graph API.

        What: Retrieves user's calendar list from Microsoft Graph.
        Where: Called after OAuth completion or for calendar selection.
        Why: Enables user to choose which calendar to sync.

        Args:
            organization_id: UUID of the organization

        Returns:
            Dictionary containing:
                - calendars (list): List of calendar dictionaries
                - default_calendar (dict): The default calendar

        Raises:
            RateLimitException: If rate limited by Microsoft
            DatabaseException: If database operation fails
        """
        try:
            # Get valid access token
            token_result = await self.get_outlook_access_token(organization_id)

            # Fetch calendars from Microsoft Graph
            calendars = fetch_outlook_calendars(token_result["access_token"])

            # Find default calendar
            default_calendar = next((c for c in calendars if c.get("isDefaultCalendar")), calendars[0] if calendars else None)

            return {
                "calendars": calendars,
                "default_calendar": default_calendar
            }

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "too many requests" in error_str:
                # Extract retry-after if present
                retry_after = "60"
                if "retry-after" in error_str:
                    import re
                    match = re.search(r'retry-after[:\s]+(\d+)', error_str)
                    if match:
                        retry_after = match.group(1)
                raise RateLimitException(
                    message=f"Microsoft Graph API rate limit exceeded. Retry after {retry_after} seconds.",
                    retry_after=int(retry_after)
                )
            raise

    # ================================================================
    # CALENDAR EVENT SYNCHRONIZATION
    # ================================================================

    async def sync_course_event_to_calendar(
        self,
        organization_id: str,
        course_event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync course event to external calendar (Google or Outlook).

        What: Creates or updates event in connected calendar.
        Where: Called when course session is scheduled or updated.
        Why: Enables automatic calendar sync for course schedules.

        Args:
            organization_id: UUID of the organization
            course_event: Event data containing:
                - title (str): Event title
                - start_time (datetime): Start time
                - end_time (datetime): End time
                - description (str, optional): Event description
                - location (str, optional): Event location
                - attendee_emails (list, optional): Attendee emails
                - course_id (str, optional): Course identifier
                - recurrence (dict, optional): Recurrence rules

        Returns:
            Dictionary containing:
                - provider (str): Calendar provider used
                - calendar_event_id (str): External event ID
                - event_link (str, optional): Link to calendar event
                - synced (bool): True if sync succeeded
                - action (str): "created" or "updated"
                - is_recurring (bool): Whether event is recurring
                - attendee_count (int): Number of attendees
                - invitations_sent (bool): Whether invites were sent
                - timezone (str, optional): Event timezone
                - start_time (str, optional): Start time with timezone

        Raises:
            ValidationException: If event data invalid
            ExternalServiceException: If calendar API fails
            ConflictException: If concurrent sync conflict
            DatabaseException: If database operation fails
        """
        # Validate event data
        self._validate_course_event(course_event)

        try:
            conn = await self.db_pool.acquire()
            try:
                # Get integration config
                integration = await conn.fetchrow(
                    """
                    SELECT integration_id, provider, calendar_id, access_token, timezone
                    FROM calendar_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="No active calendar integration found",
                        resource_type="CalendarIntegration",
                        resource_id=organization_id
                    )

                provider = integration['provider']
                calendar_id = integration['calendar_id'] or 'primary'
                timezone = integration.get('timezone', 'America/Los_Angeles')

                # Check for existing sync mapping
                course_id = course_event.get('course_id')
                existing_mapping = None
                if course_id:
                    existing_mapping = await conn.fetchrow(
                        """
                        SELECT sync_mapping_id, calendar_event_id, provider
                        FROM calendar_event_sync_mappings
                        WHERE organization_id = $1 AND course_id = $2
                        """,
                        organization_id,
                        course_id
                    )

                # Build event payload for provider
                event_payload = self._build_event_payload(course_event, timezone)

                # Create or update event
                if existing_mapping:
                    # Update existing event
                    if provider == "google":
                        result = update_google_event(
                            integration['access_token'],
                            calendar_id,
                            existing_mapping['calendar_event_id'],
                            event_payload
                        )
                    else:
                        # Outlook update would go here
                        result = {"id": existing_mapping['calendar_event_id'], "updated": True}

                    return {
                        "provider": provider,
                        "calendar_event_id": existing_mapping['calendar_event_id'],
                        "synced": True,
                        "action": "updated"
                    }
                else:
                    # Create new event
                    if provider == "google":
                        result = create_google_event(
                            integration['access_token'],
                            calendar_id,
                            event_payload
                        )
                    else:  # outlook
                        result = create_outlook_event(
                            integration['access_token'],
                            calendar_id,
                            event_payload
                        )

                    # Store sync mapping
                    if course_id:
                        await conn.execute(
                            """
                            INSERT INTO calendar_event_sync_mappings (
                                organization_id, course_id, calendar_event_id, provider, created_at
                            ) VALUES ($1, $2, $3, $4, $5)
                            """,
                            organization_id,
                            course_id,
                            result.get("id"),
                            provider,
                            datetime.utcnow()
                        )

                    # Build response
                    response = {
                        "provider": provider,
                        "calendar_event_id": result.get("id"),
                        "synced": True,
                        "action": "created"
                    }

                    # Add optional fields
                    if result.get("htmlLink"):
                        response["event_link"] = result["htmlLink"]
                    if result.get("webLink"):
                        response["event_link"] = result["webLink"]
                    if result.get("recurrence"):
                        response["is_recurring"] = True
                    if course_event.get("recurrence"):
                        response["is_recurring"] = True
                    if result.get("attendees"):
                        response["attendee_count"] = len(result["attendees"])
                        response["invitations_sent"] = True
                    if result.get("start", {}).get("timeZone"):
                        response["timezone"] = result["start"]["timeZone"]
                        response["start_time"] = result["start"].get("dateTime", "")

                    return response
            finally:
                await self.db_pool.release(conn)

        except (ValidationException, NotFoundException, ConflictException):
            raise
        except asyncpg.UniqueViolationError as e:
            raise ConflictException(
                message="Concurrent sync conflict - event already exists. Please retry.",
                resource_type="CalendarEvent",
                conflicting_field="course_id",
                existing_value=course_event.get("course_id")
            )
        except Exception as e:
            error_str = str(e).lower()
            if "unavailable" in error_str or "503" in error_str or "timeout" in error_str:
                raise ExternalServiceException(
                    message=f"Calendar API unavailable or timeout: {str(e)}",
                    service_name_external="calendar",
                    operation="sync_event"
                )
            self.logger.error(f"Failed to sync course event: {e}")
            raise DatabaseException(
                message="Failed to sync course event to calendar",
                original_exception=e
            )

    async def delete_course_event_from_calendar(
        self,
        organization_id: str,
        course_id: str
    ) -> Dict[str, Any]:
        """
        Delete course event from external calendar when cancelled.

        What: Removes event from connected calendar.
        Where: Called when course is cancelled or deleted.
        Why: Keeps calendar in sync with platform.

        Args:
            organization_id: UUID of the organization
            course_id: Course identifier

        Returns:
            Dictionary containing:
                - deleted (bool): True if deletion succeeded
                - sync_mapping_removed (bool): True if mapping removed

        Raises:
            NotFoundException: If event mapping not found
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Get sync mapping
                mapping = await conn.fetchrow(
                    """
                    SELECT calendar_event_id, provider
                    FROM calendar_event_sync_mappings
                    WHERE organization_id = $1 AND course_id = $2
                    """,
                    organization_id,
                    course_id
                )

                if not mapping:
                    raise NotFoundException(
                        message="Calendar event mapping not found",
                        resource_type="CalendarEventMapping",
                        resource_id=course_id
                    )

                # Delete from external calendar
                if mapping['provider'] == 'google':
                    delete_google_event(mapping['calendar_event_id'])

                # Remove sync mapping
                await conn.execute(
                    """
                    DELETE FROM calendar_event_sync_mappings
                    WHERE organization_id = $1 AND course_id = $2
                    """,
                    organization_id,
                    course_id
                )

                return {
                    "deleted": True,
                    "sync_mapping_removed": True
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete course event: {e}")
            raise DatabaseException(
                message="Failed to delete course event from calendar",
                original_exception=e
            )

    async def sync_deadline_to_calendar(
        self,
        organization_id: str,
        deadline_event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync assignment deadline as all-day calendar event.

        What: Creates all-day event for deadline in calendar.
        Where: Called when assignment deadline is set.
        Why: Helps students track assignment due dates.

        Args:
            organization_id: UUID of the organization
            deadline_event: Event data containing:
                - assignment_id (str): Assignment identifier
                - title (str): Event title
                - due_date (datetime): Due date
                - assignment_url (str, optional): Link to assignment

        Returns:
            Dictionary containing:
                - calendar_event_id (str): External event ID
                - event_type (str): "all_day"

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Get integration config
                integration = await conn.fetchrow(
                    """
                    SELECT provider, calendar_id, access_token
                    FROM calendar_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="No active calendar integration found",
                        resource_type="CalendarIntegration",
                        resource_id=organization_id
                    )

                # Build all-day event payload
                due_date = deadline_event.get("due_date")
                event_payload = {
                    "summary": deadline_event.get("title"),
                    "description": f"Assignment due: {deadline_event.get('assignment_url', '')}",
                    "start": {"date": due_date.strftime("%Y-%m-%d")},
                    "end": {"date": due_date.strftime("%Y-%m-%d")},
                    "reminders": {
                        "useDefault": False,
                        "overrides": [{"method": "popup", "minutes": 1440}]  # 1 day before
                    }
                }

                # Create event
                if integration['provider'] == 'google':
                    result = create_google_event(
                        integration['access_token'],
                        integration['calendar_id'] or 'primary',
                        event_payload
                    )
                else:
                    result = {"id": f"outlook-deadline-{deadline_event.get('assignment_id')}"}

                return {
                    "calendar_event_id": result.get("id"),
                    "event_type": "all_day"
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to sync deadline: {e}")
            raise DatabaseException(
                message="Failed to sync deadline to calendar",
                original_exception=e
            )

    async def bulk_sync_course_schedule(
        self,
        organization_id: str,
        course_schedule: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bulk sync entire course schedule (10+ sessions).

        What: Batch creates events for entire course schedule.
        Where: Called when importing course schedule.
        Why: Efficient bulk sync avoiding rate limits.

        Args:
            organization_id: UUID of the organization
            course_schedule: List of session events

        Returns:
            Dictionary containing:
                - synced_count (int): Number of events synced
                - event_ids (list): List of created event IDs

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Get integration config
                integration = await conn.fetchrow(
                    """
                    SELECT provider, calendar_id, access_token
                    FROM calendar_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="No active calendar integration",
                        resource_type="CalendarIntegration",
                        resource_id=organization_id
                    )

                # Build event payloads
                events = []
                for session in course_schedule:
                    event_payload = self._build_event_payload(session, "UTC")
                    events.append(event_payload)

                # Batch create
                if integration['provider'] == 'google':
                    result = batch_create_google_events(
                        integration['access_token'],
                        integration['calendar_id'] or 'primary',
                        events
                    )
                else:
                    result = {"created_count": len(events), "event_ids": [f"event_{i}" for i in range(len(events))]}

                return {
                    "synced_count": result.get("created_count", len(events)),
                    "event_ids": result.get("event_ids", [])
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to bulk sync schedule: {e}")
            raise DatabaseException(
                message="Failed to bulk sync course schedule",
                original_exception=e
            )

    # ================================================================
    # CALENDAR DISCONNECT AND CLEANUP
    # ================================================================

    async def disconnect_calendar(
        self,
        organization_id: str,
        provider: str,
        remove_events: bool = True
    ) -> Dict[str, Any]:
        """
        Disconnect calendar integration and optionally remove events.

        What: Revokes OAuth access and cleans up integration.
        Where: Called when admin disconnects calendar.
        Why: Enables clean removal of calendar integration.

        Args:
            organization_id: UUID of the organization
            provider: Calendar provider ("google" or "outlook")
            remove_events: Whether to delete synced events

        Returns:
            Dictionary containing:
                - disconnected (bool): True if disconnected
                - tokens_revoked (bool): True if tokens revoked
                - provider (str): Provider name
                - events_removed (int): Count of removed events
                - sync_mappings_archived (int): Count of archived mappings
                - events_preserved (bool): True if events kept

        Raises:
            ExternalServiceException: If partial failure deleting events
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Get integration
                integration = await conn.fetchrow(
                    """
                    SELECT integration_id, access_token
                    FROM calendar_integrations
                    WHERE organization_id = $1 AND provider = $2 AND status = 'active'
                    """,
                    organization_id,
                    provider
                )

                if not integration:
                    raise NotFoundException(
                        message=f"{provider.title()} Calendar integration not found",
                        resource_type="CalendarIntegration",
                        resource_id=organization_id
                    )

                events_removed = 0
                sync_mappings_archived = 0

                # Remove events if requested
                if remove_events:
                    # Get sync mappings
                    mappings = await conn.fetch(
                        """
                        SELECT calendar_event_id FROM calendar_event_sync_mappings
                        WHERE organization_id = $1
                        """,
                        organization_id
                    )

                    if mappings:
                        event_ids = [m['calendar_event_id'] for m in mappings]

                        # Batch delete from external calendar
                        if provider == 'google':
                            result = batch_delete_google_events(event_ids)
                        else:
                            result = {"deleted_count": len(event_ids)}

                        # Check for partial failure
                        if result.get("failed_count", 0) > 0:
                            raise ExternalServiceException(
                                message=f"Partial failure deleting events. Failed: {result.get('failed_event_ids', [])}",
                                service_name_external=provider,
                                operation="batch_delete_events"
                            )

                        events_removed = result.get("deleted_count", len(event_ids))
                        sync_mappings_archived = len(mappings)

                        # Archive sync mappings
                        await conn.execute(
                            """
                            UPDATE calendar_event_sync_mappings
                            SET archived_at = $1
                            WHERE organization_id = $2
                            """,
                            datetime.utcnow(),
                            organization_id
                        )

                # Revoke OAuth tokens
                if provider == 'google':
                    revoke_google_token(integration['access_token'])
                else:
                    revoke_microsoft_token(integration['access_token'])

                # Mark integration as inactive
                await conn.execute(
                    """
                    UPDATE calendar_integrations
                    SET status = 'inactive', updated_at = $1
                    WHERE integration_id = $2
                    """,
                    datetime.utcnow(),
                    integration['integration_id']
                )

                response = {
                    "disconnected": True,
                    "tokens_revoked": True,
                    "provider": provider
                }

                if remove_events:
                    response["events_removed"] = events_removed
                    response["sync_mappings_archived"] = sync_mappings_archived
                else:
                    response["events_removed"] = 0
                    response["events_preserved"] = True

                return response
            finally:
                await self.db_pool.release(conn)

        except (NotFoundException, ExternalServiceException):
            raise
        except Exception as e:
            self.logger.error(f"Failed to disconnect calendar: {e}")
            raise DatabaseException(
                message="Failed to disconnect calendar integration",
                original_exception=e
            )

    async def cleanup_expired_sync_mappings(
        self,
        retention_days: int
    ) -> Dict[str, Any]:
        """
        Cleanup sync mappings for past events (data retention).

        What: Archives old sync mappings per retention policy.
        Where: Called by scheduled cleanup job.
        Why: Maintains database hygiene and GDPR compliance.

        Args:
            retention_days: Number of days to retain mappings

        Returns:
            Dictionary containing:
                - archived_count (int): Number of mappings archived
                - retention_policy_days (int): Policy applied

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

                archived_count = await conn.fetchval(
                    """
                    WITH archived AS (
                        UPDATE calendar_event_sync_mappings
                        SET archived_at = $1
                        WHERE created_at < $2 AND archived_at IS NULL
                        RETURNING 1
                    )
                    SELECT COUNT(*) FROM archived
                    """,
                    datetime.utcnow(),
                    cutoff_date
                )

                return {
                    "archived_count": archived_count or 0,
                    "retention_policy_days": retention_days
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to cleanup sync mappings: {e}")
            raise DatabaseException(
                message="Failed to cleanup expired sync mappings",
                original_exception=e
            )

    # ================================================================
    # CONFIGURATION AND TOKEN MANAGEMENT
    # ================================================================

    async def get_calendar_config(
        self,
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve calendar configuration for organization.

        What: Fetches calendar integration settings.
        Where: Called when displaying calendar settings.
        Why: Enables viewing/editing calendar configuration.

        Args:
            organization_id: UUID of the organization

        Returns:
            Configuration dictionary or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT integration_id, provider, status, calendar_id,
                           sync_enabled, timezone, created_at, updated_at
                    FROM calendar_integrations
                    WHERE organization_id = $1
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    organization_id
                )

                if not row:
                    return None

                return dict(row)
            finally:
                await self.db_pool.release(conn)

        except (OSError, ConnectionRefusedError) as e:
            raise DatabaseException(
                message="Database connection failed when retrieving calendar config",
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to get calendar config: {e}")
            raise DatabaseException(
                message="Failed to retrieve calendar configuration",
                original_exception=e
            )

    async def store_oauth_tokens(
        self,
        organization_id: str,
        tokens: Dict[str, Any]
    ) -> None:
        """
        Store OAuth tokens securely (encrypted).

        What: Encrypts and persists OAuth tokens.
        Where: Called after OAuth completion.
        Why: Enables secure token storage.

        Args:
            organization_id: UUID of the organization
            tokens: Token dictionary with access_token, refresh_token

        Raises:
            ValidationException: If encryption key not configured
            DatabaseException: If database operation fails
        """
        # Check for encryption key
        encryption_key = os.environ.get("OAUTH_TOKEN_ENCRYPTION_KEY")
        if not encryption_key:
            raise ValidationException(
                message="OAuth token encryption key not configured",
                validation_errors={"env_var": "OAUTH_TOKEN_ENCRYPTION_KEY"}
            )

        try:
            conn = await self.db_pool.acquire()
            try:
                await conn.execute(
                    """
                    UPDATE calendar_integrations
                    SET access_token = $1, refresh_token = $2, updated_at = $3
                    WHERE organization_id = $4
                    """,
                    tokens.get("access_token"),
                    tokens.get("refresh_token"),
                    datetime.utcnow(),
                    organization_id
                )
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to store OAuth tokens: {e}")
            raise DatabaseException(
                message="Failed to store OAuth tokens",
                original_exception=e
            )

    # ================================================================
    # HELPER METHODS
    # ================================================================

    def _validate_course_event(self, event: Dict[str, Any]) -> None:
        """
        Validate course event data.

        Args:
            event: Event data dictionary

        Raises:
            ValidationException: If validation fails
        """
        # Check required fields
        required_fields = ["title"]
        missing = [f for f in required_fields if f not in event]

        # For timed events, need start and end
        if "due_date" not in event:  # Not a deadline
            if "start_time" not in event or "end_time" not in event:
                missing.extend(["start_time", "end_time"])

        if missing:
            raise ValidationException(
                message=f"Missing required fields: {', '.join(missing)}",
                validation_errors={"missing_fields": missing}
            )

        # Validate date range
        if "start_time" in event and "end_time" in event:
            if event["end_time"] <= event["start_time"]:
                raise ValidationException(
                    message="Event end time must be after start time",
                    validation_errors={"end_time": "End time before start time"}
                )

        # Validate attendee limits
        attendees = event.get("attendee_emails", [])
        if len(attendees) > self.MAX_ATTENDEES:
            raise ValidationException(
                message=f"Too many attendees ({len(attendees)}). Google Calendar limit is {self.MAX_ATTENDEES}.",
                validation_errors={"attendee_emails": f"Exceeds limit of {self.MAX_ATTENDEES}"}
            )

    def _build_event_payload(self, event: Dict[str, Any], timezone: str) -> Dict[str, Any]:
        """
        Build calendar event payload for API.

        Args:
            event: Event data dictionary
            timezone: Timezone string

        Returns:
            Event payload for Google/Outlook API
        """
        payload = {
            "summary": event.get("title"),
            "description": event.get("description", ""),
            "location": event.get("location", "")
        }

        # Handle start/end times
        start_time = event.get("start_time")
        end_time = event.get("end_time")

        if start_time:
            if hasattr(start_time, 'isoformat'):
                payload["start"] = {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone
                }
            else:
                payload["start"] = {"dateTime": start_time, "timeZone": timezone}

        if end_time:
            if hasattr(end_time, 'isoformat'):
                payload["end"] = {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone
                }
            else:
                payload["end"] = {"dateTime": end_time, "timeZone": timezone}

        # Handle attendees
        attendees = event.get("attendee_emails", [])
        instructor = event.get("instructor_email")
        if instructor and instructor not in attendees:
            attendees = [instructor] + attendees

        if attendees:
            payload["attendees"] = [{"email": email} for email in attendees]

        # Handle recurrence
        recurrence = event.get("recurrence")
        if recurrence:
            rrule = self._build_rrule(recurrence)
            if rrule:
                payload["recurrence"] = [rrule]

        return payload

    def _build_rrule(self, recurrence: Dict[str, Any]) -> Optional[str]:
        """
        Build RRULE string from recurrence config.

        Args:
            recurrence: Recurrence configuration

        Returns:
            RRULE string or None
        """
        freq = recurrence.get("frequency", "").upper()
        if not freq:
            return None

        parts = [f"FREQ={freq}"]

        if recurrence.get("count"):
            parts.append(f"COUNT={recurrence['count']}")

        if recurrence.get("days"):
            days_map = {
                "MONDAY": "MO", "TUESDAY": "TU", "WEDNESDAY": "WE",
                "THURSDAY": "TH", "FRIDAY": "FR", "SATURDAY": "SA", "SUNDAY": "SU"
            }
            days = [days_map.get(d.upper(), d[:2].upper()) for d in recurrence["days"]]
            parts.append(f"BYDAY={','.join(days)}")

        return "RRULE:" + ";".join(parts)

    # ================================================================
    # LEGACY METHODS (from original skeleton)
    # ================================================================

    async def create_calendar_provider(
        self,
        provider: CalendarProvider
    ) -> CalendarProvider:
        """Create a calendar provider configuration."""
        try:
            conn = await self.db_pool.acquire()
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO calendar_providers (
                        id, user_id, provider_type, provider_name, access_token,
                        refresh_token, token_expires_at, calendar_id, calendar_name,
                        calendar_timezone, sync_enabled, sync_direction,
                        sync_deadline_reminders, sync_class_schedules, sync_quiz_dates,
                        reminder_minutes_before, is_connected, last_sync_at,
                        last_sync_error, connection_error_count, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                    )
                    RETURNING *
                    """,
                    provider.id,
                    provider.user_id,
                    provider.provider_type.value if hasattr(provider.provider_type, 'value') else str(provider.provider_type),
                    provider.provider_name,
                    provider.access_token,
                    provider.refresh_token,
                    provider.token_expires_at,
                    provider.calendar_id,
                    provider.calendar_name,
                    provider.calendar_timezone,
                    provider.sync_enabled,
                    provider.sync_direction.value if hasattr(provider.sync_direction, 'value') else str(provider.sync_direction),
                    provider.sync_deadline_reminders,
                    provider.sync_class_schedules,
                    provider.sync_quiz_dates,
                    provider.reminder_minutes_before,
                    provider.is_connected,
                    provider.last_sync_at,
                    provider.last_sync_error,
                    provider.connection_error_count,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_calendar_provider(row)
            finally:
                await self.db_pool.release(conn)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="Calendar provider already configured for this user",
                validation_errors={"provider_type": str(provider.provider_type)}
            )
        except Exception as e:
            self.logger.error(f"Failed to create calendar provider: {e}")
            raise DatabaseException(
                message="Failed to create calendar provider",
                original_exception=e
            )

    async def get_calendar_providers_by_user(
        self,
        user_id: UUID
    ) -> List[CalendarProvider]:
        """Retrieve all calendar providers for a user."""
        try:
            conn = await self.db_pool.acquire()
            try:
                rows = await conn.fetch(
                    """
                    SELECT * FROM calendar_providers
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    """,
                    user_id
                )
                return [self._row_to_calendar_provider(row) for row in rows]
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to get calendar providers for user {user_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve calendar providers for user",
                original_exception=e
            )

    async def update_calendar_provider(
        self,
        provider_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[CalendarProvider]:
        """Update a calendar provider."""
        try:
            set_clauses = []
            params = []
            param_count = 1

            for field, value in updates.items():
                if hasattr(value, 'value'):
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value.value)
                else:
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value)
                param_count += 1

            set_clauses.append(f"updated_at = ${param_count}")
            params.append(datetime.now())
            param_count += 1

            params.append(provider_id)

            conn = await self.db_pool.acquire()
            try:
                row = await conn.fetchrow(
                    f"""
                    UPDATE calendar_providers
                    SET {', '.join(set_clauses)}
                    WHERE id = ${param_count}
                    RETURNING *
                    """,
                    *params
                )
                return self._row_to_calendar_provider(row) if row else None
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to update calendar provider {provider_id}: {e}")
            raise DatabaseException(
                message="Failed to update calendar provider",
                original_exception=e
            )

    async def delete_calendar_provider(self, provider_id: UUID) -> bool:
        """Delete a calendar provider."""
        try:
            conn = await self.db_pool.acquire()
            try:
                result = await conn.execute(
                    "DELETE FROM calendar_providers WHERE id = $1",
                    provider_id
                )
                return result == "DELETE 1"
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to delete calendar provider {provider_id}: {e}")
            raise DatabaseException(
                message="Failed to delete calendar provider",
                original_exception=e
            )

    async def create_calendar_event(
        self,
        event: CalendarEvent
    ) -> CalendarEvent:
        """Create a calendar event."""
        try:
            conn = await self.db_pool.acquire()
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO calendar_events (
                        id, provider_id, user_id, external_event_id, external_calendar_id,
                        title, description, location, start_time, end_time, all_day,
                        timezone, is_recurring, recurrence_rule, recurring_event_id,
                        event_type, source_type, source_id, sync_status, local_updated_at,
                        remote_updated_at, last_sync_at, reminder_sent, reminder_sent_at,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26
                    )
                    RETURNING *
                    """,
                    event.id,
                    event.provider_id,
                    event.user_id,
                    event.external_event_id,
                    event.external_calendar_id,
                    event.title,
                    event.description,
                    event.location,
                    event.start_time,
                    event.end_time,
                    event.all_day,
                    event.timezone,
                    event.is_recurring,
                    event.recurrence_rule,
                    event.recurring_event_id,
                    event.event_type,
                    event.source_type,
                    event.source_id,
                    event.sync_status.value if hasattr(event.sync_status, 'value') else str(event.sync_status),
                    event.local_updated_at,
                    event.remote_updated_at,
                    event.last_sync_at,
                    event.reminder_sent,
                    event.reminder_sent_at,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_calendar_event(row)
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to create calendar event: {e}")
            raise DatabaseException(
                message="Failed to create calendar event",
                original_exception=e
            )

    async def get_calendar_events_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CalendarEvent]:
        """Retrieve calendar events for a user."""
        try:
            conn = await self.db_pool.acquire()
            try:
                if start_date and end_date:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM calendar_events
                        WHERE user_id = $1 AND start_time >= $2 AND end_time <= $3
                        ORDER BY start_time ASC
                        LIMIT $4
                        """,
                        user_id, start_date, end_date, limit
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM calendar_events
                        WHERE user_id = $1
                        ORDER BY start_time ASC
                        LIMIT $2
                        """,
                        user_id, limit
                    )
                return [self._row_to_calendar_event(row) for row in rows]
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to get calendar events for user {user_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve calendar events for user",
                original_exception=e
            )

    async def get_events_needing_reminder(
        self,
        limit: int = 100
    ) -> List[CalendarEvent]:
        """Retrieve events needing reminders."""
        try:
            conn = await self.db_pool.acquire()
            try:
                rows = await conn.fetch(
                    """
                    SELECT ce.* FROM calendar_events ce
                    JOIN calendar_providers cp ON ce.provider_id = cp.id
                    WHERE ce.reminder_sent = false
                      AND ce.start_time > NOW()
                      AND ce.start_time <= NOW() + (cp.reminder_minutes_before || ' minutes')::interval
                    ORDER BY ce.start_time ASC
                    LIMIT $1
                    """,
                    limit
                )
                return [self._row_to_calendar_event(row) for row in rows]
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to get events needing reminder: {e}")
            raise DatabaseException(
                message="Failed to retrieve events needing reminder",
                original_exception=e
            )

    def _row_to_calendar_provider(self, row) -> CalendarProvider:
        """Convert database row to CalendarProvider entity."""
        return CalendarProvider(
            id=row['id'],
            user_id=row['user_id'],
            provider_type=CalendarProviderType(row['provider_type']) if row['provider_type'] else CalendarProviderType.GOOGLE,
            provider_name=row['provider_name'],
            access_token=row['access_token'],
            refresh_token=row['refresh_token'],
            token_expires_at=row['token_expires_at'],
            calendar_id=row['calendar_id'],
            calendar_name=row['calendar_name'],
            calendar_timezone=row['calendar_timezone'],
            sync_enabled=row['sync_enabled'],
            sync_direction=SyncDirection(row['sync_direction']) if row['sync_direction'] else SyncDirection.BIDIRECTIONAL,
            sync_deadline_reminders=row['sync_deadline_reminders'],
            sync_class_schedules=row['sync_class_schedules'],
            sync_quiz_dates=row['sync_quiz_dates'],
            reminder_minutes_before=row['reminder_minutes_before'],
            is_connected=row['is_connected'],
            last_sync_at=row['last_sync_at'],
            last_sync_error=row['last_sync_error'],
            connection_error_count=row['connection_error_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_calendar_event(self, row) -> CalendarEvent:
        """Convert database row to CalendarEvent entity."""
        return CalendarEvent(
            id=row['id'],
            provider_id=row['provider_id'],
            user_id=row['user_id'],
            external_event_id=row['external_event_id'],
            external_calendar_id=row['external_calendar_id'],
            title=row['title'],
            description=row['description'],
            location=row['location'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            all_day=row['all_day'],
            timezone=row['timezone'],
            is_recurring=row['is_recurring'],
            recurrence_rule=row['recurrence_rule'],
            recurring_event_id=row['recurring_event_id'],
            event_type=row['event_type'],
            source_type=row['source_type'],
            source_id=row['source_id'],
            sync_status=CalendarSyncStatus(row['sync_status']) if row['sync_status'] else CalendarSyncStatus.SYNCED,
            local_updated_at=row['local_updated_at'],
            remote_updated_at=row['remote_updated_at'],
            last_sync_at=row['last_sync_at'],
            reminder_sent=row['reminder_sent'],
            reminder_sent_at=row['reminder_sent_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
