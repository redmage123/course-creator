"""
Advanced Assessment Application Service

WHAT: Application service orchestrating advanced assessment business logic
WHERE: Used by API endpoints to handle advanced assessment operations
WHY: Implements business rules, validation, and coordination between
     domain entities and data access layer for advanced assessments

This service provides operations for:
- Assessment rubric creation and management
- Advanced assessment configuration and lifecycle
- Submission workflow with status transitions
- Rubric-based evaluation with criteria scoring
- Peer review assignment and completion
- Competency tracking and progression
- Portfolio artifact management
- Project milestone tracking
- Assessment analytics aggregation

Business Rules Enforced:
- Rubrics must have at least one criterion
- Assessments must have valid dates (due date > available date)
- Submissions follow valid status transitions
- Peer reviewers cannot review their own work
- Competency levels progress according to defined rules
- Analytics are updated automatically on submission completion
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from asyncpg import Pool

from content_management.domain.entities.advanced_assessment import (
    # Exceptions
    AdvancedAssessmentError,
    AssessmentValidationError,
    RubricValidationError,
    SubmissionError,
    PeerReviewError,
    CompetencyError,
    PortfolioError,
    ProjectError,
    # Enums
    AssessmentType,
    AssessmentStatus,
    SubmissionStatus,
    ProficiencyLevel,
    ReviewType,
    # Rubric entities
    RubricPerformanceLevel,
    RubricCriterion,
    AssessmentRubric,
    # Assessment entities
    AdvancedAssessment,
    AssessmentSubmission,
    RubricEvaluation,
    # Competency entities
    Competency,
    CompetencyProgress,
    # Project entities
    ProjectMilestone,
    # Portfolio entities
    PortfolioArtifact,
    # Peer review entities
    PeerReviewAssignment,
    PeerReview,
    # Analytics
    AssessmentAnalytics,
)
from data_access.advanced_assessment_dao import (
    AdvancedAssessmentDAO,
    AdvancedAssessmentDAOException,
)


class AdvancedAssessmentServiceException(AdvancedAssessmentError):
    """
    WHAT: Exception for service-level errors in advanced assessments
    WHERE: Raised during business logic processing
    WHY: Wraps domain and DAO exceptions with service context,
         providing meaningful error messages for API layer

    Attributes:
        message: Human-readable error description
        details: Additional context for debugging
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        WHAT: Initializes service exception with message and details
        WHERE: Called when raising service-level exceptions
        WHY: Provides consistent exception structure with context

        Args:
            message: Error description
            details: Optional context dictionary
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AdvancedAssessmentService:
    """
    WHAT: Application service for advanced assessment operations
    WHERE: Called by API endpoints for business logic execution
    WHY: Orchestrates operations between presentation and data layers,
         enforcing business rules and coordinating complex workflows

    Responsibilities:
    - Validate assessment and rubric configurations
    - Manage assessment lifecycle (draft -> published -> completed)
    - Handle submission workflows with proper status transitions
    - Coordinate peer review assignments and completions
    - Track competency progress and level progression
    - Maintain portfolio artifacts with reflection requirements
    - Calculate and update assessment analytics

    Attributes:
        pool: Database connection pool for operations
        dao: Data access object for persistence operations
    """

    def __init__(self, pool: Pool):
        """
        WHAT: Initializes the service with database pool
        WHERE: Called during application startup
        WHY: Sets up dependencies for database operations

        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
        self.dao = AdvancedAssessmentDAO(pool)

    # =========================================================================
    # Assessment Rubric Operations
    # =========================================================================

    async def create_rubric(
        self,
        name: str,
        description: str,
        created_by: UUID,
        criteria: List[Dict[str, Any]],
        max_score: int = 100,
        passing_score: int = 70,
        passing_percentage: float = 70.0,
        is_template: bool = False,
        organization_id: Optional[UUID] = None,
        course_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None
    ) -> AssessmentRubric:
        """
        WHAT: Creates a new assessment rubric with criteria and performance levels
        WHERE: Called when instructor creates evaluation rubric
        WHY: Rubrics provide structured, consistent evaluation criteria

        Business Rules:
        - Name is required and must be non-empty
        - At least one criterion is required
        - Each criterion must have at least one performance level
        - Weights should sum appropriately (validated but not enforced strictly)

        Args:
            name: Rubric name for identification
            description: Detailed rubric description
            created_by: UUID of creating user
            criteria: List of criterion definitions with performance levels
            max_score: Maximum possible score (default 100)
            passing_score: Minimum score to pass (default 70)
            passing_percentage: Minimum percentage to pass (default 70.0)
            is_template: Whether this is a reusable template
            organization_id: Optional organization ownership
            course_id: Optional course association
            tags: Optional tags for categorization

        Returns:
            Created AssessmentRubric with all criteria and levels

        Raises:
            AdvancedAssessmentServiceException: If validation fails
        """
        try:
            # Validate inputs
            if not name or len(name.strip()) == 0:
                raise RubricValidationError("Rubric name is required")

            if not criteria or len(criteria) == 0:
                raise RubricValidationError(
                    "At least one criterion is required for rubric"
                )

            # Build criterion entities
            criterion_entities = []
            for i, crit_data in enumerate(criteria):
                # Validate criterion
                if not crit_data.get("name"):
                    raise RubricValidationError(
                        f"Criterion {i+1} must have a name"
                    )

                # Build performance levels
                levels_data = crit_data.get("performance_levels", [])
                if not levels_data:
                    # Create default levels if none provided
                    levels_data = self._create_default_performance_levels(
                        crit_data.get("max_points", 20)
                    )

                level_entities = []
                for j, level_data in enumerate(levels_data):
                    # Get level name and use it as fallback for description
                    level_name = level_data.get("name", "Level")
                    level_desc = level_data.get("description") or f"{level_name} performance level"

                    level_entities.append(RubricPerformanceLevel(
                        id=uuid4(),
                        level=ProficiencyLevel(level_data.get("level", "proficient")),
                        name=level_name,
                        description=level_desc,
                        points=Decimal(str(level_data.get("points", 0))),
                        percentage_of_max=Decimal(str(
                            level_data.get("percentage_of_max", 0)
                        )),
                        color=level_data.get("color", ""),
                        icon=level_data.get("icon", ""),
                        sort_order=j
                    ))

                criterion_entities.append(RubricCriterion(
                    id=uuid4(),
                    name=crit_data.get("name", ""),
                    description=crit_data.get("description", ""),
                    max_points=Decimal(str(crit_data.get("max_points", 20))),
                    weight=Decimal(str(crit_data.get("weight", 1.0))),
                    sort_order=crit_data.get("sort_order", i),
                    category=crit_data.get("category", ""),
                    is_required=crit_data.get("is_required", True),
                    allow_partial_credit=crit_data.get("allow_partial_credit", True),
                    performance_levels=level_entities
                ))

            # Create rubric entity
            rubric = AssessmentRubric(
                id=uuid4(),
                name=name.strip(),
                description=description or "",
                criteria=criterion_entities,
                max_score=Decimal(str(max(1, max_score))),
                passing_score=Decimal(str(max(0, passing_score))),
                passing_percentage=Decimal(str(max(0, min(100, passing_percentage)))),
                is_template=is_template,
                organization_id=organization_id,
                course_id=course_id,
                created_by=created_by,
                tags=tags or []
            )

            return await self.dao.create_rubric(rubric)

        except (RubricValidationError, AdvancedAssessmentError):
            raise
        except AdvancedAssessmentDAOException as e:
            raise AdvancedAssessmentServiceException(
                f"Failed to create rubric: {str(e)}",
                {"name": name, "error": str(e)}
            )
        except Exception as e:
            raise AdvancedAssessmentServiceException(
                f"Unexpected error creating rubric: {str(e)}",
                {"name": name}
            )

    def _create_default_performance_levels(
        self,
        max_points: int
    ) -> List[Dict[str, Any]]:
        """
        WHAT: Creates default performance levels for a criterion
        WHERE: Called when criterion has no levels defined
        WHY: Provides sensible defaults following standard proficiency scale

        Args:
            max_points: Maximum points for the criterion

        Returns:
            List of default performance level definitions
        """
        mp = float(max_points)
        return [
            {
                "level": "not_demonstrated",
                "name": "Not Demonstrated",
                "description": "Criterion not addressed or below minimum",
                "points": 0,
                "percentage_of_max": 0
            },
            {
                "level": "emerging",
                "name": "Emerging",
                "description": "Beginning to demonstrate understanding",
                "points": mp * 0.25,
                "percentage_of_max": 25
            },
            {
                "level": "developing",
                "name": "Developing",
                "description": "Partial demonstration with gaps",
                "points": mp * 0.50,
                "percentage_of_max": 50
            },
            {
                "level": "proficient",
                "name": "Proficient",
                "description": "Meets expectations consistently",
                "points": mp * 0.70,
                "percentage_of_max": 70
            },
            {
                "level": "advanced",
                "name": "Advanced",
                "description": "Exceeds expectations",
                "points": mp * 0.85,
                "percentage_of_max": 85
            },
            {
                "level": "expert",
                "name": "Expert",
                "description": "Exceptional mastery demonstrated",
                "points": mp,
                "percentage_of_max": 100
            }
        ]

    async def get_rubric(self, rubric_id: UUID) -> Optional[AssessmentRubric]:
        """
        WHAT: Retrieves a rubric by ID with all criteria and levels
        WHERE: Called when loading rubric for display or evaluation
        WHY: Provides complete rubric structure for grading

        Args:
            rubric_id: UUID of rubric to retrieve

        Returns:
            AssessmentRubric with criteria, or None if not found
        """
        return await self.dao.get_rubric_by_id(rubric_id)

    async def get_course_rubrics(
        self,
        course_id: UUID,
        include_templates: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[AssessmentRubric]:
        """
        WHAT: Lists rubrics available for a course
        WHERE: Called when instructor selects rubric for assessment
        WHY: Shows available rubrics including organization templates

        Args:
            course_id: Course to filter by
            include_templates: Whether to include template rubrics
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AssessmentRubric
        """
        return await self.dao.get_rubrics_by_course(
            course_id, include_templates, limit, offset
        )

    async def get_template_rubrics(
        self,
        organization_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[AssessmentRubric]:
        """
        WHAT: Retrieves template rubrics for reuse
        WHERE: Called when creating new assessments
        WHY: Templates enable consistent evaluation across courses

        Args:
            organization_id: Optional organization filter
            limit: Maximum results

        Returns:
            List of template AssessmentRubric
        """
        return await self.dao.get_template_rubrics(organization_id, limit)

    async def update_rubric(
        self,
        rubric_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        max_score: Optional[int] = None,
        passing_score: Optional[int] = None,
        passing_percentage: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> AssessmentRubric:
        """
        WHAT: Updates rubric metadata
        WHERE: Called when modifying rubric configuration
        WHY: Allows rubric refinement before or after publication

        Business Rules:
        - Cannot update if rubric has been used for grading (enforced at DAO)
        - Version is incremented automatically

        Args:
            rubric_id: UUID of rubric to update
            name: Optional new name
            description: Optional new description
            max_score: Optional new max score
            passing_score: Optional new passing score
            passing_percentage: Optional new passing percentage
            tags: Optional new tags

        Returns:
            Updated AssessmentRubric

        Raises:
            AdvancedAssessmentServiceException: If rubric not found
        """
        rubric = await self.dao.get_rubric_by_id(rubric_id)
        if not rubric:
            raise AdvancedAssessmentServiceException(
                "Rubric not found",
                {"rubric_id": str(rubric_id)}
            )

        # Update fields
        if name is not None:
            rubric.name = name.strip()
        if description is not None:
            rubric.description = description
        if max_score is not None:
            rubric.max_score = Decimal(str(max(1, max_score)))
        if passing_score is not None:
            rubric.passing_score = Decimal(str(max(0, passing_score)))
        if passing_percentage is not None:
            rubric.passing_percentage = Decimal(str(
                max(0, min(100, passing_percentage))
            ))
        if tags is not None:
            rubric.tags = tags

        return await self.dao.update_rubric(rubric)

    async def delete_rubric(self, rubric_id: UUID) -> bool:
        """
        WHAT: Soft deletes a rubric
        WHERE: Called when removing unused rubric
        WHY: Preserves historical data while hiding from active use

        Args:
            rubric_id: UUID of rubric to delete

        Returns:
            True if deleted, False if not found
        """
        return await self.dao.delete_rubric(rubric_id)

    # =========================================================================
    # Advanced Assessment Operations
    # =========================================================================

    async def create_assessment(
        self,
        title: str,
        description: str,
        assessment_type: AssessmentType,
        course_id: UUID,
        created_by: UUID,
        rubric_id: Optional[UUID] = None,
        module_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        instructions: str = "",
        max_score: int = 100,
        passing_score: int = 70,
        available_from: Optional[datetime] = None,
        available_until: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        time_limit_minutes: int = 0,
        max_attempts: int = 1,
        late_submission_allowed: bool = False,
        late_penalty_percentage: float = 0.0,
        peer_review_enabled: bool = False,
        peer_review_type: Optional[ReviewType] = None,
        min_peer_reviews: int = 3,
        milestones: Optional[List[Dict[str, Any]]] = None,
        competencies: Optional[List[UUID]] = None,
        tags: Optional[List[str]] = None
    ) -> AdvancedAssessment:
        """
        WHAT: Creates a new advanced assessment with full configuration
        WHERE: Called when instructor creates assessment
        WHY: Configures assessment behavior, dates, and evaluation settings

        Business Rules:
        - Title is required
        - Due date must be after available date (if both specified)
        - Peer review assessments must have peer review enabled
        - Project assessments should have milestones

        Args:
            title: Assessment title
            description: Detailed description
            assessment_type: Type of assessment
            course_id: Parent course ID
            created_by: Creating user ID
            rubric_id: Optional associated rubric
            module_id: Optional module placement
            organization_id: Optional organization
            instructions: Student instructions
            max_score: Maximum possible score
            passing_score: Score required to pass
            available_from: When assessment becomes available
            available_until: When assessment becomes unavailable
            due_date: Primary due date
            time_limit_minutes: Time limit (0 = unlimited)
            max_attempts: Maximum submission attempts
            late_submission_allowed: Whether late submissions accepted
            late_penalty_percentage: Penalty per late period
            peer_review_enabled: Whether peer review is enabled
            peer_review_type: Type of peer review (SINGLE_BLIND, DOUBLE_BLIND, OPEN, COLLABORATIVE)
            min_peer_reviews: Minimum number of peer reviews required
            milestones: Milestone definitions for project type
            competencies: Competency UUIDs being assessed
            tags: Categorization tags

        Returns:
            Created AdvancedAssessment

        Raises:
            AdvancedAssessmentServiceException: If validation fails
        """
        try:
            # Validate required fields
            if not title or len(title.strip()) == 0:
                raise AssessmentValidationError("Assessment title is required")

            # Validate date ordering
            if available_from and due_date and due_date <= available_from:
                raise AssessmentValidationError(
                    "Due date must be after available date"
                )

            # Enable peer review for peer review type assessments
            if assessment_type == AssessmentType.PEER_REVIEW:
                peer_review_enabled = True
                if peer_review_type is None:
                    peer_review_type = ReviewType.DOUBLE_BLIND

            # Build milestone entities for project type
            # Note: Milestones need assessment_id, so we create them after assessment
            milestone_entities = []

            # Create assessment entity
            assessment = AdvancedAssessment(
                title=title.strip(),
                course_id=course_id,
                created_by=created_by,
                assessment_type=assessment_type,
                description=description or "",
                instructions=instructions,
                rubric_id=rubric_id,
                organization_id=organization_id,
                module_id=module_id,
                max_score=Decimal(str(max(1, max_score))),
                passing_score=Decimal(str(max(0, passing_score))),
                available_from=available_from,
                available_until=available_until,
                due_date=due_date,
                late_submission_allowed=late_submission_allowed,
                late_penalty_percentage=Decimal(str(
                    max(0, min(100, late_penalty_percentage))
                )),
                time_limit_minutes=max(0, time_limit_minutes) if time_limit_minutes else None,
                max_attempts=max(1, max_attempts),
                peer_review_enabled=peer_review_enabled,
                peer_review_type=peer_review_type,
                min_peer_reviews=min_peer_reviews,
                competencies=competencies or [],
                tags=tags or []
            )

            # Now build milestones with the assessment ID
            if milestones and assessment_type == AssessmentType.PROJECT:
                for i, m in enumerate(milestones):
                    milestone_entities.append(ProjectMilestone(
                        name=m.get("name", f"Milestone {i+1}"),
                        assessment_id=assessment.id,
                        sort_order=m.get("sort_order", i),
                        description=m.get("description"),
                        required_deliverables=m.get("required_deliverables", []),
                        acceptance_criteria=m.get("acceptance_criteria"),
                        due_date=m.get("due_date"),
                        weight=Decimal(str(m.get("weight", 1.0))),
                        max_points=Decimal(str(m.get("max_points", 20))) if m.get("max_points") else None,
                        rubric_id=m.get("rubric_id")
                    ))
                assessment.milestones = milestone_entities

            return await self.dao.create_assessment(assessment)

        except (AssessmentValidationError, AdvancedAssessmentError):
            raise
        except AdvancedAssessmentDAOException as e:
            raise AdvancedAssessmentServiceException(
                f"Failed to create assessment: {str(e)}",
                {"title": title, "type": assessment_type.value}
            )
        except Exception as e:
            raise AdvancedAssessmentServiceException(
                f"Unexpected error creating assessment: {str(e)}",
                {"title": title}
            )

    async def get_assessment(
        self,
        assessment_id: UUID
    ) -> Optional[AdvancedAssessment]:
        """
        WHAT: Retrieves an assessment by ID with all configuration
        WHERE: Called when loading assessment for display or submission
        WHY: Provides complete assessment definition

        Args:
            assessment_id: UUID of assessment

        Returns:
            AdvancedAssessment or None if not found
        """
        return await self.dao.get_assessment_by_id(assessment_id)

    async def get_course_assessments(
        self,
        course_id: UUID,
        assessment_type: Optional[AssessmentType] = None,
        status: Optional[AssessmentStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AdvancedAssessment]:
        """
        WHAT: Lists assessments for a course with filters
        WHERE: Called when viewing course assessment list
        WHY: Provides filtered view of course assessments

        Args:
            course_id: Course to filter by
            assessment_type: Optional type filter
            status: Optional status filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AdvancedAssessment
        """
        return await self.dao.get_assessments_by_course(
            course_id, assessment_type, status, limit, offset
        )

    async def get_available_assessments(
        self,
        course_id: UUID,
        student_id: UUID,
        limit: int = 50
    ) -> List[AdvancedAssessment]:
        """
        WHAT: Gets assessments available for a student
        WHERE: Called when student views available work
        WHY: Shows only published assessments within date range

        Args:
            course_id: Course to filter by
            student_id: Student viewing (for personalization)
            limit: Maximum results

        Returns:
            List of available AdvancedAssessment
        """
        return await self.dao.get_available_assessments(
            course_id, student_id, limit
        )

    async def publish_assessment(
        self,
        assessment_id: UUID
    ) -> AdvancedAssessment:
        """
        WHAT: Publishes a draft assessment
        WHERE: Called when instructor releases assessment
        WHY: Makes assessment available to students

        Business Rules:
        - Only draft assessments can be published
        - Assessment must have valid configuration

        Args:
            assessment_id: UUID of assessment

        Returns:
            Published AdvancedAssessment

        Raises:
            AdvancedAssessmentServiceException: If publication fails
        """
        assessment = await self.dao.get_assessment_by_id(assessment_id)
        if not assessment:
            raise AdvancedAssessmentServiceException(
                "Assessment not found",
                {"assessment_id": str(assessment_id)}
            )

        if assessment.status != AssessmentStatus.DRAFT:
            raise AdvancedAssessmentServiceException(
                f"Cannot publish assessment in {assessment.status.value} status",
                {"current_status": assessment.status.value}
            )

        assessment.status = AssessmentStatus.PUBLISHED
        assessment.published_at = datetime.utcnow()
        return await self.dao.update_assessment(assessment)

    async def archive_assessment(
        self,
        assessment_id: UUID
    ) -> AdvancedAssessment:
        """
        WHAT: Archives an assessment
        WHERE: Called when retiring assessment
        WHY: Hides from active use while preserving history

        Args:
            assessment_id: UUID of assessment

        Returns:
            Archived AdvancedAssessment
        """
        assessment = await self.dao.get_assessment_by_id(assessment_id)
        if not assessment:
            raise AdvancedAssessmentServiceException(
                "Assessment not found",
                {"assessment_id": str(assessment_id)}
            )

        assessment.status = AssessmentStatus.ARCHIVED
        return await self.dao.update_assessment(assessment)

    async def update_assessment(
        self,
        assessment_id: UUID,
        **kwargs
    ) -> AdvancedAssessment:
        """
        WHAT: Updates assessment configuration
        WHERE: Called when modifying assessment settings
        WHY: Allows assessment refinement

        Args:
            assessment_id: UUID of assessment
            **kwargs: Fields to update

        Returns:
            Updated AdvancedAssessment
        """
        assessment = await self.dao.get_assessment_by_id(assessment_id)
        if not assessment:
            raise AdvancedAssessmentServiceException(
                "Assessment not found",
                {"assessment_id": str(assessment_id)}
            )

        # Update allowed fields - using correct entity field names
        updateable = [
            "title", "description", "instructions", "max_score", "passing_score",
            "available_from", "available_until", "due_date",
            "time_limit_minutes", "max_attempts", "late_submission_allowed",
            "late_penalty_percentage", "peer_review_enabled", "peer_review_type",
            "min_peer_reviews", "tags"
        ]

        for field in updateable:
            if field in kwargs and kwargs[field] is not None:
                setattr(assessment, field, kwargs[field])

        return await self.dao.update_assessment(assessment)

    async def delete_assessment(self, assessment_id: UUID) -> bool:
        """
        WHAT: Soft deletes an assessment
        WHERE: Called when removing assessment
        WHY: Preserves submission history

        Args:
            assessment_id: UUID of assessment

        Returns:
            True if deleted
        """
        return await self.dao.delete_assessment(assessment_id)

    # =========================================================================
    # Submission Operations
    # =========================================================================

    async def start_submission(
        self,
        assessment_id: UUID,
        student_id: UUID,
        content: Optional[Dict[str, Any]] = None
    ) -> AssessmentSubmission:
        """
        WHAT: Starts a new submission for a student
        WHERE: Called when student begins assessment
        WHY: Creates submission record and tracks attempt

        Business Rules:
        - Assessment must be published and available
        - Student must not exceed max attempts
        - Student cannot have an in-progress submission

        Args:
            assessment_id: UUID of assessment
            student_id: UUID of student
            content: Optional initial content

        Returns:
            Created AssessmentSubmission

        Raises:
            AdvancedAssessmentServiceException: If validation fails
        """
        assessment = await self.dao.get_assessment_by_id(assessment_id)
        if not assessment:
            raise AdvancedAssessmentServiceException(
                "Assessment not found",
                {"assessment_id": str(assessment_id)}
            )

        # Check availability
        now = datetime.utcnow()
        if assessment.status != AssessmentStatus.PUBLISHED:
            raise SubmissionError(
                "Assessment is not available for submission"
            )

        if assessment.available_from and now < assessment.available_from:
            raise SubmissionError(
                "Assessment is not yet available"
            )

        # Check existing submissions
        existing = await self.dao.get_student_submissions(
            student_id, assessment_id, limit=100
        )
        in_progress = [s for s in existing if s.status == SubmissionStatus.IN_PROGRESS]

        if in_progress:
            # Return existing in-progress submission
            return in_progress[0]

        # Check attempt limit
        completed = [
            s for s in existing
            if s.status in [SubmissionStatus.GRADED, SubmissionStatus.APPROVED]
        ]
        if len(completed) >= assessment.max_attempts:
            raise SubmissionError(
                f"Maximum attempts ({assessment.max_attempts}) reached",
                {"current_attempts": len(completed)}
            )

        # Determine if late
        is_late = False
        if assessment.due_date and now > assessment.due_date:
            if not assessment.late_submission_allowed:
                raise SubmissionError("Assessment due date has passed")
            if assessment.available_until:
                if now > assessment.available_until:
                    raise SubmissionError("Assessment availability period has passed")
            is_late = True

        # Create submission
        submission = AssessmentSubmission(
            id=uuid4(),
            assessment_id=assessment_id,
            student_id=student_id,
            attempt_number=len(existing) + 1,
            status=SubmissionStatus.IN_PROGRESS,
            content=content or {},
            is_late=is_late
        )

        return await self.dao.create_submission(submission)

    async def update_submission_content(
        self,
        submission_id: UUID,
        content: Dict[str, Any],
        reflections: Optional[str] = None
    ) -> AssessmentSubmission:
        """
        WHAT: Updates submission content during work
        WHERE: Called as student works on submission
        WHY: Enables save-as-you-go functionality

        Args:
            submission_id: UUID of submission
            content: Updated content
            reflections: Optional student reflections

        Returns:
            Updated AssessmentSubmission
        """
        submission = await self.dao.get_submission_by_id(submission_id)
        if not submission:
            raise AdvancedAssessmentServiceException(
                "Submission not found",
                {"submission_id": str(submission_id)}
            )

        if submission.status not in [
            SubmissionStatus.IN_PROGRESS,
            SubmissionStatus.NEEDS_REVISION
        ]:
            raise SubmissionError(
                f"Cannot update submission in {submission.status.value} status"
            )

        submission.content = content
        if reflections is not None:
            submission.reflections = reflections

        return await self.dao.update_submission(submission)

    async def submit_assessment(
        self,
        submission_id: UUID,
        final_content: Optional[Dict[str, Any]] = None
    ) -> AssessmentSubmission:
        """
        WHAT: Submits assessment for grading
        WHERE: Called when student completes work
        WHY: Finalizes submission and initiates grading workflow

        Args:
            submission_id: UUID of submission
            final_content: Optional final content update

        Returns:
            Submitted AssessmentSubmission
        """
        submission = await self.dao.get_submission_by_id(submission_id)
        if not submission:
            raise AdvancedAssessmentServiceException(
                "Submission not found",
                {"submission_id": str(submission_id)}
            )

        if submission.status not in [
            SubmissionStatus.IN_PROGRESS,
            SubmissionStatus.NEEDS_REVISION,
            SubmissionStatus.REVISED
        ]:
            raise SubmissionError(
                f"Cannot submit from {submission.status.value} status"
            )

        if final_content:
            submission.content = final_content

        submission.status = SubmissionStatus.SUBMITTED
        submission.submitted_at = datetime.utcnow()

        return await self.dao.update_submission(submission)

    async def get_submission(
        self,
        submission_id: UUID
    ) -> Optional[AssessmentSubmission]:
        """
        WHAT: Retrieves a submission by ID
        WHERE: Called when loading submission for viewing/grading
        WHY: Provides submission data with artifacts

        Args:
            submission_id: UUID of submission

        Returns:
            AssessmentSubmission or None
        """
        return await self.dao.get_submission_by_id(submission_id)

    async def get_student_submissions(
        self,
        student_id: UUID,
        assessment_id: UUID
    ) -> List[AssessmentSubmission]:
        """
        WHAT: Gets all submissions by a student for an assessment
        WHERE: Called when viewing submission history
        WHY: Shows attempt history and progress

        Args:
            student_id: UUID of student
            assessment_id: UUID of assessment

        Returns:
            List of AssessmentSubmission
        """
        return await self.dao.get_student_submissions(student_id, assessment_id)

    async def get_submissions_to_grade(
        self,
        assessment_id: UUID,
        instructor_id: UUID,
        limit: int = 50
    ) -> List[AssessmentSubmission]:
        """
        WHAT: Gets submissions needing grading
        WHERE: Called for instructor grading queue
        WHY: Provides efficient grading workflow

        Args:
            assessment_id: UUID of assessment
            instructor_id: Instructor requesting
            limit: Maximum results

        Returns:
            List of submissions awaiting grading
        """
        return await self.dao.get_submissions_to_grade(assessment_id, limit)

    # =========================================================================
    # Evaluation Operations
    # =========================================================================

    async def grade_submission(
        self,
        submission_id: UUID,
        grader_id: UUID,
        total_score: Decimal,
        criterion_scores: Optional[Dict[str, Dict[str, Any]]] = None,
        feedback: str = "",
        passed: Optional[bool] = None
    ) -> Tuple[AssessmentSubmission, List[RubricEvaluation]]:
        """
        WHAT: Grades a submission using rubric criteria
        WHERE: Called when instructor evaluates work
        WHY: Records structured evaluation with criterion-level scores

        Args:
            submission_id: UUID of submission
            grader_id: UUID of grading user
            total_score: Overall score
            criterion_scores: Dict mapping criterion_id to evaluation data
                              {"criterion_uuid": {"proficiency_level": "...", "points": n, "feedback": "..."}}
            feedback: Overall feedback
            passed: Whether submission passes (auto-calculated if None)

        Returns:
            Tuple of (updated submission, list of evaluations)

        Raises:
            AdvancedAssessmentServiceException: If grading fails
        """
        submission = await self.dao.get_submission_by_id(submission_id)
        if not submission:
            raise AdvancedAssessmentServiceException(
                "Submission not found",
                {"submission_id": str(submission_id)}
            )

        if submission.status not in [
            SubmissionStatus.SUBMITTED,
            SubmissionStatus.UNDER_REVIEW,
            SubmissionStatus.REVISED
        ]:
            raise SubmissionError(
                f"Cannot grade submission in {submission.status.value} status"
            )

        # Get assessment for passing score
        assessment = await self.dao.get_assessment_by_id(submission.assessment_id)
        if not assessment:
            raise AdvancedAssessmentServiceException(
                "Assessment not found"
            )

        # Calculate pass/fail
        if passed is None:
            passed = total_score >= assessment.passing_score

        # Apply late penalty if applicable
        final_score = total_score
        if submission.is_late and assessment.late_penalty_percentage > 0:
            penalty = total_score * (assessment.late_penalty_percentage / 100)
            final_score = total_score - penalty

        # Create individual criterion evaluations if provided
        evaluations = []
        if criterion_scores:
            for criterion_id_str, score_data in criterion_scores.items():
                criterion_id = UUID(criterion_id_str) if isinstance(criterion_id_str, str) else criterion_id_str
                evaluation = RubricEvaluation(
                    submission_id=submission_id,
                    criterion_id=criterion_id,
                    evaluated_by=grader_id,
                    proficiency_level=score_data.get("proficiency_level"),
                    points_awarded=Decimal(str(score_data.get("points", 0))),
                    feedback=score_data.get("feedback"),
                    strengths=score_data.get("strengths"),
                    areas_for_improvement=score_data.get("areas_for_improvement")
                )
                saved_eval = await self.dao.create_evaluation(evaluation)
                evaluations.append(saved_eval)

        # Update submission
        submission.status = SubmissionStatus.GRADED
        submission.graded_by = grader_id
        submission.graded_at = datetime.utcnow()
        submission.final_score = final_score
        submission.passed = passed
        submission.instructor_feedback = feedback
        submission = await self.dao.update_submission(submission)

        # Update analytics
        await self._update_assessment_analytics(assessment.id)

        return submission, evaluations

    async def request_revision(
        self,
        submission_id: UUID,
        grader_id: UUID,
        revision_notes: str,
        criterion_feedback: Optional[List[Dict[str, Any]]] = None
    ) -> AssessmentSubmission:
        """
        WHAT: Requests revision from student
        WHERE: Called when work needs improvement before grading
        WHY: Provides feedback loop for quality improvement

        Args:
            submission_id: UUID of submission
            grader_id: Requesting instructor
            revision_notes: What needs to be improved
            criterion_feedback: Optional criterion-specific feedback

        Returns:
            Updated AssessmentSubmission
        """
        submission = await self.dao.get_submission_by_id(submission_id)
        if not submission:
            raise AdvancedAssessmentServiceException(
                "Submission not found",
                {"submission_id": str(submission_id)}
            )

        submission.status = SubmissionStatus.NEEDS_REVISION
        submission.revision_count += 1
        submission.revision_notes = revision_notes
        if criterion_feedback:
            submission.content["criterion_feedback"] = criterion_feedback

        return await self.dao.update_submission(submission)

    # =========================================================================
    # Peer Review Operations
    # =========================================================================

    async def assign_peer_reviewers(
        self,
        assessment_id: UUID,
        submission_id: UUID,
        reviewer_ids: List[UUID]
    ) -> List[PeerReviewAssignment]:
        """
        WHAT: Assigns peer reviewers to a submission
        WHERE: Called after submission deadline
        WHY: Distributes work for peer evaluation

        Business Rules:
        - Reviewer cannot be the submission author
        - Each reviewer should have balanced workload
        - Respects assessment peer review config

        Args:
            assessment_id: UUID of assessment
            submission_id: UUID of submission
            reviewer_ids: List of reviewer UUIDs

        Returns:
            List of created PeerReviewAssignment
        """
        submission = await self.dao.get_submission_by_id(submission_id)
        if not submission:
            raise AdvancedAssessmentServiceException(
                "Submission not found"
            )

        assessment = await self.dao.get_assessment_by_id(assessment_id)
        if not assessment:
            raise AdvancedAssessmentServiceException(
                "Assessment not found"
            )

        # Validate reviewers
        assignments = []
        config = assessment.peer_review_config or {}
        deadline = datetime.utcnow() + timedelta(
            days=config.get("review_deadline_days_after_due", 7)
        )

        for reviewer_id in reviewer_ids:
            if reviewer_id == submission.student_id:
                if not config.get("allow_self_review", False):
                    continue  # Skip self-review if not allowed

            # Determine anonymity based on review type
            is_anonymous = assessment.peer_review_type in [
                ReviewType.SINGLE_BLIND, ReviewType.DOUBLE_BLIND
            ]
            show_author = assessment.peer_review_type == ReviewType.OPEN

            assignment = PeerReviewAssignment(
                submission_id=submission_id,
                reviewer_id=reviewer_id,
                due_date=deadline,
                status=SubmissionStatus.NOT_STARTED,
                is_anonymous=is_anonymous,
                show_author_to_reviewer=show_author
            )
            created = await self.dao.create_peer_review_assignment(assignment)
            assignments.append(created)

        return assignments

    async def get_reviewer_assignments(
        self,
        reviewer_id: UUID,
        assessment_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[PeerReviewAssignment]:
        """
        WHAT: Gets peer review assignments for a reviewer
        WHERE: Called when reviewer views their queue
        WHY: Shows assigned reviews to complete

        Args:
            reviewer_id: UUID of reviewer
            assessment_id: Optional assessment filter
            status: Optional status filter

        Returns:
            List of PeerReviewAssignment
        """
        return await self.dao.get_assignments_for_reviewer(
            reviewer_id, assessment_id, status
        )

    async def submit_peer_review(
        self,
        assignment_id: UUID,
        reviewer_id: UUID,
        criterion_scores: List[Dict[str, Any]],
        total_score: Decimal,
        feedback: str,
        strengths: Optional[List[str]] = None,
        areas_for_improvement: Optional[List[str]] = None
    ) -> PeerReview:
        """
        WHAT: Submits a peer review
        WHERE: Called when reviewer completes evaluation
        WHY: Records peer feedback and scoring

        Args:
            assignment_id: UUID of assignment
            reviewer_id: UUID of reviewer
            criterion_scores: Scores per criterion
            total_score: Overall score given
            feedback: Written feedback
            strengths: List of identified strengths
            areas_for_improvement: List of improvement areas

        Returns:
            Created PeerReview
        """
        assignment = await self.dao.get_peer_assignment_by_id(assignment_id)
        if not assignment:
            raise AdvancedAssessmentServiceException(
                "Assignment not found"
            )

        if assignment.reviewer_id != reviewer_id:
            raise PeerReviewError(
                "Reviewer does not match assignment"
            )

        # Create review using correct entity field names
        review = PeerReview(
            assignment_id=assignment_id,
            submission_id=assignment.submission_id,
            reviewer_id=reviewer_id,
            rubric_scores=criterion_scores,  # Maps criterion_scores to rubric_scores
            overall_score=total_score,
            overall_feedback=feedback,
            strengths=strengths or [],
            areas_for_improvement=areas_for_improvement or []
        )
        review = await self.dao.create_peer_review(review)

        # Update assignment status
        assignment.status = "completed"
        assignment.completed_at = datetime.utcnow()
        await self.dao.update_peer_assignment(assignment)

        return review

    async def get_peer_reviews_for_submission(
        self,
        submission_id: UUID
    ) -> List[PeerReview]:
        """
        WHAT: Gets all peer reviews for a submission
        WHERE: Called when viewing aggregated feedback
        WHY: Shows all peer evaluations to student/instructor

        Args:
            submission_id: UUID of submission

        Returns:
            List of PeerReview
        """
        return await self.dao.get_reviews_for_submission(submission_id)

    # =========================================================================
    # Competency Operations
    # =========================================================================

    async def create_competency(
        self,
        name: str,
        code: str,
        description: str,
        organization_id: UUID,
        category: str = "",
        parent_id: Optional[UUID] = None,
        level: int = 1,  # Must be >= 1 per entity validation
        required_proficiency: ProficiencyLevel = ProficiencyLevel.PROFICIENT,
        evidence_requirements: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Competency:
        """
        WHAT: Creates a new competency definition
        WHERE: Called when defining organizational competencies
        WHY: Establishes measurable skills for competency-based assessment

        Args:
            name: Competency name
            code: Unique competency code
            description: Detailed description
            organization_id: Owning organization
            category: Competency category
            parent_id: Parent competency for hierarchy
            level: Hierarchy level (0 = root)
            required_proficiency: Minimum proficiency level required
            evidence_requirements: Evidence needed to demonstrate competency
            tags: Categorization tags

        Returns:
            Created Competency
        """
        # Check for duplicate code
        existing = await self.dao.get_competency_by_code(code, organization_id)
        if existing:
            raise CompetencyError(
                f"Competency with code '{code}' already exists"
            )

        competency = Competency(
            code=code.strip().upper(),
            name=name.strip(),
            required_proficiency=required_proficiency,
            description=description,
            category=category,
            parent_id=parent_id,
            level=level,
            evidence_requirements=evidence_requirements or [],
            organization_id=organization_id,
            tags=tags or []
        )

        return await self.dao.create_competency(competency)

    async def get_competency(
        self,
        competency_id: UUID
    ) -> Optional[Competency]:
        """
        WHAT: Retrieves a competency by ID
        WHERE: Called when viewing competency details
        WHY: Provides competency definition

        Args:
            competency_id: UUID of competency

        Returns:
            Competency or None
        """
        return await self.dao.get_competency_by_id(competency_id)

    async def get_organization_competencies(
        self,
        organization_id: UUID,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Competency]:
        """
        WHAT: Lists competencies for an organization
        WHERE: Called when viewing competency framework
        WHY: Shows available competencies for mapping

        Args:
            organization_id: Organization to filter by
            category: Optional category filter
            limit: Maximum results

        Returns:
            List of Competency
        """
        return await self.dao.get_competencies_by_organization(
            organization_id, category, limit
        )

    async def update_student_competency(
        self,
        student_id: UUID,
        competency_id: UUID,
        assessment_id: UUID,
        demonstrated_level: ProficiencyLevel,
        evidence_notes: str = "",
        score: Optional[Decimal] = None
    ) -> CompetencyProgress:
        """
        WHAT: Updates student's competency progress
        WHERE: Called after competency assessment
        WHY: Tracks student skill development

        Args:
            student_id: UUID of student
            competency_id: UUID of competency
            assessment_id: Assessment providing evidence
            demonstrated_level: Level demonstrated
            evidence_notes: Notes about demonstration
            score: Optional numeric score

        Returns:
            Updated CompetencyProgress
        """
        # Get or create progress record
        progress = await self.dao.get_student_competency_progress(
            student_id, competency_id
        )

        now = datetime.utcnow()

        if not progress:
            # Create new progress record with correct entity fields
            progress = CompetencyProgress(
                student_id=student_id,
                competency_id=competency_id,
                current_level=demonstrated_level,
                previous_level=ProficiencyLevel.NOT_DEMONSTRATED,
                evidence_submissions=[{
                    "assessment_id": str(assessment_id),
                    "level": demonstrated_level.value,
                    "date": now.isoformat(),
                    "notes": evidence_notes
                }],
                assessor_notes=evidence_notes,
                first_demonstrated_at=now,
                level_achieved_at=now
            )
            return await self.dao.create_competency_progress(progress)
        else:
            # Update if new level is higher
            if self._compare_proficiency_levels(
                demonstrated_level, progress.current_level
            ) > 0:
                progress.previous_level = progress.current_level
                progress.current_level = demonstrated_level
                progress.level_achieved_at = now

            # Add evidence submission to history
            if progress.evidence_submissions is None:
                progress.evidence_submissions = []
            progress.evidence_submissions.append({
                "assessment_id": str(assessment_id),
                "level": demonstrated_level.value,
                "date": now.isoformat(),
                "notes": evidence_notes
            })
            progress.assessor_notes = evidence_notes

            return await self.dao.update_competency_progress(progress)

    def _compare_proficiency_levels(
        self,
        level1: ProficiencyLevel,
        level2: ProficiencyLevel
    ) -> int:
        """
        WHAT: Compares two proficiency levels
        WHERE: Used in competency progression
        WHY: Determines if new level is higher than current

        Args:
            level1: First level
            level2: Second level

        Returns:
            1 if level1 > level2, -1 if level1 < level2, 0 if equal
        """
        order = [
            ProficiencyLevel.NOT_DEMONSTRATED,
            ProficiencyLevel.EMERGING,
            ProficiencyLevel.DEVELOPING,
            ProficiencyLevel.PROFICIENT,
            ProficiencyLevel.ADVANCED,
            ProficiencyLevel.EXPERT
        ]
        idx1 = order.index(level1)
        idx2 = order.index(level2)
        if idx1 > idx2:
            return 1
        elif idx1 < idx2:
            return -1
        return 0

    async def get_student_competencies(
        self,
        student_id: UUID,
        organization_id: Optional[UUID] = None
    ) -> List[CompetencyProgress]:
        """
        WHAT: Gets all competency progress for a student
        WHERE: Called when viewing student profile
        WHY: Shows comprehensive skill development

        Args:
            student_id: UUID of student
            organization_id: Optional org filter

        Returns:
            List of CompetencyProgress
        """
        return await self.dao.get_student_competencies(
            student_id, organization_id
        )

    # =========================================================================
    # Portfolio Operations
    # =========================================================================

    async def add_portfolio_artifact(
        self,
        submission_id: UUID,
        student_id: UUID,
        title: str,
        description: str,
        artifact_type: str,
        content_url: Optional[str] = None,
        content_text: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        student_reflection: str = "",
        context: str = "",
        learning_demonstrated: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> PortfolioArtifact:
        """
        WHAT: Adds an artifact to a portfolio submission
        WHERE: Called when student adds work sample
        WHY: Builds evidence of learning and growth

        Args:
            submission_id: UUID of portfolio submission
            student_id: UUID of student
            title: Artifact title
            description: Description of work
            artifact_type: Type of artifact
            content_url: URL of uploaded file/content
            content_text: Text content of artifact
            attachments: List of attachment metadata
            student_reflection: Student reflection on artifact
            context: Context for the artifact creation
            learning_demonstrated: Learning outcomes demonstrated
            tags: Categorization tags

        Returns:
            Created PortfolioArtifact
        """
        artifact = PortfolioArtifact(
            title=title.strip(),
            submission_id=submission_id,
            student_id=student_id,
            artifact_type=artifact_type,
            description=description,
            content_url=content_url,
            content_text=content_text,
            attachments=attachments or [],
            context=context,
            tags=tags or [],
            student_reflection=student_reflection,
            learning_demonstrated=learning_demonstrated or []
        )

        return await self.dao.create_artifact(artifact)

    async def update_artifact(
        self,
        artifact_id: UUID,
        **kwargs
    ) -> PortfolioArtifact:
        """
        WHAT: Updates a portfolio artifact
        WHERE: Called when editing artifact
        WHY: Allows artifact refinement

        Args:
            artifact_id: UUID of artifact
            **kwargs: Fields to update

        Returns:
            Updated PortfolioArtifact
        """
        artifact = await self.dao.get_artifact_by_id(artifact_id)
        if not artifact:
            raise AdvancedAssessmentServiceException(
                "Artifact not found",
                {"artifact_id": str(artifact_id)}
            )

        updateable = [
            "title", "description", "student_reflection", "content_url",
            "content_text", "attachments", "tags", "context", "learning_demonstrated"
        ]

        for field in updateable:
            if field in kwargs and kwargs[field] is not None:
                setattr(artifact, field, kwargs[field])

        return await self.dao.update_artifact(artifact)

    async def delete_artifact(self, artifact_id: UUID) -> bool:
        """
        WHAT: Deletes a portfolio artifact
        WHERE: Called when removing artifact
        WHY: Allows artifact removal before submission

        Args:
            artifact_id: UUID of artifact

        Returns:
            True if deleted
        """
        return await self.dao.delete_artifact(artifact_id)

    # =========================================================================
    # Project Milestone Operations
    # =========================================================================

    async def add_milestone(
        self,
        assessment_id: UUID,
        name: str,
        description: str,
        due_date: Optional[datetime] = None,
        weight: float = 1.0,
        max_points: int = 20,
        required_deliverables: Optional[List[str]] = None,
        acceptance_criteria: Optional[str] = None,
        sort_order: int = 0,
        rubric_id: Optional[UUID] = None
    ) -> ProjectMilestone:
        """
        WHAT: Adds a milestone to a project assessment
        WHERE: Called when configuring project structure
        WHY: Breaks project into manageable checkpoints

        Args:
            assessment_id: UUID of project assessment
            name: Milestone name
            description: What to accomplish
            due_date: Milestone deadline
            weight: Importance weight
            max_points: Maximum points for milestone
            required_deliverables: Required deliverables list
            acceptance_criteria: Criteria for acceptance
            sort_order: Order in project
            rubric_id: Optional rubric for evaluation

        Returns:
            Created ProjectMilestone
        """
        milestone = ProjectMilestone(
            name=name.strip(),
            assessment_id=assessment_id,
            sort_order=sort_order,
            description=description,
            required_deliverables=required_deliverables or [],
            acceptance_criteria=acceptance_criteria,
            due_date=due_date,
            weight=Decimal(str(weight)),
            max_points=Decimal(str(max_points)),
            rubric_id=rubric_id
        )

        return await self.dao.create_milestone(milestone)

    async def update_milestone(
        self,
        milestone_id: UUID,
        **kwargs
    ) -> ProjectMilestone:
        """
        WHAT: Updates a project milestone
        WHERE: Called when modifying milestone
        WHY: Allows milestone adjustment

        Args:
            milestone_id: UUID of milestone
            **kwargs: Fields to update

        Returns:
            Updated ProjectMilestone
        """
        milestone = await self.dao.get_milestone_by_id(milestone_id)
        if not milestone:
            raise AdvancedAssessmentServiceException(
                "Milestone not found"
            )

        updateable = [
            "name", "description", "due_date", "weight",
            "max_points", "required_deliverables", "acceptance_criteria",
            "sort_order", "rubric_id"
        ]

        for field in updateable:
            if field in kwargs and kwargs[field] is not None:
                setattr(milestone, field, kwargs[field])

        return await self.dao.update_milestone(milestone)

    async def delete_milestone(self, milestone_id: UUID) -> bool:
        """
        WHAT: Deletes a project milestone
        WHERE: Called when removing milestone
        WHY: Allows project restructuring

        Args:
            milestone_id: UUID of milestone

        Returns:
            True if deleted
        """
        return await self.dao.delete_milestone(milestone_id)

    # =========================================================================
    # Analytics Operations
    # =========================================================================

    async def _update_assessment_analytics(
        self,
        assessment_id: UUID
    ) -> AssessmentAnalytics:
        """
        WHAT: Updates analytics for an assessment
        WHERE: Called after submission grading
        WHY: Maintains current statistics

        Args:
            assessment_id: UUID of assessment

        Returns:
            Updated AssessmentAnalytics
        """
        # Get all submissions
        submissions = await self.dao.get_submissions_by_assessment(
            assessment_id, status=None, limit=1000, offset=0
        )

        # Count different states
        in_progress = [s for s in submissions if s.status == SubmissionStatus.IN_PROGRESS]
        completed = [
            s for s in submissions
            if s.status in [SubmissionStatus.GRADED, SubmissionStatus.APPROVED]
        ]

        if not completed:
            # No completed submissions yet - using correct field names
            analytics = AssessmentAnalytics(
                assessment_id=assessment_id,
                submissions_count=len(submissions),
                in_progress_count=len(in_progress),
                completed_count=0
            )
            return await self.dao.create_or_update_analytics(analytics)

        scores = [float(s.final_score or 0) for s in completed]
        passed = [s for s in completed if s.passed]
        failed = [s for s in completed if not s.passed]

        # Using correct AssessmentAnalytics field names
        analytics = AssessmentAnalytics(
            assessment_id=assessment_id,
            submissions_count=len(submissions),
            completed_count=len(completed),
            in_progress_count=len(in_progress),
            pass_count=len(passed),
            fail_count=len(failed),
            average_score=Decimal(str(sum(scores) / len(scores))),
            median_score=Decimal(str(sorted(scores)[len(scores) // 2])),
            highest_score=Decimal(str(max(scores))),
            lowest_score=Decimal(str(min(scores))),
            pass_rate=Decimal(str(len(passed) / len(completed) * 100))
        )

        return await self.dao.create_or_update_analytics(analytics)

    def _calculate_distribution(
        self,
        scores: List[float]
    ) -> Dict[str, int]:
        """
        WHAT: Calculates score distribution buckets
        WHERE: Used in analytics update
        WHY: Provides visual distribution data

        Args:
            scores: List of numeric scores

        Returns:
            Dictionary of score ranges to counts
        """
        distribution = {
            "0-59": 0,
            "60-69": 0,
            "70-79": 0,
            "80-89": 0,
            "90-100": 0
        }

        for score in scores:
            if score < 60:
                distribution["0-59"] += 1
            elif score < 70:
                distribution["60-69"] += 1
            elif score < 80:
                distribution["70-79"] += 1
            elif score < 90:
                distribution["80-89"] += 1
            else:
                distribution["90-100"] += 1

        return distribution

    async def get_assessment_analytics(
        self,
        assessment_id: UUID
    ) -> Optional[AssessmentAnalytics]:
        """
        WHAT: Retrieves analytics for an assessment
        WHERE: Called when viewing assessment statistics
        WHY: Provides performance insights

        Args:
            assessment_id: UUID of assessment

        Returns:
            AssessmentAnalytics or None
        """
        return await self.dao.get_analytics_by_assessment(assessment_id)
