"""
WHAT: Domain entities for Adaptive Learning Paths system
WHERE: Used by AdaptiveLearningService, LearningPathDAO, and learning path API endpoints
WHY: Provides rich domain models for personalized learning journeys with
     prerequisite enforcement, progress tracking, and adaptive recommendations

This module implements the core domain logic for adaptive learning paths,
enabling students to receive personalized learning experiences based on
their performance, pace, and learning goals.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


class PathType(str, Enum):
    """
    WHAT: Classification of learning path types
    WHERE: Used in LearningPath entity to categorize path purpose
    WHY: Enables different handling logic based on path origin and intent
    """
    RECOMMENDED = "recommended"  # AI-suggested optimal path
    CUSTOM = "custom"            # Student-created custom path
    MANDATORY = "mandatory"      # Organization-required path
    REMEDIAL = "remedial"        # Path for struggling students
    ACCELERATED = "accelerated"  # Fast-track for advanced students


class DifficultyLevel(str, Enum):
    """
    WHAT: Difficulty levels for learning content and paths
    WHERE: Used in LearningPath and LearningPathNode entities
    WHY: Supports adaptive difficulty adjustment based on performance
    """
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ADAPTIVE = "adaptive"  # Dynamically adjusted


class PathStatus(str, Enum):
    """
    WHAT: Lifecycle status of a learning path
    WHERE: Used in LearningPath entity for state management
    WHY: Tracks progression through path lifecycle for reporting and logic
    """
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class NodeStatus(str, Enum):
    """
    WHAT: Status of individual nodes within a learning path
    WHERE: Used in LearningPathNode entity
    WHY: Enables granular progress tracking and prerequisite unlocking
    """
    LOCKED = "locked"          # Prerequisites not met
    AVAILABLE = "available"    # Ready to start
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"        # Bypassed (optional content)
    FAILED = "failed"          # Failed assessment, needs retry


class ContentType(str, Enum):
    """
    WHAT: Types of learning content that can be in a path
    WHERE: Used in LearningPathNode and PrerequisiteRule entities
    WHY: Enables polymorphic content handling in learning paths
    """
    COURSE = "course"
    MODULE = "module"
    LESSON = "lesson"
    QUIZ = "quiz"
    LAB = "lab"
    ASSESSMENT = "assessment"
    MILESTONE = "milestone"


class RequirementType(str, Enum):
    """
    WHAT: Types of requirements for prerequisite completion
    WHERE: Used in PrerequisiteRule entity
    WHY: Supports flexible prerequisite validation logic
    """
    COMPLETION = "completion"      # Simply complete the content
    MINIMUM_SCORE = "minimum_score"  # Achieve minimum score
    TIME_SPENT = "time_spent"      # Spend minimum time
    MASTERY_LEVEL = "mastery_level"  # Achieve mastery level


class MasteryLevel(str, Enum):
    """
    WHAT: Levels of mastery for skill tracking
    WHERE: Used in StudentMasteryLevel entity
    WHY: Enables fine-grained skill progression tracking
    """
    NOVICE = "novice"           # 0-20%
    BEGINNER = "beginner"       # 20-40%
    INTERMEDIATE = "intermediate"  # 40-60%
    PROFICIENT = "proficient"   # 60-80%
    EXPERT = "expert"           # 80-95%
    MASTER = "master"           # 95-100%

    @classmethod
    def from_score(cls, score: Decimal) -> "MasteryLevel":
        """
        WHAT: Converts a numeric score to mastery level
        WHERE: Called when updating mastery based on assessment results
        WHY: Provides consistent mastery level determination
        """
        if score >= 95:
            return cls.MASTER
        elif score >= 80:
            return cls.EXPERT
        elif score >= 60:
            return cls.PROFICIENT
        elif score >= 40:
            return cls.INTERMEDIATE
        elif score >= 20:
            return cls.BEGINNER
        else:
            return cls.NOVICE


class RecommendationType(str, Enum):
    """
    WHAT: Types of adaptive recommendations
    WHERE: Used in AdaptiveRecommendation entity
    WHY: Categorizes recommendations for appropriate handling and display
    """
    NEXT_CONTENT = "next_content"
    REVIEW_CONTENT = "review_content"
    SKIP_CONTENT = "skip_content"
    ADJUST_DIFFICULTY = "adjust_difficulty"
    TAKE_BREAK = "take_break"
    PRACTICE_MORE = "practice_more"
    SEEK_HELP = "seek_help"
    ACCELERATE = "accelerate"
    REMEDIATION = "remediation"


class RecommendationStatus(str, Enum):
    """
    WHAT: Status of an adaptive recommendation
    WHERE: Used in AdaptiveRecommendation entity
    WHY: Tracks recommendation lifecycle and student interaction
    """
    PENDING = "pending"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    COMPLETED = "completed"
    EXPIRED = "expired"


@dataclass
class PrerequisiteRule:
    """
    WHAT: Defines prerequisite relationships between learning content
    WHERE: Used by PrerequisiteService to validate content access
    WHY: Enforces learning sequence requirements ensuring students have
         necessary foundational knowledge before advancing

    Business Rules:
    - Mandatory prerequisites must be completed before target content unlocks
    - Non-mandatory prerequisites generate warnings but allow bypass
    - Requirement types enable flexible completion criteria
    """
    id: UUID
    target_type: ContentType
    target_id: UUID
    prerequisite_type: ContentType
    prerequisite_id: UUID
    requirement_type: RequirementType = RequirementType.COMPLETION
    requirement_value: Optional[Decimal] = None
    organization_id: Optional[UUID] = None
    track_id: Optional[UUID] = None
    is_mandatory: bool = True
    bypass_allowed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None

    def is_met(self, completion_status: bool, score: Optional[Decimal] = None,
               time_spent: Optional[int] = None, mastery: Optional[MasteryLevel] = None) -> bool:
        """
        WHAT: Checks if this prerequisite requirement is satisfied
        WHERE: Called by PrerequisiteService.check_prerequisites()
        WHY: Centralizes prerequisite validation logic with support for
             multiple requirement types

        Args:
            completion_status: Whether the prerequisite content was completed
            score: Score achieved (if applicable)
            time_spent: Time spent in minutes (if applicable)
            mastery: Current mastery level (if applicable)

        Returns:
            True if prerequisite is satisfied, False otherwise
        """
        if not completion_status:
            return False

        if self.requirement_type == RequirementType.COMPLETION:
            return True

        if self.requirement_type == RequirementType.MINIMUM_SCORE:
            if score is None or self.requirement_value is None:
                return False
            return score >= self.requirement_value

        if self.requirement_type == RequirementType.TIME_SPENT:
            if time_spent is None or self.requirement_value is None:
                return False
            return time_spent >= int(self.requirement_value)

        if self.requirement_type == RequirementType.MASTERY_LEVEL:
            if mastery is None or self.requirement_value is None:
                return False
            mastery_scores = {
                MasteryLevel.NOVICE: 0, MasteryLevel.BEGINNER: 20,
                MasteryLevel.INTERMEDIATE: 40, MasteryLevel.PROFICIENT: 60,
                MasteryLevel.EXPERT: 80, MasteryLevel.MASTER: 95
            }
            return mastery_scores.get(mastery, 0) >= int(self.requirement_value)

        return False


@dataclass
class LearningPathNode:
    """
    WHAT: Individual step within a learning path
    WHERE: Used within LearningPath entity, managed by LearningPathService
    WHY: Enables granular progress tracking and flexible path composition
         with support for branching and conditional unlocking

    Business Rules:
    - Nodes unlock when prerequisites are met
    - Progress auto-updates parent path
    - Difficulty can be adjusted per-node based on performance
    """
    id: UUID
    learning_path_id: UUID
    content_type: ContentType
    content_id: UUID
    sequence_order: int
    status: NodeStatus = NodeStatus.LOCKED
    parent_node_id: Optional[UUID] = None
    is_required: bool = True
    is_unlocked: bool = False
    progress_percentage: Decimal = Decimal("0.00")
    score: Optional[Decimal] = None
    attempts: int = 0
    max_attempts: Optional[int] = None
    estimated_duration_minutes: Optional[int] = None
    actual_duration_minutes: int = 0
    time_spent_seconds: int = 0
    difficulty_adjustment: Decimal = Decimal("0.00")
    was_recommended: bool = False
    recommendation_reason: Optional[str] = None
    unlock_conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def start(self) -> None:
        """
        WHAT: Marks the node as started
        WHERE: Called when student begins working on this content
        WHY: Tracks engagement timing for analytics and pacing
        """
        if self.status == NodeStatus.LOCKED:
            raise NodeNotUnlockedException(
                f"Cannot start locked node {self.id}"
            )
        self.status = NodeStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_progress(self, progress: Decimal, score: Optional[Decimal] = None) -> None:
        """
        WHAT: Updates node progress and optionally score
        WHERE: Called by progress tracking service
        WHY: Maintains accurate progress state with auto-completion

        Args:
            progress: New progress percentage (0-100)
            score: Optional score if this is an assessment
        """
        if progress < 0 or progress > 100:
            raise InvalidProgressException(
                f"Progress must be between 0 and 100, got {progress}"
            )

        self.progress_percentage = progress
        if score is not None:
            self.score = score
        self.updated_at = datetime.utcnow()

        if progress >= 100:
            self.complete()

    def complete(self, score: Optional[Decimal] = None) -> None:
        """
        WHAT: Marks the node as completed
        WHERE: Called when student finishes content or assessment
        WHY: Triggers unlock of dependent nodes and path progress update
        """
        self.status = NodeStatus.COMPLETED
        self.progress_percentage = Decimal("100.00")
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if score is not None:
            self.score = score

    def skip(self) -> None:
        """
        WHAT: Marks optional node as skipped
        WHERE: Called when student chooses to bypass optional content
        WHY: Allows progression without completing non-required content
        """
        if self.is_required:
            raise CannotSkipRequiredNodeException(
                f"Cannot skip required node {self.id}"
            )
        self.status = NodeStatus.SKIPPED
        self.updated_at = datetime.utcnow()

    def fail(self) -> None:
        """
        WHAT: Marks node as failed (for assessments)
        WHERE: Called when student fails an assessment
        WHY: Triggers remediation recommendations
        """
        self.status = NodeStatus.FAILED
        self.attempts += 1
        self.updated_at = datetime.utcnow()

    def unlock(self) -> None:
        """
        WHAT: Unlocks the node making it available to start
        WHERE: Called when prerequisites are satisfied
        WHY: Controls content access based on prerequisite completion
        """
        self.status = NodeStatus.AVAILABLE
        self.is_unlocked = True
        self.updated_at = datetime.utcnow()

    def can_retry(self) -> bool:
        """
        WHAT: Checks if failed node can be retried
        WHERE: Called before allowing retry attempt
        WHY: Enforces attempt limits if configured
        """
        if self.max_attempts is None:
            return True
        return self.attempts < self.max_attempts

    def add_time(self, seconds: int) -> None:
        """
        WHAT: Adds time spent on this node
        WHERE: Called by activity tracking service
        WHY: Tracks engagement for analytics and pacing recommendations
        """
        self.time_spent_seconds += seconds
        self.actual_duration_minutes = self.time_spent_seconds // 60
        self.updated_at = datetime.utcnow()


@dataclass
class LearningPath:
    """
    WHAT: Personalized learning journey for a student
    WHERE: Created by AdaptiveLearningService, displayed in student dashboard
    WHY: Provides students with customized learning experiences based on
         goals, performance, pace, and learning style

    Business Rules:
    - Paths auto-adapt based on student performance when adapt_to_performance=True
    - Pacing adjusts based on learning velocity when adapt_to_pace=True
    - Progress automatically calculated from node completion
    """
    id: UUID
    student_id: UUID
    name: str
    organization_id: Optional[UUID] = None
    track_id: Optional[UUID] = None
    description: Optional[str] = None
    path_type: PathType = PathType.RECOMMENDED
    difficulty_level: DifficultyLevel = DifficultyLevel.ADAPTIVE
    status: PathStatus = PathStatus.ACTIVE
    overall_progress: Decimal = Decimal("0.00")
    estimated_duration_hours: Optional[int] = None
    actual_duration_hours: int = 0
    total_nodes: int = 0
    completed_nodes: int = 0
    current_node_id: Optional[UUID] = None
    adapt_to_performance: bool = True
    adapt_to_pace: bool = True
    target_completion_date: Optional[date] = None
    recommendation_confidence: Optional[Decimal] = None
    last_adaptation_at: Optional[datetime] = None
    adaptation_count: int = 0
    nodes: List[LearningPathNode] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def add_node(self, node: LearningPathNode) -> None:
        """
        WHAT: Adds a node to the learning path
        WHERE: Called when building or modifying a path
        WHY: Maintains node collection with automatic ordering
        """
        node.learning_path_id = self.id
        self.nodes.append(node)
        self.total_nodes = len(self.nodes)
        self._reorder_nodes()
        self.updated_at = datetime.utcnow()

    def remove_node(self, node_id: UUID) -> None:
        """
        WHAT: Removes a node from the learning path
        WHERE: Called during path adaptation or manual editing
        WHY: Allows dynamic path modification
        """
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.total_nodes = len(self.nodes)
        self._reorder_nodes()
        self.updated_at = datetime.utcnow()

    def _reorder_nodes(self) -> None:
        """
        WHAT: Resequences nodes after modification
        WHERE: Called after add/remove operations
        WHY: Maintains consistent ordering
        """
        for i, node in enumerate(sorted(self.nodes, key=lambda n: n.sequence_order)):
            node.sequence_order = i + 1

    def start(self) -> None:
        """
        WHAT: Starts the learning path
        WHERE: Called when student begins their journey
        WHY: Initializes path state and unlocks first node(s)
        """
        if self.status != PathStatus.DRAFT and self.status != PathStatus.PAUSED:
            raise InvalidPathStateException(
                f"Cannot start path in status {self.status}"
            )
        self.status = PathStatus.ACTIVE
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Unlock first available nodes (those without prerequisites)
        for node in self.nodes:
            if node.sequence_order == 1 or not node.unlock_conditions:
                node.unlock()
                if self.current_node_id is None:
                    self.current_node_id = node.id
                break

    def pause(self) -> None:
        """
        WHAT: Pauses the learning path
        WHERE: Called when student needs a break
        WHY: Preserves progress while marking path as inactive
        """
        if self.status != PathStatus.ACTIVE:
            raise InvalidPathStateException(
                f"Cannot pause path in status {self.status}"
            )
        self.status = PathStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume(self) -> None:
        """
        WHAT: Resumes a paused learning path
        WHERE: Called when student returns to continue
        WHY: Reactivates path maintaining previous progress
        """
        if self.status != PathStatus.PAUSED:
            raise InvalidPathStateException(
                f"Cannot resume path in status {self.status}"
            )
        self.status = PathStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """
        WHAT: Marks the learning path as completed
        WHERE: Called when all required nodes are completed
        WHY: Finalizes path and triggers completion handlers
        """
        self.status = PathStatus.COMPLETED
        self.overall_progress = Decimal("100.00")
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def abandon(self) -> None:
        """
        WHAT: Marks the learning path as abandoned
        WHERE: Called when student gives up on path
        WHY: Tracks abandonment for analytics and intervention
        """
        self.status = PathStatus.ABANDONED
        self.updated_at = datetime.utcnow()

    def update_progress(self) -> None:
        """
        WHAT: Recalculates overall progress from node completion
        WHERE: Called after node status changes
        WHY: Maintains accurate aggregate progress
        """
        if self.total_nodes == 0:
            self.overall_progress = Decimal("0.00")
            return

        completed = sum(1 for n in self.nodes if n.status == NodeStatus.COMPLETED)
        self.completed_nodes = completed
        self.overall_progress = Decimal(completed / self.total_nodes * 100).quantize(Decimal("0.01"))
        self.updated_at = datetime.utcnow()

        if self.completed_nodes == self.total_nodes:
            self.complete()

    def get_current_node(self) -> Optional[LearningPathNode]:
        """
        WHAT: Gets the current active node
        WHERE: Called to display current task to student
        WHY: Provides quick access to current learning focus
        """
        if self.current_node_id is None:
            return None
        return next((n for n in self.nodes if n.id == self.current_node_id), None)

    def get_next_available_node(self) -> Optional[LearningPathNode]:
        """
        WHAT: Gets the next available node to work on
        WHERE: Called after completing current node
        WHY: Guides student to next step in their journey
        """
        sorted_nodes = sorted(self.nodes, key=lambda n: n.sequence_order)
        for node in sorted_nodes:
            if node.status == NodeStatus.AVAILABLE:
                return node
        return None

    def record_adaptation(self) -> None:
        """
        WHAT: Records that an adaptation was made
        WHERE: Called after adaptive service modifies path
        WHY: Tracks adaptation frequency for analytics
        """
        self.adaptation_count += 1
        self.last_adaptation_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_on_track(self) -> bool:
        """
        WHAT: Checks if path is progressing towards target date
        WHERE: Called for at-risk student identification
        WHY: Enables proactive intervention for struggling students
        """
        if self.target_completion_date is None or self.started_at is None:
            return True

        days_elapsed = (datetime.utcnow().date() - self.started_at.date()).days
        total_days = (self.target_completion_date - self.started_at.date()).days

        if total_days <= 0:
            return self.overall_progress >= 100

        expected_progress = Decimal(days_elapsed / total_days * 100)
        return self.overall_progress >= expected_progress * Decimal("0.8")  # 80% of expected


@dataclass
class AdaptiveRecommendation:
    """
    WHAT: AI-generated learning recommendation for a student
    WHERE: Created by RecommendationEngine, displayed in student dashboard
    WHY: Provides actionable next-step suggestions based on performance
         analytics to optimize learning outcomes

    Business Rules:
    - Recommendations expire after valid_until
    - Higher priority recommendations displayed first
    - User feedback improves future recommendations
    """
    id: UUID
    student_id: UUID
    recommendation_type: RecommendationType
    title: str
    reason: str
    learning_path_id: Optional[UUID] = None
    content_type: Optional[ContentType] = None
    content_id: Optional[UUID] = None
    description: Optional[str] = None
    priority: int = 5  # 1-10, higher is more urgent
    confidence_score: Decimal = Decimal("0.50")
    trigger_metrics: Dict[str, Any] = field(default_factory=dict)
    status: RecommendationStatus = RecommendationStatus.PENDING
    valid_from: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    acted_on_at: Optional[datetime] = None
    user_feedback: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Set default expiration if not provided"""
        if self.valid_until is None:
            self.valid_until = datetime.utcnow() + timedelta(days=7)

    def view(self) -> None:
        """
        WHAT: Marks recommendation as viewed
        WHERE: Called when student sees the recommendation
        WHY: Tracks engagement with recommendations
        """
        self.status = RecommendationStatus.VIEWED
        self.viewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def accept(self) -> None:
        """
        WHAT: Marks recommendation as accepted
        WHERE: Called when student acts on recommendation
        WHY: Tracks recommendation effectiveness
        """
        self.status = RecommendationStatus.ACCEPTED
        self.acted_on_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def dismiss(self) -> None:
        """
        WHAT: Marks recommendation as dismissed
        WHERE: Called when student ignores recommendation
        WHY: Prevents repeated showing of unwanted recommendations
        """
        self.status = RecommendationStatus.DISMISSED
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """
        WHAT: Marks recommendation as completed
        WHERE: Called when recommended action is finished
        WHY: Tracks successful recommendation outcomes
        """
        self.status = RecommendationStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def expire(self) -> None:
        """
        WHAT: Marks recommendation as expired
        WHERE: Called when valid_until is passed
        WHY: Cleans up stale recommendations
        """
        self.status = RecommendationStatus.EXPIRED
        self.updated_at = datetime.utcnow()

    def is_valid(self) -> bool:
        """
        WHAT: Checks if recommendation is still valid
        WHERE: Called before displaying recommendation
        WHY: Ensures only current recommendations are shown
        """
        now = datetime.utcnow()
        return (
            self.status == RecommendationStatus.PENDING
            and self.valid_from <= now
            and (self.valid_until is None or self.valid_until > now)
        )

    def set_feedback(self, feedback: str) -> None:
        """
        WHAT: Records user feedback on recommendation
        WHERE: Called when student rates recommendation
        WHY: Improves future recommendation quality

        Args:
            feedback: One of 'helpful', 'not_helpful', 'too_easy', 'too_hard'
        """
        valid_feedback = {'helpful', 'not_helpful', 'too_easy', 'too_hard'}
        if feedback not in valid_feedback:
            raise InvalidFeedbackException(
                f"Invalid feedback '{feedback}'. Must be one of {valid_feedback}"
            )
        self.user_feedback = feedback
        self.updated_at = datetime.utcnow()


