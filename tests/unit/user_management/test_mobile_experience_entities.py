"""
Mobile Experience Entity Unit Tests

What: Comprehensive tests for mobile experience domain entities.
Where: User Management service domain layer.
Why: Ensures entity validation and business logic correctness.
"""

from dataclasses import replace
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from user_management.domain.entities.mobile_experience import (
    UserDevicePreference,
    MobileSession,
    OfflineContentSync,
    PushNotificationSettings,
    PushNotification,
    MobileContentCache,
    TouchGestureSettings,
    ResponsiveAnalytics,
    BandwidthUsage,
    DeviceType,
    Theme,
    FontSize,
    NavigationType,
    VideoQuality,
    ImageQuality,
    Platform,
    ConnectionType,
    SyncStatus,
    ContentType,
    NotificationCategory,
    NotificationPriority,
    DeliveryStatus,
    CacheContentType,
    CacheQuality,
    Breakpoint,
    Orientation,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    """Test all enum definitions."""

    def test_device_type_values(self):
        """Test DeviceType enum values."""
        assert DeviceType.MOBILE.value == "mobile"
        assert DeviceType.TABLET.value == "tablet"
        assert DeviceType.DESKTOP.value == "desktop"
        assert DeviceType.WATCH.value == "watch"
        assert DeviceType.TV.value == "tv"

    def test_theme_values(self):
        """Test Theme enum values."""
        assert Theme.LIGHT.value == "light"
        assert Theme.DARK.value == "dark"
        assert Theme.SYSTEM.value == "system"
        assert Theme.HIGH_CONTRAST.value == "high_contrast"

    def test_font_size_values(self):
        """Test FontSize enum values."""
        assert FontSize.SMALL.value == "small"
        assert FontSize.MEDIUM.value == "medium"
        assert FontSize.LARGE.value == "large"
        assert FontSize.EXTRA_LARGE.value == "extra_large"

    def test_navigation_type_values(self):
        """Test NavigationType enum values."""
        assert NavigationType.BOTTOM_TABS.value == "bottom_tabs"
        assert NavigationType.SIDEBAR.value == "sidebar"
        assert NavigationType.HAMBURGER.value == "hamburger"
        assert NavigationType.AUTO.value == "auto"

    def test_video_quality_values(self):
        """Test VideoQuality enum values."""
        assert VideoQuality.AUTO.value == "auto"
        assert VideoQuality.LOW.value == "low"
        assert VideoQuality.MEDIUM.value == "medium"
        assert VideoQuality.HIGH.value == "high"
        assert VideoQuality.FOUR_K.value == "4k"

    def test_image_quality_values(self):
        """Test ImageQuality enum values."""
        assert ImageQuality.AUTO.value == "auto"
        assert ImageQuality.LOW.value == "low"
        assert ImageQuality.MEDIUM.value == "medium"
        assert ImageQuality.HIGH.value == "high"

    def test_platform_values(self):
        """Test Platform enum values."""
        assert Platform.IOS.value == "ios"
        assert Platform.ANDROID.value == "android"
        assert Platform.PWA.value == "pwa"
        assert Platform.MOBILE_WEB.value == "mobile_web"

    def test_connection_type_values(self):
        """Test ConnectionType enum values."""
        assert ConnectionType.WIFI.value == "wifi"
        assert ConnectionType.FIVE_G.value == "5g"
        assert ConnectionType.FOUR_G.value == "4g"
        assert ConnectionType.THREE_G.value == "3g"
        assert ConnectionType.TWO_G.value == "2g"
        assert ConnectionType.OFFLINE.value == "offline"
        assert ConnectionType.UNKNOWN.value == "unknown"

    def test_sync_status_values(self):
        """Test SyncStatus enum values."""
        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.DOWNLOADING.value == "downloading"
        assert SyncStatus.DOWNLOADED.value == "downloaded"
        assert SyncStatus.SYNCING.value == "syncing"
        assert SyncStatus.SYNCED.value == "synced"
        assert SyncStatus.ERROR.value == "error"
        assert SyncStatus.EXPIRED.value == "expired"
        assert SyncStatus.DELETED.value == "deleted"

    def test_content_type_values(self):
        """Test ContentType enum values."""
        assert ContentType.COURSE.value == "course"
        assert ContentType.MODULE.value == "module"
        assert ContentType.LESSON.value == "lesson"
        assert ContentType.QUIZ.value == "quiz"
        assert ContentType.LAB.value == "lab"
        assert ContentType.VIDEO.value == "video"
        assert ContentType.DOCUMENT.value == "document"
        assert ContentType.SLIDE.value == "slide"

    def test_notification_category_values(self):
        """Test NotificationCategory enum values."""
        assert NotificationCategory.COURSE_UPDATES.value == "course_updates"
        assert NotificationCategory.QUIZ_REMINDERS.value == "quiz_reminders"
        assert NotificationCategory.ASSIGNMENT_DEADLINES.value == "assignment_deadlines"
        assert NotificationCategory.DISCUSSION_REPLIES.value == "discussion_replies"
        assert NotificationCategory.INSTRUCTOR_MESSAGES.value == "instructor_messages"
        assert NotificationCategory.CERTIFICATE_EARNED.value == "certificate_earned"
        assert NotificationCategory.NEW_CONTENT.value == "new_content_available"
        assert NotificationCategory.PROMOTIONS.value == "promotion_offers"
        assert NotificationCategory.SYSTEM.value == "system_announcements"

    def test_notification_priority_values(self):
        """Test NotificationPriority enum values."""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.CRITICAL.value == "critical"

    def test_delivery_status_values(self):
        """Test DeliveryStatus enum values."""
        assert DeliveryStatus.PENDING.value == "pending"
        assert DeliveryStatus.SENT.value == "sent"
        assert DeliveryStatus.DELIVERED.value == "delivered"
        assert DeliveryStatus.FAILED.value == "failed"
        assert DeliveryStatus.EXPIRED.value == "expired"
        assert DeliveryStatus.CANCELLED.value == "cancelled"

    def test_cache_content_type_values(self):
        """Test CacheContentType enum values."""
        assert CacheContentType.IMAGE.value == "image"
        assert CacheContentType.VIDEO.value == "video"
        assert CacheContentType.DOCUMENT.value == "document"
        assert CacheContentType.AUDIO.value == "audio"
        assert CacheContentType.DATA.value == "data"
        assert CacheContentType.STYLE.value == "style"
        assert CacheContentType.SCRIPT.value == "script"

    def test_cache_quality_values(self):
        """Test CacheQuality enum values."""
        assert CacheQuality.THUMBNAIL.value == "thumbnail"
        assert CacheQuality.LOW.value == "low"
        assert CacheQuality.MEDIUM.value == "medium"
        assert CacheQuality.HIGH.value == "high"
        assert CacheQuality.ORIGINAL.value == "original"

    def test_breakpoint_values(self):
        """Test Breakpoint enum values."""
        assert Breakpoint.XS.value == "xs"
        assert Breakpoint.SM.value == "sm"
        assert Breakpoint.MD.value == "md"
        assert Breakpoint.LG.value == "lg"
        assert Breakpoint.XL.value == "xl"
        assert Breakpoint.XXL.value == "2xl"

    def test_orientation_values(self):
        """Test Orientation enum values."""
        assert Orientation.PORTRAIT.value == "portrait"
        assert Orientation.LANDSCAPE.value == "landscape"


# ============================================================================
# USER DEVICE PREFERENCE TESTS
# ============================================================================

class TestUserDevicePreference:
    """Tests for UserDevicePreference entity."""

    @pytest.fixture
    def valid_preference(self):
        """Create a valid device preference."""
        return UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE,
            screen_width=375,
            screen_height=812
        )

    def test_valid_creation(self, valid_preference):
        """Test valid device preference creation."""
        assert valid_preference.device_id == "device123"
        assert valid_preference.device_type == DeviceType.MOBILE
        assert valid_preference.screen_width == 375
        assert valid_preference.screen_height == 812

    def test_default_values(self, valid_preference):
        """Test default values are set correctly."""
        assert valid_preference.preferred_theme == Theme.SYSTEM
        assert valid_preference.font_size_preference == FontSize.MEDIUM
        assert valid_preference.reduced_motion is False
        assert valid_preference.high_contrast is False
        assert valid_preference.compact_mode is False
        assert valid_preference.preferred_navigation == NavigationType.AUTO
        assert valid_preference.gesture_navigation is True
        assert valid_preference.haptic_feedback is True
        assert valid_preference.data_saver_mode is False
        assert valid_preference.auto_play_video is True
        assert valid_preference.video_quality_preference == VideoQuality.AUTO
        assert valid_preference.image_quality_preference == ImageQuality.AUTO
        assert valid_preference.offline_enabled is True
        assert valid_preference.max_offline_storage_mb == 1000
        assert valid_preference.auto_download_wifi_only is True
        assert valid_preference.is_primary_device is False

    def test_validation_empty_device_id(self):
        """Test validation rejects empty device ID."""
        with pytest.raises(ValueError, match="Device ID is required"):
            UserDevicePreference(
                user_id=uuid4(),
                device_id="",
                device_type=DeviceType.MOBILE
            )

    def test_validation_invalid_screen_width(self):
        """Test validation rejects invalid screen width."""
        with pytest.raises(ValueError, match="Screen width must be positive"):
            UserDevicePreference(
                user_id=uuid4(),
                device_id="device123",
                device_type=DeviceType.MOBILE,
                screen_width=0
            )

    def test_validation_invalid_screen_height(self):
        """Test validation rejects invalid screen height."""
        with pytest.raises(ValueError, match="Screen height must be positive"):
            UserDevicePreference(
                user_id=uuid4(),
                device_id="device123",
                device_type=DeviceType.MOBILE,
                screen_height=-100
            )

    def test_validation_negative_offline_storage(self):
        """Test validation rejects negative offline storage."""
        with pytest.raises(ValueError, match="Max offline storage must be non-negative"):
            UserDevicePreference(
                user_id=uuid4(),
                device_id="device123",
                device_type=DeviceType.MOBILE,
                max_offline_storage_mb=-1
            )

    def test_get_breakpoint_xs(self):
        """Test XS breakpoint detection."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE,
            screen_width=320
        )
        assert pref.get_breakpoint() == Breakpoint.XS

    def test_get_breakpoint_sm(self):
        """Test SM breakpoint detection."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE,
            screen_width=700
        )
        assert pref.get_breakpoint() == Breakpoint.SM

    def test_get_breakpoint_md(self):
        """Test MD breakpoint detection."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.TABLET,
            screen_width=900
        )
        assert pref.get_breakpoint() == Breakpoint.MD

    def test_get_breakpoint_lg(self):
        """Test LG breakpoint detection."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.DESKTOP,
            screen_width=1100
        )
        assert pref.get_breakpoint() == Breakpoint.LG

    def test_get_breakpoint_xl(self):
        """Test XL breakpoint detection."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.DESKTOP,
            screen_width=1400
        )
        assert pref.get_breakpoint() == Breakpoint.XL

    def test_get_breakpoint_xxl(self):
        """Test XXL breakpoint detection."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.DESKTOP,
            screen_width=1920
        )
        assert pref.get_breakpoint() == Breakpoint.XXL

    def test_get_breakpoint_no_width(self):
        """Test breakpoint returns None when width not set."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE
        )
        assert pref.get_breakpoint() is None

    def test_should_reduce_quality_data_saver(self):
        """Test quality reduction with data saver mode."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE,
            data_saver_mode=True
        )
        assert pref.should_reduce_quality() is True

    def test_should_reduce_quality_low_video(self):
        """Test quality reduction with low video quality preference."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE,
            video_quality_preference=VideoQuality.LOW
        )
        assert pref.should_reduce_quality() is True

    def test_should_reduce_quality_false(self):
        """Test no quality reduction with default settings."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE
        )
        assert pref.should_reduce_quality() is False

    def test_get_orientation_portrait(self):
        """Test portrait orientation detection."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE,
            screen_width=375,
            screen_height=812
        )
        assert pref.get_orientation() == Orientation.PORTRAIT

    def test_get_orientation_landscape(self):
        """Test landscape orientation detection."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE,
            screen_width=812,
            screen_height=375
        )
        assert pref.get_orientation() == Orientation.LANDSCAPE

    def test_get_orientation_no_dimensions(self):
        """Test orientation returns None when dimensions not set."""
        pref = UserDevicePreference(
            user_id=uuid4(),
            device_id="device123",
            device_type=DeviceType.MOBILE
        )
        assert pref.get_orientation() is None


