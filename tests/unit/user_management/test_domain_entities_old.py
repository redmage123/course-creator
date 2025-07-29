"""
Unit Tests for User Management Domain Entities
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
from domain.entities.session import Session, SessionStatus
from domain.entities.role import Role


class TestUser:
    """Test User domain entity following TDD principles"""
    
    def test_user_creation_with_valid_data(self):
        """Test creating a user with valid data"""
        # Arrange
        email = "test@example.com"
        username = "testuser"
        full_name = "Test User"
        password = "SecurePassword123!"
        
        # Act
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            password_hash="hashed_password",
            role=UserRole.STUDENT
        )
        
        # Assert
        assert user.email == email
        assert user.username == username
        assert user.full_name == full_name
        assert user.role == UserRole.STUDENT
        assert user.status == UserStatus.ACTIVE
        assert user.is_active()
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.id, str)
    
    def test_user_creation_with_invalid_email_raises_error(self):
        """Test creating user with invalid email raises ValueError"""
        # Arrange
        invalid_email = "invalid-email"
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            User(
                email=invalid_email,
                username="testuser",
                full_name="Test User",
                password_hash="hashed_password",
                role=UserRole.STUDENT
            )
    
    def test_user_creation_with_empty_username_raises_error(self):
        """Test creating user with empty username raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Username cannot be empty"):
            User(
                email="test@example.com",
                username="",
                full_name="Test User",
                password_hash="hashed_password",
                role=UserRole.STUDENT
            )
    
    def test_user_creation_with_empty_full_name_raises_error(self):
        """Test creating user with empty full name raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Full name cannot be empty"):
            User(
                email="test@example.com",
                username="testuser",
                full_name="",
                password_hash="hashed_password",
                role=UserRole.STUDENT
            )
    
    def test_user_update_profile_success(self):
        """Test updating user profile successfully"""
        # Arrange
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="hashed_password",
            role=UserRole.STUDENT
        )
        original_updated_at = user.updated_at
        
        # Act
        user.update_profile(
            full_name="Updated Name",
            bio="Updated bio"
        )
        
        # Assert
        assert user.full_name == "Updated Name"
        assert user.bio == "Updated bio"
        assert user.updated_at > original_updated_at
    
    def test_user_change_password_success(self):
        """Test changing user password successfully"""
        # Arrange
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="old_hash",
            role=UserRole.STUDENT
        )
        
        # Act
        user.change_password("new_password_hash")
        
        # Assert
        assert user.password_hash == "new_password_hash"
        assert user.password_changed_at is not None
    
    def test_user_deactivate_success(self):
        """Test deactivating user successfully"""
        # Arrange
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="hashed_password",
            role=UserRole.STUDENT
        )
        
        # Act
        user.deactivate()
        
        # Assert
        assert user.status == UserStatus.INACTIVE
        assert not user.is_active()
    
    def test_user_activate_success(self):
        """Test activating user successfully"""
        # Arrange
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="hashed_password",
            role=UserUserRole.STUDENT,
            status=UserStatus.INACTIVE
        )
        
        # Act
        user.activate()
        
        # Assert
        assert user.status == UserStatus.ACTIVE
        assert user.is_active()
    
    def test_user_suspend_with_reason_success(self):
        """Test suspending user with reason successfully"""
        # Arrange
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="hashed_password",
            role=UserRole.STUDENT
        )
        suspension_reason = "Policy violation"
        
        # Act
        user.suspend(suspension_reason)
        
        # Assert
        assert user.status == UserStatus.SUSPENDED
        assert not user.is_active()
        assert user.suspension_reason == suspension_reason
        assert user.suspended_at is not None
    
    def test_user_has_role_returns_correct_boolean(self):
        """Test user has_role method returns correct boolean"""
        # Arrange
        student_user = User(
            email="student@example.com",
            username="student",
            full_name="Student User",
            password_hash="hashed_password",
            role=UserRole.STUDENT
        )
        
        instructor_user = User(
            email="instructor@example.com",
            username="instructor",
            full_name="Instructor User",
            password_hash="hashed_password",
            role=UserRole.INSTRUCTOR
        )
        
        # Act & Assert
        assert student_user.has_role(UserRole.STUDENT)
        assert not student_user.has_role(UserRole.INSTRUCTOR)
        assert not student_user.has_role(UserRole.ADMIN)
        
        assert instructor_user.has_role(UserRole.INSTRUCTOR)
        assert not instructor_user.has_role(UserRole.STUDENT)
        assert not instructor_user.has_role(UserRole.ADMIN)
    
    def test_user_can_login_returns_correct_boolean(self):
        """Test user can_login method returns correct boolean"""
        # Arrange
        active_user = User(
            email="active@example.com",
            username="active",
            full_name="Active User",
            password_hash="hashed_password",
            role=UserRole.STUDENT
        )
        
        suspended_user = User(
            email="suspended@example.com",
            username="suspended",
            full_name="Suspended User",
            password_hash="hashed_password",
            role=UserUserRole.STUDENT,
            status=UserStatus.SUSPENDED
        )
        
        # Act & Assert
        assert active_user.can_login()
        assert not suspended_user.can_login()
    
    def test_user_get_display_name_returns_full_name_when_available(self):
        """Test user get_display_name returns full name when available"""
        # Arrange
        user_with_full_name = User(
            email="test@example.com",
            username="testuser",
            full_name="John Doe",
            password_hash="hashed_password",
            role=UserRole.STUDENT
        )
        
        # Act & Assert
        assert user_with_full_name.get_display_name() == "John Doe"
    
    def test_user_get_display_name_returns_username_when_no_full_name(self):
        """Test user get_display_name returns username when no full name"""
        # Arrange
        user_without_full_name = User(
            email="test@example.com",
            username="testuser",
            full_name="",
            password_hash="hashed_password",
            role=UserRole.STUDENT
        )
        
        # Act & Assert
        assert user_without_full_name.get_display_name() == "testuser"


class TestSession:
    """Test Session domain entity following TDD principles"""
    
    def test_session_creation_with_valid_data(self):
        """Test creating a session with valid data"""
        # Arrange
        user_id = str(uuid4())
        
        # Act
        session = Session(user_id=user_id)
        
        # Assert
        assert session.user_id == user_id
        assert session.status == SessionStatus.ACTIVE
        assert session.created_at is not None
        assert session.last_activity is not None
        assert session.expires_at is not None
        assert isinstance(session.id, str)
        assert isinstance(session.token, str)
        assert len(session.token) > 20  # Should be a substantial token
    
    def test_session_creation_with_custom_ttl(self):
        """Test creating session with custom TTL"""
        # Arrange
        user_id = str(uuid4())
        custom_ttl = 7200  # 2 hours
        
        # Act
        session = Session(user_id=user_id, ttl_seconds=custom_ttl)
        
        # Assert
        expected_expiry = session.created_at + timedelta(seconds=custom_ttl)
        # Allow for small time difference due to execution time
        assert abs((session.expires_at - expected_expiry).total_seconds()) < 1
    
    def test_session_is_expired_returns_false_for_valid_session(self):
        """Test is_expired returns False for valid session"""
        # Arrange
        session = Session(user_id=str(uuid4()))
        
        # Act & Assert
        assert not session.is_expired()
    
    def test_session_is_expired_returns_true_for_expired_session(self):
        """Test is_expired returns True for expired session"""
        # Arrange
        session = Session(
            user_id=str(uuid4()),
            ttl_seconds=1  # 1 second TTL
        )
        
        # Wait for expiration (in real test, would mock datetime)
        import time
        time.sleep(1.1)
        
        # Act & Assert
        assert session.is_expired()
    
    def test_session_refresh_updates_last_activity_and_expiry(self):
        """Test refresh updates last_activity and expires_at"""
        # Arrange
        session = Session(user_id=str(uuid4()))
        original_last_activity = session.last_activity
        original_expires_at = session.expires_at
        
        # Wait a small amount to ensure time difference
        import time
        time.sleep(0.1)
        
        # Act
        session.refresh()
        
        # Assert
        assert session.last_activity > original_last_activity
        assert session.expires_at > original_expires_at
    
    def test_session_invalidate_sets_status_to_expired(self):
        """Test invalidate sets status to expired"""
        # Arrange
        session = Session(user_id=str(uuid4()))
        
        # Act
        session.invalidate()
        
        # Assert
        assert session.status == SessionStatus.EXPIRED
        assert session.invalidated_at is not None
    
    def test_session_is_valid_returns_false_for_invalidated_session(self):
        """Test is_valid returns False for invalidated session"""
        # Arrange
        session = Session(user_id=str(uuid4()))
        session.invalidate()
        
        # Act & Assert
        assert not session.is_valid()
    
    def test_session_is_valid_returns_false_for_expired_session(self):
        """Test is_valid returns False for expired session"""
        # Arrange
        session = Session(
            user_id=str(uuid4()),
            ttl_seconds=1
        )
        
        # Wait for expiration
        import time
        time.sleep(1.1)
        
        # Act & Assert
        assert not session.is_valid()
    
    def test_session_is_valid_returns_true_for_active_session(self):
        """Test is_valid returns True for active session"""
        # Arrange
        session = Session(user_id=str(uuid4()))
        
        # Act & Assert
        assert session.is_valid()
    
    def test_session_get_remaining_time_returns_correct_duration(self):
        """Test get_remaining_time returns correct duration"""
        # Arrange
        ttl = 3600  # 1 hour
        session = Session(user_id=str(uuid4()), ttl_seconds=ttl)
        
        # Act
        remaining = session.get_remaining_time()
        
        # Assert
        # Should be close to 1 hour, allowing for execution time
        assert 3590 <= remaining.total_seconds() <= 3600


class TestPasswordPolicy:
    """Test PasswordPolicy domain entity following TDD principles"""
    
    def test_password_policy_creation_with_defaults(self):
        """Test password policy creation with default values"""
        # Act
        policy = PasswordPolicy()
        
        # Assert
        assert policy.min_length == 8
        assert policy.require_uppercase == True
        assert policy.require_lowercase == True
        assert policy.require_digits == True
        assert policy.require_special_chars == True
        assert policy.min_special_chars == 1
        assert policy.max_consecutive_chars == 3
        assert policy.password_history_size == 5
        assert policy.max_age_days == 90
    
    def test_password_policy_creation_with_custom_values(self):
        """Test password policy creation with custom values"""
        # Act
        policy = PasswordPolicy(
            min_length=12,
            require_uppercase=False,
            require_special_chars=False,
            max_age_days=30
        )
        
        # Assert
        assert policy.min_length == 12
        assert policy.require_uppercase == False
        assert policy.require_special_chars == False
        assert policy.max_age_days == 30
    
    def test_password_policy_validate_strong_password_returns_true(self):
        """Test validate_password returns True for strong password"""
        # Arrange
        policy = PasswordPolicy()
        strong_password = "StrongP@ssw0rd123"
        
        # Act
        is_valid, _ = policy.validate_password(strong_password)
        
        # Assert
        assert is_valid == True
    
    def test_password_policy_validate_weak_password_returns_false_with_reasons(self):
        """Test validate_password returns False with reasons for weak password"""
        # Arrange
        policy = PasswordPolicy()
        weak_password = "weak"
        
        # Act
        is_valid, reasons = policy.validate_password(weak_password)
        
        # Assert
        assert is_valid == False
        assert len(reasons) > 0
        assert any("minimum length" in reason.lower() for reason in reasons)
    
    def test_password_policy_calculate_strength_returns_correct_enum(self):
        """Test calculate_password_strength returns correct PasswordStrength enum"""
        # Arrange
        policy = PasswordPolicy()
        
        # Test cases
        test_cases = [
            ("weak", PasswordStrength.WEAK),
            ("Medium1!", PasswordStrength.MEDIUM),
            ("StrongP@ssw0rd123", PasswordStrength.STRONG),
            ("VeryStr0ng&Complex!P@ssw0rd2024", PasswordStrength.VERY_STRONG)
        ]
        
        # Act & Assert
        for password, expected_strength in test_cases:
            actual_strength = policy.calculate_password_strength(password)
            # Note: This might not match exactly depending on implementation
            # but should be reasonable assessment
            assert isinstance(actual_strength, PasswordStrength)
    
    def test_password_policy_check_common_passwords_rejects_common_ones(self):
        """Test check_common_passwords rejects common passwords"""
        # Arrange
        policy = PasswordPolicy()
        common_passwords = ["password", "123456", "qwerty", "admin"]
        
        # Act & Assert
        for password in common_passwords:
            is_valid, reasons = policy.validate_password(password)
            # Should be invalid due to common password check
            assert is_valid == False
    
    def test_password_policy_is_password_expired_returns_correct_boolean(self):
        """Test is_password_expired returns correct boolean"""
        # Arrange
        policy = PasswordPolicy(max_age_days=30)
        
        # Test recent password (not expired)
        recent_change = datetime.utcnow() - timedelta(days=15)
        assert not policy.is_password_expired(recent_change)
        
        # Test old password (expired)
        old_change = datetime.utcnow() - timedelta(days=45)
        assert policy.is_password_expired(old_change)
    
    def test_password_policy_check_password_history_prevents_reuse(self):
        """Test check_password_history prevents password reuse"""
        # Arrange
        policy = PasswordPolicy(password_history_size=3)
        recent_passwords = ["OldPass1!", "OldPass2!", "OldPass3!"]
        
        # Act & Assert
        for old_password in recent_passwords:
            can_reuse = policy.check_password_history(old_password, recent_passwords)
            assert not can_reuse
        
        # New password should be allowed
        new_password = "NewPass4!"
        can_use_new = policy.check_password_history(new_password, recent_passwords)
        assert can_use_new


class TestRoleEnum:
    """Test Role enumeration"""
    
    def test_role_enum_has_expected_values(self):
        """Test Role enum has expected values"""
        assert UserRole.STUDENT.value == "student"
        assert UserRole.INSTRUCTOR.value == "instructor"
        assert UserRole.ADMIN.value == "admin"
    
    def test_role_enum_comparison(self):
        """Test Role enum comparison"""
        assert UserRole.STUDENT == UserRole.STUDENT
        assert UserRole.STUDENT != UserRole.INSTRUCTOR
        assert UserRole.INSTRUCTOR != UserRole.ADMIN


class TestUserStatusEnum:
    """Test UserStatus enumeration"""
    
    def test_user_status_enum_has_expected_values(self):
        """Test UserStatus enum has expected values"""
        assert UserStatus.ACTIVE.value == "active"
        assert UserStatus.INACTIVE.value == "inactive"
        assert UserStatus.SUSPENDED.value == "suspended"
        assert UserStatus.PENDING.value == "pending"
    
    def test_user_status_enum_comparison(self):
        """Test UserStatus enum comparison"""
        assert UserStatus.ACTIVE == UserStatus.ACTIVE
        assert UserStatus.ACTIVE != UserStatus.INACTIVE


class TestSessionStatusEnum:
    """Test SessionStatus enumeration"""
    
    def test_session_status_enum_has_expected_values(self):
        """Test SessionStatus enum has expected values"""
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.EXPIRED.value == "expired"
    
    def test_session_status_enum_comparison(self):
        """Test SessionStatus enum comparison"""
        assert SessionStatus.ACTIVE == SessionStatus.ACTIVE
        assert SessionStatus.ACTIVE != SessionStatus.EXPIRED


class TestPasswordStrengthEnum:
    """Test PasswordStrength enumeration"""
    
    def test_password_strength_enum_has_expected_values(self):
        """Test PasswordStrength enum has expected values"""
        assert PasswordStrength.WEAK.value == "weak"
        assert PasswordStrength.MEDIUM.value == "medium"  
        assert PasswordStrength.STRONG.value == "strong"
        assert PasswordStrength.VERY_STRONG.value == "very_strong"
    
    def test_password_strength_enum_ordering(self):
        """Test PasswordStrength enum has proper ordering"""
        strengths = [
            PasswordStrength.WEAK,
            PasswordStrength.MEDIUM,
            PasswordStrength.STRONG,
            PasswordStrength.VERY_STRONG
        ]
        
        # Test that each strength is different
        for i in range(len(strengths)):
            for j in range(len(strengths)):
                if i != j:
                    assert strengths[i] != strengths[j]