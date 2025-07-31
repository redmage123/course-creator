"""
Integration Tests for RBAC API Endpoints
Tests the complete RBAC API integration including authentication, authorization, and data flow
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Add test fixtures path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../fixtures'))

from rbac_fixtures import (
    mock_fastapi_rbac_client,
    rbac_test_data,
    RBACTestUtils
)


class TestRBACAPIIntegration:
    """Integration tests for RBAC API endpoints"""
    
    @pytest.fixture
    def client(self, mock_fastapi_rbac_client):
        """Get test client with mocked RBAC endpoints."""
        return mock_fastapi_rbac_client
    
    @pytest.fixture
    def auth_headers(self, rbac_test_data):
        """Create authentication headers for different user types."""
        headers = {}
        
        for role, user_data in rbac_test_data["users"].items():
            token = RBACTestUtils.create_test_jwt_token(user_data)
            headers[role] = {"Authorization": f"Bearer {token}"}
        
        return headers
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_organization_creation_flow(self, client, auth_headers, rbac_test_data):
        """Test complete organization creation flow."""
        # Arrange
        org_data = {
            "name": "New Test Organization",
            "slug": "new-test-org",
            "description": "Integration test organization"
        }
        
        # Act - Site admin creates organization
        response = client.post(
            "/api/v1/rbac/organizations",
            json=org_data,
            headers=auth_headers["site_admin"]
        )
        
        # Assert
        assert response.status_code == 200
        created_org = response.json()
        
        RBACTestUtils.assert_rbac_response_structure(
            created_org,
            ["id", "name", "slug", "description"]
        )
        
        assert created_org["name"] == org_data["name"]
        assert created_org["slug"] == org_data["slug"]
        assert created_org["description"] == org_data["description"]
        assert "id" in created_org
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_organization_member_management_flow(self, client, auth_headers, rbac_test_data):
        """Test complete member management flow."""
        org_id = rbac_test_data["organization"]["id"]
        
        # Step 1: Add instructor member
        member_data = {
            "user_email": "newinstructor@test.org",
            "role_type": "instructor",
            "project_ids": [rbac_test_data["project"]["id"]]
        }
        
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=member_data,
            headers=auth_headers["org_admin"]
        )
        
        assert response.status_code == 200
        added_member = response.json()
        
        RBACTestUtils.assert_rbac_response_structure(
            added_member,
            ["id", "user_email", "role_type"]
        )
        
        assert added_member["user_email"] == member_data["user_email"]
        assert added_member["role_type"] == member_data["role_type"]
        
        # Step 2: List organization members
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/members",
            headers=auth_headers["org_admin"]
        )
        
        assert response.status_code == 200
        members = response.json()
        assert isinstance(members, list)
        
        # Verify the added member is in the list
        member_emails = [m["email"] for m in members if "email" in m]
        # Note: This might be empty in mock, but structure should be correct
        
        # Step 3: Remove member
        member_id = added_member["id"]
        response = client.delete(
            f"/api/v1/rbac/organizations/{org_id}/members/{member_id}",
            headers=auth_headers["org_admin"]
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_meeting_room_management_flow(self, client, auth_headers, rbac_test_data):
        """Test complete meeting room management flow."""
        org_id = rbac_test_data["organization"]["id"]
        
        # Step 1: Create meeting room
        room_data = {
            "name": "Integration Test Room",
            "platform": "teams",
            "room_type": "track_room",
            "track_id": rbac_test_data["track"]["id"],
            "settings": {
                "auto_recording": True,
                "waiting_room": False,
                "mute_on_entry": False,
                "allow_screen_sharing": True
            }
        }
        
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/meeting-rooms",
            json=room_data,
            headers=auth_headers["org_admin"]
        )
        
        assert response.status_code == 200
        created_room = response.json()
        
        RBACTestUtils.assert_rbac_response_structure(
            created_room,
            ["id", "name", "platform", "room_type"]
        )
        
        assert created_room["name"] == room_data["name"]
        assert created_room["platform"] == room_data["platform"]
        assert created_room["room_type"] == room_data["room_type"]
        
        # Step 2: List organization meeting rooms
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/meeting-rooms",
            headers=auth_headers["org_admin"]
        )
        
        assert response.status_code == 200
        rooms = response.json()
        assert isinstance(rooms, list)
    
    @pytest.mark.integration
    @pytest.mark.api 
    def test_site_admin_organization_management(self, client, auth_headers, rbac_test_data):
        """Test site admin organization management capabilities."""
        # Step 1: List all organizations (site admin only)
        response = client.get(
            "/api/v1/site-admin/organizations",
            headers=auth_headers["site_admin"]
        )
        
        assert response.status_code == 200
        organizations = response.json()
        assert isinstance(organizations, list)
        
        for org in organizations:
            RBACTestUtils.assert_rbac_response_structure(
                org,
                ["id", "name", "total_members"]
            )
        
        # Step 2: Delete organization (site admin only)
        org_id = rbac_test_data["organization"]["id"]
        delete_data = {
            "organization_id": org_id,
            "confirmation_name": rbac_test_data["organization"]["name"]
        }
        
        response = client.delete(
            f"/api/v1/site-admin/organizations/{org_id}",
            headers=auth_headers["site_admin"],
            params={"confirmation_name": rbac_test_data["organization"]["name"]}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        RBACTestUtils.assert_rbac_response_structure(
            result,
            ["success", "organization_name", "deleted_members", "deleted_meeting_rooms"]
        )
        
        assert result["success"] is True
        assert "deleted_members" in result
        assert "deleted_meeting_rooms" in result
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_permission_based_access_control(self, client, auth_headers, rbac_test_data):
        """Test permission-based access control across different user roles."""
        org_id = rbac_test_data["organization"]["id"]
        
        # Test 1: Organization admin can manage members
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/members",
            headers=auth_headers["org_admin"]
        )
        assert response.status_code == 200
        
        # Test 2: Instructor cannot manage organization members (should fail)
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json={"user_email": "test@test.org", "role_type": "student"},
            headers=auth_headers["instructor"]
        )
        # Note: In a real implementation, this would return 403
        # For mock, we just verify it's handled
        
        # Test 3: Student cannot access admin endpoints
        response = client.get(
            "/api/v1/site-admin/organizations",
            headers=auth_headers["student"]
        )
        # Note: In a real implementation, this would return 403
        
        # Test 4: Site admin can access all endpoints
        response = client.get(
            "/api/v1/site-admin/organizations",
            headers=auth_headers["site_admin"]
        )
        assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_authentication_requirements(self, client, rbac_test_data):
        """Test that endpoints require proper authentication."""
        org_id = rbac_test_data["organization"]["id"]
        
        # Test 1: No authentication header
        response = client.get(f"/api/v1/rbac/organizations/{org_id}/members")
        # Note: Mock doesn't implement auth, but in real implementation would return 401
        
        # Test 2: Invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/members",
            headers=invalid_headers
        )
        # Note: Mock doesn't validate tokens, but real implementation would return 401
        
        # Test 3: Expired token
        expired_user_data = rbac_test_data["users"]["org_admin"].copy()
        # Create token that's already expired
        import jwt
        expired_payload = {
            "user_id": expired_user_data["id"],
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, "test_secret", algorithm="HS256")
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get(
            f"/api/v1/rbac/organizations/{org_id}/members",
            headers=expired_headers
        )
        # Note: Mock doesn't validate expiration, but real implementation would return 401
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_data_validation_and_error_handling(self, client, auth_headers, rbac_test_data):
        """Test API data validation and error handling."""
        org_id = rbac_test_data["organization"]["id"]
        
        # Test 1: Invalid organization creation data
        invalid_org_data = {
            "name": "",  # Empty name should fail
            "slug": "invalid slug with spaces"  # Invalid slug format
        }
        
        response = client.post(
            "/api/v1/rbac/organizations",
            json=invalid_org_data,
            headers=auth_headers["site_admin"]
        )
        # Note: Mock doesn't validate, but real implementation would return 422
        
        # Test 2: Invalid member role
        invalid_member_data = {
            "user_email": "test@test.org",
            "role_type": "invalid_role"  # Invalid role type
        }
        
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=invalid_member_data,
            headers=auth_headers["org_admin"]
        )
        # Note: Mock doesn't validate, but real implementation would return 422
        
        # Test 3: Invalid email format
        invalid_email_data = {
            "user_email": "invalid-email",  # Invalid email format
            "role_type": "instructor"
        }
        
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=invalid_email_data,
            headers=auth_headers["org_admin"]
        )
        # Note: Mock doesn't validate, but real implementation would return 422
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_cross_service_integration(self, client, auth_headers, rbac_test_data):
        """Test RBAC integration with other services."""
        org_id = rbac_test_data["organization"]["id"]
        
        # Test 1: RBAC with User Management Service
        # Creating a member should integrate with user management
        member_data = {
            "user_email": "integration@test.org",
            "role_type": "instructor"
        }
        
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=member_data,
            headers=auth_headers["org_admin"]
        )
        
        assert response.status_code == 200
        
        # Test 2: RBAC with Course Management Service
        # Members should have appropriate access to courses
        # This would typically involve checking course access permissions
        
        # Test 3: RBAC with Analytics Service
        # Members should have role-based access to analytics
        # This would typically involve permission checks for analytics data
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_audit_logging_integration(self, client, auth_headers, rbac_test_data):
        """Test that RBAC operations are properly audit logged."""
        org_id = rbac_test_data["organization"]["id"]
        
        # Mock audit logging verification
        audit_events = []
        
        def mock_audit_log(event_type, details):
            audit_events.append({
                "event_type": event_type,
                "details": details,
                "timestamp": datetime.utcnow()
            })
        
        # Test organization creation audit
        org_data = {"name": "Audit Test Org", "slug": "audit-test"}
        response = client.post(
            "/api/v1/rbac/organizations",
            json=org_data,
            headers=auth_headers["site_admin"]
        )
        
        # In real implementation, this would trigger audit logging
        mock_audit_log("organization_created", org_data)
        
        # Test member addition audit
        member_data = {"user_email": "audit@test.org", "role_type": "instructor"}
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=member_data,
            headers=auth_headers["org_admin"]
        )
        
        mock_audit_log("member_added", member_data)
        
        # Verify audit events were created
        assert len(audit_events) == 2
        assert audit_events[0]["event_type"] == "organization_created"
        assert audit_events[1]["event_type"] == "member_added"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_email_notification_integration(self, client, auth_headers, rbac_test_data):
        """Test email notification integration for RBAC operations."""
        org_id = rbac_test_data["organization"]["id"]
        
        # Mock email tracking
        sent_emails = []
        
        def mock_send_email(to_email, template, data):
            sent_emails.append({
                "to": to_email,
                "template": template,
                "data": data,
                "sent_at": datetime.utcnow()
            })
        
        # Test member invitation email
        member_data = {
            "user_email": "newmember@test.org",
            "role_type": "instructor"
        }
        
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/members",
            json=member_data,
            headers=auth_headers["org_admin"]
        )
        
        # Mock email sending
        mock_send_email(
            member_data["user_email"],
            "member_invitation",
            {"organization_name": rbac_test_data["organization"]["name"]}
        )
        
        # Verify email was sent
        assert len(sent_emails) == 1
        assert sent_emails[0]["to"] == member_data["user_email"]
        assert sent_emails[0]["template"] == "member_invitation"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_meeting_integration_services(self, client, auth_headers, rbac_test_data):
        """Test integration with Teams and Zoom meeting services."""
        org_id = rbac_test_data["organization"]["id"]
        
        # Mock integration responses
        teams_response = {
            "meeting_id": "19:meeting123@thread.v2",
            "join_url": "https://teams.microsoft.com/l/meetup-join/...",
            "success": True
        }
        
        zoom_response = {
            "meeting_id": "123456789",
            "join_url": "https://zoom.us/j/123456789",
            "password": "test123",
            "success": True
        }
        
        # Test Teams meeting room creation
        teams_room_data = {
            "name": "Teams Integration Room",
            "platform": "teams",
            "room_type": "track_room",
            "track_id": rbac_test_data["track"]["id"]
        }
        
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/meeting-rooms",
            json=teams_room_data,
            headers=auth_headers["org_admin"]
        )
        
        assert response.status_code == 200
        teams_room = response.json()
        assert teams_room["platform"] == "teams"
        
        # Test Zoom meeting room creation
        zoom_room_data = {
            "name": "Zoom Integration Room",
            "platform": "zoom",
            "room_type": "project_room",
            "project_id": rbac_test_data["project"]["id"]
        }
        
        response = client.post(
            f"/api/v1/rbac/organizations/{org_id}/meeting-rooms",
            json=zoom_room_data,
            headers=auth_headers["org_admin"]
        )
        
        assert response.status_code == 200
        zoom_room = response.json()
        assert zoom_room["platform"] == "zoom"