"""
Integration Domain Entities

What: Domain entities for external integrations (LTI, Calendar, Slack, Webhooks).
Where: Organization Management service domain layer.
Why: Provides:
     1. LTI 1.3 platform and context management
     2. Calendar provider synchronization
     3. Slack workspace and channel integration
     4. Webhook management for external events
     5. OAuth token handling
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


# ============================================================================
# ENUMS
# ============================================================================

class LTIVersion(str, Enum):
    """
    What: LTI version types.
    Where: Platform registration.
    Why: Supports different LTI specifications.
    """
    LTI_1_1 = "1.1"
    LTI_1_3 = "1.3"


class LTIScope(str, Enum):
    """
    What: LTI OAuth scopes.
    Where: Platform capability configuration.
    Why: Defines allowed operations.
    """
    NAMES_ROLE_SERVICE = "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
    ASSIGNMENT_GRADE_SERVICE_LINEITEM = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"
    ASSIGNMENT_GRADE_SERVICE_SCORE = "https://purl.imsglobal.org/spec/lti-ags/scope/score"
    ASSIGNMENT_GRADE_SERVICE_RESULT = "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
    DEEP_LINKING = "https://purl.imsglobal.org/spec/lti-dl/scope/deep-linking"


class LTIContextType(str, Enum):
    """
    What: LTI context types.
    Where: Context classification.
    Why: Identifies context level.
    """
    COURSE_TEMPLATE = "CourseTemplate"
    COURSE_OFFERING = "CourseOffering"
    COURSE_SECTION = "CourseSection"
    GROUP = "Group"


class LTIRole(str, Enum):
    """
    What: Standard LTI roles.
    Where: User role mapping.
    Why: Maps LTI roles to system roles.
    """
    ADMINISTRATOR = "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator"
    INSTRUCTOR = "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"
    LEARNER = "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
    MENTOR = "http://purl.imsglobal.org/vocab/lis/v2/membership#Mentor"
    CONTENT_DEVELOPER = "http://purl.imsglobal.org/vocab/lis/v2/membership#ContentDeveloper"


class GradeSyncStatus(str, Enum):
    """
    What: Grade synchronization status.
    Where: LTI grade passback.
    Why: Tracks grade delivery.
    """
    PENDING = "pending"
    SENT = "sent"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    RETRY_SCHEDULED = "retry_scheduled"


class CalendarProviderType(str, Enum):
    """
    What: Supported calendar providers.
    Where: Calendar integration.
    Why: Identifies calendar service.
    """
    GOOGLE = "google"
    OUTLOOK = "outlook"
    APPLE = "apple"
    CALDAV = "caldav"


class SyncDirection(str, Enum):
    """
    What: Calendar sync direction.
    Where: Sync configuration.
    Why: Controls data flow.
    """
    BIDIRECTIONAL = "bidirectional"
    PUSH_ONLY = "push_only"
    PULL_ONLY = "pull_only"


class CalendarEventType(str, Enum):
    """
    What: Calendar event types.
    Where: Event categorization.
    Why: Identifies event source.
    """
    DEADLINE = "deadline"
    CLASS_SESSION = "class_session"
    QUIZ = "quiz"
    LAB = "lab"
    OFFICE_HOURS = "office_hours"
    ASSIGNMENT = "assignment"
    EXAM = "exam"


class CalendarSyncStatus(str, Enum):
    """
    What: Calendar event sync status.
    Where: Sync tracking.
    Why: Monitors sync state.
    """
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"


class SlackChannelType(str, Enum):
    """
    What: Slack channel types.
    Where: Channel configuration.
    Why: Identifies channel privacy.
    """
    PUBLIC = "channel"
    PRIVATE = "private"
    DIRECT_MESSAGE = "dm"


class SlackMessageType(str, Enum):
    """
    What: Slack message types.
    Where: Message categorization.
    Why: Identifies message purpose.
    """
    ANNOUNCEMENT = "announcement"
    DEADLINE_REMINDER = "deadline_reminder"
    GRADE_NOTIFICATION = "grade_notification"
    NEW_CONTENT = "new_content"
    DISCUSSION_REPLY = "discussion_reply"
    SYSTEM_ALERT = "system_alert"


class WebhookAuthType(str, Enum):
    """
    What: Webhook authentication types.
    Where: Webhook security.
    Why: Specifies auth method.
    """
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    HMAC = "hmac"
    API_KEY = "api_key"


class WebhookDeliveryStatus(str, Enum):
    """
    What: Webhook delivery status.
    Where: Delivery tracking.
    Why: Monitors delivery state.
    """
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY_SCHEDULED = "retry_scheduled"


class WebhookHandlerType(str, Enum):
    """
    What: Inbound webhook handler types.
    Where: Webhook processing.
    Why: Identifies handler logic.
    """
    GITHUB = "github"
    STRIPE = "stripe"
    ZAPIER = "zapier"
    CUSTOM = "custom"
    LMS_WEBHOOK = "lms_webhook"


class OAuthProvider(str, Enum):
    """
    What: OAuth provider types.
    Where: Token management.
    Why: Identifies auth provider.
    """
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    SLACK = "slack"
    GITHUB = "github"
    ZOOM = "zoom"


# ============================================================================
# LTI ENTITIES
# ============================================================================

@dataclass
class LTIPlatformRegistration:
    """
    What: LTI 1.3 platform registration.
    Where: External LMS connection.
    Why: Enables LTI tool integration.
    """
    organization_id: UUID
    platform_name: str
    issuer: str
    client_id: str
    auth_login_url: str
    auth_token_url: str
    jwks_url: str

    deployment_id: Optional[str] = None
    tool_public_key: Optional[str] = None
    tool_private_key: Optional[str] = None  # Encrypted
    platform_public_keys: list[dict[str, Any]] = field(default_factory=list)

    scopes: list[str] = field(default_factory=list)
    deep_linking_enabled: bool = True
    names_role_service_enabled: bool = True
    assignment_grade_service_enabled: bool = True

    is_active: bool = True
    verified_at: Optional[datetime] = None
    last_connection_at: Optional[datetime] = None

    created_by: Optional[UUID] = None
    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate platform registration data."""
        if not self.platform_name:
            raise ValueError("Platform name is required")
        if not self.issuer:
            raise ValueError("Issuer URL is required")
        if not self.client_id:
            raise ValueError("Client ID is required")
        if not self.auth_login_url:
            raise ValueError("Auth login URL is required")
        if not self.auth_token_url:
            raise ValueError("Auth token URL is required")
        if not self.jwks_url:
            raise ValueError("JWKS URL is required")

    def has_scope(self, scope: LTIScope) -> bool:
        """Check if platform has a specific scope."""
        return scope.value in self.scopes

    def mark_connected(self) -> None:
        """Mark platform as connected."""
        self.last_connection_at = datetime.now()

    def verify(self) -> None:
        """Mark platform as verified."""
        self.verified_at = datetime.now()

    def is_verified(self) -> bool:
        """Check if platform is verified."""
        return self.verified_at is not None