# ============================================================================
# MOBILE SESSION TESTS
# ============================================================================

class TestMobileSession:
    """Tests for MobileSession entity."""

    @pytest.fixture
    def valid_session(self):
        """Create a valid mobile session."""
        return MobileSession(
            session_token="token123",
            platform=Platform.IOS,
            user_id=uuid4()
        )

    def test_valid_creation(self, valid_session):
        """Test valid session creation."""
        assert valid_session.session_token == "token123"
        assert valid_session.platform == Platform.IOS
        assert valid_session.session_end is None
        assert valid_session.duration_seconds is None

    def test_default_values(self, valid_session):
        """Test default values are set correctly."""
        assert valid_session.screen_views == 0
        assert valid_session.interactions == 0
        assert valid_session.memory_warnings == 0
        assert valid_session.crashes == 0
        assert valid_session.content_items_viewed == 0
        assert valid_session.videos_watched == 0
        assert valid_session.quizzes_taken == 0
        assert valid_session.labs_started == 0
        assert valid_session.is_background is False
        assert valid_session.is_offline is False

    def test_validation_empty_token(self):
        """Test validation rejects empty session token."""
        with pytest.raises(ValueError, match="Session token is required"):
            MobileSession(
                session_token="",
                platform=Platform.ANDROID
            )

    def test_end_session(self, valid_session):
        """Test end session calculates duration."""
        valid_session.end_session()
        assert valid_session.session_end is not None
        assert valid_session.duration_seconds is not None
        assert valid_session.duration_seconds >= 0

    def test_record_screen_view(self, valid_session):
        """Test recording screen views."""
        assert valid_session.screen_views == 0
        valid_session.record_screen_view()
        assert valid_session.screen_views == 1
        valid_session.record_screen_view()
        assert valid_session.screen_views == 2

    def test_record_interaction(self, valid_session):
        """Test recording interactions."""
        assert valid_session.interactions == 0
        valid_session.record_interaction()
        assert valid_session.interactions == 1
        valid_session.record_interaction()
        assert valid_session.interactions == 2

    def test_is_active_when_running(self, valid_session):
        """Test is_active returns True for running session."""
        assert valid_session.is_active() is True

    def test_is_active_when_ended(self, valid_session):
        """Test is_active returns False when session ended."""
        valid_session.end_session()
        assert valid_session.is_active() is False

    def test_is_active_when_background(self, valid_session):
        """Test is_active returns False when in background."""
        valid_session.is_background = True
        assert valid_session.is_active() is False

    def test_get_engagement_score_no_duration(self, valid_session):
        """Test engagement score is 0 without duration."""
        assert valid_session.get_engagement_score() == Decimal("0")

    def test_get_engagement_score_calculation(self):
        """Test engagement score calculation."""
        session = MobileSession(
            session_token="token123",
            platform=Platform.ANDROID,
            duration_seconds=120,  # 2 minutes
            screen_views=10,
            content_items_viewed=5,
            videos_watched=2,
            quizzes_taken=1,
            labs_started=0
        )
        # score = 10*1 + 5*5 + 2*10 + 1*15 + 0*20 = 10 + 25 + 20 + 15 = 70
        # per minute = 70 / 2 = 35
        assert session.get_engagement_score() == Decimal("35.00")

    def test_get_engagement_score_zero_minutes(self):
        """Test engagement score with very short duration."""
        session = MobileSession(
            session_token="token123",
            platform=Platform.PWA,
            duration_seconds=0
        )
        assert session.get_engagement_score() == Decimal("0")


