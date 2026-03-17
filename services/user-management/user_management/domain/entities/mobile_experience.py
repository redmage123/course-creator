"""
Mobile Experience Domain Entities

What: Domain entities for mobile experience and responsive design features.
Where: User Management service domain layer.
Why: Provides:
     1. Device preference management
     2. Mobile session tracking
     3. Offline content synchronization
     4. Push notification configuration
     5. Touch gesture customization
     6. Bandwidth optimization settings
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


# ============================================================================
# ENUMS
# ============================================================================

class DeviceType(str, Enum):
    """
    What: Device type categories.
    Where: Device preference identification.
    Why: Enables device-specific UI optimization.
    """
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WATCH = "watch"
    TV = "tv"


class Theme(str, Enum):
    """
    What: UI theme options.
    Where: User interface preference.
    Why: Supports user visual preferences.
    """
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"
    HIGH_CONTRAST = "high_contrast"


class FontSize(str, Enum):
    """
    What: Font size preference options.
    Where: Accessibility settings.
    Why: Supports visual accessibility needs.
    """
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


class NavigationType(str, Enum):
    """
    What: Navigation style options.
    Where: UI navigation preference.
    Why: Enables device-appropriate navigation.
    """
    BOTTOM_TABS = "bottom_tabs"
    SIDEBAR = "sidebar"
    HAMBURGER = "hamburger"
    AUTO = "auto"


class VideoQuality(str, Enum):
    """
    What: Video quality preference options.
    Where: Content delivery settings.
    Why: Enables bandwidth-aware video streaming.
    """
    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FOUR_K = "4k"


class ImageQuality(str, Enum):
    """
    What: Image quality preference options.
    Where: Content delivery settings.
    Why: Enables bandwidth-aware image loading.
    """
    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Platform(str, Enum):
    """
    What: Mobile platform types.
    Where: Mobile session identification.
    Why: Enables platform-specific analytics.
    """
    IOS = "ios"
    ANDROID = "android"
    PWA = "pwa"
    MOBILE_WEB = "mobile_web"


class ConnectionType(str, Enum):
    """
    What: Network connection types.
    Where: Bandwidth optimization.
    Why: Enables connection-aware content delivery.
    """
    WIFI = "wifi"
    FIVE_G = "5g"
    FOUR_G = "4g"
    THREE_G = "3g"
    TWO_G = "2g"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class SyncStatus(str, Enum):
    """
    What: Offline content sync status.
    Where: Offline sync management.
    Why: Tracks content availability offline.
    """
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    SYNCING = "syncing"
    SYNCED = "synced"
    ERROR = "error"
    EXPIRED = "expired"
    DELETED = "deleted"


class ContentType(str, Enum):
    """
    What: Offline content types.
    Where: Content synchronization.
    Why: Categorizes downloadable content.
    """
    COURSE = "course"
    MODULE = "module"
    LESSON = "lesson"
    QUIZ = "quiz"
    LAB = "lab"
    VIDEO = "video"
    DOCUMENT = "document"
    SLIDE = "slide"


class NotificationCategory(str, Enum):
    """
    What: Push notification categories.
    Where: Notification settings.
    Why: Enables granular notification control.
    """
    COURSE_UPDATES = "course_updates"
    QUIZ_REMINDERS = "quiz_reminders"
    ASSIGNMENT_DEADLINES = "assignment_deadlines"
    DISCUSSION_REPLIES = "discussion_replies"
    INSTRUCTOR_MESSAGES = "instructor_messages"
    CERTIFICATE_EARNED = "certificate_earned"
    NEW_CONTENT = "new_content_available"
    PROMOTIONS = "promotion_offers"
    SYSTEM = "system_announcements"


class NotificationPriority(str, Enum):
    """
    What: Notification priority levels.
    Where: Push notification delivery.
    Why: Enables priority-based delivery.
    """
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DeliveryStatus(str, Enum):
    """
    What: Notification delivery status.
    Where: Notification tracking.
    Why: Tracks notification delivery lifecycle.
    """
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class CacheContentType(str, Enum):
    """
    What: Cacheable content types.
    Where: Content caching.
    Why: Categorizes cached resources.
    """
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    DATA = "data"
    STYLE = "style"
    SCRIPT = "script"


class CacheQuality(str, Enum):
    """
    What: Cached content quality variants.
    Where: Responsive content delivery.
    Why: Enables device-appropriate assets.
    """
    THUMBNAIL = "thumbnail"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ORIGINAL = "original"


class Breakpoint(str, Enum):
    """
    What: Responsive breakpoint categories.
    Where: Responsive analytics.
    Why: Enables breakpoint-based analysis.
    """
    XS = "xs"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"
    XXL = "2xl"


class Orientation(str, Enum):
    """
    What: Device orientation.
    Where: Responsive analytics.
    Why: Tracks orientation usage patterns.
    """
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class UserDevicePreference:
    """
    What: User device preference settings.
    Where: Stored per user per device.
    Why: Enables personalized responsive experience.
    """
    user_id: UUID
    device_id: str
    device_type: DeviceType

    # Device info
    device_name: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    browser_name: Optional[str] = None
    browser_version: Optional[str] = None
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    pixel_ratio: Optional[Decimal] = None

    # UI preferences
    preferred_theme: Theme = Theme.SYSTEM
    font_size_preference: FontSize = FontSize.MEDIUM
    reduced_motion: bool = False
    high_contrast: bool = False
    compact_mode: bool = False

    # Navigation
    sidebar_collapsed: bool = False
    preferred_navigation: NavigationType = NavigationType.AUTO
    gesture_navigation: bool = True
    haptic_feedback: bool = True

    # Content
    data_saver_mode: bool = False
    auto_play_video: bool = True
    video_quality_preference: VideoQuality = VideoQuality.AUTO
    image_quality_preference: ImageQuality = ImageQuality.AUTO

    # Offline
    offline_enabled: bool = True
    max_offline_storage_mb: int = 1000
    auto_download_wifi_only: bool = True

    is_primary_device: bool = False
    last_active_at: Optional[datetime] = None
    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate device preference data."""
        if not self.device_id:
            raise ValueError("Device ID is required")
        if self.screen_width is not None and self.screen_width <= 0:
            raise ValueError("Screen width must be positive")
        if self.screen_height is not None and self.screen_height <= 0:
            raise ValueError("Screen height must be positive")
        if self.max_offline_storage_mb < 0:
            raise ValueError("Max offline storage must be non-negative")

    def get_breakpoint(self) -> Optional[Breakpoint]:
        """
        What: Determine responsive breakpoint from screen width.
        Where: UI rendering decisions.
        Why: Enables breakpoint-based component selection.
        """
        if not self.screen_width:
            return None
        if self.screen_width < 640:
            return Breakpoint.XS
        if self.screen_width < 768:
            return Breakpoint.SM
        if self.screen_width < 1024:
            return Breakpoint.MD
        if self.screen_width < 1280:
            return Breakpoint.LG
        if self.screen_width < 1536:
            return Breakpoint.XL
        return Breakpoint.XXL

    def should_reduce_quality(self) -> bool:
        """
        What: Check if content quality should be reduced.
        Where: Content loading decisions.
        Why: Respects data saver and quality settings.
        """
        return self.data_saver_mode or self.video_quality_preference == VideoQuality.LOW

    def get_orientation(self) -> Optional[Orientation]:
        """
        What: Determine device orientation.
        Where: Layout decisions.
        Why: Enables orientation-specific layouts.
        """
        if not self.screen_width or not self.screen_height:
            return None
        return Orientation.LANDSCAPE if self.screen_width > self.screen_height else Orientation.PORTRAIT


