"""
WHAT: Domain entities for Peer Learning system
WHERE: Used by course-management and analytics services
WHY: Enables collaborative learning through study groups, peer reviews,
     discussion threads, and help requests to improve learning outcomes

Enhancement 3: Peer Learning System

Key Features:
1. Study Groups - Collaborative learning groups for courses
2. Peer Reviews - Student-to-student assignment feedback
3. Discussion Threads - Course-specific threaded discussions
4. Help Requests - Peer-to-peer help system

Business Rules:
- Study groups have minimum/maximum member limits
- Peer reviews can be anonymous or attributed
- Discussions support threading and moderation
- Help requests have skill matching and reputation tracking
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID


# ============================================================================
# ENUMS
# ============================================================================

class StudyGroupStatus(str, Enum):
    """
    WHAT: Status states for study groups
    WHERE: Used in StudyGroup entity
    WHY: Tracks group lifecycle from formation to completion
    """
    FORMING = "forming"      # Accepting members
    ACTIVE = "active"        # Group is actively studying
    PAUSED = "paused"        # Temporarily inactive
    COMPLETED = "completed"  # Group finished their goals
    DISBANDED = "disbanded"  # Group was dissolved


class MembershipRole(str, Enum):
    """
    WHAT: Roles within a study group
    WHERE: Used in StudyGroupMembership
    WHY: Enables group leadership and responsibility assignment
    """
    OWNER = "owner"          # Group creator (cannot leave without transfer)
    LEADER = "leader"        # Group organizer
    CO_LEADER = "co_leader"  # Assistant leader
    MEMBER = "member"        # Regular participant
    OBSERVER = "observer"    # Can view but not participate


class MembershipStatus(str, Enum):
    """
    WHAT: Status of a member in a study group
    WHERE: Used in StudyGroupMembership
    WHY: Tracks member state (pending approval, active, left, etc.)
    """
    PENDING = "pending"      # Awaiting approval
    ACTIVE = "active"        # Active member
    INACTIVE = "inactive"    # Not currently participating
    LEFT = "left"            # Voluntarily left
    REMOVED = "removed"      # Was removed by leader


class PeerReviewStatus(str, Enum):
    """
    WHAT: Status states for peer reviews
    WHERE: Used in PeerReview entity
    WHY: Tracks review lifecycle
    """
    PENDING = "pending"          # Awaiting assignment
    ASSIGNED = "assigned"        # Assigned to reviewer
    IN_PROGRESS = "in_progress"  # Reviewer is working on it
    SUBMITTED = "submitted"      # Review completed
    REVISED = "revised"          # Author requested revision
    DISPUTED = "disputed"        # Author disputes the review
    ACCEPTED = "accepted"        # Author accepted feedback


class ReviewQuality(str, Enum):
    """
    WHAT: Quality rating for a peer review
    WHERE: Used in PeerReview to rate helpfulness
    WHY: Enables reputation tracking for reviewers
    """
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class ThreadStatus(str, Enum):
    """
    WHAT: Status states for discussion threads
    WHERE: Used in DiscussionThread entity
    WHY: Tracks thread lifecycle and moderation state
    """
    OPEN = "open"            # Accepting new posts
    ANSWERED = "answered"    # Question has been answered
    LOCKED = "locked"        # No new posts allowed
    ARCHIVED = "archived"    # Historical, read-only
    HIDDEN = "hidden"        # Hidden by moderation


class HelpRequestStatus(str, Enum):
    """
    WHAT: Status states for help requests
    WHERE: Used in HelpRequest entity
    WHY: Tracks help request lifecycle
    """
    OPEN = "open"            # Looking for help
    CLAIMED = "claimed"      # Someone is helping
    IN_PROGRESS = "in_progress"  # Help session active
    RESOLVED = "resolved"    # Problem solved
    CANCELLED = "cancelled"  # Request withdrawn
    EXPIRED = "expired"      # No response in time


class HelpCategory(str, Enum):
    """
    WHAT: Categories for help requests
    WHERE: Used to classify help needs
    WHY: Enables skill-based helper matching
    """
    CONCEPT = "concept"                        # Understanding concepts
    CONCEPT_CLARIFICATION = "concept_clarification"  # Clarifying concepts (alias)
    PRACTICE = "practice"                      # Hands-on exercises
    DEBUGGING = "debugging"                    # Code troubleshooting
    PROJECT = "project"                        # Project help
    EXAM_PREP = "exam_prep"                    # Test preparation
    CAREER = "career"                          # Career advice
    GENERAL = "general"                        # General questions


# ============================================================================
# EXCEPTIONS
# ============================================================================

class PeerLearningException(Exception):
    """
    WHAT: Base exception for peer learning errors
    WHERE: Parent for all peer learning exceptions
    WHY: Enables catching all peer learning errors with single handler
    """
    pass


class StudyGroupFullException(PeerLearningException):
    """
    WHAT: Raised when study group is at max capacity
    WHERE: When trying to join a full group
    WHY: Prevents exceeding group size limits
    """
    pass


class StudyGroupNotFoundException(PeerLearningException):
    """
    WHAT: Raised when study group not found
    WHERE: When querying non-existent group
    WHY: Provides clear error for missing resources
    """
    pass


class NotGroupMemberException(PeerLearningException):
    """
    WHAT: Raised when action requires group membership
    WHERE: When non-member tries restricted action
    WHY: Enforces membership requirements
    """
    pass


class InsufficientPermissionException(PeerLearningException):
    """
    WHAT: Raised when user lacks required permissions
    WHERE: When non-leader tries leader actions
    WHY: Enforces role-based permissions
    """
    pass


class ReviewAssignmentException(PeerLearningException):
    """
    WHAT: Raised when review assignment fails
    WHERE: When review can't be assigned
    WHY: Handles review matching failures
    """
    pass


class HelpRequestNotFoundException(PeerLearningException):
    """
    WHAT: Raised when help request not found
    WHERE: When querying non-existent request
    WHY: Provides clear error for missing resources
    """
    pass


# ============================================================================
# STUDY GROUP ENTITIES
# ============================================================================

@dataclass
class StudyGroup:
    """
    WHAT: A collaborative study group for course learning
    WHERE: Created by students, managed through course interface
    WHY: Enables peer-to-peer collaborative learning to improve outcomes
         through shared study sessions, discussions, and mutual support

    Business Rules:
    - Groups have minimum 2 and maximum configurable members
    - Only leaders can approve pending members
    - Groups can be public (join freely) or private (require approval)
    - Groups are associated with specific courses or tracks
    """
    id: UUID
    name: str
    description: str
    course_id: Optional[UUID] = None
    track_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    creator_id: Optional[UUID] = None
    status: StudyGroupStatus = StudyGroupStatus.FORMING
    is_public: bool = True
    min_members: int = 2
    max_members: int = 10
    current_member_count: int = 0
    meeting_schedule: Optional[str] = None  # JSON schedule or cron expression
    meeting_platform: Optional[str] = None  # e.g., "zoom", "discord", "in_app"
    meeting_link: Optional[str] = None
    goals: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    members: List["StudyGroupMembership"] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def can_accept_members(self) -> bool:
        """
        WHAT: Checks if group can accept new members
        WHERE: Called before adding members
        WHY: Enforces capacity limits
        """
        return (
            self.status in [StudyGroupStatus.FORMING, StudyGroupStatus.ACTIVE]
            and self.current_member_count < self.max_members
        )

    def add_member(self, membership: "StudyGroupMembership" = None) -> None:
        """
        WHAT: Adds a member to the study group
        WHERE: Called when user joins or is invited
        WHY: Manages group membership with validation

        Args:
            membership: Optional membership to add. If None, just increments count.

        Raises:
            StudyGroupFullException: If group is at capacity
        """
        if not self.can_accept_members():
            raise StudyGroupFullException(
                f"Study group {self.name} is at maximum capacity ({self.max_members})"
            )

        if membership is not None:
            self.members.append(membership)
            if membership.status == MembershipStatus.ACTIVE:
                self.current_member_count += 1
        else:
            # Simple increment for convenience
            self.current_member_count += 1

        self.updated_at = datetime.utcnow()

        # Auto-activate when minimum reached
        if (self.status == StudyGroupStatus.FORMING and
            self.current_member_count >= self.min_members):
            self.activate()

    def remove_member(self, user_id: UUID = None) -> bool:
        """
        WHAT: Removes a member from the group
        WHERE: Called when member leaves or is removed
        WHY: Handles membership termination

        Args:
            user_id: Optional user ID. If None, just decrements count.

        Returns:
            True if member was found and removed (or count decremented)
        """
        if user_id is not None:
            for membership in self.members:
                if membership.user_id == user_id and membership.status == MembershipStatus.ACTIVE:
                    membership.status = MembershipStatus.LEFT
                    membership.left_at = datetime.utcnow()
                    self.current_member_count -= 1
                    self.updated_at = datetime.utcnow()
                    return True
            return False
        else:
            # Simple decrement for convenience (never go below 0)
            if self.current_member_count > 0:
                self.current_member_count -= 1
                self.updated_at = datetime.utcnow()
            return True

    def activate(self) -> None:
        """
        WHAT: Activates the study group for learning
        WHERE: Called when minimum members reached
        WHY: Transitions group from forming to active state
        """
        if self.current_member_count >= self.min_members:
            self.status = StudyGroupStatus.ACTIVE
            self.activated_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def pause(self) -> None:
        """
        WHAT: Pauses group activity temporarily
        WHERE: Called by leader during breaks
        WHY: Allows temporary suspension without disbanding
        """
        self.status = StudyGroupStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume(self) -> None:
        """
        WHAT: Resumes paused group activity
        WHERE: Called by leader to restart
        WHY: Re-activates temporarily suspended group
        """
        if self.status == StudyGroupStatus.PAUSED:
            self.status = StudyGroupStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """
        WHAT: Marks group as completed
        WHERE: Called when group achieves goals
        WHY: Records successful group completion
        """
        self.status = StudyGroupStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def disband(self) -> None:
        """
        WHAT: Disbands the study group
        WHERE: Called by leader or system
        WHY: Terminates group that can't continue
        """
        self.status = StudyGroupStatus.DISBANDED
        self.updated_at = datetime.utcnow()

    def get_active_members(self) -> List["StudyGroupMembership"]:
        """
        WHAT: Gets all active members
        WHERE: Called for member listings
        WHY: Filters to only currently participating members
        """
        return [m for m in self.members if m.status == MembershipStatus.ACTIVE]

    def get_leaders(self) -> List["StudyGroupMembership"]:
        """
        WHAT: Gets group leaders
        WHERE: Called for permission checks
        WHY: Identifies members with leadership privileges
        """
        return [
            m for m in self.members
            if m.role in [MembershipRole.LEADER, MembershipRole.CO_LEADER]
            and m.status == MembershipStatus.ACTIVE
        ]


@dataclass
class StudyGroupMembership:
    """
    WHAT: Represents a user's membership in a study group
    WHERE: Links users to study groups
    WHY: Tracks membership details including role, status, and activity

    Business Rules:
    - Each user can have one membership per group
    - Leaders can promote/demote other members
    - Activity tracking helps identify inactive members
    """
    id: UUID
    study_group_id: UUID
    user_id: UUID
    role: MembershipRole = MembershipRole.MEMBER
    status: MembershipStatus = MembershipStatus.PENDING
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    contribution_score: int = 0  # Gamification metric
    sessions_attended: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def approve(self) -> None:
        """
        WHAT: Approves pending membership
        WHERE: Called by group leader
        WHY: Completes join process for private groups
        """
        if self.status == MembershipStatus.PENDING:
            self.status = MembershipStatus.ACTIVE
            self.joined_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """
        WHAT: Activates a pending membership (alias for approve)
        WHERE: Called when membership is confirmed
        WHY: Provides intuitive method name for activation
        """
        if self.status == MembershipStatus.PENDING:
            self.status = MembershipStatus.ACTIVE
            self.joined_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def leave(self) -> None:
        """
        WHAT: Records member leaving the group
        WHERE: Called when member voluntarily leaves
        WHY: Tracks departure for audit and analytics
        """
        if self.status == MembershipStatus.ACTIVE:
            self.status = MembershipStatus.LEFT
            self.left_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def promote_to_co_leader(self) -> None:
        """
        WHAT: Promotes member to co-leader
        WHERE: Called by group leader
        WHY: Distributes leadership responsibilities
        """
        if self.role == MembershipRole.MEMBER:
            self.role = MembershipRole.CO_LEADER
            self.updated_at = datetime.utcnow()

    def demote_to_member(self) -> None:
        """
        WHAT: Demotes co-leader to regular member
        WHERE: Called by group leader
        WHY: Revokes leadership privileges
        """
        if self.role == MembershipRole.CO_LEADER:
            self.role = MembershipRole.MEMBER
            self.updated_at = datetime.utcnow()

    def record_activity(self) -> None:
        """
        WHAT: Records member activity
        WHERE: Called on participation
        WHY: Tracks engagement for analytics
        """
        self.last_active_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_contribution(self, points: int) -> None:
        """
        WHAT: Adds contribution points
        WHERE: Called on helpful actions
        WHY: Gamification for engagement
        """
        self.contribution_score += points
        self.updated_at = datetime.utcnow()


# ============================================================================
# PEER REVIEW ENTITIES
# ============================================================================

@dataclass
class PeerReview:
    """
    WHAT: A peer review of a student's work by another student
    WHERE: Used for assignment feedback and peer assessment
    WHY: Enables collaborative learning through constructive feedback,
         develops critical thinking, and reduces instructor workload

    Business Rules:
    - Reviews can be anonymous or attributed
    - Reviewers earn reputation based on feedback quality
    - Authors can dispute unfair reviews
    - Minimum criteria must be met for review to count
    """
    id: UUID
    assignment_id: UUID
    submission_id: UUID  # The work being reviewed
    author_id: UUID  # Who submitted the work
    reviewer_id: UUID  # Who is doing the review
    course_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    is_anonymous: bool = True
    status: PeerReviewStatus = PeerReviewStatus.PENDING
    # Review content
    overall_score: Optional[Decimal] = None  # 0-100
    rubric_scores: Dict[str, Decimal] = field(default_factory=dict)  # criterion: score
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    detailed_feedback: Optional[str] = None
    # Timing
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    due_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    # Quality tracking
    quality_rating: Optional[ReviewQuality] = None
    helpfulness_score: Optional[int] = None  # 1-5 rating from author
    reviewer_reputation_delta: int = 0  # Points earned/lost
    # Metadata
    time_spent_seconds: int = 0
    word_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Set default due date if not provided"""
        if self.due_at is None:
            self.due_at = datetime.utcnow() + timedelta(days=3)

    def assign(self) -> None:
        """
        WHAT: Marks review as assigned to reviewer
        WHERE: Called when review is assigned
        WHY: Initiates the review process
        """
        self.status = PeerReviewStatus.ASSIGNED
        self.assigned_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def start(self) -> None:
        """
        WHAT: Marks review as started (alias for start_review)
        WHERE: Called when reviewer begins
        WHY: Provides intuitive method name
        """
        self.status = PeerReviewStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def start_review(self) -> None:
        """
        WHAT: Marks review as started
        WHERE: Called when reviewer begins
        WHY: Tracks review progress
        """
        self.status = PeerReviewStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def submit(
        self,
        overall_score: Decimal,
        strengths: str,
        improvements: str,
        detailed_feedback: Optional[str] = None,
        rubric_scores: Optional[Dict[str, Decimal]] = None
    ) -> None:
        """
        WHAT: Submits the completed review (alias for submit_review)
        WHERE: Called when reviewer finishes
        WHY: Provides intuitive method name

        Args:
            overall_score: Overall score (0-100)
            strengths: What the submission does well
            improvements: Areas for improvement
            detailed_feedback: Optional additional feedback
            rubric_scores: Optional scores per rubric criterion
        """
        self.submit_review(overall_score, strengths, improvements, detailed_feedback, rubric_scores)

    def submit_review(
        self,
        overall_score: Decimal,
        strengths: str,
        improvements: str,
        detailed_feedback: Optional[str] = None,
        rubric_scores: Optional[Dict[str, Decimal]] = None
    ) -> None:
        """
        WHAT: Submits the completed review
        WHERE: Called when reviewer finishes
        WHY: Records review content and finalizes submission

        Args:
            overall_score: Overall score (0-100)
            strengths: What the submission does well
            improvements: Areas for improvement
            detailed_feedback: Optional additional feedback
            rubric_scores: Optional scores per rubric criterion
        """
        self.overall_score = overall_score
        self.strengths = strengths
        self.improvements = improvements
        self.detailed_feedback = detailed_feedback
        if rubric_scores:
            self.rubric_scores = rubric_scores
        self.word_count = len((strengths or "").split()) + len((improvements or "").split())
        self.status = PeerReviewStatus.SUBMITTED
        self.submitted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Calculate time spent
        if self.started_at:
            delta = datetime.utcnow() - self.started_at
            self.time_spent_seconds = int(delta.total_seconds())

    def request_revision(self) -> None:
        """
        WHAT: Author requests review revision
        WHERE: Called when author disagrees
        WHY: Enables feedback loop on reviews
        """
        self.status = PeerReviewStatus.REVISED
        self.updated_at = datetime.utcnow()

    def dispute(self) -> None:
        """
        WHAT: Author disputes the review
        WHERE: Called for unfair reviews
        WHY: Enables moderation intervention
        """
        self.status = PeerReviewStatus.DISPUTED
        self.updated_at = datetime.utcnow()

    def accept(self) -> None:
        """
        WHAT: Author accepts the review
        WHERE: Called when satisfied with feedback
        WHY: Finalizes review process
        """
        self.status = PeerReviewStatus.ACCEPTED
        self.updated_at = datetime.utcnow()

    def rate_review(self, quality: ReviewQuality, score: int) -> None:
        """
        WHAT: Author rates review quality and helpfulness
        WHERE: Called after review completion
        WHY: Tracks reviewer reputation with quality-first interface

        Args:
            quality: Quality classification
            score: 1-5 helpfulness rating
        """
        self.rate_helpfulness(score, quality)

    def rate_helpfulness(self, score: int, quality: ReviewQuality) -> None:
        """
        WHAT: Author rates review helpfulness
        WHERE: Called after review completion
        WHY: Tracks reviewer reputation

        Args:
            score: 1-5 helpfulness rating
            quality: Quality classification
        """
        self.helpfulness_score = max(1, min(5, score))
        self.quality_rating = quality

        # Calculate reputation delta based on quality
        reputation_map = {
            ReviewQuality.POOR: -10,
            ReviewQuality.FAIR: 5,
            ReviewQuality.GOOD: 15,
            ReviewQuality.EXCELLENT: 25
        }
        self.reviewer_reputation_delta = reputation_map.get(quality, 0)
        self.updated_at = datetime.utcnow()

    def is_overdue(self) -> bool:
        """
        WHAT: Checks if review is past due date
        WHERE: Called for deadline tracking
        WHY: Identifies late reviews
        """
        if self.due_at is None:
            return False
        return datetime.utcnow() > self.due_at and self.status == PeerReviewStatus.PENDING


