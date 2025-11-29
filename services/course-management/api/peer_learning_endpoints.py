"""
Peer Learning API Endpoints

WHAT: REST API endpoints for peer learning system
WHERE: services/course-management/api/peer_learning_endpoints.py
WHY: Provides HTTP interface for collaborative learning features

BUSINESS CONTEXT:
This module exposes endpoints for peer learning features including:
- Study group management (create, join, leave, browse)
- Peer review workflows (assign, submit, rate)
- Discussion forums (threads, replies, voting)
- Help requests (create, claim, resolve)
- Reputation tracking and leaderboards

ARCHITECTURAL PRINCIPLES:
- Single Responsibility: Only peer learning endpoints
- Dependency Inversion: Depends on service abstractions
- Interface Segregation: Focused, role-specific endpoints

AUTHENTICATION:
All endpoints require JWT authentication. User context determines
accessible content (users see own groups, reviews, and requests).

@module api/peer_learning_endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging
import sys
import os
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

# JWT Authentication
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth import get_current_user_id as get_authenticated_user_id

# Domain entities
from course_management.domain.entities.peer_learning import (
    StudyGroup, StudyGroupMembership, PeerReview, DiscussionThread,
    DiscussionReply, HelpRequest, PeerReputation, StudyGroupStatus,
    MembershipRole, MembershipStatus, PeerReviewStatus, ReviewQuality,
    ThreadStatus, HelpRequestStatus, HelpCategory,
    StudyGroupNotFoundException, StudyGroupFullException,
    NotGroupMemberException, InsufficientPermissionException,
    ReviewAssignmentException, HelpRequestNotFoundException
)

# Application services
from course_management.application.services.peer_learning_service import (
    PeerLearningService,
    PeerLearningServiceException
)

logger = logging.getLogger(__name__)


# =============================================================================
# API MODELS (DTOs)
# =============================================================================

# Study Group DTOs
class StudyGroupCreateDTO(BaseModel):
    """
    WHAT: DTO for creating a new study group
    WHERE: POST /study-groups
    WHY: Captures required fields for group creation
    """
    name: str = Field(..., min_length=1, max_length=200, description="Group name")
    course_id: str = Field(..., description="Course this group is studying")
    description: Optional[str] = Field(None, max_length=2000, description="Group description")
    track_id: Optional[str] = Field(None, description="Optional track context")
    is_public: bool = Field(default=True, description="Whether group is discoverable")
    max_members: int = Field(default=10, ge=2, le=50, description="Maximum members")
    min_members: int = Field(default=2, ge=2, le=10, description="Minimum for activation")
    meeting_schedule: Optional[str] = Field(None, max_length=500, description="Meeting schedule")
    meeting_platform: Optional[str] = Field(None, max_length=100, description="Meeting platform")
    goals: Optional[List[str]] = Field(None, description="Learning goals")
    tags: Optional[List[str]] = Field(None, description="Discovery tags")


class StudyGroupResponseDTO(BaseModel):
    """
    WHAT: DTO for study group API responses
    WHERE: All study group GET endpoints
    WHY: Provides consistent response structure
    """
    id: str
    name: str
    description: Optional[str]
    course_id: str
    track_id: Optional[str]
    organization_id: Optional[str]
    creator_id: str
    status: str
    is_public: bool
    min_members: int
    max_members: int
    current_member_count: int
    meeting_schedule: Optional[str]
    meeting_platform: Optional[str]
    meeting_link: Optional[str]
    goals: List[str]
    tags: List[str]
    created_at: datetime
    activated_at: Optional[datetime]


class StudyGroupMemberDTO(BaseModel):
    """
    WHAT: DTO for study group membership responses
    WHERE: GET /study-groups/{id}/members
    WHY: Shows member details
    """
    id: str
    user_id: str
    role: str
    status: str
    joined_at: Optional[datetime]
    contribution_score: int
    sessions_attended: int
    last_active_at: Optional[datetime]


# Peer Review DTOs
class PeerReviewAssignDTO(BaseModel):
    """
    WHAT: DTO for assigning a peer review
    WHERE: POST /peer-reviews/assign
    WHY: Captures assignment details
    """
    assignment_id: str = Field(..., description="Assignment ID")
    submission_id: str = Field(..., description="Submission to review")
    author_id: str = Field(..., description="Submission author")
    reviewer_id: str = Field(..., description="Assigned reviewer")
    course_id: str = Field(..., description="Course context")
    due_at: Optional[datetime] = Field(None, description="Review deadline")
    is_anonymous: bool = Field(default=True, description="Hide author identity")


class PeerReviewSubmitDTO(BaseModel):
    """
    WHAT: DTO for submitting a peer review
    WHERE: POST /peer-reviews/{id}/submit
    WHY: Captures review feedback
    """
    overall_score: float = Field(..., ge=0, le=100, description="Overall score")
    strengths: str = Field(..., min_length=10, max_length=2000, description="Identified strengths")
    improvements: str = Field(..., min_length=10, max_length=2000, description="Areas for improvement")
    detailed_feedback: Optional[str] = Field(None, max_length=5000, description="Additional feedback")
    rubric_scores: Optional[dict] = Field(None, description="Per-criterion scores")


class PeerReviewRateDTO(BaseModel):
    """
    WHAT: DTO for rating a peer review
    WHERE: POST /peer-reviews/{id}/rate
    WHY: Quality feedback on reviews
    """
    quality_rating: str = Field(
        ...,
        pattern="^(excellent|good|fair|poor|unhelpful)$",
        description="Quality assessment"
    )
    helpfulness_score: int = Field(..., ge=1, le=5, description="Helpfulness 1-5")


class PeerReviewResponseDTO(BaseModel):
    """
    WHAT: DTO for peer review API responses
    WHERE: All peer review endpoints
    WHY: Provides consistent response structure
    """
    id: str
    assignment_id: str
    submission_id: str
    reviewer_id: str
    course_id: str
    is_anonymous: bool
    status: str
    overall_score: Optional[float]
    strengths: Optional[str]
    improvements: Optional[str]
    detailed_feedback: Optional[str]
    assigned_at: datetime
    due_at: Optional[datetime]
    submitted_at: Optional[datetime]
    quality_rating: Optional[str]
    helpfulness_score: Optional[int]


# Discussion DTOs
class DiscussionThreadCreateDTO(BaseModel):
    """
    WHAT: DTO for creating a discussion thread
    WHERE: POST /discussions
    WHY: Captures thread creation fields
    """
    title: str = Field(..., min_length=5, max_length=300, description="Thread title")
    content: str = Field(..., min_length=10, max_length=10000, description="Thread content")
    course_id: str = Field(..., description="Course context")
    is_question: bool = Field(default=False, description="Is this a Q&A thread")
    study_group_id: Optional[str] = Field(None, description="Optional study group context")
    tags: Optional[List[str]] = Field(None, description="Topic tags")


class DiscussionReplyDTO(BaseModel):
    """
    WHAT: DTO for posting a reply
    WHERE: POST /discussions/{id}/replies
    WHY: Captures reply content
    """
    content: str = Field(..., min_length=5, max_length=5000, description="Reply content")
    parent_reply_id: Optional[str] = Field(None, description="For nested replies")


class DiscussionThreadResponseDTO(BaseModel):
    """
    WHAT: DTO for discussion thread responses
    WHERE: All discussion endpoints
    WHY: Provides consistent response structure
    """
    id: str
    title: str
    content: str
    author_id: str
    course_id: str
    study_group_id: Optional[str]
    status: str
    is_question: bool
    is_answered: bool
    is_pinned: bool
    best_answer_id: Optional[str]
    tags: List[str]
    view_count: int
    reply_count: int
    upvote_count: int
    downvote_count: int
    created_at: datetime
    last_reply_at: Optional[datetime]


class DiscussionReplyResponseDTO(BaseModel):
    """
    WHAT: DTO for reply responses
    WHERE: Discussion reply endpoints
    WHY: Shows reply details
    """
    id: str
    thread_id: str
    author_id: str
    content: str
    parent_reply_id: Optional[str]
    is_best_answer: bool
    upvote_count: int
    downvote_count: int
    is_edited: bool
    created_at: datetime
    edited_at: Optional[datetime]


# Help Request DTOs
class HelpRequestCreateDTO(BaseModel):
    """
    WHAT: DTO for creating a help request
    WHERE: POST /help-requests
    WHY: Captures help request details
    """
    title: str = Field(..., min_length=5, max_length=200, description="Brief description")
    description: str = Field(..., min_length=20, max_length=5000, description="Detailed description")
    category: str = Field(
        ...,
        pattern="^(concept_clarification|problem_solving|code_review|study_partner|exam_prep|project_help|general)$",
        description="Help category"
    )
    course_id: str = Field(..., description="Course context")
    skill_topic: Optional[str] = Field(None, max_length=200, description="Specific topic")
    is_anonymous: bool = Field(default=False, description="Hide requester identity")
    urgency: int = Field(default=5, ge=1, le=10, description="Priority 1-10")
    estimated_duration_minutes: int = Field(default=30, ge=5, le=180, description="Expected time needed")
    expires_in_hours: int = Field(default=24, ge=1, le=168, description="Hours until expiry")


class HelpRequestResolveDTO(BaseModel):
    """
    WHAT: DTO for resolving a help request
    WHERE: POST /help-requests/{id}/resolve
    WHY: Captures resolution details
    """
    resolution_notes: str = Field(..., min_length=10, max_length=2000, description="How help was provided")
    actual_duration_minutes: int = Field(..., ge=1, description="Actual time spent")


class HelpRequestRateDTO(BaseModel):
    """
    WHAT: DTO for rating a help session
    WHERE: POST /help-requests/{id}/rate
    WHY: Captures session feedback
    """
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    is_helper_rating: bool = Field(..., description="True=rating helper, False=rating requester")


class HelpRequestResponseDTO(BaseModel):
    """
    WHAT: DTO for help request responses
    WHERE: All help request endpoints
    WHY: Provides consistent response structure
    """
    id: str
    requester_id: str
    title: str
    description: str
    category: str
    skill_topic: Optional[str]
    course_id: str
    status: str
    helper_id: Optional[str]
    is_anonymous: bool
    urgency: int
    estimated_duration_minutes: int
    actual_duration_minutes: Optional[int]
    resolution_notes: Optional[str]
    requester_rating: Optional[int]
    helper_rating: Optional[int]
    expires_at: Optional[datetime]
    created_at: datetime
    claimed_at: Optional[datetime]
    resolved_at: Optional[datetime]


# Reputation DTOs
class PeerReputationResponseDTO(BaseModel):
    """
    WHAT: DTO for reputation responses
    WHERE: GET /reputation
    WHY: Shows peer learning standing
    """
    id: str
    user_id: str
    organization_id: Optional[str]
    overall_score: int
    review_score: int
    help_score: int
    discussion_score: int
    group_score: int
    reviews_given: int
    reviews_received: int
    help_sessions_given: int
    help_sessions_received: int
    discussions_started: int
    helpful_answers: int
    level: int
    badges: List[str]


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(tags=["peer-learning"])


def get_peer_learning_service() -> PeerLearningService:
    """
    WHAT: Dependency injection for peer learning service
    WHERE: Used by all endpoints
    WHY: Retrieves service from container for proper lifecycle management
    """
    from main import app
    if not app or not hasattr(app.state, 'container') or not app.state.container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return app.state.container.get_peer_learning_service()


# JWT-authenticated user ID extraction
get_current_user_id = get_authenticated_user_id


# =============================================================================
# STUDY GROUP ENDPOINTS
# =============================================================================

@router.post("/study-groups", response_model=StudyGroupResponseDTO)
async def create_study_group(
    request: StudyGroupCreateDTO,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Create a new study group
    WHERE: POST /study-groups
    WHY: Enables students to form collaborative learning groups

    Creates a study group for the course, with the creator as owner.
    The group starts in FORMING status until minimum members join.
    """
    try:
        group = await service.create_study_group(
            creator_id=UUID(user_id),
            name=request.name,
            course_id=UUID(request.course_id),
            description=request.description,
            track_id=UUID(request.track_id) if request.track_id else None,
            is_public=request.is_public,
            max_members=request.max_members,
            min_members=request.min_members,
            meeting_schedule=request.meeting_schedule,
            meeting_platform=request.meeting_platform,
            goals=request.goals,
            tags=request.tags
        )
        return _study_group_to_response(group)

    except PeerLearningServiceException as e:
        logger.error(f"Error creating study group: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating study group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create study group")


