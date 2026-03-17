"""
Mobile Experience Service

What: Service layer for mobile experience and responsive design operations.
Where: Application layer orchestrating mobile features business logic.
Why: Provides:
     1. Device registration and preference management
     2. Mobile session tracking and analytics
     3. Offline content synchronization
     4. Push notification delivery
     5. Bandwidth-aware content optimization
     6. Touch gesture customization
"""

from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

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
    Breakpoint,
)
from data_access.mobile_experience_dao import (
    MobileExperienceDAO,
    MobileExperienceDAOError,
    DevicePreferenceNotFoundError,
    MobileSessionNotFoundError,
    OfflineSyncNotFoundError,
    PushSettingsNotFoundError,
    NotificationNotFoundError,
)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class MobileExperienceServiceError(Exception):
    """
    What: Base exception for mobile experience service operations.
    Where: All service methods that encounter errors.
    Why: Consistent error handling for service operations.
    """
    pass


class DeviceRegistrationError(MobileExperienceServiceError):
    """
    What: Raised when device registration fails.
    Where: Device registration flow.
    Why: Distinguishes registration errors.
    """
    pass


class SessionError(MobileExperienceServiceError):
    """
    What: Raised when session operations fail.
    Where: Session management.
    Why: Distinguishes session errors.
    """
    pass


class OfflineSyncError(MobileExperienceServiceError):
    """
    What: Raised when offline sync fails.
    Where: Content synchronization.
    Why: Distinguishes sync errors.
    """
    pass


class NotificationDeliveryError(MobileExperienceServiceError):
    """
    What: Raised when notification delivery fails.
    Where: Push notification sending.
    Why: Distinguishes delivery errors.
    """
    pass


class StorageLimitExceededError(MobileExperienceServiceError):
    """
    What: Raised when storage limit is exceeded.
    Where: Offline content download.
    Why: Prevents over-downloading.
    """
    pass


# ============================================================================
# SERVICE CLASS
# ============================================================================

