"""
Unit Tests for Instructor Insights Domain Entities

What: Comprehensive unit tests for instructor insights entities including
      effectiveness metrics, course performance, reviews, recommendations,
      goals, and peer comparisons.

Where: Tests the analytics/domain/entities/instructor_insights.py module.

Why: Ensures entity validation, business logic, and data integrity.
"""

import sys
from pathlib import Path
# Add analytics service path BEFORE any analytics imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'analytics'))

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

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
# ENUM TESTS
# ============================================================================

class TestTrend:
    """Tests for Trend enum."""

    def test_all_trends_exist(self):
        """Test all trend values exist."""
        assert Trend.IMPROVING.value == "improving"
        assert Trend.STABLE.value == "stable"
        assert Trend.DECLINING.value == "declining"

    def test_trend_count(self):
        """Test correct number of trends."""
        assert len(Trend) == 3


class TestCapacityStatus:
    """Tests for CapacityStatus enum."""

    def test_all_statuses_exist(self):
        """Test all capacity status values exist."""
        assert CapacityStatus.AVAILABLE.value == "available"
        assert CapacityStatus.MODERATE.value == "moderate"
        assert CapacityStatus.HIGH.value == "high"
        assert CapacityStatus.OVERLOADED.value == "overloaded"

    def test_status_count(self):
        """Test correct number of statuses."""
        assert len(CapacityStatus) == 4


class TestRecommendationPriority:
    """Tests for RecommendationPriority enum."""

    def test_all_priorities_exist(self):
        """Test all priority values exist."""
        assert RecommendationPriority.LOW.value == "low"
        assert RecommendationPriority.MEDIUM.value == "medium"
        assert RecommendationPriority.HIGH.value == "high"
        assert RecommendationPriority.CRITICAL.value == "critical"

    def test_priority_count(self):
        """Test correct number of priorities."""
        assert len(RecommendationPriority) == 4


class TestRecommendationStatus:
    """Tests for RecommendationStatus enum."""

    def test_all_statuses_exist(self):
        """Test all recommendation status values exist."""
        assert RecommendationStatus.PENDING.value == "pending"
        assert RecommendationStatus.ACKNOWLEDGED.value == "acknowledged"
        assert RecommendationStatus.IN_PROGRESS.value == "in_progress"
        assert RecommendationStatus.COMPLETED.value == "completed"
        assert RecommendationStatus.DISMISSED.value == "dismissed"

    def test_status_count(self):
        """Test correct number of statuses."""
        assert len(RecommendationStatus) == 5


class TestGoalStatus:
    """Tests for GoalStatus enum."""

    def test_all_statuses_exist(self):
        """Test all goal status values exist."""
        assert GoalStatus.DRAFT.value == "draft"
        assert GoalStatus.ACTIVE.value == "active"
        assert GoalStatus.COMPLETED.value == "completed"
        assert GoalStatus.FAILED.value == "failed"
        assert GoalStatus.CANCELLED.value == "cancelled"

    def test_status_count(self):
        """Test correct number of statuses."""
        assert len(GoalStatus) == 5


class TestFeedbackSentiment:
    """Tests for FeedbackSentiment enum."""

    def test_all_sentiments_exist(self):
        """Test all sentiment values exist."""
        assert FeedbackSentiment.POSITIVE.value == "positive"
        assert FeedbackSentiment.NEUTRAL.value == "neutral"
        assert FeedbackSentiment.NEGATIVE.value == "negative"
        assert FeedbackSentiment.MIXED.value == "mixed"

    def test_sentiment_count(self):
        """Test correct number of sentiments."""
        assert len(FeedbackSentiment) == 4


class TestRecommendationCategory:
    """Tests for RecommendationCategory enum."""

    def test_all_categories_exist(self):
        """Test all category values exist."""
        assert RecommendationCategory.ENGAGEMENT.value == "engagement"
        assert RecommendationCategory.CONTENT_QUALITY.value == "content_quality"
        assert RecommendationCategory.RESPONSIVENESS.value == "responsiveness"
        assert RecommendationCategory.ASSESSMENT.value == "assessment"
        assert RecommendationCategory.COMMUNICATION.value == "communication"
        assert RecommendationCategory.ORGANIZATION.value == "organization"
        assert RecommendationCategory.ACCESSIBILITY.value == "accessibility"
        assert RecommendationCategory.TECHNICAL.value == "technical"

    def test_category_count(self):
        """Test correct number of categories."""
        assert len(RecommendationCategory) == 8


