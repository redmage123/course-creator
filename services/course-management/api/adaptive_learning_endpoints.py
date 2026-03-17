"""
Adaptive Learning API Endpoints

WHAT: REST API endpoints for adaptive learning path management
WHERE: services/course-management/api/adaptive_learning_endpoints.py
WHY: Provides HTTP interface for AI-driven personalized learning features

BUSINESS CONTEXT:
This module exposes endpoints for managing adaptive learning paths, including:
- Creating and managing personalized learning paths for students
- Tracking progress through learning path nodes
- Receiving and responding to AI-generated recommendations
- Monitoring skill mastery levels for spaced repetition

ARCHITECTURAL PRINCIPLES:
- Single Responsibility: Only adaptive learning endpoints
- Dependency Inversion: Depends on service abstractions
- Interface Segregation: Focused, role-specific endpoints

AUTHENTICATION:
All endpoints require JWT authentication. User context determines
accessible paths (students see own paths, instructors see students' paths).

@module api/adaptive_learning_endpoints
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
from course_management.domain.entities.learning_path import (
    LearningPath,
    LearningPathNode,
    AdaptiveRecommendation,
    StudentMasteryLevel,
    PathType,
    PathStatus,
    NodeStatus,
    ContentType,
    RecommendationType,
    RecommendationStatus,
    MasteryLevel,
    DifficultyLevel
)

# Application services
from course_management.application.services.adaptive_learning_service import (
    AdaptiveLearningService,
    AdaptiveLearningServiceException
)

logger = logging.getLogger(__name__)


# =============================================================================
# API MODELS (DTOs)
# =============================================================================

class LearningPathCreateDTO(BaseModel):
    """
    WHAT: DTO for creating a new learning path
    WHERE: POST /learning-paths
    WHY: Captures all required fields for path creation
    """
    track_id: Optional[str] = Field(None, description="Track ID for organizational context")
    name: str = Field(..., min_length=1, max_length=200, description="Path display name")
    description: Optional[str] = Field(None, max_length=2000, description="Path description")
    path_type: str = Field(
        default="sequential",
        pattern="^(sequential|adaptive|custom)$",
        description="Path progression type"
    )
    difficulty_level: str = Field(
        default="beginner",
        pattern="^(beginner|intermediate|advanced|expert)$",
        description="Target difficulty level"
    )
    estimated_duration_hours: Optional[int] = Field(
        None,
        ge=1,
        description="Estimated completion time in hours"
    )
    target_completion_date: Optional[datetime] = Field(
        None,
        description="Target date for path completion"
    )
    adapt_to_performance: bool = Field(
        default=True,
        description="Enable performance-based adaptation"
    )
    adapt_to_pace: bool = Field(
        default=True,
        description="Enable pace-based adaptation"
    )


class LearningPathResponseDTO(BaseModel):
    """
    WHAT: DTO for learning path API responses
    WHERE: All learning path GET endpoints
    WHY: Provides consistent response structure
    """
    id: str
    student_id: str
    organization_id: Optional[str]
    track_id: Optional[str]
    name: str
    description: Optional[str]
    path_type: str
    difficulty_level: str
    status: str
    overall_progress: float
    estimated_duration_hours: Optional[int]
    actual_duration_hours: Optional[int]
    total_nodes: int
    completed_nodes: int
    adapt_to_performance: bool
    adapt_to_pace: bool
    target_completion_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class LearningPathNodeDTO(BaseModel):
    """
    WHAT: DTO for learning path node responses
    WHERE: GET /learning-paths/{id}/nodes
    WHY: Exposes node details for UI rendering
    """
    id: str
    learning_path_id: str
    content_type: str
    content_id: str
    sequence_order: int
    status: str
    is_required: bool
    is_unlocked: bool
    progress_percentage: float
    score: Optional[float]
    attempts: int
    max_attempts: Optional[int]
    estimated_duration_minutes: Optional[int]
    actual_duration_minutes: Optional[int]
    completed_at: Optional[datetime]


class NodeAddDTO(BaseModel):
    """
    WHAT: DTO for adding a node to a learning path
    WHERE: POST /learning-paths/{id}/nodes
    WHY: Captures required node creation fields
    """
    content_type: str = Field(
        ...,
        pattern="^(course|lesson|quiz|lab|project|video)$",
        description="Type of content for this node"
    )
    content_id: str = Field(..., description="ID of the content item")
    sequence_order: Optional[int] = Field(
        None,
        ge=1,
        description="Order in the learning path"
    )
    is_required: bool = Field(default=True, description="Whether node must be completed")
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)


class NodeProgressDTO(BaseModel):
    """
    WHAT: DTO for updating node progress
    WHERE: PUT /learning-paths/{path_id}/nodes/{node_id}/progress
    WHY: Tracks student progress through content
    """
    progress_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Completion percentage (0-100)"
    )
    time_spent_seconds: Optional[int] = Field(None, ge=0)
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    completed: bool = Field(default=False, description="Mark node as completed")


class RecommendationResponseDTO(BaseModel):
    """
    WHAT: DTO for adaptive recommendation responses
    WHERE: GET /recommendations
    WHY: Exposes AI recommendations to students
    """
    id: str
    recommendation_type: str
    content_type: Optional[str]
    content_id: Optional[str]
    title: str
    description: Optional[str]
    reason: str
    priority: int
    confidence_score: float
    status: str
    valid_from: datetime
    valid_until: Optional[datetime]
    created_at: datetime


class RecommendationRespondDTO(BaseModel):
    """
    WHAT: DTO for responding to a recommendation
    WHERE: POST /recommendations/{id}/respond
    WHY: Captures user decision on recommendations
    """
    action: str = Field(
        ...,
        pattern="^(accept|dismiss|defer)$",
        description="Action to take on the recommendation"
    )
    feedback: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional user feedback"
    )


class MasteryLevelDTO(BaseModel):
    """
    WHAT: DTO for student mastery level responses
    WHERE: GET /mastery
    WHY: Shows skill mastery for spaced repetition
    """
    id: str
    skill_topic: str
    course_id: Optional[str]
    mastery_level: str
    mastery_score: float
    assessments_completed: int
    assessments_passed: int
    average_score: Optional[float]
    best_score: Optional[float]
    practice_streak_days: int
    last_practiced_at: Optional[datetime]
    next_review_recommended_at: Optional[datetime]


class MasteryUpdateDTO(BaseModel):
    """
    WHAT: DTO for recording assessment result
    WHERE: POST /mastery
    WHY: Updates skill mastery after practice/assessment
    """
    skill_topic: str = Field(..., min_length=1, max_length=200)
    course_id: Optional[str] = None
    score: float = Field(..., ge=0.0, le=100.0)
    time_spent_minutes: Optional[int] = Field(None, ge=0)


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(tags=["adaptive-learning"])


def get_adaptive_learning_service() -> AdaptiveLearningService:
    """
    WHAT: Dependency injection for adaptive learning service
    WHERE: Used by all endpoints
    WHY: Retrieves service from container for proper lifecycle management
    """
    from main import app
    if not app or not hasattr(app.state, 'container') or not app.state.container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return app.state.container.get_adaptive_learning_service()


# JWT-authenticated user ID extraction
get_current_user_id = get_authenticated_user_id


# =============================================================================
# LEARNING PATH ENDPOINTS
# =============================================================================

@router.post("/learning-paths", response_model=LearningPathResponseDTO)
async def create_learning_path(
    request: LearningPathCreateDTO,
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Create a new personalized learning path
    WHERE: POST /learning-paths
    WHY: Enables students to start structured learning journeys

    Creates a learning path for the authenticated student with the specified
    configuration. The path starts in DRAFT status until explicitly started.

    WORKFLOW:
    1. Validate request parameters
    2. Create learning path entity
    3. Persist to database
    4. Return created path with generated ID
    """
    try:
        path = LearningPath(
            student_id=UUID(user_id),
            track_id=UUID(request.track_id) if request.track_id else None,
            name=request.name,
            description=request.description,
            path_type=PathType(request.path_type),
            difficulty_level=DifficultyLevel(request.difficulty_level),
            status=PathStatus.DRAFT,
            overall_progress=Decimal("0.0"),
            estimated_duration_hours=request.estimated_duration_hours,
            target_completion_date=request.target_completion_date,
            adapt_to_performance=request.adapt_to_performance,
            adapt_to_pace=request.adapt_to_pace,
            adaptation_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        created_path = await service.create_learning_path(path)
        return _path_to_response(created_path)

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error creating learning path: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating learning path: {e}")
        raise HTTPException(status_code=500, detail="Failed to create learning path")


@router.get("/learning-paths", response_model=List[LearningPathResponseDTO])
async def get_my_learning_paths(
    status: Optional[str] = Query(
        None,
        pattern="^(draft|active|paused|completed|abandoned)$",
        description="Filter by path status"
    ),
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Get all learning paths for the authenticated student
    WHERE: GET /learning-paths
    WHY: Enables students to view and manage their learning journeys

    Returns all learning paths owned by the student, optionally filtered by status.
    """
    try:
        status_filter = PathStatus(status) if status else None
        paths = await service.get_student_paths(
            UUID(user_id),
            status=status_filter
        )
        return [_path_to_response(p) for p in paths]

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error fetching learning paths: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error fetching learning paths: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch learning paths")


@router.get("/learning-paths/{path_id}", response_model=LearningPathResponseDTO)
async def get_learning_path(
    path_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Get a specific learning path by ID
    WHERE: GET /learning-paths/{path_id}
    WHY: Retrieve detailed path information for display
    """
    try:
        path = await service.get_learning_path(UUID(path_id))
        if not path:
            raise HTTPException(status_code=404, detail="Learning path not found")

        # Authorization check - student can only see their own paths
        if str(path.student_id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this learning path")

        return _path_to_response(path)

    except HTTPException:
        raise
    except AdaptiveLearningServiceException as e:
        logger.error(f"Error fetching learning path: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/learning-paths/{path_id}/start", response_model=LearningPathResponseDTO)
async def start_learning_path(
    path_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Start a learning path (transition from DRAFT to ACTIVE)
    WHERE: POST /learning-paths/{path_id}/start
    WHY: Activates the learning journey and begins tracking

    Starting a path:
    - Changes status from DRAFT to ACTIVE
    - Records start timestamp
    - Unlocks first node(s) based on path configuration
    - Begins generating recommendations
    """
    try:
        path = await service.start_learning_path(UUID(path_id), UUID(user_id))
        return _path_to_response(path)

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error starting learning path: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/learning-paths/{path_id}/nodes", response_model=List[LearningPathNodeDTO])
async def get_path_nodes(
    path_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Get all nodes in a learning path
    WHERE: GET /learning-paths/{path_id}/nodes
    WHY: Displays the learning path structure to students

    Returns nodes ordered by sequence, with status and progress information.
    """
    try:
        # First verify path ownership
        path = await service.get_learning_path(UUID(path_id))
        if not path:
            raise HTTPException(status_code=404, detail="Learning path not found")
        if str(path.student_id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        nodes = await service.get_path_nodes(UUID(path_id))
        return [_node_to_response(n) for n in nodes]

    except HTTPException:
        raise
    except AdaptiveLearningServiceException as e:
        logger.error(f"Error fetching path nodes: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/learning-paths/{path_id}/nodes", response_model=LearningPathNodeDTO)
async def add_node_to_path(
    path_id: str,
    request: NodeAddDTO,
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Add a content node to a learning path
    WHERE: POST /learning-paths/{path_id}/nodes
    WHY: Builds the learning path structure with content

    Only allowed when path is in DRAFT status.
    """
    try:
        # Create node entity
        node = LearningPathNode(
            learning_path_id=UUID(path_id),
            content_type=ContentType(request.content_type),
            content_id=UUID(request.content_id),
            sequence_order=request.sequence_order or 999,
            is_required=request.is_required,
            is_unlocked=False,
            progress_percentage=Decimal("0.0"),
            attempts=0,
            estimated_duration_minutes=request.estimated_duration_minutes,
            difficulty_adjustment=Decimal("1.0"),
            was_recommended=False,
            unlock_conditions={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        created_node = await service.add_node(node, UUID(user_id))
        return _node_to_response(created_node)

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error adding node to path: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/learning-paths/{path_id}/nodes/{node_id}/progress",
    response_model=LearningPathNodeDTO
)
async def update_node_progress(
    path_id: str,
    node_id: str,
    request: NodeProgressDTO,
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Update progress on a learning path node
    WHERE: PUT /learning-paths/{path_id}/nodes/{node_id}/progress
    WHY: Tracks student progress through learning content

    Updates:
    - Progress percentage (0-100)
    - Time spent
    - Score (if assessment)
    - Completion status
    """
    try:
        updated_node = await service.update_node_progress(
            path_id=UUID(path_id),
            node_id=UUID(node_id),
            student_id=UUID(user_id),
            progress_percentage=Decimal(str(request.progress_percentage)),
            time_spent_seconds=request.time_spent_seconds,
            score=Decimal(str(request.score)) if request.score else None,
            mark_completed=request.completed
        )
        return _node_to_response(updated_node)

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error updating node progress: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# RECOMMENDATION ENDPOINTS
# =============================================================================

@router.get("/recommendations", response_model=List[RecommendationResponseDTO])
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Get AI-generated learning recommendations
    WHERE: GET /recommendations
    WHY: Provides personalized learning suggestions

    Returns pending recommendations for the student, ordered by priority.
    Recommendations are based on:
    - Learning path progress
    - Performance metrics
    - Skill mastery levels
    - Spaced repetition schedules
    """
    try:
        recommendations = await service.get_pending_recommendations(
            UUID(user_id),
            limit=limit
        )
        return [_recommendation_to_response(r) for r in recommendations]

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error fetching recommendations: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recommendations/{recommendation_id}/respond")
async def respond_to_recommendation(
    recommendation_id: str,
    request: RecommendationRespondDTO,
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Respond to an AI recommendation (accept/dismiss/defer)
    WHERE: POST /recommendations/{recommendation_id}/respond
    WHY: Captures student intent for recommendation refinement

    Actions:
    - accept: Student will follow the recommendation
    - dismiss: Student declines the recommendation
    - defer: Student will consider later
    """
    try:
        status_map = {
            "accept": RecommendationStatus.ACCEPTED,
            "dismiss": RecommendationStatus.DISMISSED,
            "defer": RecommendationStatus.DEFERRED
        }

        updated = await service.respond_to_recommendation(
            recommendation_id=UUID(recommendation_id),
            student_id=UUID(user_id),
            new_status=status_map[request.action],
            feedback=request.feedback
        )

        return {
            "message": f"Recommendation {request.action}ed successfully",
            "recommendation_id": str(updated.id),
            "new_status": updated.status.value
        }

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error responding to recommendation: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# MASTERY LEVEL ENDPOINTS
# =============================================================================

@router.get("/mastery", response_model=List[MasteryLevelDTO])
async def get_mastery_levels(
    course_id: Optional[str] = Query(None, description="Filter by course"),
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Get skill mastery levels for the student
    WHERE: GET /mastery
    WHY: Shows skill progression for spaced repetition

    Returns all mastery level records for the student, showing:
    - Skill topics mastered
    - Current mastery level (beginner to expert)
    - Practice history
    - Next recommended review dates
    """
    try:
        mastery_levels = await service.get_student_mastery(
            student_id=UUID(user_id),
            course_id=UUID(course_id) if course_id else None
        )
        return [_mastery_to_response(m) for m in mastery_levels]

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error fetching mastery levels: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mastery/due-for-review", response_model=List[MasteryLevelDTO])
async def get_skills_due_for_review(
    limit: int = Query(default=10, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Get skills that need spaced repetition review
    WHERE: GET /mastery/due-for-review
    WHY: Supports spaced repetition learning methodology

    Returns skills where next_review_recommended_at is in the past,
    indicating the student should practice to maintain retention.
    """
    try:
        skills_due = await service.get_skills_needing_review(
            student_id=UUID(user_id),
            limit=limit
        )
        return [_mastery_to_response(m) for m in skills_due]

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error fetching skills due for review: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mastery/record-assessment")
async def record_assessment_result(
    request: MasteryUpdateDTO,
    user_id: str = Depends(get_current_user_id),
    service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    WHAT: Record an assessment/practice result
    WHERE: POST /mastery/record-assessment
    WHY: Updates mastery levels based on student performance

    Records a practice or assessment result, which:
    - Updates mastery score for the skill
    - Recalculates mastery level
    - Updates spaced repetition schedule
    - May trigger new recommendations
    """
    try:
        updated_mastery = await service.record_assessment_result(
            student_id=UUID(user_id),
            skill_topic=request.skill_topic,
            course_id=UUID(request.course_id) if request.course_id else None,
            score=Decimal(str(request.score)),
            time_spent_minutes=request.time_spent_minutes
        )

        return {
            "message": "Assessment result recorded",
            "skill_topic": updated_mastery.skill_topic,
            "new_mastery_level": updated_mastery.mastery_level.value,
            "mastery_score": float(updated_mastery.mastery_score),
            "next_review": updated_mastery.next_review_recommended_at.isoformat() if updated_mastery.next_review_recommended_at else None
        }

    except AdaptiveLearningServiceException as e:
        logger.error(f"Error recording assessment: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _path_to_response(path: LearningPath) -> LearningPathResponseDTO:
    """
    WHAT: Convert LearningPath entity to response DTO
    WHERE: Used by all path endpoints
    WHY: Provides consistent response format
    """
    return LearningPathResponseDTO(
        id=str(path.id),
        student_id=str(path.student_id),
        organization_id=str(path.organization_id) if path.organization_id else None,
        track_id=str(path.track_id) if path.track_id else None,
        name=path.name,
        description=path.description,
        path_type=path.path_type.value,
        difficulty_level=path.difficulty_level.value,
        status=path.status.value,
        overall_progress=float(path.overall_progress),
        estimated_duration_hours=path.estimated_duration_hours,
        actual_duration_hours=path.actual_duration_hours,
        total_nodes=path.total_nodes,
        completed_nodes=path.completed_nodes,
        adapt_to_performance=path.adapt_to_performance,
        adapt_to_pace=path.adapt_to_pace,
        target_completion_date=path.target_completion_date,
        created_at=path.created_at,
        updated_at=path.updated_at,
        started_at=path.started_at,
        completed_at=path.completed_at
    )


def _node_to_response(node: LearningPathNode) -> LearningPathNodeDTO:
    """
    WHAT: Convert LearningPathNode entity to response DTO
    WHERE: Used by node endpoints
    WHY: Provides consistent response format
    """
    return LearningPathNodeDTO(
        id=str(node.id),
        learning_path_id=str(node.learning_path_id),
        content_type=node.content_type.value,
        content_id=str(node.content_id),
        sequence_order=node.sequence_order,
        status=node.status.value,
        is_required=node.is_required,
        is_unlocked=node.is_unlocked,
        progress_percentage=float(node.progress_percentage),
        score=float(node.score) if node.score else None,
        attempts=node.attempts,
        max_attempts=node.max_attempts,
        estimated_duration_minutes=node.estimated_duration_minutes,
        actual_duration_minutes=node.actual_duration_minutes,
        completed_at=node.completed_at
    )


def _recommendation_to_response(rec: AdaptiveRecommendation) -> RecommendationResponseDTO:
    """
    WHAT: Convert AdaptiveRecommendation entity to response DTO
    WHERE: Used by recommendation endpoints
    WHY: Provides consistent response format
    """
    return RecommendationResponseDTO(
        id=str(rec.id),
        recommendation_type=rec.recommendation_type.value,
        content_type=rec.content_type.value if rec.content_type else None,
        content_id=str(rec.content_id) if rec.content_id else None,
        title=rec.title,
        description=rec.description,
        reason=rec.reason,
        priority=rec.priority,
        confidence_score=float(rec.confidence_score),
        status=rec.status.value,
        valid_from=rec.valid_from,
        valid_until=rec.valid_until,
        created_at=rec.created_at
    )


def _mastery_to_response(mastery: StudentMasteryLevel) -> MasteryLevelDTO:
    """
    WHAT: Convert StudentMasteryLevel entity to response DTO
    WHERE: Used by mastery endpoints
    WHY: Provides consistent response format
    """
    return MasteryLevelDTO(
        id=str(mastery.id),
        skill_topic=mastery.skill_topic,
        course_id=str(mastery.course_id) if mastery.course_id else None,
        mastery_level=mastery.mastery_level.value,
        mastery_score=float(mastery.mastery_score),
        assessments_completed=mastery.assessments_completed,
        assessments_passed=mastery.assessments_passed,
        average_score=float(mastery.average_score) if mastery.average_score else None,
        best_score=float(mastery.best_score) if mastery.best_score else None,
        practice_streak_days=mastery.practice_streak_days,
        last_practiced_at=mastery.last_practiced_at,
        next_review_recommended_at=mastery.next_review_recommended_at
    )