@dataclass
class MobileSession:
    """
    What: Mobile app session data.
    Where: Session tracking for analytics.
    Why: Enables mobile-specific usage analytics.
    """
    session_token: str
    platform: Platform

    user_id: Optional[UUID] = None
    device_preference_id: Optional[UUID] = None

    # App info
    app_version: Optional[str] = None
    build_number: Optional[str] = None

    # Connection
    connection_type: Optional[ConnectionType] = None
    ip_address: Optional[str] = None
    country_code: Optional[str] = None
    timezone: Optional[str] = None

    # Session metrics
    session_start: datetime = field(default_factory=datetime.now)
    session_end: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    screen_views: int = 0
    interactions: int = 0

    # Performance
    app_launch_time_ms: Optional[int] = None
    avg_screen_load_time_ms: Optional[int] = None
    memory_warnings: int = 0
    crashes: int = 0

    # Engagement
    content_items_viewed: int = 0
    videos_watched: int = 0
    quizzes_taken: int = 0
    labs_started: int = 0

    is_background: bool = False
    is_offline: bool = False

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate session data."""
        if not self.session_token:
            raise ValueError("Session token is required")

    def end_session(self) -> None:
        """
        What: End the mobile session.
        Where: Session cleanup.
        Why: Calculates final session metrics.
        """
        self.session_end = datetime.now()
        if self.session_start:
            delta = self.session_end - self.session_start
            self.duration_seconds = int(delta.total_seconds())

    def record_screen_view(self) -> None:
        """Increment screen view count."""
        self.screen_views += 1

    def record_interaction(self) -> None:
        """Increment interaction count."""
        self.interactions += 1

    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.session_end is None and not self.is_background

    def get_engagement_score(self) -> Decimal:
        """
        What: Calculate session engagement score.
        Where: Analytics dashboard.
        Why: Measures session quality.
        """
        if not self.duration_seconds or self.duration_seconds == 0:
            return Decimal("0")

        score = Decimal("0")
        # Weight different engagement types
        score += Decimal(self.screen_views) * Decimal("1")
        score += Decimal(self.content_items_viewed) * Decimal("5")
        score += Decimal(self.videos_watched) * Decimal("10")
        score += Decimal(self.quizzes_taken) * Decimal("15")
        score += Decimal(self.labs_started) * Decimal("20")

        # Normalize by duration (per minute)
        minutes = Decimal(self.duration_seconds) / Decimal("60")
        if minutes > 0:
            return round(score / minutes, 2)
        return score


@dataclass
class OfflineContentSync:
    """
    What: Offline content synchronization record.
    Where: Offline content management.
    Why: Enables learning continuity without internet.
    """
    user_id: UUID
    device_id: str
    content_type: ContentType
    content_id: UUID

    content_version: Optional[str] = None
    sync_status: SyncStatus = SyncStatus.PENDING
    sync_priority: int = 5

    # Storage
    storage_size_bytes: Optional[int] = None
    compressed_size_bytes: Optional[int] = None
    storage_path: Optional[str] = None
    checksum: Optional[str] = None

    # Timing
    queued_at: datetime = field(default_factory=datetime.now)
    download_started_at: Optional[datetime] = None
    download_completed_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Error handling
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None

    # Offline progress
    has_offline_progress: bool = False
    offline_progress_data: Optional[dict[str, Any]] = None
    progress_synced_at: Optional[datetime] = None

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate sync data."""
        if not self.device_id:
            raise ValueError("Device ID is required")
        if self.sync_priority < 1 or self.sync_priority > 10:
            raise ValueError("Sync priority must be between 1 and 10")

    def can_retry(self) -> bool:
        """Check if download can be retried."""
        return self.retry_count < self.max_retries

    def is_available_offline(self) -> bool:
        """Check if content is available offline."""
        return self.sync_status in (SyncStatus.DOWNLOADED, SyncStatus.SYNCED)

    def is_expired(self) -> bool:
        """Check if offline content has expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    def get_compression_ratio(self) -> Optional[Decimal]:
        """Calculate compression ratio."""
        if not self.storage_size_bytes or not self.compressed_size_bytes:
            return None
        if self.storage_size_bytes == 0:
            return None
        return round(
            Decimal(self.compressed_size_bytes) / Decimal(self.storage_size_bytes),
            4
        )

    def mark_downloading(self) -> None:
        """Mark content as downloading."""
        self.sync_status = SyncStatus.DOWNLOADING
        self.download_started_at = datetime.now()

    def mark_downloaded(self) -> None:
        """Mark content as downloaded."""
        self.sync_status = SyncStatus.DOWNLOADED
        self.download_completed_at = datetime.now()

    def mark_error(self, error: str) -> None:
        """Mark sync as failed with error."""
        self.sync_status = SyncStatus.ERROR
        self.last_error = error
        self.retry_count += 1


@dataclass
class PushNotificationSettings:
    """
    What: User push notification preferences.
    Where: Per-user per-device notification config.
    Why: Enables targeted, preference-respecting notifications.
    """
    user_id: UUID

    device_preference_id: Optional[UUID] = None

    # Tokens
    fcm_token: Optional[str] = None
    apns_token: Optional[str] = None
    web_push_endpoint: Optional[str] = None
    web_push_p256dh: Optional[str] = None
    web_push_auth: Optional[str] = None

    # Global settings
    notifications_enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    quiet_hours_timezone: Optional[str] = None

    # Categories
    course_updates: bool = True
    quiz_reminders: bool = True
    assignment_deadlines: bool = True
    discussion_replies: bool = True
    instructor_messages: bool = True
    certificate_earned: bool = True
    new_content_available: bool = True
    promotion_offers: bool = False
    system_announcements: bool = True

    # Delivery
    group_notifications: bool = True
    show_preview: bool = True
    sound_enabled: bool = True
    vibration_enabled: bool = True
    badge_count_enabled: bool = True

    # Frequency
    max_notifications_per_hour: int = 10
    digest_mode: bool = False
    digest_time: Optional[time] = None

    token_updated_at: Optional[datetime] = None
    last_notification_at: Optional[datetime] = None

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate notification settings."""
        if self.max_notifications_per_hour < 0:
            raise ValueError("Max notifications per hour must be non-negative")
        if self.quiet_hours_enabled:
            if not self.quiet_hours_start or not self.quiet_hours_end:
                raise ValueError("Quiet hours start and end required when enabled")

    def has_valid_token(self) -> bool:
        """Check if valid push token exists."""
        return bool(self.fcm_token or self.apns_token or self.web_push_endpoint)

    def is_category_enabled(self, category: NotificationCategory) -> bool:
        """Check if notification category is enabled."""
        category_map = {
            NotificationCategory.COURSE_UPDATES: self.course_updates,
            NotificationCategory.QUIZ_REMINDERS: self.quiz_reminders,
            NotificationCategory.ASSIGNMENT_DEADLINES: self.assignment_deadlines,
            NotificationCategory.DISCUSSION_REPLIES: self.discussion_replies,
            NotificationCategory.INSTRUCTOR_MESSAGES: self.instructor_messages,
            NotificationCategory.CERTIFICATE_EARNED: self.certificate_earned,
            NotificationCategory.NEW_CONTENT: self.new_content_available,
            NotificationCategory.PROMOTIONS: self.promotion_offers,
            NotificationCategory.SYSTEM: self.system_announcements,
        }
        return self.notifications_enabled and category_map.get(category, False)

    def is_quiet_hours(self, current_time: Optional[time] = None) -> bool:
        """
        What: Check if current time is within quiet hours.
        Where: Notification delivery logic.
        Why: Respects user quiet time preferences.
        """
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        check_time = current_time or datetime.now().time()

        # Handle overnight quiet hours
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= check_time <= self.quiet_hours_end
        else:
            return check_time >= self.quiet_hours_start or check_time <= self.quiet_hours_end

    def can_send_notification(self, category: NotificationCategory) -> bool:
        """Check if notification can be sent now."""
        if not self.notifications_enabled:
            return False
        if not self.is_category_enabled(category):
            return False
        if self.is_quiet_hours():
            return False
        return True