class TestMetricCategory:
    """Tests for MetricCategory enum."""

    def test_all_categories_exist(self):
        """Test all metric category values exist."""
        assert MetricCategory.TEACHING_QUALITY.value == "teaching_quality"
        assert MetricCategory.STUDENT_OUTCOMES.value == "student_outcomes"
        assert MetricCategory.ENGAGEMENT.value == "engagement"
        assert MetricCategory.RESPONSIVENESS.value == "responsiveness"
        assert MetricCategory.CONTENT.value == "content"
        assert MetricCategory.SATISFACTION.value == "satisfaction"

    def test_category_count(self):
        """Test correct number of categories."""
        assert len(MetricCategory) == 6


# ============================================================================
# EFFECTIVENESS METRICS TESTS
# ============================================================================

class TestInstructorEffectivenessMetrics:
    """Tests for InstructorEffectivenessMetrics entity."""

    def test_create_valid_metrics(self):
        """Test creating metrics with valid data."""
        metrics = InstructorEffectivenessMetrics(
            instructor_id=uuid4(),
            overall_rating=Decimal("4.5"),
            teaching_quality_score=Decimal("85.0"),
            engagement_score=Decimal("78.0"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31)
        )
        assert metrics.overall_rating == Decimal("4.5")
        assert metrics.teaching_quality_score == Decimal("85.0")

    def test_rating_validation_too_high(self):
        """Test that rating above 5 is rejected."""
        with pytest.raises(ValueError, match="Overall rating must be between 0 and 5"):
            InstructorEffectivenessMetrics(
                instructor_id=uuid4(),
                overall_rating=Decimal("5.5"),
                period_start=date.today(),
                period_end=date.today()
            )

    def test_rating_validation_negative(self):
        """Test that negative rating is rejected."""
        with pytest.raises(ValueError, match="Overall rating must be between 0 and 5"):
            InstructorEffectivenessMetrics(
                instructor_id=uuid4(),
                overall_rating=Decimal("-1"),
                period_start=date.today(),
                period_end=date.today()
            )

    def test_score_validation_too_high(self):
        """Test that score above 100 is rejected."""
        with pytest.raises(ValueError, match="teaching_quality_score must be between 0 and 100"):
            InstructorEffectivenessMetrics(
                instructor_id=uuid4(),
                teaching_quality_score=Decimal("105"),
                period_start=date.today(),
                period_end=date.today()
            )

    def test_period_validation(self):
        """Test that end before start is rejected."""
        with pytest.raises(ValueError, match="Period end must not be before period start"):
            InstructorEffectivenessMetrics(
                instructor_id=uuid4(),
                period_start=date(2024, 3, 31),
                period_end=date(2024, 1, 1)
            )

    def test_calculate_composite_score(self):
        """Test composite score calculation."""
        metrics = InstructorEffectivenessMetrics(
            instructor_id=uuid4(),
            teaching_quality_score=Decimal("80"),
            content_clarity_score=Decimal("80"),
            engagement_score=Decimal("80"),
            responsiveness_score=Decimal("80"),
            period_start=date.today(),
            period_end=date.today()
        )
        score = metrics.calculate_composite_score()
        assert score == Decimal("80")

    def test_calculate_composite_score_partial(self):
        """Test composite score with partial data."""
        metrics = InstructorEffectivenessMetrics(
            instructor_id=uuid4(),
            teaching_quality_score=Decimal("90"),
            content_clarity_score=Decimal("70"),
            period_start=date.today(),
            period_end=date.today()
        )
        score = metrics.calculate_composite_score()
        # (90 * 0.30 + 70 * 0.25) / (0.30 + 0.25) = (27 + 17.5) / 0.55 = 80.91
        assert score is not None
        assert Decimal("80") < score < Decimal("82")

    def test_calculate_composite_score_no_data(self):
        """Test composite score with no data."""
        metrics = InstructorEffectivenessMetrics(
            instructor_id=uuid4(),
            period_start=date.today(),
            period_end=date.today()
        )
        score = metrics.calculate_composite_score()
        assert score is None