@dataclass
class StudentMasteryLevel:
    """
    WHAT: Tracks mastery level for a specific skill/topic per student
    WHERE: Updated by assessment results, used by adaptive engine
    WHY: Enables fine-grained skill tracking for personalized recommendations
         and spaced repetition scheduling using SM-2 algorithm

    SM-2 ALGORITHM IMPLEMENTATION:
    The SuperMemo 2 algorithm optimizes review scheduling by adjusting intervals
    based on answer quality (0-5) and an ease factor (EF) that adapts to performance.

    Key Fields for SM-2:
    - ease_factor: Multiplier for interval calculation (1.3-2.5, default 2.5)
    - repetition_count: Consecutive successful repetitions (reset on quality < 3)
    - current_interval_days: Current review interval
    - last_quality_rating: Most recent answer quality (0-5)

    Business Rules:
    - Mastery levels update based on assessment performance
    - Retention decays over time without practice
    - Spaced repetition scheduling uses SM-2 algorithm
    - Quality ratings: 0=blackout, 1=incorrect, 2=barely, 3=hard, 4=good, 5=perfect
    """
    id: UUID
    student_id: UUID
    skill_topic: str
    organization_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    mastery_level: MasteryLevel = MasteryLevel.NOVICE
    mastery_score: Decimal = Decimal("0.00")
    assessments_completed: int = 0
    assessments_passed: int = 0
    average_score: Optional[Decimal] = None
    best_score: Optional[Decimal] = None
    total_practice_time_minutes: int = 0
    last_practiced_at: Optional[datetime] = None
    practice_streak_days: int = 0
    last_assessment_at: Optional[datetime] = None
    retention_estimate: Decimal = Decimal("1.00")
    next_review_recommended_at: Optional[datetime] = None
    # SM-2 Algorithm Fields (Enhancement 2: Spaced Repetition System)
    ease_factor: Decimal = Decimal("2.50")  # SM-2 default EF, range 1.3-2.5
    repetition_count: int = 0  # Consecutive successful reviews (quality >= 3)
    current_interval_days: int = 1  # Current review interval in days
    last_quality_rating: int = 0  # Most recent SM-2 quality rating (0-5)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def score_to_quality(self, score: Decimal) -> int:
        """
        WHAT: Converts score (0-100) to SM-2 quality rating (0-5)
        WHERE: Called by record_assessment when quality not provided
        WHY: Maps assessment scores to SM-2 algorithm quality levels

        SM-2 Quality Ratings:
        - 5: Perfect response (>= 95%)
        - 4: Correct with hesitation (>= 80%)
        - 3: Correct with serious difficulty (>= 60%)
        - 2: Incorrect but easy to recall (>= 40%)
        - 1: Incorrect, remembered after hint (>= 20%)
        - 0: Complete blackout (< 20%)

        Returns:
            int: Quality rating 0-5 for SM-2 algorithm
        """
        if score >= Decimal("95"):
            return 5
        elif score >= Decimal("80"):
            return 4
        elif score >= Decimal("60"):
            return 3
        elif score >= Decimal("40"):
            return 2
        elif score >= Decimal("20"):
            return 1
        else:
            return 0

    def record_assessment(self, score: Decimal, passed: bool, quality: Optional[int] = None) -> None:
        """
        WHAT: Records an assessment result and updates mastery using SM-2 algorithm
        WHERE: Called after quiz/assessment completion
        WHY: Maintains accurate mastery tracking with adaptive interval scheduling

        SM-2 Algorithm Integration:
        - Converts score to quality rating (0-5) if not provided
        - Adjusts ease factor based on response quality
        - Calculates optimal review interval
        - Resets repetition count on failure (quality < 3)

        Args:
            score: Score achieved (0-100)
            passed: Whether the assessment was passed
            quality: Optional SM-2 quality rating (0-5). If not provided, derived from score.
        """
        self.assessments_completed += 1
        if passed:
            self.assessments_passed += 1

        # Update scores
        if self.best_score is None or score > self.best_score:
            self.best_score = score

        if self.average_score is None:
            self.average_score = score
        else:
            # Running average
            total = self.average_score * (self.assessments_completed - 1) + score
            self.average_score = total / self.assessments_completed

        # Update mastery score (weighted recent + average)
        self.mastery_score = (score * Decimal("0.6") + self.average_score * Decimal("0.4"))
        self.mastery_level = MasteryLevel.from_score(self.mastery_score)

        # Determine quality rating for SM-2
        if quality is not None:
            self.last_quality_rating = max(0, min(5, quality))  # Clamp to 0-5
        else:
            self.last_quality_rating = self.score_to_quality(score)

        self.last_assessment_at = datetime.utcnow()
        self.retention_estimate = Decimal("1.00")  # Reset retention after assessment
        self._schedule_next_review_sm2()
        self.updated_at = datetime.utcnow()

    def record_practice(self, minutes: int) -> None:
        """
        WHAT: Records practice time for this skill
        WHERE: Called after lab/exercise completion
        WHY: Tracks engagement for streak and pacing analytics
        """
        self.total_practice_time_minutes += minutes

        now = datetime.utcnow()
        if self.last_practiced_at is not None:
            days_since = (now.date() - self.last_practiced_at.date()).days
            if days_since == 1:
                self.practice_streak_days += 1
            elif days_since > 1:
                self.practice_streak_days = 1
        else:
            self.practice_streak_days = 1

        self.last_practiced_at = now
        self.updated_at = now

    def calculate_retention(self) -> Decimal:
        """
        WHAT: Calculates estimated knowledge retention based on time decay
        WHERE: Called to determine review urgency
        WHY: Implements spaced repetition scheduling

        Returns:
            Estimated retention (0-1) using exponential decay model
        """
        if self.last_assessment_at is None:
            return Decimal("1.00")

        days_since = (datetime.utcnow() - self.last_assessment_at).days

        # Exponential decay based on mastery level
        # Higher mastery = slower decay
        decay_rates = {
            MasteryLevel.NOVICE: 0.3,
            MasteryLevel.BEGINNER: 0.25,
            MasteryLevel.INTERMEDIATE: 0.2,
            MasteryLevel.PROFICIENT: 0.15,
            MasteryLevel.EXPERT: 0.1,
            MasteryLevel.MASTER: 0.05
        }
        decay_rate = decay_rates.get(self.mastery_level, 0.2)

        # R = e^(-decay * days)
        import math
        retention = math.exp(-decay_rate * days_since)
        self.retention_estimate = Decimal(str(round(retention, 2)))
        return self.retention_estimate

    def _schedule_next_review_sm2(self) -> None:
        """
        WHAT: Schedules next review using SM-2 (SuperMemo 2) algorithm
        WHERE: Called after assessment completion
        WHY: Implements optimal adaptive review scheduling based on performance

        SM-2 ALGORITHM:
        The SuperMemo 2 algorithm adjusts review intervals based on:
        1. Quality of response (0-5)
        2. Current ease factor (EF)
        3. Number of consecutive successful reviews

        Algorithm Steps:
        1. If quality < 3: Reset repetition_count to 0, interval = 1 day
        2. If quality >= 3:
           - If repetition == 0: interval = 1
           - If repetition == 1: interval = 6
           - Else: interval = previous_interval * ease_factor

        3. Update ease factor:
           EF' = EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
           EF must be >= 1.3

        Reference: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
        """
        quality = self.last_quality_rating

        if quality < 3:
            # Failed review - reset to beginning
            self.repetition_count = 0
            self.current_interval_days = 1
        else:
            # Successful review - calculate new interval
            if self.repetition_count == 0:
                self.current_interval_days = 1
            elif self.repetition_count == 1:
                self.current_interval_days = 6
            else:
                # interval = previous_interval * ease_factor
                new_interval = float(self.current_interval_days) * float(self.ease_factor)
                self.current_interval_days = int(round(new_interval))

            self.repetition_count += 1

        # Update ease factor using SM-2 formula
        # EF' = EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ef_adjustment = Decimal("0.1") - Decimal(str((5 - quality) * (0.08 + (5 - quality) * 0.02)))
        new_ef = self.ease_factor + ef_adjustment

        # Ease factor must be at least 1.3 (SM-2 minimum)
        self.ease_factor = max(Decimal("1.30"), new_ef)

        # Cap ease factor at 2.5 (SM-2 default max for good performance)
        self.ease_factor = min(Decimal("2.50"), self.ease_factor)

        # Schedule next review
        self.next_review_recommended_at = datetime.utcnow() + timedelta(days=self.current_interval_days)

    def _schedule_next_review(self) -> None:
        """
        WHAT: Legacy scheduling method (fallback to SM-2)
        WHERE: For backwards compatibility
        WHY: Maintains API compatibility while using SM-2 internally

        Note: This method is deprecated. Use _schedule_next_review_sm2() directly.
        """
        self._schedule_next_review_sm2()

    def needs_review(self) -> bool:
        """
        WHAT: Checks if this skill needs review
        WHERE: Called by recommendation engine
        WHY: Identifies skills requiring reinforcement
        """
        if self.next_review_recommended_at is None:
            return False
        return datetime.utcnow() >= self.next_review_recommended_at


