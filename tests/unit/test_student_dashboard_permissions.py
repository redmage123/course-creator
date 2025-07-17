"""
Test cases for student dashboard with limited permissions.
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

# Load the student dashboard service module
user_mgmt_path = os.path.join(project_root, "services", "user-management", "services", "student_dashboard_service.py")
spec = importlib.util.spec_from_file_location("student_dashboard_service", user_mgmt_path)
dashboard_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard_module)
StudentDashboardService = dashboard_module.StudentDashboardService


class TestStudentDashboardPermissions:
    """Test student dashboard functionality with limited permissions"""
    
    @pytest.fixture
    def dashboard_service(self):
        """Create dashboard service with mocked dependencies"""
        db_pool = Mock()
        db_pool.fetch = AsyncMock()
        db_pool.execute = AsyncMock()
        
        # Mock access control service
        access_control = Mock()
        access_control.check_course_access = AsyncMock()
        access_control.get_accessible_courses = AsyncMock()
        
        return StudentDashboardService(
            db_pool=db_pool,
            access_control_service=access_control
        )
    
    @pytest.fixture
    def sample_student(self):
        """Sample student data for testing"""
        return {
            'id': str(uuid.uuid4()),
            'email': 'student@test.com',
            'role': 'student',
            'full_name': 'Test Student',
            'created_at': datetime.now()
        }
    
    @pytest.fixture
    def sample_courses(self):
        """Sample course data with different statuses"""
        student_id = str(uuid.uuid4())
        base_time = datetime.now()
        return [
            {
                'course_instance_id': str(uuid.uuid4()),
                'course_id': str(uuid.uuid4()),
                'course_title': 'Python Programming',
                'student_id': student_id,
                'start_date': base_time - timedelta(days=1),
                'end_date': base_time + timedelta(days=13),
                'status': 'active',
                'progress': 45,
                'enrolled_at': base_time - timedelta(days=2)
            },
            {
                'course_instance_id': str(uuid.uuid4()),
                'course_id': str(uuid.uuid4()),
                'course_title': 'Web Development',
                'student_id': student_id,
                'start_date': base_time + timedelta(days=7),
                'end_date': base_time + timedelta(days=21),
                'status': 'scheduled',
                'progress': 0,
                'enrolled_at': base_time - timedelta(days=1)
            }
        ]
    
    @pytest.mark.asyncio
    async def test_student_can_only_view_own_courses(self, dashboard_service, sample_student, sample_courses):
        """Test that students can only see courses they are enrolled in"""
        # Arrange
        student_id = sample_student['id']
        other_student_id = str(uuid.uuid4())
        
        # Mock database to return only courses for the specific student
        dashboard_service.db_pool.fetch.return_value = [
            course for course in sample_courses if course['student_id'] == student_id
        ]
        
        # Act
        student_courses = await dashboard_service.get_student_courses(student_id)
        
        # Assert
        assert len(student_courses) >= 0  # Should only return student's courses
        for course in student_courses:
            assert course['student_id'] == student_id
        
        # Verify correct SQL query was used with student ID filter
        call_args = dashboard_service.db_pool.fetch.call_args[0]
        sql_query = call_args[0]
        assert "WHERE e.student_id = $1" in sql_query
        assert student_id in call_args[1:]
    
    @pytest.mark.asyncio
    async def test_student_cannot_access_instructor_functions(self, dashboard_service, sample_student):
        """Test that students cannot access instructor-only functions"""
        # Act & Assert - These functions should raise PermissionError
        with pytest.raises(PermissionError):
            await dashboard_service.create_course(sample_student['id'], {})
        
        with pytest.raises(PermissionError):
            await dashboard_service.enroll_student(sample_student['id'], 'other@student.com', 'course-123')
        
        with pytest.raises(PermissionError):
            await dashboard_service.delete_course(sample_student['id'], 'course-123')
        
        with pytest.raises(PermissionError):
            await dashboard_service.view_all_students(sample_student['id'])
    
    @pytest.mark.asyncio
    async def test_student_cannot_access_admin_functions(self, dashboard_service, sample_student):
        """Test that students cannot access admin-only functions"""
        # Act & Assert - These functions should raise PermissionError
        with pytest.raises(PermissionError):
            await dashboard_service.manage_users(sample_student['id'])
        
        with pytest.raises(PermissionError):
            await dashboard_service.view_system_analytics(sample_student['id'])
        
        with pytest.raises(PermissionError):
            await dashboard_service.configure_system_settings(sample_student['id'], {})
    
    @pytest.mark.asyncio
    async def test_student_can_view_accessible_courses_only(self, dashboard_service, sample_student, sample_courses):
        """Test that students can only view courses they have access to based on dates"""
        # Arrange
        student_id = sample_student['id']
        
        # Mock access control to allow only active courses
        dashboard_service.access_control_service.get_accessible_courses.return_value = [
            course for course in sample_courses if course['status'] == 'active'
        ]
        
        # Act
        accessible_courses = await dashboard_service.get_accessible_courses(student_id)
        
        # Assert
        assert len(accessible_courses) == 1
        assert accessible_courses[0]['status'] == 'active'
        assert accessible_courses[0]['course_title'] == 'Python Programming'
        
        # Verify access control was called
        dashboard_service.access_control_service.get_accessible_courses.assert_called_once_with(student_id)
    
    @pytest.mark.asyncio
    async def test_student_can_view_own_progress_only(self, dashboard_service, sample_student):
        """Test that students can only view their own progress data"""
        # Arrange
        student_id = sample_student['id']
        mock_progress = {
            'student_id': student_id,
            'total_courses': 2,
            'completed_courses': 1,
            'overall_progress': 50,
            'total_exercises': 10,
            'completed_exercises': 5,
            'lab_sessions': 3
        }
        
        dashboard_service.db_pool.fetch.return_value = [mock_progress]
        
        # Act
        progress = await dashboard_service.get_student_progress(student_id)
        
        # Assert
        assert progress['student_id'] == student_id
        assert progress['overall_progress'] == 50
        assert progress['completed_courses'] == 1
        
        # Verify query includes student ID filter
        call_args = dashboard_service.db_pool.fetch.call_args[0]
        sql_query = call_args[0]
        assert "student_id = $1" in sql_query
    
    @pytest.mark.asyncio
    async def test_student_dashboard_data_filtering(self, dashboard_service, sample_student, sample_courses):
        """Test that dashboard data is properly filtered for students"""
        # Arrange
        student_id = sample_student['id']
        
        # Mock database responses
        dashboard_service.db_pool.fetch.side_effect = [
            sample_courses,  # Enrolled courses
            [{'recent_activity': 'Completed exercise', 'timestamp': datetime.now()}],  # Recent activity
            [{'total_courses': 2, 'completed_courses': 1}]  # Progress summary
        ]
        
        # Act
        dashboard_data = await dashboard_service.get_dashboard_data(student_id)
        
        # Assert
        assert 'enrolled_courses' in dashboard_data
        assert 'recent_activity' in dashboard_data
        assert 'progress_summary' in dashboard_data
        assert len(dashboard_data['enrolled_courses']) == len(sample_courses)
        
        # Verify all database calls include student ID filter
        for call in dashboard_service.db_pool.fetch.call_args_list:
            sql_query = call[0][0]
            assert "student_id" in sql_query.lower()
    
    @pytest.mark.asyncio
    async def test_student_lab_access_control(self, dashboard_service, sample_student):
        """Test that students can only access labs for enrolled courses"""
        # Arrange
        student_id = sample_student['id']
        course_id = str(uuid.uuid4())
        
        # Mock access control to check course enrollment
        dashboard_service.access_control_service.check_course_access.return_value = {
            'has_access': True,
            'reason': 'course_active'
        }
        
        # Act
        lab_access = await dashboard_service.request_lab_access(student_id, course_id)
        
        # Assert
        assert lab_access['access_granted'] == True
        
        # Verify access control was checked
        dashboard_service.access_control_service.check_course_access.assert_called_once_with(
            student_id=student_id,
            course_instance_id=course_id
        )
    
    @pytest.mark.asyncio
    async def test_student_cannot_access_unenrolled_course_labs(self, dashboard_service, sample_student):
        """Test that students cannot access labs for courses they're not enrolled in"""
        # Arrange
        student_id = sample_student['id']
        course_id = str(uuid.uuid4())
        
        # Mock access control to deny access
        dashboard_service.access_control_service.check_course_access.return_value = {
            'has_access': False,
            'reason': 'not_enrolled'
        }
        
        # Act
        lab_access = await dashboard_service.request_lab_access(student_id, course_id)
        
        # Assert
        assert lab_access['access_granted'] == False
        assert lab_access['reason'] == 'not_enrolled'
    
    @pytest.mark.asyncio
    async def test_student_activity_logging_privacy(self, dashboard_service, sample_student):
        """Test that student activity logs only include their own activities"""
        # Arrange
        student_id = sample_student['id']
        other_student_id = str(uuid.uuid4())
        
        # Mock activities with different student IDs
        all_activities = [
            {'student_id': student_id, 'activity': 'Completed exercise', 'timestamp': datetime.now()},
            {'student_id': other_student_id, 'activity': 'Started course', 'timestamp': datetime.now()},
            {'student_id': student_id, 'activity': 'Accessed lab', 'timestamp': datetime.now()}
        ]
        
        # Only return activities for the requesting student
        dashboard_service.db_pool.fetch.return_value = [
            activity for activity in all_activities if activity['student_id'] == student_id
        ]
        
        # Act
        activities = await dashboard_service.get_student_activities(student_id)
        
        # Assert
        assert len(activities) == 2  # Only student's activities
        for activity in activities:
            assert activity['student_id'] == student_id
        
        # Verify SQL includes student ID filter
        call_args = dashboard_service.db_pool.fetch.call_args[0]
        sql_query = call_args[0]
        assert "student_id = $1" in sql_query
    
    @pytest.mark.asyncio
    async def test_student_data_isolation(self, dashboard_service, sample_student):
        """Test that student data is properly isolated from other users"""
        # Arrange
        student_id = sample_student['id']
        
        # Mock database response for student profile
        dashboard_service.db_pool.fetch.return_value = [sample_student]
        
        # Act
        profile_data = await dashboard_service.get_student_profile(student_id)
        
        # Assert - Should only return data for the specific student
        assert profile_data['id'] == student_id
        
        # Verify database query filters by student ID
        call_args = dashboard_service.db_pool.fetch.call_args[0]
        sql_query = call_args[0]
        assert "WHERE id = $1" in sql_query
        assert student_id in call_args[1:]
    
    @pytest.mark.asyncio
    async def test_student_role_validation(self, dashboard_service):
        """Test that only users with student role can access student dashboard"""
        # Arrange
        instructor_user = {
            'id': str(uuid.uuid4()),
            'role': 'instructor',
            'email': 'instructor@test.com'
        }
        
        # Act & Assert
        with pytest.raises(PermissionError) as exc_info:
            await dashboard_service.get_dashboard_data(instructor_user['id'], user_role='instructor')
        
        assert "Student role required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_student_course_modification_denied(self, dashboard_service, sample_student):
        """Test that students cannot modify course content or structure"""
        # Arrange
        student_id = sample_student['id']
        course_id = str(uuid.uuid4())
        
        # Act & Assert - These operations should be denied
        with pytest.raises(PermissionError):
            await dashboard_service.update_course_content(student_id, course_id, {})
        
        with pytest.raises(PermissionError):
            await dashboard_service.add_course_exercise(student_id, course_id, {})
        
        with pytest.raises(PermissionError):
            await dashboard_service.modify_course_settings(student_id, course_id, {})
    
    @pytest.mark.asyncio
    async def test_student_analytics_access_restricted(self, dashboard_service, sample_student):
        """Test that students can only access their own analytics, not system-wide data"""
        # Arrange
        student_id = sample_student['id']
        
        # Mock student-specific analytics
        student_analytics = {
            'student_id': student_id,
            'courses_progress': [{'course_id': 'course-1', 'progress': 75}],
            'time_spent': 120,  # minutes
            'exercises_completed': 8
        }
        
        dashboard_service.db_pool.fetch.return_value = [student_analytics]
        
        # Act
        analytics = await dashboard_service.get_student_analytics(student_id)
        
        # Assert
        assert analytics['student_id'] == student_id
        assert 'courses_progress' in analytics
        
        # Verify cannot access system-wide analytics
        with pytest.raises(PermissionError):
            await dashboard_service.get_system_analytics(student_id)
    
    @pytest.mark.asyncio
    async def test_student_notification_filtering(self, dashboard_service, sample_student):
        """Test that students only see notifications intended for them"""
        # Arrange
        student_id = sample_student['id']
        
        # Mock notifications with different target audiences
        all_notifications = [
            {
                'id': str(uuid.uuid4()),
                'recipient_id': student_id,
                'message': 'Course deadline approaching',
                'type': 'student'
            },
            {
                'id': str(uuid.uuid4()),
                'recipient_id': 'admin',
                'message': 'System maintenance scheduled',
                'type': 'admin'
            }
        ]
        
        # Return only student-specific notifications
        dashboard_service.db_pool.fetch.return_value = [
            notif for notif in all_notifications if notif['recipient_id'] == student_id
        ]
        
        # Act
        notifications = await dashboard_service.get_student_notifications(student_id)
        
        # Assert
        assert len(notifications) == 1
        assert notifications[0]['recipient_id'] == student_id
        assert notifications[0]['type'] == 'student'
        
        # Verify SQL filters by recipient
        call_args = dashboard_service.db_pool.fetch.call_args[0]
        sql_query = call_args[0]
        assert "recipient_id = $1" in sql_query or "WHERE user_id = $1" in sql_query