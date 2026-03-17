"""
Instructor Insights Service

What: Service layer for instructor analytics and insights operations.
Where: Application layer orchestrating instructor analytics business logic.
Why: Provides:
     1. Teaching effectiveness measurement
     2. Course performance analysis
     3. Student engagement tracking
     4. AI-generated improvement recommendations
     5. Personal goal management
     6. Peer benchmarking (anonymized)
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

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
    MetricCategory,
)
from data_access.instructor_insights_dao import (
    InstructorInsightsDAO,
    InstructorInsightsDAOError,
    EffectivenessMetricsNotFoundError,
    CoursePerformanceNotFoundError,
    ReviewNotFoundError,
    RecommendationNotFoundError,
    GoalNotFoundError,
)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class InstructorInsightsServiceError(Exception):
    """
    What: Base exception for instructor insights service operations.
    Where: All service methods that encounter errors.
    Why: Consistent error handling for service operations.
    """
    pass


class InstructorNotFoundError(InstructorInsightsServiceError):
    """
    What: Raised when instructor is not found.
    Where: Operations requiring instructor validation.
    Why: Distinguishes between not found and other errors.
    """
    pass


class UnauthorizedInsightsAccessError(InstructorInsightsServiceError):
    """
    What: Raised when user lacks permission.
    Where: Authorization checks.
    Why: Enforces access control.
    """
    pass


class InvalidGoalConfigError(InstructorInsightsServiceError):
    """
    What: Raised when goal configuration is invalid.
    Where: Goal creation/update.
    Why: Validates goal settings.
    """
    pass


class RecommendationGenerationError(InstructorInsightsServiceError):
    """
    What: Raised when recommendation generation fails.
    Where: AI recommendation engine.
    Why: Distinguishes generation errors.
    """
    pass


# ============================================================================
# SERVICE CLASS
# ============================================================================

class InstructorInsightsService:
    """
    What: Service for instructor analytics operations.
    Where: Application layer for analytics service.
    Why: Orchestrates instructor insights business logic.
    """

    def __init__(self, dao: InstructorInsightsDAO, cache=None):
        """
        What: Initialize service with DAO and optional cache.
        Where: Service initialization.
        Why: Dependency injection for testability.
        """
        self._dao = dao
        self._cache = cache

    # ========================================================================
    # EFFECTIVENESS METRICS
    # ========================================================================

    async def get_effectiveness_metrics(
        self, instructor_id: UUID, period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> Optional[InstructorEffectivenessMetrics]:
        """
        What: Get effectiveness metrics for instructor.
        Where: Dashboard display.
        Why: Primary teaching quality indicators.
        """
        try:
            if period_start and period_end:
                return await self._dao.get_effectiveness_metrics(
                    instructor_id, period_start, period_end
                )
            return await self._dao.get_latest_effectiveness_metrics(instructor_id)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get effectiveness metrics: {e}")

    async def calculate_effectiveness_metrics(
        self, instructor_id: UUID, period_start: date, period_end: date,
        organization_id: Optional[UUID] = None
    ) -> InstructorEffectivenessMetrics:
        """
        What: Calculate effectiveness metrics for period.
        Where: Scheduled analytics jobs.
        Why: Aggregates teaching quality data.
        """
        try:
            # Get course performances for the period
            performances = await self._dao.get_all_course_performances(instructor_id)
            period_performances = [
                p for p in performances
                if p.period_start >= period_start and p.period_end <= period_end
            ]

            # Calculate aggregated metrics
            total_students = sum(p.total_enrolled for p in period_performances)
            completed_students = sum(p.completed_students for p in period_performances)

            completion_rate = None
            if total_students > 0:
                completion_rate = Decimal(completed_students) / Decimal(total_students) * 100

            avg_pass_rate = None
            pass_rates = [p.pass_rate for p in period_performances if p.pass_rate is not None]
            if pass_rates:
                avg_pass_rate = sum(pass_rates) / Decimal(len(pass_rates))

            avg_score = None
            scores = [p.average_score for p in period_performances if p.average_score is not None]
            if scores:
                avg_score = sum(scores) / Decimal(len(scores))

            avg_content_rating = None
            content_ratings = [
                p.content_rating for p in period_performances
                if p.content_rating is not None
            ]
            if content_ratings:
                avg_content_rating = sum(content_ratings) / Decimal(len(content_ratings))

            # Create metrics
            metrics = InstructorEffectivenessMetrics(
                instructor_id=instructor_id,
                organization_id=organization_id,
                overall_rating=avg_content_rating,
                teaching_quality_score=avg_pass_rate,
                course_completion_rate=completion_rate,
                average_quiz_score=avg_score,
                total_students_taught=total_students,
                period_start=period_start,
                period_end=period_end,
            )

            return await self._dao.create_effectiveness_metrics(metrics)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to calculate effectiveness metrics: {e}")

    # ========================================================================
    # COURSE PERFORMANCE
    # ========================================================================

    async def get_course_performance(
        self, instructor_id: UUID, course_id: UUID
    ) -> Optional[InstructorCoursePerformance]:
        """
        What: Get performance for specific course.
        Where: Course analytics view.
        Why: Detailed course metrics.
        """
        try:
            return await self._dao.get_course_performance(instructor_id, course_id)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get course performance: {e}")

    async def get_all_course_performances(
        self, instructor_id: UUID, limit: int = 50
    ) -> list[InstructorCoursePerformance]:
        """
        What: Get all course performances.
        Where: Course list view.
        Why: Overview of all taught courses.
        """
        try:
            return await self._dao.get_all_course_performances(instructor_id, limit)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get course performances: {e}")

    async def create_course_performance(
        self, instructor_id: UUID, course_id: UUID, period_start: date,
        period_end: date, **metrics
    ) -> InstructorCoursePerformance:
        """
        What: Create course performance record.
        Where: Analytics calculation jobs.
        Why: Stores course-level metrics.
        """
        try:
            performance = InstructorCoursePerformance(
                instructor_id=instructor_id,
                course_id=course_id,
                period_start=period_start,
                period_end=period_end,
                **metrics
            )
            return await self._dao.create_course_performance(performance)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to create course performance: {e}")

    # ========================================================================
    # REVIEWS
    # ========================================================================

    async def submit_review(
        self, instructor_id: UUID, student_id: UUID,
        overall_rating: int, course_id: Optional[UUID] = None,
        **review_data
    ) -> InstructorReview:
        """
        What: Submit instructor review.
        Where: Student feedback submission.
        Why: Captures student feedback.
        """
        try:
            review = InstructorReview(
                instructor_id=instructor_id,
                student_id=student_id,
                course_id=course_id,
                overall_rating=overall_rating,
                **review_data
            )
            return await self._dao.create_review(review)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to submit review: {e}")

    async def get_instructor_reviews(
        self, instructor_id: UUID, approved_only: bool = True, limit: int = 50
    ) -> list[InstructorReview]:
        """
        What: Get reviews for instructor.
        Where: Review display.
        Why: Lists student feedback.
        """
        try:
            return await self._dao.get_instructor_reviews(
                instructor_id, approved_only, limit
            )
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get reviews: {e}")

    async def approve_review(
        self, review_id: UUID, moderated_by: UUID
    ) -> InstructorReview:
        """
        What: Approve a review.
        Where: Moderation workflow.
        Why: Makes review visible.
        """
        try:
            return await self._dao.approve_review(review_id, moderated_by)
        except ReviewNotFoundError:
            raise InstructorInsightsServiceError(f"Review {review_id} not found")
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to approve review: {e}")

    async def flag_review(
        self, review_id: UUID, reason: str, moderated_by: UUID
    ) -> InstructorReview:
        """
        What: Flag a review.
        Where: Moderation workflow.
        Why: Marks problematic content.
        """
        try:
            return await self._dao.flag_review(review_id, reason, moderated_by)
        except ReviewNotFoundError:
            raise InstructorInsightsServiceError(f"Review {review_id} not found")
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to flag review: {e}")

    async def calculate_review_summary(
        self, instructor_id: UUID
    ) -> dict[str, Any]:
        """
        What: Calculate review statistics.
        Where: Summary display.
        Why: Aggregated review metrics.
        """
        try:
            reviews = await self._dao.get_instructor_reviews(
                instructor_id, approved_only=True, limit=1000
            )

            if not reviews:
                return {
                    "total_reviews": 0,
                    "average_rating": None,
                    "rating_distribution": {},
                }

            total = len(reviews)
            avg_rating = sum(r.overall_rating for r in reviews) / total

            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for review in reviews:
                distribution[review.overall_rating] += 1

            return {
                "total_reviews": total,
                "average_rating": round(avg_rating, 2),
                "rating_distribution": distribution,
            }
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to calculate review summary: {e}")

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================

    async def create_recommendation(
        self, instructor_id: UUID, title: str, description: str,
        category: RecommendationCategory, priority: RecommendationPriority,
        recommendation_type: str, action_items: Optional[list[str]] = None,
        course_id: Optional[UUID] = None, **kwargs
    ) -> InstructorRecommendation:
        """
        What: Create improvement recommendation.
        Where: AI recommendation generation.
        Why: Stores actionable insights.
        """
        try:
            recommendation = InstructorRecommendation(
                instructor_id=instructor_id,
                course_id=course_id,
                recommendation_type=recommendation_type,
                priority=priority,
                category=category,
                title=title,
                description=description,
                action_items=action_items or [],
                **kwargs
            )
            return await self._dao.create_recommendation(recommendation)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to create recommendation: {e}")

    async def get_recommendations(
        self, instructor_id: UUID, status: Optional[RecommendationStatus] = None,
        limit: int = 50
    ) -> list[InstructorRecommendation]:
        """
        What: Get recommendations for instructor.
        Where: Recommendations dashboard.
        Why: Lists improvement suggestions.
        """
        try:
            return await self._dao.get_instructor_recommendations(
                instructor_id, status, limit
            )
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get recommendations: {e}")

    async def acknowledge_recommendation(
        self, recommendation_id: UUID
    ) -> InstructorRecommendation:
        """
        What: Mark recommendation as acknowledged.
        Where: User interaction.
        Why: Tracks engagement.
        """
        try:
            return await self._dao.update_recommendation_status(
                recommendation_id, RecommendationStatus.ACKNOWLEDGED
            )
        except RecommendationNotFoundError:
            raise InstructorInsightsServiceError(f"Recommendation {recommendation_id} not found")
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to acknowledge recommendation: {e}")

    async def complete_recommendation(
        self, recommendation_id: UUID
    ) -> InstructorRecommendation:
        """
        What: Mark recommendation as completed.
        Where: User action.
        Why: Tracks completion.
        """
        try:
            return await self._dao.update_recommendation_status(
                recommendation_id, RecommendationStatus.COMPLETED
            )
        except RecommendationNotFoundError:
            raise InstructorInsightsServiceError(f"Recommendation {recommendation_id} not found")
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to complete recommendation: {e}")

    async def dismiss_recommendation(
        self, recommendation_id: UUID, reason: str
    ) -> InstructorRecommendation:
        """
        What: Dismiss a recommendation.
        Where: User action.
        Why: Allows skipping non-applicable recommendations.
        """
        try:
            return await self._dao.update_recommendation_status(
                recommendation_id, RecommendationStatus.DISMISSED, reason
            )
        except RecommendationNotFoundError:
            raise InstructorInsightsServiceError(f"Recommendation {recommendation_id} not found")
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to dismiss recommendation: {e}")

    async def generate_recommendations(
        self, instructor_id: UUID
    ) -> list[InstructorRecommendation]:
        """
        What: Generate AI recommendations based on metrics.
        Where: Scheduled analysis or on-demand.
        Why: Provides actionable improvement suggestions.
        """
        try:
            recommendations = []

            # Get latest metrics
            metrics = await self._dao.get_latest_effectiveness_metrics(instructor_id)
            if not metrics:
                return recommendations

            # Check engagement score
            if metrics.engagement_score is not None and metrics.engagement_score < Decimal("60"):
                rec = await self.create_recommendation(
                    instructor_id=instructor_id,
                    title="Improve Student Engagement",
                    description="Your engagement score is below average. Consider adding more interactive elements to your courses.",
                    category=RecommendationCategory.ENGAGEMENT,
                    priority=RecommendationPriority.HIGH,
                    recommendation_type="ENGAGEMENT_LOW",
                    action_items=[
                        "Add discussion prompts after key lessons",
                        "Include hands-on exercises",
                        "Use multimedia content for variety",
                    ],
                    expected_impact="Increase engagement by 15-25%",
                    estimated_effort="2-4 hours per course",
                )
                recommendations.append(rec)

            # Check responsiveness
            if metrics.responsiveness_score is not None and metrics.responsiveness_score < Decimal("70"):
                rec = await self.create_recommendation(
                    instructor_id=instructor_id,
                    title="Improve Response Times",
                    description="Students are waiting longer than average for responses. Consider setting up response time goals.",
                    category=RecommendationCategory.RESPONSIVENESS,
                    priority=RecommendationPriority.MEDIUM,
                    recommendation_type="RESPONSIVENESS_LOW",
                    action_items=[
                        "Set daily time for responding to questions",
                        "Use templated responses for common questions",
                        "Enable notification preferences",
                    ],
                    expected_impact="Reduce response time by 40%",
                    estimated_effort="1 hour setup",
                )
                recommendations.append(rec)

            # Check completion rate
            if metrics.course_completion_rate is not None and metrics.course_completion_rate < Decimal("50"):
                rec = await self.create_recommendation(
                    instructor_id=instructor_id,
                    title="Improve Course Completion Rates",
                    description="Many students are not completing your courses. Consider reviewing course structure and pacing.",
                    category=RecommendationCategory.CONTENT_QUALITY,
                    priority=RecommendationPriority.HIGH,
                    recommendation_type="COMPLETION_LOW",
                    action_items=[
                        "Review course length and complexity",
                        "Add progress milestones and celebrations",
                        "Send reminder emails to inactive students",
                        "Consider breaking long courses into shorter modules",
                    ],
                    expected_impact="Increase completion by 20-30%",
                    estimated_effort="4-8 hours",
                )
                recommendations.append(rec)

            return recommendations
        except InstructorInsightsDAOError as e:
            raise RecommendationGenerationError(f"Failed to generate recommendations: {e}")

    # ========================================================================
    # GOALS
    # ========================================================================

    async def create_goal(
        self, instructor_id: UUID, title: str, metric_name: str,
        target_value: Decimal, target_date: date, goal_type: str,
        baseline_value: Optional[Decimal] = None, description: Optional[str] = None,
        organization_id: Optional[UUID] = None
    ) -> InstructorGoal:
        """
        What: Create personal improvement goal.
        Where: Goal setting.
        Why: Enables structured development.
        """
        try:
            if target_date <= date.today():
                raise InvalidGoalConfigError("Target date must be in the future")

            goal = InstructorGoal(
                instructor_id=instructor_id,
                organization_id=organization_id,
                goal_type=goal_type,
                title=title,
                description=description,
                metric_name=metric_name,
                baseline_value=baseline_value,
                target_value=target_value,
                start_date=date.today(),
                target_date=target_date,
            )
            return await self._dao.create_goal(goal)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to create goal: {e}")

    async def get_goals(
        self, instructor_id: UUID, status: Optional[GoalStatus] = None
    ) -> list[InstructorGoal]:
        """
        What: Get goals for instructor.
        Where: Goals dashboard.
        Why: Lists personal development goals.
        """
        try:
            return await self._dao.get_instructor_goals(instructor_id, status)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get goals: {e}")

    async def get_goal(self, goal_id: UUID) -> Optional[InstructorGoal]:
        """
        What: Get goal by ID.
        Where: Goal detail view.
        Why: Retrieves specific goal.
        """
        try:
            return await self._dao.get_goal(goal_id)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get goal: {e}")

    async def update_goal_progress(
        self, goal_id: UUID, current_value: Decimal
    ) -> InstructorGoal:
        """
        What: Update goal progress.
        Where: Progress tracking.
        Why: Updates current metric value.
        """
        try:
            goal = await self._dao.get_goal(goal_id)
            if not goal:
                raise InstructorInsightsServiceError(f"Goal {goal_id} not found")

            # Calculate progress
            progress = goal.calculate_progress()
            if goal.current_value != current_value:
                goal.current_value = current_value
                progress = goal.calculate_progress()

            return await self._dao.update_goal(
                goal_id,
                current_value=current_value,
                progress_percentage=progress
            )
        except GoalNotFoundError:
            raise InstructorInsightsServiceError(f"Goal {goal_id} not found")
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to update goal progress: {e}")

    async def complete_goal(self, goal_id: UUID) -> InstructorGoal:
        """
        What: Mark goal as completed.
        Where: Goal completion.
        Why: Tracks achievement.
        """
        try:
            return await self._dao.update_goal(
                goal_id,
                status=GoalStatus.COMPLETED,
                completed_date=date.today(),
                progress_percentage=Decimal("100")
            )
        except GoalNotFoundError:
            raise InstructorInsightsServiceError(f"Goal {goal_id} not found")
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to complete goal: {e}")

    async def cancel_goal(self, goal_id: UUID) -> InstructorGoal:
        """
        What: Cancel a goal.
        Where: Goal management.
        Why: Allows abandoning goals.
        """
        try:
            return await self._dao.update_goal(goal_id, status=GoalStatus.CANCELLED)
        except GoalNotFoundError:
            raise InstructorInsightsServiceError(f"Goal {goal_id} not found")
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to cancel goal: {e}")

    async def delete_goal(self, goal_id: UUID) -> bool:
        """
        What: Delete a goal.
        Where: Goal management.
        Why: Removes unwanted goals.
        """
        try:
            return await self._dao.delete_goal(goal_id)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to delete goal: {e}")

    # ========================================================================
    # PEER COMPARISONS
    # ========================================================================

    async def get_peer_comparisons(
        self, instructor_id: UUID, category: Optional[MetricCategory] = None
    ) -> list[InstructorPeerComparison]:
        """
        What: Get peer comparison data.
        Where: Benchmarking views.
        Why: Shows relative performance.
        """
        try:
            return await self._dao.get_peer_comparisons(instructor_id, category)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get peer comparisons: {e}")

    async def create_peer_comparison(
        self, instructor_id: UUID, metric_name: str, instructor_score: Decimal,
        peer_average: Decimal, percentile_rank: int, comparison_group: str,
        metric_category: MetricCategory, period_start: date, period_end: date,
        **kwargs
    ) -> InstructorPeerComparison:
        """
        What: Create peer comparison record.
        Where: Analytics calculations.
        Why: Stores benchmark data.
        """
        try:
            comparison = InstructorPeerComparison(
                instructor_id=instructor_id,
                comparison_group=comparison_group,
                instructor_score=instructor_score,
                peer_average=peer_average,
                percentile_rank=percentile_rank,
                metric_name=metric_name,
                metric_category=metric_category,
                period_start=period_start,
                period_end=period_end,
                **kwargs
            )
            return await self._dao.create_peer_comparison(comparison)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to create peer comparison: {e}")

    # ========================================================================
    # TEACHING LOAD
    # ========================================================================

    async def get_teaching_load(
        self, instructor_id: UUID
    ) -> Optional[InstructorTeachingLoad]:
        """
        What: Get current teaching load.
        Where: Workload dashboard.
        Why: Shows capacity status.
        """
        try:
            return await self._dao.get_latest_teaching_load(instructor_id)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get teaching load: {e}")

    async def create_teaching_load(
        self, instructor_id: UUID, period_start: date, period_end: date,
        organization_id: Optional[UUID] = None, **metrics
    ) -> InstructorTeachingLoad:
        """
        What: Create teaching load record.
        Where: Workload calculations.
        Why: Tracks instructor capacity.
        """
        try:
            load = InstructorTeachingLoad(
                instructor_id=instructor_id,
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
                **metrics
            )

            # Calculate capacity status
            load.capacity_status = load.calculate_capacity_status()

            return await self._dao.create_teaching_load(load)
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to create teaching load: {e}")

    # ========================================================================
    # DASHBOARD SUMMARY
    # ========================================================================

    async def get_dashboard_summary(
        self, instructor_id: UUID
    ) -> dict[str, Any]:
        """
        What: Get complete dashboard summary.
        Where: Main instructor dashboard.
        Why: Single call for all key metrics.
        """
        try:
            # Get all relevant data
            metrics = await self._dao.get_latest_effectiveness_metrics(instructor_id)
            courses = await self._dao.get_all_course_performances(instructor_id, limit=5)
            recommendations = await self._dao.get_instructor_recommendations(
                instructor_id, RecommendationStatus.PENDING, limit=5
            )
            goals = await self._dao.get_instructor_goals(
                instructor_id, GoalStatus.ACTIVE
            )
            load = await self._dao.get_latest_teaching_load(instructor_id)

            # Build summary
            summary = {
                "effectiveness": {
                    "overall_rating": float(metrics.overall_rating) if metrics and metrics.overall_rating else None,
                    "teaching_quality": float(metrics.teaching_quality_score) if metrics and metrics.teaching_quality_score else None,
                    "engagement": float(metrics.engagement_score) if metrics and metrics.engagement_score else None,
                    "responsiveness": float(metrics.responsiveness_score) if metrics and metrics.responsiveness_score else None,
                    "students_taught": metrics.total_students_taught if metrics else 0,
                    "completion_rate": float(metrics.course_completion_rate) if metrics and metrics.course_completion_rate else None,
                },
                "recent_courses": [
                    {
                        "course_id": str(c.course_id),
                        "enrolled": c.total_enrolled,
                        "pass_rate": float(c.pass_rate) if c.pass_rate else None,
                        "rating": float(c.content_rating) if c.content_rating else None,
                    }
                    for c in courses
                ],
                "pending_recommendations": len(recommendations),
                "active_goals": len(goals),
                "capacity_status": load.capacity_status.value if load else "unknown",
            }

            return summary
        except InstructorInsightsDAOError as e:
            raise InstructorInsightsServiceError(f"Failed to get dashboard summary: {e}")
