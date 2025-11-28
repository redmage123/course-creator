"""
Brain API Endpoints

This module defines the REST API endpoints for brain lifecycle management,
prediction, learning, and analytics.

Business Context:
    Provides HTTP API for:
    - Creating and managing brain instances (platform, student, instructor)
    - Making predictions with neural inference or LLM fallback
    - Teaching brains through supervised and reinforcement learning
    - Querying brain performance metrics and self-awareness data

API Design:
    - RESTful resource-based endpoints
    - Async/await for non-blocking operations
    - Proper HTTP status codes and error handling
    - JSON request/response bodies
    - OpenAPI documentation (FastAPI auto-generates)

Author: Course Creator Platform Team
Version: 1.0.0
Last Updated: 2025-11-09
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from nimcp_service.application.services.brain_service import (
    BrainService,
    BrainServiceError,
    BrainNotFoundError,
    BrainCreationError,
    BrainLearningError
)
from nimcp_service.domain.entities.brain import BrainType


# ============================================================================
# Request/Response Models
# ============================================================================

class CreatePlatformBrainRequest(BaseModel):
    """Request model for creating platform brain."""
    neuron_count: int = Field(default=50000, description="Number of neurons in the network")
    enable_ethics: bool = Field(default=True, description="Enable Golden Rule ethics engine")
    enable_curiosity: bool = Field(default=True, description="Enable autonomous curiosity system")


class CreateStudentBrainRequest(BaseModel):
    """Request model for creating student brain."""
    student_id: UUID = Field(..., description="UUID of the student owner")
    neuron_count: int = Field(default=10000, description="Number of neurons if not cloning")
    clone_from_platform: bool = Field(default=True, description="Whether to COW clone from platform brain")


class PredictionRequest(BaseModel):
    """Request model for making a prediction."""
    brain_id: UUID = Field(..., description="UUID of the brain to use")
    features: List[float] = Field(..., description="Input feature vector")
    use_llm_fallback: bool = Field(default=True, description="Whether to use LLM for low-confidence predictions")


class LearningRequest(BaseModel):
    """Request model for supervised learning."""
    brain_id: UUID = Field(..., description="UUID of the brain to teach")
    features: List[float] = Field(..., description="Input feature vector")
    label: str = Field(..., description="Ground truth label/classification")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0, description="Confidence in this training example")


class ReinforcementRequest(BaseModel):
    """Request model for reinforcement learning."""
    brain_id: UUID = Field(..., description="UUID of the brain to reinforce")
    features: List[float] = Field(..., description="Input features from the interaction")
    reward: float = Field(..., ge=0.0, le=1.0, description="Reward signal (0=failure, 1=success)")


class PredictionResponse(BaseModel):
    """Response model for predictions."""
    output: List[float] = Field(..., description="Prediction output vector")
    confidence: float = Field(..., description="Prediction confidence (0-1)")
    used_llm: bool = Field(..., description="Whether LLM was used (vs neural inference)")
    neural_inference_rate: float = Field(..., description="Current neural inference rate percentage")
    llm_cost_savings_percent: float = Field(..., description="Estimated LLM cost savings percentage")


class BrainResponse(BaseModel):
    """Response model for brain instances."""
    brain_id: UUID
    brain_type: str
    owner_id: Optional[UUID]
    parent_brain_id: Optional[UUID]
    created_at: str
    last_updated: str
    state_file_path: str
    is_active: bool

    # Performance metrics
    total_interactions: int
    neural_inference_count: int
    llm_query_count: int
    neural_inference_rate: float
    average_confidence: float
    average_accuracy: float

    # COW stats
    is_cow_clone: bool
    cow_efficiency_percent: float

    # Self-awareness
    strong_domains: dict
    weak_domains: dict
    bias_detections: dict


# ============================================================================
# API Router
# ============================================================================

router = APIRouter(prefix="/api/v1/brains", tags=["brains"])


# Dependency injection placeholder
# In production, this would be injected via FastAPI dependency system
_brain_service: Optional[BrainService] = None


def get_brain_service() -> BrainService:
    """Dependency injection for BrainService."""
    if _brain_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Brain service not initialized"
        )
    return _brain_service


def set_brain_service(service: BrainService):
    """Set the brain service instance (called from main.py)."""
    global _brain_service
    _brain_service = service


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/platform", response_model=BrainResponse, status_code=status.HTTP_201_CREATED)
async def create_platform_brain(
    request: CreatePlatformBrainRequest,
    service: BrainService = Depends(get_brain_service)
):
    """
    Create the singleton platform brain (master orchestrator).

    Business Logic:
        Platform brain is created once at system initialization and
        serves as the master brain that orchestrates all sub-brains.

    Returns:
        201 Created: Platform brain created successfully
        400 Bad Request: Platform brain already exists
        500 Internal Server Error: Creation failed

    Example:
        POST /api/v1/brains/platform
        {
            "neuron_count": 50000,
            "enable_ethics": true,
            "enable_curiosity": true
        }
    """
    try:
        brain = await service.create_platform_brain(
            neuron_count=request.neuron_count,
            enable_ethics=request.enable_ethics,
            enable_curiosity=request.enable_curiosity
        )
        return _brain_to_response(brain)

    except BrainCreationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/student", response_model=BrainResponse, status_code=status.HTTP_201_CREATED)
async def create_student_brain(
    request: CreateStudentBrainRequest,
    service: BrainService = Depends(get_brain_service)
):
    """
    Create a personal learning guide brain for a student.

    Business Logic:
        Student brains are COW clones of the platform brain for memory efficiency.
        They learn the student's unique patterns (pace, style, preferences).

    Returns:
        201 Created: Student brain created successfully
        400 Bad Request: Student already has a brain
        500 Internal Server Error: Creation failed

    Example:
        POST /api/v1/brains/student
        {
            "student_id": "550e8400-e29b-41d4-a716-446655440000",
            "neuron_count": 10000,
            "clone_from_platform": true
        }
    """
    try:
        brain = await service.create_student_brain(
            student_id=request.student_id,
            neuron_count=request.neuron_count,
            clone_from_platform=request.clone_from_platform
        )
        return _brain_to_response(brain)

    except BrainCreationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    service: BrainService = Depends(get_brain_service)
):
    """
    Make a prediction using the brain with optional LLM fallback.

    Business Logic:
        1. Neural inference (fast, free)
        2. Check confidence
        3. If confidence >= threshold: Use neural prediction
        4. If confidence < threshold: Fall back to LLM
        5. If LLM used: Learn from LLM response

    Returns:
        200 OK: Prediction successful
        404 Not Found: Brain not found
        500 Internal Server Error: Prediction failed

    Example:
        POST /api/v1/brains/predict
        {
            "brain_id": "550e8400-e29b-41d4-a716-446655440000",
            "features": [0.5, 0.3, 0.8, 0.2],
            "use_llm_fallback": true
        }
    """
    try:
        result = await service.predict(
            brain_id=request.brain_id,
            features=request.features,
            use_llm_fallback=request.use_llm_fallback
        )
        return PredictionResponse(**result)

    except BrainNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/learn", status_code=status.HTTP_204_NO_CONTENT)
async def learn(
    request: LearningRequest,
    service: BrainService = Depends(get_brain_service)
):
    """
    Teach the brain a new example through supervised learning.

    Business Logic:
        Explicit supervised learning where we provide ground truth.
        The brain adjusts its neural weights to learn this association.

    Returns:
        204 No Content: Learning successful
        404 Not Found: Brain not found
        500 Internal Server Error: Learning failed

    Example:
        POST /api/v1/brains/learn
        {
            "brain_id": "550e8400-e29b-41d4-a716-446655440000",
            "features": [0.5, 0.3, 0.8],
            "label": "positive",
            "confidence": 0.95
        }
    """
    try:
        await service.learn(
            brain_id=request.brain_id,
            features=request.features,
            label=request.label,
            confidence=request.confidence
        )
        return None  # 204 No Content

    except BrainNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BrainLearningError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/reinforce", status_code=status.HTTP_204_NO_CONTENT)
async def reinforce(
    request: ReinforcementRequest,
    service: BrainService = Depends(get_brain_service)
):
    """
    Reinforce brain behavior through reward-based learning.

    Business Logic:
        Reinforcement learning where the brain learns from outcomes.
        Positive rewards strengthen neural pathways, negative rewards weaken them.

    Returns:
        204 No Content: Reinforcement successful
        404 Not Found: Brain not found
        500 Internal Server Error: Reinforcement failed

    Example:
        POST /api/v1/brains/reinforce
        {
            "brain_id": "550e8400-e29b-41d4-a716-446655440000",
            "features": [0.5, 0.3, 0.8],
            "reward": 0.85
        }
    """
    try:
        await service.reinforce(
            brain_id=request.brain_id,
            features=request.features,
            reward=request.reward
        )
        return None  # 204 No Content

    except BrainNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{brain_id}", response_model=BrainResponse)
async def get_brain(
    brain_id: UUID,
    service: BrainService = Depends(get_brain_service)
):
    """
    Retrieve a brain instance by ID.

    Returns:
        200 OK: Brain found
        404 Not Found: Brain not found

    Example:
        GET /api/v1/brains/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        brain = await service.get_brain(brain_id)
        return _brain_to_response(brain)

    except BrainNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/student/{student_id}", response_model=BrainResponse)
