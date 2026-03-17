#!/usr/bin/env python3

"""
Advanced Assessment API Endpoints

WHAT: RESTful API for advanced assessment operations including
rubric-based grading, peer review, competency tracking, portfolios,
and project-based assessments.

WHERE: Called by frontend and other services for assessment management

WHY: Provides comprehensive assessment capabilities beyond simple quizzes,
enabling authentic assessment, competency-based evaluation, and rich feedback.

## Educational Context:

### Assessment Types Supported
- **Competency-Based**: Track mastery of specific skills against standards
- **Portfolio**: Collect and evaluate student work artifacts over time
- **Project-Based**: Multi-milestone assessments with deliverables
- **Peer Review**: Student-evaluated assignments with anonymity options

### Rubric-Based Grading
- **Holistic Rubrics**: Single score based on overall quality
- **Analytic Rubrics**: Separate scores for each criterion
- **Single-Point Rubrics**: Expectations with deviation notes
- **Performance Levels**: Customizable proficiency descriptors

### Feedback & Analytics
- **Rich Feedback**: Criterion-level comments with strengths/improvements
- **Peer Feedback**: Anonymous or attributed peer reviews
- **Analytics Dashboard**: Score distributions, pass rates, time metrics

## API Endpoints:
- POST /api/v1/assessments - Create advanced assessment
- GET /api/v1/assessments/{id} - Get assessment details
- PUT /api/v1/assessments/{id} - Update assessment
- POST /api/v1/assessments/{id}/publish - Publish assessment
- POST /api/v1/rubrics - Create assessment rubric
- POST /api/v1/submissions - Start submission
- PUT /api/v1/submissions/{id} - Update submission content
- POST /api/v1/submissions/{id}/submit - Submit for grading
- POST /api/v1/submissions/{id}/grade - Grade submission
- POST /api/v1/peer-reviews/assign - Assign peer reviewers
- POST /api/v1/peer-reviews/{id} - Submit peer review
- POST /api/v1/competencies - Create competency
- PUT /api/v1/competencies/progress - Update student competency
- POST /api/v1/portfolios/artifacts - Add portfolio artifact
- POST /api/v1/projects/milestones - Add project milestone
- GET /api/v1/analytics/assessments/{id} - Get assessment analytics

Author: Course Creator Platform
Version: 1.0.0
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field, validator

# Domain entities and enums
from content_management.domain.entities.advanced_assessment import (
    AssessmentType,
    ProficiencyLevel,
    ReviewType,
    SubmissionStatus
)

logger = logging.getLogger(__name__)

# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(
    prefix="/api/v1",
    tags=["advanced-assessments"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# ============================================================================
# Request/Response Models
# ============================================================================


class CreateAssessmentRequest(BaseModel):
    """
    WHAT: Request model for creating advanced assessments
    WHERE: POST /api/v1/assessments
    WHY: Captures all configuration for assessment creation
    """
    course_id: UUID = Field(..., description="Course this assessment belongs to")
    module_id: Optional[UUID] = Field(None, description="Optional module association")
    title: str = Field(..., min_length=3, max_length=500)
    description: str = Field(default="", max_length=5000)
    instructions: str = Field(default="", description="Student instructions")
    assessment_type: AssessmentType = Field(
        default=AssessmentType.RUBRIC,
        description="Type of assessment"
    )
    max_score: Decimal = Field(default=Decimal("100"), ge=0)
    passing_score: Decimal = Field(default=Decimal("70"), ge=0)
    weight: Decimal = Field(default=Decimal("1.0"), ge=0, le=1)
    max_attempts: int = Field(default=1, ge=1, le=100)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    late_submission_allowed: bool = False
    late_penalty_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    peer_review_enabled: bool = False
    peer_review_type: ReviewType = Field(default=ReviewType.DOUBLE_BLIND)
    peer_review_count: int = Field(default=3, ge=1, le=10)
    grading_criteria: Optional[str] = None
    submission_guidelines: Optional[str] = None


class UpdateAssessmentRequest(BaseModel):
    """
    WHAT: Request model for updating assessments
    WHERE: PUT /api/v1/assessments/{id}
    WHY: Allows partial updates to assessment configuration
    """
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = None
    instructions: Optional[str] = None
    max_score: Optional[Decimal] = Field(None, ge=0)
    passing_score: Optional[Decimal] = Field(None, ge=0)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    late_submission_allowed: Optional[bool] = None
    late_penalty_percentage: Optional[Decimal] = Field(None, ge=0, le=100)


class CreateRubricRequest(BaseModel):
    """
    WHAT: Request model for creating rubrics
    WHERE: POST /api/v1/rubrics
    WHY: Enables structured rubric creation with criteria and levels
    """
    assessment_id: UUID = Field(..., description="Assessment this rubric evaluates")
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(default="", max_length=2000)
    rubric_type: str = Field(default="analytic", description="holistic|analytic|single_point")
    criteria: List[Dict[str, Any]] = Field(
        ...,
        description="List of criterion definitions with performance levels"
    )
    is_template: bool = Field(default=False)


class RubricCriterionRequest(BaseModel):
    """
    WHAT: Request model for adding criterion to rubric
    WHERE: POST /api/v1/rubrics/{id}/criteria
    WHY: Allows adding criteria individually
    """
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    max_points: int = Field(..., ge=0)
    weight: Decimal = Field(default=Decimal("1.0"), ge=0)
    performance_levels: List[Dict[str, Any]] = Field(
        ...,
        description="List of performance level definitions"
    )


class StartSubmissionRequest(BaseModel):
    """
    WHAT: Request model for starting a submission
    WHERE: POST /api/v1/submissions
    WHY: Initiates student's work on an assessment
    """
    assessment_id: UUID
    student_id: UUID


class UpdateSubmissionRequest(BaseModel):
    """
    WHAT: Request model for updating submission content
    WHERE: PUT /api/v1/submissions/{id}
    WHY: Saves student work in progress
    """
    content: Dict[str, Any] = Field(..., description="Submission content/answers")
    reflections: Optional[str] = None


class GradeSubmissionRequest(BaseModel):
    """
    WHAT: Request model for grading submissions
    WHERE: POST /api/v1/submissions/{id}/grade
    WHY: Records evaluation with optional criterion-level scores
    """
    grader_id: UUID
    total_score: Decimal = Field(..., ge=0)
    criterion_scores: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Criterion-level scores: {criterion_id: {proficiency_level, points, feedback}}"
    )
    feedback: str = Field(default="", max_length=10000)
    passed: Optional[bool] = None


class RequestRevisionRequest(BaseModel):
    """
    WHAT: Request model for requesting revision
    WHERE: POST /api/v1/submissions/{id}/revision
    WHY: Enables feedback loop for improvement
    """
    grader_id: UUID
    revision_notes: str = Field(..., min_length=10, max_length=5000)
    criterion_feedback: Optional[List[Dict[str, Any]]] = None


class AssignPeerReviewersRequest(BaseModel):
    """
    WHAT: Request model for assigning peer reviewers
    WHERE: POST /api/v1/peer-reviews/assign
    WHY: Configures who reviews which submission
    """
    assessment_id: UUID
    submission_id: UUID
    reviewer_ids: List[UUID]


class SubmitPeerReviewRequest(BaseModel):
    """
    WHAT: Request model for submitting peer review
    WHERE: POST /api/v1/peer-reviews/{assignment_id}
    WHY: Records peer's evaluation
    """
    reviewer_id: UUID
    criterion_scores: Dict[str, Any] = Field(..., description="Scores by criterion")
    total_score: Decimal = Field(..., ge=0)
    feedback: str = Field(..., min_length=10, max_length=5000)
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None


class CreateCompetencyRequest(BaseModel):
    """
    WHAT: Request model for creating competencies
    WHERE: POST /api/v1/competencies
    WHY: Defines measurable skills/knowledge areas
    """
    name: str = Field(..., min_length=3, max_length=200)
    code: str = Field(..., min_length=2, max_length=50, description="Unique competency code")
    description: str = Field(..., max_length=2000)
    organization_id: UUID
    category: str = Field(default="", max_length=100)
    parent_id: Optional[UUID] = None
    level: int = Field(default=1, ge=1)
    required_proficiency: ProficiencyLevel = Field(default=ProficiencyLevel.PROFICIENT)
    evidence_requirements: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class UpdateCompetencyProgressRequest(BaseModel):
    """
    WHAT: Request model for updating student competency progress
    WHERE: PUT /api/v1/competencies/progress
    WHY: Tracks mastery level changes
    """
    student_id: UUID
    competency_id: UUID
    assessment_id: UUID
    demonstrated_level: ProficiencyLevel
    evidence_notes: Optional[str] = None


class AddPortfolioArtifactRequest(BaseModel):
    """
    WHAT: Request model for adding portfolio artifacts
    WHERE: POST /api/v1/portfolios/artifacts
    WHY: Collects student work evidence
    """
    submission_id: UUID
    student_id: UUID
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., max_length=2000)
    artifact_type: str = Field(..., description="document|image|video|code|presentation|other")
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    student_reflection: str = Field(default="", max_length=5000)
    context: str = Field(default="", max_length=1000)
    learning_demonstrated: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    @validator('content_url', 'content_text', 'attachments', pre=True, always=True)
    def validate_content(cls, v, values):
        """At least one content field must be provided"""
        return v


class UpdateArtifactRequest(BaseModel):
    """
    WHAT: Request model for updating portfolio artifacts
    WHERE: PUT /api/v1/portfolios/artifacts/{id}
    WHY: Allows refinement of portfolio items
    """
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    student_reflection: Optional[str] = None
    learning_demonstrated: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class AddMilestoneRequest(BaseModel):
    """
    WHAT: Request model for adding project milestones
    WHERE: POST /api/v1/projects/milestones
    WHY: Structures project-based assessments
    """
    assessment_id: UUID
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., max_length=2000)
    due_date: Optional[datetime] = None
    weight: Decimal = Field(default=Decimal("1.0"), ge=0, le=1)
    max_points: int = Field(default=20, ge=0)
    required_deliverables: Optional[List[str]] = None
    acceptance_criteria: Optional[str] = None
    sort_order: int = Field(default=0, ge=0)
    rubric_id: Optional[UUID] = None


class UpdateMilestoneRequest(BaseModel):
    """
    WHAT: Request model for updating milestones
    WHERE: PUT /api/v1/projects/milestones/{id}
    WHY: Allows milestone modifications
    """
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    weight: Optional[Decimal] = Field(None, ge=0, le=1)
    max_points: Optional[int] = Field(None, ge=0)
    required_deliverables: Optional[List[str]] = None


class AssessmentResponse(BaseModel):
    """
    WHAT: Response model for assessment operations
    WHERE: Returned by assessment endpoints
    WHY: Consistent API response format
    """
    id: UUID
    title: str
    assessment_type: str
    status: str
    max_score: Decimal
    passing_score: Decimal
    due_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    """
    WHAT: Response model for submission operations
    WHERE: Returned by submission endpoints
    WHY: Consistent submission data format
    """
    id: UUID
    assessment_id: UUID
    student_id: UUID
    status: str
    attempt_number: int
    final_score: Optional[Decimal]
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    """
    WHAT: Response model for assessment analytics
    WHERE: GET /api/v1/analytics/assessments/{id}
    WHY: Provides aggregate statistics
    """
    assessment_id: UUID
    submissions_count: int
    completed_count: int
    pass_count: int
    fail_count: int
    average_score: Decimal
    pass_rate: Decimal

    class Config:
        from_attributes = True


# ============================================================================
# Dependency Injection
# ============================================================================


def get_assessment_service():
    """
    WHAT: Dependency injection for advanced assessment service
    WHERE: Used by all assessment endpoints
    WHY: Provides singleton service instance via DI container
    """
    try:
        from main import container
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Service container not initialized"
            )
        return container.get_advanced_assessment_service()
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service configuration error"
        )


# ============================================================================
# Assessment CRUD Endpoints
# ============================================================================


@router.post("/assessments", status_code=status.HTTP_201_CREATED)
async def create_assessment(
    request: CreateAssessmentRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Creates a new advanced assessment
    WHERE: POST /api/v1/assessments
    WHY: Enables instructors to create various assessment types

    Educational Use Cases:
    - Create rubric-based assignments
    - Set up peer review activities
    - Configure competency-based assessments
    - Build project-based assessments with milestones

    Args:
        request: Assessment configuration
        service: Injected assessment service

    Returns:
        Created assessment with ID

    Raises:
        HTTPException 400: Invalid configuration
        HTTPException 500: Creation failed
    """
    try:
        assessment = await service.create_assessment(
            course_id=request.course_id,
            title=request.title,
            description=request.description,
            instructions=request.instructions,
            assessment_type=request.assessment_type,
            max_score=request.max_score,
            passing_score=request.passing_score,
            weight=request.weight,
            max_attempts=request.max_attempts,
            time_limit_minutes=request.time_limit_minutes,
            due_date=request.due_date,
            available_from=request.available_from,
            available_until=request.available_until,
            late_submission_allowed=request.late_submission_allowed,
            late_penalty_percentage=request.late_penalty_percentage,
            module_id=request.module_id,
            peer_review_enabled=request.peer_review_enabled,
            peer_review_type=request.peer_review_type,
            peer_review_count=request.peer_review_count,
            grading_criteria=request.grading_criteria,
            submission_guidelines=request.submission_guidelines
        )

        return {
            "id": str(assessment.id),
            "title": assessment.title,
            "assessment_type": assessment.assessment_type.value,
            "status": assessment.status.value,
            "created_at": assessment.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to create assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/assessments/{assessment_id}")
async def get_assessment(
    assessment_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Retrieves assessment details
    WHERE: GET /api/v1/assessments/{id}
    WHY: Provides full assessment configuration for display/editing
    """
    try:
        assessment = await service.get_assessment(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )

        return {
            "id": str(assessment.id),
            "course_id": str(assessment.course_id),
            "title": assessment.title,
            "description": assessment.description,
            "instructions": assessment.instructions,
            "assessment_type": assessment.assessment_type.value,
            "status": assessment.status.value,
            "max_score": str(assessment.max_score),
            "passing_score": str(assessment.passing_score),
            "weight": str(assessment.weight),
            "max_attempts": assessment.max_attempts,
            "time_limit_minutes": assessment.time_limit_minutes,
            "due_date": assessment.due_date.isoformat() if assessment.due_date else None,
            "available_from": assessment.available_from.isoformat() if assessment.available_from else None,
            "available_until": assessment.available_until.isoformat() if assessment.available_until else None,
            "late_submission_allowed": assessment.late_submission_allowed,
            "late_penalty_percentage": str(assessment.late_penalty_percentage),
            "peer_review_enabled": assessment.peer_review_enabled,
            "peer_review_type": assessment.peer_review_type.value if assessment.peer_review_type else None,
            "peer_review_count": assessment.peer_review_count,
            "created_at": assessment.created_at.isoformat(),
            "updated_at": assessment.updated_at.isoformat() if assessment.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/assessments/{assessment_id}")
async def update_assessment(
    assessment_id: UUID,
    request: UpdateAssessmentRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Updates assessment configuration
    WHERE: PUT /api/v1/assessments/{id}
    WHY: Allows modification of assessment settings
    """
    try:
        # Build update kwargs from non-None values
        update_data = {
            k: v for k, v in request.dict().items()
            if v is not None
        }

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )

        assessment = await service.update_assessment(assessment_id, **update_data)

        return {
            "id": str(assessment.id),
            "title": assessment.title,
            "status": assessment.status.value,
            "updated_at": assessment.updated_at.isoformat() if assessment.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/assessments/{assessment_id}/publish")
async def publish_assessment(
    assessment_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Publishes assessment for student access
    WHERE: POST /api/v1/assessments/{id}/publish
    WHY: Makes assessment available after configuration complete
    """
    try:
        assessment = await service.publish_assessment(assessment_id)

        return {
            "id": str(assessment.id),
            "title": assessment.title,
            "status": assessment.status.value,
            "published_at": assessment.published_at.isoformat() if assessment.published_at else None
        }

    except Exception as e:
        logger.error(f"Failed to publish assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/assessments/{assessment_id}")
async def archive_assessment(
    assessment_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, str]:
    """
    WHAT: Archives (soft deletes) an assessment
    WHERE: DELETE /api/v1/assessments/{id}
    WHY: Removes from active use while preserving data
    """
    try:
        await service.archive_assessment(assessment_id)
        return {"message": "Assessment archived successfully"}

    except Exception as e:
        logger.error(f"Failed to archive assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Rubric Endpoints
# ============================================================================


@router.post("/rubrics", status_code=status.HTTP_201_CREATED)
async def create_rubric(
    request: CreateRubricRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Creates a grading rubric for an assessment
    WHERE: POST /api/v1/rubrics
    WHY: Enables structured, consistent evaluation

    Rubric Types:
    - Holistic: Single overall score with general descriptors
    - Analytic: Separate scores for each criterion
    - Single-Point: Expectations with space for deviations
    """
    try:
        rubric = await service.create_rubric(
            assessment_id=request.assessment_id,
            name=request.name,
            description=request.description,
            rubric_type=request.rubric_type,
            criteria=request.criteria,
            is_template=request.is_template
        )

        return {
            "id": str(rubric.id),
            "assessment_id": str(rubric.assessment_id),
            "name": rubric.name,
            "rubric_type": rubric.rubric_type,
            "criteria_count": len(rubric.criteria) if rubric.criteria else 0,
            "created_at": rubric.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to create rubric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/rubrics/{rubric_id}")
async def get_rubric(
    rubric_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Retrieves rubric with all criteria and levels
    WHERE: GET /api/v1/rubrics/{id}
    WHY: Provides full rubric for grading interface
    """
    try:
        rubric = await service.get_rubric(rubric_id)
        if not rubric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rubric not found"
            )

        return {
            "id": str(rubric.id),
            "assessment_id": str(rubric.assessment_id),
            "name": rubric.name,
            "description": rubric.description,
            "rubric_type": rubric.rubric_type,
            "criteria": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "description": c.description,
                    "max_points": c.max_points,
                    "weight": str(c.weight),
                    "performance_levels": [
                        {
                            "level": pl.level,
                            "name": pl.name,
                            "description": pl.description,
                            "points": pl.points,
                            "percentage_of_max": str(pl.percentage_of_max)
                        }
                        for pl in c.performance_levels
                    ] if c.performance_levels else []
                }
                for c in rubric.criteria
            ] if rubric.criteria else [],
            "is_template": rubric.is_template,
            "created_at": rubric.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rubric {rubric_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Submission Endpoints
# ============================================================================


@router.post("/submissions", status_code=status.HTTP_201_CREATED)
async def start_submission(
    request: StartSubmissionRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Starts a new submission attempt
    WHERE: POST /api/v1/submissions
    WHY: Initiates student's work on assessment
    """
    try:
        submission = await service.start_submission(
            assessment_id=request.assessment_id,
            student_id=request.student_id
        )

        return {
            "id": str(submission.id),
            "assessment_id": str(submission.assessment_id),
            "student_id": str(submission.student_id),
            "status": submission.status.value,
            "attempt_number": submission.attempt_number,
            "started_at": submission.started_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to start submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/submissions/{submission_id}")
async def update_submission(
    submission_id: UUID,
    request: UpdateSubmissionRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Updates submission content (auto-save)
    WHERE: PUT /api/v1/submissions/{id}
    WHY: Enables save-as-you-go functionality
    """
    try:
        submission = await service.update_submission_content(
            submission_id=submission_id,
            content=request.content,
            reflections=request.reflections
        )

        return {
            "id": str(submission.id),
            "status": submission.status.value,
            "last_saved_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to update submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/submissions/{submission_id}/submit")
async def submit_assessment(
    submission_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Submits assessment for grading
    WHERE: POST /api/v1/submissions/{id}/submit
    WHY: Finalizes submission and enters grading queue
    """
    try:
        submission = await service.submit_assessment(submission_id)

        return {
            "id": str(submission.id),
            "status": submission.status.value,
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
            "is_late": submission.is_late
        }

    except Exception as e:
        logger.error(f"Failed to submit {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/submissions/{submission_id}")
async def get_submission(
    submission_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Retrieves submission details
    WHERE: GET /api/v1/submissions/{id}
    WHY: Provides submission data for viewing/grading
    """
    try:
        submission = await service.get_submission(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )

        return {
            "id": str(submission.id),
            "assessment_id": str(submission.assessment_id),
            "student_id": str(submission.student_id),
            "status": submission.status.value,
            "attempt_number": submission.attempt_number,
            "content": submission.content,
            "reflections": submission.reflections,
            "started_at": submission.started_at.isoformat(),
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
            "is_late": submission.is_late,
            "final_score": str(submission.final_score) if submission.final_score else None,
            "passed": submission.passed,
            "instructor_feedback": submission.instructor_feedback,
            "graded_at": submission.graded_at.isoformat() if submission.graded_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Grading Endpoints
# ============================================================================


@router.post("/submissions/{submission_id}/grade")
async def grade_submission(
    submission_id: UUID,
    request: GradeSubmissionRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Grades a submission with rubric-based evaluation
    WHERE: POST /api/v1/submissions/{id}/grade
    WHY: Records evaluation with optional criterion-level detail

    Grading Features:
    - Overall score with optional criterion breakdown
    - Automatic pass/fail determination
    - Late penalty calculation
    - Rich feedback support
    """
    try:
        submission, evaluations = await service.grade_submission(
            submission_id=submission_id,
            grader_id=request.grader_id,
            total_score=request.total_score,
            criterion_scores=request.criterion_scores,
            feedback=request.feedback,
            passed=request.passed
        )

        return {
            "id": str(submission.id),
            "status": submission.status.value,
            "final_score": str(submission.final_score),
            "passed": submission.passed,
            "graded_at": submission.graded_at.isoformat() if submission.graded_at else None,
            "evaluations_count": len(evaluations)
        }

    except Exception as e:
        logger.error(f"Failed to grade submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/submissions/{submission_id}/revision")
async def request_revision(
    submission_id: UUID,
    request: RequestRevisionRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Requests revision with feedback
    WHERE: POST /api/v1/submissions/{id}/revision
    WHY: Enables improvement cycle before final grade
    """
    try:
        submission = await service.request_revision(
            submission_id=submission_id,
            grader_id=request.grader_id,
            revision_notes=request.revision_notes,
            criterion_feedback=request.criterion_feedback
        )

        return {
            "id": str(submission.id),
            "status": submission.status.value,
            "revision_count": submission.revision_count
        }

    except Exception as e:
        logger.error(f"Failed to request revision for {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/assessments/{assessment_id}/grading-queue")
async def get_grading_queue(
    assessment_id: UUID,
    instructor_id: UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=100),
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Gets submissions awaiting grading
    WHERE: GET /api/v1/assessments/{id}/grading-queue
    WHY: Provides efficient grading workflow
    """
    try:
        submissions = await service.get_submissions_to_grade(
            assessment_id=assessment_id,
            instructor_id=instructor_id,
            limit=limit
        )

        return {
            "assessment_id": str(assessment_id),
            "count": len(submissions),
            "submissions": [
                {
                    "id": str(s.id),
                    "student_id": str(s.student_id),
                    "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                    "is_late": s.is_late,
                    "attempt_number": s.attempt_number
                }
                for s in submissions
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get grading queue for {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Peer Review Endpoints
# ============================================================================


@router.post("/peer-reviews/assign")
async def assign_peer_reviewers(
    request: AssignPeerReviewersRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Assigns peer reviewers to a submission
    WHERE: POST /api/v1/peer-reviews/assign
    WHY: Configures peer review workflow
    """
    try:
        assignments = await service.assign_peer_reviewers(
            assessment_id=request.assessment_id,
            submission_id=request.submission_id,
            reviewer_ids=request.reviewer_ids
        )

        return {
            "submission_id": str(request.submission_id),
            "assignments_created": len(assignments),
            "reviewer_ids": [str(a.reviewer_id) for a in assignments]
        }

    except Exception as e:
        logger.error(f"Failed to assign peer reviewers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/peer-reviews/{assignment_id}")
async def submit_peer_review(
    assignment_id: UUID,
    request: SubmitPeerReviewRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Submits a peer review
    WHERE: POST /api/v1/peer-reviews/{assignment_id}
    WHY: Records peer's evaluation of submission
    """
    try:
        review = await service.submit_peer_review(
            assignment_id=assignment_id,
            reviewer_id=request.reviewer_id,
            criterion_scores=request.criterion_scores,
            total_score=request.total_score,
            feedback=request.feedback,
            strengths=request.strengths,
            areas_for_improvement=request.areas_for_improvement
        )

        return {
            "id": str(review.id),
            "assignment_id": str(assignment_id),
            "overall_score": str(review.overall_score),
            "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None
        }

    except Exception as e:
        logger.error(f"Failed to submit peer review for {assignment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Competency Endpoints
# ============================================================================


@router.post("/competencies", status_code=status.HTTP_201_CREATED)
async def create_competency(
    request: CreateCompetencyRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Creates a competency definition
    WHERE: POST /api/v1/competencies
    WHY: Defines measurable learning outcomes
    """
    try:
        competency = await service.create_competency(
            name=request.name,
            code=request.code,
            description=request.description,
            organization_id=request.organization_id,
            category=request.category,
            parent_id=request.parent_id,
            level=request.level,
            required_proficiency=request.required_proficiency,
            evidence_requirements=request.evidence_requirements,
            tags=request.tags
        )

        return {
            "id": str(competency.id),
            "code": competency.code,
            "name": competency.name,
            "required_proficiency": competency.required_proficiency.value,
            "created_at": competency.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to create competency: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/competencies/progress")
async def update_competency_progress(
    request: UpdateCompetencyProgressRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Updates student's competency progress
    WHERE: PUT /api/v1/competencies/progress
    WHY: Tracks mastery level changes over time
    """
    try:
        progress = await service.update_student_competency(
            student_id=request.student_id,
            competency_id=request.competency_id,
            assessment_id=request.assessment_id,
            demonstrated_level=request.demonstrated_level,
            evidence_notes=request.evidence_notes
        )

        return {
            "id": str(progress.id),
            "student_id": str(progress.student_id),
            "competency_id": str(progress.competency_id),
            "current_level": progress.current_level.value,
            "previous_level": progress.previous_level.value if progress.previous_level else None,
            "updated_at": progress.level_achieved_at.isoformat() if progress.level_achieved_at else None
        }

    except Exception as e:
        logger.error(f"Failed to update competency progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/competencies/{competency_id}/students/{student_id}/progress")
async def get_student_competency_progress(
    competency_id: UUID,
    student_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Gets student's progress on a competency
    WHERE: GET /api/v1/competencies/{id}/students/{id}/progress
    WHY: Shows mastery level and evidence history
    """
    try:
        progress = await service.get_student_competency_progress(
            student_id=student_id,
            competency_id=competency_id
        )

        if not progress:
            return {
                "student_id": str(student_id),
                "competency_id": str(competency_id),
                "current_level": ProficiencyLevel.NOT_DEMONSTRATED.value,
                "evidence_submissions": []
            }

        return {
            "id": str(progress.id),
            "student_id": str(progress.student_id),
            "competency_id": str(progress.competency_id),
            "current_level": progress.current_level.value,
            "previous_level": progress.previous_level.value if progress.previous_level else None,
            "evidence_submissions": progress.evidence_submissions or [],
            "first_demonstrated_at": progress.first_demonstrated_at.isoformat() if progress.first_demonstrated_at else None,
            "level_achieved_at": progress.level_achieved_at.isoformat() if progress.level_achieved_at else None
        }

    except Exception as e:
        logger.error(f"Failed to get competency progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Portfolio Endpoints
# ============================================================================


@router.post("/portfolios/artifacts", status_code=status.HTTP_201_CREATED)
async def add_portfolio_artifact(
    request: AddPortfolioArtifactRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Adds an artifact to student portfolio
    WHERE: POST /api/v1/portfolios/artifacts
    WHY: Collects evidence of learning over time
    """
    try:
        artifact = await service.add_portfolio_artifact(
            submission_id=request.submission_id,
            student_id=request.student_id,
            title=request.title,
            description=request.description,
            artifact_type=request.artifact_type,
            content_url=request.content_url,
            content_text=request.content_text,
            attachments=request.attachments,
            student_reflection=request.student_reflection,
            context=request.context,
            learning_demonstrated=request.learning_demonstrated,
            tags=request.tags
        )

        return {
            "id": str(artifact.id),
            "title": artifact.title,
            "artifact_type": artifact.artifact_type,
            "created_at": artifact.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to add portfolio artifact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/portfolios/artifacts/{artifact_id}")
async def update_artifact(
    artifact_id: UUID,
    request: UpdateArtifactRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Updates a portfolio artifact
    WHERE: PUT /api/v1/portfolios/artifacts/{id}
    WHY: Allows refinement of portfolio items
    """
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        artifact = await service.update_artifact(artifact_id, **update_data)

        return {
            "id": str(artifact.id),
            "title": artifact.title,
            "updated_at": artifact.updated_at.isoformat() if artifact.updated_at else None
        }

    except Exception as e:
        logger.error(f"Failed to update artifact {artifact_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/portfolios/artifacts/{artifact_id}")
async def delete_artifact(
    artifact_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, str]:
    """
    WHAT: Deletes a portfolio artifact
    WHERE: DELETE /api/v1/portfolios/artifacts/{id}
    WHY: Removes unwanted portfolio items
    """
    try:
        await service.delete_artifact(artifact_id)
        return {"message": "Artifact deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete artifact {artifact_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/students/{student_id}/portfolio")
async def get_student_portfolio(
    student_id: UUID,
    artifact_type: Optional[str] = Query(None),
    limit: int = Query(default=50, ge=1, le=100),
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Gets student's portfolio artifacts
    WHERE: GET /api/v1/students/{id}/portfolio
    WHY: Displays collected learning evidence
    """
    try:
        artifacts = await service.get_student_portfolio(
            student_id=student_id,
            artifact_type=artifact_type,
            limit=limit
        )

        return {
            "student_id": str(student_id),
            "count": len(artifacts),
            "artifacts": [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "artifact_type": a.artifact_type,
                    "description": a.description,
                    "student_reflection": a.student_reflection,
                    "learning_demonstrated": a.learning_demonstrated,
                    "tags": a.tags,
                    "created_at": a.created_at.isoformat()
                }
                for a in artifacts
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get portfolio for student {student_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Project/Milestone Endpoints
# ============================================================================


@router.post("/projects/milestones", status_code=status.HTTP_201_CREATED)
async def add_milestone(
    request: AddMilestoneRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Adds a milestone to project-based assessment
    WHERE: POST /api/v1/projects/milestones
    WHY: Structures project with checkpoints
    """
    try:
        milestone = await service.add_milestone(
            assessment_id=request.assessment_id,
            name=request.name,
            description=request.description,
            due_date=request.due_date,
            weight=request.weight,
            max_points=request.max_points,
            required_deliverables=request.required_deliverables,
            acceptance_criteria=request.acceptance_criteria,
            sort_order=request.sort_order,
            rubric_id=request.rubric_id
        )

        return {
            "id": str(milestone.id),
            "assessment_id": str(milestone.assessment_id),
            "name": milestone.name,
            "sort_order": milestone.sort_order,
            "due_date": milestone.due_date.isoformat() if milestone.due_date else None,
            "created_at": milestone.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to add milestone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/projects/milestones/{milestone_id}")
async def update_milestone(
    milestone_id: UUID,
    request: UpdateMilestoneRequest,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Updates a project milestone
    WHERE: PUT /api/v1/projects/milestones/{id}
    WHY: Allows modification of milestone details
    """
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        milestone = await service.update_milestone(milestone_id, **update_data)

        return {
            "id": str(milestone.id),
            "name": milestone.name,
            "updated_at": milestone.updated_at.isoformat() if milestone.updated_at else None
        }

    except Exception as e:
        logger.error(f"Failed to update milestone {milestone_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/assessments/{assessment_id}/milestones")
async def get_assessment_milestones(
    assessment_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Gets all milestones for an assessment
    WHERE: GET /api/v1/assessments/{id}/milestones
    WHY: Lists project structure
    """
    try:
        milestones = await service.get_assessment_milestones(assessment_id)

        return {
            "assessment_id": str(assessment_id),
            "count": len(milestones),
            "milestones": [
                {
                    "id": str(m.id),
                    "name": m.name,
                    "description": m.description,
                    "sort_order": m.sort_order,
                    "max_points": m.max_points,
                    "weight": str(m.weight),
                    "due_date": m.due_date.isoformat() if m.due_date else None,
                    "required_deliverables": m.required_deliverables,
                    "acceptance_criteria": m.acceptance_criteria
                }
                for m in sorted(milestones, key=lambda x: x.sort_order)
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get milestones for {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Analytics Endpoints
# ============================================================================


@router.get("/analytics/assessments/{assessment_id}")
async def get_assessment_analytics(
    assessment_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Gets aggregate analytics for an assessment
    WHERE: GET /api/v1/analytics/assessments/{id}
    WHY: Provides performance insights for instructors

    Metrics Included:
    - Submission counts by status
    - Pass/fail rates
    - Score statistics (average, median, range)
    - Completion rates
    """
    try:
        analytics = await service.get_assessment_analytics(assessment_id)

        if not analytics:
            return {
                "assessment_id": str(assessment_id),
                "submissions_count": 0,
                "completed_count": 0,
                "in_progress_count": 0,
                "pass_count": 0,
                "fail_count": 0,
                "average_score": None,
                "median_score": None,
                "highest_score": None,
                "lowest_score": None,
                "pass_rate": None
            }

        return {
            "assessment_id": str(analytics.assessment_id),
            "submissions_count": analytics.submissions_count,
            "completed_count": analytics.completed_count,
            "in_progress_count": analytics.in_progress_count,
            "pass_count": analytics.pass_count,
            "fail_count": analytics.fail_count,
            "average_score": str(analytics.average_score) if analytics.average_score else None,
            "median_score": str(analytics.median_score) if analytics.median_score else None,
            "highest_score": str(analytics.highest_score) if analytics.highest_score else None,
            "lowest_score": str(analytics.lowest_score) if analytics.lowest_score else None,
            "pass_rate": str(analytics.pass_rate) if analytics.pass_rate else None,
            "calculated_at": analytics.calculated_at.isoformat() if analytics.calculated_at else None
        }

    except Exception as e:
        logger.error(f"Failed to get analytics for {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/analytics/courses/{course_id}/assessments")
async def get_course_assessment_summary(
    course_id: UUID,
    service=Depends(get_assessment_service)
) -> Dict[str, Any]:
    """
    WHAT: Gets assessment summary for entire course
    WHERE: GET /api/v1/analytics/courses/{id}/assessments
    WHY: Provides course-level performance overview
    """
    try:
        # Get all assessments for course
        assessments = await service.get_course_assessments(course_id)

        summaries = []
        for assessment in assessments:
            analytics = await service.get_assessment_analytics(assessment.id)
            summaries.append({
                "assessment_id": str(assessment.id),
                "title": assessment.title,
                "assessment_type": assessment.assessment_type.value,
                "submissions_count": analytics.submissions_count if analytics else 0,
                "pass_rate": str(analytics.pass_rate) if analytics and analytics.pass_rate else None,
                "average_score": str(analytics.average_score) if analytics and analytics.average_score else None
            })

        return {
            "course_id": str(course_id),
            "assessment_count": len(assessments),
            "assessments": summaries
        }

    except Exception as e:
        logger.error(f"Failed to get course assessment summary for {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
