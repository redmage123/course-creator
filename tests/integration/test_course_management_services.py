"""
Integration Tests for Course Management Services
Testing service integration and dependency injection following SOLID principles
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from omegaconf import DictConfig
import sys
from pathlib import Path

# Add course-management service to path for direct imports
service_path = Path(__file__).parent.parent.parent / 'services' / 'course-management'
sys.path.insert(0, str(service_path))

# Import classes directly from the service
from course_management.infrastructure.container import Container
from course_management.domain.entities.course import Course, CourseStatus, DifficultyLevel
from course_management.domain.entities.enrollment import Enrollment, EnrollmentStatus
from course_management.domain.entities.feedback import (
    CourseFeedback, StudentFeedback, FeedbackResponse, 
    FeedbackStatus, FeedbackType, InterventionLevel
)
from course_management.application.services.course_service import CourseService
from course_management.application.services.enrollment_service import EnrollmentService
from course_management.application.services.feedback_service import FeedbackService

class TestCourseServiceIntegration:
    """Test course service integration with dependencies"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'},
            'server': {'host': '0.0.0.0', 'port': 8004}
        })
    
    @pytest.fixture
    def mock_container(self, mock_config):
        """Create container with mocked dependencies"""
        container = Container(mock_config)
        
        # Mock the repositories
        container._course_repository = AsyncMock()
        container._enrollment_repository = AsyncMock()
        
        return container
    
    @pytest.fixture
    def course_service(self, mock_container):
        """Create course service with mocked dependencies"""
        return mock_container.get_course_service()
    
    @pytest.mark.asyncio
    async def test_create_course_integration(self, course_service, mock_container):
        """Test complete course creation workflow"""
        # Setup mocks
        mock_container._course_repository.get_by_id.return_value = None  # No existing course
        mock_container._course_repository.exists_by_title.return_value = False  # Title available
        
        # Create course
        course = Course(
            title="Advanced Python Programming",
            description="Learn advanced Python concepts and design patterns",
            instructor_id="instructor_123",
            category="Programming",
            difficulty_level=DifficultyLevel.ADVANCED,
            estimated_hours=60,
            max_enrollments=50
        )
        
        # Mock repository save
        saved_course = course
        saved_course.id = "course_456"
        saved_course.created_at = datetime.utcnow()
        mock_container._course_repository.create.return_value = saved_course
        
        # Execute service method
        result = await course_service.create_course(course)
        
        # Verify results
        assert result.id == "course_456"
        assert result.title == "Advanced Python Programming"
        assert result.difficulty_level == DifficultyLevel.ADVANCED
        assert result.status == CourseStatus.DRAFT
        
        # Verify repository interactions
        mock_container._course_repository.exists_by_title.assert_called_once_with("Advanced Python Programming")
        mock_container._course_repository.create.assert_called_once_with(course)
    
    @pytest.mark.asyncio
    async def test_create_course_duplicate_title(self, course_service, mock_container):
        """Test course creation with duplicate title"""
        # Setup existing course with same title
        mock_container._course_repository.exists_by_title.return_value = True
        
        # Create course with duplicate title
        course = Course(
            title="Existing Course",
            description="This title already exists",
            instructor_id="instructor_123",
            category="Programming",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_hours=20
        )
        
        # Should raise ValueError for duplicate title
        with pytest.raises(ValueError, match="Course with title 'Existing Course' already exists"):
            await course_service.create_course(course)
        
        # Repository create should not be called
        mock_container._course_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_publish_course_integration(self, course_service, mock_container):
        """Test course publishing workflow"""
        # Setup existing draft course
        draft_course = Course(
            title="Ready to Publish",
            description="Course ready for publication",
            instructor_id="instructor_123",
            category="Programming",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_hours=40,
            status=CourseStatus.DRAFT
        )
        draft_course.id = "course_789"
        
        mock_container._course_repository.get_by_id.return_value = draft_course
        
        # Mock successful validation (course has required content)
        mock_container._course_repository.has_minimum_content.return_value = True
        
        # Mock repository update
        published_course = draft_course
        published_course.status = CourseStatus.PUBLISHED
        published_course.published_at = datetime.utcnow()
        mock_container._course_repository.update.return_value = published_course
        
        # Execute publishing
        result = await course_service.publish_course("course_789")
        
        # Verify results
        assert result.status == CourseStatus.PUBLISHED
        assert result.published_at is not None
        
        # Verify repository interactions
        mock_container._course_repository.get_by_id.assert_called_once_with("course_789")
        mock_container._course_repository.has_minimum_content.assert_called_once_with("course_789")
        mock_container._course_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_instructor_courses_integration(self, course_service, mock_container):
        """Test getting courses by instructor"""
        # Mock instructor courses
        instructor_courses = [
            Course(
                title="Python Basics",
                description="Introduction to Python",
                instructor_id="instructor_123",
                category="Programming",
                difficulty_level=DifficultyLevel.BEGINNER,
                estimated_hours=20,
                status=CourseStatus.PUBLISHED
            ),
            Course(
                title="Web Development",
                description="Build web applications",
                instructor_id="instructor_123",
                category="Web Development",
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                estimated_hours=40,
                status=CourseStatus.DRAFT
            )
        ]
        
        mock_container._course_repository.get_by_instructor_id.return_value = instructor_courses
        
        # Execute service method
        result = await course_service.get_instructor_courses("instructor_123")
        
        # Verify results
        assert len(result) == 2
        assert all(course.instructor_id == "instructor_123" for course in result)
        assert any(course.status == CourseStatus.PUBLISHED for course in result)
        assert any(course.status == CourseStatus.DRAFT for course in result)
        
        # Verify repository interaction
        mock_container._course_repository.get_by_instructor_id.assert_called_once_with("instructor_123")

