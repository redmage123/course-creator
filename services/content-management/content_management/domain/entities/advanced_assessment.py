"""
Advanced Assessment Domain Entities

WHAT: Domain entities for advanced assessment types including performance-based,
      peer review, portfolio, competency-based, and project-based assessments.

WHERE: Content management service domain layer - represents core business logic
       for advanced assessment management.

WHY: Traditional quizzes only measure recall and basic understanding. Modern
     educational programs require diverse assessment types to evaluate:
     - Practical skills (performance-based)
     - Collaboration and critical thinking (peer review)
     - Growth over time (portfolio)
     - Specific skill mastery (competency-based)
     - Complex problem-solving (project-based)

Business Requirements:
- Support 10 distinct assessment types with specialized workflows
- Enable rich rubric-based evaluation with criteria and proficiency levels
- Facilitate peer review with configurable anonymity and reviewer assignments
- Track portfolio artifacts demonstrating student growth
- Map competencies to learning objectives with proficiency tracking
- Support project milestones and deliverables
- Provide comprehensive scoring and analytics

Technical Implementation:
- Immutable value objects where appropriate
- Rich domain models with business rule validation
- Custom exception hierarchy for granular error handling
- Comprehensive type hints and documentation
- Integration points for DAO and service layers
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4


# ============================================================================
# EXCEPTION HIERARCHY
# Custom exceptions for granular error handling in assessment operations
# ============================================================================

class AdvancedAssessmentError(Exception):
    """
    Base exception for all advanced assessment domain errors.

    WHAT: Root exception class for assessment-related errors.
    WHERE: Raised throughout assessment domain layer.
    WHY: Provides consistent error handling and categorization for all
         assessment operations, enabling proper exception translation
         at service and API layers.
    """
    pass


class AssessmentValidationError(AdvancedAssessmentError):
    """
    Raised when assessment validation rules are violated.

    WHAT: Exception for invalid assessment configuration or data.
    WHERE: Raised during entity creation or modification.
    WHY: Prevents invalid assessments from being created, ensuring
         educational integrity and consistent behavior.
    """
    pass


class RubricValidationError(AdvancedAssessmentError):
    """
    Raised when rubric validation fails.

    WHAT: Exception for invalid rubric structure or scoring configuration.
    WHERE: Raised during rubric creation or evaluation.
    WHY: Ensures rubrics have valid structure with proper criteria,
         weights, and performance levels for fair evaluation.
    """
    pass


class SubmissionError(AdvancedAssessmentError):
    """
    Raised when submission operations fail.

    WHAT: Exception for submission-related failures.
    WHERE: Raised during submission creation, update, or grading.
    WHY: Handles errors in student submission workflow including
         late submissions, invalid content, or status transitions.
    """
    pass


class PeerReviewError(AdvancedAssessmentError):
    """
    Raised when peer review operations fail.

    WHAT: Exception for peer review workflow errors.
    WHERE: Raised during reviewer assignment or review submission.
    WHY: Ensures peer review process maintains integrity including
         proper assignment, anonymity, and review quality.
    """
    pass


class CompetencyError(AdvancedAssessmentError):
    """
    Raised when competency operations fail.

    WHAT: Exception for competency mapping and tracking errors.
    WHERE: Raised during competency verification or progress updates.
    WHY: Maintains competency framework integrity ensuring proper
         proficiency level progression and evidence validation.
    """
    pass


class PortfolioError(AdvancedAssessmentError):
    """
    Raised when portfolio operations fail.

    WHAT: Exception for portfolio artifact management errors.
    WHERE: Raised during artifact addition or portfolio evaluation.
    WHY: Ensures portfolio integrity including artifact requirements,
         reflection quality, and growth demonstration.
    """
    pass


class ProjectError(AdvancedAssessmentError):
    """
    Raised when project assessment operations fail.

    WHAT: Exception for project milestone and deliverable errors.
    WHERE: Raised during milestone submissions or project evaluation.
    WHY: Maintains project-based assessment workflow integrity
         including milestone sequencing and deliverable requirements.
    """
    pass


# ============================================================================
# ENUMERATION TYPES
# Define valid values for assessment classification and status
# ============================================================================

class AssessmentType(Enum):
    """
    Assessment type classification for different evaluation methodologies.

    WHAT: Enumeration of supported advanced assessment types.
    WHERE: Used in AdvancedAssessment entity to specify assessment kind.
    WHY: Different assessment types require different workflows, evaluation
         methods, and student interactions. This classification enables
         type-specific behavior throughout the system.

    Assessment Types:
    - PERFORMANCE: Practical demonstrations evaluated by instructor
    - PEER_REVIEW: Work evaluated by peers using structured rubrics
    - PORTFOLIO: Collection of work demonstrating growth over time
    - COMPETENCY: Skill verification against defined competencies
    - PROJECT: Comprehensive projects with milestones and deliverables
    - RUBRIC: General rubric-based evaluation
    - PRESENTATION: Live or recorded presentations
    - INTERVIEW: Oral assessments and interviews
    - SIMULATION: Scenario-based problem solving
    - SELF_REFLECTION: Self-assessment with guided reflection
    """
    PERFORMANCE = "performance"
    PEER_REVIEW = "peer_review"
    PORTFOLIO = "portfolio"
    COMPETENCY = "competency"
    PROJECT = "project"
    RUBRIC = "rubric"
    PRESENTATION = "presentation"
    INTERVIEW = "interview"
    SIMULATION = "simulation"
    SELF_REFLECTION = "self_reflection"


class AssessmentStatus(Enum):
    """
    Assessment lifecycle status tracking.

    WHAT: Enumeration of assessment publication and availability states.
    WHERE: Used in AdvancedAssessment to track lifecycle.
    WHY: Assessments progress through states from creation to archival.
         Status controls visibility, submission availability, and
         editing permissions.

    Status Flow:
    draft -> published -> (in_progress) -> (completed) -> archived
    """
    DRAFT = "draft"
    PUBLISHED = "published"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    REQUIRES_REVISION = "requires_revision"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SubmissionStatus(Enum):
    """
    Individual submission status for student work.

    WHAT: Enumeration of submission workflow states.
    WHERE: Used in AssessmentSubmission to track progress.
    WHY: Submissions follow a workflow from creation through evaluation.
         Status determines available actions and visibility of feedback.

    Status Flow:
    not_started -> in_progress -> submitted -> under_review -> graded/approved/rejected
                                            -> needs_revision -> revised -> under_review
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    NEEDS_REVISION = "needs_revision"
    REVISED = "revised"
    GRADED = "graded"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProficiencyLevel(Enum):
    """
    Proficiency level classification for competency-based assessment.

    WHAT: Enumeration of skill demonstration levels.
    WHERE: Used in competency tracking and rubric evaluations.
    WHY: Competency-based education requires clear proficiency definitions.
         These levels provide consistent vocabulary for skill assessment
         across different competencies and evaluators.

    Level Progression:
    not_demonstrated -> emerging -> developing -> proficient -> advanced -> expert

    Typical Point Mapping (0-100 scale):
    - not_demonstrated: 0
    - emerging: 20
    - developing: 40
    - proficient: 70 (minimum passing)
    - advanced: 85
    - expert: 100
    """
    NOT_DEMONSTRATED = "not_demonstrated"
    EMERGING = "emerging"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"
    EXPERT = "expert"

    @classmethod
    def from_percentage(cls, percentage: float) -> 'ProficiencyLevel':
        """
        Convert percentage score to proficiency level.

        WHAT: Maps numeric score to proficiency classification.
        WHERE: Used when evaluating submissions or calculating competency levels.
        WHY: Enables automatic proficiency level assignment from numeric
             evaluations, ensuring consistent classification.

        Args:
            percentage: Score as percentage (0-100)

        Returns:
            Corresponding ProficiencyLevel
        """
        if percentage >= 95:
            return cls.EXPERT
        elif percentage >= 85:
            return cls.ADVANCED
        elif percentage >= 70:
            return cls.PROFICIENT
        elif percentage >= 50:
            return cls.DEVELOPING
        elif percentage >= 25:
            return cls.EMERGING
        else:
            return cls.NOT_DEMONSTRATED

    def to_percentage_range(self) -> Tuple[float, float]:
        """
        Get the percentage range for this proficiency level.

        WHAT: Returns min/max percentage for this level.
        WHERE: Used in analytics and reporting.
        WHY: Enables reverse mapping from level to expected score range.

        Returns:
            Tuple of (min_percentage, max_percentage)
        """
        ranges = {
            self.NOT_DEMONSTRATED: (0.0, 24.9),
            self.EMERGING: (25.0, 49.9),
            self.DEVELOPING: (50.0, 69.9),
            self.PROFICIENT: (70.0, 84.9),
            self.ADVANCED: (85.0, 94.9),
            self.EXPERT: (95.0, 100.0),
        }
        return ranges.get(self, (0.0, 100.0))