@dataclass
class LTIContext:
    """
    What: LTI context mapping.
    Where: Course linking.
    Why: Connects external courses to internal courses.
    """
    platform_id: UUID
    lti_context_id: str

    lti_context_type: Optional[str] = None
    lti_context_title: Optional[str] = None
    lti_context_label: Optional[str] = None

    course_id: Optional[UUID] = None
    course_instance_id: Optional[UUID] = None

    resource_link_id: Optional[str] = None
    resource_link_title: Optional[str] = None

    last_roster_sync: Optional[datetime] = None
    auto_roster_sync: bool = False
    roster_sync_interval_hours: int = 24

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate context data."""
        if not self.lti_context_id:
            raise ValueError("LTI context ID is required")
        if self.roster_sync_interval_hours < 1:
            raise ValueError("Roster sync interval must be at least 1 hour")

    def is_linked(self) -> bool:
        """Check if context is linked to a course."""
        return self.course_id is not None or self.course_instance_id is not None

    def needs_roster_sync(self) -> bool:
        """Check if roster sync is needed."""
        if not self.auto_roster_sync:
            return False
        if not self.last_roster_sync:
            return True
        delta = datetime.now() - self.last_roster_sync
        return delta.total_seconds() > (self.roster_sync_interval_hours * 3600)

    def mark_roster_synced(self) -> None:
        """Mark roster as synced."""
        self.last_roster_sync = datetime.now()


@dataclass
class LTIUserMapping:
    """
    What: LTI user mapping.
    Where: User identity linking.
    Why: Maps external LMS users to internal users.
    """
    platform_id: UUID
    user_id: UUID
    lti_user_id: str

    lti_email: Optional[str] = None
    lti_name: Optional[str] = None
    lti_given_name: Optional[str] = None
    lti_family_name: Optional[str] = None
    lti_picture_url: Optional[str] = None

    lti_roles: list[str] = field(default_factory=list)
    mapped_role_name: Optional[str] = None

    is_active: bool = True
    last_login_at: Optional[datetime] = None
    login_count: int = 0

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate user mapping data."""
        if not self.lti_user_id:
            raise ValueError("LTI user ID is required")

    def record_login(self) -> None:
        """Record a login event."""
        self.last_login_at = datetime.now()
        self.login_count += 1

    def has_role(self, role: LTIRole) -> bool:
        """Check if user has a specific LTI role."""
        return role.value in self.lti_roles

    def is_instructor(self) -> bool:
        """Check if user is an instructor."""
        return self.has_role(LTIRole.INSTRUCTOR)

    def is_learner(self) -> bool:
        """Check if user is a learner."""
        return self.has_role(LTIRole.LEARNER)


