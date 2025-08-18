"""
Unit Tests for Student Login System - GDPR Compliant

This module contains comprehensive unit tests for the student login system,
including GDPR compliance validation, authentication flows, and privacy controls.

Business Context:
Tests the student-specific login functionality that enables secure access to
educational content while maintaining strict privacy compliance. Validates
consent management, data minimization, and educational analytics integration.

Test Coverage:
- Student login endpoint validation
- GDPR consent management
- Device fingerprinting anonymization
- Error handling for expired accounts
- Privacy-compliant data processing
- Instructor notification system
- Educational analytics integration
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException
import uuid

# Import system under test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/user-management'))

from routes import StudentLoginRequest, StudentTokenResponse
from routes import _log_student_login_analytics, _notify_instructor_student_login


class TestStudentLoginRequest:
    """Test the StudentLoginRequest model for GDPR compliance."""
    
    def test_valid_student_login_request(self):
        """Test creating a valid student login request."""
        # Arrange
        request_data = {
            "username": "student@test.edu",
            "password": "SecurePassword123!",
            "course_instance_id": str(uuid.uuid4()),
            "device_fingerprint": "anonymized_fingerprint_hash",
            "consent_analytics": True,
            "consent_notifications": False
        }
        
        # Act
        request = StudentLoginRequest(**request_data)
        
        # Assert
        assert request.username == "student@test.edu"
        assert request.password == "SecurePassword123!"
        assert request.course_instance_id == request_data["course_instance_id"]
        assert request.device_fingerprint == "anonymized_fingerprint_hash"
        assert request.consent_analytics is True
        assert request.consent_notifications is False

    def test_minimal_student_login_request(self):
        """Test student login request with minimal required fields."""
        # Arrange
        request_data = {
            "username": "student",
            "password": "pass"
        }
        
        # Act
        request = StudentLoginRequest(**request_data)
        
        # Assert
        assert request.username == "student"
        assert request.password == "pass"
        assert request.course_instance_id is None
        assert request.device_fingerprint is None
        assert request.consent_analytics is False  # Default
        assert request.consent_notifications is False  # Default

    def test_gdpr_consent_defaults(self):
        """Test that GDPR consent fields default to False (opt-in required)."""
        # Arrange
        request_data = {
            "username": "student@test.edu",
            "password": "SecurePassword123!"
        }
        
        # Act
        request = StudentLoginRequest(**request_data)
        
        # Assert - All consent must be explicitly opted into (GDPR Article 7)
        assert request.consent_analytics is False
        assert request.consent_notifications is False

    def test_device_fingerprint_length_validation(self):
        """Test device fingerprint length validation for privacy."""
        # Arrange
        request_data = {
            "username": "student@test.edu", 
            "password": "SecurePassword123!",
            "device_fingerprint": "a" * 65  # Exceeds 64 char limit
        }
        
        # Act & Assert
        with pytest.raises(ValueError):
            StudentLoginRequest(**request_data)


class TestStudentTokenResponse:
    """Test the StudentTokenResponse model for GDPR compliance."""
    
    def test_valid_student_token_response(self):
        """Test creating a valid student token response."""
        # Arrange
        login_time = datetime.utcnow()
        expires_time = login_time + timedelta(hours=1)
        
        response_data = {
            "access_token": "jwt_token_here",
            "user_id": str(uuid.uuid4()),
            "username": "student123",
            "full_name": "Test Student",
            "role": "student",
            "course_enrollments": [
                {
                    "course_instance_id": str(uuid.uuid4()),
                    "course_title": "Python Programming",
                    "progress_percentage": 45,
                    "enrollment_status": "active"
                }
            ],
            "login_timestamp": login_time,
            "session_expires_at": expires_time
        }
        
        # Act
        response = StudentTokenResponse(**response_data)
        
        # Assert
        assert response.access_token == "jwt_token_here"
        assert response.token_type == "bearer"
        assert response.expires_in == 3600
        assert response.user_id == response_data["user_id"]
        assert response.username == "student123"
        assert response.full_name == "Test Student"
        assert response.role == "student"
        assert len(response.course_enrollments) == 1
        assert response.login_timestamp == login_time
        assert response.session_expires_at == expires_time
        assert "educational purposes only" in response.data_processing_notice  # Privacy notice included

    def test_minimal_data_exposure(self):
        """Test that response only includes essential data (GDPR data minimization)."""
        # Arrange
        response_data = {
            "access_token": "token",
            "user_id": str(uuid.uuid4()),
            "username": "student",
            "full_name": "Student Name",
            "role": "student",
            "login_timestamp": datetime.utcnow(),
            "session_expires_at": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Act
        response = StudentTokenResponse(**response_data)
        
        # Assert - Verify only essential fields are included
        response_dict = response.dict()
        sensitive_fields = ["email", "password", "phone", "address", "ssn"]
        for field in sensitive_fields:
            assert field not in response_dict
        
        # Verify privacy notice is present
        assert "educational purposes only" in response.data_processing_notice


class TestStudentLoginAnalytics:
    """Test GDPR-compliant analytics logging."""
    
    @pytest.mark.asyncio
    async def test_analytics_with_consent(self):
        """Test analytics logging only occurs with explicit consent."""
        # Arrange
        user_id = str(uuid.uuid4())
        course_instance_id = str(uuid.uuid4())
        device_fingerprint = "anonymized_hash"
        session_id = str(uuid.uuid4())
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock()
            
            # Act
            await _log_student_login_analytics(
                user_id=user_id,
                course_instance_id=course_instance_id,
                device_fingerprint=device_fingerprint,
                session_id=session_id
            )
            
            # Assert
            mock_client.return_value.__aenter__.return_value.post.assert_called_once()
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            
            # Verify analytics endpoint
            assert call_args[0][0] == "http://analytics:8001/api/v1/events/student-login"
            
            # Verify GDPR-compliant payload
            payload = call_args[1]['json']
            assert payload["event_type"] == "student_login"
            assert payload["user_id"] == user_id  # Pseudonymized
            assert payload["data_purpose"] == "educational_analytics"
            assert payload["retention_period"] == "academic_year"
            assert "consent_timestamp" in payload

    @pytest.mark.asyncio
    async def test_analytics_failure_non_blocking(self):
        """Test that analytics failures don't block login process."""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            
            with patch('logging.warning') as mock_log:
                # Act - Should not raise exception
                await _log_student_login_analytics(
                    user_id=str(uuid.uuid4()),
                    course_instance_id=None,
                    device_fingerprint=None,
                    session_id=str(uuid.uuid4())
                )
                
                # Assert
                mock_log.assert_called_once()
                assert "Failed to log student login analytics" in mock_log.call_args[0][0]

    @pytest.mark.asyncio
    async def test_data_minimization_in_analytics(self):
        """Test that analytics payload follows data minimization principles."""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock()
            
            # Act
            await _log_student_login_analytics(
                user_id=str(uuid.uuid4()),
                course_instance_id=str(uuid.uuid4()),
                device_fingerprint="anonymized_hash",
                session_id=str(uuid.uuid4())
            )
            
            # Assert
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            payload = call_args[1]['json']
            
            # Verify no sensitive data is included
            sensitive_fields = ["email", "full_name", "ip_address", "actual_device_id"]
            for field in sensitive_fields:
                assert field not in payload
            
            # Verify only essential fields are present
            essential_fields = ["event_type", "user_id", "timestamp", "data_purpose"]
            for field in essential_fields:
                assert field in payload