class ReviewType(Enum):
    """
    Review type configuration for peer assessments.

    WHAT: Enumeration of peer review anonymity configurations.
    WHERE: Used in AdvancedAssessment for peer review settings.
    WHY: Different peer review scenarios require different anonymity levels.
         This affects both academic integrity and psychological safety.

    Review Types:
    - SINGLE_BLIND: Reviewer sees author, author doesn't see reviewer
    - DOUBLE_BLIND: Neither party knows the other (most rigorous)
    - OPEN: Both parties know each other (promotes collaboration)
    - COLLABORATIVE: Group review process (multiple reviewers together)
    """
    SINGLE_BLIND = "single_blind"
    DOUBLE_BLIND = "double_blind"
    OPEN = "open"
    COLLABORATIVE = "collaborative"


# ============================================================================
# RUBRIC DOMAIN ENTITIES
# Define evaluation structure for all rubric-based assessments
# ============================================================================

@dataclass
class RubricPerformanceLevel:
    """
    Performance level definition for a rubric criterion.

    WHAT: Describes what a specific proficiency level looks like for a criterion.
    WHERE: Part of RubricCriterion, used during evaluation.
    WHY: Clear performance level descriptions ensure consistent evaluation
         across different graders and provide students with clear expectations.

    Business Requirements:
    - Define clear expectations for each proficiency level
    - Assign appropriate point values for each level
    - Support visual indicators (color, icon) for UI display

    Example (for "Code Quality" criterion):
    - Expert (30 pts): Code is exceptionally clean, follows all best practices...
    - Proficient (25 pts): Code is clean and readable, follows most best practices...
    - Developing (15 pts): Code works but has readability issues...
    """
    level: ProficiencyLevel
    name: str
    description: str
    points: Decimal
    percentage_of_max: Optional[Decimal] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    id: Optional[UUID] = None
    criterion_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """
        Initialize and validate performance level.

        WHAT: Auto-generates ID and validates level definition.
        WHERE: Called when creating RubricPerformanceLevel instance.
        WHY: Ensures all performance levels have valid structure and unique IDs.
        """
        if self.id is None:
            self.id = uuid4()
        self.validate()

    def validate(self) -> None:
        """
        Validate performance level business rules.

        WHAT: Validates level definition completeness and validity.
        WHERE: Called during creation and before persistence.
        WHY: Invalid performance levels would break evaluation workflow.

        Raises:
            RubricValidationError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise RubricValidationError("Performance level name is required")

        if not self.description or not self.description.strip():
            raise RubricValidationError("Performance level description is required")

        if self.points < 0:
            raise RubricValidationError("Points cannot be negative")

        if self.color and not self.color.startswith('#'):
            raise RubricValidationError("Color must be a hex color code (e.g., #FF0000)")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "criterion_id": str(self.criterion_id) if self.criterion_id else None,
            "level": self.level.value,
            "name": self.name,
            "description": self.description,
            "points": float(self.points),
            "percentage_of_max": float(self.percentage_of_max) if self.percentage_of_max else None,
            "color": self.color,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class RubricCriterion:
    """
    Individual evaluation criterion within a rubric.

    WHAT: Defines a single dimension of evaluation with performance levels.
    WHERE: Part of AssessmentRubric, used during evaluation.
    WHY: Criteria break down complex assessments into evaluable dimensions,
         enabling consistent and fair evaluation across students.

    Business Requirements:
    - Define clear evaluation dimensions with descriptions
    - Support weighted scoring for criteria of different importance
    - Include multiple performance levels with descriptions
    - Enable partial credit scoring

    Example Criteria for Code Review:
    - Functionality (30 pts, weight 2.0): Does the code work correctly?
    - Code Quality (25 pts, weight 1.5): Is the code clean and readable?
    - Documentation (15 pts, weight 1.0): Are comments and docs adequate?
    """
    name: str
    description: str
    max_points: Decimal
    weight: Decimal = Decimal("1.0")
    performance_levels: List[RubricPerformanceLevel] = field(default_factory=list)
    sort_order: int = 0
    category: Optional[str] = None
    is_required: bool = True
    allow_partial_credit: bool = True
    id: Optional[UUID] = None
    rubric_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """
        Initialize and validate criterion.

        WHAT: Auto-generates ID and validates criterion definition.
        WHERE: Called when creating RubricCriterion instance.
        WHY: Ensures all criteria have valid structure and unique IDs.
        """
        if self.id is None:
            self.id = uuid4()
        self.validate()

    def validate(self) -> None:
        """
        Validate criterion business rules.

        WHAT: Validates criterion definition and performance levels.
        WHERE: Called during creation and before persistence.
        WHY: Invalid criteria would produce inconsistent evaluations.

        Raises:
            RubricValidationError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise RubricValidationError("Criterion name is required")

        if self.max_points <= 0:
            raise RubricValidationError("Maximum points must be positive")

        if self.weight <= 0:
            raise RubricValidationError("Weight must be positive")

    def add_performance_level(self, level: RubricPerformanceLevel) -> None:
        """
        Add a performance level to this criterion.

        WHAT: Adds a new proficiency level description.
        WHERE: Called when building rubric structure.
        WHY: Criteria need multiple performance levels for evaluation.

        Args:
            level: The RubricPerformanceLevel to add

        Raises:
            RubricValidationError: If level already exists for this criterion
        """
        # Check for duplicate level
        existing_levels = {pl.level for pl in self.performance_levels}
        if level.level in existing_levels:
            raise RubricValidationError(
                f"Performance level '{level.level.value}' already exists for this criterion"
            )

        level.criterion_id = self.id
        self.performance_levels.append(level)
        self.performance_levels.sort(key=lambda x: x.sort_order)
        self.updated_at = datetime.utcnow()

    def get_level_for_points(self, points: Decimal) -> Optional[RubricPerformanceLevel]:
        """
        Find the performance level matching given points.

        WHAT: Maps a point value to its performance level.
        WHERE: Used when displaying evaluation results.
        WHY: Translates numeric score to qualitative description.

        Args:
            points: Points awarded

        Returns:
            Matching RubricPerformanceLevel or None
        """
        sorted_levels = sorted(self.performance_levels, key=lambda x: x.points, reverse=True)
        for level in sorted_levels:
            if points >= level.points:
                return level
        return sorted_levels[-1] if sorted_levels else None

    def calculate_weighted_score(self, points: Decimal) -> Decimal:
        """
        Calculate weighted score for this criterion.

        WHAT: Applies weight to points earned.
        WHERE: Used in rubric score calculation.
        WHY: Weighted scoring allows some criteria to count more than others.

        Args:
            points: Raw points awarded

        Returns:
            Weighted score
        """
        return points * self.weight

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "rubric_id": str(self.rubric_id) if self.rubric_id else None,
            "name": self.name,
            "description": self.description,
            "max_points": float(self.max_points),
            "weight": float(self.weight),
            "sort_order": self.sort_order,
            "category": self.category,
            "is_required": self.is_required,
            "allow_partial_credit": self.allow_partial_credit,
            "performance_levels": [pl.to_dict() for pl in self.performance_levels],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class AssessmentRubric:
    """
    Rubric for structured assessment evaluation.

    WHAT: Complete rubric with criteria and performance levels for evaluation.
    WHERE: Attached to AdvancedAssessment for evaluation structure.
    WHY: Rubrics ensure consistent, fair evaluation by providing clear
         criteria and expectations to both evaluators and students.

    Business Requirements:
    - Define multiple evaluation criteria with weights
    - Support reusable rubric templates
    - Calculate total scores from criterion evaluations
    - Determine pass/fail based on passing threshold

    Key Features:
    - Weighted criteria scoring
    - Performance level descriptions
    - Template support for reuse
    - Version tracking for changes
    """
    name: str
    max_score: Decimal
    created_by: UUID
    criteria: List[RubricCriterion] = field(default_factory=list)
    description: Optional[str] = None
    is_template: bool = False
    passing_score: Optional[Decimal] = None
    passing_percentage: Decimal = Decimal("70.0")
    organization_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    tags: List[str] = field(default_factory=list)
    version: int = 1
    is_active: bool = True
    id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """
        Initialize and validate rubric.

        WHAT: Auto-generates ID and validates rubric structure.
        WHERE: Called when creating AssessmentRubric instance.
        WHY: Ensures rubric has valid structure for evaluation.
        """
        if self.id is None:
            self.id = uuid4()
        if self.passing_score is None:
            self.passing_score = self.max_score * (self.passing_percentage / Decimal("100"))
        self.validate()

    def validate(self) -> None:
        """
        Validate rubric business rules.

        WHAT: Validates rubric structure and scoring configuration.
        WHERE: Called during creation and before persistence.
        WHY: Invalid rubrics would produce incorrect evaluations.

        Raises:
            RubricValidationError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise RubricValidationError("Rubric name is required")

        if self.max_score <= 0:
            raise RubricValidationError("Maximum score must be positive")

        if self.passing_score and self.passing_score > self.max_score:
            raise RubricValidationError("Passing score cannot exceed maximum score")

        if not (0 <= self.passing_percentage <= 100):
            raise RubricValidationError("Passing percentage must be between 0 and 100")

    def add_criterion(self, criterion: RubricCriterion) -> None:
        """
        Add an evaluation criterion to this rubric.

        WHAT: Adds a new criterion with optional performance levels.
        WHERE: Called when building rubric structure.
        WHY: Rubrics need multiple criteria to evaluate different dimensions.

        Args:
            criterion: The RubricCriterion to add
        """
        criterion.rubric_id = self.id
        self.criteria.append(criterion)
        self.criteria.sort(key=lambda x: x.sort_order)
        self.updated_at = datetime.utcnow()

    def remove_criterion(self, criterion_id: UUID) -> bool:
        """
        Remove a criterion from this rubric.

        WHAT: Removes criterion by ID.
        WHERE: Called when editing rubric structure.
        WHY: Allows rubric modification before publication.

        Args:
            criterion_id: UUID of criterion to remove

        Returns:
            True if removed, False if not found
        """
        for i, criterion in enumerate(self.criteria):
            if criterion.id == criterion_id:
                del self.criteria[i]
                self.updated_at = datetime.utcnow()
                return True
        return False

    def get_criterion(self, criterion_id: UUID) -> Optional[RubricCriterion]:
        """
        Get a specific criterion by ID.

        WHAT: Retrieves criterion from rubric.
        WHERE: Called during evaluation or editing.
        WHY: Need to access individual criteria for scoring.

        Args:
            criterion_id: UUID of criterion to find

        Returns:
            RubricCriterion if found, None otherwise
        """
        for criterion in self.criteria:
            if criterion.id == criterion_id:
                return criterion
        return None

    def calculate_total_weight(self) -> Decimal:
        """
        Calculate sum of all criterion weights.

        WHAT: Sums weights across all criteria.
        WHERE: Used in weighted score normalization.
        WHY: Total weight needed to calculate normalized scores.

        Returns:
            Sum of all criterion weights
        """
        return sum(c.weight for c in self.criteria)

    def calculate_max_weighted_score(self) -> Decimal:
        """
        Calculate maximum possible weighted score.

        WHAT: Sums max_points * weight for all criteria.
        WHERE: Used in percentage calculations.
        WHY: Establishes maximum for score normalization.

        Returns:
            Maximum weighted score
        """
        return sum(c.max_points * c.weight for c in self.criteria)

    def calculate_score(
        self,
        criterion_scores: Dict[UUID, Decimal]
    ) -> Dict[str, Any]:
        """
        Calculate total score from criterion evaluations.

        WHAT: Computes total score with weighted criteria.
        WHERE: Called when finalizing evaluation.
        WHY: Aggregates individual criterion scores into final grade.

        Args:
            criterion_scores: Dict mapping criterion_id to points earned

        Returns:
            Dict with total_points, weighted_score, percentage, passed

        Raises:
            RubricValidationError: If required criterion is missing
        """
        total_points = Decimal("0")
        total_weighted = Decimal("0")
        max_weighted = Decimal("0")
        missing_required = []

        for criterion in self.criteria:
            max_weighted += criterion.max_points * criterion.weight

            if criterion.id in criterion_scores:
                points = criterion_scores[criterion.id]
                total_points += points
                total_weighted += criterion.calculate_weighted_score(points)
            elif criterion.is_required:
                missing_required.append(criterion.name)

        if missing_required:
            raise RubricValidationError(
                f"Missing scores for required criteria: {', '.join(missing_required)}"
            )

        percentage = (total_weighted / max_weighted * 100) if max_weighted > 0 else Decimal("0")
        passed = total_points >= self.passing_score if self.passing_score else percentage >= self.passing_percentage

        return {
            "total_points": float(total_points),
            "weighted_score": float(total_weighted),
            "max_weighted_score": float(max_weighted),
            "percentage": float(percentage),
            "passed": passed,
            "passing_threshold": float(self.passing_score or self.max_score * self.passing_percentage / 100)
        }

    def create_template_copy(self, created_by: UUID) -> 'AssessmentRubric':
        """
        Create a copy of this rubric for use in new assessment.

        WHAT: Creates a new rubric based on this template.
        WHERE: Called when creating assessment from template.
        WHY: Templates allow rubric reuse without affecting original.

        Args:
            created_by: UUID of user creating the copy

        Returns:
            New AssessmentRubric instance
        """
        new_rubric = AssessmentRubric(
            name=f"{self.name} (Copy)",
            max_score=self.max_score,
            created_by=created_by,
            description=self.description,
            is_template=False,
            passing_score=self.passing_score,
            passing_percentage=self.passing_percentage,
            tags=self.tags.copy()
        )

        for criterion in self.criteria:
            new_criterion = RubricCriterion(
                name=criterion.name,
                description=criterion.description,
                max_points=criterion.max_points,
                weight=criterion.weight,
                sort_order=criterion.sort_order,
                category=criterion.category,
                is_required=criterion.is_required,
                allow_partial_credit=criterion.allow_partial_credit
            )

            for level in criterion.performance_levels:
                new_level = RubricPerformanceLevel(
                    level=level.level,
                    name=level.name,
                    description=level.description,
                    points=level.points,
                    percentage_of_max=level.percentage_of_max,
                    color=level.color,
                    icon=level.icon,
                    sort_order=level.sort_order
                )
                new_criterion.add_performance_level(new_level)

            new_rubric.add_criterion(new_criterion)

        return new_rubric

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "description": self.description,
            "max_score": float(self.max_score),
            "passing_score": float(self.passing_score) if self.passing_score else None,
            "passing_percentage": float(self.passing_percentage),
            "is_template": self.is_template,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "course_id": str(self.course_id) if self.course_id else None,
            "created_by": str(self.created_by),
            "tags": self.tags,
            "version": self.version,
            "is_active": self.is_active,
            "criteria": [c.to_dict() for c in self.criteria],
            "total_weight": float(self.calculate_total_weight()),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# COMPETENCY DOMAIN ENTITIES
# Define and track skill-based competencies
# ============================================================================

@dataclass
class Competency:
    """
    Competency definition for skill-based assessment.

    WHAT: Defines a measurable skill or knowledge area with proficiency requirements.
    WHERE: Linked to assessments and tracked for students.
    WHY: Competency-based education focuses on skill mastery rather than time.
         Competencies provide clear learning targets and enable precise tracking.

    Business Requirements:
    - Define skills with clear proficiency expectations
    - Support hierarchical competency structures
    - Specify evidence requirements for demonstration
    - Enable competency mapping to courses and assessments

    Example Competencies:
    - PROG-001: Python Fundamentals (proficient required)
    - PROG-002: Object-Oriented Design (advanced required)
    - DATA-001: SQL Query Writing (proficient required)
    """
    code: str
    name: str
    required_proficiency: ProficiencyLevel = ProficiencyLevel.PROFICIENT
    description: Optional[str] = None
    category: Optional[str] = None
    parent_id: Optional[UUID] = None
    level: int = 1
    evidence_requirements: Optional[str] = None
    organization_id: Optional[UUID] = None
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """
        Initialize and validate competency.

        WHAT: Auto-generates ID and validates competency definition.
        WHERE: Called when creating Competency instance.
        WHY: Ensures competency has valid structure for tracking.
        """
        if self.id is None:
            self.id = uuid4()
        self.validate()

    def validate(self) -> None:
        """
        Validate competency business rules.

        WHAT: Validates competency definition completeness.
        WHERE: Called during creation and before persistence.
        WHY: Invalid competencies would break tracking and reporting.

        Raises:
            CompetencyError: If validation fails
        """
        if not self.code or not self.code.strip():
            raise CompetencyError("Competency code is required")

        if not self.name or not self.name.strip():
            raise CompetencyError("Competency name is required")

        if self.level < 1:
            raise CompetencyError("Level must be at least 1")

    def is_child_of(self, potential_parent_id: UUID) -> bool:
        """
        Check if this competency is a child of another.

        WHAT: Checks parent relationship.
        WHERE: Used in hierarchy navigation.
        WHY: Competencies form hierarchies; need to validate relationships.

        Args:
            potential_parent_id: UUID of potential parent

        Returns:
            True if this is a child of the given parent
        """
        return self.parent_id == potential_parent_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "level": self.level,
            "required_proficiency": self.required_proficiency.value,
            "evidence_requirements": self.evidence_requirements,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "tags": self.tags,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class CompetencyProgress:
    """
    Student progress on a specific competency.

    WHAT: Tracks a student's proficiency level for a competency.
    WHERE: Updated when assessments demonstrate competency.
    WHY: Competency tracking enables mastery-based progression and
         provides clear visibility into skill development.

    Business Requirements:
    - Track current and historical proficiency levels
    - Link evidence (submissions) demonstrating competency
    - Support verification by instructors
    - Enable progression tracking over time
    """
    student_id: UUID
    competency_id: UUID
    current_level: ProficiencyLevel = ProficiencyLevel.NOT_DEMONSTRATED
    previous_level: Optional[ProficiencyLevel] = None
    evidence_submissions: List[UUID] = field(default_factory=list)
    assessor_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[UUID] = None
    first_demonstrated_at: Optional[datetime] = None
    level_achieved_at: Optional[datetime] = None
    id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize competency progress."""
        if self.id is None:
            self.id = uuid4()

    def update_level(
        self,
        new_level: ProficiencyLevel,
        submission_id: Optional[UUID] = None
    ) -> bool:
        """
        Update proficiency level based on new evidence.

        WHAT: Updates current proficiency and tracks progression.
        WHERE: Called when submission demonstrates competency.
        WHY: Competency levels should only increase (no regression).

        Args:
            new_level: New proficiency level to record
            submission_id: Optional submission demonstrating competency

        Returns:
            True if level was updated, False if no change
        """
        level_order = list(ProficiencyLevel)
        current_index = level_order.index(self.current_level)
        new_index = level_order.index(new_level)

        if new_index > current_index:
            self.previous_level = self.current_level
            self.current_level = new_level
            self.level_achieved_at = datetime.utcnow()

            if self.first_demonstrated_at is None and new_level != ProficiencyLevel.NOT_DEMONSTRATED:
                self.first_demonstrated_at = datetime.utcnow()

            if submission_id:
                self.evidence_submissions.append(submission_id)

            self.updated_at = datetime.utcnow()
            return True

        # Even if level didn't increase, track submission as evidence
        if submission_id and submission_id not in self.evidence_submissions:
            self.evidence_submissions.append(submission_id)
            self.updated_at = datetime.utcnow()

        return False

    def verify(self, verifier_id: UUID, notes: Optional[str] = None) -> None:
        """
        Mark competency as verified by instructor.

        WHAT: Records instructor verification of competency level.
        WHERE: Called when instructor confirms student proficiency.
        WHY: Some competencies require manual verification beyond auto-grading.

        Args:
            verifier_id: UUID of instructor verifying
            notes: Optional verification notes
        """
        self.verified_at = datetime.utcnow()
        self.verified_by = verifier_id
        if notes:
            self.assessor_notes = notes
        self.updated_at = datetime.utcnow()

    def meets_requirement(self, required_level: ProficiencyLevel) -> bool:
        """
        Check if current level meets or exceeds requirement.

        WHAT: Compares current level to required level.
        WHERE: Used in prerequisite and progression checks.
        WHY: Competency-based progression requires meeting requirements.

        Args:
            required_level: Minimum required proficiency

        Returns:
            True if current level meets or exceeds required
        """
        level_order = list(ProficiencyLevel)
        return level_order.index(self.current_level) >= level_order.index(required_level)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "student_id": str(self.student_id),
            "competency_id": str(self.competency_id),
            "current_level": self.current_level.value,
            "previous_level": self.previous_level.value if self.previous_level else None,
            "evidence_submissions": [str(s) for s in self.evidence_submissions],
            "assessor_notes": self.assessor_notes,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verified_by": str(self.verified_by) if self.verified_by else None,
            "first_demonstrated_at": self.first_demonstrated_at.isoformat() if self.first_demonstrated_at else None,
            "level_achieved_at": self.level_achieved_at.isoformat() if self.level_achieved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# PROJECT DOMAIN ENTITIES
