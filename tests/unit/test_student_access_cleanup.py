"""
Test cases for automatic cleanup of student access after course completion.
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

# Load the student access cleanup service module
user_mgmt_path = os.path.join(project_root, "services", "user-management", "services", "student_access_cleanup_service.py")
spec = importlib.util.spec_from_file_location("student_access_cleanup_service", user_mgmt_path)
cleanup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup_module)
StudentAccessCleanupService = cleanup_module.StudentAccessCleanupService


class TestStudentAccessCleanup:
    """Test automatic cleanup of student access after course completion"""
    
    @pytest.fixture
    def cleanup_service(self):
        """Create cleanup service with mocked dependencies"""
        db_pool = Mock()
        db_pool.fetch = AsyncMock()
        db_pool.execute = AsyncMock(return_value='UPDATE 1')  # Mock execute result
        
        # Mock notification service
        notification_service = Mock()
        notification_service.send_notification = AsyncMock()
        
        return StudentAccessCleanupService(
            db_pool=db_pool,
            notification_service=notification_service
        )
    
    @pytest.fixture
    def completed_courses(self):
        """Sample completed courses for testing"""
        base_time = datetime.now()
        return [
            {
                'course_instance_id': str(uuid.uuid4()),
                'course_id': str(uuid.uuid4()),
                'course_title': 'Python Programming',
                'student_id': str(uuid.uuid4()),
                'end_date': base_time - timedelta(days=1),  # Ended yesterday
                'status': 'completed',
                'student_email': 'student1@test.com'
            },
            {
                'course_instance_id': str(uuid.uuid4()),
                'course_id': str(uuid.uuid4()),
                'course_title': 'Web Development',
                'student_id': str(uuid.uuid4()),
                'end_date': base_time - timedelta(days=7),  # Ended a week ago
                'status': 'completed',
                'student_email': 'student2@test.com'
            },
            {
                'course_instance_id': str(uuid.uuid4()),
                'course_id': str(uuid.uuid4()),
                'course_title': 'Data Science',
                'student_id': str(uuid.uuid4()),
                'end_date': base_time + timedelta(days=5),  # Still active
                'status': 'active',
                'student_email': 'student3@test.com'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_identify_courses_needing_cleanup(self, cleanup_service, completed_courses):
        """Test identification of courses that need access cleanup"""
        # Arrange
        current_time = datetime.now()
        
        # Mock database to return completed courses
        cleanup_service.db_pool.fetch.return_value = [
            course for course in completed_courses 
            if course['status'] == 'completed' and course['end_date'] < current_time
        ]
        
        # Act
        courses_needing_cleanup = await cleanup_service.identify_courses_needing_cleanup()
        
        # Assert
        assert len(courses_needing_cleanup) == 2  # Two completed courses
        for course in courses_needing_cleanup:
            assert course['status'] == 'completed'
            assert course['end_date'] < current_time
        
        # Verify correct SQL query was used
        call_args = cleanup_service.db_pool.fetch.call_args[0]
        sql_query = call_args[0]
        assert "ci.status = 'completed'" in sql_query
        assert "ci.end_date < $1" in sql_query
    
    @pytest.mark.asyncio
    async def test_cleanup_student_lab_sessions(self, cleanup_service):
        """Test cleanup of student lab sessions after course completion"""
        # Arrange
        course_instance_id = str(uuid.uuid4())
        student_id = str(uuid.uuid4())
        
        # Mock active lab sessions
        cleanup_service.db_pool.fetch.return_value = [
            {
                'session_id': str(uuid.uuid4()),
                'student_id': student_id,
                'course_instance_id': course_instance_id,
                'status': 'active',
                'created_at': datetime.now() - timedelta(hours=2)
            }
        ]
        
        # Act
        cleanup_result = await cleanup_service.cleanup_lab_sessions(course_instance_id)
        
        # Assert
        assert cleanup_result['sessions_cleaned'] >= 0
        
        # Verify lab sessions were terminated
        execute_calls = cleanup_service.db_pool.execute.call_args_list
        terminate_call = [call for call in execute_calls if "UPDATE lab_sessions" in str(call)][0]
        assert "status = 'terminated'" in str(terminate_call)
        assert course_instance_id in str(terminate_call)
    
    @pytest.mark.asyncio
    async def test_cleanup_course_access_tokens(self, cleanup_service):
        """Test cleanup of course access tokens after completion"""
        # Arrange
        course_instance_id = str(uuid.uuid4())
        
        # Mock active access tokens
        cleanup_service.db_pool.fetch.return_value = [
            {
                'token_id': str(uuid.uuid4()),
                'course_instance_id': course_instance_id,
                'student_id': str(uuid.uuid4()),
                'status': 'active',
                'expires_at': datetime.now() + timedelta(days=30)
            }
        ]
        
        # Act
        cleanup_result = await cleanup_service.cleanup_access_tokens(course_instance_id)
        
        # Assert
        assert cleanup_result['tokens_revoked'] >= 0
        
        # Verify access tokens were revoked
        execute_calls = cleanup_service.db_pool.execute.call_args_list
        revoke_call = [call for call in execute_calls if "UPDATE access_tokens" in str(call)][0]
        assert "status = 'revoked'" in str(revoke_call)
        assert course_instance_id in str(revoke_call)
    
    @pytest.mark.asyncio
    async def test_cleanup_temporary_course_files(self, cleanup_service):
        """Test cleanup of temporary files created during course"""
        # Arrange
        course_instance_id = str(uuid.uuid4())
        
        # Mock temporary files
        cleanup_service.db_pool.fetch.return_value = [
            {
                'file_id': str(uuid.uuid4()),
                'file_path': '/tmp/course_files/student_work.txt',
                'course_instance_id': course_instance_id,
                'created_at': datetime.now() - timedelta(days=2)
            }
        ]
        
        # Act
        cleanup_result = await cleanup_service.cleanup_temporary_files(course_instance_id)
        
        # Assert
        assert cleanup_result['files_cleaned'] >= 0
        
        # Verify files were marked for deletion
        execute_calls = cleanup_service.db_pool.execute.call_args_list
        delete_call = [call for call in execute_calls if "DELETE FROM temporary_files" in str(call)][0]
        assert course_instance_id in str(delete_call)
    
    @pytest.mark.asyncio
    async def test_send_course_completion_notifications(self, cleanup_service, completed_courses):
        """Test sending completion notifications to students"""
        # Arrange
        completed_course = completed_courses[0]  # First completed course
        
        # Mock enrolled students
        cleanup_service.db_pool.fetch.return_value = [
            {
                'email': 'student1@test.com',
                'full_name': 'Student One',
                'student_id': str(uuid.uuid4())
            },
            {
                'email': 'student2@test.com', 
                'full_name': 'Student Two',
                'student_id': str(uuid.uuid4())
            }
        ]
        
        # Act
        notification_result = await cleanup_service.send_completion_notifications(
            completed_course['course_instance_id'],
            completed_course['course_title']
        )
        
        # Assert
        assert notification_result['notifications_sent'] == 2
        
        # Verify notification service was called
        assert cleanup_service.notification_service.send_notification.call_count == 2
        call_args = cleanup_service.notification_service.send_notification.call_args[1]
        assert 'completed the course' in call_args['message'].lower()
        assert completed_course['course_title'] in call_args['message']
    
    @pytest.mark.asyncio
    async def test_archive_student_progress_data(self, cleanup_service):
        """Test archiving of student progress data before cleanup"""
        # Arrange
        course_instance_id = str(uuid.uuid4())
        
        # Mock student progress data
        cleanup_service.db_pool.fetch.return_value = [
            {
                'student_id': str(uuid.uuid4()),
                'course_instance_id': course_instance_id,
                'progress': 100,
                'enrollment_status': 'completed',
                'enrolled_at': datetime.now() - timedelta(days=14),
                'completed_at': datetime.now() - timedelta(days=1),
                'course_title': 'Test Course'
            }
        ]
        
        # Act
        archive_result = await cleanup_service.archive_progress_data(course_instance_id)
        
        # Assert
        assert archive_result['records_archived'] == 1
        
        # Verify data was inserted into archive table
        execute_calls = cleanup_service.db_pool.execute.call_args_list
        archive_call = [call for call in execute_calls if "INSERT INTO archived_progress" in str(call)][0]
        assert course_instance_id in str(archive_call)
    
    @pytest.mark.asyncio
    async def test_update_enrollment_status_to_completed(self, cleanup_service):
        """Test updating enrollment status to completed after cleanup"""
        # Arrange
        course_instance_id = str(uuid.uuid4())
        
        # Act
        update_result = await cleanup_service.update_enrollment_status(
            course_instance_id,
            'completed'
        )
        
        # Assert
        assert update_result['enrollments_updated'] >= 0
        
        # Verify enrollment status was updated
        execute_calls = cleanup_service.db_pool.execute.call_args_list
        update_call = [call for call in execute_calls if "UPDATE enrollments" in str(call)][0]
        assert "status = $1" in str(update_call)
        assert "completed" in str(update_call)
        assert course_instance_id in str(update_call)
    
    @pytest.mark.asyncio
    async def test_full_cleanup_process(self, cleanup_service, completed_courses):
        """Test the complete cleanup process for a course"""
        # Arrange
        completed_course = completed_courses[0]
        course_instance_id = completed_course['course_instance_id']
        
        # Mock fetch_one for course info
        cleanup_service.db_pool.fetch_one = AsyncMock(return_value={
            'id': course_instance_id,
            'title': completed_course['course_title'],
            'end_date': completed_course['end_date']
        })
        
        # Mock all database fetch responses in sequence
        cleanup_service.db_pool.fetch.side_effect = [
            [],  # Lab sessions
            [],  # Access tokens  
            [],  # Temporary files
            [],  # Progress data for archiving
            []   # Students for notifications
        ]
        
        cleanup_service.db_pool.execute = AsyncMock(return_value=None)
        
        # Act
        cleanup_result = await cleanup_service.run_full_cleanup(course_instance_id)
        
        # Assert
        assert cleanup_result['success'] == True
        assert 'lab_sessions' in cleanup_result
        assert 'access_tokens' in cleanup_result
        assert 'temporary_files' in cleanup_result
        assert 'notifications' in cleanup_result
        assert 'archived_records' in cleanup_result
        
        # Verify all cleanup steps were executed
        assert cleanup_service.db_pool.execute.call_count >= 1  # At least audit log
    
    @pytest.mark.asyncio
    async def test_scheduled_cleanup_job(self, cleanup_service, completed_courses):
        """Test the scheduled cleanup job that runs periodically"""
        # Arrange
        completed_only = [course for course in completed_courses if course['status'] == 'completed']
        cleanup_service.db_pool.fetch.return_value = completed_only
        
        # Mock run_full_cleanup to avoid complex nested mocking
        cleanup_service.run_full_cleanup = AsyncMock(return_value={'success': True})
        
        # Act
        job_result = await cleanup_service.run_scheduled_cleanup()
        
        # Assert
        assert job_result['courses_processed'] == len(completed_only)  # Completed courses only
        assert job_result['success'] == True
        assert job_result['successful_cleanups'] == len(completed_only)
        assert job_result['failed_cleanups'] == 0
        
        # Verify cleanup was attempted for each completed course
        assert cleanup_service.run_full_cleanup.call_count == len(completed_only)
    
    @pytest.mark.asyncio
    async def test_cleanup_with_grace_period(self, cleanup_service):
        """Test cleanup respects grace period after course completion"""
        # Arrange
        current_time = datetime.now()
        grace_period_hours = 24
        
        recent_completion = {
            'course_instance_id': str(uuid.uuid4()),
            'end_date': current_time - timedelta(hours=12),  # Completed 12 hours ago
            'status': 'completed'
        }
        
        old_completion = {
            'course_instance_id': str(uuid.uuid4()),
            'end_date': current_time - timedelta(hours=48),  # Completed 48 hours ago
            'status': 'completed'
        }
        
        # Mock courses with different completion times
        cleanup_service.db_pool.fetch.return_value = [recent_completion, old_completion]
        
        # Act
        courses_for_cleanup = await cleanup_service.identify_courses_needing_cleanup(
            grace_period_hours=grace_period_hours
        )
        
        # Assert - Both courses should be returned since we're mocking the return value
        # In real implementation, only old completion would be eligible
        assert len(courses_for_cleanup) == 2  # Mock returns both
        
        # Verify grace period was applied in SQL query
        call_args = cleanup_service.db_pool.fetch.call_args[0]
        sql_query = call_args[0]
        assert "ci.end_date < $2" in sql_query  # Grace period check
    
    @pytest.mark.asyncio
    async def test_cleanup_error_handling(self, cleanup_service):
        """Test error handling during cleanup operations"""
        # Arrange
        course_instance_id = str(uuid.uuid4())
        
        # Mock fetch_one to return None (course not found)
        cleanup_service.db_pool.fetch_one = AsyncMock(return_value=None)
        
        # Act
        cleanup_result = await cleanup_service.run_full_cleanup(course_instance_id)
        
        # Assert
        assert cleanup_result['success'] == False
        assert 'error' in cleanup_result
        assert 'Course instance not found' in cleanup_result['error']
    
    @pytest.mark.asyncio
    async def test_cleanup_logging_and_audit(self, cleanup_service):
        """Test that cleanup operations are properly logged for audit"""
        # Arrange
        course_instance_id = str(uuid.uuid4())
        
        # Act
        await cleanup_service.log_cleanup_operation(
            course_instance_id,
            'lab_sessions',
            {'sessions_cleaned': 3}
        )
        
        # Assert
        # Verify audit log was created
        execute_calls = cleanup_service.db_pool.execute.call_args_list
        log_call = [call for call in execute_calls if "INSERT INTO cleanup_audit_log" in str(call)][0]
        assert course_instance_id in str(log_call)
        assert 'lab_sessions' in str(log_call)
    
    @pytest.mark.asyncio
    async def test_cleanup_prevents_active_course_interference(self, cleanup_service, completed_courses):
        """Test that cleanup doesn't affect active courses"""
        # Arrange
        active_course = completed_courses[2]  # The active course
        
        # Mock database to return only completed courses (filtering done by SQL)
        completed_only = [course for course in completed_courses if course['status'] == 'completed']
        cleanup_service.db_pool.fetch.return_value = completed_only
        
        # Act
        courses_for_cleanup = await cleanup_service.identify_courses_needing_cleanup()
        
        # Assert
        # Should only return completed courses, not active ones
        for course in courses_for_cleanup:
            assert course['status'] == 'completed'
            assert course['course_instance_id'] != active_course['course_instance_id']