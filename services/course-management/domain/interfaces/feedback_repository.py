"""
Feedback Repository Interface
Single Responsibility: Define data access operations for feedback
Dependency Inversion: Abstract interface for data persistence
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from domain.entities.feedback import CourseFeedback, StudentFeedback, FeedbackResponse, FeedbackStatus

class ICourseFeedbackRepository(ABC):
    """Interface for course feedback data access operations"""

    @abstractmethod
    async def create(self, feedback: CourseFeedback) -> CourseFeedback:
        """Create new course feedback"""
        pass

    @abstractmethod
    async def get_by_id(self, feedback_id: str) -> Optional[CourseFeedback]:
        """Get course feedback by ID"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str, include_anonymous: bool = True) -> List[CourseFeedback]:
        """Get all feedback for a course"""
        pass

    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, course_id: str) -> Optional[CourseFeedback]:
        """Get student's feedback for a specific course"""
        pass

    @abstractmethod
    async def get_by_instructor_id(self, instructor_id: str) -> List[CourseFeedback]:
        """Get all feedback for courses taught by instructor"""
        pass

    @abstractmethod
    async def update(self, feedback: CourseFeedback) -> CourseFeedback:
        """Update course feedback"""
        pass

    @abstractmethod
    async def delete(self, feedback_id: str) -> bool:
        """Delete course feedback"""
        pass

    @abstractmethod
    async def get_average_rating(self, course_id: str) -> Optional[float]:
        """Get average rating for a course"""
        pass

    @abstractmethod
    async def get_rating_distribution(self, course_id: str) -> Dict[int, int]:
        """Get distribution of ratings for a course"""
        pass

    @abstractmethod
    async def count_by_course(self, course_id: str) -> int:
        """Count feedback entries for a course"""
        pass

    @abstractmethod
    async def get_by_status(self, status: FeedbackStatus) -> List[CourseFeedback]:
        """Get feedback by status"""
        pass

class IStudentFeedbackRepository(ABC):
    """Interface for student feedback data access operations"""

    @abstractmethod
    async def create(self, feedback: StudentFeedback) -> StudentFeedback:
        """Create new student feedback"""
        pass

    @abstractmethod
    async def get_by_id(self, feedback_id: str) -> Optional[StudentFeedback]:
        """Get student feedback by ID"""
        pass

    @abstractmethod
    async def get_by_student_id(self, student_id: str, course_id: Optional[str] = None) -> List[StudentFeedback]:
        """Get all feedback for a student, optionally filtered by course"""
        pass

    @abstractmethod
    async def get_by_instructor_id(self, instructor_id: str, course_id: Optional[str] = None) -> List[StudentFeedback]:
        """Get all student feedback submitted by instructor"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[StudentFeedback]:
        """Get all student feedback for a course"""
        pass

    @abstractmethod
    async def update(self, feedback: StudentFeedback) -> StudentFeedback:
        """Update student feedback"""
        pass

    @abstractmethod
    async def delete(self, feedback_id: str) -> bool:
        """Delete student feedback"""
        pass

    @abstractmethod
    async def get_shared_feedback(self, student_id: str) -> List[StudentFeedback]:
        """Get feedback shared with the student"""
        pass

    @abstractmethod
    async def count_by_student(self, student_id: str) -> int:
        """Count feedback entries for a student"""
        pass

    @abstractmethod
    async def get_intervention_needed(self, instructor_id: str) -> List[StudentFeedback]:
        """Get students who need intervention"""
        pass

class IFeedbackResponseRepository(ABC):
    """Interface for feedback response data access operations"""

    @abstractmethod
    async def create(self, response: FeedbackResponse) -> FeedbackResponse:
        """Create new feedback response"""
        pass

    @abstractmethod
    async def get_by_id(self, response_id: str) -> Optional[FeedbackResponse]:
        """Get feedback response by ID"""
        pass

    @abstractmethod
    async def get_by_feedback_id(self, course_feedback_id: str) -> List[FeedbackResponse]:
        """Get all responses to a course feedback"""
        pass

    @abstractmethod
    async def get_by_instructor_id(self, instructor_id: str) -> List[FeedbackResponse]:
        """Get all responses by an instructor"""
        pass

    @abstractmethod
    async def update(self, response: FeedbackResponse) -> FeedbackResponse:
        """Update feedback response"""
        pass

    @abstractmethod
    async def delete(self, response_id: str) -> bool:
        """Delete feedback response"""
        pass

    @abstractmethod
    async def get_public_responses(self, course_id: str) -> List[FeedbackResponse]:
        """Get public responses for a course"""
        pass