@router.get("/study-groups", response_model=List[StudyGroupResponseDTO])
async def browse_study_groups(
    course_id: str = Query(..., description="Course to browse groups for"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Browse available study groups for a course
    WHERE: GET /study-groups
    WHY: Enables students to discover and join groups
    """
    try:
        groups = await service.browse_study_groups(
            course_id=UUID(course_id),
            user_id=UUID(user_id),
            limit=limit,
            offset=offset
        )
        return [_study_group_to_response(g) for g in groups]

    except PeerLearningServiceException as e:
        logger.error(f"Error browsing study groups: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/study-groups/my-groups", response_model=List[StudyGroupResponseDTO])
async def get_my_study_groups(
    active_only: bool = Query(default=True),
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Get study groups the user is a member of
    WHERE: GET /study-groups/my-groups
    WHY: Shows user's collaborative learning groups
    """
    try:
        groups = await service.get_user_study_groups(
            user_id=UUID(user_id),
            active_only=active_only
        )
        return [_study_group_to_response(g) for g in groups]

    except PeerLearningServiceException as e:
        logger.error(f"Error getting user study groups: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/study-groups/{group_id}", response_model=StudyGroupResponseDTO)
async def get_study_group(
    group_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Get a specific study group by ID
    WHERE: GET /study-groups/{group_id}
    WHY: Retrieve detailed group information
    """
    try:
        group = await service.get_study_group(UUID(group_id))
        return _study_group_to_response(group)

    except StudyGroupNotFoundException:
        raise HTTPException(status_code=404, detail="Study group not found")
    except PeerLearningServiceException as e:
        logger.error(f"Error getting study group: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/study-groups/{group_id}/join", response_model=StudyGroupMemberDTO)
async def join_study_group(
    group_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Join a study group
    WHERE: POST /study-groups/{group_id}/join
    WHY: Enables participation in collaborative learning
    """
    try:
        membership = await service.join_study_group(
            group_id=UUID(group_id),
            user_id=UUID(user_id)
        )
        return _membership_to_response(membership)

    except StudyGroupNotFoundException:
        raise HTTPException(status_code=404, detail="Study group not found")
    except StudyGroupFullException:
        raise HTTPException(status_code=400, detail="Study group is full")
    except PeerLearningServiceException as e:
        logger.error(f"Error joining study group: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/study-groups/{group_id}/leave")
async def leave_study_group(
    group_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Leave a study group
    WHERE: POST /study-groups/{group_id}/leave
    WHY: Allows members to exit groups
    """
    try:
        await service.leave_study_group(
            group_id=UUID(group_id),
            user_id=UUID(user_id)
        )
        return {"message": "Successfully left study group"}

    except StudyGroupNotFoundException:
        raise HTTPException(status_code=404, detail="Study group not found")
    except NotGroupMemberException:
        raise HTTPException(status_code=400, detail="Not a member of this group")
    except InsufficientPermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PeerLearningServiceException as e:
        logger.error(f"Error leaving study group: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# PEER REVIEW ENDPOINTS
# =============================================================================

@router.post("/peer-reviews/assign", response_model=PeerReviewResponseDTO)
async def assign_peer_review(
    request: PeerReviewAssignDTO,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Assign a peer review to a student
    WHERE: POST /peer-reviews/assign
    WHY: Enables peer assessment of student work

    Note: This is typically called by instructors or automated assignment systems.
    """
    try:
        review = await service.assign_peer_review(
            assignment_id=UUID(request.assignment_id),
            submission_id=UUID(request.submission_id),
            author_id=UUID(request.author_id),
            reviewer_id=UUID(request.reviewer_id),
            course_id=UUID(request.course_id),
            due_at=request.due_at,
            is_anonymous=request.is_anonymous
        )
        return _peer_review_to_response(review)

    except ReviewAssignmentException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PeerLearningServiceException as e:
        logger.error(f"Error assigning peer review: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/peer-reviews/pending", response_model=List[PeerReviewResponseDTO])
async def get_pending_reviews(
    limit: int = Query(default=50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Get pending peer review assignments
    WHERE: GET /peer-reviews/pending
    WHY: Shows outstanding review tasks
    """
    try:
        reviews = await service.get_pending_reviews(
            reviewer_id=UUID(user_id),
            limit=limit
        )
        return [_peer_review_to_response(r) for r in reviews]

    except PeerLearningServiceException as e:
        logger.error(f"Error getting pending reviews: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/peer-reviews/{review_id}/start", response_model=PeerReviewResponseDTO)
async def start_peer_review(
    review_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Mark a peer review as started
    WHERE: POST /peer-reviews/{review_id}/start
    WHY: Tracks review progress and timing
    """
    try:
        review = await service.start_peer_review(
            review_id=UUID(review_id),
            reviewer_id=UUID(user_id)
        )
        return _peer_review_to_response(review)

    except InsufficientPermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PeerLearningServiceException as e:
        logger.error(f"Error starting peer review: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/peer-reviews/{review_id}/submit", response_model=PeerReviewResponseDTO)
async def submit_peer_review(
    review_id: str,
    request: PeerReviewSubmitDTO,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Submit a completed peer review
    WHERE: POST /peer-reviews/{review_id}/submit
    WHY: Records peer assessment and updates reputation
    """
    try:
        rubric_scores = None
        if request.rubric_scores:
            rubric_scores = {k: Decimal(str(v)) for k, v in request.rubric_scores.items()}

        review = await service.submit_peer_review(
            review_id=UUID(review_id),
            reviewer_id=UUID(user_id),
            overall_score=Decimal(str(request.overall_score)),
            strengths=request.strengths,
            improvements=request.improvements,
            detailed_feedback=request.detailed_feedback,
            rubric_scores=rubric_scores
        )
        return _peer_review_to_response(review)

    except InsufficientPermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PeerLearningServiceException as e:
        logger.error(f"Error submitting peer review: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/peer-reviews/{review_id}/rate", response_model=PeerReviewResponseDTO)
async def rate_peer_review(
    review_id: str,
    request: PeerReviewRateDTO,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Rate the quality of a received peer review
    WHERE: POST /peer-reviews/{review_id}/rate
    WHY: Provides feedback for quality improvement
    """
    try:
        review = await service.rate_peer_review(
            review_id=UUID(review_id),
            author_id=UUID(user_id),
            quality_rating=ReviewQuality(request.quality_rating),
            helpfulness_score=request.helpfulness_score
        )
        return _peer_review_to_response(review)

    except InsufficientPermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PeerLearningServiceException as e:
        logger.error(f"Error rating peer review: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# DISCUSSION ENDPOINTS
# =============================================================================

@router.post("/discussions", response_model=DiscussionThreadResponseDTO)
async def create_discussion_thread(
    request: DiscussionThreadCreateDTO,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Create a new discussion thread
    WHERE: POST /discussions
    WHY: Enables asynchronous peer discussions
    """
    try:
        thread = await service.create_discussion_thread(
            author_id=UUID(user_id),
            title=request.title,
            content=request.content,
            course_id=UUID(request.course_id),
            is_question=request.is_question,
            study_group_id=UUID(request.study_group_id) if request.study_group_id else None,
            tags=request.tags
        )
        return _discussion_thread_to_response(thread)

    except PeerLearningServiceException as e:
        logger.error(f"Error creating discussion thread: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/discussions", response_model=List[DiscussionThreadResponseDTO])
async def browse_discussions(
    course_id: str = Query(..., description="Course to browse discussions for"),
    status: Optional[str] = Query(
        None,
        pattern="^(open|closed|hidden|archived)$"
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Browse discussion threads for a course
    WHERE: GET /discussions
    WHY: Enables course discussion forum
    """
    try:
        status_filter = ThreadStatus(status) if status else None
        threads = await service.browse_discussions(
            course_id=UUID(course_id),
            status=status_filter,
            limit=limit,
            offset=offset
        )
        return [_discussion_thread_to_response(t) for t in threads]

    except PeerLearningServiceException as e:
        logger.error(f"Error browsing discussions: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/discussions/{thread_id}", response_model=DiscussionThreadResponseDTO)
async def get_discussion_thread(
    thread_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Get a discussion thread with replies
    WHERE: GET /discussions/{thread_id}
    WHY: Displays thread content and conversation
    """
    try:
        thread = await service.get_discussion_thread(UUID(thread_id))
        return _discussion_thread_to_response(thread)

    except PeerLearningServiceException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Thread not found")
        logger.error(f"Error getting discussion thread: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/discussions/{thread_id}/replies", response_model=List[DiscussionReplyResponseDTO])
async def get_thread_replies(
    thread_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Get replies for a discussion thread
    WHERE: GET /discussions/{thread_id}/replies
    WHY: Loads thread conversation
    """
    try:
        thread = await service.get_discussion_thread(UUID(thread_id))
        return [_discussion_reply_to_response(r) for r in thread.replies]

    except PeerLearningServiceException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Thread not found")
        logger.error(f"Error getting thread replies: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/discussions/{thread_id}/replies", response_model=DiscussionReplyResponseDTO)
async def post_reply(
    thread_id: str,
    request: DiscussionReplyDTO,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Post a reply to a discussion thread
    WHERE: POST /discussions/{thread_id}/replies
    WHY: Enables threaded conversations
    """
    try:
        reply = await service.reply_to_discussion(
            thread_id=UUID(thread_id),
            author_id=UUID(user_id),
            content=request.content,
            parent_reply_id=UUID(request.parent_reply_id) if request.parent_reply_id else None
        )
        return _discussion_reply_to_response(reply)

    except PeerLearningServiceException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Thread not found")
        logger.error(f"Error posting reply: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/discussions/{thread_id}/vote")
async def vote_on_thread(
    thread_id: str,
    is_upvote: bool = Query(..., description="True for upvote, False for downvote"),
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Upvote or downvote a discussion thread
    WHERE: POST /discussions/{thread_id}/vote
    WHY: Community quality signals
    """
    try:
        thread = await service.vote_on_thread(
            thread_id=UUID(thread_id),
            user_id=UUID(user_id),
            is_upvote=is_upvote
        )
        return {
            "message": "Vote recorded",
            "upvotes": thread.upvote_count,
            "downvotes": thread.downvote_count
        }

    except PeerLearningServiceException as e:
        logger.error(f"Error voting on thread: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/discussions/{thread_id}/best-answer/{reply_id}")
async def mark_best_answer(
    thread_id: str,
    reply_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Mark a reply as the best answer
    WHERE: POST /discussions/{thread_id}/best-answer/{reply_id}
    WHY: Highlights helpful answers in Q&A
    """
    try:
        thread = await service.mark_best_answer(
            thread_id=UUID(thread_id),
            reply_id=UUID(reply_id),
            author_id=UUID(user_id)
        )
        return {
            "message": "Best answer marked",
            "best_answer_id": str(thread.best_answer_id)
        }

    except InsufficientPermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PeerLearningServiceException as e:
        logger.error(f"Error marking best answer: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# HELP REQUEST ENDPOINTS
# =============================================================================

@router.post("/help-requests", response_model=HelpRequestResponseDTO)
async def create_help_request(
    request: HelpRequestCreateDTO,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Create a help request for peer assistance
    WHERE: POST /help-requests
    WHY: Enables students to request help from peers
    """
    try:
        help_request = await service.create_help_request(
            requester_id=UUID(user_id),
            title=request.title,
            description=request.description,
            category=HelpCategory(request.category),
            course_id=UUID(request.course_id),
            skill_topic=request.skill_topic,
            is_anonymous=request.is_anonymous,
            urgency=request.urgency,
            estimated_duration_minutes=request.estimated_duration_minutes,
            expires_in_hours=request.expires_in_hours
        )
        return _help_request_to_response(help_request)

    except PeerLearningServiceException as e:
        logger.error(f"Error creating help request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/help-requests", response_model=List[HelpRequestResponseDTO])
async def browse_help_requests(
    course_id: Optional[str] = Query(None, description="Filter by course"),
    category: Optional[str] = Query(
        None,
        pattern="^(concept_clarification|problem_solving|code_review|study_partner|exam_prep|project_help|general)$"
    ),
    limit: int = Query(default=50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Browse open help requests
    WHERE: GET /help-requests
    WHY: Enables helpers to find requests
    """
    try:
        category_filter = HelpCategory(category) if category else None
        course_filter = UUID(course_id) if course_id else None

        requests = await service.browse_help_requests(
            course_id=course_filter,
            category=category_filter,
            limit=limit
        )
        return [_help_request_to_response(r) for r in requests]

    except PeerLearningServiceException as e:
        logger.error(f"Error browsing help requests: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/help-requests/{request_id}/claim", response_model=HelpRequestResponseDTO)
async def claim_help_request(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Claim a help request as helper
    WHERE: POST /help-requests/{request_id}/claim
    WHY: Assigns helper to requester
    """
    try:
        help_request = await service.claim_help_request(
            request_id=UUID(request_id),
            helper_id=UUID(user_id)
        )
        return _help_request_to_response(help_request)

    except HelpRequestNotFoundException:
        raise HTTPException(status_code=404, detail="Help request not found")
    except PeerLearningServiceException as e:
        logger.error(f"Error claiming help request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/help-requests/{request_id}/start", response_model=HelpRequestResponseDTO)
async def start_help_session(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Start the help session
    WHERE: POST /help-requests/{request_id}/start
    WHY: Tracks session timing
    """
    try:
        help_request = await service.start_help_session(
            request_id=UUID(request_id),
            helper_id=UUID(user_id)
        )
        return _help_request_to_response(help_request)

    except HelpRequestNotFoundException:
        raise HTTPException(status_code=404, detail="Help request not found")
    except InsufficientPermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PeerLearningServiceException as e:
        logger.error(f"Error starting help session: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/help-requests/{request_id}/resolve", response_model=HelpRequestResponseDTO)
async def resolve_help_request(
    request_id: str,
    request: HelpRequestResolveDTO,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Mark help request as resolved
    WHERE: POST /help-requests/{request_id}/resolve
    WHY: Closes request and triggers reputation
    """
    try:
        help_request = await service.resolve_help_request(
            request_id=UUID(request_id),
            resolver_id=UUID(user_id),
            resolution_notes=request.resolution_notes,
            actual_duration_minutes=request.actual_duration_minutes
        )
        return _help_request_to_response(help_request)

    except HelpRequestNotFoundException:
        raise HTTPException(status_code=404, detail="Help request not found")
    except InsufficientPermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PeerLearningServiceException as e:
        logger.error(f"Error resolving help request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/help-requests/{request_id}/rate", response_model=HelpRequestResponseDTO)
async def rate_help_session(
    request_id: str,
    request: HelpRequestRateDTO,
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Rate a help session
    WHERE: POST /help-requests/{request_id}/rate
    WHY: Provides feedback and adjusts reputation
    """
    try:
        help_request = await service.rate_help_session(
            request_id=UUID(request_id),
            rater_id=UUID(user_id),
            rating=request.rating,
            is_helper_rating=request.is_helper_rating
        )
        return _help_request_to_response(help_request)

    except HelpRequestNotFoundException:
        raise HTTPException(status_code=404, detail="Help request not found")
    except InsufficientPermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PeerLearningServiceException as e:
        logger.error(f"Error rating help session: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# REPUTATION ENDPOINTS
# =============================================================================

@router.get("/reputation", response_model=PeerReputationResponseDTO)
async def get_my_reputation(
    organization_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Get peer learning reputation
    WHERE: GET /reputation
    WHY: Shows peer learning standing
    """
    try:
        reputation = await service.get_user_reputation(
            user_id=UUID(user_id),
            organization_id=UUID(organization_id) if organization_id else None
        )
        return _reputation_to_response(reputation)

    except PeerLearningServiceException as e:
        logger.error(f"Error getting reputation: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reputation/{user_id}", response_model=PeerReputationResponseDTO)
async def get_user_reputation(
    user_id: str,
    organization_id: Optional[str] = Query(None),
    current_user_id: str = Depends(get_current_user_id),
    service: PeerLearningService = Depends(get_peer_learning_service)
):
    """
    WHAT: Get another user's reputation
    WHERE: GET /reputation/{user_id}
    WHY: View peer profiles
    """
    try:
        reputation = await service.get_user_reputation(
            user_id=UUID(user_id),
            organization_id=UUID(organization_id) if organization_id else None
        )
        return _reputation_to_response(reputation)

    except PeerLearningServiceException as e:
        logger.error(f"Error getting user reputation: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _study_group_to_response(group: StudyGroup) -> StudyGroupResponseDTO:
    """Convert StudyGroup entity to response DTO"""
    return StudyGroupResponseDTO(
        id=str(group.id),
        name=group.name,
        description=group.description,
        course_id=str(group.course_id),
        track_id=str(group.track_id) if group.track_id else None,
        organization_id=str(group.organization_id) if group.organization_id else None,
        creator_id=str(group.creator_id),
        status=group.status.value,
        is_public=group.is_public,
        min_members=group.min_members,
        max_members=group.max_members,
        current_member_count=group.current_member_count,
        meeting_schedule=group.meeting_schedule,
        meeting_platform=group.meeting_platform,
        meeting_link=group.meeting_link,
        goals=group.goals,
        tags=group.tags,
        created_at=group.created_at,
        activated_at=group.activated_at
    )


def _membership_to_response(membership: StudyGroupMembership) -> StudyGroupMemberDTO:
    """Convert StudyGroupMembership entity to response DTO"""
    return StudyGroupMemberDTO(
        id=str(membership.id),
        user_id=str(membership.user_id),
        role=membership.role.value,
        status=membership.status.value,
        joined_at=membership.joined_at,
        contribution_score=membership.contribution_score,
        sessions_attended=membership.sessions_attended,
        last_active_at=membership.last_active_at
    )


def _peer_review_to_response(review: PeerReview) -> PeerReviewResponseDTO:
    """Convert PeerReview entity to response DTO"""
    return PeerReviewResponseDTO(
        id=str(review.id),
        assignment_id=str(review.assignment_id),
        submission_id=str(review.submission_id),
        reviewer_id=str(review.reviewer_id),
        course_id=str(review.course_id),
        is_anonymous=review.is_anonymous,
        status=review.status.value,
        overall_score=float(review.overall_score) if review.overall_score else None,
        strengths=review.strengths,
        improvements=review.improvements,
        detailed_feedback=review.detailed_feedback,
        assigned_at=review.assigned_at,
        due_at=review.due_at,
        submitted_at=review.submitted_at,
        quality_rating=review.quality_rating.value if review.quality_rating else None,
        helpfulness_score=review.helpfulness_score
    )


def _discussion_thread_to_response(thread: DiscussionThread) -> DiscussionThreadResponseDTO:
    """Convert DiscussionThread entity to response DTO"""
    return DiscussionThreadResponseDTO(
        id=str(thread.id),
        title=thread.title,
        content=thread.content,
        author_id=str(thread.author_id),
        course_id=str(thread.course_id),
        study_group_id=str(thread.study_group_id) if thread.study_group_id else None,
        status=thread.status.value,
        is_question=thread.is_question,
        is_answered=thread.is_answered,
        is_pinned=thread.is_pinned,
        best_answer_id=str(thread.best_answer_id) if thread.best_answer_id else None,
        tags=thread.tags,
        view_count=thread.view_count,
        reply_count=thread.reply_count,
        upvote_count=thread.upvote_count,
        downvote_count=thread.downvote_count,
        created_at=thread.created_at,
        last_reply_at=thread.last_reply_at
    )


def _discussion_reply_to_response(reply: DiscussionReply) -> DiscussionReplyResponseDTO:
    """Convert DiscussionReply entity to response DTO"""
    return DiscussionReplyResponseDTO(
        id=str(reply.id),
        thread_id=str(reply.thread_id),
        author_id=str(reply.author_id),
        content=reply.content,
        parent_reply_id=str(reply.parent_reply_id) if reply.parent_reply_id else None,
        is_best_answer=reply.is_best_answer,
        upvote_count=reply.upvote_count,
        downvote_count=reply.downvote_count,
        is_edited=reply.is_edited,
        created_at=reply.created_at,
        edited_at=reply.edited_at
    )


def _help_request_to_response(request: HelpRequest) -> HelpRequestResponseDTO:
    """Convert HelpRequest entity to response DTO"""
    return HelpRequestResponseDTO(
        id=str(request.id),
        requester_id=str(request.requester_id),
        title=request.title,
        description=request.description,
        category=request.category.value,
        skill_topic=request.skill_topic,
        course_id=str(request.course_id),
        status=request.status.value,
        helper_id=str(request.helper_id) if request.helper_id else None,
        is_anonymous=request.is_anonymous,
        urgency=request.urgency,
        estimated_duration_minutes=request.estimated_duration_minutes,
        actual_duration_minutes=request.actual_duration_minutes,
        resolution_notes=request.resolution_notes,
        requester_rating=request.requester_rating,
        helper_rating=request.helper_rating,
        expires_at=request.expires_at,
        created_at=request.created_at,
        claimed_at=request.claimed_at,
        resolved_at=request.resolved_at
    )


def _reputation_to_response(reputation: PeerReputation) -> PeerReputationResponseDTO:
    """Convert PeerReputation entity to response DTO"""
    return PeerReputationResponseDTO(
        id=str(reputation.id),
        user_id=str(reputation.user_id),
        organization_id=str(reputation.organization_id) if reputation.organization_id else None,
        overall_score=reputation.overall_score,
        review_score=reputation.review_score,
        help_score=reputation.help_score,
        discussion_score=reputation.discussion_score,
        group_score=reputation.group_score,
        reviews_given=reputation.reviews_given,
        reviews_received=reputation.reviews_received,
        help_sessions_given=reputation.help_sessions_given,
        help_sessions_received=reputation.help_sessions_received,
        discussions_started=reputation.discussions_started,
        helpful_answers=reputation.helpful_answers,
        level=reputation.level,
        badges=reputation.badges
    )
