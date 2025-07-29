"""
Student Analytics Domain Entities
Single Responsibility: Core analytics business entities with validation and business logic
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

class ActivityType(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LAB_ACCESS = "lab_access"
    QUIZ_START = "quiz_start"
    QUIZ_COMPLETE = "quiz_complete"
    CONTENT_VIEW = "content_view"
    CODE_EXECUTION = "code_execution"
    EXERCISE_SUBMISSION = "exercise_submission"

class CompletionStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    MASTERED = "mastered"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ContentType(Enum):
    MODULE = "module"
    LESSON = "lesson"
    LAB = "lab"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    EXERCISE = "exercise"

@dataclass
class StudentActivity:
    """
    Domain entity representing a student activity event
    Encapsulates business rules for activity tracking
    """
    student_id: str
    course_id: str
    activity_type: ActivityType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    activity_data: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate activity data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate student activity business rules"""
        if not self.student_id:
            raise ValueError("Student ID is required")
        
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not isinstance(self.activity_type, ActivityType):
            raise ValueError("Invalid activity type")
        
        if self.timestamp > datetime.utcnow():
            raise ValueError("Activity timestamp cannot be in the future")
        
        # Validate activity-specific data
        self._validate_activity_specific_data()
    
    def _validate_activity_specific_data(self) -> None:
        """Validate activity-specific data based on activity type"""
        if self.activity_type == ActivityType.QUIZ_START:
            if 'quiz_id' not in self.activity_data:
                raise ValueError("Quiz start activity must include quiz_id")
        
        elif self.activity_type == ActivityType.QUIZ_COMPLETE:
            required_fields = ['quiz_id', 'score', 'questions_total', 'questions_correct']
            for field in required_fields:
                if field not in self.activity_data:
                    raise ValueError(f"Quiz complete activity must include {field}")
        
        elif self.activity_type == ActivityType.LAB_ACCESS:
            if 'lab_id' not in self.activity_data:
                raise ValueError("Lab access activity must include lab_id")
        
        elif self.activity_type == ActivityType.CODE_EXECUTION:
            if 'code_snippet' not in self.activity_data:
                raise ValueError("Code execution activity must include code_snippet")
    
    def get_duration_from_previous(self, previous_activity: 'StudentActivity') -> timedelta:
        """Calculate duration between this activity and a previous one"""
        if not previous_activity:
            return timedelta(0)
        
        if previous_activity.timestamp > self.timestamp:
            raise ValueError("Previous activity cannot be after current activity")
        
        return self.timestamp - previous_activity.timestamp
    
    def is_engagement_activity(self) -> bool:
        """Check if this activity indicates active engagement"""
        engagement_activities = {
            ActivityType.LAB_ACCESS,
            ActivityType.QUIZ_START,
            ActivityType.CODE_EXECUTION,
            ActivityType.EXERCISE_SUBMISSION,
            ActivityType.CONTENT_VIEW
        }
        return self.activity_type in engagement_activities