class TestEnrollmentServiceIntegration:
    """Test enrollment service integration with dependencies"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.fixture
    def mock_container(self, mock_config):
        """Create container with mocked dependencies"""
        container = Container(mock_config)
        
        # Mock the repositories
        container._enrollment_repository = AsyncMock()
        container._course_repository = AsyncMock()
        
        return container
    
    @pytest.fixture
    def enrollment_service(self, mock_container):
        """Create enrollment service with mocked dependencies"""
        return mock_container.get_enrollment_service()
    
    @pytest.mark.asyncio
    async def test_enroll_student_integration(self, enrollment_service, mock_container):
        """Test complete student enrollment workflow"""
        # Setup course
        course = Course(
            title="Available Course",
            description="Course with available slots",
            instructor_id="instructor_123",
            category="Programming",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_hours=20,
            max_enrollments=50,
            status=CourseStatus.PUBLISHED
        )
        course.id = "course_456"
        
        mock_container._course_repository.get_by_id.return_value = course
        mock_container._enrollment_repository.exists.return_value = False  # Student not already enrolled
        mock_container._enrollment_repository.count_active_by_course.return_value = 25  # Room available
        
        # Create enrollment
        enrollment = Enrollment(
            student_id="student_123",
            course_id="course_456",
            instructor_id="instructor_123"
        )
        
        # Mock repository save
        saved_enrollment = enrollment
        saved_enrollment.id = "enrollment_789"
        saved_enrollment.enrolled_at = datetime.utcnow()
        mock_container._enrollment_repository.create.return_value = saved_enrollment
        
        # Execute service method
        result = await enrollment_service.enroll_student(enrollment)
        
        # Verify results
        assert result.id == "enrollment_789"
        assert result.student_id == "student_123"
        assert result.course_id == "course_456"
        assert result.status == EnrollmentStatus.ACTIVE
        
        # Verify repository interactions
        mock_container._course_repository.get_by_id.assert_called_once_with("course_456")
        mock_container._enrollment_repository.exists.assert_called_once_with("student_123", "course_456")
        mock_container._enrollment_repository.count_active_by_course.assert_called_once_with("course_456")
        mock_container._enrollment_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enroll_student_course_full(self, enrollment_service, mock_container):
        """Test enrollment when course is full"""
        # Setup full course
        course = Course(
            title="Full Course",
            description="Course at capacity",
            instructor_id="instructor_123",
            category="Programming",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_hours=20,
            max_enrollments=30,
            status=CourseStatus.PUBLISHED
        )
        course.id = "course_456"
        
        mock_container._course_repository.get_by_id.return_value = course
        mock_container._enrollment_repository.exists.return_value = False
        mock_container._enrollment_repository.count_active_by_course.return_value = 30  # At capacity
        
        # Create enrollment
        enrollment = Enrollment(
            student_id="student_123",
            course_id="course_456",
            instructor_id="instructor_123"
        )
        
        # Should raise ValueError for full course
        with pytest.raises(ValueError, match="Course is at maximum capacity"):
            await enrollment_service.enroll_student(enrollment)
        
        # Repository create should not be called
        mock_container._enrollment_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_student_enrollments_integration(self, enrollment_service, mock_container):
        """Test getting student enrollments"""
        # Mock student enrollments
        enrollments = [
            Enrollment(
                student_id="student_123",
                course_id="course_001",
                instructor_id="instructor_123",
                status=EnrollmentStatus.ACTIVE
            ),
            Enrollment(
                student_id="student_123",
                course_id="course_002",
                instructor_id="instructor_456",
                status=EnrollmentStatus.COMPLETED
            )
        ]
        
        mock_container._enrollment_repository.get_by_student_id.return_value = enrollments
        
        # Execute service method
        result = await enrollment_service.get_student_enrollments("student_123")
        
        # Verify results
        assert len(result) == 2
        assert all(enrollment.student_id == "student_123" for enrollment in result)
        assert any(enrollment.status == EnrollmentStatus.ACTIVE for enrollment in result)
        assert any(enrollment.status == EnrollmentStatus.COMPLETED for enrollment in result)
        
        # Verify repository interaction
        mock_container._enrollment_repository.get_by_student_id.assert_called_once_with("student_123")

class TestFeedbackServiceIntegration:
    """Test feedback service integration with multiple dependencies"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.fixture
    def mock_container(self, mock_config):
        """Create container with mocked dependencies"""
        container = Container(mock_config)
        
        # Mock all repositories
        container._course_feedback_repository = AsyncMock()
        container._student_feedback_repository = AsyncMock()
        container._feedback_response_repository = AsyncMock()
        container._course_repository = AsyncMock()
        container._enrollment_repository = AsyncMock()
        
        return container
    
    @pytest.fixture
    def feedback_service(self, mock_container):
        """Create feedback service with mocked dependencies"""
        return mock_container.get_feedback_service()
    
    @pytest.mark.asyncio
    async def test_submit_course_feedback_integration(self, feedback_service, mock_container):
        """Test complete course feedback submission workflow"""
        # Setup course and enrollment
        course = Course(
            title="Feedback Course",
            description="Course for feedback testing",
            instructor_id="instructor_123",
            category="Programming",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_hours=20,
            status=CourseStatus.PUBLISHED
        )
        course.id = "course_456"
        
        enrollment = Enrollment(
            student_id="student_123",
            course_id="course_456",
            instructor_id="instructor_123",
            status=EnrollmentStatus.ACTIVE
        )
        
        mock_container._course_repository.get_by_id.return_value = course
        mock_container._enrollment_repository.get_by_student_and_course.return_value = enrollment
        mock_container._course_feedback_repository.get_by_student_and_course.return_value = None  # No existing feedback
        
        # Create course feedback
        feedback = CourseFeedback(
            student_id="student_123",
            course_id="course_456",
            instructor_id="instructor_123",
            overall_rating=4.5,
            content_quality_rating=4.0,
            instructor_effectiveness_rating=5.0,
            difficulty_rating=3.0,
            pace_rating=4.0,
            comments="Great course! Very informative and well-structured.",
            is_anonymous=False
        )
        
        # Mock repository save
        saved_feedback = feedback
        saved_feedback.id = "feedback_789"
        saved_feedback.submitted_at = datetime.utcnow()
        mock_container._course_feedback_repository.create.return_value = saved_feedback
        
        # Execute service method
        result = await feedback_service.submit_course_feedback(feedback)
        
        # Verify results
        assert result.id == "feedback_789"
        assert result.student_id == "student_123"
        assert result.course_id == "course_456"
        assert result.overall_rating == 4.5
        assert result.status == FeedbackStatus.SUBMITTED
        
        # Verify repository interactions
        mock_container._course_repository.get_by_id.assert_called_once_with("course_456")
        mock_container._enrollment_repository.get_by_student_and_course.assert_called_once_with("student_123", "course_456")
        mock_container._course_feedback_repository.get_by_student_and_course.assert_called_once_with("student_123", "course_456")
        mock_container._course_feedback_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_student_feedback_integration(self, feedback_service, mock_container):
        """Test instructor feedback on student workflow"""
        # Setup course and enrollment
        course = Course(
            title="Assessment Course",
            description="Course for student assessment",
            instructor_id="instructor_123",
            category="Programming",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_hours=30,
            status=CourseStatus.PUBLISHED
        )
        course.id = "course_456"
        
        enrollment = Enrollment(
            student_id="student_123",
            course_id="course_456",
            instructor_id="instructor_123",
            status=EnrollmentStatus.ACTIVE
        )
        
        mock_container._course_repository.get_by_id.return_value = course
        mock_container._enrollment_repository.get_by_student_and_course.return_value = enrollment
        
        # Create student feedback
        feedback = StudentFeedback(
            student_id="student_123",
            instructor_id="instructor_123",
            course_id="course_456",
            feedback_type=FeedbackType.PROGRESS_UPDATE,
            academic_performance_rating=4.0,
            participation_rating=3.5,
            improvement_areas=["Time management", "Code organization"],
            strengths=["Problem-solving", "Quick learner"],
            recommendations="Focus on developing consistent coding practices and time management skills.",
            intervention_level=InterventionLevel.MODERATE,
            is_shared_with_student=True
        )
        
        # Mock repository save
        saved_feedback = feedback
        saved_feedback.id = "student_feedback_456"
        saved_feedback.created_at = datetime.utcnow()
        mock_container._student_feedback_repository.create.return_value = saved_feedback
        
        # Execute service method
        result = await feedback_service.submit_student_feedback(feedback)
        
        # Verify results
        assert result.id == "student_feedback_456"
        assert result.student_id == "student_123"
        assert result.instructor_id == "instructor_123"
        assert result.feedback_type == FeedbackType.PROGRESS_UPDATE
        assert result.intervention_level == InterventionLevel.MODERATE
        assert result.is_shared_with_student == True
        
        # Verify repository interactions
        mock_container._course_repository.get_by_id.assert_called_once_with("course_456")
        mock_container._enrollment_repository.get_by_student_and_course.assert_called_once_with("student_123", "course_456")
        mock_container._student_feedback_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_course_feedback_analytics_integration(self, feedback_service, mock_container):
        """Test course feedback analytics calculation"""
        # Mock course feedback data
        course_feedback = [
            CourseFeedback(
                student_id="student_1",
                course_id="course_456",
                instructor_id="instructor_123",
                overall_rating=4.5,
                content_quality_rating=4.0,
                instructor_effectiveness_rating=5.0,
                difficulty_rating=3.0,
                pace_rating=4.0,
                status=FeedbackStatus.SUBMITTED
            ),
            CourseFeedback(
                student_id="student_2",
                course_id="course_456",
                instructor_id="instructor_123",
                overall_rating=3.5,
                content_quality_rating=4.0,
                instructor_effectiveness_rating=3.0,
                difficulty_rating=4.0,
                pace_rating=3.5,
                status=FeedbackStatus.SUBMITTED
            ),
            CourseFeedback(
                student_id="student_3",
                course_id="course_456",
                instructor_id="instructor_123",
                overall_rating=5.0,
                content_quality_rating=5.0,
                instructor_effectiveness_rating=5.0,
                difficulty_rating=2.0,
                pace_rating=5.0,
                status=FeedbackStatus.SUBMITTED
            )
        ]
        
        mock_container._course_feedback_repository.get_by_course_id.return_value = course_feedback
        mock_container._course_feedback_repository.get_average_rating.return_value = 4.33
        mock_container._course_feedback_repository.get_rating_distribution.return_value = {
            '5': 1, '4': 1, '3': 1, '2': 0, '1': 0
        }
        mock_container._course_feedback_repository.count_by_course.return_value = 3
        
        # Execute service method
        analytics = await feedback_service.get_course_feedback_analytics("course_456")
        
        # Verify analytics structure
        assert analytics['course_id'] == "course_456"
        assert analytics['total_feedback_count'] == 3
        assert analytics['average_overall_rating'] == 4.33
        assert 'rating_distribution' in analytics
        assert 'category_averages' in analytics
        
        # Verify calculated averages
        category_averages = analytics['category_averages']
        assert category_averages['content_quality'] == 4.33  # (4.0+4.0+5.0)/3
        assert category_averages['instructor_effectiveness'] == 4.33  # (5.0+3.0+5.0)/3
        assert category_averages['difficulty'] == 3.0  # (3.0+4.0+2.0)/3
        assert category_averages['pace'] == 4.17  # (4.0+3.5+5.0)/3
        
        # Verify repository interactions
        mock_container._course_feedback_repository.get_by_course_id.assert_called_once_with("course_456", include_anonymous=True)
        mock_container._course_feedback_repository.get_average_rating.assert_called_once_with("course_456")
        mock_container._course_feedback_repository.get_rating_distribution.assert_called_once_with("course_456")
        mock_container._course_feedback_repository.count_by_course.assert_called_once_with("course_456")

