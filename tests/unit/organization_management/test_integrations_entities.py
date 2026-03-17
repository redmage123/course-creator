"""
Unit tests for integration domain entities

What: Tests for LTI, Calendar, Slack, Webhook, and OAuth integration entities.
Where: Organization Management service domain layer tests.
Why: Ensures:
     1. Entity creation and validation works correctly
     2. Business logic methods produce expected results
     3. State transitions follow correct patterns
     4. Edge cases are handled properly

BUSINESS CONTEXT:
These entities support external integrations including:
- LTI 1.3 for LMS connections (Canvas, Moodle, etc.)
- Calendar synchronization (Google, Outlook, Apple)
- Slack workspace and channel integrations
- Webhook management for external notifications
- OAuth token lifecycle management
"""
import pytest
from datetime import datetime, timedelta, time
from decimal import Decimal
from uuid import uuid4

from organization_management.domain.entities.integrations import (
    # Enums
    LTIVersion,
    LTIScope,
    LTIContextType,
    LTIRole,
    GradeSyncStatus,
    CalendarProviderType,
    SyncDirection,
    CalendarEventType,
    CalendarSyncStatus,
    SlackChannelType,
    SlackMessageType,
    WebhookAuthType,
    WebhookDeliveryStatus,
    WebhookHandlerType,
    OAuthProvider,
    # Entities
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
    OAuthToken
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestLTIEnums:
    """Test LTI-related enums"""

    def test_lti_version_enum(self):
        """Test LTI version enum values"""
        assert LTIVersion.LTI_1_1.value == "1.1"
        assert LTIVersion.LTI_1_3.value == "1.3"

    def test_lti_scope_enum(self):
        """Test LTI scope enum values contain valid URIs"""
        assert "purl.imsglobal.org" in LTIScope.NAMES_ROLE_SERVICE.value
        assert "purl.imsglobal.org" in LTIScope.ASSIGNMENT_GRADE_SERVICE_LINEITEM.value
        assert "purl.imsglobal.org" in LTIScope.ASSIGNMENT_GRADE_SERVICE_SCORE.value

    def test_lti_context_type_enum(self):
        """Test LTI context type enum values"""
        assert LTIContextType.COURSE_TEMPLATE.value == "CourseTemplate"
        assert LTIContextType.COURSE_OFFERING.value == "CourseOffering"
        assert LTIContextType.COURSE_SECTION.value == "CourseSection"
        assert LTIContextType.GROUP.value == "Group"

    def test_lti_role_enum(self):
        """Test LTI role enum contains valid IMS URIs"""
        assert "purl.imsglobal.org" in LTIRole.ADMINISTRATOR.value
        assert "purl.imsglobal.org" in LTIRole.INSTRUCTOR.value
        assert "purl.imsglobal.org" in LTIRole.LEARNER.value
        assert "purl.imsglobal.org" in LTIRole.MENTOR.value

    def test_grade_sync_status_enum(self):
        """Test grade sync status enum values"""
        assert GradeSyncStatus.PENDING.value == "pending"
        assert GradeSyncStatus.SENT.value == "sent"
        assert GradeSyncStatus.CONFIRMED.value == "confirmed"
        assert GradeSyncStatus.FAILED.value == "failed"


class TestCalendarEnums:
    """Test Calendar-related enums"""

    def test_calendar_provider_type_enum(self):
        """Test calendar provider type enum values"""
        assert CalendarProviderType.GOOGLE.value == "google"
        assert CalendarProviderType.OUTLOOK.value == "outlook"
        assert CalendarProviderType.APPLE.value == "apple"
        assert CalendarProviderType.CALDAV.value == "caldav"

    def test_sync_direction_enum(self):
        """Test sync direction enum values"""
        assert SyncDirection.BIDIRECTIONAL.value == "bidirectional"
        assert SyncDirection.PUSH_ONLY.value == "push_only"
        assert SyncDirection.PULL_ONLY.value == "pull_only"

    def test_calendar_event_type_enum(self):
        """Test calendar event type enum values"""
        assert CalendarEventType.DEADLINE.value == "deadline"
        assert CalendarEventType.CLASS_SESSION.value == "class_session"
        assert CalendarEventType.QUIZ.value == "quiz"
        assert CalendarEventType.LAB.value == "lab"

    def test_calendar_sync_status_enum(self):
        """Test calendar sync status enum values"""
        assert CalendarSyncStatus.SYNCED.value == "synced"
        assert CalendarSyncStatus.PENDING.value == "pending"
        assert CalendarSyncStatus.CONFLICT.value == "conflict"
        assert CalendarSyncStatus.ERROR.value == "error"


class TestSlackEnums:
    """Test Slack-related enums"""

    def test_slack_channel_type_enum(self):
        """Test Slack channel type enum values"""
        assert SlackChannelType.PUBLIC.value == "channel"
        assert SlackChannelType.PRIVATE.value == "private"
        assert SlackChannelType.DIRECT_MESSAGE.value == "dm"

    def test_slack_message_type_enum(self):
        """Test Slack message type enum values"""
        assert SlackMessageType.ANNOUNCEMENT.value == "announcement"
        assert SlackMessageType.DEADLINE_REMINDER.value == "deadline_reminder"
        assert SlackMessageType.GRADE_NOTIFICATION.value == "grade_notification"
        assert SlackMessageType.NEW_CONTENT.value == "new_content"
        assert SlackMessageType.SYSTEM_ALERT.value == "system_alert"


class TestWebhookEnums:
    """Test Webhook-related enums"""

    def test_webhook_auth_type_enum(self):
        """Test webhook auth type enum values"""
        assert WebhookAuthType.NONE.value == "none"
        assert WebhookAuthType.BEARER.value == "bearer"
        assert WebhookAuthType.BASIC.value == "basic"
        assert WebhookAuthType.HMAC.value == "hmac"
        assert WebhookAuthType.API_KEY.value == "api_key"

    def test_webhook_delivery_status_enum(self):
        """Test webhook delivery status enum values"""
        assert WebhookDeliveryStatus.PENDING.value == "pending"
        assert WebhookDeliveryStatus.SUCCESS.value == "success"
        assert WebhookDeliveryStatus.FAILED.value == "failed"
        assert WebhookDeliveryStatus.RETRY_SCHEDULED.value == "retry_scheduled"

    def test_webhook_handler_type_enum(self):
        """Test webhook handler type enum values"""
        assert WebhookHandlerType.GITHUB.value == "github"
        assert WebhookHandlerType.STRIPE.value == "stripe"
        assert WebhookHandlerType.ZAPIER.value == "zapier"
        assert WebhookHandlerType.CUSTOM.value == "custom"
        assert WebhookHandlerType.LMS_WEBHOOK.value == "lms_webhook"


class TestOAuthEnums:
    """Test OAuth-related enums"""

    def test_oauth_provider_enum(self):
        """Test OAuth provider enum values"""
        assert OAuthProvider.GOOGLE.value == "google"
        assert OAuthProvider.MICROSOFT.value == "microsoft"
        assert OAuthProvider.SLACK.value == "slack"
        assert OAuthProvider.GITHUB.value == "github"
        assert OAuthProvider.ZOOM.value == "zoom"


# ============================================================================
# LTI ENTITY TESTS
# ============================================================================

class TestLTIPlatformRegistration:
    """Test LTIPlatformRegistration entity"""

    def test_platform_creation(self):
        """Test creating an LTI platform registration"""
        platform = LTIPlatformRegistration(
            organization_id=uuid4(),
            platform_name="Canvas LMS",
            issuer="https://canvas.instructure.com",
            client_id="test-client-123",
            auth_login_url="https://canvas.instructure.com/api/lti/authorize_redirect",
            auth_token_url="https://canvas.instructure.com/login/oauth2/token",
            jwks_url="https://canvas.instructure.com/api/lti/security/jwks"
        )

        assert platform.id is not None
        assert platform.platform_name == "Canvas LMS"
        assert platform.is_active is True
        assert platform.verified_at is None

    def test_platform_requires_name(self):
        """Test that platform name is required"""
        with pytest.raises(ValueError, match="Platform name is required"):
            LTIPlatformRegistration(
                organization_id=uuid4(),
                platform_name="",
                issuer="https://canvas.instructure.com",
                client_id="test-client",
                auth_login_url="https://test.com/auth",
                auth_token_url="https://test.com/token",
                jwks_url="https://test.com/jwks"
            )

    def test_platform_requires_issuer(self):
        """Test that issuer URL is required"""
        with pytest.raises(ValueError, match="Issuer URL is required"):
            LTIPlatformRegistration(
                organization_id=uuid4(),
                platform_name="Test Platform",
                issuer="",
                client_id="test-client",
                auth_login_url="https://test.com/auth",
                auth_token_url="https://test.com/token",
                jwks_url="https://test.com/jwks"
            )

    def test_platform_requires_client_id(self):
        """Test that client ID is required"""
        with pytest.raises(ValueError, match="Client ID is required"):
            LTIPlatformRegistration(
                organization_id=uuid4(),
                platform_name="Test Platform",
                issuer="https://test.com",
                client_id="",
                auth_login_url="https://test.com/auth",
                auth_token_url="https://test.com/token",
                jwks_url="https://test.com/jwks"
            )

    def test_platform_has_scope(self):
        """Test checking platform scopes"""
        platform = LTIPlatformRegistration(
            organization_id=uuid4(),
            platform_name="Canvas",
            issuer="https://canvas.com",
            client_id="client",
            auth_login_url="https://canvas.com/auth",
            auth_token_url="https://canvas.com/token",
            jwks_url="https://canvas.com/jwks",
            scopes=[LTIScope.NAMES_ROLE_SERVICE.value, LTIScope.ASSIGNMENT_GRADE_SERVICE_SCORE.value]
        )

        assert platform.has_scope(LTIScope.NAMES_ROLE_SERVICE)
        assert platform.has_scope(LTIScope.ASSIGNMENT_GRADE_SERVICE_SCORE)
        assert not platform.has_scope(LTIScope.DEEP_LINKING)

    def test_platform_mark_connected(self):
        """Test marking platform as connected"""
        platform = LTIPlatformRegistration(
            organization_id=uuid4(),
            platform_name="Canvas",
            issuer="https://canvas.com",
            client_id="client",
            auth_login_url="https://canvas.com/auth",
            auth_token_url="https://canvas.com/token",
            jwks_url="https://canvas.com/jwks"
        )

        assert platform.last_connection_at is None
        platform.mark_connected()
        assert platform.last_connection_at is not None

    def test_platform_verify(self):
        """Test verifying platform"""
        platform = LTIPlatformRegistration(
            organization_id=uuid4(),
            platform_name="Canvas",
            issuer="https://canvas.com",
            client_id="client",
            auth_login_url="https://canvas.com/auth",
            auth_token_url="https://canvas.com/token",
            jwks_url="https://canvas.com/jwks"
        )

        assert not platform.is_verified()
        platform.verify()
        assert platform.is_verified()
        assert platform.verified_at is not None


class TestLTIContext:
    """Test LTIContext entity"""

    def test_context_creation(self):
        """Test creating an LTI context"""
        context = LTIContext(
            platform_id=uuid4(),
            lti_context_id="course-123-section-1",
            lti_context_type="CourseSection",
            lti_context_title="Introduction to Python"
        )

        assert context.id is not None
        assert context.lti_context_id == "course-123-section-1"
        assert context.auto_roster_sync is False

    def test_context_requires_lti_context_id(self):
        """Test that LTI context ID is required"""
        with pytest.raises(ValueError, match="LTI context ID is required"):
            LTIContext(
                platform_id=uuid4(),
                lti_context_id=""
            )

    def test_context_roster_sync_interval_validation(self):
        """Test roster sync interval validation"""
        with pytest.raises(ValueError, match="Roster sync interval must be at least 1 hour"):
            LTIContext(
                platform_id=uuid4(),
                lti_context_id="test-context",
                roster_sync_interval_hours=0
            )

    def test_context_is_linked(self):
        """Test checking if context is linked"""
        context = LTIContext(
            platform_id=uuid4(),
            lti_context_id="test-context"
        )

        assert not context.is_linked()

        context.course_id = uuid4()
        assert context.is_linked()

    def test_context_needs_roster_sync(self):
        """Test checking if roster sync is needed"""
        context = LTIContext(
            platform_id=uuid4(),
            lti_context_id="test-context",
            auto_roster_sync=False
        )

        assert not context.needs_roster_sync()

        context.auto_roster_sync = True
        assert context.needs_roster_sync()  # No last_roster_sync

        context.last_roster_sync = datetime.now()
        assert not context.needs_roster_sync()

        context.last_roster_sync = datetime.now() - timedelta(hours=25)
        assert context.needs_roster_sync()

    def test_context_mark_roster_synced(self):
        """Test marking roster as synced"""
        context = LTIContext(
            platform_id=uuid4(),
            lti_context_id="test-context"
        )

        assert context.last_roster_sync is None
        context.mark_roster_synced()
        assert context.last_roster_sync is not None


class TestLTIUserMapping:
    """Test LTIUserMapping entity"""

    def test_user_mapping_creation(self):
        """Test creating an LTI user mapping"""
        mapping = LTIUserMapping(
            platform_id=uuid4(),
            user_id=uuid4(),
            lti_user_id="lti-user-123",
            lti_email="student@example.com",
            lti_name="John Doe",
            lti_roles=[LTIRole.LEARNER.value]
        )

        assert mapping.id is not None
        assert mapping.lti_user_id == "lti-user-123"
        assert mapping.is_active is True
        assert mapping.login_count == 0

    def test_user_mapping_requires_lti_user_id(self):
        """Test that LTI user ID is required"""
        with pytest.raises(ValueError, match="LTI user ID is required"):
            LTIUserMapping(
                platform_id=uuid4(),
                user_id=uuid4(),
                lti_user_id=""
            )

    def test_user_mapping_record_login(self):
        """Test recording login events"""
        mapping = LTIUserMapping(
            platform_id=uuid4(),
            user_id=uuid4(),
            lti_user_id="lti-user-123"
        )

        assert mapping.login_count == 0
        assert mapping.last_login_at is None

        mapping.record_login()
        assert mapping.login_count == 1
        assert mapping.last_login_at is not None

        mapping.record_login()
        assert mapping.login_count == 2

    def test_user_mapping_has_role(self):
        """Test checking user roles"""
        mapping = LTIUserMapping(
            platform_id=uuid4(),
            user_id=uuid4(),
            lti_user_id="lti-user-123",
            lti_roles=[LTIRole.INSTRUCTOR.value]
        )

        assert mapping.has_role(LTIRole.INSTRUCTOR)
        assert not mapping.has_role(LTIRole.LEARNER)

    def test_user_mapping_is_instructor(self):
        """Test instructor role check"""
        mapping = LTIUserMapping(
            platform_id=uuid4(),
            user_id=uuid4(),
            lti_user_id="lti-user-123",
            lti_roles=[LTIRole.INSTRUCTOR.value]
        )

        assert mapping.is_instructor()
        assert not mapping.is_learner()

    def test_user_mapping_is_learner(self):
        """Test learner role check"""
        mapping = LTIUserMapping(
            platform_id=uuid4(),
            user_id=uuid4(),
            lti_user_id="lti-user-123",
            lti_roles=[LTIRole.LEARNER.value]
        )

        assert mapping.is_learner()
        assert not mapping.is_instructor()


class TestLTIGradeSync:
    """Test LTIGradeSync entity"""

    def test_grade_sync_creation(self):
        """Test creating a grade sync record"""
        grade_sync = LTIGradeSync(
            context_id=uuid4(),
            user_mapping_id=uuid4(),
            score=Decimal("85.5"),
            max_score=Decimal("100"),
            comment="Good work!"
        )

        assert grade_sync.id is not None
        assert grade_sync.sync_status == GradeSyncStatus.PENDING
        assert grade_sync.retry_count == 0

    def test_grade_sync_negative_score_validation(self):
        """Test that negative scores are rejected"""
        with pytest.raises(ValueError, match="Score cannot be negative"):
            LTIGradeSync(
                context_id=uuid4(),
                user_mapping_id=uuid4(),
                score=Decimal("-5"),
                max_score=Decimal("100")
            )

    def test_grade_sync_zero_max_score_validation(self):
        """Test that zero max score is rejected"""
        with pytest.raises(ValueError, match="Max score must be positive"):
            LTIGradeSync(
                context_id=uuid4(),
                user_mapping_id=uuid4(),
                score=Decimal("50"),
                max_score=Decimal("0")
            )

    def test_grade_sync_get_score_percentage(self):
        """Test calculating score percentage"""
        grade_sync = LTIGradeSync(
            context_id=uuid4(),
            user_mapping_id=uuid4(),
            score=Decimal("75"),
            max_score=Decimal("100")
        )

        assert grade_sync.get_score_percentage() == Decimal("75.00")

        grade_sync.score = Decimal("45")
        grade_sync.max_score = Decimal("50")
        assert grade_sync.get_score_percentage() == Decimal("90.00")

    def test_grade_sync_mark_sent(self):
        """Test marking grade as sent"""
        grade_sync = LTIGradeSync(
            context_id=uuid4(),
            user_mapping_id=uuid4()
        )

        grade_sync.mark_sent()
        assert grade_sync.sync_status == GradeSyncStatus.SENT
        assert grade_sync.last_sync_attempt is not None

    def test_grade_sync_mark_confirmed(self):
        """Test marking grade as confirmed"""
        grade_sync = LTIGradeSync(
            context_id=uuid4(),
            user_mapping_id=uuid4()
        )

        grade_sync.mark_confirmed()
        assert grade_sync.sync_status == GradeSyncStatus.CONFIRMED
        assert grade_sync.last_sync_success is not None

    def test_grade_sync_mark_failed(self):
        """Test marking grade sync as failed"""
        grade_sync = LTIGradeSync(
            context_id=uuid4(),
            user_mapping_id=uuid4()
        )

        grade_sync.mark_failed("Network timeout")
        assert grade_sync.sync_status == GradeSyncStatus.FAILED
        assert grade_sync.sync_error_message == "Network timeout"
        assert grade_sync.retry_count == 1

    def test_grade_sync_can_retry(self):
        """Test retry logic"""
        grade_sync = LTIGradeSync(
            context_id=uuid4(),
            user_mapping_id=uuid4()
        )

        assert grade_sync.can_retry()

        grade_sync.retry_count = 2
        assert grade_sync.can_retry()

        grade_sync.retry_count = 3
        assert not grade_sync.can_retry()


# ============================================================================
# CALENDAR ENTITY TESTS
# ============================================================================

class TestCalendarProvider:
    """Test CalendarProvider entity"""

    def test_provider_creation(self):
        """Test creating a calendar provider"""
        provider = CalendarProvider(
            user_id=uuid4(),
            provider_type=CalendarProviderType.GOOGLE,
            access_token="test-token-123"
        )

        assert provider.id is not None
        assert provider.provider_type == CalendarProviderType.GOOGLE
        assert provider.sync_enabled is True
        assert provider.sync_direction == SyncDirection.BIDIRECTIONAL

    def test_provider_reminder_validation(self):
        """Test reminder minutes validation"""
        with pytest.raises(ValueError, match="Reminder minutes must be non-negative"):
            CalendarProvider(
                user_id=uuid4(),
                provider_type=CalendarProviderType.GOOGLE,
                reminder_minutes_before=-5
            )

    def test_provider_is_token_expired(self):
        """Test token expiration check"""
        provider = CalendarProvider(
            user_id=uuid4(),
            provider_type=CalendarProviderType.GOOGLE,
            token_expires_at=datetime.now() + timedelta(hours=1)
        )

        assert not provider.is_token_expired()

        provider.token_expires_at = datetime.now() - timedelta(hours=1)
        assert provider.is_token_expired()

        provider.token_expires_at = None
        assert provider.is_token_expired()

    def test_provider_needs_refresh(self):
        """Test token refresh check"""
        provider = CalendarProvider(
            user_id=uuid4(),
            provider_type=CalendarProviderType.GOOGLE,
            token_expires_at=datetime.now() + timedelta(hours=1)
        )

        assert not provider.needs_refresh()

        provider.token_expires_at = datetime.now() + timedelta(minutes=3)
        assert provider.needs_refresh()

    def test_provider_mark_connected(self):
        """Test marking provider as connected"""
        provider = CalendarProvider(
            user_id=uuid4(),
            provider_type=CalendarProviderType.GOOGLE,
            is_connected=False,
            connection_error_count=5
        )

        provider.mark_connected()
        assert provider.is_connected is True
        assert provider.connection_error_count == 0
        assert provider.last_sync_error is None

    def test_provider_mark_disconnected(self):
        """Test marking provider as disconnected"""
        provider = CalendarProvider(
            user_id=uuid4(),
            provider_type=CalendarProviderType.GOOGLE,
            is_connected=True
        )

        provider.mark_disconnected("Token revoked")
        assert provider.is_connected is False
        assert provider.last_sync_error == "Token revoked"
        assert provider.connection_error_count == 1


class TestCalendarEvent:
    """Test CalendarEvent entity"""

    def test_event_creation(self):
        """Test creating a calendar event"""
        event = CalendarEvent(
            provider_id=uuid4(),
            user_id=uuid4(),
            title="Team Meeting",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2)
        )

        assert event.id is not None
        assert event.title == "Team Meeting"
        assert event.sync_status == CalendarSyncStatus.SYNCED

    def test_event_requires_title(self):
        """Test that event title is required"""
        with pytest.raises(ValueError, match="Event title is required"):
            CalendarEvent(
                provider_id=uuid4(),
                user_id=uuid4(),
                title="",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=1)
            )

    def test_event_end_before_start_validation(self):
        """Test that end time cannot be before start time"""
        with pytest.raises(ValueError, match="End time cannot be before start time"):
            CalendarEvent(
                provider_id=uuid4(),
                user_id=uuid4(),
                title="Test Event",
                start_time=datetime.now() + timedelta(hours=2),
                end_time=datetime.now() + timedelta(hours=1)
            )

    def test_event_get_duration_minutes(self):
        """Test calculating event duration"""
        event = CalendarEvent(
            provider_id=uuid4(),
            user_id=uuid4(),
            title="Test Event",
            start_time=datetime(2025, 10, 15, 10, 0),
            end_time=datetime(2025, 10, 15, 11, 30)
        )

        assert event.get_duration_minutes() == 90

    def test_event_is_upcoming(self):
        """Test checking if event is upcoming"""
        event = CalendarEvent(
            provider_id=uuid4(),
            user_id=uuid4(),
            title="Test Event",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2)
        )

        assert event.is_upcoming()

        event.start_time = datetime.now() - timedelta(hours=1)
        event.end_time = datetime.now() + timedelta(hours=1)
        assert not event.is_upcoming()

    def test_event_is_in_progress(self):
        """Test checking if event is in progress"""
        event = CalendarEvent(
            provider_id=uuid4(),
            user_id=uuid4(),
            title="Test Event",
            start_time=datetime.now() - timedelta(minutes=30),
            end_time=datetime.now() + timedelta(minutes=30)
        )

        assert event.is_in_progress()

    def test_event_needs_reminder(self):
        """Test reminder check"""
        event = CalendarEvent(
            provider_id=uuid4(),
            user_id=uuid4(),
            title="Test Event",
            start_time=datetime.now() + timedelta(minutes=15),
            end_time=datetime.now() + timedelta(hours=1)
        )

        assert event.needs_reminder(minutes_before=30)

        event.reminder_sent = True
        assert not event.needs_reminder(minutes_before=30)

    def test_event_mark_reminder_sent(self):
        """Test marking reminder as sent"""
        event = CalendarEvent(
            provider_id=uuid4(),
            user_id=uuid4(),
            title="Test Event",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2)
        )

        assert not event.reminder_sent
        event.mark_reminder_sent()
        assert event.reminder_sent
        assert event.reminder_sent_at is not None


