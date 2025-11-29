"""
Advanced Assessment Data Access Object (DAO)

WHAT: Data access layer for advanced assessment CRUD operations and queries
WHERE: Used by AdvancedAssessmentService for all database operations
WHY: Provides abstraction over database operations following the DAO pattern,
     ensuring separation of concerns between business logic and persistence

This module provides CRUD operations for:
- Assessment Rubrics (with criteria and performance levels)
- Advanced Assessments
- Assessment Submissions
- Rubric Evaluations
- Competencies and Progress
- Project Milestones
- Portfolio Artifacts
- Peer Review Assignments and Reviews
- Assessment Analytics

Architecture:
Following the Repository pattern with asyncpg, this DAO:
- Uses connection pooling for efficient database access
- Supports transaction participation via optional connection parameter
- Converts database rows to domain entities
- Wraps all database exceptions in custom DAO exceptions
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from asyncpg import Pool, Record, Connection

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


class AdvancedAssessmentDAOException(AdvancedAssessmentError):
    """
    WHAT: Exception for DAO-specific errors
    WHERE: Raised during database operations
    WHY: Wraps database errors with context for debugging
         and proper exception handling at service layer
    """
    pass


class AdvancedAssessmentDAO:
    """
    WHAT: Data Access Object for advanced assessment operations
    WHERE: Used by AdvancedAssessmentService for persistence
    WHY: Encapsulates all database interactions following repository pattern,
         providing clean separation between domain logic and data access

    Attributes:
        pool: AsyncPG connection pool for database operations
    """

    def __init__(self, pool: Pool):
        """
        WHAT: Initializes the DAO with a connection pool
        WHERE: Called during service initialization
        WHY: Provides database connectivity for all operations

        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool

    # =========================================================================
    # Assessment Rubric Operations
    # =========================================================================

    async def create_rubric(
        self,
        rubric: AssessmentRubric,
        conn: Optional[Connection] = None
    ) -> AssessmentRubric:
        """
        WHAT: Creates a new assessment rubric with criteria and performance levels
        WHERE: Called when creating rubric-based assessments
        WHY: Persists complete rubric structure for evaluation

        Args:
            rubric: AssessmentRubric to create
            conn: Optional connection for transaction support

        Returns:
            Created AssessmentRubric with database-assigned values

        Raises:
            AdvancedAssessmentDAOException: If creation fails
        """
        query = """
            INSERT INTO assessment_rubrics (
                id, name, description, max_score, passing_score, passing_percentage,
                is_template, organization_id, course_id, created_by, tags, version,
                is_active, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
            )
            RETURNING *
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    actual_conn = conn or connection

                    row = await actual_conn.fetchrow(
                        query,
                        rubric.id,
                        rubric.name,
                        rubric.description,
                        rubric.max_score,
                        rubric.passing_score,
                        rubric.passing_percentage,
                        rubric.is_template,
                        rubric.organization_id,
                        rubric.course_id,
                        rubric.created_by,
                        rubric.tags,
                        rubric.version,
                        rubric.is_active,
                        rubric.created_at,
                        rubric.updated_at
                    )

                    # Create criteria
                    for criterion in rubric.criteria:
                        await self._create_criterion(criterion, rubric.id, actual_conn)

                    return self._row_to_rubric(row, rubric.criteria)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create rubric: {str(e)}",
                {"rubric_id": str(rubric.id), "error": str(e)}
            )

    async def _create_criterion(
        self,
        criterion: RubricCriterion,
        rubric_id: UUID,
        conn: Connection
    ) -> None:
        """
        WHAT: Creates a rubric criterion with performance levels
        WHERE: Called during rubric creation
        WHY: Persists individual evaluation dimensions

        Args:
            criterion: RubricCriterion to create
            rubric_id: Parent rubric ID
            conn: Database connection
        """
        query = """
            INSERT INTO rubric_criteria (
                id, rubric_id, name, description, max_points, weight,
                sort_order, category, is_required, allow_partial_credit,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """
        await conn.execute(
            query,
            criterion.id,
            rubric_id,
            criterion.name,
            criterion.description,
            criterion.max_points,
            criterion.weight,
            criterion.sort_order,
            criterion.category,
            criterion.is_required,
            criterion.allow_partial_credit,
            criterion.created_at,
            criterion.updated_at
        )

        # Create performance levels
        for level in criterion.performance_levels:
            await self._create_performance_level(level, criterion.id, conn)

    async def _create_performance_level(
        self,
        level: RubricPerformanceLevel,
        criterion_id: UUID,
        conn: Connection
    ) -> None:
        """
        WHAT: Creates a performance level for a criterion
        WHERE: Called during criterion creation
        WHY: Defines proficiency level descriptions for evaluation

        Args:
            level: RubricPerformanceLevel to create
            criterion_id: Parent criterion ID
            conn: Database connection
        """
        query = """
            INSERT INTO rubric_performance_levels (
                id, criterion_id, level, name, description, points,
                percentage_of_max, color, icon, sort_order, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        await conn.execute(
            query,
            level.id,
            criterion_id,
            level.level.value,
            level.name,
            level.description,
            level.points,
            level.percentage_of_max,
            level.color,
            level.icon,
            level.sort_order,
            level.created_at
        )

    async def get_rubric_by_id(
        self,
        rubric_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[AssessmentRubric]:
        """
        WHAT: Retrieves a rubric by ID with all criteria and performance levels
        WHERE: Called when loading rubric for evaluation
        WHY: Provides complete rubric structure for grading

        Args:
            rubric_id: UUID of rubric to retrieve
            conn: Optional connection

        Returns:
            AssessmentRubric with criteria and levels, or None if not found
        """
        connection = conn or self.pool

        row = await connection.fetchrow(
            "SELECT * FROM assessment_rubrics WHERE id = $1", rubric_id
        )
        if not row:
            return None

        # Get criteria
        criteria = await self._get_criteria_for_rubric(rubric_id, connection)

        return self._row_to_rubric(row, criteria)

    async def _get_criteria_for_rubric(
        self,
        rubric_id: UUID,
        conn: Connection
    ) -> List[RubricCriterion]:
        """
        WHAT: Gets all criteria for a rubric with performance levels
        WHERE: Called when loading rubric
        WHY: Criteria are needed for complete rubric representation

        Args:
            rubric_id: Parent rubric ID
            conn: Database connection

        Returns:
            List of RubricCriterion with performance levels
        """
        criteria_rows = await conn.fetch(
            "SELECT * FROM rubric_criteria WHERE rubric_id = $1 ORDER BY sort_order",
            rubric_id
        )

        criteria = []
        for criterion_row in criteria_rows:
            levels_rows = await conn.fetch(
                "SELECT * FROM rubric_performance_levels WHERE criterion_id = $1 ORDER BY sort_order",
                criterion_row['id']
            )
            levels = [self._row_to_performance_level(r) for r in levels_rows]
            criteria.append(self._row_to_criterion(criterion_row, levels))

        return criteria

    async def get_rubrics_by_course(
        self,
        course_id: UUID,
        include_templates: bool = False,
        limit: int = 100,
        offset: int = 0,
        conn: Optional[Connection] = None
    ) -> List[AssessmentRubric]:
        """
        WHAT: Retrieves rubrics for a course
        WHERE: Called when listing available rubrics
        WHY: Instructors need to see available rubrics for assessments

        Args:
            course_id: Course to filter by
            include_templates: Whether to include template rubrics
            limit: Maximum results
            offset: Pagination offset
            conn: Optional connection

        Returns:
            List of AssessmentRubric (without full criteria for performance)
        """
        query = """
            SELECT * FROM assessment_rubrics
            WHERE (course_id = $1 OR (is_template = TRUE AND $2 = TRUE))
              AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
        """
        connection = conn or self.pool
        rows = await connection.fetch(query, course_id, include_templates, limit, offset)

        rubrics = []
        for row in rows:
            # For list operations, load criteria separately if needed
            criteria = await self._get_criteria_for_rubric(row['id'], connection)
            rubrics.append(self._row_to_rubric(row, criteria))

        return rubrics

    async def get_template_rubrics(
        self,
        organization_id: Optional[UUID] = None,
        limit: int = 100,
        conn: Optional[Connection] = None
    ) -> List[AssessmentRubric]:
        """
        WHAT: Retrieves template rubrics for reuse
        WHERE: Called when creating new assessments
        WHY: Templates enable rubric reuse across assessments

        Args:
            organization_id: Optional org filter
            limit: Maximum results
            conn: Optional connection

        Returns:
            List of template AssessmentRubric
        """
        if organization_id:
            query = """
                SELECT * FROM assessment_rubrics
                WHERE is_template = TRUE
                  AND is_active = TRUE
                  AND (organization_id = $1 OR organization_id IS NULL)
                ORDER BY name
                LIMIT $2
            """
            params = [organization_id, limit]
        else:
            query = """
                SELECT * FROM assessment_rubrics
                WHERE is_template = TRUE AND is_active = TRUE
                ORDER BY name
                LIMIT $1
            """
            params = [limit]

        connection = conn or self.pool
        rows = await connection.fetch(query, *params)

        rubrics = []
        for row in rows:
            criteria = await self._get_criteria_for_rubric(row['id'], connection)
            rubrics.append(self._row_to_rubric(row, criteria))

        return rubrics

    async def update_rubric(
        self,
        rubric: AssessmentRubric,
        conn: Optional[Connection] = None
    ) -> AssessmentRubric:
        """
        WHAT: Updates a rubric and its criteria
        WHERE: Called when modifying rubric structure
        WHY: Enables rubric editing before publication

        Args:
            rubric: AssessmentRubric with updated values
            conn: Optional connection

        Returns:
            Updated AssessmentRubric
        """
        query = """
            UPDATE assessment_rubrics SET
                name = $2, description = $3, max_score = $4, passing_score = $5,
                passing_percentage = $6, tags = $7, version = version + 1,
                updated_at = $8
            WHERE id = $1
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                rubric.id,
                rubric.name,
                rubric.description,
                rubric.max_score,
                rubric.passing_score,
                rubric.passing_percentage,
                rubric.tags,
                datetime.utcnow()
            )
            criteria = await self._get_criteria_for_rubric(rubric.id, connection)
            return self._row_to_rubric(row, criteria)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to update rubric: {str(e)}",
                {"rubric_id": str(rubric.id)}
            )

    async def delete_rubric(
        self,
        rubric_id: UUID,
        conn: Optional[Connection] = None
    ) -> bool:
        """
        WHAT: Soft deletes a rubric
        WHERE: Called when removing rubric
        WHY: Preserves rubric data for historical submissions

        Args:
            rubric_id: UUID of rubric to delete
            conn: Optional connection

        Returns:
            True if deleted, False if not found
        """
        query = "UPDATE assessment_rubrics SET is_active = FALSE, updated_at = $2 WHERE id = $1"
        connection = conn or self.pool
        result = await connection.execute(query, rubric_id, datetime.utcnow())
        return result == "UPDATE 1"

    # =========================================================================
    # Advanced Assessment Operations
    # =========================================================================

    async def create_assessment(
        self,
        assessment: AdvancedAssessment,
        conn: Optional[Connection] = None
    ) -> AdvancedAssessment:
        """
        WHAT: Creates a new advanced assessment with all configuration
        WHERE: Called when instructor creates assessment
        WHY: Persists assessment definition with all settings

        Args:
            assessment: AdvancedAssessment to create
            conn: Optional connection for transaction support

        Returns:
            Created AdvancedAssessment

        Raises:
            AdvancedAssessmentDAOException: If creation fails
        """
        query = """
            INSERT INTO advanced_assessments (
                id, title, description, instructions, assessment_type, status,
                organization_id, course_id, module_id, created_by, rubric_id,
                max_score, passing_score, weight,
                available_from, available_until, due_date,
                late_submission_allowed, late_penalty_percentage, time_limit_minutes,
                max_attempts, best_attempt_counts, allow_revision,
                peer_review_enabled, peer_review_type, min_peer_reviews, peer_review_rubric_id,
                competencies, learning_objectives, deliverables,
                required_artifacts, artifact_types,
                resources, attachments,
                analytics_enabled, track_time_on_task,
                tags, metadata, version,
                created_at, updated_at, published_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27,
                $28, $29, $30, $31, $32, $33, $34, $35, $36, $37, $38, $39,
                $40, $41, $42
            )
            RETURNING *
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    actual_conn = conn or connection

                    row = await actual_conn.fetchrow(
                        query,
                        assessment.id,
                        assessment.title,
                        assessment.description,
                        assessment.instructions,
                        assessment.assessment_type.value,
                        assessment.status.value,
                        assessment.organization_id,
                        assessment.course_id,
                        assessment.module_id,
                        assessment.created_by,
                        assessment.rubric_id,
                        assessment.max_score,
                        assessment.passing_score,
                        assessment.weight,
                        assessment.available_from,
                        assessment.available_until,
                        assessment.due_date,
                        assessment.late_submission_allowed,
                        assessment.late_penalty_percentage,
                        assessment.time_limit_minutes,
                        assessment.max_attempts,
                        assessment.best_attempt_counts,
                        assessment.allow_revision,
                        assessment.peer_review_enabled,
                        assessment.peer_review_type.value if assessment.peer_review_type else None,
                        assessment.min_peer_reviews,
                        assessment.peer_review_rubric_id,
                        [str(c) for c in assessment.competencies],
                        assessment.learning_objectives,
                        assessment.deliverables,
                        assessment.required_artifacts,
                        assessment.artifact_types,
                        json.dumps(assessment.resources),
                        json.dumps(assessment.attachments),
                        assessment.analytics_enabled,
                        assessment.track_time_on_task,
                        assessment.tags,
                        json.dumps(assessment.metadata),
                        assessment.version,
                        assessment.created_at,
                        assessment.updated_at,
                        assessment.published_at
                    )

                    # Create milestones if present
                    for milestone in assessment.milestones:
                        await self._create_milestone(milestone, assessment.id, actual_conn)

                    return self._row_to_assessment(row, assessment.milestones)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create assessment: {str(e)}",
                {"assessment_id": str(assessment.id), "error": str(e)}
            )

    async def get_assessment_by_id(
        self,
        assessment_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[AdvancedAssessment]:
        """
        WHAT: Retrieves an assessment by ID with milestones
        WHERE: Called when loading assessment for viewing or editing
        WHY: Provides complete assessment definition

        Args:
            assessment_id: UUID of assessment to retrieve
            conn: Optional connection

        Returns:
            AdvancedAssessment with milestones, or None if not found
        """
        connection = conn or self.pool

        row = await connection.fetchrow(
            "SELECT * FROM advanced_assessments WHERE id = $1", assessment_id
        )
        if not row:
            return None

        milestones = await self._get_milestones_for_assessment(assessment_id, connection)

        return self._row_to_assessment(row, milestones)

    async def _get_milestones_for_assessment(
        self,
        assessment_id: UUID,
        conn: Connection
    ) -> List[ProjectMilestone]:
        """
        WHAT: Gets all milestones for an assessment
        WHERE: Called when loading assessment
        WHY: Project assessments have milestones

        Args:
            assessment_id: Parent assessment ID
            conn: Database connection

        Returns:
            List of ProjectMilestone
        """
        rows = await conn.fetch(
            "SELECT * FROM project_milestones WHERE assessment_id = $1 ORDER BY sort_order",
            assessment_id
        )
        return [self._row_to_milestone(r) for r in rows]

    async def get_assessments_by_course(
        self,
        course_id: UUID,
        assessment_type: Optional[AssessmentType] = None,
        status: Optional[AssessmentStatus] = None,
        limit: int = 100,
        offset: int = 0,
        conn: Optional[Connection] = None
    ) -> List[AdvancedAssessment]:
        """
        WHAT: Retrieves assessments for a course with optional filters
        WHERE: Called when listing course assessments
        WHY: Instructors need to see all assessments for a course

        Args:
            course_id: Course to filter by
            assessment_type: Optional type filter
            status: Optional status filter
            limit: Maximum results
            offset: Pagination offset
            conn: Optional connection

        Returns:
            List of AdvancedAssessment
        """
        query = "SELECT * FROM advanced_assessments WHERE course_id = $1"
        params: List[Any] = [course_id]
        param_idx = 2

        if assessment_type:
            query += f" AND assessment_type = ${param_idx}"
            params.append(assessment_type.value)
            param_idx += 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status.value)
            param_idx += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        connection = conn or self.pool
        rows = await connection.fetch(query, *params)

        assessments = []
        for row in rows:
            milestones = await self._get_milestones_for_assessment(row['id'], connection)
            assessments.append(self._row_to_assessment(row, milestones))

        return assessments

    async def get_available_assessments(
        self,
        course_id: UUID,
        student_id: UUID,
        conn: Optional[Connection] = None
    ) -> List[AdvancedAssessment]:
        """
        WHAT: Gets assessments available to a student
        WHERE: Called when student views course assessments
        WHY: Students only see published, available assessments

        Args:
            course_id: Course to filter by
            student_id: Student viewing assessments
            conn: Optional connection

        Returns:
            List of available AdvancedAssessment
        """
        query = """
            SELECT * FROM advanced_assessments
            WHERE course_id = $1
              AND status IN ('published', 'in_progress')
              AND (available_from IS NULL OR available_from <= NOW())
              AND (available_until IS NULL OR available_until >= NOW())
            ORDER BY due_date ASC NULLS LAST, created_at DESC
        """
        connection = conn or self.pool
        rows = await connection.fetch(query, course_id)

        assessments = []
        for row in rows:
            milestones = await self._get_milestones_for_assessment(row['id'], connection)
            assessments.append(self._row_to_assessment(row, milestones))

        return assessments

    async def update_assessment(
        self,
        assessment: AdvancedAssessment,
        conn: Optional[Connection] = None
    ) -> AdvancedAssessment:
        """
        WHAT: Updates an assessment
        WHERE: Called when modifying assessment configuration
        WHY: Enables assessment editing before publication

        Args:
            assessment: AdvancedAssessment with updated values
            conn: Optional connection

        Returns:
            Updated AdvancedAssessment
        """
        query = """
            UPDATE advanced_assessments SET
                title = $2, description = $3, instructions = $4, status = $5,
                rubric_id = $6, max_score = $7, passing_score = $8, weight = $9,
                available_from = $10, available_until = $11, due_date = $12,
                late_submission_allowed = $13, late_penalty_percentage = $14,
                time_limit_minutes = $15, max_attempts = $16, best_attempt_counts = $17,
                allow_revision = $18, peer_review_enabled = $19, peer_review_type = $20,
                min_peer_reviews = $21, peer_review_rubric_id = $22,
                competencies = $23, learning_objectives = $24, deliverables = $25,
                required_artifacts = $26, artifact_types = $27,
                resources = $28, attachments = $29,
                tags = $30, metadata = $31, version = version + 1,
                updated_at = $32, published_at = $33
            WHERE id = $1
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                assessment.id,
                assessment.title,
                assessment.description,
                assessment.instructions,
                assessment.status.value,
                assessment.rubric_id,
                assessment.max_score,
                assessment.passing_score,
                assessment.weight,
                assessment.available_from,
                assessment.available_until,
                assessment.due_date,
                assessment.late_submission_allowed,
                assessment.late_penalty_percentage,
                assessment.time_limit_minutes,
                assessment.max_attempts,
                assessment.best_attempt_counts,
                assessment.allow_revision,
                assessment.peer_review_enabled,
                assessment.peer_review_type.value if assessment.peer_review_type else None,
                assessment.min_peer_reviews,
                assessment.peer_review_rubric_id,
                [str(c) for c in assessment.competencies],
                assessment.learning_objectives,
                assessment.deliverables,
                assessment.required_artifacts,
                assessment.artifact_types,
                json.dumps(assessment.resources),
                json.dumps(assessment.attachments),
                assessment.tags,
                json.dumps(assessment.metadata),
                datetime.utcnow(),
                assessment.published_at
            )
            milestones = await self._get_milestones_for_assessment(assessment.id, connection)
            return self._row_to_assessment(row, milestones)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to update assessment: {str(e)}",
                {"assessment_id": str(assessment.id)}
            )

    async def delete_assessment(
        self,
        assessment_id: UUID,
        conn: Optional[Connection] = None
    ) -> bool:
        """
        WHAT: Soft deletes an assessment by archiving
        WHERE: Called when removing assessment
        WHY: Preserves assessment data for historical submissions

        Args:
            assessment_id: UUID of assessment to delete
            conn: Optional connection

        Returns:
            True if deleted, False if not found
        """
        query = """
            UPDATE advanced_assessments
            SET status = 'archived', updated_at = $2
            WHERE id = $1
        """
        connection = conn or self.pool
        result = await connection.execute(query, assessment_id, datetime.utcnow())
        return result == "UPDATE 1"

    # =========================================================================
    # Project Milestone Operations
    # =========================================================================

    async def _create_milestone(
        self,
        milestone: ProjectMilestone,
        assessment_id: UUID,
        conn: Connection
    ) -> None:
        """
        WHAT: Creates a project milestone
        WHERE: Called during assessment creation
        WHY: Project assessments need milestones for tracking

        Args:
            milestone: ProjectMilestone to create
            assessment_id: Parent assessment ID
            conn: Database connection
        """
        query = """
            INSERT INTO project_milestones (
                id, assessment_id, name, description, sort_order,
                required_deliverables, acceptance_criteria, due_date,
                weight, max_points, rubric_id, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        await conn.execute(
            query,
            milestone.id,
            assessment_id,
            milestone.name,
            milestone.description,
            milestone.sort_order,
            milestone.required_deliverables,
            milestone.acceptance_criteria,
            milestone.due_date,
            milestone.weight,
            milestone.max_points,
            milestone.rubric_id,
            milestone.created_at,
            milestone.updated_at
        )

    async def create_milestone(
        self,
        milestone: ProjectMilestone,
        conn: Optional[Connection] = None
    ) -> ProjectMilestone:
        """
        WHAT: Creates a project milestone standalone
        WHERE: Called when adding milestone to existing assessment
        WHY: Milestones can be added after assessment creation

        Args:
            milestone: ProjectMilestone to create
            conn: Optional connection

        Returns:
            Created ProjectMilestone
        """
        query = """
            INSERT INTO project_milestones (
                id, assessment_id, name, description, sort_order,
                required_deliverables, acceptance_criteria, due_date,
                weight, max_points, rubric_id, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                milestone.id,
                milestone.assessment_id,
                milestone.name,
                milestone.description,
                milestone.sort_order,
                milestone.required_deliverables,
                milestone.acceptance_criteria,
                milestone.due_date,
                milestone.weight,
                milestone.max_points,
                milestone.rubric_id,
                milestone.created_at,
                milestone.updated_at
            )
            return self._row_to_milestone(row)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create milestone: {str(e)}",
                {"milestone_id": str(milestone.id)}
            )

    async def get_milestone_by_id(
        self,
        milestone_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[ProjectMilestone]:
        """
        WHAT: Retrieves a milestone by ID
        WHERE: Called when accessing specific milestone
        WHY: Enables milestone-specific operations

        Args:
            milestone_id: UUID of milestone
            conn: Optional connection

        Returns:
            ProjectMilestone or None if not found
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT * FROM project_milestones WHERE id = $1", milestone_id
        )
        return self._row_to_milestone(row) if row else None

    async def update_milestone(
        self,
        milestone: ProjectMilestone,
        conn: Optional[Connection] = None
    ) -> ProjectMilestone:
        """
        WHAT: Updates a milestone
        WHERE: Called when modifying milestone
        WHY: Enables milestone editing

        Args:
            milestone: ProjectMilestone with updated values
            conn: Optional connection

        Returns:
            Updated ProjectMilestone
        """
        query = """
            UPDATE project_milestones SET
                name = $2, description = $3, sort_order = $4,
                required_deliverables = $5, acceptance_criteria = $6,
                due_date = $7, weight = $8, max_points = $9,
                rubric_id = $10, updated_at = $11
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            milestone.id,
            milestone.name,
            milestone.description,
            milestone.sort_order,
            milestone.required_deliverables,
            milestone.acceptance_criteria,
            milestone.due_date,
            milestone.weight,
            milestone.max_points,
            milestone.rubric_id,
            datetime.utcnow()
        )
        return self._row_to_milestone(row)

    async def delete_milestone(
        self,
        milestone_id: UUID,
        conn: Optional[Connection] = None
    ) -> bool:
        """
        WHAT: Deletes a milestone
        WHERE: Called when removing milestone from assessment
        WHY: Enables assessment structure modification

        Args:
            milestone_id: UUID of milestone to delete
            conn: Optional connection

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM project_milestones WHERE id = $1"
        connection = conn or self.pool
        result = await connection.execute(query, milestone_id)
        return result == "DELETE 1"

    # =========================================================================
    # Assessment Submission Operations
    # =========================================================================

    async def create_submission(
        self,
        submission: AssessmentSubmission,
        conn: Optional[Connection] = None
    ) -> AssessmentSubmission:
        """
        WHAT: Creates a new assessment submission
        WHERE: Called when student begins assessment
        WHY: Tracks student work and progress

        Args:
            submission: AssessmentSubmission to create
            conn: Optional connection

        Returns:
            Created AssessmentSubmission

        Raises:
            AdvancedAssessmentDAOException: If creation fails
        """
        query = """
            INSERT INTO assessment_submissions (
                id, assessment_id, student_id, attempt_number, status,
                content, attachments, milestone_progress, deliverable_status,
                self_reflection, reflection_responses,
                raw_score, adjusted_score, final_score, percentage, passed,
                instructor_feedback, private_notes,
                started_at, submitted_at, graded_at, graded_by,
                time_spent_minutes, is_late, late_days,
                metadata, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26,
                $27, $28
            )
            RETURNING *
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    actual_conn = conn or connection

                    row = await actual_conn.fetchrow(
                        query,
                        submission.id,
                        submission.assessment_id,
                        submission.student_id,
                        submission.attempt_number,
                        submission.status.value,
                        submission.content,
                        json.dumps(submission.attachments),
                        json.dumps(submission.milestone_progress),
                        json.dumps(submission.deliverable_status),
                        submission.self_reflection,
                        json.dumps(submission.reflection_responses),
                        submission.raw_score,
                        submission.adjusted_score,
                        submission.final_score,
                        submission.percentage,
                        submission.passed,
                        submission.instructor_feedback,
                        submission.private_notes,
                        submission.started_at,
                        submission.submitted_at,
                        submission.graded_at,
                        submission.graded_by,
                        submission.time_spent_minutes,
                        submission.is_late,
                        submission.late_days,
                        json.dumps(submission.metadata),
                        submission.created_at,
                        submission.updated_at
                    )

                    # Create portfolio artifacts if present
                    for artifact in submission.portfolio_artifacts:
                        await self._create_artifact(artifact, submission.id, actual_conn)

                    return self._row_to_submission(row, submission.portfolio_artifacts)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create submission: {str(e)}",
                {"submission_id": str(submission.id), "error": str(e)}
            )

    async def get_submission_by_id(
        self,
        submission_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[AssessmentSubmission]:
        """
        WHAT: Retrieves a submission by ID with artifacts
        WHERE: Called when loading submission for viewing or grading
        WHY: Provides complete submission data

        Args:
            submission_id: UUID of submission
            conn: Optional connection

        Returns:
            AssessmentSubmission with artifacts, or None if not found
        """
        connection = conn or self.pool

        row = await connection.fetchrow(
            "SELECT * FROM assessment_submissions WHERE id = $1", submission_id
        )
        if not row:
            return None

        artifacts = await self._get_artifacts_for_submission(submission_id, connection)

        return self._row_to_submission(row, artifacts)

    async def _get_artifacts_for_submission(
        self,
        submission_id: UUID,
        conn: Connection
    ) -> List[PortfolioArtifact]:
        """
        WHAT: Gets all artifacts for a submission
        WHERE: Called when loading submission
        WHY: Portfolio submissions have artifacts

        Args:
            submission_id: Parent submission ID
            conn: Database connection

        Returns:
            List of PortfolioArtifact
        """
        rows = await conn.fetch(
            "SELECT * FROM portfolio_artifacts WHERE submission_id = $1 ORDER BY sort_order",
            submission_id
        )
        return [self._row_to_artifact(r) for r in rows]

    async def get_submissions_by_assessment(
        self,
        assessment_id: UUID,
        status: Optional[SubmissionStatus] = None,
        limit: int = 100,
        offset: int = 0,
        conn: Optional[Connection] = None
    ) -> List[AssessmentSubmission]:
        """
        WHAT: Retrieves submissions for an assessment
        WHERE: Called when viewing all submissions for grading
        WHY: Instructors need to see all student submissions

        Args:
            assessment_id: Assessment to filter by
            status: Optional status filter
            limit: Maximum results
            offset: Pagination offset
            conn: Optional connection

        Returns:
            List of AssessmentSubmission
        """
        query = "SELECT * FROM assessment_submissions WHERE assessment_id = $1"
        params: List[Any] = [assessment_id]
        param_idx = 2

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status.value)
            param_idx += 1

        query += f" ORDER BY submitted_at DESC NULLS LAST LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        connection = conn or self.pool
        rows = await connection.fetch(query, *params)

        submissions = []
        for row in rows:
            artifacts = await self._get_artifacts_for_submission(row['id'], connection)
            submissions.append(self._row_to_submission(row, artifacts))

        return submissions

    async def get_student_submissions(
        self,
        student_id: UUID,
        assessment_id: UUID,
        conn: Optional[Connection] = None
    ) -> List[AssessmentSubmission]:
        """
        WHAT: Gets all submissions by a student for an assessment
        WHERE: Called when viewing student attempts
        WHY: Students may have multiple attempts

        Args:
            student_id: Student to filter by
            assessment_id: Assessment to filter by
            conn: Optional connection

        Returns:
            List of AssessmentSubmission ordered by attempt number
        """
        query = """
            SELECT * FROM assessment_submissions
            WHERE student_id = $1 AND assessment_id = $2
            ORDER BY attempt_number DESC
        """
        connection = conn or self.pool
        rows = await connection.fetch(query, student_id, assessment_id)

        submissions = []
        for row in rows:
            artifacts = await self._get_artifacts_for_submission(row['id'], connection)
            submissions.append(self._row_to_submission(row, artifacts))

        return submissions

    async def get_latest_submission(
        self,
        student_id: UUID,
        assessment_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[AssessmentSubmission]:
        """
        WHAT: Gets student's most recent submission for an assessment
        WHERE: Called when loading student's current progress
        WHY: Shows current status of student's work

        Args:
            student_id: Student to filter by
            assessment_id: Assessment to filter by
            conn: Optional connection

        Returns:
            Latest AssessmentSubmission or None
        """
        query = """
            SELECT * FROM assessment_submissions
            WHERE student_id = $1 AND assessment_id = $2
            ORDER BY attempt_number DESC
            LIMIT 1
        """
        connection = conn or self.pool
        row = await connection.fetchrow(query, student_id, assessment_id)

        if not row:
            return None

        artifacts = await self._get_artifacts_for_submission(row['id'], connection)
        return self._row_to_submission(row, artifacts)

    async def get_best_submission(
        self,
        student_id: UUID,
        assessment_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[AssessmentSubmission]:
        """
        WHAT: Gets student's best-scoring submission
        WHERE: Called when determining grade
        WHY: Some assessments use best attempt for final grade

        Args:
            student_id: Student to filter by
            assessment_id: Assessment to filter by
            conn: Optional connection

        Returns:
            Best AssessmentSubmission or None
        """
        query = """
            SELECT * FROM assessment_submissions
            WHERE student_id = $1 AND assessment_id = $2 AND final_score IS NOT NULL
            ORDER BY final_score DESC
            LIMIT 1
        """
        connection = conn or self.pool
        row = await connection.fetchrow(query, student_id, assessment_id)

        if not row:
            return None

        artifacts = await self._get_artifacts_for_submission(row['id'], connection)
        return self._row_to_submission(row, artifacts)

    async def update_submission(
        self,
        submission: AssessmentSubmission,
        conn: Optional[Connection] = None
    ) -> AssessmentSubmission:
        """
        WHAT: Updates a submission
        WHERE: Called during submission workflow
        WHY: Submissions change state through submission, grading

        Args:
            submission: AssessmentSubmission with updated values
            conn: Optional connection

        Returns:
            Updated AssessmentSubmission
        """
        query = """
            UPDATE assessment_submissions SET
                status = $2, content = $3, attachments = $4,
                milestone_progress = $5, deliverable_status = $6,
                self_reflection = $7, reflection_responses = $8,
                raw_score = $9, adjusted_score = $10, final_score = $11,
                percentage = $12, passed = $13,
                instructor_feedback = $14, private_notes = $15,
                started_at = $16, submitted_at = $17, graded_at = $18, graded_by = $19,
                time_spent_minutes = $20, is_late = $21, late_days = $22,
                metadata = $23, updated_at = $24
            WHERE id = $1
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                submission.id,
                submission.status.value,
                submission.content,
                json.dumps(submission.attachments),
                json.dumps(submission.milestone_progress),
                json.dumps(submission.deliverable_status),
                submission.self_reflection,
                json.dumps(submission.reflection_responses),
                submission.raw_score,
                submission.adjusted_score,
                submission.final_score,
                submission.percentage,
                submission.passed,
                submission.instructor_feedback,
                submission.private_notes,
                submission.started_at,
                submission.submitted_at,
                submission.graded_at,
                submission.graded_by,
                submission.time_spent_minutes,
                submission.is_late,
                submission.late_days,
                json.dumps(submission.metadata),
                datetime.utcnow()
            )
            artifacts = await self._get_artifacts_for_submission(submission.id, connection)
            return self._row_to_submission(row, artifacts)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to update submission: {str(e)}",
                {"submission_id": str(submission.id)}
            )

    async def get_submissions_to_grade(
        self,
        course_id: UUID,
        limit: int = 50,
        conn: Optional[Connection] = None
    ) -> List[AssessmentSubmission]:
        """
        WHAT: Gets submissions awaiting grading
        WHERE: Called for grading queue
        WHY: Instructors need to see pending work

        Args:
            course_id: Course to filter by
            limit: Maximum results
            conn: Optional connection

        Returns:
            List of submissions needing grading
        """
        query = """
            SELECT s.* FROM assessment_submissions s
            JOIN advanced_assessments a ON s.assessment_id = a.id
            WHERE a.course_id = $1
              AND s.status IN ('submitted', 'under_review', 'revised')
            ORDER BY s.submitted_at ASC
            LIMIT $2
        """
        connection = conn or self.pool
        rows = await connection.fetch(query, course_id, limit)

        submissions = []
        for row in rows:
            artifacts = await self._get_artifacts_for_submission(row['id'], connection)
            submissions.append(self._row_to_submission(row, artifacts))

        return submissions

    # =========================================================================
    # Portfolio Artifact Operations
    # =========================================================================

    async def _create_artifact(
        self,
        artifact: PortfolioArtifact,
        submission_id: UUID,
        conn: Connection
    ) -> None:
        """
        WHAT: Creates a portfolio artifact
        WHERE: Called during submission creation
        WHY: Portfolio submissions contain artifacts

        Args:
            artifact: PortfolioArtifact to create
            submission_id: Parent submission ID
            conn: Database connection
        """
        query = """
            INSERT INTO portfolio_artifacts (
                id, submission_id, student_id, title, description, artifact_type,
                content_url, content_text, attachments, creation_date, context,
                tags, student_reflection, learning_demonstrated,
                score, feedback, evaluated_by, evaluated_at,
                sort_order, is_featured, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22
            )
        """
        await conn.execute(
            query,
            artifact.id,
            submission_id,
            artifact.student_id,
            artifact.title,
            artifact.description,
            artifact.artifact_type,
            artifact.content_url,
            artifact.content_text,
            json.dumps(artifact.attachments),
            artifact.creation_date,
            artifact.context,
            artifact.tags,
            artifact.student_reflection,
            artifact.learning_demonstrated,
            artifact.score,
            artifact.feedback,
            artifact.evaluated_by,
            artifact.evaluated_at,
            artifact.sort_order,
            artifact.is_featured,
            artifact.created_at,
            artifact.updated_at
        )

    async def create_artifact(
        self,
        artifact: PortfolioArtifact,
        conn: Optional[Connection] = None
    ) -> PortfolioArtifact:
        """
        WHAT: Creates a portfolio artifact standalone
        WHERE: Called when adding artifact to existing submission
        WHY: Artifacts can be added after submission creation

        Args:
            artifact: PortfolioArtifact to create
            conn: Optional connection

        Returns:
            Created PortfolioArtifact
        """
        query = """
            INSERT INTO portfolio_artifacts (
                id, submission_id, student_id, title, description, artifact_type,
                content_url, content_text, attachments, creation_date, context,
                tags, student_reflection, learning_demonstrated,
                score, feedback, evaluated_by, evaluated_at,
                sort_order, is_featured, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22
            )
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                artifact.id,
                artifact.submission_id,
                artifact.student_id,
                artifact.title,
                artifact.description,
                artifact.artifact_type,
                artifact.content_url,
                artifact.content_text,
                json.dumps(artifact.attachments),
                artifact.creation_date,
                artifact.context,
                artifact.tags,
                artifact.student_reflection,
                artifact.learning_demonstrated,
                artifact.score,
                artifact.feedback,
                artifact.evaluated_by,
                artifact.evaluated_at,
                artifact.sort_order,
                artifact.is_featured,
                artifact.created_at,
                artifact.updated_at
            )
            return self._row_to_artifact(row)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create artifact: {str(e)}",
                {"artifact_id": str(artifact.id)}
            )

    async def get_artifact_by_id(
        self,
        artifact_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[PortfolioArtifact]:
        """
        WHAT: Retrieves an artifact by ID
        WHERE: Called when accessing specific artifact
        WHY: Enables artifact-specific operations

        Args:
            artifact_id: UUID of artifact
            conn: Optional connection

        Returns:
            PortfolioArtifact or None if not found
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT * FROM portfolio_artifacts WHERE id = $1", artifact_id
        )
        return self._row_to_artifact(row) if row else None

    async def update_artifact(
        self,
        artifact: PortfolioArtifact,
        conn: Optional[Connection] = None
    ) -> PortfolioArtifact:
        """
        WHAT: Updates an artifact
        WHERE: Called when modifying artifact
        WHY: Enables artifact editing and evaluation

        Args:
            artifact: PortfolioArtifact with updated values
            conn: Optional connection

        Returns:
            Updated PortfolioArtifact
        """
        query = """
            UPDATE portfolio_artifacts SET
                title = $2, description = $3, artifact_type = $4,
                content_url = $5, content_text = $6, attachments = $7,
                context = $8, tags = $9, student_reflection = $10,
                learning_demonstrated = $11, score = $12, feedback = $13,
                evaluated_by = $14, evaluated_at = $15,
                sort_order = $16, is_featured = $17, updated_at = $18
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            artifact.id,
            artifact.title,
            artifact.description,
            artifact.artifact_type,
            artifact.content_url,
            artifact.content_text,
            json.dumps(artifact.attachments),
            artifact.context,
            artifact.tags,
            artifact.student_reflection,
            artifact.learning_demonstrated,
            artifact.score,
            artifact.feedback,
            artifact.evaluated_by,
            artifact.evaluated_at,
            artifact.sort_order,
            artifact.is_featured,
            datetime.utcnow()
        )
        return self._row_to_artifact(row)

    async def delete_artifact(
        self,
        artifact_id: UUID,
        conn: Optional[Connection] = None
    ) -> bool:
        """
        WHAT: Deletes an artifact
        WHERE: Called when removing artifact from portfolio
        WHY: Students may remove artifacts before submission

        Args:
            artifact_id: UUID of artifact to delete
            conn: Optional connection

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM portfolio_artifacts WHERE id = $1"
        connection = conn or self.pool
        result = await connection.execute(query, artifact_id)
        return result == "DELETE 1"

    # =========================================================================
    # Rubric Evaluation Operations
    # =========================================================================

    async def create_evaluation(
        self,
        evaluation: RubricEvaluation,
        conn: Optional[Connection] = None
    ) -> RubricEvaluation:
        """
        WHAT: Creates a rubric evaluation for a criterion
        WHERE: Called during grading
        WHY: Records criterion-level scoring

        Args:
            evaluation: RubricEvaluation to create
            conn: Optional connection

        Returns:
            Created RubricEvaluation
        """
        query = """
            INSERT INTO rubric_evaluations (
                id, submission_id, criterion_id, evaluated_by,
                proficiency_level, points_awarded, feedback,
                strengths, areas_for_improvement, evidence_references,
                evaluated_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                evaluation.id,
                evaluation.submission_id,
                evaluation.criterion_id,
                evaluation.evaluated_by,
                evaluation.proficiency_level.value if evaluation.proficiency_level else None,
                evaluation.points_awarded,
                evaluation.feedback,
                evaluation.strengths,
                evaluation.areas_for_improvement,
                json.dumps(evaluation.evidence_references),
                evaluation.evaluated_at,
                evaluation.updated_at
            )
            return self._row_to_evaluation(row)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create evaluation: {str(e)}",
                {"evaluation_id": str(evaluation.id)}
            )

    async def get_evaluations_for_submission(
        self,
        submission_id: UUID,
        conn: Optional[Connection] = None
    ) -> List[RubricEvaluation]:
        """
        WHAT: Gets all criterion evaluations for a submission
        WHERE: Called when viewing detailed grading
        WHY: Shows breakdown of scoring by criterion

        Args:
            submission_id: Submission to filter by
            conn: Optional connection

        Returns:
            List of RubricEvaluation
        """
        query = """
            SELECT * FROM rubric_evaluations
            WHERE submission_id = $1
            ORDER BY criterion_id
        """
        connection = conn or self.pool
        rows = await connection.fetch(query, submission_id)
        return [self._row_to_evaluation(r) for r in rows]

    async def update_evaluation(
        self,
        evaluation: RubricEvaluation,
        conn: Optional[Connection] = None
    ) -> RubricEvaluation:
        """
        WHAT: Updates a rubric evaluation
        WHERE: Called when adjusting criterion score
        WHY: Enables evaluation modification

        Args:
            evaluation: RubricEvaluation with updated values
            conn: Optional connection

        Returns:
            Updated RubricEvaluation
        """
        query = """
            UPDATE rubric_evaluations SET
                proficiency_level = $2, points_awarded = $3, feedback = $4,
                strengths = $5, areas_for_improvement = $6,
                evidence_references = $7, evaluated_at = $8, updated_at = $9
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            evaluation.id,
            evaluation.proficiency_level.value if evaluation.proficiency_level else None,
            evaluation.points_awarded,
            evaluation.feedback,
            evaluation.strengths,
            evaluation.areas_for_improvement,
            json.dumps(evaluation.evidence_references),
            evaluation.evaluated_at,
            datetime.utcnow()
        )
        return self._row_to_evaluation(row)

    # =========================================================================
    # Peer Review Operations
    # =========================================================================

    async def create_peer_review_assignment(
        self,
        assignment: PeerReviewAssignment,
        conn: Optional[Connection] = None
    ) -> PeerReviewAssignment:
        """
        WHAT: Creates a peer review assignment
        WHERE: Called when assigning reviewer to submission
        WHY: Links reviewers to submissions for peer assessment

        Args:
            assignment: PeerReviewAssignment to create
            conn: Optional connection

        Returns:
            Created PeerReviewAssignment
        """
        query = """
            INSERT INTO peer_review_assignments (
                id, submission_id, reviewer_id, due_date, status,
                is_anonymous, show_author_to_reviewer,
                assigned_at, started_at, completed_at, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                assignment.id,
                assignment.submission_id,
                assignment.reviewer_id,
                assignment.due_date,
                assignment.status.value,
                assignment.is_anonymous,
                assignment.show_author_to_reviewer,
                assignment.assigned_at,
                assignment.started_at,
                assignment.completed_at,
                assignment.created_at,
                assignment.updated_at
            )
            return self._row_to_peer_assignment(row)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create peer review assignment: {str(e)}",
                {"assignment_id": str(assignment.id)}
            )

    async def get_peer_assignment_by_id(
        self,
        assignment_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[PeerReviewAssignment]:
        """
        WHAT: Retrieves a peer review assignment by ID
        WHERE: Called when accessing specific assignment
        WHY: Enables assignment-specific operations

        Args:
            assignment_id: UUID of assignment
            conn: Optional connection

        Returns:
            PeerReviewAssignment or None if not found
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT * FROM peer_review_assignments WHERE id = $1", assignment_id
        )
        return self._row_to_peer_assignment(row) if row else None

    async def get_assignments_for_reviewer(
        self,
        reviewer_id: UUID,
        status: Optional[SubmissionStatus] = None,
        limit: int = 50,
        conn: Optional[Connection] = None
    ) -> List[PeerReviewAssignment]:
        """
        WHAT: Gets peer review assignments for a reviewer
        WHERE: Called when showing reviewer's pending reviews
        WHY: Reviewers need to see their assigned reviews

        Args:
            reviewer_id: Reviewer to filter by
            status: Optional status filter
            limit: Maximum results
            conn: Optional connection

        Returns:
            List of PeerReviewAssignment
        """
        query = "SELECT * FROM peer_review_assignments WHERE reviewer_id = $1"
        params: List[Any] = [reviewer_id]

        if status:
            query += " AND status = $2"
            params.append(status.value)

        query += " ORDER BY due_date ASC NULLS LAST LIMIT $" + str(len(params) + 1)
        params.append(limit)

        connection = conn or self.pool
        rows = await connection.fetch(query, *params)
        return [self._row_to_peer_assignment(r) for r in rows]

    async def get_assignments_for_submission(
        self,
        submission_id: UUID,
        conn: Optional[Connection] = None
    ) -> List[PeerReviewAssignment]:
        """
        WHAT: Gets all peer review assignments for a submission
        WHERE: Called when viewing peer reviews for a submission
        WHY: Shows who is reviewing a submission

        Args:
            submission_id: Submission to filter by
            conn: Optional connection

        Returns:
            List of PeerReviewAssignment
        """
        query = """
            SELECT * FROM peer_review_assignments
            WHERE submission_id = $1
            ORDER BY assigned_at
        """
        connection = conn or self.pool
        rows = await connection.fetch(query, submission_id)
        return [self._row_to_peer_assignment(r) for r in rows]

    async def update_peer_assignment(
        self,
        assignment: PeerReviewAssignment,
        conn: Optional[Connection] = None
    ) -> PeerReviewAssignment:
        """
        WHAT: Updates a peer review assignment
        WHERE: Called when assignment status changes
        WHY: Tracks review progress

        Args:
            assignment: PeerReviewAssignment with updated values
            conn: Optional connection

        Returns:
            Updated PeerReviewAssignment
        """
        query = """
            UPDATE peer_review_assignments SET
                status = $2, started_at = $3, completed_at = $4, updated_at = $5
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            assignment.id,
            assignment.status.value,
            assignment.started_at,
            assignment.completed_at,
            datetime.utcnow()
        )
        return self._row_to_peer_assignment(row)

    async def create_peer_review(
        self,
        review: PeerReview,
        conn: Optional[Connection] = None
    ) -> PeerReview:
        """
        WHAT: Creates a peer review
        WHERE: Called when reviewer submits feedback
        WHY: Records peer feedback and scores

        Args:
            review: PeerReview to create
            conn: Optional connection

        Returns:
            Created PeerReview
        """
        query = """
            INSERT INTO peer_reviews (
                id, assignment_id, submission_id, reviewer_id,
                rubric_scores, overall_score, overall_feedback,
                strengths, areas_for_improvement, specific_suggestions,
                helpfulness_rating, helpfulness_feedback, instructor_quality_score,
                submitted_at, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                review.id,
                review.assignment_id,
                review.submission_id,
                review.reviewer_id,
                json.dumps(review.rubric_scores),
                review.overall_score,
                review.overall_feedback,
                review.strengths,
                review.areas_for_improvement,
                review.specific_suggestions,
                review.helpfulness_rating,
                review.helpfulness_feedback,
                review.instructor_quality_score,
                review.submitted_at,
                review.created_at,
                review.updated_at
            )
            return self._row_to_peer_review(row)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create peer review: {str(e)}",
                {"review_id": str(review.id)}
            )

    async def get_peer_review_by_id(
        self,
        review_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[PeerReview]:
        """
        WHAT: Retrieves a peer review by ID
        WHERE: Called when accessing specific review
        WHY: Enables review-specific operations

        Args:
            review_id: UUID of review
            conn: Optional connection

        Returns:
            PeerReview or None if not found
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT * FROM peer_reviews WHERE id = $1", review_id
        )
        return self._row_to_peer_review(row) if row else None

    async def get_reviews_for_submission(
        self,
        submission_id: UUID,
        conn: Optional[Connection] = None
    ) -> List[PeerReview]:
        """
        WHAT: Gets all peer reviews for a submission
        WHERE: Called when viewing feedback received
        WHY: Shows all peer feedback for a submission

        Args:
            submission_id: Submission to filter by
            conn: Optional connection

        Returns:
            List of PeerReview
        """
        query = """
            SELECT * FROM peer_reviews
            WHERE submission_id = $1 AND submitted_at IS NOT NULL
            ORDER BY submitted_at
        """
        connection = conn or self.pool
        rows = await connection.fetch(query, submission_id)
        return [self._row_to_peer_review(r) for r in rows]

    async def update_peer_review(
        self,
        review: PeerReview,
        conn: Optional[Connection] = None
    ) -> PeerReview:
        """
        WHAT: Updates a peer review
        WHERE: Called when modifying review or adding ratings
        WHY: Enables review updates and quality tracking

        Args:
            review: PeerReview with updated values
            conn: Optional connection

        Returns:
            Updated PeerReview
        """
        query = """
            UPDATE peer_reviews SET
                rubric_scores = $2, overall_score = $3, overall_feedback = $4,
                strengths = $5, areas_for_improvement = $6, specific_suggestions = $7,
                helpfulness_rating = $8, helpfulness_feedback = $9,
                instructor_quality_score = $10, submitted_at = $11, updated_at = $12
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            review.id,
            json.dumps(review.rubric_scores),
            review.overall_score,
            review.overall_feedback,
            review.strengths,
            review.areas_for_improvement,
            review.specific_suggestions,
            review.helpfulness_rating,
            review.helpfulness_feedback,
            review.instructor_quality_score,
            review.submitted_at,
            datetime.utcnow()
        )
        return self._row_to_peer_review(row)

    # =========================================================================
    # Competency Operations
    # =========================================================================

    async def create_competency(
        self,
        competency: Competency,
        conn: Optional[Connection] = None
    ) -> Competency:
        """
        WHAT: Creates a competency definition
        WHERE: Called when defining competencies
        WHY: Competencies are skills to be tracked

        Args:
            competency: Competency to create
            conn: Optional connection

        Returns:
            Created Competency
        """
        query = """
            INSERT INTO competencies (
                id, code, name, description, category, parent_id, level,
                required_proficiency, evidence_requirements, organization_id,
                tags, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                competency.id,
                competency.code,
                competency.name,
                competency.description,
                competency.category,
                competency.parent_id,
                competency.level,
                competency.required_proficiency.value,
                competency.evidence_requirements,
                competency.organization_id,
                competency.tags,
                competency.is_active,
                competency.created_at,
                competency.updated_at
            )
            return self._row_to_competency(row)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create competency: {str(e)}",
                {"competency_id": str(competency.id)}
            )

    async def get_competency_by_id(
        self,
        competency_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[Competency]:
        """
        WHAT: Retrieves a competency by ID
        WHERE: Called when accessing specific competency
        WHY: Enables competency-specific operations

        Args:
            competency_id: UUID of competency
            conn: Optional connection

        Returns:
            Competency or None if not found
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT * FROM competencies WHERE id = $1", competency_id
        )
        return self._row_to_competency(row) if row else None

    async def get_competency_by_code(
        self,
        code: str,
        organization_id: Optional[UUID] = None,
        conn: Optional[Connection] = None
    ) -> Optional[Competency]:
        """
        WHAT: Retrieves a competency by code
        WHERE: Called when looking up by code
        WHY: Codes are human-readable identifiers

        Args:
            code: Competency code
            organization_id: Optional org filter
            conn: Optional connection

        Returns:
            Competency or None if not found
        """
        if organization_id:
            query = """
                SELECT * FROM competencies
                WHERE code = $1 AND (organization_id = $2 OR organization_id IS NULL)
                  AND is_active = TRUE
            """
            params = [code, organization_id]
        else:
            query = "SELECT * FROM competencies WHERE code = $1 AND is_active = TRUE"
            params = [code]

        connection = conn or self.pool
        row = await connection.fetchrow(query, *params)
        return self._row_to_competency(row) if row else None

    async def get_competencies_by_organization(
        self,
        organization_id: UUID,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        conn: Optional[Connection] = None
    ) -> List[Competency]:
        """
        WHAT: Gets competencies for an organization
        WHERE: Called when listing available competencies
        WHY: Organizations define their competency frameworks

        Args:
            organization_id: Organization to filter by
            category: Optional category filter
            limit: Maximum results
            offset: Pagination offset
            conn: Optional connection

        Returns:
            List of Competency
        """
        query = """
            SELECT * FROM competencies
            WHERE (organization_id = $1 OR organization_id IS NULL)
              AND is_active = TRUE
        """
        params: List[Any] = [organization_id]

        if category:
            query += " AND category = $2"
            params.append(category)

        query += f" ORDER BY level, name LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        connection = conn or self.pool
        rows = await connection.fetch(query, *params)
        return [self._row_to_competency(r) for r in rows]

    async def update_competency(
        self,
        competency: Competency,
        conn: Optional[Connection] = None
    ) -> Competency:
        """
        WHAT: Updates a competency
        WHERE: Called when modifying competency definition
        WHY: Enables competency editing

        Args:
            competency: Competency with updated values
            conn: Optional connection

        Returns:
            Updated Competency
        """
        query = """
            UPDATE competencies SET
                name = $2, description = $3, category = $4,
                required_proficiency = $5, evidence_requirements = $6,
                tags = $7, updated_at = $8
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            competency.id,
            competency.name,
            competency.description,
            competency.category,
            competency.required_proficiency.value,
            competency.evidence_requirements,
            competency.tags,
            datetime.utcnow()
        )
        return self._row_to_competency(row)

    async def create_competency_progress(
        self,
        progress: CompetencyProgress,
        conn: Optional[Connection] = None
    ) -> CompetencyProgress:
        """
        WHAT: Creates competency progress for a student
        WHERE: Called when tracking student competency
        WHY: Tracks student proficiency on competencies

        Args:
            progress: CompetencyProgress to create
            conn: Optional connection

        Returns:
            Created CompetencyProgress
        """
        query = """
            INSERT INTO competency_progress (
                id, student_id, competency_id, current_level, previous_level,
                evidence_submissions, assessor_notes, verified_at, verified_by,
                first_demonstrated_at, level_achieved_at, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                progress.id,
                progress.student_id,
                progress.competency_id,
                progress.current_level.value,
                progress.previous_level.value if progress.previous_level else None,
                [str(s) for s in progress.evidence_submissions],
                progress.assessor_notes,
                progress.verified_at,
                progress.verified_by,
                progress.first_demonstrated_at,
                progress.level_achieved_at,
                progress.created_at,
                progress.updated_at
            )
            return self._row_to_competency_progress(row)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to create competency progress: {str(e)}",
                {"progress_id": str(progress.id)}
            )

    async def get_student_competency_progress(
        self,
        student_id: UUID,
        competency_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[CompetencyProgress]:
        """
        WHAT: Gets student's progress on a competency
        WHERE: Called when checking student proficiency
        WHY: Shows current competency level

        Args:
            student_id: Student to filter by
            competency_id: Competency to filter by
            conn: Optional connection

        Returns:
            CompetencyProgress or None if not found
        """
        query = """
            SELECT * FROM competency_progress
            WHERE student_id = $1 AND competency_id = $2
        """
        connection = conn or self.pool
        row = await connection.fetchrow(query, student_id, competency_id)
        return self._row_to_competency_progress(row) if row else None

    async def get_student_competencies(
        self,
        student_id: UUID,
        conn: Optional[Connection] = None
    ) -> List[CompetencyProgress]:
        """
        WHAT: Gets all competency progress for a student
        WHERE: Called when viewing student profile
        WHY: Shows all tracked competencies

        Args:
            student_id: Student to filter by
            conn: Optional connection

        Returns:
            List of CompetencyProgress
        """
        query = """
            SELECT * FROM competency_progress
            WHERE student_id = $1
            ORDER BY level_achieved_at DESC NULLS LAST
        """
        connection = conn or self.pool
        rows = await connection.fetch(query, student_id)
        return [self._row_to_competency_progress(r) for r in rows]

    async def update_competency_progress(
        self,
        progress: CompetencyProgress,
        conn: Optional[Connection] = None
    ) -> CompetencyProgress:
        """
        WHAT: Updates competency progress
        WHERE: Called when proficiency level changes
        WHY: Tracks competency progression

        Args:
            progress: CompetencyProgress with updated values
            conn: Optional connection

        Returns:
            Updated CompetencyProgress
        """
        query = """
            UPDATE competency_progress SET
                current_level = $2, previous_level = $3, evidence_submissions = $4,
                assessor_notes = $5, verified_at = $6, verified_by = $7,
                first_demonstrated_at = $8, level_achieved_at = $9, updated_at = $10
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            progress.id,
            progress.current_level.value,
            progress.previous_level.value if progress.previous_level else None,
            [str(s) for s in progress.evidence_submissions],
            progress.assessor_notes,
            progress.verified_at,
            progress.verified_by,
            progress.first_demonstrated_at,
            progress.level_achieved_at,
            datetime.utcnow()
        )
        return self._row_to_competency_progress(row)

    # =========================================================================
    # Assessment Analytics Operations
    # =========================================================================

    async def create_or_update_analytics(
        self,
        analytics: AssessmentAnalytics,
        conn: Optional[Connection] = None
    ) -> AssessmentAnalytics:
        """
        WHAT: Creates or updates assessment analytics
        WHERE: Called when recalculating analytics
        WHY: Caches computed statistics for performance

        Args:
            analytics: AssessmentAnalytics to upsert
            conn: Optional connection

        Returns:
            Upserted AssessmentAnalytics
        """
        query = """
            INSERT INTO assessment_analytics (
                id, assessment_id, total_students, submissions_count,
                completed_count, in_progress_count,
                average_score, median_score, highest_score, lowest_score, score_std_deviation,
                pass_count, fail_count, pass_rate,
                average_time_minutes, median_time_minutes,
                criterion_averages, criterion_distributions,
                peer_review_completion_rate, average_peer_review_score, peer_review_variance,
                calculated_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24
            )
            ON CONFLICT (assessment_id) DO UPDATE SET
                total_students = EXCLUDED.total_students,
                submissions_count = EXCLUDED.submissions_count,
                completed_count = EXCLUDED.completed_count,
                in_progress_count = EXCLUDED.in_progress_count,
                average_score = EXCLUDED.average_score,
                median_score = EXCLUDED.median_score,
                highest_score = EXCLUDED.highest_score,
                lowest_score = EXCLUDED.lowest_score,
                score_std_deviation = EXCLUDED.score_std_deviation,
                pass_count = EXCLUDED.pass_count,
                fail_count = EXCLUDED.fail_count,
                pass_rate = EXCLUDED.pass_rate,
                average_time_minutes = EXCLUDED.average_time_minutes,
                median_time_minutes = EXCLUDED.median_time_minutes,
                criterion_averages = EXCLUDED.criterion_averages,
                criterion_distributions = EXCLUDED.criterion_distributions,
                peer_review_completion_rate = EXCLUDED.peer_review_completion_rate,
                average_peer_review_score = EXCLUDED.average_peer_review_score,
                peer_review_variance = EXCLUDED.peer_review_variance,
                calculated_at = EXCLUDED.calculated_at,
                updated_at = NOW()
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                analytics.id,
                analytics.assessment_id,
                analytics.total_students,
                analytics.submissions_count,
                analytics.completed_count,
                analytics.in_progress_count,
                analytics.average_score,
                analytics.median_score,
                analytics.highest_score,
                analytics.lowest_score,
                analytics.score_std_deviation,
                analytics.pass_count,
                analytics.fail_count,
                analytics.pass_rate,
                analytics.average_time_minutes,
                analytics.median_time_minutes,
                json.dumps({k: float(v) for k, v in analytics.criterion_averages.items()}),
                json.dumps(analytics.criterion_distributions),
                analytics.peer_review_completion_rate,
                analytics.average_peer_review_score,
                analytics.peer_review_variance,
                analytics.calculated_at,
                analytics.created_at,
                analytics.updated_at
            )
            return self._row_to_analytics(row)
        except Exception as e:
            raise AdvancedAssessmentDAOException(
                f"Failed to upsert analytics: {str(e)}",
                {"assessment_id": str(analytics.assessment_id)}
            )

    async def get_analytics_by_assessment(
        self,
        assessment_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[AssessmentAnalytics]:
        """
        WHAT: Gets analytics for an assessment
        WHERE: Called when viewing assessment statistics
        WHY: Provides pre-computed analytics for display

        Args:
            assessment_id: Assessment to filter by
            conn: Optional connection

        Returns:
            AssessmentAnalytics or None if not found
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT * FROM assessment_analytics WHERE assessment_id = $1",
            assessment_id
        )
        return self._row_to_analytics(row) if row else None

    # =========================================================================
    # Row Conversion Helpers
    # =========================================================================

    def _row_to_rubric(
        self,
        row: Record,
        criteria: List[RubricCriterion]
    ) -> AssessmentRubric:
        """Converts database row to AssessmentRubric entity."""
        return AssessmentRubric(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            max_score=row['max_score'],
            passing_score=row['passing_score'],
            passing_percentage=row['passing_percentage'],
            is_template=row['is_template'],
            organization_id=row['organization_id'],
            course_id=row['course_id'],
            created_by=row['created_by'],
            criteria=criteria,
            tags=row['tags'] or [],
            version=row['version'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_criterion(
        self,
        row: Record,
        levels: List[RubricPerformanceLevel]
    ) -> RubricCriterion:
        """Converts database row to RubricCriterion entity."""
        return RubricCriterion(
            id=row['id'],
            rubric_id=row['rubric_id'],
            name=row['name'],
            description=row['description'],
            max_points=row['max_points'],
            weight=row['weight'],
            sort_order=row['sort_order'],
            category=row['category'],
            is_required=row['is_required'],
            allow_partial_credit=row['allow_partial_credit'],
            performance_levels=levels,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_performance_level(self, row: Record) -> RubricPerformanceLevel:
        """Converts database row to RubricPerformanceLevel entity."""
        return RubricPerformanceLevel(
            id=row['id'],
            criterion_id=row['criterion_id'],
            level=ProficiencyLevel(row['level']),
            name=row['name'],
            description=row['description'],
            points=row['points'],
            percentage_of_max=row['percentage_of_max'],
            color=row['color'],
            icon=row['icon'],
            sort_order=row['sort_order'],
            created_at=row['created_at']
        )

    def _row_to_assessment(
        self,
        row: Record,
        milestones: List[ProjectMilestone]
    ) -> AdvancedAssessment:
        """Converts database row to AdvancedAssessment entity."""
        return AdvancedAssessment(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            instructions=row['instructions'],
            assessment_type=AssessmentType(row['assessment_type']),
            status=AssessmentStatus(row['status']),
            organization_id=row['organization_id'],
            course_id=row['course_id'],
            module_id=row['module_id'],
            created_by=row['created_by'],
            rubric_id=row['rubric_id'],
            max_score=row['max_score'],
            passing_score=row['passing_score'],
            weight=row['weight'],
            available_from=row['available_from'],
            available_until=row['available_until'],
            due_date=row['due_date'],
            late_submission_allowed=row['late_submission_allowed'],
            late_penalty_percentage=row['late_penalty_percentage'],
            time_limit_minutes=row['time_limit_minutes'],
            max_attempts=row['max_attempts'],
            best_attempt_counts=row['best_attempt_counts'],
            allow_revision=row['allow_revision'],
            peer_review_enabled=row['peer_review_enabled'],
            peer_review_type=ReviewType(row['peer_review_type']) if row['peer_review_type'] else None,
            min_peer_reviews=row['min_peer_reviews'],
            peer_review_rubric_id=row['peer_review_rubric_id'],
            competencies=[UUID(c) for c in (row['competencies'] or [])],
            learning_objectives=row['learning_objectives'] or [],
            milestones=milestones,
            deliverables=row['deliverables'] or [],
            required_artifacts=row['required_artifacts'],
            artifact_types=row['artifact_types'] or [],
            resources=json.loads(row['resources']) if row['resources'] else [],
            attachments=json.loads(row['attachments']) if row['attachments'] else [],
            analytics_enabled=row['analytics_enabled'],
            track_time_on_task=row['track_time_on_task'],
            tags=row['tags'] or [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            version=row['version'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            published_at=row['published_at']
        )

    def _row_to_milestone(self, row: Record) -> ProjectMilestone:
        """Converts database row to ProjectMilestone entity."""
        return ProjectMilestone(
            id=row['id'],
            assessment_id=row['assessment_id'],
            name=row['name'],
            description=row['description'],
            sort_order=row['sort_order'],
            required_deliverables=row['required_deliverables'] or [],
            acceptance_criteria=row['acceptance_criteria'],
            due_date=row['due_date'],
            weight=row['weight'],
            max_points=row['max_points'],
            rubric_id=row['rubric_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_submission(
        self,
        row: Record,
        artifacts: List[PortfolioArtifact]
    ) -> AssessmentSubmission:
        """Converts database row to AssessmentSubmission entity."""
        return AssessmentSubmission(
            id=row['id'],
            assessment_id=row['assessment_id'],
            student_id=row['student_id'],
            attempt_number=row['attempt_number'],
            status=SubmissionStatus(row['status']),
            content=row['content'],
            attachments=json.loads(row['attachments']) if row['attachments'] else [],
            portfolio_artifacts=artifacts,
            milestone_progress=json.loads(row['milestone_progress']) if row['milestone_progress'] else {},
            deliverable_status=json.loads(row['deliverable_status']) if row['deliverable_status'] else {},
            self_reflection=row['self_reflection'],
            reflection_responses=json.loads(row['reflection_responses']) if row['reflection_responses'] else {},
            raw_score=row['raw_score'],
            adjusted_score=row['adjusted_score'],
            final_score=row['final_score'],
            percentage=row['percentage'],
            passed=row['passed'],
            instructor_feedback=row['instructor_feedback'],
            private_notes=row['private_notes'],
            started_at=row['started_at'],
            submitted_at=row['submitted_at'],
            graded_at=row['graded_at'],
            graded_by=row['graded_by'],
            time_spent_minutes=row['time_spent_minutes'],
            is_late=row['is_late'],
            late_days=row['late_days'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_artifact(self, row: Record) -> PortfolioArtifact:
        """Converts database row to PortfolioArtifact entity."""
        return PortfolioArtifact(
            id=row['id'],
            submission_id=row['submission_id'],
            student_id=row['student_id'],
            title=row['title'],
            description=row['description'],
            artifact_type=row['artifact_type'],
            content_url=row['content_url'],
            content_text=row['content_text'],
            attachments=json.loads(row['attachments']) if row['attachments'] else [],
            creation_date=row['creation_date'],
            context=row['context'],
            tags=row['tags'] or [],
            student_reflection=row['student_reflection'],
            learning_demonstrated=row['learning_demonstrated'],
            score=row['score'],
            feedback=row['feedback'],
            evaluated_by=row['evaluated_by'],
            evaluated_at=row['evaluated_at'],
            sort_order=row['sort_order'],
            is_featured=row['is_featured'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_evaluation(self, row: Record) -> RubricEvaluation:
        """Converts database row to RubricEvaluation entity."""
        return RubricEvaluation(
            id=row['id'],
            submission_id=row['submission_id'],
            criterion_id=row['criterion_id'],
            evaluated_by=row['evaluated_by'],
            proficiency_level=ProficiencyLevel(row['proficiency_level']) if row['proficiency_level'] else None,
            points_awarded=row['points_awarded'],
            feedback=row['feedback'],
            strengths=row['strengths'],
            areas_for_improvement=row['areas_for_improvement'],
            evidence_references=json.loads(row['evidence_references']) if row['evidence_references'] else [],
            evaluated_at=row['evaluated_at'],
            updated_at=row['updated_at']
        )

    def _row_to_peer_assignment(self, row: Record) -> PeerReviewAssignment:
        """Converts database row to PeerReviewAssignment entity."""
        return PeerReviewAssignment(
            id=row['id'],
            submission_id=row['submission_id'],
            reviewer_id=row['reviewer_id'],
            due_date=row['due_date'],
            status=SubmissionStatus(row['status']),
            is_anonymous=row['is_anonymous'],
            show_author_to_reviewer=row['show_author_to_reviewer'],
            assigned_at=row['assigned_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_peer_review(self, row: Record) -> PeerReview:
        """Converts database row to PeerReview entity."""
        return PeerReview(
            id=row['id'],
            assignment_id=row['assignment_id'],
            submission_id=row['submission_id'],
            reviewer_id=row['reviewer_id'],
            rubric_scores=json.loads(row['rubric_scores']) if row['rubric_scores'] else {},
            overall_score=row['overall_score'],
            overall_feedback=row['overall_feedback'],
            strengths=row['strengths'],
            areas_for_improvement=row['areas_for_improvement'],
            specific_suggestions=row['specific_suggestions'],
            helpfulness_rating=row['helpfulness_rating'],
            helpfulness_feedback=row['helpfulness_feedback'],
            instructor_quality_score=row['instructor_quality_score'],
            submitted_at=row['submitted_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_competency(self, row: Record) -> Competency:
        """Converts database row to Competency entity."""
        return Competency(
            id=row['id'],
            code=row['code'],
            name=row['name'],
            description=row['description'],
            category=row['category'],
            parent_id=row['parent_id'],
            level=row['level'],
            required_proficiency=ProficiencyLevel(row['required_proficiency']),
            evidence_requirements=row['evidence_requirements'],
            organization_id=row['organization_id'],
            tags=row['tags'] or [],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_competency_progress(self, row: Record) -> CompetencyProgress:
        """Converts database row to CompetencyProgress entity."""
        return CompetencyProgress(
            id=row['id'],
            student_id=row['student_id'],
            competency_id=row['competency_id'],
            current_level=ProficiencyLevel(row['current_level']),
            previous_level=ProficiencyLevel(row['previous_level']) if row['previous_level'] else None,
            evidence_submissions=[UUID(s) for s in (row['evidence_submissions'] or [])],
            assessor_notes=row['assessor_notes'],
            verified_at=row['verified_at'],
            verified_by=row['verified_by'],
            first_demonstrated_at=row['first_demonstrated_at'],
            level_achieved_at=row['level_achieved_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_analytics(self, row: Record) -> AssessmentAnalytics:
        """Converts database row to AssessmentAnalytics entity."""
        criterion_averages_raw = json.loads(row['criterion_averages']) if row['criterion_averages'] else {}
        return AssessmentAnalytics(
            id=row['id'],
            assessment_id=row['assessment_id'],
            total_students=row['total_students'],
            submissions_count=row['submissions_count'],
            completed_count=row['completed_count'],
            in_progress_count=row['in_progress_count'],
            average_score=row['average_score'],
            median_score=row['median_score'],
            highest_score=row['highest_score'],
            lowest_score=row['lowest_score'],
            score_std_deviation=row['score_std_deviation'],
            pass_count=row['pass_count'],
            fail_count=row['fail_count'],
            pass_rate=row['pass_rate'],
            average_time_minutes=row['average_time_minutes'],
            median_time_minutes=row['median_time_minutes'],
            criterion_averages={k: Decimal(str(v)) for k, v in criterion_averages_raw.items()},
            criterion_distributions=json.loads(row['criterion_distributions']) if row['criterion_distributions'] else {},
            peer_review_completion_rate=row['peer_review_completion_rate'],
            average_peer_review_score=row['average_peer_review_score'],
            peer_review_variance=row['peer_review_variance'],
            calculated_at=row['calculated_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
