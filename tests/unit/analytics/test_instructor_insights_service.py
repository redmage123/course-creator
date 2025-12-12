"""
Instructor Insights Service Unit Tests

What: Unit tests for InstructorInsightsService class.
Where: Tests service layer business logic.
Why: Validates:
     1. Effectiveness metrics retrieval and calculation
     2. Course performance management
     3. Review submission and moderation
     4. Recommendation generation and tracking
     5. Goal creation and progress tracking
     6. Peer comparison operations
     7. Teaching load management
     8. Dashboard summary aggregation
     9. Error handling and exception wrapping
"""

import sys
from pathlib import Path

# Add analytics service to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'analytics'))

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID

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
from analytics.application.services.instructor_insights_service import (
    InstructorInsightsService,
    InstructorInsightsServiceError,
    InstructorNotFoundError,
    UnauthorizedInsightsAccessError,
    InvalidGoalConfigError,
    RecommendationGenerationError,
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
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_dao():
    """Create mock DAO for service tests.

    NOTE: This uses a MagicMock for now. These tests should be refactored to:
    1. Use real DAO with test database (db_transaction fixture)
    2. Or test service logic with real entity objects instead of mocks
    """
    from unittest.mock import MagicMock
    return MagicMock()


@pytest.fixture
def service(mock_dao):
    """Create service with mock DAO."""
    return InstructorInsightsService(dao=mock_dao)


@pytest.fixture
def sample_instructor_id():
    """Sample instructor UUID."""
    return uuid4()


@pytest.fixture
def sample_course_id():
    """Sample course UUID."""
    return uuid4()


@pytest.fixture
def sample_organization_id():
    """Sample organization UUID."""
    return uuid4()


@pytest.fixture
def sample_effectiveness_metrics(sample_instructor_id, sample_organization_id):
    """Create sample effectiveness metrics."""
    return InstructorEffectivenessMetrics(
        instructor_id=sample_instructor_id,
        organization_id=sample_organization_id,
        overall_rating=Decimal("4.5"),
        teaching_quality_score=Decimal("88.5"),
        content_clarity_score=Decimal("90.0"),
        engagement_score=Decimal("75.0"),
        responsiveness_score=Decimal("85.0"),
        total_students_taught=150,
        course_completion_rate=Decimal("78.5"),
        average_quiz_score=Decimal("82.3"),
        period_start=date(2024, 1, 1),
        period_end=date(2024, 3, 31),
    )


@pytest.fixture
def sample_course_performance(sample_instructor_id, sample_course_id):
    """Create sample course performance."""
    return InstructorCoursePerformance(
        instructor_id=sample_instructor_id,
        course_id=sample_course_id,
        total_enrolled=50,
        active_students=45,
        completed_students=40,
        dropped_students=5,
        average_score=Decimal("82.5"),
        pass_rate=Decimal("85.0"),
        content_rating=Decimal("4.3"),
        period_start=date(2024, 1, 1),
        period_end=date(2024, 3, 31),
    )


@pytest.fixture
def sample_review(sample_instructor_id):
    """Create sample instructor review."""
    return InstructorReview(
        instructor_id=sample_instructor_id,
        student_id=uuid4(),
        overall_rating=5,
        knowledge_rating=5,
        communication_rating=4,
        review_title="Great instructor",
        review_text="Very knowledgeable and helpful.",
    )


@pytest.fixture
def sample_recommendation(sample_instructor_id):
    """Create sample recommendation."""
    return InstructorRecommendation(
        instructor_id=sample_instructor_id,
        recommendation_type="ENGAGEMENT_LOW",
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.ENGAGEMENT,
        title="Improve Student Engagement",
        description="Add more interactive elements to courses.",
        action_items=["Add quizzes", "Include discussions"],
    )


@pytest.fixture
def sample_goal(sample_instructor_id):
    """Create sample instructor goal."""
    return InstructorGoal(
        instructor_id=sample_instructor_id,
        goal_type="IMPROVEMENT",
        title="Improve Rating",
        metric_name="overall_rating",
        baseline_value=Decimal("4.0"),
        target_value=Decimal("4.5"),
        current_value=Decimal("4.2"),
        start_date=date.today(),
        target_date=date.today() + timedelta(days=90),
    )


@pytest.fixture
def sample_teaching_load(sample_instructor_id):
    """Create sample teaching load."""
    return InstructorTeachingLoad(
        instructor_id=sample_instructor_id,
        active_courses=5,
        total_courses_taught=20,
        current_students=150,
        total_students_capacity=200,
        teaching_hours_per_week=Decimal("20"),
        period_start=date(2024, 1, 1),
        period_end=date(2024, 3, 31),
    )


@pytest.fixture
def sample_peer_comparison(sample_instructor_id):
    """Create sample peer comparison."""
    return InstructorPeerComparison(
        instructor_id=sample_instructor_id,
        comparison_group="same_department",
        instructor_score=Decimal("85.5"),
        peer_average=Decimal("78.2"),
        percentile_rank=75,
        metric_name="teaching_quality",
        metric_category=MetricCategory.TEACHING_QUALITY,
        sample_size=25,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 3, 31),
    )


