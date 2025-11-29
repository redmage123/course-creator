"""
WHAT: Data Access Object for Adaptive Learning Paths
WHERE: Used by AdaptiveLearningService and LearningPathService
WHY: Provides clean database abstraction for learning path operations
     with proper exception handling and transaction support

This DAO implements the repository pattern for all learning path related
database operations including paths, nodes, prerequisites, and recommendations.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

import asyncpg

from course_management.domain.entities.learning_path import (
    LearningPath, LearningPathNode, PrerequisiteRule, AdaptiveRecommendation,
    StudentMasteryLevel, PathType, PathStatus, NodeStatus, ContentType,
    RequirementType, RecommendationType, RecommendationStatus, MasteryLevel,
    DifficultyLevel, LearningPathNotFoundException, RecommendationNotFoundException,
    AdaptiveLearningException
)

logger = logging.getLogger(__name__)


class LearningPathDAOException(AdaptiveLearningException):
    """
    WHAT: Base exception for DAO operations
    WHERE: Thrown by all DAO methods on database errors
    WHY: Wraps low-level database exceptions with context
    """
    pass


class LearningPathDAO:
    """
    WHAT: Data Access Object for learning path database operations
    WHERE: Used by AdaptiveLearningService for all persistence operations
    WHY: Centralizes database logic, enables testing with mocks,
         provides clean separation from business logic

    All methods wrap base exceptions in custom exceptions as per coding standards.
    """

    def __init__(self, pool: asyncpg.Pool):
        """
        WHAT: Initialize DAO with database connection pool
        WHERE: Called by dependency injection in service layer
        WHY: Enables connection pooling for performance
        """
        self._pool = pool

    # =========================================================================
    # LEARNING PATH OPERATIONS
    # =========================================================================

    async def create_learning_path(self, path: LearningPath) -> LearningPath:
        """
        WHAT: Creates a new learning path in the database
        WHERE: Called by AdaptiveLearningService.create_path()
        WHY: Persists new learning paths with all metadata

        Args:
            path: LearningPath entity to persist

        Returns:
            Created LearningPath with database-generated fields

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            INSERT INTO learning_paths (
                id, student_id, organization_id, track_id, name, description,
                path_type, difficulty_level, status, overall_progress,
                estimated_duration_hours, actual_duration_hours, total_nodes,
                completed_nodes, current_node_id, adapt_to_performance,
                adapt_to_pace, target_completion_date, recommendation_confidence,
                last_adaptation_at, adaptation_count, created_at, updated_at,
                started_at, completed_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25
            )
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    path.id, path.student_id, path.organization_id, path.track_id,
                    path.name, path.description, path.path_type.value,
                    path.difficulty_level.value, path.status.value,
                    float(path.overall_progress), path.estimated_duration_hours,
                    path.actual_duration_hours, path.total_nodes, path.completed_nodes,
                    path.current_node_id, path.adapt_to_performance, path.adapt_to_pace,
                    path.target_completion_date,
                    float(path.recommendation_confidence) if path.recommendation_confidence else None,
                    path.last_adaptation_at, path.adaptation_count,
                    path.created_at, path.updated_at, path.started_at, path.completed_at
                )
                logger.info(f"Created learning path {path.id} for student {path.student_id}")
                return self._row_to_learning_path(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating learning path: {e}")
            raise LearningPathDAOException(
                f"Failed to create learning path for student {path.student_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating learning path: {e}")
            raise LearningPathDAOException(
                f"Unexpected error creating learning path: {str(e)}"
            ) from e

    async def get_learning_path_by_id(self, path_id: UUID) -> Optional[LearningPath]:
        """
        WHAT: Retrieves a learning path by ID with its nodes
        WHERE: Called by service layer for path operations
        WHY: Provides complete path data for display and processing

        Args:
            path_id: UUID of the learning path

        Returns:
            LearningPath with nodes if found, None otherwise

        Raises:
            LearningPathDAOException: On database errors
        """
        query = "SELECT * FROM learning_paths WHERE id = $1"
        nodes_query = """
            SELECT * FROM learning_path_nodes
            WHERE learning_path_id = $1
            ORDER BY sequence_order
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, path_id)
                if row is None:
                    return None

                path = self._row_to_learning_path(row)

                # Load nodes
                node_rows = await conn.fetch(nodes_query, path_id)
                path.nodes = [self._row_to_learning_path_node(nr) for nr in node_rows]

                return path
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting learning path {path_id}: {e}")
            raise LearningPathDAOException(
                f"Failed to get learning path {path_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting learning path: {e}")
            raise LearningPathDAOException(
                f"Unexpected error getting learning path {path_id}: {str(e)}"
            ) from e

    async def get_learning_paths_by_student(
        self,
        student_id: UUID,
        status: Optional[PathStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[LearningPath]:
        """
        WHAT: Retrieves all learning paths for a student
        WHERE: Called for student dashboard display
        WHY: Enables viewing all paths with optional status filtering

        Args:
            student_id: UUID of the student
            status: Optional filter by path status
            limit: Maximum paths to return
            offset: Pagination offset

        Returns:
            List of LearningPath entities

        Raises:
            LearningPathDAOException: On database errors
        """
        if status:
            query = """
                SELECT * FROM learning_paths
                WHERE student_id = $1 AND status = $2
                ORDER BY updated_at DESC
                LIMIT $3 OFFSET $4
            """
            params = [student_id, status.value, limit, offset]
        else:
            query = """
                SELECT * FROM learning_paths
                WHERE student_id = $1
                ORDER BY updated_at DESC
                LIMIT $2 OFFSET $3
            """
            params = [student_id, limit, offset]

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [self._row_to_learning_path(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting paths for student {student_id}: {e}")
            raise LearningPathDAOException(
                f"Failed to get learning paths for student {student_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting student paths: {e}")
            raise LearningPathDAOException(
                f"Unexpected error getting paths for student {student_id}: {str(e)}"
            ) from e

    async def update_learning_path(self, path: LearningPath) -> LearningPath:
        """
        WHAT: Updates an existing learning path
        WHERE: Called after path modifications
        WHY: Persists path state changes including progress updates

        Args:
            path: Updated LearningPath entity

        Returns:
            Updated LearningPath

        Raises:
            LearningPathNotFoundException: If path doesn't exist
            LearningPathDAOException: On database errors
        """
        query = """
            UPDATE learning_paths SET
                name = $2, description = $3, path_type = $4, difficulty_level = $5,
                status = $6, overall_progress = $7, estimated_duration_hours = $8,
                actual_duration_hours = $9, total_nodes = $10, completed_nodes = $11,
                current_node_id = $12, adapt_to_performance = $13, adapt_to_pace = $14,
                target_completion_date = $15, recommendation_confidence = $16,
                last_adaptation_at = $17, adaptation_count = $18, updated_at = $19,
                started_at = $20, completed_at = $21
            WHERE id = $1
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    path.id, path.name, path.description, path.path_type.value,
                    path.difficulty_level.value, path.status.value,
                    float(path.overall_progress), path.estimated_duration_hours,
                    path.actual_duration_hours, path.total_nodes, path.completed_nodes,
                    path.current_node_id, path.adapt_to_performance, path.adapt_to_pace,
                    path.target_completion_date,
                    float(path.recommendation_confidence) if path.recommendation_confidence else None,
                    path.last_adaptation_at, path.adaptation_count, datetime.utcnow(),
                    path.started_at, path.completed_at
                )
                if row is None:
                    raise LearningPathNotFoundException(
                        f"Learning path {path.id} not found"
                    )
                logger.info(f"Updated learning path {path.id}")
                return self._row_to_learning_path(row)
        except LearningPathNotFoundException:
            raise
        except asyncpg.PostgresError as e:
            logger.error(f"Database error updating learning path {path.id}: {e}")
            raise LearningPathDAOException(
                f"Failed to update learning path {path.id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error updating learning path: {e}")
            raise LearningPathDAOException(
                f"Unexpected error updating learning path {path.id}: {str(e)}"
            ) from e

    async def delete_learning_path(self, path_id: UUID) -> bool:
        """
        WHAT: Deletes a learning path and its nodes
        WHERE: Called for path cleanup/removal
        WHY: Removes path with cascade to related data

        Args:
            path_id: UUID of path to delete

        Returns:
            True if deleted, False if not found

        Raises:
            LearningPathDAOException: On database errors
        """
        query = "DELETE FROM learning_paths WHERE id = $1 RETURNING id"
        try:
            async with self._pool.acquire() as conn:
                result = await conn.fetchrow(query, path_id)
                if result:
                    logger.info(f"Deleted learning path {path_id}")
                    return True
                return False
        except asyncpg.PostgresError as e:
            logger.error(f"Database error deleting learning path {path_id}: {e}")
            raise LearningPathDAOException(
                f"Failed to delete learning path {path_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error deleting learning path: {e}")
            raise LearningPathDAOException(
                f"Unexpected error deleting learning path {path_id}: {str(e)}"
            ) from e

    # =========================================================================
    # LEARNING PATH NODE OPERATIONS
    # =========================================================================

    async def create_node(self, node: LearningPathNode) -> LearningPathNode:
        """
        WHAT: Creates a learning path node
        WHERE: Called when adding nodes to a path
        WHY: Persists individual learning steps

        Args:
            node: LearningPathNode entity to create

        Returns:
            Created LearningPathNode

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            INSERT INTO learning_path_nodes (
                id, learning_path_id, content_type, content_id, sequence_order,
                status, parent_node_id, is_required, is_unlocked, progress_percentage,
                score, attempts, max_attempts, estimated_duration_minutes,
                actual_duration_minutes, time_spent_seconds, difficulty_adjustment,
                was_recommended, recommendation_reason, unlock_conditions,
                created_at, updated_at, started_at, completed_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24
            )
            RETURNING *
        """
        try:
            import json
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    node.id, node.learning_path_id, node.content_type.value,
                    node.content_id, node.sequence_order, node.status.value,
                    node.parent_node_id, node.is_required, node.is_unlocked,
                    float(node.progress_percentage),
                    float(node.score) if node.score else None,
                    node.attempts, node.max_attempts, node.estimated_duration_minutes,
                    node.actual_duration_minutes, node.time_spent_seconds,
                    float(node.difficulty_adjustment), node.was_recommended,
                    node.recommendation_reason, json.dumps(node.unlock_conditions),
                    node.created_at, node.updated_at, node.started_at, node.completed_at
                )
                logger.debug(f"Created node {node.id} in path {node.learning_path_id}")
                return self._row_to_learning_path_node(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating node: {e}")
            raise LearningPathDAOException(
                f"Failed to create node in path {node.learning_path_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating node: {e}")
            raise LearningPathDAOException(
                f"Unexpected error creating node: {str(e)}"
            ) from e

    async def update_node(self, node: LearningPathNode) -> LearningPathNode:
        """
        WHAT: Updates a learning path node
        WHERE: Called on progress updates, status changes
        WHY: Persists node state changes

        Args:
            node: Updated LearningPathNode

        Returns:
            Updated LearningPathNode

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            UPDATE learning_path_nodes SET
                status = $2, is_unlocked = $3, progress_percentage = $4, score = $5,
                attempts = $6, actual_duration_minutes = $7, time_spent_seconds = $8,
                difficulty_adjustment = $9, updated_at = $10, started_at = $11,
                completed_at = $12
            WHERE id = $1
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    node.id, node.status.value, node.is_unlocked,
                    float(node.progress_percentage),
                    float(node.score) if node.score else None,
                    node.attempts, node.actual_duration_minutes, node.time_spent_seconds,
                    float(node.difficulty_adjustment), datetime.utcnow(),
                    node.started_at, node.completed_at
                )
                if row is None:
                    raise LearningPathDAOException(f"Node {node.id} not found")
                return self._row_to_learning_path_node(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error updating node {node.id}: {e}")
            raise LearningPathDAOException(
                f"Failed to update node {node.id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error updating node: {e}")
            raise LearningPathDAOException(
                f"Unexpected error updating node {node.id}: {str(e)}"
            ) from e

    async def get_nodes_by_path(self, path_id: UUID) -> List[LearningPathNode]:
        """
        WHAT: Retrieves all nodes for a learning path
        WHERE: Called when loading full path data
        WHY: Enables path display with all steps

        Args:
            path_id: UUID of the learning path

        Returns:
            List of LearningPathNode ordered by sequence

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            SELECT * FROM learning_path_nodes
            WHERE learning_path_id = $1
            ORDER BY sequence_order
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, path_id)
                return [self._row_to_learning_path_node(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting nodes for path {path_id}: {e}")
            raise LearningPathDAOException(
                f"Failed to get nodes for path {path_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting nodes: {e}")
            raise LearningPathDAOException(
                f"Unexpected error getting nodes for path {path_id}: {str(e)}"
            ) from e

    # =========================================================================
    # PREREQUISITE OPERATIONS
    # =========================================================================

    async def create_prerequisite_rule(self, rule: PrerequisiteRule) -> PrerequisiteRule:
        """
        WHAT: Creates a prerequisite rule
        WHERE: Called when defining content dependencies
        WHY: Establishes learning sequence requirements

        Args:
            rule: PrerequisiteRule to create

        Returns:
            Created PrerequisiteRule

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            INSERT INTO prerequisite_rules (
                id, target_type, target_id, prerequisite_type, prerequisite_id,
                requirement_type, requirement_value, organization_id, track_id,
                is_mandatory, bypass_allowed, created_at, updated_at, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    rule.id, rule.target_type.value, rule.target_id,
                    rule.prerequisite_type.value, rule.prerequisite_id,
                    rule.requirement_type.value,
                    float(rule.requirement_value) if rule.requirement_value else None,
                    rule.organization_id, rule.track_id, rule.is_mandatory,
                    rule.bypass_allowed, rule.created_at, rule.updated_at,
                    rule.created_by
                )
                logger.info(f"Created prerequisite rule {rule.id}")
                return self._row_to_prerequisite_rule(row)
        except asyncpg.UniqueViolationError as e:
            logger.warning(f"Duplicate prerequisite rule: {e}")
            raise LearningPathDAOException(
                f"Prerequisite rule already exists for target {rule.target_id}"
            ) from e
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating prerequisite rule: {e}")
            raise LearningPathDAOException(
                f"Failed to create prerequisite rule: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating prerequisite rule: {e}")
            raise LearningPathDAOException(
                f"Unexpected error creating prerequisite rule: {str(e)}"
            ) from e

    async def get_prerequisites_for_content(
        self,
        content_type: ContentType,
        content_id: UUID
    ) -> List[PrerequisiteRule]:
        """
        WHAT: Gets all prerequisites for specific content
        WHERE: Called during enrollment/access validation
        WHY: Enables prerequisite checking before content access

        Args:
            content_type: Type of the target content
            content_id: UUID of the target content

        Returns:
            List of PrerequisiteRule for this content

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            SELECT * FROM prerequisite_rules
            WHERE target_type = $1 AND target_id = $2
            ORDER BY created_at
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, content_type.value, content_id)
                return [self._row_to_prerequisite_rule(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting prerequisites: {e}")
            raise LearningPathDAOException(
                f"Failed to get prerequisites for {content_type.value}/{content_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting prerequisites: {e}")
            raise LearningPathDAOException(
                f"Unexpected error getting prerequisites: {str(e)}"
            ) from e

    async def delete_prerequisite_rule(self, rule_id: UUID) -> bool:
        """
        WHAT: Deletes a prerequisite rule
        WHERE: Called when removing dependencies
        WHY: Allows content sequence modification

        Args:
            rule_id: UUID of rule to delete

        Returns:
            True if deleted, False if not found

        Raises:
            LearningPathDAOException: On database errors
        """
        query = "DELETE FROM prerequisite_rules WHERE id = $1 RETURNING id"
        try:
            async with self._pool.acquire() as conn:
                result = await conn.fetchrow(query, rule_id)
                return result is not None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error deleting prerequisite rule {rule_id}: {e}")
            raise LearningPathDAOException(
                f"Failed to delete prerequisite rule {rule_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error deleting prerequisite rule: {e}")
            raise LearningPathDAOException(
                f"Unexpected error deleting prerequisite rule: {str(e)}"
            ) from e

    # =========================================================================
    # RECOMMENDATION OPERATIONS
    # =========================================================================

    async def create_recommendation(
        self,
        recommendation: AdaptiveRecommendation
    ) -> AdaptiveRecommendation:
        """
        WHAT: Creates an adaptive recommendation
        WHERE: Called by recommendation engine
        WHY: Persists AI-generated learning suggestions

        Args:
            recommendation: AdaptiveRecommendation to create

        Returns:
            Created AdaptiveRecommendation

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            INSERT INTO adaptive_recommendations (
                id, student_id, learning_path_id, recommendation_type, content_type,
                content_id, title, description, reason, priority, confidence_score,
                trigger_metrics, status, valid_from, valid_until, viewed_at,
                acted_on_at, user_feedback, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20
            )
            RETURNING *
        """
        try:
            import json
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    recommendation.id, recommendation.student_id,
                    recommendation.learning_path_id,
                    recommendation.recommendation_type.value,
                    recommendation.content_type.value if recommendation.content_type else None,
                    recommendation.content_id, recommendation.title,
                    recommendation.description, recommendation.reason,
                    recommendation.priority, float(recommendation.confidence_score),
                    json.dumps(recommendation.trigger_metrics),
                    recommendation.status.value, recommendation.valid_from,
                    recommendation.valid_until, recommendation.viewed_at,
                    recommendation.acted_on_at, recommendation.user_feedback,
                    recommendation.created_at, recommendation.updated_at
                )
                logger.info(f"Created recommendation {recommendation.id}")
                return self._row_to_recommendation(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating recommendation: {e}")
            raise LearningPathDAOException(
                f"Failed to create recommendation: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating recommendation: {e}")
            raise LearningPathDAOException(
                f"Unexpected error creating recommendation: {str(e)}"
            ) from e

    async def get_pending_recommendations(
        self,
        student_id: UUID,
        limit: int = 10
    ) -> List[AdaptiveRecommendation]:
        """
        WHAT: Gets pending recommendations for a student
        WHERE: Called for student dashboard display
        WHY: Shows actionable learning suggestions

        Args:
            student_id: UUID of the student
            limit: Maximum recommendations to return

        Returns:
            List of pending AdaptiveRecommendation ordered by priority

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            SELECT * FROM adaptive_recommendations
            WHERE student_id = $1
              AND status = 'pending'
              AND valid_from <= NOW()
              AND (valid_until IS NULL OR valid_until > NOW())
            ORDER BY priority DESC, created_at ASC
            LIMIT $2
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, student_id, limit)
                return [self._row_to_recommendation(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting recommendations: {e}")
            raise LearningPathDAOException(
                f"Failed to get recommendations for student {student_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting recommendations: {e}")
            raise LearningPathDAOException(
                f"Unexpected error getting recommendations: {str(e)}"
            ) from e

    async def update_recommendation(
        self,
        recommendation: AdaptiveRecommendation
    ) -> AdaptiveRecommendation:
        """
        WHAT: Updates a recommendation
        WHERE: Called on status changes (viewed, accepted, etc.)
        WHY: Tracks recommendation lifecycle

        Args:
            recommendation: Updated AdaptiveRecommendation

        Returns:
            Updated AdaptiveRecommendation

        Raises:
            RecommendationNotFoundException: If not found
            LearningPathDAOException: On database errors
        """
        query = """
            UPDATE adaptive_recommendations SET
                status = $2, viewed_at = $3, acted_on_at = $4,
                user_feedback = $5, updated_at = $6
            WHERE id = $1
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    recommendation.id, recommendation.status.value,
                    recommendation.viewed_at, recommendation.acted_on_at,
                    recommendation.user_feedback, datetime.utcnow()
                )
                if row is None:
                    raise RecommendationNotFoundException(
                        f"Recommendation {recommendation.id} not found"
                    )
                return self._row_to_recommendation(row)
        except RecommendationNotFoundException:
            raise
        except asyncpg.PostgresError as e:
            logger.error(f"Database error updating recommendation: {e}")
            raise LearningPathDAOException(
                f"Failed to update recommendation {recommendation.id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error updating recommendation: {e}")
            raise LearningPathDAOException(
                f"Unexpected error updating recommendation: {str(e)}"
            ) from e

    # =========================================================================
    # MASTERY LEVEL OPERATIONS
    # =========================================================================

    async def upsert_mastery_level(
        self,
        mastery: StudentMasteryLevel
    ) -> StudentMasteryLevel:
        """
        WHAT: Creates or updates student mastery level with SM-2 algorithm fields
        WHERE: Called after assessments to update skill tracking
        WHY: Maintains accurate skill mastery data including spaced repetition
             parameters for optimal review scheduling

        Args:
            mastery: StudentMasteryLevel to upsert (includes SM-2 fields)

        Returns:
            Upserted StudentMasteryLevel with all fields including SM-2 data

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            INSERT INTO student_mastery_levels (
                id, student_id, skill_topic, organization_id, course_id,
                mastery_level, mastery_score, assessments_completed,
                assessments_passed, average_score, best_score,
                total_practice_time_minutes, last_practiced_at,
                practice_streak_days, last_assessment_at, retention_estimate,
                next_review_recommended_at, ease_factor, repetition_count,
                current_interval_days, last_quality_rating,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23
            )
            ON CONFLICT (student_id, skill_topic, course_id)
            DO UPDATE SET
                mastery_level = EXCLUDED.mastery_level,
                mastery_score = EXCLUDED.mastery_score,
                assessments_completed = EXCLUDED.assessments_completed,
                assessments_passed = EXCLUDED.assessments_passed,
                average_score = EXCLUDED.average_score,
                best_score = EXCLUDED.best_score,
                total_practice_time_minutes = EXCLUDED.total_practice_time_minutes,
                last_practiced_at = EXCLUDED.last_practiced_at,
                practice_streak_days = EXCLUDED.practice_streak_days,
                last_assessment_at = EXCLUDED.last_assessment_at,
                retention_estimate = EXCLUDED.retention_estimate,
                next_review_recommended_at = EXCLUDED.next_review_recommended_at,
                ease_factor = EXCLUDED.ease_factor,
                repetition_count = EXCLUDED.repetition_count,
                current_interval_days = EXCLUDED.current_interval_days,
                last_quality_rating = EXCLUDED.last_quality_rating,
                updated_at = NOW()
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    mastery.id, mastery.student_id, mastery.skill_topic,
                    mastery.organization_id, mastery.course_id,
                    mastery.mastery_level.value, float(mastery.mastery_score),
                    mastery.assessments_completed, mastery.assessments_passed,
                    float(mastery.average_score) if mastery.average_score else None,
                    float(mastery.best_score) if mastery.best_score else None,
                    mastery.total_practice_time_minutes, mastery.last_practiced_at,
                    mastery.practice_streak_days, mastery.last_assessment_at,
                    float(mastery.retention_estimate),
                    mastery.next_review_recommended_at,
                    float(mastery.ease_factor),
                    mastery.repetition_count,
                    mastery.current_interval_days,
                    mastery.last_quality_rating,
                    mastery.created_at, mastery.updated_at
                )
                return self._row_to_mastery_level(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error upserting mastery level: {e}")
            raise LearningPathDAOException(
                f"Failed to upsert mastery level: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error upserting mastery level: {e}")
            raise LearningPathDAOException(
                f"Unexpected error upserting mastery level: {str(e)}"
            ) from e

    async def get_mastery_levels_by_student(
        self,
        student_id: UUID,
        course_id: Optional[UUID] = None
    ) -> List[StudentMasteryLevel]:
        """
        WHAT: Gets all mastery levels for a student
        WHERE: Called for skill dashboard display
        WHY: Shows student's skill progression

        Args:
            student_id: UUID of the student
            course_id: Optional filter by course

        Returns:
            List of StudentMasteryLevel

        Raises:
            LearningPathDAOException: On database errors
        """
        if course_id:
            query = """
                SELECT * FROM student_mastery_levels
                WHERE student_id = $1 AND course_id = $2
                ORDER BY mastery_score DESC
            """
            params = [student_id, course_id]
        else:
            query = """
                SELECT * FROM student_mastery_levels
                WHERE student_id = $1
                ORDER BY mastery_score DESC
            """
            params = [student_id]

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [self._row_to_mastery_level(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting mastery levels: {e}")
            raise LearningPathDAOException(
                f"Failed to get mastery levels for student {student_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting mastery levels: {e}")
            raise LearningPathDAOException(
                f"Unexpected error getting mastery levels: {str(e)}"
            ) from e

    async def get_skills_needing_review(
        self,
        student_id: UUID,
        limit: int = 10
    ) -> List[StudentMasteryLevel]:
        """
        WHAT: Gets skills that need review (spaced repetition)
        WHERE: Called by recommendation engine
        WHY: Identifies skills for reinforcement

        Args:
            student_id: UUID of the student
            limit: Maximum skills to return

        Returns:
            List of StudentMasteryLevel needing review

        Raises:
            LearningPathDAOException: On database errors
        """
        query = """
            SELECT * FROM student_mastery_levels
            WHERE student_id = $1
              AND next_review_recommended_at IS NOT NULL
              AND next_review_recommended_at <= NOW()
            ORDER BY next_review_recommended_at ASC
            LIMIT $2
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, student_id, limit)
                return [self._row_to_mastery_level(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting skills needing review: {e}")
            raise LearningPathDAOException(
                f"Failed to get skills needing review: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting skills needing review: {e}")
            raise LearningPathDAOException(
                f"Unexpected error getting skills needing review: {str(e)}"
            ) from e

    # =========================================================================
    # ROW CONVERSION METHODS
    # =========================================================================

    def _row_to_learning_path(self, row: asyncpg.Record) -> LearningPath:
        """
        WHAT: Converts database row to LearningPath entity
        WHERE: Called by all path retrieval methods
        WHY: Centralizes entity mapping from database
        """
        return LearningPath(
            id=row['id'],
            student_id=row['student_id'],
            organization_id=row['organization_id'],
            track_id=row['track_id'],
            name=row['name'],
            description=row['description'],
            path_type=PathType(row['path_type']),
            difficulty_level=DifficultyLevel(row['difficulty_level']),
            status=PathStatus(row['status']),
            overall_progress=Decimal(str(row['overall_progress'])),
            estimated_duration_hours=row['estimated_duration_hours'],
            actual_duration_hours=row['actual_duration_hours'],
            total_nodes=row['total_nodes'],
            completed_nodes=row['completed_nodes'],
            current_node_id=row['current_node_id'],
            adapt_to_performance=row['adapt_to_performance'],
            adapt_to_pace=row['adapt_to_pace'],
            target_completion_date=row['target_completion_date'],
            recommendation_confidence=Decimal(str(row['recommendation_confidence'])) if row['recommendation_confidence'] else None,
            last_adaptation_at=row['last_adaptation_at'],
            adaptation_count=row['adaptation_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at']
        )

    def _row_to_learning_path_node(self, row: asyncpg.Record) -> LearningPathNode:
        """
        WHAT: Converts database row to LearningPathNode entity
        WHERE: Called by all node retrieval methods
        WHY: Centralizes entity mapping from database
        """
        import json
        unlock_conditions = row['unlock_conditions']
        if isinstance(unlock_conditions, str):
            unlock_conditions = json.loads(unlock_conditions)

        return LearningPathNode(
            id=row['id'],
            learning_path_id=row['learning_path_id'],
            content_type=ContentType(row['content_type']),
            content_id=row['content_id'],
            sequence_order=row['sequence_order'],
            status=NodeStatus(row['status']),
            parent_node_id=row['parent_node_id'],
            is_required=row['is_required'],
            is_unlocked=row['is_unlocked'],
            progress_percentage=Decimal(str(row['progress_percentage'])),
            score=Decimal(str(row['score'])) if row['score'] else None,
            attempts=row['attempts'],
            max_attempts=row['max_attempts'],
            estimated_duration_minutes=row['estimated_duration_minutes'],
            actual_duration_minutes=row['actual_duration_minutes'],
            time_spent_seconds=row['time_spent_seconds'],
            difficulty_adjustment=Decimal(str(row['difficulty_adjustment'])),
            was_recommended=row['was_recommended'],
            recommendation_reason=row['recommendation_reason'],
            unlock_conditions=unlock_conditions or {},
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at']
        )

    def _row_to_prerequisite_rule(self, row: asyncpg.Record) -> PrerequisiteRule:
        """
        WHAT: Converts database row to PrerequisiteRule entity
        WHERE: Called by all prerequisite retrieval methods
        WHY: Centralizes entity mapping from database
        """
        return PrerequisiteRule(
            id=row['id'],
            target_type=ContentType(row['target_type']),
            target_id=row['target_id'],
            prerequisite_type=ContentType(row['prerequisite_type']),
            prerequisite_id=row['prerequisite_id'],
            requirement_type=RequirementType(row['requirement_type']),
            requirement_value=Decimal(str(row['requirement_value'])) if row['requirement_value'] else None,
            organization_id=row['organization_id'],
            track_id=row['track_id'],
            is_mandatory=row['is_mandatory'],
            bypass_allowed=row['bypass_allowed'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=row['created_by']
        )

    def _row_to_recommendation(self, row: asyncpg.Record) -> AdaptiveRecommendation:
        """
        WHAT: Converts database row to AdaptiveRecommendation entity
        WHERE: Called by all recommendation retrieval methods
        WHY: Centralizes entity mapping from database
        """
        import json
        trigger_metrics = row['trigger_metrics']
        if isinstance(trigger_metrics, str):
            trigger_metrics = json.loads(trigger_metrics)

        return AdaptiveRecommendation(
            id=row['id'],
            student_id=row['student_id'],
            learning_path_id=row['learning_path_id'],
            recommendation_type=RecommendationType(row['recommendation_type']),
            content_type=ContentType(row['content_type']) if row['content_type'] else None,
            content_id=row['content_id'],
            title=row['title'],
            description=row['description'],
            reason=row['reason'],
            priority=row['priority'],
            confidence_score=Decimal(str(row['confidence_score'])),
            trigger_metrics=trigger_metrics or {},
            status=RecommendationStatus(row['status']),
            valid_from=row['valid_from'],
            valid_until=row['valid_until'],
            viewed_at=row['viewed_at'],
            acted_on_at=row['acted_on_at'],
            user_feedback=row['user_feedback'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_mastery_level(self, row: asyncpg.Record) -> StudentMasteryLevel:
        """
        WHAT: Converts database row to StudentMasteryLevel entity
        WHERE: Called by all mastery retrieval methods
        WHY: Centralizes entity mapping from database, including SM-2 algorithm
             fields for spaced repetition scheduling
        """
        return StudentMasteryLevel(
            id=row['id'],
            student_id=row['student_id'],
            skill_topic=row['skill_topic'],
            organization_id=row['organization_id'],
            course_id=row['course_id'],
            mastery_level=MasteryLevel(row['mastery_level']),
            mastery_score=Decimal(str(row['mastery_score'])),
            assessments_completed=row['assessments_completed'],
            assessments_passed=row['assessments_passed'],
            average_score=Decimal(str(row['average_score'])) if row['average_score'] else None,
            best_score=Decimal(str(row['best_score'])) if row['best_score'] else None,
            total_practice_time_minutes=row['total_practice_time_minutes'],
            last_practiced_at=row['last_practiced_at'],
            practice_streak_days=row['practice_streak_days'],
            last_assessment_at=row['last_assessment_at'],
            retention_estimate=Decimal(str(row['retention_estimate'])),
            next_review_recommended_at=row['next_review_recommended_at'],
            # SM-2 Algorithm Fields (Enhancement 2: Spaced Repetition System)
            ease_factor=Decimal(str(row['ease_factor'])) if row.get('ease_factor') else Decimal("2.50"),
            repetition_count=row.get('repetition_count', 0),
            current_interval_days=row.get('current_interval_days', 1),
            last_quality_rating=row.get('last_quality_rating', 0),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
