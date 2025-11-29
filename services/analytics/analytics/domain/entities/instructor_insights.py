"""
Instructor Insights Domain Entities

What: Domain entities for comprehensive instructor analytics including
      effectiveness metrics, course performance, student engagement,
      content ratings, reviews, workload, and improvement recommendations.

Where: Analytics domain layer for instructor-focused analytics.

Why: Provides instructors with actionable insights to:
     1. Measure teaching effectiveness across multiple dimensions
     2. Track student engagement and performance per course
     3. Receive AI-generated improvement recommendations
     4. Set and track personal improvement goals
     5. Compare performance with peer benchmarks (anonymized)
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


# ============================================================================
# ENUMS
# ============================================================================

class Trend(Enum):
    """
    What: Direction of metric change over time.
    Where: Used in effectiveness and engagement metrics.
    Why: Visual indicator for instructors to understand trajectory.
    """
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class CapacityStatus(Enum):
    """
    What: Instructor workload capacity status.
    Where: Teaching load calculations.
    Why: Helps manage instructor assignments and prevent burnout.
    """
    AVAILABLE = "available"
    MODERATE = "moderate"
    HIGH = "high"
    OVERLOADED = "overloaded"


class RecommendationPriority(Enum):
    """
    What: Priority level for improvement recommendations.
    Where: AI-generated recommendations.
    Why: Helps instructors focus on high-impact improvements first.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationStatus(Enum):
    """
    What: Status of an improvement recommendation.
    Where: Recommendation tracking.
    Why: Tracks instructor engagement with recommendations.
    """
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class GoalStatus(Enum):
    """
    What: Status of instructor improvement goals.
    Where: Goal tracking system.
    Why: Enables personal development tracking.
    """
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FeedbackSentiment(Enum):
    """
    What: Sentiment analysis result for student feedback.
    Where: Content ratings and reviews.
    Why: Quick categorization for analysis.
    """
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class RecommendationCategory(Enum):
    """
    What: Categories of improvement recommendations.
    Where: Recommendation filtering and organization.
    Why: Allows instructors to focus on specific improvement areas.
    """
    ENGAGEMENT = "engagement"
    CONTENT_QUALITY = "content_quality"
    RESPONSIVENESS = "responsiveness"
    ASSESSMENT = "assessment"
    COMMUNICATION = "communication"
    ORGANIZATION = "organization"
    ACCESSIBILITY = "accessibility"
    TECHNICAL = "technical"


class MetricCategory(Enum):
    """
    What: Categories for peer comparison metrics.
    Where: Comparative analytics.
    Why: Organizes peer comparisons by area.
    """
    TEACHING_QUALITY = "teaching_quality"
    STUDENT_OUTCOMES = "student_outcomes"
    ENGAGEMENT = "engagement"
    RESPONSIVENESS = "responsiveness"
    CONTENT = "content"
    SATISFACTION = "satisfaction"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class InstructorEffectivenessMetrics:
    """
    What: Core teaching effectiveness scores for an instructor.
    Where: Primary instructor analytics dashboard.
    Why: Aggregates key performance indicators for teaching quality.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Core metrics (0-100 scale for scores, 0-5 for ratings)
    overall_rating: Optional[Decimal] = None
    teaching_quality_score: Optional[Decimal] = None
    content_clarity_score: Optional[Decimal] = None
    engagement_score: Optional[Decimal] = None
    responsiveness_score: Optional[Decimal] = None

    # Derived metrics
    total_students_taught: int = 0
    course_completion_rate: Optional[Decimal] = None
    average_quiz_score: Optional[Decimal] = None
    student_retention_rate: Optional[Decimal] = None

    # Trends
    rating_trend: Optional[Trend] = None
    engagement_trend: Optional[Trend] = None

    # Period tracking
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Timestamps
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate metrics after initialization."""
        if self.overall_rating is not None:
            if not (Decimal("0") <= self.overall_rating <= Decimal("5")):
                raise ValueError("Overall rating must be between 0 and 5")

        score_fields = [
            'teaching_quality_score', 'content_clarity_score',
            'engagement_score', 'responsiveness_score',
            'course_completion_rate', 'student_retention_rate'
        ]
        for field_name in score_fields:
            value = getattr(self, field_name)
            if value is not None:
                if not (Decimal("0") <= value <= Decimal("100")):
                    raise ValueError(f"{field_name} must be between 0 and 100")

        if self.period_end < self.period_start:
            raise ValueError("Period end must not be before period start")

    def calculate_composite_score(self) -> Optional[Decimal]:
        """
        What: Calculate weighted composite effectiveness score.
        Where: Overall instructor scoring.
        Why: Single metric for quick assessment.
        """
        weights = {
            'teaching_quality_score': Decimal("0.30"),
            'content_clarity_score': Decimal("0.25"),
            'engagement_score': Decimal("0.25"),
            'responsiveness_score': Decimal("0.20"),
        }

        total_weight = Decimal("0")
        weighted_sum = Decimal("0")

        for field_name, weight in weights.items():
            value = getattr(self, field_name)
            if value is not None:
                weighted_sum += value * weight
                total_weight += weight

        if total_weight == 0:
            return None

        return weighted_sum / total_weight