# ============================================================================
# DISCUSSION ENTITIES
# ============================================================================

@dataclass
class DiscussionThread:
    """
    WHAT: A discussion thread for course topics
    WHERE: Used in course forums and study groups
    WHY: Enables asynchronous peer discussions for Q&A,
         knowledge sharing, and collaborative problem-solving

    Business Rules:
    - Threads can be pinned for visibility
    - Moderation can lock or hide threads
    - Best answers can be marked (for questions)
    - Thread creators can edit their posts
    """
    id: UUID
    title: str
    content: str
    author_id: UUID
    course_id: Optional[UUID] = None
    study_group_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    parent_thread_id: Optional[UUID] = None  # For sub-threads
    status: ThreadStatus = ThreadStatus.OPEN
    is_question: bool = False
    is_answered: bool = False
    is_pinned: bool = False
    best_answer_id: Optional[UUID] = None
    tags: List[str] = field(default_factory=list)
    view_count: int = 0
    reply_count: int = 0
    upvote_count: int = 0
    downvote_count: int = 0
    last_reply_at: Optional[datetime] = None
    last_reply_by: Optional[UUID] = None
    replies: List["DiscussionReply"] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    edited_at: Optional[datetime] = None

    def add_reply(self, reply_or_user_id: "DiscussionReply" = None) -> None:
        """
        WHAT: Adds a reply to the thread
        WHERE: Called when user posts reply
        WHY: Manages thread replies

        Args:
            reply_or_user_id: Either a DiscussionReply object or a user UUID.
                              If UUID, just increments count and records author.
        """
        if self.status == ThreadStatus.LOCKED:
            raise PeerLearningException("Thread is locked")

        if reply_or_user_id is None:
            # Simple increment
            self.reply_count += 1
            self.last_reply_at = datetime.utcnow()
        elif isinstance(reply_or_user_id, UUID):
            # User ID provided - simplified tracking
            self.reply_count += 1
            self.last_reply_at = datetime.utcnow()
            self.last_reply_by = reply_or_user_id
        else:
            # Full DiscussionReply object
            self.replies.append(reply_or_user_id)
            self.reply_count += 1
            self.last_reply_at = datetime.utcnow()
            self.last_reply_by = reply_or_user_id.author_id

        self.updated_at = datetime.utcnow()

    def vote_score(self) -> int:
        """
        WHAT: Calculates net vote score (upvotes - downvotes)
        WHERE: Called for thread ranking
        WHY: Enables quality-based sorting
        """
        return self.upvote_count - self.downvote_count

    def mark_best_answer(self, answer_id: UUID) -> None:
        """
        WHAT: Marks a reply as the best answer (alias for mark_as_answered)
        WHERE: Called by thread author or instructor
        WHY: Provides intuitive method name
        """
        self.mark_as_answered(answer_id)

    def mark_as_answered(self, answer_id: UUID) -> None:
        """
        WHAT: Marks thread as answered with best answer
        WHERE: Called by thread author or instructor
        WHY: Highlights resolved questions
        """
        if self.is_question:
            self.is_answered = True
            self.best_answer_id = answer_id
            self.status = ThreadStatus.ANSWERED
            self.updated_at = datetime.utcnow()

    def pin(self) -> None:
        """
        WHAT: Pins thread for visibility
        WHERE: Called by moderators
        WHY: Highlights important threads
        """
        self.is_pinned = True
        self.updated_at = datetime.utcnow()

    def unpin(self) -> None:
        """
        WHAT: Removes pin from thread
        WHERE: Called by moderators
        WHY: Returns thread to normal visibility
        """
        self.is_pinned = False
        self.updated_at = datetime.utcnow()

    def lock(self) -> None:
        """
        WHAT: Locks thread from new replies
        WHERE: Called by moderators
        WHY: Prevents further discussion
        """
        self.status = ThreadStatus.LOCKED
        self.updated_at = datetime.utcnow()

    def unlock(self) -> None:
        """
        WHAT: Unlocks thread for replies
        WHERE: Called by moderators
        WHY: Re-enables discussion
        """
        if self.status == ThreadStatus.LOCKED:
            self.status = ThreadStatus.OPEN
            self.updated_at = datetime.utcnow()

    def hide(self) -> None:
        """
        WHAT: Hides thread from view
        WHERE: Called by moderators for violations
        WHY: Removes inappropriate content
        """
        self.status = ThreadStatus.HIDDEN
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """
        WHAT: Archives thread
        WHERE: Called for old threads
        WHY: Preserves historical content
        """
        self.status = ThreadStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def record_view(self) -> None:
        """
        WHAT: Records a view
        WHERE: Called on thread access
        WHY: Tracks popularity
        """
        self.view_count += 1

    def upvote(self) -> None:
        """
        WHAT: Adds an upvote
        WHERE: Called when user upvotes
        WHY: Tracks thread quality
        """
        self.upvote_count += 1
        self.updated_at = datetime.utcnow()

    def downvote(self) -> None:
        """
        WHAT: Adds a downvote
        WHERE: Called when user downvotes
        WHY: Tracks thread quality
        """
        self.downvote_count += 1
        self.updated_at = datetime.utcnow()

    def edit(self, new_content: str) -> None:
        """
        WHAT: Edits thread content
        WHERE: Called by author
        WHY: Allows content updates
        """
        self.content = new_content
        self.edited_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


