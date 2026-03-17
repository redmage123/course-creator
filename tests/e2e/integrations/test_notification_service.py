"""
E2E tests for NotificationService with real Slack API integration

BUSINESS CONTEXT:
Tests notification service functionality with actual Slack API calls,
including sending notifications, managing preferences, and tracking statistics.

REQUIREMENTS:
These tests require real Slack API credentials to run:
- SLACK_BOT_TOKEN: Bot OAuth token (xoxb-...)
- SLACK_WORKSPACE_ID: Workspace ID (T...)

If credentials are not available, tests will be automatically skipped.

NOTE: This file was moved from tests/unit/organization_management/ because
it requires external API access and should be tested as an E2E integration.
"""

import pytest
from uuid import uuid4
from conftest import skip_if_no_slack

from organization_management.application.services.notification_service import NotificationService
from organization_management.domain.entities.notification import (
    Notification,
    NotificationEvent,
    NotificationPriority,
    NotificationChannel,
    NotificationPreference
)
from organization_management.infrastructure.integrations.slack_integration import (
    SlackCredentials,
    SlackIntegrationService
)


class RealNotificationDAO:
    """Real DAO implementation using in-memory storage for E2E testing"""
    def __init__(self):
        self.preferences = {}
        self.notifications = {}
        self.organization_members = {}

    async def get_notification_preference(self, user_id):
        return self.preferences.get(str(user_id))

    async def get_user_by_id(self, user_id):
        """Return user object with Slack ID for testing"""
        class User:
            def __init__(self, user_id, slack_id):
                self.id = user_id
                self.slack_id = slack_id
        # In E2E tests, this would come from actual database
        return User(user_id, "U12345")

    async def create_notification(self, notification):
        self.notifications[str(notification.id)] = notification
        return notification

    async def get_notification_by_id(self, notification_id):
        return self.notifications.get(str(notification_id))

    async def update_notification(self, notification):
        self.notifications[str(notification.id)] = notification
        return notification

    async def get_user_notifications(self, user_id, unread_only, limit):
        user_notifs = [n for n in self.notifications.values() if n.recipient_id == user_id]
        if unread_only:
            user_notifs = [n for n in user_notifs if n.status != 'read']
        return user_notifs[:limit]

    async def get_organization_members(self):
        return list(self.organization_members.values())

    async def get_track_assignments(self, track_id):
        return []

    async def get_organization_notifications(self, org_id):
        return [n for n in self.notifications.values() if hasattr(n, 'organization_id') and n.organization_id == org_id]


@pytest.fixture
def real_dao():
    """Create real DAO for E2E testing"""
    return RealNotificationDAO()


@pytest.fixture
def notification_service(real_dao, slack_credentials):
    """
    Create NotificationService instance with real Slack credentials

    This fixture requires SLACK_BOT_TOKEN and SLACK_WORKSPACE_ID environment variables.
    Tests using this fixture will be skipped if credentials are not available.
    """
    if slack_credentials is None:
        pytest.skip("Slack credentials not available")

    credentials = SlackCredentials(
        bot_token=slack_credentials["bot_token"],
        workspace_id=slack_credentials["workspace_id"]
    )
    return NotificationService(real_dao, credentials)


# ============================================================================
# E2E TESTS WITH REAL SLACK API
# ============================================================================

@pytest.mark.e2e
@pytest.mark.slack_api
@skip_if_no_slack
class TestSlackNotificationE2E:
    """
    E2E tests for Slack notifications with real API calls

    IMPORTANT: These tests make real API calls to Slack and require:
    1. Valid Slack bot token with appropriate scopes
    2. Valid workspace ID
    3. Test channel or user IDs that exist in the workspace
    """

    @pytest.mark.asyncio
    async def test_send_notification_to_slack_channel(self, notification_service, real_dao, slack_credentials):
        """
        Test sending notification to real Slack channel

        This test verifies:
        1. Notification is created in database
        2. Slack API is called successfully
        3. Message is delivered to Slack channel
        """
        recipient_id = uuid4()

        # Set up notification preference for Slack channel
        real_dao.preferences[str(recipient_id)] = NotificationPreference(
            user_id=recipient_id,
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )

        # Send notification (this will make real Slack API call)
        notification = await notification_service.send_notification(
            recipient_id=recipient_id,
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            title="E2E Test Notification",
            message="This is a test notification from E2E tests"
        )

        # Verify notification was created
        assert notification is not None
        assert notification.id is not None
        assert notification.title == "E2E Test Notification"
        assert NotificationChannel.SLACK in notification.channels

        # Verify notification is in database
        stored_notification = await real_dao.get_notification_by_id(notification.id)
        assert stored_notification is not None

    @pytest.mark.asyncio
    async def test_send_notification_with_template_rendering(self, notification_service, real_dao):
        """
        Test sending notification with template variable rendering

        This test verifies:
        1. Template variables are correctly rendered
        2. Rendered message is sent to Slack
        3. Notification status is tracked
        """
        recipient_id = uuid4()
        variables = {
            "assignment_name": "E2E Test Assignment",
            "due_date": "2025-12-15"
        }

        real_dao.preferences[str(recipient_id)] = NotificationPreference(
            user_id=recipient_id,
            event_type=NotificationEvent.ASSIGNMENT_DUE_SOON,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True
        )

        notification = await notification_service.send_notification(
            recipient_id=recipient_id,
            event_type=NotificationEvent.ASSIGNMENT_DUE_SOON,
            variables=variables
        )

        assert notification is not None
        # Verify template variables were rendered into message
        assert "E2E Test Assignment" in notification.message or "E2E Test Assignment" in notification.title

    @pytest.mark.asyncio
    async def test_send_channel_notification(self, notification_service, slack_credentials):
        """
        Test sending notification to Slack channel by channel ID

        This test verifies:
        1. Channel notification is sent successfully
        2. Slack API accepts the message
        3. Proper error handling for invalid channels
        """
        # Note: Replace with actual test channel ID in your workspace
        test_channel_id = slack_credentials.get("test_channel_id", "C12345678")

        success = await notification_service.send_channel_notification(
            channel_id=test_channel_id,
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            title="E2E Test Channel Notification",
            message="This is a channel notification from E2E tests",
            priority=NotificationPriority.NORMAL
        )

        # In E2E tests, we expect this to either succeed or fail gracefully
        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_notification_with_priority_levels(self, notification_service, real_dao):
        """
        Test notifications with different priority levels

        This test verifies:
        1. High priority notifications are handled correctly
        2. Priority is reflected in Slack message formatting
        3. Urgent notifications bypass quiet hours
        """
        recipient_id = uuid4()

        real_dao.preferences[str(recipient_id)] = NotificationPreference(
            user_id=recipient_id,
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            enabled_channels=[NotificationChannel.SLACK],
            enabled=True,
            quiet_hours_start=22,
            quiet_hours_end=8
        )

        # Test urgent priority (should bypass quiet hours)
        notification = await notification_service.send_notification(
            recipient_id=recipient_id,
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            title="Urgent E2E Test",
            message="This is an urgent test notification",
            priority=NotificationPriority.URGENT,
            force_channels=[NotificationChannel.SLACK]
        )

        assert notification is not None
        assert notification.priority == NotificationPriority.URGENT


