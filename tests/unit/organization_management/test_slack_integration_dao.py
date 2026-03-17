"""
SlackIntegrationDAO Unit Tests - TDD RED Phase

BUSINESS CONTEXT:
The SlackIntegrationDAO handles Slack workspace integration functionality for organizations,
allowing course notifications, announcements, and alerts to be sent to Slack channels.

REFACTORING CONTEXT:
This test file is part of the IntegrationsDAO god class refactoring (2,911 lines → 5 specialized DAOs).
The SlackIntegrationDAO will be extracted to handle ONLY Slack-related operations.

TEST COVERAGE (TDD RED Phase):
1. Slack OAuth and Workspace Connection (7 tests)
2. Channel Management and Discovery (5 tests)
3. Message Posting and Notifications (8 tests)
4. Slash Command Integration (5 tests)
5. Error Handling and Rate Limiting (7 tests)

DEPENDENCIES:
- Custom exceptions from shared/exceptions/__init__.py
- Slack SDK (slack_sdk)
- Slack OAuth flow (slack_sdk.oauth)
- Slack Web API (slack_sdk.web)

EXPECTED BEHAVIOR (TDD RED - These tests WILL FAIL until implementation):
All tests define the DESIRED behavior for the SlackIntegrationDAO.
Implementation should follow the Clean Architecture pattern:
- Domain layer: Slack message entities
- Application layer: Slack notification service
- Infrastructure layer: SlackIntegrationDAO (database + API operations)

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

# These imports will fail until the SlackIntegrationDAO is created (TDD RED phase)
try:
    from organization_management.infrastructure.repositories.slack_integration_dao import SlackIntegrationDAO
except ImportError:
    SlackIntegrationDAO = None  # Expected during RED phase

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

    # Configure for direct await pattern (used by SlackIntegrationDAO implementation)
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
def sample_slack_workspace():
    """Sample Slack workspace configuration."""
    return {
        "team_id": "T0123456789",
        "team_name": "Tech University",
        "team_domain": "techuni",
        "team_url": "https://techuni.slack.com"
    }


@pytest.fixture
def sample_slack_oauth_tokens():
    """Sample Slack OAuth tokens (bot and user tokens)."""
    return {
        "access_token": "test-fake-slack-bot-token-not-real-1234567890",
        "token_type": "bot",
        "scope": "channels:read,chat:write,commands,users:read",
        "bot_user_id": "U0123BOTUSER",
        "app_id": "A0123456789",
        "expires_in": None  # Slack bot tokens don't expire
    }


@pytest.fixture
def sample_slack_channel():
    """Sample Slack channel information."""
    return {
        "id": "C0123456789",
        "name": "course-announcements",
        "is_channel": True,
        "is_private": False,
        "num_members": 42
    }


@pytest.fixture
def sample_course_announcement():
    """Sample course announcement to post to Slack."""
    return {
        "course_id": "course-123",
        "title": "New Python Course Starting Next Week",
        "message": "Registration is now open for Introduction to Python Programming. The course starts on Monday, January 15th.",
        "instructor": "Dr. Smith",
        "url": "https://platform.example.com/courses/123"
    }


# ============================================================================
# TEST CLASS 1: Slack OAuth and Workspace Connection
# ============================================================================

@pytest.mark.skipif(SlackIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestSlackOAuthAndWorkspaceConnection:
    """
    Tests for Slack OAuth integration and workspace connection.

    BUSINESS REQUIREMENTS:
    - Organizations can connect their Slack workspace
    - OAuth 2.0 authorization flow must be secure
    - Bot token and user token must be stored separately
    - Workspace metadata must be cached
    """

    @pytest.mark.asyncio
    async def test_initiate_slack_oauth_flow(self, fake_db_pool, sample_organization_id):
        """
        Test initiating Slack OAuth authorization flow.

        EXPECTED BEHAVIOR:
        - Generates authorization URL with correct scopes
        - Stores state parameter securely
        - Requests bot token (not just user token)
        - Returns authorization URL for admin redirect
        """
        import urllib.parse
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - no existing integration
        fake_db_pool.acquire.return_value.fetchrow.return_value = None

        # Act
        result = await dao.initiate_slack_oauth(
            organization_id=sample_organization_id,
            redirect_uri="https://platform.example.com/integrations/slack/callback"
        )

        # Assert
        assert result["provider"] == "slack"
        assert result["authorization_url"].startswith("https://slack.com/oauth/v2/authorize")
        assert "state" in result
        # URL-decode the authorization URL to check scopes (urllib.parse.urlencode encodes colons)
        decoded_url = urllib.parse.unquote(result["authorization_url"])
        assert "channels:read" in decoded_url
        assert "chat:write" in decoded_url
        assert "commands" in decoded_url

    @pytest.mark.asyncio
    async def test_complete_slack_oauth_flow(self, fake_db_pool, sample_organization_id, sample_slack_oauth_tokens, sample_slack_workspace):
        """
        Test completing Slack OAuth flow with authorization code.

        EXPECTED BEHAVIOR:
        - Exchanges authorization code for bot token
        - Stores workspace metadata (team_id, team_name)
        - Stores bot token securely
        - Fetches available channels
        - Returns workspace info
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)
        state = "valid-state-token"

        # Arrange - mock state verification and integration insert
        fake_db_pool.acquire.return_value.fetchrow.side_effect = [
            {"state": state},  # First call: state verification
            {"integration_id": "slack-int-123", "team_id": sample_slack_workspace["team_id"], "team_name": sample_slack_workspace["team_name"], "bot_user_id": sample_slack_oauth_tokens["bot_user_id"], "status": "active"}  # Second call: insert returning
        ]

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.exchange_slack_code") as mock_exchange:
            mock_exchange.return_value = {
                **sample_slack_oauth_tokens,
                "team": sample_slack_workspace
            }

            # Act
            result = await dao.complete_slack_oauth(
                organization_id=sample_organization_id,
                authorization_code="1234567890.1234567890.abcdef",
                state=state
            )

        # Assert
        assert result["workspace"]["team_id"] == "T0123456789"
        assert result["workspace"]["team_name"] == "Tech University"
        assert result["bot_user_id"] == "U0123BOTUSER"
        assert result["status"] == "connected"

    @pytest.mark.asyncio
    async def test_slack_oauth_with_invalid_state(self, fake_db_pool, sample_organization_id):
        """
        Test OAuth callback with invalid state parameter (security check).

        EXPECTED BEHAVIOR:
        - Validates state parameter matches stored state
        - Raises AuthenticationException on mismatch
        - Does not exchange authorization code
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - state mismatch
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "stored_state": "valid-state-123"
        }

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            await dao.complete_slack_oauth(
                organization_id=sample_organization_id,
                authorization_code="code123",
                state="invalid-state-456"
            )

        assert "state mismatch" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_slack_oauth_duplicate_workspace_connection(self, fake_db_pool, sample_organization_id, sample_slack_workspace):
        """
        Test attempting to connect Slack workspace when already connected.

        EXPECTED BEHAVIOR:
        - Checks for existing workspace connection (by team_id)
        - Raises ConflictException if already connected
        - Provides option to disconnect and reconnect
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - existing connection
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "integration_id": "existing-slack-123",
            "team_id": sample_slack_workspace["team_id"],
            "status": "active"
        }

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            await dao.initiate_slack_oauth(
                organization_id=sample_organization_id,
                redirect_uri="https://platform.example.com/callback"
            )

        assert "already connected" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_slack_oauth_insufficient_scopes(self, fake_db_pool, sample_organization_id):
        """
        Test OAuth completion when admin grants insufficient scopes.

        EXPECTED BEHAVIOR:
        - Validates required scopes were granted
        - Raises ValidationException if critical scopes missing
        - Lists required vs granted scopes
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)
        state = "valid-state"

        # Arrange - state verification passes
        fake_db_pool.acquire.return_value.fetchrow.return_value = {"state": state}

        insufficient_tokens = {
            "access_token": "xoxb-LIMITED",
            "scope": "channels:read",  # Missing chat:write, commands
            "token_type": "bot"
        }

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.exchange_slack_code") as mock_exchange:
            mock_exchange.return_value = insufficient_tokens

            # Act & Assert
            with pytest.raises(ValidationException) as exc_info:
                await dao.complete_slack_oauth(
                    organization_id=sample_organization_id,
                    authorization_code="code",
                    state=state
                )

            assert "chat:write" in str(exc_info.value) or "scope" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_slack_workspace_info(self, fake_db_pool, sample_organization_id, sample_slack_workspace):
        """
        Test retrieving connected Slack workspace information.

        EXPECTED BEHAVIOR:
        - Queries workspace metadata from database
        - Returns team info (name, domain, URL)
        - Returns bot user ID
        - Returns connection status
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "integration_id": "slack-int-123",
            "team_id": sample_slack_workspace["team_id"],
            "team_name": sample_slack_workspace["team_name"],
            "team_domain": sample_slack_workspace["team_domain"],
            "bot_user_id": "U0123BOTUSER",
            "status": "active"
        }

        # Act
        result = await dao.get_workspace_info(
            organization_id=sample_organization_id
        )

        # Assert
        assert result["team_name"] == "Tech University"
        assert result["team_id"] == "T0123456789"
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_slack_workspace_not_connected(self, fake_db_pool, sample_organization_id):
        """
        Test querying workspace info when Slack not connected.

        EXPECTED BEHAVIOR:
        - Returns None or raises NotFoundException
        - Provides clear message that workspace not connected
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - no connection
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            await dao.get_workspace_info(
                organization_id=sample_organization_id
            )

        assert "not connected" in str(exc_info.value).lower()


# ============================================================================
# TEST CLASS 2: Channel Management and Discovery
# ============================================================================

@pytest.mark.skipif(SlackIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestSlackChannelManagement:
    """
    Tests for Slack channel discovery and management.

    BUSINESS REQUIREMENTS:
    - Fetch list of available channels in workspace
    - Allow selection of default announcement channel
    - Support both public and private channels
    - Cache channel list for performance
    """

    @pytest.mark.asyncio
    async def test_fetch_available_channels(self, fake_db_pool, sample_organization_id, sample_slack_oauth_tokens):
        """
        Test fetching list of available Slack channels.

        EXPECTED BEHAVIOR:
        - Uses Slack Web API conversations.list
        - Returns public channels
        - Filters archived channels
        - Returns channel metadata (id, name, member count)
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        fake_channels = [
            {"id": "C001", "name": "general", "is_archived": False, "num_members": 100},
            {"id": "C002", "name": "course-announcements", "is_archived": False, "num_members": 42},
            {"id": "C003", "name": "old-channel", "is_archived": True, "num_members": 5}
        ]

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.fetch_slack_channels") as mock_fetch:
            mock_fetch.return_value = fake_channels

            # Act
            result = await dao.get_available_channels(
                organization_id=sample_organization_id
            )

        # Assert
        assert len(result["channels"]) == 2  # Archived channel filtered out
        assert result["channels"][0]["name"] == "general"
        assert result["channels"][1]["name"] == "course-announcements"

    @pytest.mark.asyncio
    async def test_set_default_announcement_channel(self, fake_db_pool, sample_organization_id, sample_slack_channel):
        """
        Test setting default channel for course announcements.

        EXPECTED BEHAVIOR:
        - Validates channel exists in workspace
        - Stores channel configuration
        - Returns confirmation
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Act
        result = await dao.set_default_channel(
            organization_id=sample_organization_id,
            channel_id=sample_slack_channel["id"],
            channel_name=sample_slack_channel["name"],
            purpose="course_announcements"
        )

        # Assert
        assert result["channel_id"] == "C0123456789"
        assert result["purpose"] == "course_announcements"
        assert result["configured"] is True

    @pytest.mark.asyncio
    async def test_get_default_channels(self, fake_db_pool, sample_organization_id):
        """
        Test retrieving configured default channels by purpose.

        EXPECTED BEHAVIOR:
        - Returns channels for different purposes (announcements, grades, alerts)
        - Returns empty list if no channels configured
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetch.return_value = [
            {"channel_id": "C001", "channel_name": "announcements", "purpose": "course_announcements"},
            {"channel_id": "C002", "channel_name": "grades", "purpose": "grade_notifications"}
        ]

        # Act
        result = await dao.get_default_channels(
            organization_id=sample_organization_id
        )

        # Assert
        assert len(result["channels"]) == 2
        assert result["channels"]["course_announcements"]["channel_id"] == "C001"
        assert result["channels"]["grade_notifications"]["channel_id"] == "C002"

    @pytest.mark.asyncio
    async def test_validate_channel_permissions(self, fake_db_pool, sample_organization_id):
        """
        Test validating bot has permissions to post to channel.

        EXPECTED BEHAVIOR:
        - Checks if bot is member of channel
        - Attempts test message (or dry run)
        - Returns permission status
        - Raises ValidationException if no permission
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.check_channel_membership") as mock_check:
            mock_check.return_value = {"is_member": False}

            # Act & Assert
            with pytest.raises(ValidationException) as exc_info:
                await dao.validate_channel_permissions(
                    organization_id=sample_organization_id,
                    channel_id="C0123456789"
                )

            assert "not a member" in str(exc_info.value).lower() or "permission" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_fetch_private_channels_requires_permission(self, fake_db_pool, sample_organization_id):
        """
        Test that fetching private channels requires special permission.

        EXPECTED BEHAVIOR:
        - Attempts to fetch private channels
        - Requires groups:read scope
        - Raises ValidationException if scope missing
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.fetch_slack_channels") as mock_fetch:
            mock_fetch.side_effect = Exception("missing_scope: groups:read")

            # Act & Assert
            with pytest.raises(ValidationException) as exc_info:
                await dao.get_available_channels(
                    organization_id=sample_organization_id,
                    include_private=True
                )

            assert "scope" in str(exc_info.value).lower()


