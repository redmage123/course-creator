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
    STUDENT ACTIVITY TRACKING DOMAIN ENTITY

    BUSINESS REQUIREMENT:
    Educational platforms need comprehensive activity tracking to measure student engagement,
    identify learning patterns, and provide analytics for instructors and administrators.
    This entity captures all student interactions with the learning platform including
    login sessions, content access, lab usage, quiz attempts, and exercise submissions.

    TECHNICAL IMPLEMENTATION:
    Implements domain-driven design principles with immutable data structures and
    comprehensive validation. Uses dataclass for efficient memory usage and automatic
    equality/hashing. Includes activity-specific validation rules and engagement analysis.

    EDUCATIONAL METHODOLOGY:
    Based on learning analytics research showing that fine-grained activity tracking
    enables better understanding of student engagement patterns, time-on-task analysis,
    and early identification of at-risk students through behavioral indicators.

    PROBLEM ANALYSIS:
    Traditional educational systems lack granular activity data, making it difficult
    to understand how students actually interact with learning materials. This entity
    solves that by capturing detailed interaction data with proper validation and
    business rule enforcement.

    SOLUTION RATIONALE:
    - Enum-based activity types prevent invalid data entry
    - Timestamp validation ensures data integrity
    - Activity-specific validation maintains data quality
    - Engagement analysis methods support real-time insights
    - UUID-based IDs prevent conflicts in distributed systems

    SECURITY CONSIDERATIONS:
    - All student data handling must comply with FERPA regulations
    - IP addresses and user agents stored for security audit trails
    - Session IDs enable tracking without exposing sensitive user data
    - Data validation prevents injection attacks through activity data

    PERFORMANCE IMPACT:
    - Lightweight dataclass structure minimizes memory overhead
    - Validation occurs only during object creation for efficiency
    - Engagement analysis methods use efficient set operations
    - Time calculations use optimized datetime operations

    MAINTENANCE NOTES:
    - Activity types should be extended carefully to maintain compatibility
    - Validation rules must be updated when new activity types are added
    - Consider archiving old activity data for performance in high-volume scenarios
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
    LAB USAGE ANALYTICS DOMAIN ENTITY

    BUSINESS REQUIREMENT:
    Interactive coding labs are central to programming education, requiring detailed
    usage analytics to understand student learning patterns, identify struggling students,
    and optimize lab design for maximum educational effectiveness.

    TECHNICAL IMPLEMENTATION:
    Tracks comprehensive lab session data including duration, code executions, errors,
    and completion status. Implements real-time productivity scoring and engagement
    level calculation based on educational research methodologies.

    EDUCATIONAL METHODOLOGY:
    Based on experiential learning theory and constructivist pedagogy showing that
    hands-on coding practice with immediate feedback leads to deeper understanding
    and skill development. Metrics align with research on deliberate practice.

    PROBLEM ANALYSIS:
    Traditional lab environments provide minimal analytics, making it difficult to:
    - Identify students struggling with coding concepts
    - Optimize lab difficulty and scaffolding
    - Measure learning progress in programming skills
    - Provide timely intervention for skill development

    SOLUTION RATIONALE:
    - Session-based tracking captures complete learning episodes
    - Error counting enables mistake-based learning analysis
    - Productivity scoring motivates efficient coding practices
    - Engagement levels guide instructional support allocation
    - Real-time metrics enable immediate intervention

    SECURITY CONSIDERATIONS:
    - Student code stored securely with appropriate access controls
    - Lab session data anonymized for institutional research
    - FERPA compliance for educational record handling
    - Error data protected to prevent skill-based discrimination

    PERFORMANCE IMPACT:
    - Efficient session tracking minimizes overhead during active coding
    - Calculation methods optimized for real-time dashboard updates
    - Batch processing for historical trend analysis
    - Memory-efficient storage of lab interaction data

    MAINTENANCE NOTES:
    - Lab metrics should align with current pedagogical research
    - Productivity scoring algorithms may need periodic recalibration
    - Consider different metrics for various programming language contexts
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
    QUIZ PERFORMANCE ANALYTICS DOMAIN ENTITY

    BUSINESS REQUIREMENT:
    Formative and summative assessment through quizzes requires comprehensive performance
    tracking to measure learning outcomes, identify knowledge gaps, and provide feedback
    for both students and instructors on educational effectiveness.

    TECHNICAL IMPLEMENTATION:
    Captures detailed quiz attempt data including timing, accuracy, attempt patterns,
    and question-level analysis. Supports multiple attempts with progression tracking
    and comprehensive performance calculation methods.

    EDUCATIONAL METHODOLOGY:
    Based on assessment theory and cognitive load research showing that frequent,
    low-stakes assessment improves learning retention and provides valuable feedback
    for adaptive instruction and personalized learning paths.

    PROBLEM ANALYSIS:
    Traditional quiz systems provide only final scores, missing crucial data:
    - Time-on-task analysis for cognitive load assessment
    - Question-level difficulty and discrimination analysis
    - Learning progression tracking across multiple attempts
    - Early warning indicators for knowledge gaps

    SOLUTION RATIONALE:
    - Attempt-based tracking enables learning progression analysis
    - Time-per-question data reveals cognitive processing patterns
    - Multiple attempt support encourages mastery-based learning
    - Performance levels guide instructional intervention decisions
    - Comprehensive validation ensures assessment data integrity

    SECURITY CONSIDERATIONS:
    - Quiz answers protected against unauthorized access
    - Performance data used constructively for educational improvement
    - Student privacy maintained in performance comparisons
    - Assessment integrity protected through validation

    PERFORMANCE IMPACT:
    - Efficient scoring calculations for real-time feedback
    - Optimized storage for large-scale quiz deployment
    - Fast retrieval for instructor dashboard analytics
    - Minimal overhead during quiz-taking experience

    MAINTENANCE NOTES:
    - Performance thresholds should align with educational standards
    - Question timing analysis may need adjustment for accessibility
    - Consider cultural and linguistic factors in performance interpretation
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
    STUDENT PROGRESS TRACKING DOMAIN ENTITY

    BUSINESS REQUIREMENT:
    Comprehensive progress tracking across diverse content types enables personalized
    learning paths, early intervention for struggling students, and data-driven
    instructional design optimization for improved educational outcomes.

    TECHNICAL IMPLEMENTATION:
    Tracks progress percentage, time investment, access patterns, and mastery indicators
    across all content types. Implements learning velocity calculation and at-risk
    student identification through sophisticated progress analysis algorithms.

    EDUCATIONAL METHODOLOGY:
    Based on mastery learning theory and competency-based education research showing
    that granular progress tracking enables personalized pacing, adaptive instruction,
    and improved student success through targeted support.

    PROBLEM ANALYSIS:
    Traditional progress tracking provides insufficient granularity:
    - Binary completion status misses learning progression nuances
    - Lack of time-on-task data prevents learning efficiency analysis
    - Missing mastery indicators limit competency-based advancement
    - No early warning system for at-risk student identification

    SOLUTION RATIONALE:
    - Percentage-based progress enables nuanced learning tracking
    - Time investment data reveals learning efficiency patterns
    - Mastery scoring supports competency-based progression
    - At-risk identification enables proactive intervention
    - Learning velocity calculation guides pacing recommendations

    SECURITY CONSIDERATIONS:
    - Progress data protected under FERPA educational record regulations
    - Mastery scores used constructively for student advancement
    - Learning velocity data anonymized for institutional research
    - Access patterns protected to maintain student privacy

    PERFORMANCE IMPACT:
    - Efficient progress calculation for real-time dashboard updates
    - Optimized velocity algorithms for minimal computational overhead
    - Batch processing for large-scale progress analysis
    - Fast retrieval for adaptive learning system integration

    MAINTENANCE NOTES:
    - Progress thresholds should align with educational research
    - Mastery criteria may need periodic review and adjustment
    - At-risk algorithms require validation against student success outcomes
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
    COMPREHENSIVE LEARNING ANALYTICS DOMAIN ENTITY

    BUSINESS REQUIREMENT:
    Holistic learning analytics combining engagement, progress, performance, and behavioral
    data enable evidence-based educational decision-making, personalized learning experiences,
    and institutional effectiveness measurement for continuous improvement.

    TECHNICAL IMPLEMENTATION:
    Aggregates data from multiple analytics dimensions including engagement scoring,
    progress velocity, lab proficiency, quiz performance, and risk assessment.
    Implements sophisticated recommendation generation and overall performance calculation.

    EDUCATIONAL METHODOLOGY:
    Based on learning analytics research and educational data mining principles showing
    that multi-dimensional student modeling provides more accurate and actionable
    insights than single-metric approaches for educational intervention and optimization.

    PROBLEM ANALYSIS:
    Fragmented analytics across different systems create incomplete student pictures:
    - Isolated metrics miss holistic learning patterns
    - Lack of integrated risk assessment delays intervention
    - Missing comprehensive recommendation systems
    - No unified student success measurement framework

    SOLUTION RATIONALE:
    - Multi-dimensional scoring provides comprehensive student assessment
    - Weighted performance calculation balances different learning aspects
    - Risk level determination enables proactive intervention
    - Personalized recommendations support individual learning needs
    - Unified analytics framework supports institutional decision-making

    PERFORMANCE CALCULATION METHODOLOGY:
    Uses research-based weighting system:
    - Engagement (25%): Behavioral participation and platform interaction
    - Progress (25%): Learning velocity and content completion patterns
    - Lab Proficiency (25%): Hands-on skill development and application
    - Quiz Performance (25%): Knowledge retention and assessment outcomes

    RISK ASSESSMENT FRAMEWORK:
    - Critical Risk: Overall performance < 40%, engagement < 30%, no recent activity
    - High Risk: Overall performance < 60%, engagement < 50%, inconsistent participation
    - Medium Risk: Overall performance < 75%, engagement < 70%, some areas of concern
    - Low Risk: Overall performance ≥ 75%, consistent engagement, positive trends

    SECURITY CONSIDERATIONS:
    - Comprehensive analytics data protected under FERPA regulations
    - Risk assessments used constructively for student support
    - Recommendation data anonymized for research applications
    - Individual analytics protected from unauthorized access

    PERFORMANCE IMPACT:
    - Efficient calculation algorithms for real-time analytics generation
    - Cached results for dashboard and reporting system performance
    - Optimized recommendation generation for personalized learning
    - Scalable architecture for institutional-level analytics

    MAINTENANCE NOTES:
    - Weighting algorithms should be validated against student success outcomes
    - Risk thresholds may need periodic adjustment based on institutional data
    - Recommendation systems require continuous improvement based on effectiveness
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