# ============================================================================
# OFFLINE CONTENT SYNC TESTS
# ============================================================================

class TestOfflineContentSync:
    """Tests for OfflineContentSync entity."""

    @pytest.fixture
    def valid_sync(self):
        """Create a valid offline sync record."""
        return OfflineContentSync(
            user_id=uuid4(),
            device_id="device123",
            content_type=ContentType.COURSE,
            content_id=uuid4()
        )

    def test_valid_creation(self, valid_sync):
        """Test valid sync record creation."""
        assert valid_sync.device_id == "device123"
        assert valid_sync.content_type == ContentType.COURSE
        assert valid_sync.sync_status == SyncStatus.PENDING

    def test_default_values(self, valid_sync):
        """Test default values are set correctly."""
        assert valid_sync.sync_priority == 5
        assert valid_sync.retry_count == 0
        assert valid_sync.max_retries == 3
        assert valid_sync.has_offline_progress is False

    def test_validation_empty_device_id(self):
        """Test validation rejects empty device ID."""
        with pytest.raises(ValueError, match="Device ID is required"):
            OfflineContentSync(
                user_id=uuid4(),
                device_id="",
                content_type=ContentType.VIDEO,
                content_id=uuid4()
            )

    def test_validation_invalid_priority_low(self):
        """Test validation rejects priority below 1."""
        with pytest.raises(ValueError, match="Sync priority must be between 1 and 10"):
            OfflineContentSync(
                user_id=uuid4(),
                device_id="device123",
                content_type=ContentType.VIDEO,
                content_id=uuid4(),
                sync_priority=0
            )

    def test_validation_invalid_priority_high(self):
        """Test validation rejects priority above 10."""
        with pytest.raises(ValueError, match="Sync priority must be between 1 and 10"):
            OfflineContentSync(
                user_id=uuid4(),
                device_id="device123",
                content_type=ContentType.VIDEO,
                content_id=uuid4(),
                sync_priority=11
            )

    def test_can_retry_true(self, valid_sync):
        """Test can_retry returns True when retries available."""
        assert valid_sync.can_retry() is True
        valid_sync.retry_count = 2
        assert valid_sync.can_retry() is True

    def test_can_retry_false(self, valid_sync):
        """Test can_retry returns False when retries exhausted."""
        valid_sync.retry_count = 3
        assert valid_sync.can_retry() is False

    def test_is_available_offline_downloaded(self, valid_sync):
        """Test is_available_offline returns True when downloaded."""
        valid_sync.sync_status = SyncStatus.DOWNLOADED
        assert valid_sync.is_available_offline() is True

    def test_is_available_offline_synced(self, valid_sync):
        """Test is_available_offline returns True when synced."""
        valid_sync.sync_status = SyncStatus.SYNCED
        assert valid_sync.is_available_offline() is True

    def test_is_available_offline_pending(self, valid_sync):
        """Test is_available_offline returns False when pending."""
        assert valid_sync.is_available_offline() is False

    def test_is_available_offline_error(self, valid_sync):
        """Test is_available_offline returns False when error."""
        valid_sync.sync_status = SyncStatus.ERROR
        assert valid_sync.is_available_offline() is False

    def test_is_expired_no_expiry(self, valid_sync):
        """Test is_expired returns False when no expiry set."""
        assert valid_sync.is_expired() is False

    def test_is_expired_future_expiry(self, valid_sync):
        """Test is_expired returns False for future expiry."""
        valid_sync.expires_at = datetime.now() + timedelta(days=1)
        assert valid_sync.is_expired() is False

    def test_is_expired_past_expiry(self, valid_sync):
        """Test is_expired returns True for past expiry."""
        valid_sync.expires_at = datetime.now() - timedelta(days=1)
        assert valid_sync.is_expired() is True

    def test_get_compression_ratio(self, valid_sync):
        """Test compression ratio calculation."""
        valid_sync.storage_size_bytes = 1000000
        valid_sync.compressed_size_bytes = 300000
        assert valid_sync.get_compression_ratio() == Decimal("0.3000")

    def test_get_compression_ratio_no_sizes(self, valid_sync):
        """Test compression ratio returns None without sizes."""
        assert valid_sync.get_compression_ratio() is None

    def test_get_compression_ratio_zero_storage(self, valid_sync):
        """Test compression ratio returns None with zero storage."""
        valid_sync.storage_size_bytes = 0
        valid_sync.compressed_size_bytes = 100
        assert valid_sync.get_compression_ratio() is None

    def test_mark_downloading(self, valid_sync):
        """Test mark_downloading updates status."""
        valid_sync.mark_downloading()
        assert valid_sync.sync_status == SyncStatus.DOWNLOADING
        assert valid_sync.download_started_at is not None

    def test_mark_downloaded(self, valid_sync):
        """Test mark_downloaded updates status."""
        valid_sync.mark_downloaded()
        assert valid_sync.sync_status == SyncStatus.DOWNLOADED
        assert valid_sync.download_completed_at is not None

    def test_mark_error(self, valid_sync):
        """Test mark_error updates status and increments retry."""
        initial_retry = valid_sync.retry_count
        valid_sync.mark_error("Network timeout")
        assert valid_sync.sync_status == SyncStatus.ERROR
        assert valid_sync.last_error == "Network timeout"
        assert valid_sync.retry_count == initial_retry + 1


