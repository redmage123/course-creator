"""
WHAT: Unit tests for SM-2 Spaced Repetition Algorithm implementation
WHERE: Tests course_management.domain.entities.learning_path.StudentMasteryLevel
WHY: Validates correct implementation of SuperMemo 2 algorithm for optimal
     review scheduling and long-term memory retention

SM-2 Algorithm Reference: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2

Test Coverage:
- score_to_quality() conversion (0-100 to 0-5 quality ratings)
- SM-2 ease factor calculations and bounds
- Repetition count management (reset on failure, increment on success)
- Interval scheduling (1, 6, then ease_factor multiplied)
- Next review date calculations
- Edge cases and boundary conditions
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

# Ensure correct service path is at the front of sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'))

from course_management.domain.entities.learning_path import (
    StudentMasteryLevel, MasteryLevel
)


class TestScoreToQuality:
    """
    WHAT: Tests for score_to_quality() conversion method
    WHERE: Tests StudentMasteryLevel.score_to_quality()
    WHY: Validates correct mapping of assessment scores (0-100)
         to SM-2 quality ratings (0-5)
    """

    @pytest.fixture
    def mastery(self):
        """Basic StudentMasteryLevel for testing"""
        return StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Python Loops"
        )

    def test_perfect_score_returns_quality_5(self, mastery):
        """Score >= 95% maps to quality 5 (perfect response)"""
        assert mastery.score_to_quality(Decimal("100")) == 5
        assert mastery.score_to_quality(Decimal("95")) == 5
        assert mastery.score_to_quality(Decimal("99.5")) == 5

    def test_good_score_returns_quality_4(self, mastery):
        """Score 80-94% maps to quality 4 (correct with hesitation)"""
        assert mastery.score_to_quality(Decimal("94")) == 4
        assert mastery.score_to_quality(Decimal("80")) == 4
        assert mastery.score_to_quality(Decimal("87")) == 4

    def test_adequate_score_returns_quality_3(self, mastery):
        """Score 60-79% maps to quality 3 (correct with difficulty)"""
        assert mastery.score_to_quality(Decimal("79")) == 3
        assert mastery.score_to_quality(Decimal("60")) == 3
        assert mastery.score_to_quality(Decimal("70")) == 3

    def test_poor_score_returns_quality_2(self, mastery):
        """Score 40-59% maps to quality 2 (incorrect, easy to recall)"""
        assert mastery.score_to_quality(Decimal("59")) == 2
        assert mastery.score_to_quality(Decimal("40")) == 2
        assert mastery.score_to_quality(Decimal("50")) == 2

    def test_very_poor_score_returns_quality_1(self, mastery):
        """Score 20-39% maps to quality 1 (incorrect, remembered after hint)"""
        assert mastery.score_to_quality(Decimal("39")) == 1
        assert mastery.score_to_quality(Decimal("20")) == 1
        assert mastery.score_to_quality(Decimal("30")) == 1

    def test_blackout_score_returns_quality_0(self, mastery):
        """Score < 20% maps to quality 0 (complete blackout)"""
        assert mastery.score_to_quality(Decimal("19")) == 0
        assert mastery.score_to_quality(Decimal("0")) == 0
        assert mastery.score_to_quality(Decimal("10")) == 0

    def test_boundary_values(self, mastery):
        """Test exact boundary values"""
        # Test transitions at exact boundaries
        assert mastery.score_to_quality(Decimal("19.99")) == 0
        assert mastery.score_to_quality(Decimal("20.00")) == 1
        assert mastery.score_to_quality(Decimal("39.99")) == 1
        assert mastery.score_to_quality(Decimal("40.00")) == 2
        assert mastery.score_to_quality(Decimal("59.99")) == 2
        assert mastery.score_to_quality(Decimal("60.00")) == 3
        assert mastery.score_to_quality(Decimal("79.99")) == 3
        assert mastery.score_to_quality(Decimal("80.00")) == 4
        assert mastery.score_to_quality(Decimal("94.99")) == 4
        assert mastery.score_to_quality(Decimal("95.00")) == 5


class TestSM2FailedReview:
    """
    WHAT: Tests for SM-2 behavior on failed reviews (quality < 3)
    WHERE: Tests _schedule_next_review_sm2() failure path
    WHY: Validates correct reset behavior when student fails to recall
         material adequately
    """

    @pytest.fixture
    def mastery_with_history(self):
        """Mastery with some successful review history"""
        mastery = StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="SQL Joins",
            ease_factor=Decimal("2.30"),
            repetition_count=5,
            current_interval_days=30,
            last_quality_rating=4
        )
        return mastery

    def test_quality_0_resets_repetition_count(self, mastery_with_history):
        """Quality 0 (blackout) resets repetition count to 0"""
        mastery_with_history.record_assessment(Decimal("10"), passed=False, quality=0)
        assert mastery_with_history.repetition_count == 0

    def test_quality_1_resets_repetition_count(self, mastery_with_history):
        """Quality 1 (incorrect) resets repetition count to 0"""
        mastery_with_history.record_assessment(Decimal("25"), passed=False, quality=1)
        assert mastery_with_history.repetition_count == 0

    def test_quality_2_resets_repetition_count(self, mastery_with_history):
        """Quality 2 (incorrect, easy recall) resets repetition count to 0"""
        mastery_with_history.record_assessment(Decimal("45"), passed=False, quality=2)
        assert mastery_with_history.repetition_count == 0

    def test_failed_review_sets_interval_to_1(self, mastery_with_history):
        """Failed review (quality < 3) resets interval to 1 day"""
        mastery_with_history.record_assessment(Decimal("30"), passed=False, quality=1)
        assert mastery_with_history.current_interval_days == 1

    def test_failed_review_schedules_next_day(self, mastery_with_history):
        """Failed review schedules next review for tomorrow"""
        before = datetime.utcnow()
        mastery_with_history.record_assessment(Decimal("15"), passed=False, quality=0)
        after = datetime.utcnow()

        expected_min = before + timedelta(days=1)
        expected_max = after + timedelta(days=1)

        assert mastery_with_history.next_review_recommended_at >= expected_min
        assert mastery_with_history.next_review_recommended_at <= expected_max

    def test_failed_review_decreases_ease_factor(self, mastery_with_history):
        """Failed review decreases ease factor (but not below 1.3)"""
        original_ef = mastery_with_history.ease_factor
        mastery_with_history.record_assessment(Decimal("30"), passed=False, quality=1)
        assert mastery_with_history.ease_factor < original_ef

    def test_ease_factor_never_below_1_3(self, mastery_with_history):
        """Ease factor cannot go below 1.3 (SM-2 minimum)"""
        # Set to minimum and fail multiple times
        mastery_with_history.ease_factor = Decimal("1.30")
        for _ in range(5):
            mastery_with_history.record_assessment(Decimal("0"), passed=False, quality=0)

        assert mastery_with_history.ease_factor >= Decimal("1.30")


class TestSM2SuccessfulReview:
    """
    WHAT: Tests for SM-2 behavior on successful reviews (quality >= 3)
    WHERE: Tests _schedule_next_review_sm2() success path
    WHY: Validates correct interval expansion on successful recall
    """

    @pytest.fixture
    def fresh_mastery(self):
        """Fresh mastery with no review history"""
        return StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Data Structures"
        )

    @pytest.fixture
    def mastery_one_review(self):
        """Mastery after first successful review"""
        mastery = StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Algorithms",
            repetition_count=1,
            current_interval_days=1
        )
        return mastery

    @pytest.fixture
    def mastery_two_reviews(self):
        """Mastery after second successful review"""
        mastery = StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Web Development",
            repetition_count=2,
            current_interval_days=6
        )
        return mastery

    def test_first_success_interval_is_1_day(self, fresh_mastery):
        """First successful review (rep 0->1) sets interval to 1 day"""
        fresh_mastery.record_assessment(Decimal("80"), passed=True, quality=4)
        assert fresh_mastery.current_interval_days == 1
        assert fresh_mastery.repetition_count == 1

    def test_second_success_interval_is_6_days(self, mastery_one_review):
        """Second successful review (rep 1->2) sets interval to 6 days"""
        mastery_one_review.record_assessment(Decimal("85"), passed=True, quality=4)
        assert mastery_one_review.current_interval_days == 6
        assert mastery_one_review.repetition_count == 2

    def test_third_success_multiplies_by_ef(self, mastery_two_reviews):
        """Third+ review multiplies interval by ease factor"""
        original_ef = mastery_two_reviews.ease_factor  # 2.50
        mastery_two_reviews.record_assessment(Decimal("90"), passed=True, quality=4)

        # Expected: 6 * 2.5 = 15 (after first quality 4 EF adjustment)
        assert mastery_two_reviews.repetition_count == 3
        # Interval should be close to 6 * original_ef
        expected_interval = round(6 * float(original_ef))
        # Allow for EF adjustment in same cycle
        assert mastery_two_reviews.current_interval_days >= expected_interval - 2
        assert mastery_two_reviews.current_interval_days <= expected_interval + 2

    def test_quality_3_increments_repetition(self, fresh_mastery):
        """Quality 3 (correct with difficulty) still increments repetition"""
        fresh_mastery.record_assessment(Decimal("65"), passed=True, quality=3)
        assert fresh_mastery.repetition_count == 1

    def test_quality_4_increments_repetition(self, fresh_mastery):
        """Quality 4 (good recall) increments repetition"""
        fresh_mastery.record_assessment(Decimal("85"), passed=True, quality=4)
        assert fresh_mastery.repetition_count == 1

    def test_quality_5_increments_repetition(self, fresh_mastery):
        """Quality 5 (perfect) increments repetition"""
        fresh_mastery.record_assessment(Decimal("100"), passed=True, quality=5)
        assert fresh_mastery.repetition_count == 1


class TestSM2EaseFactorAdjustment:
    """
    WHAT: Tests for SM-2 ease factor formula calculations
    WHERE: Tests EF adjustment in _schedule_next_review_sm2()
    WHY: Validates correct implementation of SM-2 EF formula:
         EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    """

    @pytest.fixture
    def default_mastery(self):
        """Mastery with default ease factor 2.50"""
        return StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Testing"
        )

    def test_quality_5_increases_ease_factor(self, default_mastery):
        """Perfect quality (5) increases ease factor"""
        original_ef = default_mastery.ease_factor
        default_mastery.record_assessment(Decimal("100"), passed=True, quality=5)

        # EF formula for q=5: EF + (0.1 - 0 * (0.08 + 0 * 0.02)) = EF + 0.1
        expected = original_ef + Decimal("0.1")
        # But capped at 2.50
        expected = min(expected, Decimal("2.50"))
        assert default_mastery.ease_factor == expected

    def test_quality_4_maintains_or_increases_ef(self, default_mastery):
        """Good quality (4) maintains or slightly increases EF"""
        # EF formula for q=4: EF + (0.1 - 1 * (0.08 + 1 * 0.02)) = EF + 0.1 - 0.1 = EF
        original_ef = default_mastery.ease_factor
        default_mastery.record_assessment(Decimal("85"), passed=True, quality=4)
        # Should be exactly the same (or very close due to Decimal precision)
        assert abs(float(default_mastery.ease_factor) - float(original_ef)) < 0.01

    def test_quality_3_decreases_ease_factor(self, default_mastery):
        """Difficult recall (3) decreases ease factor"""
        original_ef = default_mastery.ease_factor
        default_mastery.record_assessment(Decimal("65"), passed=True, quality=3)

        # EF formula for q=3: EF + (0.1 - 2 * (0.08 + 2 * 0.02)) = EF + 0.1 - 0.24 = EF - 0.14
        assert default_mastery.ease_factor < original_ef

    def test_quality_0_significantly_decreases_ef(self, default_mastery):
        """Complete blackout (0) significantly decreases EF"""
        original_ef = default_mastery.ease_factor
        default_mastery.record_assessment(Decimal("5"), passed=False, quality=0)

        # EF formula for q=0: EF + (0.1 - 5 * (0.08 + 5 * 0.02)) = EF + 0.1 - 0.9 = EF - 0.8
        assert default_mastery.ease_factor < original_ef

    def test_ease_factor_minimum_bound(self, default_mastery):
        """Ease factor cannot go below 1.3"""
        default_mastery.ease_factor = Decimal("1.40")
        default_mastery.record_assessment(Decimal("0"), passed=False, quality=0)
        # Large decrease should hit floor
        assert default_mastery.ease_factor == Decimal("1.30")

    def test_ease_factor_maximum_bound(self, default_mastery):
        """Ease factor cannot exceed 2.5"""
        default_mastery.ease_factor = Decimal("2.45")
        default_mastery.record_assessment(Decimal("100"), passed=True, quality=5)
        assert default_mastery.ease_factor == Decimal("2.50")


class TestSM2IntervalCalculations:
    """
    WHAT: Tests for SM-2 interval progression calculations
    WHERE: Tests interval calculation in _schedule_next_review_sm2()
    WHY: Validates correct interval growth pattern for spaced repetition
    """

    @pytest.fixture
    def mastery(self):
        """Mastery for interval testing"""
        return StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="API Design"
        )

    def test_interval_progression_with_perfect_recall(self, mastery):
        """Test interval growth with consistent quality 5 responses"""
        # First review: interval = 1
        mastery.record_assessment(Decimal("100"), passed=True, quality=5)
        assert mastery.current_interval_days == 1

        # Second review: interval = 6
        mastery.record_assessment(Decimal("100"), passed=True, quality=5)
        assert mastery.current_interval_days == 6

        # Third review: interval = 6 * EF (EF is now ~2.6 capped at 2.5)
        mastery.record_assessment(Decimal("100"), passed=True, quality=5)
        assert mastery.current_interval_days >= 14  # 6 * 2.5 = 15, rounded

        # Fourth review: interval should continue growing
        prev_interval = mastery.current_interval_days
        mastery.record_assessment(Decimal("100"), passed=True, quality=5)
        assert mastery.current_interval_days > prev_interval

    def test_interval_reset_on_failure(self, mastery):
        """Test interval resets to 1 after a failure"""
        # Build up some history
        mastery.record_assessment(Decimal("90"), passed=True, quality=5)
        mastery.record_assessment(Decimal("90"), passed=True, quality=5)
        mastery.record_assessment(Decimal("90"), passed=True, quality=5)
        assert mastery.current_interval_days > 6

        # Fail
        mastery.record_assessment(Decimal("30"), passed=False, quality=1)
        assert mastery.current_interval_days == 1
        assert mastery.repetition_count == 0

    def test_interval_grows_slower_with_lower_ef(self, mastery):
        """Lower ease factor results in slower interval growth"""
        mastery.ease_factor = Decimal("1.50")
        mastery.repetition_count = 2
        mastery.current_interval_days = 6

        mastery.record_assessment(Decimal("65"), passed=True, quality=3)
        # 6 * 1.5 = 9 (approximately, EF adjusts)
        assert mastery.current_interval_days <= 12


class TestSM2QualityAutoDerivation:
    """
    WHAT: Tests for automatic quality derivation from scores
    WHERE: Tests record_assessment() without explicit quality
    WHY: Validates that quality is correctly derived when not provided
    """

    @pytest.fixture
    def mastery(self):
        """Mastery for auto-quality testing"""
        return StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Version Control"
        )

    def test_high_score_derives_quality_5(self, mastery):
        """Score >= 95% derives quality 5"""
        mastery.record_assessment(Decimal("98"), passed=True)
        assert mastery.last_quality_rating == 5

    def test_good_score_derives_quality_4(self, mastery):
        """Score 80-94% derives quality 4"""
        mastery.record_assessment(Decimal("87"), passed=True)
        assert mastery.last_quality_rating == 4

    def test_passing_score_derives_quality_3(self, mastery):
        """Score 60-79% derives quality 3"""
        mastery.record_assessment(Decimal("72"), passed=True)
        assert mastery.last_quality_rating == 3

    def test_low_score_derives_quality_2(self, mastery):
        """Score 40-59% derives quality 2"""
        mastery.record_assessment(Decimal("55"), passed=False)
        assert mastery.last_quality_rating == 2

    def test_very_low_score_derives_quality_1(self, mastery):
        """Score 20-39% derives quality 1"""
        mastery.record_assessment(Decimal("28"), passed=False)
        assert mastery.last_quality_rating == 1

    def test_failing_score_derives_quality_0(self, mastery):
        """Score < 20% derives quality 0"""
        mastery.record_assessment(Decimal("12"), passed=False)
        assert mastery.last_quality_rating == 0

    def test_explicit_quality_overrides_derived(self, mastery):
        """Explicit quality parameter overrides derived quality"""
        mastery.record_assessment(Decimal("95"), passed=True, quality=3)
        assert mastery.last_quality_rating == 3  # Explicit, not derived 5


class TestSM2ReviewScheduling:
    """
    WHAT: Tests for next_review_recommended_at scheduling
    WHERE: Tests review date calculation in _schedule_next_review_sm2()
    WHY: Validates correct future date calculation for reviews
    """

    @pytest.fixture
    def mastery(self):
        """Mastery for scheduling tests"""
        return StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Database Design"
        )

    def test_first_review_scheduled_for_tomorrow(self, mastery):
        """First successful review schedules for 1 day later"""
        before = datetime.utcnow()
        mastery.record_assessment(Decimal("85"), passed=True, quality=4)

        expected_date = before.date() + timedelta(days=1)
        actual_date = mastery.next_review_recommended_at.date()
        # Allow for seconds difference during test execution
        assert actual_date == expected_date or actual_date == expected_date + timedelta(days=1)

    def test_second_review_scheduled_for_6_days(self, mastery):
        """Second successful review schedules for 6 days later"""
        mastery.record_assessment(Decimal("85"), passed=True, quality=4)
        before = datetime.utcnow()
        mastery.record_assessment(Decimal("85"), passed=True, quality=4)

        expected_date = before.date() + timedelta(days=6)
        actual_date = mastery.next_review_recommended_at.date()
        assert actual_date == expected_date or actual_date == expected_date + timedelta(days=1)

    def test_failure_schedules_for_tomorrow(self, mastery):
        """Failed review schedules for next day regardless of history"""
        # Build up history
        mastery.record_assessment(Decimal("90"), passed=True, quality=5)
        mastery.record_assessment(Decimal("90"), passed=True, quality=5)
        mastery.record_assessment(Decimal("90"), passed=True, quality=5)

        before = datetime.utcnow()
        mastery.record_assessment(Decimal("20"), passed=False, quality=1)

        expected_date = before.date() + timedelta(days=1)
        actual_date = mastery.next_review_recommended_at.date()
        assert actual_date == expected_date or actual_date == expected_date + timedelta(days=1)

    def test_needs_review_respects_scheduled_date(self, mastery):
        """needs_review() correctly checks against scheduled date"""
        mastery.record_assessment(Decimal("85"), passed=True, quality=4)

        # Should not need review immediately after assessment
        assert mastery.needs_review() is False

        # Set to past to simulate time passing
        mastery.next_review_recommended_at = datetime.utcnow() - timedelta(hours=1)
        assert mastery.needs_review() is True


class TestSM2EdgeCases:
    """
    WHAT: Tests for SM-2 edge cases and boundary conditions
    WHERE: Tests unusual inputs and boundary scenarios
    WHY: Ensures robust handling of edge cases
    """

    @pytest.fixture
    def mastery(self):
        """Mastery for edge case testing"""
        return StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Edge Cases"
        )

    def test_zero_score_assessment(self, mastery):
        """Zero score is handled correctly"""
        mastery.record_assessment(Decimal("0"), passed=False, quality=0)
        assert mastery.assessments_completed == 1
        assert mastery.repetition_count == 0
        assert mastery.current_interval_days == 1

    def test_perfect_score_assessment(self, mastery):
        """Perfect 100% score is handled correctly"""
        mastery.record_assessment(Decimal("100"), passed=True, quality=5)
        assert mastery.assessments_completed == 1
        assert mastery.assessments_passed == 1
        assert mastery.last_quality_rating == 5

    def test_many_consecutive_failures(self, mastery):
        """Many consecutive failures don't break anything"""
        for _ in range(20):
            mastery.record_assessment(Decimal("10"), passed=False, quality=0)

        assert mastery.repetition_count == 0
        assert mastery.current_interval_days == 1
        assert mastery.ease_factor == Decimal("1.30")  # Should hit floor
        assert mastery.assessments_completed == 20

    def test_many_consecutive_successes(self, mastery):
        """Many consecutive successes grow interval significantly"""
        for _ in range(10):
            mastery.record_assessment(Decimal("95"), passed=True, quality=5)

        assert mastery.repetition_count == 10
        assert mastery.current_interval_days > 100  # Should be very large
        assert mastery.ease_factor == Decimal("2.50")  # Should hit ceiling

    def test_alternating_success_failure(self, mastery):
        """Alternating success and failure pattern"""
        for i in range(6):
            if i % 2 == 0:
                mastery.record_assessment(Decimal("90"), passed=True, quality=5)
            else:
                mastery.record_assessment(Decimal("20"), passed=False, quality=1)

        # After failure, should reset
        assert mastery.current_interval_days <= 6
        assert mastery.repetition_count <= 2

    def test_quality_exactly_3_is_success(self, mastery):
        """Quality exactly 3 is treated as success"""
        mastery.record_assessment(Decimal("60"), passed=True, quality=3)
        assert mastery.repetition_count == 1

    def test_quality_exactly_2_is_failure(self, mastery):
        """Quality exactly 2 is treated as failure"""
        # First build some history
        mastery.record_assessment(Decimal("90"), passed=True, quality=5)
        mastery.record_assessment(Decimal("90"), passed=True, quality=5)
        assert mastery.repetition_count == 2

        # Then fail with quality 2
        mastery.record_assessment(Decimal("45"), passed=False, quality=2)
        assert mastery.repetition_count == 0