# ============================================================================
# SLACK ENTITY TESTS
# ============================================================================

class TestSlackWorkspace:
    """Test SlackWorkspace entity"""

    def test_workspace_creation(self):
        """Test creating a Slack workspace"""
        workspace = SlackWorkspace(
            organization_id=uuid4(),
            workspace_id="T12345678",
            bot_token="xoxb-test-token",
            workspace_name="Test Workspace"
        )

        assert workspace.id is not None
        assert workspace.workspace_id == "T12345678"
        assert workspace.is_active is True
        assert workspace.enable_notifications is True

    def test_workspace_requires_workspace_id(self):
        """Test that workspace ID is required"""
        with pytest.raises(ValueError, match="Workspace ID is required"):
            SlackWorkspace(
                organization_id=uuid4(),
                workspace_id="",
                bot_token="test-token"
            )

    def test_workspace_requires_bot_token(self):
        """Test that bot token is required"""
        with pytest.raises(ValueError, match="Bot token is required"):
            SlackWorkspace(
                organization_id=uuid4(),
                workspace_id="T12345678",
                bot_token=""
            )

    def test_workspace_record_activity(self):
        """Test recording activity timestamp"""
        workspace = SlackWorkspace(
            organization_id=uuid4(),
            workspace_id="T12345678",
            bot_token="test-token"
        )

        assert workspace.last_activity_at is None
        workspace.record_activity()
        assert workspace.last_activity_at is not None

    def test_workspace_has_scope(self):
        """Test checking workspace scopes"""
        workspace = SlackWorkspace(
            organization_id=uuid4(),
            workspace_id="T12345678",
            bot_token="test-token",
            scopes=["chat:write", "channels:read", "users:read"]
        )

        assert workspace.has_scope("chat:write")
        assert workspace.has_scope("channels:read")
        assert not workspace.has_scope("files:write")