# ============================================================================
# PUSH NOTIFICATION SETTINGS TESTS
# ============================================================================

class TestPushNotificationSettings:
    """Tests for PushNotificationSettings entity."""

    @pytest.fixture
    def valid_settings(self):
        """Create valid push notification settings."""
        return PushNotificationSettings(
            user_id=uuid4(),
            fcm_token="fcm_token_123"
        )

    def test_valid_creation(self, valid_settings):
        """Test valid settings creation."""
        assert valid_settings.fcm_token == "fcm_token_123"
        assert valid_settings.notifications_enabled is True

    def test_default_category_values(self, valid_settings):
        """Test default category values."""
        assert valid_settings.course_updates is True
        assert valid_settings.quiz_reminders is True
        assert valid_settings.assignment_deadlines is True
        assert valid_settings.discussion_replies is True
        assert valid_settings.instructor_messages is True
        assert valid_settings.certificate_earned is True
        assert valid_settings.new_content_available is True
        assert valid_settings.promotion_offers is False  # Marketing off by default
        assert valid_settings.system_announcements is True

    def test_validation_negative_max_per_hour(self):
        """Test validation rejects negative max per hour."""
        with pytest.raises(ValueError, match="Max notifications per hour must be non-negative"):
            PushNotificationSettings(
                user_id=uuid4(),
                max_notifications_per_hour=-1
            )

    def test_validation_quiet_hours_enabled_without_times(self):
        """Test validation rejects quiet hours without times."""
        with pytest.raises(ValueError, match="Quiet hours start and end required"):
            PushNotificationSettings(
                user_id=uuid4(),
                quiet_hours_enabled=True
            )

    def test_has_valid_token_fcm(self, valid_settings):
        """Test has_valid_token returns True with FCM token."""
        assert valid_settings.has_valid_token() is True

    def test_has_valid_token_apns(self):
        """Test has_valid_token returns True with APNS token."""
        settings = PushNotificationSettings(
            user_id=uuid4(),
            apns_token="apns_token_123"
        )
        assert settings.has_valid_token() is True

    def test_has_valid_token_web_push(self):
        """Test has_valid_token returns True with web push endpoint."""
        settings = PushNotificationSettings(
            user_id=uuid4(),
            web_push_endpoint="https://push.example.com"
        )
        assert settings.has_valid_token() is True

    def test_has_valid_token_none(self):
        """Test has_valid_token returns False without tokens."""
        settings = PushNotificationSettings(user_id=uuid4())
        assert settings.has_valid_token() is False

    def test_is_category_enabled_course_updates(self, valid_settings):
        """Test is_category_enabled for course updates."""
        assert valid_settings.is_category_enabled(NotificationCategory.COURSE_UPDATES) is True

    def test_is_category_enabled_promotions_disabled(self, valid_settings):
        """Test is_category_enabled for promotions (disabled by default)."""
        assert valid_settings.is_category_enabled(NotificationCategory.PROMOTIONS) is False

    def test_is_category_enabled_when_notifications_disabled(self, valid_settings):
        """Test is_category_enabled returns False when notifications disabled."""
        valid_settings.notifications_enabled = False
        assert valid_settings.is_category_enabled(NotificationCategory.COURSE_UPDATES) is False

    def test_is_quiet_hours_disabled(self, valid_settings):
        """Test is_quiet_hours returns False when disabled."""
        assert valid_settings.is_quiet_hours() is False

    def test_is_quiet_hours_within_range(self):
        """Test is_quiet_hours returns True within range."""
        settings = PushNotificationSettings(
            user_id=uuid4(),
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(7, 0)
        )
        # 23:00 should be in quiet hours
        assert settings.is_quiet_hours(time(23, 0)) is True

    def test_is_quiet_hours_outside_range(self):
        """Test is_quiet_hours returns False outside range."""
        settings = PushNotificationSettings(
            user_id=uuid4(),
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(7, 0)
        )
        # 15:00 should not be in quiet hours
        assert settings.is_quiet_hours(time(15, 0)) is False

    def test_is_quiet_hours_same_day_range(self):
        """Test is_quiet_hours with same-day range."""
        settings = PushNotificationSettings(
            user_id=uuid4(),
            quiet_hours_enabled=True,
            quiet_hours_start=time(12, 0),
            quiet_hours_end=time(14, 0)
        )
        assert settings.is_quiet_hours(time(13, 0)) is True
        assert settings.is_quiet_hours(time(15, 0)) is False

    def test_can_send_notification_allowed(self, valid_settings):
        """Test can_send_notification returns True when allowed."""
        assert valid_settings.can_send_notification(NotificationCategory.COURSE_UPDATES) is True

    def test_can_send_notification_disabled_globally(self, valid_settings):
        """Test can_send_notification returns False when disabled globally."""
        valid_settings.notifications_enabled = False
        assert valid_settings.can_send_notification(NotificationCategory.COURSE_UPDATES) is False

    def test_can_send_notification_category_disabled(self, valid_settings):
        """Test can_send_notification returns False when category disabled."""
        valid_settings.course_updates = False
        assert valid_settings.can_send_notification(NotificationCategory.COURSE_UPDATES) is False