@dataclass
class InstructorCoursePerformance:
    """
    What: Per-course performance analytics for an instructor.
    Where: Course-specific analytics views.
    Why: Enables course-by-course performance analysis.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    course_id: UUID = field(default_factory=uuid4)
    course_instance_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None

    # Enrollment metrics
    total_enrolled: int = 0
    active_students: int = 0
    completed_students: int = 0
    dropped_students: int = 0

    # Performance metrics
    average_score: Optional[Decimal] = None
    median_score: Optional[Decimal] = None
    score_std_deviation: Optional[Decimal] = None
    pass_rate: Optional[Decimal] = None

    # Engagement metrics
    average_time_to_complete: Optional[timedelta] = None
    content_views_per_student: Optional[Decimal] = None
    lab_completions_per_student: Optional[Decimal] = None
    quiz_attempts_per_student: Optional[Decimal] = None

    # Quality ratings (1-5 scale)
    content_rating: Optional[Decimal] = None
    difficulty_rating: Optional[Decimal] = None
    workload_rating: Optional[Decimal] = None

    # Period
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Timestamps
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate course performance data."""
        if self.pass_rate is not None:
            if not (Decimal("0") <= self.pass_rate <= Decimal("100")):
                raise ValueError("Pass rate must be between 0 and 100")

        rating_fields = ['content_rating', 'difficulty_rating', 'workload_rating']
        for field_name in rating_fields:
            value = getattr(self, field_name)
            if value is not None:
                if not (Decimal("0") <= value <= Decimal("5")):
                    raise ValueError(f"{field_name} must be between 0 and 5")

    def get_completion_rate(self) -> Optional[Decimal]:
        """
        What: Calculate course completion rate.
        Where: Course performance summary.
        Why: Key metric for course effectiveness.
        """
        if self.total_enrolled == 0:
            return None
        return Decimal(self.completed_students) / Decimal(self.total_enrolled) * 100

    def get_dropout_rate(self) -> Optional[Decimal]:
        """
        What: Calculate student dropout rate.
        Where: Retention analysis.
        Why: Identifies courses needing intervention.
        """
        if self.total_enrolled == 0:
            return None
        return Decimal(self.dropped_students) / Decimal(self.total_enrolled) * 100


@dataclass
class InstructorStudentEngagement:
    """
    What: Aggregated student engagement metrics per instructor.
    Where: Engagement analytics dashboard.
    Why: Measures overall student interaction levels.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Session metrics
    total_sessions: int = 0
    total_session_duration: Optional[timedelta] = None
    average_session_duration: Optional[timedelta] = None
    peak_hour: Optional[int] = None  # 0-23

    # Interaction metrics
    total_content_views: int = 0
    total_lab_sessions: int = 0
    total_quiz_attempts: int = 0
    total_forum_posts: int = 0
    total_questions_asked: int = 0

    # Response metrics
    questions_answered: int = 0
    average_response_time: Optional[timedelta] = None

    # Engagement patterns (JSON)
    most_active_day: Optional[str] = None
    engagement_distribution: dict[str, Any] = field(default_factory=dict)
    activity_heatmap: dict[str, Any] = field(default_factory=dict)

    # Period
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Timestamps
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate engagement data."""
        if self.peak_hour is not None:
            if not (0 <= self.peak_hour <= 23):
                raise ValueError("Peak hour must be between 0 and 23")

    def get_response_rate(self) -> Optional[Decimal]:
        """
        What: Calculate question response rate.
        Where: Responsiveness metrics.
        Why: Measures instructor availability.
        """
        if self.total_questions_asked == 0:
            return None
        return Decimal(self.questions_answered) / Decimal(self.total_questions_asked) * 100