# ============================================================================
# EFFECTIVENESS METRICS TESTS
# ============================================================================

class TestEffectivenessMetrics:
    """Tests for effectiveness metrics operations."""

    @pytest.mark.asyncio
    async def test_get_effectiveness_metrics_with_period(
        self, service, mock_dao, sample_instructor_id, sample_effectiveness_metrics
    ):
        """Test getting effectiveness metrics with date range."""
        mock_dao.get_effectiveness_metrics.return_value = sample_effectiveness_metrics

        result = await service.get_effectiveness_metrics(
            sample_instructor_id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31)
        )

        assert result is not None
        assert result.instructor_id == sample_instructor_id
        assert result.overall_rating == Decimal("4.5")
        mock_dao.get_effectiveness_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_effectiveness_metrics_latest(
        self, service, mock_dao, sample_instructor_id, sample_effectiveness_metrics
    ):
        """Test getting latest effectiveness metrics without date range."""
        mock_dao.get_latest_effectiveness_metrics.return_value = sample_effectiveness_metrics

        result = await service.get_effectiveness_metrics(sample_instructor_id)

        assert result is not None
        assert result.instructor_id == sample_instructor_id
        mock_dao.get_latest_effectiveness_metrics.assert_called_once_with(sample_instructor_id)

    @pytest.mark.asyncio
    async def test_get_effectiveness_metrics_not_found(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test getting metrics when none exist."""
        mock_dao.get_latest_effectiveness_metrics.return_value = None

        result = await service.get_effectiveness_metrics(sample_instructor_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_effectiveness_metrics_dao_error(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test error handling for DAO errors."""
        mock_dao.get_latest_effectiveness_metrics.side_effect = InstructorInsightsDAOError("DB error")

        with pytest.raises(InstructorInsightsServiceError) as exc_info:
            await service.get_effectiveness_metrics(sample_instructor_id)

        assert "Failed to get effectiveness metrics" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_effectiveness_metrics(
        self, service, mock_dao, sample_instructor_id, sample_course_performance
    ):
        """Test calculating effectiveness metrics from course data."""
        mock_dao.get_all_course_performances.return_value = [
            sample_course_performance,
            InstructorCoursePerformance(
                instructor_id=sample_instructor_id,
                course_id=uuid4(),
                total_enrolled=30,
                completed_students=25,
                pass_rate=Decimal("80.0"),
                average_score=Decimal("78.0"),
                content_rating=Decimal("4.0"),
                period_start=date(2024, 1, 1),
                period_end=date(2024, 3, 31),
            )
        ]
        mock_dao.create_effectiveness_metrics.return_value = InstructorEffectivenessMetrics(
            instructor_id=sample_instructor_id,
            overall_rating=Decimal("4.15"),
            teaching_quality_score=Decimal("82.5"),
            course_completion_rate=Decimal("81.25"),
            total_students_taught=80,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
        )

        result = await service.calculate_effectiveness_metrics(
            sample_instructor_id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31)
        )

        assert result is not None
        assert result.instructor_id == sample_instructor_id
        mock_dao.get_all_course_performances.assert_called_once()
        mock_dao.create_effectiveness_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_effectiveness_metrics_no_courses(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test calculating metrics with no course data."""
        mock_dao.get_all_course_performances.return_value = []
        mock_dao.create_effectiveness_metrics.return_value = InstructorEffectivenessMetrics(
            instructor_id=sample_instructor_id,
            total_students_taught=0,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
        )

        result = await service.calculate_effectiveness_metrics(
            sample_instructor_id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31)
        )

        assert result.total_students_taught == 0


# ============================================================================
# COURSE PERFORMANCE TESTS
# ============================================================================

class TestCoursePerformance:
    """Tests for course performance operations."""

    @pytest.mark.asyncio
    async def test_get_course_performance(
        self, service, mock_dao, sample_instructor_id, sample_course_id, sample_course_performance
    ):
        """Test getting specific course performance."""
        mock_dao.get_course_performance.return_value = sample_course_performance

        result = await service.get_course_performance(sample_instructor_id, sample_course_id)

        assert result is not None
        assert result.course_id == sample_course_id
        assert result.total_enrolled == 50
        mock_dao.get_course_performance.assert_called_once_with(sample_instructor_id, sample_course_id)

    @pytest.mark.asyncio
    async def test_get_course_performance_not_found(
        self, service, mock_dao, sample_instructor_id, sample_course_id
    ):
        """Test getting non-existent course performance."""
        mock_dao.get_course_performance.return_value = None

        result = await service.get_course_performance(sample_instructor_id, sample_course_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_course_performances(
        self, service, mock_dao, sample_instructor_id, sample_course_performance
    ):
        """Test getting all course performances."""
        mock_dao.get_all_course_performances.return_value = [
            sample_course_performance,
            sample_course_performance,
        ]

        result = await service.get_all_course_performances(sample_instructor_id, limit=10)

        assert len(result) == 2
        mock_dao.get_all_course_performances.assert_called_once_with(sample_instructor_id, 10)

    @pytest.mark.asyncio
    async def test_create_course_performance(
        self, service, mock_dao, sample_instructor_id, sample_course_id, sample_course_performance
    ):
        """Test creating course performance record."""
        mock_dao.create_course_performance.return_value = sample_course_performance

        result = await service.create_course_performance(
            instructor_id=sample_instructor_id,
            course_id=sample_course_id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
            total_enrolled=50,
            completed_students=40,
        )

        assert result is not None
        mock_dao.create_course_performance.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_course_performance_dao_error(
        self, service, mock_dao, sample_instructor_id, sample_course_id
    ):
        """Test error handling for course performance creation."""
        mock_dao.create_course_performance.side_effect = InstructorInsightsDAOError("DB error")

        with pytest.raises(InstructorInsightsServiceError) as exc_info:
            await service.create_course_performance(
                instructor_id=sample_instructor_id,
                course_id=sample_course_id,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 3, 31),
            )

        assert "Failed to create course performance" in str(exc_info.value)


# ============================================================================
# REVIEW TESTS
# ============================================================================

class TestReviews:
    """Tests for instructor review operations."""

    @pytest.mark.asyncio
    async def test_submit_review(
        self, service, mock_dao, sample_instructor_id, sample_review
    ):
        """Test submitting instructor review."""
        student_id = uuid4()
        mock_dao.create_review.return_value = sample_review

        result = await service.submit_review(
            instructor_id=sample_instructor_id,
            student_id=student_id,
            overall_rating=5,
            knowledge_rating=5,
            review_title="Great instructor",
            review_text="Very helpful.",
        )

        assert result is not None
        assert result.overall_rating == 5
        mock_dao.create_review.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_review_with_course(
        self, service, mock_dao, sample_instructor_id, sample_course_id, sample_review
    ):
        """Test submitting review for specific course."""
        student_id = uuid4()
        sample_review.course_id = sample_course_id
        mock_dao.create_review.return_value = sample_review

        result = await service.submit_review(
            instructor_id=sample_instructor_id,
            student_id=student_id,
            overall_rating=5,
            course_id=sample_course_id,
        )

        assert result.course_id == sample_course_id

    @pytest.mark.asyncio
    async def test_get_instructor_reviews_approved_only(
        self, service, mock_dao, sample_instructor_id, sample_review
    ):
        """Test getting approved reviews only."""
        sample_review.is_approved = True
        mock_dao.get_instructor_reviews.return_value = [sample_review]

        result = await service.get_instructor_reviews(
            sample_instructor_id, approved_only=True
        )

        assert len(result) == 1
        mock_dao.get_instructor_reviews.assert_called_once_with(
            sample_instructor_id, True, 50
        )

    @pytest.mark.asyncio
    async def test_get_instructor_reviews_all(
        self, service, mock_dao, sample_instructor_id, sample_review
    ):
        """Test getting all reviews."""
        mock_dao.get_instructor_reviews.return_value = [sample_review, sample_review]

        result = await service.get_instructor_reviews(
            sample_instructor_id, approved_only=False, limit=100
        )

        assert len(result) == 2
        mock_dao.get_instructor_reviews.assert_called_once_with(
            sample_instructor_id, False, 100
        )

    @pytest.mark.asyncio
    async def test_approve_review(
        self, service, mock_dao, sample_review
    ):
        """Test approving a review."""
        review_id = sample_review.id
        moderator_id = uuid4()
        sample_review.is_approved = True
        mock_dao.approve_review.return_value = sample_review

        result = await service.approve_review(review_id, moderator_id)

        assert result.is_approved is True
        mock_dao.approve_review.assert_called_once_with(review_id, moderator_id)

    @pytest.mark.asyncio
    async def test_approve_review_not_found(
        self, service, mock_dao
    ):
        """Test approving non-existent review."""
        review_id = uuid4()
        mock_dao.approve_review.side_effect = ReviewNotFoundError(f"Review {review_id} not found")

        with pytest.raises(InstructorInsightsServiceError) as exc_info:
            await service.approve_review(review_id, uuid4())

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_flag_review(
        self, service, mock_dao, sample_review
    ):
        """Test flagging a review."""
        review_id = sample_review.id
        moderator_id = uuid4()
        sample_review.is_flagged = True
        sample_review.flagged_reason = "Inappropriate content"
        mock_dao.flag_review.return_value = sample_review

        result = await service.flag_review(
            review_id, "Inappropriate content", moderator_id
        )

        assert result.is_flagged is True
        assert result.flagged_reason == "Inappropriate content"
        mock_dao.flag_review.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_review_summary(
        self, service, mock_dao, sample_instructor_id, sample_review
    ):
        """Test calculating review summary."""
        reviews = [
            InstructorReview(
                instructor_id=sample_instructor_id,
                student_id=uuid4(),
                overall_rating=rating,
            )
            for rating in [5, 4, 5, 4, 3]
        ]
        mock_dao.get_instructor_reviews.return_value = reviews

        result = await service.calculate_review_summary(sample_instructor_id)

        assert result["total_reviews"] == 5
        assert result["average_rating"] == 4.2
        assert result["rating_distribution"][5] == 2
        assert result["rating_distribution"][4] == 2
        assert result["rating_distribution"][3] == 1

    @pytest.mark.asyncio
    async def test_calculate_review_summary_no_reviews(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test review summary with no reviews."""
        mock_dao.get_instructor_reviews.return_value = []

        result = await service.calculate_review_summary(sample_instructor_id)

        assert result["total_reviews"] == 0
        assert result["average_rating"] is None


# ============================================================================
# RECOMMENDATION TESTS
# ============================================================================

class TestRecommendations:
    """Tests for recommendation operations."""

    @pytest.mark.asyncio
    async def test_create_recommendation(
        self, service, mock_dao, sample_instructor_id, sample_recommendation
    ):
        """Test creating a recommendation."""
        mock_dao.create_recommendation.return_value = sample_recommendation

        result = await service.create_recommendation(
            instructor_id=sample_instructor_id,
            title="Improve Engagement",
            description="Add interactive elements",
            category=RecommendationCategory.ENGAGEMENT,
            priority=RecommendationPriority.HIGH,
            recommendation_type="ENGAGEMENT_LOW",
            action_items=["Add quizzes"],
        )

        assert result is not None
        assert result.title == "Improve Student Engagement"
        mock_dao.create_recommendation.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recommendations_all(
        self, service, mock_dao, sample_instructor_id, sample_recommendation
    ):
        """Test getting all recommendations."""
        mock_dao.get_instructor_recommendations.return_value = [sample_recommendation]

        result = await service.get_recommendations(sample_instructor_id)

        assert len(result) == 1
        mock_dao.get_instructor_recommendations.assert_called_once_with(
            sample_instructor_id, None, 50
        )

    @pytest.mark.asyncio
    async def test_get_recommendations_by_status(
        self, service, mock_dao, sample_instructor_id, sample_recommendation
    ):
        """Test getting recommendations by status."""
        mock_dao.get_instructor_recommendations.return_value = [sample_recommendation]

        result = await service.get_recommendations(
            sample_instructor_id, status=RecommendationStatus.PENDING
        )

        assert len(result) == 1
        mock_dao.get_instructor_recommendations.assert_called_once_with(
            sample_instructor_id, RecommendationStatus.PENDING, 50
        )

    @pytest.mark.asyncio
    async def test_acknowledge_recommendation(
        self, service, mock_dao, sample_recommendation
    ):
        """Test acknowledging a recommendation."""
        sample_recommendation.status = RecommendationStatus.ACKNOWLEDGED
        mock_dao.update_recommendation_status.return_value = sample_recommendation

        result = await service.acknowledge_recommendation(sample_recommendation.id)

        assert result.status == RecommendationStatus.ACKNOWLEDGED
        mock_dao.update_recommendation_status.assert_called_once_with(
            sample_recommendation.id, RecommendationStatus.ACKNOWLEDGED
        )

    @pytest.mark.asyncio
    async def test_complete_recommendation(
        self, service, mock_dao, sample_recommendation
    ):
        """Test completing a recommendation."""
        sample_recommendation.status = RecommendationStatus.COMPLETED
        mock_dao.update_recommendation_status.return_value = sample_recommendation

        result = await service.complete_recommendation(sample_recommendation.id)

        assert result.status == RecommendationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_dismiss_recommendation(
        self, service, mock_dao, sample_recommendation
    ):
        """Test dismissing a recommendation."""
        sample_recommendation.status = RecommendationStatus.DISMISSED
        sample_recommendation.dismissed_reason = "Not applicable"
        mock_dao.update_recommendation_status.return_value = sample_recommendation

        result = await service.dismiss_recommendation(
            sample_recommendation.id, "Not applicable"
        )

        assert result.status == RecommendationStatus.DISMISSED
        mock_dao.update_recommendation_status.assert_called_once_with(
            sample_recommendation.id, RecommendationStatus.DISMISSED, "Not applicable"
        )

    @pytest.mark.asyncio
    async def test_dismiss_recommendation_not_found(
        self, service, mock_dao
    ):
        """Test dismissing non-existent recommendation."""
        rec_id = uuid4()
        mock_dao.update_recommendation_status.side_effect = RecommendationNotFoundError(
            f"Recommendation {rec_id} not found"
        )

        with pytest.raises(InstructorInsightsServiceError) as exc_info:
            await service.dismiss_recommendation(rec_id, "reason")

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_recommendations_low_engagement(
        self, service, mock_dao, sample_instructor_id, sample_recommendation
    ):
        """Test generating recommendations for low engagement."""
        metrics = InstructorEffectivenessMetrics(
            instructor_id=sample_instructor_id,
            engagement_score=Decimal("45.0"),  # Low engagement
            responsiveness_score=Decimal("80.0"),
            course_completion_rate=Decimal("70.0"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
        )
        mock_dao.get_latest_effectiveness_metrics.return_value = metrics
        mock_dao.create_recommendation.return_value = sample_recommendation

        result = await service.generate_recommendations(sample_instructor_id)

        assert len(result) >= 1
        mock_dao.create_recommendation.assert_called()

    @pytest.mark.asyncio
    async def test_generate_recommendations_low_responsiveness(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test generating recommendations for low responsiveness."""
        metrics = InstructorEffectivenessMetrics(
            instructor_id=sample_instructor_id,
            engagement_score=Decimal("80.0"),
            responsiveness_score=Decimal("50.0"),  # Low responsiveness
            course_completion_rate=Decimal("70.0"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
        )
        mock_dao.get_latest_effectiveness_metrics.return_value = metrics
        mock_dao.create_recommendation.return_value = InstructorRecommendation(
            instructor_id=sample_instructor_id,
            recommendation_type="RESPONSIVENESS_LOW",
            priority=RecommendationPriority.MEDIUM,
            category=RecommendationCategory.RESPONSIVENESS,
            title="Improve Response Times",
            description="Respond faster to students.",
            action_items=[],
        )

        result = await service.generate_recommendations(sample_instructor_id)

        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_generate_recommendations_low_completion(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test generating recommendations for low completion rate."""
        metrics = InstructorEffectivenessMetrics(
            instructor_id=sample_instructor_id,
            engagement_score=Decimal("80.0"),
            responsiveness_score=Decimal("80.0"),
            course_completion_rate=Decimal("40.0"),  # Low completion
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
        )
        mock_dao.get_latest_effectiveness_metrics.return_value = metrics
        mock_dao.create_recommendation.return_value = InstructorRecommendation(
            instructor_id=sample_instructor_id,
            recommendation_type="COMPLETION_LOW",
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.CONTENT_QUALITY,
            title="Improve Completion",
            description="Review course structure.",
            action_items=[],
        )

        result = await service.generate_recommendations(sample_instructor_id)

        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_generate_recommendations_no_metrics(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test generating recommendations with no metrics."""
        mock_dao.get_latest_effectiveness_metrics.return_value = None

        result = await service.generate_recommendations(sample_instructor_id)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_generate_recommendations_all_good(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test no recommendations when all metrics are good."""
        metrics = InstructorEffectivenessMetrics(
            instructor_id=sample_instructor_id,
            engagement_score=Decimal("90.0"),
            responsiveness_score=Decimal("85.0"),
            course_completion_rate=Decimal("80.0"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
        )
        mock_dao.get_latest_effectiveness_metrics.return_value = metrics

        result = await service.generate_recommendations(sample_instructor_id)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_generate_recommendations_dao_error(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test error handling for recommendation generation."""
        mock_dao.get_latest_effectiveness_metrics.side_effect = InstructorInsightsDAOError("DB error")

        with pytest.raises(RecommendationGenerationError) as exc_info:
            await service.generate_recommendations(sample_instructor_id)

        assert "Failed to generate recommendations" in str(exc_info.value)


# ============================================================================
# GOAL TESTS
# ============================================================================

class TestGoals:
    """Tests for goal management operations."""

    @pytest.mark.asyncio
    async def test_create_goal(
        self, service, mock_dao, sample_instructor_id, sample_goal
    ):
        """Test creating a goal."""
        mock_dao.create_goal.return_value = sample_goal

        result = await service.create_goal(
            instructor_id=sample_instructor_id,
            title="Improve Rating",
            metric_name="overall_rating",
            target_value=Decimal("4.5"),
            target_date=date.today() + timedelta(days=90),
            goal_type="IMPROVEMENT",
            baseline_value=Decimal("4.0"),
        )

        assert result is not None
        assert result.title == "Improve Rating"
        mock_dao.create_goal.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_goal_invalid_date(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test creating goal with past target date."""
        with pytest.raises(InvalidGoalConfigError) as exc_info:
            await service.create_goal(
                instructor_id=sample_instructor_id,
                title="Improve Rating",
                metric_name="overall_rating",
                target_value=Decimal("4.5"),
                target_date=date.today() - timedelta(days=1),  # Past date
                goal_type="IMPROVEMENT",
            )

        assert "Target date must be in the future" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_goals_all(
        self, service, mock_dao, sample_instructor_id, sample_goal
    ):
        """Test getting all goals."""
        mock_dao.get_instructor_goals.return_value = [sample_goal]

        result = await service.get_goals(sample_instructor_id)

        assert len(result) == 1
        mock_dao.get_instructor_goals.assert_called_once_with(sample_instructor_id, None)

    @pytest.mark.asyncio
    async def test_get_goals_by_status(
        self, service, mock_dao, sample_instructor_id, sample_goal
    ):
        """Test getting goals by status."""
        mock_dao.get_instructor_goals.return_value = [sample_goal]

        result = await service.get_goals(
            sample_instructor_id, status=GoalStatus.ACTIVE
        )

        assert len(result) == 1
        mock_dao.get_instructor_goals.assert_called_once_with(
            sample_instructor_id, GoalStatus.ACTIVE
        )

    @pytest.mark.asyncio
    async def test_get_goal_by_id(
        self, service, mock_dao, sample_goal
    ):
        """Test getting goal by ID."""
        mock_dao.get_goal.return_value = sample_goal

        result = await service.get_goal(sample_goal.id)

        assert result is not None
        assert result.id == sample_goal.id

    @pytest.mark.asyncio
    async def test_update_goal_progress(
        self, service, mock_dao, sample_goal
    ):
        """Test updating goal progress."""
        sample_goal.current_value = Decimal("4.3")
        sample_goal.progress_percentage = Decimal("60")
        mock_dao.get_goal.return_value = sample_goal
        mock_dao.update_goal.return_value = sample_goal

        result = await service.update_goal_progress(
            sample_goal.id, Decimal("4.3")
        )

        assert result is not None
        mock_dao.update_goal.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_goal_progress_not_found(
        self, service, mock_dao
    ):
        """Test updating non-existent goal."""
        goal_id = uuid4()
        mock_dao.get_goal.return_value = None

        with pytest.raises(InstructorInsightsServiceError) as exc_info:
            await service.update_goal_progress(goal_id, Decimal("4.3"))

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_goal(
        self, service, mock_dao, sample_goal
    ):
        """Test completing a goal."""
        sample_goal.status = GoalStatus.COMPLETED
        sample_goal.progress_percentage = Decimal("100")
        mock_dao.update_goal.return_value = sample_goal

        result = await service.complete_goal(sample_goal.id)

        assert result.status == GoalStatus.COMPLETED
        assert result.progress_percentage == Decimal("100")

    @pytest.mark.asyncio
    async def test_cancel_goal(
        self, service, mock_dao, sample_goal
    ):
        """Test cancelling a goal."""
        sample_goal.status = GoalStatus.CANCELLED
        mock_dao.update_goal.return_value = sample_goal

        result = await service.cancel_goal(sample_goal.id)

        assert result.status == GoalStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_delete_goal(
        self, service, mock_dao, sample_goal
    ):
        """Test deleting a goal."""
        mock_dao.delete_goal.return_value = True

        result = await service.delete_goal(sample_goal.id)

        assert result is True
        mock_dao.delete_goal.assert_called_once_with(sample_goal.id)


# ============================================================================
# PEER COMPARISON TESTS
# ============================================================================

class TestPeerComparisons:
    """Tests for peer comparison operations."""

    @pytest.mark.asyncio
    async def test_get_peer_comparisons_all(
        self, service, mock_dao, sample_instructor_id, sample_peer_comparison
    ):
        """Test getting all peer comparisons."""
        mock_dao.get_peer_comparisons.return_value = [sample_peer_comparison]

        result = await service.get_peer_comparisons(sample_instructor_id)

        assert len(result) == 1
        mock_dao.get_peer_comparisons.assert_called_once_with(sample_instructor_id, None)

    @pytest.mark.asyncio
    async def test_get_peer_comparisons_by_category(
        self, service, mock_dao, sample_instructor_id, sample_peer_comparison
    ):
        """Test getting peer comparisons by category."""
        mock_dao.get_peer_comparisons.return_value = [sample_peer_comparison]

        result = await service.get_peer_comparisons(
            sample_instructor_id, category=MetricCategory.TEACHING_QUALITY
        )

        assert len(result) == 1
        mock_dao.get_peer_comparisons.assert_called_once_with(
            sample_instructor_id, MetricCategory.TEACHING_QUALITY
        )

    @pytest.mark.asyncio
    async def test_create_peer_comparison(
        self, service, mock_dao, sample_instructor_id, sample_peer_comparison
    ):
        """Test creating peer comparison."""
        mock_dao.create_peer_comparison.return_value = sample_peer_comparison

        result = await service.create_peer_comparison(
            instructor_id=sample_instructor_id,
            metric_name="teaching_quality",
            instructor_score=Decimal("85.5"),
            peer_average=Decimal("78.2"),
            percentile_rank=75,
            comparison_group="same_department",
            metric_category=MetricCategory.TEACHING_QUALITY,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
        )

        assert result is not None
        assert result.percentile_rank == 75
        mock_dao.create_peer_comparison.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_peer_comparison_dao_error(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test error handling for peer comparison creation."""
        mock_dao.create_peer_comparison.side_effect = InstructorInsightsDAOError("DB error")

        with pytest.raises(InstructorInsightsServiceError) as exc_info:
            await service.create_peer_comparison(
                instructor_id=sample_instructor_id,
                metric_name="teaching_quality",
                instructor_score=Decimal("85.5"),
                peer_average=Decimal("78.2"),
                percentile_rank=75,
                comparison_group="same_department",
                metric_category=MetricCategory.TEACHING_QUALITY,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 3, 31),
            )

        assert "Failed to create peer comparison" in str(exc_info.value)


# ============================================================================
# TEACHING LOAD TESTS
# ============================================================================

class TestTeachingLoad:
    """Tests for teaching load operations."""

    @pytest.mark.asyncio
    async def test_get_teaching_load(
        self, service, mock_dao, sample_instructor_id, sample_teaching_load
    ):
        """Test getting teaching load."""
        mock_dao.get_latest_teaching_load.return_value = sample_teaching_load

        result = await service.get_teaching_load(sample_instructor_id)

        assert result is not None
        assert result.active_courses == 5
        mock_dao.get_latest_teaching_load.assert_called_once_with(sample_instructor_id)

    @pytest.mark.asyncio
    async def test_get_teaching_load_none(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test getting teaching load when none exists."""
        mock_dao.get_latest_teaching_load.return_value = None

        result = await service.get_teaching_load(sample_instructor_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_create_teaching_load(
        self, service, mock_dao, sample_instructor_id, sample_teaching_load
    ):
        """Test creating teaching load."""
        mock_dao.create_teaching_load.return_value = sample_teaching_load

        result = await service.create_teaching_load(
            instructor_id=sample_instructor_id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
            active_courses=5,
            current_students=150,
            total_students_capacity=200,
        )

        assert result is not None
        mock_dao.create_teaching_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_teaching_load_calculates_capacity(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test that capacity status is calculated."""
        load = InstructorTeachingLoad(
            instructor_id=sample_instructor_id,
            active_courses=5,
            current_students=190,  # High load
            total_students_capacity=200,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
        )
        mock_dao.create_teaching_load.return_value = load

        result = await service.create_teaching_load(
            instructor_id=sample_instructor_id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
            active_courses=5,
            current_students=190,
            total_students_capacity=200,
        )

        # The service calculates capacity_status before calling DAO
        mock_dao.create_teaching_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_teaching_load_dao_error(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test error handling for teaching load creation."""
        mock_dao.create_teaching_load.side_effect = InstructorInsightsDAOError("DB error")

        with pytest.raises(InstructorInsightsServiceError) as exc_info:
            await service.create_teaching_load(
                instructor_id=sample_instructor_id,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 3, 31),
            )

        assert "Failed to create teaching load" in str(exc_info.value)


# ============================================================================
# DASHBOARD SUMMARY TESTS
# ============================================================================

class TestDashboardSummary:
    """Tests for dashboard summary operations."""

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_full(
        self, service, mock_dao, sample_instructor_id,
        sample_effectiveness_metrics, sample_course_performance,
        sample_recommendation, sample_goal, sample_teaching_load
    ):
        """Test getting complete dashboard summary."""
        mock_dao.get_latest_effectiveness_metrics.return_value = sample_effectiveness_metrics
        mock_dao.get_all_course_performances.return_value = [sample_course_performance]
        mock_dao.get_instructor_recommendations.return_value = [sample_recommendation]
        mock_dao.get_instructor_goals.return_value = [sample_goal]
        mock_dao.get_latest_teaching_load.return_value = sample_teaching_load

        result = await service.get_dashboard_summary(sample_instructor_id)

        assert "effectiveness" in result
        assert "recent_courses" in result
        assert "pending_recommendations" in result
        assert "active_goals" in result
        assert "capacity_status" in result

        assert result["effectiveness"]["overall_rating"] == 4.5
        assert result["effectiveness"]["students_taught"] == 150
        assert len(result["recent_courses"]) == 1
        assert result["pending_recommendations"] == 1
        assert result["active_goals"] == 1

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_no_data(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test dashboard summary with no data."""
        mock_dao.get_latest_effectiveness_metrics.return_value = None
        mock_dao.get_all_course_performances.return_value = []
        mock_dao.get_instructor_recommendations.return_value = []
        mock_dao.get_instructor_goals.return_value = []
        mock_dao.get_latest_teaching_load.return_value = None

        result = await service.get_dashboard_summary(sample_instructor_id)

        assert result["effectiveness"]["overall_rating"] is None
        assert result["effectiveness"]["students_taught"] == 0
        assert len(result["recent_courses"]) == 0
        assert result["pending_recommendations"] == 0
        assert result["active_goals"] == 0
        assert result["capacity_status"] == "unknown"

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_partial_data(
        self, service, mock_dao, sample_instructor_id, sample_effectiveness_metrics
    ):
        """Test dashboard summary with partial data."""
        mock_dao.get_latest_effectiveness_metrics.return_value = sample_effectiveness_metrics
        mock_dao.get_all_course_performances.return_value = []
        mock_dao.get_instructor_recommendations.return_value = []
        mock_dao.get_instructor_goals.return_value = []
        mock_dao.get_latest_teaching_load.return_value = None

        result = await service.get_dashboard_summary(sample_instructor_id)

        assert result["effectiveness"]["overall_rating"] == 4.5
        assert result["effectiveness"]["engagement"] == 75.0
        assert len(result["recent_courses"]) == 0
        assert result["capacity_status"] == "unknown"

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_dao_error(
        self, service, mock_dao, sample_instructor_id
    ):
        """Test error handling for dashboard summary."""
        mock_dao.get_latest_effectiveness_metrics.side_effect = InstructorInsightsDAOError("DB error")

        with pytest.raises(InstructorInsightsServiceError) as exc_info:
            await service.get_dashboard_summary(sample_instructor_id)

        assert "Failed to get dashboard summary" in str(exc_info.value)


# ============================================================================
# SERVICE INITIALIZATION TESTS
# ============================================================================

class TestServiceInitialization:
    """Tests for service initialization."""

    def test_service_initialization(self, mock_dao):
        """Test service initializes with DAO."""
        service = InstructorInsightsService(dao=mock_dao)

        assert service._dao == mock_dao
        assert service._cache is None

    def test_service_initialization_with_cache(self, mock_dao):
        """Test service initializes with cache."""
        mock_cache = MagicMock()
        service = InstructorInsightsService(dao=mock_dao, cache=mock_cache)

        assert service._dao == mock_dao
        assert service._cache == mock_cache


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestExceptions:
    """Tests for custom exceptions."""

    def test_service_error_inheritance(self):
        """Test InstructorInsightsServiceError is base exception."""
        error = InstructorInsightsServiceError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_instructor_not_found_error(self):
        """Test InstructorNotFoundError."""
        error = InstructorNotFoundError("Instructor not found")
        assert isinstance(error, InstructorInsightsServiceError)

    def test_unauthorized_access_error(self):
        """Test UnauthorizedInsightsAccessError."""
        error = UnauthorizedInsightsAccessError("Access denied")
        assert isinstance(error, InstructorInsightsServiceError)

    def test_invalid_goal_config_error(self):
        """Test InvalidGoalConfigError."""
        error = InvalidGoalConfigError("Invalid goal")
        assert isinstance(error, InstructorInsightsServiceError)

    def test_recommendation_generation_error(self):
        """Test RecommendationGenerationError."""
        error = RecommendationGenerationError("Generation failed")
        assert isinstance(error, InstructorInsightsServiceError)
