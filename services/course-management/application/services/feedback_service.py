"""
Feedback Service Implementation
Single Responsibility: Implement feedback management business logic
Dependency Inversion: Depends on repository abstractions, not concrete implementations
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from ...domain.entities.feedback import CourseFeedback, StudentFeedback, FeedbackResponse
from ...domain.interfaces.feedback_repository import (
    ICourseFeedbackRepository, IStudentFeedbackRepository, IFeedbackResponseRepository
)
from ...domain.interfaces.feedback_service import IFeedbackService
from ...domain.interfaces.course_repository import ICourseRepository
from ...domain.interfaces.enrollment_repository import IEnrollmentRepository

class FeedbackService(IFeedbackService):
    """
    Feedback service implementation with business logic
    """
    
    def __init__(self, 
                 course_feedback_repository: ICourseFeedbackRepository,
                 student_feedback_repository: IStudentFeedbackRepository, 
                 feedback_response_repository: IFeedbackResponseRepository,
                 course_repository: ICourseRepository,
                 enrollment_repository: IEnrollmentRepository):
        self._course_feedback_repository = course_feedback_repository
        self._student_feedback_repository = student_feedback_repository
        self._feedback_response_repository = feedback_response_repository
        self._course_repository = course_repository
        self._enrollment_repository = enrollment_repository
    
    # Course Feedback Operations
    async def submit_course_feedback(self, feedback: CourseFeedback) -> CourseFeedback:
        """Submit course feedback from a student with business validation"""
        # Generate ID if not provided
        if not feedback.id:
            feedback.id = str(uuid.uuid4())
        
        # Set submission timestamp
        feedback.submission_date = datetime.utcnow()
        feedback.created_at = datetime.utcnow()
        feedback.updated_at = datetime.utcnow()
        
        # Validate business rules
        feedback.validate()
        
        # Check if course exists
        course = await self._course_repository.get_by_id(feedback.course_id)
        if not course:
            raise ValueError(f"Course with ID {feedback.course_id} not found")
        
        # Check if student is enrolled in the course
        enrollment = await self._enrollment_repository.get_by_student_and_course(
            feedback.student_id, feedback.course_id
        )
        if not enrollment:
            raise ValueError("Student must be enrolled to provide feedback")
        
        # Check if student has already provided feedback
        existing_feedback = await self._course_feedback_repository.get_by_student_and_course(
            feedback.student_id, feedback.course_id
        )
        if existing_feedback:
            raise ValueError("Student has already provided feedback for this course")
        
        return await self._course_feedback_repository.create(feedback)
    
    async def get_course_feedback_by_id(self, feedback_id: str) -> Optional[CourseFeedback]:
        """Get course feedback by ID"""
        if not feedback_id:
            return None
        
        return await self._course_feedback_repository.get_by_id(feedback_id)
    
    async def get_course_feedback(self, course_id: str, include_anonymous: bool = True) -> List[CourseFeedback]:
        """Get all feedback for a course"""
        if not course_id:
            return []
        
        return await self._course_feedback_repository.get_by_course_id(course_id, include_anonymous)
    
    async def get_student_course_feedback(self, student_id: str, course_id: str) -> Optional[CourseFeedback]:
        """Get a student's feedback for a specific course"""
        if not student_id or not course_id:
            return None
        
        return await self._course_feedback_repository.get_by_student_and_course(student_id, course_id)
    
    async def get_instructor_feedback_summary(self, instructor_id: str) -> Dict[str, Any]:
        """Get feedback summary for an instructor across all courses"""
        if not instructor_id:
            return {}
        
        # Get all feedback for instructor's courses
        feedback_list = await self._course_feedback_repository.get_by_instructor_id(instructor_id)
        
        if not feedback_list:
            return {
                'total_feedback': 0,
                'average_rating': 0.0,
                'rating_distribution': {},
                'positive_feedback_rate': 0.0,
                'needs_attention_count': 0
            }
        
        # Calculate summary statistics
        total_feedback = len(feedback_list)
        total_rating = sum(f.overall_rating for f in feedback_list)
        average_rating = total_rating / total_feedback
        
        # Rating distribution
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[i] = len([f for f in feedback_list if f.overall_rating == i])
        
        # Positive feedback rate (4-5 stars)
        positive_count = len([f for f in feedback_list if f.is_positive_feedback()])
        positive_feedback_rate = positive_count / total_feedback * 100
        
        # Count feedback needing attention
        needs_attention_count = len([f for f in feedback_list if f.needs_attention()])
        
        return {
            'total_feedback': total_feedback,
            'average_rating': round(average_rating, 2),
            'rating_distribution': rating_distribution,
            'positive_feedback_rate': round(positive_feedback_rate, 2),
            'needs_attention_count': needs_attention_count
        }
    
    # Student Feedback Operations
    async def submit_student_feedback(self, feedback: StudentFeedback) -> StudentFeedback:
        """Submit feedback about a student from instructor"""
        # Generate ID if not provided
        if not feedback.id:
            feedback.id = str(uuid.uuid4())
        
        # Set submission timestamp
        feedback.submission_date = datetime.utcnow()
        feedback.created_at = datetime.utcnow()
        feedback.updated_at = datetime.utcnow()
        
        # Validate business rules
        feedback.validate()
        
        # Check if course exists and instructor owns it
        course = await self._course_repository.get_by_id(feedback.course_id)
        if not course:
            raise ValueError(f"Course with ID {feedback.course_id} not found")
        
        if course.instructor_id != feedback.instructor_id:
            raise ValueError("Instructor can only provide feedback for their own courses")
        
        # Check if student is enrolled in the course
        enrollment = await self._enrollment_repository.get_by_student_and_course(
            feedback.student_id, feedback.course_id
        )
        if not enrollment:
            raise ValueError("Student must be enrolled to receive feedback")
        
        return await self._student_feedback_repository.create(feedback)
    
    async def get_student_feedback_by_id(self, feedback_id: str) -> Optional[StudentFeedback]:
        """Get student feedback by ID"""
        if not feedback_id:
            return None
        
        return await self._student_feedback_repository.get_by_id(feedback_id)
    
    async def get_student_feedback(self, student_id: str, course_id: Optional[str] = None) -> List[StudentFeedback]:
        """Get all feedback for a student, optionally filtered by course"""
        if not student_id:
            return []
        
        return await self._student_feedback_repository.get_by_student_id(student_id, course_id)
    
    async def get_instructor_student_feedback(self, instructor_id: str, course_id: Optional[str] = None) -> List[StudentFeedback]:
        """Get all student feedback submitted by an instructor"""
        if not instructor_id:
            return []
        
        return await self._student_feedback_repository.get_by_instructor_id(instructor_id, course_id)
    
    async def update_student_feedback(self, feedback: StudentFeedback) -> StudentFeedback:
        """Update student feedback"""
        if not feedback.id:
            raise ValueError("Feedback ID is required for update")
        
        # Check if feedback exists
        existing_feedback = await self._student_feedback_repository.get_by_id(feedback.id)
        if not existing_feedback:
            raise ValueError(f"Feedback with ID {feedback.id} not found")
        
        # Validate business rules
        feedback.validate()
        
        # Update timestamp
        feedback.updated_at = datetime.utcnow()
        
        return await self._student_feedback_repository.update(feedback)
    
    async def share_student_feedback(self, feedback_id: str) -> StudentFeedback:
        """Share student feedback with the student"""
        feedback = await self._student_feedback_repository.get_by_id(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback with ID {feedback_id} not found")
        
        feedback.share_with_student()
        return await self._student_feedback_repository.update(feedback)
    
    async def make_student_feedback_private(self, feedback_id: str) -> StudentFeedback:
        """Make student feedback private"""
        feedback = await self._student_feedback_repository.get_by_id(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback with ID {feedback_id} not found")
        
        feedback.make_private()
        return await self._student_feedback_repository.update(feedback)
    
    # Feedback Response Operations
    async def submit_feedback_response(self, response: FeedbackResponse) -> FeedbackResponse:
        """Submit response to course feedback"""
        # Generate ID if not provided
        if not response.id:
            response.id = str(uuid.uuid4())
        
        # Set response timestamp
        response.response_date = datetime.utcnow()
        response.created_at = datetime.utcnow()
        response.updated_at = datetime.utcnow()
        
        # Validate business rules
        response.validate()
        
        # Check if course feedback exists
        course_feedback = await self._course_feedback_repository.get_by_id(response.course_feedback_id)
        if not course_feedback:
            raise ValueError(f"Course feedback with ID {response.course_feedback_id} not found")
        
        # Check if instructor owns the course
        if course_feedback.instructor_id != response.instructor_id:
            raise ValueError("Instructor can only respond to feedback for their own courses")
        
        return await self._feedback_response_repository.create(response)
    
    async def get_feedback_responses(self, course_feedback_id: str) -> List[FeedbackResponse]:
        """Get all responses to a course feedback"""
        if not course_feedback_id:
            return []
        
        return await self._feedback_response_repository.get_by_feedback_id(course_feedback_id)
    
    async def update_feedback_response(self, response: FeedbackResponse) -> FeedbackResponse:
        """Update a feedback response"""
        if not response.id:
            raise ValueError("Response ID is required for update")
        
        # Check if response exists
        existing_response = await self._feedback_response_repository.get_by_id(response.id)
        if not existing_response:
            raise ValueError(f"Response with ID {response.id} not found")
        
        # Validate business rules
        response.validate()
        
        # Update timestamp
        response.updated_at = datetime.utcnow()
        
        return await self._feedback_response_repository.update(response)
    
    # Analytics Operations
    async def get_course_feedback_analytics(self, course_id: str) -> Dict[str, Any]:
        """Get analytics for course feedback"""
        if not course_id:
            return {}
        
        feedback_list = await self._course_feedback_repository.get_by_course_id(course_id)
        
        if not feedback_list:
            return {
                'total_feedback': 0,
                'average_rating': 0.0,
                'rating_distribution': {},
                'completion_to_feedback_rate': 0.0
            }
        
        # Calculate analytics
        total_feedback = len(feedback_list)
        average_rating = await self._course_feedback_repository.get_average_rating(course_id)
        rating_distribution = await self._course_feedback_repository.get_rating_distribution(course_id)
        
        # Completion to feedback rate
        completed_enrollments = await self._enrollment_repository.count_completed_by_course(course_id)
        completion_to_feedback_rate = (total_feedback / completed_enrollments * 100) if completed_enrollments > 0 else 0
        
        return {
            'total_feedback': total_feedback,
            'average_rating': round(average_rating or 0.0, 2),
            'rating_distribution': rating_distribution,
            'completion_to_feedback_rate': round(completion_to_feedback_rate, 2)
        }
    
    async def get_student_performance_analytics(self, student_id: str) -> Dict[str, Any]:
        """Get performance analytics for a student"""
        if not student_id:
            return {}
        
        feedback_list = await self._student_feedback_repository.get_by_student_id(student_id)
        
        if not feedback_list:
            return {
                'total_feedback': 0,
                'average_performance': 0.0,
                'improvement_trend': 'no_data',
                'intervention_needed': False
            }
        
        # Calculate performance metrics
        performance_ratings = [f.overall_performance for f in feedback_list if f.overall_performance is not None]
        average_performance = sum(performance_ratings) / len(performance_ratings) if performance_ratings else 0.0
        
        # Check if intervention is needed
        intervention_needed = any(f.is_intervention_needed() for f in feedback_list)
        
        # Improvement trend (simplified)
        improvement_trend = 'stable'  # This could be more sophisticated
        if len(performance_ratings) >= 2:
            if performance_ratings[-1] > performance_ratings[0]:
                improvement_trend = 'improving'
            elif performance_ratings[-1] < performance_ratings[0]:
                improvement_trend = 'declining'
        
        return {
            'total_feedback': len(feedback_list),
            'average_performance': round(average_performance, 2),
            'improvement_trend': improvement_trend,
            'intervention_needed': intervention_needed
        }
    
    async def flag_feedback_for_review(self, feedback_id: str, feedback_type: str = "course") -> bool:
        """Flag feedback for administrative review"""
        if feedback_type == "course":
            feedback = await self._course_feedback_repository.get_by_id(feedback_id)
            if feedback:
                feedback.flag_for_review()
                await self._course_feedback_repository.update(feedback)
                return True
        elif feedback_type == "student":
            feedback = await self._student_feedback_repository.get_by_id(feedback_id)
            if feedback:
                feedback.flag_for_review()
                await self._student_feedback_repository.update(feedback)
                return True
        
        return False
    
    async def archive_feedback(self, feedback_id: str, feedback_type: str = "course") -> bool:
        """Archive feedback"""
        if feedback_type == "course":
            feedback = await self._course_feedback_repository.get_by_id(feedback_id)
            if feedback:
                feedback.archive()
                await self._course_feedback_repository.update(feedback)
                return True
        elif feedback_type == "student":
            feedback = await self._student_feedback_repository.get_by_id(feedback_id)
            if feedback:
                feedback.archive()
                await self._student_feedback_repository.update(feedback)
                return True
        
        return False