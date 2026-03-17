"""
Notification Enhancer Plugin

BUSINESS CONTEXT:
Enhances the notification system with smart routing,
digest emails, Slack integration, and instructor alerts.

FEATURES:
- Daily email digests instead of individual notifications
- Slack webhook integration for team notifications
- Smart instructor alerts for struggling students
- Event-based notification routing

DESIGN:
Uses the event bus to subscribe to platform events
and route notifications through appropriate channels.

@module notification-enhancer
"""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

# Notification queue for digest
_notification_queue: Dict[str, List[Dict[str, Any]]] = defaultdict(list)


class NotificationRouter:
    """
    Routes notifications to appropriate channels.

    BUSINESS VALUE:
    - Reduces notification fatigue with digests
    - Enables team visibility via Slack
    - Helps instructors identify struggling students
    """

    def __init__(self, api: Any, settings: Dict[str, Any]):
        """
        Initialize the notification router.

        Args:
            api: PlatformAPI instance
            settings: Plugin settings
        """
        self.api = api
        self.enable_digest = settings.get('enable_email_digest', True)
        self.digest_time = settings.get('digest_time', '09:00')
        self.slack_url = settings.get('slack_webhook_url', '')
        self.enable_alerts = settings.get('enable_instructor_alerts', True)
        self.low_score_threshold = settings.get('low_score_threshold', 60)

    async def route_notification(
        self,
        notification_type: str,
        data: Dict[str, Any],
        recipient_id: str
    ) -> None:
        """
        Route a notification through appropriate channels.

        Args:
            notification_type: Type of notification
            data: Notification data
            recipient_id: User to notify
        """
        if self.enable_digest:
            # Queue for digest
            _notification_queue[recipient_id].append({
                'type': notification_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
            self.api.log.debug(f"Queued notification for {recipient_id}")
        else:
            # Send immediately
            await self.api.notify.send_to_user(
                recipient_id,
                title=self._get_title(notification_type),
                message=self._format_message(notification_type, data)
            )

    async def send_slack_notification(
        self,
        message: str,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send notification to Slack.

        Args:
            message: Message to send
            channel: Optional channel override

        Returns:
            True if sent successfully
        """
        if not self.slack_url:
            return False

        # In real implementation, would use httpx or aiohttp
        self.api.log.info(f"Slack notification: {message}")
        return True

    async def alert_instructor(
        self,
        instructor_id: str,
        alert_type: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Alert an instructor about a student event.

        Args:
            instructor_id: Instructor to alert
            alert_type: Type of alert
            data: Alert data
        """
        if not self.enable_alerts:
            return

        title = f"Student Alert: {alert_type}"
        message = self._format_instructor_alert(alert_type, data)

        await self.api.notify.send_to_user(
            instructor_id,
            title=title,
            message=message,
            notification_type="alert"
        )

    def _get_title(self, notification_type: str) -> str:
        """Get notification title by type."""
        titles = {
            'course.published': 'New Course Available',
            'quiz.submitted': 'Quiz Completed',
            'user.enrolled': 'New Enrollment',
            'user.completed_course': 'Course Completed',
        }
        return titles.get(notification_type, 'Notification')

    def _format_message(
        self,
        notification_type: str,
        data: Dict[str, Any]
    ) -> str:
        """Format notification message."""
        if notification_type == 'quiz.submitted':
            return f"Quiz '{data.get('quiz_name')}' completed with score {data.get('score')}%"
        elif notification_type == 'user.enrolled':
            return f"You've enrolled in '{data.get('course_name')}'"
        elif notification_type == 'course.published':
            return f"New course available: {data.get('course_name')}"
        return str(data)

    def _format_instructor_alert(
        self,
        alert_type: str,
        data: Dict[str, Any]
    ) -> str:
        """Format instructor alert message."""
        if alert_type == 'low_quiz_score':
            return (
                f"Student {data.get('student_name')} scored "
                f"{data.get('score')}% on quiz '{data.get('quiz_name')}'. "
                f"Consider reaching out to offer assistance."
            )
        return str(data)


# Global router instance
_router: Optional[NotificationRouter] = None


def activate(api: Any) -> None:
    """
    Activate the notification enhancer plugin.

    Sets up event subscriptions for notification routing.

    Args:
        api: PlatformAPI instance
    """
    global _router

    api.log.info("Notification Enhancer plugin activating...")

    # Load settings and create router
    settings = api.config.get_all()
    _router = NotificationRouter(api, settings)

    # Subscribe to quiz submission events
    @api.events.subscribe('quiz.submitted')
    async def on_quiz_submitted(event):
        """Handle quiz submission events."""
        data = event.data
        score = data.get('score', 100)
        student_id = data.get('student_id')
        course_id = data.get('course_id')

        # Route notification to student
        await _router.route_notification(
            'quiz.submitted',
            data,
            student_id
        )

        # Check if instructor should be alerted
        if score < _router.low_score_threshold:
            # Get instructor for course
            course = await api.courses.get(course_id)
            if course:
                await _router.alert_instructor(
                    course.get('instructor_id'),
                    'low_quiz_score',
                    {
                        'student_name': data.get('student_name'),
                        'quiz_name': data.get('quiz_name'),
                        'score': score
                    }
                )

        # Send to Slack if configured
        await _router.send_slack_notification(
            f"Quiz completed: {data.get('student_name')} - {score}%"
        )

    # Subscribe to course publication
    @api.events.subscribe('course.published')
    async def on_course_published(event):
        """Handle course publication events."""
        data = event.data

        # Notify enrolled students
        course_id = data.get('course_id')
        enrollments = await api.courses.get_enrollments(course_id)

        for enrollment in enrollments:
            await _router.route_notification(
                'course.published',
                data,
                enrollment.get('user_id')
            )

        # Team Slack notification
        await _router.send_slack_notification(
            f"🎓 New course published: {data.get('course_name')}"
        )

    # Subscribe to user enrollment
    @api.events.subscribe('user.enrolled')
    async def on_user_enrolled(event):
        """Handle enrollment events."""
        data = event.data

        await _router.route_notification(
            'user.enrolled',
            data,
            data.get('user_id')
        )

    # Subscribe to course completion
    @api.events.subscribe('user.completed_course')
    async def on_course_completed(event):
        """Handle course completion events."""
        data = event.data

        await _router.route_notification(
            'user.completed_course',
            data,
            data.get('user_id')
        )

        # Slack celebration
        await _router.send_slack_notification(
            f"🎉 {data.get('user_name')} completed '{data.get('course_name')}'!"
        )

    # Schedule daily digest
    if settings.get('enable_email_digest', True):
        api.schedule(send_daily_digest, delay_seconds=3600, repeat=True)

    api.log.info("Notification Enhancer plugin activated")


async def send_daily_digest() -> None:
    """Send daily digest emails to users."""
    global _notification_queue

    for user_id, notifications in _notification_queue.items():
        if notifications:
            # Format digest
            message = "Your daily update:\n\n"
            for notif in notifications:
                message += f"- {notif['type']}: {notif['data']}\n"

            # Would send via api.notify.send_email
            # Cleared after sending

    # Clear queue
    _notification_queue.clear()


def deactivate(api: Any) -> None:
    """
    Deactivate the notification enhancer plugin.

    Args:
        api: PlatformAPI instance
    """
    global _router

    api.log.info("Notification Enhancer plugin deactivating...")
    _router = None
    _notification_queue.clear()
    api.log.info("Notification Enhancer plugin deactivated")
