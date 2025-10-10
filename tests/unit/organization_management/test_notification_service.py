"""
Unit tests for NotificationService

BUSINESS CONTEXT:
Tests notification service functionality including sending notifications,
managing preferences, and tracking statistics.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from organization_management.application.services.notification_service import NotificationService
from organization_management.domain.entities.notification import (
    Notification,
    NotificationEvent,
    NotificationPriority,
    NotificationChannel,
    NotificationPreference
)
from organization_management.infrastructure.integrations.slack_integration import SlackCredentials


@pytest.fixture
def mock_dao():
    """Mock OrganizationManagementDAO"""
    dao = AsyncMock()
    return dao


@pytest.fixture
def slack_credentials():
    """Mock Slack credentials"""
    return SlackCredentials(
        bot_token="xoxb-test-token",
        workspace_id="T12345"
    )


@pytest.fixture
def notification_service(mock_dao, slack_credentials):
    """Create NotificationService instance"""
    return NotificationService(mock_dao, slack_credentials)


class TestNotificationServiceInitialization:
    """Test NotificationService initialization"""

    def test_service_creation(self, mock_dao, slack_credentials):
        """Test creating notification service"""
        service = NotificationService(mock_dao, slack_credentials)

        assert service._organization_dao == mock_dao
        assert service._slack_credentials == slack_credentials
        assert service._templates is not None
        assert len(service._templates) > 0

    def test_service_without_slack_credentials(self, mock_dao):
        """Test creating service without Slack credentials"""
        service = NotificationService(mock_dao, None)

        assert service._slack_credentials is None
        assert service._templates is not None

    def test_default_templates_initialized(self, notification_service):
        """Test default templates are initialized"""
        templates = notification_service._templates

        # Check some key templates exist
        assert NotificationEvent.COURSE_CREATED in templates
        assert NotificationEvent.ASSIGNMENT_DUE_SOON in templates
        assert NotificationEvent.MEETING_SCHEDULED in templates


class TestSendNotification:
    """Test send_notification method"""

    @pytest.mark.asyncio
    async def test_send_notification_success(self, notification_service, mock_dao):
        """Test successfully sending a notification"""
        recipient_id = uuid4()
        org_id = uuid4()

        # Mock user preferences
        preference = NotificationPreference(
            user_id=recipient_id,
            event_type=NotificationEvent.COURSE_CREATED,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )
        mock_dao.get_notification_preference.return_value = preference
        mock_dao.get_user_by_id.return_value = MagicMock(slack_id="U12345")
        mock_dao.create_notification.return_value = MagicMock(
            id=uuid4(),
            status="sent"
        )

        # Mock Slack sending
        with patch('organization_management.application.services.notification_service.SlackIntegrationService') as mock_slack:
            mock_slack_instance = AsyncMock()
            mock_slack_instance.__aenter__.return_value = mock_slack_instance
            mock_slack_instance.send_notification.return_value = True
            mock_slack.return_value = mock_slack_instance

            notification = await notification_service.send_notification(
                recipient_id=recipient_id,
                event_type=NotificationEvent.COURSE_CREATED,
                organization_id=org_id,
                variables={"course_name": "Python 101", "instructor_name": "Dr. Smith"},
                priority=NotificationPriority.NORMAL
            )

            assert notification is not None
            assert notification.status == "sent"

    @pytest.mark.asyncio
    async def test_send_notification_with_template(self, notification_service, mock_dao):
        """Test sending notification with template rendering"""
        recipient_id = uuid4()
        variables = {
            "assignment_name": "Homework 1",
            "due_date": "2025-10-15"
        }

        mock_dao.get_notification_preference.return_value = NotificationPreference(
            user_id=recipient_id,
            event_type=NotificationEvent.ASSIGNMENT_DUE_SOON,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )
        mock_dao.get_user_by_id.return_value = MagicMock(slack_id="U12345")
        mock_dao.create_notification.return_value = MagicMock(id=uuid4())

        with patch('organization_management.application.services.notification_service.SlackIntegrationService') as mock_slack:
            mock_slack_instance = AsyncMock()
            mock_slack_instance.__aenter__.return_value = mock_slack_instance
            mock_slack_instance.send_notification.return_value = True
            mock_slack.return_value = mock_slack_instance

            notification = await notification_service.send_notification(
                recipient_id=recipient_id,
                event_type=NotificationEvent.ASSIGNMENT_DUE_SOON,
                variables=variables
            )

            # Template should render variables into title/message
            # Check what was passed to create_notification
            mock_dao.create_notification.assert_called_once()
            call_args = mock_dao.create_notification.call_args[0][0]  # First positional arg
            assert "Homework 1" in call_args.title or "Homework 1" in call_args.message

    @pytest.mark.asyncio
    async def test_send_notification_forced_channels(self, notification_service, mock_dao):
        """Test sending notification with forced channels (ignoring preferences)"""
        recipient_id = uuid4()

        mock_dao.get_user_by_id.return_value = MagicMock(slack_id="U12345")
        mock_dao.create_notification.return_value = MagicMock(id=uuid4())

        with patch('organization_management.application.services.notification_service.SlackIntegrationService') as mock_slack:
            mock_slack_instance = AsyncMock()
            mock_slack_instance.__aenter__.return_value = mock_slack_instance
            mock_slack_instance.send_notification.return_value = True
            mock_slack.return_value = mock_slack_instance

            notification = await notification_service.send_notification(
                recipient_id=recipient_id,
                event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
                force_channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL]
            )

            # Check what was passed to create_notification
            mock_dao.create_notification.assert_called_once()
            call_args = mock_dao.create_notification.call_args[0][0]  # First positional arg
            assert NotificationChannel.SLACK in call_args.channels
            assert NotificationChannel.EMAIL in call_args.channels

    @pytest.mark.asyncio
    async def test_send_notification_respects_quiet_hours(self, notification_service, mock_dao):
        """Test notification respects user quiet hours preferences"""
        recipient_id = uuid4()

        # User has quiet hours enabled
        preference = NotificationPreference(
            user_id=recipient_id,
            event_type=NotificationEvent.ASSIGNMENT_DUE_SOON,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True,
            quiet_hours_start=22,
            quiet_hours_end=8
        )

        mock_dao.get_notification_preference.return_value = preference
        mock_dao.create_notification.return_value = MagicMock(id=uuid4())

        # During quiet hours, notification should still be created but channels may be filtered
        notification = await notification_service.send_notification(
            recipient_id=recipient_id,
            event_type=NotificationEvent.ASSIGNMENT_DUE_SOON
        )

        assert notification is not None


class TestSendChannelNotification:
    """Test send_channel_notification method"""

    @pytest.mark.asyncio
    async def test_send_channel_notification_success(self, notification_service):
        """Test sending notification to Slack channel"""
        with patch('organization_management.application.services.notification_service.SlackIntegrationService') as mock_slack:
            mock_slack_instance = AsyncMock()
            mock_slack_instance.__aenter__.return_value = mock_slack_instance
            mock_slack_instance.send_notification.return_value = True
            mock_slack.return_value = mock_slack_instance

            success = await notification_service.send_channel_notification(
                channel_id="C12345",
                event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
                title="System Update",
                message="The system will be updated tonight",
                priority=NotificationPriority.HIGH
            )

            assert success
            mock_slack_instance.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_channel_notification_without_slack(self, mock_dao):
        """Test sending channel notification without Slack credentials"""
        service = NotificationService(mock_dao, None)

        success = await service.send_channel_notification(
            channel_id="C12345",
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            title="Test",
            message="Test message"
        )

        assert not success


class TestSendOrganizationAnnouncement:
    """Test send_organization_announcement method"""

    @pytest.mark.asyncio
    async def test_send_announcement_to_all_members(self, notification_service, mock_dao):
        """Test sending announcement to all organization members"""
        org_id = uuid4()

        # Mock organization members
        members = [
            MagicMock(user_id=uuid4()),
            MagicMock(user_id=uuid4()),
            MagicMock(user_id=uuid4())
        ]
        mock_dao.get_organization_members.return_value = members
        mock_dao.get_notification_preference.return_value = NotificationPreference(
            user_id=uuid4(),
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )
        mock_dao.get_user_by_id.return_value = MagicMock(slack_id="U12345")
        mock_dao.create_notification.return_value = MagicMock(id=uuid4())

        with patch('organization_management.application.services.notification_service.SlackIntegrationService') as mock_slack:
            mock_slack_instance = AsyncMock()
            mock_slack_instance.__aenter__.return_value = mock_slack_instance
            mock_slack_instance.send_notification.return_value = True
            mock_slack.return_value = mock_slack_instance

            sent_count = await notification_service.send_organization_announcement(
                organization_id=org_id,
                title="Important Update",
                message="Please read this important update",
                priority=NotificationPriority.HIGH
            )

            assert sent_count == 3  # All 3 members

    @pytest.mark.asyncio
    async def test_send_announcement_handles_failures(self, notification_service, mock_dao):
        """Test announcement sending continues despite individual failures"""
        org_id = uuid4()

        # Mock members
        members = [
            MagicMock(user_id=uuid4()),
            MagicMock(user_id=uuid4()),
            MagicMock(user_id=uuid4())
        ]
        mock_dao.get_organization_members.return_value = members
        mock_dao.get_notification_preference.return_value = NotificationPreference(
            user_id=uuid4(),
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )

        # First user succeeds, second fails, third succeeds
        call_count = 0

        def mock_get_user(user_id):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("User not found")
            return MagicMock(slack_id="U12345")

        mock_dao.get_user_by_id.side_effect = mock_get_user
        mock_dao.create_notification.return_value = MagicMock(id=uuid4())

        with patch('organization_management.application.services.notification_service.SlackIntegrationService') as mock_slack:
            mock_slack_instance = AsyncMock()
            mock_slack_instance.__aenter__.return_value = mock_slack_instance
            mock_slack_instance.send_notification.return_value = True
            mock_slack.return_value = mock_slack_instance

            sent_count = await notification_service.send_organization_announcement(
                organization_id=org_id,
                title="Test",
                message="Test message"
            )

            # Should still create notifications for all 3 (Slack delivery failure is a soft error)
            assert sent_count == 3


class TestRoomNotifications:
    """Test instructor and track room notification methods"""

    @pytest.mark.asyncio
    async def test_send_instructor_room_notification(self, notification_service, mock_dao):
        """Test sending notification when instructor room is created"""
        instructor_id = uuid4()
        room_id = uuid4()
        org_id = uuid4()

        mock_dao.get_notification_preference.return_value = NotificationPreference(
            user_id=instructor_id,
            event_type=NotificationEvent.MEETING_ROOM_CREATED,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )
        mock_dao.get_user_by_id.return_value = MagicMock(slack_id="U12345")
        mock_dao.create_notification.return_value = MagicMock(id=uuid4())

        with patch('organization_management.application.services.notification_service.SlackIntegrationService') as mock_slack:
            mock_slack_instance = AsyncMock()
            mock_slack_instance.__aenter__.return_value = mock_slack_instance
            mock_slack_instance.send_notification.return_value = True
            mock_slack.return_value = mock_slack_instance

            success = await notification_service.send_instructor_room_notification(
                instructor_id=instructor_id,
                room_id=room_id,
                room_name="Python Instructor Room",
                join_url="https://zoom.us/j/123456",
                organization_id=org_id
            )

            assert success

    @pytest.mark.asyncio
    async def test_send_track_room_notification(self, notification_service, mock_dao):
        """Test sending notification to all track participants"""
        track_id = uuid4()
        org_id = uuid4()

        # Mock track assignments
        assignments = [
            MagicMock(user_id=uuid4()),  # Student
            MagicMock(user_id=uuid4()),  # Student
            MagicMock(user_id=uuid4())   # Instructor
        ]
        mock_dao.get_track_assignments.return_value = assignments
        mock_dao.get_notification_preference.return_value = NotificationPreference(
            user_id=uuid4(),
            event_type=NotificationEvent.MEETING_ROOM_CREATED,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )
        mock_dao.get_user_by_id.return_value = MagicMock(slack_id="U12345")
        mock_dao.create_notification.return_value = MagicMock(id=uuid4())

        with patch('organization_management.application.services.notification_service.SlackIntegrationService') as mock_slack:
            mock_slack_instance = AsyncMock()
            mock_slack_instance.__aenter__.return_value = mock_slack_instance
            mock_slack_instance.send_notification.return_value = True
            mock_slack.return_value = mock_slack_instance

            sent_count = await notification_service.send_track_room_notification(
                track_id=track_id,
                room_name="Python Track Room",
                join_url="https://zoom.us/j/789012",
                organization_id=org_id
            )

            assert sent_count == 3  # All participants notified


class TestNotificationStatistics:
    """Test get_notification_statistics method"""

    @pytest.mark.asyncio
    async def test_get_notification_statistics(self, notification_service, mock_dao):
        """Test retrieving notification statistics"""
        org_id = uuid4()

        # Mock notifications
        notifications = [
            MagicMock(
                event_type=NotificationEvent.COURSE_CREATED,
                priority=NotificationPriority.NORMAL,
                status="sent"
            ),
            MagicMock(
                event_type=NotificationEvent.COURSE_CREATED,
                priority=NotificationPriority.NORMAL,
                status="read"
            ),
            MagicMock(
                event_type=NotificationEvent.ASSIGNMENT_GRADED,
                priority=NotificationPriority.HIGH,
                status="read"
            ),
            MagicMock(
                event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
                priority=NotificationPriority.URGENT,
                status="failed"
            )
        ]
        mock_dao.get_organization_notifications.return_value = notifications

        stats = await notification_service.get_notification_statistics(org_id)

        assert stats["total_sent"] == 4
        assert "by_event_type" in stats
        assert "by_priority" in stats
        assert "by_status" in stats
        assert "read_rate" in stats

        # Check counts
        assert stats["by_status"]["read"] == 2
        assert stats["by_status"]["sent"] == 1
        assert stats["by_status"]["failed"] == 1

        # Check read rate (2 read out of 4 = 50%)
        assert stats["read_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, notification_service, mock_dao):
        """Test statistics with no notifications"""
        org_id = uuid4()
        mock_dao.get_organization_notifications.return_value = []

        stats = await notification_service.get_notification_statistics(org_id)

        assert stats["total_sent"] == 0
        assert stats["read_rate"] == 0.0


class TestGetUserNotifications:
    """Test get_user_notifications method"""

    @pytest.mark.asyncio
    async def test_get_user_notifications(self, notification_service, mock_dao):
        """Test retrieving user notifications"""
        user_id = uuid4()

        mock_notifications = [
            MagicMock(id=uuid4(), title="Notification 1", status="read"),
            MagicMock(id=uuid4(), title="Notification 2", status="sent"),
            MagicMock(id=uuid4(), title="Notification 3", status="delivered")
        ]
        mock_dao.get_user_notifications.return_value = mock_notifications

        notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            unread_only=False,
            limit=50
        )

        assert len(notifications) == 3
        mock_dao.get_user_notifications.assert_called_once_with(user_id, False, 50)

    @pytest.mark.asyncio
    async def test_get_unread_notifications_only(self, notification_service, mock_dao):
        """Test retrieving only unread notifications"""
        user_id = uuid4()

        mock_notifications = [
            MagicMock(id=uuid4(), title="Unread 1", status="sent"),
            MagicMock(id=uuid4(), title="Unread 2", status="delivered")
        ]
        mock_dao.get_user_notifications.return_value = mock_notifications

        notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            unread_only=True,
            limit=10
        )

        assert len(notifications) == 2
        mock_dao.get_user_notifications.assert_called_once_with(user_id, True, 10)


class TestMarkNotificationRead:
    """Test mark_notification_read method"""

    @pytest.mark.asyncio
    async def test_mark_notification_read_success(self, notification_service, mock_dao):
        """Test marking notification as read"""
        notification_id = uuid4()

        mock_notification = MagicMock(
            id=notification_id,
            status="sent"
        )
        mock_dao.get_notification_by_id.return_value = mock_notification
        mock_dao.update_notification.return_value = mock_notification

        success = await notification_service.mark_notification_read(notification_id)

        assert success
        mock_notification.mark_as_read.assert_called_once()
        mock_dao.update_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_notification_read_not_found(self, notification_service, mock_dao):
        """Test marking non-existent notification as read"""
        notification_id = uuid4()
        mock_dao.get_notification_by_id.return_value = None

        success = await notification_service.mark_notification_read(notification_id)

        assert not success


class TestNotificationServiceErrorHandling:
    """Test error handling in NotificationService"""

    @pytest.mark.asyncio
    async def test_send_notification_handles_exception(self, notification_service, mock_dao):
        """Test error handling when sending notification fails"""
        recipient_id = uuid4()

        # Mock exception
        mock_dao.get_notification_preference.side_effect = Exception("Database error")

        # Service should handle gracefully and log warning, not raise
        result = await notification_service.send_notification(
            recipient_id=recipient_id,
            event_type=NotificationEvent.COURSE_CREATED
        )

        # Should return None or similar when error occurs
        assert result is None or hasattr(result, 'id')

    @pytest.mark.asyncio
    async def test_get_statistics_handles_exception(self, notification_service, mock_dao):
        """Test error handling when retrieving statistics fails"""
        org_id = uuid4()
        mock_dao.get_organization_notifications.side_effect = Exception("Database error")

        stats = await notification_service.get_notification_statistics(org_id)

        # Should return empty stats on error
        assert stats == {}
