"""
Feedback Domain Entities
Single Responsibility: Represent course and student feedback with business logic
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class FeedbackStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    FLAGGED = "flagged"

class FeedbackType(Enum):
    REGULAR = "regular"
    MIDTERM = "midterm" 
    FINAL = "final"
    INTERVENTION = "intervention"

class ProgressAssessment(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"

class ExpectedOutcome(Enum):
    EXCEEDS_EXPECTATIONS = "exceeds_expectations"
    MEETS_EXPECTATIONS = "meets_expectations"
    BELOW_EXPECTATIONS = "below_expectations"
    AT_RISK = "at_risk"

class AcknowledgmentType(Enum):
    STANDARD = "standard"
    DETAILED = "detailed"
    ACTION_PLAN = "action_plan"

@dataclass
class CourseFeedback:
    """
    Course feedback domain entity - student feedback about a course
    """
    student_id: str
    course_id: str
    instructor_id: str
    overall_rating: int
    is_anonymous: bool = False
    status: FeedbackStatus = FeedbackStatus.ACTIVE
    id: Optional[str] = None
    content_quality: Optional[int] = None
    instructor_effectiveness: Optional[int] = None
    difficulty_appropriateness: Optional[int] = None
    lab_quality: Optional[int] = None
    positive_aspects: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    additional_comments: Optional[str] = None
    would_recommend: Optional[bool] = None
    submission_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate invariants after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules and invariants"""
        if not self.student_id:
            raise ValueError("Feedback must have a student ID")
        
        if not self.course_id:
            raise ValueError("Feedback must have a course ID")
        
        if not self.instructor_id:
            raise ValueError("Feedback must have an instructor ID")
        
        if not (1 <= self.overall_rating <= 5):
            raise ValueError("Overall rating must be between 1 and 5")
        
        # Validate optional ratings
        for rating_field, value in [
            ("content_quality", self.content_quality),
            ("instructor_effectiveness", self.instructor_effectiveness),
            ("difficulty_appropriateness", self.difficulty_appropriateness),
            ("lab_quality", self.lab_quality)
        ]:
            if value is not None and not (1 <= value <= 5):
                raise ValueError(f"{rating_field} must be between 1 and 5")
    
    def is_positive_feedback(self) -> bool:
        """Business rule: Check if feedback is generally positive"""
        return self.overall_rating >= 4
    
    def needs_attention(self) -> bool:
        """Business rule: Check if feedback indicates issues requiring attention"""
        return (
            self.overall_rating <= 2 or
            (self.content_quality is not None and self.content_quality <= 2) or
            (self.instructor_effectiveness is not None and self.instructor_effectiveness <= 2)
        )
    
    def flag_for_review(self) -> None:
        """Business rule: Flag feedback for administrative review"""
        self.status = FeedbackStatus.FLAGGED
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Business rule: Archive feedback"""
        self.status = FeedbackStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    def get_average_rating(self) -> float:
        """Calculate average rating across all rating categories"""
        ratings = [self.overall_rating]
        
        if self.content_quality is not None:
            ratings.append(self.content_quality)
        if self.instructor_effectiveness is not None:
            ratings.append(self.instructor_effectiveness)
        if self.difficulty_appropriateness is not None:
            ratings.append(self.difficulty_appropriateness)
        if self.lab_quality is not None:
            ratings.append(self.lab_quality)
        
        return sum(ratings) / len(ratings)

@dataclass
class StudentFeedback:
    """
    Student feedback domain entity - instructor feedback about a student
    """
    instructor_id: str
    student_id: str
    course_id: str
    feedback_type: FeedbackType = FeedbackType.REGULAR
    is_shared_with_student: bool = False
    status: FeedbackStatus = FeedbackStatus.ACTIVE
    id: Optional[str] = None
    overall_performance: Optional[int] = None
    participation: Optional[int] = None
    lab_performance: Optional[int] = None
    quiz_performance: Optional[int] = None
    improvement_trend: Optional[int] = None
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    specific_recommendations: Optional[str] = None
    notable_achievements: Optional[str] = None
    concerns: Optional[str] = None
    progress_assessment: Optional[ProgressAssessment] = None
    expected_outcome: Optional[ExpectedOutcome] = None
    submission_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate invariants after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules and invariants"""
        if not self.instructor_id:
            raise ValueError("Feedback must have an instructor ID")
        
        if not self.student_id:
            raise ValueError("Feedback must have a student ID")
        
        if not self.course_id:
            raise ValueError("Feedback must have a course ID")
        
        # Validate optional ratings
        for rating_field, value in [
            ("overall_performance", self.overall_performance),
            ("participation", self.participation),
            ("lab_performance", self.lab_performance),
            ("quiz_performance", self.quiz_performance),
            ("improvement_trend", self.improvement_trend)
        ]:
            if value is not None and not (1 <= value <= 5):
                raise ValueError(f"{rating_field} must be between 1 and 5")
    
    def is_intervention_needed(self) -> bool:
        """Business rule: Check if student needs intervention"""
        return (
            self.expected_outcome == ExpectedOutcome.AT_RISK or
            self.progress_assessment == ProgressAssessment.POOR or
            (self.overall_performance is not None and self.overall_performance <= 2)
        )
    
    def is_high_performer(self) -> bool:
        """Business rule: Check if student is a high performer"""
        return (
            self.expected_outcome == ExpectedOutcome.EXCEEDS_EXPECTATIONS or
            self.progress_assessment == ProgressAssessment.EXCELLENT or
            (self.overall_performance is not None and self.overall_performance >= 4)
        )
    
    def share_with_student(self) -> None:
        """Business rule: Mark feedback as shareable with student"""
        self.is_shared_with_student = True
        self.updated_at = datetime.utcnow()
    
    def make_private(self) -> None:
        """Business rule: Make feedback private (not shared with student)"""
        self.is_shared_with_student = False
        self.updated_at = datetime.utcnow()
    
    def escalate_to_intervention(self) -> None:
        """Business rule: Escalate feedback to intervention type"""
        if not self.is_intervention_needed():
            raise ValueError("Feedback does not meet intervention criteria")
        
        self.feedback_type = FeedbackType.INTERVENTION
        self.updated_at = datetime.utcnow()
    
    def get_performance_summary(self) -> dict:
        """Get performance summary across all areas"""
        ratings = {}
        
        if self.overall_performance is not None:
            ratings['overall'] = self.overall_performance
        if self.participation is not None:
            ratings['participation'] = self.participation
        if self.lab_performance is not None:
            ratings['labs'] = self.lab_performance
        if self.quiz_performance is not None:
            ratings['quizzes'] = self.quiz_performance
        if self.improvement_trend is not None:
            ratings['improvement'] = self.improvement_trend
        
        if ratings:
            ratings['average'] = sum(ratings.values()) / len(ratings)
        
        return ratings

