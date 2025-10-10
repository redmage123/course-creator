"""
Unit tests for bulk meeting room creation functionality

BUSINESS CONTEXT:
Tests bulk room creation for instructors and tracks,
including notification sending and error handling.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from organization_management.application.services.meeting_room_service import MeetingRoomService
from organization_management.application.services.notification_service import NotificationService
from organization_management.domain.entities.meeting_room import MeetingPlatform, MeetingRoom, RoomType
from organization_management.domain.entities.enhanced_role import RoleType, EnhancedRole


@pytest.fixture
def mock_dao():
    """Mock OrganizationManagementDAO"""
    return AsyncMock()


@pytest.fixture
def mock_notification_service():
    """Mock NotificationService"""
    return AsyncMock(spec=NotificationService)


@pytest.fixture
def meeting_room_service(mock_dao, mock_notification_service):
    """Create MeetingRoomService instance"""
    return MeetingRoomService(
        organization_dao=mock_dao,
        teams_credentials=None,
        zoom_credentials=None,
        slack_credentials=None,
        notification_service=mock_notification_service
    )


class TestCreateInstructorRoomWithNotification:
    """Test create_instructor_room with notification support"""

    @pytest.mark.asyncio
    async def test_create_instructor_room_sends_notification(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test that creating instructor room sends notification"""
        instructor_id = uuid4()
        org_id = uuid4()
        created_by = uuid4()

        # Mock room creation
        mock_room = MagicMock(
            id=uuid4(),
            name="Instructor Room",
            join_url="https://zoom.us/j/123456",
            platform=MeetingPlatform.ZOOM
        )
        mock_dao.create_room.return_value = mock_room

        # Mock Zoom room creation
        with patch.object(meeting_room_service, '_create_zoom_room', new_callable=AsyncMock) as mock_zoom:
            mock_zoom.return_value = {
                "external_room_id": "zoom-123",
                "join_url": "https://zoom.us/j/123456"
            }

            await meeting_room_service.create_instructor_room(
                instructor_id=instructor_id,
                organization_id=org_id,
                platform=MeetingPlatform.ZOOM,
                created_by=created_by,
                send_notification=True
            )

            # Verify notification was sent
            mock_notification_service.send_instructor_room_notification.assert_called_once_with(
                instructor_id=instructor_id,
                room_id=mock_room.id,
                room_name=mock_room.name,
                join_url=mock_room.join_url,
                organization_id=org_id
            )

    @pytest.mark.asyncio
    async def test_create_instructor_room_without_notification(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test creating instructor room without sending notification"""
        instructor_id = uuid4()
        org_id = uuid4()
        created_by = uuid4()

        mock_room = MagicMock(id=uuid4(), join_url="https://zoom.us/j/123456")
        mock_dao.create_room.return_value = mock_room

        with patch.object(meeting_room_service, '_create_zoom_room', new_callable=AsyncMock) as mock_zoom:
            mock_zoom.return_value = {"external_room_id": "zoom-123", "join_url": "https://zoom.us/j/123456"}

            await meeting_room_service.create_instructor_room(
                instructor_id=instructor_id,
                organization_id=org_id,
                platform=MeetingPlatform.ZOOM,
                created_by=created_by,
                send_notification=False
            )

            # Verify notification was NOT sent
            mock_notification_service.send_instructor_room_notification.assert_not_called()


class TestCreateTrackRoomWithNotification:
    """Test create_track_room with notification support"""

    @pytest.mark.asyncio
    async def test_create_track_room_sends_notification(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test that creating track room sends notifications to all participants"""
        track_id = uuid4()
        org_id = uuid4()
        created_by = uuid4()

        mock_room = MagicMock(
            id=uuid4(),
            name="Python Track Room",
            join_url="https://teams.microsoft.com/l/meetup/123",
            platform=MeetingPlatform.TEAMS
        )
        mock_dao.create_room.return_value = mock_room

        with patch.object(meeting_room_service, '_create_teams_room', new_callable=AsyncMock) as mock_teams:
            mock_teams.return_value = {
                "external_room_id": "teams-123",
                "join_url": "https://teams.microsoft.com/l/meetup/123"
            }

            await meeting_room_service.create_track_room(
                track_id=track_id,
                organization_id=org_id,
                platform=MeetingPlatform.TEAMS,
                created_by=created_by,
                send_notification=True
            )

            # Verify notification was sent
            mock_notification_service.send_track_room_notification.assert_called_once_with(
                track_id=track_id,
                room_name=mock_room.name,
                join_url=mock_room.join_url,
                organization_id=org_id
            )


class TestBulkCreateInstructorRooms:
    """Test create_rooms_for_all_instructors method"""

    @pytest.mark.asyncio
    async def test_bulk_create_instructor_rooms_success(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test successfully creating rooms for all instructors"""
        org_id = uuid4()
        created_by = uuid4()

        # Mock 3 instructors
        instructor1_id = uuid4()
        instructor2_id = uuid4()
        instructor3_id = uuid4()

        memberships = [
            MagicMock(
                user_id=instructor1_id,
                role=EnhancedRole(role_type=RoleType.INSTRUCTOR, organization_id=org_id)
            ),
            MagicMock(
                user_id=instructor2_id,
                role=EnhancedRole(role_type=RoleType.INSTRUCTOR, organization_id=org_id)
            ),
            MagicMock(
                user_id=instructor3_id,
                role=EnhancedRole(role_type=RoleType.INSTRUCTOR, organization_id=org_id)
            )
        ]
        mock_dao.get_organization_members.return_value = memberships

        # No existing rooms
        mock_dao.get_instructor_rooms.return_value = []

        # Mock room creation
        def create_room_side_effect(room):
            room.id = uuid4()
            room.join_url = "https://zoom.us/j/123456"
            return room

        mock_dao.create_room.side_effect = create_room_side_effect

        with patch.object(meeting_room_service, '_create_zoom_room', new_callable=AsyncMock) as mock_zoom:
            mock_zoom.return_value = {
                "external_room_id": "zoom-123",
                "join_url": "https://zoom.us/j/123456"
            }

            results = await meeting_room_service.create_rooms_for_all_instructors(
                organization_id=org_id,
                platform=MeetingPlatform.ZOOM,
                created_by=created_by,
                send_notifications=True
            )

            assert results["total"] == 3
            assert results["created"] == 3
            assert results["failed"] == 0
            assert len(results["errors"]) == 0

            # Verify notifications were sent for all instructors
            assert mock_notification_service.send_instructor_room_notification.call_count == 3

    @pytest.mark.asyncio
    async def test_bulk_create_skips_existing_rooms(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test that bulk creation skips instructors who already have rooms"""
        org_id = uuid4()
        created_by = uuid4()

        instructor1_id = uuid4()
        instructor2_id = uuid4()

        memberships = [
            MagicMock(
                user_id=instructor1_id,
                role=EnhancedRole(role_type=RoleType.INSTRUCTOR, organization_id=org_id)
            ),
            MagicMock(
                user_id=instructor2_id,
                role=EnhancedRole(role_type=RoleType.INSTRUCTOR, organization_id=org_id)
            )
        ]
        mock_dao.get_organization_members.return_value = memberships

        # Instructor 1 already has a Zoom room
        def get_instructor_rooms_side_effect(instructor_id):
            if instructor_id == instructor1_id:
                return [MagicMock(platform=MeetingPlatform.ZOOM)]
            return []

        mock_dao.get_instructor_rooms.side_effect = get_instructor_rooms_side_effect

        def create_room_side_effect(room):
            room.id = uuid4()
            room.join_url = "https://zoom.us/j/123456"
            return room

        mock_dao.create_room.side_effect = create_room_side_effect

        with patch.object(meeting_room_service, '_create_zoom_room', new_callable=AsyncMock) as mock_zoom:
            mock_zoom.return_value = {"external_room_id": "zoom-123", "join_url": "https://zoom.us/j/123456"}

            results = await meeting_room_service.create_rooms_for_all_instructors(
                organization_id=org_id,
                platform=MeetingPlatform.ZOOM,
                created_by=created_by
            )

            assert results["total"] == 2
            assert results["created"] == 1  # Only instructor 2
            assert results["failed"] == 0

    @pytest.mark.asyncio
    async def test_bulk_create_handles_failures(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test that bulk creation continues despite individual failures"""
        org_id = uuid4()
        created_by = uuid4()

        instructor1_id = uuid4()
        instructor2_id = uuid4()
        instructor3_id = uuid4()

        memberships = [
            MagicMock(
                user_id=instructor1_id,
                role=EnhancedRole(role_type=RoleType.INSTRUCTOR, organization_id=org_id)
            ),
            MagicMock(
                user_id=instructor2_id,
                role=EnhancedRole(role_type=RoleType.INSTRUCTOR, organization_id=org_id)
            ),
            MagicMock(
                user_id=instructor3_id,
                role=EnhancedRole(role_type=RoleType.INSTRUCTOR, organization_id=org_id)
            )
        ]
        mock_dao.get_organization_members.return_value = memberships
        mock_dao.get_instructor_rooms.return_value = []

        # Second instructor fails
        call_count = 0

        def create_room_side_effect(room):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Room creation failed")
            room.id = uuid4()
            room.join_url = "https://zoom.us/j/123456"
            return room

        mock_dao.create_room.side_effect = create_room_side_effect

        with patch.object(meeting_room_service, '_create_zoom_room', new_callable=AsyncMock) as mock_zoom:
            mock_zoom.return_value = {"external_room_id": "zoom-123", "join_url": "https://zoom.us/j/123456"}

            results = await meeting_room_service.create_rooms_for_all_instructors(
                organization_id=org_id,
                platform=MeetingPlatform.ZOOM,
                created_by=created_by
            )

            assert results["total"] == 3
            assert results["created"] == 2
            assert results["failed"] == 1
            assert len(results["errors"]) == 1
            assert str(instructor2_id) in results["errors"][0]["instructor_id"]

    @pytest.mark.asyncio
    async def test_bulk_create_with_no_instructors(
        self,
        meeting_room_service,
        mock_dao
    ):
        """Test bulk creation with organization that has no instructors"""
        org_id = uuid4()
        created_by = uuid4()

        # No instructors in organization
        mock_dao.get_organization_members.return_value = []

        results = await meeting_room_service.create_rooms_for_all_instructors(
            organization_id=org_id,
            platform=MeetingPlatform.TEAMS,
            created_by=created_by
        )

        assert results["total"] == 0
        assert results["created"] == 0
        assert results["failed"] == 0


class TestBulkCreateTrackRooms:
    """Test create_rooms_for_all_tracks method"""

    @pytest.mark.asyncio
    async def test_bulk_create_track_rooms_success(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test successfully creating rooms for all tracks"""
        org_id = uuid4()
        created_by = uuid4()

        # Mock 3 tracks
        track1 = MagicMock(id=uuid4(), name="Python Fundamentals")
        track2 = MagicMock(id=uuid4(), name="Advanced Python")
        track3 = MagicMock(id=uuid4(), name="Web Development")

        mock_dao.get_organization_tracks.return_value = [track1, track2, track3]
        mock_dao.get_track_rooms.return_value = []  # No existing rooms

        def create_room_side_effect(room):
            room.id = uuid4()
            room.join_url = "https://slack.com/channels/C123"
            return room

        mock_dao.create_room.side_effect = create_room_side_effect

        with patch.object(meeting_room_service, '_create_slack_room', new_callable=AsyncMock) as mock_slack:
            mock_slack.return_value = {
                "external_room_id": "C123",
                "join_url": "https://slack.com/channels/C123"
            }

            results = await meeting_room_service.create_rooms_for_all_tracks(
                organization_id=org_id,
                platform=MeetingPlatform.SLACK,
                created_by=created_by,
                send_notifications=True
            )

            assert results["total"] == 3
            assert results["created"] == 3
            assert results["failed"] == 0

            # Verify notifications were sent for all tracks
            assert mock_notification_service.send_track_room_notification.call_count == 3

    @pytest.mark.asyncio
    async def test_bulk_create_tracks_skips_existing(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test that bulk creation skips tracks with existing rooms"""
        org_id = uuid4()
        created_by = uuid4()

        track1 = MagicMock(id=uuid4(), name="Track 1")
        track2 = MagicMock(id=uuid4(), name="Track 2")

        mock_dao.get_organization_tracks.return_value = [track1, track2]

        # Track 1 already has a Slack room
        def get_track_rooms_side_effect(track_id):
            if track_id == track1.id:
                return [MagicMock(platform=MeetingPlatform.SLACK)]
            return []

        mock_dao.get_track_rooms.side_effect = get_track_rooms_side_effect

        def create_room_side_effect(room):
            room.id = uuid4()
            room.join_url = "https://slack.com/channels/C123"
            return room

        mock_dao.create_room.side_effect = create_room_side_effect

        with patch.object(meeting_room_service, '_create_slack_room', new_callable=AsyncMock) as mock_slack:
            mock_slack.return_value = {"external_room_id": "C123", "join_url": "https://slack.com/channels/C123"}

            results = await meeting_room_service.create_rooms_for_all_tracks(
                organization_id=org_id,
                platform=MeetingPlatform.SLACK,
                created_by=created_by
            )

            assert results["total"] == 2
            assert results["created"] == 1  # Only track 2
            assert results["failed"] == 0

    @pytest.mark.asyncio
    async def test_bulk_create_tracks_handles_failures(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test that bulk track creation continues despite failures"""
        org_id = uuid4()
        created_by = uuid4()

        track1 = MagicMock(id=uuid4(), name="Track 1")
        track2 = MagicMock(id=uuid4(), name="Track 2")
        track3 = MagicMock(id=uuid4(), name="Track 3")

        mock_dao.get_organization_tracks.return_value = [track1, track2, track3]
        mock_dao.get_track_rooms.return_value = []

        # Second track fails
        call_count = 0

        def create_room_side_effect(room):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Failed to create room")
            room.id = uuid4()
            room.join_url = "https://teams.microsoft.com/l/meetup/123"
            return room

        mock_dao.create_room.side_effect = create_room_side_effect

        with patch.object(meeting_room_service, '_create_teams_room', new_callable=AsyncMock) as mock_teams:
            mock_teams.return_value = {"external_room_id": "teams-123", "join_url": "https://teams.microsoft.com/l/meetup/123"}

            results = await meeting_room_service.create_rooms_for_all_tracks(
                organization_id=org_id,
                platform=MeetingPlatform.TEAMS,
                created_by=created_by
            )

            assert results["total"] == 3
            assert results["created"] == 2
            assert results["failed"] == 1
            assert len(results["errors"]) == 1
            # Check track_name is present (may be MagicMock or string)
            assert "track_name" in results["errors"][0]
            assert results["errors"][0]["track_name"] == "Track 2" or str(track2.name) in str(results["errors"][0]["track_name"])


class TestBulkOperationsNotificationSettings:
    """Test notification settings in bulk operations"""

    @pytest.mark.asyncio
    async def test_bulk_create_instructors_with_notifications_disabled(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test bulk creation with notifications disabled"""
        org_id = uuid4()
        created_by = uuid4()

        memberships = [
            MagicMock(
                user_id=uuid4(),
                role=EnhancedRole(role_type=RoleType.INSTRUCTOR, organization_id=org_id)
            )
        ]
        mock_dao.get_organization_members.return_value = memberships
        mock_dao.get_instructor_rooms.return_value = []

        def create_room_side_effect(room):
            room.id = uuid4()
            room.join_url = "https://zoom.us/j/123456"
            return room

        mock_dao.create_room.side_effect = create_room_side_effect

        with patch.object(meeting_room_service, '_create_zoom_room', new_callable=AsyncMock) as mock_zoom:
            mock_zoom.return_value = {"external_room_id": "zoom-123", "join_url": "https://zoom.us/j/123456"}

            results = await meeting_room_service.create_rooms_for_all_instructors(
                organization_id=org_id,
                platform=MeetingPlatform.ZOOM,
                created_by=created_by,
                send_notifications=False  # Disabled
            )

            assert results["created"] == 1

            # Verify NO notifications were sent
            mock_notification_service.send_instructor_room_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_bulk_create_tracks_with_notifications_disabled(
        self,
        meeting_room_service,
        mock_dao,
        mock_notification_service
    ):
        """Test bulk track creation with notifications disabled"""
        org_id = uuid4()
        created_by = uuid4()

        track = MagicMock(id=uuid4(), name="Test Track")
        mock_dao.get_organization_tracks.return_value = [track]
        mock_dao.get_track_rooms.return_value = []

        def create_room_side_effect(room):
            room.id = uuid4()
            room.join_url = "https://zoom.us/j/123456"
            return room

        mock_dao.create_room.side_effect = create_room_side_effect

        with patch.object(meeting_room_service, '_create_zoom_room', new_callable=AsyncMock) as mock_zoom:
            mock_zoom.return_value = {"external_room_id": "zoom-123", "join_url": "https://zoom.us/j/123456"}

            results = await meeting_room_service.create_rooms_for_all_tracks(
                organization_id=org_id,
                platform=MeetingPlatform.ZOOM,
                created_by=created_by,
                send_notifications=False  # Disabled
            )

            assert results["created"] == 1

            # Verify NO notifications were sent
            mock_notification_service.send_track_room_notification.assert_not_called()