# ============================================================================
# COURSE PERFORMANCE TESTS
# ============================================================================

class TestInstructorCoursePerformance:
    """Tests for InstructorCoursePerformance entity."""

    def test_create_valid_performance(self):
        """Test creating performance with valid data."""
        perf = InstructorCoursePerformance(
            instructor_id=uuid4(),
            course_id=uuid4(),
            total_enrolled=100,
            completed_students=80,
            pass_rate=Decimal("85.0"),
            period_start=date.today(),
            period_end=date.today()
        )
        assert perf.total_enrolled == 100
        assert perf.pass_rate == Decimal("85.0")

    def test_pass_rate_validation(self):
        """Test pass rate validation."""
        with pytest.raises(ValueError, match="Pass rate must be between 0 and 100"):
            InstructorCoursePerformance(
                instructor_id=uuid4(),
                course_id=uuid4(),
                pass_rate=Decimal("110"),
                period_start=date.today(),
                period_end=date.today()
            )

    def test_rating_validation(self):
        """Test rating validation."""
        with pytest.raises(ValueError, match="content_rating must be between 0 and 5"):
            InstructorCoursePerformance(
                instructor_id=uuid4(),
                course_id=uuid4(),
                content_rating=Decimal("6"),
                period_start=date.today(),
                period_end=date.today()
            )

    def test_get_completion_rate(self):
        """Test completion rate calculation."""
        perf = InstructorCoursePerformance(
            instructor_id=uuid4(),
            course_id=uuid4(),
            total_enrolled=100,
            completed_students=75,
            period_start=date.today(),
            period_end=date.today()
        )
        rate = perf.get_completion_rate()
        assert rate == Decimal("75")

    def test_get_completion_rate_no_students(self):
        """Test completion rate with no students."""
        perf = InstructorCoursePerformance(
            instructor_id=uuid4(),
            course_id=uuid4(),
            total_enrolled=0,
            period_start=date.today(),
            period_end=date.today()
        )
        rate = perf.get_completion_rate()
        assert rate is None

    def test_get_dropout_rate(self):
        """Test dropout rate calculation."""
        perf = InstructorCoursePerformance(
            instructor_id=uuid4(),
            course_id=uuid4(),
            total_enrolled=100,
            dropped_students=15,
            period_start=date.today(),
            period_end=date.today()
        )
        rate = perf.get_dropout_rate()
        assert rate == Decimal("15")


# ============================================================================
# STUDENT ENGAGEMENT TESTS
# ============================================================================

class TestInstructorStudentEngagement:
    """Tests for InstructorStudentEngagement entity."""

    def test_create_valid_engagement(self):
        """Test creating engagement with valid data."""
        eng = InstructorStudentEngagement(
            instructor_id=uuid4(),
            total_sessions=500,
            total_content_views=2000,
            peak_hour=14,
            period_start=date.today(),
            period_end=date.today()
        )
        assert eng.total_sessions == 500
        assert eng.peak_hour == 14

    def test_peak_hour_validation_too_high(self):
        """Test peak hour validation."""
        with pytest.raises(ValueError, match="Peak hour must be between 0 and 23"):
            InstructorStudentEngagement(
                instructor_id=uuid4(),
                peak_hour=25,
                period_start=date.today(),
                period_end=date.today()
            )

    def test_peak_hour_validation_negative(self):
        """Test peak hour negative validation."""
        with pytest.raises(ValueError, match="Peak hour must be between 0 and 23"):
            InstructorStudentEngagement(
                instructor_id=uuid4(),
                peak_hour=-1,
                period_start=date.today(),
                period_end=date.today()
            )

    def test_get_response_rate(self):
        """Test response rate calculation."""
        eng = InstructorStudentEngagement(
            instructor_id=uuid4(),
            total_questions_asked=100,
            questions_answered=85,
            period_start=date.today(),
            period_end=date.today()
        )
        rate = eng.get_response_rate()
        assert rate == Decimal("85")

    def test_get_response_rate_no_questions(self):
        """Test response rate with no questions."""
        eng = InstructorStudentEngagement(
            instructor_id=uuid4(),
            total_questions_asked=0,
            period_start=date.today(),
            period_end=date.today()
        )
        rate = eng.get_response_rate()
        assert rate is None