@dataclass
class FeedbackResponse:
    """
    Feedback response domain entity - instructor response to course feedback
    """
    course_feedback_id: str
    instructor_id: str
    response_text: str
    acknowledgment_type: AcknowledgmentType = AcknowledgmentType.STANDARD
    is_public: bool = False
    id: Optional[str] = None
    action_items: Optional[str] = None
    response_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate invariants after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules and invariants"""
        if not self.course_feedback_id:
            raise ValueError("Response must reference a course feedback")
        
        if not self.instructor_id:
            raise ValueError("Response must have an instructor ID")
        
        if not self.response_text or len(self.response_text.strip()) == 0:
            raise ValueError("Response text cannot be empty")
        
        if len(self.response_text) > 2000:
            raise ValueError("Response text cannot exceed 2000 characters")
    
    def make_public(self) -> None:
        """Business rule: Make response visible to all students"""
        self.is_public = True
        self.updated_at = datetime.utcnow()
    
    def make_private(self) -> None:
        """Business rule: Make response private"""
        self.is_public = False
        self.updated_at = datetime.utcnow()
    
    def add_action_items(self, action_items: str) -> None:
        """Business rule: Add action items to response"""
        self.action_items = action_items
        self.acknowledgment_type = AcknowledgmentType.ACTION_PLAN
        self.updated_at = datetime.utcnow()