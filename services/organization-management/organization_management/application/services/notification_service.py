"""
Notification Service
Handles sending notifications through various channels (Slack, email, in-app, SMS)
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from organization_management.domain.entities.notification import (
    Notification,
    NotificationChannel,
    NotificationEvent,
    NotificationPreference,
    NotificationPriority,
    NotificationTemplate
)
from organization_management.infrastructure.integrations.slack_integration import (
    SlackCredentials,
    SlackIntegrationService
)
from organization_management.data_access.organization_dao import OrganizationManagementDAO


class NotificationService:
    """
    Service for managing and sending notifications across multiple channels

    BUSINESS CONTEXT:
    This service is the central hub for all platform notifications.
    It respects user preferences, handles multiple delivery channels,
    and provides analytics on notification delivery.
    """

    def __init__(
        self,
        organization_dao: OrganizationManagementDAO,
        slack_credentials: Optional[SlackCredentials] = None
    ):
        self._organization_dao = organization_dao
        self._slack_credentials = slack_credentials
        self._logger = logging.getLogger(__name__)

        # Default notification templates
        self._templates = self._initialize_default_templates()

    def _initialize_default_templates(self) -> Dict[NotificationEvent, Dict[NotificationChannel, NotificationTemplate]]:
        """
        Initialize default notification templates for all event types

        BUSINESS REQUIREMENT:
        Provides consistent, professional messaging across the platform
        """
        templates = {}

        # Course events
        templates[NotificationEvent.COURSE_CREATED] = {
            NotificationChannel.SLACK: NotificationTemplate(
                event_type=NotificationEvent.COURSE_CREATED,
                channel=NotificationChannel.SLACK,
                title_template="New Course Created: {{course_name}}",
                message_template="{{instructor_name}} has created a new course: {{course_name}}. Students can now enroll!",
                variables=["course_name", "instructor_name"]
            )
        }

        templates[NotificationEvent.ASSIGNMENT_DUE_SOON] = {
            NotificationChannel.SLACK: NotificationTemplate(
                event_type=NotificationEvent.ASSIGNMENT_DUE_SOON,
                channel=NotificationChannel.SLACK,
                title_template="Assignment Due Soon: {{assignment_name}}",
                message_template="Reminder: '{{assignment_name}}' is due on {{due_date}}. Don't forget to submit!",
                variables=["assignment_name", "due_date"]
            )
        }

        templates[NotificationEvent.ASSIGNMENT_GRADED] = {
            NotificationChannel.SLACK: NotificationTemplate(
                event_type=NotificationEvent.ASSIGNMENT_GRADED,
                channel=NotificationChannel.SLACK,
                title_template="Assignment Graded: {{assignment_name}}",
                message_template="Your assignment '{{assignment_name}}' has been graded. Score: {{score}}/{{max_score}}. {{feedback}}",
                variables=["assignment_name", "score", "max_score", "feedback"]
            )
        }

        templates[NotificationEvent.MEETING_SCHEDULED] = {
            NotificationChannel.SLACK: NotificationTemplate(
                event_type=NotificationEvent.MEETING_SCHEDULED,
                channel=NotificationChannel.SLACK,
                title_template="Meeting Scheduled: {{meeting_name}}",
                message_template="A meeting has been scheduled: {{meeting_name}} on {{meeting_date}} at {{meeting_time}}. Join URL: {{join_url}}",
                variables=["meeting_name", "meeting_date", "meeting_time", "join_url"]
            )
        }

        templates[NotificationEvent.INSTRUCTOR_ADDED] = {
            NotificationChannel.SLACK: NotificationTemplate(
                event_type=NotificationEvent.INSTRUCTOR_ADDED,
                channel=NotificationChannel.SLACK,
                title_template="New Instructor Added",
                message_template="{{instructor_name}} has been added as an instructor to {{organization_name}}.",
                variables=["instructor_name", "organization_name"]
            )
        }

        templates[NotificationEvent.CERTIFICATE_EARNED] = {
            NotificationChannel.SLACK: NotificationTemplate(
                event_type=NotificationEvent.CERTIFICATE_EARNED,
                channel=NotificationChannel.SLACK,
                title_template="Congratulations! Certificate Earned",
                message_template="{{student_name}} has earned a certificate for completing {{course_name}}!",
                variables=["student_name", "course_name"]
            )
        }

        return templates

    async def send_notification(
        self,
        recipient_id: UUID,
        event_type: NotificationEvent,
        organization_id: Optional[UUID] = None,
        variables: Optional[Dict[str, str]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        force_channels: Optional[List[NotificationChannel]] = None
    ) -> Notification:
        """
        Send notification to a user

        BUSINESS REQUIREMENT:
        Respects user preferences unless force_channels is specified
        Supports multiple delivery channels
        Logs all notifications for audit trail
        """
        try:
            # Get user preferences
            preferences = await self._get_user_preferences(recipient_id, event_type)

            # Determine channels
            if force_channels:
                channels = force_channels
            elif preferences:
                channels = [
                    ch for ch in preferences.enabled_channels
                    if preferences.should_send_notification(ch)
                ]
            else:
                # Default to Slack if no preferences
                channels = [NotificationChannel.SLACK]

            # Get template and render message
            template = self._get_template(event_type, NotificationChannel.SLACK)
            if template and variables:
                title = template.render_title(variables)
                message = template.render_message(variables)
            else:
                title = f"Notification: {event_type.value}"
                message = "You have a new notification."

            # Create notification entity
            notification = Notification(
                event_type=event_type,
                recipient_id=recipient_id,
                organization_id=organization_id,
                title=title,
                message=message,
                priority=priority,
                channels=channels,
                metadata=variables or {}
            )

            if not notification.is_valid():
                raise ValueError("Invalid notification configuration")

            # Send through each channel
            for channel in channels:
                if channel == NotificationChannel.SLACK:
                    await self._send_slack_notification(notification)
                elif channel == NotificationChannel.EMAIL:
                    await self._send_email_notification(notification)
                elif channel == NotificationChannel.IN_APP:
                    await self._send_in_app_notification(notification)

            notification.mark_as_sent()

            # Save to database
            saved_notification = await self._organization_dao.create_notification(notification)

            self._logger.info(f"Sent notification {notification.id} to user {recipient_id}")
            return saved_notification

        except Exception as e:
            self._logger.error(f"Failed to send notification: {e}")
            raise

    async def send_channel_notification(
        self,
        channel_id: str,
        event_type: NotificationEvent,
        title: str,
        message: str,
        organization_id: Optional[UUID] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> bool:
        """
        Send notification to a Slack channel (not to individual user)

        BUSINESS CONTEXT:
        Used for organization-wide announcements, course updates,
        and team notifications
        """
        try:
            if not self._slack_credentials:
                self._logger.warning("Slack credentials not configured")
                return False

            # Determine color based on priority
            color_map = {
                NotificationPriority.LOW: "#36a64f",      # green
                NotificationPriority.NORMAL: "#2196F3",   # blue
                NotificationPriority.HIGH: "#ff9800",     # orange
                NotificationPriority.URGENT: "#f44336"    # red
            }
            color = color_map.get(priority, "#2196F3")

            async with SlackIntegrationService(self._slack_credentials) as slack:
                success = await slack.send_notification(channel_id, title, message, color)

            if success:
                self._logger.info(f"Sent channel notification to {channel_id}")

            return success

        except Exception as e:
            self._logger.error(f"Failed to send channel notification: {e}")
            return False

    async def send_organization_announcement(
        self,
        organization_id: UUID,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> int:
        """
        Send announcement to all members of an organization

        BUSINESS CONTEXT:
        Used for organization-wide announcements, system updates,
        policy changes, etc.
        """
        try:
            # Get all users in organization
            members = await self._organization_dao.get_organization_members(organization_id)

            sent_count = 0
            for member in members:
                try:
                    await self.send_notification(
                        recipient_id=member.user_id,
                        event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
                        organization_id=organization_id,
                        variables={"title": title, "message": message},
                        priority=priority
                    )
                    sent_count += 1
                except Exception as e:
                    self._logger.warning(f"Failed to notify user {member.user_id}: {e}")

            self._logger.info(f"Sent organization announcement to {sent_count} users")
            return sent_count

        except Exception as e:
            self._logger.error(f"Failed to send organization announcement: {e}")
            return 0

    async def send_instructor_room_notification(
        self,
        instructor_id: UUID,
        room_id: UUID,
        room_name: str,
        join_url: str,
        organization_id: UUID
    ) -> bool:
        """
        Notify instructor about their new meeting room

        BUSINESS CONTEXT:
        When org admin creates a room for an instructor, the instructor
        should be notified with the room details and join URL
        """
        try:
            variables = {
                "room_name": room_name,
                "join_url": join_url
            }

            await self.send_notification(
                recipient_id=instructor_id,
                event_type=NotificationEvent.MEETING_ROOM_CREATED,
                organization_id=organization_id,
                variables=variables,
                priority=NotificationPriority.NORMAL
            )

            return True

        except Exception as e:
            self._logger.error(f"Failed to send instructor room notification: {e}")
            return False

    async def send_track_room_notification(
        self,
        track_id: UUID,
        room_name: str,
        join_url: str,
        organization_id: UUID
    ) -> int:
        """
        Notify all students and instructors in a track about new meeting room

        BUSINESS CONTEXT:
        When org admin creates a room for a track, all participants
        should be notified
        """
        try:
            # Get all users assigned to track
            assignments = await self._organization_dao.get_track_assignments(track_id)

            sent_count = 0
            for assignment in assignments:
                try:
                    variables = {
                        "room_name": room_name,
                        "join_url": join_url
                    }

                    await self.send_notification(
                        recipient_id=assignment.user_id,
                        event_type=NotificationEvent.MEETING_ROOM_CREATED,
                        organization_id=organization_id,
                        variables=variables,
                        priority=NotificationPriority.NORMAL
                    )
                    sent_count += 1
                except Exception as e:
                    self._logger.warning(f"Failed to notify user {assignment.user_id}: {e}")

            self._logger.info(f"Sent track room notification to {sent_count} users")
            return sent_count

        except Exception as e:
            self._logger.error(f"Failed to send track room notification: {e}")
            return 0

    async def _send_slack_notification(self, notification: Notification) -> bool:
        """Send notification via Slack"""
        if not self._slack_credentials:
            self._logger.warning("Slack credentials not configured")
            return False

        try:
            # Get user's Slack channel/DM ID from database
            user_slack_id = await self._get_user_slack_id(notification.recipient_id)
            if not user_slack_id:
                self._logger.warning(f"No Slack ID found for user {notification.recipient_id}")
                return False

            # Determine color based on priority
            color_map = {
                NotificationPriority.LOW: "#36a64f",      # green
                NotificationPriority.NORMAL: "#2196F3",   # blue
                NotificationPriority.HIGH: "#ff9800",     # orange
                NotificationPriority.URGENT: "#f44336"    # red
            }
            color = color_map.get(notification.priority, "#2196F3")

            async with SlackIntegrationService(self._slack_credentials) as slack:
                success = await slack.send_notification(
                    user_slack_id,
                    notification.title,
                    notification.message,
                    color
                )

            return success

        except Exception as e:
            self._logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def _send_email_notification(self, notification: Notification) -> bool:
        """
        Send notification via email

        TODO: Implement email integration
        """
        self._logger.info(f"Email notification not yet implemented: {notification.id}")
        return False

    async def _send_in_app_notification(self, notification: Notification) -> bool:
        """Send notification to in-app notification center"""
        try:
            # Save to database for in-app display
            await self._organization_dao.create_notification(notification)
            return True
        except Exception as e:
            self._logger.error(f"Failed to save in-app notification: {e}")
            return False

    async def _get_user_preferences(
        self,
        user_id: UUID,
        event_type: NotificationEvent
    ) -> Optional[NotificationPreference]:
        """Get user notification preferences for event type"""
        try:
            return await self._organization_dao.get_notification_preference(user_id, event_type)
        except Exception as e:
            self._logger.warning(f"Failed to get user preferences: {e}")
            return None

    async def _get_user_slack_id(self, user_id: UUID) -> Optional[str]:
        """Get user's Slack ID from database"""
        try:
            user = await self._organization_dao.get_user_by_id(user_id)
            if user and hasattr(user, 'slack_id'):
                return user.slack_id
            return None
        except Exception as e:
            self._logger.warning(f"Failed to get user Slack ID: {e}")
            return None

    def _get_template(
        self,
        event_type: NotificationEvent,
        channel: NotificationChannel
    ) -> Optional[NotificationTemplate]:
        """Get notification template for event type and channel"""
        if event_type in self._templates:
            return self._templates[event_type].get(channel)
        return None

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications for user

        BUSINESS CONTEXT:
        Supports in-app notification center
        """
        try:
            return await self._organization_dao.get_user_notifications(
                user_id,
                unread_only,
                limit
            )
        except Exception as e:
            self._logger.error(f"Failed to get user notifications: {e}")
            return []

    async def mark_notification_read(self, notification_id: UUID) -> bool:
        """Mark notification as read"""
        try:
            notification = await self._organization_dao.get_notification_by_id(notification_id)
            if not notification:
                return False

            notification.mark_as_read()
            await self._organization_dao.update_notification(notification)

            return True
        except Exception as e:
            self._logger.error(f"Failed to mark notification read: {e}")
            return False

    async def get_notification_statistics(self, organization_id: UUID) -> Dict:
        """
        Get notification statistics for organization

        BUSINESS CONTEXT:
        Provides insights into notification effectiveness and user engagement
        """
        try:
            notifications = await self._organization_dao.get_organization_notifications(organization_id)

            stats = {
                "total_sent": len(notifications),
                "by_event_type": {},
                "by_priority": {},
                "by_status": {},
                "read_rate": 0.0
            }

            for notification in notifications:
                # Count by event type
                event_key = notification.event_type.value
                stats["by_event_type"][event_key] = stats["by_event_type"].get(event_key, 0) + 1

                # Count by priority
                priority_key = notification.priority.value
                stats["by_priority"][priority_key] = stats["by_priority"].get(priority_key, 0) + 1

                # Count by status
                status_key = notification.status
                stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1

            # Calculate read rate
            if stats["total_sent"] > 0:
                read_count = stats["by_status"].get("read", 0)
                stats["read_rate"] = (read_count / stats["total_sent"]) * 100

            return stats

        except Exception as e:
            self._logger.error(f"Failed to get notification statistics: {e}")
            return {}