# ============================================================================
# CONTENT RATING TESTS
# ============================================================================

class TestContentRating:
    """Tests for ContentRating entity."""

    def test_create_valid_rating(self):
        """Test creating rating with valid data."""
        rating = ContentRating(
            instructor_id=uuid4(),
            course_id=uuid4(),
            content_id=uuid4(),
            content_type="lesson",
            student_id=uuid4(),
            clarity_rating=5,
            helpfulness_rating=4
        )
        assert rating.clarity_rating == 5
        assert rating.helpfulness_rating == 4

    def test_rating_too_high(self):
        """Test rating above 5 is rejected."""
        with pytest.raises(ValueError, match="clarity_rating must be between 1 and 5"):
            ContentRating(
                instructor_id=uuid4(),
                course_id=uuid4(),
                content_id=uuid4(),
                content_type="lesson",
                student_id=uuid4(),
                clarity_rating=6
            )

    def test_rating_too_low(self):
        """Test rating below 1 is rejected."""
        with pytest.raises(ValueError, match="helpfulness_rating must be between 1 and 5"):
            ContentRating(
                instructor_id=uuid4(),
                course_id=uuid4(),
                content_id=uuid4(),
                content_type="lesson",
                student_id=uuid4(),
                helpfulness_rating=0
            )

    def test_get_average_rating(self):
        """Test average rating calculation."""
        rating = ContentRating(
            instructor_id=uuid4(),
            course_id=uuid4(),
            content_id=uuid4(),
            content_type="lesson",
            student_id=uuid4(),
            clarity_rating=5,
            helpfulness_rating=4,
            relevance_rating=3
        )
        avg = rating.get_average_rating()
        assert avg == Decimal("4")

    def test_get_average_rating_partial(self):
        """Test average rating with partial data."""
        rating = ContentRating(
            instructor_id=uuid4(),
            course_id=uuid4(),
            content_id=uuid4(),
            content_type="lesson",
            student_id=uuid4(),
            clarity_rating=4
        )
        avg = rating.get_average_rating()
        assert avg == Decimal("4")


# ============================================================================
# INSTRUCTOR REVIEW TESTS
# ============================================================================

class TestInstructorReview:
    """Tests for InstructorReview entity."""

    def test_create_valid_review(self):
        """Test creating review with valid data."""
        review = InstructorReview(
            instructor_id=uuid4(),
            student_id=uuid4(),
            overall_rating=5,
            review_title="Great instructor!",
            review_text="Very helpful and responsive."
        )
        assert review.overall_rating == 5
        assert review.review_title == "Great instructor!"

    def test_overall_rating_validation_too_high(self):
        """Test overall rating above 5 is rejected."""
        with pytest.raises(ValueError, match="Overall rating must be between 1 and 5"):
            InstructorReview(
                instructor_id=uuid4(),
                student_id=uuid4(),
                overall_rating=6
            )

    def test_overall_rating_validation_too_low(self):
        """Test overall rating below 1 is rejected."""
        with pytest.raises(ValueError, match="Overall rating must be between 1 and 5"):
            InstructorReview(
                instructor_id=uuid4(),
                student_id=uuid4(),
                overall_rating=0
            )

    def test_optional_rating_validation(self):
        """Test optional rating validation."""
        with pytest.raises(ValueError, match="knowledge_rating must be between 1 and 5"):
            InstructorReview(
                instructor_id=uuid4(),
                student_id=uuid4(),
                overall_rating=4,
                knowledge_rating=6
            )

    def test_get_helpfulness_score(self):
        """Test helpfulness score calculation."""
        review = InstructorReview(
            instructor_id=uuid4(),
            student_id=uuid4(),
            overall_rating=5,
            helpful_count=80,
            not_helpful_count=20
        )
        score = review.get_helpfulness_score()
        assert score == Decimal("80")

    def test_get_helpfulness_score_no_votes(self):
        """Test helpfulness score with no votes."""
        review = InstructorReview(
            instructor_id=uuid4(),
            student_id=uuid4(),
            overall_rating=5
        )
        score = review.get_helpfulness_score()
        assert score is None