@dataclass
class ContentRating:
    """
    What: Student rating on specific instructor content.
    Where: Content quality tracking.
    Why: Identifies strong and weak content areas.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    course_id: UUID = field(default_factory=uuid4)
    content_id: UUID = field(default_factory=uuid4)
    content_type: str = ""
    student_id: UUID = field(default_factory=uuid4)

    # Ratings (1-5 scale)
    clarity_rating: Optional[int] = None
    helpfulness_rating: Optional[int] = None
    relevance_rating: Optional[int] = None
    difficulty_rating: Optional[int] = None

    # Feedback
    feedback_text: Optional[str] = None
    feedback_sentiment: Optional[FeedbackSentiment] = None

    # Metadata
    is_anonymous: bool = False
    is_verified_enrollment: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate ratings."""
        rating_fields = [
            'clarity_rating', 'helpfulness_rating',
            'relevance_rating', 'difficulty_rating'
        ]
        for field_name in rating_fields:
            value = getattr(self, field_name)
            if value is not None:
                if not (1 <= value <= 5):
                    raise ValueError(f"{field_name} must be between 1 and 5")

    def get_average_rating(self) -> Optional[Decimal]:
        """
        What: Calculate average across all dimensions.
        Where: Content summary views.
        Why: Single metric for content quality.
        """
        ratings = [
            self.clarity_rating, self.helpfulness_rating,
            self.relevance_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        if not valid_ratings:
            return None
        return Decimal(sum(valid_ratings)) / Decimal(len(valid_ratings))


@dataclass
class InstructorReview:
    """
    What: Overall instructor review from a student.
    Where: Instructor review section.
    Why: Captures comprehensive feedback on instructor.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    course_id: Optional[UUID] = None
    student_id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Overall rating (required)
    overall_rating: int = 3

    # Dimension ratings (1-5 scale)
    knowledge_rating: Optional[int] = None
    communication_rating: Optional[int] = None
    availability_rating: Optional[int] = None
    feedback_quality_rating: Optional[int] = None
    organization_rating: Optional[int] = None

    # Review content
    review_title: Optional[str] = None
    review_text: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None

    # Moderation
    is_approved: bool = False
    is_flagged: bool = False
    flagged_reason: Optional[str] = None
    moderated_by: Optional[UUID] = None
    moderated_at: Optional[datetime] = None

    # Helpful votes
    helpful_count: int = 0
    not_helpful_count: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate review data."""
        if not (1 <= self.overall_rating <= 5):
            raise ValueError("Overall rating must be between 1 and 5")

        optional_ratings = [
            'knowledge_rating', 'communication_rating', 'availability_rating',
            'feedback_quality_rating', 'organization_rating'
        ]
        for field_name in optional_ratings:
            value = getattr(self, field_name)
            if value is not None:
                if not (1 <= value <= 5):
                    raise ValueError(f"{field_name} must be between 1 and 5")

    def get_helpfulness_score(self) -> Optional[Decimal]:
        """
        What: Calculate helpfulness score from votes.
        Where: Review sorting.
        Why: Surface most helpful reviews.
        """
        total_votes = self.helpful_count + self.not_helpful_count
        if total_votes == 0:
            return None
        return Decimal(self.helpful_count) / Decimal(total_votes) * 100


@dataclass
class InstructorTeachingLoad:
    """
    What: Instructor workload and capacity metrics.
    Where: Workload management dashboard.
    Why: Prevents overloading and optimizes assignments.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Course load
    active_courses: int = 0
    total_courses_taught: int = 0
    courses_this_period: int = 0

    # Student load
    current_students: int = 0
    total_students_capacity: Optional[int] = None
    student_load_percentage: Optional[Decimal] = None

    # Time allocation (hours per week)
    teaching_hours_per_week: Optional[Decimal] = None
    grading_hours_per_week: Optional[Decimal] = None
    support_hours_per_week: Optional[Decimal] = None
    content_creation_hours_per_week: Optional[Decimal] = None

    # Pending work
    assignments_pending_grading: int = 0
    questions_pending_response: int = 0
    estimated_pending_hours: Optional[Decimal] = None

    # Status
    capacity_status: CapacityStatus = CapacityStatus.AVAILABLE
    recommended_action: Optional[str] = None

    # Period
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Timestamps
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def get_total_weekly_hours(self) -> Decimal:
        """
        What: Calculate total weekly hours commitment.
        Where: Workload summary.
        Why: Overall time investment metric.
        """
        hours = [
            self.teaching_hours_per_week or Decimal("0"),
            self.grading_hours_per_week or Decimal("0"),
            self.support_hours_per_week or Decimal("0"),
            self.content_creation_hours_per_week or Decimal("0"),
        ]
        return sum(hours, Decimal("0"))

    def calculate_capacity_status(self) -> CapacityStatus:
        """
        What: Calculate capacity status based on load.
        Where: Status determination.
        Why: Automatic status updates based on metrics.
        """
        if self.total_students_capacity and self.current_students:
            load_pct = Decimal(self.current_students) / Decimal(self.total_students_capacity) * 100
            if load_pct >= 100:
                return CapacityStatus.OVERLOADED
            elif load_pct >= 85:
                return CapacityStatus.HIGH
            elif load_pct >= 60:
                return CapacityStatus.MODERATE
        return CapacityStatus.AVAILABLE


@dataclass
class InstructorResponseMetrics:
    """
    What: Response time metrics for grading and questions.
    Where: Responsiveness tracking.
    Why: Measures instructor availability and timeliness.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Grading response times
    avg_grading_time: Optional[timedelta] = None
    median_grading_time: Optional[timedelta] = None
    grading_sla_compliance: Optional[Decimal] = None
    assignments_graded: int = 0
    assignments_overdue: int = 0

    # Question response times
    avg_question_response_time: Optional[timedelta] = None
    median_question_response_time: Optional[timedelta] = None
    question_sla_compliance: Optional[Decimal] = None
    questions_answered: int = 0
    questions_unanswered: int = 0

    # Feedback metrics
    avg_feedback_time: Optional[timedelta] = None
    feedback_quality_score: Optional[Decimal] = None

    # Communication metrics
    messages_sent: int = 0
    announcements_made: int = 0
    forum_participation_rate: Optional[Decimal] = None

    # Period
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Timestamps
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate compliance percentages."""
        compliance_fields = ['grading_sla_compliance', 'question_sla_compliance', 'feedback_quality_score']
        for field_name in compliance_fields:
            value = getattr(self, field_name)
            if value is not None:
                if not (Decimal("0") <= value <= Decimal("100")):
                    raise ValueError(f"{field_name} must be between 0 and 100")

    def get_overall_responsiveness_score(self) -> Optional[Decimal]:
        """
        What: Calculate overall responsiveness score.
        Where: Summary metrics.
        Why: Single metric for responsiveness.
        """
        scores = [
            self.grading_sla_compliance,
            self.question_sla_compliance,
        ]
        valid_scores = [s for s in scores if s is not None]
        if not valid_scores:
            return None
        return sum(valid_scores) / Decimal(len(valid_scores))


@dataclass
class InstructorRecommendation:
    """
    What: AI-generated improvement recommendation.
    Where: Recommendations dashboard.
    Why: Actionable insights for continuous improvement.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    course_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None

    # Recommendation details
    recommendation_type: str = ""
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    category: RecommendationCategory = RecommendationCategory.ENGAGEMENT

    # Content
    title: str = ""
    description: str = ""
    action_items: list[str] = field(default_factory=list)
    expected_impact: Optional[str] = None
    estimated_effort: Optional[str] = None

    # Source data
    based_on_metrics: dict[str, Any] = field(default_factory=dict)
    comparison_data: dict[str, Any] = field(default_factory=dict)

    # Status tracking
    status: RecommendationStatus = RecommendationStatus.PENDING
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dismissed_reason: Optional[str] = None

    # Effectiveness
    outcome_measured: bool = False
    outcome_data: Optional[dict[str, Any]] = None

    # Timestamps
    generated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate recommendation data."""
        if not self.title:
            raise ValueError("Recommendation title is required")
        if not self.description:
            raise ValueError("Recommendation description is required")

    def is_expired(self) -> bool:
        """Check if recommendation has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def acknowledge(self) -> None:
        """Mark recommendation as acknowledged."""
        self.status = RecommendationStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, outcome_data: Optional[dict[str, Any]] = None) -> None:
        """Mark recommendation as completed."""
        self.status = RecommendationStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if outcome_data:
            self.outcome_measured = True
            self.outcome_data = outcome_data
        self.updated_at = datetime.utcnow()

    def dismiss(self, reason: str) -> None:
        """Dismiss the recommendation."""
        self.status = RecommendationStatus.DISMISSED
        self.dismissed_reason = reason
        self.updated_at = datetime.utcnow()


