"""
Feedback Service Interface
Single Responsibility: Define feedback management operations
Interface Segregation: Focused interface for feedback operations only
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from domain.entities.feedback import CourseFeedback, StudentFeedback, FeedbackResponse

class IFeedbackService(ABC):
    """Interface for feedback management operations"""

    # Course Feedback Operations
    @abstractmethod
    async def submit_course_feedback(self, feedback: CourseFeedback) -> CourseFeedback:
        """Submit course feedback from a student"""
        pass

    @abstractmethod
    async def get_course_feedback_by_id(self, feedback_id: str) -> Optional[CourseFeedback]:
        """Get course feedback by ID"""
        pass

    @abstractmethod
    async def get_course_feedback(self, course_id: str, include_anonymous: bool = True) -> List[CourseFeedback]:
        """Get all feedback for a course"""
        pass

    @abstractmethod
    async def get_student_course_feedback(self, student_id: str, course_id: str) -> Optional[CourseFeedback]:
        """Get a student's feedback for a specific course"""
        pass

    @abstractmethod
    async def get_instructor_feedback_summary(self, instructor_id: str) -> Dict[str, Any]:
        """Get feedback summary for an instructor across all courses"""
        pass

    # Student Feedback Operations  
    @abstractmethod
    async def submit_student_feedback(self, feedback: StudentFeedback) -> StudentFeedback:
        """Submit feedback about a student from instructor"""
        pass

    @abstractmethod
    async def get_student_feedback_by_id(self, feedback_id: str) -> Optional[StudentFeedback]:
        """Get student feedback by ID"""
        pass

    @abstractmethod
    async def get_student_feedback(self, student_id: str, course_id: Optional[str] = None) -> List[StudentFeedback]:
        """Get all feedback for a student, optionally filtered by course"""
        pass

    @abstractmethod
    async def get_instructor_student_feedback(self, instructor_id: str, course_id: Optional[str] = None) -> List[StudentFeedback]:
        """Get all student feedback submitted by an instructor"""
        pass

    @abstractmethod
    async def update_student_feedback(self, feedback: StudentFeedback) -> StudentFeedback:
        """Update student feedback"""
        pass

    @abstractmethod
    async def share_student_feedback(self, feedback_id: str) -> StudentFeedback:
        """Share student feedback with the student"""
        pass

    @abstractmethod
    async def make_student_feedback_private(self, feedback_id: str) -> StudentFeedback:
        """Make student feedback private"""
        pass

    # Feedback Response Operations
    @abstractmethod
    async def submit_feedback_response(self, response: FeedbackResponse) -> FeedbackResponse:
        """Submit response to course feedback"""
        pass

    @abstractmethod
    async def get_feedback_responses(self, course_feedback_id: str) -> List[FeedbackResponse]:
        """Get all responses to a course feedback"""
        pass

    @abstractmethod
    async def update_feedback_response(self, response: FeedbackResponse) -> FeedbackResponse:
        """Update a feedback response"""
        pass

    # Analytics Operations
    @abstractmethod
    async def get_course_feedback_analytics(self, course_id: str) -> Dict[str, Any]:
        """Get analytics for course feedback"""
        pass

    @abstractmethod
    async def get_student_performance_analytics(self, student_id: str) -> Dict[str, Any]:
        """Get performance analytics for a student"""
        pass

    @abstractmethod
    async def flag_feedback_for_review(self, feedback_id: str, feedback_type: str = "course") -> bool:
        """Flag feedback for administrative review"""
        pass

    @abstractmethod
    async def archive_feedback(self, feedback_id: str, feedback_type: str = "course") -> bool:
        """Archive feedback"""
        pass