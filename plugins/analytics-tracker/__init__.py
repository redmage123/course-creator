"""
Analytics Tracker Plugin

BUSINESS CONTEXT:
Tracks detailed user analytics and provides learning insights.
Uses the advice system to wrap core functions with timing
and tracking capabilities.

FEATURES:
- Page view tracking
- Time spent analytics
- Learning pattern analysis
- Performance insights
- API response timing

DESIGN:
Uses around_advice to wrap API endpoints with timing.
Uses events for activity tracking.
Stores aggregated analytics for reporting.

@module analytics-tracker
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class UserSession:
    """
    Tracks a user's session activity.

    Aggregates events for analytics purposes.
    """
    user_id: str
    started_at: datetime = field(default_factory=datetime.now)
    events: List[Dict[str, Any]] = field(default_factory=list)
    page_views: int = 0
    time_on_content: float = 0.0
    quiz_attempts: int = 0

    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add an event to the session."""
        self.events.append({
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })


@dataclass
class LearningInsight:
    """
    A learning insight derived from analytics.

    Used to provide actionable feedback to users and instructors.
    """
    insight_type: str
    title: str
    description: str
    recommendations: List[str]
    confidence: float  # 0-1


class AnalyticsTracker:
    """
    Tracks and analyzes user learning behavior.

    BUSINESS VALUE:
    - Identifies learning patterns
    - Highlights struggling students
    - Optimizes content based on engagement
    - Provides data-driven insights
    """

    def __init__(self, api: Any, settings: Dict[str, Any]):
        """
        Initialize the analytics tracker.

        Args:
            api: PlatformAPI instance
            settings: Plugin settings
        """
        self.api = api
        self.track_page_views = settings.get('track_page_views', True)
        self.track_time = settings.get('track_time_spent', True)
        self.anonymize = settings.get('anonymize_data', False)
        self.enable_insights = settings.get('enable_insights', True)

        # In-memory session tracking (would use Redis in production)
        self.sessions: Dict[str, UserSession] = {}
        # Aggregated analytics
        self.content_views: Dict[str, int] = defaultdict(int)
        self.api_timings: Dict[str, List[float]] = defaultdict(list)

    def get_or_create_session(self, user_id: str) -> UserSession:
        """Get or create a session for user."""
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id=user_id)
        return self.sessions[user_id]

    def track_page_view(
        self,
        user_id: str,
        page: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Track a page view.

        Args:
            user_id: User viewing the page
            page: Page identifier
            metadata: Additional context
        """
        if not self.track_page_views:
            return

        session = self.get_or_create_session(user_id)
        session.page_views += 1
        session.add_event('page_view', {
            'page': page,
            'metadata': metadata or {}
        })

        # Track content popularity
        self.content_views[page] += 1

    def track_time_on_content(
        self,
        user_id: str,
        content_id: str,
        duration_seconds: float
    ) -> None:
        """
        Track time spent on content.

        Args:
            user_id: User ID
            content_id: Content identifier
            duration_seconds: Time spent
        """
        if not self.track_time:
            return

        session = self.get_or_create_session(user_id)
        session.time_on_content += duration_seconds
        session.add_event('time_on_content', {
            'content_id': content_id,
            'duration': duration_seconds
        })

    def track_api_timing(
        self,
        endpoint: str,
        duration_ms: float
    ) -> None:
        """
        Track API endpoint response time.

        Args:
            endpoint: API endpoint
            duration_ms: Response time in ms
        """
        self.api_timings[endpoint].append(duration_ms)

        # Keep only last 1000 samples
        if len(self.api_timings[endpoint]) > 1000:
            self.api_timings[endpoint] = self.api_timings[endpoint][-1000:]

    def get_api_stats(self, endpoint: str) -> Dict[str, float]:
        """
        Get API timing statistics.

        Args:
            endpoint: API endpoint

        Returns:
            Stats dict with avg, min, max, p95
        """
        timings = self.api_timings.get(endpoint, [])
        if not timings:
            return {}

        sorted_timings = sorted(timings)
        p95_idx = int(len(sorted_timings) * 0.95)

        return {
            'avg': sum(timings) / len(timings),
            'min': min(timings),
            'max': max(timings),
            'p95': sorted_timings[p95_idx] if p95_idx < len(sorted_timings) else max(timings),
            'count': len(timings)
        }

    def generate_user_insights(
        self,
        user_id: str
    ) -> List[LearningInsight]:
        """
        Generate learning insights for a user.

        Args:
            user_id: User to analyze

        Returns:
            List of insights
        """
        if not self.enable_insights:
            return []

        insights = []
        session = self.sessions.get(user_id)

        if not session:
            return insights

        # Analyze quiz performance
        quiz_events = [
            e for e in session.events
            if e['type'] == 'quiz_submitted'
        ]

        if quiz_events:
            avg_score = sum(
                e['data'].get('score', 0) for e in quiz_events
            ) / len(quiz_events)

            if avg_score < 60:
                insights.append(LearningInsight(
                    insight_type='struggling',
                    title='Quiz Performance',
                    description='Your recent quiz scores are below average.',
                    recommendations=[
                        'Review the course materials before attempting quizzes',
                        'Try the practice quizzes to build confidence',
                        'Consider reaching out to your instructor'
                    ],
                    confidence=0.85
                ))
            elif avg_score > 90:
                insights.append(LearningInsight(
                    insight_type='excelling',
                    title='Excellent Progress!',
                    description='You are performing exceptionally well.',
                    recommendations=[
                        'Consider helping peers in the discussion forum',
                        'Try advanced content or certifications',
                        'Explore related courses to expand your skills'
                    ],
                    confidence=0.90
                ))

        # Analyze time patterns
        if session.time_on_content > 0:
            avg_time_per_view = session.time_on_content / max(session.page_views, 1)

            if avg_time_per_view < 30:  # Less than 30 seconds
                insights.append(LearningInsight(
                    insight_type='rushing',
                    title='Learning Pace',
                    description='You may be moving through content quickly.',
                    recommendations=[
                        'Take time to absorb the material',
                        'Try taking notes as you learn',
                        'Review sections you find challenging'
                    ],
                    confidence=0.70
                ))

        return insights

    def get_popular_content(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular content by views.

        Args:
            limit: Max results

        Returns:
            List of content with view counts
        """
        sorted_content = sorted(
            self.content_views.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [
            {'content_id': k, 'views': v}
            for k, v in sorted_content[:limit]
        ]


# Global tracker instance
_tracker: Optional[AnalyticsTracker] = None


def activate(api: Any) -> None:
    """
    Activate the analytics tracker plugin.

    Sets up event subscriptions and advice for tracking.

    Args:
        api: PlatformAPI instance
    """
    global _tracker

    api.log.info("Analytics Tracker plugin activating...")

    # Create tracker
    settings = api.config.get_all()
    _tracker = AnalyticsTracker(api, settings)

    # Subscribe to user events
    @api.events.subscribe('user.login')
    async def on_login(event):
        """Track user login."""
        user_id = event.data.get('user_id')
        _tracker.get_or_create_session(user_id)
        api.log.debug(f"Session started for user {user_id}")

    @api.events.subscribe('user.logout')
    async def on_logout(event):
        """End user session tracking."""
        user_id = event.data.get('user_id')
        if user_id in _tracker.sessions:
            session = _tracker.sessions[user_id]
            api.log.info(
                f"Session ended for {user_id}: "
                f"{session.page_views} views, "
                f"{session.time_on_content}s on content"
            )
            # Would persist to database here
            del _tracker.sessions[user_id]

    # Track content views
    @api.events.subscribe('content.accessed')
    async def on_content_accessed(event):
        """Track content access."""
        _tracker.track_page_view(
            event.data.get('user_id'),
            event.data.get('content_id'),
            event.data
        )

    @api.events.subscribe('course.viewed')
    async def on_course_viewed(event):
        """Track course views."""
        _tracker.track_page_view(
            event.data.get('user_id'),
            f"course:{event.data.get('course_id')}",
            event.data
        )

    # Track video watching
    @api.events.subscribe('video.watched')
    async def on_video_watched(event):
        """Track video watch time."""
        _tracker.track_time_on_content(
            event.data.get('user_id'),
            event.data.get('video_id'),
            event.data.get('watch_duration', 0)
        )

    # Track quiz events
    @api.events.subscribe('quiz.submitted')
    async def on_quiz_submitted(event):
        """Track quiz submissions."""
        user_id = event.data.get('user_id')
        session = _tracker.get_or_create_session(user_id)
        session.quiz_attempts += 1
        session.add_event('quiz_submitted', event.data)

    # Track lab events
    @api.events.subscribe('lab.code_executed')
    async def on_code_executed(event):
        """Track code execution in labs."""
        user_id = event.data.get('user_id')
        session = _tracker.get_or_create_session(user_id)
        session.add_event('code_executed', {
            'language': event.data.get('language'),
            'success': event.data.get('success'),
            'execution_time': event.data.get('execution_time')
        })

    # Add around advice for API timing
    from plugin_system.core.advice import Advice

    advice = Advice.get_instance()

    def with_timing(original_func, *args, **kwargs):
        """Wrap function with timing."""
        start = time.time()
        try:
            return original_func(*args, **kwargs)
        finally:
            elapsed = (time.time() - start) * 1000  # Convert to ms
            endpoint = original_func.__qualname__
            _tracker.track_api_timing(endpoint, elapsed)

    # Apply timing to key service methods
    api.log.info("Analytics Tracker plugin activated")


def deactivate(api: Any) -> None:
    """
    Deactivate the analytics tracker.

    Args:
        api: PlatformAPI instance
    """
    global _tracker

    api.log.info("Analytics Tracker plugin deactivating...")

    # Persist any remaining session data
    if _tracker:
        for user_id, session in _tracker.sessions.items():
            api.log.info(f"Persisting session for {user_id}")
            # Would save to database

    _tracker = None
    api.log.info("Analytics Tracker plugin deactivated")


def get_tracker() -> Optional[AnalyticsTracker]:
    """Get the current tracker instance."""
    return _tracker


def get_user_insights(user_id: str) -> List[LearningInsight]:
    """
    Get learning insights for a user.

    Args:
        user_id: User ID

    Returns:
        List of insights
    """
    if _tracker:
        return _tracker.generate_user_insights(user_id)
    return []