async def get_student_brain(
    student_id: UUID,
    service: BrainService = Depends(get_brain_service)
):
    """
    Retrieve a student's personal brain.

    Returns:
        200 OK: Brain found
        404 Not Found: Student has no brain

    Example:
        GET /api/v1/brains/student/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        brain = await service.get_student_brain(student_id)
        return _brain_to_response(brain)

    except BrainNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/platform/instance", response_model=BrainResponse)
async def get_platform_brain(
    service: BrainService = Depends(get_brain_service)
):
    """
    Retrieve the platform brain.

    Returns:
        200 OK: Platform brain found
        404 Not Found: Platform brain not found

    Example:
        GET /api/v1/brains/platform/instance
    """
    try:
        brain = await service.get_platform_brain()
        return _brain_to_response(brain)

    except BrainNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================

def _brain_to_response(brain) -> BrainResponse:
    """Convert Brain entity to API response model."""
    return BrainResponse(
        brain_id=brain.brain_id,
        brain_type=brain.brain_type.value,
        owner_id=brain.owner_id,
        parent_brain_id=brain.parent_brain_id,
        created_at=brain.created_at.isoformat(),
        last_updated=brain.last_updated.isoformat(),
        state_file_path=brain.state_file_path,
        is_active=brain.is_active,
        total_interactions=brain.performance.total_interactions,
        neural_inference_count=brain.performance.neural_inference_count,
        llm_query_count=brain.performance.llm_query_count,
        neural_inference_rate=brain.performance.neural_inference_rate,
        average_confidence=brain.performance.average_confidence,
        average_accuracy=brain.performance.average_accuracy,
        is_cow_clone=brain.cow_stats.is_cow_clone,
        cow_efficiency_percent=brain.cow_stats.cow_efficiency_percent,
        strong_domains=brain.self_awareness.strong_domains,
        weak_domains=brain.self_awareness.weak_domains,
        bias_detections=brain.self_awareness.bias_detections
    )
