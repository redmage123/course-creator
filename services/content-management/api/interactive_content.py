"""
Interactive Content API Endpoints

WHAT: FastAPI router for interactive content operations
WHERE: Mounted on content-management service at /api/v1/interactive
WHY: Provides REST API for creating, managing, and evaluating interactive content

This module provides endpoints for:
- Interactive element CRUD operations
- Content type-specific operations
- Session tracking and evaluation
- Content analytics
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from content_management.domain.entities.interactive_content import (
    InteractiveContentType,
    InteractiveElementStatus,
    DifficultyLevel,
    CodeLanguage,
)
from content_management.application.services.interactive_content_service import (
    InteractiveContentService,
    InteractiveContentServiceException,
)


# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter()


# =============================================================================
# Pydantic DTOs
# =============================================================================

# --- Base Element DTOs ---

class CreateInteractiveElementDTO(BaseModel):
    """
    WHAT: DTO for creating interactive elements
    WHERE: Used in POST /elements endpoint
    WHY: Validates input for element creation
    """
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    content_type: InteractiveContentType
    course_id: UUID
    module_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    estimated_duration_minutes: int = Field(default=10, ge=1, le=480)
    learning_objectives: List[str] = Field(default_factory=list)
    max_attempts: int = Field(default=0, ge=0)
    points_value: int = Field(default=10, ge=0)
    tags: List[str] = Field(default_factory=list)


class InteractiveElementDTO(BaseModel):
    """
    WHAT: DTO for interactive element responses
    WHERE: Used in element response payloads
    WHY: Standardizes element data format
    """
    id: UUID
    title: str
    description: str
    content_type: str
    course_id: UUID
    module_id: Optional[UUID]
    lesson_id: Optional[UUID]
    creator_id: UUID
    organization_id: Optional[UUID]
    status: str
    version: int
    difficulty_level: str
    estimated_duration_minutes: int
    learning_objectives: List[str]
    max_attempts: int
    hints_enabled: bool
    points_value: int
    total_attempts: int
    total_completions: int
    avg_score: float
    engagement_score: float
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class UpdateElementStatusDTO(BaseModel):
    """DTO for updating element status."""
    status: str = Field(..., description="New status: review, approved, published, archived")
    reviewer_notes: Optional[str] = None
    approver_id: Optional[UUID] = None


# --- Simulation DTOs ---

class CreateSimulationDTO(BaseModel):
    """
    WHAT: DTO for creating simulations
    WHERE: Used in POST /simulations endpoint
    WHY: Validates simulation configuration
    """
    element_id: UUID
    name: str = Field(..., min_length=1, max_length=500)
    scenario_description: str
    initial_state: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_outcomes: List[Dict[str, Any]] = Field(default_factory=list)
    simulation_type: str = Field(default="guided")
    time_limit_seconds: int = Field(default=0, ge=0)
    guided_steps: List[Dict[str, Any]] = Field(default_factory=list)
    passing_score: int = Field(default=70, ge=0, le=100)


class SimulationDTO(BaseModel):
    """DTO for simulation responses."""
    id: UUID
    element_id: UUID
    name: str
    scenario_description: str
    initial_state: Dict[str, Any]
    parameters: Dict[str, Any]
    expected_outcomes: List[Dict[str, Any]]
    simulation_type: str
    time_limit_seconds: int
    guided_steps: List[Dict[str, Any]]
    passing_score: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluateSimulationDTO(BaseModel):
    """DTO for simulation evaluation request."""
    user_state: Dict[str, Any]


# --- Drag-Drop DTOs ---

class CreateDragDropDTO(BaseModel):
    """
    WHAT: DTO for creating drag-drop activities
    WHERE: Used in POST /drag-drop endpoint
    WHY: Validates drag-drop configuration
    """
    element_id: UUID
    activity_type: str = Field(..., description="categorize, match, order, sort")
    instructions: str
    items: List[Dict[str, Any]]
    zones: List[Dict[str, Any]]
    shuffle_items: bool = True
    partial_credit: bool = True


class DragDropDTO(BaseModel):
    """DTO for drag-drop activity responses."""
    id: UUID
    element_id: UUID
    activity_type: str
    instructions: str
    items: List[Dict[str, Any]]
    zones: List[Dict[str, Any]]
    shuffle_items: bool
    partial_credit: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluateDragDropDTO(BaseModel):
    """DTO for drag-drop evaluation."""
    placements: Dict[str, List[str]]  # zone_id -> list of item_ids


# --- Diagram DTOs ---

class CreateDiagramDTO(BaseModel):
    """
    WHAT: DTO for creating interactive diagrams
    WHERE: Used in POST /diagrams endpoint
    WHY: Validates diagram configuration
    """
    element_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    base_image_url: str
    layers: List[Dict[str, Any]] = Field(default_factory=list)
    hotspots: List[Dict[str, Any]] = Field(default_factory=list)
    guided_tour_enabled: bool = True
    quiz_mode_enabled: bool = False
    quiz_passing_score: int = Field(default=70, ge=0, le=100)


class DiagramDTO(BaseModel):
    """DTO for diagram responses."""
    id: UUID
    element_id: UUID
    title: str
    base_image_url: str
    layers: List[Dict[str, Any]]
    hotspots: List[Dict[str, Any]]
    guided_tour_enabled: bool
    quiz_mode_enabled: bool
    quiz_passing_score: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluateDiagramQuizDTO(BaseModel):
    """DTO for diagram quiz evaluation."""
    answers: Dict[str, str]  # hotspot_id -> answer


# --- Code Playground DTOs ---

class CreatePlaygroundDTO(BaseModel):
    """
    WHAT: DTO for creating code playgrounds
    WHERE: Used in POST /playgrounds endpoint
    WHY: Validates playground configuration
    """
    element_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    instructions: str
    language: CodeLanguage
    starter_code: str = ""
    solution_code: str = ""
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    passing_score: int = Field(default=70, ge=0, le=100)


class PlaygroundDTO(BaseModel):
    """DTO for code playground responses."""
    id: UUID
    element_id: UUID
    title: str
    instructions: str
    language: str
    language_version: str
    starter_code: str
    test_cases: List[Dict[str, Any]]
    show_test_cases: bool
    passing_score: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluatePlaygroundDTO(BaseModel):
    """DTO for code playground evaluation."""
    outputs: List[Dict[str, str]]  # test_id -> output


# --- Branching Scenario DTOs ---

class CreateScenarioDTO(BaseModel):
    """
    WHAT: DTO for creating branching scenarios
    WHERE: Used in POST /scenarios endpoint
    WHY: Validates scenario configuration
    """
    element_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    introduction: str
    branches: List[Dict[str, Any]]
    max_score: int = Field(default=100, ge=0)
    passing_score: int = Field(default=70, ge=0, le=100)
    allow_backtrack: bool = False
    visual_style: str = "cards"


class ScenarioDTO(BaseModel):
    """DTO for branching scenario responses."""
    id: UUID
    element_id: UUID
    title: str
    introduction: str
    branches: List[Dict[str, Any]]
    start_branch_id: Optional[UUID]
    max_score: int
    passing_score: int
    allow_backtrack: bool
    visual_style: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluateScenarioDTO(BaseModel):
    """DTO for scenario evaluation."""
    path: List[UUID]
    choices: List[Dict[str, Any]]


# --- Timeline DTOs ---

class CreateTimelineDTO(BaseModel):
    """
    WHAT: DTO for creating interactive timelines
    WHERE: Used in POST /timelines endpoint
    WHY: Validates timeline configuration
    """
    element_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    events: List[Dict[str, Any]]
    time_scale: str = "years"
    categories: List[Dict[str, str]] = Field(default_factory=list)


class TimelineDTO(BaseModel):
    """DTO for timeline responses."""
    id: UUID
    element_id: UUID
    title: str
    description: str
    events: List[Dict[str, Any]]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    time_scale: str
    categories: List[Dict[str, str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Flashcard DTOs ---

class CreateFlashcardDeckDTO(BaseModel):
    """
    WHAT: DTO for creating flashcard decks
    WHERE: Used in POST /flashcard-decks endpoint
    WHY: Validates deck configuration
    """
    element_id: UUID
    name: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    cards: List[Dict[str, Any]]
    new_cards_per_day: int = Field(default=20, ge=1, le=100)
    reviews_per_day: int = Field(default=100, ge=1, le=500)


class FlashcardDeckDTO(BaseModel):
    """DTO for flashcard deck responses."""
    id: UUID
    element_id: UUID
    name: str
    description: str
    cards: List[Dict[str, Any]]
    new_cards_per_day: int
    reviews_per_day: int
    total_reviews: int
    correct_reviews: int
    streak_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecordFlashcardReviewDTO(BaseModel):
    """DTO for recording flashcard review."""
    card_id: UUID
    quality: int = Field(..., ge=0, le=5)


# --- Interactive Video DTOs ---

class CreateVideoDTO(BaseModel):
    """
    WHAT: DTO for creating interactive videos
    WHERE: Used in POST /videos endpoint
    WHY: Validates video configuration
    """
    element_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    video_url: str
    video_duration_seconds: float = Field(..., gt=0)
    interactions: List[Dict[str, Any]] = Field(default_factory=list)
    chapters: List[Dict[str, Any]] = Field(default_factory=list)
    watch_percentage_required: int = Field(default=80, ge=0, le=100)
    passing_score: int = Field(default=70, ge=0, le=100)


class VideoDTO(BaseModel):
    """DTO for interactive video responses."""
    id: UUID
    element_id: UUID
    title: str
    description: str
    video_url: str
    video_duration_seconds: float
    interactions: List[Dict[str, Any]]
    chapters: List[Dict[str, Any]]
    watch_percentage_required: int
    passing_score: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluateVideoDTO(BaseModel):
    """DTO for video session evaluation."""
    watch_time_seconds: float = Field(..., ge=0)
    interaction_responses: Dict[str, Any]


# --- Session DTOs ---

class StartSessionDTO(BaseModel):
    """DTO for starting an interaction session."""
    element_id: UUID
    device_type: str = ""
    browser: str = ""


class RecordActionDTO(BaseModel):
    """DTO for recording session action."""
    action_type: str
    data: Optional[Dict[str, Any]] = None


class CompleteSessionDTO(BaseModel):
    """DTO for completing a session."""
    score: float = Field(..., ge=0, le=100)
    passed: bool


class SessionDTO(BaseModel):
    """DTO for session responses."""
    id: UUID
    element_id: UUID
    user_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: float
    status: str
    completion_percentage: float
    score: float
    passed: bool
    attempts: int
    hints_used: int
    actions_count: int

    class Config:
        from_attributes = True


# --- Generic Response DTOs ---

class EvaluationResultDTO(BaseModel):
    """DTO for evaluation results."""
    score: float
    passed: bool
    feedback: Any
    details: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Dependency Injection
# =============================================================================

async def get_service() -> InteractiveContentService:
    """
    WHAT: Provides the InteractiveContentService instance
    WHERE: Used as dependency in route handlers
    WHY: Enables dependency injection for testability

    Note: In production, this would get the pool from app state
    """
    from main import app
    return InteractiveContentService(app.state.pool)


# =============================================================================
# Interactive Element Endpoints
# =============================================================================

@router.post(
    "/elements",
    response_model=InteractiveElementDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create interactive element",
    description="Creates a new interactive element (base for all content types)"
)
async def create_element(
    dto: CreateInteractiveElementDTO,
    creator_id: UUID = Query(..., description="ID of the creating user"),
    service: InteractiveContentService = Depends(get_service)
):
    """
    WHAT: Creates a new interactive element
    WHERE: Called when creating any interactive content
    WHY: Creates the base element that content types reference
    """
    try:
        element = await service.create_interactive_element(
            title=dto.title,
            description=dto.description,
            content_type=dto.content_type,
            course_id=dto.course_id,
            creator_id=creator_id,
            module_id=dto.module_id,
            lesson_id=dto.lesson_id,
            organization_id=dto.organization_id,
            difficulty_level=dto.difficulty_level,
            estimated_duration_minutes=dto.estimated_duration_minutes,
            learning_objectives=dto.learning_objectives,
            max_attempts=dto.max_attempts,
            points_value=dto.points_value,
            tags=dto.tags
        )
        return _element_to_dto(element)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/elements/{element_id}",
    response_model=InteractiveElementDTO,
    summary="Get interactive element",
    description="Retrieves an interactive element by ID"
)
async def get_element(
    element_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Gets an interactive element by ID."""
    element = await service.get_interactive_element(element_id)
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    return _element_to_dto(element)