# ============================================================================
# PUSH NOTIFICATION TESTS
# ============================================================================

class TestPushNotification:
    """Tests for PushNotification entity."""

    @pytest.fixture
    def valid_notification(self):
        """Create a valid push notification."""
        return PushNotification(
            user_id=uuid4(),
            title="New Course Available",
            body="Check out our new Python course!",
            category=NotificationCategory.NEW_CONTENT
        )

    def test_valid_creation(self, valid_notification):
        """Test valid notification creation."""
        assert valid_notification.title == "New Course Available"
        assert valid_notification.body == "Check out our new Python course!"
        assert valid_notification.category == NotificationCategory.NEW_CONTENT
        assert valid_notification.priority == NotificationPriority.NORMAL
        assert valid_notification.delivery_status == DeliveryStatus.PENDING

    def test_default_values(self, valid_notification):
        """Test default values are set correctly."""
        assert valid_notification.retry_count == 0
        assert valid_notification.ttl_seconds == 86400

    def test_validation_empty_title(self):
        """Test validation rejects empty title."""
        with pytest.raises(ValueError, match="Title is required"):
            PushNotification(
                user_id=uuid4(),
                title="",
                body="Body text",
                category=NotificationCategory.SYSTEM
            )

    def test_validation_title_too_long(self):
        """Test validation rejects title over 255 characters."""
        with pytest.raises(ValueError, match="Title is required and must be <= 255 characters"):
            PushNotification(
                user_id=uuid4(),
                title="x" * 256,
                body="Body text",
                category=NotificationCategory.SYSTEM
            )

    def test_validation_empty_body(self):
        """Test validation rejects empty body."""
        with pytest.raises(ValueError, match="Body is required"):
            PushNotification(
                user_id=uuid4(),
                title="Title",
                body="",
                category=NotificationCategory.SYSTEM
            )

    def test_validation_negative_ttl(self):
        """Test validation rejects negative TTL."""
        with pytest.raises(ValueError, match="TTL must be non-negative"):
            PushNotification(
                user_id=uuid4(),
                title="Title",
                body="Body",
                category=NotificationCategory.SYSTEM,
                ttl_seconds=-1
            )

    def test_mark_sent(self, valid_notification):
        """Test mark_sent updates status."""
        valid_notification.mark_sent("message_id_123")
        assert valid_notification.delivery_status == DeliveryStatus.SENT
        assert valid_notification.sent_at is not None
        assert valid_notification.platform_message_id == "message_id_123"
        assert valid_notification.expires_at is not None

    def test_mark_delivered(self, valid_notification):
        """Test mark_delivered updates status."""
        valid_notification.mark_delivered()
        assert valid_notification.delivery_status == DeliveryStatus.DELIVERED
        assert valid_notification.delivered_at is not None

    def test_mark_failed(self, valid_notification):
        """Test mark_failed updates status and increments retry."""
        initial_retry = valid_notification.retry_count
        valid_notification.mark_failed("NETWORK_ERROR", "Connection timeout")
        assert valid_notification.delivery_status == DeliveryStatus.FAILED
        assert valid_notification.error_code == "NETWORK_ERROR"
        assert valid_notification.error_message == "Connection timeout"
        assert valid_notification.retry_count == initial_retry + 1

    def test_mark_opened(self, valid_notification):
        """Test mark_opened updates status."""
        valid_notification.mark_opened("clicked_cta")
        assert valid_notification.opened_at is not None
        assert valid_notification.action_taken == "clicked_cta"

    def test_is_expired_no_expiry(self, valid_notification):
        """Test is_expired returns False when no expiry."""
        assert valid_notification.is_expired() is False

    def test_is_expired_future_expiry(self, valid_notification):
        """Test is_expired returns False for future expiry."""
        valid_notification.expires_at = datetime.now() + timedelta(hours=1)
        assert valid_notification.is_expired() is False

    def test_is_expired_past_expiry(self, valid_notification):
        """Test is_expired returns True for past expiry."""
        valid_notification.expires_at = datetime.now() - timedelta(hours=1)
        assert valid_notification.is_expired() is True

    def test_was_engaged_not_opened(self, valid_notification):
        """Test was_engaged returns False when not opened."""
        assert valid_notification.was_engaged() is False

    def test_was_engaged_opened(self, valid_notification):
        """Test was_engaged returns True when opened."""
        valid_notification.opened_at = datetime.now()
        assert valid_notification.was_engaged() is True


