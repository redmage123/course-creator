"""
WHAT: Service layer for Peer Learning System
WHERE: Used by API endpoints for study groups, peer reviews, discussions, and help requests
WHY: Orchestrates business logic for collaborative learning features including
     study group management, peer review workflows, discussion forums, and help matching

This service implements the core peer learning functionality including:
- Study group creation, joining, and management
- Peer review assignment and submission workflows
- Discussion thread and reply management with voting
- Help request matching and resolution tracking
- Reputation scoring across all peer learning activities
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from course_management.domain.entities.peer_learning import (
    StudyGroup, StudyGroupMembership, PeerReview, DiscussionThread,
    DiscussionReply, HelpRequest, PeerReputation, StudyGroupStatus,
    MembershipRole, MembershipStatus, PeerReviewStatus, ReviewQuality,
    ThreadStatus, HelpRequestStatus, HelpCategory, PeerLearningException,
    StudyGroupNotFoundException, StudyGroupFullException, NotGroupMemberException,
    InsufficientPermissionException, ReviewAssignmentException,
    HelpRequestNotFoundException
)
from data_access.peer_learning_dao import PeerLearningDAO, PeerLearningDAOException

logger = logging.getLogger(__name__)


class PeerLearningServiceException(PeerLearningException):
    """
    WHAT: Base exception for peer learning service errors
    WHERE: Thrown by service methods on business logic errors
    WHY: Distinguishes service-level errors from DAO errors
    """
    pass


class PeerLearningService:
    """
    WHAT: Service for managing peer learning features
    WHERE: Used by peer learning API endpoints and background tasks
    WHY: Centralizes business logic for collaborative learning including
         study groups, peer reviews, discussions, and help requests

    This service coordinates between:
    - PeerLearningDAO for persistence
    - Reputation tracking for gamification
    - User management for permissions
    """

    # Reputation point constants
    REPUTATION_POINTS_REVIEW_GIVEN = 10
    REPUTATION_POINTS_HELPFUL_REVIEW = 25
    REPUTATION_POINTS_HELP_SESSION_GIVEN = 20
    REPUTATION_POINTS_HELP_SESSION_EXCELLENT = 30
    REPUTATION_POINTS_DISCUSSION_STARTED = 5
    REPUTATION_POINTS_BEST_ANSWER = 50
    REPUTATION_POINTS_UPVOTE_RECEIVED = 2
    REPUTATION_POINTS_GROUP_PARTICIPATION = 15

    def __init__(
        self,
        peer_learning_dao: PeerLearningDAO,
        user_dao: Any = None,  # UserManagementDAO
        notification_service: Any = None  # NotificationService
    ):
        """
        WHAT: Initialize service with required dependencies
        WHERE: Called by dependency injection container
        WHY: Enables loose coupling and testability

        Args:
            peer_learning_dao: DAO for peer learning operations
            user_dao: DAO for user data access (optional)
            notification_service: Service for sending notifications (optional)
        """
        self._dao = peer_learning_dao
        self._user_dao = user_dao
        self._notification_service = notification_service

    # =========================================================================
    # STUDY GROUP MANAGEMENT
    # =========================================================================

    async def create_study_group(
        self,
        creator_id: UUID,
        name: str,
        course_id: UUID,
        description: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        track_id: Optional[UUID] = None,
        is_public: bool = True,
        max_members: int = 10,
        min_members: int = 2,
        meeting_schedule: Optional[str] = None,
        meeting_platform: Optional[str] = None,
        goals: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> StudyGroup:
        """
        WHAT: Creates a new study group for collaborative learning
        WHERE: Called from POST /api/v1/study-groups/
        WHY: Enables students to form study groups for courses

        Args:
            creator_id: UUID of the user creating the group
            name: Display name for the group
            course_id: UUID of the course this group studies
            description: Optional group description
            organization_id: Optional organization context
            track_id: Optional track context
            is_public: Whether group is visible for discovery
            max_members: Maximum allowed members (2-50)
            min_members: Minimum for activation (default 2)
            meeting_schedule: Optional recurring schedule description
            meeting_platform: Platform for meetings (e.g., "Zoom", "Discord")
            goals: Optional list of learning goals
            tags: Optional tags for discovery

        Returns:
            Created StudyGroup entity with creator as owner

        Raises:
            PeerLearningServiceException: On creation failure
        """
        try:
            # Validate max_members
            if max_members < 2 or max_members > 50:
                raise PeerLearningServiceException(
                    "Study group must allow between 2 and 50 members"
                )

            group = StudyGroup(
                id=uuid4(),
                name=name,
                description=description,
                course_id=course_id,
                track_id=track_id,
                organization_id=organization_id,
                creator_id=creator_id,
                is_public=is_public,
                max_members=max_members,
                min_members=min_members,
                meeting_schedule=meeting_schedule,
                meeting_platform=meeting_platform,
                goals=goals or [],
                tags=tags or []
            )

            created_group = await self._dao.create_study_group(group)
            logger.info(f"Created study group {created_group.id}: {name} by user {creator_id}")

            # Automatically add creator as owner
            await self._add_member_to_group(
                created_group.id, creator_id, MembershipRole.OWNER
            )

            return created_group

        except PeerLearningDAOException as e:
            logger.error(f"DAO error creating study group: {e}")
            raise PeerLearningServiceException(
                f"Failed to create study group: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating study group: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error creating study group: {str(e)}"
            ) from e

    async def get_study_group(self, group_id: UUID) -> StudyGroup:
        """
        WHAT: Retrieves a study group by ID with members
        WHERE: Called from GET /api/v1/study-groups/{id}
        WHY: Provides complete group data for display

        Args:
            group_id: UUID of the study group

        Returns:
            StudyGroup with member list

        Raises:
            StudyGroupNotFoundException: If group doesn't exist
            PeerLearningServiceException: On retrieval failure
        """
        try:
            group = await self._dao.get_study_group_by_id(group_id)
            if group is None:
                raise StudyGroupNotFoundException(
                    f"Study group {group_id} not found"
                )
            return group
        except StudyGroupNotFoundException:
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error getting study group: {e}")
            raise PeerLearningServiceException(
                f"Failed to get study group: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting study group: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error getting study group: {str(e)}"
            ) from e

    async def browse_study_groups(
        self,
        course_id: UUID,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[StudyGroup]:
        """
        WHAT: Browse available study groups for a course
        WHERE: Called from course study groups listing
        WHY: Enables students to discover and join groups

        Args:
            course_id: UUID of the course
            user_id: Optional user to check membership
            limit: Maximum groups to return
            offset: Pagination offset

        Returns:
            List of StudyGroup entities

        Raises:
            PeerLearningServiceException: On retrieval failure
        """
        try:
            return await self._dao.get_study_groups_by_course(
                course_id, include_private=False, limit=limit, offset=offset
            )
        except PeerLearningDAOException as e:
            logger.error(f"DAO error browsing study groups: {e}")
            raise PeerLearningServiceException(
                f"Failed to browse study groups: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error browsing study groups: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error browsing study groups: {str(e)}"
            ) from e

    async def join_study_group(
        self,
        group_id: UUID,
        user_id: UUID
    ) -> StudyGroupMembership:
        """
        WHAT: Joins a user to a study group
        WHERE: Called when user requests to join
        WHY: Enables collaborative learning participation

        Args:
            group_id: UUID of the study group
            user_id: UUID of the user joining

        Returns:
            Created StudyGroupMembership

        Raises:
            StudyGroupNotFoundException: If group doesn't exist
            StudyGroupFullException: If group is at capacity
            PeerLearningServiceException: On join failure
        """
        try:
            group = await self.get_study_group(group_id)

            # Check group can accept members
            if not group.can_accept_members():
                raise StudyGroupFullException(
                    f"Study group {group_id} cannot accept new members"
                )

            # Check user isn't already a member
            existing_memberships = await self._dao.get_user_memberships(user_id)
            for m in existing_memberships:
                if m.study_group_id == group_id:
                    raise PeerLearningServiceException(
                        f"User {user_id} is already a member of this group"
                    )

            # Add member
            membership = await self._add_member_to_group(
                group_id, user_id, MembershipRole.MEMBER
            )

            # Update group member count
            group.add_member()
            await self._dao.update_study_group(group)

            # Check if group should now be activated
            if group.status == StudyGroupStatus.FORMING:
                if group.current_member_count >= group.min_members:
                    group.activate()
                    await self._dao.update_study_group(group)
                    logger.info(f"Study group {group_id} activated with {group.current_member_count} members")

            logger.info(f"User {user_id} joined study group {group_id}")
            return membership

        except (StudyGroupNotFoundException, StudyGroupFullException):
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error joining study group: {e}")
            raise PeerLearningServiceException(
                f"Failed to join study group: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error joining study group: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error joining study group: {str(e)}"
            ) from e

    async def leave_study_group(
        self,
        group_id: UUID,
        user_id: UUID
    ) -> None:
        """
        WHAT: Removes a user from a study group
        WHERE: Called when user leaves voluntarily
        WHY: Allows members to exit groups

        Args:
            group_id: UUID of the study group
            user_id: UUID of the user leaving

        Raises:
            StudyGroupNotFoundException: If group doesn't exist
            NotGroupMemberException: If user isn't a member
            PeerLearningServiceException: On leave failure
        """
        try:
            group = await self.get_study_group(group_id)

            # Find membership
            membership = None
            for m in group.members:
                if m.user_id == user_id:
                    membership = m
                    break

            if membership is None:
                raise NotGroupMemberException(
                    f"User {user_id} is not a member of group {group_id}"
                )

            # Check if owner trying to leave
            if membership.role == MembershipRole.OWNER:
                # Owner must transfer ownership first or dissolve group
                raise InsufficientPermissionException(
                    "Group owner must transfer ownership before leaving"
                )

            # Update membership status
            membership.leave()
            await self._dao.update_membership(membership)

            # Update group member count
            group.remove_member()
            await self._dao.update_study_group(group)

            logger.info(f"User {user_id} left study group {group_id}")

        except (StudyGroupNotFoundException, NotGroupMemberException, InsufficientPermissionException):
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error leaving study group: {e}")
            raise PeerLearningServiceException(
                f"Failed to leave study group: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error leaving study group: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error leaving study group: {str(e)}"
            ) from e

    async def _add_member_to_group(
        self,
        group_id: UUID,
        user_id: UUID,
        role: MembershipRole
    ) -> StudyGroupMembership:
        """
        WHAT: Internal method to add a member to a group
        WHERE: Called by create_study_group and join_study_group
        WHY: Centralizes membership creation logic
        """
        membership = StudyGroupMembership(
            id=uuid4(),
            study_group_id=group_id,
            user_id=user_id,
            role=role,
            status=MembershipStatus.ACTIVE
        )
        membership.activate()
        return await self._dao.create_membership(membership)

    async def get_user_study_groups(
        self,
        user_id: UUID,
        active_only: bool = True
    ) -> List[StudyGroup]:
        """
        WHAT: Gets all study groups for a user
        WHERE: Called from user dashboard
        WHY: Shows user's collaborative learning groups

        Args:
            user_id: UUID of the user
            active_only: Only return active memberships

        Returns:
            List of StudyGroup entities

        Raises:
            PeerLearningServiceException: On retrieval failure
        """
        try:
            memberships = await self._dao.get_user_memberships(user_id, active_only)
            groups = []
            for m in memberships:
                try:
                    group = await self._dao.get_study_group_by_id(m.study_group_id)
                    if group:
                        groups.append(group)
                except Exception:
                    pass  # Skip if group not found
            return groups
        except PeerLearningDAOException as e:
            logger.error(f"DAO error getting user study groups: {e}")
            raise PeerLearningServiceException(
                f"Failed to get user study groups: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting user study groups: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error getting user study groups: {str(e)}"
            ) from e

    # =========================================================================
    # PEER REVIEW MANAGEMENT
    # =========================================================================

    async def assign_peer_review(
        self,
        assignment_id: UUID,
        submission_id: UUID,
        author_id: UUID,
        reviewer_id: UUID,
        course_id: UUID,
        due_at: Optional[datetime] = None,
        is_anonymous: bool = True,
        organization_id: Optional[UUID] = None
    ) -> PeerReview:
        """
        WHAT: Assigns a peer review task to a student
        WHERE: Called by assignment submission workflow or instructor
        WHY: Enables peer assessment of student work

        Args:
            assignment_id: UUID of the assignment
            submission_id: UUID of the submission to review
            author_id: UUID of submission author (for tracking)
            reviewer_id: UUID of the assigned reviewer
            course_id: UUID of the course
            due_at: Optional deadline for the review
            is_anonymous: Whether author identity is hidden
            organization_id: Optional organization context

        Returns:
            Created PeerReview assignment

        Raises:
            ReviewAssignmentException: If reviewer cannot be assigned
            PeerLearningServiceException: On assignment failure
        """
        try:
            # Validate reviewer is not the author
            if author_id == reviewer_id:
                raise ReviewAssignmentException(
                    "Cannot assign peer review to the submission author"
                )

            # Set default due date if not specified (7 days)
            if due_at is None:
                due_at = datetime.utcnow() + timedelta(days=7)

            review = PeerReview(
                id=uuid4(),
                assignment_id=assignment_id,
                submission_id=submission_id,
                author_id=author_id,
                reviewer_id=reviewer_id,
                course_id=course_id,
                organization_id=organization_id,
                is_anonymous=is_anonymous,
                due_at=due_at
            )
            review.assign()

            created_review = await self._dao.create_peer_review(review)
            logger.info(f"Assigned peer review {created_review.id} to reviewer {reviewer_id}")

            # Send notification if service available
            if self._notification_service:
                try:
                    await self._notification_service.send_notification(
                        reviewer_id,
                        "New Peer Review Assignment",
                        f"You have been assigned a peer review due {due_at.strftime('%Y-%m-%d')}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to send peer review notification: {e}")

            return created_review

        except ReviewAssignmentException:
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error assigning peer review: {e}")
            raise PeerLearningServiceException(
                f"Failed to assign peer review: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error assigning peer review: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error assigning peer review: {str(e)}"
            ) from e

    async def start_peer_review(self, review_id: UUID, reviewer_id: UUID) -> PeerReview:
        """
        WHAT: Marks a peer review as started
        WHERE: Called when reviewer opens the submission
        WHY: Tracks review progress and timing

        Args:
            review_id: UUID of the peer review
            reviewer_id: UUID of the reviewer (for verification)

        Returns:
            Updated PeerReview

        Raises:
            PeerLearningServiceException: On start failure
        """
        try:
            review = await self._dao.get_peer_review_by_id(review_id)
            if review is None:
                raise PeerLearningServiceException(f"Peer review {review_id} not found")

            if review.reviewer_id != reviewer_id:
                raise InsufficientPermissionException(
                    "Only assigned reviewer can start this review"
                )

            review.start()
            return await self._dao.update_peer_review(review)

        except InsufficientPermissionException:
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error starting peer review: {e}")
            raise PeerLearningServiceException(
                f"Failed to start peer review: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error starting peer review: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error starting peer review: {str(e)}"
            ) from e

    async def submit_peer_review(
        self,
        review_id: UUID,
        reviewer_id: UUID,
        overall_score: Decimal,
        strengths: str,
        improvements: str,
        detailed_feedback: Optional[str] = None,
        rubric_scores: Optional[Dict[str, Decimal]] = None
    ) -> PeerReview:
        """
        WHAT: Submits a completed peer review
        WHERE: Called when reviewer completes feedback
        WHY: Records peer assessment and updates reputation

        Args:
            review_id: UUID of the peer review
            reviewer_id: UUID of the reviewer (for verification)
            overall_score: Overall score (0-100)
            strengths: Text describing submission strengths
            improvements: Text describing areas for improvement
            detailed_feedback: Optional additional feedback
            rubric_scores: Optional scores per rubric criterion

        Returns:
            Completed PeerReview

        Raises:
            PeerLearningServiceException: On submission failure
        """
        try:
            review = await self._dao.get_peer_review_by_id(review_id)
            if review is None:
                raise PeerLearningServiceException(f"Peer review {review_id} not found")

            if review.reviewer_id != reviewer_id:
                raise InsufficientPermissionException(
                    "Only assigned reviewer can submit this review"
                )

            # Submit the review
            review.submit(overall_score, strengths, improvements)
            if detailed_feedback:
                review.detailed_feedback = detailed_feedback
            if rubric_scores:
                review.rubric_scores = rubric_scores

            updated_review = await self._dao.update_peer_review(review)

            # Update reviewer reputation
            await self._award_reputation_points(
                reviewer_id,
                self.REPUTATION_POINTS_REVIEW_GIVEN,
                'review',
                review.organization_id
            )

            logger.info(f"Peer review {review_id} submitted by {reviewer_id}")
            return updated_review

        except InsufficientPermissionException:
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error submitting peer review: {e}")
            raise PeerLearningServiceException(
                f"Failed to submit peer review: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error submitting peer review: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error submitting peer review: {str(e)}"
            ) from e

    async def rate_peer_review(
        self,
        review_id: UUID,
        author_id: UUID,
        quality_rating: ReviewQuality,
        helpfulness_score: int
    ) -> PeerReview:
        """
        WHAT: Rates a received peer review's quality
        WHERE: Called by submission author after viewing review
        WHY: Enables quality feedback and reputation adjustment

        Args:
            review_id: UUID of the peer review
            author_id: UUID of the submission author (for verification)
            quality_rating: Quality assessment (excellent, good, fair, poor, unhelpful)
            helpfulness_score: 1-5 helpfulness rating

        Returns:
            Updated PeerReview with rating

        Raises:
            PeerLearningServiceException: On rating failure
        """
        try:
            review = await self._dao.get_peer_review_by_id(review_id)
            if review is None:
                raise PeerLearningServiceException(f"Peer review {review_id} not found")

            if review.author_id != author_id:
                raise InsufficientPermissionException(
                    "Only submission author can rate this review"
                )

            review.rate_review(quality_rating, helpfulness_score)
            updated_review = await self._dao.update_peer_review(review)

            # Award bonus reputation for helpful reviews
            if quality_rating in [ReviewQuality.EXCELLENT, ReviewQuality.GOOD]:
                await self._award_reputation_points(
                    review.reviewer_id,
                    self.REPUTATION_POINTS_HELPFUL_REVIEW if quality_rating == ReviewQuality.EXCELLENT else 10,
                    'review',
                    review.organization_id
                )

            return updated_review

        except InsufficientPermissionException:
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error rating peer review: {e}")
            raise PeerLearningServiceException(
                f"Failed to rate peer review: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error rating peer review: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error rating peer review: {str(e)}"
            ) from e

    async def get_pending_reviews(
        self,
        reviewer_id: UUID,
        limit: int = 50
    ) -> List[PeerReview]:
        """
        WHAT: Gets pending peer review assignments for a user
        WHERE: Called from reviewer dashboard
        WHY: Shows outstanding review tasks

        Args:
            reviewer_id: UUID of the reviewer
            limit: Maximum reviews to return

        Returns:
            List of pending PeerReview entities

        Raises:
            PeerLearningServiceException: On retrieval failure
        """
        try:
            return await self._dao.get_reviews_for_reviewer(
                reviewer_id, PeerReviewStatus.ASSIGNED, limit
            )
        except PeerLearningDAOException as e:
            logger.error(f"DAO error getting pending reviews: {e}")
            raise PeerLearningServiceException(
                f"Failed to get pending reviews: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting pending reviews: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error getting pending reviews: {str(e)}"
            ) from e

    # =========================================================================
    # DISCUSSION FORUM MANAGEMENT
    # =========================================================================

    async def create_discussion_thread(
        self,
        author_id: UUID,
        title: str,
        content: str,
        course_id: UUID,
        is_question: bool = False,
        organization_id: Optional[UUID] = None,
        study_group_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None
    ) -> DiscussionThread:
        """
        WHAT: Creates a new discussion thread
        WHERE: Called from POST /api/v1/discussions/
        WHY: Enables asynchronous peer discussions

        Args:
            author_id: UUID of the thread author
            title: Thread title
            content: Thread body content
            course_id: UUID of the course context
            is_question: Whether this is a Q&A thread
            organization_id: Optional organization context
            study_group_id: Optional study group context
            tags: Optional topic tags

        Returns:
            Created DiscussionThread

        Raises:
            PeerLearningServiceException: On creation failure
        """
        try:
            thread = DiscussionThread(
                id=uuid4(),
                title=title,
                content=content,
                author_id=author_id,
                course_id=course_id,
                organization_id=organization_id,
                study_group_id=study_group_id,
                is_question=is_question,
                tags=tags or []
            )

            created_thread = await self._dao.create_discussion_thread(thread)
            logger.info(f"Created discussion thread {created_thread.id}: {title}")

            # Award reputation for starting discussion
            await self._award_reputation_points(
                author_id,
                self.REPUTATION_POINTS_DISCUSSION_STARTED,
                'discussion',
                organization_id
            )

            return created_thread

        except PeerLearningDAOException as e:
            logger.error(f"DAO error creating discussion thread: {e}")
            raise PeerLearningServiceException(
                f"Failed to create discussion thread: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating discussion thread: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error creating discussion thread: {str(e)}"
            ) from e

    async def get_discussion_thread(self, thread_id: UUID) -> DiscussionThread:
        """
        WHAT: Retrieves a discussion thread with replies
        WHERE: Called from GET /api/v1/discussions/{id}
        WHY: Provides complete thread for display

        Args:
            thread_id: UUID of the thread

        Returns:
            DiscussionThread with replies

        Raises:
            PeerLearningServiceException: If thread not found or on failure
        """
        try:
            thread = await self._dao.get_discussion_thread_by_id(thread_id)
            if thread is None:
                raise PeerLearningServiceException(
                    f"Discussion thread {thread_id} not found"
                )
            return thread
        except PeerLearningDAOException as e:
            logger.error(f"DAO error getting discussion thread: {e}")
            raise PeerLearningServiceException(
                f"Failed to get discussion thread: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting discussion thread: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error getting discussion thread: {str(e)}"
            ) from e

    async def browse_discussions(
        self,
        course_id: UUID,
        status: Optional[ThreadStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DiscussionThread]:
        """
        WHAT: Browse discussion threads for a course
        WHERE: Called from course forum listing
        WHY: Enables browsing course discussions

        Args:
            course_id: UUID of the course
            status: Optional filter by status
            limit: Maximum threads to return
            offset: Pagination offset

        Returns:
            List of DiscussionThread entities

        Raises:
            PeerLearningServiceException: On retrieval failure
        """
        try:
            return await self._dao.get_threads_by_course(
                course_id, status, limit, offset
            )
        except PeerLearningDAOException as e:
            logger.error(f"DAO error browsing discussions: {e}")
            raise PeerLearningServiceException(
                f"Failed to browse discussions: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error browsing discussions: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error browsing discussions: {str(e)}"
            ) from e

    async def reply_to_discussion(
        self,
        thread_id: UUID,
        author_id: UUID,
        content: str,
        parent_reply_id: Optional[UUID] = None
    ) -> DiscussionReply:
        """
        WHAT: Posts a reply to a discussion thread
        WHERE: Called when user submits reply
        WHY: Enables threaded discussions

        Args:
            thread_id: UUID of the thread
            author_id: UUID of the reply author
            content: Reply content
            parent_reply_id: Optional parent reply for nested replies

        Returns:
            Created DiscussionReply

        Raises:
            PeerLearningServiceException: On reply failure
        """
        try:
            # Verify thread exists
            thread = await self.get_discussion_thread(thread_id)

            reply = DiscussionReply(
                id=uuid4(),
                thread_id=thread_id,
                author_id=author_id,
                content=content,
                parent_reply_id=parent_reply_id
            )

            created_reply = await self._dao.create_discussion_reply(reply)

            # Update thread stats
            thread.add_reply(author_id)
            await self._dao.update_discussion_thread(thread)

            logger.debug(f"Created reply {created_reply.id} on thread {thread_id}")
            return created_reply

        except PeerLearningDAOException as e:
            logger.error(f"DAO error replying to discussion: {e}")
            raise PeerLearningServiceException(
                f"Failed to reply to discussion: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error replying to discussion: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error replying to discussion: {str(e)}"
            ) from e

    async def mark_best_answer(
        self,
        thread_id: UUID,
        reply_id: UUID,
        author_id: UUID
    ) -> DiscussionThread:
        """
        WHAT: Marks a reply as the best answer for a question thread
        WHERE: Called by thread author
        WHY: Highlights correct/helpful answers in Q&A

        Args:
            thread_id: UUID of the thread
            reply_id: UUID of the reply to mark
            author_id: UUID of the thread author (for verification)

        Returns:
            Updated DiscussionThread

        Raises:
            PeerLearningServiceException: On marking failure
        """
        try:
            thread = await self.get_discussion_thread(thread_id)

            if thread.author_id != author_id:
                raise InsufficientPermissionException(
                    "Only thread author can mark best answer"
                )

            if not thread.is_question:
                raise PeerLearningServiceException(
                    "Can only mark best answer on question threads"
                )

            thread.mark_best_answer(reply_id)
            updated_thread = await self._dao.update_discussion_thread(thread)

            # Find reply author and award reputation
            for reply in thread.replies:
                if reply.id == reply_id:
                    await self._award_reputation_points(
                        reply.author_id,
                        self.REPUTATION_POINTS_BEST_ANSWER,
                        'discussion',
                        thread.organization_id
                    )
                    break

            return updated_thread

        except InsufficientPermissionException:
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error marking best answer: {e}")
            raise PeerLearningServiceException(
                f"Failed to mark best answer: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error marking best answer: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error marking best answer: {str(e)}"
            ) from e

    async def vote_on_thread(
        self,
        thread_id: UUID,
        user_id: UUID,
        is_upvote: bool
    ) -> DiscussionThread:
        """
        WHAT: Records a vote on a discussion thread
        WHERE: Called when user upvotes/downvotes
        WHY: Enables community quality signals

        Args:
            thread_id: UUID of the thread
            user_id: UUID of the voter
            is_upvote: True for upvote, False for downvote

        Returns:
            Updated DiscussionThread

        Raises:
            PeerLearningServiceException: On voting failure
        """
        try:
            thread = await self.get_discussion_thread(thread_id)

            if is_upvote:
                thread.upvote()
                # Award small reputation to author
                await self._award_reputation_points(
                    thread.author_id,
                    self.REPUTATION_POINTS_UPVOTE_RECEIVED,
                    'discussion',
                    thread.organization_id
                )
            else:
                thread.downvote()

            return await self._dao.update_discussion_thread(thread)

        except PeerLearningDAOException as e:
            logger.error(f"DAO error voting on thread: {e}")
            raise PeerLearningServiceException(
                f"Failed to vote on thread: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error voting on thread: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error voting on thread: {str(e)}"
            ) from e

    # =========================================================================
    # HELP REQUEST MANAGEMENT
    # =========================================================================

    async def create_help_request(
        self,
        requester_id: UUID,
        title: str,
        description: str,
        category: HelpCategory,
        course_id: UUID,
        skill_topic: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        is_anonymous: bool = False,
        urgency: int = 5,
        estimated_duration_minutes: int = 30,
        expires_in_hours: int = 24
    ) -> HelpRequest:
        """
        WHAT: Creates a help request for peer assistance
        WHERE: Called from POST /api/v1/help-requests/
        WHY: Enables students to request help from peers

        Args:
            requester_id: UUID of the student needing help
            title: Brief description of help needed
            description: Detailed description
            category: Category of help needed
            course_id: UUID of the course context
            skill_topic: Optional specific topic
            organization_id: Optional organization context
            is_anonymous: Whether to hide requester identity
            urgency: Priority 1-10 (10 = most urgent)
            estimated_duration_minutes: Expected time needed
            expires_in_hours: Hours until request expires

        Returns:
            Created HelpRequest

        Raises:
            PeerLearningServiceException: On creation failure
        """
        try:
            request = HelpRequest(
                id=uuid4(),
                requester_id=requester_id,
                title=title,
                description=description,
                category=category,
                skill_topic=skill_topic,
                course_id=course_id,
                organization_id=organization_id,
                is_anonymous=is_anonymous,
                urgency=min(max(urgency, 1), 10),
                estimated_duration_minutes=estimated_duration_minutes,
                expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
            )

            created_request = await self._dao.create_help_request(request)
            logger.info(f"Created help request {created_request.id}: {title}")

            return created_request

        except PeerLearningDAOException as e:
            logger.error(f"DAO error creating help request: {e}")
            raise PeerLearningServiceException(
                f"Failed to create help request: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating help request: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error creating help request: {str(e)}"
            ) from e

    async def browse_help_requests(
        self,
        course_id: Optional[UUID] = None,
        category: Optional[HelpCategory] = None,
        limit: int = 50
    ) -> List[HelpRequest]:
        """
        WHAT: Browse open help requests
        WHERE: Called by students looking to help
        WHY: Enables peer matching for help

        Args:
            course_id: Optional filter by course
            category: Optional filter by category
            limit: Maximum requests to return

        Returns:
            List of open HelpRequest entities

        Raises:
            PeerLearningServiceException: On retrieval failure
        """
        try:
            return await self._dao.get_open_help_requests(
                course_id, category, limit
            )
        except PeerLearningDAOException as e:
            logger.error(f"DAO error browsing help requests: {e}")
            raise PeerLearningServiceException(
                f"Failed to browse help requests: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error browsing help requests: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error browsing help requests: {str(e)}"
            ) from e

    async def claim_help_request(
        self,
        request_id: UUID,
        helper_id: UUID
    ) -> HelpRequest:
        """
        WHAT: Claims a help request as a helper
        WHERE: Called when user volunteers to help
        WHY: Assigns helper to requester

        Args:
            request_id: UUID of the help request
            helper_id: UUID of the helper

        Returns:
            Updated HelpRequest

        Raises:
            HelpRequestNotFoundException: If request doesn't exist
            PeerLearningServiceException: On claim failure
        """
        try:
            request = await self._dao.get_help_request_by_id(request_id)
            if request is None:
                raise HelpRequestNotFoundException(
                    f"Help request {request_id} not found"
                )

            # Verify request is open
            if request.status != HelpRequestStatus.OPEN:
                raise PeerLearningServiceException(
                    f"Help request {request_id} is not open for claiming"
                )

            # Cannot claim own request
            if request.requester_id == helper_id:
                raise PeerLearningServiceException(
                    "Cannot claim your own help request"
                )

            request.claim(helper_id)
            updated_request = await self._dao.update_help_request(request)

            logger.info(f"Help request {request_id} claimed by {helper_id}")
            return updated_request

        except HelpRequestNotFoundException:
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error claiming help request: {e}")
            raise PeerLearningServiceException(
                f"Failed to claim help request: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error claiming help request: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error claiming help request: {str(e)}"
            ) from e

    async def start_help_session(self, request_id: UUID, helper_id: UUID) -> HelpRequest:
        """
        WHAT: Starts the help session
        WHERE: Called when helper begins assisting
        WHY: Tracks session timing

        Args:
            request_id: UUID of the help request
            helper_id: UUID of the helper (for verification)

        Returns:
            Updated HelpRequest

        Raises:
            PeerLearningServiceException: On start failure
        """
        try:
            request = await self._dao.get_help_request_by_id(request_id)
            if request is None:
                raise HelpRequestNotFoundException(
                    f"Help request {request_id} not found"
                )

            if request.helper_id != helper_id:
                raise InsufficientPermissionException(
                    "Only assigned helper can start session"
                )

            request.start_session()
            return await self._dao.update_help_request(request)

        except (HelpRequestNotFoundException, InsufficientPermissionException):
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error starting help session: {e}")
            raise PeerLearningServiceException(
                f"Failed to start help session: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error starting help session: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error starting help session: {str(e)}"
            ) from e

    async def resolve_help_request(
        self,
        request_id: UUID,
        resolver_id: UUID,
        resolution_notes: str,
        actual_duration_minutes: int
    ) -> HelpRequest:
        """
        WHAT: Marks a help request as resolved
        WHERE: Called when help session completes
        WHY: Closes request and triggers reputation

        Args:
            request_id: UUID of the help request
            resolver_id: UUID of person marking resolved (requester or helper)
            resolution_notes: Summary of how help was provided
            actual_duration_minutes: Actual time spent

        Returns:
            Resolved HelpRequest

        Raises:
            PeerLearningServiceException: On resolution failure
        """
        try:
            request = await self._dao.get_help_request_by_id(request_id)
            if request is None:
                raise HelpRequestNotFoundException(
                    f"Help request {request_id} not found"
                )

            if resolver_id not in [request.requester_id, request.helper_id]:
                raise InsufficientPermissionException(
                    "Only requester or helper can resolve request"
                )

            request.resolve(resolution_notes, actual_duration_minutes)
            updated_request = await self._dao.update_help_request(request)

            # Award reputation to helper
            if request.helper_id:
                await self._award_reputation_points(
                    request.helper_id,
                    self.REPUTATION_POINTS_HELP_SESSION_GIVEN,
                    'help',
                    request.organization_id
                )

            logger.info(f"Help request {request_id} resolved")
            return updated_request

        except (HelpRequestNotFoundException, InsufficientPermissionException):
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error resolving help request: {e}")
            raise PeerLearningServiceException(
                f"Failed to resolve help request: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error resolving help request: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error resolving help request: {str(e)}"
            ) from e

    async def rate_help_session(
        self,
        request_id: UUID,
        rater_id: UUID,
        rating: int,
        is_helper_rating: bool
    ) -> HelpRequest:
        """
        WHAT: Rates the help session quality
        WHERE: Called after session resolution
        WHY: Provides feedback and adjusts reputation

        Args:
            request_id: UUID of the help request
            rater_id: UUID of the person rating
            rating: Rating 1-5
            is_helper_rating: True if rating the helper, False if rating requester

        Returns:
            Updated HelpRequest with rating

        Raises:
            PeerLearningServiceException: On rating failure
        """
        try:
            request = await self._dao.get_help_request_by_id(request_id)
            if request is None:
                raise HelpRequestNotFoundException(
                    f"Help request {request_id} not found"
                )

            # Verify rater is part of the session
            if rater_id not in [request.requester_id, request.helper_id]:
                raise InsufficientPermissionException(
                    "Only session participants can rate"
                )

            # Rate appropriately
            if is_helper_rating:
                if rater_id != request.requester_id:
                    raise InsufficientPermissionException(
                        "Only requester can rate helper"
                    )
                request.rate_helper(rating)
                # Bonus reputation for excellent rating
                if rating >= 5 and request.helper_id:
                    await self._award_reputation_points(
                        request.helper_id,
                        self.REPUTATION_POINTS_HELP_SESSION_EXCELLENT,
                        'help',
                        request.organization_id
                    )
            else:
                if rater_id != request.helper_id:
                    raise InsufficientPermissionException(
                        "Only helper can rate requester"
                    )
                request.rate_requester(rating)

            return await self._dao.update_help_request(request)

        except (HelpRequestNotFoundException, InsufficientPermissionException):
            raise
        except PeerLearningDAOException as e:
            logger.error(f"DAO error rating help session: {e}")
            raise PeerLearningServiceException(
                f"Failed to rate help session: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error rating help session: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error rating help session: {str(e)}"
            ) from e

    # =========================================================================
    # REPUTATION MANAGEMENT
    # =========================================================================

    async def get_user_reputation(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None
    ) -> PeerReputation:
        """
        WHAT: Gets peer learning reputation for a user
        WHERE: Called from profile and leaderboard displays
        WHY: Shows user's peer learning standing

        Args:
            user_id: UUID of the user
            organization_id: Optional organization context

        Returns:
            PeerReputation entity (creates if doesn't exist)

        Raises:
            PeerLearningServiceException: On retrieval failure
        """
        try:
            reputation = await self._dao.get_reputation_by_user(user_id, organization_id)

            if reputation is None:
                # Create initial reputation
                reputation = PeerReputation(
                    id=uuid4(),
                    user_id=user_id,
                    organization_id=organization_id
                )
                reputation = await self._dao.upsert_reputation(reputation)

            return reputation

        except PeerLearningDAOException as e:
            logger.error(f"DAO error getting reputation: {e}")
            raise PeerLearningServiceException(
                f"Failed to get reputation: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error getting reputation: {e}")
            raise PeerLearningServiceException(
                f"Unexpected error getting reputation: {str(e)}"
            ) from e

    async def _award_reputation_points(
        self,
        user_id: UUID,
        points: int,
        category: str,
        organization_id: Optional[UUID] = None
    ) -> PeerReputation:
        """
        WHAT: Internal method to award reputation points
        WHERE: Called by various service methods after achievements
        WHY: Centralizes reputation scoring logic

        Args:
            user_id: UUID of the user earning points
            points: Number of points to award
            category: Category of achievement ('review', 'help', 'discussion', 'group')
            organization_id: Optional organization context

        Returns:
            Updated PeerReputation
        """
        try:
            reputation = await self.get_user_reputation(user_id, organization_id)

            # Update category-specific score
            if category == 'review':
                reputation.add_review_given()
                reputation.review_score += points
            elif category == 'help':
                reputation.add_help_session_given()
                reputation.help_score += points
            elif category == 'discussion':
                reputation.discussions_started += 1
                reputation.discussion_score += points
            elif category == 'group':
                reputation.group_score += points

            # Update overall score
            reputation.overall_score += points
            reputation.update_level()

            return await self._dao.upsert_reputation(reputation)

        except Exception as e:
            logger.warning(f"Error awarding reputation points: {e}")
            # Don't raise - reputation is supplementary
            return await self.get_user_reputation(user_id, organization_id)
