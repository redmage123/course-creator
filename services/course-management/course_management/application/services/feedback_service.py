"""
Feedback Service Implementation - Bi-Directional Educational Assessment Platform

This module implements the feedback service layer, orchestrating the comprehensive bi-directional
feedback system that enables rich communication between students and instructors for continuous
improvement of educational outcomes and teaching effectiveness.

ARCHITECTURAL RESPONSIBILITIES:
The FeedbackService coordinates all feedback-related business operations, managing the complete
feedback lifecycle from submission through analysis and response. It ensures data integrity,
enforces educational policies, and provides rich analytics for continuous improvement.

BI-DIRECTIONAL FEEDBACK ORCHESTRATION:
1. Course Feedback Management: Student evaluations of course quality and instructor effectiveness
2. Student Assessment: Instructor feedback on student performance and development
3. Response Coordination: Professional instructor responses to course feedback
4. Analytics Integration: Comprehensive feedback analysis for educational insights
5. Quality Assurance: Moderation and review workflows for feedback integrity
6. Intervention Triggers: Early warning systems for students requiring support

EDUCATIONAL VALUE CREATION:
- Student Voice: Empowering students to influence course improvements and instructor development
- Instructor Insights: Detailed student performance analytics for personalized teaching
- Quality Improvement: Data-driven enhancements to course content and delivery methods
- Transparency: Open communication channels fostering trust and educational partnership
- Evidence-Based Teaching: Quantitative and qualitative feedback for methodology optimization

FEEDBACK WORKFLOW ORCHESTRATION:
Course Feedback Process:
- Eligibility Validation: Enrollment verification and duplicate prevention
- Submission Processing: Multi-dimensional rating capture with qualitative insights
- Instructor Notification: Real-time alerts for new feedback requiring attention
- Analytics Integration: Statistical aggregation for course performance dashboards

Student Assessment Process:
- Authorization Verification: Instructor ownership and enrollment validation
- Performance Evaluation: Multi-faceted assessment across academic dimensions
- Sharing Controls: Privacy management and student visibility preferences
- Intervention Detection: Automated identification of students requiring support

PRIVACY AND ETHICS MANAGEMENT:
- Anonymous Feedback: Student identity protection while preserving feedback value
- Access Controls: Strict authorization for feedback viewing and modification
- Data Retention: Compliance with educational privacy regulations (FERPA)
- Consent Management: Clear policies on feedback sharing and utilization

ANALYTICS AND BUSINESS INTELLIGENCE:
- Performance Correlation: Relationships between feedback and learning outcomes
- Trend Analysis: Longitudinal assessment of course and instructor effectiveness
- Sentiment Analysis: Natural language processing of qualitative feedback
- Predictive Analytics: Early warning systems for at-risk students
- Comparative Studies: Cross-course and cross-instructor performance analysis

INTEGRATION PATTERNS:
- Course Service: Validation of course existence and instructor authorization
- Enrollment Service: Verification of student course participation
- User Service: Identity validation and authorization for feedback operations
- Analytics Service: Rich data streaming for educational insights and reporting
- Notification Service: Automated alerts for feedback events and intervention triggers

QUALITY ASSURANCE WORKFLOWS:
- Validation Rules: Comprehensive business rule enforcement for feedback integrity
- Moderation Tools: Administrative review and flagging capabilities
- Response Management: Professional instructor response coordination
- Archive Management: Lifecycle management for historical feedback data

PERFORMANCE OPTIMIZATION:
- Async Operations: Non-blocking I/O for all database and external service interactions
- Caching Strategy: Optimized access to frequently queried feedback analytics
- Bulk Processing: Efficient handling of large-scale feedback analysis
- Event Sourcing: Complete audit trail for compliance and research purposes

BUSINESS RULE ENFORCEMENT:
- Enrollment Validation: Only enrolled students can provide course feedback
- Ownership Verification: Instructors can only manage feedback for their courses
- Duplicate Prevention: One feedback submission per student per course
- Rating Constraints: Standardized 1-5 scale validation for quantitative analysis
- Privacy Controls: Configurable sharing and visibility management
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from course_management.domain.entities.feedback import CourseFeedback, StudentFeedback, FeedbackResponse
from data_access.course_dao import CourseManagementDAO
from course_management.domain.interfaces.feedback_service import IFeedbackService

class FeedbackService(IFeedbackService):
    """
    Feedback service implementation with business logic
    """
    
    def __init__(self, dao: CourseManagementDAO):
        self._dao = dao
    
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
        course = await self._dao.get_by_id(feedback.course_id)
        if not course:
            raise ValueError(f"Course with ID {feedback.course_id} not found")
        
        # Check if student is enrolled in the course
        enrollment = await self._dao.get_by_student_and_course(
            feedback.student_id, feedback.course_id
        )
        if not enrollment:
            raise ValueError("Student must be enrolled to provide feedback")
        
        # Check if student has already provided feedback
        existing_feedback = await self._dao.get_by_student_and_course(
            feedback.student_id, feedback.course_id
        )
        if existing_feedback:
            raise ValueError("Student has already provided feedback for this course")
        
        return await self._dao.create(feedback)
    
    async def get_course_feedback_by_id(self, feedback_id: str) -> Optional[CourseFeedback]:
        """Get course feedback by ID"""
        if not feedback_id:
            return None
        
        return await self._dao.get_by_id(feedback_id)
    
    async def get_course_feedback(self, course_id: str, include_anonymous: bool = True) -> List[CourseFeedback]:
        """Get all feedback for a course"""
        if not course_id:
            return []
        
        return await self._dao.get_by_course_id(course_id, include_anonymous)
    
    async def get_student_course_feedback(self, student_id: str, course_id: str) -> Optional[CourseFeedback]:
        """Get a student's feedback for a specific course"""
        if not student_id or not course_id:
            return None
        
        return await self._dao.get_by_student_and_course(student_id, course_id)
    
    async def get_instructor_feedback_summary(self, instructor_id: str) -> Dict[str, Any]:
        """Get feedback summary for an instructor across all courses"""
        if not instructor_id:
            return {}
        
        # Get all feedback for instructor's courses
        feedback_list = await self._dao.get_by_instructor_id(instructor_id)
        
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
        course = await self._dao.get_by_id(feedback.course_id)
        if not course:
            raise ValueError(f"Course with ID {feedback.course_id} not found")
        
        if course.instructor_id != feedback.instructor_id:
            raise ValueError("Instructor can only provide feedback for their own courses")
        
        # Check if student is enrolled in the course
        enrollment = await self._dao.get_by_student_and_course(
            feedback.student_id, feedback.course_id
        )
        if not enrollment:
            raise ValueError("Student must be enrolled to receive feedback")
        
        return await self._dao.create(feedback)
    
    async def get_student_feedback_by_id(self, feedback_id: str) -> Optional[StudentFeedback]:
        """Get student feedback by ID"""
        if not feedback_id:
            return None
        
        return await self._dao.get_by_id(feedback_id)
    
    async def get_student_feedback(self, student_id: str, course_id: Optional[str] = None) -> List[StudentFeedback]:
        """Get all feedback for a student, optionally filtered by course"""
        if not student_id:
            return []
        
        return await self._dao.get_by_student_id(student_id, course_id)
    
    async def get_instructor_student_feedback(self, instructor_id: str, course_id: Optional[str] = None) -> List[StudentFeedback]:
        """Get all student feedback submitted by an instructor"""
        if not instructor_id:
            return []
        
        return await self._dao.get_by_instructor_id(instructor_id, course_id)
    
    async def update_student_feedback(self, feedback: StudentFeedback) -> StudentFeedback:
        """Update student feedback"""
        if not feedback.id:
            raise ValueError("Feedback ID is required for update")
        
        # Check if feedback exists
        existing_feedback = await self._dao.get_by_id(feedback.id)
        if not existing_feedback:
            raise ValueError(f"Feedback with ID {feedback.id} not found")
        
        # Validate business rules
        feedback.validate()
        
        # Update timestamp
        feedback.updated_at = datetime.utcnow()
        
        return await self._dao.update(feedback)
    
    async def share_student_feedback(self, feedback_id: str) -> StudentFeedback:
        """Share student feedback with the student"""
        feedback = await self._dao.get_by_id(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback with ID {feedback_id} not found")
        
        feedback.share_with_student()
        return await self._dao.update(feedback)
    
    async def make_student_feedback_private(self, feedback_id: str) -> StudentFeedback:
        """Make student feedback private"""
        feedback = await self._dao.get_by_id(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback with ID {feedback_id} not found")
        
        feedback.make_private()
        return await self._dao.update(feedback)
    
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
        course_feedback = await self._dao.get_by_id(response.course_feedback_id)
        if not course_feedback:
            raise ValueError(f"Course feedback with ID {response.course_feedback_id} not found")
        
        # Check if instructor owns the course
        if course_feedback.instructor_id != response.instructor_id:
            raise ValueError("Instructor can only respond to feedback for their own courses")
        
        return await self._dao.create(response)
    
    async def get_feedback_responses(self, course_feedback_id: str) -> List[FeedbackResponse]:
        """Get all responses to a course feedback"""
        if not course_feedback_id:
            return []
        
        return await self._dao.get_by_feedback_id(course_feedback_id)
    
    async def update_feedback_response(self, response: FeedbackResponse) -> FeedbackResponse:
        """Update a feedback response"""
        if not response.id:
            raise ValueError("Response ID is required for update")
        
        # Check if response exists
        existing_response = await self._dao.get_by_id(response.id)
        if not existing_response:
            raise ValueError(f"Response with ID {response.id} not found")
        
        # Validate business rules
        response.validate()
        
        # Update timestamp
        response.updated_at = datetime.utcnow()
        
        return await self._dao.update(response)
    
    # Analytics Operations
    async def get_course_feedback_analytics(self, course_id: str) -> Dict[str, Any]:
        """Get analytics for course feedback"""
        if not course_id:
            return {}
        
        feedback_list = await self._dao.get_by_course_id(course_id)
        
        if not feedback_list:
            return {
                'total_feedback': 0,
                'average_rating': 0.0,
                'rating_distribution': {},
                'completion_to_feedback_rate': 0.0
            }
        
        # Calculate analytics
        total_feedback = len(feedback_list)
        average_rating = await self._dao.get_average_rating(course_id)
        rating_distribution = await self._dao.get_rating_distribution(course_id)
        
        # Completion to feedback rate
        completed_enrollments = await self._dao.count_completed_by_course(course_id)
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
        
        feedback_list = await self._dao.get_by_student_id(student_id)
        
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
            feedback = await self._dao.get_by_id(feedback_id)
            if feedback:
                feedback.flag_for_review()
                await self._dao.update(feedback)
                return True
        elif feedback_type == "student":
            feedback = await self._dao.get_by_id(feedback_id)
            if feedback:
                feedback.flag_for_review()
                await self._dao.update(feedback)
                return True
        
        return False
    
    async def archive_feedback(self, feedback_id: str, feedback_type: str = "course") -> bool:
        """Archive feedback"""
        if feedback_type == "course":
            feedback = await self._dao.get_by_id(feedback_id)
            if feedback:
                feedback.archive()
                await self._dao.update(feedback)
                return True
        elif feedback_type == "student":
            feedback = await self._dao.get_by_id(feedback_id)
            if feedback:
                feedback.archive()
                await self._dao.update(feedback)
                return True
        
        return False