@dataclass
class LTIGradeSync:
    """
    What: LTI grade synchronization record.
    Where: Grade passback tracking.
    Why: Tracks grade delivery to LMS.
    """
    context_id: UUID
    user_mapping_id: UUID

    lineitem_id: Optional[str] = None
    score: Optional[Decimal] = None
    max_score: Decimal = Decimal("100.00")
    comment: Optional[str] = None

    quiz_attempt_id: Optional[UUID] = None
    assignment_id: Optional[UUID] = None

    sync_status: GradeSyncStatus = GradeSyncStatus.PENDING
    last_sync_attempt: Optional[datetime] = None
    last_sync_success: Optional[datetime] = None
    sync_error_message: Optional[str] = None
    retry_count: int = 0

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate grade sync data."""
        if self.score is not None and self.score < 0:
            raise ValueError("Score cannot be negative")
        if self.max_score <= 0:
            raise ValueError("Max score must be positive")

    def get_score_percentage(self) -> Optional[Decimal]:
        """Calculate score as percentage."""
        if self.score is None:
            return None
        return round((self.score / self.max_score) * 100, 2)

    def mark_sent(self) -> None:
        """Mark grade as sent."""
        self.sync_status = GradeSyncStatus.SENT
        self.last_sync_attempt = datetime.now()

    def mark_confirmed(self) -> None:
        """Mark grade as confirmed."""
        self.sync_status = GradeSyncStatus.CONFIRMED
        self.last_sync_success = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark grade sync as failed."""
        self.sync_status = GradeSyncStatus.FAILED
        self.sync_error_message = error
        self.retry_count += 1
        self.last_sync_attempt = datetime.now()

    def can_retry(self, max_retries: int = 3) -> bool:
        """Check if sync can be retried."""
        return self.retry_count < max_retries


# ============================================================================
# CALENDAR ENTITIES
# ============================================================================

