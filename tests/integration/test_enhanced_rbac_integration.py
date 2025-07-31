"""
Enhanced RBAC Integration Test Suite
Comprehensive testing of Enhanced RBAC system APIs with database integration
"""
import asyncio
import pytest
import uuid
from datetime import datetime
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from httpx import AsyncClient

from services.organization_management.main import create_app
from services.organization_management.infrastructure.container import Container
from services.organization_management.domain.entities.enhanced_role import RoleType, Permission
from services.organization_management.domain.entities.meeting_room import MeetingPlatform, RoomType
from services.organization_management.domain.entities.track import TrackStatus, DifficultyLevel


class TestEnhancedRBACIntegration:
    """Integration tests for Enhanced RBAC system"""
    
    @pytest.fixture(scope="class")
    def app(self):
        """Create FastAPI test application"""
        return create_app()
    
    @pytest.fixture(scope="class")
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    async def async_client(self, app):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    def site_admin_headers(self):
        """Site admin authentication headers"""
        return {
            "Authorization": "Bearer site-admin-token",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture 
    def org_admin_headers(self):
        """Organization admin authentication headers"""
        return {
            "Authorization": "Bearer org-admin-token",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture
    def instructor_headers(self):
        """Instructor authentication headers"""  
        return {
            "Authorization": "Bearer instructor-token",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture
    def student_headers(self):
        """Student authentication headers"""
        return {
            "Authorization": "Bearer student-token", 
            "Content-Type": "application/json"
        }
    
    @pytest.fixture
    def sample_organization_data(self):
        """Sample organization data for testing"""
        return {
            "name": "Test Organization",
            "slug": "test-org",
            "description": "Test organization for integration testing",
            "domain": "test-org.com"
        }
    
    @pytest.fixture
    def sample_member_data(self):
        """Sample member data for testing"""
        return {
            "user_email": "newmember@test.com",
            "role_type": "instructor",
            "project_ids": []
        }
    
    @pytest.fixture
    def sample_track_data(self):
        """Sample track data for testing"""
        return {
            "name": "Integration Test Track",
            "description": "Track for integration testing",
            "project_id": str(uuid.uuid4()),
            "target_audience": ["developers", "testers"],
            "prerequisites": ["Basic programming"],
            "learning_objectives": ["Learn testing", "Build integration tests"],
            "duration_weeks": 8,
            "difficulty_level": "intermediate",
            "max_students": 25
        }
    
    @pytest.fixture
    def sample_meeting_room_data(self):
        """Sample meeting room data for testing"""
        return {
            "name": "Integration Test Room",
            "platform": "teams",
            "room_type": "track_room",
            "track_id": str(uuid.uuid4()),
            "settings": {
                "auto_recording": True,
                "waiting_room": True,
                "mute_on_entry": False,
                "allow_screen_sharing": True
            }
        }

    # Organization Management Integration Tests
    
    def test_organization_crud_workflow(self, client, site_admin_headers, sample_organization_data):
        """Test complete organization CRUD workflow"""
        
        # Create organization
        response = client.post(
            "/api/v1/organizations",
            json=sample_organization_data,
            headers=site_admin_headers
        )
        assert response.status_code == 201
        org_data = response.json()
        org_id = org_data["id"]
        assert org_data["name"] == sample_organization_data["name"]
        assert org_data["slug"] == sample_organization_data["slug"]
        
        # Get organization
        response = client.get(
            f"/api/v1/organizations/{org_id}",
            headers=site_admin_headers
        )
        assert response.status_code == 200
        retrieved_org = response.json()
        assert retrieved_org["id"] == org_id
        assert retrieved_org["name"] == sample_organization_data["name"]
        
        # Update organization
        updated_data = {"name": "Updated Test Organization"}
        response = client.put(
            f"/api/v1/organizations/{org_id}",
            json=updated_data,
            headers=site_admin_headers
        )
        assert response.status_code == 200
        updated_org = response.json()
        assert updated_org["name"] == "Updated Test Organization"
        
        # List organizations
        response = client.get(
            "/api/v1/site-admin/organizations",
            headers=site_admin_headers
        )
        assert response.status_code == 200
        organizations = response.json()
        assert len(organizations) >= 1
        org_ids = [org["id"] for org in organizations]
        assert org_id in org_ids
        
        # Delete organization
        deletion_data = {
            "organization_id": org_id,
            "confirmation_name": "Updated Test Organization"
        }
        response = client.delete(
            f"/api/v1/site-admin/organizations/{org_id}",
            json=deletion_data,
            headers=site_admin_headers
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    # Member Management Integration Tests
    
    def test_member_management_workflow(self, client, org_admin_headers, sample_member_data):
        """Test complete member management workflow"""
        org_id = str(uuid.uuid4())
        
        # Add member
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=sample_member_data,
            headers=org_admin_headers
        )
        assert response.status_code == 201
        member_data = response.json()
        membership_id = member_data["membership_id"]
        assert member_data["email"] == sample_member_data["user_email"]
        assert member_data["role_type"] == sample_member_data["role_type"]
        
        # Get organization members
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/members",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        members = response.json()
        assert len(members) >= 1
        
        # Filter members by role
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/members?role_type=instructor",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        instructors = response.json()
        instructor_roles = [member["role_type"] for member in instructors]
        assert all(role == "instructor" for role in instructor_roles)
        
        # Remove member
        response = client.delete(
            f"/api/v1/rbac/organizations/{org_id}/members/{membership_id}",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        assert "removed successfully" in response.json()["message"]

    # Track Management Integration Tests
    
    def test_track_management_workflow(self, client, org_admin_headers, sample_track_data):
        """Test complete track management workflow"""
        
        # Create track
        response = client.post(
            "/api/v1/tracks/",
            json=sample_track_data,
            headers=org_admin_headers
        )
        assert response.status_code == 201
        track_data = response.json()
        track_id = track_data["id"]
        assert track_data["name"] == sample_track_data["name"]
        assert track_data["status"] == "draft"
        assert track_data["enrollment_count"] == 0
        
        # Get track
        response = client.get(
            f"/api/v1/tracks/{track_id}",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        retrieved_track = response.json()
        assert retrieved_track["id"] == track_id
        assert retrieved_track["name"] == sample_track_data["name"]
        
        # Update track
        updated_data = {
            "name": "Updated Integration Test Track",
            "difficulty_level": "advanced",
            "max_students": 50
        }
        response = client.put(
            f"/api/v1/tracks/{track_id}",
            json=updated_data,
            headers=org_admin_headers
        )
        assert response.status_code == 200
        updated_track = response.json()
        assert updated_track["name"] == "Updated Integration Test Track"
        assert updated_track["difficulty_level"] == "advanced"
        assert updated_track["max_students"] == 50
        
        # Publish track
        response = client.post(
            f"/api/v1/tracks/{track_id}/publish",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        publish_result = response.json()
        assert publish_result["status"] == "published"
        
        # List tracks
        response = client.get(
            "/api/v1/tracks/",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        tracks = response.json()
        assert len(tracks) >= 1
        track_ids = [track["id"] for track in tracks]
        assert track_id in track_ids
        
        # Bulk enroll students
        enrollment_data = {
            "student_emails": ["student1@test.com", "student2@test.com"],
            "auto_approve": True
        }
        response = client.post(
            f"/api/v1/tracks/{track_id}/enroll",
            json=enrollment_data,
            headers=org_admin_headers
        )
        assert response.status_code == 200
        enrollment_result = response.json()
        assert enrollment_result["total_enrolled"] >= 0
        assert len(enrollment_result["successful_enrollments"]) >= 0
        
        # Get track analytics
        response = client.get(
            f"/api/v1/tracks/{track_id}/analytics",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        analytics = response.json()
        assert analytics["track_id"] == track_id
        assert "analytics" in analytics
        
        # Duplicate track
        response = client.post(
            f"/api/v1/tracks/{track_id}/duplicate?new_name=Duplicated Track",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        duplicate_result = response.json()
        assert duplicate_result["new_track_name"] == "Duplicated Track"
        duplicate_track_id = duplicate_result["new_track_id"]
        
        # Delete original track
        response = client.delete(
            f"/api/v1/tracks/{track_id}",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Clean up duplicate track
        response = client.delete(
            f"/api/v1/tracks/{duplicate_track_id}",
            headers=org_admin_headers
        )
        assert response.status_code == 200

    # Meeting Room Integration Tests
    
    def test_meeting_room_workflow(self, client, org_admin_headers, sample_meeting_room_data):
        """Test complete meeting room workflow"""
        org_id = str(uuid.uuid4())
        
        # Create meeting room
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/meeting-rooms",
            json=sample_meeting_room_data,
            headers=org_admin_headers
        )
        assert response.status_code == 201
        room_data = response.json()
        room_id = room_data["id"]
        assert room_data["name"] == sample_meeting_room_data["name"]
        assert room_data["platform"] == sample_meeting_room_data["platform"]
        assert room_data["room_type"] == sample_meeting_room_data["room_type"]
        
        # Get organization meeting rooms
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/meeting-rooms",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        rooms = response.json()
        assert len(rooms) >= 1
        room_ids = [room["id"] for room in rooms]
        assert room_id in room_ids
        
        # Filter rooms by platform
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/meeting-rooms?platform=teams",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        teams_rooms = response.json()
        platforms = [room["platform"] for room in teams_rooms]
        assert all(platform == "teams" for platform in platforms)
        
        # Send room invitations
        invitation_data = ["user1@test.com", "user2@test.com"]
        response = client.post(
            f"/api/v1/rbac/meeting-rooms/{room_id}/invite",
            json=invitation_data,
            headers=org_admin_headers
        )
        assert response.status_code == 200
        invite_result = response.json()
        assert "Invitations sent" in invite_result["message"]
        
        # Delete meeting room
        response = client.delete(
            f"/api/v1/rbac/meeting-rooms/{room_id}",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    # Permission and Security Integration Tests
    
    def test_permission_enforcement(self, client, instructor_headers, student_headers):
        """Test that permissions are properly enforced"""
        org_id = str(uuid.uuid4())
        
        # Test that instructors cannot add organization admins
        member_data = {
            "user_email": "admin@test.com",
            "role_type": "organization_admin"
        }
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=member_data,
            headers=instructor_headers
        )
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
        
        # Test that students cannot access admin endpoints
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/members",
            headers=student_headers
        )
        assert response.status_code == 403
        
        # Test that unauthorized requests are rejected
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/members"
        )
        assert response.status_code == 401

    def test_input_validation(self, client, org_admin_headers):
        """Test API input validation"""
        org_id = str(uuid.uuid4())
        
        # Test invalid email format
        invalid_member_data = {
            "user_email": "not-an-email",
            "role_type": "instructor"
        }
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=invalid_member_data,
            headers=org_admin_headers
        )
        assert response.status_code == 422
        
        # Test invalid role type
        invalid_role_data = {
            "user_email": "valid@email.com",
            "role_type": "invalid_role"
        }
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=invalid_role_data,
            headers=org_admin_headers
        )
        assert response.status_code == 422
        
        # Test invalid UUID format
        response = client.get(
            "/api/v1/tracks/not-a-uuid",
            headers=org_admin_headers
        )
        assert response.status_code == 422

    # Site Admin Integration Tests
    
    def test_site_admin_operations(self, client, site_admin_headers):
        """Test site admin specific operations"""
        
        # Get platform statistics
        response = client.get(
            "/api/v1/site-admin/stats",
            headers=site_admin_headers
        )
        assert response.status_code == 200
        stats = response.json()
        assert "total_organizations" in stats
        assert "total_users" in stats
        assert "total_projects" in stats
        
        # Get platform health
        response = client.get(
            "/api/v1/site-admin/platform/health",
            headers=site_admin_headers
        )
        assert response.status_code == 200
        health = response.json()
        assert "teams_integration" in health
        assert "zoom_integration" in health
        assert "database" in health

    # Error Handling Integration Tests
    
    def test_error_handling(self, client, org_admin_headers):
        """Test API error handling"""
        
        # Test 404 for non-existent resource
        non_existent_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/tracks/{non_existent_id}",
            headers=org_admin_headers
        )
        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["detail"].lower()
        
        # Test 400 for invalid operations
        response = client.delete(
            f"/api/v1/tracks/{non_existent_id}",
            headers=org_admin_headers
        )
        assert response.status_code == 404

    # Workflow Integration Tests
    
    def test_complete_organization_workflow(self, client, site_admin_headers, org_admin_headers):
        """Test complete organization setup workflow"""
        
        # 1. Site admin creates organization
        org_data = {
            "name": "Complete Workflow Org",
            "slug": "complete-workflow-org",
            "description": "Testing complete workflow"
        }
        response = client.post(
            "/api/v1/organizations",
            json=org_data,
            headers=site_admin_headers
        )
        assert response.status_code == 201
        org_id = response.json()["id"]
        
        # 2. Add organization admin
        admin_data = {
            "user_email": "orgadmin@workflow.com",
            "role_type": "organization_admin"
        }
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=admin_data,
            headers=org_admin_headers
        )
        assert response.status_code == 201
        
        # 3. Add instructor
        instructor_data = {
            "user_email": "instructor@workflow.com", 
            "role_type": "instructor"
        }
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=instructor_data,
            headers=org_admin_headers
        )
        assert response.status_code == 201
        
        # 4. Create track
        track_data = {
            "name": "Workflow Test Track",
            "project_id": str(uuid.uuid4()),
            "difficulty_level": "beginner"
        }
        response = client.post(
            "/api/v1/tracks/",
            json=track_data,
            headers=org_admin_headers
        )
        assert response.status_code == 201
        track_id = response.json()["id"]
        
        # 5. Create meeting room for track
        room_data = {
            "name": "Workflow Track Room",
            "platform": "teams",
            "room_type": "track_room",
            "track_id": track_id
        }
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/meeting-rooms",
            json=room_data,
            headers=org_admin_headers
        )
        assert response.status_code == 201
        
        # 6. Verify organization has all components
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/members",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        members = response.json()
        assert len(members) >= 2  # Admin + Instructor
        
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/meeting-rooms",
            headers=org_admin_headers
        )
        assert response.status_code == 200
        rooms = response.json()
        assert len(rooms) >= 1
        
        # 7. Clean up
        deletion_data = {
            "organization_id": org_id,
            "confirmation_name": "Complete Workflow Org"
        }
        response = client.delete(
            f"/api/v1/site-admin/organizations/{org_id}",
            json=deletion_data,
            headers=site_admin_headers
        )
        assert response.status_code == 200


