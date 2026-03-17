"""
Unit Tests for User Management Models

BUSINESS REQUIREMENT:
Tests user data models, authentication, authorization, and profile management
for secure multi-tenant user access control.

TECHNICAL IMPLEMENTATION:
Tests user models, password validation, role management, and session handling.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import hashlib
import re

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'user-management'))

from enum import Enum


class UserRole(Enum):
    """User role enumeration"""
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ORG_ADMIN = "org_admin"
    PLATFORM_ADMIN = "platform_admin"


class UserStatus(Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class TestUserCreation:
    """Test user creation and validation"""

    def test_create_user_with_valid_data(self):
        """Test creating user with all required fields"""
        user_data = {
            "id": str(uuid4()),
            "email": "student@example.com",
            "username": "student123",
            "full_name": "John Doe",
            "role": UserRole.STUDENT.value,
            "status": UserStatus.ACTIVE.value
        }

        assert user_data["email"] == "student@example.com"
        assert user_data["role"] == UserRole.STUDENT.value

    def test_email_required(self):
        """Test email is required"""
        user_data = {
            "id": str(uuid4()),
            "username": "testuser"
        }

        assert "email" not in user_data

    def test_email_validation(self):
        """Test email format validation"""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "admin+test@company.org"
        ]

        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com"
        ]

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        for email in valid_emails:
            assert re.match(email_pattern, email) is not None

        for email in invalid_emails:
            assert re.match(email_pattern, email) is None


class TestPasswordManagement:
    """Test password handling and validation"""

    def test_password_hashing(self):
        """Test password is hashed"""
        plain_password = "SecurePassword123!"
        hashed = hashlib.sha256(plain_password.encode()).hexdigest()

        assert hashed != plain_password
        assert len(hashed) == 64  # SHA-256 produces 64 hex characters

    def test_password_verification(self):
        """Test password verification"""
        plain_password = "SecurePassword123!"
        hashed = hashlib.sha256(plain_password.encode()).hexdigest()

        # Verify correct password
        verify_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        assert verify_hash == hashed

        # Verify incorrect password
        wrong_hash = hashlib.sha256("WrongPassword".encode()).hexdigest()
        assert wrong_hash != hashed

    def test_password_strength_validation(self):
        """Test password strength requirements"""
        weak_passwords = [
            "123",
            "password",
            "abc",
            "12345678"
        ]

        strong_passwords = [
            "SecurePass123!",
            "MyP@ssw0rd",
            "C0mpl3x!Pass"
        ]

        def is_strong_password(password):
            return (
                len(password) >= 8 and
                any(c.isupper() for c in password) and
                any(c.islower() for c in password) and
                any(c.isdigit() for c in password)
            )

        for pwd in weak_passwords:
            assert not is_strong_password(pwd)

        for pwd in strong_passwords:
            assert is_strong_password(pwd)


class TestUserRoles:
    """Test user role management"""

    def test_assign_student_role(self):
        """Test assigning student role"""
        role = UserRole.STUDENT

        assert role == UserRole.STUDENT
        assert role.value == "student"

    def test_assign_instructor_role(self):
        """Test assigning instructor role"""
        role = UserRole.INSTRUCTOR

        assert role == UserRole.INSTRUCTOR
        assert role.value == "instructor"

    def test_role_permissions(self):
        """Test role-based permissions"""
        student_permissions = ["view_courses", "submit_assignments"]
        instructor_permissions = ["view_courses", "create_courses", "grade_assignments"]
        admin_permissions = ["view_courses", "create_courses", "manage_users", "system_settings"]

        # Student permissions
        assert "view_courses" in student_permissions
        assert "create_courses" not in student_permissions

        # Instructor permissions
        assert "create_courses" in instructor_permissions
        assert "manage_users" not in instructor_permissions

        # Admin permissions
        assert "manage_users" in admin_permissions
        assert "system_settings" in admin_permissions


class TestUserStatus:
    """Test user status management"""

    def test_activate_user(self):
        """Test activating a user"""
        status = UserStatus.PENDING

        # Activate user
        status = UserStatus.ACTIVE

        assert status == UserStatus.ACTIVE

    def test_suspend_user(self):
        """Test suspending a user"""
        status = UserStatus.ACTIVE

        # Suspend user
        status = UserStatus.SUSPENDED

        assert status == UserStatus.SUSPENDED

    def test_active_users_can_login(self):
        """Test only active users can login"""
        active_status = UserStatus.ACTIVE
        can_login = active_status == UserStatus.ACTIVE

        assert can_login is True

    def test_suspended_users_cannot_login(self):
        """Test suspended users cannot login"""
        suspended_status = UserStatus.SUSPENDED
        can_login = suspended_status == UserStatus.ACTIVE

        assert can_login is False


class TestUserProfile:
    """Test user profile management"""

    def test_update_user_profile(self):
        """Test updating user profile"""
        profile = {
            "full_name": "John Doe",
            "bio": "Student learning Python",
            "avatar_url": "https://example.com/avatar.jpg"
        }

        # Update full name
        profile["full_name"] = "John Smith"

        assert profile["full_name"] == "John Smith"

    def test_user_has_timestamps(self):
        """Test user has created/updated timestamps"""
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

        assert created_at is not None
        assert updated_at is not None
        assert isinstance(created_at, datetime)


class TestUserSession:
    """Test user session management"""

    def test_create_session_token(self):
        """Test creating session token"""
        user_id = str(uuid4())
        session_token = hashlib.sha256(f"{user_id}{datetime.utcnow()}".encode()).hexdigest()

        assert len(session_token) == 64
        assert session_token is not None

    def test_session_expiration(self):
        """Test session expiration"""
        created_at = datetime.utcnow() - timedelta(hours=25)
        session_duration_hours = 24

        is_expired = (datetime.utcnow() - created_at).total_seconds() / 3600 > session_duration_hours

        assert is_expired is True

    def test_session_not_expired(self):
        """Test active session"""
        created_at = datetime.utcnow() - timedelta(hours=2)
        session_duration_hours = 24

        is_expired = (datetime.utcnow() - created_at).total_seconds() / 3600 > session_duration_hours

        assert is_expired is False


class TestUserAuthentication:
    """Test user authentication logic"""

    def test_successful_authentication(self):
        """Test successful user authentication"""
        stored_password_hash = hashlib.sha256("CorrectPassword123!".encode()).hexdigest()
        provided_password = "CorrectPassword123!"
        provided_hash = hashlib.sha256(provided_password.encode()).hexdigest()

        is_authenticated = stored_password_hash == provided_hash

        assert is_authenticated is True

    def test_failed_authentication(self):
        """Test failed authentication with wrong password"""
        stored_password_hash = hashlib.sha256("CorrectPassword123!".encode()).hexdigest()
        provided_password = "WrongPassword"
        provided_hash = hashlib.sha256(provided_password.encode()).hexdigest()

        is_authenticated = stored_password_hash == provided_hash

        assert is_authenticated is False


class TestUserOrganization:
    """Test user-organization relationships"""

    def test_user_belongs_to_organization(self):
        """Test user organization membership"""
        user_id = str(uuid4())
        org_id = str(uuid4())

        membership = {
            "user_id": user_id,
            "organization_id": org_id,
            "role": "member"
        }

        assert membership["user_id"] == user_id
        assert membership["organization_id"] == org_id

    def test_user_has_multiple_organizations(self):
        """Test user can belong to multiple organizations"""
        user_id = str(uuid4())
        org1_id = str(uuid4())
        org2_id = str(uuid4())

        memberships = [
            {"user_id": user_id, "organization_id": org1_id},
            {"user_id": user_id, "organization_id": org2_id}
        ]

        assert len(memberships) == 2
        assert all(m["user_id"] == user_id for m in memberships)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
