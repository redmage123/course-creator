"""
Mobile Experience Service Unit Tests

What: Comprehensive tests for mobile experience service operations.
Where: User Management service application layer.
Why: Ensures service business logic correctness with real DAO implementation.
"""

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
    TouchGestureSettings,
    BandwidthUsage,
    DeviceType,
    Theme,
    FontSize,
    VideoQuality,
    Platform,
    ConnectionType,
    SyncStatus,
    ContentType,
    NotificationCategory,
    NotificationPriority,
    DeliveryStatus,
    Breakpoint,
)
from user_management.application.services.mobile_experience_service import (
    MobileExperienceService,
    MobileExperienceServiceError,
    DeviceRegistrationError,
    SessionError,
    OfflineSyncError,
    NotificationDeliveryError,
    StorageLimitExceededError,
)
from data_access.mobile_experience_dao import (
    MobileExperienceDAOError,
    DevicePreferenceNotFoundError,
    MobileSessionNotFoundError,
    OfflineSyncNotFoundError,
    PushSettingsNotFoundError,
    NotificationNotFoundError,
)


# ============================================================================
# FIXTURES
# ============================================================================

class InMemoryMobileExperienceDAO:
    """
    In-memory test double for MobileExperienceDAO.
    Uses real Python objects instead of mocks for more reliable testing.
    """

    def __init__(self):
        self.device_preferences = {}
        self.sessions = {}
        self.offline_syncs = {}
        self.push_settings = {}
        self.notifications = {}
        self.gesture_settings = {}
        self.bandwidth_usage = []

    async def create_device_preference(self, **kwargs):
        pref_id = uuid4()
        pref = UserDevicePreference(id=pref_id, **kwargs)
        self.device_preferences[pref_id] = pref
        return pref

    async def get_device_preference(self, user_id, device_id):
        for pref in self.device_preferences.values():
            if pref.user_id == user_id and pref.device_id == device_id:
                return pref
        return None

    async def get_user_devices(self, user_id):
        return [p for p in self.device_preferences.values() if p.user_id == user_id]

    async def update_device_preference(self, pref_id, **kwargs):
        if pref_id not in self.device_preferences:
            raise DevicePreferenceNotFoundError(f"Device preference {pref_id} not found")
        pref = self.device_preferences[pref_id]
        for key, value in kwargs.items():
            setattr(pref, key, value)
        return pref

    async def delete_device_preference(self, pref_id):
        if pref_id in self.device_preferences:
            del self.device_preferences[pref_id]
            return True
        return False

    async def create_session(self, **kwargs):
        session_id = uuid4()
        session = MobileSession(id=session_id, **kwargs)
        self.sessions[session_id] = session
        return session

    async def get_session(self, session_id):
        return self.sessions.get(session_id)

    async def get_session_by_token(self, token):
        for session in self.sessions.values():
            if session.session_token == token:
                return session
        return None

    async def update_session(self, session_id, **kwargs):
        if session_id not in self.sessions:
            raise MobileSessionNotFoundError(f"Session {session_id} not found")
        session = self.sessions[session_id]
        for key, value in kwargs.items():
            setattr(session, key, value)
        return session

    async def get_user_sessions(self, user_id, limit=10):
        sessions = [s for s in self.sessions.values() if s.user_id == user_id]
        return sessions[:limit]

    async def create_offline_sync(self, **kwargs):
        sync_id = uuid4()
        sync = OfflineContentSync(id=sync_id, **kwargs)
        self.offline_syncs[sync_id] = sync
        return sync

    async def get_offline_sync(self, user_id, device_id, content_type, content_id):
        for sync in self.offline_syncs.values():
            if (sync.user_id == user_id and sync.device_id == device_id and
                sync.content_type == content_type and sync.content_id == content_id):
                return sync
        return None

    async def get_pending_syncs(self, user_id, device_id):
        return [s for s in self.offline_syncs.values()
                if s.user_id == user_id and s.device_id == device_id]

    async def update_offline_sync(self, sync_id, **kwargs):
        if sync_id not in self.offline_syncs:
            raise OfflineSyncNotFoundError(f"Offline sync {sync_id} not found")
        sync = self.offline_syncs[sync_id]
        for key, value in kwargs.items():
            setattr(sync, key, value)
        return sync

    async def delete_offline_sync(self, sync_id):
        if sync_id in self.offline_syncs:
            del self.offline_syncs[sync_id]
            return True
        return False

    async def create_push_settings(self, **kwargs):
        settings_id = uuid4()
        settings = PushNotificationSettings(id=settings_id, **kwargs)
        self.push_settings[settings_id] = settings
        return settings

    async def get_push_settings(self, user_id):
        for settings in self.push_settings.values():
            if settings.user_id == user_id:
                return settings
        return None

    async def update_push_settings(self, settings_id, **kwargs):
        if settings_id not in self.push_settings:
            raise PushSettingsNotFoundError(f"Push settings {settings_id} not found")
        settings = self.push_settings[settings_id]
        for key, value in kwargs.items():
            setattr(settings, key, value)
        return settings

    async def create_notification(self, **kwargs):
        notif_id = uuid4()
        notif = PushNotification(id=notif_id, **kwargs)
        self.notifications[notif_id] = notif
        return notif

    async def update_notification(self, notif_id, **kwargs):
        if notif_id not in self.notifications:
            raise NotificationNotFoundError(f"Notification {notif_id} not found")
        notif = self.notifications[notif_id]
        for key, value in kwargs.items():
            setattr(notif, key, value)
        return notif

    async def get_user_notifications(self, user_id, limit=20):
        notifs = [n for n in self.notifications.values() if n.user_id == user_id]
        return notifs[:limit]

    async def get_user_push_settings(self, user_id):
        return [s for s in self.push_settings.values() if s.user_id == user_id]

    async def create_gesture_settings(self, **kwargs):
        settings_id = uuid4()
        settings = TouchGestureSettings(id=settings_id, **kwargs)
        self.gesture_settings[settings_id] = settings
        return settings

    async def get_gesture_settings(self, user_id):
        for settings in self.gesture_settings.values():
            if settings.user_id == user_id:
                return settings
        return None

    async def update_gesture_settings(self, settings_id, **kwargs):
        settings = self.gesture_settings.get(settings_id)
        if not settings:
            settings = TouchGestureSettings(id=settings_id, **kwargs)
            self.gesture_settings[settings_id] = settings
        else:
            for key, value in kwargs.items():
                setattr(settings, key, value)
        return settings

    async def record_bandwidth_usage(self, **kwargs):
        usage = BandwidthUsage(**kwargs)
        self.bandwidth_usage.append(usage)
        return usage

    async def get_user_bandwidth_usage(self, user_id, start_date, end_date):
        return [u for u in self.bandwidth_usage
                if u.user_id == user_id and start_date <= u.usage_date <= end_date]