# ============================================================================
# TEST CLASS 3: Message Posting and Notifications
# ============================================================================

@pytest.mark.skipif(SlackIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestSlackMessagePostingAndNotifications:
    """
    Tests for posting messages and notifications to Slack.

    BUSINESS REQUIREMENTS:
    - Post course announcements to configured channels
    - Send grade notifications to individual students
    - Alert instructors about assignment submissions
    - Format messages with Slack Block Kit
    - Support attachments and rich formatting
    """

    @pytest.mark.asyncio
    async def test_post_course_announcement(self, fake_db_pool, sample_organization_id, sample_course_announcement):
        """
        Test posting course announcement to Slack channel.

        EXPECTED BEHAVIOR:
        - Uses Slack Block Kit for rich formatting
        - Posts to configured announcement channel
        - Includes course link button
        - Stores message timestamp for updates/deletes
        - Returns message permalink
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "channel_id": "C001",
            "bot_token": "xoxb-valid-token"
        }

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.return_value = {
                "ok": True,
                "ts": "1234567890.123456",
                "channel": "C001",
                "message": {"text": sample_course_announcement["message"]}
            }

            # Act
            result = await dao.post_course_announcement(
                organization_id=sample_organization_id,
                announcement=sample_course_announcement
            )

        # Assert
        assert result["posted"] is True
        assert result["message_ts"] == "1234567890.123456"
        assert result["channel_id"] == "C001"

    @pytest.mark.asyncio
    async def test_post_message_with_blocks(self, fake_db_pool, sample_organization_id):
        """
        Test posting message with Slack Block Kit formatting.

        EXPECTED BEHAVIOR:
        - Accepts blocks array for rich formatting
        - Supports header, section, divider, button blocks
        - Validates block structure
        - Posts formatted message
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        message_blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "New Course Available"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Introduction to Python* starts next week!"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Course"},
                        "url": "https://platform.example.com/courses/123"
                    }
                ]
            }
        ]

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.return_value = {"ok": True, "ts": "123.456"}

            # Act
            result = await dao.post_message(
                organization_id=sample_organization_id,
                channel_id="C001",
                blocks=message_blocks
            )

        # Assert
        assert result["posted"] is True
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_direct_message_to_user(self, fake_db_pool, sample_organization_id):
        """
        Test sending direct message to specific Slack user.

        EXPECTED BEHAVIOR:
        - Looks up user by email or Slack user ID
        - Opens DM channel
        - Sends message to user
        - Used for grade notifications or private alerts
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.open_dm_channel") as mock_open, \
             patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_open.return_value = {"channel": {"id": "D0123456789"}}
            mock_post.return_value = {"ok": True, "ts": "123.456"}

            # Act
            result = await dao.send_direct_message(
                organization_id=sample_organization_id,
                user_email="student@example.com",
                message="Your assignment has been graded: A+"
            )

        # Assert
        assert result["sent"] is True
        assert result["dm_channel_id"] == "D0123456789"

    @pytest.mark.asyncio
    async def test_update_existing_message(self, fake_db_pool, sample_organization_id):
        """
        Test updating an existing Slack message.

        EXPECTED BEHAVIOR:
        - Uses stored message timestamp
        - Updates message text/blocks
        - Preserves channel and thread
        - Used for editing announcements
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.update_slack_message") as mock_update:
            mock_update.return_value = {"ok": True, "ts": "123.456"}

            # Act
            result = await dao.update_message(
                organization_id=sample_organization_id,
                channel_id="C001",
                message_ts="123.456",
                new_text="Updated announcement: Course delayed to next Tuesday"
            )

        # Assert
        assert result["updated"] is True

    @pytest.mark.asyncio
    async def test_delete_message(self, fake_db_pool, sample_organization_id):
        """
        Test deleting a Slack message.

        EXPECTED BEHAVIOR:
        - Uses stored message timestamp
        - Deletes message from channel
        - Removes message tracking record
        - Used for removing outdated announcements
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.delete_slack_message") as mock_delete:
            mock_delete.return_value = {"ok": True}

            # Act
            result = await dao.delete_message(
                organization_id=sample_organization_id,
                channel_id="C001",
                message_ts="123.456"
            )

        # Assert
        assert result["deleted"] is True

    @pytest.mark.asyncio
    async def test_post_threaded_reply(self, fake_db_pool, sample_organization_id):
        """
        Test posting message as thread reply.

        EXPECTED BEHAVIOR:
        - Uses parent message timestamp
        - Posts message in thread
        - Preserves thread context
        - Used for Q&A in announcement threads
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.return_value = {"ok": True, "ts": "123.457", "thread_ts": "123.456"}

            # Act
            result = await dao.post_threaded_reply(
                organization_id=sample_organization_id,
                channel_id="C001",
                thread_ts="123.456",
                text="For more information, contact Dr. Smith"
            )

        # Assert
        assert result["posted"] is True
        assert result["thread_ts"] == "123.456"

    @pytest.mark.asyncio
    async def test_post_with_file_attachment(self, fake_db_pool, sample_organization_id):
        """
        Test posting message with file attachment (e.g., syllabus PDF).

        EXPECTED BEHAVIOR:
        - Uploads file to Slack
        - Posts message with file attached
        - Supports PDF, images, documents
        - Returns file URL
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.upload_slack_file") as mock_upload, \
             patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_upload.return_value = {"ok": True, "file": {"id": "F0123456789", "permalink": "https://files.slack.com/..."}}
            mock_post.return_value = {"ok": True, "ts": "123.456"}

            # Act
            result = await dao.post_with_attachment(
                organization_id=sample_organization_id,
                channel_id="C001",
                text="Course syllabus attached",
                file_path="/path/to/syllabus.pdf",
                filename="python_course_syllabus.pdf"
            )

        # Assert
        assert result["posted"] is True
        assert result["file_id"] == "F0123456789"

    @pytest.mark.asyncio
    async def test_post_message_with_mentions(self, fake_db_pool, sample_organization_id):
        """
        Test posting message with user mentions (@username).

        EXPECTED BEHAVIOR:
        - Formats mentions as <@USER_ID>
        - Notifies mentioned users
        - Supports @channel, @here mentions
        - Used for urgent alerts
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.return_value = {"ok": True, "ts": "123.456"}

            # Act
            result = await dao.post_message(
                organization_id=sample_organization_id,
                channel_id="C001",
                text="<!here> Assignment deadline extended by 24 hours"
            )

        # Assert
        assert result["posted"] is True


