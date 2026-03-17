"""
SlackIntegrationDAO - Slack Integration Data Access Object

BUSINESS CONTEXT:
The SlackIntegrationDAO handles Slack workspace integration functionality for organizations,
allowing course notifications, announcements, and alerts to be sent to Slack channels.

REFACTORING CONTEXT:
Extracted from IntegrationsDAO god class (2,911 lines → 5 specialized DAOs).
This DAO handles ONLY Slack-related operations.

ARCHITECTURE:
Following Clean Architecture patterns:
- Domain layer: Slack message entities
- Application layer: Slack notification service (future)
- Infrastructure layer: This DAO (database + Slack API operations)

EXTERNAL INTEGRATIONS:
- Slack OAuth 2.0 flow
- Slack Web API (chat.postMessage, files.upload, etc.)
- Slack Events API (slash commands)

Related Files:
- services/organization-management/organization_management/domain/entities/integrations.py
- tests/unit/organization_management/test_slack_integration_dao.py (32 tests)
"""

import asyncpg
import hashlib
import hmac
import logging
import json
import os
import re
import secrets
import time
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

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
# SLACK OAUTH CONFIGURATION
# ============================================================================

SLACK_OAUTH_CONFIG = {
    "authorize_url": "https://slack.com/oauth/v2/authorize",
    "token_url": "https://slack.com/api/oauth.v2.access",
    "scopes": [
        "channels:read",
        "chat:write",
        "commands",
        "users:read",
        "users:read.email",
        "files:write",
        "groups:read"
    ],
    "required_scopes": ["channels:read", "chat:write", "commands"]
}

# Slack message size limit (characters)
SLACK_MESSAGE_SIZE_LIMIT = 40000


# ============================================================================
# MODULE-LEVEL STUB FUNCTIONS (for external API calls - mock in tests)
# ============================================================================

def exchange_slack_code(
    authorization_code: str,
    redirect_uri: str
) -> Dict[str, Any]:
    """
    Exchange authorization code for Slack OAuth tokens.

    This is a stub function that should be mocked in tests.
    In production, this would call Slack's oauth.v2.access endpoint.

    Args:
        authorization_code: The code from Slack OAuth callback
        redirect_uri: The registered redirect URI

    Returns:
        Dictionary with access_token, team info, bot_user_id, etc.
    """
    raise ExternalServiceException(
        message="Slack code exchange not implemented. Mock this function in tests.",
        service_name_external="Slack"
    )


def fetch_slack_channels(
    bot_token: str,
    include_private: bool = False
) -> List[Dict[str, Any]]:
    """
    Fetch available channels from Slack workspace.

    This is a stub function that should be mocked in tests.
    In production, this would call Slack's conversations.list API.

    Args:
        bot_token: The Slack bot token
        include_private: Whether to include private channels

    Returns:
        List of channel dictionaries with id, name, is_archived, num_members
    """
    raise ExternalServiceException(
        message="Slack channels fetch not implemented. Mock this function in tests.",
        service_name_external="Slack"
    )


def check_channel_membership(
    bot_token: str,
    channel_id: str
) -> Dict[str, Any]:
    """
    Check if bot is member of a channel.

    This is a stub function that should be mocked in tests.

    Args:
        bot_token: The Slack bot token
        channel_id: The channel ID to check

    Returns:
        Dictionary with is_member boolean
    """
    raise ExternalServiceException(
        message="Channel membership check not implemented. Mock this function in tests.",
        service_name_external="Slack"
    )