@dataclass
class PushNotification:
    """
    What: Push notification record.
    Where: Notification history tracking.
    Why: Enables notification analytics and debugging.
    """
    user_id: UUID
    title: str
    body: str
    category: NotificationCategory

    setting_id: Optional[UUID] = None
    priority: NotificationPriority = NotificationPriority.NORMAL

    # Targeting
    deep_link: Optional[str] = None
    action_type: Optional[str] = None
    action_data: Optional[dict[str, Any]] = None

    # Media
    image_url: Optional[str] = None
    icon_url: Optional[str] = None

    # Status
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    platform_message_id: Optional[str] = None

    # Interaction
    opened_at: Optional[datetime] = None
    action_taken: Optional[str] = None
    dismissed_at: Optional[datetime] = None

    # Error
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    # Timing
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    ttl_seconds: int = 86400
    expires_at: Optional[datetime] = None

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate notification data."""
        if not self.title or len(self.title) > 255:
            raise ValueError("Title is required and must be <= 255 characters")
        if not self.body:
            raise ValueError("Body is required")
        if self.ttl_seconds < 0:
            raise ValueError("TTL must be non-negative")

    def mark_sent(self, message_id: Optional[str] = None) -> None:
        """Mark notification as sent."""
        self.delivery_status = DeliveryStatus.SENT
        self.sent_at = datetime.now()
        self.platform_message_id = message_id
        self.expires_at = datetime.now() + timedelta(seconds=self.ttl_seconds)

    def mark_delivered(self) -> None:
        """Mark notification as delivered."""
        self.delivery_status = DeliveryStatus.DELIVERED
        self.delivered_at = datetime.now()

    def mark_failed(self, error_code: str, error_message: str) -> None:
        """Mark notification as failed."""
        self.delivery_status = DeliveryStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.retry_count += 1

    def mark_opened(self, action: Optional[str] = None) -> None:
        """Mark notification as opened."""
        self.opened_at = datetime.now()
        self.action_taken = action

    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    def was_engaged(self) -> bool:
        """Check if user engaged with notification."""
        return self.opened_at is not None


@dataclass
class MobileContentCache:
    """
    What: Cached mobile content variant.
    Where: CDN/cache management.
    Why: Enables efficient bandwidth-aware delivery.
    """
    content_type: CacheContentType
    content_id: UUID
    variant_key: str
    cache_url: str
    file_size_bytes: int

    variant_quality: Optional[CacheQuality] = None
    cdn_url: Optional[str] = None
    mime_type: Optional[str] = None

    # Optimization
    is_compressed: bool = False
    compression_ratio: Optional[Decimal] = None
    is_lazy_loadable: bool = True
    preload_priority: int = 5

    # Responsive
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[Decimal] = None

    # Validation
    etag: Optional[str] = None
    last_modified: Optional[datetime] = None
    cache_control: Optional[str] = None
    max_age_seconds: Optional[int] = None

    # Stats
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None

    expires_at: Optional[datetime] = None
    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate cache data."""
        if not self.variant_key:
            raise ValueError("Variant key is required")
        if not self.cache_url:
            raise ValueError("Cache URL is required")
        if self.file_size_bytes < 0:
            raise ValueError("File size must be non-negative")

    def record_access(self) -> None:
        """Record cache access."""
        self.access_count += 1
        self.last_accessed_at = datetime.now()

    def is_expired(self) -> bool:
        """Check if cache has expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    def is_stale(self) -> bool:
        """Check if cache might be stale based on max_age."""
        if not self.last_modified or not self.max_age_seconds:
            return False
        age = datetime.now() - self.last_modified
        return age.total_seconds() > self.max_age_seconds

    def get_size_kb(self) -> Decimal:
        """Get file size in KB."""
        return round(Decimal(self.file_size_bytes) / Decimal("1024"), 2)


@dataclass
class TouchGestureSettings:
    """
    What: Custom touch gesture mappings.
    Where: Per-user gesture customization.
    Why: Enables accessibility and personalization.
    """
    user_id: UUID

    device_preference_id: Optional[UUID] = None

    # Gesture actions
    swipe_left_action: str = "next_item"
    swipe_right_action: str = "previous_item"
    swipe_down_action: str = "refresh"
    swipe_up_action: str = "scroll_up"
    double_tap_action: str = "toggle_fullscreen"
    long_press_action: str = "context_menu"
    pinch_action: str = "zoom"
    two_finger_swipe_action: str = "navigate_back"

    # Sensitivity
    swipe_threshold_px: int = 50
    long_press_duration_ms: int = 500
    double_tap_interval_ms: int = 300
    scroll_sensitivity: Decimal = Decimal("1.0")

    # Accessibility
    gesture_feedback_enabled: bool = True
    gesture_hints_enabled: bool = True
    simplified_gestures: bool = False

    is_active: bool = True
    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate gesture settings."""
        if self.swipe_threshold_px < 10:
            raise ValueError("Swipe threshold must be at least 10px")
        if self.long_press_duration_ms < 100:
            raise ValueError("Long press duration must be at least 100ms")
        if self.double_tap_interval_ms < 100:
            raise ValueError("Double tap interval must be at least 100ms")
        if self.scroll_sensitivity <= Decimal("0"):
            raise ValueError("Scroll sensitivity must be positive")

    def get_gesture_action(self, gesture: str) -> Optional[str]:
        """Get action for gesture type."""
        gesture_map = {
            "swipe_left": self.swipe_left_action,
            "swipe_right": self.swipe_right_action,
            "swipe_down": self.swipe_down_action,
            "swipe_up": self.swipe_up_action,
            "double_tap": self.double_tap_action,
            "long_press": self.long_press_action,
            "pinch": self.pinch_action,
            "two_finger_swipe": self.two_finger_swipe_action,
        }
        return gesture_map.get(gesture)


