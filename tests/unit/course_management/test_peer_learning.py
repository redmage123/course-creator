"""
WHAT: Unit tests for Peer Learning System
WHERE: tests/unit/course_management/test_peer_learning.py
WHY: Validates business logic for study groups, peer reviews, discussions,
     help requests, and reputation tracking

This test module provides comprehensive coverage for:
- Study group lifecycle (creation, membership, activation)
- Peer review workflow (assignment, submission, quality rating)
- Discussion forum operations (threads, replies, voting)
- Help request matching and resolution
- Reputation scoring and gamification
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID

# Ensure correct service path is at the front of sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'))

from course_management.domain.entities.peer_learning import (
    StudyGroup, StudyGroupMembership, PeerReview, DiscussionThread,
    DiscussionReply, HelpRequest, PeerReputation, StudyGroupStatus,
    MembershipRole, MembershipStatus, PeerReviewStatus, ReviewQuality,
    ThreadStatus, HelpRequestStatus, HelpCategory,
    StudyGroupFullException, NotGroupMemberException,
    InsufficientPermissionException
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_uuids():
    """
    WHAT: Generate sample UUIDs for tests
    WHERE: Used across all test classes
    WHY: Provides consistent test data
    """
    return {
        'user1': uuid4(),
        'user2': uuid4(),
        'user3': uuid4(),
        'course': uuid4(),
        'track': uuid4(),
        'organization': uuid4(),
        'assignment': uuid4(),
        'submission': uuid4()
    }


@pytest.fixture
def study_group(sample_uuids):
    """
    WHAT: Create a sample study group
    WHERE: Used in study group tests
    WHY: Provides consistent test entity
    """
    return StudyGroup(
        id=uuid4(),
        name="Python Study Group",
        description="Learning Python together",
        course_id=sample_uuids['course'],
        organization_id=sample_uuids['organization'],
        creator_id=sample_uuids['user1'],
        max_members=10,
        min_members=2,
        is_public=True
    )


@pytest.fixture
def peer_review(sample_uuids):
    """
    WHAT: Create a sample peer review
    WHERE: Used in peer review tests
    WHY: Provides consistent test entity
    """
    return PeerReview(
        id=uuid4(),
        assignment_id=sample_uuids['assignment'],
        submission_id=sample_uuids['submission'],
        author_id=sample_uuids['user1'],
        reviewer_id=sample_uuids['user2'],
        course_id=sample_uuids['course'],
        is_anonymous=True,
        due_at=datetime.utcnow() + timedelta(days=7)
    )


@pytest.fixture
def discussion_thread(sample_uuids):
    """
    WHAT: Create a sample discussion thread
    WHERE: Used in discussion tests
    WHY: Provides consistent test entity
    """
    return DiscussionThread(
        id=uuid4(),
        title="How do decorators work?",
        content="I'm trying to understand Python decorators...",
        author_id=sample_uuids['user1'],
        course_id=sample_uuids['course'],
        is_question=True,
        tags=['python', 'decorators']
    )


@pytest.fixture
def help_request(sample_uuids):
    """
    WHAT: Create a sample help request
    WHERE: Used in help request tests
    WHY: Provides consistent test entity
    """
    return HelpRequest(
        id=uuid4(),
        requester_id=sample_uuids['user1'],
        title="Need help with recursion",
        description="I don't understand how recursive functions work...",
        category=HelpCategory.CONCEPT_CLARIFICATION,
        course_id=sample_uuids['course'],
        urgency=7,
        estimated_duration_minutes=30,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )


# =============================================================================
# STUDY GROUP TESTS
# =============================================================================

class TestStudyGroupCreation:
    """Tests for study group creation and initialization"""

    def test_group_starts_in_forming_status(self, study_group):
        """
        WHAT: Verify new groups start in FORMING status
        WHERE: StudyGroup.__init__
        WHY: Groups need members before becoming active
        """
        assert study_group.status == StudyGroupStatus.FORMING

    def test_group_has_zero_members_initially(self, study_group):
        """
        WHAT: Verify new groups have no members
        WHERE: StudyGroup.__init__
        WHY: Creator must join separately
        """
        assert study_group.current_member_count == 0

    def test_group_has_empty_member_list(self, study_group):
        """
        WHAT: Verify members list is initialized empty
        WHERE: StudyGroup.__init__
        WHY: Members are added separately
        """
        assert study_group.members == []

    def test_group_has_creation_timestamp(self, study_group):
        """
        WHAT: Verify creation timestamp is set
        WHERE: StudyGroup.__init__
        WHY: Audit trail requirement
        """
        assert study_group.created_at is not None


class TestStudyGroupMembership:
    """Tests for study group membership operations"""

    def test_can_accept_members_when_forming(self, study_group):
        """
        WHAT: Verify forming groups accept members
        WHERE: StudyGroup.can_accept_members
        WHY: Groups need to fill up before activation
        """
        assert study_group.can_accept_members() is True

    def test_cannot_accept_members_when_full(self, study_group):
        """
        WHAT: Verify full groups reject new members
        WHERE: StudyGroup.can_accept_members
        WHY: Prevent exceeding max capacity
        """
        study_group.current_member_count = study_group.max_members
        assert study_group.can_accept_members() is False

    def test_add_member_increments_count(self, study_group):
        """
        WHAT: Verify adding member increases count
        WHERE: StudyGroup.add_member
        WHY: Accurate member tracking
        """
        initial_count = study_group.current_member_count
        study_group.add_member()
        assert study_group.current_member_count == initial_count + 1

    def test_remove_member_decrements_count(self, study_group):
        """
        WHAT: Verify removing member decreases count
        WHERE: StudyGroup.remove_member
        WHY: Accurate member tracking
        """
        study_group.current_member_count = 5
        study_group.remove_member()
        assert study_group.current_member_count == 4

    def test_remove_member_never_goes_negative(self, study_group):
        """
        WHAT: Verify count doesn't go below zero
        WHERE: StudyGroup.remove_member
        WHY: Data integrity
        """
        study_group.current_member_count = 0
        study_group.remove_member()
        assert study_group.current_member_count == 0


class TestStudyGroupActivation:
    """Tests for study group status transitions"""

    def test_activate_sets_active_status(self, study_group):
        """
        WHAT: Verify activation changes status
        WHERE: StudyGroup.activate
        WHY: Enables group activities
        """
        study_group.current_member_count = study_group.min_members
        study_group.activate()
        assert study_group.status == StudyGroupStatus.ACTIVE

    def test_activate_sets_timestamp(self, study_group):
        """
        WHAT: Verify activation timestamp is recorded
        WHERE: StudyGroup.activate
        WHY: Audit trail for activation time
        """
        study_group.current_member_count = study_group.min_members
        study_group.activate()
        assert study_group.activated_at is not None

    def test_complete_sets_completed_status(self, study_group):
        """
        WHAT: Verify completion changes status
        WHERE: StudyGroup.complete
        WHY: Marks group as finished
        """
        study_group.status = StudyGroupStatus.ACTIVE
        study_group.complete()
        assert study_group.status == StudyGroupStatus.COMPLETED

    def test_complete_sets_timestamp(self, study_group):
        """
        WHAT: Verify completion timestamp is recorded
        WHERE: StudyGroup.complete
        WHY: Track when group completed
        """
        study_group.status = StudyGroupStatus.ACTIVE
        study_group.complete()
        assert study_group.completed_at is not None


class TestStudyGroupMembershipEntity:
    """Tests for StudyGroupMembership entity"""

    def test_membership_starts_pending(self, sample_uuids):
        """
        WHAT: Verify new membership starts pending
        WHERE: StudyGroupMembership.__init__
        WHY: May require approval in some cases
        """
        membership = StudyGroupMembership(
            id=uuid4(),
            study_group_id=uuid4(),
            user_id=sample_uuids['user1'],
            role=MembershipRole.MEMBER
        )
        assert membership.status == MembershipStatus.PENDING

    def test_activate_membership(self, sample_uuids):
        """
        WHAT: Verify membership activation
        WHERE: StudyGroupMembership.activate
        WHY: Confirm user as active member
        """
        membership = StudyGroupMembership(
            id=uuid4(),
            study_group_id=uuid4(),
            user_id=sample_uuids['user1'],
            role=MembershipRole.MEMBER
        )
        membership.activate()
        assert membership.status == MembershipStatus.ACTIVE
        assert membership.joined_at is not None

    def test_leave_membership(self, sample_uuids):
        """
        WHAT: Verify leaving sets left status
        WHERE: StudyGroupMembership.leave
        WHY: Track member departures
        """
        membership = StudyGroupMembership(
            id=uuid4(),
            study_group_id=uuid4(),
            user_id=sample_uuids['user1'],
            role=MembershipRole.MEMBER,
            status=MembershipStatus.ACTIVE
        )
        membership.leave()
        assert membership.status == MembershipStatus.LEFT
        assert membership.left_at is not None

    def test_record_activity_updates_timestamp(self, sample_uuids):
        """
        WHAT: Verify activity recording
        WHERE: StudyGroupMembership.record_activity
        WHY: Track engagement
        """
        membership = StudyGroupMembership(
            id=uuid4(),
            study_group_id=uuid4(),
            user_id=sample_uuids['user1'],
            role=MembershipRole.MEMBER,
            status=MembershipStatus.ACTIVE
        )
        membership.record_activity()
        assert membership.last_active_at is not None


# =============================================================================
# PEER REVIEW TESTS
# =============================================================================

class TestPeerReviewCreation:
    """Tests for peer review assignment creation"""

    def test_review_starts_as_assigned(self, peer_review):
        """
        WHAT: Verify new review starts as assigned
        WHERE: PeerReview.__init__
        WHY: Tracks assignment state
        """
        # Default status should be assigned after calling assign()
        peer_review.assign()
        assert peer_review.status == PeerReviewStatus.ASSIGNED

    def test_review_has_assigned_timestamp(self, peer_review):
        """
        WHAT: Verify assigned timestamp is set
        WHERE: PeerReview.assign
        WHY: Track when assigned
        """
        peer_review.assign()
        assert peer_review.assigned_at is not None

    def test_review_preserves_anonymity_setting(self, peer_review):
        """
        WHAT: Verify anonymity is preserved
        WHERE: PeerReview.__init__
        WHY: Privacy requirement
        """
        assert peer_review.is_anonymous is True


class TestPeerReviewWorkflow:
    """Tests for peer review workflow states"""

    def test_start_review_sets_in_progress(self, peer_review):
        """
        WHAT: Verify starting sets in_progress
        WHERE: PeerReview.start
        WHY: Track review progress
        """
        peer_review.assign()
        peer_review.start()
        assert peer_review.status == PeerReviewStatus.IN_PROGRESS

    def test_start_review_sets_timestamp(self, peer_review):
        """
        WHAT: Verify start timestamp is recorded
        WHERE: PeerReview.start
        WHY: Track when started
        """
        peer_review.assign()
        peer_review.start()
        assert peer_review.started_at is not None

    def test_submit_review_requires_feedback(self, peer_review):
        """
        WHAT: Verify submission records feedback
        WHERE: PeerReview.submit
        WHY: Ensure quality feedback
        """
        peer_review.assign()
        peer_review.start()
        peer_review.submit(
            overall_score=Decimal("85.5"),
            strengths="Good structure",
            improvements="Add more examples"
        )
        assert peer_review.status == PeerReviewStatus.SUBMITTED
        assert peer_review.overall_score == Decimal("85.5")
        assert peer_review.strengths == "Good structure"
        assert peer_review.improvements == "Add more examples"

    def test_submit_review_sets_timestamp(self, peer_review):
        """
        WHAT: Verify submission timestamp
        WHERE: PeerReview.submit
        WHY: Track when submitted
        """
        peer_review.assign()
        peer_review.start()
        peer_review.submit(Decimal("85"), "Good", "Improve")
        assert peer_review.submitted_at is not None

    def test_submit_calculates_word_count(self, peer_review):
        """
        WHAT: Verify word count calculation
        WHERE: PeerReview.submit
        WHY: Measure review quality
        """
        peer_review.assign()
        peer_review.start()
        peer_review.submit(
            Decimal("85"),
            "This is good work with clear structure",
            "Could use more detailed examples throughout"
        )
        assert peer_review.word_count > 0


class TestPeerReviewRating:
    """Tests for peer review quality rating"""

    def test_rate_review_stores_quality(self, peer_review):
        """
        WHAT: Verify quality rating storage
        WHERE: PeerReview.rate_review
        WHY: Quality feedback loop
        """
        peer_review.assign()
        peer_review.start()
        peer_review.submit(Decimal("85"), "Good", "Improve")
        peer_review.rate_review(ReviewQuality.EXCELLENT, 5)
        assert peer_review.quality_rating == ReviewQuality.EXCELLENT

    def test_rate_review_stores_helpfulness(self, peer_review):
        """
        WHAT: Verify helpfulness score storage
        WHERE: PeerReview.rate_review
        WHY: Measure review usefulness
        """
        peer_review.assign()
        peer_review.start()
        peer_review.submit(Decimal("85"), "Good", "Improve")
        peer_review.rate_review(ReviewQuality.GOOD, 4)
        assert peer_review.helpfulness_score == 4

    def test_excellent_rating_gives_positive_reputation(self, peer_review):
        """
        WHAT: Verify excellent rating boosts reputation
        WHERE: PeerReview.rate_review
        WHY: Incentivize quality reviews
        """
        peer_review.assign()
        peer_review.start()
        peer_review.submit(Decimal("85"), "Good", "Improve")
        peer_review.rate_review(ReviewQuality.EXCELLENT, 5)
        assert peer_review.reviewer_reputation_delta > 0

    def test_poor_rating_gives_negative_reputation(self, peer_review):
        """
        WHAT: Verify poor rating decreases reputation
        WHERE: PeerReview.rate_review
        WHY: Discourage low-quality reviews
        """
        peer_review.assign()
        peer_review.start()
        peer_review.submit(Decimal("85"), "Good", "Improve")
        peer_review.rate_review(ReviewQuality.POOR, 1)
        assert peer_review.reviewer_reputation_delta < 0


# =============================================================================
# DISCUSSION TESTS
# =============================================================================

class TestDiscussionThreadCreation:
    """Tests for discussion thread creation"""

    def test_thread_starts_open(self, discussion_thread):
        """
        WHAT: Verify new thread starts open
        WHERE: DiscussionThread.__init__
        WHY: Allow immediate participation
        """
        assert discussion_thread.status == ThreadStatus.OPEN

    def test_thread_has_zero_replies_initially(self, discussion_thread):
        """
        WHAT: Verify no replies initially
        WHERE: DiscussionThread.__init__
        WHY: Accurate counting
        """
        assert discussion_thread.reply_count == 0

    def test_thread_has_zero_votes_initially(self, discussion_thread):
        """
        WHAT: Verify no votes initially
        WHERE: DiscussionThread.__init__
        WHY: Start neutral
        """
        assert discussion_thread.upvote_count == 0
        assert discussion_thread.downvote_count == 0

    def test_question_thread_not_answered_initially(self, discussion_thread):
        """
        WHAT: Verify Q&A not answered initially
        WHERE: DiscussionThread.__init__
        WHY: No answer marked yet
        """
        assert discussion_thread.is_answered is False


class TestDiscussionVoting:
    """Tests for thread voting mechanics"""

    def test_upvote_increments_count(self, discussion_thread):
        """
        WHAT: Verify upvote increases count
        WHERE: DiscussionThread.upvote
        WHY: Accurate vote tracking
        """
        initial = discussion_thread.upvote_count
        discussion_thread.upvote()
        assert discussion_thread.upvote_count == initial + 1

    def test_downvote_increments_count(self, discussion_thread):
        """
        WHAT: Verify downvote increases count
        WHERE: DiscussionThread.downvote
        WHY: Accurate vote tracking
        """
        initial = discussion_thread.downvote_count
        discussion_thread.downvote()
        assert discussion_thread.downvote_count == initial + 1

    def test_vote_score_calculation(self, discussion_thread):
        """
        WHAT: Verify net vote score
        WHERE: DiscussionThread.vote_score
        WHY: Ranking threads
        """
        discussion_thread.upvote_count = 10
        discussion_thread.downvote_count = 3
        assert discussion_thread.vote_score() == 7


class TestDiscussionReplies:
    """Tests for thread reply operations"""

    def test_add_reply_increments_count(self, discussion_thread, sample_uuids):
        """
        WHAT: Verify reply increases count
        WHERE: DiscussionThread.add_reply
        WHY: Accurate reply tracking
        """
        initial = discussion_thread.reply_count
        discussion_thread.add_reply(sample_uuids['user2'])
        assert discussion_thread.reply_count == initial + 1

    def test_add_reply_updates_last_reply_at(self, discussion_thread, sample_uuids):
        """
        WHAT: Verify last reply timestamp
        WHERE: DiscussionThread.add_reply
        WHY: Sort by activity
        """
        discussion_thread.add_reply(sample_uuids['user2'])
        assert discussion_thread.last_reply_at is not None

    def test_add_reply_records_author(self, discussion_thread, sample_uuids):
        """
        WHAT: Verify last replier tracked
        WHERE: DiscussionThread.add_reply
        WHY: Show recent activity
        """
        discussion_thread.add_reply(sample_uuids['user2'])
        assert discussion_thread.last_reply_by == sample_uuids['user2']


class TestDiscussionBestAnswer:
    """Tests for Q&A best answer marking"""

    def test_mark_best_answer_sets_id(self, discussion_thread, sample_uuids):
        """
        WHAT: Verify best answer ID set
        WHERE: DiscussionThread.mark_best_answer
        WHY: Track accepted answer
        """
        reply_id = uuid4()
        discussion_thread.mark_best_answer(reply_id)
        assert discussion_thread.best_answer_id == reply_id

    def test_mark_best_answer_sets_answered(self, discussion_thread):
        """
        WHAT: Verify is_answered flag set
        WHERE: DiscussionThread.mark_best_answer
        WHY: Filter answered questions
        """
        discussion_thread.mark_best_answer(uuid4())
        assert discussion_thread.is_answered is True


class TestDiscussionReplyEntity:
    """Tests for DiscussionReply entity"""

    def test_reply_starts_with_zero_votes(self, sample_uuids):
        """
        WHAT: Verify replies start neutral
        WHERE: DiscussionReply.__init__
        WHY: Fair starting point
        """
        reply = DiscussionReply(
            id=uuid4(),
            thread_id=uuid4(),
            author_id=sample_uuids['user1'],
            content="Here's how decorators work..."
        )
        assert reply.upvote_count == 0
        assert reply.downvote_count == 0

    def test_reply_not_best_answer_initially(self, sample_uuids):
        """
        WHAT: Verify reply not marked initially
        WHERE: DiscussionReply.__init__
        WHY: Must be explicitly marked
        """
        reply = DiscussionReply(
            id=uuid4(),
            thread_id=uuid4(),
            author_id=sample_uuids['user1'],
            content="Here's how decorators work..."
        )
        assert reply.is_best_answer is False

    def test_edit_reply_sets_edited_flag(self, sample_uuids):
        """
        WHAT: Verify edit tracking
        WHERE: DiscussionReply.edit
        WHY: Show edited indicator
        """
        reply = DiscussionReply(
            id=uuid4(),
            thread_id=uuid4(),
            author_id=sample_uuids['user1'],
            content="Original content"
        )
        reply.edit("Updated content")
        assert reply.is_edited is True
        assert reply.content == "Updated content"


# =============================================================================
# HELP REQUEST TESTS
# =============================================================================

class TestHelpRequestCreation:
    """Tests for help request creation"""

    def test_request_starts_open(self, help_request):
        """
        WHAT: Verify new request starts open
        WHERE: HelpRequest.__init__
        WHY: Available for helpers
        """
        assert help_request.status == HelpRequestStatus.OPEN

    def test_request_has_no_helper_initially(self, help_request):
        """
        WHAT: Verify no helper assigned
        WHERE: HelpRequest.__init__
        WHY: Awaiting claim
        """
        assert help_request.helper_id is None

    def test_request_preserves_urgency(self, help_request):
        """
        WHAT: Verify urgency stored
        WHERE: HelpRequest.__init__
        WHY: Priority sorting
        """
        assert help_request.urgency == 7

    def test_request_has_expiration(self, help_request):
        """
        WHAT: Verify expiration set
        WHERE: HelpRequest.__init__
        WHY: Auto-expire stale requests
        """
        assert help_request.expires_at is not None
        assert help_request.expires_at > datetime.utcnow()


class TestHelpRequestWorkflow:
    """Tests for help request lifecycle"""

    def test_claim_assigns_helper(self, help_request, sample_uuids):
        """
        WHAT: Verify claiming assigns helper
        WHERE: HelpRequest.claim
        WHY: Connect helper with requester
        """
        help_request.claim(sample_uuids['user2'])
        assert help_request.helper_id == sample_uuids['user2']

    def test_claim_sets_claimed_status(self, help_request, sample_uuids):
        """
        WHAT: Verify claim changes status
        WHERE: HelpRequest.claim
        WHY: Prevent multiple claims
        """
        help_request.claim(sample_uuids['user2'])
        assert help_request.status == HelpRequestStatus.CLAIMED

    def test_claim_records_timestamp(self, help_request, sample_uuids):
        """
        WHAT: Verify claim timestamp
        WHERE: HelpRequest.claim
        WHY: Track response time
        """
        help_request.claim(sample_uuids['user2'])
        assert help_request.claimed_at is not None

    def test_start_session_sets_in_progress(self, help_request, sample_uuids):
        """
        WHAT: Verify starting sets in_progress
        WHERE: HelpRequest.start_session
        WHY: Track active sessions
        """
        help_request.claim(sample_uuids['user2'])
        help_request.start_session()
        assert help_request.status == HelpRequestStatus.IN_PROGRESS

    def test_start_session_records_timestamp(self, help_request, sample_uuids):
        """
        WHAT: Verify session start timestamp
        WHERE: HelpRequest.start_session
        WHY: Calculate duration
        """
        help_request.claim(sample_uuids['user2'])
        help_request.start_session()
        assert help_request.session_started_at is not None


class TestHelpRequestResolution:
    """Tests for help request resolution"""

    def test_resolve_sets_resolved_status(self, help_request, sample_uuids):
        """
        WHAT: Verify resolution changes status
        WHERE: HelpRequest.resolve
        WHY: Mark as completed
        """
        help_request.claim(sample_uuids['user2'])
        help_request.start_session()
        help_request.resolve("Explained recursion with examples", 25)
        assert help_request.status == HelpRequestStatus.RESOLVED

    def test_resolve_stores_notes(self, help_request, sample_uuids):
        """
        WHAT: Verify resolution notes stored
        WHERE: HelpRequest.resolve
        WHY: Document solution
        """
        help_request.claim(sample_uuids['user2'])
        help_request.start_session()
        help_request.resolve("Explained recursion with examples", 25)
        assert help_request.resolution_notes == "Explained recursion with examples"

    def test_resolve_stores_duration(self, help_request, sample_uuids):
        """
        WHAT: Verify actual duration stored
        WHERE: HelpRequest.resolve
        WHY: Track time spent
        """
        help_request.claim(sample_uuids['user2'])
        help_request.start_session()
        help_request.resolve("Explained", 25)
        assert help_request.actual_duration_minutes == 25

    def test_resolve_sets_timestamp(self, help_request, sample_uuids):
        """
        WHAT: Verify resolution timestamp
        WHERE: HelpRequest.resolve
        WHY: Track completion time
        """
        help_request.claim(sample_uuids['user2'])
        help_request.start_session()
        help_request.resolve("Done", 20)
        assert help_request.resolved_at is not None


class TestHelpRequestRating:
    """Tests for help session ratings"""

    def test_rate_helper_stores_rating(self, help_request, sample_uuids):
        """
        WHAT: Verify helper rating stored
        WHERE: HelpRequest.rate_helper
        WHY: Quality feedback
        """
        help_request.claim(sample_uuids['user2'])
        help_request.start_session()
        help_request.resolve("Done", 20)
        help_request.rate_helper(5)
        assert help_request.helper_rating == 5

    def test_rate_requester_stores_rating(self, help_request, sample_uuids):
        """
        WHAT: Verify requester rating stored
        WHERE: HelpRequest.rate_requester
        WHY: Two-way feedback
        """
        help_request.claim(sample_uuids['user2'])
        help_request.start_session()
        help_request.resolve("Done", 20)
        help_request.rate_requester(4)
        assert help_request.requester_rating == 4


class TestHelpRequestExpiration:
    """Tests for help request expiration"""

    def test_is_expired_returns_false_when_future(self, help_request):
        """
        WHAT: Verify not expired when future
        WHERE: HelpRequest.is_expired
        WHY: Still available
        """
        help_request.expires_at = datetime.utcnow() + timedelta(hours=12)
        assert help_request.is_expired() is False

    def test_is_expired_returns_true_when_past(self, help_request):
        """
        WHAT: Verify expired when past
        WHERE: HelpRequest.is_expired
        WHY: No longer available
        """
        help_request.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert help_request.is_expired() is True

    def test_expire_sets_expired_status(self, help_request):
        """
        WHAT: Verify expiration changes status
        WHERE: HelpRequest.expire
        WHY: Mark as unavailable
        """
        help_request.expire()
        assert help_request.status == HelpRequestStatus.EXPIRED


# =============================================================================
# REPUTATION TESTS
# =============================================================================

class TestPeerReputationCreation:
    """Tests for peer reputation initialization"""

    def test_reputation_starts_at_zero(self, sample_uuids):
        """
        WHAT: Verify new reputation starts at zero
        WHERE: PeerReputation.__init__
        WHY: Fair starting point
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1']
        )
        assert reputation.overall_score == 0

    def test_reputation_starts_at_level_1(self, sample_uuids):
        """
        WHAT: Verify starting level
        WHERE: PeerReputation.__init__
        WHY: Everyone starts at level 1
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1']
        )
        assert reputation.level == 1

    def test_reputation_has_empty_badges(self, sample_uuids):
        """
        WHAT: Verify no badges initially
        WHERE: PeerReputation.__init__
        WHY: Must earn badges
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1']
        )
        assert reputation.badges == []