@dataclass
class InstructorPeerComparison:
    """
    What: Anonymized peer comparison metrics.
    Where: Benchmarking views.
    Why: Context for personal performance.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None
    comparison_group: str = ""

    # Instructor's metrics
    instructor_score: Optional[Decimal] = None

    # Peer metrics (anonymized)
    peer_average: Optional[Decimal] = None
    peer_median: Optional[Decimal] = None
    peer_min: Optional[Decimal] = None
    peer_max: Optional[Decimal] = None
    peer_std_deviation: Optional[Decimal] = None

    # Percentile ranking
    percentile_rank: Optional[int] = None

    # Metric details
    metric_name: str = ""
    metric_category: MetricCategory = MetricCategory.TEACHING_QUALITY
    sample_size: Optional[int] = None

    # Period
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Timestamps
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate comparison data."""
        if self.percentile_rank is not None:
            if not (0 <= self.percentile_rank <= 100):
                raise ValueError("Percentile rank must be between 0 and 100")

    def get_position_description(self) -> str:
        """
        What: Get human-readable position description.
        Where: UI display.
        Why: Clear communication of standing.
        """
        if self.percentile_rank is None:
            return "Unknown"
        if self.percentile_rank >= 90:
            return "Top 10%"
        elif self.percentile_rank >= 75:
            return "Top 25%"
        elif self.percentile_rank >= 50:
            return "Above Average"
        elif self.percentile_rank >= 25:
            return "Below Average"
        else:
            return "Bottom 25%"