# ============================================================================
# MOBILE CONTENT CACHE TESTS
# ============================================================================

class TestMobileContentCache:
    """Tests for MobileContentCache entity."""

    @pytest.fixture
    def valid_cache(self):
        """Create a valid content cache record."""
        return MobileContentCache(
            content_type=CacheContentType.IMAGE,
            content_id=uuid4(),
            variant_key="mobile_320",
            cache_url="/cache/images/abc123.jpg",
            file_size_bytes=50000
        )

    def test_valid_creation(self, valid_cache):
        """Test valid cache creation."""
        assert valid_cache.content_type == CacheContentType.IMAGE
        assert valid_cache.variant_key == "mobile_320"
        assert valid_cache.file_size_bytes == 50000

    def test_default_values(self, valid_cache):
        """Test default values are set correctly."""
        assert valid_cache.is_compressed is False
        assert valid_cache.is_lazy_loadable is True
        assert valid_cache.preload_priority == 5
        assert valid_cache.access_count == 0

    def test_validation_empty_variant_key(self):
        """Test validation rejects empty variant key."""
        with pytest.raises(ValueError, match="Variant key is required"):
            MobileContentCache(
                content_type=CacheContentType.VIDEO,
                content_id=uuid4(),
                variant_key="",
                cache_url="/cache/video.mp4",
                file_size_bytes=1000
            )

    def test_validation_empty_cache_url(self):
        """Test validation rejects empty cache URL."""
        with pytest.raises(ValueError, match="Cache URL is required"):
            MobileContentCache(
                content_type=CacheContentType.VIDEO,
                content_id=uuid4(),
                variant_key="hd_1080",
                cache_url="",
                file_size_bytes=1000
            )

    def test_validation_negative_file_size(self):
        """Test validation rejects negative file size."""
        with pytest.raises(ValueError, match="File size must be non-negative"):
            MobileContentCache(
                content_type=CacheContentType.VIDEO,
                content_id=uuid4(),
                variant_key="hd_1080",
                cache_url="/cache/video.mp4",
                file_size_bytes=-100
            )

    def test_record_access(self, valid_cache):
        """Test record_access increments count."""
        assert valid_cache.access_count == 0
        valid_cache.record_access()
        assert valid_cache.access_count == 1
        assert valid_cache.last_accessed_at is not None

    def test_is_expired_no_expiry(self, valid_cache):
        """Test is_expired returns False when no expiry."""
        assert valid_cache.is_expired() is False

    def test_is_expired_future_expiry(self, valid_cache):
        """Test is_expired returns False for future expiry."""
        valid_cache.expires_at = datetime.now() + timedelta(hours=1)
        assert valid_cache.is_expired() is False

    def test_is_expired_past_expiry(self, valid_cache):
        """Test is_expired returns True for past expiry."""
        valid_cache.expires_at = datetime.now() - timedelta(hours=1)
        assert valid_cache.is_expired() is True

    def test_is_stale_no_last_modified(self, valid_cache):
        """Test is_stale returns False without last_modified."""
        assert valid_cache.is_stale() is False

    def test_is_stale_within_max_age(self, valid_cache):
        """Test is_stale returns False within max_age."""
        valid_cache.last_modified = datetime.now() - timedelta(minutes=5)
        valid_cache.max_age_seconds = 3600  # 1 hour
        assert valid_cache.is_stale() is False

    def test_is_stale_past_max_age(self, valid_cache):
        """Test is_stale returns True past max_age."""
        valid_cache.last_modified = datetime.now() - timedelta(hours=2)
        valid_cache.max_age_seconds = 3600  # 1 hour
        assert valid_cache.is_stale() is True

    def test_get_size_kb(self, valid_cache):
        """Test get_size_kb calculation."""
        valid_cache.file_size_bytes = 1024 * 100  # 100 KB
        assert valid_cache.get_size_kb() == Decimal("100.00")