@dataclass
class DiscussionReply:
    """
    WHAT: A reply in a discussion thread
    WHERE: Used within DiscussionThread
    WHY: Enables threaded discussions

    Business Rules:
    - Replies can be nested (parent_reply_id)
    - Authors can edit their replies
    - Helpful replies can be marked as best answer
    """
    id: UUID
    thread_id: UUID
    author_id: UUID
    content: str
    parent_reply_id: Optional[UUID] = None  # For nested replies
    is_best_answer: bool = False
    upvote_count: int = 0
    downvote_count: int = 0
    is_edited: bool = False
    is_hidden: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    edited_at: Optional[datetime] = None

    def mark_as_best_answer(self) -> None:
        """
        WHAT: Marks as best answer
        WHERE: Called by thread author
        WHY: Highlights most helpful reply
        """
        self.is_best_answer = True
        self.updated_at = datetime.utcnow()

    def upvote(self) -> None:
        """
        WHAT: Adds an upvote
        WHERE: Called when user upvotes
        WHY: Tracks reply quality
        """
        self.upvote_count += 1
        self.updated_at = datetime.utcnow()

    def downvote(self) -> None:
        """
        WHAT: Adds a downvote
        WHERE: Called when user downvotes
        WHY: Tracks reply quality
        """
        self.downvote_count += 1
        self.updated_at = datetime.utcnow()

    def edit(self, new_content: str) -> None:
        """
        WHAT: Edits reply content
        WHERE: Called by author
        WHY: Allows content updates
        """
        self.content = new_content
        self.is_edited = True
        self.edited_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def hide(self) -> None:
        """
        WHAT: Hides reply from view
        WHERE: Called by moderators
        WHY: Removes inappropriate content
        """
        self.is_hidden = True
        self.updated_at = datetime.utcnow()


