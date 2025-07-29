"""
Unit Tests for Course Management Domain Entities
Following SOLID principles and TDD methodology
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

# Import domain entities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'))

from domain.entities.course import Course, DifficultyLevel, DurationUnit
from domain.entities.enrollment import Enrollment, EnrollmentStatus, EnrollmentRequest, BulkEnrollmentRequest
from domain.entities.feedback import CourseFeedback, StudentFeedback, FeedbackResponse, FeedbackType


class TestCourse:
    """Test Course domain entity following TDD principles"""
    
    def test_course_creation_with_valid_data(self):
        """Test creating a course with valid data"""
        # Arrange
        title = "Python Programming Fundamentals"
        description = "Learn Python from basics to advanced concepts"
        instructor_id = str(uuid4())
        
        # Act
        course = Course(
            title=title,
            description=description,
            instructor_id=instructor_id,
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        # Assert
        assert course.title == title
        assert course.description == description
        assert course.instructor_id == instructor_id
        assert course.difficulty_level == DifficultyLevel.BEGINNER
        assert course.price == 0.0
        assert not course.is_published
        assert course.created_at is not None
        assert course.updated_at is not None
        assert isinstance(course.id, str)
        assert course.tags == []
    
    def test_course_creation_with_empty_title_raises_error(self):
        """Test creating course with empty title raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Course(
                title="",
                description="Valid description",
                instructor_id=str(uuid4()),
                difficulty_level=DifficultyLevel.BEGINNER
            )
    
    def test_course_creation_with_empty_description_raises_error(self):
        """Test creating course with empty description raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Description cannot be empty"):
            Course(
                title="Valid Title",
                description="",
                instructor_id=str(uuid4()),
                difficulty_level=DifficultyLevel.BEGINNER
            )
    
    def test_course_creation_with_negative_price_raises_error(self):
        """Test creating course with negative price raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Price cannot be negative"):
            Course(
                title="Valid Title",
                description="Valid description",
                instructor_id=str(uuid4()),
                difficulty_level=DifficultyLevel.BEGINNER,
                price=-10.0
            )
    
    def test_course_update_details_success(self):
        """Test updating course details successfully"""
        # Arrange
        course = Course(
            title="Original Title",
            description="Original description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        original_updated_at = course.updated_at
        
        # Act
        course.update_details(
            title="Updated Title",
            description="Updated description",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            price=49.99
        )
        
        # Assert
        assert course.title == "Updated Title"
        assert course.description == "Updated description"
        assert course.difficulty_level == DifficultyLevel.INTERMEDIATE
        assert course.price == 49.99
        assert course.updated_at > original_updated_at
    
    def test_course_publish_success(self):
        """Test publishing course successfully"""
        # Arrange
        course = Course(
            title="Test Course",
            description="Test description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        # Act
        course.publish()
        
        # Assert
        assert course.is_published
        assert course.published_at is not None
    
    def test_course_unpublish_success(self):
        """Test unpublishing course successfully"""
        # Arrange
        course = Course(
            title="Test Course",
            description="Test description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        course.publish()
        
        # Act
        course.unpublish()
        
        # Assert
        assert not course.is_published
        assert course.published_at is None
    
    def test_course_add_tag_success(self):
        """Test adding tag to course successfully"""
        # Arrange
        course = Course(
            title="Test Course",
            description="Test description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        # Act
        course.add_tag("python")
        course.add_tag("programming")
        
        # Assert
        assert "python" in course.tags
        assert "programming" in course.tags
        assert len(course.tags) == 2
    
    def test_course_add_duplicate_tag_ignored(self):
        """Test adding duplicate tag is ignored"""
        # Arrange
        course = Course(
            title="Test Course",
            description="Test description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        # Act
        course.add_tag("python")
        course.add_tag("python")  # Duplicate
        
        # Assert
        assert course.tags.count("python") == 1
        assert len(course.tags) == 1
    
    def test_course_remove_tag_success(self):
        """Test removing tag from course successfully"""
        # Arrange
        course = Course(
            title="Test Course",
            description="Test description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER,
            tags=["python", "programming"]
        )
        
        # Act
        course.remove_tag("python")
        
        # Assert
        assert "python" not in course.tags
        assert "programming" in course.tags
        assert len(course.tags) == 1
    
    def test_course_remove_nonexistent_tag_ignored(self):
        """Test removing non-existent tag is ignored"""
        # Arrange
        course = Course(
            title="Test Course",
            description="Test description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER,
            tags=["python"]
        )
        
        # Act
        course.remove_tag("java")  # Non-existent tag
        
        # Assert
        assert course.tags == ["python"]
    
    def test_course_set_thumbnail_success(self):
        """Test setting course thumbnail successfully"""
        # Arrange
        course = Course(
            title="Test Course",
            description="Test description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        thumbnail_url = "https://example.com/thumbnail.jpg"
        
        # Act
        course.set_thumbnail(thumbnail_url)
        
        # Assert
        assert course.thumbnail_url == thumbnail_url
    
    def test_course_can_be_enrolled_returns_true_for_published_course(self):
        """Test can_be_enrolled returns True for published course"""
        # Arrange
        course = Course(
            title="Test Course",
            description="Test description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        course.publish()
        
        # Act & Assert
        assert course.can_be_enrolled()
    
    def test_course_can_be_enrolled_returns_false_for_unpublished_course(self):
        """Test can_be_enrolled returns False for unpublished course"""
        # Arrange
        course = Course(
            title="Test Course",
            description="Test description",
            instructor_id=str(uuid4()),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        # Act & Assert
        assert not course.can_be_enrolled()


class TestEnrollment:
    """Test Enrollment domain entity following TDD principles"""
    
    def test_enrollment_creation_with_valid_data(self):
        """Test creating enrollment with valid data"""
        # Arrange
        student_id = str(uuid4())
        course_id = str(uuid4())
        
        # Act
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id
        )
        
        # Assert
        assert enrollment.student_id == student_id
        assert enrollment.course_id == course_id
        assert enrollment.status == EnrollmentStatus.ACTIVE
        assert enrollment.enrolled_at is not None
        assert enrollment.progress_percentage == 0.0
        assert isinstance(enrollment.id, str)
    
    def test_enrollment_creation_with_custom_status(self):
        """Test creating enrollment with custom status"""
        # Arrange
        student_id = str(uuid4())
        course_id = str(uuid4())
        
        # Act
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.PENDING
        )
        
        # Assert
        assert enrollment.status == EnrollmentStatus.PENDING
    
    def test_enrollment_update_progress_success(self):
        """Test updating enrollment progress successfully"""
        # Arrange
        enrollment = Enrollment(
            student_id=str(uuid4()),
            course_id=str(uuid4())
        )
        
        # Act
        enrollment.update_progress(75.5)
        
        # Assert
        assert enrollment.progress_percentage == 75.5
        assert enrollment.last_accessed is not None
    
    def test_enrollment_update_progress_with_invalid_percentage_raises_error(self):
        """Test updating progress with invalid percentage raises ValueError"""
        # Arrange
        enrollment = Enrollment(
            student_id=str(uuid4()),
            course_id=str(uuid4())
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Progress percentage must be between 0 and 100"):
            enrollment.update_progress(150.0)
        
        with pytest.raises(ValueError, match="Progress percentage must be between 0 and 100"):
            enrollment.update_progress(-10.0)
    
    def test_enrollment_complete_success(self):
        """Test completing enrollment successfully"""
        # Arrange
        enrollment = Enrollment(
            student_id=str(uuid4()),
            course_id=str(uuid4())
        )
        
        # Act
        enrollment.complete()
        
        # Assert
        assert enrollment.status == EnrollmentStatus.COMPLETED
        assert enrollment.progress_percentage == 100.0
        assert enrollment.completed_at is not None
    
    def test_enrollment_withdraw_success(self):
        """Test withdrawing from enrollment successfully"""
        # Arrange
        enrollment = Enrollment(
            student_id=str(uuid4()),
            course_id=str(uuid4())
        )
        withdrawal_reason = "Schedule conflict"
        
        # Act
        enrollment.withdraw(withdrawal_reason)
        
        # Assert
        assert enrollment.status == EnrollmentStatus.WITHDRAWN
        assert enrollment.withdrawal_reason == withdrawal_reason
        assert enrollment.withdrawn_at is not None
    
    def test_enrollment_is_active_returns_correct_boolean(self):
        """Test is_active returns correct boolean"""
        # Arrange
        active_enrollment = Enrollment(
            student_id=str(uuid4()),
            course_id=str(uuid4())
        )
        
        withdrawn_enrollment = Enrollment(
            student_id=str(uuid4()),
            course_id=str(uuid4())
        )
        withdrawn_enrollment.withdraw("Test reason")
        
        # Act & Assert
        assert active_enrollment.is_active()
        assert not withdrawn_enrollment.is_active()
    
    def test_enrollment_is_completed_returns_correct_boolean(self):
        """Test is_completed returns correct boolean"""
        # Arrange
        active_enrollment = Enrollment(
            student_id=str(uuid4()),
            course_id=str(uuid4())
        )
        
        completed_enrollment = Enrollment(
            student_id=str(uuid4()),
            course_id=str(uuid4())
        )
        completed_enrollment.complete()
        
        # Act & Assert
        assert not active_enrollment.is_completed()
        assert completed_enrollment.is_completed()


class TestEnrollmentRequest:
    """Test EnrollmentRequest domain entity following TDD principles"""
    
    def test_enrollment_request_creation_with_valid_data(self):
        """Test creating enrollment request with valid data"""
        # Arrange
        student_email = "student@example.com"
        course_id = str(uuid4())
        
        # Act
        request = EnrollmentRequest(
            student_email=student_email,
            course_id=course_id
        )
        
        # Assert
        assert request.student_email == student_email
        assert request.course_id == course_id
        assert isinstance(request.id, str)
    
    def test_enrollment_request_creation_with_invalid_email_raises_error(self):
        """Test creating enrollment request with invalid email raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            EnrollmentRequest(
                student_email="invalid-email",
                course_id=str(uuid4())
            )
    
    def test_enrollment_request_validate_returns_true_for_valid_request(self):
        """Test validate returns True for valid request"""
        # Arrange
        request = EnrollmentRequest(
            student_email="student@example.com",
            course_id=str(uuid4())
        )
        
        # Act & Assert
        assert request.validate()
    
    def test_enrollment_request_to_enrollment_creates_enrollment(self):
        """Test to_enrollment creates Enrollment entity"""
        # Arrange
        request = EnrollmentRequest(
            student_email="student@example.com",
            course_id=str(uuid4())
        )
        student_id = str(uuid4())
        
        # Act
        enrollment = request.to_enrollment(student_id)
        
        # Assert
        assert isinstance(enrollment, Enrollment)
        assert enrollment.student_id == student_id
        assert enrollment.course_id == request.course_id
        assert enrollment.status == EnrollmentStatus.ACTIVE


class TestBulkEnrollmentRequest:
    """Test BulkEnrollmentRequest domain entity following TDD principles"""
    
    def test_bulk_enrollment_request_creation_with_valid_data(self):
        """Test creating bulk enrollment request with valid data"""
        # Arrange
        course_id = str(uuid4())
        student_emails = ["student1@example.com", "student2@example.com", "student3@example.com"]
        
        # Act
        request = BulkEnrollmentRequest(
            course_id=course_id,
            student_emails=student_emails
        )
        
        # Assert
        assert request.course_id == course_id
        assert request.student_emails == student_emails
        assert isinstance(request.id, str)
    
    def test_bulk_enrollment_request_creation_with_empty_emails_raises_error(self):
        """Test creating bulk enrollment request with empty emails raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="At least one student email is required"):
            BulkEnrollmentRequest(
                course_id=str(uuid4()),
                student_emails=[]
            )
    
    def test_bulk_enrollment_request_creation_with_invalid_email_raises_error(self):
        """Test creating bulk enrollment request with invalid email raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            BulkEnrollmentRequest(
                course_id=str(uuid4()),
                student_emails=["valid@example.com", "invalid-email"]
            )
    
    def test_bulk_enrollment_request_validate_returns_true_for_valid_request(self):
        """Test validate returns True for valid request"""
        # Arrange
        request = BulkEnrollmentRequest(
            course_id=str(uuid4()),
            student_emails=["student1@example.com", "student2@example.com"]
        )
        
        # Act & Assert
        assert request.validate()
    
    def test_bulk_enrollment_request_to_individual_requests_creates_list(self):
        """Test to_individual_requests creates list of EnrollmentRequest objects"""
        # Arrange
        course_id = str(uuid4())
        student_emails = ["student1@example.com", "student2@example.com"]
        request = BulkEnrollmentRequest(
            course_id=course_id,
            student_emails=student_emails
        )
        
        # Act
        individual_requests = request.to_individual_requests()
        
        # Assert
        assert len(individual_requests) == 2
        assert all(isinstance(req, EnrollmentRequest) for req in individual_requests)
        assert individual_requests[0].student_email == student_emails[0]
        assert individual_requests[1].student_email == student_emails[1]
        assert all(req.course_id == course_id for req in individual_requests)


class TestCourseFeedback:
    """Test CourseFeedback domain entity following TDD principles"""
    
    def test_course_feedback_creation_with_valid_data(self):
        """Test creating course feedback with valid data"""
        # Arrange
        student_id = str(uuid4())
        course_id = str(uuid4())
        overall_rating = 4
        
        # Act
        feedback = CourseFeedback(
            student_id=student_id,
            course_id=course_id,
            overall_rating=overall_rating
        )
        
        # Assert
        assert feedback.student_id == student_id
        assert feedback.course_id == course_id
        assert feedback.overall_rating == overall_rating
        assert feedback.feedback_type == FeedbackType.COURSE
        assert feedback.created_at is not None
        assert isinstance(feedback.id, str)
    
    def test_course_feedback_creation_with_invalid_rating_raises_error(self):
        """Test creating course feedback with invalid rating raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            CourseFeedback(
                student_id=str(uuid4()),
                course_id=str(uuid4()),
                overall_rating=6
            )
        
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            CourseFeedback(
                student_id=str(uuid4()),
                course_id=str(uuid4()),
                overall_rating=0
            )
    
    def test_course_feedback_update_rating_success(self):
        """Test updating course feedback rating successfully"""
        # Arrange
        feedback = CourseFeedback(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            overall_rating=3
        )
        
        # Act
        feedback.update_rating(5, content_quality=4, instructor_effectiveness=5)
        
        # Assert
        assert feedback.overall_rating == 5
        assert feedback.content_quality == 4
        assert feedback.instructor_effectiveness == 5
        assert feedback.updated_at is not None
    
    def test_course_feedback_add_comment_success(self):
        """Test adding comment to course feedback successfully"""
        # Arrange
        feedback = CourseFeedback(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            overall_rating=4
        )
        comment = "Great course, very informative!"
        
        # Act
        feedback.add_comment(comment)
        
        # Assert
        assert feedback.additional_comments == comment
        assert feedback.updated_at is not None
    
    def test_course_feedback_mark_anonymous_success(self):
        """Test marking course feedback as anonymous successfully"""
        # Arrange
        feedback = CourseFeedback(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            overall_rating=4
        )
        
        # Act
        feedback.mark_anonymous()
        
        # Assert
        assert feedback.is_anonymous
    
    def test_course_feedback_calculate_average_rating_success(self):
        """Test calculating average rating successfully"""
        # Arrange
        feedback = CourseFeedback(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            overall_rating=4,
            content_quality=5,
            instructor_effectiveness=3,
            difficulty_appropriateness=4
        )
        
        # Act
        average = feedback.calculate_average_detailed_rating()
        
        # Assert
        expected_average = (5 + 3 + 4) / 3  # Only non-None ratings
        assert average == expected_average


class TestStudentFeedback:
    """Test StudentFeedback domain entity following TDD principles"""
    
    def test_student_feedback_creation_with_valid_data(self):
        """Test creating student feedback with valid data"""
        # Arrange
        instructor_id = str(uuid4())
        student_id = str(uuid4())
        course_id = str(uuid4())
        performance_rating = 4
        
        # Act
        feedback = StudentFeedback(
            instructor_id=instructor_id,
            student_id=student_id,
            course_id=course_id,
            performance_rating=performance_rating
        )
        
        # Assert
        assert feedback.instructor_id == instructor_id
        assert feedback.student_id == student_id
        assert feedback.course_id == course_id
        assert feedback.performance_rating == performance_rating
        assert feedback.feedback_type == FeedbackType.STUDENT
        assert feedback.created_at is not None
        assert isinstance(feedback.id, str)
    
    def test_student_feedback_add_recommendation_success(self):
        """Test adding recommendation to student feedback successfully"""
        # Arrange
        feedback = StudentFeedback(
            instructor_id=str(uuid4()),
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            performance_rating=4
        )
        recommendation = "Focus more on practical exercises"
        
        # Act
        feedback.add_recommendation(recommendation)
        
        # Assert
        assert recommendation in feedback.recommendations
    
    def test_student_feedback_set_visibility_success(self):
        """Test setting student feedback visibility successfully"""
        # Arrange
        feedback = StudentFeedback(
            instructor_id=str(uuid4()),
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            performance_rating=4
        )
        
        # Act
        feedback.set_visibility(False)
        
        # Assert
        assert not feedback.is_visible_to_student


class TestFeedbackResponse:
    """Test FeedbackResponse domain entity following TDD principles"""
    
    def test_feedback_response_creation_with_valid_data(self):
        """Test creating feedback response with valid data"""
        # Arrange
        feedback_id = str(uuid4())
        responder_id = str(uuid4())
        response_text = "Thank you for your feedback!"
        
        # Act
        response = FeedbackResponse(
            feedback_id=feedback_id,
            responder_id=responder_id,
            response_text=response_text
        )
        
        # Assert
        assert response.feedback_id == feedback_id
        assert response.responder_id == responder_id
        assert response.response_text == response_text
        assert response.created_at is not None
        assert isinstance(response.id, str)
    
    def test_feedback_response_update_text_success(self):
        """Test updating feedback response text successfully"""
        # Arrange
        response = FeedbackResponse(
            feedback_id=str(uuid4()),
            responder_id=str(uuid4()),
            response_text="Original response"
        )
        new_text = "Updated response text"
        
        # Act
        response.update_text(new_text)
        
        # Assert
        assert response.response_text == new_text
        assert response.updated_at is not None


class TestEnums:
    """Test enumeration classes"""
    
    def test_difficulty_level_enum_values(self):
        """Test DifficultyLevel enum has expected values"""
        assert DifficultyLevel.BEGINNER.value == "beginner"
        assert DifficultyLevel.INTERMEDIATE.value == "intermediate"
        assert DifficultyLevel.ADVANCED.value == "advanced"
    
    def test_duration_unit_enum_values(self):
        """Test DurationUnit enum has expected values"""
        assert DurationUnit.HOURS.value == "hours"
        assert DurationUnit.DAYS.value == "days"
        assert DurationUnit.WEEKS.value == "weeks"
        assert DurationUnit.MONTHS.value == "months"
    
    def test_enrollment_status_enum_values(self):
        """Test EnrollmentStatus enum has expected values"""
        assert EnrollmentStatus.PENDING.value == "pending"
        assert EnrollmentStatus.ACTIVE.value == "active"
        assert EnrollmentStatus.COMPLETED.value == "completed"
        assert EnrollmentStatus.WITHDRAWN.value == "withdrawn"
    
    def test_feedback_type_enum_values(self):
        """Test FeedbackType enum has expected values"""
        assert FeedbackType.COURSE.value == "course"
        assert FeedbackType.STUDENT.value == "student"