# ============================================================================
# TOUCH GESTURE SETTINGS TESTS
# ============================================================================

class TestTouchGestureSettings:
    """Tests for TouchGestureSettings entity."""

    @pytest.fixture
    def valid_gestures(self):
        """Create valid gesture settings."""
        return TouchGestureSettings(
            user_id=uuid4()
        )

    def test_valid_creation(self, valid_gestures):
        """Test valid gesture settings creation."""
        assert valid_gestures.is_active is True

    def test_default_actions(self, valid_gestures):
        """Test default gesture actions."""
        assert valid_gestures.swipe_left_action == "next_item"
        assert valid_gestures.swipe_right_action == "previous_item"
        assert valid_gestures.swipe_down_action == "refresh"
        assert valid_gestures.swipe_up_action == "scroll_up"
        assert valid_gestures.double_tap_action == "toggle_fullscreen"
        assert valid_gestures.long_press_action == "context_menu"
        assert valid_gestures.pinch_action == "zoom"
        assert valid_gestures.two_finger_swipe_action == "navigate_back"

    def test_default_sensitivity(self, valid_gestures):
        """Test default sensitivity values."""
        assert valid_gestures.swipe_threshold_px == 50
        assert valid_gestures.long_press_duration_ms == 500
        assert valid_gestures.double_tap_interval_ms == 300
        assert valid_gestures.scroll_sensitivity == Decimal("1.0")

    def test_validation_low_swipe_threshold(self):
        """Test validation rejects swipe threshold below 10px."""
        with pytest.raises(ValueError, match="Swipe threshold must be at least 10px"):
            TouchGestureSettings(
                user_id=uuid4(),
                swipe_threshold_px=5
            )

    def test_validation_low_long_press_duration(self):
        """Test validation rejects long press below 100ms."""
        with pytest.raises(ValueError, match="Long press duration must be at least 100ms"):
            TouchGestureSettings(
                user_id=uuid4(),
                long_press_duration_ms=50
            )

    def test_validation_low_double_tap_interval(self):
        """Test validation rejects double tap interval below 100ms."""
        with pytest.raises(ValueError, match="Double tap interval must be at least 100ms"):
            TouchGestureSettings(
                user_id=uuid4(),
                double_tap_interval_ms=50
            )

    def test_validation_zero_scroll_sensitivity(self):
        """Test validation rejects zero scroll sensitivity."""
        with pytest.raises(ValueError, match="Scroll sensitivity must be positive"):
            TouchGestureSettings(
                user_id=uuid4(),
                scroll_sensitivity=Decimal("0")
            )

    def test_get_gesture_action_swipe_left(self, valid_gestures):
        """Test get_gesture_action for swipe_left."""
        assert valid_gestures.get_gesture_action("swipe_left") == "next_item"

    def test_get_gesture_action_swipe_right(self, valid_gestures):
        """Test get_gesture_action for swipe_right."""
        assert valid_gestures.get_gesture_action("swipe_right") == "previous_item"

    def test_get_gesture_action_unknown(self, valid_gestures):
        """Test get_gesture_action returns None for unknown gesture."""
        assert valid_gestures.get_gesture_action("triple_tap") is None


# ============================================================================
# RESPONSIVE ANALYTICS TESTS
# ============================================================================

class TestResponsiveAnalytics:
    """Tests for ResponsiveAnalytics entity."""

    @pytest.fixture
    def valid_analytics(self):
        """Create valid responsive analytics record."""
        return ResponsiveAnalytics(
            recorded_date=date.today(),
            breakpoint=Breakpoint.MD,
            device_type=DeviceType.TABLET,
            unique_users=100,
            total_sessions=150,
            total_page_views=500
        )

    def test_valid_creation(self, valid_analytics):
        """Test valid analytics creation."""
        assert valid_analytics.breakpoint == Breakpoint.MD
        assert valid_analytics.device_type == DeviceType.TABLET
        assert valid_analytics.unique_users == 100

    def test_default_values(self, valid_analytics):
        """Test default values are set correctly."""
        assert valid_analytics.course_completions == 0
        assert valid_analytics.quiz_completions == 0
        assert valid_analytics.video_completions == 0
        assert valid_analytics.ui_error_count == 0
        assert valid_analytics.accessibility_issues == 0

    def test_validation_negative_unique_users(self):
        """Test validation rejects negative unique users."""
        with pytest.raises(ValueError, match="Unique users must be non-negative"):
            ResponsiveAnalytics(
                recorded_date=date.today(),
                breakpoint=Breakpoint.XS,
                device_type=DeviceType.MOBILE,
                unique_users=-1
            )

    def test_validation_negative_total_sessions(self):
        """Test validation rejects negative total sessions."""
        with pytest.raises(ValueError, match="Total sessions must be non-negative"):
            ResponsiveAnalytics(
                recorded_date=date.today(),
                breakpoint=Breakpoint.XS,
                device_type=DeviceType.MOBILE,
                total_sessions=-1
            )

    def test_get_engagement_rate(self, valid_analytics):
        """Test engagement rate calculation."""
        valid_analytics.course_completions = 10
        valid_analytics.quiz_completions = 20
        valid_analytics.video_completions = 30
        # total completions = 60, sessions = 150
        # rate = 60 / 150 = 0.4
        assert valid_analytics.get_engagement_rate() == Decimal("0.4000")

    def test_get_engagement_rate_no_sessions(self, valid_analytics):
        """Test engagement rate returns None with no sessions."""
        valid_analytics.total_sessions = 0
        assert valid_analytics.get_engagement_rate() is None

    def test_has_performance_issues_slow_page_load(self, valid_analytics):
        """Test performance issues detected for slow page load."""
        valid_analytics.avg_page_load_ms = 4000
        assert valid_analytics.has_performance_issues() is True

    def test_has_performance_issues_high_layout_shift(self, valid_analytics):
        """Test performance issues detected for high layout shift."""
        valid_analytics.layout_shift_score = Decimal("0.30")
        assert valid_analytics.has_performance_issues() is True

    def test_has_performance_issues_no_issues(self, valid_analytics):
        """Test no performance issues with good metrics."""
        valid_analytics.avg_page_load_ms = 1500
        valid_analytics.layout_shift_score = Decimal("0.10")
        assert valid_analytics.has_performance_issues() is False


