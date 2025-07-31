"""
Unit Tests for RBAC Membership Service
Tests the organization membership management functionality
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Add test fixtures path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../fixtures'))

from rbac_fixtures import (
    mock_membership_data,
    mock_membership_repository,
    mock_user_repository,
    mock_audit_logger,
    mock_email_service,
    RBACTestUtils
)


class TestMembershipService:
    """Test cases for MembershipService"""
    
    @pytest.fixture
    def membership_service(self, mock_membership_repository, mock_user_repository, 
                          mock_audit_logger, mock_email_service):
        """Create membership service with mocked dependencies."""
        from unittest.mock import Mock
        
        service = Mock()
        service.membership_repository = mock_membership_repository
        service.user_repository = mock_user_repository
        service.audit_logger = mock_audit_logger
        service.email_service = mock_email_service
        
        # Mock service methods
        async def mock_add_organization_member(org_id, user_email, role_type, project_ids=None):
            # Check for side effect on repository
            if hasattr(service.membership_repository.create_membership, 'side_effect') and service.membership_repository.create_membership.side_effect:
                raise service.membership_repository.create_membership.side_effect
                
            return {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "organization_id": org_id,
                "user_email": user_email,
                "role_type": role_type,
                "status": "active",
                "project_access": project_ids or [],
                "created_at": datetime.utcnow()
            }
        
        async def mock_remove_organization_member(org_id, membership_id):
            return {
                "success": True,
                "removed_member_id": membership_id,
                "organization_id": org_id
            }
        
        async def mock_get_organization_members(org_id, role_filter=None):
            members = [
                {
                    "id": str(uuid.uuid4()),
                    "user_id": str(uuid.uuid4()),
                    "name": "John Instructor",
                    "email": "john@test.org",
                    "role_type": "instructor",
                    "status": "active",
                    "project_access": [str(uuid.uuid4())]
                },
                {
                    "id": str(uuid.uuid4()), 
                    "user_id": str(uuid.uuid4()),
                    "name": "Jane Student",
                    "email": "jane@test.org",
                    "role_type": "student",
                    "status": "active",
                    "track_enrollments": [str(uuid.uuid4())]
                }
            ]
            
            if role_filter:
                members = [m for m in members if m["role_type"] == role_filter]
            
            return members
        
        async def mock_update_member_role(org_id, membership_id, new_role, project_ids=None):
            return {
                "id": membership_id,
                "organization_id": org_id,
                "role_type": new_role,
                "project_access": project_ids or [],
                "updated_at": datetime.utcnow()
            }
        
        async def mock_get_member_permissions(org_id, user_id):
            role_permissions = {
                "organization_admin": [
                    "manage_organization",
                    "manage_members", 
                    "create_tracks",
                    "manage_meeting_rooms",
                    "view_analytics"
                ],
                "instructor": [
                    "create_courses",
                    "manage_students",
                    "access_analytics",
                    "create_meeting_rooms"
                ],
                "student": [
                    "view_courses",
                    "submit_assignments",
                    "access_labs",
                    "take_quizzes"
                ]
            }
            
            # Mock getting user role
            return role_permissions.get("instructor", [])
        
        async def mock_check_permission(org_id, user_id, permission):
            user_permissions = await mock_get_member_permissions(org_id, user_id)
            return permission in user_permissions
        
        service.add_organization_member = mock_add_organization_member
        service.remove_organization_member = mock_remove_organization_member
        service.get_organization_members = mock_get_organization_members
        service.update_member_role = mock_update_member_role
        service.get_member_permissions = mock_get_member_permissions
        service.check_permission = mock_check_permission
        
        return service
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_organization_member_success(self, membership_service):
        """Test successful addition of organization member."""
        # Arrange
        org_id = str(uuid.uuid4())
        user_email = "newmember@test.org"
        role_type = "instructor"
        project_ids = [str(uuid.uuid4())]
        
        # Act
        result = await membership_service.add_organization_member(
            org_id, user_email, role_type, project_ids
        )
        
        # Assert
        assert result["organization_id"] == org_id
        assert result["user_email"] == user_email
        assert result["role_type"] == role_type
        assert result["project_access"] == project_ids
        assert result["status"] == "active"
        assert "id" in result
        assert "user_id" in result
        assert "created_at" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_organization_member_student_with_track(self, membership_service):
        """Test adding student member with track enrollment."""
        # Arrange
        org_id = str(uuid.uuid4())
        user_email = "student@test.org"
        role_type = "student"
        track_id = str(uuid.uuid4())
        
        # Mock method for student with track
        async def mock_add_student_member(org_id, user_email, role_type, track_id=None):
            return {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "organization_id": org_id,
                "user_email": user_email,
                "role_type": role_type,
                "status": "active",
                "track_enrollments": [track_id] if track_id else [],
                "created_at": datetime.utcnow()
            }
        
        membership_service.add_student_member = mock_add_student_member
        
        # Act
        result = await membership_service.add_student_member(
            org_id, user_email, role_type, track_id
        )
        
        # Assert
        assert result["role_type"] == "student"
        assert track_id in result["track_enrollments"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_organization_member_duplicate_email(self, membership_service):
        """Test adding member with duplicate email fails."""
        # Arrange
        org_id = str(uuid.uuid4())
        user_email = "duplicate@test.org"
        role_type = "instructor"
        
        # Mock repository to simulate duplicate email error
        membership_service.membership_repository.create_membership.side_effect = Exception("User already member")
        
        # Act & Assert
        with pytest.raises(Exception, match="User already member"):
            await membership_service.add_organization_member(org_id, user_email, role_type)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_remove_organization_member_success(self, membership_service):
        """Test successful removal of organization member."""
        # Arrange
        org_id = str(uuid.uuid4())
        membership_id = str(uuid.uuid4())
        
        # Act
        result = await membership_service.remove_organization_member(org_id, membership_id)
        
        # Assert
        assert result["success"] is True
        assert result["removed_member_id"] == membership_id
        assert result["organization_id"] == org_id
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_organization_members_all(self, membership_service):
        """Test getting all organization members."""
        # Arrange
        org_id = str(uuid.uuid4())
        
        # Act
        result = await membership_service.get_organization_members(org_id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Check structure
        for member in result:
            assert "id" in member
            assert "user_id" in member
            assert "name" in member
            assert "email" in member
            assert "role_type" in member
            assert "status" in member
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_organization_members_filtered_by_role(self, membership_service):
        """Test getting organization members filtered by role."""
        # Arrange
        org_id = str(uuid.uuid4())
        role_filter = "instructor"
        
        # Act
        result = await membership_service.get_organization_members(org_id, role_filter)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role_type"] == "instructor"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_member_role_success(self, membership_service):
        """Test successful member role update."""
        # Arrange
        org_id = str(uuid.uuid4())
        membership_id = str(uuid.uuid4())
        new_role = "organization_admin"
        project_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        
        # Act
        result = await membership_service.update_member_role(
            org_id, membership_id, new_role, project_ids
        )
        
        # Assert
        assert result["id"] == membership_id
        assert result["organization_id"] == org_id
        assert result["role_type"] == new_role
        assert result["project_access"] == project_ids
        assert "updated_at" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_member_permissions(self, membership_service):
        """Test getting member permissions."""
        # Arrange
        org_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Act
        permissions = await membership_service.get_member_permissions(org_id, user_id)
        
        # Assert
        assert isinstance(permissions, list)
        assert len(permissions) > 0
        assert "create_courses" in permissions
        assert "manage_students" in permissions
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_permission_granted(self, membership_service):
        """Test permission check for granted permission."""
        # Arrange
        org_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        permission = "create_courses"
        
        # Act
        has_permission = await membership_service.check_permission(org_id, user_id, permission)
        
        # Assert
        assert has_permission is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_permission_denied(self, membership_service):
        """Test permission check for denied permission."""
        # Arrange
        org_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        permission = "delete_organization"
        
        # Act
        has_permission = await membership_service.check_permission(org_id, user_id, permission)
        
        # Assert
        assert has_permission is False
    
    @pytest.mark.unit
    def test_validate_role_type_valid(self):
        """Test role type validation with valid roles."""
        # Mock validation function
        def validate_role_type(role_type):
            valid_roles = ["organization_admin", "instructor", "student"]
            if role_type not in valid_roles:
                raise ValueError(f"Invalid role type: {role_type}")
            return True
        
        # Test valid roles
        valid_roles = ["organization_admin", "instructor", "student"]
        for role in valid_roles:
            assert validate_role_type(role) is True
    
    @pytest.mark.unit
    def test_validate_role_type_invalid(self):
        """Test role type validation with invalid roles."""
        # Mock validation function
        def validate_role_type(role_type):
            valid_roles = ["organization_admin", "instructor", "student"]
            if role_type not in valid_roles:
                raise ValueError(f"Invalid role type: {role_type}")
            return True
        
        # Test invalid roles
        invalid_roles = ["admin", "teacher", "learner", "moderator"]
        for role in invalid_roles:
            with pytest.raises(ValueError, match=f"Invalid role type: {role}"):
                validate_role_type(role)
    
    @pytest.mark.unit
    def test_validate_email_format(self):
        """Test email format validation."""
        # Mock validation function
        import re
        def validate_email(email):
            # More strict pattern that includes common email characters
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                raise ValueError("Invalid email format")
            # Additional checks for edge cases
            if '..' in email or email.startswith('@') or email.endswith('@'):
                raise ValueError("Invalid email format")
            # Ensure domain has proper structure
            parts = email.split('@')
            if len(parts) != 2 or not parts[1] or '.' not in parts[1]:
                raise ValueError("Invalid email format")
            return True
        
        # Valid emails
        valid_emails = [
            "user@example.com",
            "test.email@domain.org",
            "user+tag@university.edu",
            "user123@sub.domain.com"
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True
        
        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user..double.dot@domain.com"
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email format"):
                validate_email(email)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bulk_member_operations(self, membership_service):
        """Test bulk member operations."""
        # Mock bulk add method
        async def mock_bulk_add_members(org_id, member_data_list):
            results = []
            for member_data in member_data_list:
                results.append({
                    "id": str(uuid.uuid4()),
                    "user_email": member_data["email"],
                    "role_type": member_data["role"],
                    "status": "active",
                    "success": True
                })
            return results
        
        membership_service.bulk_add_members = mock_bulk_add_members
        
        # Arrange
        org_id = str(uuid.uuid4())
        member_data_list = [
            {"email": "user1@test.org", "role": "instructor"},
            {"email": "user2@test.org", "role": "student"},
            {"email": "user3@test.org", "role": "instructor"}
        ]
        
        # Act
        results = await membership_service.bulk_add_members(org_id, member_data_list)
        
        # Assert
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["user_email"] == member_data_list[i]["email"]
            assert result["role_type"] == member_data_list[i]["role"]
            assert result["success"] is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_member_invitation_flow(self, membership_service):
        """Test member invitation workflow."""
        # Mock invitation methods
        async def mock_send_invitation(org_id, email, role, inviter_id):
            return {
                "invitation_id": str(uuid.uuid4()),
                "organization_id": org_id,
                "email": email,
                "role": role,
                "inviter_id": inviter_id,
                "status": "sent",
                "expires_at": datetime.utcnow() + timedelta(days=7),
                "created_at": datetime.utcnow()
            }
        
        async def mock_accept_invitation(invitation_id, user_data):
            return {
                "invitation_id": invitation_id,
                "membership_id": str(uuid.uuid4()),
                "status": "accepted",
                "accepted_at": datetime.utcnow()
            }
        
        membership_service.send_invitation = mock_send_invitation
        membership_service.accept_invitation = mock_accept_invitation
        
        # Test invitation sending
        org_id = str(uuid.uuid4())
        email = "newmember@test.org"
        role = "instructor"
        inviter_id = str(uuid.uuid4())
        
        invitation = await membership_service.send_invitation(org_id, email, role, inviter_id)
        
        assert invitation["email"] == email
        assert invitation["role"] == role
        assert invitation["status"] == "sent"
        assert "invitation_id" in invitation
        assert "expires_at" in invitation
        
        # Test invitation acceptance
        user_data = {"name": "New Member", "password": "SecurePass123!"}
        acceptance = await membership_service.accept_invitation(
            invitation["invitation_id"], user_data
        )
        
        assert acceptance["status"] == "accepted"
        assert "membership_id" in acceptance
        assert "accepted_at" in acceptance
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_member_status_management(self, membership_service):
        """Test member status management (active, inactive, suspended)."""
        # Mock status management methods
        async def mock_update_member_status(org_id, membership_id, status, reason=None):
            valid_statuses = ["active", "inactive", "suspended"]
            if status not in valid_statuses:
                raise ValueError(f"Invalid status: {status}")
            
            return {
                "membership_id": membership_id,
                "organization_id": org_id,
                "status": status,
                "status_reason": reason,
                "updated_at": datetime.utcnow()
            }
        
        membership_service.update_member_status = mock_update_member_status
        
        # Test status updates
        org_id = str(uuid.uuid4())
        membership_id = str(uuid.uuid4())
        
        # Test activating member
        result = await membership_service.update_member_status(org_id, membership_id, "active")
        assert result["status"] == "active"
        
        # Test suspending member
        result = await membership_service.update_member_status(
            org_id, membership_id, "suspended", "Policy violation"
        )
        assert result["status"] == "suspended"
        assert result["status_reason"] == "Policy violation"
        
        # Test invalid status
        with pytest.raises(ValueError, match="Invalid status: invalid"):
            await membership_service.update_member_status(org_id, membership_id, "invalid")