class TestSlackChannelMapping:
    """Test SlackChannelMapping entity"""

    def test_channel_mapping_creation(self):
        """Test creating a channel mapping"""
        mapping = SlackChannelMapping(
            workspace_id=uuid4(),
            channel_id="C12345678",
            entity_type="course",
            entity_id=uuid4(),
            channel_name="intro-to-python"
        )

        assert mapping.id is not None
        assert mapping.channel_id == "C12345678"
        assert mapping.is_active is True
        assert mapping.notify_announcements is True

    def test_channel_mapping_requires_channel_id(self):
        """Test that channel ID is required"""
        with pytest.raises(ValueError, match="Channel ID is required"):
            SlackChannelMapping(
                workspace_id=uuid4(),
                channel_id="",
                entity_type="course",
                entity_id=uuid4()
            )

    def test_channel_mapping_requires_entity_type(self):
        """Test that entity type is required"""
        with pytest.raises(ValueError, match="Entity type is required"):
            SlackChannelMapping(
                workspace_id=uuid4(),
                channel_id="C12345678",
                entity_type="",
                entity_id=uuid4()
            )

    def test_channel_mapping_should_notify(self):
        """Test notification routing logic"""
        mapping = SlackChannelMapping(
            workspace_id=uuid4(),
            channel_id="C12345678",
            entity_type="course",
            entity_id=uuid4(),
            notify_announcements=True,
            notify_deadlines=True,
            notify_grades=False
        )

        assert mapping.should_notify(SlackMessageType.ANNOUNCEMENT)
        assert mapping.should_notify(SlackMessageType.DEADLINE_REMINDER)
        assert not mapping.should_notify(SlackMessageType.GRADE_NOTIFICATION)
        assert mapping.should_notify(SlackMessageType.SYSTEM_ALERT)  # Always true

        mapping.is_active = False
        assert not mapping.should_notify(SlackMessageType.ANNOUNCEMENT)

    def test_channel_mapping_record_message(self):
        """Test recording message timestamp"""
        mapping = SlackChannelMapping(
            workspace_id=uuid4(),
            channel_id="C12345678",
            entity_type="course",
            entity_id=uuid4()
        )

        assert mapping.last_message_at is None
        mapping.record_message()
        assert mapping.last_message_at is not None