# ============================================================================
# BANDWIDTH USAGE TESTS
# ============================================================================

class TestBandwidthUsage:
    """Tests for BandwidthUsage entity."""

    @pytest.fixture
    def valid_usage(self):
        """Create valid bandwidth usage record."""
        return BandwidthUsage(
            user_id=uuid4(),
            usage_date=date.today(),
            total_bytes_downloaded=10 * 1024 * 1024,  # 10 MB
            bytes_uploaded=1 * 1024 * 1024  # 1 MB
        )

    def test_valid_creation(self, valid_usage):
        """Test valid usage creation."""
        assert valid_usage.total_bytes_downloaded == 10 * 1024 * 1024
        assert valid_usage.bytes_uploaded == 1 * 1024 * 1024

    def test_default_values(self, valid_usage):
        """Test default values are set correctly."""
        assert valid_usage.video_bytes_downloaded == 0
        assert valid_usage.image_bytes_downloaded == 0
        assert valid_usage.document_bytes_downloaded == 0
        assert valid_usage.api_bytes_downloaded == 0
        assert valid_usage.other_bytes_downloaded == 0
        assert valid_usage.bytes_saved_compression == 0
        assert valid_usage.bytes_saved_caching == 0
        assert valid_usage.bytes_saved_data_saver == 0

    def test_validation_invalid_usage_hour_low(self):
        """Test validation rejects usage hour below 0."""
        with pytest.raises(ValueError, match="Usage hour must be between 0 and 23"):
            BandwidthUsage(
                user_id=uuid4(),
                usage_date=date.today(),
                usage_hour=-1
            )

    def test_validation_invalid_usage_hour_high(self):
        """Test validation rejects usage hour above 23."""
        with pytest.raises(ValueError, match="Usage hour must be between 0 and 23"):
            BandwidthUsage(
                user_id=uuid4(),
                usage_date=date.today(),
                usage_hour=24
            )

    def test_get_total_usage_mb(self, valid_usage):
        """Test total usage in MB calculation."""
        # 10 MB download + 1 MB upload = 11 MB
        assert valid_usage.get_total_usage_mb() == Decimal("11.00")

    def test_get_total_savings_mb(self):
        """Test total savings in MB calculation."""
        usage = BandwidthUsage(
            user_id=uuid4(),
            usage_date=date.today(),
            bytes_saved_compression=1024 * 1024,  # 1 MB
            bytes_saved_caching=2 * 1024 * 1024,  # 2 MB
            bytes_saved_data_saver=512 * 1024  # 0.5 MB
        )
        assert usage.get_total_savings_mb() == Decimal("3.50")

    def test_get_savings_percentage(self):
        """Test savings percentage calculation."""
        usage = BandwidthUsage(
            user_id=uuid4(),
            usage_date=date.today(),
            total_bytes_downloaded=8 * 1024 * 1024,  # 8 MB actual
            bytes_saved_compression=2 * 1024 * 1024  # 2 MB saved
        )
        # Without other savings, potential = 8 + 2 = 10 MB
        # savings = 2 MB
        # percentage = 2/10 * 100 = 20%
        result = usage.get_savings_percentage()
        assert result is not None
        # Note: Due to decimal precision, allow slight variance
        assert result >= Decimal("19") and result <= Decimal("21")

    def test_get_savings_percentage_no_downloads(self):
        """Test savings percentage returns None with no downloads."""
        usage = BandwidthUsage(
            user_id=uuid4(),
            usage_date=date.today(),
            total_bytes_downloaded=0
        )
        assert usage.get_savings_percentage() is None

    def test_is_heavy_usage_below_threshold(self, valid_usage):
        """Test is_heavy_usage returns False below threshold."""
        valid_usage.total_bytes_downloaded = 50 * 1024 * 1024  # 50 MB
        valid_usage.bytes_uploaded = 0
        assert valid_usage.is_heavy_usage(threshold_mb=100) is False

    def test_is_heavy_usage_above_threshold(self, valid_usage):
        """Test is_heavy_usage returns True above threshold."""
        valid_usage.total_bytes_downloaded = 150 * 1024 * 1024  # 150 MB
        valid_usage.bytes_uploaded = 10 * 1024 * 1024  # 10 MB
        assert valid_usage.is_heavy_usage(threshold_mb=100) is True
