"""
Test cases for student enrollment with auto-generated passwords and email notifications.
Following TDD approach - these tests should fail initially.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import uuid
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import using importlib to handle hyphenated directory names
import importlib.util
import os

# Load the student enrollment service module
user_mgmt_path = os.path.join(project_root, "services", "user-management", "services", "student_enrollment_service.py")
spec = importlib.util.spec_from_file_location("student_enrollment_service", user_mgmt_path)
student_enrollment_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(student_enrollment_module)
StudentEnrollmentService = student_enrollment_module.StudentEnrollmentService

# Load the models module
models_path = os.path.join(project_root, "services", "user-management", "models", "course_instance.py")
spec = importlib.util.spec_from_file_location("course_instance", models_path)
models_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models_module)
CourseInstance = models_module.CourseInstance
Enrollment = models_module.Enrollment

# Mock User class for now
class User:
    pass


class TestStudentEnrollment:
    """Test student enrollment functionality"""
    
    @pytest.fixture
    def enrollment_service(self):
        """Create enrollment service with mocked dependencies"""
        db_pool = Mock()
        db_pool.fetch = AsyncMock()
        db_pool.execute = AsyncMock()
        
        email_service = Mock()
        email_service.send_enrollment_notification = AsyncMock()
        
        return StudentEnrollmentService(
            db_pool=db_pool,
            email_service=email_service,
            password_generator=Mock()
        )
    
    @pytest.fixture
    def sample_course_instance(self):
        """Sample course instance for testing"""
        return {
            'id': str(uuid.uuid4()),
            'course_id': str(uuid.uuid4()),
            'title': 'Python Programming Basics',
            'instructor_name': 'Dr. Jane Smith',
            'start_date': datetime.now() + timedelta(days=7),
            'end_date': datetime.now() + timedelta(days=14),
            'status': 'scheduled'
        }
    
    @pytest.mark.asyncio
    async def test_enroll_student_generates_random_password(self, enrollment_service, sample_course_instance):
        """Test that enrolling a student generates a random password"""
        # Arrange
        student_email = "student@example.com"
        expected_password = "RandomPass123!"
        enrollment_service.password_generator.generate_password.return_value = expected_password
        enrollment_service.db_pool.fetch.return_value = []  # Student doesn't exist
        
        # Act
        result = await enrollment_service.enroll_student(student_email, sample_course_instance)
        
        # Assert
        enrollment_service.password_generator.generate_password.assert_called_once()
        assert result['password'] == expected_password
        assert result['email'] == student_email
    
    @pytest.mark.asyncio
    async def test_enroll_student_creates_user_in_database(self, enrollment_service, sample_course_instance):
        """Test that enrolling a student creates user record in database"""
        # Arrange
        student_email = "newstudent@example.com"
        generated_password = "SecurePass456!"
        enrollment_service.password_generator.generate_password.return_value = generated_password
        enrollment_service.db_pool.fetch.return_value = []  # Student doesn't exist
        
        # Act
        await enrollment_service.enroll_student(student_email, sample_course_instance)
        
        # Assert
        # Verify user creation SQL was called
        calls = enrollment_service.db_pool.execute.call_args_list
        user_creation_call = calls[0]
        # Check for INSERT INTO users (may have schema prefix like course_creator.users)
        assert ("INSERT INTO users" in user_creation_call[0][0] or
                "INSERT INTO course_creator.users" in user_creation_call[0][0])
        assert student_email in str(user_creation_call)
        assert "student" in str(user_creation_call)  # Role should be 'student'
    
    @pytest.mark.asyncio
    async def test_enroll_student_sends_notification_email(self, enrollment_service, sample_course_instance):
        """Test that enrolling a student sends notification email with course details"""
        # Arrange
        student_email = "student@university.edu"
        generated_password = "TempPass789!"
        enrollment_service.password_generator.generate_password.return_value = generated_password
        enrollment_service.db_pool.fetch.return_value = []
        
        # Act
        await enrollment_service.enroll_student(student_email, sample_course_instance)
        
        # Assert
        enrollment_service.email_service.send_enrollment_notification.assert_called_once()
        call_args = enrollment_service.email_service.send_enrollment_notification.call_args
        
        # Verify email contains required information
        email_data = call_args[1]  # kwargs
        assert email_data['student_email'] == student_email
        assert email_data['course_title'] == sample_course_instance['title']
        assert email_data['instructor_name'] == sample_course_instance['instructor_name']
        assert email_data['start_date'] == sample_course_instance['start_date']
        assert email_data['end_date'] == sample_course_instance['end_date']
        assert email_data['login_email'] == student_email
        assert email_data['password'] == generated_password
    
    @pytest.mark.asyncio
    async def test_enroll_existing_student_uses_existing_account(self, enrollment_service, sample_course_instance):
        """Test that enrolling an existing student doesn't create duplicate account"""
        # Arrange
        student_email = "existing@example.com"
        existing_user = [{
            'id': str(uuid.uuid4()),
            'email': student_email,
            'role': 'student'
        }]
        enrollment_service.db_pool.fetch.return_value = existing_user
        
        # Act
        result = await enrollment_service.enroll_student(student_email, sample_course_instance)
        
        # Assert
        # Should not generate new password for existing user
        enrollment_service.password_generator.generate_password.assert_not_called()
        
        # Should still send enrollment notification
        enrollment_service.email_service.send_enrollment_notification.assert_called_once()
        
        # Should not create new user record
        execute_calls = enrollment_service.db_pool.execute.call_args_list
        user_creation_calls = [call for call in execute_calls if "INSERT INTO users" in str(call)]
        assert len(user_creation_calls) == 0
    
    @pytest.mark.asyncio
    async def test_enroll_student_creates_enrollment_record(self, enrollment_service, sample_course_instance):
        """Test that enrollment creates proper enrollment record linking student to course instance"""
        # Arrange
        student_email = "student@test.com"
        enrollment_service.password_generator.generate_password.return_value = "TestPass123!"
        enrollment_service.db_pool.fetch.return_value = []
        enrollment_service.db_pool.execute = AsyncMock()
        
        # Act
        await enrollment_service.enroll_student(student_email, sample_course_instance)
        
        # Assert
        calls = enrollment_service.db_pool.execute.call_args_list
        enrollment_creation_call = [call for call in calls if "INSERT INTO enrollments" in str(call)][0]
        
        assert sample_course_instance['id'] in str(enrollment_creation_call)
        # Check that enrollment record was created (student_id will be UUID, not email)
        assert "INSERT INTO enrollments" in str(enrollment_creation_call)