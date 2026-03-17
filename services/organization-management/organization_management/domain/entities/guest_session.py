"""
Guest Session Entity - Time-Limited Demo Sessions for Unauthenticated Users

BUSINESS REQUIREMENT:
Guest users need time-limited sessions to explore the platform demo service
without registration. Sessions track usage, enforce rate limits, and collect
conversion analytics to optimize the sales funnel.

TECHNICAL REQUIREMENTS:
- 30-minute session expiration after creation
- Rate limiting: 10 AI assistant requests per session
- Conversion tracking: record which features were viewed
- Automatic session cleanup on expiration
- Analytics export for marketing optimization
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID, uuid4


@dataclass
class GuestSession:
    """
    Guest Session Entity

    BUSINESS CONTEXT:
    Represents a time-limited demo session for an unauthenticated guest user.
    Sessions are created automatically when users visit the platform and expire
    after 30 minutes of inactivity to encourage registration.

    TECHNICAL IMPLEMENTATION:
    - Stateless session tracking with UUID
    - Client-side session ID stored in browser (cookie or localStorage)
    - Server-side validation of session expiration and rate limits
    - Analytics data collected for conversion funnel optimization
    """

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default=None)
    last_activity_at: datetime = field(default_factory=datetime.utcnow)

    # Rate limiting for AI assistant
    ai_requests_count: int = 0
    ai_requests_limit: int = 10

    # Conversion tracking
    features_viewed: List[str] = field(default_factory=list)

    # Session metadata
    ip_address: str = None
    user_agent: str = None

    # Enhanced chatbot features (v3.3.0)
    user_profile: Dict[str, Any] = field(default_factory=dict)  # role, pain_points, interests, etc.
    conversation_mode: str = 'initial'  # initial, onboarding, exploration, demo
    is_returning_guest: bool = False  # Recognized from previous session
    communication_style: str = 'unknown'  # technical, business, casual

    def __post_init__(self):
        """Initialize session with 30-minute expiration"""
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(minutes=30)

    def is_expired(self) -> bool:
        """
        Check if session has expired

        BUSINESS REQUIREMENT:
        Sessions expire after 30 minutes to encourage registration.
        Expired sessions cannot be used for demo access.

        TECHNICAL IMPLEMENTATION:
        Compare current time with expires_at timestamp.
        """
        return datetime.utcnow() >= self.expires_at

    def renew(self) -> None:
        """
        Renew session expiration

        BUSINESS REQUIREMENT:
        Active sessions can be extended when users interact with demo features.
        This provides a better user experience while still encouraging registration.

        TECHNICAL IMPLEMENTATION:
        Reset expires_at to 30 minutes from current time.
        Update last_activity_at to track engagement.
        """
        self.expires_at = datetime.utcnow() + timedelta(minutes=30)
        self.last_activity_at = datetime.utcnow()

    def has_ai_requests_remaining(self) -> bool:
        """
        Check if guest has AI assistant requests remaining

        BUSINESS REQUIREMENT:
        Guests are limited to 10 AI questions per session to prevent abuse
        and encourage registration for unlimited access.

        TECHNICAL IMPLEMENTATION:
        Compare ai_requests_count with ai_requests_limit (default 10).
        """
        return self.ai_requests_count < self.ai_requests_limit

    def increment_ai_requests(self) -> None:
        """
        Increment AI request counter

        BUSINESS REQUIREMENT:
        Track AI assistant usage for rate limiting and conversion analytics.

        TECHNICAL IMPLEMENTATION:
        Increment counter and update last activity timestamp.
        """
        self.ai_requests_count += 1
        self.last_activity_at = datetime.utcnow()

    def record_feature_view(self, feature_name: str) -> None:
        """
        Record that guest viewed a specific feature

        BUSINESS REQUIREMENT:
        Track which demo features guests explore to optimize conversion funnel.
        Marketing team uses this data to understand which features drive registrations.

        TECHNICAL IMPLEMENTATION:
        Append feature name to features_viewed list.
        Common feature names:
        - 'ai_content_generation'
        - 'rag_knowledge_graph'
        - 'docker_labs'
        - 'analytics_dashboard'
        - 'course_catalog'
        - 'student_demo_workflow'
        - 'instructor_demo_workflow'
        """
        if feature_name not in self.features_viewed:
            self.features_viewed.append(feature_name)
        self.last_activity_at = datetime.utcnow()

    def to_analytics_dict(self) -> Dict[str, Any]:
        """
        Export session data for conversion analytics

        BUSINESS REQUIREMENT:
        Marketing team needs analytics data to track:
        - Which features drive registration conversions
        - How long guests engage before converting
        - AI assistant usage patterns
        - Geographic and device distribution

        TECHNICAL IMPLEMENTATION:
        Return dictionary with all tracking data for analytics pipeline.
        Includes conversion_score (0-10) based on engagement level.
        """
        # Calculate conversion score (0-10 scale)
        # Higher score = more engaged guest = higher conversion probability
        features_count = len(self.features_viewed)
        ai_engagement_bonus = 1 if self.ai_requests_count > 5 else 0
        conversion_score = min(10, features_count * 2 + ai_engagement_bonus)

        return {
            'session_id': str(self.id),
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_activity_at': self.last_activity_at.isoformat(),
            'duration_seconds': (self.last_activity_at - self.created_at).total_seconds(),
            'is_expired': self.is_expired(),
            'ai_requests_count': self.ai_requests_count,
            'ai_requests_limit': self.ai_requests_limit,
            'features_viewed': self.features_viewed,
            'features_count': features_count,
            'conversion_score': conversion_score,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session to dictionary representation

        BUSINESS REQUIREMENT:
        Session data needs to be serialized for API responses and storage.

        TECHNICAL IMPLEMENTATION:
        Return complete session state as dictionary for JSON serialization.
        """
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_activity_at': self.last_activity_at.isoformat(),
            'is_expired': self.is_expired(),
            'ai_requests_count': self.ai_requests_count,
            'ai_requests_limit': self.ai_requests_limit,
            'ai_requests_remaining': self.ai_requests_limit - self.ai_requests_count,
            'features_viewed': self.features_viewed,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
