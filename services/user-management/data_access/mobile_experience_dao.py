"""
Mobile Experience Data Access Object

What: DAO for mobile experience data operations.
Where: Data access layer for mobile-related tables.
Why: Centralizes all database operations for mobile features.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

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
# CUSTOM EXCEPTIONS
# ============================================================================

class MobileExperienceDAOError(Exception):
    """
    What: Base exception for mobile experience DAO operations.
    Where: All DAO methods that encounter errors.
    Why: Provides consistent error handling for data access operations.
    """
    pass


class DevicePreferenceNotFoundError(MobileExperienceDAOError):
    """
    What: Raised when device preference is not found.
    Where: Get/update operations for device preferences.
    Why: Distinguishes between not found and other errors.
    """
    pass


class MobileSessionNotFoundError(MobileExperienceDAOError):
    """
    What: Raised when mobile session is not found.
    Where: Get/update operations for sessions.
    Why: Distinguishes between not found and other errors.
    """
    pass


class OfflineSyncNotFoundError(MobileExperienceDAOError):
    """
    What: Raised when offline sync record is not found.
    Where: Get/update operations for offline sync.
    Why: Distinguishes between not found and other errors.
    """
    pass


class PushSettingsNotFoundError(MobileExperienceDAOError):
    """
    What: Raised when push settings are not found.
    Where: Get/update operations for push settings.
    Why: Distinguishes between not found and other errors.
    """
    pass


class NotificationNotFoundError(MobileExperienceDAOError):
    """
    What: Raised when notification is not found.
    Where: Get/update operations for notifications.
    Why: Distinguishes between not found and other errors.
    """
    pass


# ============================================================================
# DAO CLASS
# ============================================================================

class MobileExperienceDAO:
    """
    What: Data Access Object for mobile experience operations.
    Where: Data layer for user management service.
    Why: Encapsulates all mobile-related database operations.
    """

    def __init__(self, db_pool):
        """
        What: Initialize DAO with database connection pool.
        Where: Service initialization.
        Why: Enables async database operations.
        """
        self._pool = db_pool

    # ========================================================================
    # DEVICE PREFERENCES
    # ========================================================================

    async def create_device_preference(
        self, preference: UserDevicePreference
    ) -> UserDevicePreference:
        """
        What: Create new device preference.
        Where: Device registration.
        Why: Stores user device settings.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO user_device_preferences (
                        id, user_id, device_id, device_type,
                        device_name, os_name, os_version, browser_name, browser_version,
                        screen_width, screen_height, pixel_ratio,
                        preferred_theme, font_size_preference, reduced_motion, high_contrast, compact_mode,
                        sidebar_collapsed, preferred_navigation, gesture_navigation, haptic_feedback,
                        data_saver_mode, auto_play_video, video_quality_preference, image_quality_preference,
                        offline_enabled, max_offline_storage_mb, auto_download_wifi_only,
                        is_primary_device, last_active_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30)
                    ON CONFLICT (user_id, device_id) DO UPDATE SET
                        device_type = EXCLUDED.device_type,
                        device_name = EXCLUDED.device_name,
                        last_active_at = NOW(),
                        updated_at = NOW()
                    RETURNING *
                    """,
                    preference.id, preference.user_id, preference.device_id,
                    preference.device_type.value, preference.device_name,
                    preference.os_name, preference.os_version, preference.browser_name,
                    preference.browser_version, preference.screen_width, preference.screen_height,
                    preference.pixel_ratio, preference.preferred_theme.value,
                    preference.font_size_preference.value, preference.reduced_motion,
                    preference.high_contrast, preference.compact_mode, preference.sidebar_collapsed,
                    preference.preferred_navigation.value, preference.gesture_navigation,
                    preference.haptic_feedback, preference.data_saver_mode, preference.auto_play_video,
                    preference.video_quality_preference.value, preference.image_quality_preference.value,
                    preference.offline_enabled, preference.max_offline_storage_mb,
                    preference.auto_download_wifi_only, preference.is_primary_device,
                    preference.last_active_at or datetime.now()
                )
                return self._map_device_preference(row)
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to create device preference: {e}")

    async def get_device_preference(
        self, user_id: UUID, device_id: str
    ) -> Optional[UserDevicePreference]:
        """
        What: Get device preference by user and device.
        Where: Device identification.
        Why: Retrieves device-specific settings.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM user_device_preferences WHERE user_id = $1 AND device_id = $2",
                    user_id, device_id
                )
                if row:
                    return self._map_device_preference(row)
                return None
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get device preference: {e}")

    async def get_user_devices(self, user_id: UUID) -> list[UserDevicePreference]:
        """
        What: Get all devices for user.
        Where: Device management.
        Why: Lists all user devices.
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM user_device_preferences
                    WHERE user_id = $1
                    ORDER BY last_active_at DESC
                    """,
                    user_id
                )
                return [self._map_device_preference(row) for row in rows]
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get user devices: {e}")

    async def update_device_preference(
        self, preference_id: UUID, **updates
    ) -> UserDevicePreference:
        """
        What: Update device preference.
        Where: Settings changes.
        Why: Allows partial updates to preferences.
        """
        try:
            set_clauses = []
            values = [preference_id]
            param_index = 2

            enum_fields = {
                'device_type': DeviceType,
                'preferred_theme': Theme,
                'font_size_preference': FontSize,
                'preferred_navigation': NavigationType,
                'video_quality_preference': VideoQuality,
                'image_quality_preference': ImageQuality,
            }

            for key, value in updates.items():
                if key in enum_fields and value is not None:
                    value = value.value if hasattr(value, 'value') else value
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1

            if not set_clauses:
                raise MobileExperienceDAOError("No updates provided")

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE user_device_preferences
                    SET {', '.join(set_clauses)}, updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    *values
                )
                if not row:
                    raise DevicePreferenceNotFoundError(f"Device preference {preference_id} not found")
                return self._map_device_preference(row)
        except DevicePreferenceNotFoundError:
            raise
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to update device preference: {e}")

    async def delete_device_preference(self, preference_id: UUID) -> bool:
        """
        What: Delete device preference.
        Where: Device removal.
        Why: Removes device registration.
        """
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM user_device_preferences WHERE id = $1",
                    preference_id
                )
                return "DELETE 1" in result
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to delete device preference: {e}")

    # ========================================================================
    # MOBILE SESSIONS
    # ========================================================================

    async def create_session(self, session: MobileSession) -> MobileSession:
        """
        What: Create mobile session.
        Where: App launch.
        Why: Tracks mobile app sessions.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO mobile_sessions (
                        id, user_id, device_preference_id, session_token,
                        app_version, build_number, platform,
                        connection_type, ip_address, country_code, timezone,
                        session_start, app_launch_time_ms, is_background, is_offline
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    RETURNING *
                    """,
                    session.id, session.user_id, session.device_preference_id,
                    session.session_token, session.app_version, session.build_number,
                    session.platform.value,
                    session.connection_type.value if session.connection_type else None,
                    session.ip_address, session.country_code, session.timezone,
                    session.session_start, session.app_launch_time_ms,
                    session.is_background, session.is_offline
                )
                return self._map_session(row)
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to create session: {e}")

    async def get_session(self, session_id: UUID) -> Optional[MobileSession]:
        """
        What: Get session by ID.
        Where: Session lookup.
        Why: Retrieves session data.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM mobile_sessions WHERE id = $1",
                    session_id
                )
                if row:
                    return self._map_session(row)
                return None
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get session: {e}")

    async def get_session_by_token(self, token: str) -> Optional[MobileSession]:
        """
        What: Get session by token.
        Where: Token validation.
        Why: Validates session tokens.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM mobile_sessions WHERE session_token = $1",
                    token
                )
                if row:
                    return self._map_session(row)
                return None
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get session by token: {e}")

    async def update_session(self, session_id: UUID, **updates) -> MobileSession:
        """
        What: Update session.
        Where: Session updates.
        Why: Tracks session metrics.
        """
        try:
            set_clauses = []
            values = [session_id]
            param_index = 2

            for key, value in updates.items():
                if key == 'connection_type' and value is not None:
                    value = value.value if hasattr(value, 'value') else value
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE mobile_sessions
                    SET {', '.join(set_clauses)}, updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    *values
                )
                if not row:
                    raise MobileSessionNotFoundError(f"Session {session_id} not found")
                return self._map_session(row)
        except MobileSessionNotFoundError:
            raise
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to update session: {e}")

    async def get_user_sessions(
        self, user_id: UUID, limit: int = 50
    ) -> list[MobileSession]:
        """
        What: Get sessions for user.
        Where: Session history.
        Why: Lists user's mobile sessions.
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM mobile_sessions
                    WHERE user_id = $1
                    ORDER BY session_start DESC LIMIT $2
                    """,
                    user_id, limit
                )
                return [self._map_session(row) for row in rows]
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get user sessions: {e}")

    # ========================================================================
    # OFFLINE SYNC
    # ========================================================================

    async def create_offline_sync(
        self, sync: OfflineContentSync
    ) -> OfflineContentSync:
        """
        What: Create offline sync record.
        Where: Content download queue.
        Why: Tracks offline content.
        """
        try:
            import json
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO offline_content_sync (
                        id, user_id, device_id, content_type, content_id,
                        content_version, sync_status, sync_priority,
                        storage_size_bytes, compressed_size_bytes, storage_path, checksum,
                        queued_at, expires_at, max_retries,
                        has_offline_progress, offline_progress_data
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    ON CONFLICT (user_id, device_id, content_type, content_id) DO UPDATE SET
                        sync_status = EXCLUDED.sync_status,
                        updated_at = NOW()
                    RETURNING *
                    """,
                    sync.id, sync.user_id, sync.device_id,
                    sync.content_type.value, sync.content_id,
                    sync.content_version, sync.sync_status.value, sync.sync_priority,
                    sync.storage_size_bytes, sync.compressed_size_bytes,
                    sync.storage_path, sync.checksum, sync.queued_at, sync.expires_at,
                    sync.max_retries, sync.has_offline_progress,
                    json.dumps(sync.offline_progress_data) if sync.offline_progress_data else None
                )
                return self._map_offline_sync(row)
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to create offline sync: {e}")

    async def get_offline_sync(
        self, user_id: UUID, device_id: str, content_type: ContentType, content_id: UUID
    ) -> Optional[OfflineContentSync]:
        """
        What: Get offline sync record.
        Where: Offline content check.
        Why: Checks if content is synced.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM offline_content_sync
                    WHERE user_id = $1 AND device_id = $2 AND content_type = $3 AND content_id = $4
                    """,
                    user_id, device_id, content_type.value, content_id
                )
                if row:
                    return self._map_offline_sync(row)
                return None
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get offline sync: {e}")

    async def get_pending_syncs(
        self, user_id: UUID, device_id: str, limit: int = 50
    ) -> list[OfflineContentSync]:
        """
        What: Get pending sync items.
        Where: Download queue.
        Why: Lists items to download.
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM offline_content_sync
                    WHERE user_id = $1 AND device_id = $2
                    AND sync_status IN ('pending', 'error')
                    AND retry_count < max_retries
                    ORDER BY sync_priority ASC, queued_at ASC
                    LIMIT $3
                    """,
                    user_id, device_id, limit
                )
                return [self._map_offline_sync(row) for row in rows]
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get pending syncs: {e}")

    async def update_offline_sync(
        self, sync_id: UUID, **updates
    ) -> OfflineContentSync:
        """
        What: Update offline sync record.
        Where: Sync status changes.
        Why: Tracks sync progress.
        """
        try:
            import json
            set_clauses = []
            values = [sync_id]
            param_index = 2

            for key, value in updates.items():
                if key == 'sync_status' and value is not None:
                    value = value.value if hasattr(value, 'value') else value
                elif key == 'content_type' and value is not None:
                    value = value.value if hasattr(value, 'value') else value
                elif key == 'offline_progress_data' and value is not None:
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE offline_content_sync
                    SET {', '.join(set_clauses)}, updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    *values
                )
                if not row:
                    raise OfflineSyncNotFoundError(f"Offline sync {sync_id} not found")
                return self._map_offline_sync(row)
        except OfflineSyncNotFoundError:
            raise
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to update offline sync: {e}")

    async def delete_offline_sync(self, sync_id: UUID) -> bool:
        """Delete offline sync record."""
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM offline_content_sync WHERE id = $1",
                    sync_id
                )
                return "DELETE 1" in result
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to delete offline sync: {e}")

    # ========================================================================
    # PUSH NOTIFICATION SETTINGS
    # ========================================================================

    async def create_push_settings(
        self, settings: PushNotificationSettings
    ) -> PushNotificationSettings:
        """
        What: Create push notification settings.
        Where: Device registration.
        Why: Stores notification preferences.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO push_notification_settings (
                        id, user_id, device_preference_id,
                        fcm_token, apns_token, web_push_endpoint, web_push_p256dh, web_push_auth,
                        notifications_enabled, quiet_hours_enabled, quiet_hours_start,
                        quiet_hours_end, quiet_hours_timezone,
                        course_updates, quiz_reminders, assignment_deadlines,
                        discussion_replies, instructor_messages, certificate_earned,
                        new_content_available, promotion_offers, system_announcements,
                        group_notifications, show_preview, sound_enabled, vibration_enabled,
                        badge_count_enabled, max_notifications_per_hour, digest_mode, digest_time,
                        token_updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31)
                    RETURNING *
                    """,
                    settings.id, settings.user_id, settings.device_preference_id,
                    settings.fcm_token, settings.apns_token, settings.web_push_endpoint,
                    settings.web_push_p256dh, settings.web_push_auth,
                    settings.notifications_enabled, settings.quiet_hours_enabled,
                    settings.quiet_hours_start, settings.quiet_hours_end, settings.quiet_hours_timezone,
                    settings.course_updates, settings.quiz_reminders, settings.assignment_deadlines,
                    settings.discussion_replies, settings.instructor_messages, settings.certificate_earned,
                    settings.new_content_available, settings.promotion_offers, settings.system_announcements,
                    settings.group_notifications, settings.show_preview, settings.sound_enabled,
                    settings.vibration_enabled, settings.badge_count_enabled,
                    settings.max_notifications_per_hour, settings.digest_mode, settings.digest_time,
                    settings.token_updated_at
                )
                return self._map_push_settings(row)
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to create push settings: {e}")

    async def get_push_settings(
        self, user_id: UUID, device_preference_id: Optional[UUID] = None
    ) -> Optional[PushNotificationSettings]:
        """
        What: Get push settings.
        Where: Notification sending.
        Why: Retrieves notification preferences.
        """
        try:
            async with self._pool.acquire() as conn:
                if device_preference_id:
                    row = await conn.fetchrow(
                        """
                        SELECT * FROM push_notification_settings
                        WHERE user_id = $1 AND device_preference_id = $2
                        """,
                        user_id, device_preference_id
                    )
                else:
                    row = await conn.fetchrow(
                        """
                        SELECT * FROM push_notification_settings
                        WHERE user_id = $1 ORDER BY updated_at DESC LIMIT 1
                        """,
                        user_id
                    )
                if row:
                    return self._map_push_settings(row)
                return None
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get push settings: {e}")

    async def get_user_push_settings(
        self, user_id: UUID
    ) -> list[PushNotificationSettings]:
        """
        What: Get all push settings for user.
        Where: Multi-device notifications.
        Why: Lists all notification settings.
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM push_notification_settings WHERE user_id = $1",
                    user_id
                )
                return [self._map_push_settings(row) for row in rows]
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get user push settings: {e}")

    async def update_push_settings(
        self, settings_id: UUID, **updates
    ) -> PushNotificationSettings:
        """Update push notification settings."""
        try:
            set_clauses = []
            values = [settings_id]
            param_index = 2

            for key, value in updates.items():
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE push_notification_settings
                    SET {', '.join(set_clauses)}, updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    *values
                )
                if not row:
                    raise PushSettingsNotFoundError(f"Push settings {settings_id} not found")
                return self._map_push_settings(row)
        except PushSettingsNotFoundError:
            raise
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to update push settings: {e}")

    # ========================================================================
    # PUSH NOTIFICATION HISTORY
    # ========================================================================

    async def create_notification(
        self, notification: PushNotification
    ) -> PushNotification:
        """
        What: Create notification record.
        Where: Notification sending.
        Why: Tracks notification history.
        """
        try:
            import json
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO push_notification_history (
                        id, user_id, setting_id, title, body, category, priority,
                        deep_link, action_type, action_data, image_url, icon_url,
                        delivery_status, scheduled_for, ttl_seconds, expires_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    RETURNING *
                    """,
                    notification.id, notification.user_id, notification.setting_id,
                    notification.title, notification.body, notification.category.value,
                    notification.priority.value, notification.deep_link, notification.action_type,
                    json.dumps(notification.action_data) if notification.action_data else None,
                    notification.image_url, notification.icon_url, notification.delivery_status.value,
                    notification.scheduled_for, notification.ttl_seconds, notification.expires_at
                )
                return self._map_notification(row)
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to create notification: {e}")

    async def get_notification(self, notification_id: UUID) -> Optional[PushNotification]:
        """Get notification by ID."""
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM push_notification_history WHERE id = $1",
                    notification_id
                )
                if row:
                    return self._map_notification(row)
                return None
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get notification: {e}")

    async def update_notification(
        self, notification_id: UUID, **updates
    ) -> PushNotification:
        """Update notification record."""
        try:
            set_clauses = []
            values = [notification_id]
            param_index = 2

            for key, value in updates.items():
                if key in ('category', 'priority', 'delivery_status') and value is not None:
                    value = value.value if hasattr(value, 'value') else value
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE push_notification_history
                    SET {', '.join(set_clauses)}
                    WHERE id = $1
                    RETURNING *
                    """,
                    *values
                )
                if not row:
                    raise NotificationNotFoundError(f"Notification {notification_id} not found")
                return self._map_notification(row)
        except NotificationNotFoundError:
            raise
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to update notification: {e}")

    async def get_user_notifications(
        self, user_id: UUID, limit: int = 50
    ) -> list[PushNotification]:
        """Get notifications for user."""
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM push_notification_history
                    WHERE user_id = $1
                    ORDER BY created_at DESC LIMIT $2
                    """,
                    user_id, limit
                )
                return [self._map_notification(row) for row in rows]
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get user notifications: {e}")

    # ========================================================================
    # TOUCH GESTURE SETTINGS
    # ========================================================================

    async def create_gesture_settings(
        self, settings: TouchGestureSettings
    ) -> TouchGestureSettings:
        """Create touch gesture settings."""
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO touch_gesture_settings (
                        id, user_id, device_preference_id,
                        swipe_left_action, swipe_right_action, swipe_down_action, swipe_up_action,
                        double_tap_action, long_press_action, pinch_action, two_finger_swipe_action,
                        swipe_threshold_px, long_press_duration_ms, double_tap_interval_ms,
                        scroll_sensitivity, gesture_feedback_enabled, gesture_hints_enabled,
                        simplified_gestures, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                    RETURNING *
                    """,
                    settings.id, settings.user_id, settings.device_preference_id,
                    settings.swipe_left_action, settings.swipe_right_action,
                    settings.swipe_down_action, settings.swipe_up_action,
                    settings.double_tap_action, settings.long_press_action,
                    settings.pinch_action, settings.two_finger_swipe_action,
                    settings.swipe_threshold_px, settings.long_press_duration_ms,
                    settings.double_tap_interval_ms, settings.scroll_sensitivity,
                    settings.gesture_feedback_enabled, settings.gesture_hints_enabled,
                    settings.simplified_gestures, settings.is_active
                )
                return self._map_gesture_settings(row)
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to create gesture settings: {e}")

    async def get_gesture_settings(
        self, user_id: UUID, device_preference_id: Optional[UUID] = None
    ) -> Optional[TouchGestureSettings]:
        """Get gesture settings."""
        try:
            async with self._pool.acquire() as conn:
                if device_preference_id:
                    row = await conn.fetchrow(
                        """
                        SELECT * FROM touch_gesture_settings
                        WHERE user_id = $1 AND device_preference_id = $2 AND is_active = true
                        """,
                        user_id, device_preference_id
                    )
                else:
                    row = await conn.fetchrow(
                        """
                        SELECT * FROM touch_gesture_settings
                        WHERE user_id = $1 AND is_active = true
                        ORDER BY updated_at DESC LIMIT 1
                        """,
                        user_id
                    )
                if row:
                    return self._map_gesture_settings(row)
                return None
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get gesture settings: {e}")

    async def update_gesture_settings(
        self, settings_id: UUID, **updates
    ) -> TouchGestureSettings:
        """Update gesture settings."""
        try:
            set_clauses = []
            values = [settings_id]
            param_index = 2

            for key, value in updates.items():
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE touch_gesture_settings
                    SET {', '.join(set_clauses)}, updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    *values
                )
                if not row:
                    raise MobileExperienceDAOError(f"Gesture settings {settings_id} not found")
                return self._map_gesture_settings(row)
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to update gesture settings: {e}")

    # ========================================================================
    # BANDWIDTH USAGE
    # ========================================================================

    async def record_bandwidth_usage(
        self, usage: BandwidthUsage
    ) -> BandwidthUsage:
        """Record bandwidth usage."""
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO bandwidth_usage (
                        id, user_id, device_preference_id, session_id,
                        usage_date, usage_hour,
                        video_bytes_downloaded, image_bytes_downloaded, document_bytes_downloaded,
                        api_bytes_downloaded, other_bytes_downloaded, total_bytes_downloaded,
                        bytes_uploaded, connection_type, is_metered,
                        bytes_saved_compression, bytes_saved_caching, bytes_saved_data_saver
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                    ON CONFLICT (user_id, device_preference_id, usage_date, usage_hour) DO UPDATE SET
                        video_bytes_downloaded = bandwidth_usage.video_bytes_downloaded + EXCLUDED.video_bytes_downloaded,
                        image_bytes_downloaded = bandwidth_usage.image_bytes_downloaded + EXCLUDED.image_bytes_downloaded,
                        total_bytes_downloaded = bandwidth_usage.total_bytes_downloaded + EXCLUDED.total_bytes_downloaded
                    RETURNING *
                    """,
                    usage.id, usage.user_id, usage.device_preference_id, usage.session_id,
                    usage.usage_date, usage.usage_hour,
                    usage.video_bytes_downloaded, usage.image_bytes_downloaded,
                    usage.document_bytes_downloaded, usage.api_bytes_downloaded,
                    usage.other_bytes_downloaded, usage.total_bytes_downloaded,
                    usage.bytes_uploaded,
                    usage.connection_type.value if usage.connection_type else None,
                    usage.is_metered, usage.bytes_saved_compression,
                    usage.bytes_saved_caching, usage.bytes_saved_data_saver
                )
                return self._map_bandwidth_usage(row)
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to record bandwidth usage: {e}")

    async def get_user_bandwidth_usage(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[BandwidthUsage]:
        """Get bandwidth usage for date range."""
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM bandwidth_usage
                    WHERE user_id = $1 AND usage_date BETWEEN $2 AND $3
                    ORDER BY usage_date, usage_hour
                    """,
                    user_id, start_date, end_date
                )
                return [self._map_bandwidth_usage(row) for row in rows]
        except Exception as e:
            raise MobileExperienceDAOError(f"Failed to get bandwidth usage: {e}")

    # ========================================================================
    # MAPPING METHODS
    # ========================================================================

    def _map_device_preference(self, row) -> UserDevicePreference:
        """Map database row to UserDevicePreference entity."""
        return UserDevicePreference(
            id=row['id'],
            user_id=row['user_id'],
            device_id=row['device_id'],
            device_type=DeviceType(row['device_type']),
            device_name=row['device_name'],
            os_name=row['os_name'],
            os_version=row['os_version'],
            browser_name=row['browser_name'],
            browser_version=row['browser_version'],
            screen_width=row['screen_width'],
            screen_height=row['screen_height'],
            pixel_ratio=row['pixel_ratio'],
            preferred_theme=Theme(row['preferred_theme']) if row['preferred_theme'] else Theme.SYSTEM,
            font_size_preference=FontSize(row['font_size_preference']) if row['font_size_preference'] else FontSize.MEDIUM,
            reduced_motion=row['reduced_motion'] or False,
            high_contrast=row['high_contrast'] or False,
            compact_mode=row['compact_mode'] or False,
            sidebar_collapsed=row['sidebar_collapsed'] or False,
            preferred_navigation=NavigationType(row['preferred_navigation']) if row['preferred_navigation'] else NavigationType.AUTO,
            gesture_navigation=row['gesture_navigation'] if row['gesture_navigation'] is not None else True,
            haptic_feedback=row['haptic_feedback'] if row['haptic_feedback'] is not None else True,
            data_saver_mode=row['data_saver_mode'] or False,
            auto_play_video=row['auto_play_video'] if row['auto_play_video'] is not None else True,
            video_quality_preference=VideoQuality(row['video_quality_preference']) if row['video_quality_preference'] else VideoQuality.AUTO,
            image_quality_preference=ImageQuality(row['image_quality_preference']) if row['image_quality_preference'] else ImageQuality.AUTO,
            offline_enabled=row['offline_enabled'] if row['offline_enabled'] is not None else True,
            max_offline_storage_mb=row['max_offline_storage_mb'] or 1000,
            auto_download_wifi_only=row['auto_download_wifi_only'] if row['auto_download_wifi_only'] is not None else True,
            is_primary_device=row['is_primary_device'] or False,
            last_active_at=row['last_active_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_session(self, row) -> MobileSession:
        """Map database row to MobileSession entity."""
        return MobileSession(
            id=row['id'],
            user_id=row['user_id'],
            device_preference_id=row['device_preference_id'],
            session_token=row['session_token'],
            app_version=row['app_version'],
            build_number=row['build_number'],
            platform=Platform(row['platform']),
            connection_type=ConnectionType(row['connection_type']) if row['connection_type'] else None,
            ip_address=str(row['ip_address']) if row['ip_address'] else None,
            country_code=row['country_code'],
            timezone=row['timezone'],
            session_start=row['session_start'],
            session_end=row['session_end'],
            duration_seconds=row['duration_seconds'],
            screen_views=row['screen_views'] or 0,
            interactions=row['interactions'] or 0,
            app_launch_time_ms=row['app_launch_time_ms'],
            avg_screen_load_time_ms=row['avg_screen_load_time_ms'],
            memory_warnings=row['memory_warnings'] or 0,
            crashes=row['crashes'] or 0,
            content_items_viewed=row['content_items_viewed'] or 0,
            videos_watched=row['videos_watched'] or 0,
            quizzes_taken=row['quizzes_taken'] or 0,
            labs_started=row['labs_started'] or 0,
            is_background=row['is_background'] or False,
            is_offline=row['is_offline'] or False,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_offline_sync(self, row) -> OfflineContentSync:
        """Map database row to OfflineContentSync entity."""
        import json
        progress_data = row['offline_progress_data']
        if isinstance(progress_data, str):
            progress_data = json.loads(progress_data)

        return OfflineContentSync(
            id=row['id'],
            user_id=row['user_id'],
            device_id=row['device_id'],
            content_type=ContentType(row['content_type']),
            content_id=row['content_id'],
            content_version=row['content_version'],
            sync_status=SyncStatus(row['sync_status']),
            sync_priority=row['sync_priority'] or 5,
            storage_size_bytes=row['storage_size_bytes'],
            compressed_size_bytes=row['compressed_size_bytes'],
            storage_path=row['storage_path'],
            checksum=row['checksum'],
            queued_at=row['queued_at'],
            download_started_at=row['download_started_at'],
            download_completed_at=row['download_completed_at'],
            last_synced_at=row['last_synced_at'],
            expires_at=row['expires_at'],
            retry_count=row['retry_count'] or 0,
            max_retries=row['max_retries'] or 3,
            last_error=row['last_error'],
            has_offline_progress=row['has_offline_progress'] or False,
            offline_progress_data=progress_data,
            progress_synced_at=row['progress_synced_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_push_settings(self, row) -> PushNotificationSettings:
        """Map database row to PushNotificationSettings entity."""
        return PushNotificationSettings(
            id=row['id'],
            user_id=row['user_id'],
            device_preference_id=row['device_preference_id'],
            fcm_token=row['fcm_token'],
            apns_token=row['apns_token'],
            web_push_endpoint=row['web_push_endpoint'],
            web_push_p256dh=row['web_push_p256dh'],
            web_push_auth=row['web_push_auth'],
            notifications_enabled=row['notifications_enabled'] if row['notifications_enabled'] is not None else True,
            quiet_hours_enabled=row['quiet_hours_enabled'] or False,
            quiet_hours_start=row['quiet_hours_start'],
            quiet_hours_end=row['quiet_hours_end'],
            quiet_hours_timezone=row['quiet_hours_timezone'],
            course_updates=row['course_updates'] if row['course_updates'] is not None else True,
            quiz_reminders=row['quiz_reminders'] if row['quiz_reminders'] is not None else True,
            assignment_deadlines=row['assignment_deadlines'] if row['assignment_deadlines'] is not None else True,
            discussion_replies=row['discussion_replies'] if row['discussion_replies'] is not None else True,
            instructor_messages=row['instructor_messages'] if row['instructor_messages'] is not None else True,
            certificate_earned=row['certificate_earned'] if row['certificate_earned'] is not None else True,
            new_content_available=row['new_content_available'] if row['new_content_available'] is not None else True,
            promotion_offers=row['promotion_offers'] or False,
            system_announcements=row['system_announcements'] if row['system_announcements'] is not None else True,
            group_notifications=row['group_notifications'] if row['group_notifications'] is not None else True,
            show_preview=row['show_preview'] if row['show_preview'] is not None else True,
            sound_enabled=row['sound_enabled'] if row['sound_enabled'] is not None else True,
            vibration_enabled=row['vibration_enabled'] if row['vibration_enabled'] is not None else True,
            badge_count_enabled=row['badge_count_enabled'] if row['badge_count_enabled'] is not None else True,
            max_notifications_per_hour=row['max_notifications_per_hour'] or 10,
            digest_mode=row['digest_mode'] or False,
            digest_time=row['digest_time'],
            token_updated_at=row['token_updated_at'],
            last_notification_at=row['last_notification_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_notification(self, row) -> PushNotification:
        """Map database row to PushNotification entity."""
        import json
        action_data = row['action_data']
        if isinstance(action_data, str):
            action_data = json.loads(action_data)

        return PushNotification(
            id=row['id'],
            user_id=row['user_id'],
            setting_id=row['setting_id'],
            title=row['title'],
            body=row['body'],
            category=NotificationCategory(row['category']),
            priority=NotificationPriority(row['priority']),
            deep_link=row['deep_link'],
            action_type=row['action_type'],
            action_data=action_data,
            image_url=row['image_url'],
            icon_url=row['icon_url'],
            delivery_status=DeliveryStatus(row['delivery_status']),
            platform_message_id=row['platform_message_id'],
            opened_at=row['opened_at'],
            action_taken=row['action_taken'],
            dismissed_at=row['dismissed_at'],
            error_code=row['error_code'],
            error_message=row['error_message'],
            retry_count=row['retry_count'] or 0,
            scheduled_for=row['scheduled_for'],
            sent_at=row['sent_at'],
            delivered_at=row['delivered_at'],
            ttl_seconds=row['ttl_seconds'] or 86400,
            expires_at=row['expires_at'],
            created_at=row['created_at'],
        )

    def _map_gesture_settings(self, row) -> TouchGestureSettings:
        """Map database row to TouchGestureSettings entity."""
        return TouchGestureSettings(
            id=row['id'],
            user_id=row['user_id'],
            device_preference_id=row['device_preference_id'],
            swipe_left_action=row['swipe_left_action'] or 'next_item',
            swipe_right_action=row['swipe_right_action'] or 'previous_item',
            swipe_down_action=row['swipe_down_action'] or 'refresh',
            swipe_up_action=row['swipe_up_action'] or 'scroll_up',
            double_tap_action=row['double_tap_action'] or 'toggle_fullscreen',
            long_press_action=row['long_press_action'] or 'context_menu',
            pinch_action=row['pinch_action'] or 'zoom',
            two_finger_swipe_action=row['two_finger_swipe_action'] or 'navigate_back',
            swipe_threshold_px=row['swipe_threshold_px'] or 50,
            long_press_duration_ms=row['long_press_duration_ms'] or 500,
            double_tap_interval_ms=row['double_tap_interval_ms'] or 300,
            scroll_sensitivity=row['scroll_sensitivity'] or Decimal("1.0"),
            gesture_feedback_enabled=row['gesture_feedback_enabled'] if row['gesture_feedback_enabled'] is not None else True,
            gesture_hints_enabled=row['gesture_hints_enabled'] if row['gesture_hints_enabled'] is not None else True,
            simplified_gestures=row['simplified_gestures'] or False,
            is_active=row['is_active'] if row['is_active'] is not None else True,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_bandwidth_usage(self, row) -> BandwidthUsage:
        """Map database row to BandwidthUsage entity."""
        return BandwidthUsage(
            id=row['id'],
            user_id=row['user_id'],
            device_preference_id=row['device_preference_id'],
            session_id=row['session_id'],
            usage_date=row['usage_date'],
            usage_hour=row['usage_hour'],
            video_bytes_downloaded=row['video_bytes_downloaded'] or 0,
            image_bytes_downloaded=row['image_bytes_downloaded'] or 0,
            document_bytes_downloaded=row['document_bytes_downloaded'] or 0,
            api_bytes_downloaded=row['api_bytes_downloaded'] or 0,
            other_bytes_downloaded=row['other_bytes_downloaded'] or 0,
            total_bytes_downloaded=row['total_bytes_downloaded'] or 0,
            bytes_uploaded=row['bytes_uploaded'] or 0,
            connection_type=ConnectionType(row['connection_type']) if row['connection_type'] else None,
            is_metered=row['is_metered'],
            bytes_saved_compression=row['bytes_saved_compression'] or 0,
            bytes_saved_caching=row['bytes_saved_caching'] or 0,
            bytes_saved_data_saver=row['bytes_saved_data_saver'] or 0,
            created_at=row['created_at'],
        )