@dataclass
class InstructorGoal:
    """
    What: Personal improvement goal set by instructor.
    Where: Goal tracking dashboard.
    Why: Enables structured professional development.
    """
    id: UUID = field(default_factory=uuid4)
    instructor_id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Goal details
    goal_type: str = ""
    title: str = ""
    description: Optional[str] = None

    # Target metrics
    metric_name: str = ""
    baseline_value: Optional[Decimal] = None
    target_value: Decimal = Decimal("0")
    current_value: Optional[Decimal] = None

    # Progress
    progress_percentage: Decimal = Decimal("0")

    # Timeline
    start_date: date = field(default_factory=date.today)
    target_date: date = field(default_factory=date.today)
    completed_date: Optional[date] = None

    # Status
    status: GoalStatus = GoalStatus.ACTIVE

    # Notes
    milestones: list[dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate goal data."""
        if not self.title:
            raise ValueError("Goal title is required")
        if self.target_date < self.start_date:
            raise ValueError("Target date must not be before start date")
        if not (Decimal("0") <= self.progress_percentage <= Decimal("100")):
            raise ValueError("Progress percentage must be between 0 and 100")

    def calculate_progress(self) -> Decimal:
        """
        What: Calculate progress towards goal.
        Where: Progress tracking.
        Why: Automatic progress calculation.
        """
        if self.baseline_value is None or self.current_value is None:
            return self.progress_percentage

        if self.target_value == self.baseline_value:
            return Decimal("100") if self.current_value >= self.target_value else Decimal("0")

        progress = (self.current_value - self.baseline_value) / (self.target_value - self.baseline_value) * 100
        return max(Decimal("0"), min(Decimal("100"), progress))

    def days_remaining(self) -> int:
        """Get days remaining until target date."""
        remaining = self.target_date - date.today()
        return max(0, remaining.days)

    def is_overdue(self) -> bool:
        """Check if goal is overdue."""
        return date.today() > self.target_date and self.status == GoalStatus.ACTIVE

    def complete(self) -> None:
        """Mark goal as completed."""
        self.status = GoalStatus.COMPLETED
        self.completed_date = date.today()
        self.progress_percentage = Decimal("100")
        self.updated_at = datetime.utcnow()

    def add_milestone(self, title: str, target_value: Decimal, achieved: bool = False) -> None:
        """Add a milestone to the goal."""
        milestone = {
            "title": title,
            "target_value": str(target_value),
            "achieved": achieved,
            "achieved_at": datetime.utcnow().isoformat() if achieved else None
        }
        self.milestones.append(milestone)
        self.updated_at = datetime.utcnow()
