"""
Integration Tests for Third-Party Meeting Room Platforms
Tests Zoom, Microsoft Teams, and Slack integrations
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from organization_management.domain.entities.meeting_room import MeetingRoom, MeetingPlatform, RoomType
from organization_management.application.services.meeting_room_service import MeetingRoomService
from organization_management.infrastructure.integrations.zoom_integration import ZoomIntegrationService, ZoomCredentials
from organization_management.infrastructure.integrations.teams_integration import TeamsIntegrationService, TeamsCredentials
from organization_management.infrastructure.integrations.slack_integration import SlackIntegrationService, SlackCredentials


class TestZoomIntegration:
    """Test Zoom meeting room integration"""

    @pytest.fixture
    def zoom_credentials(self):
        """Mock Zoom credentials"""
        return ZoomCredentials(
            api_key="test_api_key",
            api_secret="test_api_secret",
            account_id="test_account"
        )

    @pytest.fixture
    def sample_room(self):
        """Sample meeting room"""
        return MeetingRoom(
            name="Test Track Room",
            platform=MeetingPlatform.ZOOM,
            room_type=RoomType.TRACK_ROOM,
            organization_id=uuid4(),
            track_id=uuid4(),
            created_by=uuid4(),
            settings={
                "auto_recording": True,
                "waiting_room": True,
                "mute_on_entry": True
            }
        )

    @pytest.mark.asyncio
    async def test_zoom_create_meeting_room(self, zoom_credentials, sample_room):
        """Test creating a Zoom meeting room"""
        async with ZoomIntegrationService(zoom_credentials) as zoom:
            with patch.object(zoom, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {
                    'id': '12345678',
                    'join_url': 'https://zoom.us/j/12345678',
                    'start_url': 'https://zoom.us/s/12345678',
                    'password': 'abc123'
                }

                result = await zoom.create_meeting_room(sample_room)

                assert result['external_room_id'] == '12345678'
                assert result['join_url'] == 'https://zoom.us/j/12345678'
                assert result['passcode'] == 'abc123'
                mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_zoom_update_meeting_room(self, zoom_credentials, sample_room):
        """Test updating a Zoom meeting room"""
        sample_room.external_room_id = "12345678"
        sample_room.name = "Updated Room Name"

        async with ZoomIntegrationService(zoom_credentials) as zoom:
            with patch.object(zoom, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {'success': True}

                result = await zoom.update_meeting_room(sample_room, {})

                assert result == {'success': True}
                mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_zoom_delete_meeting_room(self, zoom_credentials):
        """Test deleting a Zoom meeting room"""
        external_room_id = "12345678"

        async with ZoomIntegrationService(zoom_credentials) as zoom:
            with patch.object(zoom, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {}

                result = await zoom.delete_meeting_room(external_room_id)

                assert result is True
                mock_request.assert_called_once_with('DELETE', f'/meetings/{external_room_id}')

    @pytest.mark.asyncio
    async def test_zoom_send_invitation(self, zoom_credentials):
        """Test sending Zoom meeting invitations"""
        external_room_id = "12345678"
        emails = ["user1@example.com", "user2@example.com"]

        async with ZoomIntegrationService(zoom_credentials) as zoom:
            with patch.object(zoom, 'get_meeting_room_info', new_callable=AsyncMock) as mock_info:
                with patch.object(zoom, 'create_meeting_registration', new_callable=AsyncMock) as mock_register:
                    mock_info.return_value = {'id': external_room_id}
                    mock_register.return_value = {'success': True}

                    result = await zoom.send_meeting_invitation(external_room_id, emails)

                    assert result is True
                    assert mock_register.call_count == len(emails)

    def test_zoom_validate_configuration(self, zoom_credentials):
        """Test Zoom configuration validation"""
        zoom = ZoomIntegrationService(zoom_credentials)
        assert zoom.validate_configuration() is True

        invalid_creds = ZoomCredentials(api_key="", api_secret="")
        zoom_invalid = ZoomIntegrationService(invalid_creds)
        assert zoom_invalid.validate_configuration() is False


class TestTeamsIntegration:
    """Test Microsoft Teams meeting room integration"""

    @pytest.fixture
    def teams_credentials(self):
        """Mock Teams credentials"""
        return TeamsCredentials(
            tenant_id="test_tenant",
            client_id="test_client",
            client_secret="test_secret"
        )

    @pytest.fixture
    def sample_room(self):
        """Sample meeting room"""
        return MeetingRoom(
            name="Test Project Room",
            platform=MeetingPlatform.TEAMS,
            room_type=RoomType.PROJECT_ROOM,
            organization_id=uuid4(),
            project_id=uuid4(),
            created_by=uuid4(),
            settings={
                "auto_recording": False,
                "chat_enabled": True,
                "lobby_bypass": "organization"
            }
        )

    @pytest.mark.asyncio
    async def test_teams_create_meeting_room(self, teams_credentials, sample_room):
        """Test creating a Teams meeting room"""
        async with TeamsIntegrationService(teams_credentials) as teams:
            with patch.object(teams, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {
                    'id': 'teams-meeting-id',
                    'joinWebUrl': 'https://teams.microsoft.com/l/meetup-join/...',
                    'videoTeleconferenceId': '123456789'
                }

                result = await teams.create_meeting_room(sample_room)

                assert result['external_room_id'] == 'teams-meeting-id'
                assert 'teams.microsoft.com' in result['join_url']
                mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_teams_update_meeting_room(self, teams_credentials, sample_room):
        """Test updating a Teams meeting room"""
        sample_room.external_room_id = "teams-meeting-id"
        sample_room.name = "Updated Teams Room"

        async with TeamsIntegrationService(teams_credentials) as teams:
            with patch.object(teams, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {'success': True}

                result = await teams.update_meeting_room(sample_room, {})

                assert result == {'success': True}
                mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_teams_delete_meeting_room(self, teams_credentials):
        """Test deleting a Teams meeting room"""
        external_room_id = "teams-meeting-id"

        async with TeamsIntegrationService(teams_credentials) as teams:
            with patch.object(teams, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {}

                result = await teams.delete_meeting_room(external_room_id)

                assert result is True
                mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_teams_send_invitation(self, teams_credentials):
        """Test sending Teams meeting invitations"""
        external_room_id = "teams-meeting-id"
        emails = ["user1@example.com", "user2@example.com"]

        async with TeamsIntegrationService(teams_credentials) as teams:
            with patch.object(teams, 'get_meeting_room_info', new_callable=AsyncMock) as mock_info:
                with patch.object(teams, '_make_request', new_callable=AsyncMock) as mock_request:
                    mock_info.return_value = {
                        'id': external_room_id,
                        'subject': 'Test Meeting',
                        'joinWebUrl': 'https://teams.microsoft.com/...'
                    }
                    mock_request.return_value = {'success': True}

                    result = await teams.send_meeting_invitation(external_room_id, emails)

                    assert result is True
                    mock_request.assert_called_once()

    def test_teams_validate_configuration(self, teams_credentials):
        """Test Teams configuration validation"""
        teams = TeamsIntegrationService(teams_credentials)
        assert teams.validate_configuration() is True

        invalid_creds = TeamsCredentials(tenant_id="", client_id="", client_secret="")
        teams_invalid = TeamsIntegrationService(invalid_creds)
        assert teams_invalid.validate_configuration() is False


class TestSlackIntegration:
    """Test Slack channel integration"""

    @pytest.fixture
    def slack_credentials(self):
        """Mock Slack credentials"""
        return SlackCredentials(
            bot_token="xoxb-test-token",
            workspace_id="T12345678"
        )

    @pytest.fixture
    def sample_room(self):
        """Sample meeting room (Slack channel)"""
        return MeetingRoom(
            name="Test Instructor Room",
            platform=MeetingPlatform.SLACK,
            room_type=RoomType.INSTRUCTOR_ROOM,
            organization_id=uuid4(),
            instructor_id=uuid4(),
            created_by=uuid4(),
            settings={
                "private_channel": False,
                "enable_huddles": True
            }
        )

    @pytest.mark.asyncio
    async def test_slack_create_channel(self, slack_credentials, sample_room):
        """Test creating a Slack channel"""
        async with SlackIntegrationService(slack_credentials) as slack:
            with patch.object(slack, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {
                    'ok': True,
                    'channel': {
                        'id': 'C12345678',
                        'name': 'test-instructor-room',
                        'is_private': False
                    }
                }

                result = await slack.create_meeting_room(sample_room)

                assert result['external_room_id'] == 'C12345678'
                assert result['channel_name'] == 'test-instructor-room'
                assert 'slack://channel' in result['join_url']
                mock_request.assert_called()

    @pytest.mark.asyncio
    async def test_slack_update_channel(self, slack_credentials, sample_room):
        """Test updating a Slack channel"""
        sample_room.external_room_id = "C12345678"
        sample_room.name = "Updated Slack Channel"

        async with SlackIntegrationService(slack_credentials) as slack:
            with patch.object(slack, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {'ok': True}

                result = await slack.update_meeting_room(sample_room, {})

                assert result == {'success': True}
                assert mock_request.call_count >= 2  # rename + set topic/purpose

    @pytest.mark.asyncio
    async def test_slack_archive_channel(self, slack_credentials):
        """Test archiving a Slack channel"""
        external_room_id = "C12345678"

        async with SlackIntegrationService(slack_credentials) as slack:
            with patch.object(slack, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {'ok': True}

                result = await slack.delete_meeting_room(external_room_id)

                assert result is True
                mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_slack_invite_users(self, slack_credentials):
        """Test inviting users to Slack channel"""
        external_room_id = "C12345678"
        emails = ["user1@example.com", "user2@example.com"]

        async with SlackIntegrationService(slack_credentials) as slack:
            with patch.object(slack, 'get_user_by_email', new_callable=AsyncMock) as mock_lookup:
                with patch.object(slack, '_make_request', new_callable=AsyncMock) as mock_request:
                    mock_lookup.side_effect = [
                        {'id': 'U12345'},
                        {'id': 'U67890'}
                    ]
                    mock_request.return_value = {'ok': True}

                    result = await slack.send_meeting_invitation(external_room_id, emails)

                    assert result is True
                    assert mock_lookup.call_count == len(emails)

    @pytest.mark.asyncio
    async def test_slack_send_message(self, slack_credentials):
        """Test sending message to Slack channel"""
        channel_id = "C12345678"
        message = "Test notification message"

        async with SlackIntegrationService(slack_credentials) as slack:
            with patch.object(slack, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {
                    'ok': True,
                    'ts': '1234567890.123456'
                }

                result = await slack.send_message(channel_id, message)

                assert result['ok'] is True
                mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_slack_send_notification(self, slack_credentials):
        """Test sending formatted notification to Slack"""
        channel_id = "C12345678"
        title = "Course Update"
        message = "New assignment posted"

        async with SlackIntegrationService(slack_credentials) as slack:
            with patch.object(slack, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {'ok': True}

                result = await slack.send_notification(channel_id, title, message, color="good")

                assert result is True
                mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_slack_connection_test(self, slack_credentials):
        """Test Slack API connection"""
        async with SlackIntegrationService(slack_credentials) as slack:
            with patch.object(slack, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {
                    'ok': True,
                    'team': 'Test Workspace',
                    'team_id': 'T12345678',
                    'user': 'bot_user',
                    'bot_id': 'B12345678'
                }

                result = await slack.test_connection()

                assert result['connected'] is True
                assert result['team'] == 'Test Workspace'

    def test_slack_validate_configuration(self, slack_credentials):
        """Test Slack configuration validation"""
        slack = SlackIntegrationService(slack_credentials)
        assert slack.validate_configuration() is True

        invalid_creds = SlackCredentials(bot_token="invalid-token")
        slack_invalid = SlackIntegrationService(invalid_creds)
        assert slack_invalid.validate_configuration() is False


class TestMeetingRoomService:
    """Test MeetingRoomService with all three platforms"""

    @pytest.fixture
    def mock_dao(self):
        """Mock organization DAO"""
        dao = Mock()
        dao.create_room = AsyncMock()
        dao.get_room_by_id = AsyncMock()
        dao.update_room = AsyncMock()
        dao.delete_room = AsyncMock()
        dao.get_organization_rooms = AsyncMock(return_value=[])
        return dao

    @pytest.fixture
    def meeting_room_service(self, mock_dao):
        """Meeting room service with mock credentials"""
        zoom_creds = ZoomCredentials(api_key="test", api_secret="test")
        teams_creds = TeamsCredentials(tenant_id="test", client_id="test", client_secret="test")
        slack_creds = SlackCredentials(bot_token="xoxb-test")

        return MeetingRoomService(
            organization_dao=mock_dao,
            teams_credentials=teams_creds,
            zoom_credentials=zoom_creds,
            slack_credentials=slack_creds
        )

    @pytest.mark.asyncio
    async def test_create_room_zoom(self, meeting_room_service, mock_dao):
        """Test creating Zoom room through service"""
        org_id = uuid4()
        track_id = uuid4()
        created_by = uuid4()

        with patch.object(meeting_room_service, '_create_zoom_room', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                'external_room_id': '12345',
                'join_url': 'https://zoom.us/j/12345'
            }
            mock_dao.create_room.return_value = MeetingRoom(
                id=uuid4(),
                name="Test Room",
                platform=MeetingPlatform.ZOOM,
                room_type=RoomType.TRACK_ROOM,
                organization_id=org_id,
                track_id=track_id,
                created_by=created_by,
                external_room_id='12345',
                join_url='https://zoom.us/j/12345'
            )

            room = await meeting_room_service.create_meeting_room(
                organization_id=org_id,
                name="Test Room",
                platform=MeetingPlatform.ZOOM,
                room_type=RoomType.TRACK_ROOM,
                created_by=created_by,
                track_id=track_id
            )

            assert room.platform == MeetingPlatform.ZOOM
            assert room.external_room_id == '12345'
            mock_create.assert_called_once()
            mock_dao.create_room.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_room_teams(self, meeting_room_service, mock_dao):
        """Test creating Teams room through service"""
        org_id = uuid4()
        instructor_id = uuid4()
        created_by = uuid4()

        with patch.object(meeting_room_service, '_create_teams_room', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                'external_room_id': 'teams-id',
                'join_url': 'https://teams.microsoft.com/...'
            }
            mock_dao.create_room.return_value = MeetingRoom(
                id=uuid4(),
                name="Instructor Room",
                platform=MeetingPlatform.TEAMS,
                room_type=RoomType.INSTRUCTOR_ROOM,
                organization_id=org_id,
                instructor_id=instructor_id,
                created_by=created_by,
                external_room_id='teams-id'
            )

            room = await meeting_room_service.create_meeting_room(
                organization_id=org_id,
                name="Instructor Room",
                platform=MeetingPlatform.TEAMS,
                room_type=RoomType.INSTRUCTOR_ROOM,
                created_by=created_by,
                instructor_id=instructor_id
            )

            assert room.platform == MeetingPlatform.TEAMS
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_room_slack(self, meeting_room_service, mock_dao):
        """Test creating Slack channel through service"""
        org_id = uuid4()
        project_id = uuid4()
        created_by = uuid4()

        with patch.object(meeting_room_service, '_create_slack_room', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                'external_room_id': 'C12345',
                'join_url': 'slack://channel?...',
                'channel_name': 'project-room'
            }
            mock_dao.create_room.return_value = MeetingRoom(
                id=uuid4(),
                name="Project Room",
                platform=MeetingPlatform.SLACK,
                room_type=RoomType.PROJECT_ROOM,
                organization_id=org_id,
                project_id=project_id,
                created_by=created_by,
                external_room_id='C12345'
            )

            room = await meeting_room_service.create_meeting_room(
                organization_id=org_id,
                name="Project Room",
                platform=MeetingPlatform.SLACK,
                room_type=RoomType.PROJECT_ROOM,
                created_by=created_by,
                project_id=project_id
            )

            assert room.platform == MeetingPlatform.SLACK
            mock_create.assert_called_once()

    def test_validate_all_platforms(self, meeting_room_service):
        """Test platform configuration validation for all platforms"""
        assert meeting_room_service.validate_platform_configuration(MeetingPlatform.ZOOM) is True
        assert meeting_room_service.validate_platform_configuration(MeetingPlatform.TEAMS) is True
        assert meeting_room_service.validate_platform_configuration(MeetingPlatform.SLACK) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