# ============================================================================
# TEST CLASS 4: Slash Command Integration
# ============================================================================

@pytest.mark.skipif(SlackIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestSlackSlashCommandIntegration:
    """
    Tests for Slack slash command integration.

    BUSINESS REQUIREMENTS:
    - Support custom slash commands (e.g., /course-status)
    - Validate request signature for security
    - Respond within 3-second timeout
    - Support ephemeral responses (visible only to user)
    """

    @pytest.mark.asyncio
    async def test_register_slash_command(self, fake_db_pool, sample_organization_id):
        """
        Test registering a new slash command.

        EXPECTED BEHAVIOR:
        - Stores command configuration
        - Sets webhook URL for command responses
        - Returns command metadata
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        command_config = {
            "command": "/course-status",
            "description": "Check status of your enrolled courses",
            "usage_hint": "/course-status [course-id]",
            "webhook_url": "https://platform.example.com/slack/commands/course-status"
        }

        # Act
        result = await dao.register_slash_command(
            organization_id=sample_organization_id,
            command_config=command_config
        )

        # Assert
        assert result["command"] == "/course-status"
        assert result["registered"] is True

    @pytest.mark.asyncio
    async def test_validate_slash_command_request(self, fake_db_pool, sample_organization_id):
        """
        Test validating incoming slash command request signature.

        EXPECTED BEHAVIOR:
        - Validates request timestamp (replay attack prevention)
        - Validates HMAC signature using signing secret
        - Raises AuthenticationException if invalid
        """
        import time
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Arrange - mock the integration with a signing secret
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "signing_secret": "test_signing_secret_12345"
        }

        # Invalid signature with current timestamp
        current_timestamp = str(int(time.time()))
        request_data = {
            "timestamp": current_timestamp,
            "signature": "v0=invalid_signature",
            "body": "command=/test&user_id=U123"
        }

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            await dao.validate_command_request(
                organization_id=sample_organization_id,
                request_data=request_data
            )

        assert "signature" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_respond_to_slash_command_ephemeral(self, fake_db_pool, sample_organization_id):
        """
        Test responding to slash command with ephemeral message.

        EXPECTED BEHAVIOR:
        - Sends response visible only to command user
        - Does not post to channel
        - Used for status checks, errors
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.return_value = {"ok": True}

            # Act
            result = await dao.respond_to_command(
                organization_id=sample_organization_id,
                response_url="https://hooks.slack.com/commands/...",
                text="You are enrolled in 3 courses",
                response_type="ephemeral"
            )

        # Assert
        assert result["sent"] is True
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_respond_to_slash_command_in_channel(self, fake_db_pool, sample_organization_id):
        """
        Test responding to slash command with in-channel message.

        EXPECTED BEHAVIOR:
        - Sends response visible to entire channel
        - Used for public commands like /announce
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.return_value = {"ok": True}

            # Act
            result = await dao.respond_to_command(
                organization_id=sample_organization_id,
                response_url="https://hooks.slack.com/commands/...",
                text="Course announcement: Python 101 starts Monday",
                response_type="in_channel"
            )

        # Assert
        assert result["sent"] is True

    @pytest.mark.asyncio
    async def test_slash_command_response_timeout(self, fake_db_pool, sample_organization_id):
        """
        Test handling slash command response timeout (3 seconds).

        EXPECTED BEHAVIOR:
        - Sends immediate acknowledgment
        - Processes command asynchronously
        - Sends follow-up message with result
        - Used for long-running commands
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.return_value = {"ok": True}

            # Act
            result = await dao.respond_with_delayed_result(
                organization_id=sample_organization_id,
                response_url="https://hooks.slack.com/commands/...",
                initial_text="Processing your request...",
                result_text="Here are your course statistics: ..."
            )

        # Assert
        assert result["acknowledged"] is True
        assert result["result_sent"] is True


# ============================================================================
# TEST CLASS 5: Error Handling and Rate Limiting
# ============================================================================

@pytest.mark.skipif(SlackIntegrationDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestSlackErrorHandlingAndRateLimiting:
    """
    Tests for Slack API error handling and rate limiting.

    BUSINESS REQUIREMENTS:
    - Handle Slack API rate limits (Tier 1: 1/min, Tier 2: 20/min, Tier 3: 50/min)
    - Graceful degradation when Slack is unavailable
    - Clear error messages for common failures
    - Automatic token refresh if needed
    """

    @pytest.mark.asyncio
    async def test_slack_api_rate_limit_handling(self, fake_db_pool, sample_organization_id):
        """
        Test handling Slack API rate limit (429 Too Many Requests).

        EXPECTED BEHAVIOR:
        - Catches rate limit error
        - Extracts Retry-After header
        - Raises RateLimitException with retry time
        - Queues message for retry
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.side_effect = Exception("rate_limited: Retry-After 60")

            # Act & Assert
            with pytest.raises(RateLimitException) as exc_info:
                await dao.post_message(
                    organization_id=sample_organization_id,
                    channel_id="C001",
                    text="Test message"
                )

            assert "rate limit" in str(exc_info.value).lower()
            assert "60" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_slack_token_revoked(self, fake_db_pool, sample_organization_id):
        """
        Test handling revoked Slack token.

        EXPECTED BEHAVIOR:
        - Detects token_revoked error
        - Marks integration as inactive
        - Raises AuthenticationException
        - Notifies org admin to reconnect
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.side_effect = Exception("token_revoked: The token has been revoked")

            # Act & Assert
            with pytest.raises(AuthenticationException) as exc_info:
                await dao.post_message(
                    organization_id=sample_organization_id,
                    channel_id="C001",
                    text="Test"
                )

            assert "revoked" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_slack_channel_not_found(self, fake_db_pool, sample_organization_id):
        """
        Test posting to non-existent or archived channel.

        EXPECTED BEHAVIOR:
        - Detects channel_not_found error
        - Raises NotFoundException
        - Suggests checking channel configuration
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.side_effect = Exception("channel_not_found")

            # Act & Assert
            with pytest.raises(NotFoundException) as exc_info:
                await dao.post_message(
                    organization_id=sample_organization_id,
                    channel_id="C_NONEXISTENT",
                    text="Test"
                )

            assert "channel" in str(exc_info.value).lower()
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_slack_api_unavailable(self, fake_db_pool, sample_organization_id):
        """
        Test handling Slack API downtime.

        EXPECTED BEHAVIOR:
        - Catches connection/timeout errors
        - Raises ExternalServiceException
        - Marks message for retry
        - Does not block course operations
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.side_effect = Exception("Slack API unavailable (503)")

            # Act & Assert
            with pytest.raises(ExternalServiceException) as exc_info:
                await dao.post_message(
                    organization_id=sample_organization_id,
                    channel_id="C001",
                    text="Test"
                )

            assert "unavailable" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_slack_message_too_large(self, fake_db_pool, sample_organization_id):
        """
        Test posting message exceeding Slack size limits (40,000 chars).

        EXPECTED BEHAVIOR:
        - Validates message size
        - Raises ValidationException if too large
        - Suggests truncation or file attachment
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        huge_message = "A" * 50000  # Exceeds 40k limit

        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            await dao.post_message(
                organization_id=sample_organization_id,
                channel_id="C001",
                text=huge_message
            )

        assert "size" in str(exc_info.value).lower() or "limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_database_connection_failure(self, fake_db_pool, sample_organization_id):
        """
        Test handling database connection failure.

        EXPECTED BEHAVIOR:
        - Catches connection errors
        - Raises DatabaseException with context
        - Does not expose internal error details
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        # Use ConnectionRefusedError as asyncpg.ConnectionError doesn't exist
        fake_db_pool.acquire.side_effect = ConnectionRefusedError("DB unavailable")

        # Act & Assert
        with pytest.raises(DatabaseException) as exc_info:
            await dao.get_workspace_info(
                organization_id=sample_organization_id
            )

        assert "database" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_slack_workspace_deactivated(self, fake_db_pool, sample_organization_id):
        """
        Test handling deactivated Slack workspace.

        EXPECTED BEHAVIOR:
        - Detects account_inactive error
        - Marks integration as inactive
        - Raises AuthenticationException
        - Provides clear guidance to user
        """
        dao = SlackIntegrationDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.slack_integration_dao.post_slack_message") as mock_post:
            mock_post.side_effect = Exception("account_inactive: Workspace has been deactivated")

            # Act & Assert
            with pytest.raises(AuthenticationException) as exc_info:
                await dao.post_message(
                    organization_id=sample_organization_id,
                    channel_id="C001",
                    text="Test"
                )

            assert "inactive" in str(exc_info.value).lower() or "deactivated" in str(exc_info.value).lower()