class TestReputationScoring:
    """Tests for reputation score updates"""

    def test_add_review_increments_count(self, sample_uuids):
        """
        WHAT: Verify review count increment
        WHERE: PeerReputation.add_review_given
        WHY: Track contributions
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1']
        )
        initial = reputation.reviews_given
        reputation.add_review_given()
        assert reputation.reviews_given == initial + 1

    def test_add_help_session_increments_count(self, sample_uuids):
        """
        WHAT: Verify help session count increment
        WHERE: PeerReputation.add_help_session_given
        WHY: Track contributions
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1']
        )
        initial = reputation.help_sessions_given
        reputation.add_help_session_given()
        assert reputation.help_sessions_given == initial + 1


class TestReputationLevels:
    """Tests for reputation level calculation"""

    def test_level_1_at_zero_score(self, sample_uuids):
        """
        WHAT: Verify level 1 at start
        WHERE: PeerReputation.update_level
        WHY: Starting level
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1'],
            overall_score=0
        )
        reputation.update_level()
        assert reputation.level == 1

    def test_level_increases_with_score(self, sample_uuids):
        """
        WHAT: Verify level increases
        WHERE: PeerReputation.update_level
        WHY: Progression system
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1'],
            overall_score=150
        )
        reputation.update_level()
        assert reputation.level > 1

    def test_level_5_at_500_score(self, sample_uuids):
        """
        WHAT: Verify level 5 at 500 points
        WHERE: PeerReputation.update_level
        WHY: Mid-level milestone
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1'],
            overall_score=500
        )
        reputation.update_level()
        assert reputation.level == 5

    def test_level_10_at_2000_score(self, sample_uuids):
        """
        WHAT: Verify level 10 at 2000 points
        WHERE: PeerReputation.update_level
        WHY: High achievement
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1'],
            overall_score=2000
        )
        reputation.update_level()
        assert reputation.level == 10