class TestSlackUserMapping:
    """Test SlackUserMapping entity"""

    def test_user_mapping_creation(self):
        """Test creating a Slack user mapping"""
        mapping = SlackUserMapping(
            workspace_id=uuid4(),
            user_id=uuid4(),
            slack_user_id="U12345678",
            slack_username="johndoe",
            slack_email="john@example.com"
        )

        assert mapping.id is not None
        assert mapping.slack_user_id == "U12345678"
        assert mapping.dm_notifications_enabled is True

    def test_user_mapping_requires_slack_user_id(self):
        """Test that Slack user ID is required"""
        with pytest.raises(ValueError, match="Slack user ID is required"):
            SlackUserMapping(
                workspace_id=uuid4(),
                user_id=uuid4(),
                slack_user_id=""
            )

    def test_user_mapping_can_dm(self):
        """Test DM permission check"""
        mapping = SlackUserMapping(
            workspace_id=uuid4(),
            user_id=uuid4(),
            slack_user_id="U12345678",
            dm_notifications_enabled=True,
            is_active=True
        )

        assert mapping.can_dm()

        mapping.dm_notifications_enabled = False
        assert not mapping.can_dm()

        mapping.dm_notifications_enabled = True
        mapping.is_active = False
        assert not mapping.can_dm()

    def test_user_mapping_record_dm(self):
        """Test recording DM timestamp"""
        mapping = SlackUserMapping(
            workspace_id=uuid4(),
            user_id=uuid4(),
            slack_user_id="U12345678"
        )

        assert mapping.last_dm_at is None
        mapping.record_dm()
        assert mapping.last_dm_at is not None