@dataclass
class CalendarProvider:
    """
    What: Calendar provider configuration.
    Where: User calendar integration.
    Why: Manages calendar sync settings.
    """
    user_id: UUID
    provider_type: CalendarProviderType

    provider_name: Optional[str] = None
    access_token: Optional[str] = None  # Encrypted
    refresh_token: Optional[str] = None  # Encrypted
    token_expires_at: Optional[datetime] = None

    calendar_id: Optional[str] = None
    calendar_name: Optional[str] = None
    calendar_timezone: Optional[str] = None

    sync_enabled: bool = True
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    sync_deadline_reminders: bool = True
    sync_class_schedules: bool = True
    sync_quiz_dates: bool = True
    reminder_minutes_before: int = 30

    is_connected: bool = False
    last_sync_at: Optional[datetime] = None
    last_sync_error: Optional[str] = None
    connection_error_count: int = 0

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate provider data."""
        if self.reminder_minutes_before < 0:
            raise ValueError("Reminder minutes must be non-negative")

    def is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.token_expires_at:
            return True
        return datetime.now() >= self.token_expires_at

    def needs_refresh(self) -> bool:
        """Check if token needs refresh (expires in < 5 mins)."""
        if not self.token_expires_at:
            return True
        return datetime.now() >= (self.token_expires_at - timedelta(minutes=5))

    def mark_connected(self) -> None:
        """Mark provider as connected."""
        self.is_connected = True
        self.connection_error_count = 0
        self.last_sync_error = None

    def mark_disconnected(self, error: Optional[str] = None) -> None:
        """Mark provider as disconnected."""
        self.is_connected = False
        self.last_sync_error = error
        if error:
            self.connection_error_count += 1

    def mark_synced(self) -> None:
        """Mark last sync time."""
        self.last_sync_at = datetime.now()


@dataclass
class CalendarEvent:
    """
    What: Synced calendar event.
    Where: Calendar synchronization.
    Why: Tracks events between platforms.
    """
    provider_id: UUID
    user_id: UUID
    title: str
    start_time: datetime
    end_time: datetime

    external_event_id: Optional[str] = None
    external_calendar_id: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None

    all_day: bool = False
    timezone: Optional[str] = None

    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    recurring_event_id: Optional[UUID] = None

    event_type: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None

    sync_status: CalendarSyncStatus = CalendarSyncStatus.SYNCED
    local_updated_at: Optional[datetime] = None
    remote_updated_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None

    reminder_sent: bool = False
    reminder_sent_at: Optional[datetime] = None

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate event data."""
        if not self.title:
            raise ValueError("Event title is required")
        if self.end_time < self.start_time:
            raise ValueError("End time cannot be before start time")

    def get_duration_minutes(self) -> int:
        """Get event duration in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    def is_upcoming(self) -> bool:
        """Check if event is upcoming."""
        return self.start_time > datetime.now()

    def is_in_progress(self) -> bool:
        """Check if event is currently in progress."""
        now = datetime.now()
        return self.start_time <= now <= self.end_time

    def needs_reminder(self, minutes_before: int = 30) -> bool:
        """Check if reminder should be sent."""
        if self.reminder_sent:
            return False
        reminder_time = self.start_time - timedelta(minutes=minutes_before)
        return datetime.now() >= reminder_time

    def mark_reminder_sent(self) -> None:
        """Mark reminder as sent."""
        self.reminder_sent = True
        self.reminder_sent_at = datetime.now()


# ============================================================================
# SLACK ENTITIES
# ============================================================================

@dataclass
class SlackWorkspace:
    """
    What: Slack workspace configuration.
    Where: Organization Slack integration.
    Why: Manages Slack connection settings.
    """
    organization_id: UUID
    workspace_id: str
    bot_token: str  # Encrypted

    workspace_name: Optional[str] = None
    workspace_domain: Optional[str] = None
    bot_user_id: Optional[str] = None
    app_id: Optional[str] = None

    scopes: list[str] = field(default_factory=list)

    default_announcements_channel: Optional[str] = None
    default_alerts_channel: Optional[str] = None

    enable_notifications: bool = True
    enable_commands: bool = True
    enable_ai_assistant: bool = False

    is_active: bool = True
    installed_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None

    installed_by: Optional[UUID] = None
    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate workspace data."""
        if not self.workspace_id:
            raise ValueError("Workspace ID is required")
        if not self.bot_token:
            raise ValueError("Bot token is required")

    def record_activity(self) -> None:
        """Record activity timestamp."""
        self.last_activity_at = datetime.now()

    def has_scope(self, scope: str) -> bool:
        """Check if workspace has a specific scope."""
        return scope in self.scopes


@dataclass
class SlackChannelMapping:
    """
    What: Slack channel to entity mapping.
    Where: Channel notification routing.
    Why: Links channels to courses/projects.
    """
    workspace_id: UUID
    channel_id: str
    entity_type: str
    entity_id: UUID

    channel_name: Optional[str] = None
    channel_type: SlackChannelType = SlackChannelType.PUBLIC

    notify_announcements: bool = True
    notify_deadlines: bool = True
    notify_grades: bool = True
    notify_new_content: bool = True
    notify_discussions: bool = True

    is_active: bool = True
    last_message_at: Optional[datetime] = None

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate channel mapping data."""
        if not self.channel_id:
            raise ValueError("Channel ID is required")
        if not self.entity_type:
            raise ValueError("Entity type is required")

    def should_notify(self, message_type: SlackMessageType) -> bool:
        """Check if notification should be sent for message type."""
        if not self.is_active:
            return False

        type_map = {
            SlackMessageType.ANNOUNCEMENT: self.notify_announcements,
            SlackMessageType.DEADLINE_REMINDER: self.notify_deadlines,
            SlackMessageType.GRADE_NOTIFICATION: self.notify_grades,
            SlackMessageType.NEW_CONTENT: self.notify_new_content,
            SlackMessageType.DISCUSSION_REPLY: self.notify_discussions,
            SlackMessageType.SYSTEM_ALERT: True,  # Always send system alerts
        }
        return type_map.get(message_type, False)

    def record_message(self) -> None:
        """Record message timestamp."""
        self.last_message_at = datetime.now()


@dataclass
class SlackUserMapping:
    """
    What: Slack user to platform user mapping.
    Where: User identity linking.
    Why: Enables personalized notifications.
    """
    workspace_id: UUID
    user_id: UUID
    slack_user_id: str

    slack_username: Optional[str] = None
    slack_email: Optional[str] = None
    slack_real_name: Optional[str] = None
    slack_display_name: Optional[str] = None

    dm_notifications_enabled: bool = True
    mention_notifications_enabled: bool = True
    daily_digest_enabled: bool = False
    digest_time: Optional[time] = None

    is_active: bool = True
    last_dm_at: Optional[datetime] = None

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate user mapping data."""
        if not self.slack_user_id:
            raise ValueError("Slack user ID is required")

    def can_dm(self) -> bool:
        """Check if DM can be sent to user."""
        return self.is_active and self.dm_notifications_enabled

    def record_dm(self) -> None:
        """Record DM timestamp."""
        self.last_dm_at = datetime.now()