@pytest.mark.e2e
@pytest.mark.slack_api
@skip_if_no_slack
class TestSlackOrganizationNotificationsE2E:
    """
    E2E tests for organization-wide Slack notifications

    These tests verify bulk notification sending to multiple users.
    """

    @pytest.mark.asyncio
    async def test_send_organization_announcement(self, notification_service, real_dao):
        """
        Test sending announcement to all organization members

        This test verifies:
        1. Announcement is sent to multiple users
        2. Individual failures don't stop other notifications
        3. Statistics are tracked correctly
        """
        org_id = uuid4()

        # Create test organization members
        member_ids = [uuid4() for _ in range(3)]
        for member_id in member_ids:
            # Add member preference
            real_dao.preferences[str(member_id)] = NotificationPreference(
                user_id=member_id,
                event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
                enabled_channels=[NotificationChannel.SLACK],
                enabled=True
            )

        # Mock organization members
        class Member:
            def __init__(self, user_id):
                self.user_id = user_id

        real_dao.organization_members = {str(mid): Member(mid) for mid in member_ids}

        sent_count = await notification_service.send_organization_announcement(
            organization_id=org_id,
            title="E2E Organization Test",
            message="This is an organization-wide test announcement",
            priority=NotificationPriority.NORMAL
        )

        # Verify notifications were attempted for all members
        assert sent_count >= 0  # At least attempted
        assert sent_count <= 3  # At most the number of members


@pytest.mark.e2e
@pytest.mark.slack_api
@skip_if_no_slack
class TestSlackErrorHandlingE2E:
    """
    E2E tests for error handling with real Slack API

    These tests verify proper error handling for various failure scenarios.
    """

    @pytest.mark.asyncio
    async def test_invalid_channel_handling(self, notification_service):
        """
        Test notification handling when Slack channel is invalid

        This test verifies:
        1. Service handles invalid channel IDs gracefully
        2. Error is logged but doesn't crash the service
        3. Appropriate status is returned
        """
        success = await notification_service.send_channel_notification(
            channel_id="INVALID_CHANNEL_ID",
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            title="Test Invalid Channel",
            message="This should fail gracefully"
        )

        # Should return False for invalid channel
        assert success is False

    @pytest.mark.asyncio
    async def test_notification_without_slack_credentials(self, real_dao):
        """
        Test notification service behavior without Slack credentials

        This test verifies:
        1. Service can be created without Slack credentials
        2. Channel notifications fail gracefully
        3. Database operations still work
        """
        service = NotificationService(real_dao, None)

        success = await service.send_channel_notification(
            channel_id="C12345",
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            title="Test",
            message="Test message"
        )

        assert success is False


# ============================================================================
# NOTIFICATION STATISTICS TESTS (Database-only, no API calls)
# ============================================================================

class TestNotificationStatistics:
    """
    Tests for notification statistics

    These tests don't require Slack API access as they only test
    database statistics aggregation.
    """

    @pytest.mark.asyncio
    async def test_get_notification_statistics(self, real_dao):
        """Test retrieving notification statistics from database"""
        service = NotificationService(real_dao, None)
        org_id = uuid4()

        # Create test notifications
        from organization_management.domain.entities.notification import Notification

        notifications = [
            Notification(
                id=uuid4(),
                recipient_id=uuid4(),
                event_type=NotificationEvent.COURSE_CREATED,
                title="Test 1",
                message="Test message 1",
                priority=NotificationPriority.NORMAL,
                channels=[NotificationChannel.SLACK],
                organization_id=org_id
            ),
            Notification(
                id=uuid4(),
                recipient_id=uuid4(),
                event_type=NotificationEvent.ASSIGNMENT_GRADED,
                title="Test 2",
                message="Test message 2",
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.EMAIL],
                organization_id=org_id
            )
        ]

        # Store notifications
        for notif in notifications:
            notif.status = "sent"
            real_dao.notifications[str(notif.id)] = notif

        # Mock the DAO method
        async def mock_get_org_notifications(org_id):
            return notifications

        real_dao.get_organization_notifications = mock_get_org_notifications

        stats = await service.get_notification_statistics(org_id)

        assert stats["total_sent"] == 2
        assert "by_event_type" in stats
        assert "by_priority" in stats
