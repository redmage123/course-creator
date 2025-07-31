"""
RBAC Test Fixtures
Enhanced RBAC system test fixtures for comprehensive testing
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, List, Any, Optional


@pytest.fixture
def mock_organization_data():
    """Create mock organization data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Organization",
        "slug": "test-org",
        "description": "A test organization for RBAC testing",
        "is_active": True,
        "settings": {
            "max_members": 100,
            "allow_self_registration": False,
            "require_email_verification": True
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_rbac_role_data():
    """Create mock RBAC role data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Role",
        "description": "A test role for RBAC testing",
        "role_type": "instructor",
        "permissions": [
            "read_courses",
            "create_courses",
            "manage_students",
            "access_analytics"
        ],
        "is_system_role": False,
        "organization_id": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_membership_data():
    """Create mock organization membership data."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "organization_id": str(uuid.uuid4()),
        "role_type": "instructor",
        "status": "active",
        "permissions": [
            "read_courses",
            "create_courses",
            "manage_students"
        ],
        "project_access": [str(uuid.uuid4())],
        "invited_by": str(uuid.uuid4()),
        "joined_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_track_data():
    """Create mock learning track data."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Python Programming Track",
        "description": "Comprehensive Python programming learning path",
        "organization_id": str(uuid.uuid4()),
        "project_id": str(uuid.uuid4()),
        "difficulty_level": "intermediate",
        "duration_weeks": 12,
        "target_audience": ["developers", "students"],
        "prerequisites": ["basic_programming"],
        "learning_objectives": [
            "Master Python syntax",
            "Understand OOP concepts",
            "Build real-world applications"
        ],
        "status": "active",
        "auto_enrollment": True,
        "created_by": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_meeting_room_data():
    """Create mock meeting room data."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Python Track Room",
        "display_name": "Python Programming - Track Room",
        "organization_id": str(uuid.uuid4()),
        "platform": "teams",
        "room_type": "track_room",
        "track_id": str(uuid.uuid4()),
        "project_id": None,
        "instructor_id": None,
        "meeting_id": "19:meeting_id@thread.v2",
        "join_url": "https://teams.microsoft.com/l/meetup-join/...",
        "settings": {
            "auto_recording": True,
            "waiting_room": False,
            "mute_on_entry": False,
            "allow_screen_sharing": True
        },
        "status": "active",
        "created_by": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_project_data():
    """Create mock project data for RBAC testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Python Web Development",
        "description": "Learn to build web applications with Python",
        "organization_id": str(uuid.uuid4()),
        "instructor_ids": [str(uuid.uuid4())],
        "track_ids": [str(uuid.uuid4())],
        "status": "active",
        "settings": {
            "allow_student_collaboration": True,
            "require_instructor_approval": False,
            "enable_peer_review": True
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_permission_data():
    """Create mock permission data."""
    return {
        "id": str(uuid.uuid4()),
        "name": "manage_courses",
        "description": "Ability to create, edit, and delete courses",
        "resource": "courses",
        "action": "manage",
        "conditions": {
            "organization_scope": True,
            "project_scope": False
        },
        "is_system_permission": True,
        "created_at": datetime.utcnow()
    }


@pytest.fixture 
def mock_site_admin_user_data():
    """Create mock site admin user data."""
    return {
        "id": str(uuid.uuid4()),
        "username": "siteadmin",
        "email": "admin@courseplatform.com",
        "full_name": "Site Administrator",
        "is_site_admin": True,
        "is_active": True,
        "organization_id": None,
        "role": "site_admin",
        "permissions": [
            "manage_platform",
            "delete_organizations",
            "manage_site_settings",
            "view_audit_logs",
            "manage_integrations"
        ],
        "last_login": datetime.utcnow() - timedelta(hours=1),
        "created_at": datetime.utcnow() - timedelta(days=30),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_org_admin_user_data():
    """Create mock organization admin user data."""
    return {
        "id": str(uuid.uuid4()),
        "username": "orgadmin",
        "email": "admin@testorg.com",
        "full_name": "Organization Administrator", 
        "is_site_admin": False,
        "is_active": True,
        "organization_id": str(uuid.uuid4()),
        "organization_name": "Test Organization",
        "role": "organization_admin",
        "permissions": [
            "manage_organization",
            "manage_members",
            "create_tracks",
            "manage_meeting_rooms",
            "view_analytics",
            "assign_projects"
        ],
        "last_login": datetime.utcnow() - timedelta(minutes=30),
        "created_at": datetime.utcnow() - timedelta(days=7),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_instructor_user_data():
    """Create mock instructor user data."""
    return {
        "id": str(uuid.uuid4()),
        "username": "instructor",
        "email": "instructor@testorg.com",
        "full_name": "Test Instructor",
        "is_site_admin": False,
        "is_active": True,
        "organization_id": str(uuid.uuid4()),
        "organization_name": "Test Organization",
        "role": "instructor",
        "permissions": [
            "create_courses",
            "manage_students",
            "access_analytics",
            "create_meeting_rooms"
        ],
        "project_access": [str(uuid.uuid4()), str(uuid.uuid4())],
        "last_login": datetime.utcnow() - timedelta(minutes=15),
        "created_at": datetime.utcnow() - timedelta(days=3),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_student_user_data():
    """Create mock student user data."""
    return {
        "id": str(uuid.uuid4()),
        "username": "student",
        "email": "student@testorg.com",
        "full_name": "Test Student",
        "is_site_admin": False,
        "is_active": True,
        "organization_id": str(uuid.uuid4()),
        "organization_name": "Test Organization",
        "role": "student",
        "permissions": [
            "view_courses",
            "submit_assignments",
            "access_labs",
            "take_quizzes"
        ],
        "track_enrollments": [str(uuid.uuid4())],
        "last_login": datetime.utcnow() - timedelta(minutes=5),
        "created_at": datetime.utcnow() - timedelta(days=1),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_organization_repository():
    """Create mock organization repository."""
    mock_repo = AsyncMock()
    mock_repo.create_organization.return_value = None
    mock_repo.get_organization_by_id.return_value = None
    mock_repo.get_organization_by_slug.return_value = None
    mock_repo.update_organization.return_value = None
    mock_repo.delete_organization.return_value = True
    mock_repo.list_organizations.return_value = []
    mock_repo.get_organization_stats.return_value = {
        "total_members": 0,
        "total_projects": 0,
        "total_tracks": 0,
        "total_meeting_rooms": 0
    }
    return mock_repo


@pytest.fixture
def mock_membership_repository():
    """Create mock membership repository."""
    mock_repo = AsyncMock()
    mock_repo.create_membership.return_value = None
    mock_repo.get_membership_by_id.return_value = None
    mock_repo.get_user_memberships.return_value = []
    mock_repo.get_organization_members.return_value = []
    mock_repo.update_membership.return_value = None
    mock_repo.delete_membership.return_value = True
    mock_repo.get_member_permissions.return_value = []
    mock_repo.has_permission.return_value = False
    return mock_repo


@pytest.fixture
def mock_track_repository():
    """Create mock track repository."""
    mock_repo = AsyncMock()
    mock_repo.create_track.return_value = None
    mock_repo.get_track_by_id.return_value = None
    mock_repo.list_organization_tracks.return_value = []
    mock_repo.update_track.return_value = None
    mock_repo.delete_track.return_value = True
    mock_repo.assign_student_to_track.return_value = None
    mock_repo.get_track_enrollments.return_value = []
    return mock_repo


@pytest.fixture
def mock_meeting_room_repository():
    """Create mock meeting room repository."""
    mock_repo = AsyncMock()
    mock_repo.create_meeting_room.return_value = None
    mock_repo.get_meeting_room_by_id.return_value = None
    mock_repo.list_organization_rooms.return_value = []
    mock_repo.update_meeting_room.return_value = None
    mock_repo.delete_meeting_room.return_value = True
    mock_repo.get_room_participants.return_value = []
    return mock_repo


@pytest.fixture
def mock_project_repository():
    """Create mock project repository."""
    mock_repo = AsyncMock()
    mock_repo.create_project.return_value = None
    mock_repo.get_project_by_id.return_value = None
    mock_repo.list_organization_projects.return_value = []
    mock_repo.update_project.return_value = None
    mock_repo.delete_project.return_value = True
    mock_repo.assign_instructor_to_project.return_value = None
    mock_repo.get_project_instructors.return_value = []
    return mock_repo


@pytest.fixture
def mock_user_repository():
    """Create mock user repository."""
    mock_repo = AsyncMock()
    mock_repo.create_user.return_value = None
    mock_repo.get_user_by_id.return_value = None
    mock_repo.get_user_by_email.return_value = None
    mock_repo.list_users.return_value = []
    mock_repo.update_user.return_value = None
    mock_repo.delete_user.return_value = True
    mock_repo.exists_by_email.return_value = False
    mock_repo.get_user_roles.return_value = []
    return mock_repo


@pytest.fixture
def mock_rbac_service():
    """Create mock RBAC service."""
    mock_service = AsyncMock()
    mock_service.create_organization.return_value = Mock()
    mock_service.add_organization_member.return_value = Mock()
    mock_service.remove_organization_member.return_value = True
    mock_service.create_track.return_value = Mock()
    mock_service.create_meeting_room.return_value = Mock()
    mock_service.check_permission.return_value = True
    mock_service.get_user_permissions.return_value = []
    mock_service.assign_project_access.return_value = True
    return mock_service


@pytest.fixture
def mock_teams_integration():
    """Create mock Teams integration service."""
    mock_integration = AsyncMock()
    mock_integration.create_meeting.return_value = {
        "meeting_id": "19:meeting_id@thread.v2",
        "join_url": "https://teams.microsoft.com/l/meetup-join/...",
        "organizer_url": "https://teams.microsoft.com/l/meetup-join/..."
    }
    mock_integration.delete_meeting.return_value = True
    mock_integration.get_meeting_info.return_value = {
        "id": "meeting_id",
        "subject": "Test Meeting",
        "participants": [],
        "status": "active"
    }
    mock_integration.test_connection.return_value = True
    return mock_integration


@pytest.fixture
def mock_zoom_integration():
    """Create mock Zoom integration service."""
    mock_integration = AsyncMock()
    mock_integration.create_meeting.return_value = {
        "meeting_id": "123456789",
        "join_url": "https://zoom.us/j/123456789",
        "password": "test123"
    }
    mock_integration.delete_meeting.return_value = True
    mock_integration.get_meeting_info.return_value = {
        "id": "123456789",
        "topic": "Test Meeting",
        "participants": [],
        "status": "waiting"
    }
    mock_integration.test_connection.return_value = True
    return mock_integration


@pytest.fixture
def mock_audit_logger():
    """Create mock audit logger for RBAC actions."""
    mock_logger = AsyncMock()
    mock_logger.log_organization_created.return_value = None
    mock_logger.log_member_added.return_value = None
    mock_logger.log_member_removed.return_value = None
    mock_logger.log_permission_granted.return_value = None
    mock_logger.log_permission_revoked.return_value = None
    mock_logger.log_track_created.return_value = None
    mock_logger.log_meeting_room_created.return_value = None
    mock_logger.log_organization_deleted.return_value = None
    return mock_logger


@pytest.fixture
def mock_email_service():
    """Create mock email service for RBAC notifications."""
    mock_service = AsyncMock()
    mock_service.send_invitation_email.return_value = True
    mock_service.send_role_assignment_email.return_value = True
    mock_service.send_track_enrollment_email.return_value = True
    mock_service.send_meeting_invitation_email.return_value = True
    return mock_service


@pytest.fixture
def rbac_test_data():
    """Complete RBAC test data set."""
    org_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    track_id = str(uuid.uuid4())
    
    return {
        "organization": {
            "id": org_id,
            "name": "Test University",
            "slug": "test-university",
            "description": "A comprehensive test organization",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        "project": {
            "id": project_id,
            "name": "Advanced Python Course",
            "organization_id": org_id,
            "status": "active"
        },
        "track": {
            "id": track_id,
            "name": "Full Stack Development",
            "project_id": project_id,
            "organization_id": org_id,
            "difficulty_level": "advanced",
            "duration_weeks": 16
        },
        "users": {
            "site_admin": {
                "id": str(uuid.uuid4()),
                "email": "siteadmin@platform.com",
                "full_name": "Site Administrator",
                "is_site_admin": True,
                "role": "site_admin"
            },
            "org_admin": {
                "id": str(uuid.uuid4()),
                "email": "admin@testuniversity.edu",
                "full_name": "Organization Administrator",
                "organization_id": org_id,
                "role": "organization_admin"
            },
            "instructor": {
                "id": str(uuid.uuid4()),
                "email": "instructor@testuniversity.edu",
                "full_name": "Test Instructor", 
                "organization_id": org_id,
                "role": "instructor",
                "project_access": [project_id]
            },
            "student": {
                "id": str(uuid.uuid4()),
                "email": "student@testuniversity.edu",
                "full_name": "Test Student",
                "organization_id": org_id,
                "role": "student",
                "track_enrollments": [track_id]
            }
        },
        "meeting_rooms": [
            {
                "id": str(uuid.uuid4()),
                "name": "Main Lecture Hall",
                "platform": "teams",
                "room_type": "organization_room",
                "organization_id": org_id
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Python Track Room", 
                "platform": "zoom",
                "room_type": "track_room",
                "track_id": track_id,
                "organization_id": org_id
            }
        ]
    }


@pytest.fixture
def mock_fastapi_rbac_client():
    """Create mock FastAPI client for RBAC testing."""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI, HTTPException, Depends
    from fastapi.security import HTTPBearer
    
    app = FastAPI()
    security = HTTPBearer()
    
    @app.get("/api/v1/rbac/organizations")
    def get_organizations():
        return [{"id": "org1", "name": "Test Org"}]
    
    @app.post("/api/v1/rbac/organizations")
    def create_organization(data: dict):
        return {"id": str(uuid.uuid4()), **data}
    
    @app.get("/api/v1/rbac/organizations/{org_id}/members")
    def get_organization_members(org_id: str):
        return [{"id": "member1", "role": "instructor"}]
    
    @app.post("/api/v1/rbac/organizations/{org_id}/members")
    def add_organization_member(org_id: str, data: dict):
        return {"id": str(uuid.uuid4()), **data}
    
    @app.delete("/api/v1/rbac/organizations/{org_id}/members/{member_id}")
    def remove_organization_member(org_id: str, member_id: str):
        return {"success": True}
    
    @app.get("/api/v1/rbac/organizations/{org_id}/meeting-rooms")
    def get_organization_rooms(org_id: str):
        return [{"id": "room1", "name": "Test Room"}]
    
    @app.post("/api/v1/rbac/organizations/{org_id}/meeting-rooms")
    def create_meeting_room(org_id: str, data: dict):
        return {"id": str(uuid.uuid4()), **data}
    
    @app.get("/api/v1/site-admin/organizations")
    def get_all_organizations():
        return [{"id": "org1", "name": "Test Org", "total_members": 5}]
    
    @app.delete("/api/v1/site-admin/organizations/{org_id}")
    def delete_organization(org_id: str, confirmation_name: str = None):
        return {
            "success": True,
            "organization_name": "Test Org",
            "deleted_members": 5,
            "deleted_meeting_rooms": 2
        }
    
    return TestClient(app)


class RBACTestUtils:
    """Utility class for RBAC testing."""
    
    @staticmethod
    def create_test_jwt_token(user_data: Dict[str, Any]) -> str:
        """Create a test JWT token for RBAC testing."""
        import jwt
        payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "role": user_data.get("role", "student"),
            "organization_id": user_data.get("organization_id"),
            "is_site_admin": user_data.get("is_site_admin", False),
            "permissions": user_data.get("permissions", []),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, "test_secret", algorithm="HS256")
    
    @staticmethod
    def create_mock_request_with_auth(user_data: Dict[str, Any]):
        """Create a mock FastAPI request with authentication."""
        token = RBACTestUtils.create_test_jwt_token(user_data)
        request_mock = Mock()
        request_mock.headers = {"Authorization": f"Bearer {token}"}
        return request_mock
    
    @staticmethod
    def assert_rbac_response_structure(response_data: Dict[str, Any], expected_fields: List[str]):
        """Assert that RBAC API response has expected structure."""
        for field in expected_fields:
            assert field in response_data, f"Missing field: {field}"
    
    @staticmethod
    def assert_permission_denied(response):
        """Assert that response indicates permission denied."""
        assert response.status_code == 403
        assert "permission" in response.json().get("detail", "").lower()
    
    @staticmethod
    def assert_authentication_required(response):
        """Assert that response indicates authentication required."""
        assert response.status_code == 401
        assert "unauthorized" in response.json().get("detail", "").lower()


# Make utility class available to all tests
pytest.RBACTestUtils = RBACTestUtils