class TestSlackMessage:
    """Test SlackMessage entity"""

    def test_message_creation(self):
        """Test creating a Slack message"""
        message = SlackMessage(
            workspace_id=uuid4(),
            message_type=SlackMessageType.ANNOUNCEMENT,
            message_text="Hello everyone!"
        )

        assert message.id is not None
        assert message.message_text == "Hello everyone!"
        assert message.delivery_status == "sent"

    def test_message_requires_text(self):
        """Test that message text is required"""
        with pytest.raises(ValueError, match="Message text is required"):
            SlackMessage(
                workspace_id=uuid4(),
                message_type=SlackMessageType.ANNOUNCEMENT,
                message_text=""
            )

    def test_message_mark_delivered(self):
        """Test marking message as delivered"""
        message = SlackMessage(
            workspace_id=uuid4(),
            message_type=SlackMessageType.ANNOUNCEMENT,
            message_text="Hello!"
        )

        message.mark_delivered("1234567890.123456")
        assert message.delivery_status == "delivered"
        assert message.slack_message_ts == "1234567890.123456"

    def test_message_mark_failed(self):
        """Test marking message as failed"""
        message = SlackMessage(
            workspace_id=uuid4(),
            message_type=SlackMessageType.ANNOUNCEMENT,
            message_text="Hello!"
        )

        message.mark_failed("Channel not found")
        assert message.delivery_status == "failed"
        assert message.error_message == "Channel not found"