# ============================================================================
# Custom Exceptions
# ============================================================================

class AdaptiveLearningException(Exception):
    """
    WHAT: Base exception for adaptive learning errors
    WHERE: Parent for all adaptive learning exceptions
    WHY: Enables catching all adaptive learning errors with single handler
    """
    pass


class NodeNotUnlockedException(AdaptiveLearningException):
    """
    WHAT: Raised when attempting to access locked content
    WHERE: Thrown by LearningPathNode.start()
    WHY: Enforces prerequisite completion requirements
    """
    pass


class InvalidProgressException(AdaptiveLearningException):
    """
    WHAT: Raised when progress value is invalid
    WHERE: Thrown by LearningPathNode.update_progress()
    WHY: Ensures data integrity for progress tracking
    """
    pass


class CannotSkipRequiredNodeException(AdaptiveLearningException):
    """
    WHAT: Raised when attempting to skip required content
    WHERE: Thrown by LearningPathNode.skip()
    WHY: Enforces mandatory content completion
    """
    pass


class InvalidPathStateException(AdaptiveLearningException):
    """
    WHAT: Raised when path operation invalid for current state
    WHERE: Thrown by LearningPath state transition methods
    WHY: Ensures valid path lifecycle transitions
    """
    pass


class InvalidFeedbackException(AdaptiveLearningException):
    """
    WHAT: Raised when invalid feedback value provided
    WHERE: Thrown by AdaptiveRecommendation.set_feedback()
    WHY: Ensures feedback data quality
    """
    pass


class PrerequisiteNotMetException(AdaptiveLearningException):
    """
    WHAT: Raised when prerequisites are not satisfied
    WHERE: Thrown by PrerequisiteService
    WHY: Enforces learning sequence requirements
    """
    pass


class LearningPathNotFoundException(AdaptiveLearningException):
    """
    WHAT: Raised when learning path not found
    WHERE: Thrown by LearningPathDAO/Service
    WHY: Clear error for missing resources
    """
    pass


class RecommendationNotFoundException(AdaptiveLearningException):
    """
    WHAT: Raised when recommendation not found
    WHERE: Thrown by RecommendationDAO/Service
    WHY: Clear error for missing resources
    """
    pass