# ============================================================================
# HELP REQUEST ENTITIES
# ============================================================================

@dataclass
class HelpRequest:
    """
    WHAT: A request for peer-to-peer help
    WHERE: Used in help matching system
    WHY: Connects students needing help with peers who can assist,
         enabling collaborative problem-solving and knowledge sharing

    Business Rules:
    - Requests expire after configurable time
    - Helpers earn reputation for successful help
    - Skill matching considers mastery levels
    - Anonymous requests protect student privacy
    """
    id: UUID
    requester_id: UUID
    title: str
    description: str
    category: HelpCategory = HelpCategory.GENERAL
    skill_topic: Optional[str] = None
    course_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    status: HelpRequestStatus = HelpRequestStatus.OPEN
    helper_id: Optional[UUID] = None
    is_anonymous: bool = False
    urgency: int = 5  # 1-10, higher is more urgent
    estimated_duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None
    # Resolution tracking
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    requester_rating: Optional[int] = None  # 1-5 rating of helper
    helper_rating: Optional[int] = None  # 1-5 rating of requester
    reputation_earned: int = 0
    # Timing
    expires_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    session_started_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Set default expiration if not provided"""
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)

    def claim(self, helper_id: UUID) -> None:
        """
        WHAT: Claims the help request
        WHERE: Called when helper volunteers
        WHY: Assigns helper to request

        Args:
            helper_id: UUID of the helper
        """
        if self.status != HelpRequestStatus.OPEN:
            raise PeerLearningException("Request is not open for claiming")
        if helper_id == self.requester_id:
            raise PeerLearningException("Cannot claim your own request")

        self.helper_id = helper_id
        self.status = HelpRequestStatus.CLAIMED
        self.claimed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def start_session(self) -> None:
        """
        WHAT: Starts the help session
        WHERE: Called when help begins
        WHY: Tracks session timing
        """
        if self.status != HelpRequestStatus.CLAIMED:
            raise PeerLearningException("Request must be claimed first")

        self.status = HelpRequestStatus.IN_PROGRESS
        self.session_started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def resolve(self, notes: Optional[str] = None, duration_minutes: Optional[int] = None) -> None:
        """
        WHAT: Marks request as resolved
        WHERE: Called when problem solved
        WHY: Completes help request lifecycle

        Args:
            notes: Optional resolution notes
            duration_minutes: Optional explicit duration (overrides calculated)
        """
        self.status = HelpRequestStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = notes
        self.updated_at = datetime.utcnow()

        # Set duration - use explicit value if provided, otherwise calculate
        if duration_minutes is not None:
            self.actual_duration_minutes = duration_minutes
        elif self.session_started_at:
            delta = datetime.utcnow() - self.session_started_at
            self.actual_duration_minutes = int(delta.total_seconds() / 60)

    def cancel(self) -> None:
        """
        WHAT: Cancels the help request
        WHERE: Called by requester
        WHY: Withdraws request
        """
        self.status = HelpRequestStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def expire(self) -> None:
        """
        WHAT: Marks request as expired
        WHERE: Called when timeout reached
        WHY: Cleans up unanswered requests
        """
        self.status = HelpRequestStatus.EXPIRED
        self.updated_at = datetime.utcnow()

    def rate_helper(self, rating: int) -> None:
        """
        WHAT: Requester rates the helper (sets helper_rating)
        WHERE: Called after resolution
        WHY: Tracks helper reputation

        Args:
            rating: 1-5 rating of the helper
        """
        self.helper_rating = max(1, min(5, rating))
        # Calculate reputation earned (higher rating = more points)
        self.reputation_earned = (rating - 2) * 10  # -10 to +30
        self.updated_at = datetime.utcnow()

    def rate_requester(self, rating: int) -> None:
        """
        WHAT: Helper rates the requester (sets requester_rating)
        WHERE: Called after resolution
        WHY: Tracks requester behavior

        Args:
            rating: 1-5 rating of the requester
        """
        self.requester_rating = max(1, min(5, rating))
        self.updated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """
        WHAT: Checks if request has expired
        WHERE: Called for cleanup
        WHY: Identifies stale requests
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at and self.status == HelpRequestStatus.OPEN


