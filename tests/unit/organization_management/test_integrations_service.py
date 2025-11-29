"""
Unit tests for IntegrationsService

What: Tests for the integrations service business logic layer.
Where: Organization Management service application layer tests.
Why: Ensures:
     1. Service methods correctly validate inputs
     2. Business logic is properly applied before DAO calls
     3. Error handling produces appropriate exceptions
     4. Token and credential management works correctly
     5. Multi-tenant isolation is maintained

BUSINESS CONTEXT:
The IntegrationsService provides the business logic layer for:
- LTI 1.3 platform registration and context management
- Calendar provider synchronization
- Slack workspace and channel integration
- Webhook management for external notifications
- OAuth token lifecycle management
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from organization_management.application.services.integrations_service import IntegrationsService
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
    GradeSyncStatus,
    CalendarProviderType,
    CalendarSyncStatus,
    SlackChannelType,
    SlackMessageType,
    WebhookAuthType,
    WebhookDeliveryStatus,
    WebhookHandlerType,
    OAuthProvider
)
from organization_management.exceptions import ValidationException


@pytest.fixture
def mock_dao():
    """Create a mock DAO for testing"""
    dao = AsyncMock()
    return dao


@pytest.fixture
def integrations_service(mock_dao):
    """Create IntegrationsService with mock DAO"""
    return IntegrationsService(mock_dao)


# ============================================================================
# LTI PLATFORM MANAGEMENT TESTS
# ============================================================================

class TestRegisterLTIPlatform:
    """Test LTI platform registration"""

    @pytest.mark.asyncio
    async def test_register_lti_platform_success(self, integrations_service, mock_dao):
        """Test successful LTI platform registration"""
        org_id = uuid4()
        created_platform = LTIPlatformRegistration(
            id=uuid4(),
            organization_id=org_id,
            platform_name="Canvas LMS",
            issuer="https://canvas.instructure.com",
            client_id="test-client-123",
            auth_login_url="https://canvas.instructure.com/auth",
            auth_token_url="https://canvas.instructure.com/token",
            jwks_url="https://canvas.instructure.com/jwks"
        )
        mock_dao.create_lti_platform.return_value = created_platform

        result = await integrations_service.register_lti_platform(
            organization_id=org_id,
            platform_name="Canvas LMS",
            issuer="https://canvas.instructure.com",
            client_id="test-client-123",
            auth_login_url="https://canvas.instructure.com/auth",
            auth_token_url="https://canvas.instructure.com/token",
            jwks_url="https://canvas.instructure.com/jwks"
        )

        assert result == created_platform
        mock_dao.create_lti_platform.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_lti_platform_with_scopes(self, integrations_service, mock_dao):
        """Test platform registration with scopes"""
        org_id = uuid4()
        scopes = ["scope1", "scope2"]
        mock_dao.create_lti_platform.return_value = MagicMock()

        await integrations_service.register_lti_platform(
            organization_id=org_id,
            platform_name="Canvas",
            issuer="https://canvas.com",
            client_id="client",
            auth_login_url="https://canvas.com/auth",
            auth_token_url="https://canvas.com/token",
            jwks_url="https://canvas.com/jwks",
            scopes=scopes
        )

        call_args = mock_dao.create_lti_platform.call_args[0][0]
        assert call_args.scopes == scopes

    @pytest.mark.asyncio
    async def test_register_lti_platform_empty_name_raises_error(self, integrations_service):
        """Test that empty platform name raises ValidationException"""
        with pytest.raises(ValidationException) as exc_info:
            await integrations_service.register_lti_platform(
                organization_id=uuid4(),
                platform_name="",
                issuer="https://canvas.com",
                client_id="client",
                auth_login_url="https://canvas.com/auth",
                auth_token_url="https://canvas.com/token",
                jwks_url="https://canvas.com/jwks"
            )

        assert "platform_name" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_register_lti_platform_whitespace_name_raises_error(self, integrations_service):
        """Test that whitespace-only platform name raises ValidationException"""
        with pytest.raises(ValidationException) as exc_info:
            await integrations_service.register_lti_platform(
                organization_id=uuid4(),
                platform_name="   ",
                issuer="https://canvas.com",
                client_id="client",
                auth_login_url="https://canvas.com/auth",
                auth_token_url="https://canvas.com/token",
                jwks_url="https://canvas.com/jwks"
            )

        assert "platform_name" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_register_lti_platform_invalid_issuer_raises_error(self, integrations_service):
        """Test that invalid issuer URL raises ValidationException"""
        with pytest.raises(ValidationException) as exc_info:
            await integrations_service.register_lti_platform(
                organization_id=uuid4(),
                platform_name="Canvas",
                issuer="invalid-url",
                client_id="client",
                auth_login_url="https://canvas.com/auth",
                auth_token_url="https://canvas.com/token",
                jwks_url="https://canvas.com/jwks"
            )

        assert "issuer" in exc_info.value.field_errors


class TestGetLTIPlatform:
    """Test LTI platform retrieval"""

    @pytest.mark.asyncio
    async def test_get_lti_platform_success(self, integrations_service, mock_dao):
        """Test successful platform retrieval"""
        platform_id = uuid4()
        expected_platform = MagicMock()
        mock_dao.get_lti_platform_by_id.return_value = expected_platform

        result = await integrations_service.get_lti_platform(platform_id)

        assert result == expected_platform
        mock_dao.get_lti_platform_by_id.assert_called_once_with(platform_id)

    @pytest.mark.asyncio
    async def test_get_lti_platform_by_issuer_success(self, integrations_service, mock_dao):
        """Test platform retrieval by issuer and client ID"""
        issuer = "https://canvas.com"
        client_id = "client-123"
        expected_platform = MagicMock()
        mock_dao.get_lti_platform_by_issuer.return_value = expected_platform

        result = await integrations_service.get_lti_platform_by_issuer(issuer, client_id)

        assert result == expected_platform
        mock_dao.get_lti_platform_by_issuer.assert_called_once_with(issuer, client_id)

    @pytest.mark.asyncio
    async def test_get_organization_lti_platforms(self, integrations_service, mock_dao):
        """Test retrieving all platforms for an organization"""
        org_id = uuid4()
        expected_platforms = [MagicMock(), MagicMock()]
        mock_dao.get_lti_platforms_by_organization.return_value = expected_platforms

        result = await integrations_service.get_organization_lti_platforms(org_id)

        assert result == expected_platforms
        mock_dao.get_lti_platforms_by_organization.assert_called_once_with(org_id, 100, 0)


class TestVerifyLTIPlatform:
    """Test LTI platform verification"""

    @pytest.mark.asyncio
    async def test_verify_lti_platform_success(self, integrations_service, mock_dao):
        """Test successful platform verification"""
        platform_id = uuid4()
        updated_platform = MagicMock()
        mock_dao.update_lti_platform.return_value = updated_platform

        result = await integrations_service.verify_lti_platform(platform_id)

        assert result == updated_platform
        call_args = mock_dao.update_lti_platform.call_args
        assert call_args[0][0] == platform_id
        assert "verified_at" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_verify_lti_platform_not_found_raises_error(self, integrations_service, mock_dao):
        """Test verification of non-existent platform raises error"""
        platform_id = uuid4()
        mock_dao.update_lti_platform.return_value = None

        with pytest.raises(ValidationException) as exc_info:
            await integrations_service.verify_lti_platform(platform_id)

        assert "platform_id" in exc_info.value.field_errors


class TestRecordLTIConnection:
    """Test recording LTI connections"""

    @pytest.mark.asyncio
    async def test_record_lti_connection_success(self, integrations_service, mock_dao):
        """Test recording platform connection"""
        platform_id = uuid4()
        updated_platform = MagicMock()
        mock_dao.update_lti_platform.return_value = updated_platform

        result = await integrations_service.record_lti_connection(platform_id)

        assert result == updated_platform
        call_args = mock_dao.update_lti_platform.call_args
        assert "last_connection_at" in call_args[0][1]


class TestDeactivateLTIPlatform:
    """Test LTI platform deactivation"""

    @pytest.mark.asyncio
    async def test_deactivate_lti_platform_success(self, integrations_service, mock_dao):
        """Test platform deactivation"""
        platform_id = uuid4()
        mock_dao.update_lti_platform.return_value = MagicMock()

        await integrations_service.deactivate_lti_platform(platform_id)

        call_args = mock_dao.update_lti_platform.call_args
        assert call_args[0][1]["is_active"] is False


# ============================================================================
# LTI CONTEXT MANAGEMENT TESTS
# ============================================================================

class TestCreateOrUpdateLTIContext:
    """Test LTI context creation and updates"""

    @pytest.mark.asyncio
    async def test_create_new_lti_context(self, integrations_service, mock_dao):
        """Test creating a new LTI context"""
        platform_id = uuid4()
        lti_context_id = "course-python-101"

        mock_dao.get_lti_context_by_lti_id.return_value = None
        created_context = MagicMock()
        mock_dao.create_lti_context.return_value = created_context

        result = await integrations_service.create_or_update_lti_context(
            platform_id=platform_id,
            lti_context_id=lti_context_id,
            lti_context_type="CourseSection",
            lti_context_title="Python 101"
        )

        assert result == created_context
        mock_dao.create_lti_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_existing_lti_context(self, integrations_service, mock_dao):
        """Test updating an existing LTI context"""
        platform_id = uuid4()
        lti_context_id = "course-python-101"
        existing_context = MagicMock()
        existing_context.id = uuid4()

        mock_dao.get_lti_context_by_lti_id.return_value = existing_context
        updated_context = MagicMock()
        mock_dao.update_lti_context.return_value = updated_context

        result = await integrations_service.create_or_update_lti_context(
            platform_id=platform_id,
            lti_context_id=lti_context_id,
            lti_context_type="CourseSection",
            lti_context_title="Python 101 Updated"
        )

        assert result == updated_context
        mock_dao.create_lti_context.assert_not_called()
        mock_dao.update_lti_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_link_context_to_course(self, integrations_service, mock_dao):
        """Test linking context to a course"""
        context_id = uuid4()
        course_id = uuid4()
        mock_dao.update_lti_context.return_value = MagicMock()

        await integrations_service.link_context_to_course(context_id, course_id)

        call_args = mock_dao.update_lti_context.call_args
        assert call_args[0][1]["course_id"] == course_id


# ============================================================================
# LTI USER MANAGEMENT TESTS
# ============================================================================

class TestCreateOrUpdateLTIUser:
    """Test LTI user mapping creation and updates"""

    @pytest.mark.asyncio
    async def test_create_new_lti_user_mapping(self, integrations_service, mock_dao):
        """Test creating a new LTI user mapping"""
        platform_id = uuid4()
        user_id = uuid4()
        lti_user_id = "lti-user-123"

        mock_dao.get_lti_user_mapping_by_lti_user.return_value = None
        created_mapping = MagicMock()
        mock_dao.create_lti_user_mapping.return_value = created_mapping

        result = await integrations_service.create_or_update_lti_user(
            platform_id=platform_id,
            user_id=user_id,
            lti_user_id=lti_user_id,
            lti_email="student@example.com",
            lti_name="John Doe"
        )

        assert result == created_mapping
        call_args = mock_dao.create_lti_user_mapping.call_args[0][0]
        assert call_args.login_count == 1

    @pytest.mark.asyncio
    async def test_update_existing_lti_user_mapping(self, integrations_service, mock_dao):
        """Test updating an existing LTI user mapping"""
        platform_id = uuid4()
        lti_user_id = "lti-user-123"
        existing_mapping = MagicMock()
        existing_mapping.id = uuid4()
        existing_mapping.login_count = 5

        mock_dao.get_lti_user_mapping_by_lti_user.return_value = existing_mapping
        updated_mapping = MagicMock()
        mock_dao.update_lti_user_mapping.return_value = updated_mapping

        result = await integrations_service.create_or_update_lti_user(
            platform_id=platform_id,
            user_id=uuid4(),
            lti_user_id=lti_user_id
        )

        assert result == updated_mapping
        call_args = mock_dao.update_lti_user_mapping.call_args[0][1]
        assert call_args["login_count"] == 6


# ============================================================================
# LTI GRADE SYNC TESTS
# ============================================================================

class TestQueueGradeForSync:
    """Test grade sync queue operations"""

    @pytest.mark.asyncio
    async def test_queue_grade_for_sync_success(self, integrations_service, mock_dao):
        """Test queuing a grade for LTI sync"""
        context_id = uuid4()
        user_mapping_id = uuid4()
        created_grade_sync = MagicMock()
        mock_dao.create_lti_grade_sync.return_value = created_grade_sync

        result = await integrations_service.queue_grade_for_sync(
            context_id=context_id,
            user_mapping_id=user_mapping_id,
            score=Decimal("85.5"),
            max_score=Decimal("100"),
            comment="Good work!"
        )

        assert result == created_grade_sync
        call_args = mock_dao.create_lti_grade_sync.call_args[0][0]
        assert call_args.score == Decimal("85.5")
        assert call_args.sync_status == GradeSyncStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_pending_grade_syncs(self, integrations_service, mock_dao):
        """Test retrieving pending grade syncs"""
        pending_syncs = [MagicMock(), MagicMock()]
        mock_dao.get_pending_grade_syncs.return_value = pending_syncs

        result = await integrations_service.get_pending_grade_syncs(limit=50)

        assert result == pending_syncs
        mock_dao.get_pending_grade_syncs.assert_called_once_with(50)

    @pytest.mark.asyncio
    async def test_update_grade_sync_status(self, integrations_service, mock_dao):
        """Test updating grade sync status"""
        grade_sync_id = uuid4()
        mock_dao.update_grade_sync_status.return_value = MagicMock()

        await integrations_service.update_grade_sync_status(
            grade_sync_id=grade_sync_id,
            status=GradeSyncStatus.CONFIRMED
        )

        mock_dao.update_grade_sync_status.assert_called_once_with(
            grade_sync_id, GradeSyncStatus.CONFIRMED, None
        )


# ============================================================================
# CALENDAR PROVIDER TESTS
# ============================================================================

class TestConnectCalendar:
    """Test calendar provider connection"""

    @pytest.mark.asyncio
    async def test_connect_calendar_success(self, integrations_service, mock_dao):
        """Test successful calendar connection"""
        user_id = uuid4()
        created_provider = MagicMock()
        mock_dao.create_calendar_provider.return_value = created_provider

        result = await integrations_service.connect_calendar(
            user_id=user_id,
            provider_type=CalendarProviderType.GOOGLE,
            access_token="access-token-123",
            refresh_token="refresh-token-456"
        )

        assert result == created_provider
        call_args = mock_dao.create_calendar_provider.call_args[0][0]
        assert call_args.is_connected is True
        assert call_args.sync_enabled is True

    @pytest.mark.asyncio
    async def test_get_user_calendars(self, integrations_service, mock_dao):
        """Test retrieving user calendars"""
        user_id = uuid4()
        calendars = [MagicMock(), MagicMock()]
        mock_dao.get_calendar_providers_by_user.return_value = calendars

        result = await integrations_service.get_user_calendars(user_id)

        assert result == calendars
        mock_dao.get_calendar_providers_by_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_update_calendar_tokens(self, integrations_service, mock_dao):
        """Test updating calendar OAuth tokens"""
        provider_id = uuid4()
        new_expires = datetime.now() + timedelta(hours=1)
        mock_dao.update_calendar_provider.return_value = MagicMock()

        await integrations_service.update_calendar_tokens(
            provider_id=provider_id,
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            token_expires_at=new_expires
        )

        call_args = mock_dao.update_calendar_provider.call_args[0][1]
        assert call_args["access_token"] == "new-access-token"
        assert call_args["refresh_token"] == "new-refresh-token"

    @pytest.mark.asyncio
    async def test_disconnect_calendar(self, integrations_service, mock_dao):
        """Test disconnecting a calendar"""
        provider_id = uuid4()
        mock_dao.delete_calendar_provider.return_value = True

        result = await integrations_service.disconnect_calendar(provider_id)

        assert result is True
        mock_dao.delete_calendar_provider.assert_called_once_with(provider_id)


# ============================================================================
# CALENDAR EVENT TESTS
# ============================================================================

class TestSyncCalendarEvent:
    """Test calendar event synchronization"""

    @pytest.mark.asyncio
    async def test_sync_calendar_event_success(self, integrations_service, mock_dao):
        """Test syncing a calendar event"""
        provider_id = uuid4()
        user_id = uuid4()
        created_event = MagicMock()
        mock_dao.create_calendar_event.return_value = created_event

        start_time = datetime.now() + timedelta(hours=1)
        end_time = datetime.now() + timedelta(hours=2)

        result = await integrations_service.sync_calendar_event(
            provider_id=provider_id,
            user_id=user_id,
            title="Team Meeting",
            start_time=start_time,
            end_time=end_time,
            description="Weekly team standup"
        )

        assert result == created_event
        call_args = mock_dao.create_calendar_event.call_args[0][0]
        assert call_args.sync_status == CalendarSyncStatus.SYNCED

    @pytest.mark.asyncio
    async def test_get_user_calendar_events(self, integrations_service, mock_dao):
        """Test retrieving user calendar events"""
        user_id = uuid4()
        events = [MagicMock(), MagicMock()]
        mock_dao.get_calendar_events_by_user.return_value = events

        result = await integrations_service.get_user_calendar_events(user_id)

        assert result == events


# ============================================================================
# SLACK WORKSPACE TESTS
# ============================================================================

class TestConnectSlackWorkspace:
    """Test Slack workspace connection"""

    @pytest.mark.asyncio
    async def test_connect_slack_workspace_success(self, integrations_service, mock_dao):
        """Test successful Slack workspace connection"""
        org_id = uuid4()
        created_workspace = MagicMock()
        mock_dao.create_slack_workspace.return_value = created_workspace

        result = await integrations_service.connect_slack_workspace(
            organization_id=org_id,
            workspace_id="T12345678",
            bot_token="xoxb-test-token",
            workspace_name="Test Workspace",
            scopes=["chat:write", "channels:read"]
        )

        assert result == created_workspace
        call_args = mock_dao.create_slack_workspace.call_args[0][0]
        assert call_args.is_active is True
        assert call_args.installed_at is not None

    @pytest.mark.asyncio
    async def test_get_organization_slack_workspace(self, integrations_service, mock_dao):
        """Test retrieving organization Slack workspace"""
        org_id = uuid4()
        workspace = MagicMock()
        mock_dao.get_slack_workspace_by_organization.return_value = workspace

        result = await integrations_service.get_organization_slack_workspace(org_id)

        assert result == workspace

    @pytest.mark.asyncio
    async def test_update_slack_settings(self, integrations_service, mock_dao):
        """Test updating Slack workspace settings"""
        workspace_id = uuid4()
        mock_dao.update_slack_workspace.return_value = MagicMock()

        await integrations_service.update_slack_settings(
            workspace_id=workspace_id,
            enable_notifications=True,
            enable_commands=False,
            enable_ai_assistant=True,
            default_announcements_channel="C12345678"
        )

        call_args = mock_dao.update_slack_workspace.call_args[0][1]
        assert call_args["enable_notifications"] is True
        assert call_args["enable_commands"] is False
        assert call_args["enable_ai_assistant"] is True


# ============================================================================
# SLACK CHANNEL MAPPING TESTS
# ============================================================================

class TestMapSlackChannel:
    """Test Slack channel mapping"""

    @pytest.mark.asyncio
    async def test_map_slack_channel_success(self, integrations_service, mock_dao):
        """Test mapping a Slack channel to an entity"""
        workspace_id = uuid4()
        entity_id = uuid4()
        created_mapping = MagicMock()
        mock_dao.create_slack_channel_mapping.return_value = created_mapping

        result = await integrations_service.map_slack_channel(
            workspace_id=workspace_id,
            channel_id="C12345678",
            entity_type="course",
            entity_id=entity_id,
            channel_name="python-101",
            notify_announcements=True,
            notify_grades=True
        )

        assert result == created_mapping
        call_args = mock_dao.create_slack_channel_mapping.call_args[0][0]
        assert call_args.is_active is True

    @pytest.mark.asyncio
    async def test_get_entity_slack_channels(self, integrations_service, mock_dao):
        """Test retrieving Slack channels for an entity"""
        entity_id = uuid4()
        mappings = [MagicMock(), MagicMock()]
        mock_dao.get_slack_channel_mappings_by_entity.return_value = mappings

        result = await integrations_service.get_entity_slack_channels("course", entity_id)

        assert result == mappings


# ============================================================================
# SLACK USER MAPPING TESTS
# ============================================================================

class TestLinkSlackUser:
    """Test Slack user linking"""

    @pytest.mark.asyncio
    async def test_link_slack_user_success(self, integrations_service, mock_dao):
        """Test linking a Slack user to a platform user"""
        workspace_id = uuid4()
        user_id = uuid4()
        created_mapping = MagicMock()
        mock_dao.create_slack_user_mapping.return_value = created_mapping

        result = await integrations_service.link_slack_user(
            workspace_id=workspace_id,
            user_id=user_id,
            slack_user_id="U12345678",
            slack_username="johndoe",
            slack_email="john@example.com"
        )

        assert result == created_mapping
        call_args = mock_dao.create_slack_user_mapping.call_args[0][0]
        assert call_args.dm_notifications_enabled is True

    @pytest.mark.asyncio
    async def test_get_user_slack_mapping(self, integrations_service, mock_dao):
        """Test retrieving Slack mapping for a user"""
        user_id = uuid4()
        workspace_id = uuid4()
        mapping = MagicMock()
        mock_dao.get_slack_user_mapping_by_user.return_value = mapping

        result = await integrations_service.get_user_slack_mapping(user_id, workspace_id)

        assert result == mapping


# ============================================================================
# SLACK MESSAGE TESTS
# ============================================================================

class TestRecordSlackMessage:
    """Test Slack message recording"""

    @pytest.mark.asyncio
    async def test_record_slack_message_success(self, integrations_service, mock_dao):
        """Test recording a sent Slack message"""
        workspace_id = uuid4()
        created_message = MagicMock()
        mock_dao.create_slack_message.return_value = created_message

        result = await integrations_service.record_slack_message(
            workspace_id=workspace_id,
            message_type=SlackMessageType.ANNOUNCEMENT,
            message_text="Hello everyone!",
            slack_message_ts="1234567890.123456"
        )

        assert result == created_message
        call_args = mock_dao.create_slack_message.call_args[0][0]
        assert call_args.delivery_status == "sent"


# ============================================================================
# OUTBOUND WEBHOOK TESTS
# ============================================================================

class TestCreateOutboundWebhook:
    """Test outbound webhook creation"""

    @pytest.mark.asyncio
    async def test_create_outbound_webhook_success(self, integrations_service, mock_dao):
        """Test successful webhook creation"""
        org_id = uuid4()
        created_webhook = MagicMock()
        mock_dao.create_outbound_webhook.return_value = created_webhook

        result = await integrations_service.create_outbound_webhook(
            organization_id=org_id,
            name="Course Events",
            target_url="https://api.example.com/webhooks",
            event_types=["course.created", "course.published"]
        )

        assert result == created_webhook
        call_args = mock_dao.create_outbound_webhook.call_args[0][0]
        assert call_args.is_active is True

    @pytest.mark.asyncio
    async def test_create_outbound_webhook_invalid_url_raises_error(self, integrations_service):
        """Test that invalid URL raises ValidationException"""
        with pytest.raises(ValidationException) as exc_info:
            await integrations_service.create_outbound_webhook(
                organization_id=uuid4(),
                name="Test Webhook",
                target_url="invalid-url"
            )

        assert "target_url" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_get_organization_webhooks(self, integrations_service, mock_dao):
        """Test retrieving organization webhooks"""
        org_id = uuid4()
        webhooks = [MagicMock(), MagicMock()]
        mock_dao.get_outbound_webhooks_by_organization.return_value = webhooks

        result = await integrations_service.get_organization_webhooks(org_id)

        assert result == webhooks


class TestTriggerWebhooksForEvent:
    """Test webhook event triggering"""

    @pytest.mark.asyncio
    async def test_trigger_webhooks_for_event_success(self, integrations_service, mock_dao):
        """Test triggering webhooks for an event"""
        org_id = uuid4()
        event_id = uuid4()
        webhook1 = MagicMock()
        webhook1.id = uuid4()
        webhook2 = MagicMock()
        webhook2.id = uuid4()

        mock_dao.get_active_webhooks_for_event.return_value = [webhook1, webhook2]
        mock_dao.create_webhook_delivery_log.side_effect = lambda x: x

        result = await integrations_service.trigger_webhooks_for_event(
            organization_id=org_id,
            event_type="course.created",
            event_id=event_id,
            payload={"course_id": str(uuid4())}
        )

        assert len(result) == 2
        assert mock_dao.create_webhook_delivery_log.call_count == 2

    @pytest.mark.asyncio
    async def test_trigger_webhooks_no_matching_webhooks(self, integrations_service, mock_dao):
        """Test triggering when no webhooks match"""
        mock_dao.get_active_webhooks_for_event.return_value = []

        result = await integrations_service.trigger_webhooks_for_event(
            organization_id=uuid4(),
            event_type="unknown.event",
            event_id=uuid4(),
            payload={}
        )

        assert result == []


# ============================================================================
# INBOUND WEBHOOK TESTS
# ============================================================================

class TestCreateInboundWebhook:
    """Test inbound webhook creation"""

    @pytest.mark.asyncio
    async def test_create_inbound_webhook_success(self, integrations_service, mock_dao):
        """Test successful inbound webhook creation"""
        org_id = uuid4()
        created_webhook = MagicMock()
        mock_dao.create_inbound_webhook.return_value = created_webhook

        result = await integrations_service.create_inbound_webhook(
            organization_id=org_id,
            name="GitHub Webhook",
            handler_type=WebhookHandlerType.GITHUB,
            allowed_ips=["192.168.1.1"]
        )

        assert result == created_webhook
        call_args = mock_dao.create_inbound_webhook.call_args[0][0]
        assert call_args.is_active is True
        assert len(call_args.webhook_token) > 0  # Token should be generated

    @pytest.mark.asyncio
    async def test_get_inbound_webhook_by_token(self, integrations_service, mock_dao):
        """Test retrieving inbound webhook by token"""
        webhook = MagicMock()
        mock_dao.get_inbound_webhook_by_token.return_value = webhook

        result = await integrations_service.get_inbound_webhook_by_token("test-token")

        assert result == webhook

    @pytest.mark.asyncio
    async def test_record_inbound_webhook_received(self, integrations_service, mock_dao):
        """Test recording inbound webhook receipt"""
        webhook_id = uuid4()
        mock_dao.update_inbound_webhook_stats.return_value = MagicMock()

        await integrations_service.record_inbound_webhook_received(
            webhook_id=webhook_id,
            processed=True
        )

        mock_dao.update_inbound_webhook_stats.assert_called_once_with(webhook_id, True)


# ============================================================================
# OAUTH TOKEN TESTS
# ============================================================================

class TestStoreOAuthToken:
    """Test OAuth token storage"""

    @pytest.mark.asyncio
    async def test_store_oauth_token_for_user_success(self, integrations_service, mock_dao):
        """Test storing OAuth token for a user"""
        user_id = uuid4()
        created_token = MagicMock()
        mock_dao.create_oauth_token.return_value = created_token

        result = await integrations_service.store_oauth_token(
            provider=OAuthProvider.GOOGLE,
            access_token="access-token-123",
            user_id=user_id,
            refresh_token="refresh-token-456"
        )

        assert result == created_token
        call_args = mock_dao.create_oauth_token.call_args[0][0]
        assert call_args.is_valid is True

    @pytest.mark.asyncio
    async def test_store_oauth_token_for_organization_success(self, integrations_service, mock_dao):
        """Test storing OAuth token for an organization"""
        org_id = uuid4()
        mock_dao.create_oauth_token.return_value = MagicMock()

        await integrations_service.store_oauth_token(
            provider=OAuthProvider.SLACK,
            access_token="xoxp-token-123",
            organization_id=org_id
        )

        call_args = mock_dao.create_oauth_token.call_args[0][0]
        assert call_args.organization_id == org_id

    @pytest.mark.asyncio
    async def test_store_oauth_token_no_owner_raises_error(self, integrations_service):
        """Test that missing owner raises ValidationException"""
        with pytest.raises(ValidationException) as exc_info:
            await integrations_service.store_oauth_token(
                provider=OAuthProvider.GOOGLE,
                access_token="test-token"
            )

        assert "owner" in exc_info.value.field_errors


class TestGetOAuthToken:
    """Test OAuth token retrieval"""

    @pytest.mark.asyncio
    async def test_get_oauth_token_success(self, integrations_service, mock_dao):
        """Test retrieving OAuth token"""
        user_id = uuid4()
        token = MagicMock()
        mock_dao.get_oauth_token.return_value = token

        result = await integrations_service.get_oauth_token(
            provider=OAuthProvider.GOOGLE,
            user_id=user_id
        )

        assert result == token
        mock_dao.get_oauth_token.assert_called_once_with(user_id, None, OAuthProvider.GOOGLE)


class TestRefreshOAuthToken:
    """Test OAuth token refresh"""

    @pytest.mark.asyncio
    async def test_refresh_oauth_token_success(self, integrations_service, mock_dao):
        """Test refreshing OAuth token"""
        token_id = uuid4()
        new_expires = datetime.now() + timedelta(hours=1)
        mock_dao.update_oauth_token.return_value = MagicMock()

        await integrations_service.refresh_oauth_token(
            token_id=token_id,
            new_access_token="new-access-token",
            new_expires_at=new_expires,
            new_refresh_token="new-refresh-token"
        )

        call_args = mock_dao.update_oauth_token.call_args[0][1]
        assert call_args["access_token"] == "new-access-token"
        assert call_args["refresh_token"] == "new-refresh-token"
        assert call_args["consecutive_failures"] == 0


class TestInvalidateOAuthToken:
    """Test OAuth token invalidation"""

    @pytest.mark.asyncio
    async def test_invalidate_oauth_token_success(self, integrations_service, mock_dao):
        """Test invalidating OAuth token"""
        token_id = uuid4()
        mock_dao.update_oauth_token.return_value = MagicMock()

        await integrations_service.invalidate_oauth_token(token_id)

        call_args = mock_dao.update_oauth_token.call_args[0][1]
        assert call_args["is_valid"] is False

    @pytest.mark.asyncio
    async def test_revoke_oauth_token_success(self, integrations_service, mock_dao):
        """Test revoking and deleting OAuth token"""
        token_id = uuid4()
        mock_dao.delete_oauth_token.return_value = True

        result = await integrations_service.revoke_oauth_token(token_id)

        assert result is True
        mock_dao.delete_oauth_token.assert_called_once_with(token_id)


# ============================================================================
# INTEGRATION SCENARIO TESTS
# ============================================================================

class TestLTIIntegrationScenario:
    """Test complete LTI integration scenarios"""

    @pytest.mark.asyncio
    async def test_complete_lti_launch_flow(self, integrations_service, mock_dao):
        """Test complete LTI launch flow through service"""
        org_id = uuid4()
        platform_id = uuid4()
        user_id = uuid4()

        # Step 1: Register platform
        platform = MagicMock()
        platform.id = platform_id
        mock_dao.create_lti_platform.return_value = platform

        await integrations_service.register_lti_platform(
            organization_id=org_id,
            platform_name="Canvas",
            issuer="https://canvas.com",
            client_id="client",
            auth_login_url="https://canvas.com/auth",
            auth_token_url="https://canvas.com/token",
            jwks_url="https://canvas.com/jwks"
        )

        # Step 2: Create context
        mock_dao.get_lti_context_by_lti_id.return_value = None
        context = MagicMock()
        context.id = uuid4()
        mock_dao.create_lti_context.return_value = context

        await integrations_service.create_or_update_lti_context(
            platform_id=platform_id,
            lti_context_id="course-123",
            lti_context_title="Python 101"
        )

        # Step 3: Create user mapping
        mock_dao.get_lti_user_mapping_by_lti_user.return_value = None
        mock_dao.create_lti_user_mapping.return_value = MagicMock()

        await integrations_service.create_or_update_lti_user(
            platform_id=platform_id,
            user_id=user_id,
            lti_user_id="lti-user-123"
        )

        # Verify all DAO calls were made
        assert mock_dao.create_lti_platform.called
        assert mock_dao.create_lti_context.called
        assert mock_dao.create_lti_user_mapping.called


class TestSlackIntegrationScenario:
    """Test complete Slack integration scenarios"""

    @pytest.mark.asyncio
    async def test_complete_slack_notification_flow(self, integrations_service, mock_dao):
        """Test complete Slack notification flow through service"""
        org_id = uuid4()
        workspace_id = uuid4()
        course_id = uuid4()

        # Step 1: Connect workspace
        workspace = MagicMock()
        workspace.id = workspace_id
        mock_dao.create_slack_workspace.return_value = workspace

        await integrations_service.connect_slack_workspace(
            organization_id=org_id,
            workspace_id="T12345678",
            bot_token="xoxb-token",
            workspace_name="Test Workspace"
        )

        # Step 2: Map channel
        mock_dao.create_slack_channel_mapping.return_value = MagicMock()

        await integrations_service.map_slack_channel(
            workspace_id=workspace_id,
            channel_id="C12345678",
            entity_type="course",
            entity_id=course_id,
            channel_name="python-101"
        )

        # Step 3: Record message
        mock_dao.create_slack_message.return_value = MagicMock()

        await integrations_service.record_slack_message(
            workspace_id=workspace_id,
            message_type=SlackMessageType.ANNOUNCEMENT,
            message_text="Hello!"
        )

        # Verify all DAO calls were made
        assert mock_dao.create_slack_workspace.called
        assert mock_dao.create_slack_channel_mapping.called
        assert mock_dao.create_slack_message.called


class TestWebhookIntegrationScenario:
    """Test complete webhook integration scenarios"""

    @pytest.mark.asyncio
    async def test_complete_outbound_webhook_flow(self, integrations_service, mock_dao):
        """Test complete outbound webhook flow through service"""
        org_id = uuid4()
        webhook_id = uuid4()

        # Step 1: Create webhook
        webhook = MagicMock()
        webhook.id = webhook_id
        mock_dao.create_outbound_webhook.return_value = webhook

        await integrations_service.create_outbound_webhook(
            organization_id=org_id,
            name="Course Events",
            target_url="https://api.example.com/webhooks",
            event_types=["course.created"]
        )

        # Step 2: Trigger webhook
        mock_dao.get_active_webhooks_for_event.return_value = [webhook]
        mock_dao.create_webhook_delivery_log.side_effect = lambda x: x

        result = await integrations_service.trigger_webhooks_for_event(
            organization_id=org_id,
            event_type="course.created",
            event_id=uuid4(),
            payload={"course_id": "123"}
        )

        assert len(result) == 1
        assert mock_dao.create_webhook_delivery_log.called
