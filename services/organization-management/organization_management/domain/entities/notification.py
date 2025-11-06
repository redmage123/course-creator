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
        """
        Mark notification as sent to delivery channel

        BUSINESS PURPOSE:
        Records when notification was successfully sent to external service
        (Slack API, email server, SMS gateway, etc.).

        WHY THIS APPROACH:
        - Status transition from "pending" to "sent"
        - Records sent timestamp for delivery analytics
        - Indicates successful handoff to external service

        DELIVERY STATUS WORKFLOW:
        pending → sent → delivered → read

        Returns:
            None - updates entity in place (sets status and sent_at)
        """
        self.status = "sent"
        self.sent_at = datetime.utcnow()

    def mark_as_delivered(self):
        """
        Mark notification as delivered to recipient

        BUSINESS PURPOSE:
        Records confirmation from external service that notification was
        successfully delivered to recipient (email received, Slack message posted).

        WHY THIS APPROACH:
        - Status transition from "sent" to "delivered"
        - Indicates external service confirmation
        - No timestamp (sent_at remains the key metric)

        DELIVERY STATUS WORKFLOW:
        pending → sent → delivered → read

        Returns:
            None - updates entity in place (sets status to "delivered")
        """
        self.status = "delivered"

    def mark_as_read(self):
        """
        Mark notification as read by recipient

        BUSINESS PURPOSE:
        Records when recipient opened/viewed notification. Used for engagement
        analytics and delivery confirmation.

        WHY THIS APPROACH:
        - Status transition to final "read" state
        - Records read timestamp for engagement metrics
        - Indicates successful user engagement

        DELIVERY STATUS WORKFLOW:
        pending → sent → delivered → read (final)

        Returns:
            None - updates entity in place (sets status and read_at)
        """
        self.status = "read"
        self.read_at = datetime.utcnow()

    def mark_as_failed(self):
        """
        Mark notification delivery as failed

        BUSINESS PURPOSE:
        Records permanent delivery failure (invalid email, channel unavailable,
        API error, etc.). Allows retry logic or manual intervention.

        WHY THIS APPROACH:
        - Terminal status indicates no further delivery attempts
        - No timestamp (sent_at or created_at used for failure time)
        - Allows filtering failed notifications for retry

        COMMON FAILURE REASONS:
        - Invalid email address
        - Slack channel deleted
        - SMS delivery failure
        - API rate limiting

        Returns:
            None - updates entity in place (sets status to "failed")
        """
        self.status = "failed"

    def is_sent(self) -> bool:
        """
        Check if notification was successfully sent

        BUSINESS PURPOSE:
        Quick check for whether notification left the system successfully.
        Includes all post-sent statuses (sent, delivered, read).

        WHY THIS APPROACH:
        - Treats "sent", "delivered", and "read" as successful states
        - Simple boolean for conditional logic
        - Encapsulates multiple status checks

        Returns:
            bool: True if status is sent/delivered/read, False otherwise
        """
        return self.status in ["sent", "delivered", "read"]

    def is_read(self) -> bool:
        """
        Check if notification was read by recipient

        BUSINESS PURPOSE:
        Determines if recipient engaged with notification. Used for
        engagement analytics and follow-up decisions.

        WHY THIS APPROACH:
        - Simple status check for readability
        - Returns boolean for conditional logic
        - Encapsulates status comparison

        Returns:
            bool: True if status is "read", False otherwise
        """
        return self.status == "read"

    def is_valid(self) -> bool:
        """
        Validate notification data integrity

        BUSINESS PURPOSE:
        Ensures notification has all required fields before sending.
        Prevents invalid notifications from being created.

        WHY THIS APPROACH:
        - Validates required foreign key relationships
        - Ensures content fields are non-empty
        - Requires at least one delivery channel

        VALIDATION RULES:
        - event_type must be set (valid NotificationEvent)
        - recipient_id must be set (valid user reference)
        - title must be non-empty string
        - message must be non-empty string
        - channels list must contain at least one NotificationChannel

        Returns:
            bool: True if all validations pass, False otherwise
        """
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
        """
        Check if notification channel is enabled for this event type

        BUSINESS PURPOSE:
        Validates user has enabled specific channel (Slack, email, SMS) for
        this event type before sending notification.

        WHY THIS APPROACH:
        - Checks both global enabled flag and channel-specific list
        - Returns False if preference is globally disabled
        - Respects granular channel preferences

        Args:
            channel: NotificationChannel to check (SLACK, EMAIL, IN_APP, SMS)

        Returns:
            bool: True if enabled and channel is in enabled_channels, False otherwise
        """
        return self.enabled and channel in self.enabled_channels

    def is_quiet_hours(self) -> bool:
        """
        Check if current time is within user's quiet hours

        BUSINESS PURPOSE:
        Respects user's "do not disturb" preferences to prevent notification
        fatigue. Quiet hours suppress non-urgent notifications.

        WHY THIS APPROACH:
        - Returns False if quiet hours not configured (always send)
        - Handles quiet hours spanning midnight (22:00 - 06:00)
        - Uses UTC hour for timezone-independent calculation

        QUIET HOURS LOGIC:
        - Normal hours: start=22, end=6 → quiet from 22:00-05:59
        - Spanning midnight: start >= current OR current < end

        Returns:
            bool: True if current time is within quiet hours, False otherwise
        """
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
        Determine if notification should be sent based on user preferences

        BUSINESS PURPOSE:
        Comprehensive check that respects user preferences, channel enablement,
        and quiet hours before sending notification.

        WHY THIS APPROACH:
        - Combines multiple preference checks in logical order
        - Early returns for performance (short-circuit evaluation)
        - Prevents notification fatigue and respects user privacy

        BUSINESS RULE:
        Urgent notifications (not implemented yet) should bypass quiet hours.
        Current implementation suppresses all notifications during quiet hours.

        VALIDATION LOGIC:
        1. Check if preferences are globally enabled
        2. Check if specific channel is enabled
        3. Check if current time is within quiet hours

        Args:
            channel: NotificationChannel to check (SLACK, EMAIL, IN_APP, SMS)

        Returns:
            bool: True if notification should be sent, False otherwise
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
        """
        Render notification title with variable substitution

        BUSINESS PURPOSE:
        Generates personalized notification titles by replacing template variables
        with actual values (user names, course names, dates, etc.).

        WHY THIS APPROACH:
        - Simple string replacement for template variables
        - Variable format: {{variable_name}} (double braces)
        - Converts all values to strings for consistent output
        - Iterates over provided variables dictionary

        TEMPLATE EXAMPLE:
        - Template: "Welcome, {{user_name}}!"
        - Variables: {"user_name": "John"}
        - Output: "Welcome, John!"

        Args:
            variables: Dictionary mapping variable names to values

        Returns:
            str: Rendered title with variables replaced
        """
        title = self.title_template
        for var_name, var_value in variables.items():
            title = title.replace(f"{{{{{var_name}}}}}", str(var_value))
        return title

    def render_message(self, variables: Dict[str, str]) -> str:
        """
        Render notification message with variable substitution

        BUSINESS PURPOSE:
        Generates personalized notification messages by replacing template variables
        with actual values (course progress, assignment grades, meeting links, etc.).

        WHY THIS APPROACH:
        - Simple string replacement for template variables
        - Variable format: {{variable_name}} (double braces)
        - Converts all values to strings for consistent output
        - Iterates over provided variables dictionary

        TEMPLATE EXAMPLE:
        - Template: "Your assignment {{assignment_name}} was graded: {{grade}}"
        - Variables: {"assignment_name": "Python Quiz 1", "grade": "95%"}
        - Output: "Your assignment Python Quiz 1 was graded: 95%"

        Args:
            variables: Dictionary mapping variable names to values

        Returns:
            str: Rendered message with variables replaced
        """
        message = self.message_template
        for var_name, var_value in variables.items():
            message = message.replace(f"{{{{{var_name}}}}}", str(var_value))
        return message

    def is_valid(self) -> bool:
        """
        Validate notification template data integrity

        BUSINESS PURPOSE:
        Ensures template has all required fields before use. Prevents
        invalid templates from being created or used for rendering.

        WHY THIS APPROACH:
        - Validates event type and channel are set
        - Ensures title and message templates are non-empty
        - Does not validate variable substitution (runtime concern)

        VALIDATION RULES:
        - event_type must be set (valid NotificationEvent)
        - channel must be set (valid NotificationChannel)
        - title_template must be non-empty string
        - message_template must be non-empty string

        Returns:
            bool: True if all validations pass, False otherwise
        """
        return (
            self.event_type is not None and
            self.channel is not None and
            self.title_template and
            self.message_template
        )