@dataclass
class LabUsageMetrics:
    """
    Domain entity for lab usage tracking and analysis
    """
    student_id: str
    course_id: str
    lab_id: str
    session_start: datetime
    session_end: Optional[datetime] = None
    actions_performed: int = 0
    code_executions: int = 0
    errors_encountered: int = 0
    completion_status: CompletionStatus = CompletionStatus.IN_PROGRESS
    final_code: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate lab metrics after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate lab usage metrics business rules"""
        if not self.student_id:
            raise ValueError("Student ID is required")
        
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not self.lab_id:
            raise ValueError("Lab ID is required")
        
        if self.session_start > datetime.utcnow():
            raise ValueError("Session start cannot be in the future")
        
        if self.session_end and self.session_end < self.session_start:
            raise ValueError("Session end cannot be before session start")
        
        if self.actions_performed < 0:
            raise ValueError("Actions performed cannot be negative")
        
        if self.code_executions < 0:
            raise ValueError("Code executions cannot be negative")
        
        if self.errors_encountered < 0:
            raise ValueError("Errors encountered cannot be negative")
    
    def get_duration_minutes(self) -> Optional[int]:
        """Calculate session duration in minutes"""
        if not self.session_end:
            return None
        
        duration = self.session_end - self.session_start
        return int(duration.total_seconds() / 60)
    
    def get_productivity_score(self) -> float:
        """Calculate productivity score based on actions and errors"""
        if self.actions_performed == 0:
            return 0.0
        
        # Base score on actions performed, penalize for errors
        base_score = min(self.actions_performed / 10.0, 10.0)  # Max 10 points for actions
        error_penalty = min(self.errors_encountered * 0.5, base_score * 0.5)  # Max 50% penalty
        
        return max(0.0, base_score - error_penalty)
    
    def get_engagement_level(self) -> str:
        """Determine engagement level based on metrics"""
        duration = self.get_duration_minutes()
        if not duration:
            return "unknown"
        
        if duration < 5:
            return "low"
        elif duration < 30:
            if self.actions_performed >= 10:
                return "high"
            elif self.actions_performed >= 5:
                return "medium"
            else:
                return "low"
        else:  # Long sessions
            actions_per_minute = self.actions_performed / duration
            if actions_per_minute >= 0.5:
                return "high"
            elif actions_per_minute >= 0.2:
                return "medium"
            else:
                return "low"
    
    def end_session(self, final_code: Optional[str] = None) -> None:
        """End the lab session with optional final code"""
        self.session_end = datetime.utcnow()
        self.final_code = final_code
        
        # Determine completion status based on metrics
        if self.actions_performed >= 5 and self.code_executions >= 1:
            self.completion_status = CompletionStatus.COMPLETED
        elif self.actions_performed >= 1:
            self.completion_status = CompletionStatus.IN_PROGRESS
        else:
            self.completion_status = CompletionStatus.ABANDONED

@dataclass
class QuizPerformance:
    """
    Domain entity for quiz performance tracking and analysis
    """
    student_id: str
    course_id: str
    quiz_id: str
    attempt_number: int
    start_time: datetime
    questions_total: int
    end_time: Optional[datetime] = None
    questions_answered: int = 0
    questions_correct: int = 0
    answers: Dict[str, Any] = field(default_factory=dict)
    time_per_question: Dict[str, float] = field(default_factory=dict)
    status: CompletionStatus = CompletionStatus.IN_PROGRESS
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate quiz performance after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate quiz performance business rules"""
        if not self.student_id:
            raise ValueError("Student ID is required")
        
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not self.quiz_id:
            raise ValueError("Quiz ID is required")
        
        if self.attempt_number < 1:
            raise ValueError("Attempt number must be positive")
        
        if self.questions_total < 1:
            raise ValueError("Quiz must have at least one question")
        
        if self.questions_answered > self.questions_total:
            raise ValueError("Questions answered cannot exceed total questions")
        
        if self.questions_correct > self.questions_answered:
            raise ValueError("Correct answers cannot exceed answered questions")
        
        if self.end_time and self.end_time < self.start_time:
            raise ValueError("End time cannot be before start time")
    
    def get_score_percentage(self) -> Optional[float]:
        """Calculate score as percentage"""
        if self.questions_total == 0:
            return None
        
        return (self.questions_correct / self.questions_total) * 100
    
    def get_duration_minutes(self) -> Optional[int]:
        """Calculate quiz duration in minutes"""
        if not self.end_time:
            return None
        
        duration = self.end_time - self.start_time
        return int(duration.total_seconds() / 60)
    
    def get_average_time_per_question(self) -> Optional[float]:
        """Calculate average time per question in seconds"""
        if not self.time_per_question:
            duration = self.get_duration_minutes()
            if duration and self.questions_answered > 0:
                return (duration * 60) / self.questions_answered
            return None
        
        if len(self.time_per_question) == 0:
            return None
        
        return sum(self.time_per_question.values()) / len(self.time_per_question)
    
    def get_performance_level(self) -> str:
        """Determine performance level based on score and completion"""
        score = self.get_score_percentage()
        if not score:
            return "incomplete"
        
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "satisfactory"
        elif score >= 60:
            return "needs_improvement"
        else:
            return "poor"
    
    def is_completed(self) -> bool:
        """Check if quiz is completed"""
        return self.status == CompletionStatus.COMPLETED and self.end_time is not None
    
    def complete_quiz(self) -> None:
        """Mark quiz as completed"""
        self.end_time = datetime.utcnow()
        self.status = CompletionStatus.COMPLETED

