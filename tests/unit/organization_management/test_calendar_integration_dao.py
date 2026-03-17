"""
CalendarIntegrationDAO Unit Tests - TDD RED Phase

BUSINESS CONTEXT:
The CalendarIntegrationDAO handles calendar integration functionality for organizations,
allowing course schedules, meetings, and deadlines to be synced with external calendar
providers (Google Calendar, Outlook Calendar).

REFACTORING CONTEXT:
This test file is part of the IntegrationsDAO god class refactoring (2,911 lines → 5 specialized DAOs).
The CalendarIntegrationDAO will be extracted to handle ONLY calendar-related operations.

TEST COVERAGE (TDD RED Phase):
1. Google Calendar OAuth 2.0 Integration (8 tests)
2. Outlook Calendar Integration (6 tests)
3. Event Synchronization (10 tests)
4. Calendar Disconnect and Cleanup (6 tests)
5. Error Handling and Edge Cases (8 tests)

DEPENDENCIES:
- Custom exceptions from shared/exceptions/__init__.py
- Google Calendar API (googleapiclient.discovery)
- Microsoft Graph API (msal, requests)
- OAuth 2.0 token management

EXPECTED BEHAVIOR (TDD RED - These tests WILL FAIL until implementation):
All tests define the DESIRED behavior for the CalendarIntegrationDAO.
Implementation should follow the Clean Architecture pattern:
- Domain layer: Calendar event entities
- Application layer: Calendar synchronization service
- Infrastructure layer: CalendarIntegrationDAO (database operations)

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

# These imports will fail until the CalendarIntegrationDAO is created (TDD RED phase)
try:
    from organization_management.infrastructure.repositories.calendar_integration_dao import CalendarIntegrationDAO
except ImportError:
    CalendarIntegrationDAO = None  # Expected during RED phase

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

    # Configure for direct await pattern (used by CalendarIntegrationDAO implementation)
    pool.acquire.return_value = conn
    pool.release = AsyncMock()

    # Also configure for async context manager pattern (if needed)
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    # Configure connection methods
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.fetchval = AsyncMock()
    conn.execute = AsyncMock()
    return pool


@pytest.fixture
def sample_organization_id():
    """Sample organization UUID."""
    return "org-550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_calendar_config():
    """Sample calendar integration configuration."""
    return {
        "organization_id": "org-550e8400-e29b-41d4-a716-446655440000",
        "provider": "google",
        "calendar_id": "primary",
        "sync_enabled": True,
        "sync_interval_minutes": 15,
        "sync_past_days": 30,
        "sync_future_days": 90
    }


@pytest.fixture
def sample_google_oauth_tokens():
    """Sample Google OAuth 2.0 tokens."""
    return {
        "access_token": "ya29.a0AfH6SMBx...",
        "refresh_token": "1//0gJKwXYZ...",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }


@pytest.fixture
def sample_outlook_oauth_tokens():
    """Sample Microsoft OAuth 2.0 tokens."""
    return {
        "access_token": "EwBwA8l6BAAURSN...",
        "refresh_token": "M.R3_BAY.-CRvF...",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }


@pytest.fixture
def sample_course_event():
    """Sample course event to sync to calendar."""
    return {
        "course_id": "course-123",
        "title": "Introduction to Python Programming",
        "start_time": datetime.utcnow() + timedelta(days=7),
        "end_time": datetime.utcnow() + timedelta(days=7, hours=2),
        "description": "First session of Python course",
        "location": "Room 101",
        "instructor_email": "instructor@example.com",
        "attendee_emails": ["student1@example.com", "student2@example.com"]
    }


# ============================================================================
# TEST CLASS 1: Google Calendar OAuth 2.0 Integration
# ============================================================================

@pytest.mark.skipif(CalendarIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestGoogleCalendarOAuthIntegration:
    """
    Tests for Google Calendar OAuth 2.0 integration.

    BUSINESS REQUIREMENTS:
    - Organizations can connect their Google Workspace calendar
    - OAuth 2.0 authorization flow must be secure
    - Tokens must be encrypted at rest
    - Token refresh must be automatic
    """

    @pytest.mark.asyncio
    async def test_initiate_google_oauth_flow(self, fake_db_pool, sample_organization_id):
        """
        Test initiating Google OAuth 2.0 authorization flow.

        EXPECTED BEHAVIOR:
        - Generates authorization URL with correct scopes
        - Stores state parameter securely
        - Returns authorization URL for user redirect
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - no existing integration
        fake_db_pool.acquire.return_value.fetchrow.return_value = None

        # Act
        result = await dao.initiate_google_oauth(
            organization_id=sample_organization_id,
            redirect_uri="https://platform.example.com/integrations/google/callback"
        )

        # Assert
        assert result["provider"] == "google"
        assert result["authorization_url"].startswith("https://accounts.google.com/o/oauth2/v2/auth")
        assert "state" in result
        assert "calendar" in result["authorization_url"].lower()  # Scope check
        assert sample_organization_id in result["state"]  # State should include org context

    @pytest.mark.asyncio
    async def test_complete_google_oauth_flow(self, fake_db_pool, sample_organization_id, sample_google_oauth_tokens):
        """
        Test completing Google OAuth 2.0 flow with authorization code.

        EXPECTED BEHAVIOR:
        - Exchanges authorization code for access/refresh tokens
        - Stores encrypted tokens in database
        - Validates token expiration
        - Returns success confirmation
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)
        state = "secure-state-token"

        # Arrange - fetchrow returns state first, then integration
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {"state": state},  # First call: state verification
            {"integration_id": "int-123", "organization_id": sample_organization_id, "provider": "google", "status": "active"}  # Second call: insert returning
        ]

        # Add scope to tokens
        tokens_with_scope = sample_google_oauth_tokens.copy()
        tokens_with_scope["scope"] = "https://www.googleapis.com/auth/calendar.events"

        fake_calendars = [{"id": "primary", "summary": "Work Calendar"}]

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.exchange_google_code") as mock_exchange, \
             patch("organization_management.infrastructure.repositories.calendar_integration_dao.fetch_google_calendars") as mock_fetch:
            mock_exchange.return_value = tokens_with_scope
            mock_fetch.return_value = fake_calendars

            # Act
            result = await dao.complete_google_oauth(
                organization_id=sample_organization_id,
                authorization_code="4/0AY0e-g7XYZ...",
                state=state
            )

        # Assert
        assert result["integration_id"] == "int-123"
        assert result["provider"] == "google"
        assert result["status"] == "active"
        assert result["tokens_stored"] is True

    @pytest.mark.asyncio
    async def test_refresh_google_access_token(self, fake_db_pool, sample_organization_id, sample_google_oauth_tokens):
        """
        Test automatic refresh of expired Google access token.

        EXPECTED BEHAVIOR:
        - Detects expired access token
        - Uses refresh token to obtain new access token
        - Updates stored tokens in database
        - Returns new valid access token
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - expired token (use datetime object, not string)
        expired_expires_at = datetime.utcnow() - timedelta(hours=1)

        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "int-123",
            "access_token": sample_google_oauth_tokens["access_token"],
            "refresh_token": sample_google_oauth_tokens["refresh_token"],
            "expires_at": expired_expires_at  # datetime object
        }

        new_token = sample_google_oauth_tokens.copy()
        new_token["access_token"] = "ya29.NEW_TOKEN"

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.refresh_google_token") as mock_refresh:
            mock_refresh.return_value = new_token

            # Act
            result = await dao.get_google_access_token(
                organization_id=sample_organization_id
            )

        # Assert
        assert result["access_token"] == "ya29.NEW_TOKEN"
        assert result["refreshed"] is True
        mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_google_oauth_with_invalid_state(self, fake_db_pool, sample_organization_id):
        """
        Test OAuth callback with invalid state parameter (security check).

        EXPECTED BEHAVIOR:
        - Validates state parameter matches stored state
        - Raises AuthenticationException on mismatch
        - Does not exchange authorization code
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - stored state different from provided state
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "state": "valid-state-123"  # Different from what we'll provide
        }

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            await dao.complete_google_oauth(
                organization_id=sample_organization_id,
                authorization_code="4/0AY0e-g7XYZ...",
                state="invalid-state-456"  # Doesn't match stored state
            )

        assert "state mismatch" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_google_oauth_with_expired_authorization_code(self, fake_db_pool, sample_organization_id):
        """
        Test OAuth with expired authorization code.

        EXPECTED BEHAVIOR:
        - Attempts to exchange code
        - Receives error from Google API
        - Raises AuthenticationException with helpful message
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)
        state = "valid-state"

        # Arrange - state verification passes
        fake_db_pool.acquire.return_value.fetchrow.return_value = {"state": state}

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.exchange_google_code") as mock_exchange:
            mock_exchange.side_effect = Exception("invalid_grant: Code expired")

            # Act & Assert
            with pytest.raises(AuthenticationException) as exc_info:
                await dao.complete_google_oauth(
                    organization_id=sample_organization_id,
                    authorization_code="expired-code",
                    state=state
                )

            assert "expired" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_google_oauth_stores_calendar_list(self, fake_db_pool, sample_organization_id, sample_google_oauth_tokens):
        """
        Test that OAuth completion retrieves and stores available calendars.

        EXPECTED BEHAVIOR:
        - After token exchange, fetches user's calendar list
        - Stores calendar metadata (id, name, timezone)
        - Allows selection of primary calendar
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)
        state = "valid-state"

        # Arrange - state verification and integration insert
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {"state": state},  # State verification
            {"integration_id": "int-456", "organization_id": sample_organization_id, "provider": "google", "status": "active"}  # Insert returning
        ]

        fake_calendars = [
            {"id": "primary", "summary": "Work Calendar", "timeZone": "America/New_York"},
            {"id": "calendar2", "summary": "Personal", "timeZone": "America/New_York"}
        ]

        # Add scope to tokens
        tokens_with_scope = sample_google_oauth_tokens.copy()
        tokens_with_scope["scope"] = "https://www.googleapis.com/auth/calendar.events"

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.exchange_google_code") as mock_exchange, \
             patch("organization_management.infrastructure.repositories.calendar_integration_dao.fetch_google_calendars") as mock_fetch:
            mock_exchange.return_value = tokens_with_scope
            mock_fetch.return_value = fake_calendars

            # Act
            result = await dao.complete_google_oauth(
                organization_id=sample_organization_id,
                authorization_code="valid-code",
                state=state
            )

        # Assert
        assert result["available_calendars"] == fake_calendars
        assert result["default_calendar"] == "primary"

    @pytest.mark.asyncio
    async def test_google_oauth_duplicate_connection(self, fake_db_pool, sample_organization_id):
        """
        Test attempting to connect Google Calendar when already connected.

        EXPECTED BEHAVIOR:
        - Checks for existing active Google Calendar integration
        - Raises ConflictException if already connected
        - Provides option to disconnect and reconnect
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - existing active integration
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "existing-int-123",
            "provider": "google",
            "status": "active"
        }

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            await dao.initiate_google_oauth(
                organization_id=sample_organization_id,
                redirect_uri="https://platform.example.com/callback"
            )

        assert "already connected" in str(exc_info.value).lower()
        assert "existing-int-123" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_google_oauth_insufficient_scopes(self, fake_db_pool, sample_organization_id):
        """
        Test OAuth completion when user grants insufficient scopes.

        EXPECTED BEHAVIOR:
        - Validates required scopes were granted
        - Raises ValidationException if calendar.events scope missing
        - Provides clear message about required permissions
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)
        state = "valid-state"

        # Arrange - state verification must pass first
        fake_db_pool.acquire.return_value.fetchrow.return_value = {"state": state}

        # Arrange - tokens without calendar scope
        insufficient_tokens = {
            "access_token": "ya29.LIMITED_TOKEN",
            "scope": "profile email",  # Missing calendar.events
            "token_type": "Bearer"
        }

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.exchange_google_code") as mock_exchange:
            mock_exchange.return_value = insufficient_tokens

            # Act & Assert
            with pytest.raises(ValidationException) as exc_info:
                await dao.complete_google_oauth(
                    organization_id=sample_organization_id,
                    authorization_code="valid-code",
                    state=state
                )

            assert "calendar.events" in str(exc_info.value)
            assert "required scope" in str(exc_info.value).lower()


# ============================================================================
# TEST CLASS 2: Outlook Calendar Integration
# ============================================================================

@pytest.mark.skipif(CalendarIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestOutlookCalendarIntegration:
    """
    Tests for Microsoft Outlook/Office 365 Calendar integration.

    BUSINESS REQUIREMENTS:
    - Organizations can connect their Microsoft 365 calendar
    - Uses Microsoft Graph API
    - Supports both personal and organizational accounts
    """

    @pytest.mark.asyncio
    async def test_initiate_outlook_oauth_flow(self, fake_db_pool, sample_organization_id):
        """
        Test initiating Microsoft OAuth 2.0 authorization flow.

        EXPECTED BEHAVIOR:
        - Generates authorization URL with Microsoft identity platform
        - Requests Calendars.ReadWrite permission
        - Returns authorization URL
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Act
        result = await dao.initiate_outlook_oauth(
            organization_id=sample_organization_id,
            redirect_uri="https://platform.example.com/integrations/outlook/callback"
        )

        # Assert
        assert result["provider"] == "outlook"
        assert "login.microsoftonline.com" in result["authorization_url"]
        assert "Calendars.ReadWrite" in result["authorization_url"]
        assert "state" in result

    @pytest.mark.asyncio
    async def test_complete_outlook_oauth_flow(self, fake_db_pool, sample_organization_id, sample_outlook_oauth_tokens):
        """
        Test completing Outlook OAuth flow with authorization code.

        EXPECTED BEHAVIOR:
        - Exchanges code for access/refresh tokens
        - Stores tokens securely
        - Validates Microsoft Graph API access
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.exchange_microsoft_code") as mock_exchange:
            mock_exchange.return_value = sample_outlook_oauth_tokens

            # Act
            result = await dao.complete_outlook_oauth(
                organization_id=sample_organization_id,
                authorization_code="M.R3_BAY.-CRvF...",
                state="valid-state"
            )

        # Assert
        assert result["provider"] == "outlook"
        assert result["status"] == "active"
        assert result["tokens_stored"] is True

    @pytest.mark.asyncio
    async def test_refresh_outlook_access_token(self, fake_db_pool, sample_organization_id, sample_outlook_oauth_tokens):
        """
        Test automatic refresh of expired Outlook access token.

        EXPECTED BEHAVIOR:
        - Detects token expiration
        - Uses refresh token with Microsoft identity platform
        - Updates stored credentials
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - expired token (use datetime object, not string)
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "int-outlook-123",
            "access_token": "EXPIRED_TOKEN",
            "refresh_token": sample_outlook_oauth_tokens["refresh_token"],
            "expires_at": datetime.utcnow() - timedelta(hours=1)  # datetime object
        }

        new_token = sample_outlook_oauth_tokens.copy()
        new_token["access_token"] = "NEW_OUTLOOK_TOKEN"

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.refresh_microsoft_token") as mock_refresh:
            mock_refresh.return_value = new_token

            # Act
            result = await dao.get_outlook_access_token(
                organization_id=sample_organization_id
            )

        # Assert
        assert result["access_token"] == "NEW_OUTLOOK_TOKEN"
        assert result["refreshed"] is True

    @pytest.mark.asyncio
    async def test_outlook_fetch_calendars(self, fake_db_pool, sample_organization_id, sample_outlook_oauth_tokens):
        """
        Test fetching available Outlook calendars via Microsoft Graph API.

        EXPECTED BEHAVIOR:
        - Uses Microsoft Graph API /me/calendars endpoint
        - Returns list of calendars with metadata
        - Stores calendar list for selection
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - need to set up integration record for get_outlook_access_token
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "int-outlook-123",
            "access_token": sample_outlook_oauth_tokens["access_token"],
            "refresh_token": sample_outlook_oauth_tokens["refresh_token"],
            "expires_at": datetime.utcnow() + timedelta(hours=1)  # Valid token
        }

        fake_calendars = [
            {"id": "AAMkAGI2...", "name": "Calendar", "isDefaultCalendar": True},
            {"id": "AAMkAGI3...", "name": "Meetings", "isDefaultCalendar": False}
        ]

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.fetch_outlook_calendars") as mock_fetch:
            mock_fetch.return_value = fake_calendars

            # Act
            result = await dao.get_outlook_calendars(
                organization_id=sample_organization_id
            )

        # Assert
        assert len(result["calendars"]) == 2
        assert result["default_calendar"]["id"] == "AAMkAGI2..."

    @pytest.mark.asyncio
    async def test_outlook_graph_api_rate_limit(self, fake_db_pool, sample_organization_id, sample_outlook_oauth_tokens):
        """
        Test handling Microsoft Graph API rate limiting (429 Too Many Requests).

        EXPECTED BEHAVIOR:
        - Catches 429 status code
        - Extracts Retry-After header
        - Raises RateLimitException with retry information
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - need valid integration for access token
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "int-outlook-123",
            "access_token": sample_outlook_oauth_tokens["access_token"],
            "refresh_token": sample_outlook_oauth_tokens["refresh_token"],
            "expires_at": datetime.utcnow() + timedelta(hours=1)  # Valid token
        }

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.fetch_outlook_calendars") as mock_fetch:
            mock_fetch.side_effect = Exception("429 Too Many Requests, Retry-After: 60")

            # Act & Assert
            with pytest.raises(RateLimitException) as exc_info:
                await dao.get_outlook_calendars(
                    organization_id=sample_organization_id
                )

            assert "rate limit" in str(exc_info.value).lower()
            assert "60" in str(exc_info.value)  # Retry-After value

    @pytest.mark.asyncio
    async def test_outlook_revoked_access(self, fake_db_pool, sample_organization_id, sample_outlook_oauth_tokens):
        """
        Test handling revoked Outlook calendar access.

        EXPECTED BEHAVIOR:
        - Detects 401 Unauthorized or invalid_grant error
        - Marks integration as inactive
        - Raises AuthenticationException
        - Notifies organization admin
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - need expired token to trigger refresh
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "int-outlook-123",
            "access_token": "EXPIRED_TOKEN",
            "refresh_token": sample_outlook_oauth_tokens["refresh_token"],
            "expires_at": datetime.utcnow() - timedelta(hours=1)  # Expired to trigger refresh
        }

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.refresh_microsoft_token") as mock_refresh:
            mock_refresh.side_effect = Exception("invalid_grant: Token has been revoked")

            # Act & Assert
            with pytest.raises(AuthenticationException) as exc_info:
                await dao.get_outlook_access_token(
                    organization_id=sample_organization_id
                )

            assert "revoked" in str(exc_info.value).lower()


# ============================================================================
# TEST CLASS 3: Event Synchronization
# ============================================================================

@pytest.mark.skipif(CalendarIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestCalendarEventSynchronization:
    """
    Tests for synchronizing course events to external calendars.

    BUSINESS REQUIREMENTS:
    - Course schedules automatically sync to instructor/student calendars
    - Meeting room bookings create calendar events
    - Deadlines and due dates appear as calendar reminders
    - Bidirectional sync (platform → calendar, calendar → platform)
    """

    @pytest.mark.asyncio
    async def test_sync_course_start_to_google_calendar(self, fake_db_pool, sample_organization_id, sample_course_event, sample_google_oauth_tokens):
        """
        Test syncing course start event to Google Calendar.

        EXPECTED BEHAVIOR:
        - Creates event in Google Calendar via API
        - Stores calendar event ID for future updates
        - Sets event reminder 15 minutes before start
        - Includes course link in event description
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - multiple fetchrow calls: 1) integration, 2) existing mapping
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {  # First call: get integration
                "integration_id": "int-123",
                "provider": "google",
                "calendar_id": "primary",
                "access_token": sample_google_oauth_tokens["access_token"]
            },
            None  # Second call: no existing sync mapping (create new)
        ]

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.create_google_event") as mock_create:
            mock_create.return_value = {"id": "google_event_xyz", "htmlLink": "https://calendar.google.com/event?eid=xyz"}

            # Act
            result = await dao.sync_course_event_to_calendar(
                organization_id=sample_organization_id,
                course_event=sample_course_event
            )

        # Assert
        assert result["provider"] == "google"
        assert result["calendar_event_id"] == "google_event_xyz"
        assert result["event_link"] == "https://calendar.google.com/event?eid=xyz"
        assert result["synced"] is True

    @pytest.mark.asyncio
    async def test_sync_course_start_to_outlook_calendar(self, fake_db_pool, sample_organization_id, sample_course_event, sample_outlook_oauth_tokens):
        """
        Test syncing course start event to Outlook Calendar.

        EXPECTED BEHAVIOR:
        - Creates event via Microsoft Graph API
        - Stores event ID for updates
        - Sets reminder
        - Includes Teams meeting link if available
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - multiple fetchrow calls: 1) integration, 2) existing mapping
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {  # First call: get integration
                "integration_id": "int-outlook-123",
                "provider": "outlook",
                "calendar_id": "AAMkAGI2...",
                "access_token": sample_outlook_oauth_tokens["access_token"]
            },
            None  # Second call: no existing sync mapping (create new)
        ]

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.create_outlook_event") as mock_create:
            mock_create.return_value = {"id": "AAMkADU...", "webLink": "https://outlook.office.com/calendar/item/AAMkADU"}

            # Act
            result = await dao.sync_course_event_to_calendar(
                organization_id=sample_organization_id,
                course_event=sample_course_event
            )

        # Assert
        assert result["provider"] == "outlook"
        assert result["calendar_event_id"] == "AAMkADU..."
        assert result["synced"] is True

    @pytest.mark.asyncio
    async def test_update_existing_calendar_event(self, fake_db_pool, sample_organization_id, sample_course_event, sample_google_oauth_tokens):
        """
        Test updating an existing calendar event when course time changes.

        EXPECTED BEHAVIOR:
        - Detects existing event mapping
        - Updates event in external calendar
        - Preserves event ID
        - Notifies attendees of change
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - multiple fetchrow calls: 1) integration, 2) existing mapping
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {  # First call: get integration
                "integration_id": "int-123",
                "provider": "google",
                "calendar_id": "primary",
                "access_token": sample_google_oauth_tokens["access_token"]
            },
            {  # Second call: existing sync mapping (update)
                "sync_mapping_id": "mapping-123",
                "calendar_event_id": "google_event_xyz",
                "provider": "google"
            }
        ]

        updated_event = sample_course_event.copy()
        updated_event["start_time"] = sample_course_event["start_time"] + timedelta(days=1)
        updated_event["end_time"] = sample_course_event["end_time"] + timedelta(days=1)  # Also update end time

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.update_google_event") as mock_update:
            mock_update.return_value = {"id": "google_event_xyz", "updated": True}

            # Act
            result = await dao.sync_course_event_to_calendar(
                organization_id=sample_organization_id,
                course_event=updated_event
            )

        # Assert
        assert result["action"] == "updated"
        assert result["calendar_event_id"] == "google_event_xyz"
        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_calendar_event_when_course_cancelled(self, fake_db_pool, sample_organization_id):
        """
        Test deleting calendar event when course is cancelled.

        EXPECTED BEHAVIOR:
        - Finds event mapping in database
        - Deletes event from external calendar
        - Removes sync mapping
        - Sends cancellation notification
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange
        course_id = "course-123"
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "calendar_event_id": "google_event_xyz",
            "provider": "google"
        }

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.delete_google_event") as mock_delete:
            mock_delete.return_value = {"deleted": True}

            # Act
            result = await dao.delete_course_event_from_calendar(
                organization_id=sample_organization_id,
                course_id=course_id
            )

        # Assert
        assert result["deleted"] is True
        assert result["sync_mapping_removed"] is True
        mock_delete.assert_called_once_with("google_event_xyz")

    @pytest.mark.asyncio
    async def test_sync_recurring_course_schedule(self, fake_db_pool, sample_organization_id, sample_google_oauth_tokens):
        """
        Test syncing recurring course schedule (e.g., every Monday for 8 weeks).

        EXPECTED BEHAVIOR:
        - Creates recurring event with RRULE
        - Stores single event ID for entire series
        - Updates all occurrences when one changes
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - multiple fetchrow calls: 1) integration, 2) existing mapping
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {  # First call: get integration
                "integration_id": "int-123",
                "provider": "google",
                "calendar_id": "primary",
                "access_token": sample_google_oauth_tokens["access_token"]
            },
            None  # Second call: no existing sync mapping (create new)
        ]

        recurring_event = {
            "course_id": "course-recurring-123",
            "title": "Weekly Python Class",
            "start_time": datetime.utcnow() + timedelta(days=7),
            "end_time": datetime.utcnow() + timedelta(days=7, hours=2),
            "recurrence": {
                "frequency": "WEEKLY",
                "days": ["MONDAY"],
                "count": 8
            }
        }

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.create_google_event") as mock_create:
            mock_create.return_value = {
                "id": "google_recurring_xyz",
                "recurrence": ["RRULE:FREQ=WEEKLY;COUNT=8;BYDAY=MO"]
            }

            # Act
            result = await dao.sync_course_event_to_calendar(
                organization_id=sample_organization_id,
                course_event=recurring_event
            )

        # Assert
        assert result["calendar_event_id"] == "google_recurring_xyz"
        assert result["is_recurring"] is True

    @pytest.mark.asyncio
    async def test_sync_deadline_as_all_day_event(self, fake_db_pool, sample_organization_id, sample_google_oauth_tokens):
        """
        Test syncing assignment deadline as all-day calendar event.

        EXPECTED BEHAVIOR:
        - Creates all-day event for deadline
        - Sets reminder 1 day before
        - Includes assignment link in description
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - need integration record
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "int-123",
            "provider": "google",
            "calendar_id": "primary",
            "access_token": sample_google_oauth_tokens["access_token"]
        }

        deadline_event = {
            "assignment_id": "assign-123",
            "title": "Python Final Project Due",
            "due_date": datetime.utcnow() + timedelta(days=14),
            "type": "deadline",
            "assignment_url": "https://platform.example.com/assignments/123"
        }

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.create_google_event") as mock_create:
            mock_create.return_value = {"id": "google_deadline_xyz"}

            # Act
            result = await dao.sync_deadline_to_calendar(
                organization_id=sample_organization_id,
                deadline_event=deadline_event
            )

        # Assert
        assert result["calendar_event_id"] == "google_deadline_xyz"
        assert result["event_type"] == "all_day"

    @pytest.mark.asyncio
    async def test_sync_multiple_attendees(self, fake_db_pool, sample_organization_id, sample_course_event, sample_google_oauth_tokens):
        """
        Test syncing event with multiple attendees (instructor + students).

        EXPECTED BEHAVIOR:
        - Adds instructor as organizer
        - Adds all students as attendees
        - Sends calendar invitations
        - Tracks RSVP status
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - multiple fetchrow calls: 1) integration, 2) existing mapping
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {  # First call: get integration
                "integration_id": "int-123",
                "provider": "google",
                "calendar_id": "primary",
                "access_token": sample_google_oauth_tokens["access_token"]
            },
            None  # Second call: no existing sync mapping (create new)
        ]

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.create_google_event") as mock_create:
            mock_create.return_value = {
                "id": "google_multi_attendee_xyz",
                "attendees": [
                    {"email": "instructor@example.com", "responseStatus": "accepted"},
                    {"email": "student1@example.com", "responseStatus": "needsAction"},
                    {"email": "student2@example.com", "responseStatus": "needsAction"}
                ]
            }

            # Act
            result = await dao.sync_course_event_to_calendar(
                organization_id=sample_organization_id,
                course_event=sample_course_event
            )

        # Assert
        assert result["attendee_count"] == 3
        assert result["invitations_sent"] is True

    @pytest.mark.asyncio
    async def test_bulk_sync_course_schedule(self, fake_db_pool, sample_organization_id):
        """
        Test bulk syncing entire course schedule (10+ sessions).

        EXPECTED BEHAVIOR:
        - Batches API requests to avoid rate limits
        - Creates all events in transaction
        - Stores mapping for all events
        - Returns summary of synced events
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        course_schedule = [
            {
                "session_number": i,
                "title": f"Session {i}",
                "start_time": datetime.utcnow() + timedelta(days=7*i),
                "end_time": datetime.utcnow() + timedelta(days=7*i, hours=2)
            }
            for i in range(1, 11)  # 10 sessions
        ]

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.batch_create_google_events") as mock_batch:
            mock_batch.return_value = {
                "created_count": 10,
                "event_ids": [f"event_{i}" for i in range(10)]
            }

            # Act
            result = await dao.bulk_sync_course_schedule(
                organization_id=sample_organization_id,
                course_schedule=course_schedule
            )

        # Assert
        assert result["synced_count"] == 10
        assert len(result["event_ids"]) == 10

    @pytest.mark.asyncio
    async def test_sync_with_custom_timezone(self, fake_db_pool, sample_organization_id, sample_course_event, sample_google_oauth_tokens):
        """
        Test syncing event with custom timezone (e.g., Pacific Time).

        EXPECTED BEHAVIOR:
        - Converts event time to organization's timezone
        - Creates event with correct timezone in calendar
        - Stores timezone metadata
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - multiple fetchrow calls: 1) integration with timezone, 2) existing mapping
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {  # First call: get integration with timezone
                "integration_id": "int-123",
                "provider": "google",
                "calendar_id": "primary",
                "access_token": sample_google_oauth_tokens["access_token"],
                "timezone": "America/Los_Angeles"
            },
            None  # Second call: no existing sync mapping (create new)
        ]

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.create_google_event") as mock_create:
            mock_create.return_value = {
                "id": "event_tz_xyz",
                "start": {"dateTime": "2024-01-15T10:00:00-08:00", "timeZone": "America/Los_Angeles"}
            }

            # Act
            result = await dao.sync_course_event_to_calendar(
                organization_id=sample_organization_id,
                course_event=sample_course_event
            )

        # Assert
        assert result["timezone"] == "America/Los_Angeles"
        assert "-08:00" in str(result["start_time"])

    @pytest.mark.asyncio
    async def test_sync_fails_gracefully_on_api_error(self, fake_db_pool, sample_organization_id, sample_course_event, sample_google_oauth_tokens):
        """
        Test graceful failure when calendar API is unavailable.

        EXPECTED BEHAVIOR:
        - Catches API error
        - Logs error details
        - Marks sync as pending retry
        - Does not block course creation
        - Raises ExternalServiceException
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - multiple fetchrow calls: 1) integration, 2) existing mapping
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {  # First call: get integration
                "integration_id": "int-123",
                "provider": "google",
                "calendar_id": "primary",
                "access_token": sample_google_oauth_tokens["access_token"]
            },
            None  # Second call: no existing sync mapping (create new)
        ]

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.create_google_event") as mock_create:
            mock_create.side_effect = Exception("Google Calendar API unavailable (503)")

            # Act & Assert
            with pytest.raises(ExternalServiceException) as exc_info:
                await dao.sync_course_event_to_calendar(
                    organization_id=sample_organization_id,
                    course_event=sample_course_event
                )

            assert "api unavailable" in str(exc_info.value).lower()
            assert "503" in str(exc_info.value)


# ============================================================================
# TEST CLASS 4: Calendar Disconnect and Cleanup
# ============================================================================

@pytest.mark.skipif(CalendarIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestCalendarDisconnectAndCleanup:
    """
    Tests for disconnecting calendar integrations and cleaning up data.

    BUSINESS REQUIREMENTS:
    - Organizations can disconnect calendar integrations
    - All synced events are removed from external calendar
    - Stored tokens are securely deleted
    - Sync mappings are archived (not deleted for audit trail)
    """

    @pytest.mark.asyncio
    async def test_disconnect_google_calendar(self, fake_db_pool, sample_organization_id):
        """
        Test disconnecting Google Calendar integration.

        EXPECTED BEHAVIOR:
        - Revokes OAuth tokens with Google
        - Deletes stored credentials
        - Marks integration as inactive
        - Returns confirmation
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - fetchrow returns integration, fetch returns empty sync mappings
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "int-google-123",
            "provider": "google",
            "access_token": "ya29.TOKEN"
        }
        fake_db_pool.acquire.return_value.fetch.return_value = []  # No sync mappings

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.revoke_google_token") as mock_revoke:
            mock_revoke.return_value = {"revoked": True}

            # Act
            result = await dao.disconnect_calendar(
                organization_id=sample_organization_id,
                provider="google"
            )

        # Assert
        assert result["disconnected"] is True
        assert result["tokens_revoked"] is True
        assert result["provider"] == "google"
        mock_revoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_all_synced_events(self, fake_db_pool, sample_organization_id):
        """
        Test that disconnect removes all synced events from external calendar.

        EXPECTED BEHAVIOR:
        - Queries all event sync mappings
        - Deletes each event from Google Calendar
        - Archives sync mappings (soft delete)
        - Returns count of events removed
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - fetchrow returns integration record
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "integration_id": "int-google-123",
            "provider": "google",
            "access_token": "ya29.TOKEN"
        }

        # Arrange - 5 synced events (fetch returns sync mappings)
        fake_sync_mappings = [
            {"calendar_event_id": f"event_{i}", "course_id": f"course_{i}"}
            for i in range(5)
        ]

        fake_db_pool.acquire.return_value.fetch.return_value = fake_sync_mappings

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.batch_delete_google_events") as mock_batch_delete, \
             patch("organization_management.infrastructure.repositories.calendar_integration_dao.revoke_google_token") as mock_revoke:
            mock_batch_delete.return_value = {"deleted_count": 5}
            mock_revoke.return_value = {"revoked": True}

            # Act
            result = await dao.disconnect_calendar(
                organization_id=sample_organization_id,
                provider="google",
                remove_events=True
            )

        # Assert
        assert result["events_removed"] == 5
        assert result["sync_mappings_archived"] == 5

    @pytest.mark.asyncio
    async def test_disconnect_without_removing_events(self, fake_db_pool, sample_organization_id):
        """
        Test disconnecting calendar but keeping events (user choice).

        EXPECTED BEHAVIOR:
        - Revokes tokens
        - Does NOT delete events from calendar
        - Archives sync mappings
        - Events remain visible in user's calendar
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.revoke_google_token") as mock_revoke:
            mock_revoke.return_value = {"revoked": True}

            # Act
            result = await dao.disconnect_calendar(
                organization_id=sample_organization_id,
                provider="google",
                remove_events=False  # Keep events
            )

        # Assert
        assert result["disconnected"] is True
        assert result["events_removed"] == 0
        assert result["events_preserved"] is True

    @pytest.mark.asyncio
    async def test_disconnect_outlook_calendar(self, fake_db_pool, sample_organization_id):
        """
        Test disconnecting Outlook Calendar integration.

        EXPECTED BEHAVIOR:
        - Revokes Microsoft access
        - Deletes stored tokens
        - Marks integration inactive
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.revoke_microsoft_token") as mock_revoke:
            mock_revoke.return_value = {"revoked": True}

            # Act
            result = await dao.disconnect_calendar(
                organization_id=sample_organization_id,
                provider="outlook"
            )

        # Assert
        assert result["provider"] == "outlook"
        assert result["disconnected"] is True

    @pytest.mark.asyncio
    async def test_cleanup_expired_sync_mappings(self, fake_db_pool):
        """
        Test cleanup of sync mappings for past events (data retention).

        EXPECTED BEHAVIOR:
        - Finds sync mappings older than retention period (90 days)
        - Archives old mappings
        - Preserves recent mappings
        - Returns count of archived records
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - 10 old mappings, 5 recent mappings
        fake_db_pool.acquire.return_value.fetchval.return_value = 10

        # Act
        result = await dao.cleanup_expired_sync_mappings(
            retention_days=90
        )

        # Assert
        assert result["archived_count"] == 10
        assert result["retention_policy_days"] == 90

    @pytest.mark.asyncio
    async def test_disconnect_with_partial_failure(self, fake_db_pool, sample_organization_id):
        """
        Test disconnect when some events fail to delete from calendar.

        EXPECTED BEHAVIOR:
        - Attempts to delete all events
        - Some deletions fail (e.g., event already deleted by user)
        - Still completes disconnect
        - Returns list of failed event IDs
        - Raises ExternalServiceException with partial failure info
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        fake_sync_mappings = [
            {"calendar_event_id": f"event_{i}"}
            for i in range(5)
        ]
        fake_db_pool.acquire.return_value.fetch.return_value = fake_sync_mappings

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.batch_delete_google_events") as mock_batch_delete:
            mock_batch_delete.return_value = {
                "deleted_count": 3,
                "failed_count": 2,
                "failed_event_ids": ["event_3", "event_4"]
            }

            # Act & Assert
            with pytest.raises(ExternalServiceException) as exc_info:
                await dao.disconnect_calendar(
                    organization_id=sample_organization_id,
                    provider="google",
                    remove_events=True
                )

            assert "partial failure" in str(exc_info.value).lower()
            assert "event_3" in str(exc_info.value)


# ============================================================================
# TEST CLASS 5: Error Handling and Edge Cases
# ============================================================================

@pytest.mark.skipif(CalendarIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestCalendarIntegrationErrorHandling:
    """
    Tests for error handling and edge cases in calendar integration.

    BUSINESS REQUIREMENTS:
    - Graceful handling of API failures
    - Clear error messages for users
    - Automatic retry for transient failures
    - Fallback behavior when calendar unavailable
    """

    @pytest.mark.asyncio
    async def test_get_calendar_config_not_found(self, fake_db_pool, sample_organization_id):
        """
        Test querying calendar config when none exists.

        EXPECTED BEHAVIOR:
        - Returns None or empty result
        - Does not raise exception
        - Provides helpful message
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - no config found
        fake_db_pool.acquire.return_value.fetchrow.return_value = None

        # Act
        result = await dao.get_calendar_config(
            organization_id=sample_organization_id
        )

        # Assert
        assert result is None or result == {}

    @pytest.mark.asyncio
    async def test_sync_event_with_invalid_dates(self, fake_db_pool, sample_organization_id):
        """
        Test syncing event with invalid date range (end before start).

        EXPECTED BEHAVIOR:
        - Validates date range
        - Raises ValidationException
        - Provides clear error message
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        invalid_event = {
            "title": "Invalid Event",
            "start_time": datetime.utcnow() + timedelta(days=7),
            "end_time": datetime.utcnow() + timedelta(days=6)  # End before start!
        }

        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            await dao.sync_course_event_to_calendar(
                organization_id=sample_organization_id,
                course_event=invalid_event
            )

        # Implementation says "end time must be after start time"
        assert "end time" in str(exc_info.value).lower()
        assert "after start" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_sync_event_with_missing_required_fields(self, fake_db_pool, sample_organization_id):
        """
        Test syncing event with missing required fields.

        EXPECTED BEHAVIOR:
        - Validates required fields (title, start_time, end_time)
        - Raises ValidationException
        - Lists missing fields
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        incomplete_event = {
            "title": "Event Without Times"
            # Missing start_time and end_time
        }

        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            await dao.sync_course_event_to_calendar(
                organization_id=sample_organization_id,
                course_event=incomplete_event
            )

        assert "required field" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_database_connection_failure(self, fake_db_pool, sample_organization_id):
        """
        Test handling database connection failure.

        EXPECTED BEHAVIOR:
        - Catches connection error
        - Raises DatabaseException with context
        - Provides operation name in error
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - database connection fails (use ConnectionRefusedError as asyncpg.ConnectionError doesn't exist)
        fake_db_pool.acquire.side_effect = ConnectionRefusedError("Could not connect to database")

        # Act & Assert
        with pytest.raises(DatabaseException) as exc_info:
            await dao.get_calendar_config(
                organization_id=sample_organization_id
            )

        assert "database" in str(exc_info.value).lower() or "calendar" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_calendar_api_network_timeout(self, fake_db_pool, sample_organization_id, sample_course_event, sample_google_oauth_tokens):
        """
        Test handling network timeout when calling calendar API.

        EXPECTED BEHAVIOR:
        - Catches timeout exception
        - Raises ExternalServiceException
        - Marks event sync for retry
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - multiple fetchrow calls: 1) integration, 2) existing mapping
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {  # First call: get integration
                "integration_id": "int-123",
                "provider": "google",
                "calendar_id": "primary",
                "access_token": sample_google_oauth_tokens["access_token"]
            },
            None  # Second call: no existing sync mapping (create new)
        ]

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.create_google_event") as mock_create:
            mock_create.side_effect = Exception("Request timeout after 30 seconds")

            # Act & Assert
            with pytest.raises(ExternalServiceException) as exc_info:
                await dao.sync_course_event_to_calendar(
                    organization_id=sample_organization_id,
                    course_event=sample_course_event
                )

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_token_encryption_key_missing(self, fake_db_pool, sample_organization_id):
        """
        Test behavior when token encryption key is not configured.

        EXPECTED BEHAVIOR:
        - Detects missing encryption key
        - Raises ValidationException
        - Prevents storing tokens in plaintext
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        with patch.dict("os.environ", {}, clear=True):  # Clear environment
            # Act & Assert
            with pytest.raises(ValidationException) as exc_info:
                await dao.store_oauth_tokens(
                    organization_id=sample_organization_id,
                    tokens={"access_token": "token123"}
                )

            assert "encryption" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_sync_event_exceeds_calendar_limits(self, fake_db_pool, sample_organization_id):
        """
        Test syncing event that exceeds calendar provider limits.

        EXPECTED BEHAVIOR:
        - Detects limit violation (e.g., 100+ attendees for Google)
        - Raises ValidationException
        - Suggests workaround (split into multiple events)
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        large_event = {
            "title": "Mass Course Enrollment",
            "start_time": datetime.utcnow() + timedelta(days=7),
            "end_time": datetime.utcnow() + timedelta(days=7, hours=2),
            "attendee_emails": [f"student{i}@example.com" for i in range(150)]  # Exceeds Google limit
        }

        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            await dao.sync_course_event_to_calendar(
                organization_id=sample_organization_id,
                course_event=large_event
            )

        assert "attendee" in str(exc_info.value).lower()
        assert "limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_concurrent_sync_conflict(self, fake_db_pool, sample_organization_id, sample_course_event, sample_google_oauth_tokens):
        """
        Test handling concurrent sync operations causing conflicts.

        EXPECTED BEHAVIOR:
        - Detects concurrent modification
        - Uses optimistic locking or transaction isolation
        - Raises ConflictException
        - Suggests retry
        """
        dao = CalendarIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - multiple fetchrow calls: 1) integration, 2) existing mapping
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {  # First call: get integration
                "integration_id": "int-123",
                "provider": "google",
                "calendar_id": "primary",
                "access_token": sample_google_oauth_tokens["access_token"]
            },
            None  # Second call: no existing sync mapping (create new)
        ]

        # Configure execute to raise UniqueViolationError when storing sync mapping
        import asyncpg
        fake_db_pool.acquire.return_value.execute.side_effect = \
            asyncpg.UniqueViolationError("duplicate key value violates unique constraint")

        with patch("organization_management.infrastructure.repositories.calendar_integration_dao.create_google_event") as mock_create:
            mock_create.return_value = {"id": "google_event_xyz", "htmlLink": "https://calendar.google.com/event?eid=xyz"}

            # Act & Assert
            with pytest.raises(ConflictException) as exc_info:
                await dao.sync_course_event_to_calendar(
                    organization_id=sample_organization_id,
                    course_event=sample_course_event
                )

            assert "concurrent" in str(exc_info.value).lower() or "already exists" in str(exc_info.value).lower()