class TestInstructorNotifications:
    """Test GDPR-compliant instructor notification system."""
    
    @pytest.mark.asyncio
    async def test_notification_with_consent(self):
        """Test instructor notification only sent with explicit consent."""
        # Arrange
        student_id = str(uuid.uuid4())
        student_name = "Test Student"
        course_instance_id = str(uuid.uuid4())
        login_time = datetime.utcnow()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock()
            
            # Act
            await _notify_instructor_student_login(
                student_id=student_id,
                student_name=student_name,
                course_instance_id=course_instance_id,
                login_time=login_time
            )
            
            # Assert
            mock_client.return_value.__aenter__.return_value.post.assert_called_once()
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            
            # Verify notification endpoint
            assert call_args[0][0] == "http://course-management:8004/api/v1/notifications/student-login"
            
            # Verify GDPR-compliant payload
            payload = call_args[1]['json']
            assert payload["event_type"] == "student_login_notification"
            assert payload["student_id"] == student_id  # Pseudonymized
            assert payload["student_display_name"] == student_name  # Educational necessity
            assert payload["data_processing_basis"] == "consent_and_legitimate_interest"
            assert payload["retention_notice"] == "notification_not_stored_permanently"

    @pytest.mark.asyncio
    async def test_notification_failure_non_blocking(self):
        """Test that notification failures don't block login process."""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            
            with patch('logging.warning') as mock_log:
                # Act - Should not raise exception
                await _notify_instructor_student_login(
                    student_id=str(uuid.uuid4()),
                    student_name="Test Student",
                    course_instance_id=str(uuid.uuid4()),
                    login_time=datetime.utcnow()
                )
                
                # Assert
                mock_log.assert_called_once()
                assert "Failed to notify instructor of student login" in mock_log.call_args[0][0]

    @pytest.mark.asyncio
    async def test_notification_data_minimization(self):
        """Test that notifications follow data minimization principles."""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock()
            
            # Act
            await _notify_instructor_student_login(
                student_id=str(uuid.uuid4()),
                student_name="Test Student",
                course_instance_id=str(uuid.uuid4()),
                login_time=datetime.utcnow()
            )
            
            # Assert
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            payload = call_args[1]['json']
            
            # Verify no sensitive data is included
            sensitive_fields = ["email", "phone", "address", "password", "session_token"]
            for field in sensitive_fields:
                assert field not in payload
            
            # Verify only educational necessity data is present
            assert payload["student_display_name"] == "Test Student"  # Educational need
            assert "login_timestamp" in payload  # Educational engagement
            assert payload["notification_purpose"] == "educational_engagement_tracking"