def post_slack_message(
    bot_token: str,
    channel_id: str,
    text: Optional[str] = None,
    blocks: Optional[List[Dict]] = None,
    thread_ts: Optional[str] = None,
    response_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Post a message to a Slack channel.

    This is a stub function that should be mocked in tests.
    In production, this would call Slack's chat.postMessage API.

    Args:
        bot_token: The Slack bot token
        channel_id: The channel to post to
        text: Plain text message
        blocks: Block Kit blocks for rich formatting
        thread_ts: Parent message timestamp for threading
        response_url: Webhook URL for slash command responses

    Returns:
        Dictionary with ok, ts (timestamp), channel, message
    """
    raise ExternalServiceException(
        message="Slack message posting not implemented. Mock this function in tests.",
        service_name_external="Slack"
    )


def update_slack_message(
    bot_token: str,
    channel_id: str,
    message_ts: str,
    text: Optional[str] = None,
    blocks: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Update an existing Slack message.

    This is a stub function that should be mocked in tests.

    Args:
        bot_token: The Slack bot token
        channel_id: The channel containing the message
        message_ts: The message timestamp to update
        text: New text content
        blocks: New Block Kit blocks

    Returns:
        Dictionary with ok, ts
    """
    raise ExternalServiceException(
        message="Slack message update not implemented. Mock this function in tests.",
        service_name_external="Slack"
    )


def delete_slack_message(
    bot_token: str,
    channel_id: str,
    message_ts: str
) -> Dict[str, Any]:
    """
    Delete a Slack message.

    This is a stub function that should be mocked in tests.

    Args:
        bot_token: The Slack bot token
        channel_id: The channel containing the message
        message_ts: The message timestamp to delete

    Returns:
        Dictionary with ok
    """
    raise ExternalServiceException(
        message="Slack message deletion not implemented. Mock this function in tests.",
        service_name_external="Slack"
    )


def open_dm_channel(
    bot_token: str,
    user_email: str
) -> Dict[str, Any]:
    """
    Open a DM channel with a user by email.

    This is a stub function that should be mocked in tests.

    Args:
        bot_token: The Slack bot token
        user_email: The user's email address

    Returns:
        Dictionary with channel info
    """
    raise ExternalServiceException(
        message="Slack DM channel opening not implemented. Mock this function in tests.",
        service_name_external="Slack"
    )


def upload_slack_file(
    bot_token: str,
    channel_id: str,
    file_path: str,
    filename: str,
    initial_comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a file to Slack.

    This is a stub function that should be mocked in tests.

    Args:
        bot_token: The Slack bot token
        channel_id: The channel to share the file in
        file_path: Path to the local file
        filename: Display name for the file
        initial_comment: Optional comment with the file

    Returns:
        Dictionary with ok, file info
    """
    raise ExternalServiceException(
        message="Slack file upload not implemented. Mock this function in tests.",
        service_name_external="Slack"
    )


# ============================================================================
# SLACKINTEGRATIONDAO CLASS
# ============================================================================

class SlackIntegrationDAO:
    """
    Data Access Object for Slack integration operations.

    RESPONSIBILITIES:
    - OAuth 2.0 flow management for Slack workspace connection
    - Channel discovery and configuration
    - Message posting and management
    - Slash command handling
    - Error handling and rate limit management

    ARCHITECTURE:
    - Uses asyncpg for database operations
    - Module-level stub functions for Slack API (mockable in tests)
    - Follows repository pattern from Clean Architecture

    USAGE:
    ```python
    dao = SlackIntegrationDAO(db_pool=pool)

    # Initiate OAuth
    result = await dao.initiate_slack_oauth(org_id, redirect_uri)

    # Post announcement
    result = await dao.post_course_announcement(org_id, announcement)
    ```
    """

    def __init__(self, db_pool):
        """
        Initialize SlackIntegrationDAO.

        Args:
            db_pool: asyncpg connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    # ========================================================================
    # OAUTH AND WORKSPACE CONNECTION METHODS
    # ========================================================================

    async def initiate_slack_oauth(
        self,
        organization_id: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Initiate Slack OAuth 2.0 authorization flow.

        BUSINESS LOGIC:
        1. Check for existing active Slack integration
        2. Generate secure state parameter
        3. Store state for verification
        4. Build authorization URL with required scopes

        Args:
            organization_id: The organization initiating OAuth
            redirect_uri: The callback URL after authorization

        Returns:
            Dictionary with provider, authorization_url, state

        Raises:
            ConflictException: If Slack already connected
            DatabaseException: On database errors
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Check for existing active integration
                existing = await conn.fetchrow(
                    """
                    SELECT integration_id, team_id, status
                    FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if existing:
                    raise ConflictException(
                        message=f"Slack workspace already connected. Integration ID: {existing['integration_id']}",
                        resource_type="SlackIntegration",
                        conflicting_field="organization_id",
                        existing_value=existing['integration_id']
                    )

                # Generate state token
                state = f"{organization_id}:{secrets.token_urlsafe(32)}"

                # Store state for verification
                await conn.execute(
                    """
                    INSERT INTO slack_oauth_states (organization_id, state, created_at, expires_at)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (organization_id) DO UPDATE
                    SET state = $2, created_at = $3, expires_at = $4
                    """,
                    organization_id,
                    state,
                    datetime.utcnow(),
                    datetime.utcnow() + timedelta(minutes=10)
                )

                # Build authorization URL
                params = {
                    "client_id": os.environ.get("SLACK_CLIENT_ID", ""),
                    "redirect_uri": redirect_uri,
                    "scope": ",".join(SLACK_OAUTH_CONFIG["scopes"]),
                    "state": state
                }
                auth_url = f"{SLACK_OAUTH_CONFIG['authorize_url']}?{urllib.parse.urlencode(params)}"

                return {
                    "provider": "slack",
                    "authorization_url": auth_url,
                    "state": state
                }
            finally:
                await self.db_pool.release(conn)

        except ConflictException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to initiate Slack OAuth: {e}")
            raise DatabaseException(
                message="Failed to initiate Slack OAuth flow",
                original_exception=e
            )

    async def complete_slack_oauth(
        self,
        organization_id: str,
        authorization_code: str,
        state: str
    ) -> Dict[str, Any]:
        """
        Complete Slack OAuth flow with authorization code.

        BUSINESS LOGIC:
        1. Verify state parameter matches stored state
        2. Exchange authorization code for tokens
        3. Validate required scopes were granted
        4. Store workspace metadata and tokens
        5. Return connection status

        Args:
            organization_id: The organization completing OAuth
            authorization_code: The code from Slack callback
            state: The state parameter for CSRF verification

        Returns:
            Dictionary with workspace info, bot_user_id, status

        Raises:
            AuthenticationException: On state mismatch or expired code
            ValidationException: On insufficient scopes
            DatabaseException: On database errors
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Verify state
                stored = await conn.fetchrow(
                    """
                    SELECT state FROM slack_oauth_states
                    WHERE organization_id = $1 AND expires_at > $2
                    """,
                    organization_id,
                    datetime.utcnow()
                )

                if not stored:
                    stored = await conn.fetchrow(
                        """
                        SELECT stored_state as state FROM slack_oauth_states
                        WHERE organization_id = $1
                        """,
                        organization_id
                    )

                stored_state = stored.get("state") if stored else None

                if not stored_state or stored_state != state:
                    raise AuthenticationException(
                        message="OAuth state mismatch. Possible CSRF attack or expired session.",
                        reason="state_mismatch"
                    )

                # Exchange code for tokens
                redirect_uri = os.environ.get("SLACK_REDIRECT_URI", "")
                token_response = exchange_slack_code(authorization_code, redirect_uri)

                # Validate required scopes
                granted_scopes = token_response.get("scope", "").split(",")
                for required_scope in SLACK_OAUTH_CONFIG["required_scopes"]:
                    if required_scope not in granted_scopes:
                        raise ValidationException(
                            message=f"Required scope not granted: {required_scope}. Please authorize all requested permissions.",
                            field_name="scope",
                            field_value=token_response.get("scope")
                        )

                # Extract workspace info
                team = token_response.get("team", {})
                team_id = team.get("team_id", team.get("id", ""))
                team_name = team.get("team_name", team.get("name", ""))

                # Store integration
                result = await conn.fetchrow(
                    """
                    INSERT INTO slack_integrations
                    (organization_id, team_id, team_name, bot_token, bot_user_id,
                     app_id, scopes, status, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, 'active', $8, $8)
                    RETURNING integration_id, team_id, team_name, bot_user_id, status
                    """,
                    organization_id,
                    team_id,
                    team_name,
                    token_response.get("access_token"),
                    token_response.get("bot_user_id"),
                    token_response.get("app_id"),
                    token_response.get("scope"),
                    datetime.utcnow()
                )

                return {
                    "workspace": {
                        "team_id": team_id,
                        "team_name": team_name
                    },
                    "bot_user_id": token_response.get("bot_user_id"),
                    "status": "connected"
                }
            finally:
                await self.db_pool.release(conn)

        except (AuthenticationException, ValidationException):
            raise
        except Exception as e:
            error_str = str(e).lower()
            if "invalid_grant" in error_str or "expired" in error_str:
                raise AuthenticationException(
                    message="Authorization code has expired. Please try again.",
                    reason="code_expired"
                )
            self.logger.error(f"Failed to complete Slack OAuth: {e}")
            raise DatabaseException(
                message="Failed to complete Slack OAuth flow",
                original_exception=e
            )

    async def get_workspace_info(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get connected Slack workspace information.

        Args:
            organization_id: The organization to query

        Returns:
            Dictionary with team_name, team_id, bot_user_id, status

        Raises:
            NotFoundException: If Slack not connected
            DatabaseException: On database errors
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT integration_id, team_id, team_name, team_domain,
                           bot_user_id, status
                    FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not row:
                    raise NotFoundException(
                        message="Slack workspace not connected. Please connect Slack first.",
                        resource_type="SlackIntegration",
                        resource_id=organization_id
                    )

                return dict(row)
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except (OSError, ConnectionRefusedError) as e:
            raise DatabaseException(
                message="Database connection failed",
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to get workspace info: {e}")
            raise DatabaseException(
                message="Failed to retrieve Slack workspace info",
                original_exception=e
            )

    # ========================================================================
    # CHANNEL MANAGEMENT METHODS
    # ========================================================================

    async def get_available_channels(
        self,
        organization_id: str,
        include_private: bool = False
    ) -> Dict[str, Any]:
        """
        Get available Slack channels in the workspace.

        BUSINESS LOGIC:
        1. Get bot token from database
        2. Fetch channels via Slack API
        3. Filter out archived channels
        4. Return channel list

        Args:
            organization_id: The organization to query
            include_private: Whether to include private channels

        Returns:
            Dictionary with channels list

        Raises:
            ValidationException: On missing scope for private channels
            ExternalServiceException: On Slack API errors
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Get bot token
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token, scopes FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                bot_token = integration['bot_token']

                # Fetch channels from Slack
                try:
                    all_channels = fetch_slack_channels(bot_token, include_private)
                except Exception as e:
                    error_str = str(e).lower()
                    if "missing_scope" in error_str or "groups:read" in error_str:
                        raise ValidationException(
                            message="Missing scope for private channels. Please reconnect with groups:read scope.",
                            field_name="scope",
                            field_value="groups:read"
                        )
                    raise

                # Filter out archived channels
                active_channels = [
                    ch for ch in all_channels
                    if not ch.get("is_archived", False)
                ]

                return {"channels": active_channels}
            finally:
                await self.db_pool.release(conn)

        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            self.logger.error(f"Failed to fetch channels: {e}")
            raise ExternalServiceException(
                message="Failed to fetch Slack channels",
                service_name_external="Slack",
                original_exception=e
            )

    async def set_default_channel(
        self,
        organization_id: str,
        channel_id: str,
        channel_name: str,
        purpose: str
    ) -> Dict[str, Any]:
        """
        Set default channel for a specific purpose.

        Args:
            organization_id: The organization
            channel_id: The Slack channel ID
            channel_name: The channel name
            purpose: The purpose (course_announcements, grade_notifications, etc.)

        Returns:
            Dictionary with channel_id, purpose, configured status
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                await conn.execute(
                    """
                    INSERT INTO slack_channel_configs
                    (organization_id, channel_id, channel_name, purpose, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $5)
                    ON CONFLICT (organization_id, purpose) DO UPDATE
                    SET channel_id = $2, channel_name = $3, updated_at = $5
                    """,
                    organization_id,
                    channel_id,
                    channel_name,
                    purpose,
                    datetime.utcnow()
                )

                return {
                    "channel_id": channel_id,
                    "purpose": purpose,
                    "configured": True
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to set default channel: {e}")
            raise DatabaseException(
                message="Failed to set default Slack channel",
                original_exception=e
            )

    async def get_default_channels(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get configured default channels by purpose.

        Args:
            organization_id: The organization to query

        Returns:
            Dictionary with channels keyed by purpose
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                rows = await conn.fetch(
                    """
                    SELECT channel_id, channel_name, purpose
                    FROM slack_channel_configs
                    WHERE organization_id = $1
                    """,
                    organization_id
                )

                channels = {}
                for row in rows:
                    channels[row['purpose']] = {
                        "channel_id": row['channel_id'],
                        "channel_name": row['channel_name']
                    }

                return {"channels": channels}
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to get default channels: {e}")
            raise DatabaseException(
                message="Failed to retrieve default Slack channels",
                original_exception=e
            )

    async def validate_channel_permissions(
        self,
        organization_id: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Validate bot has permission to post to channel.

        Args:
            organization_id: The organization
            channel_id: The channel to validate

        Returns:
            Dictionary with is_member, can_post status

        Raises:
            ValidationException: If bot not a member
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                # Check membership
                result = check_channel_membership(integration['bot_token'], channel_id)

                if not result.get("is_member", False):
                    raise ValidationException(
                        message=f"Bot is not a member of channel {channel_id}. Please invite the bot to the channel.",
                        field_name="channel_id",
                        field_value=channel_id
                    )

                return {"is_member": True, "can_post": True}
            finally:
                await self.db_pool.release(conn)

        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate channel permissions: {e}")
            raise ExternalServiceException(
                message="Failed to validate channel permissions",
                service_name_external="Slack",
                original_exception=e
            )

    # ========================================================================
    # MESSAGE POSTING METHODS
    # ========================================================================

    async def post_message(
        self,
        organization_id: str,
        channel_id: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Post a message to a Slack channel.

        BUSINESS LOGIC:
        1. Validate message size
        2. Get bot token
        3. Post message via Slack API
        4. Handle errors (rate limit, token revoked, etc.)

        Args:
            organization_id: The organization
            channel_id: The channel to post to
            text: Plain text message (optional if blocks provided)
            blocks: Block Kit blocks for rich formatting

        Returns:
            Dictionary with posted status, message_ts, channel_id

        Raises:
            ValidationException: On message too large
            RateLimitException: On rate limit hit
            AuthenticationException: On token revoked
            NotFoundException: On channel not found
            ExternalServiceException: On API errors
        """
        # Validate message size
        if text and len(text) > SLACK_MESSAGE_SIZE_LIMIT:
            raise ValidationException(
                message=f"Message exceeds Slack size limit of {SLACK_MESSAGE_SIZE_LIMIT} characters. Consider using file attachment instead.",
                field_name="text",
                field_value=f"{len(text)} characters"
            )

        try:
            conn = await self.db_pool.acquire()
            try:
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                # Post message
                try:
                    result = post_slack_message(
                        bot_token=integration['bot_token'],
                        channel_id=channel_id,
                        text=text,
                        blocks=blocks
                    )
                except Exception as e:
                    self._handle_slack_api_error(e)

                return {
                    "posted": True,
                    "message_ts": result.get("ts"),
                    "channel_id": result.get("channel", channel_id)
                }
            finally:
                await self.db_pool.release(conn)

        except (ValidationException, NotFoundException, RateLimitException,
                AuthenticationException, ExternalServiceException):
            raise
        except Exception as e:
            self.logger.error(f"Failed to post message: {e}")
            raise ExternalServiceException(
                message="Failed to post Slack message",
                service_name_external="Slack",
                original_exception=e
            )

    async def post_course_announcement(
        self,
        organization_id: str,
        announcement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post course announcement to configured channel.

        Args:
            organization_id: The organization
            announcement: Dictionary with title, message, url, instructor

        Returns:
            Dictionary with posted status, message_ts, channel_id
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Get configured announcement channel and bot token
                config = await conn.fetchrow(
                    """
                    SELECT c.channel_id, i.bot_token
                    FROM slack_channel_configs c
                    JOIN slack_integrations i ON c.organization_id = i.organization_id
                    WHERE c.organization_id = $1
                      AND c.purpose = 'course_announcements'
                      AND i.status = 'active'
                    """,
                    organization_id
                )

                if not config:
                    raise NotFoundException(
                        message="No announcement channel configured",
                        resource_type="SlackChannelConfig"
                    )

                # Build Block Kit message
                blocks = self._build_announcement_blocks(announcement)

                # Post message
                result = post_slack_message(
                    bot_token=config['bot_token'],
                    channel_id=config['channel_id'],
                    text=announcement.get("message", ""),
                    blocks=blocks
                )

                return {
                    "posted": True,
                    "message_ts": result.get("ts"),
                    "channel_id": config['channel_id']
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self._handle_slack_api_error(e)
            raise ExternalServiceException(
                message="Failed to post course announcement",
                service_name_external="Slack",
                original_exception=e
            )

    async def send_direct_message(
        self,
        organization_id: str,
        user_email: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send direct message to a user by email.

        Args:
            organization_id: The organization
            user_email: The recipient's email
            message: The message text

        Returns:
            Dictionary with sent status, dm_channel_id
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                # Open DM channel
                dm_result = open_dm_channel(integration['bot_token'], user_email)
                dm_channel_id = dm_result.get("channel", {}).get("id")

                # Send message
                post_slack_message(
                    bot_token=integration['bot_token'],
                    channel_id=dm_channel_id,
                    text=message
                )

                return {
                    "sent": True,
                    "dm_channel_id": dm_channel_id
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self._handle_slack_api_error(e)
            raise ExternalServiceException(
                message="Failed to send direct message",
                service_name_external="Slack",
                original_exception=e
            )

    async def update_message(
        self,
        organization_id: str,
        channel_id: str,
        message_ts: str,
        new_text: Optional[str] = None,
        new_blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing Slack message.

        Args:
            organization_id: The organization
            channel_id: The channel containing the message
            message_ts: The message timestamp
            new_text: New text content
            new_blocks: New Block Kit blocks

        Returns:
            Dictionary with updated status
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                update_slack_message(
                    bot_token=integration['bot_token'],
                    channel_id=channel_id,
                    message_ts=message_ts,
                    text=new_text,
                    blocks=new_blocks
                )

                return {"updated": True}
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self._handle_slack_api_error(e)
            raise ExternalServiceException(
                message="Failed to update message",
                service_name_external="Slack",
                original_exception=e
            )

    async def delete_message(
        self,
        organization_id: str,
        channel_id: str,
        message_ts: str
    ) -> Dict[str, Any]:
        """
        Delete a Slack message.

        Args:
            organization_id: The organization
            channel_id: The channel containing the message
            message_ts: The message timestamp

        Returns:
            Dictionary with deleted status
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                delete_slack_message(
                    bot_token=integration['bot_token'],
                    channel_id=channel_id,
                    message_ts=message_ts
                )

                return {"deleted": True}
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self._handle_slack_api_error(e)
            raise ExternalServiceException(
                message="Failed to delete message",
                service_name_external="Slack",
                original_exception=e
            )

    async def post_threaded_reply(
        self,
        organization_id: str,
        channel_id: str,
        thread_ts: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Post a threaded reply to an existing message.

        Args:
            organization_id: The organization
            channel_id: The channel containing the thread
            thread_ts: The parent message timestamp
            text: The reply text

        Returns:
            Dictionary with posted status, thread_ts
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                result = post_slack_message(
                    bot_token=integration['bot_token'],
                    channel_id=channel_id,
                    text=text,
                    thread_ts=thread_ts
                )

                return {
                    "posted": True,
                    "message_ts": result.get("ts"),
                    "thread_ts": thread_ts
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self._handle_slack_api_error(e)
            raise ExternalServiceException(
                message="Failed to post threaded reply",
                service_name_external="Slack",
                original_exception=e
            )

    async def post_with_attachment(
        self,
        organization_id: str,
        channel_id: str,
        text: str,
        file_path: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Post message with file attachment.

        Args:
            organization_id: The organization
            channel_id: The channel to post to
            text: Message text
            file_path: Path to file
            filename: Display filename

        Returns:
            Dictionary with posted status, file_id
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                # Upload file
                file_result = upload_slack_file(
                    bot_token=integration['bot_token'],
                    channel_id=channel_id,
                    file_path=file_path,
                    filename=filename,
                    initial_comment=text
                )

                # Post message with file reference
                post_slack_message(
                    bot_token=integration['bot_token'],
                    channel_id=channel_id,
                    text=text
                )

                return {
                    "posted": True,
                    "file_id": file_result.get("file", {}).get("id")
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self._handle_slack_api_error(e)
            raise ExternalServiceException(
                message="Failed to post with attachment",
                service_name_external="Slack",
                original_exception=e
            )

    # ========================================================================
    # SLASH COMMAND METHODS
    # ========================================================================

    async def register_slash_command(
        self,
        organization_id: str,
        command_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a slash command configuration.

        Args:
            organization_id: The organization
            command_config: Dictionary with command, description, usage_hint, webhook_url

        Returns:
            Dictionary with command, registered status
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                await conn.execute(
                    """
                    INSERT INTO slack_slash_commands
                    (organization_id, command, description, usage_hint, webhook_url, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (organization_id, command) DO UPDATE
                    SET description = $3, usage_hint = $4, webhook_url = $5
                    """,
                    organization_id,
                    command_config.get("command"),
                    command_config.get("description"),
                    command_config.get("usage_hint"),
                    command_config.get("webhook_url"),
                    datetime.utcnow()
                )

                return {
                    "command": command_config.get("command"),
                    "registered": True
                }
            finally:
                await self.db_pool.release(conn)

        except Exception as e:
            self.logger.error(f"Failed to register slash command: {e}")
            raise DatabaseException(
                message="Failed to register slash command",
                original_exception=e
            )

    async def validate_command_request(
        self,
        organization_id: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate incoming slash command request signature.

        Args:
            organization_id: The organization
            request_data: Dictionary with timestamp, signature, body

        Returns:
            Dictionary with valid status

        Raises:
            AuthenticationException: On invalid signature
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                # Get signing secret
                integration = await conn.fetchrow(
                    """
                    SELECT signing_secret FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                signing_secret = integration.get("signing_secret") if integration else os.environ.get("SLACK_SIGNING_SECRET", "")

                # Validate timestamp (prevent replay attacks)
                timestamp = request_data.get("timestamp", "")
                current_time = int(time.time())
                if abs(current_time - int(timestamp)) > 300:  # 5 minute window
                    raise AuthenticationException(
                        message="Request timestamp too old. Possible replay attack.",
                        reason="timestamp_expired"
                    )

                # Validate signature
                sig_basestring = f"v0:{timestamp}:{request_data.get('body', '')}"
                expected_sig = "v0=" + hmac.new(
                    signing_secret.encode(),
                    sig_basestring.encode(),
                    hashlib.sha256
                ).hexdigest()

                provided_sig = request_data.get("signature", "")
                if not hmac.compare_digest(expected_sig, provided_sig):
                    raise AuthenticationException(
                        message="Invalid request signature. Request may have been tampered with.",
                        reason="invalid_signature"
                    )

                return {"valid": True}
            finally:
                await self.db_pool.release(conn)

        except AuthenticationException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate command request: {e}")
            raise AuthenticationException(
                message="Failed to validate slash command request",
                reason="validation_error"
            )

    async def respond_to_command(
        self,
        organization_id: str,
        response_url: str,
        text: str,
        response_type: str = "ephemeral"
    ) -> Dict[str, Any]:
        """
        Respond to a slash command.

        Args:
            organization_id: The organization
            response_url: The Slack webhook URL for response
            text: The response text
            response_type: "ephemeral" (private) or "in_channel" (public)

        Returns:
            Dictionary with sent status
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                # Post response via webhook URL
                post_slack_message(
                    bot_token=integration['bot_token'],
                    channel_id="",  # Not needed for response_url
                    text=text,
                    response_url=response_url
                )

                return {"sent": True}
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self._handle_slack_api_error(e)
            raise ExternalServiceException(
                message="Failed to respond to slash command",
                service_name_external="Slack",
                original_exception=e
            )

    async def respond_with_delayed_result(
        self,
        organization_id: str,
        response_url: str,
        initial_text: str,
        result_text: str
    ) -> Dict[str, Any]:
        """
        Respond to slash command with immediate ack and delayed result.

        Args:
            organization_id: The organization
            response_url: The Slack webhook URL
            initial_text: Immediate acknowledgment text
            result_text: Delayed result text

        Returns:
            Dictionary with acknowledged and result_sent status
        """
        try:
            conn = await self.db_pool.acquire()
            try:
                integration = await conn.fetchrow(
                    """
                    SELECT bot_token FROM slack_integrations
                    WHERE organization_id = $1 AND status = 'active'
                    """,
                    organization_id
                )

                if not integration:
                    raise NotFoundException(
                        message="Slack workspace not connected",
                        resource_type="SlackIntegration"
                    )

                # Send immediate acknowledgment
                post_slack_message(
                    bot_token=integration['bot_token'],
                    channel_id="",
                    text=initial_text,
                    response_url=response_url
                )

                # Send result (in production, this would be async)
                post_slack_message(
                    bot_token=integration['bot_token'],
                    channel_id="",
                    text=result_text,
                    response_url=response_url
                )

                return {
                    "acknowledged": True,
                    "result_sent": True
                }
            finally:
                await self.db_pool.release(conn)

        except NotFoundException:
            raise
        except Exception as e:
            self._handle_slack_api_error(e)
            raise ExternalServiceException(
                message="Failed to send delayed response",
                service_name_external="Slack",
                original_exception=e
            )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _handle_slack_api_error(self, error: Exception) -> None:
        """
        Handle Slack API errors and raise appropriate exceptions.

        Args:
            error: The original exception

        Raises:
            RateLimitException: On rate limit hit
            AuthenticationException: On token revoked or workspace deactivated
            NotFoundException: On channel not found
            ExternalServiceException: On other API errors
        """
        error_str = str(error).lower()

        # Rate limit
        if "rate_limited" in error_str or "retry-after" in error_str:
            retry_after = 60  # Default
            match = re.search(r'retry-after[:\s]+(\d+)', error_str, re.IGNORECASE)
            if match:
                retry_after = int(match.group(1))
            raise RateLimitException(
                message=f"Slack API rate limit exceeded. Retry after {retry_after} seconds.",
                retry_after=retry_after
            )

        # Token revoked
        if "token_revoked" in error_str:
            raise AuthenticationException(
                message="Slack token has been revoked. Please reconnect the workspace.",
                reason="token_revoked"
            )

        # Workspace deactivated
        if "account_inactive" in error_str or "deactivated" in error_str:
            raise AuthenticationException(
                message="Slack workspace has been deactivated. Please contact your Slack administrator.",
                reason="workspace_inactive"
            )

        # Channel not found
        if "channel_not_found" in error_str:
            raise NotFoundException(
                message="Slack channel not found. It may have been deleted or archived.",
                resource_type="SlackChannel"
            )

        # API unavailable
        if "unavailable" in error_str or "503" in error_str or "timeout" in error_str:
            raise ExternalServiceException(
                message=f"Slack API unavailable: {error}",
                service_name_external="Slack",
                original_exception=error
            )

    def _build_announcement_blocks(
        self,
        announcement: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build Block Kit blocks for course announcement.

        Args:
            announcement: Dictionary with title, message, url, instructor

        Returns:
            List of Block Kit block dictionaries
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": announcement.get("title", "Course Announcement")
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": announcement.get("message", "")
                }
            }
        ]

        # Add instructor if provided
        if announcement.get("instructor"):
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Instructor:* {announcement['instructor']}"
                    }
                ]
            })

        # Add button if URL provided
        if announcement.get("url"):
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Course"
                        },
                        "url": announcement["url"]
                    }
                ]
            })

        return blocks