@dataclass
class ResponsiveAnalytics:
    """
    What: Responsive design analytics record.
    Where: Analytics aggregation.
    Why: Enables data-driven responsive design.
    """
    recorded_date: date
    breakpoint: Breakpoint
    device_type: DeviceType

    organization_id: Optional[UUID] = None
    orientation: Optional[Orientation] = None

    # Usage metrics
    unique_users: int = 0
    total_sessions: int = 0
    total_page_views: int = 0
    avg_session_duration_seconds: Optional[int] = None

    # Engagement
    course_completions: int = 0
    quiz_completions: int = 0
    video_completions: int = 0

    # Performance
    avg_page_load_ms: Optional[int] = None
    avg_interaction_delay_ms: Optional[int] = None
    layout_shift_score: Optional[Decimal] = None

    # Problems
    ui_error_count: int = 0
    accessibility_issues: int = 0

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate analytics data."""
        if self.unique_users < 0:
            raise ValueError("Unique users must be non-negative")
        if self.total_sessions < 0:
            raise ValueError("Total sessions must be non-negative")

    def get_engagement_rate(self) -> Optional[Decimal]:
        """Calculate engagement rate as completions per session."""
        if not self.total_sessions:
            return None
        completions = self.course_completions + self.quiz_completions + self.video_completions
        return round(Decimal(completions) / Decimal(self.total_sessions), 4)

    def has_performance_issues(self) -> bool:
        """Check for performance problems."""
        if self.avg_page_load_ms and self.avg_page_load_ms > 3000:
            return True
        if self.layout_shift_score and self.layout_shift_score > Decimal("0.25"):
            return True
        return False


@dataclass
class BandwidthUsage:
    """
    What: User bandwidth usage tracking.
    Where: Data usage analytics.
    Why: Enables data saver features and monitoring.
    """
    user_id: UUID
    usage_date: date

    device_preference_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    usage_hour: Optional[int] = None

    # Downloads by type
    video_bytes_downloaded: int = 0
    image_bytes_downloaded: int = 0
    document_bytes_downloaded: int = 0
    api_bytes_downloaded: int = 0
    other_bytes_downloaded: int = 0
    total_bytes_downloaded: int = 0

    # Uploads
    bytes_uploaded: int = 0

    # Connection
    connection_type: Optional[ConnectionType] = None
    is_metered: Optional[bool] = None

    # Savings
    bytes_saved_compression: int = 0
    bytes_saved_caching: int = 0
    bytes_saved_data_saver: int = 0

    id: UUID = field(default_factory=uuid4)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate bandwidth data."""
        if self.usage_hour is not None and (self.usage_hour < 0 or self.usage_hour > 23):
            raise ValueError("Usage hour must be between 0 and 23")

    def get_total_usage_mb(self) -> Decimal:
        """Get total usage in megabytes."""
        total = self.total_bytes_downloaded + self.bytes_uploaded
        return round(Decimal(total) / Decimal("1048576"), 2)  # 1024 * 1024

    def get_total_savings_mb(self) -> Decimal:
        """Get total savings in megabytes."""
        total = self.bytes_saved_compression + self.bytes_saved_caching + self.bytes_saved_data_saver
        return round(Decimal(total) / Decimal("1048576"), 2)

    def get_savings_percentage(self) -> Optional[Decimal]:
        """Calculate percentage of data saved."""
        potential = self.total_bytes_downloaded + self.get_total_savings_mb() * 1048576
        if potential == 0:
            return None
        savings = self.bytes_saved_compression + self.bytes_saved_caching + self.bytes_saved_data_saver
        return round(Decimal(savings) / Decimal(potential) * 100, 2)

    def is_heavy_usage(self, threshold_mb: int = 100) -> bool:
        """Check if usage exceeds threshold."""
        return self.get_total_usage_mb() > Decimal(threshold_mb)