class MobileExperienceService:
    """
    What: Service for mobile experience operations.
    Where: Application layer for user management service.
    Why: Orchestrates mobile features business logic.
    """

    def __init__(self, dao: MobileExperienceDAO, push_provider=None, cache=None):
        """
        What: Initialize service with DAO and optional providers.
        Where: Service initialization.
        Why: Dependency injection for testability.
        """
        self._dao = dao
        self._push_provider = push_provider
        self._cache = cache

    # ========================================================================
    # DEVICE PREFERENCES
    # ========================================================================

    async def register_device(
        self, user_id: UUID, device_id: str, device_type: DeviceType,
        device_name: Optional[str] = None, screen_width: Optional[int] = None,
        screen_height: Optional[int] = None, **device_info
    ) -> UserDevicePreference:
        """
        What: Register or update a user device.
        Where: App launch or device detection.
        Why: Enables device-specific experience.
        """
        try:
            preference = UserDevicePreference(
                user_id=user_id,
                device_id=device_id,
                device_type=device_type,
                device_name=device_name,
                screen_width=screen_width,
                screen_height=screen_height,
                last_active_at=datetime.now(),
                **device_info
            )
            return await self._dao.create_device_preference(preference)
        except MobileExperienceDAOError as e:
            raise DeviceRegistrationError(f"Failed to register device: {e}")

    async def get_device_preference(
        self, user_id: UUID, device_id: str
    ) -> Optional[UserDevicePreference]:
        """
        What: Get device preference.
        Where: Device identification.
        Why: Retrieves device settings.
        """
        try:
            return await self._dao.get_device_preference(user_id, device_id)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get device preference: {e}")

    async def get_user_devices(self, user_id: UUID) -> list[UserDevicePreference]:
        """
        What: Get all devices for user.
        Where: Device management.
        Why: Lists registered devices.
        """
        try:
            return await self._dao.get_user_devices(user_id)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get user devices: {e}")

    async def update_device_preference(
        self, preference_id: UUID, **updates
    ) -> UserDevicePreference:
        """
        What: Update device preference.
        Where: Settings changes.
        Why: Saves user preferences.
        """
        try:
            return await self._dao.update_device_preference(preference_id, **updates)
        except DevicePreferenceNotFoundError:
            raise MobileExperienceServiceError(f"Device preference {preference_id} not found")
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to update device preference: {e}")

    async def set_primary_device(
        self, user_id: UUID, device_id: str
    ) -> UserDevicePreference:
        """
        What: Set device as primary.
        Where: Device management.
        Why: Designates main device.
        """
        try:
            # First, unset any existing primary device
            devices = await self._dao.get_user_devices(user_id)
            for device in devices:
                if device.is_primary_device and device.device_id != device_id:
                    await self._dao.update_device_preference(
                        device.id, is_primary_device=False
                    )

            # Set new primary device
            preference = await self._dao.get_device_preference(user_id, device_id)
            if not preference:
                raise MobileExperienceServiceError(f"Device {device_id} not found")

            return await self._dao.update_device_preference(
                preference.id, is_primary_device=True
            )
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to set primary device: {e}")

    async def remove_device(self, preference_id: UUID) -> bool:
        """
        What: Remove a device.
        Where: Device management.
        Why: Unregisters device.
        """
        try:
            return await self._dao.delete_device_preference(preference_id)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to remove device: {e}")

    async def get_optimal_content_settings(
        self, user_id: UUID, device_id: str
    ) -> dict[str, Any]:
        """
        What: Get optimal content settings for device.
        Where: Content loading decisions.
        Why: Provides bandwidth-aware settings.
        """
        try:
            preference = await self._dao.get_device_preference(user_id, device_id)
            if not preference:
                return {
                    "video_quality": "auto",
                    "image_quality": "auto",
                    "lazy_load": True,
                    "preload": False,
                }

            return {
                "video_quality": preference.video_quality_preference.value,
                "image_quality": preference.image_quality_preference.value,
                "auto_play": preference.auto_play_video,
                "data_saver": preference.data_saver_mode,
                "lazy_load": True,
                "preload": not preference.data_saver_mode,
                "reduce_quality": preference.should_reduce_quality(),
                "breakpoint": preference.get_breakpoint().value if preference.get_breakpoint() else None,
            }
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get content settings: {e}")

    # ========================================================================
    # MOBILE SESSIONS
    # ========================================================================

    async def start_session(
        self, session_token: str, platform: Platform,
        user_id: Optional[UUID] = None, device_preference_id: Optional[UUID] = None,
        **session_info
    ) -> MobileSession:
        """
        What: Start a new mobile session.
        Where: App launch.
        Why: Tracks mobile app usage.
        """
        try:
            session = MobileSession(
                session_token=session_token,
                platform=platform,
                user_id=user_id,
                device_preference_id=device_preference_id,
                session_start=datetime.now(),
                **session_info
            )
            return await self._dao.create_session(session)
        except MobileExperienceDAOError as e:
            raise SessionError(f"Failed to start session: {e}")

    async def get_session(self, session_id: UUID) -> Optional[MobileSession]:
        """
        What: Get session by ID.
        Where: Session lookup.
        Why: Retrieves session data.
        """
        try:
            return await self._dao.get_session(session_id)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get session: {e}")

    async def get_session_by_token(self, token: str) -> Optional[MobileSession]:
        """
        What: Get session by token.
        Where: Token validation.
        Why: Validates session tokens.
        """
        try:
            return await self._dao.get_session_by_token(token)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get session: {e}")

    async def update_session_metrics(
        self, session_id: UUID, **metrics
    ) -> MobileSession:
        """
        What: Update session metrics.
        Where: Activity tracking.
        Why: Records session engagement.
        """
        try:
            return await self._dao.update_session(session_id, **metrics)
        except MobileSessionNotFoundError:
            raise SessionError(f"Session {session_id} not found")
        except MobileExperienceDAOError as e:
            raise SessionError(f"Failed to update session: {e}")

    async def end_session(self, session_id: UUID) -> MobileSession:
        """
        What: End a mobile session.
        Where: App close or background.
        Why: Calculates final metrics.
        """
        try:
            session = await self._dao.get_session(session_id)
            if not session:
                raise SessionError(f"Session {session_id} not found")

            session.end_session()
            return await self._dao.update_session(
                session_id,
                session_end=session.session_end,
                duration_seconds=session.duration_seconds
            )
        except MobileExperienceDAOError as e:
            raise SessionError(f"Failed to end session: {e}")

    async def record_screen_view(self, session_id: UUID) -> MobileSession:
        """
        What: Record a screen view.
        Where: Screen navigation.
        Why: Tracks screen views.
        """
        try:
            session = await self._dao.get_session(session_id)
            if not session:
                raise SessionError(f"Session {session_id} not found")

            return await self._dao.update_session(
                session_id, screen_views=session.screen_views + 1
            )
        except MobileExperienceDAOError as e:
            raise SessionError(f"Failed to record screen view: {e}")

    async def get_user_sessions(
        self, user_id: UUID, limit: int = 50
    ) -> list[MobileSession]:
        """
        What: Get sessions for user.
        Where: Session history.
        Why: Lists mobile sessions.
        """
        try:
            return await self._dao.get_user_sessions(user_id, limit)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get sessions: {e}")

    # ========================================================================
    # OFFLINE SYNC
    # ========================================================================

    async def queue_content_for_offline(
        self, user_id: UUID, device_id: str, content_type: ContentType,
        content_id: UUID, priority: int = 5, **sync_info
    ) -> OfflineContentSync:
        """
        What: Queue content for offline download.
        Where: Content saving.
        Why: Enables offline access.
        """
        try:
            # Check storage limits
            preference = await self._dao.get_device_preference(user_id, device_id)
            if preference:
                storage_size = sync_info.get('storage_size_bytes', 0)
                current_usage = await self._get_offline_storage_usage(user_id, device_id)
                max_storage = preference.max_offline_storage_mb * 1024 * 1024

                if current_usage + storage_size > max_storage:
                    raise StorageLimitExceededError(
                        f"Storage limit exceeded. Current: {current_usage}, Max: {max_storage}"
                    )

            sync = OfflineContentSync(
                user_id=user_id,
                device_id=device_id,
                content_type=content_type,
                content_id=content_id,
                sync_priority=priority,
                queued_at=datetime.now(),
                **sync_info
            )
            return await self._dao.create_offline_sync(sync)
        except StorageLimitExceededError:
            raise
        except MobileExperienceDAOError as e:
            raise OfflineSyncError(f"Failed to queue content: {e}")

    async def _get_offline_storage_usage(
        self, user_id: UUID, device_id: str
    ) -> int:
        """Calculate total offline storage usage."""
        try:
            syncs = await self._dao.get_pending_syncs(user_id, device_id, limit=1000)
            return sum(s.storage_size_bytes or 0 for s in syncs if s.is_available_offline())
        except:
            return 0

    async def get_offline_content(
        self, user_id: UUID, device_id: str, content_type: ContentType, content_id: UUID
    ) -> Optional[OfflineContentSync]:
        """
        What: Get offline content sync status.
        Where: Content availability check.
        Why: Checks if content is available offline.
        """
        try:
            return await self._dao.get_offline_sync(
                user_id, device_id, content_type, content_id
            )
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get offline content: {e}")

    async def get_pending_downloads(
        self, user_id: UUID, device_id: str, limit: int = 50
    ) -> list[OfflineContentSync]:
        """
        What: Get pending download queue.
        Where: Download manager.
        Why: Lists items to download.
        """
        try:
            return await self._dao.get_pending_syncs(user_id, device_id, limit)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get pending downloads: {e}")

    async def mark_download_started(self, sync_id: UUID) -> OfflineContentSync:
        """
        What: Mark download as started.
        Where: Download initiation.
        Why: Tracks download progress.
        """
        try:
            return await self._dao.update_offline_sync(
                sync_id,
                sync_status=SyncStatus.DOWNLOADING,
                download_started_at=datetime.now()
            )
        except OfflineSyncNotFoundError:
            raise OfflineSyncError(f"Offline sync {sync_id} not found")
        except MobileExperienceDAOError as e:
            raise OfflineSyncError(f"Failed to update download status: {e}")

    async def mark_download_completed(
        self, sync_id: UUID, storage_path: str, checksum: Optional[str] = None,
        compressed_size: Optional[int] = None
    ) -> OfflineContentSync:
        """
        What: Mark download as completed.
        Where: Download completion.
        Why: Updates sync status.
        """
        try:
            return await self._dao.update_offline_sync(
                sync_id,
                sync_status=SyncStatus.DOWNLOADED,
                download_completed_at=datetime.now(),
                storage_path=storage_path,
                checksum=checksum,
                compressed_size_bytes=compressed_size
            )
        except OfflineSyncNotFoundError:
            raise OfflineSyncError(f"Offline sync {sync_id} not found")
        except MobileExperienceDAOError as e:
            raise OfflineSyncError(f"Failed to mark download completed: {e}")

    async def mark_download_failed(
        self, sync_id: UUID, error: str
    ) -> OfflineContentSync:
        """
        What: Mark download as failed.
        Where: Download error handling.
        Why: Tracks failures for retry.
        """
        try:
            sync = await self._dao.get_offline_sync_by_id(sync_id) if hasattr(self._dao, 'get_offline_sync_by_id') else None
            retry_count = (sync.retry_count + 1) if sync else 1

            return await self._dao.update_offline_sync(
                sync_id,
                sync_status=SyncStatus.ERROR,
                last_error=error,
                retry_count=retry_count
            )
        except MobileExperienceDAOError as e:
            raise OfflineSyncError(f"Failed to mark download failed: {e}")

    async def sync_offline_progress(
        self, sync_id: UUID, progress_data: dict[str, Any]
    ) -> OfflineContentSync:
        """
        What: Sync offline progress to server.
        Where: Reconnection.
        Why: Preserves offline work.
        """
        try:
            return await self._dao.update_offline_sync(
                sync_id,
                has_offline_progress=True,
                offline_progress_data=progress_data,
                progress_synced_at=datetime.now(),
                sync_status=SyncStatus.SYNCED
            )
        except OfflineSyncNotFoundError:
            raise OfflineSyncError(f"Offline sync {sync_id} not found")
        except MobileExperienceDAOError as e:
            raise OfflineSyncError(f"Failed to sync progress: {e}")

    async def remove_offline_content(self, sync_id: UUID) -> bool:
        """
        What: Remove offline content.
        Where: Storage cleanup.
        Why: Frees storage space.
        """
        try:
            return await self._dao.delete_offline_sync(sync_id)
        except MobileExperienceDAOError as e:
            raise OfflineSyncError(f"Failed to remove offline content: {e}")

    # ========================================================================
    # PUSH NOTIFICATIONS
    # ========================================================================

    async def configure_push_notifications(
        self, user_id: UUID, device_preference_id: Optional[UUID] = None,
        fcm_token: Optional[str] = None, apns_token: Optional[str] = None,
        **settings
    ) -> PushNotificationSettings:
        """
        What: Configure push notifications.
        Where: Notification setup.
        Why: Stores notification preferences.
        """
        try:
            push_settings = PushNotificationSettings(
                user_id=user_id,
                device_preference_id=device_preference_id,
                fcm_token=fcm_token,
                apns_token=apns_token,
                token_updated_at=datetime.now() if fcm_token or apns_token else None,
                **settings
            )
            return await self._dao.create_push_settings(push_settings)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to configure notifications: {e}")

    async def get_push_settings(
        self, user_id: UUID, device_preference_id: Optional[UUID] = None
    ) -> Optional[PushNotificationSettings]:
        """
        What: Get push notification settings.
        Where: Notification sending.
        Why: Retrieves preferences.
        """
        try:
            return await self._dao.get_push_settings(user_id, device_preference_id)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get push settings: {e}")

    async def update_push_settings(
        self, settings_id: UUID, **updates
    ) -> PushNotificationSettings:
        """
        What: Update push settings.
        Where: Settings changes.
        Why: Saves notification preferences.
        """
        try:
            return await self._dao.update_push_settings(settings_id, **updates)
        except PushSettingsNotFoundError:
            raise MobileExperienceServiceError(f"Push settings {settings_id} not found")
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to update push settings: {e}")

    async def update_push_token(
        self, settings_id: UUID, fcm_token: Optional[str] = None,
        apns_token: Optional[str] = None
    ) -> PushNotificationSettings:
        """
        What: Update push token.
        Where: Token refresh.
        Why: Keeps tokens current.
        """
        updates = {"token_updated_at": datetime.now()}
        if fcm_token:
            updates["fcm_token"] = fcm_token
        if apns_token:
            updates["apns_token"] = apns_token

        return await self.update_push_settings(settings_id, **updates)

    async def send_notification(
        self, user_id: UUID, title: str, body: str, category: NotificationCategory,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        deep_link: Optional[str] = None, **notification_data
    ) -> PushNotification:
        """
        What: Send push notification.
        Where: Notification triggers.
        Why: Delivers notifications to user.
        """
        try:
            # Get push settings
            settings = await self._dao.get_push_settings(user_id)
            if not settings or not settings.has_valid_token():
                raise NotificationDeliveryError(f"No valid push token for user {user_id}")

            # Check if category is enabled
            if not settings.can_send_notification(category):
                raise NotificationDeliveryError(
                    f"Notifications disabled for category {category.value}"
                )

            # Create notification record
            notification = PushNotification(
                user_id=user_id,
                setting_id=settings.id,
                title=title,
                body=body,
                category=category,
                priority=priority,
                deep_link=deep_link,
                **notification_data
            )

            # Save to history
            notification = await self._dao.create_notification(notification)

            # Send via provider if available
            if self._push_provider:
                try:
                    message_id = await self._push_provider.send(
                        token=settings.fcm_token or settings.apns_token,
                        title=title,
                        body=body,
                        data=notification_data.get('action_data', {}),
                        priority=priority.value,
                    )
                    notification.mark_sent(message_id)
                    await self._dao.update_notification(
                        notification.id,
                        delivery_status=DeliveryStatus.SENT,
                        sent_at=notification.sent_at,
                        platform_message_id=notification.platform_message_id,
                        expires_at=notification.expires_at
                    )
                except Exception as e:
                    notification.mark_failed("SEND_ERROR", str(e))
                    await self._dao.update_notification(
                        notification.id,
                        delivery_status=DeliveryStatus.FAILED,
                        error_code=notification.error_code,
                        error_message=notification.error_message
                    )

            return notification
        except NotificationDeliveryError:
            raise
        except MobileExperienceDAOError as e:
            raise NotificationDeliveryError(f"Failed to send notification: {e}")

    async def mark_notification_opened(
        self, notification_id: UUID, action: Optional[str] = None
    ) -> PushNotification:
        """
        What: Mark notification as opened.
        Where: Notification tap.
        Why: Tracks engagement.
        """
        try:
            return await self._dao.update_notification(
                notification_id,
                opened_at=datetime.now(),
                action_taken=action
            )
        except NotificationNotFoundError:
            raise MobileExperienceServiceError(f"Notification {notification_id} not found")
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to mark notification opened: {e}")

    async def get_user_notifications(
        self, user_id: UUID, limit: int = 50
    ) -> list[PushNotification]:
        """
        What: Get notifications for user.
        Where: Notification history.
        Why: Lists sent notifications.
        """
        try:
            return await self._dao.get_user_notifications(user_id, limit)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get notifications: {e}")

    # ========================================================================
    # TOUCH GESTURES
    # ========================================================================

    async def configure_gestures(
        self, user_id: UUID, device_preference_id: Optional[UUID] = None,
        **gesture_settings
    ) -> TouchGestureSettings:
        """
        What: Configure touch gesture settings.
        Where: Gesture customization.
        Why: Enables accessibility.
        """
        try:
            settings = TouchGestureSettings(
                user_id=user_id,
                device_preference_id=device_preference_id,
                **gesture_settings
            )
            return await self._dao.create_gesture_settings(settings)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to configure gestures: {e}")

    async def get_gesture_settings(
        self, user_id: UUID, device_preference_id: Optional[UUID] = None
    ) -> Optional[TouchGestureSettings]:
        """
        What: Get gesture settings.
        Where: Gesture handling.
        Why: Retrieves gesture mappings.
        """
        try:
            return await self._dao.get_gesture_settings(user_id, device_preference_id)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get gesture settings: {e}")

    async def update_gesture_settings(
        self, settings_id: UUID, **updates
    ) -> TouchGestureSettings:
        """
        What: Update gesture settings.
        Where: Customization changes.
        Why: Saves gesture preferences.
        """
        try:
            return await self._dao.update_gesture_settings(settings_id, **updates)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to update gesture settings: {e}")

    # ========================================================================
    # BANDWIDTH TRACKING
    # ========================================================================

    async def record_bandwidth_usage(
        self, user_id: UUID, usage_date: date, connection_type: Optional[ConnectionType] = None,
        device_preference_id: Optional[UUID] = None, **usage_data
    ) -> BandwidthUsage:
        """
        What: Record bandwidth usage.
        Where: Data tracking.
        Why: Enables data monitoring.
        """
        try:
            usage = BandwidthUsage(
                user_id=user_id,
                usage_date=usage_date,
                device_preference_id=device_preference_id,
                connection_type=connection_type,
                **usage_data
            )
            return await self._dao.record_bandwidth_usage(usage)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to record bandwidth usage: {e}")

    async def get_bandwidth_usage(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[BandwidthUsage]:
        """
        What: Get bandwidth usage for period.
        Where: Data monitoring.
        Why: Shows data consumption.
        """
        try:
            return await self._dao.get_user_bandwidth_usage(user_id, start_date, end_date)
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get bandwidth usage: {e}")

    async def get_bandwidth_summary(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """
        What: Get bandwidth usage summary.
        Where: Data dashboard.
        Why: Aggregated usage stats.
        """
        try:
            usage_records = await self._dao.get_user_bandwidth_usage(
                user_id, start_date, end_date
            )

            if not usage_records:
                return {
                    "total_downloaded_mb": 0,
                    "total_uploaded_mb": 0,
                    "total_saved_mb": 0,
                    "by_type": {},
                    "by_connection": {},
                }

            total_downloaded = sum(u.total_bytes_downloaded for u in usage_records)
            total_uploaded = sum(u.bytes_uploaded for u in usage_records)
            total_saved = sum(
                u.bytes_saved_compression + u.bytes_saved_caching + u.bytes_saved_data_saver
                for u in usage_records
            )

            # Aggregate by type
            video_bytes = sum(u.video_bytes_downloaded for u in usage_records)
            image_bytes = sum(u.image_bytes_downloaded for u in usage_records)
            document_bytes = sum(u.document_bytes_downloaded for u in usage_records)
            api_bytes = sum(u.api_bytes_downloaded for u in usage_records)

            # Aggregate by connection type
            by_connection = {}
            for u in usage_records:
                conn = u.connection_type.value if u.connection_type else 'unknown'
                by_connection[conn] = by_connection.get(conn, 0) + u.total_bytes_downloaded

            mb = Decimal("1048576")  # 1024 * 1024
            return {
                "total_downloaded_mb": float(Decimal(total_downloaded) / mb),
                "total_uploaded_mb": float(Decimal(total_uploaded) / mb),
                "total_saved_mb": float(Decimal(total_saved) / mb),
                "by_type": {
                    "video_mb": float(Decimal(video_bytes) / mb),
                    "image_mb": float(Decimal(image_bytes) / mb),
                    "document_mb": float(Decimal(document_bytes) / mb),
                    "api_mb": float(Decimal(api_bytes) / mb),
                },
                "by_connection": {
                    k: float(Decimal(v) / mb) for k, v in by_connection.items()
                },
            }
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get bandwidth summary: {e}")

    # ========================================================================
    # MOBILE DASHBOARD
    # ========================================================================

    async def get_mobile_dashboard(
        self, user_id: UUID, device_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        What: Get mobile experience dashboard.
        Where: Settings overview.
        Why: Single call for all mobile settings.
        """
        try:
            devices = await self._dao.get_user_devices(user_id)
            push_settings = await self._dao.get_user_push_settings(user_id)
            sessions = await self._dao.get_user_sessions(user_id, limit=5)

            current_device = None
            if device_id:
                current_device = next(
                    (d for d in devices if d.device_id == device_id), None
                )

            return {
                "devices": {
                    "count": len(devices),
                    "primary": next(
                        (d.device_id for d in devices if d.is_primary_device), None
                    ),
                    "current": current_device.device_type.value if current_device else None,
                },
                "notifications": {
                    "enabled": any(s.notifications_enabled for s in push_settings),
                    "devices_configured": len([s for s in push_settings if s.has_valid_token()]),
                },
                "offline": {
                    "enabled": current_device.offline_enabled if current_device else False,
                    "max_storage_mb": current_device.max_offline_storage_mb if current_device else 1000,
                },
                "recent_sessions": len(sessions),
                "preferences": {
                    "theme": current_device.preferred_theme.value if current_device else "system",
                    "font_size": current_device.font_size_preference.value if current_device else "medium",
                    "data_saver": current_device.data_saver_mode if current_device else False,
                } if current_device else None,
            }
        except MobileExperienceDAOError as e:
            raise MobileExperienceServiceError(f"Failed to get mobile dashboard: {e}")
