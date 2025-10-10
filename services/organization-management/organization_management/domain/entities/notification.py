"""
Notification Domain Entities
Defines notification types, events, and preferences for the platform
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class NotificationEvent(Enum):
    """Platform notification event types"""
    # Course Events
    COURSE_CREATED = "course_created"
    COURSE_UPDATED = "course_updated"
    COURSE_PUBLISHED = "course_published"
    COURSE_ARCHIVED = "course_archived"

    # Assignment Events
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_DUE_SOON = "assignment_due_soon"
    ASSIGNMENT_OVERDUE = "assignment_overdue"
    ASSIGNMENT_SUBMITTED = "assignment_submitted"
    ASSIGNMENT_GRADED = "assignment_graded"

    # Quiz Events
    QUIZ_AVAILABLE = "quiz_available"
    QUIZ_DUE_SOON = "quiz_due_soon"
    QUIZ_COMPLETED = "quiz_completed"
    QUIZ_GRADED = "quiz_graded"

    # Enrollment Events
    STUDENT_ENROLLED = "student_enrolled"
    STUDENT_UNENROLLED = "student_unenrolled"
    ENROLLMENT_APPROVED = "enrollment_approved"
    ENROLLMENT_REJECTED = "enrollment_rejected"

    # Meeting Room Events
    MEETING_ROOM_CREATED = "meeting_room_created"
    MEETING_SCHEDULED = "meeting_scheduled"
    MEETING_CANCELLED = "meeting_cancelled"
    MEETING_REMINDER = "meeting_reminder"

    # Progress Events
    MODULE_COMPLETED = "module_completed"
    COURSE_COMPLETED = "course_completed"
    CERTIFICATE_EARNED = "certificate_earned"
    MILESTONE_ACHIEVED = "milestone_achieved"

    # Organization Events
    INSTRUCTOR_ADDED = "instructor_added"
    INSTRUCTOR_REMOVED = "instructor_removed"
    ROLE_CHANGED = "role_changed"
    TRACK_CREATED = "track_created"
    PROJECT_CREATED = "project_created"

    # System Events
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    MAINTENANCE_SCHEDULED = "maintenance_scheduled"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_LOCKED = "account_locked"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(Enum):
    """Notification delivery channels"""
    SLACK = "slack"
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"


@dataclass
class Notification:
    """
    Notification entity representing a platform notification

    BUSINESS CONTEXT:
    Notifications inform users about important events across the platform.
    They can be delivered via multiple channels (Slack, email, in-app, SMS).
    Users can configure preferences for which events they want to receive.
    """
    id: UUID = field(default_factory=uuid4)
    event_type: NotificationEvent = None
    recipient_id: UUID = None  # User ID
    organization_id: Optional[UUID] = None
    title: str = ""
    message: str = ""
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, delivered, read, failed

    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = "sent"
        self.sent_at = datetime.utcnow()

    def mark_as_delivered(self):
        """Mark notification as delivered"""
        self.status = "delivered"

    def mark_as_read(self):
        """Mark notification as read"""
        self.status = "read"
        self.read_at = datetime.utcnow()

    def mark_as_failed(self):
        """Mark notification as failed"""
        self.status = "failed"

    def is_sent(self) -> bool:
        """Check if notification was sent"""
        return self.status in ["sent", "delivered", "read"]

    def is_read(self) -> bool:
        """Check if notification was read"""
        return self.status == "read"

    def is_valid(self) -> bool:
        """Validate notification"""
        return (
            self.event_type is not None and
            self.recipient_id is not None and
            self.title and
            self.message and
            len(self.channels) > 0
        )


@dataclass
class NotificationPreference:
    """
    User notification preferences

    BUSINESS CONTEXT:
    Users can configure which types of notifications they want to receive
    and through which channels. This respects user privacy and reduces
    notification fatigue.
    """
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = None
    event_type: NotificationEvent = None
    enabled_channels: List[NotificationChannel] = field(default_factory=list)
    enabled: bool = True
    quiet_hours_start: Optional[int] = None  # Hour of day (0-23)
    quiet_hours_end: Optional[int] = None    # Hour of day (0-23)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if channel is enabled for this event type"""
        return self.enabled and channel in self.enabled_channels

    def is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours"""
        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False

        current_hour = datetime.utcnow().hour

        if self.quiet_hours_start < self.quiet_hours_end:
            return self.quiet_hours_start <= current_hour < self.quiet_hours_end
        else:
            # Quiet hours span midnight
            return current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end

    def should_send_notification(self, channel: NotificationChannel) -> bool:
        """
        Determine if notification should be sent based on preferences

        BUSINESS REQUIREMENT:
        Respects user preferences and quiet hours
        """
        if not self.enabled:
            return False

        if not self.is_channel_enabled(channel):
            return False

        if self.is_quiet_hours():
            # Still send urgent notifications during quiet hours
            return False

        return True


@dataclass
class NotificationTemplate:
    """
    Notification template for consistent messaging

    BUSINESS CONTEXT:
    Templates ensure consistent, professional communication across
    all notification channels. They support variable substitution
    for personalization.
    """
    id: UUID = field(default_factory=uuid4)
    event_type: NotificationEvent = None
    channel: NotificationChannel = None
    title_template: str = ""
    message_template: str = ""
    variables: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def render_title(self, variables: Dict[str, str]) -> str:
        """Render title with variable substitution"""
        title = self.title_template
        for var_name, var_value in variables.items():
            title = title.replace(f"{{{{{var_name}}}}}", str(var_value))
        return title

    def render_message(self, variables: Dict[str, str]) -> str:
        """Render message with variable substitution"""
        message = self.message_template
        for var_name, var_value in variables.items():
            message = message.replace(f"{{{{{var_name}}}}}", str(var_value))
        return message

    def is_valid(self) -> bool:
        """Validate template"""
        return (
            self.event_type is not None and
            self.channel is not None and
            self.title_template and
            self.message_template
        )
