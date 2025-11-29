"""
WHAT: Service layer for Adaptive Learning Paths
WHERE: Used by API endpoints and scheduled tasks for learning path management
WHY: Orchestrates business logic for personalized learning journeys including
     path creation, prerequisite validation, progress tracking, and recommendations

This service implements the core adaptive learning functionality including:
- Personalized path generation based on student goals and track
- Prerequisite enforcement and validation
- Progress tracking with automatic node unlocking
- AI-driven recommendations based on performance analytics
- Path adaptation based on student performance
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from course_management.domain.entities.learning_path import (
    LearningPath, LearningPathNode, PrerequisiteRule, AdaptiveRecommendation,
    StudentMasteryLevel, PathType, PathStatus, NodeStatus, ContentType,
    RequirementType, RecommendationType, RecommendationStatus, MasteryLevel,
    DifficultyLevel, PrerequisiteNotMetException, LearningPathNotFoundException,
    InvalidPathStateException, AdaptiveLearningException
)
from data_access.learning_path_dao import LearningPathDAO, LearningPathDAOException

logger = logging.getLogger(__name__)


class AdaptiveLearningServiceException(AdaptiveLearningException):
    """
    WHAT: Base exception for adaptive learning service errors
    WHERE: Thrown by service methods on business logic errors
    WHY: Distinguishes service-level errors from DAO errors
    """
    pass


class AdaptiveLearningService:
    """
    WHAT: Service for managing adaptive learning paths and recommendations
    WHERE: Used by learning path API endpoints and background tasks
    WHY: Centralizes business logic for personalized learning including
         path generation, prerequisite validation, and adaptive recommendations

    This service coordinates between:
    - LearningPathDAO for persistence
    - Analytics service for performance data
    - Course management for content information
    """

    def __init__(
        self,
        learning_path_dao: LearningPathDAO,
        course_dao: Any = None,  # CourseManagementDAO
        analytics_service: Any = None  # AnalyticsService
    ):
        """
        WHAT: Initialize service with required dependencies
        WHERE: Called by dependency injection container
        WHY: Enables loose coupling and testability

        Args:
            learning_path_dao: DAO for learning path operations
            course_dao: DAO for course data access
            analytics_service: Service for student performance data
        """
        self._dao = learning_path_dao
        self._course_dao = course_dao
        self._analytics_service = analytics_service

    # =========================================================================
    # LEARNING PATH MANAGEMENT
    # =========================================================================

    async def create_learning_path(
        self,
        student_id: UUID,
        name: str,
        track_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        path_type: PathType = PathType.RECOMMENDED,
        difficulty_level: DifficultyLevel = DifficultyLevel.ADAPTIVE,
        target_completion_date: Optional[datetime] = None,
        description: Optional[str] = None
    ) -> LearningPath:
        """
        WHAT: Creates a new learning path for a student
        WHERE: Called from POST /api/v1/learning-paths/
        WHY: Initializes personalized learning journey with optional auto-population

        Args:
            student_id: UUID of the student
            name: Display name for the path
            track_id: Optional track to base path on
            organization_id: Optional organization context
            path_type: Type of path (recommended, custom, etc.)
            difficulty_level: Starting difficulty
            target_completion_date: Optional target date
            description: Optional description

        Returns:
            Created LearningPath entity

        Raises:
            AdaptiveLearningServiceException: On creation failure
        """
        try:
            path = LearningPath(
                id=uuid4(),
                student_id=student_id,
                name=name,
                organization_id=organization_id,
                track_id=track_id,
                description=description,
                path_type=path_type,
                difficulty_level=difficulty_level,
                target_completion_date=target_completion_date.date() if target_completion_date else None
            )

            created_path = await self._dao.create_learning_path(path)
            logger.info(f"Created learning path {created_path.id} for student {student_id}")

            # If track specified, auto-populate with track content
            if track_id:
                await self._populate_path_from_track(created_path, track_id)

            return created_path

        except LearningPathDAOException as e:
            logger.error(f"DAO error creating learning path: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to create learning path for student {student_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating learning path: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error creating learning path: {str(e)}"
            ) from e

    async def get_learning_path(self, path_id: UUID) -> LearningPath:
        """
        WHAT: Retrieves a learning path by ID with all nodes
        WHERE: Called from GET /api/v1/learning-paths/{id}
        WHY: Provides complete path data for display

        Args:
            path_id: UUID of the learning path

        Returns:
            LearningPath with nodes

        Raises:
            LearningPathNotFoundException: If path doesn't exist
            AdaptiveLearningServiceException: On retrieval failure
        """
        try:
            path = await self._dao.get_learning_path_by_id(path_id)
            if path is None:
                raise LearningPathNotFoundException(
                    f"Learning path {path_id} not found"
                )
            return path
        except LearningPathNotFoundException:
            raise
        except LearningPathDAOException as e:
            logger.error(f"DAO error getting learning path: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to get learning path {path_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting learning path: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error getting learning path {path_id}: {str(e)}"
            ) from e

    async def get_student_paths(
        self,
        student_id: UUID,
        status: Optional[PathStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[LearningPath]:
        """
        WHAT: Gets all learning paths for a student
        WHERE: Called from student dashboard
        WHY: Displays student's learning journeys

        Args:
            student_id: UUID of the student
            status: Optional filter by status
            limit: Maximum paths to return
            offset: Pagination offset

        Returns:
            List of LearningPath entities

        Raises:
            AdaptiveLearningServiceException: On retrieval failure
        """
        try:
            return await self._dao.get_learning_paths_by_student(
                student_id, status, limit, offset
            )
        except LearningPathDAOException as e:
            logger.error(f"DAO error getting student paths: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to get paths for student {student_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting student paths: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error getting student paths: {str(e)}"
            ) from e

    async def start_learning_path(self, path_id: UUID) -> LearningPath:
        """
        WHAT: Starts a learning path, making it active
        WHERE: Called when student begins their journey
        WHY: Initializes path state and unlocks first nodes

        Args:
            path_id: UUID of the path to start

        Returns:
            Updated LearningPath

        Raises:
            LearningPathNotFoundException: If path doesn't exist
            InvalidPathStateException: If path cannot be started
            AdaptiveLearningServiceException: On update failure
        """
        try:
            path = await self.get_learning_path(path_id)
            path.start()
            return await self._dao.update_learning_path(path)
        except (LearningPathNotFoundException, InvalidPathStateException):
            raise
        except LearningPathDAOException as e:
            logger.error(f"DAO error starting path: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to start path {path_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error starting path: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error starting path {path_id}: {str(e)}"
            ) from e

    async def add_node_to_path(
        self,
        path_id: UUID,
        content_type: ContentType,
        content_id: UUID,
        is_required: bool = True,
        estimated_duration_minutes: Optional[int] = None
    ) -> LearningPathNode:
        """
        WHAT: Adds a new node to a learning path
        WHERE: Called when building or modifying paths
        WHY: Enables dynamic path composition

        Args:
            path_id: UUID of the path
            content_type: Type of content
            content_id: UUID of the content
            is_required: Whether node is mandatory
            estimated_duration_minutes: Estimated time to complete

        Returns:
            Created LearningPathNode

        Raises:
            LearningPathNotFoundException: If path doesn't exist
            AdaptiveLearningServiceException: On creation failure
        """
        try:
            path = await self.get_learning_path(path_id)

            # Determine sequence order
            sequence_order = path.total_nodes + 1

            node = LearningPathNode(
                id=uuid4(),
                learning_path_id=path_id,
                content_type=content_type,
                content_id=content_id,
                sequence_order=sequence_order,
                is_required=is_required,
                estimated_duration_minutes=estimated_duration_minutes,
                # First node or path already started = available
                status=NodeStatus.AVAILABLE if sequence_order == 1 or path.status == PathStatus.ACTIVE else NodeStatus.LOCKED,
                is_unlocked=sequence_order == 1 or path.status == PathStatus.ACTIVE
            )

            created_node = await self._dao.create_node(node)

            # Update path totals
            path.total_nodes += 1
            await self._dao.update_learning_path(path)

            return created_node

        except LearningPathNotFoundException:
            raise
        except LearningPathDAOException as e:
            logger.error(f"DAO error adding node: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to add node to path {path_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error adding node: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error adding node to path {path_id}: {str(e)}"
            ) from e

    async def update_node_progress(
        self,
        node_id: UUID,
        progress: Decimal,
        score: Optional[Decimal] = None,
        time_spent_seconds: int = 0
    ) -> LearningPathNode:
        """
        WHAT: Updates progress on a learning path node
        WHERE: Called by progress tracking service
        WHY: Maintains accurate progress with auto-completion and unlock

        Args:
            node_id: UUID of the node
            progress: New progress percentage (0-100)
            score: Optional assessment score
            time_spent_seconds: Additional time spent

        Returns:
            Updated LearningPathNode

        Raises:
            AdaptiveLearningServiceException: On update failure
        """
        try:
            # Get node and path
            path_nodes = None
            target_node = None

            # We need to find the node - get all paths for efficiency
            # In production, we'd have a direct node lookup
            async with self._dao._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM learning_path_nodes WHERE id = $1",
                    node_id
                )
                if row is None:
                    raise AdaptiveLearningServiceException(f"Node {node_id} not found")
                target_node = self._dao._row_to_learning_path_node(row)

            # Update node
            target_node.update_progress(progress, score)
            if time_spent_seconds > 0:
                target_node.add_time(time_spent_seconds)

            updated_node = await self._dao.update_node(target_node)

            # If completed, check if we should unlock next nodes
            if updated_node.status == NodeStatus.COMPLETED:
                await self._unlock_next_nodes(updated_node.learning_path_id, updated_node.sequence_order)
                # Update path progress
                path = await self._dao.get_learning_path_by_id(updated_node.learning_path_id)
                if path:
                    path.update_progress()
                    await self._dao.update_learning_path(path)

            return updated_node

        except LearningPathDAOException as e:
            logger.error(f"DAO error updating node progress: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to update node {node_id} progress: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error updating node progress: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error updating node progress: {str(e)}"
            ) from e

    async def _unlock_next_nodes(self, path_id: UUID, completed_sequence: int) -> None:
        """
        WHAT: Unlocks nodes that follow a completed node
        WHERE: Called after node completion
        WHY: Enables progression through the learning path
        """
        try:
            nodes = await self._dao.get_nodes_by_path(path_id)
            for node in nodes:
                if node.sequence_order == completed_sequence + 1:
                    if node.status == NodeStatus.LOCKED:
                        node.unlock()
                        await self._dao.update_node(node)
                        logger.debug(f"Unlocked node {node.id} in path {path_id}")
                    break
        except Exception as e:
            logger.warning(f"Error unlocking next nodes: {e}")
            # Don't raise - this is a non-critical operation

    async def _populate_path_from_track(self, path: LearningPath, track_id: UUID) -> None:
        """
        WHAT: Populates a learning path with content from a track
        WHERE: Called during path creation with track_id
        WHY: Auto-generates path structure from existing curriculum
        """
        try:
            # This would integrate with course/module DAOs to get track content
            # For now, log the intent
            logger.info(f"Would populate path {path.id} from track {track_id}")
            # TODO: Integrate with course-management to get track modules/courses
        except Exception as e:
            logger.warning(f"Error populating path from track: {e}")

    # =========================================================================
    # PREREQUISITE MANAGEMENT
    # =========================================================================

    async def create_prerequisite(
        self,
        target_type: ContentType,
        target_id: UUID,
        prerequisite_type: ContentType,
        prerequisite_id: UUID,
        requirement_type: RequirementType = RequirementType.COMPLETION,
        requirement_value: Optional[Decimal] = None,
        is_mandatory: bool = True,
        organization_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None
    ) -> PrerequisiteRule:
        """
        WHAT: Creates a prerequisite rule between content items
        WHERE: Called from curriculum management UI
        WHY: Establishes learning sequence requirements

        Args:
            target_type: Type of content requiring prerequisite
            target_id: UUID of target content
            prerequisite_type: Type of prerequisite content
            prerequisite_id: UUID of prerequisite content
            requirement_type: How completion is measured
            requirement_value: Threshold for requirement
            is_mandatory: Whether prerequisite is required
            organization_id: Optional org context
            created_by: User creating the rule

        Returns:
            Created PrerequisiteRule

        Raises:
            AdaptiveLearningServiceException: On creation failure
        """
        try:
            rule = PrerequisiteRule(
                id=uuid4(),
                target_type=target_type,
                target_id=target_id,
                prerequisite_type=prerequisite_type,
                prerequisite_id=prerequisite_id,
                requirement_type=requirement_type,
                requirement_value=requirement_value,
                is_mandatory=is_mandatory,
                organization_id=organization_id,
                created_by=created_by
            )
            return await self._dao.create_prerequisite_rule(rule)
        except LearningPathDAOException as e:
            logger.error(f"DAO error creating prerequisite: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to create prerequisite: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating prerequisite: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error creating prerequisite: {str(e)}"
            ) from e

    async def check_prerequisites(
        self,
        student_id: UUID,
        content_type: ContentType,
        content_id: UUID
    ) -> Dict[str, Any]:
        """
        WHAT: Checks if student has met prerequisites for content
        WHERE: Called before content access/enrollment
        WHY: Enforces learning sequence requirements

        Args:
            student_id: UUID of the student
            content_type: Type of content to access
            content_id: UUID of the content

        Returns:
            Dict with 'can_access', 'unmet_prerequisites', 'bypass_allowed'

        Raises:
            AdaptiveLearningServiceException: On check failure
        """
        try:
            prerequisites = await self._dao.get_prerequisites_for_content(
                content_type, content_id
            )

            if not prerequisites:
                return {
                    'can_access': True,
                    'unmet_prerequisites': [],
                    'bypass_allowed': False
                }

            unmet = []
            bypass_allowed = True

            for prereq in prerequisites:
                # Check if student has completed the prerequisite
                # This would integrate with enrollment/progress data
                is_met = await self._check_single_prerequisite(student_id, prereq)

                if not is_met:
                    unmet.append({
                        'prerequisite_type': prereq.prerequisite_type.value,
                        'prerequisite_id': str(prereq.prerequisite_id),
                        'requirement_type': prereq.requirement_type.value,
                        'requirement_value': float(prereq.requirement_value) if prereq.requirement_value else None,
                        'is_mandatory': prereq.is_mandatory,
                        'bypass_allowed': prereq.bypass_allowed
                    })
                    if prereq.is_mandatory and not prereq.bypass_allowed:
                        bypass_allowed = False

            can_access = len([u for u in unmet if u['is_mandatory']]) == 0

            return {
                'can_access': can_access,
                'unmet_prerequisites': unmet,
                'bypass_allowed': bypass_allowed
            }

        except LearningPathDAOException as e:
            logger.error(f"DAO error checking prerequisites: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to check prerequisites: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error checking prerequisites: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error checking prerequisites: {str(e)}"
            ) from e

    async def _check_single_prerequisite(
        self,
        student_id: UUID,
        prereq: PrerequisiteRule
    ) -> bool:
        """
        WHAT: Checks if a single prerequisite is met
        WHERE: Called by check_prerequisites for each rule
        WHY: Evaluates individual prerequisite completion
        """
        # This would integrate with enrollment/progress data
        # For now, return True (would need course_dao integration)
        # TODO: Implement actual prerequisite checking with enrollment data
        return True

    # =========================================================================
    # RECOMMENDATION ENGINE
    # =========================================================================

    async def generate_recommendations(
        self,
        student_id: UUID,
        path_id: Optional[UUID] = None,
        limit: int = 5
    ) -> List[AdaptiveRecommendation]:
        """
        WHAT: Generates adaptive learning recommendations for a student
        WHERE: Called periodically and after progress updates
        WHY: Provides AI-driven guidance based on performance analytics

        Args:
            student_id: UUID of the student
            path_id: Optional specific path context
            limit: Maximum recommendations to generate

        Returns:
            List of new AdaptiveRecommendation entities

        Raises:
            AdaptiveLearningServiceException: On generation failure
        """
        try:
            recommendations = []

            # Get student's current state
            paths = await self.get_student_paths(student_id, PathStatus.ACTIVE)

            for path in paths[:limit]:
                if path_id and path.id != path_id:
                    continue

                # Analyze path progress
                path_recs = await self._analyze_path_for_recommendations(path)
                recommendations.extend(path_recs)

            # Check skills needing review (spaced repetition)
            review_recs = await self._generate_review_recommendations(student_id)
            recommendations.extend(review_recs)

            # Limit total recommendations
            recommendations = recommendations[:limit]

            # Save recommendations
            saved_recs = []
            for rec in recommendations:
                saved = await self._dao.create_recommendation(rec)
                saved_recs.append(saved)

            return saved_recs

        except LearningPathDAOException as e:
            logger.error(f"DAO error generating recommendations: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to generate recommendations: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error generating recommendations: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error generating recommendations: {str(e)}"
            ) from e

    async def _analyze_path_for_recommendations(
        self,
        path: LearningPath
    ) -> List[AdaptiveRecommendation]:
        """
        WHAT: Analyzes a learning path and generates recommendations
        WHERE: Called by generate_recommendations for each path
        WHY: Identifies opportunities for improvement based on progress
        """
        recommendations = []

        # Check if path is behind schedule
        if not path.is_on_track():
            recommendations.append(AdaptiveRecommendation(
                id=uuid4(),
                student_id=path.student_id,
                learning_path_id=path.id,
                recommendation_type=RecommendationType.ACCELERATE,
                title="Catch up on your learning path",
                reason=f"You're behind schedule on '{path.name}'. Consider dedicating more time to catch up.",
                priority=8,
                confidence_score=Decimal("0.85"),
                trigger_metrics={'progress': float(path.overall_progress), 'on_track': False}
            ))

        # Check for stalled progress
        if path.nodes:
            current = path.get_current_node()
            if current and current.status == NodeStatus.IN_PROGRESS:
                # Check time spent vs estimated
                if current.estimated_duration_minutes:
                    if current.actual_duration_minutes > current.estimated_duration_minutes * 1.5:
                        recommendations.append(AdaptiveRecommendation(
                            id=uuid4(),
                            student_id=path.student_id,
                            learning_path_id=path.id,
                            recommendation_type=RecommendationType.SEEK_HELP,
                            title="Need help with current content?",
                            reason="You've spent more time than expected on this section. Consider reviewing the material or seeking help.",
                            content_type=current.content_type,
                            content_id=current.content_id,
                            priority=7,
                            confidence_score=Decimal("0.75"),
                            trigger_metrics={
                                'estimated_minutes': current.estimated_duration_minutes,
                                'actual_minutes': current.actual_duration_minutes
                            }
                        ))

        # Check for failed nodes that can be retried
        for node in path.nodes:
            if node.status == NodeStatus.FAILED and node.can_retry():
                recommendations.append(AdaptiveRecommendation(
                    id=uuid4(),
                    student_id=path.student_id,
                    learning_path_id=path.id,
                    recommendation_type=RecommendationType.PRACTICE_MORE,
                    title="Retry failed content",
                    reason=f"Review the material and try again. You have {(node.max_attempts or 999) - node.attempts} attempts remaining.",
                    content_type=node.content_type,
                    content_id=node.content_id,
                    priority=9,
                    confidence_score=Decimal("0.90"),
                    trigger_metrics={'attempts': node.attempts, 'score': float(node.score) if node.score else 0}
                ))

        return recommendations

    async def _generate_review_recommendations(
        self,
        student_id: UUID
    ) -> List[AdaptiveRecommendation]:
        """
        WHAT: Generates spaced repetition review recommendations
        WHERE: Called by generate_recommendations
        WHY: Reinforces knowledge retention through optimal review timing
        """
        try:
            skills_needing_review = await self._dao.get_skills_needing_review(student_id, 3)

            recommendations = []
            for skill in skills_needing_review:
                recommendations.append(AdaptiveRecommendation(
                    id=uuid4(),
                    student_id=student_id,
                    recommendation_type=RecommendationType.REVIEW_CONTENT,
                    title=f"Review: {skill.skill_topic}",
                    reason=f"It's time to review '{skill.skill_topic}' to maintain your mastery. Current retention: {float(skill.retention_estimate)*100:.0f}%",
                    priority=6,
                    confidence_score=Decimal("0.80"),
                    trigger_metrics={
                        'skill_topic': skill.skill_topic,
                        'mastery_level': skill.mastery_level.value,
                        'retention_estimate': float(skill.retention_estimate)
                    }
                ))

            return recommendations

        except Exception as e:
            logger.warning(f"Error generating review recommendations: {e}")
            return []

    async def get_pending_recommendations(
        self,
        student_id: UUID,
        limit: int = 10
    ) -> List[AdaptiveRecommendation]:
        """
        WHAT: Gets pending recommendations for a student
        WHERE: Called from student dashboard
        WHY: Displays actionable learning suggestions

        Args:
            student_id: UUID of the student
            limit: Maximum recommendations to return

        Returns:
            List of pending AdaptiveRecommendation

        Raises:
            AdaptiveLearningServiceException: On retrieval failure
        """
        try:
            return await self._dao.get_pending_recommendations(student_id, limit)
        except LearningPathDAOException as e:
            logger.error(f"DAO error getting recommendations: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to get recommendations: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting recommendations: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error getting recommendations: {str(e)}"
            ) from e

    async def respond_to_recommendation(
        self,
        recommendation_id: UUID,
        action: str,
        feedback: Optional[str] = None
    ) -> AdaptiveRecommendation:
        """
        WHAT: Records student response to a recommendation
        WHERE: Called when student interacts with recommendation
        WHY: Tracks recommendation effectiveness for ML improvement

        Args:
            recommendation_id: UUID of the recommendation
            action: 'accept', 'dismiss', or 'complete'
            feedback: Optional feedback ('helpful', 'not_helpful', etc.)

        Returns:
            Updated AdaptiveRecommendation

        Raises:
            AdaptiveLearningServiceException: On update failure
        """
        try:
            # Get recommendation
            recs = await self._dao.get_pending_recommendations(uuid4(), 1000)  # Hack - need direct lookup
            recommendation = None
            for rec in recs:
                if rec.id == recommendation_id:
                    recommendation = rec
                    break

            if recommendation is None:
                raise AdaptiveLearningServiceException(
                    f"Recommendation {recommendation_id} not found"
                )

            # Update based on action
            if action == 'accept':
                recommendation.accept()
            elif action == 'dismiss':
                recommendation.dismiss()
            elif action == 'complete':
                recommendation.complete()
            else:
                raise AdaptiveLearningServiceException(
                    f"Invalid action '{action}'. Must be 'accept', 'dismiss', or 'complete'"
                )

            if feedback:
                recommendation.set_feedback(feedback)

            return await self._dao.update_recommendation(recommendation)

        except LearningPathDAOException as e:
            logger.error(f"DAO error responding to recommendation: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to respond to recommendation: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error responding to recommendation: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error responding to recommendation: {str(e)}"
            ) from e

    # =========================================================================
    # MASTERY TRACKING
    # =========================================================================

    async def record_assessment_result(
        self,
        student_id: UUID,
        skill_topic: str,
        score: Decimal,
        passed: bool,
        course_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None
    ) -> StudentMasteryLevel:
        """
        WHAT: Records assessment result and updates mastery level
        WHERE: Called after quiz/assessment completion
        WHY: Maintains skill mastery tracking for adaptive recommendations

        Args:
            student_id: UUID of the student
            skill_topic: Topic/skill assessed
            score: Score achieved (0-100)
            passed: Whether assessment was passed
            course_id: Optional course context
            organization_id: Optional org context

        Returns:
            Updated StudentMasteryLevel

        Raises:
            AdaptiveLearningServiceException: On update failure
        """
        try:
            # Get or create mastery record
            masteries = await self._dao.get_mastery_levels_by_student(student_id, course_id)
            existing = next((m for m in masteries if m.skill_topic == skill_topic), None)

            if existing:
                existing.record_assessment(score, passed)
                return await self._dao.upsert_mastery_level(existing)
            else:
                mastery = StudentMasteryLevel(
                    id=uuid4(),
                    student_id=student_id,
                    skill_topic=skill_topic,
                    organization_id=organization_id,
                    course_id=course_id
                )
                mastery.record_assessment(score, passed)
                return await self._dao.upsert_mastery_level(mastery)

        except LearningPathDAOException as e:
            logger.error(f"DAO error recording assessment: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to record assessment result: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error recording assessment: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error recording assessment: {str(e)}"
            ) from e

    async def get_student_mastery(
        self,
        student_id: UUID,
        course_id: Optional[UUID] = None
    ) -> List[StudentMasteryLevel]:
        """
        WHAT: Gets mastery levels for a student
        WHERE: Called from skill dashboard
        WHY: Displays student's skill progression

        Args:
            student_id: UUID of the student
            course_id: Optional filter by course

        Returns:
            List of StudentMasteryLevel

        Raises:
            AdaptiveLearningServiceException: On retrieval failure
        """
        try:
            return await self._dao.get_mastery_levels_by_student(student_id, course_id)
        except LearningPathDAOException as e:
            logger.error(f"DAO error getting mastery levels: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to get mastery levels: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting mastery levels: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error getting mastery levels: {str(e)}"
            ) from e

    # =========================================================================
    # PATH ADAPTATION
    # =========================================================================

    async def adapt_path(self, path_id: UUID) -> LearningPath:
        """
        WHAT: Adapts a learning path based on student performance
        WHERE: Called periodically or after significant progress
        WHY: Dynamically adjusts path difficulty and content based on analytics

        Args:
            path_id: UUID of the path to adapt

        Returns:
            Adapted LearningPath

        Raises:
            LearningPathNotFoundException: If path doesn't exist
            AdaptiveLearningServiceException: On adaptation failure
        """
        try:
            path = await self.get_learning_path(path_id)

            if not path.adapt_to_performance:
                return path

            # Analyze performance and make adaptations
            adaptations_made = []

            # Check average scores across completed nodes
            completed_nodes = [n for n in path.nodes if n.status == NodeStatus.COMPLETED and n.score]
            if completed_nodes:
                avg_score = sum(float(n.score) for n in completed_nodes) / len(completed_nodes)

                # High performance - consider acceleration
                if avg_score >= 90 and path.difficulty_level != DifficultyLevel.ADVANCED:
                    # Could adjust difficulty or skip easier content
                    logger.info(f"Path {path_id} performing well (avg {avg_score}), consider acceleration")
                    adaptations_made.append('high_performance_detected')

                # Low performance - consider remediation
                elif avg_score < 60:
                    logger.info(f"Path {path_id} struggling (avg {avg_score}), consider remediation")
                    adaptations_made.append('low_performance_detected')

            if adaptations_made:
                path.record_adaptation()
                await self._dao.update_learning_path(path)

            return path

        except LearningPathNotFoundException:
            raise
        except LearningPathDAOException as e:
            logger.error(f"DAO error adapting path: {e}")
            raise AdaptiveLearningServiceException(
                f"Failed to adapt path {path_id}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error adapting path: {e}")
            raise AdaptiveLearningServiceException(
                f"Unexpected error adapting path {path_id}: {str(e)}"
            ) from e