class TestContainerIntegration:
    """Test dependency injection container integration"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.mark.asyncio
    async def test_container_initialization(self, mock_config):
        """Test container initialization and cleanup"""
        container = Container(mock_config)
        
        # Mock the database connection
        container._connection_pool = AsyncMock()
        
        await container.initialize()
        assert container._connection_pool is not None
        
        await container.cleanup()
    
    def test_container_service_creation(self, mock_config):
        """Test container creates services correctly"""
        container = Container(mock_config)
        
        # Test service creation
        course_service = container.get_course_service()
        assert isinstance(course_service, CourseService)
        
        enrollment_service = container.get_enrollment_service()
        assert isinstance(enrollment_service, EnrollmentService)
        
        feedback_service = container.get_feedback_service()
        assert isinstance(feedback_service, FeedbackService)
        
        # Test singleton behavior
        course_service2 = container.get_course_service()
        assert course_service is course_service2
    
    def test_container_repository_creation(self, mock_config):
        """Test container creates repositories correctly"""
        container = Container(mock_config)
        
        # Test repository creation (returns mock implementations for now)
        course_repo = container.get_course_repository()
        assert course_repo is not None
        
        enrollment_repo = container.get_enrollment_repository()
        assert enrollment_repo is not None
        
        feedback_repo = container.get_course_feedback_repository()
        assert feedback_repo is not None
        
        # Test singleton behavior
        course_repo2 = container.get_course_repository()
        assert course_repo is course_repo2

class TestCrossServiceIntegration:
    """Test integration between different course management services"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.fixture
    def container_with_mocks(self, mock_config):
        """Create container with mocked external dependencies"""
        container = Container(mock_config)
        
        # Mock all repositories
        container._course_repository = AsyncMock()
        container._enrollment_repository = AsyncMock()
        container._course_feedback_repository = AsyncMock()
        container._student_feedback_repository = AsyncMock()
        container._feedback_response_repository = AsyncMock()
        
        return container
    
    @pytest.mark.asyncio
    async def test_course_creation_to_enrollment_workflow(self, container_with_mocks):
        """Test workflow from course creation to student enrollment"""
        # Step 1: Create course
        course_service = container_with_mocks.get_course_service()
        
        # Mock course creation
        container_with_mocks._course_repository.exists_by_title.return_value = False
        
        created_course = Course(
            title="Full Stack Development",
            description="Complete web development course",
            instructor_id="instructor_123",
            category="Web Development",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_hours=80,
            max_enrollments=25
        )
        created_course.id = "course_789"
        created_course.status = CourseStatus.PUBLISHED
        container_with_mocks._course_repository.create.return_value = created_course
        
        course = await course_service.create_course(created_course)
        
        # Step 2: Enroll student in created course
        enrollment_service = container_with_mocks.get_enrollment_service()
        
        # Mock enrollment prerequisites
        container_with_mocks._course_repository.get_by_id.return_value = created_course
        container_with_mocks._enrollment_repository.exists.return_value = False
        container_with_mocks._enrollment_repository.count_active_by_course.return_value = 10  # Room available
        
        enrollment = Enrollment(
            student_id="student_456",
            course_id="course_789",
            instructor_id="instructor_123"
        )
        enrollment.id = "enrollment_123"
        container_with_mocks._enrollment_repository.create.return_value = enrollment
        
        enrolled = await enrollment_service.enroll_student(enrollment)
        
        # Verify the workflow worked
        assert course.id == enrolled.course_id
        assert course.instructor_id == enrolled.instructor_id
        
        # Both services should have been called
        container_with_mocks._course_repository.create.assert_called_once()
        container_with_mocks._enrollment_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enrollment_to_feedback_workflow(self, container_with_mocks):
        """Test workflow from enrollment to feedback submission"""
        enrollment_service = container_with_mocks.get_enrollment_service()
        feedback_service = container_with_mocks.get_feedback_service()
        
        # Step 1: Student enrollment
        course = Course(
            title="Python for Beginners",
            description="Introduction to Python programming",
            instructor_id="instructor_789",
            category="Programming",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_hours=30,
            max_enrollments=40,
            status=CourseStatus.PUBLISHED
        )
        course.id = "course_101"
        
        enrollment = Enrollment(
            student_id="student_202",
            course_id="course_101",
            instructor_id="instructor_789",
            status=EnrollmentStatus.ACTIVE
        )
        enrollment.id = "enrollment_303"
        
        # Mock enrollment retrieval
        container_with_mocks._enrollment_repository.get_by_student_id.return_value = [enrollment]
        
        student_enrollments = await enrollment_service.get_student_enrollments("student_202")
        
        # Step 2: Submit feedback for enrolled course
        # Mock feedback prerequisites
        container_with_mocks._course_repository.get_by_id.return_value = course
        container_with_mocks._enrollment_repository.get_by_student_and_course.return_value = enrollment
        container_with_mocks._course_feedback_repository.get_by_student_and_course.return_value = None
        
        feedback = CourseFeedback(
            student_id="student_202",
            course_id="course_101",
            instructor_id="instructor_789",
            overall_rating=4.8,
            content_quality_rating=5.0,
            instructor_effectiveness_rating=4.5,
            difficulty_rating=2.0,
            pace_rating=4.0,
            comments="Excellent introduction course! Well paced and clear explanations."
        )
        feedback.id = "feedback_404"
        container_with_mocks._course_feedback_repository.create.return_value = feedback
        
        submitted_feedback = await feedback_service.submit_course_feedback(feedback)
        
        # Verify the workflow worked
        assert len(student_enrollments) == 1
        assert student_enrollments[0].course_id == submitted_feedback.course_id
        assert student_enrollments[0].student_id == submitted_feedback.student_id
        
        # Both services should have been involved
        container_with_mocks._enrollment_repository.get_by_student_id.assert_called_once()
        container_with_mocks._course_feedback_repository.create.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])