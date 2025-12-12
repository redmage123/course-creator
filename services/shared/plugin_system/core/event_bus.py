"""
Event Bus - Async Event Pub/Sub System

BUSINESS CONTEXT:
Provides asynchronous event publishing and subscription for plugins.
Events are fired when significant things happen in the platform.

DESIGN PHILOSOPHY:
- Events are async to not block platform operations
- Subscribers can be sync or async
- Events carry typed data payloads
- Supports wildcards for event categories
- Thread-safe for concurrent access

EXAMPLE USAGE:
    # Subscribe to events
    @event_bus.subscribe('course.*')
    async def handle_course_events(event):
        print(f"Course event: {event.name}, data: {event.data}")

    # Publish an event
    await event_bus.publish(Event(
        name='course.created',
        data={'course_id': '123', 'name': 'Python Basics'}
    ))

@module event_bus
"""

import asyncio
import fnmatch
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """
    An event that occurred in the platform.

    Attributes:
        name: Event identifier (e.g., 'course.created', 'quiz.submitted')
        data: Event payload (any serializable data)
        timestamp: When the event occurred
        source: What generated the event (service name, plugin id)
        event_id: Unique identifier for this event instance
        organization_id: Optional organization context
        user_id: Optional user context
    """
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    event_id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'name': self.name,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'event_id': str(self.event_id),
            'organization_id': str(self.organization_id) if self.organization_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
        }


@dataclass
class EventSubscription:
    """
    A subscription to events matching a pattern.

    Attributes:
        pattern: Event name pattern (supports wildcards like 'course.*')
        handler: Function to call when event matches
        plugin_id: Plugin that created this subscription
        priority: Execution order (lower = earlier)
        is_async: Whether handler is async
    """
    pattern: str
    handler: Callable[[Event], Any]
    plugin_id: Optional[str] = None
    priority: int = 50
    is_async: bool = False

    def __post_init__(self):
        self.is_async = asyncio.iscoroutinefunction(self.handler)

    def matches(self, event_name: str) -> bool:
        """Check if this subscription matches an event name."""
        return fnmatch.fnmatch(event_name, self.pattern)


class EventBus:
    """
    Asynchronous event publish/subscribe system.

    BUSINESS VALUE:
    - Decouples platform components
    - Enables reactive plugin behavior
    - Supports event-driven architecture
    - Provides async event processing

    EVENT NAMING CONVENTION:
    Use dot-separated hierarchical names:
    - course.created, course.updated, course.deleted
    - quiz.submitted, quiz.graded
    - user.registered, user.logged_in
    - enrollment.created, enrollment.completed

    WILDCARDS:
    - 'course.*' - All course events
    - '*.created' - All creation events
    - '*' - All events (use sparingly)

    Example:
        bus = EventBus.get_instance()

        # Subscribe
        @bus.subscribe('enrollment.*')
        async def on_enrollment(event):
            await send_notification(event.data['student_id'])

        # Publish
        await bus.publish(Event(
            name='enrollment.created',
            data={'student_id': '123', 'course_id': '456'}
        ))
    """

    _instance: Optional['EventBus'] = None
    _lock = threading.Lock()

    def __init__(self):
        self._subscriptions: List[EventSubscription] = []
        self._sub_lock = threading.RLock()
        self._event_history: List[Event] = []
        self._history_limit = 1000

    @classmethod
    def get_instance(cls) -> 'EventBus':
        """Get the singleton EventBus instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def subscribe(
        self,
        pattern: str,
        handler: Optional[Callable[[Event], Any]] = None,
        *,
        priority: int = 50,
        plugin_id: Optional[str] = None
    ) -> Union[EventSubscription, Callable]:
        """
        Subscribe to events matching a pattern.

        Can be used as a decorator or called directly.

        Args:
            pattern: Event name pattern (supports wildcards)
            handler: Event handler function (optional for decorator)
            priority: Execution order (lower = earlier)
            plugin_id: Plugin identifier

        Returns:
            Subscription or decorator

        Example:
            # As decorator
            @bus.subscribe('course.*')
            async def handle_courses(event):
                pass

            # Direct call
            bus.subscribe('quiz.submitted', my_handler)
        """
        def create_subscription(fn: Callable) -> EventSubscription:
            sub = EventSubscription(
                pattern=pattern,
                handler=fn,
                plugin_id=plugin_id,
                priority=priority
            )

            with self._sub_lock:
                self._subscriptions.append(sub)
                self._subscriptions.sort(key=lambda s: s.priority)

            logger.debug(f"Subscribed to '{pattern}' (plugin={plugin_id})")
            return sub

        if handler is not None:
            return create_subscription(handler)

        def decorator(fn: Callable) -> Callable:
            create_subscription(fn)
            return fn

        return decorator

    def unsubscribe(self, subscription: EventSubscription) -> bool:
        """
        Remove a subscription.

        Args:
            subscription: Subscription to remove

        Returns:
            True if found and removed
        """
        with self._sub_lock:
            if subscription in self._subscriptions:
                self._subscriptions.remove(subscription)
                return True
        return False

    def unsubscribe_plugin(self, plugin_id: str) -> int:
        """
        Remove all subscriptions for a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Number of subscriptions removed
        """
        with self._sub_lock:
            original = len(self._subscriptions)
            self._subscriptions = [
                s for s in self._subscriptions
                if s.plugin_id != plugin_id
            ]
            removed = original - len(self._subscriptions)

        if removed > 0:
            logger.debug(f"Removed {removed} subscriptions for plugin {plugin_id}")
        return removed

    async def publish(self, event: Event) -> List[Any]:
        """
        Publish an event to all matching subscribers.

        Args:
            event: Event to publish

        Returns:
            List of handler results
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._history_limit:
            self._event_history = self._event_history[-self._history_limit:]

        # Find matching subscriptions
        with self._sub_lock:
            matching = [s for s in self._subscriptions if s.matches(event.name)]

        logger.debug(f"Publishing event '{event.name}' to {len(matching)} subscribers")

        results = []
        for sub in matching:
            try:
                if sub.is_async:
                    result = await sub.handler(event)
                else:
                    result = sub.handler(event)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in event handler for '{event.name}': {e}")

        return results

    def publish_sync(self, event: Event) -> None:
        """
        Publish an event without waiting (fire-and-forget).

        Creates a task for async handlers.

        Args:
            event: Event to publish
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.publish(event))
        except RuntimeError:
            # No running loop, run synchronously
            asyncio.run(self.publish(event))

    def get_subscriptions(
        self,
        pattern: Optional[str] = None,
        plugin_id: Optional[str] = None
    ) -> List[EventSubscription]:
        """
        List subscriptions with optional filtering.

        Args:
            pattern: Filter by pattern
            plugin_id: Filter by plugin

        Returns:
            List of matching subscriptions
        """
        with self._sub_lock:
            subs = self._subscriptions.copy()

        if pattern:
            subs = [s for s in subs if s.pattern == pattern]
        if plugin_id:
            subs = [s for s in subs if s.plugin_id == plugin_id]

        return subs

    def get_recent_events(
        self,
        name_pattern: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get recent events from history.

        Args:
            name_pattern: Filter by event name pattern
            limit: Maximum events to return

        Returns:
            List of recent events
        """
        events = self._event_history.copy()

        if name_pattern:
            events = [e for e in events if fnmatch.fnmatch(e.name, name_pattern)]

        return events[-limit:]