# ============================================================================
# TEACHING LOAD TESTS
# ============================================================================

class TestInstructorTeachingLoad:
    """Tests for InstructorTeachingLoad entity."""

    def test_create_valid_load(self):
        """Test creating teaching load with valid data."""
        load = InstructorTeachingLoad(
            instructor_id=uuid4(),
            active_courses=5,
            current_students=150,
            teaching_hours_per_week=Decimal("20"),
            period_start=date.today(),
            period_end=date.today()
        )
        assert load.active_courses == 5
        assert load.current_students == 150

    def test_get_total_weekly_hours(self):
        """Test total weekly hours calculation."""
        load = InstructorTeachingLoad(
            instructor_id=uuid4(),
            teaching_hours_per_week=Decimal("20"),
            grading_hours_per_week=Decimal("10"),
            support_hours_per_week=Decimal("5"),
            content_creation_hours_per_week=Decimal("5"),
            period_start=date.today(),
            period_end=date.today()
        )
        total = load.get_total_weekly_hours()
        assert total == Decimal("40")

    def test_get_total_weekly_hours_partial(self):
        """Test total weekly hours with partial data."""
        load = InstructorTeachingLoad(
            instructor_id=uuid4(),
            teaching_hours_per_week=Decimal("20"),
            period_start=date.today(),
            period_end=date.today()
        )
        total = load.get_total_weekly_hours()
        assert total == Decimal("20")

    def test_calculate_capacity_status_overloaded(self):
        """Test capacity status when overloaded."""
        load = InstructorTeachingLoad(
            instructor_id=uuid4(),
            current_students=120,
            total_students_capacity=100,
            period_start=date.today(),
            period_end=date.today()
        )
        status = load.calculate_capacity_status()
        assert status == CapacityStatus.OVERLOADED

    def test_calculate_capacity_status_high(self):
        """Test capacity status when high."""
        load = InstructorTeachingLoad(
            instructor_id=uuid4(),
            current_students=90,
            total_students_capacity=100,
            period_start=date.today(),
            period_end=date.today()
        )
        status = load.calculate_capacity_status()
        assert status == CapacityStatus.HIGH

    def test_calculate_capacity_status_moderate(self):
        """Test capacity status when moderate."""
        load = InstructorTeachingLoad(
            instructor_id=uuid4(),
            current_students=70,
            total_students_capacity=100,
            period_start=date.today(),
            period_end=date.today()
        )
        status = load.calculate_capacity_status()
        assert status == CapacityStatus.MODERATE

    def test_calculate_capacity_status_available(self):
        """Test capacity status when available."""
        load = InstructorTeachingLoad(
            instructor_id=uuid4(),
            current_students=50,
            total_students_capacity=100,
            period_start=date.today(),
            period_end=date.today()
        )
        status = load.calculate_capacity_status()
        assert status == CapacityStatus.AVAILABLE


# ============================================================================
# RESPONSE METRICS TESTS
# ============================================================================

class TestInstructorResponseMetrics:
    """Tests for InstructorResponseMetrics entity."""

    def test_create_valid_metrics(self):
        """Test creating response metrics with valid data."""
        metrics = InstructorResponseMetrics(
            instructor_id=uuid4(),
            grading_sla_compliance=Decimal("95.0"),
            question_sla_compliance=Decimal("88.0"),
            period_start=date.today(),
            period_end=date.today()
        )
        assert metrics.grading_sla_compliance == Decimal("95.0")

    def test_compliance_validation_too_high(self):
        """Test compliance above 100 is rejected."""
        with pytest.raises(ValueError, match="grading_sla_compliance must be between 0 and 100"):
            InstructorResponseMetrics(
                instructor_id=uuid4(),
                grading_sla_compliance=Decimal("105"),
                period_start=date.today(),
                period_end=date.today()
            )

    def test_compliance_validation_negative(self):
        """Test negative compliance is rejected."""
        with pytest.raises(ValueError, match="question_sla_compliance must be between 0 and 100"):
            InstructorResponseMetrics(
                instructor_id=uuid4(),
                question_sla_compliance=Decimal("-5"),
                period_start=date.today(),
                period_end=date.today()
            )

    def test_get_overall_responsiveness_score(self):
        """Test overall responsiveness score calculation."""
        metrics = InstructorResponseMetrics(
            instructor_id=uuid4(),
            grading_sla_compliance=Decimal("90"),
            question_sla_compliance=Decimal("80"),
            period_start=date.today(),
            period_end=date.today()
        )
        score = metrics.get_overall_responsiveness_score()
        assert score == Decimal("85")

    def test_get_overall_responsiveness_score_partial(self):
        """Test overall responsiveness score with partial data."""
        metrics = InstructorResponseMetrics(
            instructor_id=uuid4(),
            grading_sla_compliance=Decimal("90"),
            period_start=date.today(),
            period_end=date.today()
        )
        score = metrics.get_overall_responsiveness_score()
        assert score == Decimal("90")


