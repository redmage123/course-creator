"""
WHAT: Unit tests for Adaptive Learning Path domain entities
WHERE: Tests course_management.domain.entities.learning_path
WHY: Validates business logic in domain entities including state transitions,
     prerequisite validation, progress tracking, and mastery calculations

Test Coverage:
- LearningPath lifecycle (create, start, pause, resume, complete, abandon)
- LearningPathNode progress tracking and status transitions
- PrerequisiteRule validation logic
- AdaptiveRecommendation lifecycle
- StudentMasteryLevel scoring and spaced repetition scheduling
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
    LearningPath, LearningPathNode, PrerequisiteRule, AdaptiveRecommendation,
    StudentMasteryLevel, PathType, PathStatus, NodeStatus, ContentType,
    RequirementType, RecommendationType, RecommendationStatus, MasteryLevel,
    DifficultyLevel, NodeNotUnlockedException, InvalidProgressException,
    CannotSkipRequiredNodeException, InvalidPathStateException,
    InvalidFeedbackException
)


class TestMasteryLevel:
    """
    WHAT: Tests for MasteryLevel enum and score conversion
    WHERE: Tests MasteryLevel.from_score() method
    WHY: Ensures consistent mastery level determination from numeric scores
    """

    def test_from_score_master(self):
        """Test score >= 95 returns MASTER"""
        assert MasteryLevel.from_score(Decimal("95")) == MasteryLevel.MASTER
        assert MasteryLevel.from_score(Decimal("100")) == MasteryLevel.MASTER

    def test_from_score_expert(self):
        """Test score 80-94 returns EXPERT"""
        assert MasteryLevel.from_score(Decimal("80")) == MasteryLevel.EXPERT
        assert MasteryLevel.from_score(Decimal("94")) == MasteryLevel.EXPERT

    def test_from_score_proficient(self):
        """Test score 60-79 returns PROFICIENT"""
        assert MasteryLevel.from_score(Decimal("60")) == MasteryLevel.PROFICIENT
        assert MasteryLevel.from_score(Decimal("79")) == MasteryLevel.PROFICIENT

    def test_from_score_intermediate(self):
        """Test score 40-59 returns INTERMEDIATE"""
        assert MasteryLevel.from_score(Decimal("40")) == MasteryLevel.INTERMEDIATE
        assert MasteryLevel.from_score(Decimal("59")) == MasteryLevel.INTERMEDIATE

    def test_from_score_beginner(self):
        """Test score 20-39 returns BEGINNER"""
        assert MasteryLevel.from_score(Decimal("20")) == MasteryLevel.BEGINNER
        assert MasteryLevel.from_score(Decimal("39")) == MasteryLevel.BEGINNER

    def test_from_score_novice(self):
        """Test score < 20 returns NOVICE"""
        assert MasteryLevel.from_score(Decimal("0")) == MasteryLevel.NOVICE
        assert MasteryLevel.from_score(Decimal("19")) == MasteryLevel.NOVICE


class TestPrerequisiteRule:
    """
    WHAT: Tests for PrerequisiteRule entity
    WHERE: Tests prerequisite validation logic
    WHY: Ensures correct evaluation of prerequisite requirements
    """

    @pytest.fixture
    def completion_rule(self):
        """Prerequisite requiring simple completion"""
        return PrerequisiteRule(
            id=uuid4(),
            target_type=ContentType.COURSE,
            target_id=uuid4(),
            prerequisite_type=ContentType.COURSE,
            prerequisite_id=uuid4(),
            requirement_type=RequirementType.COMPLETION
        )

    @pytest.fixture
    def score_rule(self):
        """Prerequisite requiring minimum score"""
        return PrerequisiteRule(
            id=uuid4(),
            target_type=ContentType.MODULE,
            target_id=uuid4(),
            prerequisite_type=ContentType.QUIZ,
            prerequisite_id=uuid4(),
            requirement_type=RequirementType.MINIMUM_SCORE,
            requirement_value=Decimal("70.00")
        )

    def test_completion_rule_met_when_completed(self, completion_rule):
        """Completion rule is met when content is completed"""
        assert completion_rule.is_met(completion_status=True) is True

    def test_completion_rule_not_met_when_incomplete(self, completion_rule):
        """Completion rule is not met when content is incomplete"""
        assert completion_rule.is_met(completion_status=False) is False

    def test_score_rule_met_when_score_sufficient(self, score_rule):
        """Score rule is met when score meets threshold"""
        assert score_rule.is_met(completion_status=True, score=Decimal("75")) is True
        assert score_rule.is_met(completion_status=True, score=Decimal("70")) is True

    def test_score_rule_not_met_when_score_insufficient(self, score_rule):
        """Score rule is not met when score below threshold"""
        assert score_rule.is_met(completion_status=True, score=Decimal("65")) is False

    def test_score_rule_not_met_when_incomplete(self, score_rule):
        """Score rule is not met when content incomplete regardless of score"""
        assert score_rule.is_met(completion_status=False, score=Decimal("100")) is False

    def test_score_rule_not_met_when_no_score(self, score_rule):
        """Score rule is not met when no score provided"""
        assert score_rule.is_met(completion_status=True, score=None) is False


class TestLearningPathNode:
    """
    WHAT: Tests for LearningPathNode entity
    WHERE: Tests node progress tracking and status transitions
    WHY: Ensures correct node lifecycle management and progress calculation
    """

    @pytest.fixture
    def unlocked_node(self):
        """Node that is available to start"""
        return LearningPathNode(
            id=uuid4(),
            learning_path_id=uuid4(),
            content_type=ContentType.MODULE,
            content_id=uuid4(),
            sequence_order=1,
            status=NodeStatus.AVAILABLE,
            is_unlocked=True
        )

    @pytest.fixture
    def locked_node(self):
        """Node that is locked"""
        return LearningPathNode(
            id=uuid4(),
            learning_path_id=uuid4(),
            content_type=ContentType.MODULE,
            content_id=uuid4(),
            sequence_order=2,
            status=NodeStatus.LOCKED,
            is_unlocked=False
        )

    @pytest.fixture
    def optional_node(self):
        """Optional node that can be skipped"""
        return LearningPathNode(
            id=uuid4(),
            learning_path_id=uuid4(),
            content_type=ContentType.LESSON,
            content_id=uuid4(),
            sequence_order=3,
            status=NodeStatus.AVAILABLE,
            is_required=False,
            is_unlocked=True
        )

    def test_start_unlocked_node(self, unlocked_node):
        """Starting an unlocked node sets status to IN_PROGRESS"""
        unlocked_node.start()
        assert unlocked_node.status == NodeStatus.IN_PROGRESS
        assert unlocked_node.started_at is not None

    def test_start_locked_node_raises_exception(self, locked_node):
        """Starting a locked node raises NodeNotUnlockedException"""
        with pytest.raises(NodeNotUnlockedException):
            locked_node.start()

    def test_update_progress_valid_range(self, unlocked_node):
        """Progress updates within valid range are accepted"""
        unlocked_node.start()
        unlocked_node.update_progress(Decimal("50"))
        assert unlocked_node.progress_percentage == Decimal("50")

    def test_update_progress_auto_completes_at_100(self, unlocked_node):
        """Progress at 100% auto-completes the node"""
        unlocked_node.start()
        unlocked_node.update_progress(Decimal("100"))
        assert unlocked_node.status == NodeStatus.COMPLETED
        assert unlocked_node.completed_at is not None

    def test_update_progress_invalid_negative_raises(self, unlocked_node):
        """Negative progress raises InvalidProgressException"""
        unlocked_node.start()
        with pytest.raises(InvalidProgressException):
            unlocked_node.update_progress(Decimal("-10"))

    def test_update_progress_invalid_over_100_raises(self, unlocked_node):
        """Progress over 100 raises InvalidProgressException"""
        unlocked_node.start()
        with pytest.raises(InvalidProgressException):
            unlocked_node.update_progress(Decimal("110"))

    def test_complete_node(self, unlocked_node):
        """Completing a node sets correct status and timestamp"""
        unlocked_node.start()
        unlocked_node.complete(score=Decimal("85"))
        assert unlocked_node.status == NodeStatus.COMPLETED
        assert unlocked_node.progress_percentage == Decimal("100.00")
        assert unlocked_node.score == Decimal("85")
        assert unlocked_node.completed_at is not None

    def test_skip_optional_node(self, optional_node):
        """Optional nodes can be skipped"""
        optional_node.skip()
        assert optional_node.status == NodeStatus.SKIPPED

    def test_skip_required_node_raises(self, unlocked_node):
        """Skipping a required node raises CannotSkipRequiredNodeException"""
        with pytest.raises(CannotSkipRequiredNodeException):
            unlocked_node.skip()

    def test_fail_node_increments_attempts(self, unlocked_node):
        """Failing a node increments attempt counter"""
        unlocked_node.start()
        initial_attempts = unlocked_node.attempts
        unlocked_node.fail()
        assert unlocked_node.status == NodeStatus.FAILED
        assert unlocked_node.attempts == initial_attempts + 1

    def test_unlock_node(self, locked_node):
        """Unlocking a node makes it available"""
        locked_node.unlock()
        assert locked_node.status == NodeStatus.AVAILABLE
        assert locked_node.is_unlocked is True

    def test_can_retry_unlimited(self, unlocked_node):
        """Node without max_attempts can always retry"""
        unlocked_node.attempts = 10
        assert unlocked_node.can_retry() is True

    def test_can_retry_within_limit(self, unlocked_node):
        """Node can retry when attempts < max_attempts"""
        unlocked_node.max_attempts = 3
        unlocked_node.attempts = 2
        assert unlocked_node.can_retry() is True

    def test_cannot_retry_at_limit(self, unlocked_node):
        """Node cannot retry when attempts >= max_attempts"""
        unlocked_node.max_attempts = 3
        unlocked_node.attempts = 3
        assert unlocked_node.can_retry() is False

    def test_add_time(self, unlocked_node):
        """Adding time updates time tracking fields"""
        unlocked_node.add_time(120)  # 2 minutes
        assert unlocked_node.time_spent_seconds == 120
        assert unlocked_node.actual_duration_minutes == 2

        unlocked_node.add_time(60)  # 1 more minute
        assert unlocked_node.time_spent_seconds == 180
        assert unlocked_node.actual_duration_minutes == 3


class TestLearningPath:
    """
    WHAT: Tests for LearningPath entity
    WHERE: Tests path lifecycle management and progress tracking
    WHY: Ensures correct path state transitions and progress calculations
    """

    @pytest.fixture
    def draft_path(self):
        """Path in draft state"""
        return LearningPath(
            id=uuid4(),
            student_id=uuid4(),
            name="Test Path",
            status=PathStatus.DRAFT
        )

    @pytest.fixture
    def active_path(self):
        """Path with active status and nodes"""
        path = LearningPath(
            id=uuid4(),
            student_id=uuid4(),
            name="Active Path",
            status=PathStatus.ACTIVE,
            started_at=datetime.utcnow()
        )
        # Add some nodes
        for i in range(3):
            node = LearningPathNode(
                id=uuid4(),
                learning_path_id=path.id,
                content_type=ContentType.MODULE,
                content_id=uuid4(),
                sequence_order=i + 1,
                status=NodeStatus.COMPLETED if i == 0 else NodeStatus.AVAILABLE
            )
            path.nodes.append(node)
        path.total_nodes = 3
        path.completed_nodes = 1
        return path

    def test_start_draft_path(self, draft_path):
        """Starting a draft path makes it active"""
        draft_path.start()
        assert draft_path.status == PathStatus.ACTIVE
        assert draft_path.started_at is not None

    def test_start_completed_path_raises(self):
        """Starting a completed path raises InvalidPathStateException"""
        path = LearningPath(
            id=uuid4(),
            student_id=uuid4(),
            name="Completed Path",
            status=PathStatus.COMPLETED
        )
        with pytest.raises(InvalidPathStateException):
            path.start()

    def test_pause_active_path(self, active_path):
        """Pausing an active path sets status to PAUSED"""
        active_path.pause()
        assert active_path.status == PathStatus.PAUSED

    def test_pause_non_active_path_raises(self, draft_path):
        """Pausing a non-active path raises InvalidPathStateException"""
        with pytest.raises(InvalidPathStateException):
            draft_path.pause()

    def test_resume_paused_path(self, active_path):
        """Resuming a paused path makes it active again"""
        active_path.pause()
        active_path.resume()
        assert active_path.status == PathStatus.ACTIVE

    def test_resume_non_paused_path_raises(self, active_path):
        """Resuming a non-paused path raises InvalidPathStateException"""
        with pytest.raises(InvalidPathStateException):
            active_path.resume()

    def test_complete_path(self, active_path):
        """Completing a path sets correct status and timestamps"""
        active_path.complete()
        assert active_path.status == PathStatus.COMPLETED
        assert active_path.overall_progress == Decimal("100.00")
        assert active_path.completed_at is not None

    def test_abandon_path(self, active_path):
        """Abandoning a path sets status to ABANDONED"""
        active_path.abandon()
        assert active_path.status == PathStatus.ABANDONED

    def test_update_progress_calculates_correctly(self, active_path):
        """Progress calculation from node completion is correct"""
        # 1 of 3 nodes completed = 33.33%
        active_path.update_progress()
        assert active_path.overall_progress == Decimal("33.33")
        assert active_path.completed_nodes == 1

    def test_update_progress_auto_completes_path(self, active_path):
        """Path auto-completes when all nodes completed"""
        for node in active_path.nodes:
            node.status = NodeStatus.COMPLETED
        active_path.update_progress()
        assert active_path.status == PathStatus.COMPLETED
        assert active_path.overall_progress == Decimal("100.00")

    def test_add_node_increments_total(self, active_path):
        """Adding a node increments total_nodes"""
        initial_total = active_path.total_nodes
        new_node = LearningPathNode(
            id=uuid4(),
            learning_path_id=active_path.id,
            content_type=ContentType.QUIZ,
            content_id=uuid4(),
            sequence_order=4
        )
        active_path.add_node(new_node)
        assert active_path.total_nodes == initial_total + 1

    def test_remove_node_decrements_total(self, active_path):
        """Removing a node decrements total_nodes"""
        initial_total = active_path.total_nodes
        node_to_remove = active_path.nodes[0].id
        active_path.remove_node(node_to_remove)
        assert active_path.total_nodes == initial_total - 1

    def test_get_current_node(self, active_path):
        """Getting current node returns correct node"""
        active_path.current_node_id = active_path.nodes[1].id
        current = active_path.get_current_node()
        assert current is not None
        assert current.id == active_path.nodes[1].id

    def test_get_next_available_node(self, active_path):
        """Getting next available node skips completed nodes"""
        next_node = active_path.get_next_available_node()
        assert next_node is not None
        assert next_node.status == NodeStatus.AVAILABLE

    def test_is_on_track_no_target(self, active_path):
        """Path without target date is always on track"""
        active_path.target_completion_date = None
        assert active_path.is_on_track() is True

    def test_is_on_track_ahead_of_schedule(self, active_path):
        """Path ahead of schedule returns True"""
        active_path.target_completion_date = (datetime.utcnow() + timedelta(days=30)).date()
        active_path.overall_progress = Decimal("50")  # 50% done with 30 days left
        assert active_path.is_on_track() is True

    def test_record_adaptation_increments_count(self, active_path):
        """Recording adaptation increments counter and timestamp"""
        initial_count = active_path.adaptation_count
        active_path.record_adaptation()
        assert active_path.adaptation_count == initial_count + 1
        assert active_path.last_adaptation_at is not None


class TestAdaptiveRecommendation:
    """
    WHAT: Tests for AdaptiveRecommendation entity
    WHERE: Tests recommendation lifecycle and validation
    WHY: Ensures correct recommendation state management and feedback handling
    """

    @pytest.fixture
    def recommendation(self):
        """Basic recommendation"""
        return AdaptiveRecommendation(
            id=uuid4(),
            student_id=uuid4(),
            recommendation_type=RecommendationType.NEXT_CONTENT,
            title="Continue to next module",
            reason="You've completed the prerequisites"
        )

    def test_view_recommendation(self, recommendation):
        """Viewing a recommendation updates status and timestamp"""
        recommendation.view()
        assert recommendation.status == RecommendationStatus.VIEWED
        assert recommendation.viewed_at is not None

    def test_accept_recommendation(self, recommendation):
        """Accepting a recommendation updates status and timestamp"""
        recommendation.accept()
        assert recommendation.status == RecommendationStatus.ACCEPTED
        assert recommendation.acted_on_at is not None

    def test_dismiss_recommendation(self, recommendation):
        """Dismissing a recommendation updates status"""
        recommendation.dismiss()
        assert recommendation.status == RecommendationStatus.DISMISSED

    def test_complete_recommendation(self, recommendation):
        """Completing a recommendation updates status"""
        recommendation.complete()
        assert recommendation.status == RecommendationStatus.COMPLETED

    def test_expire_recommendation(self, recommendation):
        """Expiring a recommendation updates status"""
        recommendation.expire()
        assert recommendation.status == RecommendationStatus.EXPIRED

    def test_is_valid_pending_not_expired(self, recommendation):
        """Pending recommendation within validity period is valid"""
        assert recommendation.is_valid() is True

    def test_is_valid_expired(self, recommendation):
        """Expired recommendation is not valid"""
        recommendation.valid_until = datetime.utcnow() - timedelta(hours=1)
        assert recommendation.is_valid() is False

    def test_is_valid_not_yet_valid(self, recommendation):
        """Recommendation before valid_from is not valid"""
        recommendation.valid_from = datetime.utcnow() + timedelta(hours=1)
        assert recommendation.is_valid() is False

    def test_is_valid_already_viewed(self, recommendation):
        """Viewed recommendation is not valid for pending check"""
        recommendation.view()
        assert recommendation.is_valid() is False

    def test_set_feedback_valid(self, recommendation):
        """Valid feedback values are accepted"""
        recommendation.set_feedback("helpful")
        assert recommendation.user_feedback == "helpful"

        recommendation.set_feedback("not_helpful")
        assert recommendation.user_feedback == "not_helpful"

    def test_set_feedback_invalid_raises(self, recommendation):
        """Invalid feedback values raise InvalidFeedbackException"""
        with pytest.raises(InvalidFeedbackException):
            recommendation.set_feedback("invalid_feedback")


class TestStudentMasteryLevel:
    """
    WHAT: Tests for StudentMasteryLevel entity
    WHERE: Tests mastery tracking and spaced repetition scheduling
    WHY: Ensures correct skill tracking and review scheduling
    """

    @pytest.fixture
    def mastery(self):
        """Basic mastery level"""
        return StudentMasteryLevel(
            id=uuid4(),
            student_id=uuid4(),
            skill_topic="Python Loops"
        )

    def test_record_assessment_updates_scores(self, mastery):
        """Recording assessment updates score metrics"""
        mastery.record_assessment(Decimal("85"), passed=True)

        assert mastery.assessments_completed == 1
        assert mastery.assessments_passed == 1
        assert mastery.best_score == Decimal("85")
        assert mastery.average_score == Decimal("85")
        assert mastery.mastery_level == MasteryLevel.EXPERT

    def test_record_assessment_updates_best_score(self, mastery):
        """Best score is updated only when exceeded"""
        mastery.record_assessment(Decimal("70"), passed=True)
        mastery.record_assessment(Decimal("80"), passed=True)
        mastery.record_assessment(Decimal("75"), passed=True)

        assert mastery.best_score == Decimal("80")

    def test_record_assessment_calculates_average(self, mastery):
        """Average score is calculated correctly"""
        mastery.record_assessment(Decimal("60"), passed=True)
        mastery.record_assessment(Decimal("80"), passed=True)

        # Average should be running average
        assert mastery.average_score is not None
        assert mastery.assessments_completed == 2

    def test_record_assessment_schedules_review(self, mastery):
        """Recording assessment schedules next review"""
        mastery.record_assessment(Decimal("50"), passed=False)

        assert mastery.next_review_recommended_at is not None
        assert mastery.next_review_recommended_at > datetime.utcnow()

    def test_record_practice_updates_time(self, mastery):
        """Recording practice updates time tracking"""
        mastery.record_practice(30)

        assert mastery.total_practice_time_minutes == 30
        assert mastery.last_practiced_at is not None
        assert mastery.practice_streak_days == 1

    def test_needs_review_when_scheduled(self, mastery):
        """Skill needs review when past scheduled date"""
        mastery.next_review_recommended_at = datetime.utcnow() - timedelta(days=1)
        assert mastery.needs_review() is True

    def test_no_review_needed_when_not_due(self, mastery):
        """Skill doesn't need review when not past scheduled date"""
        mastery.next_review_recommended_at = datetime.utcnow() + timedelta(days=1)
        assert mastery.needs_review() is False

    def test_no_review_needed_when_not_scheduled(self, mastery):
        """Skill doesn't need review when no schedule set"""
        mastery.next_review_recommended_at = None
        assert mastery.needs_review() is False

    def test_calculate_retention_decays_over_time(self, mastery):
        """Retention estimate decays based on time since assessment"""
        mastery.last_assessment_at = datetime.utcnow() - timedelta(days=7)
        mastery.mastery_level = MasteryLevel.INTERMEDIATE

        retention = mastery.calculate_retention()

        assert retention < Decimal("1.00")
        assert retention >= Decimal("0.00")