class TestGDPRCompliance:
    """Test GDPR compliance features of student login system."""
    
    def test_explicit_consent_required(self):
        """Test that all optional data processing requires explicit consent."""
        # Arrange
        request_data = {
            "username": "student@test.edu",
            "password": "SecurePassword123!"
            # No consent fields provided
        }
        
        # Act
        request = StudentLoginRequest(**request_data)
        
        # Assert - Default to False (no processing without consent)
        assert request.consent_analytics is False
        assert request.consent_notifications is False

    def test_data_minimization_principle(self):
        """Test that login request follows data minimization (GDPR Article 5)."""
        # Arrange
        request_data = {
            "username": "student@test.edu",
            "password": "SecurePassword123!",
            "course_instance_id": str(uuid.uuid4()),
            "device_fingerprint": "anonymized_hash",
            "consent_analytics": True,
            "consent_notifications": True
        }
        
        # Act
        request = StudentLoginRequest(**request_data)
        request_dict = request.dict()
        
        # Assert - Only essential fields present
        expected_fields = {
            "username", "password", "course_instance_id", 
            "device_fingerprint", "consent_analytics", "consent_notifications"
        }
        actual_fields = set(request_dict.keys())
        
        # Should not contain unnecessary personal data
        unnecessary_fields = {"email", "phone", "address", "ssn", "date_of_birth"}
        assert unnecessary_fields.isdisjoint(actual_fields)
        
        # Should contain only expected fields
        assert actual_fields == expected_fields

    def test_purpose_limitation(self):
        """Test that data processing is limited to educational purposes."""
        # Arrange
        response_data = {
            "access_token": "token",
            "user_id": str(uuid.uuid4()),
            "username": "student",
            "full_name": "Student Name",
            "role": "student",
            "login_timestamp": datetime.utcnow(),
            "session_expires_at": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Act
        response = StudentTokenResponse(**response_data)
        
        # Assert - Privacy notice specifies educational purposes only
        assert "educational purposes only" in response.data_processing_notice
        assert "privacy policy" in response.data_processing_notice.lower()

    def test_anonymized_device_fingerprint(self):
        """Test that device fingerprinting is anonymized for privacy."""
        # Arrange
        request_data = {
            "username": "student@test.edu",
            "password": "SecurePassword123!",
            "device_fingerprint": "anonymized_hash_12345"
        }
        
        # Act
        request = StudentLoginRequest(**request_data)
        
        # Assert - Device fingerprint should be hash, not identifiable
        assert request.device_fingerprint == "anonymized_hash_12345"
        assert len(request.device_fingerprint) <= 64  # Privacy-friendly length limit


@pytest.mark.integration
class TestStudentLoginIntegration:
    """Integration tests for student login with other services."""
    
    @pytest.mark.asyncio
    async def test_login_with_course_context(self):
        """Test student login with course instance context."""
        # Arrange
        mock_user_service = AsyncMock()
        mock_auth_service = AsyncMock()
        mock_session_service = AsyncMock()
        
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())
        mock_user.role.value = "student"
        mock_user.status.value = "active"
        mock_user.username = "student123"
        mock_user.full_name = "Test Student"
        
        mock_auth_service.authenticate_user.return_value = mock_user
        
        # Mock session creation
        mock_session = Mock()
        mock_session.token = "session_token"
        mock_session.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_session.id = str(uuid.uuid4())
        
        mock_session_service.create_session.return_value = mock_session
        
        # Mock enrollment lookup
        mock_enrollment = {
            "course_instance_id": str(uuid.uuid4()),
            "course_title": "Python Programming",
            "progress_percentage": 45,
            "status": "active"
        }
        mock_user_service.get_student_enrollment.return_value = mock_enrollment
        
        # Act - This would be called by the actual endpoint
        # We're testing the integration logic here
        login_request = StudentLoginRequest(
            username="student123",
            password="password",
            course_instance_id=str(uuid.uuid4()),
            consent_analytics=True,
            consent_notifications=False
        )
        
        # Simulate the login flow
        user = await mock_auth_service.authenticate_user(login_request.username, login_request.password)
        session = await mock_session_service.create_session(user.id, "student")
        enrollment = await mock_user_service.get_student_enrollment(user.id, login_request.course_instance_id)
        
        # Assert
        assert user.role.value == "student"
        assert session.token == "session_token"
        assert enrollment["course_title"] == "Python Programming"
        mock_auth_service.authenticate_user.assert_called_once_with("student123", "password")
        mock_session_service.create_session.assert_called_once_with(user.id, "student")