@dataclass
class SlackMessage:
    """
    What: Slack message record.
    Where: Message history tracking.
    Why: Enables analytics and audit.
    """
    workspace_id: UUID
    message_type: SlackMessageType
    message_text: str

    channel_mapping_id: Optional[UUID] = None
    user_mapping_id: Optional[UUID] = None
    slack_message_ts: Optional[str] = None

    source_type: Optional[str] = None
    source_id: Optional[UUID] = None

    delivery_status: str = "sent"
    sent_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None

    reaction_count: int = 0
    reply_count: int = 0

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate message data."""
        if not self.message_text:
            raise ValueError("Message text is required")

    def mark_delivered(self, message_ts: str) -> None:
        """Mark message as delivered."""
        self.delivery_status = "delivered"
        self.slack_message_ts = message_ts

    def mark_failed(self, error: str) -> None:
        """Mark message as failed."""
        self.delivery_status = "failed"
        self.error_message = error


# ============================================================================
# WEBHOOK ENTITIES
# ============================================================================

@dataclass
class OutboundWebhook:
    """
    What: Outbound webhook configuration.
    Where: External service notifications.
    Why: Sends events to external services.
    """
    organization_id: UUID
    name: str
    target_url: str

    description: Optional[str] = None
    auth_type: WebhookAuthType = WebhookAuthType.NONE
    auth_secret: Optional[str] = None  # Encrypted

    event_types: list[str] = field(default_factory=list)
    filter_conditions: dict[str, Any] = field(default_factory=dict)

    retry_count: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 30

    is_active: bool = True
    last_triggered_at: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0

    created_by: Optional[UUID] = None
    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate webhook data."""
        if not self.name:
            raise ValueError("Webhook name is required")
        if not self.target_url:
            raise ValueError("Target URL is required")
        if self.retry_count < 0:
            raise ValueError("Retry count must be non-negative")
        if self.timeout_seconds < 1:
            raise ValueError("Timeout must be at least 1 second")

    def should_trigger(self, event_type: str) -> bool:
        """Check if webhook should trigger for event type."""
        if not self.is_active:
            return False
        if not self.event_types:
            return True  # No filter means all events
        return event_type in self.event_types

    def record_success(self) -> None:
        """Record successful delivery."""
        self.last_triggered_at = datetime.now()
        self.success_count += 1

    def record_failure(self) -> None:
        """Record failed delivery."""
        self.last_triggered_at = datetime.now()
        self.failure_count += 1

    def get_success_rate(self) -> Optional[Decimal]:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return None
        return round(Decimal(self.success_count) / Decimal(total) * 100, 2)


@dataclass
class WebhookDeliveryLog:
    """
    What: Webhook delivery attempt log.
    Where: Delivery tracking.
    Why: Records delivery attempts for debugging.
    """
    webhook_id: UUID
    event_type: str
    event_id: UUID
    payload: dict[str, Any]

    attempt_number: int = 1
    request_timestamp: datetime = field(default_factory=datetime.now)
    response_timestamp: Optional[datetime] = None

    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    response_headers: Optional[dict[str, str]] = None

    delivery_status: WebhookDeliveryStatus = WebhookDeliveryStatus.PENDING
    error_message: Optional[str] = None
    next_retry_at: Optional[datetime] = None

    id: UUID = field(default_factory=uuid4)

    def mark_success(self, status_code: int, body: Optional[str] = None) -> None:
        """Mark delivery as successful."""
        self.delivery_status = WebhookDeliveryStatus.SUCCESS
        self.response_timestamp = datetime.now()
        self.response_status_code = status_code
        self.response_body = body

    def mark_failed(self, error: str, status_code: Optional[int] = None) -> None:
        """Mark delivery as failed."""
        self.delivery_status = WebhookDeliveryStatus.FAILED
        self.response_timestamp = datetime.now()
        self.error_message = error
        self.response_status_code = status_code

    def schedule_retry(self, delay_seconds: int) -> None:
        """Schedule retry attempt."""
        self.delivery_status = WebhookDeliveryStatus.RETRY_SCHEDULED
        self.next_retry_at = datetime.now() + timedelta(seconds=delay_seconds)

    def get_response_time_ms(self) -> Optional[int]:
        """Calculate response time in milliseconds."""
        if not self.response_timestamp:
            return None
        delta = self.response_timestamp - self.request_timestamp
        return int(delta.total_seconds() * 1000)