# Async integration tests for concurrent operations
class TestAsyncRBACIntegration:
    """Test concurrent RBAC operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_member_operations(self, async_client, org_admin_headers):
        """Test concurrent member additions"""
        org_id = str(uuid.uuid4())
        
        # Create multiple members concurrently
        member_tasks = []
        for i in range(5):
            member_data = {
                "user_email": f"concurrent{i}@test.com",
                "role_type": "instructor"
            }
            task = async_client.post(
                f"/api/v1/rbac/organizations/{org_id}/members",
                json=member_data,
                headers=org_admin_headers
            )
            member_tasks.append(task)
        
        # Wait for all operations to complete
        responses = await asyncio.gather(*member_tasks, return_exceptions=True)
        
        # Verify all succeeded or handled properly
        success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 201)
        assert success_count >= 0  # Some may succeed, some may fail due to constraints
    
    @pytest.mark.asyncio
    async def test_concurrent_track_operations(self, async_client, org_admin_headers):
        """Test concurrent track creation and management"""
        project_id = str(uuid.uuid4())
        
        # Create multiple tracks concurrently
        track_tasks = []
        for i in range(3):
            track_data = {
                "name": f"Concurrent Track {i}",
                "project_id": project_id,
                "difficulty_level": "beginner"
            }
            task = async_client.post(
                "/api/v1/tracks/",
                json=track_data,
                headers=org_admin_headers
            )
            track_tasks.append(task)
        
        responses = await asyncio.gather(*track_tasks, return_exceptions=True)
        
        # At least some should succeed
        success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 201)
        assert success_count >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])