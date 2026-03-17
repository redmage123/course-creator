"""
Instructor Insights Data Access Object

What: DAO for instructor analytics data operations.
Where: Data access layer for instructor insights tables.
Why: Centralizes all database operations for instructor analytics.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from analytics.domain.entities.instructor_insights import (
    InstructorEffectivenessMetrics,
    InstructorCoursePerformance,
    InstructorStudentEngagement,
    ContentRating,
    InstructorReview,
    InstructorTeachingLoad,
    InstructorResponseMetrics,
    InstructorRecommendation,
    InstructorPeerComparison,
    InstructorGoal,
    Trend,
    CapacityStatus,
    RecommendationPriority,
    RecommendationStatus,
    RecommendationCategory,
    GoalStatus,
    FeedbackSentiment,
    MetricCategory,
)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class InstructorInsightsDAOError(Exception):
    """
    What: Base exception for instructor insights DAO operations.
    Where: All DAO methods that encounter errors.
    Why: Provides consistent error handling for data access operations.
    """
    pass


class EffectivenessMetricsNotFoundError(InstructorInsightsDAOError):
    """
    What: Raised when effectiveness metrics are not found.
    Where: Get/update operations for effectiveness metrics.
    Why: Distinguishes between not found and other errors.
    """
    pass


class CoursePerformanceNotFoundError(InstructorInsightsDAOError):
    """
    What: Raised when course performance data is not found.
    Where: Get/update operations for course performance.
    Why: Distinguishes between not found and other errors.
    """
    pass


class ReviewNotFoundError(InstructorInsightsDAOError):
    """
    What: Raised when instructor review is not found.
    Where: Get/update operations for reviews.
    Why: Distinguishes between not found and other errors.
    """
    pass


class RecommendationNotFoundError(InstructorInsightsDAOError):
    """
    What: Raised when recommendation is not found.
    Where: Get/update operations for recommendations.
    Why: Distinguishes between not found and other errors.
    """
    pass


class GoalNotFoundError(InstructorInsightsDAOError):
    """
    What: Raised when goal is not found.
    Where: Get/update operations for goals.
    Why: Distinguishes between not found and other errors.
    """
    pass


# ============================================================================
# DAO CLASS
# ============================================================================

class InstructorInsightsDAO:
    """
    What: Data Access Object for instructor insights operations.
    Where: Data layer for analytics service.
    Why: Encapsulates all instructor analytics database operations.
    """

    def __init__(self, db_pool):
        """
        What: Initialize DAO with database connection pool.
        Where: Service initialization.
        Why: Enables async database operations.
        """
        self._pool = db_pool

    # ========================================================================
    # EFFECTIVENESS METRICS
    # ========================================================================

    async def create_effectiveness_metrics(
        self, metrics: InstructorEffectivenessMetrics
    ) -> InstructorEffectivenessMetrics:
        """
        What: Create new effectiveness metrics record.
        Where: Period-end calculations.
        Why: Stores aggregated teaching effectiveness data.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO instructor_effectiveness_metrics (
                        id, instructor_id, organization_id,
                        overall_rating, teaching_quality_score, content_clarity_score,
                        engagement_score, responsiveness_score,
                        total_students_taught, course_completion_rate,
                        average_quiz_score, student_retention_rate,
                        rating_trend, engagement_trend,
                        period_start, period_end
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    RETURNING *
                    """,
                    metrics.id, metrics.instructor_id, metrics.organization_id,
                    metrics.overall_rating, metrics.teaching_quality_score,
                    metrics.content_clarity_score, metrics.engagement_score,
                    metrics.responsiveness_score, metrics.total_students_taught,
                    metrics.course_completion_rate, metrics.average_quiz_score,
                    metrics.student_retention_rate,
                    metrics.rating_trend.value if metrics.rating_trend else None,
                    metrics.engagement_trend.value if metrics.engagement_trend else None,
                    metrics.period_start, metrics.period_end
                )
                return self._map_effectiveness_metrics(row)
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to create effectiveness metrics: {e}")

    async def get_effectiveness_metrics(
        self, instructor_id: UUID, period_start: date, period_end: date
    ) -> Optional[InstructorEffectivenessMetrics]:
        """
        What: Get effectiveness metrics for instructor and period.
        Where: Dashboard display.
        Why: Retrieves specific period's metrics.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM instructor_effectiveness_metrics
                    WHERE instructor_id = $1 AND period_start = $2 AND period_end = $3
                    """,
                    instructor_id, period_start, period_end
                )
                if row:
                    return self._map_effectiveness_metrics(row)
                return None
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get effectiveness metrics: {e}")

    async def get_latest_effectiveness_metrics(
        self, instructor_id: UUID
    ) -> Optional[InstructorEffectivenessMetrics]:
        """
        What: Get most recent effectiveness metrics.
        Where: Dashboard default view.
        Why: Quick access to current metrics.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM instructor_effectiveness_metrics
                    WHERE instructor_id = $1
                    ORDER BY period_end DESC LIMIT 1
                    """,
                    instructor_id
                )
                if row:
                    return self._map_effectiveness_metrics(row)
                return None
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get latest effectiveness metrics: {e}")

    async def update_effectiveness_metrics(
        self, metrics_id: UUID, **updates
    ) -> InstructorEffectivenessMetrics:
        """
        What: Update effectiveness metrics.
        Where: Recalculation operations.
        Why: Allows partial updates to metrics.
        """
        try:
            set_clauses = []
            values = [metrics_id]
            param_index = 2

            for key, value in updates.items():
                if key in ['rating_trend', 'engagement_trend'] and value is not None:
                    value = value.value if isinstance(value, Trend) else value
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1

            if not set_clauses:
                raise InstructorInsightsDAOError("No updates provided")

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE instructor_effectiveness_metrics
                    SET {', '.join(set_clauses)}, updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    *values
                )
                if not row:
                    raise EffectivenessMetricsNotFoundError(f"Metrics {metrics_id} not found")
                return self._map_effectiveness_metrics(row)
        except EffectivenessMetricsNotFoundError:
            raise
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to update effectiveness metrics: {e}")

    # ========================================================================
    # COURSE PERFORMANCE
    # ========================================================================

    async def create_course_performance(
        self, performance: InstructorCoursePerformance
    ) -> InstructorCoursePerformance:
        """
        What: Create course performance record.
        Where: Course analytics calculations.
        Why: Stores per-course metrics.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO instructor_course_performance (
                        id, instructor_id, course_id, course_instance_id, organization_id,
                        total_enrolled, active_students, completed_students, dropped_students,
                        average_score, median_score, score_std_deviation, pass_rate,
                        average_time_to_complete, content_views_per_student,
                        lab_completions_per_student, quiz_attempts_per_student,
                        content_rating, difficulty_rating, workload_rating,
                        period_start, period_end
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
                    RETURNING *
                    """,
                    performance.id, performance.instructor_id, performance.course_id,
                    performance.course_instance_id, performance.organization_id,
                    performance.total_enrolled, performance.active_students,
                    performance.completed_students, performance.dropped_students,
                    performance.average_score, performance.median_score,
                    performance.score_std_deviation, performance.pass_rate,
                    performance.average_time_to_complete, performance.content_views_per_student,
                    performance.lab_completions_per_student, performance.quiz_attempts_per_student,
                    performance.content_rating, performance.difficulty_rating,
                    performance.workload_rating, performance.period_start, performance.period_end
                )
                return self._map_course_performance(row)
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to create course performance: {e}")

    async def get_course_performance(
        self, instructor_id: UUID, course_id: UUID,
        period_start: Optional[date] = None
    ) -> Optional[InstructorCoursePerformance]:
        """
        What: Get course performance for instructor.
        Where: Course analytics views.
        Why: Retrieves specific course metrics.
        """
        try:
            async with self._pool.acquire() as conn:
                if period_start:
                    row = await conn.fetchrow(
                        """
                        SELECT * FROM instructor_course_performance
                        WHERE instructor_id = $1 AND course_id = $2 AND period_start = $3
                        """,
                        instructor_id, course_id, period_start
                    )
                else:
                    row = await conn.fetchrow(
                        """
                        SELECT * FROM instructor_course_performance
                        WHERE instructor_id = $1 AND course_id = $2
                        ORDER BY period_end DESC LIMIT 1
                        """,
                        instructor_id, course_id
                    )
                if row:
                    return self._map_course_performance(row)
                return None
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get course performance: {e}")

    async def get_all_course_performances(
        self, instructor_id: UUID, limit: int = 50
    ) -> list[InstructorCoursePerformance]:
        """
        What: Get all course performances for instructor.
        Where: Course list views.
        Why: Overview of all taught courses.
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM instructor_course_performance
                    WHERE instructor_id = $1
                    ORDER BY period_end DESC LIMIT $2
                    """,
                    instructor_id, limit
                )
                return [self._map_course_performance(row) for row in rows]
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get course performances: {e}")

    # ========================================================================
    # REVIEWS
    # ========================================================================

    async def create_review(self, review: InstructorReview) -> InstructorReview:
        """
        What: Create instructor review.
        Where: Student feedback submission.
        Why: Stores student reviews.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO instructor_reviews (
                        id, instructor_id, course_id, student_id, organization_id,
                        overall_rating, knowledge_rating, communication_rating,
                        availability_rating, feedback_quality_rating, organization_rating,
                        review_title, review_text, pros, cons,
                        is_approved, is_flagged
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    RETURNING *
                    """,
                    review.id, review.instructor_id, review.course_id,
                    review.student_id, review.organization_id,
                    review.overall_rating, review.knowledge_rating,
                    review.communication_rating, review.availability_rating,
                    review.feedback_quality_rating, review.organization_rating,
                    review.review_title, review.review_text, review.pros, review.cons,
                    review.is_approved, review.is_flagged
                )
                return self._map_review(row)
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to create review: {e}")

    async def get_review(self, review_id: UUID) -> Optional[InstructorReview]:
        """
        What: Get review by ID.
        Where: Review detail views.
        Why: Retrieves specific review.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM instructor_reviews WHERE id = $1",
                    review_id
                )
                if row:
                    return self._map_review(row)
                return None
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get review: {e}")

    async def get_instructor_reviews(
        self, instructor_id: UUID, approved_only: bool = True, limit: int = 50
    ) -> list[InstructorReview]:
        """
        What: Get all reviews for instructor.
        Where: Instructor review page.
        Why: Lists all feedback.
        """
        try:
            async with self._pool.acquire() as conn:
                if approved_only:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM instructor_reviews
                        WHERE instructor_id = $1 AND is_approved = true AND is_flagged = false
                        ORDER BY created_at DESC LIMIT $2
                        """,
                        instructor_id, limit
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM instructor_reviews
                        WHERE instructor_id = $1
                        ORDER BY created_at DESC LIMIT $2
                        """,
                        instructor_id, limit
                    )
                return [self._map_review(row) for row in rows]
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get instructor reviews: {e}")

    async def approve_review(self, review_id: UUID, moderated_by: UUID) -> InstructorReview:
        """
        What: Approve a review.
        Where: Moderation workflow.
        Why: Makes review visible.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE instructor_reviews
                    SET is_approved = true, moderated_by = $2, moderated_at = NOW(), updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    review_id, moderated_by
                )
                if not row:
                    raise ReviewNotFoundError(f"Review {review_id} not found")
                return self._map_review(row)
        except ReviewNotFoundError:
            raise
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to approve review: {e}")

    async def flag_review(
        self, review_id: UUID, reason: str, moderated_by: UUID
    ) -> InstructorReview:
        """
        What: Flag a review for concerns.
        Where: Moderation workflow.
        Why: Marks problematic reviews.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE instructor_reviews
                    SET is_flagged = true, flagged_reason = $2, moderated_by = $3, moderated_at = NOW(), updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    review_id, reason, moderated_by
                )
                if not row:
                    raise ReviewNotFoundError(f"Review {review_id} not found")
                return self._map_review(row)
        except ReviewNotFoundError:
            raise
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to flag review: {e}")

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================

    async def create_recommendation(
        self, recommendation: InstructorRecommendation
    ) -> InstructorRecommendation:
        """
        What: Create improvement recommendation.
        Where: AI recommendation generation.
        Why: Stores actionable insights.
        """
        try:
            async with self._pool.acquire() as conn:
                import json
                row = await conn.fetchrow(
                    """
                    INSERT INTO instructor_recommendations (
                        id, instructor_id, course_id, organization_id,
                        recommendation_type, priority, category,
                        title, description, action_items,
                        expected_impact, estimated_effort,
                        based_on_metrics, comparison_data,
                        status, expires_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    RETURNING *
                    """,
                    recommendation.id, recommendation.instructor_id,
                    recommendation.course_id, recommendation.organization_id,
                    recommendation.recommendation_type, recommendation.priority.value,
                    recommendation.category.value, recommendation.title,
                    recommendation.description, json.dumps(recommendation.action_items),
                    recommendation.expected_impact, recommendation.estimated_effort,
                    json.dumps(recommendation.based_on_metrics),
                    json.dumps(recommendation.comparison_data),
                    recommendation.status.value, recommendation.expires_at
                )
                return self._map_recommendation(row)
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to create recommendation: {e}")

    async def get_recommendation(self, recommendation_id: UUID) -> Optional[InstructorRecommendation]:
        """
        What: Get recommendation by ID.
        Where: Recommendation detail views.
        Why: Retrieves specific recommendation.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM instructor_recommendations WHERE id = $1",
                    recommendation_id
                )
                if row:
                    return self._map_recommendation(row)
                return None
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get recommendation: {e}")

    async def get_instructor_recommendations(
        self, instructor_id: UUID, status: Optional[RecommendationStatus] = None,
        limit: int = 50
    ) -> list[InstructorRecommendation]:
        """
        What: Get recommendations for instructor.
        Where: Recommendations dashboard.
        Why: Lists actionable insights.
        """
        try:
            async with self._pool.acquire() as conn:
                if status:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM instructor_recommendations
                        WHERE instructor_id = $1 AND status = $2
                        ORDER BY priority DESC, generated_at DESC LIMIT $3
                        """,
                        instructor_id, status.value, limit
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM instructor_recommendations
                        WHERE instructor_id = $1
                        ORDER BY priority DESC, generated_at DESC LIMIT $2
                        """,
                        instructor_id, limit
                    )
                return [self._map_recommendation(row) for row in rows]
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get recommendations: {e}")

    async def update_recommendation_status(
        self, recommendation_id: UUID, status: RecommendationStatus,
        dismissed_reason: Optional[str] = None
    ) -> InstructorRecommendation:
        """
        What: Update recommendation status.
        Where: Status tracking.
        Why: Tracks instructor engagement.
        """
        try:
            async with self._pool.acquire() as conn:
                if status == RecommendationStatus.ACKNOWLEDGED:
                    row = await conn.fetchrow(
                        """
                        UPDATE instructor_recommendations
                        SET status = $2, acknowledged_at = NOW(), updated_at = NOW()
                        WHERE id = $1
                        RETURNING *
                        """,
                        recommendation_id, status.value
                    )
                elif status == RecommendationStatus.COMPLETED:
                    row = await conn.fetchrow(
                        """
                        UPDATE instructor_recommendations
                        SET status = $2, completed_at = NOW(), updated_at = NOW()
                        WHERE id = $1
                        RETURNING *
                        """,
                        recommendation_id, status.value
                    )
                elif status == RecommendationStatus.DISMISSED:
                    row = await conn.fetchrow(
                        """
                        UPDATE instructor_recommendations
                        SET status = $2, dismissed_reason = $3, updated_at = NOW()
                        WHERE id = $1
                        RETURNING *
                        """,
                        recommendation_id, status.value, dismissed_reason
                    )
                else:
                    row = await conn.fetchrow(
                        """
                        UPDATE instructor_recommendations
                        SET status = $2, updated_at = NOW()
                        WHERE id = $1
                        RETURNING *
                        """,
                        recommendation_id, status.value
                    )
                if not row:
                    raise RecommendationNotFoundError(f"Recommendation {recommendation_id} not found")
                return self._map_recommendation(row)
        except RecommendationNotFoundError:
            raise
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to update recommendation status: {e}")

    # ========================================================================
    # GOALS
    # ========================================================================

    async def create_goal(self, goal: InstructorGoal) -> InstructorGoal:
        """
        What: Create instructor goal.
        Where: Goal setting.
        Why: Enables personal development tracking.
        """
        try:
            async with self._pool.acquire() as conn:
                import json
                row = await conn.fetchrow(
                    """
                    INSERT INTO instructor_goals (
                        id, instructor_id, organization_id,
                        goal_type, title, description,
                        metric_name, baseline_value, target_value, current_value,
                        progress_percentage, start_date, target_date,
                        status, milestones, notes
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    RETURNING *
                    """,
                    goal.id, goal.instructor_id, goal.organization_id,
                    goal.goal_type, goal.title, goal.description,
                    goal.metric_name, goal.baseline_value, goal.target_value,
                    goal.current_value, goal.progress_percentage,
                    goal.start_date, goal.target_date,
                    goal.status.value, json.dumps(goal.milestones), goal.notes
                )
                return self._map_goal(row)
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to create goal: {e}")

    async def get_goal(self, goal_id: UUID) -> Optional[InstructorGoal]:
        """
        What: Get goal by ID.
        Where: Goal detail views.
        Why: Retrieves specific goal.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM instructor_goals WHERE id = $1",
                    goal_id
                )
                if row:
                    return self._map_goal(row)
                return None
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get goal: {e}")

    async def get_instructor_goals(
        self, instructor_id: UUID, status: Optional[GoalStatus] = None
    ) -> list[InstructorGoal]:
        """
        What: Get goals for instructor.
        Where: Goals dashboard.
        Why: Lists personal development goals.
        """
        try:
            async with self._pool.acquire() as conn:
                if status:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM instructor_goals
                        WHERE instructor_id = $1 AND status = $2
                        ORDER BY target_date ASC
                        """,
                        instructor_id, status.value
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM instructor_goals
                        WHERE instructor_id = $1
                        ORDER BY status, target_date ASC
                        """,
                        instructor_id
                    )
                return [self._map_goal(row) for row in rows]
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get goals: {e}")

    async def update_goal(self, goal_id: UUID, **updates) -> InstructorGoal:
        """
        What: Update goal.
        Where: Goal progress updates.
        Why: Tracks goal progress.
        """
        try:
            import json
            set_clauses = []
            values = [goal_id]
            param_index = 2

            for key, value in updates.items():
                if key == 'status' and isinstance(value, GoalStatus):
                    value = value.value
                elif key == 'milestones':
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1

            if not set_clauses:
                raise InstructorInsightsDAOError("No updates provided")

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE instructor_goals
                    SET {', '.join(set_clauses)}, updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    *values
                )
                if not row:
                    raise GoalNotFoundError(f"Goal {goal_id} not found")
                return self._map_goal(row)
        except GoalNotFoundError:
            raise
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to update goal: {e}")

    async def delete_goal(self, goal_id: UUID) -> bool:
        """
        What: Delete goal.
        Where: Goal management.
        Why: Removes cancelled goals.
        """
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM instructor_goals WHERE id = $1",
                    goal_id
                )
                return "DELETE 1" in result
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to delete goal: {e}")

    # ========================================================================
    # PEER COMPARISONS
    # ========================================================================

    async def create_peer_comparison(
        self, comparison: InstructorPeerComparison
    ) -> InstructorPeerComparison:
        """
        What: Create peer comparison record.
        Where: Analytics calculations.
        Why: Stores benchmark data.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO instructor_peer_comparison (
                        id, instructor_id, organization_id, comparison_group,
                        instructor_score, peer_average, peer_median,
                        peer_min, peer_max, peer_std_deviation,
                        percentile_rank, metric_name, metric_category,
                        sample_size, period_start, period_end
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    RETURNING *
                    """,
                    comparison.id, comparison.instructor_id, comparison.organization_id,
                    comparison.comparison_group, comparison.instructor_score,
                    comparison.peer_average, comparison.peer_median,
                    comparison.peer_min, comparison.peer_max, comparison.peer_std_deviation,
                    comparison.percentile_rank, comparison.metric_name,
                    comparison.metric_category.value, comparison.sample_size,
                    comparison.period_start, comparison.period_end
                )
                return self._map_peer_comparison(row)
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to create peer comparison: {e}")

    async def get_peer_comparisons(
        self, instructor_id: UUID, metric_category: Optional[MetricCategory] = None
    ) -> list[InstructorPeerComparison]:
        """
        What: Get peer comparisons for instructor.
        Where: Benchmarking views.
        Why: Shows relative performance.
        """
        try:
            async with self._pool.acquire() as conn:
                if metric_category:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM instructor_peer_comparison
                        WHERE instructor_id = $1 AND metric_category = $2
                        ORDER BY calculated_at DESC
                        """,
                        instructor_id, metric_category.value
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM instructor_peer_comparison
                        WHERE instructor_id = $1
                        ORDER BY calculated_at DESC
                        """,
                        instructor_id
                    )
                return [self._map_peer_comparison(row) for row in rows]
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get peer comparisons: {e}")

    # ========================================================================
    # TEACHING LOAD
    # ========================================================================

    async def create_teaching_load(
        self, load: InstructorTeachingLoad
    ) -> InstructorTeachingLoad:
        """
        What: Create teaching load record.
        Where: Workload calculations.
        Why: Tracks instructor capacity.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO instructor_teaching_load (
                        id, instructor_id, organization_id,
                        active_courses, total_courses_taught, courses_this_period,
                        current_students, total_students_capacity, student_load_percentage,
                        teaching_hours_per_week, grading_hours_per_week,
                        support_hours_per_week, content_creation_hours_per_week,
                        assignments_pending_grading, questions_pending_response,
                        estimated_pending_hours, capacity_status, recommended_action,
                        period_start, period_end
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    RETURNING *
                    """,
                    load.id, load.instructor_id, load.organization_id,
                    load.active_courses, load.total_courses_taught, load.courses_this_period,
                    load.current_students, load.total_students_capacity,
                    load.student_load_percentage, load.teaching_hours_per_week,
                    load.grading_hours_per_week, load.support_hours_per_week,
                    load.content_creation_hours_per_week, load.assignments_pending_grading,
                    load.questions_pending_response, load.estimated_pending_hours,
                    load.capacity_status.value, load.recommended_action,
                    load.period_start, load.period_end
                )
                return self._map_teaching_load(row)
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to create teaching load: {e}")

    async def get_latest_teaching_load(
        self, instructor_id: UUID
    ) -> Optional[InstructorTeachingLoad]:
        """
        What: Get latest teaching load.
        Where: Workload dashboard.
        Why: Current capacity status.
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM instructor_teaching_load
                    WHERE instructor_id = $1
                    ORDER BY period_end DESC LIMIT 1
                    """,
                    instructor_id
                )
                if row:
                    return self._map_teaching_load(row)
                return None
        except Exception as e:
            raise InstructorInsightsDAOError(f"Failed to get teaching load: {e}")

    # ========================================================================
    # MAPPING METHODS
    # ========================================================================

    def _map_effectiveness_metrics(self, row) -> InstructorEffectivenessMetrics:
        """Map database row to InstructorEffectivenessMetrics entity."""
        return InstructorEffectivenessMetrics(
            id=row['id'],
            instructor_id=row['instructor_id'],
            organization_id=row['organization_id'],
            overall_rating=row['overall_rating'],
            teaching_quality_score=row['teaching_quality_score'],
            content_clarity_score=row['content_clarity_score'],
            engagement_score=row['engagement_score'],
            responsiveness_score=row['responsiveness_score'],
            total_students_taught=row['total_students_taught'] or 0,
            course_completion_rate=row['course_completion_rate'],
            average_quiz_score=row['average_quiz_score'],
            student_retention_rate=row['student_retention_rate'],
            rating_trend=Trend(row['rating_trend']) if row['rating_trend'] else None,
            engagement_trend=Trend(row['engagement_trend']) if row['engagement_trend'] else None,
            period_start=row['period_start'],
            period_end=row['period_end'],
            calculated_at=row['calculated_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_course_performance(self, row) -> InstructorCoursePerformance:
        """Map database row to InstructorCoursePerformance entity."""
        return InstructorCoursePerformance(
            id=row['id'],
            instructor_id=row['instructor_id'],
            course_id=row['course_id'],
            course_instance_id=row['course_instance_id'],
            organization_id=row['organization_id'],
            total_enrolled=row['total_enrolled'] or 0,
            active_students=row['active_students'] or 0,
            completed_students=row['completed_students'] or 0,
            dropped_students=row['dropped_students'] or 0,
            average_score=row['average_score'],
            median_score=row['median_score'],
            score_std_deviation=row['score_std_deviation'],
            pass_rate=row['pass_rate'],
            average_time_to_complete=row['average_time_to_complete'],
            content_views_per_student=row['content_views_per_student'],
            lab_completions_per_student=row['lab_completions_per_student'],
            quiz_attempts_per_student=row['quiz_attempts_per_student'],
            content_rating=row['content_rating'],
            difficulty_rating=row['difficulty_rating'],
            workload_rating=row['workload_rating'],
            period_start=row['period_start'],
            period_end=row['period_end'],
            calculated_at=row['calculated_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_review(self, row) -> InstructorReview:
        """Map database row to InstructorReview entity."""
        return InstructorReview(
            id=row['id'],
            instructor_id=row['instructor_id'],
            course_id=row['course_id'],
            student_id=row['student_id'],
            organization_id=row['organization_id'],
            overall_rating=row['overall_rating'],
            knowledge_rating=row['knowledge_rating'],
            communication_rating=row['communication_rating'],
            availability_rating=row['availability_rating'],
            feedback_quality_rating=row['feedback_quality_rating'],
            organization_rating=row['organization_rating'],
            review_title=row['review_title'],
            review_text=row['review_text'],
            pros=row['pros'],
            cons=row['cons'],
            is_approved=row['is_approved'],
            is_flagged=row['is_flagged'],
            flagged_reason=row['flagged_reason'],
            moderated_by=row['moderated_by'],
            moderated_at=row['moderated_at'],
            helpful_count=row['helpful_count'] or 0,
            not_helpful_count=row['not_helpful_count'] or 0,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_recommendation(self, row) -> InstructorRecommendation:
        """Map database row to InstructorRecommendation entity."""
        import json
        action_items = row['action_items']
        if isinstance(action_items, str):
            action_items = json.loads(action_items)
        based_on = row['based_on_metrics']
        if isinstance(based_on, str):
            based_on = json.loads(based_on)
        comparison = row['comparison_data']
        if isinstance(comparison, str):
            comparison = json.loads(comparison)

        return InstructorRecommendation(
            id=row['id'],
            instructor_id=row['instructor_id'],
            course_id=row['course_id'],
            organization_id=row['organization_id'],
            recommendation_type=row['recommendation_type'],
            priority=RecommendationPriority(row['priority']),
            category=RecommendationCategory(row['category']),
            title=row['title'],
            description=row['description'],
            action_items=action_items or [],
            expected_impact=row['expected_impact'],
            estimated_effort=row['estimated_effort'],
            based_on_metrics=based_on or {},
            comparison_data=comparison or {},
            status=RecommendationStatus(row['status']),
            acknowledged_at=row['acknowledged_at'],
            completed_at=row['completed_at'],
            dismissed_reason=row['dismissed_reason'],
            outcome_measured=row['outcome_measured'] or False,
            outcome_data=row['outcome_data'],
            generated_at=row['generated_at'],
            expires_at=row['expires_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_goal(self, row) -> InstructorGoal:
        """Map database row to InstructorGoal entity."""
        import json
        milestones = row['milestones']
        if isinstance(milestones, str):
            milestones = json.loads(milestones)

        return InstructorGoal(
            id=row['id'],
            instructor_id=row['instructor_id'],
            organization_id=row['organization_id'],
            goal_type=row['goal_type'],
            title=row['title'],
            description=row['description'],
            metric_name=row['metric_name'],
            baseline_value=row['baseline_value'],
            target_value=row['target_value'],
            current_value=row['current_value'],
            progress_percentage=row['progress_percentage'] or Decimal("0"),
            start_date=row['start_date'],
            target_date=row['target_date'],
            completed_date=row['completed_date'],
            status=GoalStatus(row['status']),
            milestones=milestones or [],
            notes=row['notes'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _map_peer_comparison(self, row) -> InstructorPeerComparison:
        """Map database row to InstructorPeerComparison entity."""
        return InstructorPeerComparison(
            id=row['id'],
            instructor_id=row['instructor_id'],
            organization_id=row['organization_id'],
            comparison_group=row['comparison_group'],
            instructor_score=row['instructor_score'],
            peer_average=row['peer_average'],
            peer_median=row['peer_median'],
            peer_min=row['peer_min'],
            peer_max=row['peer_max'],
            peer_std_deviation=row['peer_std_deviation'],
            percentile_rank=row['percentile_rank'],
            metric_name=row['metric_name'],
            metric_category=MetricCategory(row['metric_category']),
            sample_size=row['sample_size'],
            period_start=row['period_start'],
            period_end=row['period_end'],
            calculated_at=row['calculated_at'],
            created_at=row['created_at'],
        )

    def _map_teaching_load(self, row) -> InstructorTeachingLoad:
        """Map database row to InstructorTeachingLoad entity."""
        return InstructorTeachingLoad(
            id=row['id'],
            instructor_id=row['instructor_id'],
            organization_id=row['organization_id'],
            active_courses=row['active_courses'] or 0,
            total_courses_taught=row['total_courses_taught'] or 0,
            courses_this_period=row['courses_this_period'] or 0,
            current_students=row['current_students'] or 0,
            total_students_capacity=row['total_students_capacity'],
            student_load_percentage=row['student_load_percentage'],
            teaching_hours_per_week=row['teaching_hours_per_week'],
            grading_hours_per_week=row['grading_hours_per_week'],
            support_hours_per_week=row['support_hours_per_week'],
            content_creation_hours_per_week=row['content_creation_hours_per_week'],
            assignments_pending_grading=row['assignments_pending_grading'] or 0,
            questions_pending_response=row['questions_pending_response'] or 0,
            estimated_pending_hours=row['estimated_pending_hours'],
            capacity_status=CapacityStatus(row['capacity_status']),
            recommended_action=row['recommended_action'],
            period_start=row['period_start'],
            period_end=row['period_end'],
            calculated_at=row['calculated_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )
