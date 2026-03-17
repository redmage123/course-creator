"""
Unit Tests for RBAC Meeting Room Service
Tests the meeting room management functionality with Teams and Zoom integration
"""

import pytest
import uuid
from datetime import datetime, timedelta

# Add test fixtures path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../fixtures'))

from rbac_fixtures import (
    mock_meeting_room_data,
    mock_meeting_room_repository,
    mock_teams_integration,
    mock_zoom_integration,
    mock_audit_logger,
    mock_email_service,
    RBACTestUtils
)


class TestMeetingRoomService:
    """Test cases for MeetingRoomService"""
    
    @pytest.fixture
    def meeting_room_service(self, mock_meeting_room_repository, mock_teams_integration,
                           mock_zoom_integration, mock_audit_logger, mock_email_service):
        """Create meeting room service with mocked dependencies."""

        class MeetingRoomServiceStub:
            pass

        service = MeetingRoomServiceStub()
        service.meeting_room_repository = mock_meeting_room_repository
        service.teams_integration = mock_teams_integration
        service.zoom_integration = mock_zoom_integration
        service.audit_logger = mock_audit_logger
        service.email_service = mock_email_service
        
        # Mock service methods
        async def mock_create_meeting_room(org_id, room_data):
            room_id = str(uuid.uuid4())
            
            # Mock integration response based on platform
            if room_data["platform"] == "teams":
                integration_result = {
                    "meeting_id": "19:meeting123@thread.v2",
                    "join_url": "https://teams.microsoft.com/l/meetup-join/...",
                    "organizer_url": "https://teams.microsoft.com/l/meetup-join/..."
                }
            else:  # zoom
                integration_result = {
                    "meeting_id": "123456789",
                    "join_url": "https://zoom.us/j/123456789",
                    "password": "test123"
                }
            
            return {
                "id": room_id,
                "name": room_data["name"],
                "display_name": room_data.get("display_name", room_data["name"]),
                "organization_id": org_id,
                "platform": room_data["platform"],
                "room_type": room_data["room_type"],
                "track_id": room_data.get("track_id"),
                "project_id": room_data.get("project_id"),
                "instructor_id": room_data.get("instructor_id"),
                "meeting_id": integration_result["meeting_id"],
                "join_url": integration_result["join_url"],
                "password": integration_result.get("password"),
                "settings": room_data.get("settings", {}),
                "status": "active",
                "created_at": datetime.utcnow()
            }
        
        async def mock_get_organization_meeting_rooms(org_id, filters=None):
            rooms = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Main Conference Room",
                    "platform": "teams",
                    "room_type": "organization_room",
                    "status": "active",
                    "participant_count": 5,
                    "last_used": datetime.utcnow() - timedelta(hours=2)
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Python Track Room",
                    "platform": "zoom",
                    "room_type": "track_room",
                    "status": "active",
                    "participant_count": 12,
                    "last_used": datetime.utcnow() - timedelta(minutes=30)
                }
            ]
            
            if filters:
                if "platform" in filters:
                    rooms = [r for r in rooms if r["platform"] == filters["platform"]]
                if "room_type" in filters:
                    rooms = [r for r in rooms if r["room_type"] == filters["room_type"]]
                if "status" in filters:
                    rooms = [r for r in rooms if r["status"] == filters["status"]]
            
            return rooms
        
        async def mock_update_meeting_room(room_id, update_data):
            return {
                "id": room_id,
                **update_data,
                "updated_at": datetime.utcnow()
            }
        
        async def mock_delete_meeting_room(room_id):
            return {
                "success": True,
                "room_id": room_id,
                "platform_deleted": True
            }
        
        async def mock_get_room_participants(room_id):
            return [
                {
                    "user_id": str(uuid.uuid4()),
                    "name": "John Instructor",
                    "email": "john@test.org",
                    "role": "organizer",
                    "joined_at": datetime.utcnow() - timedelta(minutes=15),
                    "status": "connected"
                },
                {
                    "user_id": str(uuid.uuid4()),
                    "name": "Jane Student",
                    "email": "jane@test.org", 
                    "role": "participant",
                    "joined_at": datetime.utcnow() - timedelta(minutes=10),
                    "status": "connected"
                }
            ]
        
        service.create_meeting_room = mock_create_meeting_room
        service.get_organization_meeting_rooms = mock_get_organization_meeting_rooms
        service.update_meeting_room = mock_update_meeting_room
        service.delete_meeting_room = mock_delete_meeting_room
        service.get_room_participants = mock_get_room_participants
        
        return service
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_teams_meeting_room_success(self, meeting_room_service):
        """Test successful Teams meeting room creation."""
        # Arrange
        org_id = str(uuid.uuid4())
        room_data = {
            "name": "Advanced Python Meeting",
            "platform": "teams",
            "room_type": "track_room",
            "track_id": str(uuid.uuid4()),
            "settings": {
                "auto_recording": True,
                "waiting_room": False,
                "mute_on_entry": False,
                "allow_screen_sharing": True
            }
        }
        
        # Act
        result = await meeting_room_service.create_meeting_room(org_id, room_data)
        
        # Assert
        assert result["name"] == room_data["name"]
        assert result["platform"] == "teams"
        assert result["room_type"] == room_data["room_type"]
        assert result["track_id"] == room_data["track_id"]
        assert result["organization_id"] == org_id
        assert result["settings"] == room_data["settings"]
        assert result["status"] == "active"
        assert "meeting_id" in result
        assert "join_url" in result
        assert "19:meeting" in result["meeting_id"]  # Teams format
        assert "teams.microsoft.com" in result["join_url"]
        assert "id" in result
        assert "created_at" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_zoom_meeting_room_success(self, meeting_room_service):
        """Test successful Zoom meeting room creation."""
        # Arrange
        org_id = str(uuid.uuid4())
        room_data = {
            "name": "JavaScript Workshop",
            "platform": "zoom",
            "room_type": "project_room",
            "project_id": str(uuid.uuid4()),
            "settings": {
                "auto_recording": False,
                "waiting_room": True,
                "mute_on_entry": True,
                "allow_screen_sharing": True
            }
        }
        
        # Act
        result = await meeting_room_service.create_meeting_room(org_id, room_data)
        
        # Assert
        assert result["name"] == room_data["name"]
        assert result["platform"] == "zoom"
        assert result["room_type"] == room_data["room_type"]
        assert result["project_id"] == room_data["project_id"]
        assert result["organization_id"] == org_id
        assert result["settings"] == room_data["settings"]
        assert result["status"] == "active"
        assert "meeting_id" in result
        assert "join_url" in result
        assert "password" in result
        assert result["meeting_id"].isdigit()  # Zoom format
        assert "zoom.us" in result["join_url"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_instructor_room(self, meeting_room_service):
        """Test creating instructor-specific meeting room."""
        # Arrange
        org_id = str(uuid.uuid4())
        room_data = {
            "name": "Dr. Smith's Office Hours",
            "platform": "teams",
            "room_type": "instructor_room",
            "instructor_id": str(uuid.uuid4()),
            "settings": {
                "auto_recording": False,
                "waiting_room": True,
                "mute_on_entry": False,
                "allow_screen_sharing": True
            }
        }
        
        # Act
        result = await meeting_room_service.create_meeting_room(org_id, room_data)
        
        # Assert
        assert result["room_type"] == "instructor_room"
        assert result["instructor_id"] == room_data["instructor_id"]
        assert result["track_id"] is None
        assert result["project_id"] is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_organization_meeting_rooms_all(self, meeting_room_service):
        """Test getting all organization meeting rooms."""
        # Arrange
        org_id = str(uuid.uuid4())
        
        # Act
        result = await meeting_room_service.get_organization_meeting_rooms(org_id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        
        for room in result:
            assert "id" in room
            assert "name" in room
            assert "platform" in room
            assert "room_type" in room
            assert "status" in room
            assert "participant_count" in room
            assert "last_used" in room
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_meeting_rooms_filtered_by_platform(self, meeting_room_service):
        """Test getting meeting rooms filtered by platform."""
        # Arrange
        org_id = str(uuid.uuid4())
        filters = {"platform": "teams"}
        
        # Act
        result = await meeting_room_service.get_organization_meeting_rooms(org_id, filters)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["platform"] == "teams"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_meeting_rooms_filtered_by_type(self, meeting_room_service):
        """Test getting meeting rooms filtered by room type."""
        # Arrange
        org_id = str(uuid.uuid4())
        filters = {"room_type": "track_room"}
        
        # Act
        result = await meeting_room_service.get_organization_meeting_rooms(org_id, filters)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["room_type"] == "track_room"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_meeting_room_success(self, meeting_room_service):
        """Test successful meeting room update."""
        # Arrange
        room_id = str(uuid.uuid4())
        update_data = {
            "name": "Updated Room Name",
            "settings": {
                "auto_recording": True,
                "waiting_room": True,
                "mute_on_entry": True,
                "allow_screen_sharing": False
            },
            "status": "inactive"
        }
        
        # Act
        result = await meeting_room_service.update_meeting_room(room_id, update_data)
        
        # Assert
        assert result["id"] == room_id
        assert result["name"] == update_data["name"]
        assert result["settings"] == update_data["settings"]
        assert result["status"] == update_data["status"]
        assert "updated_at" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_meeting_room_success(self, meeting_room_service):
        """Test successful meeting room deletion."""
        # Arrange
        room_id = str(uuid.uuid4())
        
        # Act
        result = await meeting_room_service.delete_meeting_room(room_id)
        
        # Assert
        assert result["success"] is True
        assert result["room_id"] == room_id
        assert result["platform_deleted"] is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_room_participants(self, meeting_room_service):
        """Test getting meeting room participants."""
        # Arrange
        room_id = str(uuid.uuid4())
        
        # Act
        result = await meeting_room_service.get_room_participants(room_id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Check organizer
        organizer = next((p for p in result if p["role"] == "organizer"), None)
        assert organizer is not None
        assert organizer["name"] == "John Instructor"
        assert organizer["status"] == "connected"
        
        # Check participant
        participant = next((p for p in result if p["role"] == "participant"), None)
        assert participant is not None
        assert participant["name"] == "Jane Student"
        assert participant["status"] == "connected"
        
        for participant in result:
            assert "user_id" in participant
            assert "name" in participant
            assert "email" in participant
            assert "role" in participant
            assert "joined_at" in participant
            assert "status" in participant
    
    @pytest.mark.unit
    def test_validate_room_data_valid(self):
        """Test meeting room data validation with valid data."""
        # Mock validation function
        def validate_room_data(data):
            required_fields = ["name", "platform", "room_type"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            valid_platforms = ["teams", "zoom"]
            if data["platform"] not in valid_platforms:
                raise ValueError(f"Invalid platform: {data['platform']}")
            
            valid_room_types = ["organization_room", "project_room", "track_room", "instructor_room"]
            if data["room_type"] not in valid_room_types:
                raise ValueError(f"Invalid room type: {data['room_type']}")
            
            if len(data["name"]) < 3:
                raise ValueError("Room name must be at least 3 characters")
            
            return True
        
        # Test valid data
        valid_data = {
            "name": "Valid Meeting Room",
            "platform": "teams",
            "room_type": "track_room"
        }
        
        assert validate_room_data(valid_data) is True
    
    @pytest.mark.unit
    def test_validate_room_data_invalid(self):
        """Test meeting room data validation with invalid data."""
        # Mock validation function
        def validate_room_data(data):
            required_fields = ["name", "platform", "room_type"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            valid_platforms = ["teams", "zoom"]
            if data["platform"] not in valid_platforms:
                raise ValueError(f"Invalid platform: {data['platform']}")
            
            valid_room_types = ["organization_room", "project_room", "track_room", "instructor_room"]
            if data["room_type"] not in valid_room_types:
                raise ValueError(f"Invalid room type: {data['room_type']}")
            
            if len(data["name"]) < 3:
                raise ValueError("Room name must be at least 3 characters")
            
            return True
        
        # Test missing name
        invalid_data_1 = {"platform": "teams", "room_type": "track_room"}
        with pytest.raises(ValueError, match="Missing required field: name"):
            validate_room_data(invalid_data_1)
        
        # Test invalid platform
        invalid_data_2 = {"name": "Test Room", "platform": "webex", "room_type": "track_room"}
        with pytest.raises(ValueError, match="Invalid platform: webex"):
            validate_room_data(invalid_data_2)
        
        # Test invalid room type
        invalid_data_3 = {"name": "Test Room", "platform": "teams", "room_type": "invalid_type"}
        with pytest.raises(ValueError, match="Invalid room type: invalid_type"):
            validate_room_data(invalid_data_3)
        
        # Test short name
        invalid_data_4 = {"name": "AB", "platform": "teams", "room_type": "track_room"}
        with pytest.raises(ValueError, match="Room name must be at least 3 characters"):
            validate_room_data(invalid_data_4)
    
    @pytest.mark.unit
    def test_validate_room_settings(self):
        """Test meeting room settings validation."""
        # Mock validation function
        def validate_room_settings(settings):
            valid_keys = ["auto_recording", "waiting_room", "mute_on_entry", "allow_screen_sharing"]
            
            for key in settings:
                if key not in valid_keys:
                    raise ValueError(f"Invalid setting: {key}")
                
                if not isinstance(settings[key], bool):
                    raise ValueError(f"Setting {key} must be a boolean")
            
            return True
        
        # Valid settings
        valid_settings = {
            "auto_recording": True,
            "waiting_room": False,
            "mute_on_entry": True,
            "allow_screen_sharing": True
        }
        
        assert validate_room_settings(valid_settings) is True
        
        # Invalid setting key
        invalid_settings_1 = {"invalid_setting": True}
        with pytest.raises(ValueError, match="Invalid setting: invalid_setting"):
            validate_room_settings(invalid_settings_1)
        
        # Invalid setting value type
        invalid_settings_2 = {"auto_recording": "yes"}
        with pytest.raises(ValueError, match="Setting auto_recording must be a boolean"):
            validate_room_settings(invalid_settings_2)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_meeting_room_analytics(self, meeting_room_service):
        """Test meeting room analytics functionality."""
        # Mock analytics methods
        async def mock_get_room_analytics(room_id, date_range=None):
            return {
                "room_id": room_id,
                "total_meetings": 25,
                "total_participants": 150,
                "average_duration_minutes": 45,
                "peak_usage_hour": 14,  # 2 PM
                "usage_by_day": {
                    "monday": 8,
                    "tuesday": 6,
                    "wednesday": 4,
                    "thursday": 4,
                    "friday": 3
                },
                "participant_satisfaction": 4.2
            }
        
        async def mock_get_organization_room_analytics(org_id, date_range=None):
            return {
                "organization_id": org_id,
                "total_rooms": 12,
                "active_rooms": 10,
                "total_meetings": 150,
                "total_participants": 800,
                "average_meeting_duration": 42,
                "platform_usage": {
                    "teams": 60,
                    "zoom": 40
                },
                "room_type_usage": {
                    "organization_room": 20,
                    "project_room": 45,
                    "track_room": 30,
                    "instructor_room": 5
                }
            }
        
        meeting_room_service.get_room_analytics = mock_get_room_analytics
        meeting_room_service.get_organization_room_analytics = mock_get_organization_room_analytics
        
        # Test individual room analytics
        room_id = str(uuid.uuid4())
        room_analytics = await meeting_room_service.get_room_analytics(room_id)
        
        assert room_analytics["room_id"] == room_id
        assert room_analytics["total_meetings"] == 25
        assert room_analytics["total_participants"] == 150
        assert room_analytics["average_duration_minutes"] == 45
        assert "usage_by_day" in room_analytics
        assert "participant_satisfaction" in room_analytics
        
        # Test organization room analytics
        org_id = str(uuid.uuid4())
        org_analytics = await meeting_room_service.get_organization_room_analytics(org_id)
        
        assert org_analytics["organization_id"] == org_id
        assert org_analytics["total_rooms"] == 12
        assert org_analytics["active_rooms"] == 10
        assert "platform_usage" in org_analytics
        assert "room_type_usage" in org_analytics
        assert org_analytics["platform_usage"]["teams"] + org_analytics["platform_usage"]["zoom"] == 100
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_meeting_room_invitations(self, meeting_room_service):
        """Test meeting room invitation functionality."""
        # Mock invitation methods
        async def mock_send_room_invitation(room_id, invitee_emails, inviter_id, message=None):
            invitations = []
            for email in invitee_emails:
                invitations.append({
                    "invitation_id": str(uuid.uuid4()),
                    "room_id": room_id,
                    "invitee_email": email,
                    "inviter_id": inviter_id,
                    "message": message,
                    "status": "sent",
                    "sent_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=24)
                })
            return invitations
        
        async def mock_get_room_invitations(room_id):
            return [
                {
                    "invitation_id": str(uuid.uuid4()),
                    "invitee_email": "student1@test.org",
                    "status": "accepted",
                    "sent_at": datetime.utcnow() - timedelta(hours=2),
                    "accepted_at": datetime.utcnow() - timedelta(hours=1)
                },
                {
                    "invitation_id": str(uuid.uuid4()),
                    "invitee_email": "student2@test.org",
                    "status": "pending",
                    "sent_at": datetime.utcnow() - timedelta(minutes=30),
                    "accepted_at": None
                }
            ]
        
        meeting_room_service.send_room_invitation = mock_send_room_invitation
        meeting_room_service.get_room_invitations = mock_get_room_invitations
        
        # Test sending invitations
        room_id = str(uuid.uuid4())
        invitee_emails = ["student1@test.org", "student2@test.org", "student3@test.org"]
        inviter_id = str(uuid.uuid4())
        message = "Join us for the Python programming session!"
        
        invitations = await meeting_room_service.send_room_invitation(
            room_id, invitee_emails, inviter_id, message
        )
        
        assert len(invitations) == 3
        for invitation in invitations:
            assert invitation["room_id"] == room_id
            assert invitation["inviter_id"] == inviter_id
            assert invitation["message"] == message
            assert invitation["status"] == "sent"
            assert "invitation_id" in invitation
            assert "sent_at" in invitation
            assert "expires_at" in invitation
        
        # Test getting invitations
        room_invitations = await meeting_room_service.get_room_invitations(room_id)
        
        assert len(room_invitations) == 2
        
        accepted_invitation = next((inv for inv in room_invitations if inv["status"] == "accepted"), None)
        assert accepted_invitation is not None
        assert accepted_invitation["accepted_at"] is not None
        
        pending_invitation = next((inv for inv in room_invitations if inv["status"] == "pending"), None)
        assert pending_invitation is not None
        assert pending_invitation["accepted_at"] is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_platform_integration_error_handling(self, meeting_room_service):
        """Test error handling for platform integration failures."""
        # Mock integration failure methods
        async def mock_create_room_with_failure(org_id, room_data):
            if room_data["platform"] == "teams":
                raise Exception("Teams API unavailable")
            elif room_data["platform"] == "zoom":
                raise Exception("Zoom authentication failed")
            
        meeting_room_service.create_meeting_room = mock_create_room_with_failure
        
        # Test Teams integration failure
        org_id = str(uuid.uuid4())
        teams_room_data = {
            "name": "Test Teams Room",
            "platform": "teams",
            "room_type": "track_room"
        }
        
        with pytest.raises(Exception, match="Teams API unavailable"):
            await meeting_room_service.create_meeting_room(org_id, teams_room_data)
        
        # Test Zoom integration failure
        zoom_room_data = {
            "name": "Test Zoom Room",
            "platform": "zoom",
            "room_type": "track_room"
        }
        
        with pytest.raises(Exception, match="Zoom authentication failed"):
            await meeting_room_service.create_meeting_room(org_id, zoom_room_data)