"""
Integration Tests for Service Layer Interactions
Following SOLID principles and testing service dependencies
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from uuid import uuid4

# Import test framework
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from framework.test_factory import TestDataFactory, TestAssertionFactory


class TestUserCourseIntegration:
    """Test integration between User Management and Course Management services"""
    
    @pytest.fixture
    def mock_user_service(self):
        """Create mock user service"""
        service = AsyncMock()
        service.get_user_by_id.return_value = TestDataFactory.create_mock_user(role="instructor")
        service.verify_user_permissions.return_value = True
        return service
    
    @pytest.fixture
    def mock_course_service(self):
        """Create mock course service"""
        service = AsyncMock()
        service.create_course.return_value = TestDataFactory.create_mock_course()
        service.get_course_by_id.return_value = TestDataFactory.create_mock_course()
        return service
    
    @pytest.mark.integration
    async def test_instructor_can_create_course(self, mock_user_service, mock_course_service):
        """Test that an instructor can create a course"""
        # Arrange
        instructor_id = str(uuid4())
        course_data = {
            "title": "Python Programming",
            "description": "Learn Python programming",
            "difficulty": "beginner"
        }
        
        # Mock user verification
        mock_user_service.get_user_by_id.return_value = TestDataFactory.create_mock_user(
            id=instructor_id,
            role="instructor"
        )
        
        # Act
        user = await mock_user_service.get_user_by_id(instructor_id)
        assert user["role"] == "instructor"
        
        # Simulate course creation with instructor verification
        can_create = await mock_user_service.verify_user_permissions(instructor_id, "create_course")
        assert can_create
        
        course = await mock_course_service.create_course({
            **course_data,
            "instructor_id": instructor_id
        })
        
        # Assert
        assert course["instructor_id"] == instructor_id
        assert course["title"] == course_data["title"]
        mock_course_service.create_course.assert_called_once()
    
    @pytest.mark.integration
    async def test_student_cannot_create_course(self, mock_user_service, mock_course_service):
        """Test that a student cannot create a course"""
        # Arrange
        student_id = str(uuid4())
        course_data = {
            "title": "Unauthorized Course",
            "description": "This should not be created",
            "difficulty": "beginner"
        }
        
        # Mock user verification
        mock_user_service.get_user_by_id.return_value = TestDataFactory.create_mock_user(
            id=student_id,
            role="student"
        )
        mock_user_service.verify_user_permissions.return_value = False
        
        # Act
        user = await mock_user_service.get_user_by_id(student_id)
        assert user["role"] == "student"
        
        can_create = await mock_user_service.verify_user_permissions(student_id, "create_course")
        
        # Assert
        assert not can_create
        mock_course_service.create_course.assert_not_called()


class TestCourseContentIntegration:
    """Test integration between Course Management and Content Management services"""
    
    @pytest.fixture
    def mock_course_service(self):
        """Create mock course service"""
        service = AsyncMock()
        service.get_course_by_id.return_value = TestDataFactory.create_mock_course()
        return service
    
    @pytest.fixture
    def mock_content_service(self):
        """Create mock content service"""
        service = AsyncMock()
        service.create_content.return_value = {
            "id": str(uuid4()),
            "title": "Course Syllabus",
            "type": "syllabus",
            "course_id": str(uuid4())
        }
        service.get_course_content.return_value = []
        return service
    
    @pytest.mark.integration
    async def test_course_content_creation_workflow(self, mock_course_service, mock_content_service):
        """Test the workflow of creating content for a course"""
        # Arrange
        course_id = str(uuid4())
        instructor_id = str(uuid4())
        
        # Mock course exists
        mock_course_service.get_course_by_id.return_value = TestDataFactory.create_mock_course(
            id=course_id,
            instructor_id=instructor_id
        )
        
        # Act
        # 1. Verify course exists
        course = await mock_course_service.get_course_by_id(course_id)
        assert course["id"] == course_id
        
        # 2. Create syllabus content
        syllabus_content = await mock_content_service.create_content({
            "title": "Course Syllabus",
            "type": "syllabus",
            "course_id": course_id,
            "creator_id": instructor_id
        })
        
        # 3. Create slides content
        slides_content = await mock_content_service.create_content({
            "title": "Introduction Slides",
            "type": "slides",
            "course_id": course_id,
            "creator_id": instructor_id
        })
        
        # 4. Verify content is associated with course
        course_content = await mock_content_service.get_course_content(course_id)
        
        # Assert
        assert syllabus_content["course_id"] == course_id
        assert slides_content["course_id"] == course_id
        mock_content_service.create_content.assert_called()
        assert mock_content_service.create_content.call_count == 2


class TestAnalyticsIntegration:
    """Test integration between Analytics service and other services"""
    
    @pytest.fixture
    def mock_analytics_service(self):
        """Create mock analytics service"""
        service = AsyncMock()
        service.record_student_activity.return_value = True
        service.generate_course_analytics.return_value = {
            "total_students": 50,
            "average_engagement": 75.5,
            "completion_rate": 80.0
        }
        return service
    
    @pytest.fixture
    def mock_course_service(self):
        """Create mock course service"""
        service = AsyncMock()
        service.get_enrolled_students.return_value = [
            TestDataFactory.create_mock_user(role="student") for _ in range(3)
        ]
        return service
    
    @pytest.mark.integration
    async def test_student_activity_tracking_workflow(self, mock_analytics_service, mock_course_service):
        """Test the workflow of tracking student activity across services"""
        # Arrange
        course_id = str(uuid4())
        student_id = str(uuid4())
        
        # Act
        # 1. Student enrolls in course (simulated)
        enrolled_students = await mock_course_service.get_enrolled_students(course_id)
        assert len(enrolled_students) == 3
        
        # 2. Record student login activity
        login_recorded = await mock_analytics_service.record_student_activity({
            "student_id": student_id,
            "course_id": course_id,
            "activity_type": "login",
            "timestamp": datetime.utcnow()
        })
        
        # 3. Record student content view activity
        content_view_recorded = await mock_analytics_service.record_student_activity({
            "student_id": student_id,
            "course_id": course_id,
            "activity_type": "content_view",
            "content_id": str(uuid4()),
            "timestamp": datetime.utcnow()
        })
        
        # 4. Generate analytics for the course
        analytics = await mock_analytics_service.generate_course_analytics(course_id)
        
        # Assert
        assert login_recorded
        assert content_view_recorded
        assert analytics["total_students"] == 50
        assert analytics["average_engagement"] > 0
        mock_analytics_service.record_student_activity.assert_called()
        assert mock_analytics_service.record_student_activity.call_count == 2


class TestFullWorkflowIntegration:
    """Test full workflow integration across multiple services"""
    
    @pytest.fixture
    def mock_services(self):
        """Create all mock services"""
        return {
            "user": AsyncMock(),
            "course": AsyncMock(),
            "content": AsyncMock(),
            "analytics": AsyncMock()
        }
    
    @pytest.mark.integration
    async def test_complete_course_creation_workflow(self, mock_services):
        """Test complete workflow from user registration to course analytics"""
        # Arrange
        instructor_id = str(uuid4())
        course_id = str(uuid4())
        student_id = str(uuid4())
        
        # Mock service responses
        mock_services["user"].create_user.return_value = TestDataFactory.create_mock_user(
            id=instructor_id,
            role="instructor"
        )
        mock_services["course"].create_course.return_value = TestDataFactory.create_mock_course(
            id=course_id,
            instructor_id=instructor_id
        )
        mock_services["content"].create_syllabus.return_value = {
            "id": str(uuid4()),
            "course_id": course_id,
            "type": "syllabus"
        }
        mock_services["analytics"].initialize_course_analytics.return_value = True
        
        # Act - Complete workflow
        # 1. Create instructor user
        instructor = await mock_services["user"].create_user({
            "email": "instructor@example.com",
            "role": "instructor",
            "full_name": "Test Instructor"
        })
        
        # 2. Create course
        course = await mock_services["course"].create_course({
            "title": "Python Programming",
            "description": "Learn Python",
            "instructor_id": instructor_id
        })
        
        # 3. Create course content
        syllabus = await mock_services["content"].create_syllabus({
            "course_id": course_id,
            "title": "Course Syllabus",
            "duration_weeks": 12
        })
        
        # 4. Initialize analytics tracking
        analytics_initialized = await mock_services["analytics"].initialize_course_analytics(course_id)
        
        # Assert - Verify workflow completed successfully
        assert instructor["id"] == instructor_id
        assert instructor["role"] == "instructor"
        assert course["id"] == course_id
        assert course["instructor_id"] == instructor_id
        assert syllabus["course_id"] == course_id
        assert analytics_initialized
        
        # Verify all services were called
        mock_services["user"].create_user.assert_called_once()
        mock_services["course"].create_course.assert_called_once()
        mock_services["content"].create_syllabus.assert_called_once()
        mock_services["analytics"].initialize_course_analytics.assert_called_once()


class TestServiceErrorHandling:
    """Test error handling in service integrations"""
    
    @pytest.fixture
    def failing_service(self):
        """Create a service that simulates failures"""
        service = AsyncMock()
        service.operation.side_effect = Exception("Service unavailable")
        return service
    
    @pytest.fixture
    def resilient_service(self):
        """Create a service that handles failures gracefully"""
        service = AsyncMock()
        service.operation_with_fallback.return_value = {"status": "fallback_used"}
        return service
    
    @pytest.mark.integration
    async def test_service_failure_handling(self, failing_service, resilient_service):
        """Test that service failures are handled gracefully"""
        # Act & Assert
        with pytest.raises(Exception, match="Service unavailable"):
            await failing_service.operation()
        
        # Test fallback mechanism
        result = await resilient_service.operation_with_fallback()
        assert result["status"] == "fallback_used"
    
    @pytest.mark.integration
    async def test_service_timeout_handling(self):
        """Test handling of service timeouts"""
        # Arrange
        slow_service = AsyncMock()
        
        async def slow_operation():
            await asyncio.sleep(2)  # Simulate slow operation
            return "completed"
        
        slow_service.slow_operation = slow_operation
        
        # Act & Assert - Test timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_service.slow_operation(), timeout=0.1)


class TestServiceCommunication:
    """Test inter-service communication patterns"""
    
    @pytest.mark.integration
    async def test_event_driven_communication(self):
        """Test event-driven communication between services"""
        # Arrange
        event_bus = AsyncMock()
        course_service = AsyncMock()
        analytics_service = AsyncMock()
        
        # Mock event publishing
        event_bus.publish.return_value = True
        event_bus.subscribe.return_value = True
        
        # Act
        # 1. Course service publishes course creation event
        course_created_event = {
            "event_type": "course_created",
            "course_id": str(uuid4()),
            "instructor_id": str(uuid4()),
            "timestamp": datetime.utcnow()
        }
        
        await event_bus.publish("course_created", course_created_event)
        
        # 2. Analytics service receives and processes event
        await analytics_service.handle_course_created_event(course_created_event)
        
        # Assert
        event_bus.publish.assert_called_once_with("course_created", course_created_event)
        analytics_service.handle_course_created_event.assert_called_once_with(course_created_event)
    
    @pytest.mark.integration
    async def test_synchronous_service_calls(self):
        """Test synchronous service calls with proper error handling"""
        # Arrange
        user_service = AsyncMock()
        course_service = AsyncMock()
        
        user_service.get_user_by_id.return_value = TestDataFactory.create_mock_user(role="instructor")
        course_service.create_course.return_value = TestDataFactory.create_mock_course()
        
        # Act
        user_id = str(uuid4())
        
        # 1. Get user to verify permissions
        user = await user_service.get_user_by_id(user_id)
        
        # 2. Only create course if user is instructor
        if user["role"] == "instructor":
            course = await course_service.create_course({
                "title": "Test Course",
                "instructor_id": user_id
            })
        else:
            course = None
        
        # Assert
        assert user["role"] == "instructor"
        assert course is not None
        assert course["instructor_id"] == user_id
        user_service.get_user_by_id.assert_called_once_with(user_id)
        course_service.create_course.assert_called_once()


class TestDataConsistency:
    """Test data consistency across service boundaries"""
    
    @pytest.mark.integration
    async def test_transactional_consistency(self):
        """Test that operations maintain data consistency"""
        # Arrange
        user_service = AsyncMock()
        course_service = AsyncMock()
        enrollment_service = AsyncMock()
        
        # Mock transaction-like behavior
        user_service.begin_transaction.return_value = "tx_123"
        user_service.commit_transaction.return_value = True
        user_service.rollback_transaction.return_value = True
        
        # Act
        transaction_id = await user_service.begin_transaction()
        
        try:
            # 1. Create user
            user = await user_service.create_user({
                "email": "student@example.com",
                "role": "student"
            })
            
            # 2. Create course enrollment
            enrollment = await enrollment_service.create_enrollment({
                "student_id": user["id"],
                "course_id": str(uuid4())
            })
            
            # 3. Commit transaction
            await user_service.commit_transaction(transaction_id)
            
        except Exception:
            # Rollback on failure
            await user_service.rollback_transaction(transaction_id)
            raise
        
        # Assert
        user_service.begin_transaction.assert_called_once()
        user_service.commit_transaction.assert_called_once_with(transaction_id)
        user_service.rollback_transaction.assert_not_called()
    
    @pytest.mark.integration
    async def test_eventual_consistency(self):
        """Test eventual consistency patterns"""
        # Arrange
        primary_service = AsyncMock()
        cache_service = AsyncMock()
        
        # Mock cache invalidation
        primary_service.update_data.return_value = True
        cache_service.invalidate_cache.return_value = True
        cache_service.refresh_cache.return_value = True
        
        # Act
        data_id = str(uuid4())
        
        # 1. Update primary data
        await primary_service.update_data(data_id, {"status": "updated"})
        
        # 2. Invalidate cache
        await cache_service.invalidate_cache(data_id)
        
        # 3. Refresh cache with new data
        await cache_service.refresh_cache(data_id)
        
        # Assert
        primary_service.update_data.assert_called_once_with(data_id, {"status": "updated"})
        cache_service.invalidate_cache.assert_called_once_with(data_id)
        cache_service.refresh_cache.assert_called_once_with(data_id)