@dataclass
class InboundWebhook:
    """
    What: Inbound webhook configuration.
    Where: External event reception.
    Why: Receives events from external services.
    """
    organization_id: UUID
    name: str
    webhook_token: str  # Used in URL path
    handler_type: WebhookHandlerType

    description: Optional[str] = None
    auth_type: WebhookAuthType = WebhookAuthType.API_KEY
    auth_secret: Optional[str] = None  # For HMAC verification
    allowed_ips: list[str] = field(default_factory=list)

    handler_config: dict[str, Any] = field(default_factory=dict)

    is_active: bool = True
    last_received_at: Optional[datetime] = None
    total_received: int = 0
    total_processed: int = 0
    total_failed: int = 0

    created_by: Optional[UUID] = None
    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate webhook data."""
        if not self.name:
            raise ValueError("Webhook name is required")
        if not self.webhook_token:
            raise ValueError("Webhook token is required")

    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed."""
        if not self.allowed_ips:
            return True  # No whitelist means all IPs allowed
        return ip in self.allowed_ips

    def record_received(self) -> None:
        """Record receipt of webhook."""
        self.last_received_at = datetime.now()
        self.total_received += 1

    def record_processed(self) -> None:
        """Record successful processing."""
        self.total_processed += 1

    def record_failed(self) -> None:
        """Record failed processing."""
        self.total_failed += 1

    def get_success_rate(self) -> Optional[Decimal]:
        """Calculate processing success rate."""
        if self.total_received == 0:
            return None
        return round(Decimal(self.total_processed) / Decimal(self.total_received) * 100, 2)


# ============================================================================
# OAUTH TOKEN ENTITY
# ============================================================================

@dataclass
class OAuthToken:
    """
    What: OAuth token storage.
    Where: Integration authentication.
    Why: Manages tokens for external services.
    """
    provider: OAuthProvider
    access_token: str  # Encrypted

    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    provider_user_id: Optional[str] = None

    refresh_token: Optional[str] = None  # Encrypted
    token_type: str = "Bearer"

    expires_at: Optional[datetime] = None
    refresh_expires_at: Optional[datetime] = None

    scopes: list[str] = field(default_factory=list)

    is_valid: bool = True
    last_used_at: Optional[datetime] = None
    last_refreshed_at: Optional[datetime] = None

    consecutive_failures: int = 0
    last_error: Optional[str] = None

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate token data."""
        if not self.access_token:
            raise ValueError("Access token is required")
        if not self.user_id and not self.organization_id:
            raise ValueError("Either user_id or organization_id is required")

    def is_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at

    def can_refresh(self) -> bool:
        """Check if token can be refreshed."""
        if not self.refresh_token:
            return False
        if self.refresh_expires_at and datetime.now() >= self.refresh_expires_at:
            return False
        return True

    def needs_refresh(self) -> bool:
        """Check if token should be refreshed (expires in < 5 mins)."""
        if not self.expires_at:
            return False
        return datetime.now() >= (self.expires_at - timedelta(minutes=5))

    def mark_used(self) -> None:
        """Record token usage."""
        self.last_used_at = datetime.now()
        self.consecutive_failures = 0
        self.last_error = None

    def mark_refreshed(self, new_access_token: str, new_expires_at: datetime) -> None:
        """Update token after refresh."""
        self.access_token = new_access_token
        self.expires_at = new_expires_at
        self.last_refreshed_at = datetime.now()
        self.consecutive_failures = 0
        self.last_error = None

    def mark_failed(self, error: str) -> None:
        """Record token failure."""
        self.consecutive_failures += 1
        self.last_error = error
        if self.consecutive_failures >= 3:
            self.is_valid = False

    def invalidate(self) -> None:
        """Invalidate the token."""
        self.is_valid = False