class TestReputationBadges:
    """Tests for reputation badge system"""

    def test_add_badge(self, sample_uuids):
        """
        WHAT: Verify badge addition
        WHERE: PeerReputation.add_badge
        WHY: Award achievements
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1']
        )
        reputation.add_badge("First Review")
        assert "First Review" in reputation.badges

    def test_no_duplicate_badges(self, sample_uuids):
        """
        WHAT: Verify no duplicate badges
        WHERE: PeerReputation.add_badge
        WHY: Each badge earned once
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1']
        )
        reputation.add_badge("First Review")
        reputation.add_badge("First Review")
        assert reputation.badges.count("First Review") == 1

    def test_has_badge_returns_true(self, sample_uuids):
        """
        WHAT: Verify has_badge check
        WHERE: PeerReputation.has_badge
        WHY: Check for specific badges
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1']
        )
        reputation.add_badge("Helper")
        assert reputation.has_badge("Helper") is True

    def test_has_badge_returns_false(self, sample_uuids):
        """
        WHAT: Verify has_badge negative
        WHERE: PeerReputation.has_badge
        WHY: Check for missing badges
        """
        reputation = PeerReputation(
            id=uuid4(),
            user_id=sample_uuids['user1']
        )
        assert reputation.has_badge("Expert") is False


# =============================================================================
# INTEGRATION TESTS (Entity Interactions)
# =============================================================================

class TestPeerLearningWorkflows:
    """Integration tests for peer learning workflows"""

    def test_full_help_request_workflow(self, sample_uuids):
        """
        WHAT: Test complete help request flow
        WHERE: Integration test
        WHY: Validate end-to-end workflow
        """
        # Create request
        request = HelpRequest(
            id=uuid4(),
            requester_id=sample_uuids['user1'],
            title="Help with loops",
            description="I need help understanding for loops",
            category=HelpCategory.CONCEPT_CLARIFICATION,
            course_id=sample_uuids['course'],
            urgency=5,
            estimated_duration_minutes=20,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        assert request.status == HelpRequestStatus.OPEN

        # Claim request
        request.claim(sample_uuids['user2'])
        assert request.status == HelpRequestStatus.CLAIMED
        assert request.helper_id == sample_uuids['user2']

        # Start session
        request.start_session()
        assert request.status == HelpRequestStatus.IN_PROGRESS

        # Resolve
        request.resolve("Explained for loops with examples", 15)
        assert request.status == HelpRequestStatus.RESOLVED

        # Rate
        request.rate_helper(5)
        request.rate_requester(4)
        assert request.helper_rating == 5
        assert request.requester_rating == 4

    def test_full_peer_review_workflow(self, sample_uuids):
        """
        WHAT: Test complete peer review flow
        WHERE: Integration test
        WHY: Validate end-to-end workflow
        """
        # Create and assign review
        review = PeerReview(
            id=uuid4(),
            assignment_id=sample_uuids['assignment'],
            submission_id=sample_uuids['submission'],
            author_id=sample_uuids['user1'],
            reviewer_id=sample_uuids['user2'],
            course_id=sample_uuids['course'],
            is_anonymous=True,
            due_at=datetime.utcnow() + timedelta(days=7)
        )
        review.assign()
        assert review.status == PeerReviewStatus.ASSIGNED

        # Start review
        review.start()
        assert review.status == PeerReviewStatus.IN_PROGRESS

        # Submit review
        review.submit(
            overall_score=Decimal("88.5"),
            strengths="Excellent code organization and documentation",
            improvements="Could add more unit tests"
        )
        assert review.status == PeerReviewStatus.SUBMITTED

        # Rate review quality
        review.rate_review(ReviewQuality.EXCELLENT, 5)
        assert review.quality_rating == ReviewQuality.EXCELLENT
        assert review.reviewer_reputation_delta > 0

    def test_discussion_thread_full_workflow(self, sample_uuids):
        """
        WHAT: Test complete discussion workflow
        WHERE: Integration test
        WHY: Validate end-to-end workflow
        """
        # Create thread
        thread = DiscussionThread(
            id=uuid4(),
            title="Best practices for testing?",
            content="What are the best practices for unit testing in Python?",
            author_id=sample_uuids['user1'],
            course_id=sample_uuids['course'],
            is_question=True,
            tags=['testing', 'python', 'best-practices']
        )
        assert thread.status == ThreadStatus.OPEN
        assert thread.is_question is True

        # Add replies
        thread.add_reply(sample_uuids['user2'])
        thread.add_reply(sample_uuids['user3'])
        assert thread.reply_count == 2

        # Vote on thread
        thread.upvote()
        thread.upvote()
        thread.downvote()
        assert thread.vote_score() == 1

        # Mark best answer
        reply_id = uuid4()
        thread.mark_best_answer(reply_id)
        assert thread.is_answered is True
        assert thread.best_answer_id == reply_id
