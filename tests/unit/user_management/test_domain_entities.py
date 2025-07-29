"""
Unit Tests for User Management Domain Entities (Simplified)
Following SOLID principles and TDD methodology
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

# Import domain entities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'user-management'))

from domain.entities.user import User, UserRole, UserStatus


class TestUser:
    """Test User domain entity following TDD principles"""
    
    def test_user_creation_with_valid_data(self):
        """Test creating user with valid data"""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "role": UserRole.STUDENT,
            "status": UserStatus.ACTIVE
        }
        
        # Act
        user = User(**user_data)
        
        # Assert
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.role == UserRole.STUDENT
        assert user.status == UserStatus.ACTIVE
        assert user.id is not None
    
    def test_user_validation_with_invalid_email(self):
        """Test user validation fails with invalid email"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            User(
                email="invalid-email",
                username="testuser",
                full_name="Test User"
            )
    
    def test_user_validation_with_empty_username(self):
        """Test user validation fails with empty username"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Username is required"):
            User(
                email="test@example.com",
                username="",
                full_name="Test User"
            )
    
    def test_user_role_change(self):
        """Test changing user role"""
        # Arrange
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT
        )
        
        # Act
        user.change_role(UserRole.INSTRUCTOR)
        
        # Assert
        assert user.role == UserRole.INSTRUCTOR
    
    def test_user_status_change(self):
        """Test changing user status"""
        # Arrange
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            status=UserStatus.ACTIVE
        )
        
        # Act
        user.change_status(UserStatus.INACTIVE)
        
        # Assert
        assert user.status == UserStatus.INACTIVE
    
    def test_user_is_active(self):
        """Test user active status check"""
        # Arrange
        active_user = User(
            email="active@example.com",
            username="activeuser",
            full_name="Active User",
            status=UserStatus.ACTIVE
        )
        
        inactive_user = User(
            email="inactive@example.com",
            username="inactiveuser", 
            full_name="Inactive User",
            status=UserStatus.INACTIVE
        )
        
        # Act & Assert
        assert active_user.is_active() is True
        assert inactive_user.is_active() is False
    
    def test_user_is_instructor(self):
        """Test user instructor privileges check"""
        # Arrange
        student_user = User(
            email="student@example.com",
            username="student",
            full_name="Student User",
            role=UserRole.STUDENT
        )
        
        instructor_user = User(
            email="instructor@example.com",
            username="instructor",
            full_name="Instructor User",
            role=UserRole.INSTRUCTOR
        )
        
        admin_user = User(
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            role=UserRole.ADMIN
        )
        
        # Act & Assert
        assert student_user.is_instructor() is False
        assert instructor_user.is_instructor() is True
        assert admin_user.is_instructor() is True
    
    def test_user_can_create_courses(self):
        """Test user course creation permissions"""
        # Arrange
        active_instructor = User(
            email="instructor@example.com",
            username="instructor",
            full_name="Instructor User",
            role=UserRole.INSTRUCTOR,
            status=UserStatus.ACTIVE
        )
        
        inactive_instructor = User(
            email="inactive@example.com",
            username="inactive",
            full_name="Inactive Instructor",
            role=UserRole.INSTRUCTOR,
            status=UserStatus.INACTIVE
        )
        
        student = User(
            email="student@example.com",
            username="student",
            full_name="Student User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        
        # Act & Assert
        assert active_instructor.can_create_courses() is True
        assert inactive_instructor.can_create_courses() is False
        assert student.can_create_courses() is False


class TestUserRole:
    """Test UserRole enum"""
    
    def test_user_role_values(self):
        """Test UserRole enum values"""
        # Act & Assert
        assert UserRole.STUDENT.value == "student"
        assert UserRole.INSTRUCTOR.value == "instructor"
        assert UserRole.ADMIN.value == "admin"
    
    def test_user_role_equality(self):
        """Test UserRole enum equality"""
        # Act & Assert
        assert UserRole.STUDENT == UserRole.STUDENT
        assert UserRole.STUDENT != UserRole.INSTRUCTOR
        assert UserRole.INSTRUCTOR != UserRole.ADMIN


class TestUserStatus:
    """Test UserStatus enum"""
    
    def test_user_status_values(self):
        """Test UserStatus enum values"""
        # Act & Assert
        assert UserStatus.ACTIVE.value == "active"
        assert UserStatus.INACTIVE.value == "inactive"
        assert UserStatus.SUSPENDED.value == "suspended"
        assert UserStatus.PENDING.value == "pending"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])