# Predefined platform events
class PlatformEvents:
    """
    Constants for platform event names.

    Use these to ensure consistent event naming.
    """

    # Course events
    COURSE_CREATED = 'course.created'
    COURSE_UPDATED = 'course.updated'
    COURSE_DELETED = 'course.deleted'
    COURSE_PUBLISHED = 'course.published'

    # Enrollment events
    ENROLLMENT_CREATED = 'enrollment.created'
    ENROLLMENT_COMPLETED = 'enrollment.completed'
    ENROLLMENT_DROPPED = 'enrollment.dropped'

    # Quiz events
    QUIZ_STARTED = 'quiz.started'
    QUIZ_SUBMITTED = 'quiz.submitted'
    QUIZ_GRADED = 'quiz.graded'
    QUIZ_PASSED = 'quiz.passed'
    QUIZ_FAILED = 'quiz.failed'

    # Lab events
    LAB_STARTED = 'lab.started'
    LAB_COMPLETED = 'lab.completed'
    LAB_ENVIRONMENT_CREATED = 'lab.environment.created'
    LAB_ENVIRONMENT_DESTROYED = 'lab.environment.destroyed'

    # User events
    USER_REGISTERED = 'user.registered'
    USER_LOGGED_IN = 'user.logged_in'
    USER_LOGGED_OUT = 'user.logged_out'
    USER_PROFILE_UPDATED = 'user.profile.updated'

    # Content events
    CONTENT_GENERATED = 'content.generated'
    SLIDE_CREATED = 'slide.created'
    VIDEO_UPLOADED = 'video.uploaded'

    # AI Assistant events
    AI_QUERY = 'ai.query'
    AI_RESPONSE = 'ai.response'

    # Progress events
    PROGRESS_UPDATED = 'progress.updated'
    CERTIFICATE_EARNED = 'certificate.earned'

    # Organization events
    ORGANIZATION_CREATED = 'organization.created'
    MEMBER_ADDED = 'organization.member.added'
    MEMBER_REMOVED = 'organization.member.removed'

    # Project/Track events
    PROJECT_CREATED = 'project.created'
    TRACK_CREATED = 'track.created'
    TRACK_ENROLLMENT = 'track.enrollment'