# ============================================================================
# RECOMMENDATION TESTS
# ============================================================================

class TestInstructorRecommendation:
    """Tests for InstructorRecommendation entity."""

    def test_create_valid_recommendation(self):
        """Test creating recommendation with valid data."""
        rec = InstructorRecommendation(
            instructor_id=uuid4(),
            recommendation_type="ENGAGEMENT_LOW",
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.ENGAGEMENT,
            title="Improve Engagement",
            description="Add more interactive elements."
        )
        assert rec.title == "Improve Engagement"
        assert rec.priority == RecommendationPriority.HIGH

    def test_title_required(self):
        """Test title is required."""
        with pytest.raises(ValueError, match="Recommendation title is required"):
            InstructorRecommendation(
                instructor_id=uuid4(),
                recommendation_type="TEST",
                title="",
                description="Test description"
            )

    def test_description_required(self):
        """Test description is required."""
        with pytest.raises(ValueError, match="Recommendation description is required"):
            InstructorRecommendation(
                instructor_id=uuid4(),
                recommendation_type="TEST",
                title="Test Title",
                description=""
            )

    def test_is_expired(self):
        """Test expiration check."""
        rec = InstructorRecommendation(
            instructor_id=uuid4(),
            recommendation_type="TEST",
            title="Test",
            description="Test",
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        assert rec.is_expired() is True

    def test_is_not_expired(self):
        """Test not expired."""
        rec = InstructorRecommendation(
            instructor_id=uuid4(),
            recommendation_type="TEST",
            title="Test",
            description="Test",
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        assert rec.is_expired() is False

    def test_is_expired_no_expiry(self):
        """Test no expiry set."""
        rec = InstructorRecommendation(
            instructor_id=uuid4(),
            recommendation_type="TEST",
            title="Test",
            description="Test"
        )
        assert rec.is_expired() is False

    def test_acknowledge(self):
        """Test acknowledging recommendation."""
        rec = InstructorRecommendation(
            instructor_id=uuid4(),
            recommendation_type="TEST",
            title="Test",
            description="Test"
        )
        rec.acknowledge()
        assert rec.status == RecommendationStatus.ACKNOWLEDGED
        assert rec.acknowledged_at is not None

    def test_complete(self):
        """Test completing recommendation."""
        rec = InstructorRecommendation(
            instructor_id=uuid4(),
            recommendation_type="TEST",
            title="Test",
            description="Test"
        )
        rec.complete({"improvement": 15})
        assert rec.status == RecommendationStatus.COMPLETED
        assert rec.completed_at is not None
        assert rec.outcome_measured is True
        assert rec.outcome_data == {"improvement": 15}

    def test_dismiss(self):
        """Test dismissing recommendation."""
        rec = InstructorRecommendation(
            instructor_id=uuid4(),
            recommendation_type="TEST",
            title="Test",
            description="Test"
        )
        rec.dismiss("Not applicable")
        assert rec.status == RecommendationStatus.DISMISSED
        assert rec.dismissed_reason == "Not applicable"


# ============================================================================
# PEER COMPARISON TESTS
# ============================================================================

class TestInstructorPeerComparison:
    """Tests for InstructorPeerComparison entity."""

    def test_create_valid_comparison(self):
        """Test creating comparison with valid data."""
        comp = InstructorPeerComparison(
            instructor_id=uuid4(),
            comparison_group="department",
            instructor_score=Decimal("85"),
            peer_average=Decimal("78"),
            percentile_rank=75,
            metric_name="engagement_score",
            metric_category=MetricCategory.ENGAGEMENT,
            period_start=date.today(),
            period_end=date.today()
        )
        assert comp.percentile_rank == 75
        assert comp.instructor_score == Decimal("85")

    def test_percentile_validation_too_high(self):
        """Test percentile above 100 is rejected."""
        with pytest.raises(ValueError, match="Percentile rank must be between 0 and 100"):
            InstructorPeerComparison(
                instructor_id=uuid4(),
                comparison_group="department",
                metric_name="test",
                percentile_rank=105,
                period_start=date.today(),
                period_end=date.today()
            )

    def test_percentile_validation_negative(self):
        """Test negative percentile is rejected."""
        with pytest.raises(ValueError, match="Percentile rank must be between 0 and 100"):
            InstructorPeerComparison(
                instructor_id=uuid4(),
                comparison_group="department",
                metric_name="test",
                percentile_rank=-5,
                period_start=date.today(),
                period_end=date.today()
            )

    def test_get_position_description_top_10(self):
        """Test position description for top 10%."""
        comp = InstructorPeerComparison(
            instructor_id=uuid4(),
            comparison_group="department",
            metric_name="test",
            percentile_rank=95,
            period_start=date.today(),
            period_end=date.today()
        )
        assert comp.get_position_description() == "Top 10%"

    def test_get_position_description_top_25(self):
        """Test position description for top 25%."""
        comp = InstructorPeerComparison(
            instructor_id=uuid4(),
            comparison_group="department",
            metric_name="test",
            percentile_rank=80,
            period_start=date.today(),
            period_end=date.today()
        )
        assert comp.get_position_description() == "Top 25%"

    def test_get_position_description_above_average(self):
        """Test position description for above average."""
        comp = InstructorPeerComparison(
            instructor_id=uuid4(),
            comparison_group="department",
            metric_name="test",
            percentile_rank=60,
            period_start=date.today(),
            period_end=date.today()
        )
        assert comp.get_position_description() == "Above Average"

    def test_get_position_description_below_average(self):
        """Test position description for below average."""
        comp = InstructorPeerComparison(
            instructor_id=uuid4(),
            comparison_group="department",
            metric_name="test",
            percentile_rank=30,
            period_start=date.today(),
            period_end=date.today()
        )
        assert comp.get_position_description() == "Below Average"

    def test_get_position_description_bottom_25(self):
        """Test position description for bottom 25%."""
        comp = InstructorPeerComparison(
            instructor_id=uuid4(),
            comparison_group="department",
            metric_name="test",
            percentile_rank=20,
            period_start=date.today(),
            period_end=date.today()
        )
        assert comp.get_position_description() == "Bottom 25%"


# ============================================================================
# GOAL TESTS
# ============================================================================

class TestInstructorGoal:
    """Tests for InstructorGoal entity."""

    def test_create_valid_goal(self):
        """Test creating goal with valid data."""
        goal = InstructorGoal(
            instructor_id=uuid4(),
            goal_type="improvement",
            title="Improve Engagement Score",
            metric_name="engagement_score",
            baseline_value=Decimal("60"),
            target_value=Decimal("80"),
            start_date=date.today(),
            target_date=date.today() + timedelta(days=90)
        )
        assert goal.title == "Improve Engagement Score"
        assert goal.target_value == Decimal("80")

    def test_title_required(self):
        """Test title is required."""
        with pytest.raises(ValueError, match="Goal title is required"):
            InstructorGoal(
                instructor_id=uuid4(),
                goal_type="improvement",
                title="",
                metric_name="test",
                target_value=Decimal("80"),
                start_date=date.today(),
                target_date=date.today() + timedelta(days=30)
            )

    def test_target_date_validation(self):
        """Test target date before start date is rejected."""
        with pytest.raises(ValueError, match="Target date must not be before start date"):
            InstructorGoal(
                instructor_id=uuid4(),
                goal_type="improvement",
                title="Test Goal",
                metric_name="test",
                target_value=Decimal("80"),
                start_date=date.today(),
                target_date=date.today() - timedelta(days=1)
            )

    def test_progress_validation_too_high(self):
        """Test progress above 100 is rejected."""
        with pytest.raises(ValueError, match="Progress percentage must be between 0 and 100"):
            InstructorGoal(
                instructor_id=uuid4(),
                goal_type="improvement",
                title="Test Goal",
                metric_name="test",
                target_value=Decimal("80"),
                progress_percentage=Decimal("105"),
                start_date=date.today(),
                target_date=date.today() + timedelta(days=30)
            )

    def test_calculate_progress(self):
        """Test progress calculation."""
        goal = InstructorGoal(
            instructor_id=uuid4(),
            goal_type="improvement",
            title="Test Goal",
            metric_name="engagement_score",
            baseline_value=Decimal("60"),
            target_value=Decimal("80"),
            current_value=Decimal("70"),
            start_date=date.today(),
            target_date=date.today() + timedelta(days=90)
        )
        progress = goal.calculate_progress()
        assert progress == Decimal("50")  # 10 out of 20 = 50%

    def test_calculate_progress_complete(self):
        """Test progress calculation when complete."""
        goal = InstructorGoal(
            instructor_id=uuid4(),
            goal_type="improvement",
            title="Test Goal",
            metric_name="engagement_score",
            baseline_value=Decimal("60"),
            target_value=Decimal("80"),
            current_value=Decimal("85"),
            start_date=date.today(),
            target_date=date.today() + timedelta(days=90)
        )
        progress = goal.calculate_progress()
        assert progress == Decimal("100")

    def test_days_remaining(self):
        """Test days remaining calculation."""
        goal = InstructorGoal(
            instructor_id=uuid4(),
            goal_type="improvement",
            title="Test Goal",
            metric_name="test",
            target_value=Decimal("80"),
            start_date=date.today(),
            target_date=date.today() + timedelta(days=30)
        )
        remaining = goal.days_remaining()
        assert remaining == 30

    def test_days_remaining_past_due(self):
        """Test days remaining when past due."""
        goal = InstructorGoal(
            instructor_id=uuid4(),
            goal_type="improvement",
            title="Test Goal",
            metric_name="test",
            target_value=Decimal("80"),
            start_date=date.today() - timedelta(days=40),
            target_date=date.today() - timedelta(days=10)
        )
        remaining = goal.days_remaining()
        assert remaining == 0

    def test_is_overdue(self):
        """Test overdue check."""
        goal = InstructorGoal(
            instructor_id=uuid4(),
            goal_type="improvement",
            title="Test Goal",
            metric_name="test",
            target_value=Decimal("80"),
            start_date=date.today() - timedelta(days=40),
            target_date=date.today() - timedelta(days=10),
            status=GoalStatus.ACTIVE
        )
        assert goal.is_overdue() is True

    def test_is_not_overdue(self):
        """Test not overdue."""
        goal = InstructorGoal(
            instructor_id=uuid4(),
            goal_type="improvement",
            title="Test Goal",
            metric_name="test",
            target_value=Decimal("80"),
            start_date=date.today(),
            target_date=date.today() + timedelta(days=30),
            status=GoalStatus.ACTIVE
        )
        assert goal.is_overdue() is False

    def test_complete(self):
        """Test completing goal."""
        goal = InstructorGoal(
            instructor_id=uuid4(),
            goal_type="improvement",
            title="Test Goal",
            metric_name="test",
            target_value=Decimal("80"),
            start_date=date.today(),
            target_date=date.today() + timedelta(days=30)
        )
        goal.complete()
        assert goal.status == GoalStatus.COMPLETED
        assert goal.completed_date == date.today()
        assert goal.progress_percentage == Decimal("100")

    def test_add_milestone(self):
        """Test adding milestone."""
        goal = InstructorGoal(
            instructor_id=uuid4(),
            goal_type="improvement",
            title="Test Goal",
            metric_name="test",
            target_value=Decimal("80"),
            start_date=date.today(),
            target_date=date.today() + timedelta(days=30)
        )
        goal.add_milestone("First milestone", Decimal("70"), achieved=True)
        assert len(goal.milestones) == 1
        assert goal.milestones[0]["title"] == "First milestone"
        assert goal.milestones[0]["achieved"] is True