@dataclass
class StudentProgress:
    """
    Domain entity for tracking student progress on content items
    """
    student_id: str
    course_id: str
    content_item_id: str
    content_type: ContentType
    status: CompletionStatus = CompletionStatus.NOT_STARTED
    progress_percentage: float = 0.0
    time_spent_minutes: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    completion_date: Optional[datetime] = None
    mastery_score: Optional[float] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate student progress after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate student progress business rules"""
        if not self.student_id:
            raise ValueError("Student ID is required")
        
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not self.content_item_id:
            raise ValueError("Content item ID is required")
        
        if not isinstance(self.content_type, ContentType):
            raise ValueError("Invalid content type")
        
        if not isinstance(self.status, CompletionStatus):
            raise ValueError("Invalid completion status")
        
        if not (0 <= self.progress_percentage <= 100):
            raise ValueError("Progress percentage must be between 0 and 100")
        
        if self.time_spent_minutes < 0:
            raise ValueError("Time spent cannot be negative")
        
        if self.mastery_score is not None and not (0 <= self.mastery_score <= 100):
            raise ValueError("Mastery score must be between 0 and 100")
        
        if self.completion_date and self.completion_date > datetime.utcnow():
            raise ValueError("Completion date cannot be in the future")
    
    def update_progress(self, progress_percentage: float, time_spent_additional: int = 0) -> None:
        """Update progress with validation"""
        if not (0 <= progress_percentage <= 100):
            raise ValueError("Progress percentage must be between 0 and 100")
        
        if time_spent_additional < 0:
            raise ValueError("Additional time spent cannot be negative")
        
        self.progress_percentage = progress_percentage
        self.time_spent_minutes += time_spent_additional
        self.last_accessed = datetime.utcnow()
        
        # Update status based on progress
        if progress_percentage == 0:
            self.status = CompletionStatus.NOT_STARTED
        elif progress_percentage < 100:
            self.status = CompletionStatus.IN_PROGRESS
        else:
            self.status = CompletionStatus.COMPLETED
            if not self.completion_date:
                self.completion_date = datetime.utcnow()
    
    def mark_mastered(self, mastery_score: float) -> None:
        """Mark content as mastered with score"""
        if not (0 <= mastery_score <= 100):
            raise ValueError("Mastery score must be between 0 and 100")
        
        self.status = CompletionStatus.MASTERED
        self.mastery_score = mastery_score
        self.progress_percentage = 100.0
        self.completion_date = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
    
    def get_learning_velocity(self, days_since_start: int) -> float:
        """Calculate learning velocity (progress per day)"""
        if days_since_start <= 0:
            return 0.0
        
        return self.progress_percentage / days_since_start
    
    def is_at_risk(self, expected_progress: float, days_since_start: int) -> bool:
        """Determine if student is at risk based on expected progress"""
        if days_since_start <= 0:
            return False
        
        # Student is at risk if they're significantly behind expected progress
        # and haven't accessed content recently
        days_since_access = (datetime.utcnow() - self.last_accessed).days
        
        return (self.progress_percentage < expected_progress * 0.7 and 
                days_since_access > 3)

@dataclass
class LearningAnalytics:
    """
    Domain entity for comprehensive learning analytics
    Aggregates multiple metrics to provide insights
    """
    student_id: str
    course_id: str
    analysis_date: datetime = field(default_factory=datetime.utcnow)
    engagement_score: float = 0.0
    progress_velocity: float = 0.0
    lab_proficiency: float = 0.0
    quiz_performance: float = 0.0
    time_on_platform: int = 0
    streak_days: int = 0
    risk_level: RiskLevel = RiskLevel.LOW
    recommendations: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate learning analytics after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate learning analytics business rules"""
        if not self.student_id:
            raise ValueError("Student ID is required")
        
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not (0 <= self.engagement_score <= 100):
            raise ValueError("Engagement score must be between 0 and 100")
        
        if self.progress_velocity < 0:
            raise ValueError("Progress velocity cannot be negative")
        
        if not (0 <= self.lab_proficiency <= 100):
            raise ValueError("Lab proficiency must be between 0 and 100")
        
        if not (0 <= self.quiz_performance <= 100):
            raise ValueError("Quiz performance must be between 0 and 100")
        
        if self.time_on_platform < 0:
            raise ValueError("Time on platform cannot be negative")
        
        if self.streak_days < 0:
            raise ValueError("Streak days cannot be negative")
        
        if not isinstance(self.risk_level, RiskLevel):
            raise ValueError("Invalid risk level")
    
    def calculate_overall_performance(self) -> float:
        """Calculate overall performance score"""
        # Weighted average of different metrics
        weights = {
            'engagement': 0.25,
            'progress': 0.25,
            'lab_proficiency': 0.25,
            'quiz_performance': 0.25
        }
        
        # Normalize progress velocity to 0-100 scale (assuming max 10 items per week)
        normalized_velocity = min(self.progress_velocity * 10, 100)
        
        overall_score = (
            self.engagement_score * weights['engagement'] +
            normalized_velocity * weights['progress'] +
            self.lab_proficiency * weights['lab_proficiency'] +
            self.quiz_performance * weights['quiz_performance']
        )
        
        return round(overall_score, 2)
    
    def update_risk_level(self) -> None:
        """Update risk level based on current metrics"""
        overall_performance = self.calculate_overall_performance()
        days_since_analysis = (datetime.utcnow() - self.analysis_date).days
        
        # High risk indicators
        if (overall_performance < 40 or 
            self.engagement_score < 30 or 
            self.streak_days == 0 and days_since_analysis > 7):
            self.risk_level = RiskLevel.CRITICAL
        elif (overall_performance < 60 or 
              self.engagement_score < 50 or 
              self.streak_days < 3):
            self.risk_level = RiskLevel.HIGH
        elif (overall_performance < 75 or 
              self.engagement_score < 70):
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.LOW
    
    def generate_recommendations(self) -> List[str]:
        """Generate personalized recommendations based on analytics"""
        recommendations = []
        
        if self.engagement_score < 50:
            recommendations.append("Increase platform engagement through interactive content")
        
        if self.lab_proficiency < 60:
            recommendations.append("Focus on hands-on coding practice in lab environments")
        
        if self.quiz_performance < 70:
            recommendations.append("Review course materials and retake quizzes for better understanding")
        
        if self.progress_velocity < 1.0:
            recommendations.append("Set a regular study schedule to maintain consistent progress")
        
        if self.streak_days == 0:
            recommendations.append("Establish a daily learning routine to build momentum")
        
        if self.time_on_platform < 60:  # Less than 1 hour per week
            recommendations.append("Increase study time allocation for better learning outcomes")
        
        self.recommendations = recommendations
        return recommendations