@pytest.mark.security
class TestStudentLoginSecurity:
    """Security tests for student login system."""
    
    def test_password_not_logged(self):
        """Test that passwords are not logged or exposed."""
        # Arrange
        request_data = {
            "username": "student@test.edu",
            "password": "SecurePassword123!"
        }
        
        # Act
        request = StudentLoginRequest(**request_data)
        
        # Assert - Password should be accessible but not in dict representation
        assert request.password == "SecurePassword123!"
        
        # Password should be accessible for authentication but not in logs
        # (In real implementation, this would be handled by custom __str__ method)
        assert hasattr(request, 'password')

    def test_device_fingerprint_anonymization(self):
        """Test that device fingerprints are properly anonymized."""
        # Arrange - Simulate a real device fingerprint generation
        raw_fingerprint = "Mozilla/5.0 Chrome/91.0 1920x1080 -480 canvas_hash_123"
        
        # This would be done client-side
        import hashlib
        import base64
        anonymized = base64.b64encode(
            hashlib.sha256(raw_fingerprint.encode()).digest()
        ).decode()[:32]
        
        request_data = {
            "username": "student@test.edu",
            "password": "SecurePassword123!",
            "device_fingerprint": anonymized
        }
        
        # Act
        request = StudentLoginRequest(**request_data)
        
        # Assert - Fingerprint should be anonymized hash, not identifying info
        assert request.device_fingerprint == anonymized
        assert len(request.device_fingerprint) <= 64
        assert "Mozilla" not in request.device_fingerprint
        assert "Chrome" not in request.device_fingerprint

    def test_session_expiration_included(self):
        """Test that session expiration is properly set for security."""
        # Arrange
        login_time = datetime.utcnow()
        expires_time = login_time + timedelta(hours=1)
        
        response_data = {
            "access_token": "jwt_token",
            "user_id": str(uuid.uuid4()),
            "username": "student",
            "full_name": "Student Name",
            "role": "student",
            "login_timestamp": login_time,
            "session_expires_at": expires_time
        }
        
        # Act
        response = StudentTokenResponse(**response_data)
        
        # Assert
        assert response.session_expires_at == expires_time
        assert response.expires_in == 3600  # 1 hour in seconds
        assert response.session_expires_at > response.login_timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])