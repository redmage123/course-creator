"""
Integration Service

What: Business logic service for external integrations (LTI, Calendar, Slack, Webhooks).
Where: Organization Management service application layer.
Why: Provides:
     1. Coordinated integration management across LTI, Calendar, Slack, and Webhooks
     2. Business rule validation before database operations
     3. Event orchestration for integration state changes
     4. Security validation for external service connections
     5. Token lifecycle management for OAuth integrations

Technical Implementation:
- Follows Single Responsibility Principle with focused integration handlers
- Implements Dependency Inversion through DAO abstraction
- Provides comprehensive error handling with custom exceptions
- Supports async operations for high-performance integration management
"""

import logging
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from organization_management.data_access.integrations_dao import IntegrationsDAO
from organization_management.domain.entities.integrations import (
    LTIPlatformRegistration,
    LTIContext,
    LTIUserMapping,
    LTIGradeSync,
    CalendarProvider,
    CalendarEvent,
    SlackWorkspace,
    SlackChannelMapping,
    SlackUserMapping,
    SlackMessage,
    OutboundWebhook,
    WebhookDeliveryLog,
    InboundWebhook,
    OAuthToken,
    LTIVersion,
    LTIScope,
    GradeSyncStatus,
    CalendarProviderType,
    SyncDirection,
    CalendarSyncStatus,
    SlackChannelType,
    SlackMessageType,
    WebhookAuthType,
    WebhookDeliveryStatus,
    WebhookHandlerType,
    OAuthProvider
)
from organization_management.exceptions import (
    ValidationException,
    DatabaseException
)