# Manage project-based assessments with milestones
# ============================================================================

@dataclass
class ProjectMilestone:
    """
    Milestone for project-based assessments.

    WHAT: Defines a checkpoint in a larger project with deliverables.
    WHERE: Part of project-type AdvancedAssessment.
    WHY: Projects need intermediate checkpoints for feedback and tracking.
         Milestones break large projects into manageable pieces with deadlines.

    Business Requirements:
    - Define clear milestone requirements and acceptance criteria
    - Support rubric-based evaluation per milestone
    - Enable weighted scoring across milestones
    - Track milestone completion status

    Example Milestones for Capstone Project:
    1. Project Proposal (10%) - Due Week 2
    2. Design Document (20%) - Due Week 4
    3. Implementation (40%) - Due Week 8
    4. Final Presentation (30%) - Due Week 10
    """
    name: str
    assessment_id: UUID
    sort_order: int = 0
    description: Optional[str] = None
    required_deliverables: List[str] = field(default_factory=list)
    acceptance_criteria: Optional[str] = None
    due_date: Optional[datetime] = None
    weight: Decimal = Decimal("1.0")
    max_points: Optional[Decimal] = None
    rubric_id: Optional[UUID] = None
    id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize and validate milestone."""
        if self.id is None:
            self.id = uuid4()
        self.validate()

    def validate(self) -> None:
        """
        Validate milestone business rules.

        WHAT: Validates milestone definition.
        WHERE: Called during creation and before persistence.
        WHY: Invalid milestones would break project workflow.

        Raises:
            ProjectError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise ProjectError("Milestone name is required")

        if self.weight <= 0:
            raise ProjectError("Weight must be positive")

        if self.max_points is not None and self.max_points <= 0:
            raise ProjectError("Maximum points must be positive")

    def is_overdue(self) -> bool:
        """
        Check if milestone is past due date.

        WHAT: Compares due date to current time.
        WHERE: Used in status displays and notifications.
        WHY: Students and instructors need to know about overdue work.

        Returns:
            True if past due date, False otherwise
        """
        if self.due_date is None:
            return False
        return datetime.utcnow() > self.due_date

    def days_until_due(self) -> Optional[int]:
        """
        Calculate days until milestone is due.

        WHAT: Computes days remaining.
        WHERE: Used in notifications and displays.
        WHY: Helps students prioritize and plan work.

        Returns:
            Days until due (negative if overdue), None if no due date
        """
        if self.due_date is None:
            return None
        delta = self.due_date - datetime.utcnow()
        return delta.days

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "assessment_id": str(self.assessment_id),
            "name": self.name,
            "description": self.description,
            "sort_order": self.sort_order,
            "required_deliverables": self.required_deliverables,
            "acceptance_criteria": self.acceptance_criteria,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "weight": float(self.weight),
            "max_points": float(self.max_points) if self.max_points else None,
            "rubric_id": str(self.rubric_id) if self.rubric_id else None,
            "is_overdue": self.is_overdue(),
            "days_until_due": self.days_until_due(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# PORTFOLIO DOMAIN ENTITIES
# Manage portfolio-based assessments
# ============================================================================

@dataclass
class PortfolioArtifact:
    """
    Individual artifact in a portfolio assessment.

    WHAT: Represents a piece of work included in a portfolio.
    WHERE: Part of portfolio-type AssessmentSubmission.
    WHY: Portfolios demonstrate growth over time through collected work.
         Each artifact shows specific learning with student reflection.

    Business Requirements:
    - Support multiple artifact types (document, code, video, image)
    - Require student reflection explaining artifact inclusion
    - Enable individual artifact evaluation
    - Track creation date for growth demonstration

    Artifact Types:
    - Document: Papers, reports, essays
    - Code: Programs, scripts, projects
    - Video: Presentations, demonstrations
    - Image: Diagrams, artwork, screenshots
    """
    title: str
    submission_id: UUID
    student_id: UUID
    artifact_type: str
    description: Optional[str] = None
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    creation_date: Optional[datetime] = None
    context: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    student_reflection: Optional[str] = None
    learning_demonstrated: Optional[str] = None
    score: Optional[Decimal] = None
    feedback: Optional[str] = None
    evaluated_by: Optional[UUID] = None
    evaluated_at: Optional[datetime] = None
    sort_order: int = 0
    is_featured: bool = False
    id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize and validate artifact."""
        if self.id is None:
            self.id = uuid4()
        if self.creation_date is None:
            self.creation_date = datetime.utcnow()
        self.validate()

    def validate(self) -> None:
        """
        Validate artifact business rules.

        WHAT: Validates artifact definition and content.
        WHERE: Called during creation and before persistence.
        WHY: Artifacts must have valid content for portfolio.

        Raises:
            PortfolioError: If validation fails
        """
        if not self.title or not self.title.strip():
            raise PortfolioError("Artifact title is required")

        if not self.artifact_type or not self.artifact_type.strip():
            raise PortfolioError("Artifact type is required")

        # Must have some content
        if not self.content_url and not self.content_text and not self.attachments:
            raise PortfolioError("Artifact must have content (URL, text, or attachments)")

    def add_reflection(self, reflection: str, learning: Optional[str] = None) -> None:
        """
        Add or update student reflection on artifact.

        WHAT: Records student's explanation of why artifact is included.
        WHERE: Called when student completes portfolio.
        WHY: Reflection is key to portfolio assessment - shows metacognition.

        Args:
            reflection: Student's reflection on the artifact
            learning: Description of learning demonstrated
        """
        if not reflection or not reflection.strip():
            raise PortfolioError("Reflection cannot be empty")

        self.student_reflection = reflection.strip()
        if learning:
            self.learning_demonstrated = learning.strip()
        self.updated_at = datetime.utcnow()

    def evaluate(
        self,
        score: Decimal,
        feedback: str,
        evaluator_id: UUID
    ) -> None:
        """
        Record evaluation of this artifact.

        WHAT: Records score and feedback from evaluator.
        WHERE: Called during portfolio grading.
        WHY: Individual artifacts may be scored within portfolio.

        Args:
            score: Numeric score for artifact
            feedback: Written feedback
            evaluator_id: UUID of evaluator
        """
        if score < 0:
            raise PortfolioError("Score cannot be negative")

        self.score = score
        self.feedback = feedback
        self.evaluated_by = evaluator_id
        self.evaluated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "submission_id": str(self.submission_id),
            "student_id": str(self.student_id),
            "title": self.title,
            "description": self.description,
            "artifact_type": self.artifact_type,
            "content_url": self.content_url,
            "content_text": self.content_text,
            "attachments": self.attachments,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "context": self.context,
            "tags": self.tags,
            "student_reflection": self.student_reflection,
            "learning_demonstrated": self.learning_demonstrated,
            "score": float(self.score) if self.score else None,
            "feedback": self.feedback,
            "evaluated_by": str(self.evaluated_by) if self.evaluated_by else None,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "sort_order": self.sort_order,
            "is_featured": self.is_featured,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# PEER REVIEW DOMAIN ENTITIES
# Manage peer assessment workflow
# ============================================================================

@dataclass
class PeerReviewAssignment:
    """
    Assignment of reviewer to submission.

    WHAT: Links a peer reviewer to a submission for evaluation.
    WHERE: Created when peer review assessment is distributed.
    WHY: Peer review requires tracking who reviews whom and status.
         Supports various anonymity configurations.

    Business Requirements:
    - Assign multiple reviewers per submission
    - Track review completion status
    - Support various anonymity configurations
    - Enforce review deadlines
    """
    submission_id: UUID
    reviewer_id: UUID
    due_date: Optional[datetime] = None
    status: SubmissionStatus = SubmissionStatus.NOT_STARTED
    is_anonymous: bool = True
    show_author_to_reviewer: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    id: Optional[UUID] = None
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize assignment."""
        if self.id is None:
            self.id = uuid4()

    def start_review(self) -> None:
        """
        Mark review as started.

        WHAT: Updates status when reviewer begins review.
        WHERE: Called when reviewer opens submission.
        WHY: Tracks review progress for completion monitoring.
        """
        if self.status != SubmissionStatus.NOT_STARTED:
            raise PeerReviewError("Review has already been started")

        self.status = SubmissionStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete_review(self) -> None:
        """
        Mark review as completed.

        WHAT: Updates status when reviewer submits feedback.
        WHERE: Called when reviewer completes evaluation.
        WHY: Tracks completion for grade release and analytics.
        """
        if self.status == SubmissionStatus.GRADED:
            raise PeerReviewError("Review is already completed")

        self.status = SubmissionStatus.GRADED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_overdue(self) -> bool:
        """Check if review is past due date."""
        if self.due_date is None:
            return False
        return datetime.utcnow() > self.due_date and self.status != SubmissionStatus.GRADED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "submission_id": str(self.submission_id),
            "reviewer_id": str(self.reviewer_id),
            "status": self.status.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "is_anonymous": self.is_anonymous,
            "show_author_to_reviewer": self.show_author_to_reviewer,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_overdue": self.is_overdue(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class PeerReview:
    """
    Peer review feedback submission.

    WHAT: Contains the actual feedback and scores from a peer reviewer.
    WHERE: Created when reviewer completes evaluation.
    WHY: Peer reviews provide diverse perspectives and develop critical
         evaluation skills in reviewers while providing feedback to authors.

    Business Requirements:
    - Support rubric-based scoring
    - Collect qualitative feedback (strengths, improvements, suggestions)
    - Enable review quality rating by submission author
    - Allow instructor quality oversight
    """
    assignment_id: UUID
    submission_id: UUID
    reviewer_id: UUID
    rubric_scores: Dict[str, Any] = field(default_factory=dict)
    overall_score: Optional[Decimal] = None
    overall_feedback: Optional[str] = None
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    specific_suggestions: Optional[str] = None
    helpfulness_rating: Optional[int] = None
    helpfulness_feedback: Optional[str] = None
    instructor_quality_score: Optional[Decimal] = None
    submitted_at: Optional[datetime] = None
    id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize peer review."""
        if self.id is None:
            self.id = uuid4()

    def submit(self) -> None:
        """
        Submit the peer review.

        WHAT: Marks review as submitted.
        WHERE: Called when reviewer completes feedback.
        WHY: Submitted reviews become visible to authors and instructors.

        Raises:
            PeerReviewError: If validation fails
        """
        if self.submitted_at is not None:
            raise PeerReviewError("Review has already been submitted")

        if not self.overall_feedback or not self.overall_feedback.strip():
            raise PeerReviewError("Overall feedback is required")

        self.submitted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def rate_helpfulness(self, rating: int, feedback: Optional[str] = None) -> None:
        """
        Rate the helpfulness of this review.

        WHAT: Records author's rating of review quality.
        WHERE: Called when author reviews the feedback received.
        WHY: Helpfulness ratings improve peer review quality over time
             and can factor into reviewer evaluation.

        Args:
            rating: 1-5 rating of helpfulness
            feedback: Optional explanation of rating

        Raises:
            PeerReviewError: If rating is invalid
        """
        if not 1 <= rating <= 5:
            raise PeerReviewError("Helpfulness rating must be between 1 and 5")

        self.helpfulness_rating = rating
        if feedback:
            self.helpfulness_feedback = feedback.strip()
        self.updated_at = datetime.utcnow()

    def set_instructor_quality_score(self, score: Decimal) -> None:
        """
        Set instructor's quality assessment of this review.

        WHAT: Records instructor evaluation of review quality.
        WHERE: Called during instructor oversight of peer reviews.
        WHY: Ensures peer reviews meet quality standards and
             provides feedback to reviewers on their review skills.

        Args:
            score: Quality score (0-100)
        """
        if not 0 <= score <= 100:
            raise PeerReviewError("Quality score must be between 0 and 100")

        self.instructor_quality_score = score
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "assignment_id": str(self.assignment_id),
            "submission_id": str(self.submission_id),
            "reviewer_id": str(self.reviewer_id),
            "rubric_scores": self.rubric_scores,
            "overall_score": float(self.overall_score) if self.overall_score else None,
            "overall_feedback": self.overall_feedback,
            "strengths": self.strengths,
            "areas_for_improvement": self.areas_for_improvement,
            "specific_suggestions": self.specific_suggestions,
            "helpfulness_rating": self.helpfulness_rating,
            "helpfulness_feedback": self.helpfulness_feedback,
            "instructor_quality_score": float(self.instructor_quality_score) if self.instructor_quality_score else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# MAIN ASSESSMENT AND SUBMISSION ENTITIES
# Core entities for advanced assessment management
# ============================================================================

@dataclass
class AdvancedAssessment:
    """
    Advanced assessment definition supporting multiple assessment types.

    WHAT: Main entity defining an advanced assessment with configuration.
    WHERE: Core entity for all advanced assessment types.
    WHY: Traditional quizzes are insufficient for measuring complex skills.
         Advanced assessments support diverse evaluation methodologies.

    Business Requirements:
    - Support 10 assessment types with specialized workflows
    - Enable rubric-based evaluation
    - Configure peer review settings
    - Map competencies and learning objectives
    - Define project milestones and deliverables
    - Specify portfolio artifact requirements
    - Configure timing, attempts, and late policies

    Key Configuration Areas:
    1. Basic: Title, description, instructions, type
    2. Scoring: Max score, passing score, weight, rubric
    3. Timing: Available dates, due date, time limit
    4. Attempts: Max attempts, best vs latest, revision allowed
    5. Peer Review: Enabled, type, min reviews, rubric
    6. Competencies: Mapped competencies and objectives
    7. Project: Milestones, deliverables
    8. Portfolio: Required artifacts, artifact types
    """
    title: str
    course_id: UUID
    created_by: UUID
    assessment_type: AssessmentType
    description: Optional[str] = None
    instructions: Optional[str] = None
    status: AssessmentStatus = AssessmentStatus.DRAFT
    rubric_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    module_id: Optional[UUID] = None

    # Scoring configuration
    max_score: Decimal = Decimal("100.0")
    passing_score: Optional[Decimal] = None
    weight: Decimal = Decimal("1.0")

    # Timing configuration
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    due_date: Optional[datetime] = None
    late_submission_allowed: bool = False
    late_penalty_percentage: Decimal = Decimal("0")
    time_limit_minutes: Optional[int] = None

    # Attempt configuration
    max_attempts: int = 1
    best_attempt_counts: bool = True
    allow_revision: bool = True

    # Peer review configuration
    peer_review_enabled: bool = False
    peer_review_type: Optional[ReviewType] = None
    min_peer_reviews: int = 3
    peer_review_rubric_id: Optional[UUID] = None

    # Competency mapping
    competencies: List[UUID] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)

    # Project configuration
    milestones: List[ProjectMilestone] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)

    # Portfolio configuration
    required_artifacts: Optional[int] = None
    artifact_types: List[str] = field(default_factory=list)

    # Resources
    resources: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)

    # Analytics
    analytics_enabled: bool = True
    track_time_on_task: bool = True

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1

    # Identity and timestamps
    id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize and validate assessment."""
        if self.id is None:
            self.id = uuid4()
        self.validate()

    def validate(self) -> None:
        """
        Validate assessment business rules.

        WHAT: Validates assessment configuration for type-specific requirements.
        WHERE: Called during creation and modification.
        WHY: Invalid assessments would cause workflow failures.

        Raises:
            AssessmentValidationError: If validation fails
        """
        if not self.title or not self.title.strip():
            raise AssessmentValidationError("Assessment title is required")

        if self.max_score <= 0:
            raise AssessmentValidationError("Maximum score must be positive")

        if self.passing_score is not None and self.passing_score > self.max_score:
            raise AssessmentValidationError("Passing score cannot exceed maximum score")

        if self.weight <= 0:
            raise AssessmentValidationError("Weight must be positive")

        if self.available_from and self.available_until:
            if self.available_until <= self.available_from:
                raise AssessmentValidationError("Available until must be after available from")

        if self.time_limit_minutes is not None and self.time_limit_minutes <= 0:
            raise AssessmentValidationError("Time limit must be positive")

        if self.max_attempts <= 0:
            raise AssessmentValidationError("Max attempts must be positive")

        # Type-specific validation
        if self.assessment_type == AssessmentType.PEER_REVIEW:
            if not self.peer_review_enabled:
                raise AssessmentValidationError("Peer review must be enabled for peer review assessments")
            if self.min_peer_reviews < 1:
                raise AssessmentValidationError("At least one peer review is required")

        if self.assessment_type == AssessmentType.PORTFOLIO:
            if self.required_artifacts is not None and self.required_artifacts <= 0:
                raise AssessmentValidationError("Required artifacts must be positive")

        if self.late_penalty_percentage < 0 or self.late_penalty_percentage > 100:
            raise AssessmentValidationError("Late penalty must be between 0 and 100")

    def publish(self) -> None:
        """
        Publish the assessment making it available to students.

        WHAT: Changes status from draft to published.
        WHERE: Called when instructor is ready to release assessment.
        WHY: Separates assessment creation from availability.

        Raises:
            AssessmentValidationError: If assessment cannot be published
        """
        if self.status != AssessmentStatus.DRAFT:
            raise AssessmentValidationError(
                f"Cannot publish assessment in {self.status.value} status"
            )

        self.status = AssessmentStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """
        Archive the assessment.

        WHAT: Changes status to archived.
        WHERE: Called when assessment is no longer needed.
        WHY: Preserves assessment data while hiding from active use.
        """
        self.status = AssessmentStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def is_available(self) -> bool:
        """
        Check if assessment is currently available to students.

        WHAT: Checks publication status and availability window.
        WHERE: Used to determine if students can access assessment.
        WHY: Controls student access based on status and dates.

        Returns:
            True if assessment is available, False otherwise
        """
        if self.status not in [AssessmentStatus.PUBLISHED, AssessmentStatus.IN_PROGRESS]:
            return False

        now = datetime.utcnow()

        if self.available_from and now < self.available_from:
            return False

        if self.available_until and now > self.available_until:
            return False

        return True

    def is_past_due(self) -> bool:
        """
        Check if assessment is past due date.

        WHAT: Compares current time to due date.
        WHERE: Used for late submission calculation.
        WHY: Late submissions may have penalties or be rejected.

        Returns:
            True if past due, False otherwise
        """
        if self.due_date is None:
            return False
        return datetime.utcnow() > self.due_date

    def calculate_late_penalty(self, submission_time: datetime) -> Decimal:
        """
        Calculate late penalty for a submission.

        WHAT: Computes penalty based on submission time vs due date.
        WHERE: Used when grading late submissions.
        WHY: Late penalties incentivize timely submission.

        Args:
            submission_time: When the submission was made

        Returns:
            Penalty as percentage (0-100)
        """
        if self.due_date is None or submission_time <= self.due_date:
            return Decimal("0")

        if not self.late_submission_allowed:
            return Decimal("100")  # Full penalty (no credit)

        return self.late_penalty_percentage

    def add_milestone(self, milestone: ProjectMilestone) -> None:
        """
        Add a milestone to project assessment.

        WHAT: Adds milestone to project.
        WHERE: Called when configuring project assessment.
        WHY: Projects need milestones for tracking and intermediate evaluation.

        Args:
            milestone: The milestone to add
        """
        if self.assessment_type not in [AssessmentType.PROJECT, AssessmentType.PORTFOLIO]:
            raise AssessmentValidationError(
                "Milestones can only be added to project or portfolio assessments"
            )

        milestone.assessment_id = self.id
        self.milestones.append(milestone)
        self.milestones.sort(key=lambda m: m.sort_order)
        self.updated_at = datetime.utcnow()

    def add_competency(self, competency_id: UUID) -> None:
        """
        Map a competency to this assessment.

        WHAT: Links competency to assessment.
        WHERE: Called when configuring competency mapping.
        WHY: Assessments demonstrate competencies; mapping enables tracking.

        Args:
            competency_id: UUID of competency to map
        """
        if competency_id not in self.competencies:
            self.competencies.append(competency_id)
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "assessment_type": self.assessment_type.value,
            "status": self.status.value,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "course_id": str(self.course_id),
            "module_id": str(self.module_id) if self.module_id else None,
            "created_by": str(self.created_by),
            "rubric_id": str(self.rubric_id) if self.rubric_id else None,
            "max_score": float(self.max_score),
            "passing_score": float(self.passing_score) if self.passing_score else None,
            "weight": float(self.weight),
            "available_from": self.available_from.isoformat() if self.available_from else None,
            "available_until": self.available_until.isoformat() if self.available_until else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "late_submission_allowed": self.late_submission_allowed,
            "late_penalty_percentage": float(self.late_penalty_percentage),
            "time_limit_minutes": self.time_limit_minutes,
            "max_attempts": self.max_attempts,
            "best_attempt_counts": self.best_attempt_counts,
            "allow_revision": self.allow_revision,
            "peer_review_enabled": self.peer_review_enabled,
            "peer_review_type": self.peer_review_type.value if self.peer_review_type else None,
            "min_peer_reviews": self.min_peer_reviews,
            "peer_review_rubric_id": str(self.peer_review_rubric_id) if self.peer_review_rubric_id else None,
            "competencies": [str(c) for c in self.competencies],
            "learning_objectives": self.learning_objectives,
            "milestones": [m.to_dict() for m in self.milestones],
            "deliverables": self.deliverables,
            "required_artifacts": self.required_artifacts,
            "artifact_types": self.artifact_types,
            "resources": self.resources,
            "attachments": self.attachments,
            "analytics_enabled": self.analytics_enabled,
            "track_time_on_task": self.track_time_on_task,
            "tags": self.tags,
            "metadata": self.metadata,
            "version": self.version,
            "is_available": self.is_available(),
            "is_past_due": self.is_past_due(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None
        }


@dataclass
class AssessmentSubmission:
    """
    Student submission for an advanced assessment.

    WHAT: Tracks student work and evaluation for an assessment.
    WHERE: Created when student begins assessment.
    WHY: Submissions contain student work, track progress, and store grades.

    Business Requirements:
    - Support multiple attempts with best/latest selection
    - Track submission content and attachments
    - Record portfolio artifacts and project milestones
    - Calculate scores with late penalties
    - Store instructor feedback and private notes
    - Track time spent on task

    Status Flow:
    not_started -> in_progress -> submitted -> under_review -> graded
                                            -> needs_revision -> revised -> under_review
    """
    assessment_id: UUID
    student_id: UUID
    attempt_number: int = 1
    status: SubmissionStatus = SubmissionStatus.NOT_STARTED

    # Content
    content: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    portfolio_artifacts: List[PortfolioArtifact] = field(default_factory=list)

    # Project tracking
    milestone_progress: Dict[str, Any] = field(default_factory=dict)
    deliverable_status: Dict[str, Any] = field(default_factory=dict)

    # Self-reflection
    self_reflection: Optional[str] = None
    reflection_responses: Dict[str, Any] = field(default_factory=dict)

    # Scoring
    raw_score: Optional[Decimal] = None
    adjusted_score: Optional[Decimal] = None
    final_score: Optional[Decimal] = None
    percentage: Optional[Decimal] = None
    passed: Optional[bool] = None

    # Feedback
    instructor_feedback: Optional[str] = None
    private_notes: Optional[str] = None

    # Timing
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    graded_by: Optional[UUID] = None
    time_spent_minutes: int = 0
    is_late: bool = False
    late_days: int = 0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Identity and timestamps
    id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize submission."""
        if self.id is None:
            self.id = uuid4()

    def start(self) -> None:
        """
        Start working on the assessment.

        WHAT: Changes status to in_progress and records start time.
        WHERE: Called when student begins assessment.
        WHY: Tracks when work started for timing and analytics.

        Raises:
            SubmissionError: If already started
        """
        if self.status != SubmissionStatus.NOT_STARTED:
            raise SubmissionError("Assessment has already been started")

        self.status = SubmissionStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def submit(self, due_date: Optional[datetime] = None) -> None:
        """
        Submit the assessment for evaluation.

        WHAT: Changes status to submitted and calculates lateness.
        WHERE: Called when student submits work.
        WHY: Marks work as ready for evaluation and captures timing.

        Args:
            due_date: Optional due date for lateness calculation

        Raises:
            SubmissionError: If status doesn't allow submission
        """
        if self.status not in [SubmissionStatus.IN_PROGRESS, SubmissionStatus.NEEDS_REVISION, SubmissionStatus.REVISED]:
            raise SubmissionError(f"Cannot submit from {self.status.value} status")

        self.status = SubmissionStatus.SUBMITTED
        self.submitted_at = datetime.utcnow()

        # Calculate time spent
        if self.started_at:
            delta = self.submitted_at - self.started_at
            self.time_spent_minutes = int(delta.total_seconds() / 60)

        # Calculate lateness
        if due_date and self.submitted_at > due_date:
            self.is_late = True
            late_delta = self.submitted_at - due_date
            self.late_days = late_delta.days + (1 if late_delta.seconds > 0 else 0)

        self.updated_at = datetime.utcnow()

    def request_revision(self, feedback: str) -> None:
        """
        Request revision from student.

        WHAT: Changes status to needs_revision with feedback.
        WHERE: Called by evaluator when work needs improvement.
        WHY: Enables formative feedback and iterative improvement.

        Args:
            feedback: Feedback explaining what needs revision
        """
        if self.status not in [SubmissionStatus.SUBMITTED, SubmissionStatus.UNDER_REVIEW]:
            raise SubmissionError(f"Cannot request revision from {self.status.value} status")

        self.status = SubmissionStatus.NEEDS_REVISION
        self.instructor_feedback = feedback
        self.updated_at = datetime.utcnow()

    def submit_revision(self) -> None:
        """
        Submit revised work.

        WHAT: Changes status from needs_revision to revised.
        WHERE: Called when student submits updated work.
        WHY: Tracks revision cycle for workflow.
        """
        if self.status != SubmissionStatus.NEEDS_REVISION:
            raise SubmissionError("Revision not requested")

        self.status = SubmissionStatus.REVISED
        self.updated_at = datetime.utcnow()

    def grade(
        self,
        raw_score: Decimal,
        max_score: Decimal,
        passing_score: Optional[Decimal],
        grader_id: UUID,
        feedback: Optional[str] = None,
        late_penalty: Decimal = Decimal("0")
    ) -> None:
        """
        Record grade for submission.

        WHAT: Sets scores, calculates percentage, and determines pass/fail.
        WHERE: Called when evaluator completes grading.
        WHY: Finalizes evaluation and makes grade available.

        Args:
            raw_score: Score before penalties
            max_score: Maximum possible score
            passing_score: Minimum score to pass
            grader_id: UUID of person grading
            feedback: Optional feedback to student
            late_penalty: Penalty percentage for late submission
        """
        self.raw_score = raw_score

        # Apply late penalty
        if late_penalty > 0:
            penalty_amount = raw_score * (late_penalty / Decimal("100"))
            self.adjusted_score = raw_score - penalty_amount
        else:
            self.adjusted_score = raw_score

        self.final_score = self.adjusted_score
        self.percentage = (self.final_score / max_score * 100) if max_score > 0 else Decimal("0")

        if passing_score is not None:
            self.passed = self.final_score >= passing_score
        else:
            self.passed = self.percentage >= 70  # Default 70% passing

        self.graded_at = datetime.utcnow()
        self.graded_by = grader_id

        if feedback:
            self.instructor_feedback = feedback

        self.status = SubmissionStatus.GRADED
        self.updated_at = datetime.utcnow()

    def add_artifact(self, artifact: PortfolioArtifact) -> None:
        """
        Add artifact to portfolio submission.

        WHAT: Adds artifact to portfolio.
        WHERE: Called when building portfolio.
        WHY: Portfolios consist of multiple artifacts.

        Args:
            artifact: The artifact to add
        """
        artifact.submission_id = self.id
        artifact.student_id = self.student_id
        self.portfolio_artifacts.append(artifact)
        self.updated_at = datetime.utcnow()

    def update_milestone_progress(self, milestone_id: UUID, status: str, notes: Optional[str] = None) -> None:
        """
        Update progress on a project milestone.

        WHAT: Records progress on specific milestone.
        WHERE: Called as student completes milestone work.
        WHY: Tracks project progress at milestone level.

        Args:
            milestone_id: UUID of milestone
            status: Progress status
            notes: Optional progress notes
        """
        self.milestone_progress[str(milestone_id)] = {
            "status": status,
            "notes": notes,
            "updated_at": datetime.utcnow().isoformat()
        }
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "assessment_id": str(self.assessment_id),
            "student_id": str(self.student_id),
            "attempt_number": self.attempt_number,
            "status": self.status.value,
            "content": self.content,
            "attachments": self.attachments,
            "portfolio_artifacts": [a.to_dict() for a in self.portfolio_artifacts],
            "milestone_progress": self.milestone_progress,
            "deliverable_status": self.deliverable_status,
            "self_reflection": self.self_reflection,
            "reflection_responses": self.reflection_responses,
            "raw_score": float(self.raw_score) if self.raw_score else None,
            "adjusted_score": float(self.adjusted_score) if self.adjusted_score else None,
            "final_score": float(self.final_score) if self.final_score else None,
            "percentage": float(self.percentage) if self.percentage else None,
            "passed": self.passed,
            "instructor_feedback": self.instructor_feedback,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "graded_by": str(self.graded_by) if self.graded_by else None,
            "time_spent_minutes": self.time_spent_minutes,
            "is_late": self.is_late,
            "late_days": self.late_days,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class RubricEvaluation:
    """
    Individual criterion evaluation for a submission.

    WHAT: Records score and feedback for one rubric criterion.
    WHERE: Created during rubric-based evaluation.
    WHY: Detailed criterion-level evaluation provides specific feedback
         and enables criterion-level analytics.

    Business Requirements:
    - Score individual criteria with proficiency levels
    - Provide specific feedback per criterion
    - Identify strengths and improvement areas
    - Reference specific evidence from submission
    """
    submission_id: UUID
    criterion_id: UUID
    evaluated_by: UUID
    proficiency_level: Optional[ProficiencyLevel] = None
    points_awarded: Optional[Decimal] = None
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    evidence_references: List[Dict[str, Any]] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize evaluation."""
        if self.id is None:
            self.id = uuid4()

    def update_score(
        self,
        level: ProficiencyLevel,
        points: Decimal,
        feedback: Optional[str] = None
    ) -> None:
        """
        Update the evaluation score.

        WHAT: Sets proficiency level and points with optional feedback.
        WHERE: Called during grading.
        WHY: Allows evaluation updates before final submission.

        Args:
            level: Proficiency level achieved
            points: Points awarded
            feedback: Optional feedback text
        """
        if points < 0:
            raise RubricValidationError("Points cannot be negative")

        self.proficiency_level = level
        self.points_awarded = points
        if feedback:
            self.feedback = feedback
        self.evaluated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "submission_id": str(self.submission_id),
            "criterion_id": str(self.criterion_id),
            "evaluated_by": str(self.evaluated_by),
            "proficiency_level": self.proficiency_level.value if self.proficiency_level else None,
            "points_awarded": float(self.points_awarded) if self.points_awarded else None,
            "feedback": self.feedback,
            "strengths": self.strengths,
            "areas_for_improvement": self.areas_for_improvement,
            "evidence_references": self.evidence_references,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# ANALYTICS ENTITY
# Aggregate assessment analytics
# ============================================================================

@dataclass
class AssessmentAnalytics:
    """
    Aggregated analytics for an assessment.

    WHAT: Stores computed statistics for an assessment.
    WHERE: Updated when submissions are graded.
    WHY: Pre-computed analytics enable fast dashboard loading
         and provide insights into assessment effectiveness.

    Metrics Tracked:
    - Participation: Total students, submissions, completion rate
    - Scores: Average, median, min, max, standard deviation
    - Pass/Fail: Pass count, fail count, pass rate
    - Time: Average and median time to complete
    - Criterion-level: Per-criterion averages and distributions
    - Peer review: Completion rate, score variance
    """
    assessment_id: UUID
    total_students: int = 0
    submissions_count: int = 0
    completed_count: int = 0
    in_progress_count: int = 0

    # Score metrics
    average_score: Optional[Decimal] = None
    median_score: Optional[Decimal] = None
    highest_score: Optional[Decimal] = None
    lowest_score: Optional[Decimal] = None
    score_std_deviation: Optional[Decimal] = None

    # Pass/fail metrics
    pass_count: int = 0
    fail_count: int = 0
    pass_rate: Optional[Decimal] = None

    # Time metrics
    average_time_minutes: Optional[int] = None
    median_time_minutes: Optional[int] = None

    # Criterion-level analytics
    criterion_averages: Dict[str, Decimal] = field(default_factory=dict)
    criterion_distributions: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Peer review metrics
    peer_review_completion_rate: Optional[Decimal] = None
    average_peer_review_score: Optional[Decimal] = None
    peer_review_variance: Optional[Decimal] = None

    # Timestamps
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize analytics."""
        if self.id is None:
            self.id = uuid4()

    def calculate_pass_rate(self) -> None:
        """
        Calculate pass rate from pass/fail counts.

        WHAT: Computes pass rate percentage.
        WHERE: Called when updating analytics.
        WHY: Pass rate is key metric for assessment effectiveness.
        """
        total = self.pass_count + self.fail_count
        if total > 0:
            self.pass_rate = Decimal(self.pass_count) / Decimal(total) * 100
        else:
            self.pass_rate = None

    def update_timestamp(self) -> None:
        """Update calculation timestamp."""
        self.calculated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id) if self.id else None,
            "assessment_id": str(self.assessment_id),
            "total_students": self.total_students,
            "submissions_count": self.submissions_count,
            "completed_count": self.completed_count,
            "in_progress_count": self.in_progress_count,
            "average_score": float(self.average_score) if self.average_score else None,
            "median_score": float(self.median_score) if self.median_score else None,
            "highest_score": float(self.highest_score) if self.highest_score else None,
            "lowest_score": float(self.lowest_score) if self.lowest_score else None,
            "score_std_deviation": float(self.score_std_deviation) if self.score_std_deviation else None,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "pass_rate": float(self.pass_rate) if self.pass_rate else None,
            "average_time_minutes": self.average_time_minutes,
            "median_time_minutes": self.median_time_minutes,
            "criterion_averages": {k: float(v) for k, v in self.criterion_averages.items()},
            "criterion_distributions": self.criterion_distributions,
            "peer_review_completion_rate": float(self.peer_review_completion_rate) if self.peer_review_completion_rate else None,
            "average_peer_review_score": float(self.average_peer_review_score) if self.average_peer_review_score else None,
            "peer_review_variance": float(self.peer_review_variance) if self.peer_review_variance else None,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