class TestSM2IntegrationWithMasteryTracking:
    """
    WHAT: Integration tests for SM-2 with other mastery tracking features
    WHERE: Tests interaction between SM-2 and mastery level/scores
    WHY: Ensures SM-2 works correctly with existing mastery features
    """

    @pytest.fixture
    def mastery(self):
        """Mastery for integration testing"""
        return StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Integration Test"
        )

    def test_assessment_updates_both_scores_and_sm2(self, mastery):
        """Assessment updates both score tracking and SM-2 fields"""
        mastery.record_assessment(Decimal("85"), passed=True, quality=4)

        # Score tracking
        assert mastery.assessments_completed == 1
        assert mastery.assessments_passed == 1
        assert mastery.best_score == Decimal("85")
        assert mastery.average_score == Decimal("85")

        # SM-2 fields
        assert mastery.repetition_count == 1
        assert mastery.last_quality_rating == 4
        assert mastery.next_review_recommended_at is not None

    def test_mastery_level_updates_based_on_score(self, mastery):
        """Mastery level updates based on score (not quality)"""
        mastery.record_assessment(Decimal("85"), passed=True, quality=4)
        assert mastery.mastery_level == MasteryLevel.EXPERT

        mastery.record_assessment(Decimal("65"), passed=True, quality=3)
        # Average is now ~75
        assert mastery.mastery_level == MasteryLevel.PROFICIENT

    def test_retention_resets_after_assessment(self, mastery):
        """Retention estimate resets to 1.0 after assessment"""
        mastery.retention_estimate = Decimal("0.50")
        mastery.record_assessment(Decimal("80"), passed=True, quality=4)
        assert mastery.retention_estimate == Decimal("1.00")

    def test_last_assessment_at_updates(self, mastery):
        """last_assessment_at updates with each assessment"""
        before = datetime.utcnow()
        mastery.record_assessment(Decimal("80"), passed=True, quality=4)
        after = datetime.utcnow()

        assert mastery.last_assessment_at >= before
        assert mastery.last_assessment_at <= after