# ============================================================================
# WEBHOOK ENTITY TESTS
# ============================================================================

class TestOutboundWebhook:
    """Test OutboundWebhook entity"""

    def test_webhook_creation(self):
        """Test creating an outbound webhook"""
        webhook = OutboundWebhook(
            organization_id=uuid4(),
            name="Course Events Webhook",
            target_url="https://api.example.com/webhooks",
            event_types=["course.created", "course.published"]
        )

        assert webhook.id is not None
        assert webhook.name == "Course Events Webhook"
        assert webhook.is_active is True
        assert webhook.success_count == 0

    def test_webhook_requires_name(self):
        """Test that webhook name is required"""
        with pytest.raises(ValueError, match="Webhook name is required"):
            OutboundWebhook(
                organization_id=uuid4(),
                name="",
                target_url="https://example.com"
            )

    def test_webhook_requires_target_url(self):
        """Test that target URL is required"""
        with pytest.raises(ValueError, match="Target URL is required"):
            OutboundWebhook(
                organization_id=uuid4(),
                name="Test Webhook",
                target_url=""
            )

    def test_webhook_retry_validation(self):
        """Test retry count validation"""
        with pytest.raises(ValueError, match="Retry count must be non-negative"):
            OutboundWebhook(
                organization_id=uuid4(),
                name="Test Webhook",
                target_url="https://example.com",
                retry_count=-1
            )

    def test_webhook_timeout_validation(self):
        """Test timeout validation"""
        with pytest.raises(ValueError, match="Timeout must be at least 1 second"):
            OutboundWebhook(
                organization_id=uuid4(),
                name="Test Webhook",
                target_url="https://example.com",
                timeout_seconds=0
            )

    def test_webhook_should_trigger(self):
        """Test trigger logic"""
        webhook = OutboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            target_url="https://example.com",
            event_types=["course.created", "course.published"],
            is_active=True
        )

        assert webhook.should_trigger("course.created")
        assert webhook.should_trigger("course.published")
        assert not webhook.should_trigger("user.registered")

        webhook.is_active = False
        assert not webhook.should_trigger("course.created")

    def test_webhook_no_event_filter_triggers_all(self):
        """Test that empty event filter triggers all events"""
        webhook = OutboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            target_url="https://example.com",
            event_types=[],
            is_active=True
        )

        assert webhook.should_trigger("any.event")
        assert webhook.should_trigger("course.created")

    def test_webhook_record_success(self):
        """Test recording successful delivery"""
        webhook = OutboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            target_url="https://example.com"
        )

        webhook.record_success()
        assert webhook.success_count == 1
        assert webhook.last_triggered_at is not None

    def test_webhook_record_failure(self):
        """Test recording failed delivery"""
        webhook = OutboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            target_url="https://example.com"
        )

        webhook.record_failure()
        assert webhook.failure_count == 1
        assert webhook.last_triggered_at is not None

    def test_webhook_get_success_rate(self):
        """Test calculating success rate"""
        webhook = OutboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            target_url="https://example.com"
        )

        assert webhook.get_success_rate() is None  # No deliveries

        webhook.success_count = 8
        webhook.failure_count = 2
        assert webhook.get_success_rate() == Decimal("80.00")


class TestWebhookDeliveryLog:
    """Test WebhookDeliveryLog entity"""

    def test_delivery_log_creation(self):
        """Test creating a delivery log"""
        log = WebhookDeliveryLog(
            webhook_id=uuid4(),
            event_type="course.created",
            event_id=uuid4(),
            payload={"course_id": "123", "title": "Test Course"}
        )

        assert log.id is not None
        assert log.delivery_status == WebhookDeliveryStatus.PENDING
        assert log.attempt_number == 1

    def test_delivery_log_mark_success(self):
        """Test marking delivery as successful"""
        log = WebhookDeliveryLog(
            webhook_id=uuid4(),
            event_type="course.created",
            event_id=uuid4(),
            payload={}
        )

        log.mark_success(200, '{"status": "ok"}')
        assert log.delivery_status == WebhookDeliveryStatus.SUCCESS
        assert log.response_status_code == 200
        assert log.response_body == '{"status": "ok"}'
        assert log.response_timestamp is not None

    def test_delivery_log_mark_failed(self):
        """Test marking delivery as failed"""
        log = WebhookDeliveryLog(
            webhook_id=uuid4(),
            event_type="course.created",
            event_id=uuid4(),
            payload={}
        )

        log.mark_failed("Connection timeout", 504)
        assert log.delivery_status == WebhookDeliveryStatus.FAILED
        assert log.error_message == "Connection timeout"
        assert log.response_status_code == 504

    def test_delivery_log_schedule_retry(self):
        """Test scheduling retry"""
        log = WebhookDeliveryLog(
            webhook_id=uuid4(),
            event_type="course.created",
            event_id=uuid4(),
            payload={}
        )

        log.schedule_retry(60)
        assert log.delivery_status == WebhookDeliveryStatus.RETRY_SCHEDULED
        assert log.next_retry_at is not None

    def test_delivery_log_get_response_time(self):
        """Test calculating response time"""
        log = WebhookDeliveryLog(
            webhook_id=uuid4(),
            event_type="course.created",
            event_id=uuid4(),
            payload={}
        )

        assert log.get_response_time_ms() is None

        log.response_timestamp = log.request_timestamp + timedelta(milliseconds=250)
        assert log.get_response_time_ms() == 250


