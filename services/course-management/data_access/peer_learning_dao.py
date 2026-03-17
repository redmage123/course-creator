"""
WHAT: Data Access Object for Peer Learning System
WHERE: Used by PeerLearningService for all database operations
WHY: Provides clean database abstraction for study groups, peer reviews,
     discussions, and help requests with proper exception handling

This DAO implements the repository pattern for all peer learning related
database operations with comprehensive error handling.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
import json

import asyncpg

from course_management.domain.entities.peer_learning import (
    StudyGroup, StudyGroupMembership, PeerReview, DiscussionThread,
    DiscussionReply, HelpRequest, PeerReputation, StudyGroupStatus,
    MembershipRole, MembershipStatus, PeerReviewStatus, ReviewQuality,
    ThreadStatus, HelpRequestStatus, HelpCategory, PeerLearningException,
    StudyGroupNotFoundException, HelpRequestNotFoundException
)

logger = logging.getLogger(__name__)


class PeerLearningDAOException(PeerLearningException):
    """
    WHAT: Base exception for Peer Learning DAO operations
    WHERE: Thrown by all DAO methods on database errors
    WHY: Wraps low-level database exceptions with context
    """
    pass


class PeerLearningDAO:
    """
    WHAT: Data Access Object for peer learning database operations
    WHERE: Used by PeerLearningService for all persistence operations
    WHY: Centralizes database logic, enables testing with mocks,
         provides clean separation from business logic

    All methods wrap base exceptions in custom exceptions as per coding standards.
    """

    def __init__(self, pool: asyncpg.Pool):
        """
        WHAT: Initialize DAO with database connection pool
        WHERE: Called by dependency injection in service layer
        WHY: Enables connection pooling for performance
        """
        self._pool = pool

    # =========================================================================
    # STUDY GROUP OPERATIONS
    # =========================================================================

    async def create_study_group(self, group: StudyGroup) -> StudyGroup:
        """
        WHAT: Creates a new study group in the database
        WHERE: Called by PeerLearningService.create_study_group()
        WHY: Persists new study groups with all metadata

        Args:
            group: StudyGroup entity to persist

        Returns:
            Created StudyGroup with database-generated fields

        Raises:
            PeerLearningDAOException: On database errors
        """
        query = """
            INSERT INTO study_groups (
                id, name, description, course_id, track_id, organization_id,
                creator_id, status, is_public, min_members, max_members,
                current_member_count, meeting_schedule, meeting_platform,
                meeting_link, goals, tags, created_at, updated_at,
                activated_at, completed_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                $14, $15, $16, $17, $18, $19, $20, $21
            )
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    group.id, group.name, group.description, group.course_id,
                    group.track_id, group.organization_id, group.creator_id,
                    group.status.value, group.is_public, group.min_members,
                    group.max_members, group.current_member_count,
                    group.meeting_schedule, group.meeting_platform,
                    group.meeting_link, json.dumps(group.goals),
                    json.dumps(group.tags), group.created_at, group.updated_at,
                    group.activated_at, group.completed_at
                )
                logger.info(f"Created study group {group.id}: {group.name}")
                return self._row_to_study_group(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating study group: {e}")
            raise PeerLearningDAOException(
                f"Failed to create study group: {str(e)}"
            ) from e

    async def get_study_group_by_id(self, group_id: UUID) -> Optional[StudyGroup]:
        """
        WHAT: Retrieves a study group by ID with memberships
        WHERE: Called for group detail views
        WHY: Provides complete group data

        Args:
            group_id: UUID of the study group

        Returns:
            StudyGroup with memberships if found, None otherwise
        """
        query = "SELECT * FROM study_groups WHERE id = $1"
        members_query = """
            SELECT * FROM study_group_memberships
            WHERE study_group_id = $1 AND status = 'active'
            ORDER BY role, joined_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, group_id)
                if row is None:
                    return None

                group = self._row_to_study_group(row)

                member_rows = await conn.fetch(members_query, group_id)
                group.members = [self._row_to_membership(mr) for mr in member_rows]

                return group
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting study group {group_id}: {e}")
            raise PeerLearningDAOException(
                f"Failed to get study group: {str(e)}"
            ) from e

    async def get_study_groups_by_course(
        self,
        course_id: UUID,
        include_private: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[StudyGroup]:
        """
        WHAT: Retrieves study groups for a course
        WHERE: Called for course study groups listing
        WHY: Enables browsing available study groups

        Args:
            course_id: UUID of the course
            include_private: Whether to include private groups
            limit: Maximum groups to return
            offset: Pagination offset

        Returns:
            List of StudyGroup entities
        """
        if include_private:
            query = """
                SELECT * FROM study_groups
                WHERE course_id = $1 AND status IN ('forming', 'active')
                ORDER BY current_member_count DESC
                LIMIT $2 OFFSET $3
            """
            params = [course_id, limit, offset]
        else:
            query = """
                SELECT * FROM study_groups
                WHERE course_id = $1 AND status IN ('forming', 'active') AND is_public = true
                ORDER BY current_member_count DESC
                LIMIT $2 OFFSET $3
            """
            params = [course_id, limit, offset]

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [self._row_to_study_group(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting study groups for course {course_id}: {e}")
            raise PeerLearningDAOException(
                f"Failed to get study groups: {str(e)}"
            ) from e

    async def update_study_group(self, group: StudyGroup) -> StudyGroup:
        """
        WHAT: Updates an existing study group
        WHERE: Called after group modifications
        WHY: Persists group state changes

        Args:
            group: Updated StudyGroup entity

        Returns:
            Updated StudyGroup
        """
        query = """
            UPDATE study_groups SET
                name = $2, description = $3, status = $4, is_public = $5,
                min_members = $6, max_members = $7, current_member_count = $8,
                meeting_schedule = $9, meeting_platform = $10, meeting_link = $11,
                goals = $12, tags = $13, updated_at = $14, activated_at = $15,
                completed_at = $16
            WHERE id = $1
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    group.id, group.name, group.description, group.status.value,
                    group.is_public, group.min_members, group.max_members,
                    group.current_member_count, group.meeting_schedule,
                    group.meeting_platform, group.meeting_link,
                    json.dumps(group.goals), json.dumps(group.tags),
                    datetime.utcnow(), group.activated_at, group.completed_at
                )
                if row is None:
                    raise StudyGroupNotFoundException(f"Study group {group.id} not found")
                return self._row_to_study_group(row)
        except StudyGroupNotFoundException:
            raise
        except asyncpg.PostgresError as e:
            logger.error(f"Database error updating study group {group.id}: {e}")
            raise PeerLearningDAOException(
                f"Failed to update study group: {str(e)}"
            ) from e

    # =========================================================================
    # MEMBERSHIP OPERATIONS
    # =========================================================================

    async def create_membership(self, membership: StudyGroupMembership) -> StudyGroupMembership:
        """
        WHAT: Creates a study group membership
        WHERE: Called when user joins a group
        WHY: Persists membership records

        Args:
            membership: StudyGroupMembership to create

        Returns:
            Created StudyGroupMembership
        """
        query = """
            INSERT INTO study_group_memberships (
                id, study_group_id, user_id, role, status, contribution_score,
                sessions_attended, last_active_at, created_at, updated_at,
                joined_at, left_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    membership.id, membership.study_group_id, membership.user_id,
                    membership.role.value, membership.status.value,
                    membership.contribution_score, membership.sessions_attended,
                    membership.last_active_at, membership.created_at,
                    membership.updated_at, membership.joined_at, membership.left_at
                )
                logger.debug(f"Created membership {membership.id} for user {membership.user_id}")
                return self._row_to_membership(row)
        except asyncpg.UniqueViolationError:
            raise PeerLearningDAOException(
                f"User {membership.user_id} is already a member of this group"
            )
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating membership: {e}")
            raise PeerLearningDAOException(
                f"Failed to create membership: {str(e)}"
            ) from e

    async def update_membership(self, membership: StudyGroupMembership) -> StudyGroupMembership:
        """
        WHAT: Updates a membership record
        WHERE: Called on status/role changes
        WHY: Persists membership updates
        """
        query = """
            UPDATE study_group_memberships SET
                role = $2, status = $3, contribution_score = $4,
                sessions_attended = $5, last_active_at = $6, updated_at = $7,
                joined_at = $8, left_at = $9
            WHERE id = $1
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    membership.id, membership.role.value, membership.status.value,
                    membership.contribution_score, membership.sessions_attended,
                    membership.last_active_at, datetime.utcnow(),
                    membership.joined_at, membership.left_at
                )
                return self._row_to_membership(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error updating membership: {e}")
            raise PeerLearningDAOException(
                f"Failed to update membership: {str(e)}"
            ) from e

    async def get_user_memberships(
        self,
        user_id: UUID,
        active_only: bool = True
    ) -> List[StudyGroupMembership]:
        """
        WHAT: Gets all memberships for a user
        WHERE: Called for user's group listings
        WHY: Shows user's study groups
        """
        if active_only:
            query = """
                SELECT * FROM study_group_memberships
                WHERE user_id = $1 AND status = 'active'
                ORDER BY joined_at DESC
            """
        else:
            query = """
                SELECT * FROM study_group_memberships
                WHERE user_id = $1
                ORDER BY created_at DESC
            """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, user_id)
                return [self._row_to_membership(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting memberships for user {user_id}: {e}")
            raise PeerLearningDAOException(
                f"Failed to get memberships: {str(e)}"
            ) from e

    # =========================================================================
    # PEER REVIEW OPERATIONS
    # =========================================================================

    async def create_peer_review(self, review: PeerReview) -> PeerReview:
        """
        WHAT: Creates a peer review assignment
        WHERE: Called when assigning reviewers
        WHY: Persists review assignments
        """
        query = """
            INSERT INTO peer_reviews (
                id, assignment_id, submission_id, course_id, organization_id,
                author_id, reviewer_id, is_anonymous, status, overall_score,
                rubric_scores, strengths, improvements, detailed_feedback,
                assigned_at, due_at, started_at, submitted_at, quality_rating,
                helpfulness_score, reviewer_reputation_delta, time_spent_seconds,
                word_count, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25
            )
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    review.id, review.assignment_id, review.submission_id,
                    review.course_id, review.organization_id, review.author_id,
                    review.reviewer_id, review.is_anonymous, review.status.value,
                    float(review.overall_score) if review.overall_score else None,
                    json.dumps({k: float(v) for k, v in review.rubric_scores.items()}),
                    review.strengths, review.improvements, review.detailed_feedback,
                    review.assigned_at, review.due_at, review.started_at,
                    review.submitted_at,
                    review.quality_rating.value if review.quality_rating else None,
                    review.helpfulness_score, review.reviewer_reputation_delta,
                    review.time_spent_seconds, review.word_count,
                    review.created_at, review.updated_at
                )
                logger.info(f"Created peer review {review.id}")
                return self._row_to_peer_review(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating peer review: {e}")
            raise PeerLearningDAOException(
                f"Failed to create peer review: {str(e)}"
            ) from e

    async def get_peer_review_by_id(self, review_id: UUID) -> Optional[PeerReview]:
        """
        WHAT: Retrieves a peer review by ID
        WHERE: Called for review detail views
        WHY: Provides complete review data
        """
        query = "SELECT * FROM peer_reviews WHERE id = $1"
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, review_id)
                return self._row_to_peer_review(row) if row else None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting peer review {review_id}: {e}")
            raise PeerLearningDAOException(
                f"Failed to get peer review: {str(e)}"
            ) from e

    async def get_reviews_for_reviewer(
        self,
        reviewer_id: UUID,
        status: Optional[PeerReviewStatus] = None,
        limit: int = 50
    ) -> List[PeerReview]:
        """
        WHAT: Gets reviews assigned to a reviewer
        WHERE: Called for reviewer's dashboard
        WHY: Shows pending and completed reviews
        """
        if status:
            query = """
                SELECT * FROM peer_reviews
                WHERE reviewer_id = $1 AND status = $2
                ORDER BY due_at ASC
                LIMIT $3
            """
            params = [reviewer_id, status.value, limit]
        else:
            query = """
                SELECT * FROM peer_reviews
                WHERE reviewer_id = $1
                ORDER BY due_at ASC
                LIMIT $2
            """
            params = [reviewer_id, limit]

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [self._row_to_peer_review(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting reviews for reviewer: {e}")
            raise PeerLearningDAOException(
                f"Failed to get reviews: {str(e)}"
            ) from e

    async def update_peer_review(self, review: PeerReview) -> PeerReview:
        """
        WHAT: Updates a peer review
        WHERE: Called on review submission/status changes
        WHY: Persists review updates
        """
        query = """
            UPDATE peer_reviews SET
                status = $2, overall_score = $3, rubric_scores = $4,
                strengths = $5, improvements = $6, detailed_feedback = $7,
                started_at = $8, submitted_at = $9, quality_rating = $10,
                helpfulness_score = $11, reviewer_reputation_delta = $12,
                time_spent_seconds = $13, word_count = $14, updated_at = $15
            WHERE id = $1
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    review.id, review.status.value,
                    float(review.overall_score) if review.overall_score else None,
                    json.dumps({k: float(v) for k, v in review.rubric_scores.items()}),
                    review.strengths, review.improvements, review.detailed_feedback,
                    review.started_at, review.submitted_at,
                    review.quality_rating.value if review.quality_rating else None,
                    review.helpfulness_score, review.reviewer_reputation_delta,
                    review.time_spent_seconds, review.word_count, datetime.utcnow()
                )
                return self._row_to_peer_review(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error updating peer review: {e}")
            raise PeerLearningDAOException(
                f"Failed to update peer review: {str(e)}"
            ) from e

    # =========================================================================
    # DISCUSSION OPERATIONS
    # =========================================================================

    async def create_discussion_thread(self, thread: DiscussionThread) -> DiscussionThread:
        """
        WHAT: Creates a discussion thread
        WHERE: Called when user posts new thread
        WHY: Persists discussion threads
        """
        query = """
            INSERT INTO discussion_threads (
                id, title, content, author_id, course_id, study_group_id,
                organization_id, parent_thread_id, status, is_question,
                is_answered, is_pinned, best_answer_id, tags, view_count,
                reply_count, upvote_count, downvote_count, last_reply_at,
                last_reply_by, created_at, updated_at, edited_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23
            )
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    thread.id, thread.title, thread.content, thread.author_id,
                    thread.course_id, thread.study_group_id, thread.organization_id,
                    thread.parent_thread_id, thread.status.value, thread.is_question,
                    thread.is_answered, thread.is_pinned, thread.best_answer_id,
                    json.dumps(thread.tags), thread.view_count, thread.reply_count,
                    thread.upvote_count, thread.downvote_count, thread.last_reply_at,
                    thread.last_reply_by, thread.created_at, thread.updated_at,
                    thread.edited_at
                )
                logger.info(f"Created discussion thread {thread.id}: {thread.title}")
                return self._row_to_discussion_thread(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating discussion thread: {e}")
            raise PeerLearningDAOException(
                f"Failed to create discussion thread: {str(e)}"
            ) from e

    async def get_discussion_thread_by_id(
        self,
        thread_id: UUID,
        include_replies: bool = True
    ) -> Optional[DiscussionThread]:
        """
        WHAT: Retrieves a discussion thread by ID
        WHERE: Called for thread detail views
        WHY: Provides complete thread with replies
        """
        query = "SELECT * FROM discussion_threads WHERE id = $1"
        replies_query = """
            SELECT * FROM discussion_replies
            WHERE thread_id = $1 AND is_hidden = false
            ORDER BY created_at ASC
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, thread_id)
                if row is None:
                    return None

                thread = self._row_to_discussion_thread(row)

                if include_replies:
                    reply_rows = await conn.fetch(replies_query, thread_id)
                    thread.replies = [self._row_to_discussion_reply(rr) for rr in reply_rows]

                # Increment view count
                await conn.execute(
                    "UPDATE discussion_threads SET view_count = view_count + 1 WHERE id = $1",
                    thread_id
                )

                return thread
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting discussion thread: {e}")
            raise PeerLearningDAOException(
                f"Failed to get discussion thread: {str(e)}"
            ) from e

    async def get_threads_by_course(
        self,
        course_id: UUID,
        status: Optional[ThreadStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DiscussionThread]:
        """
        WHAT: Gets discussion threads for a course
        WHERE: Called for course forum listing
        WHY: Shows course discussions
        """
        if status:
            query = """
                SELECT * FROM discussion_threads
                WHERE course_id = $1 AND status = $2
                ORDER BY is_pinned DESC, last_reply_at DESC NULLS LAST
                LIMIT $3 OFFSET $4
            """
            params = [course_id, status.value, limit, offset]
        else:
            query = """
                SELECT * FROM discussion_threads
                WHERE course_id = $1 AND status NOT IN ('hidden', 'archived')
                ORDER BY is_pinned DESC, last_reply_at DESC NULLS LAST
                LIMIT $2 OFFSET $3
            """
            params = [course_id, limit, offset]

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [self._row_to_discussion_thread(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting threads: {e}")
            raise PeerLearningDAOException(
                f"Failed to get threads: {str(e)}"
            ) from e

    async def update_discussion_thread(self, thread: DiscussionThread) -> DiscussionThread:
        """
        WHAT: Updates a discussion thread
        WHERE: Called on thread edits/status changes
        WHY: Persists thread updates
        """
        query = """
            UPDATE discussion_threads SET
                title = $2, content = $3, status = $4, is_question = $5,
                is_answered = $6, is_pinned = $7, best_answer_id = $8,
                tags = $9, reply_count = $10, upvote_count = $11,
                downvote_count = $12, last_reply_at = $13, last_reply_by = $14,
                updated_at = $15, edited_at = $16
            WHERE id = $1
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    thread.id, thread.title, thread.content, thread.status.value,
                    thread.is_question, thread.is_answered, thread.is_pinned,
                    thread.best_answer_id, json.dumps(thread.tags), thread.reply_count,
                    thread.upvote_count, thread.downvote_count, thread.last_reply_at,
                    thread.last_reply_by, datetime.utcnow(), thread.edited_at
                )
                return self._row_to_discussion_thread(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error updating thread: {e}")
            raise PeerLearningDAOException(
                f"Failed to update thread: {str(e)}"
            ) from e

    async def create_discussion_reply(self, reply: DiscussionReply) -> DiscussionReply:
        """
        WHAT: Creates a reply to a discussion thread
        WHERE: Called when user posts reply
        WHY: Persists discussion replies
        """
        query = """
            INSERT INTO discussion_replies (
                id, thread_id, author_id, content, parent_reply_id,
                is_best_answer, upvote_count, downvote_count, is_edited,
                is_hidden, created_at, updated_at, edited_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    reply.id, reply.thread_id, reply.author_id, reply.content,
                    reply.parent_reply_id, reply.is_best_answer, reply.upvote_count,
                    reply.downvote_count, reply.is_edited, reply.is_hidden,
                    reply.created_at, reply.updated_at, reply.edited_at
                )
                return self._row_to_discussion_reply(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating reply: {e}")
            raise PeerLearningDAOException(
                f"Failed to create reply: {str(e)}"
            ) from e

    # =========================================================================
    # HELP REQUEST OPERATIONS
    # =========================================================================

    async def create_help_request(self, request: HelpRequest) -> HelpRequest:
        """
        WHAT: Creates a help request
        WHERE: Called when student needs peer help
        WHY: Persists help requests
        """
        query = """
            INSERT INTO help_requests (
                id, requester_id, title, description, category, skill_topic,
                course_id, organization_id, status, helper_id, is_anonymous,
                urgency, estimated_duration_minutes, actual_duration_minutes,
                resolution_notes, requester_rating, helper_rating, reputation_earned,
                created_at, updated_at, expires_at, claimed_at, session_started_at,
                resolved_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24
            )
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    request.id, request.requester_id, request.title,
                    request.description, request.category.value, request.skill_topic,
                    request.course_id, request.organization_id, request.status.value,
                    request.helper_id, request.is_anonymous, request.urgency,
                    request.estimated_duration_minutes, request.actual_duration_minutes,
                    request.resolution_notes, request.requester_rating,
                    request.helper_rating, request.reputation_earned,
                    request.created_at, request.updated_at, request.expires_at,
                    request.claimed_at, request.session_started_at, request.resolved_at
                )
                logger.info(f"Created help request {request.id}: {request.title}")
                return self._row_to_help_request(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error creating help request: {e}")
            raise PeerLearningDAOException(
                f"Failed to create help request: {str(e)}"
            ) from e

    async def get_help_request_by_id(self, request_id: UUID) -> Optional[HelpRequest]:
        """
        WHAT: Retrieves a help request by ID
        WHERE: Called for request detail views
        WHY: Provides complete request data
        """
        query = "SELECT * FROM help_requests WHERE id = $1"
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, request_id)
                return self._row_to_help_request(row) if row else None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting help request: {e}")
            raise PeerLearningDAOException(
                f"Failed to get help request: {str(e)}"
            ) from e

    async def get_open_help_requests(
        self,
        course_id: Optional[UUID] = None,
        category: Optional[HelpCategory] = None,
        limit: int = 50
    ) -> List[HelpRequest]:
        """
        WHAT: Gets open help requests
        WHERE: Called for helper matching
        WHY: Shows available requests for helpers
        """
        conditions = ["status = 'open'", "(expires_at IS NULL OR expires_at > NOW())"]
        params = []
        param_idx = 1

        if course_id:
            conditions.append(f"course_id = ${param_idx}")
            params.append(course_id)
            param_idx += 1

        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category.value)
            param_idx += 1

        params.append(limit)
        query = f"""
            SELECT * FROM help_requests
            WHERE {' AND '.join(conditions)}
            ORDER BY urgency DESC, created_at ASC
            LIMIT ${param_idx}
        """

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [self._row_to_help_request(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting help requests: {e}")
            raise PeerLearningDAOException(
                f"Failed to get help requests: {str(e)}"
            ) from e

    async def update_help_request(self, request: HelpRequest) -> HelpRequest:
        """
        WHAT: Updates a help request
        WHERE: Called on claim/resolve/status changes
        WHY: Persists request updates
        """
        query = """
            UPDATE help_requests SET
                status = $2, helper_id = $3, resolution_notes = $4,
                requester_rating = $5, helper_rating = $6, reputation_earned = $7,
                actual_duration_minutes = $8, updated_at = $9, claimed_at = $10,
                session_started_at = $11, resolved_at = $12
            WHERE id = $1
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    request.id, request.status.value, request.helper_id,
                    request.resolution_notes, request.requester_rating,
                    request.helper_rating, request.reputation_earned,
                    request.actual_duration_minutes, datetime.utcnow(),
                    request.claimed_at, request.session_started_at, request.resolved_at
                )
                if row is None:
                    raise HelpRequestNotFoundException(f"Help request {request.id} not found")
                return self._row_to_help_request(row)
        except HelpRequestNotFoundException:
            raise
        except asyncpg.PostgresError as e:
            logger.error(f"Database error updating help request: {e}")
            raise PeerLearningDAOException(
                f"Failed to update help request: {str(e)}"
            ) from e

    # =========================================================================
    # REPUTATION OPERATIONS
    # =========================================================================

    async def upsert_reputation(self, reputation: PeerReputation) -> PeerReputation:
        """
        WHAT: Creates or updates peer reputation
        WHERE: Called after peer interactions
        WHY: Maintains reputation tracking
        """
        query = """
            INSERT INTO peer_reputations (
                id, user_id, organization_id, overall_score, review_score,
                help_score, discussion_score, group_score, reviews_given,
                reviews_received, help_sessions_given, help_sessions_received,
                discussions_started, helpful_answers, level, badges,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            ON CONFLICT (user_id, organization_id)
            DO UPDATE SET
                overall_score = EXCLUDED.overall_score,
                review_score = EXCLUDED.review_score,
                help_score = EXCLUDED.help_score,
                discussion_score = EXCLUDED.discussion_score,
                group_score = EXCLUDED.group_score,
                reviews_given = EXCLUDED.reviews_given,
                reviews_received = EXCLUDED.reviews_received,
                help_sessions_given = EXCLUDED.help_sessions_given,
                help_sessions_received = EXCLUDED.help_sessions_received,
                discussions_started = EXCLUDED.discussions_started,
                helpful_answers = EXCLUDED.helpful_answers,
                level = EXCLUDED.level,
                badges = EXCLUDED.badges,
                updated_at = NOW()
            RETURNING *
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    reputation.id, reputation.user_id, reputation.organization_id,
                    reputation.overall_score, reputation.review_score,
                    reputation.help_score, reputation.discussion_score,
                    reputation.group_score, reputation.reviews_given,
                    reputation.reviews_received, reputation.help_sessions_given,
                    reputation.help_sessions_received, reputation.discussions_started,
                    reputation.helpful_answers, reputation.level,
                    json.dumps(reputation.badges), reputation.created_at,
                    reputation.updated_at
                )
                return self._row_to_reputation(row)
        except asyncpg.PostgresError as e:
            logger.error(f"Database error upserting reputation: {e}")
            raise PeerLearningDAOException(
                f"Failed to upsert reputation: {str(e)}"
            ) from e

    async def get_reputation_by_user(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None
    ) -> Optional[PeerReputation]:
        """
        WHAT: Gets reputation for a user
        WHERE: Called for profile displays
        WHY: Shows user's peer learning reputation
        """
        if organization_id:
            query = """
                SELECT * FROM peer_reputations
                WHERE user_id = $1 AND organization_id = $2
            """
            params = [user_id, organization_id]
        else:
            query = """
                SELECT * FROM peer_reputations
                WHERE user_id = $1
                ORDER BY overall_score DESC
                LIMIT 1
            """
            params = [user_id]

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                return self._row_to_reputation(row) if row else None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error getting reputation: {e}")
            raise PeerLearningDAOException(
                f"Failed to get reputation: {str(e)}"
            ) from e

    # =========================================================================
    # ROW CONVERSION METHODS
    # =========================================================================

    def _row_to_study_group(self, row: asyncpg.Record) -> StudyGroup:
        """Converts database row to StudyGroup entity"""
        goals = row['goals'] if isinstance(row['goals'], list) else json.loads(row['goals'] or '[]')
        tags = row['tags'] if isinstance(row['tags'], list) else json.loads(row['tags'] or '[]')

        return StudyGroup(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            course_id=row['course_id'],
            track_id=row['track_id'],
            organization_id=row['organization_id'],
            creator_id=row['creator_id'],
            status=StudyGroupStatus(row['status']),
            is_public=row['is_public'],
            min_members=row['min_members'],
            max_members=row['max_members'],
            current_member_count=row['current_member_count'],
            meeting_schedule=row['meeting_schedule'],
            meeting_platform=row['meeting_platform'],
            meeting_link=row['meeting_link'],
            goals=goals,
            tags=tags,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            activated_at=row['activated_at'],
            completed_at=row['completed_at']
        )

    def _row_to_membership(self, row: asyncpg.Record) -> StudyGroupMembership:
        """Converts database row to StudyGroupMembership entity"""
        return StudyGroupMembership(
            id=row['id'],
            study_group_id=row['study_group_id'],
            user_id=row['user_id'],
            role=MembershipRole(row['role']),
            status=MembershipStatus(row['status']),
            joined_at=row['joined_at'],
            left_at=row['left_at'],
            last_active_at=row['last_active_at'],
            contribution_score=row['contribution_score'],
            sessions_attended=row['sessions_attended'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_peer_review(self, row: asyncpg.Record) -> PeerReview:
        """Converts database row to PeerReview entity"""
        rubric = row['rubric_scores']
        if isinstance(rubric, str):
            rubric = json.loads(rubric or '{}')
        rubric_scores = {k: Decimal(str(v)) for k, v in (rubric or {}).items()}

        return PeerReview(
            id=row['id'],
            assignment_id=row['assignment_id'],
            submission_id=row['submission_id'],
            author_id=row['author_id'],
            reviewer_id=row['reviewer_id'],
            course_id=row['course_id'],
            organization_id=row['organization_id'],
            is_anonymous=row['is_anonymous'],
            status=PeerReviewStatus(row['status']),
            overall_score=Decimal(str(row['overall_score'])) if row['overall_score'] else None,
            rubric_scores=rubric_scores,
            strengths=row['strengths'],
            improvements=row['improvements'],
            detailed_feedback=row['detailed_feedback'],
            assigned_at=row['assigned_at'],
            due_at=row['due_at'],
            started_at=row['started_at'],
            submitted_at=row['submitted_at'],
            quality_rating=ReviewQuality(row['quality_rating']) if row['quality_rating'] else None,
            helpfulness_score=row['helpfulness_score'],
            reviewer_reputation_delta=row['reviewer_reputation_delta'],
            time_spent_seconds=row['time_spent_seconds'],
            word_count=row['word_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_discussion_thread(self, row: asyncpg.Record) -> DiscussionThread:
        """Converts database row to DiscussionThread entity"""
        tags = row['tags'] if isinstance(row['tags'], list) else json.loads(row['tags'] or '[]')

        return DiscussionThread(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            author_id=row['author_id'],
            course_id=row['course_id'],
            study_group_id=row['study_group_id'],
            organization_id=row['organization_id'],
            parent_thread_id=row['parent_thread_id'],
            status=ThreadStatus(row['status']),
            is_question=row['is_question'],
            is_answered=row['is_answered'],
            is_pinned=row['is_pinned'],
            best_answer_id=row['best_answer_id'],
            tags=tags,
            view_count=row['view_count'],
            reply_count=row['reply_count'],
            upvote_count=row['upvote_count'],
            downvote_count=row['downvote_count'],
            last_reply_at=row['last_reply_at'],
            last_reply_by=row['last_reply_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            edited_at=row['edited_at']
        )

    def _row_to_discussion_reply(self, row: asyncpg.Record) -> DiscussionReply:
        """Converts database row to DiscussionReply entity"""
        return DiscussionReply(
            id=row['id'],
            thread_id=row['thread_id'],
            author_id=row['author_id'],
            content=row['content'],
            parent_reply_id=row['parent_reply_id'],
            is_best_answer=row['is_best_answer'],
            upvote_count=row['upvote_count'],
            downvote_count=row['downvote_count'],
            is_edited=row['is_edited'],
            is_hidden=row['is_hidden'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            edited_at=row['edited_at']
        )

    def _row_to_help_request(self, row: asyncpg.Record) -> HelpRequest:
        """Converts database row to HelpRequest entity"""
        return HelpRequest(
            id=row['id'],
            requester_id=row['requester_id'],
            title=row['title'],
            description=row['description'],
            category=HelpCategory(row['category']),
            skill_topic=row['skill_topic'],
            course_id=row['course_id'],
            organization_id=row['organization_id'],
            status=HelpRequestStatus(row['status']),
            helper_id=row['helper_id'],
            is_anonymous=row['is_anonymous'],
            urgency=row['urgency'],
            estimated_duration_minutes=row['estimated_duration_minutes'],
            actual_duration_minutes=row['actual_duration_minutes'],
            resolved_at=row['resolved_at'],
            resolution_notes=row['resolution_notes'],
            requester_rating=row['requester_rating'],
            helper_rating=row['helper_rating'],
            reputation_earned=row['reputation_earned'],
            expires_at=row['expires_at'],
            claimed_at=row['claimed_at'],
            session_started_at=row['session_started_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_reputation(self, row: asyncpg.Record) -> PeerReputation:
        """Converts database row to PeerReputation entity"""
        badges = row['badges'] if isinstance(row['badges'], list) else json.loads(row['badges'] or '[]')

        return PeerReputation(
            id=row['id'],
            user_id=row['user_id'],
            organization_id=row['organization_id'],
            overall_score=row['overall_score'],
            review_score=row['review_score'],
            help_score=row['help_score'],
            discussion_score=row['discussion_score'],
            group_score=row['group_score'],
            reviews_given=row['reviews_given'],
            reviews_received=row['reviews_received'],
            help_sessions_given=row['help_sessions_given'],
            help_sessions_received=row['help_sessions_received'],
            discussions_started=row['discussions_started'],
            helpful_answers=row['helpful_answers'],
            level=row['level'],
            badges=badges,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
