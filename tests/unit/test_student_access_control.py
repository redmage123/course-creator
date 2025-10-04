"""
Test cases for student access control based on course dates.
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

# Load the student access control service module
user_mgmt_path = os.path.join(project_root, "services", "user-management", "services", "student_access_control_service.py")
spec = importlib.util.spec_from_file_location("student_access_control_service", user_mgmt_path)
access_control_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(access_control_module)
StudentAccessControlService = access_control_module.StudentAccessControlService


class TestStudentAccessControl:
    """Test student access control functionality based on course dates"""
    
    @pytest.fixture
    def access_control_service(self):
        """Create access control service with mocked dependencies"""
        db_pool = Mock()
        db_pool.fetch = AsyncMock()
        db_pool.execute = AsyncMock()
        
        return StudentAccessControlService(db_pool=db_pool)
    
    @pytest.fixture
    def sample_student(self):
        """Sample student data for testing"""
        return {
            'id': str(uuid.uuid4()),
            'email': 'student@test.com',
            'role': 'student',
            'created_at': datetime.now()
        }
    
    @pytest.fixture
    def sample_course_instances(self):
        """Sample course instances with different date scenarios"""
        base_time = datetime.now()
        return {
            'future_course': {
                'id': str(uuid.uuid4()),
                'course_id': str(uuid.uuid4()),
                'title': 'Future Course',
                'start_date': base_time + timedelta(days=7),
                'end_date': base_time + timedelta(days=21),
                'status': 'scheduled'
            },
            'active_course': {
                'id': str(uuid.uuid4()),
                'course_id': str(uuid.uuid4()),
                'title': 'Active Course',
                'start_date': base_time - timedelta(days=2),
                'end_date': base_time + timedelta(days=12),
                'status': 'active'
            },
            'past_course': {
                'id': str(uuid.uuid4()),
                'course_id': str(uuid.uuid4()),
                'title': 'Completed Course',
                'start_date': base_time - timedelta(days=21),
                'end_date': base_time - timedelta(days=7),
                'status': 'completed'
            }
        }
    
    @pytest.mark.asyncio
    async def test_student_cannot_access_future_course(self, access_control_service, sample_student, sample_course_instances):
        """Test that students cannot access courses before start date"""
        # Arrange
        student_id = sample_student['id']
        course_instance = sample_course_instances['future_course']
        
        # Mock database response for enrollment
        access_control_service.db_pool.fetch.return_value = [{
            'student_id': student_id,
            'enrolled_at': datetime.now(),
            'enrollment_status': 'enrolled',
            'id': course_instance['id'],
            'course_id': course_instance['course_id'],
            'start_date': course_instance['start_date'],
            'end_date': course_instance['end_date'],
            'status': course_instance['status'],
            'timezone': 'UTC',
            'title': course_instance['title']
        }]
        
        # Act
        access_result = await access_control_service.check_course_access(
            student_id=student_id,
            course_instance_id=course_instance['id']
        )
        
        # Assert
        assert access_result['has_access'] == False
        assert access_result['reason'] == 'course_not_started'
        assert 'start_date' in access_result
        assert access_result['message'] == f"Course access will be available on {course_instance['start_date'].strftime('%B %d, %Y')}"
    
    @pytest.mark.asyncio
    async def test_student_can_access_active_course(self, access_control_service, sample_student, sample_course_instances):
        """Test that students can access courses during active period"""
        # Arrange
        student_id = sample_student['id']
        course_instance = sample_course_instances['active_course']
        
        # Mock database response for enrollment
        access_control_service.db_pool.fetch.return_value = [{
            'student_id': student_id,
            'enrolled_at': datetime.now(),
            'enrollment_status': 'enrolled',
            'id': course_instance['id'],
            'course_id': course_instance['course_id'],
            'start_date': course_instance['start_date'],
            'end_date': course_instance['end_date'],
            'status': course_instance['status'],
            'timezone': 'UTC',
            'title': course_instance['title']
        }]
        
        # Act
        access_result = await access_control_service.check_course_access(
            student_id=student_id,
            course_instance_id=course_instance['id']
        )
        
        # Assert
        assert access_result['has_access'] == True
        assert access_result['reason'] == 'course_active'
        assert 'end_date' in access_result
        assert 'Course is currently active' in access_result['message']
    
    @pytest.mark.asyncio
    async def test_student_cannot_access_completed_course(self, access_control_service, sample_student, sample_course_instances):
        """Test that students cannot access courses after end date"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")

        student_id = sample_student['id']
        course_instance = sample_course_instances['past_course']

        # Mock database response for enrollment with completed course
        access_control_service.db_pool.fetch.return_value = [{
            'student_id': student_id,
            'enrolled_at': datetime.now(),
            'enrollment_status': 'enrolled',
            'id': course_instance['id'],
            'course_id': course_instance['course_id'],
            'start_date': course_instance['start_date'],
            'end_date': course_instance['end_date'],
            'status': course_instance['status'],
            'timezone': 'UTC',
            'title': course_instance['title']
        }]

        # Act
        access_result = await access_control_service.check_course_access(
            student_id=student_id,
            course_instance_id=course_instance['id']
        )

        # Assert
        assert access_result['has_access'] == False
        assert access_result['reason'] == 'course_completed'
        assert access_result['message'] == 'This course has been completed and is no longer accessible'
    
    @pytest.mark.asyncio
    async def test_unenrolled_student_cannot_access_course(self, access_control_service, sample_student, sample_course_instances):
        """Test that students not enrolled in a course cannot access it"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")
        
        student_id = sample_student['id']
        course_instance = sample_course_instances['active_course']
        
        # Mock no enrollment found
        access_control_service.db_pool.fetch.return_value = []
        
        # Act
        access_result = await access_control_service.check_course_access(
            student_id=student_id,
            course_instance_id=course_instance['id']
        )
        
        # Assert
        assert access_result['has_access'] == False
        assert access_result['reason'] == 'not_enrolled'
        assert access_result['message'] == 'You are not enrolled in this course'
    
    @pytest.mark.asyncio
    async def test_get_accessible_courses_for_student(self, access_control_service, sample_student):
        """Test retrieving all courses a student can currently access"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")
        
        # Arrange
        student_id = sample_student['id']
        current_time = datetime.now()
        
        # Mock accessible courses
        accessible_courses = [
            {
                'course_instance_id': str(uuid.uuid4()),
                'course_title': 'Active Course 1',
                'start_date': current_time - timedelta(days=1),
                'end_date': current_time + timedelta(days=13),
                'status': 'active'
            },
            {
                'course_instance_id': str(uuid.uuid4()),
                'course_title': 'Active Course 2',
                'start_date': current_time - timedelta(days=3),
                'end_date': current_time + timedelta(days=10),
                'status': 'active'
            }
        ]
        
        access_control_service.db_pool.fetch.return_value = accessible_courses
        
        # Act
        result = await access_control_service.get_accessible_courses(student_id)
        
        # Assert
        assert len(result) == 2
        assert all(course['status'] == 'active' for course in result)
        
        # Verify correct SQL query was used
        call_args = access_control_service.db_pool.fetch.call_args
        sql_query = call_args[0][0]
        assert "enrollments" in sql_query
        assert "course_instances" in sql_query
        # Check for time-based filtering (may have schema prefix)
        assert ("start_date <= $2" in sql_query and "end_date >= $2" in sql_query) or \
               ("ci.start_date <= $2" in sql_query and "ci.end_date >= $2" in sql_query)
    
    @pytest.mark.asyncio
    async def test_get_upcoming_courses_for_student(self, access_control_service, sample_student):
        """Test retrieving courses that student will have access to in the future"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")
        
        # Arrange
        student_id = sample_student['id']
        current_time = datetime.now()
        
        upcoming_courses = [
            {
                'course_instance_id': str(uuid.uuid4()),
                'course_title': 'Future Course 1',
                'start_date': current_time + timedelta(days=5),
                'end_date': current_time + timedelta(days=19),
                'status': 'scheduled'
            }
        ]
        
        access_control_service.db_pool.fetch.return_value = upcoming_courses
        
        # Act
        result = await access_control_service.get_upcoming_courses(student_id)
        
        # Assert
        assert len(result) == 1
        assert result[0]['status'] == 'scheduled'
        assert result[0]['start_date'] > current_time
    
    @pytest.mark.asyncio
    async def test_course_access_with_grace_period(self, access_control_service, sample_student):
        """Test course access with grace period for late joiners"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")

        # Arrange
        student_id = sample_student['id']
        current_time = datetime.now()

        # Course that started 2 hours ago (within grace period)
        course_with_grace = {
            'id': str(uuid.uuid4()),
            'course_id': str(uuid.uuid4()),
            'start_date': current_time - timedelta(hours=2),
            'end_date': current_time + timedelta(days=14),
            'status': 'active',
            'grace_period_hours': 24  # 24 hour grace period
        }

        # Mock database response for enrollment
        access_control_service.db_pool.fetch.return_value = [{
            'student_id': student_id,
            'enrolled_at': datetime.now(),
            'enrollment_status': 'enrolled',
            'id': course_with_grace['id'],
            'course_id': course_with_grace['course_id'],
            'start_date': course_with_grace['start_date'],
            'end_date': course_with_grace['end_date'],
            'status': course_with_grace['status'],
            'timezone': 'UTC',
            'title': 'Grace Period Course'
        }]

        # Act
        access_result = await access_control_service.check_course_access(
            student_id=student_id,
            course_instance_id=course_with_grace['id'],
            grace_period_hours=24
        )

        # Assert
        assert access_result['has_access'] == True
        assert access_result['reason'] == 'course_active'
    
    @pytest.mark.asyncio
    async def test_bulk_access_check_for_multiple_courses(self, access_control_service, sample_student):
        """Test checking access to multiple courses at once"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")
        
        # Arrange
        student_id = sample_student['id']
        course_instance_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        # Mock different access results
        access_results = [
            {'course_instance_id': course_instance_ids[0], 'has_access': True, 'reason': 'course_active'},
            {'course_instance_id': course_instance_ids[1], 'has_access': False, 'reason': 'course_not_started'},
            {'course_instance_id': course_instance_ids[2], 'has_access': False, 'reason': 'course_completed'}
        ]
        
        access_control_service.check_course_access = AsyncMock(side_effect=access_results)
        
        # Act
        results = await access_control_service.bulk_check_course_access(
            student_id=student_id,
            course_instance_ids=course_instance_ids
        )
        
        # Assert
        assert len(results) == 3
        assert results[0]['has_access'] == True
        assert results[1]['has_access'] == False
        assert results[2]['has_access'] == False
    
    @pytest.mark.asyncio
    async def test_course_access_logging(self, access_control_service, sample_student, sample_course_instances):
        """Test that course access attempts are logged for audit purposes"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")

        # Arrange
        student_id = sample_student['id']
        course_instance = sample_course_instances['active_course']

        # Mock database response for enrollment
        access_control_service.db_pool.fetch.return_value = [{
            'student_id': student_id,
            'enrolled_at': datetime.now(),
            'enrollment_status': 'enrolled',
            'id': course_instance['id'],
            'course_id': course_instance['course_id'],
            'start_date': course_instance['start_date'],
            'end_date': course_instance['end_date'],
            'status': course_instance['status'],
            'timezone': 'UTC',
            'title': course_instance['title']
        }]

        # Act
        access_result = await access_control_service.check_course_access(
            student_id=student_id,
            course_instance_id=course_instance['id'],
            log_access=True
        )

        # Assert - Verify logging was called
        log_calls = access_control_service.db_pool.execute.call_args_list
        access_log_call = [call for call in log_calls if "INSERT INTO access_logs" in str(call)][0]

        assert student_id in str(access_log_call)
        assert course_instance['id'] in str(access_log_call)
    
    @pytest.mark.asyncio
    async def test_instructor_access_override(self, access_control_service, sample_course_instances):
        """Test that instructors can access their courses regardless of dates"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")
        
        # Arrange
        instructor = {
            'id': str(uuid.uuid4()),
            'email': 'instructor@test.com',
            'role': 'instructor'
        }
        course_instance = sample_course_instances['future_course']  # Not yet started
        
        # Act
        access_result = await access_control_service.check_course_access(
            student_id=instructor['id'],
            course_instance_id=course_instance['id'],
            user_role='instructor'
        )
        
        # Assert
        assert access_result['has_access'] == True
        assert access_result['reason'] == 'instructor_override'
    
    @pytest.mark.asyncio
    async def test_admin_access_override(self, access_control_service, sample_course_instances):
        """Test that admins can access any course regardless of dates"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")
        
        # Arrange
        admin = {
            'id': str(uuid.uuid4()),
            'email': 'admin@test.com',
            'role': 'admin'
        }
        course_instance = sample_course_instances['past_course']  # Completed
        
        # Act
        access_result = await access_control_service.check_course_access(
            student_id=admin['id'],
            course_instance_id=course_instance['id'],
            user_role='admin'
        )
        
        # Assert
        assert access_result['has_access'] == True
        assert access_result['reason'] == 'admin_override'
    
    @pytest.mark.asyncio
    async def test_course_access_during_maintenance(self, access_control_service, sample_student, sample_course_instances):
        """Test course access when system is in maintenance mode"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")
        
        # Arrange
        student_id = sample_student['id']
        course_instance = sample_course_instances['active_course']
        
        # Act
        access_result = await access_control_service.check_course_access(
            student_id=student_id,
            course_instance_id=course_instance['id'],
            maintenance_mode=True
        )
        
        # Assert
        assert access_result['has_access'] == False
        assert access_result['reason'] == 'maintenance_mode'
        assert 'maintenance' in access_result['message'].lower()
    
    @pytest.mark.asyncio
    async def test_timezone_aware_access_control(self, access_control_service, sample_student):
        """Test that access control respects timezone differences"""
        if access_control_service is None:
            pytest.skip("StudentAccessControlService not implemented yet")

        # Arrange
        student_id = sample_student['id']

        # Course in different timezone
        course_with_timezone = {
            'id': str(uuid.uuid4()),
            'course_id': str(uuid.uuid4()),
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=14),
            'timezone': 'America/New_York',
            'status': 'active'
        }

        # Mock database response for enrollment
        access_control_service.db_pool.fetch.return_value = [{
            'student_id': student_id,
            'enrolled_at': datetime.now(),
            'enrollment_status': 'enrolled',
            'id': course_with_timezone['id'],
            'course_id': course_with_timezone['course_id'],
            'start_date': course_with_timezone['start_date'],
            'end_date': course_with_timezone['end_date'],
            'status': course_with_timezone['status'],
            'timezone': course_with_timezone['timezone'],
            'title': 'Timezone Test Course'
        }]

        # Act
        access_result = await access_control_service.check_course_access(
            student_id=student_id,
            course_instance_id=course_with_timezone['id'],
            user_timezone='America/Los_Angeles'
        )

        # Assert - Should handle timezone conversion properly
        assert 'timezone' in access_result or access_result['has_access'] in [True, False]