class TestInboundWebhook:
    """Test InboundWebhook entity"""

    def test_inbound_webhook_creation(self):
        """Test creating an inbound webhook"""
        webhook = InboundWebhook(
            organization_id=uuid4(),
            name="GitHub Webhook",
            webhook_token="abc123xyz",
            handler_type=WebhookHandlerType.GITHUB
        )

        assert webhook.id is not None
        assert webhook.name == "GitHub Webhook"
        assert webhook.is_active is True
        assert webhook.total_received == 0

    def test_inbound_webhook_requires_name(self):
        """Test that webhook name is required"""
        with pytest.raises(ValueError, match="Webhook name is required"):
            InboundWebhook(
                organization_id=uuid4(),
                name="",
                webhook_token="test-token",
                handler_type=WebhookHandlerType.GITHUB
            )

    def test_inbound_webhook_requires_token(self):
        """Test that webhook token is required"""
        with pytest.raises(ValueError, match="Webhook token is required"):
            InboundWebhook(
                organization_id=uuid4(),
                name="Test Webhook",
                webhook_token="",
                handler_type=WebhookHandlerType.GITHUB
            )

    def test_inbound_webhook_is_ip_allowed(self):
        """Test IP whitelist checking"""
        webhook = InboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            webhook_token="test-token",
            handler_type=WebhookHandlerType.GITHUB,
            allowed_ips=["192.168.1.1", "10.0.0.1"]
        )

        assert webhook.is_ip_allowed("192.168.1.1")
        assert webhook.is_ip_allowed("10.0.0.1")
        assert not webhook.is_ip_allowed("192.168.1.2")

        webhook.allowed_ips = []
        assert webhook.is_ip_allowed("any.ip.address.here")

    def test_inbound_webhook_record_received(self):
        """Test recording webhook receipt"""
        webhook = InboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            webhook_token="test-token",
            handler_type=WebhookHandlerType.GITHUB
        )

        webhook.record_received()
        assert webhook.total_received == 1
        assert webhook.last_received_at is not None

    def test_inbound_webhook_record_processed(self):
        """Test recording successful processing"""
        webhook = InboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            webhook_token="test-token",
            handler_type=WebhookHandlerType.GITHUB
        )

        webhook.record_processed()
        assert webhook.total_processed == 1

    def test_inbound_webhook_record_failed(self):
        """Test recording failed processing"""
        webhook = InboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            webhook_token="test-token",
            handler_type=WebhookHandlerType.GITHUB
        )

        webhook.record_failed()
        assert webhook.total_failed == 1

    def test_inbound_webhook_get_success_rate(self):
        """Test calculating success rate"""
        webhook = InboundWebhook(
            organization_id=uuid4(),
            name="Test Webhook",
            webhook_token="test-token",
            handler_type=WebhookHandlerType.GITHUB
        )

        assert webhook.get_success_rate() is None

        webhook.total_received = 10
        webhook.total_processed = 9
        assert webhook.get_success_rate() == Decimal("90.00")


# ============================================================================
# OAUTH TOKEN ENTITY TESTS
# ============================================================================

class TestOAuthToken:
    """Test OAuthToken entity"""

    def test_token_creation_with_user(self):
        """Test creating an OAuth token for a user"""
        token = OAuthToken(
            provider=OAuthProvider.GOOGLE,
            access_token="access-token-123",
            user_id=uuid4(),
            refresh_token="refresh-token-456"
        )

        assert token.id is not None
        assert token.provider == OAuthProvider.GOOGLE
        assert token.is_valid is True

    def test_token_creation_with_organization(self):
        """Test creating an OAuth token for an organization"""
        token = OAuthToken(
            provider=OAuthProvider.SLACK,
            access_token="xoxp-token-123",
            organization_id=uuid4()
        )

        assert token.id is not None
        assert token.provider == OAuthProvider.SLACK

    def test_token_requires_access_token(self):
        """Test that access token is required"""
        with pytest.raises(ValueError, match="Access token is required"):
            OAuthToken(
                provider=OAuthProvider.GOOGLE,
                access_token="",
                user_id=uuid4()
            )

    def test_token_requires_owner(self):
        """Test that either user_id or organization_id is required"""
        with pytest.raises(ValueError, match="Either user_id or organization_id is required"):
            OAuthToken(
                provider=OAuthProvider.GOOGLE,
                access_token="test-token"
            )

    def test_token_is_expired(self):
        """Test token expiration check"""
        token = OAuthToken(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
            user_id=uuid4(),
            expires_at=datetime.now() + timedelta(hours=1)
        )

        assert not token.is_expired()

        token.expires_at = datetime.now() - timedelta(hours=1)
        assert token.is_expired()

        token.expires_at = None
        assert not token.is_expired()  # No expiration = not expired

    def test_token_can_refresh(self):
        """Test refresh capability check"""
        token = OAuthToken(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
            user_id=uuid4(),
            refresh_token="refresh-token"
        )

        assert token.can_refresh()

        token.refresh_token = None
        assert not token.can_refresh()

        token.refresh_token = "refresh-token"
        token.refresh_expires_at = datetime.now() - timedelta(days=1)
        assert not token.can_refresh()

    def test_token_needs_refresh(self):
        """Test refresh timing check"""
        token = OAuthToken(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
            user_id=uuid4(),
            expires_at=datetime.now() + timedelta(hours=1)
        )

        assert not token.needs_refresh()

        token.expires_at = datetime.now() + timedelta(minutes=3)
        assert token.needs_refresh()

        token.expires_at = None
        assert not token.needs_refresh()

    def test_token_mark_used(self):
        """Test marking token as used"""
        token = OAuthToken(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
            user_id=uuid4()
        )
        token.consecutive_failures = 2
        token.last_error = "Previous error"

        token.mark_used()
        assert token.last_used_at is not None
        assert token.consecutive_failures == 0
        assert token.last_error is None

    def test_token_mark_refreshed(self):
        """Test updating token after refresh"""
        token = OAuthToken(
            provider=OAuthProvider.GOOGLE,
            access_token="old-token",
            user_id=uuid4()
        )

        new_expires = datetime.now() + timedelta(hours=1)
        token.mark_refreshed("new-token", new_expires)

        assert token.access_token == "new-token"
        assert token.expires_at == new_expires
        assert token.last_refreshed_at is not None
        assert token.consecutive_failures == 0

    def test_token_mark_failed(self):
        """Test recording token failure"""
        token = OAuthToken(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
            user_id=uuid4()
        )

        token.mark_failed("Invalid token")
        assert token.consecutive_failures == 1
        assert token.last_error == "Invalid token"
        assert token.is_valid is True

        token.mark_failed("Invalid token")
        token.mark_failed("Invalid token")
        assert token.consecutive_failures == 3
        assert token.is_valid is False  # Invalidated after 3 failures

    def test_token_invalidate(self):
        """Test token invalidation"""
        token = OAuthToken(
            provider=OAuthProvider.GOOGLE,
            access_token="test-token",
            user_id=uuid4()
        )

        assert token.is_valid is True
        token.invalidate()
        assert token.is_valid is False