@dataclass
class PeerReputation:
    """
    WHAT: Tracks a student's peer learning reputation
    WHERE: Updated by peer interactions
    WHY: Gamifies peer learning and identifies helpful students

    Business Rules:
    - Reputation is skill-specific
    - Higher reputation unlocks privileges
    - Negative actions decrease reputation
    - Monthly decay prevents stagnation
    """
    id: UUID
    user_id: UUID
    organization_id: Optional[UUID] = None
    overall_score: int = 0
    review_score: int = 0  # Points from peer reviews
    help_score: int = 0  # Points from helping others
    discussion_score: int = 0  # Points from forum activity
    group_score: int = 0  # Points from study group participation
    reviews_given: int = 0
    reviews_received: int = 0
    help_sessions_given: int = 0
    help_sessions_received: int = 0
    discussions_started: int = 0
    helpful_answers: int = 0  # Marked as best answer
    level: int = 1  # Reputation level (1-10)
    badges: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_points(self, category: str, points: int) -> None:
        """
        WHAT: Adds reputation points
        WHERE: Called on positive actions
        WHY: Rewards helpful behavior

        Args:
            category: review, help, discussion, or group
            points: Points to add (can be negative)
        """
        category_map = {
            "review": "review_score",
            "help": "help_score",
            "discussion": "discussion_score",
            "group": "group_score"
        }
        if category in category_map:
            current = getattr(self, category_map[category])
            setattr(self, category_map[category], max(0, current + points))

        self.overall_score = (
            self.review_score + self.help_score +
            self.discussion_score + self.group_score
        )
        self._update_level()
        self.updated_at = datetime.utcnow()

    def add_review_given(self) -> None:
        """
        WHAT: Increments reviews given counter
        WHERE: Called when user completes a peer review
        WHY: Tracks contribution for reputation/badges
        """
        self.reviews_given += 1
        self.updated_at = datetime.utcnow()

    def add_review_received(self) -> None:
        """
        WHAT: Increments reviews received counter
        WHERE: Called when user receives a peer review
        WHY: Tracks engagement metrics
        """
        self.reviews_received += 1
        self.updated_at = datetime.utcnow()

    def add_help_session_given(self) -> None:
        """
        WHAT: Increments help sessions given counter
        WHERE: Called when user helps another student
        WHY: Tracks contribution for reputation/badges
        """
        self.help_sessions_given += 1
        self.updated_at = datetime.utcnow()

    def add_help_session_received(self) -> None:
        """
        WHAT: Increments help sessions received counter
        WHERE: Called when user receives help
        WHY: Tracks engagement metrics
        """
        self.help_sessions_received += 1
        self.updated_at = datetime.utcnow()

    def update_level(self) -> None:
        """
        WHAT: Updates reputation level based on score (public wrapper)
        WHERE: Called after score changes
        WHY: Provides progression system
        """
        self._update_level()

    def _update_level(self) -> None:
        """
        WHAT: Updates reputation level based on score
        WHERE: Called after point changes
        WHY: Provides progression system

        Level thresholds:
        - Level 1: 0+
        - Level 2: 100+
        - Level 3: 200+
        - Level 4: 350+
        - Level 5: 500+
        - Level 6: 700+
        - Level 7: 1000+
        - Level 8: 1400+
        - Level 9: 1800+
        - Level 10: 2000+
        """
        level_thresholds = [0, 100, 200, 350, 500, 700, 1000, 1400, 1800, 2000]
        for i, threshold in enumerate(level_thresholds):
            if self.overall_score < threshold:
                self.level = max(1, i)
                return
        self.level = 10

    def add_badge(self, badge: str) -> None:
        """
        WHAT: Awards a badge
        WHERE: Called on achievements
        WHY: Recognition system
        """
        if badge not in self.badges:
            self.badges.append(badge)
            self.updated_at = datetime.utcnow()

    def has_badge(self, badge: str) -> bool:
        """
        WHAT: Checks if user has a specific badge
        WHERE: Called for badge verification
        WHY: Enables badge-based permissions/features
        """
        return badge in self.badges