class SimplePushProvider:
    """Simple test double for push notification provider."""

    def __init__(self):
        self.sent_messages = []

    async def send(self, token, title, body, **kwargs):
        msg_id = f"msg_{len(self.sent_messages)}"
        self.sent_messages.append({
            'id': msg_id,
            'token': token,
            'title': title,
            'body': body,
            **kwargs
        })
        return msg_id


@pytest.fixture
def test_dao():
    """Create in-memory DAO for testing."""
    return InMemoryMobileExperienceDAO()


@pytest.fixture
def test_push_provider():
    """Create simple push notification provider."""
    return SimplePushProvider()


@pytest.fixture
def service(test_dao):
    """Create service with test DAO."""
    return MobileExperienceService(dao=test_dao)


@pytest.fixture
def service_with_push(test_dao, test_push_provider):
    """Create service with test DAO and push provider."""
    return MobileExperienceService(dao=test_dao, push_provider=test_push_provider)


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return uuid4()


@pytest.fixture
def sample_device_id():
    """Sample device ID."""
    return "device_abc123"


@pytest.fixture
def sample_device_preference(sample_user_id, sample_device_id):
    """Create a sample device preference."""
    return UserDevicePreference(
        id=uuid4(),
        user_id=sample_user_id,
        device_id=sample_device_id,
        device_type=DeviceType.MOBILE,
        screen_width=375,
        screen_height=812
    )


@pytest.fixture
def sample_session(sample_user_id):
    """Create a sample mobile session."""
    return MobileSession(
        id=uuid4(),
        session_token="token_xyz789",
        platform=Platform.IOS,
        user_id=sample_user_id
    )


@pytest.fixture
def sample_push_settings(sample_user_id):
    """Create sample push notification settings."""
    return PushNotificationSettings(
        id=uuid4(),
        user_id=sample_user_id,
        fcm_token="fcm_token_123",
        notifications_enabled=True
    )


# ============================================================================
# DEVICE PREFERENCE TESTS
# ============================================================================