# ============================================================================
# INTEGRATION SCENARIO TESTS
# ============================================================================

class TestLTIIntegrationScenario:
    """Test complete LTI integration scenarios"""

    def test_lti_launch_flow(self):
        """Test complete LTI launch flow"""
        # Step 1: Platform registration
        platform = LTIPlatformRegistration(
            organization_id=uuid4(),
            platform_name="Canvas LMS",
            issuer="https://canvas.instructure.com",
            client_id="test-client",
            auth_login_url="https://canvas.instructure.com/auth",
            auth_token_url="https://canvas.instructure.com/token",
            jwks_url="https://canvas.instructure.com/jwks",
            scopes=[LTIScope.NAMES_ROLE_SERVICE.value, LTIScope.ASSIGNMENT_GRADE_SERVICE_SCORE.value]
        )

        # Step 2: Context creation
        context = LTIContext(
            platform_id=platform.id,
            lti_context_id="course-python-101",
            lti_context_type=LTIContextType.COURSE_SECTION.value,
            lti_context_title="Python 101"
        )

        # Step 3: User mapping
        user_mapping = LTIUserMapping(
            platform_id=platform.id,
            user_id=uuid4(),
            lti_user_id="lti-user-12345",
            lti_email="student@university.edu",
            lti_name="Alice Student",
            lti_roles=[LTIRole.LEARNER.value]
        )

        # Verify the flow
        assert platform.has_scope(LTIScope.ASSIGNMENT_GRADE_SERVICE_SCORE)
        assert not context.is_linked()
        assert user_mapping.is_learner()
        assert not user_mapping.is_instructor()

        # Link context to course
        context.course_id = uuid4()
        assert context.is_linked()

        # Record login
        user_mapping.record_login()
        assert user_mapping.login_count == 1

        # Create grade sync
        grade_sync = LTIGradeSync(
            context_id=context.id,
            user_mapping_id=user_mapping.id,
            score=Decimal("92.5"),
            max_score=Decimal("100")
        )

        assert grade_sync.get_score_percentage() == Decimal("92.50")
        assert grade_sync.sync_status == GradeSyncStatus.PENDING


class TestSlackIntegrationScenario:
    """Test complete Slack integration scenarios"""

    def test_slack_notification_flow(self):
        """Test complete Slack notification flow"""
        # Step 1: Workspace setup
        workspace = SlackWorkspace(
            organization_id=uuid4(),
            workspace_id="T12345678",
            bot_token="xoxb-test-token",
            workspace_name="Education Platform",
            scopes=["chat:write", "channels:read"]
        )

        # Step 2: Channel mapping
        course_id = uuid4()
        channel_mapping = SlackChannelMapping(
            workspace_id=workspace.id,
            channel_id="C12345678",
            channel_name="python-101",
            entity_type="course",
            entity_id=course_id,
            notify_announcements=True,
            notify_grades=True
        )

        # Step 3: User mapping
        user_mapping = SlackUserMapping(
            workspace_id=workspace.id,
            user_id=uuid4(),
            slack_user_id="U12345678",
            slack_username="alice",
            dm_notifications_enabled=True
        )

        # Verify notification routing
        assert channel_mapping.should_notify(SlackMessageType.ANNOUNCEMENT)
        assert channel_mapping.should_notify(SlackMessageType.GRADE_NOTIFICATION)
        assert user_mapping.can_dm()

        # Create message
        message = SlackMessage(
            workspace_id=workspace.id,
            message_type=SlackMessageType.ANNOUNCEMENT,
            message_text="New assignment posted!",
            channel_mapping_id=channel_mapping.id
        )

        message.mark_delivered("1234567890.123456")
        assert message.delivery_status == "delivered"


class TestWebhookIntegrationScenario:
    """Test complete webhook integration scenarios"""

    def test_outbound_webhook_delivery_flow(self):
        """Test complete outbound webhook delivery flow"""
        # Step 1: Create webhook
        webhook = OutboundWebhook(
            organization_id=uuid4(),
            name="LMS Integration",
            target_url="https://lms.example.com/webhooks",
            event_types=["course.published", "enrollment.created"],
            auth_type=WebhookAuthType.HMAC,
            auth_secret="secret-key-123"
        )

        # Step 2: Check if event should trigger
        assert webhook.should_trigger("course.published")
        assert not webhook.should_trigger("user.created")

        # Step 3: Create delivery log
        event_id = uuid4()
        delivery_log = WebhookDeliveryLog(
            webhook_id=webhook.id,
            event_type="course.published",
            event_id=event_id,
            payload={"course_id": str(uuid4()), "title": "New Course"}
        )

        # Step 4: Simulate successful delivery
        delivery_log.mark_success(200, '{"received": true}')
        webhook.record_success()

        assert delivery_log.delivery_status == WebhookDeliveryStatus.SUCCESS
        assert webhook.success_count == 1

    def test_inbound_webhook_processing_flow(self):
        """Test complete inbound webhook processing flow"""
        # Step 1: Create inbound webhook
        webhook = InboundWebhook(
            organization_id=uuid4(),
            name="Stripe Payments",
            webhook_token="whsec_test123",
            handler_type=WebhookHandlerType.STRIPE,
            auth_type=WebhookAuthType.HMAC,
            allowed_ips=["54.187.174.169", "54.187.205.235"]
        )

        # Step 2: Verify IP
        assert webhook.is_ip_allowed("54.187.174.169")
        assert not webhook.is_ip_allowed("192.168.1.1")

        # Step 3: Record receipt
        webhook.record_received()
        assert webhook.total_received == 1

        # Step 4: Record processing
        webhook.record_processed()
        assert webhook.total_processed == 1
        assert webhook.get_success_rate() == Decimal("100.00")
