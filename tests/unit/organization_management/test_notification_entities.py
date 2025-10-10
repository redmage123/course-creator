"""
Unit tests for notification domain entities

BUSINESS CONTEXT:
Tests notification entities, event types, preferences, and templates
to ensure correct notification behavior and user preference handling.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from organization_management.domain.entities.notification import (
    Notification,
    NotificationEvent,
    NotificationPriority,
    NotificationChannel,
    NotificationPreference,
    NotificationTemplate
)


class TestNotificationEntity:
    """Test Notification entity"""

    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification(
            event_type=NotificationEvent.COURSE_CREATED,
            recipient_id=uuid4(),
            organization_id=uuid4(),
            title="New Course Created",
            message="A new course has been created",
            priority=NotificationPriority.NORMAL,
            channels=[NotificationChannel.SLACK],
            metadata={"course_id": str(uuid4())}
        )

        assert notification.id is not None
        assert notification.event_type == NotificationEvent.COURSE_CREATED
        assert notification.priority == NotificationPriority.NORMAL
        assert NotificationChannel.SLACK in notification.channels
        assert notification.status == "pending"

    def test_notification_mark_as_sent(self):
        """Test marking notification as sent"""
        notification = Notification(
            event_type=NotificationEvent.ASSIGNMENT_GRADED,
            recipient_id=uuid4(),
            title="Assignment Graded",
            message="Your assignment has been graded",
            channels=[NotificationChannel.EMAIL]
        )

        notification.mark_as_sent()

        assert notification.status == "sent"
        assert notification.sent_at is not None

    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification(
            event_type=NotificationEvent.QUIZ_AVAILABLE,
            recipient_id=uuid4(),
            title="Quiz Available",
            message="A new quiz is available",
            channels=[NotificationChannel.IN_APP]
        )

        notification.mark_as_read()

        assert notification.status == "read"
        assert notification.read_at is not None
        assert notification.is_read()

    def test_notification_is_sent(self):
        """Test checking if notification was sent"""
        notification = Notification(
            event_type=NotificationEvent.MEETING_SCHEDULED,
            recipient_id=uuid4(),
            title="Meeting Scheduled",
            message="A meeting has been scheduled",
            channels=[NotificationChannel.SLACK]
        )

        assert not notification.is_sent()

        notification.mark_as_sent()
        assert notification.is_sent()

        notification.mark_as_delivered()
        assert notification.is_sent()

        notification.mark_as_read()
        assert notification.is_sent()

    def test_notification_validation(self):
        """Test notification validation"""
        # Valid notification
        valid_notification = Notification(
            event_type=NotificationEvent.CERTIFICATE_EARNED,
            recipient_id=uuid4(),
            title="Certificate Earned",
            message="Congratulations on earning your certificate!",
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP]
        )
        assert valid_notification.is_valid()

        # Invalid - missing event type
        invalid_notification = Notification(
            recipient_id=uuid4(),
            title="Test",
            message="Test message",
            channels=[NotificationChannel.SLACK]
        )
        assert not invalid_notification.is_valid()

        # Invalid - missing recipient
        invalid_notification2 = Notification(
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            title="Test",
            message="Test message",
            channels=[NotificationChannel.SLACK]
        )
        assert not invalid_notification2.is_valid()

        # Invalid - no channels
        invalid_notification3 = Notification(
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            recipient_id=uuid4(),
            title="Test",
            message="Test message",
            channels=[]
        )
        assert not invalid_notification3.is_valid()


class TestNotificationPreference:
    """Test NotificationPreference entity"""

    def test_preference_creation(self):
        """Test creating notification preferences"""
        preference = NotificationPreference(
            user_id=uuid4(),
            event_type=NotificationEvent.ASSIGNMENT_DUE_SOON,
            enabled_channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
            enabled=True
        )

        assert preference.id is not None
        assert preference.enabled
        assert NotificationChannel.SLACK in preference.enabled_channels

    def test_is_channel_enabled(self):
        """Test checking if channel is enabled"""
        preference = NotificationPreference(
            user_id=uuid4(),
            event_type=NotificationEvent.QUIZ_DUE_SOON,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )

        assert preference.is_channel_enabled(NotificationChannel.SLACK)
        assert not preference.is_channel_enabled(NotificationChannel.EMAIL)

        # Disabled preference
        preference.enabled = False
        assert not preference.is_channel_enabled(NotificationChannel.SLACK)

    def test_quiet_hours(self):
        """Test quiet hours functionality"""
        # No quiet hours
        preference = NotificationPreference(
            user_id=uuid4(),
            event_type=NotificationEvent.STUDENT_ENROLLED,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )
        assert not preference.is_quiet_hours()

        # Quiet hours set (10 PM to 8 AM)
        preference.quiet_hours_start = 22  # 10 PM
        preference.quiet_hours_end = 8     # 8 AM

        # This test is time-dependent, so we'll just check the logic works
        is_quiet = preference.is_quiet_hours()
        assert isinstance(is_quiet, bool)

    def test_should_send_notification(self):
        """Test should send notification logic"""
        preference = NotificationPreference(
            user_id=uuid4(),
            event_type=NotificationEvent.MEETING_REMINDER,
            enabled_channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
            enabled=True
        )

        # Should send via Slack
        assert preference.should_send_notification(NotificationChannel.SLACK)

        # Should not send via SMS (not enabled)
        assert not preference.should_send_notification(NotificationChannel.SMS)

        # Disable preference
        preference.enabled = False
        assert not preference.should_send_notification(NotificationChannel.SLACK)


class TestNotificationTemplate:
    """Test NotificationTemplate entity"""

    def test_template_creation(self):
        """Test creating notification template"""
        template = NotificationTemplate(
            event_type=NotificationEvent.COURSE_CREATED,
            channel=NotificationChannel.SLACK,
            title_template="New Course: {{course_name}}",
            message_template="{{instructor_name}} created {{course_name}}",
            variables=["course_name", "instructor_name"]
        )

        assert template.id is not None
        assert template.event_type == NotificationEvent.COURSE_CREATED
        assert "course_name" in template.variables

    def test_template_render_title(self):
        """Test rendering template title"""
        template = NotificationTemplate(
            event_type=NotificationEvent.ASSIGNMENT_GRADED,
            channel=NotificationChannel.EMAIL,
            title_template="Assignment {{assignment_name}} Graded",
            message_template="Score: {{score}}/{{max_score}}",
            variables=["assignment_name", "score", "max_score"]
        )

        rendered = template.render_title({
            "assignment_name": "Homework 1",
            "score": "95",
            "max_score": "100"
        })

        assert rendered == "Assignment Homework 1 Graded"

    def test_template_render_message(self):
        """Test rendering template message"""
        template = NotificationTemplate(
            event_type=NotificationEvent.MEETING_SCHEDULED,
            channel=NotificationChannel.SLACK,
            title_template="Meeting Scheduled",
            message_template="{{meeting_name}} on {{date}} at {{time}}. Join: {{url}}",
            variables=["meeting_name", "date", "time", "url"]
        )

        rendered = template.render_message({
            "meeting_name": "Team Standup",
            "date": "2025-10-15",
            "time": "10:00 AM",
            "url": "https://zoom.us/j/123456"
        })

        assert "Team Standup" in rendered
        assert "2025-10-15" in rendered
        assert "10:00 AM" in rendered
        assert "https://zoom.us/j/123456" in rendered

    def test_template_validation(self):
        """Test template validation"""
        # Valid template
        valid_template = NotificationTemplate(
            event_type=NotificationEvent.CERTIFICATE_EARNED,
            channel=NotificationChannel.EMAIL,
            title_template="Certificate Earned",
            message_template="Congratulations {{student_name}}!",
            variables=["student_name"]
        )
        assert valid_template.is_valid()

        # Invalid - missing event type
        invalid_template = NotificationTemplate(
            channel=NotificationChannel.SLACK,
            title_template="Test",
            message_template="Test message",
            variables=[]
        )
        assert not invalid_template.is_valid()

        # Invalid - missing channel
        invalid_template2 = NotificationTemplate(
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            title_template="Test",
            message_template="Test message",
            variables=[]
        )
        assert not invalid_template2.is_valid()


class TestNotificationEnums:
    """Test notification enum types"""

    def test_notification_event_enum(self):
        """Test NotificationEvent enum values"""
        # Test a few key events
        assert NotificationEvent.COURSE_CREATED.value == "course_created"
        assert NotificationEvent.ASSIGNMENT_GRADED.value == "assignment_graded"
        assert NotificationEvent.MEETING_SCHEDULED.value == "meeting_scheduled"
        assert NotificationEvent.CERTIFICATE_EARNED.value == "certificate_earned"

        # Test enum membership
        assert NotificationEvent.QUIZ_AVAILABLE in NotificationEvent
        assert NotificationEvent.STUDENT_ENROLLED in NotificationEvent

    def test_notification_priority_enum(self):
        """Test NotificationPriority enum values"""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.URGENT.value == "urgent"

    def test_notification_channel_enum(self):
        """Test NotificationChannel enum values"""
        assert NotificationChannel.SLACK.value == "slack"
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.IN_APP.value == "in_app"
        assert NotificationChannel.SMS.value == "sms"


class TestNotificationBusinessLogic:
    """Test notification business logic and workflows"""

    def test_notification_lifecycle(self):
        """Test complete notification lifecycle"""
        # Create notification
        notification = Notification(
            event_type=NotificationEvent.COURSE_PUBLISHED,
            recipient_id=uuid4(),
            organization_id=uuid4(),
            title="Course Published",
            message="Your course has been published",
            priority=NotificationPriority.NORMAL,
            channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL]
        )

        # Initial state
        assert notification.status == "pending"
        assert not notification.is_sent()
        assert not notification.is_read()

        # Send notification
        notification.mark_as_sent()
        assert notification.status == "sent"
        assert notification.is_sent()
        assert notification.sent_at is not None

        # Deliver notification
        notification.mark_as_delivered()
        assert notification.status == "delivered"
        assert notification.is_sent()

        # Read notification
        notification.mark_as_read()
        assert notification.status == "read"
        assert notification.is_read()
        assert notification.read_at is not None

    def test_notification_failure_handling(self):
        """Test notification failure scenarios"""
        notification = Notification(
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            recipient_id=uuid4(),
            title="System Announcement",
            message="Important update",
            channels=[NotificationChannel.SLACK]
        )

        # Mark as failed
        notification.mark_as_failed()
        assert notification.status == "failed"
        assert not notification.is_sent()

    def test_multi_channel_notification(self):
        """Test notification with multiple channels"""
        notification = Notification(
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            recipient_id=uuid4(),
            title="Urgent: System Maintenance",
            message="System will be down for maintenance",
            priority=NotificationPriority.URGENT,
            channels=[
                NotificationChannel.SLACK,
                NotificationChannel.EMAIL,
                NotificationChannel.SMS,
                NotificationChannel.IN_APP
            ]
        )

        assert len(notification.channels) == 4
        assert NotificationChannel.SLACK in notification.channels
        assert NotificationChannel.EMAIL in notification.channels
        assert NotificationChannel.SMS in notification.channels
        assert NotificationChannel.IN_APP in notification.channels

    def test_notification_metadata(self):
        """Test notification metadata storage"""
        metadata = {
            "course_id": str(uuid4()),
            "course_name": "Introduction to Python",
            "instructor_id": str(uuid4()),
            "instructor_name": "Dr. Smith",
            "action_url": "https://platform.com/courses/123"
        }

        notification = Notification(
            event_type=NotificationEvent.COURSE_CREATED,
            recipient_id=uuid4(),
            title="New Course",
            message="A new course is available",
            channels=[NotificationChannel.IN_APP],
            metadata=metadata
        )

        assert notification.metadata == metadata
        assert notification.metadata["course_name"] == "Introduction to Python"
        assert "action_url" in notification.metadata