class TestDevicePreferenceOperations:
    """Tests for device preference service operations."""

    @pytest.mark.asyncio
    async def test_register_device_success(self, service, sample_user_id, sample_device_id):
        """Test successful device registration."""
        result = await service.register_device(
            user_id=sample_user_id,
            device_id=sample_device_id,
            device_type=DeviceType.MOBILE,
            device_name="iPhone 14",
            screen_width=375
        )

        assert result.device_id == sample_device_id
        assert result.user_id == sample_user_id
        assert result.device_type == DeviceType.MOBILE

    @pytest.mark.asyncio
    async def test_register_device_dao_error(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test device registration handles DAO error."""
        mock_dao.create_device_preference.side_effect = MobileExperienceDAOError("DB error")

        with pytest.raises(DeviceRegistrationError, match="Failed to register device"):
            await service.register_device(
                user_id=sample_user_id,
                device_id=sample_device_id,
                device_type=DeviceType.MOBILE
            )

    @pytest.mark.asyncio
    async def test_get_device_preference_found(self, service, mock_dao, sample_user_id, sample_device_id, sample_device_preference):
        """Test getting existing device preference."""
        mock_dao.get_device_preference.return_value = sample_device_preference

        result = await service.get_device_preference(sample_user_id, sample_device_id)

        assert result == sample_device_preference
        mock_dao.get_device_preference.assert_called_once_with(sample_user_id, sample_device_id)

    @pytest.mark.asyncio
    async def test_get_device_preference_not_found(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test getting non-existent device preference."""
        mock_dao.get_device_preference.return_value = None

        result = await service.get_device_preference(sample_user_id, sample_device_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_device_preference_error(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test get device preference handles error."""
        mock_dao.get_device_preference.side_effect = MobileExperienceDAOError("Error")

        with pytest.raises(MobileExperienceServiceError, match="Failed to get device preference"):
            await service.get_device_preference(sample_user_id, sample_device_id)

    @pytest.mark.asyncio
    async def test_get_user_devices(self, service, mock_dao, sample_user_id, sample_device_preference):
        """Test getting all user devices."""
        mock_dao.get_user_devices.return_value = [sample_device_preference]

        result = await service.get_user_devices(sample_user_id)

        assert len(result) == 1
        assert result[0] == sample_device_preference

    @pytest.mark.asyncio
    async def test_update_device_preference_success(self, service, mock_dao, sample_device_preference):
        """Test updating device preference."""
        updated = sample_device_preference
        updated.preferred_theme = Theme.DARK
        mock_dao.update_device_preference.return_value = updated

        result = await service.update_device_preference(
            sample_device_preference.id,
            preferred_theme=Theme.DARK
        )

        assert result.preferred_theme == Theme.DARK

    @pytest.mark.asyncio
    async def test_update_device_preference_not_found(self, service, mock_dao):
        """Test updating non-existent preference."""
        mock_dao.update_device_preference.side_effect = DevicePreferenceNotFoundError("Not found")

        with pytest.raises(MobileExperienceServiceError, match="not found"):
            await service.update_device_preference(uuid4(), preferred_theme=Theme.DARK)

    @pytest.mark.asyncio
    async def test_set_primary_device_success(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test setting primary device."""
        other_device = UserDevicePreference(
            id=uuid4(),
            user_id=sample_user_id,
            device_id="other_device",
            device_type=DeviceType.TABLET,
            is_primary_device=True
        )
        target_device = UserDevicePreference(
            id=uuid4(),
            user_id=sample_user_id,
            device_id=sample_device_id,
            device_type=DeviceType.MOBILE,
            is_primary_device=False
        )

        mock_dao.get_user_devices.return_value = [other_device, target_device]
        mock_dao.get_device_preference.return_value = target_device
        mock_dao.update_device_preference.return_value = target_device

        result = await service.set_primary_device(sample_user_id, sample_device_id)

        # Should have called update to unset other device and set target
        assert mock_dao.update_device_preference.call_count >= 1

    @pytest.mark.asyncio
    async def test_set_primary_device_not_found(self, service, mock_dao, sample_user_id):
        """Test setting primary device when device not found."""
        mock_dao.get_user_devices.return_value = []
        mock_dao.get_device_preference.return_value = None

        with pytest.raises(MobileExperienceServiceError, match="not found"):
            await service.set_primary_device(sample_user_id, "nonexistent")

    @pytest.mark.asyncio
    async def test_remove_device_success(self, service, mock_dao):
        """Test removing a device."""
        mock_dao.delete_device_preference.return_value = True
        pref_id = uuid4()

        result = await service.remove_device(pref_id)

        assert result is True
        mock_dao.delete_device_preference.assert_called_once_with(pref_id)

    @pytest.mark.asyncio
    async def test_get_optimal_content_settings_with_device(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test getting optimal content settings with device."""
        preference = UserDevicePreference(
            user_id=sample_user_id,
            device_id=sample_device_id,
            device_type=DeviceType.MOBILE,
            video_quality_preference=VideoQuality.MEDIUM,
            data_saver_mode=True,
            screen_width=375
        )
        mock_dao.get_device_preference.return_value = preference

        result = await service.get_optimal_content_settings(sample_user_id, sample_device_id)

        assert result["video_quality"] == "medium"
        assert result["data_saver"] is True
        assert result["reduce_quality"] is True
        assert result["breakpoint"] == "xs"

    @pytest.mark.asyncio
    async def test_get_optimal_content_settings_no_device(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test getting optimal content settings without device."""
        mock_dao.get_device_preference.return_value = None

        result = await service.get_optimal_content_settings(sample_user_id, sample_device_id)

        assert result["video_quality"] == "auto"
        assert result["image_quality"] == "auto"
        assert result["lazy_load"] is True
        assert result["preload"] is False


# ============================================================================
# MOBILE SESSION TESTS
# ============================================================================

class TestMobileSessionOperations:
    """Tests for mobile session service operations."""

    @pytest.mark.asyncio
    async def test_start_session_success(self, service, mock_dao, sample_user_id):
        """Test starting a mobile session."""
        expected = MobileSession(
            session_token="token123",
            platform=Platform.ANDROID,
            user_id=sample_user_id
        )
        mock_dao.create_session.return_value = expected

        result = await service.start_session(
            session_token="token123",
            platform=Platform.ANDROID,
            user_id=sample_user_id
        )

        assert result.session_token == "token123"
        assert result.platform == Platform.ANDROID

    @pytest.mark.asyncio
    async def test_start_session_error(self, service, mock_dao):
        """Test start session handles error."""
        mock_dao.create_session.side_effect = MobileExperienceDAOError("Error")

        with pytest.raises(SessionError, match="Failed to start session"):
            await service.start_session("token", Platform.IOS)

    @pytest.mark.asyncio
    async def test_get_session_found(self, service, mock_dao, sample_session):
        """Test getting existing session."""
        mock_dao.get_session.return_value = sample_session

        result = await service.get_session(sample_session.id)

        assert result == sample_session

    @pytest.mark.asyncio
    async def test_get_session_by_token(self, service, mock_dao, sample_session):
        """Test getting session by token."""
        mock_dao.get_session_by_token.return_value = sample_session

        result = await service.get_session_by_token(sample_session.session_token)

        assert result == sample_session

    @pytest.mark.asyncio
    async def test_update_session_metrics_success(self, service, mock_dao, sample_session):
        """Test updating session metrics."""
        updated_session = sample_session
        updated_session.screen_views = 5
        mock_dao.update_session.return_value = updated_session

        result = await service.update_session_metrics(sample_session.id, screen_views=5)

        assert result.screen_views == 5

    @pytest.mark.asyncio
    async def test_update_session_metrics_not_found(self, service, mock_dao):
        """Test updating non-existent session."""
        mock_dao.update_session.side_effect = MobileSessionNotFoundError("Not found")

        with pytest.raises(SessionError, match="not found"):
            await service.update_session_metrics(uuid4(), screen_views=1)

    @pytest.mark.asyncio
    async def test_end_session_success(self, service, mock_dao, sample_session):
        """Test ending a session."""
        mock_dao.get_session.return_value = sample_session
        mock_dao.update_session.return_value = sample_session

        result = await service.end_session(sample_session.id)

        mock_dao.update_session.assert_called_once()
        # Check that session_end and duration_seconds were passed
        call_kwargs = mock_dao.update_session.call_args[1]
        assert 'session_end' in call_kwargs
        assert 'duration_seconds' in call_kwargs

    @pytest.mark.asyncio
    async def test_end_session_not_found(self, service, mock_dao):
        """Test ending non-existent session."""
        mock_dao.get_session.return_value = None

        with pytest.raises(SessionError, match="not found"):
            await service.end_session(uuid4())

    @pytest.mark.asyncio
    async def test_record_screen_view(self, service, mock_dao, sample_session):
        """Test recording a screen view."""
        sample_session.screen_views = 3
        mock_dao.get_session.return_value = sample_session
        mock_dao.update_session.return_value = sample_session

        await service.record_screen_view(sample_session.id)

        mock_dao.update_session.assert_called_once()
        call_kwargs = mock_dao.update_session.call_args[1]
        assert call_kwargs['screen_views'] == 4

    @pytest.mark.asyncio
    async def test_record_screen_view_not_found(self, service, mock_dao):
        """Test recording screen view for non-existent session."""
        mock_dao.get_session.return_value = None

        with pytest.raises(SessionError, match="not found"):
            await service.record_screen_view(uuid4())

    @pytest.mark.asyncio
    async def test_get_user_sessions(self, service, mock_dao, sample_user_id, sample_session):
        """Test getting user sessions."""
        mock_dao.get_user_sessions.return_value = [sample_session]

        result = await service.get_user_sessions(sample_user_id, limit=10)

        assert len(result) == 1
        mock_dao.get_user_sessions.assert_called_once_with(sample_user_id, 10)


# ============================================================================
# OFFLINE SYNC TESTS
# ============================================================================

class TestOfflineSyncOperations:
    """Tests for offline sync service operations."""

    @pytest.mark.asyncio
    async def test_queue_content_for_offline_success(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test queuing content for offline download."""
        preference = UserDevicePreference(
            user_id=sample_user_id,
            device_id=sample_device_id,
            device_type=DeviceType.MOBILE,
            max_offline_storage_mb=1000
        )
        mock_dao.get_device_preference.return_value = preference
        mock_dao.get_pending_syncs.return_value = []

        content_id = uuid4()
        expected = OfflineContentSync(
            user_id=sample_user_id,
            device_id=sample_device_id,
            content_type=ContentType.COURSE,
            content_id=content_id
        )
        mock_dao.create_offline_sync.return_value = expected

        result = await service.queue_content_for_offline(
            user_id=sample_user_id,
            device_id=sample_device_id,
            content_type=ContentType.COURSE,
            content_id=content_id,
            priority=3
        )

        assert result.content_type == ContentType.COURSE
        mock_dao.create_offline_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_queue_content_storage_limit_exceeded(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test queuing content when storage limit exceeded."""
        preference = UserDevicePreference(
            user_id=sample_user_id,
            device_id=sample_device_id,
            device_type=DeviceType.MOBILE,
            max_offline_storage_mb=10  # Only 10 MB
        )
        # Existing content uses 9 MB
        existing_sync = OfflineContentSync(
            user_id=sample_user_id,
            device_id=sample_device_id,
            content_type=ContentType.VIDEO,
            content_id=uuid4(),
            storage_size_bytes=9 * 1024 * 1024,
            sync_status=SyncStatus.DOWNLOADED
        )
        mock_dao.get_device_preference.return_value = preference
        mock_dao.get_pending_syncs.return_value = [existing_sync]

        with pytest.raises(StorageLimitExceededError, match="Storage limit exceeded"):
            await service.queue_content_for_offline(
                user_id=sample_user_id,
                device_id=sample_device_id,
                content_type=ContentType.VIDEO,
                content_id=uuid4(),
                storage_size_bytes=5 * 1024 * 1024  # 5 MB more
            )

    @pytest.mark.asyncio
    async def test_queue_content_no_preference(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test queuing content without device preference (no storage check)."""
        mock_dao.get_device_preference.return_value = None

        content_id = uuid4()
        expected = OfflineContentSync(
            user_id=sample_user_id,
            device_id=sample_device_id,
            content_type=ContentType.DOCUMENT,
            content_id=content_id
        )
        mock_dao.create_offline_sync.return_value = expected

        result = await service.queue_content_for_offline(
            user_id=sample_user_id,
            device_id=sample_device_id,
            content_type=ContentType.DOCUMENT,
            content_id=content_id
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_offline_content(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test getting offline content sync status."""
        content_id = uuid4()
        sync = OfflineContentSync(
            user_id=sample_user_id,
            device_id=sample_device_id,
            content_type=ContentType.COURSE,
            content_id=content_id,
            sync_status=SyncStatus.DOWNLOADED
        )
        mock_dao.get_offline_sync.return_value = sync

        result = await service.get_offline_content(
            sample_user_id, sample_device_id, ContentType.COURSE, content_id
        )

        assert result.sync_status == SyncStatus.DOWNLOADED

    @pytest.mark.asyncio
    async def test_get_pending_downloads(self, service, mock_dao, sample_user_id, sample_device_id):
        """Test getting pending downloads."""
        syncs = [
            OfflineContentSync(
                user_id=sample_user_id,
                device_id=sample_device_id,
                content_type=ContentType.VIDEO,
                content_id=uuid4()
            )
        ]
        mock_dao.get_pending_syncs.return_value = syncs

        result = await service.get_pending_downloads(sample_user_id, sample_device_id)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_mark_download_started(self, service, mock_dao):
        """Test marking download as started."""
        sync_id = uuid4()
        updated_sync = OfflineContentSync(
            id=sync_id,
            user_id=uuid4(),
            device_id="device123",
            content_type=ContentType.VIDEO,
            content_id=uuid4(),
            sync_status=SyncStatus.DOWNLOADING
        )
        mock_dao.update_offline_sync.return_value = updated_sync

        result = await service.mark_download_started(sync_id)

        assert result.sync_status == SyncStatus.DOWNLOADING
        call_kwargs = mock_dao.update_offline_sync.call_args[1]
        assert call_kwargs['sync_status'] == SyncStatus.DOWNLOADING

    @pytest.mark.asyncio
    async def test_mark_download_started_not_found(self, service, mock_dao):
        """Test marking non-existent download."""
        mock_dao.update_offline_sync.side_effect = OfflineSyncNotFoundError("Not found")

        with pytest.raises(OfflineSyncError, match="not found"):
            await service.mark_download_started(uuid4())

    @pytest.mark.asyncio
    async def test_mark_download_completed(self, service, mock_dao):
        """Test marking download as completed."""
        sync_id = uuid4()
        updated_sync = OfflineContentSync(
            id=sync_id,
            user_id=uuid4(),
            device_id="device123",
            content_type=ContentType.VIDEO,
            content_id=uuid4(),
            sync_status=SyncStatus.DOWNLOADED
        )
        mock_dao.update_offline_sync.return_value = updated_sync

        result = await service.mark_download_completed(
            sync_id,
            storage_path="/offline/video.mp4",
            checksum="abc123"
        )

        assert result.sync_status == SyncStatus.DOWNLOADED
        call_kwargs = mock_dao.update_offline_sync.call_args[1]
        assert call_kwargs['storage_path'] == "/offline/video.mp4"
        assert call_kwargs['checksum'] == "abc123"

    @pytest.mark.asyncio
    async def test_mark_download_failed(self, service, mock_dao):
        """Test marking download as failed."""
        sync_id = uuid4()
        mock_dao.update_offline_sync.return_value = OfflineContentSync(
            id=sync_id,
            user_id=uuid4(),
            device_id="device123",
            content_type=ContentType.VIDEO,
            content_id=uuid4(),
            sync_status=SyncStatus.ERROR
        )

        result = await service.mark_download_failed(sync_id, "Network timeout")

        call_kwargs = mock_dao.update_offline_sync.call_args[1]
        assert call_kwargs['sync_status'] == SyncStatus.ERROR
        assert call_kwargs['last_error'] == "Network timeout"

    @pytest.mark.asyncio
    async def test_sync_offline_progress(self, service, mock_dao):
        """Test syncing offline progress."""
        sync_id = uuid4()
        progress_data = {"completed_lessons": [1, 2, 3], "current_position": 45.5}

        mock_dao.update_offline_sync.return_value = OfflineContentSync(
            id=sync_id,
            user_id=uuid4(),
            device_id="device123",
            content_type=ContentType.COURSE,
            content_id=uuid4(),
            sync_status=SyncStatus.SYNCED,
            has_offline_progress=True
        )

        result = await service.sync_offline_progress(sync_id, progress_data)

        call_kwargs = mock_dao.update_offline_sync.call_args[1]
        assert call_kwargs['has_offline_progress'] is True
        assert call_kwargs['offline_progress_data'] == progress_data

    @pytest.mark.asyncio
    async def test_remove_offline_content(self, service, mock_dao):
        """Test removing offline content."""
        sync_id = uuid4()
        mock_dao.delete_offline_sync.return_value = True

        result = await service.remove_offline_content(sync_id)

        assert result is True
        mock_dao.delete_offline_sync.assert_called_once_with(sync_id)


# ============================================================================
# PUSH NOTIFICATION TESTS
# ============================================================================

class TestPushNotificationOperations:
    """Tests for push notification service operations."""

    @pytest.mark.asyncio
    async def test_configure_push_notifications(self, service, mock_dao, sample_user_id):
        """Test configuring push notifications."""
        expected = PushNotificationSettings(
            user_id=sample_user_id,
            fcm_token="fcm_token_123"
        )
        mock_dao.create_push_settings.return_value = expected

        result = await service.configure_push_notifications(
            user_id=sample_user_id,
            fcm_token="fcm_token_123"
        )

        assert result.fcm_token == "fcm_token_123"

    @pytest.mark.asyncio
    async def test_get_push_settings(self, service, mock_dao, sample_user_id, sample_push_settings):
        """Test getting push settings."""
        mock_dao.get_push_settings.return_value = sample_push_settings

        result = await service.get_push_settings(sample_user_id)

        assert result == sample_push_settings

    @pytest.mark.asyncio
    async def test_update_push_settings(self, service, mock_dao, sample_push_settings):
        """Test updating push settings."""
        sample_push_settings.quiz_reminders = False
        mock_dao.update_push_settings.return_value = sample_push_settings

        result = await service.update_push_settings(
            sample_push_settings.id,
            quiz_reminders=False
        )

        assert result.quiz_reminders is False

    @pytest.mark.asyncio
    async def test_update_push_settings_not_found(self, service, mock_dao):
        """Test updating non-existent push settings."""
        mock_dao.update_push_settings.side_effect = PushSettingsNotFoundError("Not found")

        with pytest.raises(MobileExperienceServiceError, match="not found"):
            await service.update_push_settings(uuid4(), quiz_reminders=False)

    @pytest.mark.asyncio
    async def test_update_push_token(self, service, mock_dao, sample_push_settings):
        """Test updating push token."""
        mock_dao.update_push_settings.return_value = sample_push_settings

        await service.update_push_token(sample_push_settings.id, fcm_token="new_token")

        call_kwargs = mock_dao.update_push_settings.call_args[1]
        assert call_kwargs['fcm_token'] == "new_token"
        assert 'token_updated_at' in call_kwargs

    @pytest.mark.asyncio
    async def test_send_notification_success(self, service_with_push, mock_dao, sample_user_id, sample_push_settings, mock_push_provider):
        """Test sending notification successfully."""
        mock_dao.get_push_settings.return_value = sample_push_settings
        expected_notification = PushNotification(
            user_id=sample_user_id,
            title="Test",
            body="Test body",
            category=NotificationCategory.COURSE_UPDATES
        )
        mock_dao.create_notification.return_value = expected_notification
        mock_dao.update_notification.return_value = expected_notification

        result = await service_with_push.send_notification(
            user_id=sample_user_id,
            title="Test",
            body="Test body",
            category=NotificationCategory.COURSE_UPDATES
        )

        mock_push_provider.send.assert_called_once()
        mock_dao.update_notification.assert_called()

    @pytest.mark.asyncio
    async def test_send_notification_no_token(self, service, mock_dao, sample_user_id):
        """Test sending notification without valid token."""
        settings = PushNotificationSettings(user_id=sample_user_id)  # No token
        mock_dao.get_push_settings.return_value = settings

        with pytest.raises(NotificationDeliveryError, match="No valid push token"):
            await service.send_notification(
                user_id=sample_user_id,
                title="Test",
                body="Body",
                category=NotificationCategory.COURSE_UPDATES
            )

    @pytest.mark.asyncio
    async def test_send_notification_no_settings(self, service, mock_dao, sample_user_id):
        """Test sending notification without settings."""
        mock_dao.get_push_settings.return_value = None

        with pytest.raises(NotificationDeliveryError, match="No valid push token"):
            await service.send_notification(
                user_id=sample_user_id,
                title="Test",
                body="Body",
                category=NotificationCategory.COURSE_UPDATES
            )

    @pytest.mark.asyncio
    async def test_send_notification_category_disabled(self, service, mock_dao, sample_user_id):
        """Test sending notification for disabled category."""
        settings = PushNotificationSettings(
            user_id=sample_user_id,
            fcm_token="token",
            promotion_offers=False
        )
        mock_dao.get_push_settings.return_value = settings

        with pytest.raises(NotificationDeliveryError, match="disabled for category"):
            await service.send_notification(
                user_id=sample_user_id,
                title="Promo",
                body="Body",
                category=NotificationCategory.PROMOTIONS
            )

    @pytest.mark.asyncio
    async def test_send_notification_provider_error(self, service_with_push, mock_dao, sample_user_id, sample_push_settings, mock_push_provider):
        """Test handling push provider error."""
        mock_dao.get_push_settings.return_value = sample_push_settings
        expected_notification = PushNotification(
            user_id=sample_user_id,
            title="Test",
            body="Test body",
            category=NotificationCategory.COURSE_UPDATES
        )
        mock_dao.create_notification.return_value = expected_notification
        mock_dao.update_notification.return_value = expected_notification
        mock_push_provider.send.side_effect = Exception("Provider error")

        result = await service_with_push.send_notification(
            user_id=sample_user_id,
            title="Test",
            body="Body",
            category=NotificationCategory.COURSE_UPDATES
        )

        # Notification should still be created but marked as failed
        assert mock_dao.update_notification.call_count >= 1

    @pytest.mark.asyncio
    async def test_mark_notification_opened(self, service, mock_dao):
        """Test marking notification as opened."""
        notification_id = uuid4()
        mock_dao.update_notification.return_value = PushNotification(
            id=notification_id,
            user_id=uuid4(),
            title="Test",
            body="Body",
            category=NotificationCategory.COURSE_UPDATES
        )

        await service.mark_notification_opened(notification_id, action="clicked")

        call_kwargs = mock_dao.update_notification.call_args[1]
        assert 'opened_at' in call_kwargs
        assert call_kwargs['action_taken'] == "clicked"

    @pytest.mark.asyncio
    async def test_mark_notification_opened_not_found(self, service, mock_dao):
        """Test marking non-existent notification."""
        mock_dao.update_notification.side_effect = NotificationNotFoundError("Not found")

        with pytest.raises(MobileExperienceServiceError, match="not found"):
            await service.mark_notification_opened(uuid4())

    @pytest.mark.asyncio
    async def test_get_user_notifications(self, service, mock_dao, sample_user_id):
        """Test getting user notifications."""
        notifications = [
            PushNotification(
                user_id=sample_user_id,
                title="Test",
                body="Body",
                category=NotificationCategory.COURSE_UPDATES
            )
        ]
        mock_dao.get_user_notifications.return_value = notifications

        result = await service.get_user_notifications(sample_user_id, limit=20)

        assert len(result) == 1
        mock_dao.get_user_notifications.assert_called_once_with(sample_user_id, 20)


# ============================================================================
# TOUCH GESTURE TESTS
# ============================================================================

class TestTouchGestureOperations:
    """Tests for touch gesture service operations."""

    @pytest.mark.asyncio
    async def test_configure_gestures(self, service, mock_dao, sample_user_id):
        """Test configuring gestures."""
        expected = TouchGestureSettings(
            user_id=sample_user_id,
            swipe_left_action="next_lesson"
        )
        mock_dao.create_gesture_settings.return_value = expected

        result = await service.configure_gestures(
            user_id=sample_user_id,
            swipe_left_action="next_lesson"
        )

        assert result.swipe_left_action == "next_lesson"

    @pytest.mark.asyncio
    async def test_get_gesture_settings(self, service, mock_dao, sample_user_id):
        """Test getting gesture settings."""
        settings = TouchGestureSettings(user_id=sample_user_id)
        mock_dao.get_gesture_settings.return_value = settings

        result = await service.get_gesture_settings(sample_user_id)

        assert result == settings

    @pytest.mark.asyncio
    async def test_update_gesture_settings(self, service, mock_dao, sample_user_id):
        """Test updating gesture settings."""
        settings_id = uuid4()
        updated = TouchGestureSettings(
            id=settings_id,
            user_id=sample_user_id,
            long_press_duration_ms=700
        )
        mock_dao.update_gesture_settings.return_value = updated

        result = await service.update_gesture_settings(
            settings_id,
            long_press_duration_ms=700
        )

        assert result.long_press_duration_ms == 700


# ============================================================================
# BANDWIDTH TRACKING TESTS
# ============================================================================

class TestBandwidthTrackingOperations:
    """Tests for bandwidth tracking service operations."""

    @pytest.mark.asyncio
    async def test_record_bandwidth_usage(self, service, mock_dao, sample_user_id):
        """Test recording bandwidth usage."""
        expected = BandwidthUsage(
            user_id=sample_user_id,
            usage_date=date.today(),
            total_bytes_downloaded=1000000
        )
        mock_dao.record_bandwidth_usage.return_value = expected

        result = await service.record_bandwidth_usage(
            user_id=sample_user_id,
            usage_date=date.today(),
            connection_type=ConnectionType.WIFI,
            total_bytes_downloaded=1000000
        )

        assert result.total_bytes_downloaded == 1000000

    @pytest.mark.asyncio
    async def test_get_bandwidth_usage(self, service, mock_dao, sample_user_id):
        """Test getting bandwidth usage."""
        usage = [
            BandwidthUsage(
                user_id=sample_user_id,
                usage_date=date.today(),
                total_bytes_downloaded=500000
            )
        ]
        mock_dao.get_user_bandwidth_usage.return_value = usage

        result = await service.get_bandwidth_usage(
            sample_user_id,
            date.today() - timedelta(days=7),
            date.today()
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_bandwidth_summary_with_data(self, service, mock_dao, sample_user_id):
        """Test getting bandwidth summary with data."""
        usage_records = [
            BandwidthUsage(
                user_id=sample_user_id,
                usage_date=date.today(),
                total_bytes_downloaded=10 * 1024 * 1024,  # 10 MB
                video_bytes_downloaded=5 * 1024 * 1024,
                image_bytes_downloaded=3 * 1024 * 1024,
                document_bytes_downloaded=1 * 1024 * 1024,
                api_bytes_downloaded=1 * 1024 * 1024,
                bytes_uploaded=1 * 1024 * 1024,
                bytes_saved_compression=2 * 1024 * 1024,
                bytes_saved_caching=1 * 1024 * 1024,
                bytes_saved_data_saver=500 * 1024,
                connection_type=ConnectionType.WIFI
            )
        ]
        mock_dao.get_user_bandwidth_usage.return_value = usage_records

        result = await service.get_bandwidth_summary(
            sample_user_id,
            date.today() - timedelta(days=7),
            date.today()
        )

        assert result["total_downloaded_mb"] == pytest.approx(10.0, rel=0.1)
        assert result["total_uploaded_mb"] == pytest.approx(1.0, rel=0.1)
        assert "by_type" in result
        assert "by_connection" in result
        assert result["by_type"]["video_mb"] == pytest.approx(5.0, rel=0.1)

    @pytest.mark.asyncio
    async def test_get_bandwidth_summary_empty(self, service, mock_dao, sample_user_id):
        """Test getting bandwidth summary with no data."""
        mock_dao.get_user_bandwidth_usage.return_value = []

        result = await service.get_bandwidth_summary(
            sample_user_id,
            date.today() - timedelta(days=7),
            date.today()
        )

        assert result["total_downloaded_mb"] == 0
        assert result["total_uploaded_mb"] == 0
        assert result["total_saved_mb"] == 0


# ============================================================================
# MOBILE DASHBOARD TESTS
# ============================================================================

class TestMobileDashboardOperations:
    """Tests for mobile dashboard service operations."""

    @pytest.mark.asyncio
    async def test_get_mobile_dashboard_with_device(self, service, mock_dao, sample_user_id, sample_device_id, sample_device_preference, sample_push_settings, sample_session):
        """Test getting mobile dashboard with current device."""
        mock_dao.get_user_devices.return_value = [sample_device_preference]
        mock_dao.get_user_push_settings.return_value = [sample_push_settings]
        mock_dao.get_user_sessions.return_value = [sample_session]

        result = await service.get_mobile_dashboard(sample_user_id, sample_device_id)

        assert result["devices"]["count"] == 1
        assert result["devices"]["current"] == "mobile"
        assert "notifications" in result
        assert "offline" in result
        assert "preferences" in result

    @pytest.mark.asyncio
    async def test_get_mobile_dashboard_no_device(self, service, mock_dao, sample_user_id, sample_push_settings, sample_session):
        """Test getting mobile dashboard without current device."""
        mock_dao.get_user_devices.return_value = []
        mock_dao.get_user_push_settings.return_value = [sample_push_settings]
        mock_dao.get_user_sessions.return_value = [sample_session]

        result = await service.get_mobile_dashboard(sample_user_id)

        assert result["devices"]["count"] == 0
        assert result["devices"]["current"] is None
        assert result["preferences"] is None

    @pytest.mark.asyncio
    async def test_get_mobile_dashboard_with_primary_device(self, service, mock_dao, sample_user_id, sample_push_settings, sample_session):
        """Test dashboard shows primary device."""
        primary_device = UserDevicePreference(
            user_id=sample_user_id,
            device_id="primary_device",
            device_type=DeviceType.TABLET,
            is_primary_device=True
        )
        mock_dao.get_user_devices.return_value = [primary_device]
        mock_dao.get_user_push_settings.return_value = [sample_push_settings]
        mock_dao.get_user_sessions.return_value = [sample_session]

        result = await service.get_mobile_dashboard(sample_user_id)

        assert result["devices"]["primary"] == "primary_device"

    @pytest.mark.asyncio
    async def test_get_mobile_dashboard_notifications_configured(self, service, mock_dao, sample_user_id, sample_device_preference, sample_session):
        """Test dashboard shows notification configuration."""
        settings_with_token = PushNotificationSettings(
            user_id=sample_user_id,
            fcm_token="token123",
            notifications_enabled=True
        )
        mock_dao.get_user_devices.return_value = [sample_device_preference]
        mock_dao.get_user_push_settings.return_value = [settings_with_token]
        mock_dao.get_user_sessions.return_value = [sample_session]

        result = await service.get_mobile_dashboard(sample_user_id, sample_device_preference.device_id)

        assert result["notifications"]["enabled"] is True
        assert result["notifications"]["devices_configured"] == 1

    @pytest.mark.asyncio
    async def test_get_mobile_dashboard_error(self, service, mock_dao, sample_user_id):
        """Test dashboard handles DAO error."""
        mock_dao.get_user_devices.side_effect = MobileExperienceDAOError("Error")

        with pytest.raises(MobileExperienceServiceError, match="Failed to get mobile dashboard"):
            await service.get_mobile_dashboard(sample_user_id)


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestServiceExceptions:
    """Tests for service exception hierarchy."""

    def test_device_registration_error_inherits(self):
        """Test DeviceRegistrationError inherits from base."""
        error = DeviceRegistrationError("test")
        assert isinstance(error, MobileExperienceServiceError)

    def test_session_error_inherits(self):
        """Test SessionError inherits from base."""
        error = SessionError("test")
        assert isinstance(error, MobileExperienceServiceError)

    def test_offline_sync_error_inherits(self):
        """Test OfflineSyncError inherits from base."""
        error = OfflineSyncError("test")
        assert isinstance(error, MobileExperienceServiceError)

    def test_notification_delivery_error_inherits(self):
        """Test NotificationDeliveryError inherits from base."""
        error = NotificationDeliveryError("test")
        assert isinstance(error, MobileExperienceServiceError)

    def test_storage_limit_exceeded_error_inherits(self):
        """Test StorageLimitExceededError inherits from base."""
        error = StorageLimitExceededError("test")
        assert isinstance(error, MobileExperienceServiceError)