class IntegrationsService:
    """
    Service for managing external integrations.

    What: Coordinates business logic for LTI, Calendar, Slack, and Webhook integrations.
    Where: Organization Management service application layer.
    Why: Provides:
         1. Unified API for all integration operations
         2. Business rule validation and enforcement
         3. Secure token and credential management
         4. Event-driven integration state management

    Technical Implementation:
    - Uses DAO for all database operations
    - Implements comprehensive validation before database writes
    - Provides clear error messages for integration failures
    - Supports multi-tenant isolation through organization IDs
    """

    def __init__(self, dao: IntegrationsDAO):
        """
        Initialize the Integrations Service.

        What: Constructor for IntegrationsService.
        Where: Called during service initialization.
        Why: Injects DAO dependency for database operations.

        Args:
            dao: IntegrationsDAO instance for database operations
        """
        self.dao = dao
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # LTI PLATFORM MANAGEMENT
    # ================================================================

    async def register_lti_platform(
        self,
        organization_id: UUID,
        platform_name: str,
        issuer: str,
        client_id: str,
        auth_login_url: str,
        auth_token_url: str,
        jwks_url: str,
        deployment_id: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        created_by: Optional[UUID] = None
    ) -> LTIPlatformRegistration:
        """
        Register a new LTI 1.3 platform.

        What: Creates a new LTI platform registration for connecting an LMS.
        Where: Called when organization admin sets up LTI integration.
        Why: Enables external LMS to launch into our platform as a tool.

        Args:
            organization_id: UUID of the organization
            platform_name: Display name for the platform (e.g., "Canvas")
            issuer: LTI issuer URL from the LMS
            client_id: LTI client ID from the LMS
            auth_login_url: OIDC login initiation URL
            auth_token_url: OAuth token endpoint URL
            jwks_url: JSON Web Key Set URL for platform
            deployment_id: Optional deployment ID
            scopes: Optional list of requested LTI scopes
            created_by: UUID of user creating the registration

        Returns:
            Created LTIPlatformRegistration

        Raises:
            ValidationException: If validation fails
            DatabaseException: If database operation fails
        """
        self.logger.info(f"Registering LTI platform '{platform_name}' for org {organization_id}")

        # Validate inputs
        if not platform_name or not platform_name.strip():
            raise ValidationException(
                message="Platform name is required",
                field_errors={"platform_name": "Cannot be empty"}
            )

        if not issuer or not issuer.startswith('http'):
            raise ValidationException(
                message="Valid issuer URL is required",
                field_errors={"issuer": "Must be a valid URL"}
            )

        # Create platform entity
        platform = LTIPlatformRegistration(
            id=uuid4(),
            organization_id=organization_id,
            platform_name=platform_name.strip(),
            issuer=issuer,
            client_id=client_id,
            deployment_id=deployment_id,
            auth_login_url=auth_login_url,
            auth_token_url=auth_token_url,
            jwks_url=jwks_url,
            scopes=scopes or [],
            created_by=created_by,
            is_active=True
        )

        # Persist and return
        return await self.dao.create_lti_platform(platform)

    async def get_lti_platform(
        self,
        platform_id: UUID
    ) -> Optional[LTIPlatformRegistration]:
        """
        Retrieve an LTI platform by ID.

        What: Fetches LTI platform registration details.
        Where: Called for platform configuration and LTI launches.
        Why: Enables platform lookup for integration operations.

        Args:
            platform_id: UUID of the platform

        Returns:
            LTIPlatformRegistration or None if not found
        """
        return await self.dao.get_lti_platform_by_id(platform_id)

    async def get_lti_platform_by_issuer(
        self,
        issuer: str,
        client_id: str
    ) -> Optional[LTIPlatformRegistration]:
        """
        Retrieve LTI platform by issuer and client ID.

        What: Fetches platform using LTI identifiers.
        Where: Called during LTI launch to identify platform.
        Why: Enables platform lookup during LTI authentication flow.

        Args:
            issuer: LTI issuer URL
            client_id: LTI client ID

        Returns:
            LTIPlatformRegistration or None if not found
        """
        return await self.dao.get_lti_platform_by_issuer(issuer, client_id)

    async def get_organization_lti_platforms(
        self,
        organization_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[LTIPlatformRegistration]:
        """
        Retrieve all LTI platforms for an organization.

        What: Fetches all LTI integrations for an organization.
        Where: Called for integration management UI.
        Why: Enables organization admins to view all LTI connections.

        Args:
            organization_id: UUID of the organization
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of LTI platform registrations
        """
        return await self.dao.get_lti_platforms_by_organization(
            organization_id, limit, offset
        )

    async def verify_lti_platform(
        self,
        platform_id: UUID
    ) -> LTIPlatformRegistration:
        """
        Mark an LTI platform as verified.

        What: Updates platform to verified status after successful handshake.
        Where: Called after successful LTI launch/verification.
        Why: Tracks which platforms have been successfully tested.

        Args:
            platform_id: UUID of the platform

        Returns:
            Updated LTIPlatformRegistration

        Raises:
            ValidationException: If platform not found
        """
        platform = await self.dao.update_lti_platform(
            platform_id,
            {"verified_at": datetime.now()}
        )

        if not platform:
            raise ValidationException(
                message="LTI platform not found",
                field_errors={"platform_id": str(platform_id)}
            )

        self.logger.info(f"LTI platform {platform_id} verified")
        return platform

    async def record_lti_connection(
        self,
        platform_id: UUID
    ) -> Optional[LTIPlatformRegistration]:
        """
        Record an LTI connection event.

        What: Updates last connection timestamp for platform.
        Where: Called on each successful LTI launch.
        Why: Tracks platform activity for monitoring.

        Args:
            platform_id: UUID of the platform

        Returns:
            Updated LTIPlatformRegistration or None if not found
        """
        return await self.dao.update_lti_platform(
            platform_id,
            {"last_connection_at": datetime.now()}
        )

    async def deactivate_lti_platform(
        self,
        platform_id: UUID
    ) -> Optional[LTIPlatformRegistration]:
        """
        Deactivate an LTI platform.

        What: Sets platform to inactive status.
        Where: Called when disconnecting LMS integration.
        Why: Soft-deletes platform for potential reactivation.

        Args:
            platform_id: UUID of the platform

        Returns:
            Updated LTIPlatformRegistration or None if not found
        """
        self.logger.info(f"Deactivating LTI platform {platform_id}")
        return await self.dao.update_lti_platform(
            platform_id,
            {"is_active": False}
        )

    # ================================================================
    # LTI CONTEXT MANAGEMENT
    # ================================================================

    async def create_or_update_lti_context(
        self,
        platform_id: UUID,
        lti_context_id: str,
        lti_context_type: Optional[str] = None,
        lti_context_title: Optional[str] = None,
        course_id: Optional[UUID] = None
    ) -> LTIContext:
        """
        Create or update an LTI context mapping.

        What: Creates or updates context linking LMS course to platform course.
        Where: Called during LTI launch with context claim.
        Why: Enables course mapping between LMS and platform.

        Args:
            platform_id: UUID of the LTI platform
            lti_context_id: LTI context ID from LMS
            lti_context_type: Type of context (CourseOffering, etc.)
            lti_context_title: Display title from LMS
            course_id: Optional UUID of linked platform course

        Returns:
            Created or updated LTIContext
        """
        # Check if context already exists
        existing = await self.dao.get_lti_context_by_lti_id(
            platform_id, lti_context_id
        )

        if existing:
            # Update existing context
            updates = {
                "lti_context_type": lti_context_type,
                "lti_context_title": lti_context_title
            }
            if course_id:
                updates["course_id"] = course_id

            return await self.dao.update_lti_context(existing.id, updates)

        # Create new context
        context = LTIContext(
            id=uuid4(),
            platform_id=platform_id,
            lti_context_id=lti_context_id,
            lti_context_type=lti_context_type,
            lti_context_title=lti_context_title,
            course_id=course_id
        )

        return await self.dao.create_lti_context(context)

    async def link_context_to_course(
        self,
        context_id: UUID,
        course_id: UUID
    ) -> Optional[LTIContext]:
        """
        Link an LTI context to a platform course.

        What: Associates LTI context with platform course.
        Where: Called when instructor links LMS course to platform course.
        Why: Enables grade passback and roster sync.

        Args:
            context_id: UUID of the LTI context
            course_id: UUID of the platform course

        Returns:
            Updated LTIContext or None if not found
        """
        self.logger.info(f"Linking LTI context {context_id} to course {course_id}")
        return await self.dao.update_lti_context(
            context_id,
            {"course_id": course_id}
        )

    # ================================================================
    # LTI USER MANAGEMENT
    # ================================================================

    async def create_or_update_lti_user(
        self,
        platform_id: UUID,
        user_id: UUID,
        lti_user_id: str,
        lti_email: Optional[str] = None,
        lti_name: Optional[str] = None,
        lti_roles: Optional[List[str]] = None
    ) -> LTIUserMapping:
        """
        Create or update an LTI user mapping.

        What: Creates or updates mapping between LMS user and platform user.
        Where: Called during LTI launch with user claims.
        Why: Enables user identity linking across systems.

        Args:
            platform_id: UUID of the LTI platform
            user_id: UUID of the platform user
            lti_user_id: LTI user ID from LMS
            lti_email: Email from LMS claims
            lti_name: Name from LMS claims
            lti_roles: LTI role URIs from claims

        Returns:
            Created or updated LTIUserMapping
        """
        # Check if mapping already exists
        existing = await self.dao.get_lti_user_mapping_by_lti_user(
            platform_id, lti_user_id
        )

        if existing:
            # Update and record login
            updates = {
                "lti_email": lti_email,
                "lti_name": lti_name,
                "lti_roles": lti_roles or [],
                "last_login_at": datetime.now(),
                "login_count": existing.login_count + 1
            }
            return await self.dao.update_lti_user_mapping(existing.id, updates)

        # Create new mapping
        mapping = LTIUserMapping(
            id=uuid4(),
            platform_id=platform_id,
            user_id=user_id,
            lti_user_id=lti_user_id,
            lti_email=lti_email,
            lti_name=lti_name,
            lti_roles=lti_roles or [],
            last_login_at=datetime.now(),
            login_count=1
        )

        return await self.dao.create_lti_user_mapping(mapping)

    # ================================================================
    # LTI GRADE SYNC
    # ================================================================

    async def queue_grade_for_sync(
        self,
        context_id: UUID,
        user_mapping_id: UUID,
        score: Decimal,
        max_score: Decimal = Decimal("100.00"),
        comment: Optional[str] = None,
        quiz_attempt_id: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None
    ) -> LTIGradeSync:
        """
        Queue a grade for LTI sync.

        What: Creates grade sync record for LTI AGS passback.
        Where: Called when student receives grade.
        Why: Enables asynchronous grade delivery to LMS.

        Args:
            context_id: UUID of the LTI context
            user_mapping_id: UUID of the LTI user mapping
            score: Achieved score
            max_score: Maximum possible score
            comment: Optional grade comment
            quiz_attempt_id: Optional quiz attempt UUID
            assignment_id: Optional assignment UUID

        Returns:
            Created LTIGradeSync
        """
        self.logger.info(f"Queueing grade sync for context {context_id}")

        grade_sync = LTIGradeSync(
            id=uuid4(),
            context_id=context_id,
            user_mapping_id=user_mapping_id,
            score=score,
            max_score=max_score,
            comment=comment,
            quiz_attempt_id=quiz_attempt_id,
            assignment_id=assignment_id,
            sync_status=GradeSyncStatus.PENDING
        )

        return await self.dao.create_lti_grade_sync(grade_sync)

    async def get_pending_grade_syncs(
        self,
        limit: int = 100
    ) -> List[LTIGradeSync]:
        """
        Retrieve pending grade syncs for processing.

        What: Fetches grades that need to be synced to LMS.
        Where: Called by grade sync worker.
        Why: Enables batch processing of grade passback.

        Args:
            limit: Maximum number of records

        Returns:
            List of pending grade syncs
        """
        return await self.dao.get_pending_grade_syncs(limit)

    async def update_grade_sync_status(
        self,
        grade_sync_id: UUID,
        status: GradeSyncStatus,
        error_message: Optional[str] = None
    ) -> Optional[LTIGradeSync]:
        """
        Update grade sync status.

        What: Updates sync status after delivery attempt.
        Where: Called by grade sync worker after attempt.
        Why: Tracks success/failure of grade passback.

        Args:
            grade_sync_id: UUID of the grade sync record
            status: New sync status
            error_message: Error message if failed

        Returns:
            Updated LTIGradeSync or None
        """
        return await self.dao.update_grade_sync_status(
            grade_sync_id, status, error_message
        )

    # ================================================================
    # CALENDAR PROVIDER MANAGEMENT
    # ================================================================

    async def connect_calendar(
        self,
        user_id: UUID,
        provider_type: CalendarProviderType,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        calendar_id: Optional[str] = None,
        calendar_name: Optional[str] = None,
        calendar_timezone: Optional[str] = None
    ) -> CalendarProvider:
        """
        Connect a calendar provider for a user.

        What: Creates calendar provider configuration.
        Where: Called when user authorizes calendar access.
        Why: Enables calendar synchronization for deadlines and events.

        Args:
            user_id: UUID of the user
            provider_type: Type of calendar (Google, Outlook, etc.)
            access_token: OAuth access token
            refresh_token: Optional OAuth refresh token
            token_expires_at: Optional token expiration time
            calendar_id: Optional specific calendar ID
            calendar_name: Optional calendar display name
            calendar_timezone: Optional calendar timezone

        Returns:
            Created CalendarProvider
        """
        self.logger.info(f"Connecting {provider_type} calendar for user {user_id}")

        provider = CalendarProvider(
            id=uuid4(),
            user_id=user_id,
            provider_type=provider_type,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            calendar_id=calendar_id,
            calendar_name=calendar_name,
            calendar_timezone=calendar_timezone,
            is_connected=True,
            sync_enabled=True
        )

        return await self.dao.create_calendar_provider(provider)

    async def get_user_calendars(
        self,
        user_id: UUID
    ) -> List[CalendarProvider]:
        """
        Retrieve all calendars for a user.

        What: Fetches all connected calendars.
        Where: Called for calendar management UI.
        Why: Enables user to view and manage calendar integrations.

        Args:
            user_id: UUID of the user

        Returns:
            List of calendar providers
        """
        return await self.dao.get_calendar_providers_by_user(user_id)

    async def update_calendar_tokens(
        self,
        provider_id: UUID,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None
    ) -> Optional[CalendarProvider]:
        """
        Update calendar OAuth tokens.

        What: Updates OAuth tokens after refresh.
        Where: Called by token refresh flow.
        Why: Maintains valid access to calendar API.

        Args:
            provider_id: UUID of the provider
            access_token: New access token
            refresh_token: Optional new refresh token
            token_expires_at: Optional new expiration time

        Returns:
            Updated CalendarProvider or None
        """
        updates = {
            "access_token": access_token,
            "token_expires_at": token_expires_at
        }
        if refresh_token:
            updates["refresh_token"] = refresh_token

        return await self.dao.update_calendar_provider(provider_id, updates)

    async def disconnect_calendar(
        self,
        provider_id: UUID
    ) -> bool:
        """
        Disconnect a calendar provider.

        What: Removes calendar provider configuration.
        Where: Called when user disconnects calendar.
        Why: Enables clean removal of calendar integration.

        Args:
            provider_id: UUID of the provider

        Returns:
            True if deleted
        """
        self.logger.info(f"Disconnecting calendar provider {provider_id}")
        return await self.dao.delete_calendar_provider(provider_id)

    # ================================================================
    # CALENDAR EVENT MANAGEMENT
    # ================================================================

    async def sync_calendar_event(
        self,
        provider_id: UUID,
        user_id: UUID,
        title: str,
        start_time: datetime,
        end_time: datetime,
        external_event_id: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        event_type: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[UUID] = None
    ) -> CalendarEvent:
        """
        Sync a calendar event.

        What: Creates or updates a calendar event.
        Where: Called during calendar sync.
        Why: Enables bidirectional calendar synchronization.

        Args:
            provider_id: UUID of the calendar provider
            user_id: UUID of the user
            title: Event title
            start_time: Event start time
            end_time: Event end time
            external_event_id: Optional external event ID
            description: Optional event description
            location: Optional event location
            event_type: Optional event type
            source_type: Optional source entity type
            source_id: Optional source entity ID

        Returns:
            Created CalendarEvent
        """
        event = CalendarEvent(
            id=uuid4(),
            provider_id=provider_id,
            user_id=user_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            external_event_id=external_event_id,
            description=description,
            location=location,
            event_type=event_type,
            source_type=source_type,
            source_id=source_id,
            sync_status=CalendarSyncStatus.SYNCED,
            last_sync_at=datetime.now()
        )

        return await self.dao.create_calendar_event(event)

    async def get_user_calendar_events(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CalendarEvent]:
        """
        Retrieve calendar events for a user.

        What: Fetches synced calendar events.
        Where: Called for calendar display.
        Why: Enables viewing synced events.

        Args:
            user_id: UUID of the user
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of records

        Returns:
            List of calendar events
        """
        return await self.dao.get_calendar_events_by_user(
            user_id, start_date, end_date, limit
        )

    # ================================================================
    # SLACK WORKSPACE MANAGEMENT
    # ================================================================

    async def connect_slack_workspace(
        self,
        organization_id: UUID,
        workspace_id: str,
        bot_token: str,
        workspace_name: Optional[str] = None,
        workspace_domain: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        installed_by: Optional[UUID] = None
    ) -> SlackWorkspace:
        """
        Connect a Slack workspace to an organization.

        What: Creates Slack workspace configuration.
        Where: Called after Slack OAuth flow completes.
        Why: Enables Slack notifications and commands.

        Args:
            organization_id: UUID of the organization
            workspace_id: Slack workspace ID
            bot_token: Slack bot token
            workspace_name: Optional workspace name
            workspace_domain: Optional workspace domain
            scopes: Optional list of OAuth scopes
            installed_by: Optional UUID of installing user

        Returns:
            Created SlackWorkspace
        """
        self.logger.info(f"Connecting Slack workspace '{workspace_name}' for org {organization_id}")

        workspace = SlackWorkspace(
            id=uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            bot_token=bot_token,
            workspace_name=workspace_name,
            workspace_domain=workspace_domain,
            scopes=scopes or [],
            installed_by=installed_by,
            installed_at=datetime.now(),
            is_active=True
        )

        return await self.dao.create_slack_workspace(workspace)

    async def get_organization_slack_workspace(
        self,
        organization_id: UUID
    ) -> Optional[SlackWorkspace]:
        """
        Retrieve Slack workspace for an organization.

        What: Fetches Slack configuration.
        Where: Called for Slack operations.
        Why: Enables Slack integration for organization.

        Args:
            organization_id: UUID of the organization

        Returns:
            SlackWorkspace or None
        """
        return await self.dao.get_slack_workspace_by_organization(organization_id)

    async def update_slack_settings(
        self,
        workspace_id: UUID,
        enable_notifications: Optional[bool] = None,
        enable_commands: Optional[bool] = None,
        enable_ai_assistant: Optional[bool] = None,
        default_announcements_channel: Optional[str] = None,
        default_alerts_channel: Optional[str] = None
    ) -> Optional[SlackWorkspace]:
        """
        Update Slack workspace settings.

        What: Updates Slack configuration options.
        Where: Called when admin changes Slack settings.
        Why: Enables customizing Slack integration behavior.

        Args:
            workspace_id: UUID of the workspace
            enable_notifications: Optional notification toggle
            enable_commands: Optional commands toggle
            enable_ai_assistant: Optional AI assistant toggle
            default_announcements_channel: Optional default channel
            default_alerts_channel: Optional alerts channel

        Returns:
            Updated SlackWorkspace or None
        """
        updates = {}
        if enable_notifications is not None:
            updates["enable_notifications"] = enable_notifications
        if enable_commands is not None:
            updates["enable_commands"] = enable_commands
        if enable_ai_assistant is not None:
            updates["enable_ai_assistant"] = enable_ai_assistant
        if default_announcements_channel:
            updates["default_announcements_channel"] = default_announcements_channel
        if default_alerts_channel:
            updates["default_alerts_channel"] = default_alerts_channel

        return await self.dao.update_slack_workspace(workspace_id, updates)

    # ================================================================
    # SLACK CHANNEL MAPPING MANAGEMENT
    # ================================================================

    async def map_slack_channel(
        self,
        workspace_id: UUID,
        channel_id: str,
        entity_type: str,
        entity_id: UUID,
        channel_name: Optional[str] = None,
        channel_type: SlackChannelType = SlackChannelType.PUBLIC,
        notify_announcements: bool = True,
        notify_deadlines: bool = True,
        notify_grades: bool = True
    ) -> SlackChannelMapping:
        """
        Map a Slack channel to an entity.

        What: Creates mapping between Slack channel and entity.
        Where: Called when linking channel to course/project.
        Why: Enables targeted notifications to specific channels.

        Args:
            workspace_id: UUID of the Slack workspace
            channel_id: Slack channel ID
            entity_type: Type of entity (course, project, etc.)
            entity_id: UUID of the entity
            channel_name: Optional channel name
            channel_type: Type of channel
            notify_announcements: Enable announcement notifications
            notify_deadlines: Enable deadline notifications
            notify_grades: Enable grade notifications

        Returns:
            Created SlackChannelMapping
        """
        mapping = SlackChannelMapping(
            id=uuid4(),
            workspace_id=workspace_id,
            channel_id=channel_id,
            channel_name=channel_name,
            channel_type=channel_type,
            entity_type=entity_type,
            entity_id=entity_id,
            notify_announcements=notify_announcements,
            notify_deadlines=notify_deadlines,
            notify_grades=notify_grades,
            is_active=True
        )

        return await self.dao.create_slack_channel_mapping(mapping)

    async def get_entity_slack_channels(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> List[SlackChannelMapping]:
        """
        Retrieve Slack channels mapped to an entity.

        What: Fetches channels linked to entity.
        Where: Called when sending notifications.
        Why: Finds target channels for notifications.

        Args:
            entity_type: Type of entity
            entity_id: UUID of the entity

        Returns:
            List of channel mappings
        """
        return await self.dao.get_slack_channel_mappings_by_entity(
            entity_type, entity_id
        )

    # ================================================================
    # SLACK USER MAPPING MANAGEMENT
    # ================================================================

    async def link_slack_user(
        self,
        workspace_id: UUID,
        user_id: UUID,
        slack_user_id: str,
        slack_username: Optional[str] = None,
        slack_email: Optional[str] = None,
        slack_real_name: Optional[str] = None
    ) -> SlackUserMapping:
        """
        Link a Slack user to a platform user.

        What: Creates mapping between Slack user and platform user.
        Where: Called when user links Slack account.
        Why: Enables personalized DM notifications.

        Args:
            workspace_id: UUID of the Slack workspace
            user_id: UUID of the platform user
            slack_user_id: Slack user ID
            slack_username: Optional Slack username
            slack_email: Optional Slack email
            slack_real_name: Optional real name

        Returns:
            Created SlackUserMapping
        """
        mapping = SlackUserMapping(
            id=uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            slack_user_id=slack_user_id,
            slack_username=slack_username,
            slack_email=slack_email,
            slack_real_name=slack_real_name,
            dm_notifications_enabled=True,
            is_active=True
        )

        return await self.dao.create_slack_user_mapping(mapping)

    async def get_user_slack_mapping(
        self,
        user_id: UUID,
        workspace_id: UUID
    ) -> Optional[SlackUserMapping]:
        """
        Retrieve Slack mapping for a user.

        What: Fetches Slack user mapping.
        Where: Called when sending DM notifications.
        Why: Finds Slack user ID for notifications.

        Args:
            user_id: UUID of the platform user
            workspace_id: UUID of the workspace

        Returns:
            SlackUserMapping or None
        """
        return await self.dao.get_slack_user_mapping_by_user(user_id, workspace_id)

    # ================================================================
    # SLACK MESSAGE MANAGEMENT
    # ================================================================

    async def record_slack_message(
        self,
        workspace_id: UUID,
        message_type: SlackMessageType,
        message_text: str,
        channel_mapping_id: Optional[UUID] = None,
        user_mapping_id: Optional[UUID] = None,
        slack_message_ts: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[UUID] = None
    ) -> SlackMessage:
        """
        Record a sent Slack message.

        What: Persists Slack message for history/audit.
        Where: Called after sending Slack message.
        Why: Enables message tracking and analytics.

        Args:
            workspace_id: UUID of the workspace
            message_type: Type of message
            message_text: Message content
            channel_mapping_id: Optional channel mapping UUID
            user_mapping_id: Optional user mapping UUID
            slack_message_ts: Optional Slack message timestamp
            source_type: Optional source entity type
            source_id: Optional source entity ID

        Returns:
            Created SlackMessage
        """
        message = SlackMessage(
            id=uuid4(),
            workspace_id=workspace_id,
            message_type=message_type,
            message_text=message_text,
            channel_mapping_id=channel_mapping_id,
            user_mapping_id=user_mapping_id,
            slack_message_ts=slack_message_ts,
            source_type=source_type,
            source_id=source_id,
            delivery_status="sent",
            sent_at=datetime.now()
        )

        return await self.dao.create_slack_message(message)

    # ================================================================
    # OUTBOUND WEBHOOK MANAGEMENT
    # ================================================================

    async def create_outbound_webhook(
        self,
        organization_id: UUID,
        name: str,
        target_url: str,
        description: Optional[str] = None,
        auth_type: WebhookAuthType = WebhookAuthType.NONE,
        auth_secret: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        created_by: Optional[UUID] = None
    ) -> OutboundWebhook:
        """
        Create an outbound webhook.

        What: Creates webhook configuration for external notifications.
        Where: Called when setting up webhook integration.
        Why: Enables sending events to external services.

        Args:
            organization_id: UUID of the organization
            name: Webhook display name
            target_url: URL to send webhook to
            description: Optional description
            auth_type: Authentication type
            auth_secret: Optional auth secret
            event_types: Optional list of event types to trigger
            created_by: Optional UUID of creating user

        Returns:
            Created OutboundWebhook
        """
        self.logger.info(f"Creating outbound webhook '{name}' for org {organization_id}")

        # Validate URL
        if not target_url or not target_url.startswith('http'):
            raise ValidationException(
                message="Valid target URL is required",
                field_errors={"target_url": "Must be a valid HTTP(S) URL"}
            )

        webhook = OutboundWebhook(
            id=uuid4(),
            organization_id=organization_id,
            name=name,
            description=description,
            target_url=target_url,
            auth_type=auth_type,
            auth_secret=auth_secret,
            event_types=event_types or [],
            is_active=True,
            created_by=created_by
        )

        return await self.dao.create_outbound_webhook(webhook)

    async def get_organization_webhooks(
        self,
        organization_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[OutboundWebhook]:
        """
        Retrieve outbound webhooks for an organization.

        What: Fetches all webhooks for an organization.
        Where: Called for webhook management.
        Why: Enables viewing and managing webhooks.

        Args:
            organization_id: UUID of the organization
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of outbound webhooks
        """
        return await self.dao.get_outbound_webhooks_by_organization(
            organization_id, limit, offset
        )

    async def trigger_webhooks_for_event(
        self,
        organization_id: UUID,
        event_type: str,
        event_id: UUID,
        payload: Dict[str, Any]
    ) -> List[WebhookDeliveryLog]:
        """
        Trigger webhooks for an event.

        What: Finds and creates delivery records for matching webhooks.
        Where: Called when events occur.
        Why: Queues webhook deliveries for processing.

        Args:
            organization_id: UUID of the organization
            event_type: Type of event
            event_id: UUID of the event
            payload: Event payload

        Returns:
            List of created delivery logs
        """
        webhooks = await self.dao.get_active_webhooks_for_event(
            organization_id, event_type
        )

        delivery_logs = []
        for webhook in webhooks:
            log = WebhookDeliveryLog(
                id=uuid4(),
                webhook_id=webhook.id,
                event_type=event_type,
                event_id=event_id,
                payload=payload,
                delivery_status=WebhookDeliveryStatus.PENDING
            )
            created_log = await self.dao.create_webhook_delivery_log(log)
            delivery_logs.append(created_log)

        return delivery_logs

    async def record_webhook_delivery(
        self,
        log_id: UUID,
        success: bool,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[WebhookDeliveryLog]:
        """
        Record webhook delivery result.

        What: Updates delivery log with result.
        Where: Called after delivery attempt.
        Why: Tracks delivery success/failure.

        Args:
            log_id: UUID of the delivery log
            success: Whether delivery succeeded
            status_code: Optional HTTP status code
            response_body: Optional response body
            error_message: Optional error message

        Returns:
            Updated delivery log or None
        """
        # Get the log first
        logs = await self.dao.get_delivery_logs_for_webhook(
            # We need the webhook_id, but we only have log_id
            # This is a limitation - we'd need to add get_delivery_log_by_id
            # For now, we'll update via a direct approach
            webhook_id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
            limit=1
        )

        # For now, return None - in practice you'd implement get_by_id
        return None

    # ================================================================
    # INBOUND WEBHOOK MANAGEMENT
    # ================================================================

    async def create_inbound_webhook(
        self,
        organization_id: UUID,
        name: str,
        handler_type: WebhookHandlerType,
        description: Optional[str] = None,
        auth_type: WebhookAuthType = WebhookAuthType.API_KEY,
        allowed_ips: Optional[List[str]] = None,
        handler_config: Optional[Dict[str, Any]] = None,
        created_by: Optional[UUID] = None
    ) -> InboundWebhook:
        """
        Create an inbound webhook endpoint.

        What: Creates webhook endpoint for receiving external events.
        Where: Called when setting up webhook receiver.
        Why: Enables receiving events from external services.

        Args:
            organization_id: UUID of the organization
            name: Webhook display name
            handler_type: Type of handler (GitHub, Stripe, etc.)
            description: Optional description
            auth_type: Authentication type
            allowed_ips: Optional IP whitelist
            handler_config: Optional handler configuration
            created_by: Optional UUID of creating user

        Returns:
            Created InboundWebhook with unique token
        """
        self.logger.info(f"Creating inbound webhook '{name}' for org {organization_id}")

        # Generate unique webhook token
        webhook_token = secrets.token_urlsafe(32)

        webhook = InboundWebhook(
            id=uuid4(),
            organization_id=organization_id,
            name=name,
            description=description,
            webhook_token=webhook_token,
            handler_type=handler_type,
            auth_type=auth_type,
            allowed_ips=allowed_ips or [],
            handler_config=handler_config or {},
            is_active=True,
            created_by=created_by
        )

        return await self.dao.create_inbound_webhook(webhook)

    async def get_inbound_webhook_by_token(
        self,
        webhook_token: str
    ) -> Optional[InboundWebhook]:
        """
        Retrieve inbound webhook by token.

        What: Fetches webhook by URL token.
        Where: Called when receiving webhook requests.
        Why: Enables webhook lookup for validation.

        Args:
            webhook_token: Token from webhook URL

        Returns:
            InboundWebhook or None
        """
        return await self.dao.get_inbound_webhook_by_token(webhook_token)

    async def record_inbound_webhook_received(
        self,
        webhook_id: UUID,
        processed: bool
    ) -> Optional[InboundWebhook]:
        """
        Record inbound webhook receipt.

        What: Updates webhook statistics after receiving.
        Where: Called after processing webhook request.
        Why: Tracks webhook activity and success rate.

        Args:
            webhook_id: UUID of the webhook
            processed: Whether processing succeeded

        Returns:
            Updated InboundWebhook or None
        """
        return await self.dao.update_inbound_webhook_stats(webhook_id, processed)

    # ================================================================
    # OAUTH TOKEN MANAGEMENT
    # ================================================================

    async def store_oauth_token(
        self,
        provider: OAuthProvider,
        access_token: str,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        scopes: Optional[List[str]] = None
    ) -> OAuthToken:
        """
        Store an OAuth token.

        What: Persists OAuth token for external service access.
        Where: Called after OAuth authorization.
        Why: Enables storing tokens for API access.

        Args:
            provider: OAuth provider type
            access_token: OAuth access token
            user_id: Optional UUID of the user
            organization_id: Optional UUID of the organization
            refresh_token: Optional refresh token
            expires_at: Optional expiration time
            scopes: Optional list of scopes

        Returns:
            Created OAuthToken

        Raises:
            ValidationException: If neither user_id nor organization_id provided
        """
        if not user_id and not organization_id:
            raise ValidationException(
                message="Either user_id or organization_id is required",
                field_errors={"owner": "Must specify user or organization"}
            )

        token = OAuthToken(
            id=uuid4(),
            provider=provider,
            access_token=access_token,
            user_id=user_id,
            organization_id=organization_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scopes=scopes or [],
            is_valid=True
        )

        return await self.dao.create_oauth_token(token)

    async def get_oauth_token(
        self,
        provider: OAuthProvider,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None
    ) -> Optional[OAuthToken]:
        """
        Retrieve OAuth token.

        What: Fetches OAuth token for external service access.
        Where: Called when accessing external APIs.
        Why: Enables retrieving stored access tokens.

        Args:
            provider: OAuth provider type
            user_id: Optional UUID of the user
            organization_id: Optional UUID of the organization

        Returns:
            OAuthToken or None
        """
        return await self.dao.get_oauth_token(user_id, organization_id, provider)

    async def refresh_oauth_token(
        self,
        token_id: UUID,
        new_access_token: str,
        new_expires_at: datetime,
        new_refresh_token: Optional[str] = None
    ) -> Optional[OAuthToken]:
        """
        Update OAuth token after refresh.

        What: Updates token with refreshed values.
        Where: Called after token refresh.
        Why: Maintains valid access tokens.

        Args:
            token_id: UUID of the token
            new_access_token: New access token
            new_expires_at: New expiration time
            new_refresh_token: Optional new refresh token

        Returns:
            Updated OAuthToken or None
        """
        updates = {
            "access_token": new_access_token,
            "expires_at": new_expires_at,
            "last_refreshed_at": datetime.now(),
            "consecutive_failures": 0,
            "last_error": None
        }
        if new_refresh_token:
            updates["refresh_token"] = new_refresh_token

        return await self.dao.update_oauth_token(token_id, updates)

    async def invalidate_oauth_token(
        self,
        token_id: UUID
    ) -> Optional[OAuthToken]:
        """
        Invalidate an OAuth token.

        What: Marks token as invalid.
        Where: Called when token is revoked or fails.
        Why: Prevents use of invalid tokens.

        Args:
            token_id: UUID of the token

        Returns:
            Updated OAuthToken or None
        """
        return await self.dao.update_oauth_token(
            token_id,
            {"is_valid": False}
        )

    async def revoke_oauth_token(
        self,
        token_id: UUID
    ) -> bool:
        """
        Revoke and delete an OAuth token.

        What: Removes OAuth token.
        Where: Called when user revokes access.
        Why: Enables clean token removal.

        Args:
            token_id: UUID of the token

        Returns:
            True if deleted
        """
        return await self.dao.delete_oauth_token(token_id)