@router.get(
    "/courses/{course_id}/elements",
    response_model=List[InteractiveElementDTO],
    summary="List course interactive content",
    description="Lists all interactive elements for a course"
)
async def list_course_elements(
    course_id: UUID,
    content_type: Optional[InteractiveContentType] = None,
    status_filter: Optional[InteractiveElementStatus] = Query(None, alias="status"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    service: InteractiveContentService = Depends(get_service)
):
    """Lists interactive elements for a course."""
    elements = await service.get_course_interactive_content(
        course_id=course_id,
        content_type=content_type,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    return [_element_to_dto(e) for e in elements]


@router.patch(
    "/elements/{element_id}/status",
    response_model=InteractiveElementDTO,
    summary="Update element status",
    description="Updates the status of an interactive element"
)
async def update_element_status(
    element_id: UUID,
    dto: UpdateElementStatusDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Updates element status (submit for review, approve, publish, archive)."""
    try:
        if dto.status == "review":
            element = await service.submit_for_review(element_id, dto.reviewer_notes)
        elif dto.status == "approved":
            if not dto.approver_id:
                raise HTTPException(status_code=400, detail="Approver ID required")
            element = await service.approve_element(element_id, dto.approver_id)
        elif dto.status == "published":
            element = await service.publish_element(element_id)
        elif dto.status == "archived":
            element = await service.archive_element(element_id)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid status: {dto.status}")

        return _element_to_dto(element)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/elements/{element_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete element",
    description="Deletes an interactive element and all associated content"
)
async def delete_element(
    element_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Deletes an interactive element."""
    deleted = await service.delete_element(element_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Element not found")


# =============================================================================
# Simulation Endpoints
# =============================================================================

@router.post(
    "/simulations",
    response_model=SimulationDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create simulation",
    description="Creates a new simulation for an interactive element"
)
async def create_simulation(
    dto: CreateSimulationDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Creates a new simulation."""
    try:
        simulation = await service.create_simulation(
            element_id=dto.element_id,
            name=dto.name,
            scenario_description=dto.scenario_description,
            initial_state=dto.initial_state,
            parameters=dto.parameters,
            expected_outcomes=dto.expected_outcomes,
            simulation_type=dto.simulation_type,
            time_limit_seconds=dto.time_limit_seconds,
            guided_steps=dto.guided_steps,
            passing_score=dto.passing_score
        )
        return _simulation_to_dto(simulation)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/simulations/{simulation_id}",
    response_model=SimulationDTO,
    summary="Get simulation",
    description="Retrieves a simulation by ID"
)
async def get_simulation(
    simulation_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Gets a simulation by ID."""
    simulation = await service.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return _simulation_to_dto(simulation)


@router.post(
    "/simulations/{simulation_id}/evaluate",
    response_model=EvaluationResultDTO,
    summary="Evaluate simulation",
    description="Evaluates user's simulation results"
)
async def evaluate_simulation(
    simulation_id: UUID,
    dto: EvaluateSimulationDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Evaluates a simulation submission."""
    try:
        result = await service.evaluate_simulation(simulation_id, dto.user_state)
        return EvaluationResultDTO(
            score=result["score"],
            passed=result["passed"],
            feedback=result["feedback"],
            details=result
        )
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Drag-Drop Endpoints
# =============================================================================

@router.post(
    "/drag-drop",
    response_model=DragDropDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create drag-drop activity",
    description="Creates a new drag-drop activity"
)
async def create_drag_drop(
    dto: CreateDragDropDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Creates a drag-drop activity."""
    try:
        activity = await service.create_drag_drop_activity(
            element_id=dto.element_id,
            activity_type=dto.activity_type,
            instructions=dto.instructions,
            items=dto.items,
            zones=dto.zones,
            shuffle_items=dto.shuffle_items,
            partial_credit=dto.partial_credit
        )
        return _drag_drop_to_dto(activity)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/drag-drop/{activity_id}",
    response_model=DragDropDTO,
    summary="Get drag-drop activity",
    description="Retrieves a drag-drop activity by ID"
)
async def get_drag_drop(
    activity_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Gets a drag-drop activity by ID."""
    activity = await service.get_drag_drop_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return _drag_drop_to_dto(activity)


@router.post(
    "/drag-drop/{activity_id}/evaluate",
    response_model=EvaluationResultDTO,
    summary="Evaluate drag-drop submission",
    description="Evaluates a drag-drop activity submission"
)
async def evaluate_drag_drop(
    activity_id: UUID,
    dto: EvaluateDragDropDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Evaluates a drag-drop submission."""
    try:
        result = await service.evaluate_drag_drop(activity_id, dto.placements)
        return EvaluationResultDTO(
            score=result["score"],
            passed=result["score"] >= 70,  # Default passing threshold
            feedback=result["feedback"],
            details=result
        )
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Interactive Diagram Endpoints
# =============================================================================

@router.post(
    "/diagrams",
    response_model=DiagramDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create interactive diagram",
    description="Creates a new interactive diagram"
)
async def create_diagram(
    dto: CreateDiagramDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Creates an interactive diagram."""
    try:
        diagram = await service.create_interactive_diagram(
            element_id=dto.element_id,
            title=dto.title,
            base_image_url=dto.base_image_url,
            layers=dto.layers,
            hotspots=dto.hotspots,
            guided_tour_enabled=dto.guided_tour_enabled,
            quiz_mode_enabled=dto.quiz_mode_enabled,
            quiz_passing_score=dto.quiz_passing_score
        )
        return _diagram_to_dto(diagram)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/diagrams/{diagram_id}",
    response_model=DiagramDTO,
    summary="Get interactive diagram",
    description="Retrieves an interactive diagram by ID"
)
async def get_diagram(
    diagram_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Gets an interactive diagram by ID."""
    diagram = await service.get_interactive_diagram(diagram_id)
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    return _diagram_to_dto(diagram)


@router.post(
    "/diagrams/{diagram_id}/evaluate-quiz",
    response_model=EvaluationResultDTO,
    summary="Evaluate diagram quiz",
    description="Evaluates diagram quiz answers"
)
async def evaluate_diagram_quiz(
    diagram_id: UUID,
    dto: EvaluateDiagramQuizDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Evaluates diagram quiz answers."""
    try:
        result = await service.evaluate_diagram_quiz(diagram_id, dto.answers)
        return EvaluationResultDTO(
            score=result["score"],
            passed=result.get("passed", False),
            feedback=result["feedback"],
            details=result
        )
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Code Playground Endpoints
# =============================================================================

@router.post(
    "/playgrounds",
    response_model=PlaygroundDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create code playground",
    description="Creates a new code playground"
)
async def create_playground(
    dto: CreatePlaygroundDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Creates a code playground."""
    try:
        playground = await service.create_code_playground(
            element_id=dto.element_id,
            title=dto.title,
            instructions=dto.instructions,
            language=dto.language,
            starter_code=dto.starter_code,
            solution_code=dto.solution_code,
            test_cases=dto.test_cases,
            timeout_seconds=dto.timeout_seconds,
            passing_score=dto.passing_score
        )
        return _playground_to_dto(playground)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/playgrounds/{playground_id}",
    response_model=PlaygroundDTO,
    summary="Get code playground",
    description="Retrieves a code playground by ID"
)
async def get_playground(
    playground_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Gets a code playground by ID."""
    playground = await service.get_code_playground(playground_id)
    if not playground:
        raise HTTPException(status_code=404, detail="Playground not found")
    return _playground_to_dto(playground)


@router.post(
    "/playgrounds/{playground_id}/evaluate",
    response_model=EvaluationResultDTO,
    summary="Evaluate code submission",
    description="Evaluates code playground submission"
)
async def evaluate_playground(
    playground_id: UUID,
    dto: EvaluatePlaygroundDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Evaluates code playground output."""
    try:
        result = await service.evaluate_code_output(playground_id, dto.outputs)
        return EvaluationResultDTO(
            score=result["score"],
            passed=result["passed"],
            feedback=result["results"],
            details=result
        )
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Branching Scenario Endpoints
# =============================================================================

@router.post(
    "/scenarios",
    response_model=ScenarioDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create branching scenario",
    description="Creates a new branching scenario"
)
async def create_scenario(
    dto: CreateScenarioDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Creates a branching scenario."""
    try:
        scenario = await service.create_branching_scenario(
            element_id=dto.element_id,
            title=dto.title,
            introduction=dto.introduction,
            branches=dto.branches,
            max_score=dto.max_score,
            passing_score=dto.passing_score,
            allow_backtrack=dto.allow_backtrack,
            visual_style=dto.visual_style
        )
        return _scenario_to_dto(scenario)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/scenarios/{scenario_id}",
    response_model=ScenarioDTO,
    summary="Get branching scenario",
    description="Retrieves a branching scenario by ID"
)
async def get_scenario(
    scenario_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Gets a branching scenario by ID."""
    scenario = await service.get_branching_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return _scenario_to_dto(scenario)


@router.post(
    "/scenarios/{scenario_id}/evaluate",
    response_model=EvaluationResultDTO,
    summary="Evaluate scenario path",
    description="Evaluates the path through a branching scenario"
)
async def evaluate_scenario(
    scenario_id: UUID,
    dto: EvaluateScenarioDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Evaluates scenario path."""
    try:
        result = await service.evaluate_scenario_path(scenario_id, dto.path, dto.choices)
        return EvaluationResultDTO(
            score=result["score"],
            passed=result["passed"],
            feedback=result["feedback"],
            details=result
        )
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Timeline Endpoints
# =============================================================================

@router.post(
    "/timelines",
    response_model=TimelineDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create interactive timeline",
    description="Creates a new interactive timeline"
)
async def create_timeline(
    dto: CreateTimelineDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Creates an interactive timeline."""
    try:
        timeline = await service.create_interactive_timeline(
            element_id=dto.element_id,
            title=dto.title,
            description=dto.description,
            events=dto.events,
            time_scale=dto.time_scale,
            categories=dto.categories
        )
        return _timeline_to_dto(timeline)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/timelines/{timeline_id}",
    response_model=TimelineDTO,
    summary="Get interactive timeline",
    description="Retrieves an interactive timeline by ID"
)
async def get_timeline(
    timeline_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Gets an interactive timeline by ID."""
    timeline = await service.get_interactive_timeline(timeline_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return _timeline_to_dto(timeline)


# =============================================================================
# Flashcard Deck Endpoints
# =============================================================================

@router.post(
    "/flashcard-decks",
    response_model=FlashcardDeckDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create flashcard deck",
    description="Creates a new flashcard deck"
)
async def create_flashcard_deck(
    dto: CreateFlashcardDeckDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Creates a flashcard deck."""
    try:
        deck = await service.create_flashcard_deck(
            element_id=dto.element_id,
            name=dto.name,
            description=dto.description,
            cards=dto.cards,
            new_cards_per_day=dto.new_cards_per_day,
            reviews_per_day=dto.reviews_per_day
        )
        return _flashcard_deck_to_dto(deck)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/flashcard-decks/{deck_id}",
    response_model=FlashcardDeckDTO,
    summary="Get flashcard deck",
    description="Retrieves a flashcard deck by ID"
)
async def get_flashcard_deck(
    deck_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Gets a flashcard deck by ID."""
    deck = await service.get_flashcard_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return _flashcard_deck_to_dto(deck)


@router.post(
    "/flashcard-decks/{deck_id}/review",
    response_model=Dict[str, Any],
    summary="Record flashcard review",
    description="Records a flashcard review for spaced repetition"
)
async def record_flashcard_review(
    deck_id: UUID,
    dto: RecordFlashcardReviewDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Records a flashcard review."""
    try:
        card = await service.record_flashcard_review(deck_id, dto.card_id, dto.quality)
        return {
            "card_id": str(card.id),
            "next_review": card.next_review.isoformat() if card.next_review else None,
            "interval_days": card.interval_days,
            "difficulty": card.difficulty
        }
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Interactive Video Endpoints
# =============================================================================

@router.post(
    "/videos",
    response_model=VideoDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create interactive video",
    description="Creates a new interactive video"
)
async def create_video(
    dto: CreateVideoDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Creates an interactive video."""
    try:
        video = await service.create_interactive_video(
            element_id=dto.element_id,
            title=dto.title,
            description=dto.description,
            video_url=dto.video_url,
            video_duration_seconds=dto.video_duration_seconds,
            interactions=dto.interactions,
            chapters=dto.chapters,
            watch_percentage_required=dto.watch_percentage_required,
            passing_score=dto.passing_score
        )
        return _video_to_dto(video)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/videos/{video_id}",
    response_model=VideoDTO,
    summary="Get interactive video",
    description="Retrieves an interactive video by ID"
)
async def get_video(
    video_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Gets an interactive video by ID."""
    video = await service.get_interactive_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return _video_to_dto(video)


@router.post(
    "/videos/{video_id}/evaluate",
    response_model=EvaluationResultDTO,
    summary="Evaluate video session",
    description="Evaluates an interactive video viewing session"
)
async def evaluate_video_session(
    video_id: UUID,
    dto: EvaluateVideoDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Evaluates video session."""
    try:
        result = await service.evaluate_video_session(
            video_id, dto.watch_time_seconds, dto.interaction_responses
        )
        return EvaluationResultDTO(
            score=result["score"],
            passed=result["completed"],
            feedback=result["results"],
            details=result
        )
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Session Tracking Endpoints
# =============================================================================

@router.post(
    "/sessions",
    response_model=SessionDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Start interaction session",
    description="Starts a new interaction session for tracking"
)
async def start_session(
    dto: StartSessionDTO,
    user_id: UUID = Query(..., description="ID of the user"),
    service: InteractiveContentService = Depends(get_service)
):
    """Starts an interaction session."""
    try:
        session = await service.start_interaction_session(
            element_id=dto.element_id,
            user_id=user_id,
            device_type=dto.device_type,
            browser=dto.browser
        )
        return _session_to_dto(session)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sessions/{session_id}/actions",
    response_model=SessionDTO,
    summary="Record session action",
    description="Records an action in an interaction session"
)
async def record_action(
    session_id: UUID,
    dto: RecordActionDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Records a session action."""
    try:
        session = await service.record_session_action(
            session_id, dto.action_type, dto.data
        )
        return _session_to_dto(session)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sessions/{session_id}/complete",
    response_model=SessionDTO,
    summary="Complete session",
    description="Marks a session as completed with final score"
)
async def complete_session(
    session_id: UUID,
    dto: CompleteSessionDTO,
    service: InteractiveContentService = Depends(get_service)
):
    """Completes an interaction session."""
    try:
        session = await service.complete_session(session_id, dto.score, dto.passed)
        return _session_to_dto(session)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sessions/{session_id}/abandon",
    response_model=SessionDTO,
    summary="Abandon session",
    description="Marks a session as abandoned"
)
async def abandon_session(
    session_id: UUID,
    service: InteractiveContentService = Depends(get_service)
):
    """Marks a session as abandoned."""
    try:
        session = await service.abandon_session(session_id)
        return _session_to_dto(session)
    except InteractiveContentServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/users/{user_id}/sessions",
    response_model=List[SessionDTO],
    summary="Get user sessions",
    description="Gets a user's interaction sessions for an element"
)
async def get_user_sessions(
    user_id: UUID,
    element_id: UUID = Query(...),
    limit: int = Query(default=10, le=50),
    service: InteractiveContentService = Depends(get_service)
):
    """Gets user's sessions for an element."""
    sessions = await service.get_user_sessions(user_id, element_id, limit)
    return [_session_to_dto(s) for s in sessions]


# =============================================================================
# DTO Conversion Helpers
# =============================================================================

def _element_to_dto(element) -> InteractiveElementDTO:
    """Converts InteractiveElement to DTO."""
    return InteractiveElementDTO(
        id=element.id,
        title=element.title,
        description=element.description,
        content_type=element.content_type.value,
        course_id=element.course_id,
        module_id=element.module_id,
        lesson_id=element.lesson_id,
        creator_id=element.creator_id,
        organization_id=element.organization_id,
        status=element.status.value,
        version=element.version,
        difficulty_level=element.difficulty_level.value,
        estimated_duration_minutes=element.estimated_duration_minutes,
        learning_objectives=element.learning_objectives,
        max_attempts=element.max_attempts,
        hints_enabled=element.hints_enabled,
        points_value=element.points_value,
        total_attempts=element.total_attempts,
        total_completions=element.total_completions,
        avg_score=element.avg_score,
        engagement_score=element.engagement_score,
        tags=element.tags,
        created_at=element.created_at,
        updated_at=element.updated_at,
        published_at=element.published_at
    )


def _simulation_to_dto(simulation) -> SimulationDTO:
    """Converts Simulation to DTO."""
    return SimulationDTO(
        id=simulation.id,
        element_id=simulation.element_id,
        name=simulation.name,
        scenario_description=simulation.scenario_description,
        initial_state=simulation.initial_state,
        parameters=simulation.parameters,
        expected_outcomes=simulation.expected_outcomes,
        simulation_type=simulation.simulation_type,
        time_limit_seconds=simulation.time_limit_seconds,
        guided_steps=simulation.guided_steps,
        passing_score=simulation.passing_score,
        is_active=simulation.is_active,
        created_at=simulation.created_at,
        updated_at=simulation.updated_at
    )


def _drag_drop_to_dto(activity) -> DragDropDTO:
    """Converts DragDropActivity to DTO."""
    items = [{
        "id": str(item.id),
        "content": item.content,
        "content_type": item.content_type,
        "image_url": item.image_url,
        "correct_zone_ids": [str(z) for z in item.correct_zone_ids],
        "feedback_correct": item.feedback_correct,
        "feedback_incorrect": item.feedback_incorrect,
        "points": item.points,
        "order_index": item.order_index
    } for item in activity.items]

    zones = [{
        "id": str(zone.id),
        "label": zone.label,
        "description": zone.description,
        "accepts_multiple": zone.accepts_multiple,
        "max_items": zone.max_items,
        "position": zone.position,
        "style": zone.style
    } for zone in activity.zones]

    return DragDropDTO(
        id=activity.id,
        element_id=activity.element_id,
        activity_type=activity.activity_type,
        instructions=activity.instructions,
        items=items,
        zones=zones,
        shuffle_items=activity.shuffle_items,
        partial_credit=activity.partial_credit,
        is_active=activity.is_active,
        created_at=activity.created_at,
        updated_at=activity.updated_at
    )


def _diagram_to_dto(diagram) -> DiagramDTO:
    """Converts InteractiveDiagram to DTO."""
    layers = [{
        "id": str(layer.id),
        "name": layer.name,
        "description": layer.description,
        "image_url": layer.image_url,
        "is_visible": layer.is_visible,
        "is_base_layer": layer.is_base_layer,
        "opacity": layer.opacity,
        "order_index": layer.order_index
    } for layer in diagram.layers]

    hotspots = [{
        "id": str(hotspot.id),
        "label": hotspot.label,
        "description": hotspot.description,
        "shape": hotspot.shape,
        "coordinates": hotspot.coordinates,
        "popup_content": hotspot.popup_content,
        "popup_media_url": hotspot.popup_media_url,
        "is_quiz_point": hotspot.is_quiz_point,
        "quiz_question": hotspot.quiz_question,
        "order_index": hotspot.order_index
    } for hotspot in diagram.hotspots]

    return DiagramDTO(
        id=diagram.id,
        element_id=diagram.element_id,
        title=diagram.title,
        base_image_url=diagram.base_image_url,
        layers=layers,
        hotspots=hotspots,
        guided_tour_enabled=diagram.guided_tour_enabled,
        quiz_mode_enabled=diagram.quiz_mode_enabled,
        quiz_passing_score=diagram.quiz_passing_score,
        is_active=diagram.is_active,
        created_at=diagram.created_at,
        updated_at=diagram.updated_at
    )


def _playground_to_dto(playground) -> PlaygroundDTO:
    """Converts CodePlayground to DTO."""
    return PlaygroundDTO(
        id=playground.id,
        element_id=playground.element_id,
        title=playground.title,
        instructions=playground.instructions,
        language=playground.language.value,
        language_version=playground.language_version,
        starter_code=playground.starter_code,
        test_cases=[tc for tc in playground.test_cases if not tc.get("is_hidden")],
        show_test_cases=playground.show_test_cases,
        passing_score=playground.passing_score,
        is_active=playground.is_active,
        created_at=playground.created_at,
        updated_at=playground.updated_at
    )


def _scenario_to_dto(scenario) -> ScenarioDTO:
    """Converts BranchingScenario to DTO."""
    branches = [{
        "id": str(branch.id),
        "content": branch.content,
        "content_type": branch.content_type,
        "media_url": branch.media_url,
        "options": branch.options,
        "is_start": branch.is_start,
        "is_end": branch.is_end,
        "is_success_end": branch.is_success_end,
        "is_failure_end": branch.is_failure_end,
        "points_value": branch.points_value
    } for branch in scenario.branches]

    return ScenarioDTO(
        id=scenario.id,
        element_id=scenario.element_id,
        title=scenario.title,
        introduction=scenario.introduction,
        branches=branches,
        start_branch_id=scenario.start_branch_id,
        max_score=scenario.max_score,
        passing_score=scenario.passing_score,
        allow_backtrack=scenario.allow_backtrack,
        visual_style=scenario.visual_style,
        is_active=scenario.is_active,
        created_at=scenario.created_at,
        updated_at=scenario.updated_at
    )


def _timeline_to_dto(timeline) -> TimelineDTO:
    """Converts InteractiveTimeline to DTO."""
    events = [{
        "id": str(event.id),
        "title": event.title,
        "description": event.description,
        "date": event.date.isoformat() if event.date else None,
        "date_display": event.date_display,
        "content": event.content,
        "content_type": event.content_type,
        "media_url": event.media_url,
        "category": event.category,
        "importance": event.importance,
        "is_milestone": event.is_milestone,
        "icon": event.icon,
        "color": event.color
    } for event in timeline.events]

    return TimelineDTO(
        id=timeline.id,
        element_id=timeline.element_id,
        title=timeline.title,
        description=timeline.description,
        events=events,
        start_date=timeline.start_date,
        end_date=timeline.end_date,
        time_scale=timeline.time_scale,
        categories=timeline.categories,
        is_active=timeline.is_active,
        created_at=timeline.created_at,
        updated_at=timeline.updated_at
    )


def _flashcard_deck_to_dto(deck) -> FlashcardDeckDTO:
    """Converts FlashcardDeck to DTO."""
    cards = [{
        "id": str(card.id),
        "front_content": card.front_content,
        "back_content": card.back_content,
        "front_content_type": card.front_content_type,
        "back_content_type": card.back_content_type,
        "front_media_url": card.front_media_url,
        "back_media_url": card.back_media_url,
        "difficulty": card.difficulty,
        "interval_days": card.interval_days,
        "repetitions": card.repetitions,
        "next_review": card.next_review.isoformat() if card.next_review else None,
        "tags": card.tags
    } for card in deck.cards]

    return FlashcardDeckDTO(
        id=deck.id,
        element_id=deck.element_id,
        name=deck.name,
        description=deck.description,
        cards=cards,
        new_cards_per_day=deck.new_cards_per_day,
        reviews_per_day=deck.reviews_per_day,
        total_reviews=deck.total_reviews,
        correct_reviews=deck.correct_reviews,
        streak_days=deck.streak_days,
        is_active=deck.is_active,
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )


def _video_to_dto(video) -> VideoDTO:
    """Converts InteractiveVideo to DTO."""
    interactions = [{
        "id": str(interaction.id),
        "timestamp_seconds": interaction.timestamp_seconds,
        "interaction_type": interaction.interaction_type,
        "title": interaction.title,
        "content": interaction.content,
        "question": interaction.question,
        "options": interaction.options,
        "points": interaction.points,
        "pause_video": interaction.pause_video,
        "required": interaction.required,
        "skip_allowed": interaction.skip_allowed
    } for interaction in video.interactions]

    return VideoDTO(
        id=video.id,
        element_id=video.element_id,
        title=video.title,
        description=video.description,
        video_url=video.video_url,
        video_duration_seconds=video.video_duration_seconds,
        interactions=interactions,
        chapters=video.chapters,
        watch_percentage_required=video.watch_percentage_required,
        passing_score=video.passing_score,
        is_active=video.is_active,
        created_at=video.created_at,
        updated_at=video.updated_at
    )


def _session_to_dto(session) -> SessionDTO:
    """Converts InteractionSession to DTO."""
    return SessionDTO(
        id=session.id,
        element_id=session.element_id,
        user_id=session.user_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        status=session.status,
        completion_percentage=session.completion_percentage,
        score=session.score,
        passed=session.passed,
        attempts=session.attempts,
        hints_used=session.hints_used,
        actions_count=session.actions_count
    )
