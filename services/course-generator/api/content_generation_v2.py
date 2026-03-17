"""
Content Generation V2 API Endpoints

WHAT: FastAPI router implementing REST endpoints for AI-powered content generation V2
WHERE: Mounted at /api/v2/generation in course-generator service
WHY: Provides HTTP interface for content generation operations including
     request management, templates, refinements, batches, and analytics

Enhancement 4: AI-Powered Content Generation V2

Endpoint Categories:
1. Generation Requests - Create, retrieve, and process generation requests
2. Generation Results - Access generated content and quality scores
3. Templates - Manage customizable generation templates
4. Refinements - Content improvement workflow
5. Batch Operations - Bulk content generation
6. Analytics - Performance and quality metrics
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from course_generator.domain.entities.content_generation_v2 import (
    GenerationContentType,
    GenerationStatus,
    QualityLevel,
    RefinementType,
    BatchStatus,
    TemplateCategory,
    ContentGenerationException,
    InvalidGenerationParametersException,
    GenerationTimeoutException,
    QualityThresholdNotMetException,
    MaxRefinementsExceededException,
    BatchSizeLimitException,
    TemplateNotFoundException
)


# ============================================================================
# PYDANTIC REQUEST/RESPONSE MODELS
# ============================================================================

class CreateGenerationRequestDTO(BaseModel):
    """
    WHAT: DTO for creating a new generation request
    WHERE: POST /requests endpoint
    WHY: Validates input parameters for generation request
    """
    course_id: UUID = Field(..., description="Course to generate content for")
    content_type: GenerationContentType = Field(..., description="Type of content to generate")
    requester_id: UUID = Field(..., description="User requesting generation")
    organization_id: Optional[UUID] = Field(None, description="Organization context")
    module_id: Optional[UUID] = Field(None, description="Specific module for content")
    template_id: Optional[UUID] = Field(None, description="Template to use")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")
    difficulty_level: str = Field("intermediate", description="Target difficulty level")
    target_audience: str = Field("general", description="Target audience")
    language: str = Field("en", description="Content language")
    use_rag: bool = Field(True, description="Whether to use RAG enhancement")
    use_cache: bool = Field(True, description="Whether to use caching")


class GenerationRequestDTO(BaseModel):
    """
    WHAT: DTO for generation request response
    WHERE: Response from request endpoints
    WHY: Provides consistent request information
    """
    id: UUID
    course_id: UUID
    content_type: GenerationContentType
    requester_id: UUID
    organization_id: Optional[UUID]
    module_id: Optional[UUID]
    template_id: Optional[UUID]
    status: GenerationStatus
    parameters: Dict[str, Any]
    difficulty_level: str
    target_audience: str
    language: str
    use_rag: bool
    use_cache: bool
    result_id: Optional[UUID]
    error_message: Optional[str]
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class GenerationResultDTO(BaseModel):
    """
    WHAT: DTO for generation result response
    WHERE: Response from result endpoints
    WHY: Provides generated content with metadata
    """
    id: UUID
    request_id: UUID
    course_id: UUID
    content_type: GenerationContentType
    raw_output: str
    processed_content: Dict[str, Any]
    quality_score_id: Optional[UUID]
    quality_level: QualityLevel
    model_used: str
    generation_method: str
    rag_context_used: bool
    cached: bool
    cache_key: Optional[str]
    version: int
    parent_result_id: Optional[UUID]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class QualityScoreDTO(BaseModel):
    """
    WHAT: DTO for quality score response
    WHERE: Response from quality endpoints
    WHY: Provides detailed quality metrics
    """
    id: UUID
    result_id: UUID
    accuracy_score: int
    relevance_score: int
    completeness_score: int
    clarity_score: int
    structure_score: int
    engagement_score: int
    difficulty_alignment_score: int
    overall_score: int
    quality_level: QualityLevel
    scoring_method: str
    scorer_id: Optional[UUID]
    confidence: float
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateTemplateDTO(BaseModel):
    """
    WHAT: DTO for creating a new template
    WHERE: POST /templates endpoint
    WHY: Validates template creation input
    """
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: str = Field(..., description="Template description")
    content_type: GenerationContentType = Field(..., description="Content type")
    category: TemplateCategory = Field(TemplateCategory.STANDARD, description="Category")
    system_prompt: str = Field(..., description="System prompt for AI")
    user_prompt_template: str = Field(..., description="User prompt with variables")
    required_variables: List[str] = Field(default_factory=list, description="Required variables")
    creator_id: UUID = Field(..., description="User creating template")
    organization_id: Optional[UUID] = Field(None, description="Organization scope")
    is_global: bool = Field(False, description="Whether globally available")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output JSON schema")
    default_parameters: Optional[Dict[str, Any]] = Field(None, description="Default parameters")
    min_quality_score: int = Field(60, ge=0, le=100, description="Minimum quality threshold")


class TemplateDTO(BaseModel):
    """
    WHAT: DTO for template response
    WHERE: Response from template endpoints
    WHY: Provides template information
    """
    id: UUID
    name: str
    description: str
    content_type: GenerationContentType
    category: TemplateCategory
    system_prompt: str
    user_prompt_template: str
    required_variables: List[str]
    default_parameters: Dict[str, Any]
    creator_id: Optional[UUID]
    organization_id: Optional[UUID]
    is_global: bool
    is_active: bool
    is_archived: bool
    min_quality_score: int
    usage_count: int
    success_count: int
    avg_quality_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateRefinementDTO(BaseModel):
    """
    WHAT: DTO for creating a refinement request
    WHERE: POST /refinements endpoint
    WHY: Validates refinement creation input
    """
    result_id: UUID = Field(..., description="Result to refine")
    refinement_type: RefinementType = Field(..., description="Type of refinement")
    requester_id: UUID = Field(..., description="User requesting refinement")
    feedback: str = Field(..., min_length=1, description="User feedback")
    specific_instructions: str = Field("", description="Additional instructions")
    target_sections: Optional[List[str]] = Field(None, description="Sections to refine")


class RefinementDTO(BaseModel):
    """
    WHAT: DTO for refinement response
    WHERE: Response from refinement endpoints
    WHY: Provides refinement information
    """
    id: UUID
    result_id: UUID
    refinement_type: RefinementType
    requester_id: UUID
    feedback: str
    specific_instructions: str
    target_sections: List[str]
    preserve_structure: bool
    max_changes: int
    refined_result_id: Optional[UUID]
    status: GenerationStatus
    changes_made: List[str]
    original_quality_score: int
    refined_quality_score: int
    quality_improvement: int
    iteration_number: int
    max_iterations: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CreateBatchDTO(BaseModel):
    """
    WHAT: DTO for creating a batch generation
    WHERE: POST /batches endpoint
    WHY: Validates batch creation input
    """
    name: str = Field(..., min_length=1, max_length=255, description="Batch name")
    description: str = Field("", description="Batch description")
    course_id: UUID = Field(..., description="Course for generation")
    requester_id: UUID = Field(..., description="User requesting batch")
    content_types: List[GenerationContentType] = Field(..., description="Content types")
    organization_id: Optional[UUID] = Field(None, description="Organization context")
    target_modules: Optional[List[UUID]] = Field(None, description="Target modules")
    shared_parameters: Optional[Dict[str, Any]] = Field(None, description="Shared parameters")


class BatchDTO(BaseModel):
    """
    WHAT: DTO for batch response
    WHERE: Response from batch endpoints
    WHY: Provides batch information
    """
    id: UUID
    name: str
    description: str
    course_id: UUID
    requester_id: UUID
    organization_id: Optional[UUID]
    shared_parameters: Dict[str, Any]
    content_types: List[GenerationContentType]
    target_modules: List[UUID]
    status: BatchStatus
    total_items: int
    completed_items: int
    failed_items: int
    progress_percentage: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    total_estimated_cost: float
    actual_cost: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalyticsDTO(BaseModel):
    """
    WHAT: DTO for analytics response
    WHERE: Response from analytics endpoints
    WHY: Provides generation analytics
    """
    id: UUID
    organization_id: Optional[UUID]
    period_start: datetime
    period_end: Optional[datetime]
    total_requests: int
    completed_requests: int
    failed_requests: int
    cached_responses: int
    avg_generation_time_seconds: float
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    avg_cost_per_request: float
    cost_savings_from_cache: float
    avg_quality_score: float
    excellent_count: int
    good_count: int
    acceptable_count: int
    needs_work_count: int
    poor_count: int
    content_type_counts: Dict[str, int]
    total_refinements: int
    successful_refinements: int
    avg_quality_improvement: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# API ROUTER
# ============================================================================

router = APIRouter()


# Dependency placeholder - would be injected by DI container
async def get_service():
    """Dependency to get ContentGenerationV2Service instance."""
    # This would be replaced with actual DI
    raise NotImplementedError("Service dependency not configured")


# ============================================================================
# GENERATION REQUEST ENDPOINTS
# ============================================================================

@router.post(
    "/requests",
    response_model=GenerationRequestDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create generation request",
    description="Create a new content generation request"
)
async def create_generation_request(
    dto: CreateGenerationRequestDTO,
    service=Depends(get_service)
):
    """
    WHAT: Creates a new content generation request
    WHERE: POST /api/v2/generation/requests
    WHY: Entry point for content generation workflow
    """
    try:
        request = await service.create_generation_request(
            course_id=dto.course_id,
            content_type=dto.content_type,
            requester_id=dto.requester_id,
            organization_id=dto.organization_id,
            module_id=dto.module_id,
            template_id=dto.template_id,
            parameters=dto.parameters,
            difficulty_level=dto.difficulty_level,
            target_audience=dto.target_audience,
            language=dto.language,
            use_rag=dto.use_rag,
            use_cache=dto.use_cache
        )
        return GenerationRequestDTO(
            id=request.id,
            course_id=request.course_id,
            content_type=request.content_type,
            requester_id=request.requester_id,
            organization_id=request.organization_id,
            module_id=request.module_id,
            template_id=request.template_id,
            status=request.status,
            parameters=request.parameters,
            difficulty_level=request.difficulty_level,
            target_audience=request.target_audience,
            language=request.language,
            use_rag=request.use_rag,
            use_cache=request.use_cache,
            result_id=request.result_id,
            error_message=request.error_message,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            estimated_cost=float(request.estimated_cost),
            created_at=request.created_at,
            updated_at=request.updated_at,
            started_at=request.started_at,
            completed_at=request.completed_at
        )
    except TemplateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidGenerationParametersException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/requests/{request_id}",
    response_model=GenerationRequestDTO,
    summary="Get generation request",
    description="Retrieve a generation request by ID"
)
async def get_generation_request(
    request_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Retrieves a generation request by ID
    WHERE: GET /api/v2/generation/requests/{request_id}
    WHY: Provides request status and details
    """
    request = await service.get_generation_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    return GenerationRequestDTO(
        id=request.id,
        course_id=request.course_id,
        content_type=request.content_type,
        requester_id=request.requester_id,
        organization_id=request.organization_id,
        module_id=request.module_id,
        template_id=request.template_id,
        status=request.status,
        parameters=request.parameters,
        difficulty_level=request.difficulty_level,
        target_audience=request.target_audience,
        language=request.language,
        use_rag=request.use_rag,
        use_cache=request.use_cache,
        result_id=request.result_id,
        error_message=request.error_message,
        input_tokens=request.input_tokens,
        output_tokens=request.output_tokens,
        estimated_cost=float(request.estimated_cost),
        created_at=request.created_at,
        updated_at=request.updated_at,
        started_at=request.started_at,
        completed_at=request.completed_at
    )


@router.post(
    "/requests/{request_id}/process",
    response_model=GenerationResultDTO,
    summary="Process generation request",
    description="Process a pending generation request to completion"
)
async def process_generation_request(
    request_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Processes a generation request to completion
    WHERE: POST /api/v2/generation/requests/{request_id}/process
    WHY: Triggers content generation workflow
    """
    try:
        result = await service.process_generation_request(request_id)
        return GenerationResultDTO(
            id=result.id,
            request_id=result.request_id,
            course_id=result.course_id,
            content_type=result.content_type,
            raw_output=result.raw_output,
            processed_content=result.processed_content,
            quality_score_id=result.quality_score_id,
            quality_level=result.quality_level,
            model_used=result.model_used,
            generation_method=result.generation_method,
            rag_context_used=result.rag_context_used,
            cached=result.cached,
            cache_key=result.cache_key,
            version=result.version,
            parent_result_id=result.parent_result_id,
            created_at=result.created_at,
            expires_at=result.expires_at
        )
    except ContentGenerationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GenerationTimeoutException as e:
        raise HTTPException(status_code=408, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RESULT ENDPOINTS
# ============================================================================

@router.get(
    "/results/{result_id}",
    response_model=GenerationResultDTO,
    summary="Get generation result",
    description="Retrieve generated content by ID"
)
async def get_generation_result(
    result_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Retrieves a generation result by ID
    WHERE: GET /api/v2/generation/results/{result_id}
    WHY: Provides access to generated content
    """
    result = await service.get_generation_result(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    return GenerationResultDTO(
        id=result.id,
        request_id=result.request_id,
        course_id=result.course_id,
        content_type=result.content_type,
        raw_output=result.raw_output,
        processed_content=result.processed_content,
        quality_score_id=result.quality_score_id,
        quality_level=result.quality_level,
        model_used=result.model_used,
        generation_method=result.generation_method,
        rag_context_used=result.rag_context_used,
        cached=result.cached,
        cache_key=result.cache_key,
        version=result.version,
        parent_result_id=result.parent_result_id,
        created_at=result.created_at,
        expires_at=result.expires_at
    )


@router.get(
    "/results/{result_id}/quality",
    response_model=QualityScoreDTO,
    summary="Get result quality score",
    description="Retrieve quality metrics for generated content"
)
async def get_result_quality(
    result_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Retrieves quality score for a generation result
    WHERE: GET /api/v2/generation/results/{result_id}/quality
    WHY: Provides detailed quality metrics
    """
    result, quality_score = await service.get_result_with_quality(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    if not quality_score:
        raise HTTPException(status_code=404, detail="Quality score not found")

    return QualityScoreDTO(
        id=quality_score.id,
        result_id=quality_score.result_id,
        accuracy_score=quality_score.accuracy_score,
        relevance_score=quality_score.relevance_score,
        completeness_score=quality_score.completeness_score,
        clarity_score=quality_score.clarity_score,
        structure_score=quality_score.structure_score,
        engagement_score=quality_score.engagement_score,
        difficulty_alignment_score=quality_score.difficulty_alignment_score,
        overall_score=quality_score.overall_score,
        quality_level=quality_score.quality_level,
        scoring_method=quality_score.scoring_method,
        scorer_id=quality_score.scorer_id,
        confidence=quality_score.confidence,
        strengths=quality_score.strengths,
        weaknesses=quality_score.weaknesses,
        improvement_suggestions=quality_score.improvement_suggestions,
        created_at=quality_score.created_at,
        updated_at=quality_score.updated_at
    )


# ============================================================================
# TEMPLATE ENDPOINTS
# ============================================================================

@router.post(
    "/templates",
    response_model=TemplateDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create template",
    description="Create a new generation template"
)
async def create_template(
    dto: CreateTemplateDTO,
    service=Depends(get_service)
):
    """
    WHAT: Creates a new generation template
    WHERE: POST /api/v2/generation/templates
    WHY: Enables custom template creation
    """
    try:
        template = await service.create_template(
            name=dto.name,
            description=dto.description,
            content_type=dto.content_type,
            category=dto.category,
            system_prompt=dto.system_prompt,
            user_prompt_template=dto.user_prompt_template,
            required_variables=dto.required_variables,
            creator_id=dto.creator_id,
            organization_id=dto.organization_id,
            is_global=dto.is_global,
            output_schema=dto.output_schema,
            default_parameters=dto.default_parameters,
            min_quality_score=dto.min_quality_score
        )
        return TemplateDTO(
            id=template.id,
            name=template.name,
            description=template.description,
            content_type=template.content_type,
            category=template.category,
            system_prompt=template.system_prompt,
            user_prompt_template=template.user_prompt_template,
            required_variables=template.required_variables,
            default_parameters=template.default_parameters,
            creator_id=template.creator_id,
            organization_id=template.organization_id,
            is_global=template.is_global,
            is_active=template.is_active,
            is_archived=template.is_archived,
            min_quality_score=template.min_quality_score,
            usage_count=template.usage_count,
            success_count=template.success_count,
            avg_quality_score=template.avg_quality_score,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/templates",
    response_model=List[TemplateDTO],
    summary="List templates",
    description="Retrieve available generation templates"
)
async def list_templates(
    content_type: Optional[GenerationContentType] = Query(None),
    category: Optional[TemplateCategory] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    service=Depends(get_service)
):
    """
    WHAT: Lists available generation templates
    WHERE: GET /api/v2/generation/templates
    WHY: Enables template discovery
    """
    templates = await service.list_templates(
        content_type=content_type,
        category=category,
        organization_id=organization_id
    )
    return [
        TemplateDTO(
            id=t.id,
            name=t.name,
            description=t.description,
            content_type=t.content_type,
            category=t.category,
            system_prompt=t.system_prompt,
            user_prompt_template=t.user_prompt_template,
            required_variables=t.required_variables,
            default_parameters=t.default_parameters,
            creator_id=t.creator_id,
            organization_id=t.organization_id,
            is_global=t.is_global,
            is_active=t.is_active,
            is_archived=t.is_archived,
            min_quality_score=t.min_quality_score,
            usage_count=t.usage_count,
            success_count=t.success_count,
            avg_quality_score=t.avg_quality_score,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in templates
    ]


@router.get(
    "/templates/{template_id}",
    response_model=TemplateDTO,
    summary="Get template",
    description="Retrieve a template by ID"
)
async def get_template(
    template_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Retrieves a template by ID
    WHERE: GET /api/v2/generation/templates/{template_id}
    WHY: Provides template details
    """
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateDTO(
        id=template.id,
        name=template.name,
        description=template.description,
        content_type=template.content_type,
        category=template.category,
        system_prompt=template.system_prompt,
        user_prompt_template=template.user_prompt_template,
        required_variables=template.required_variables,
        default_parameters=template.default_parameters,
        creator_id=template.creator_id,
        organization_id=template.organization_id,
        is_global=template.is_global,
        is_active=template.is_active,
        is_archived=template.is_archived,
        min_quality_score=template.min_quality_score,
        usage_count=template.usage_count,
        success_count=template.success_count,
        avg_quality_score=template.avg_quality_score,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive template",
    description="Archive a template (soft delete)"
)
async def archive_template(
    template_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Archives a template
    WHERE: DELETE /api/v2/generation/templates/{template_id}
    WHY: Soft delete preserving history
    """
    try:
        success = await service.archive_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
    except TemplateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# REFINEMENT ENDPOINTS
# ============================================================================

@router.post(
    "/refinements",
    response_model=RefinementDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create refinement",
    description="Create a content refinement request"
)
async def create_refinement(
    dto: CreateRefinementDTO,
    service=Depends(get_service)
):
    """
    WHAT: Creates a new refinement request
    WHERE: POST /api/v2/generation/refinements
    WHY: Initiates content improvement workflow
    """
    try:
        refinement = await service.create_refinement(
            result_id=dto.result_id,
            refinement_type=dto.refinement_type,
            requester_id=dto.requester_id,
            feedback=dto.feedback,
            specific_instructions=dto.specific_instructions,
            target_sections=dto.target_sections
        )
        return RefinementDTO(
            id=refinement.id,
            result_id=refinement.result_id,
            refinement_type=refinement.refinement_type,
            requester_id=refinement.requester_id,
            feedback=refinement.feedback,
            specific_instructions=refinement.specific_instructions,
            target_sections=refinement.target_sections,
            preserve_structure=refinement.preserve_structure,
            max_changes=refinement.max_changes,
            refined_result_id=refinement.refined_result_id,
            status=refinement.status,
            changes_made=refinement.changes_made,
            original_quality_score=refinement.original_quality_score,
            refined_quality_score=refinement.refined_quality_score,
            quality_improvement=refinement.quality_improvement,
            iteration_number=refinement.iteration_number,
            max_iterations=refinement.max_iterations,
            created_at=refinement.created_at,
            completed_at=refinement.completed_at
        )
    except MaxRefinementsExceededException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ContentGenerationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/refinements/{refinement_id}/process",
    response_model=GenerationResultDTO,
    summary="Process refinement",
    description="Process a refinement to completion"
)
async def process_refinement(
    refinement_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Processes a refinement to completion
    WHERE: POST /api/v2/generation/refinements/{refinement_id}/process
    WHY: Generates refined content
    """
    try:
        result = await service.process_refinement(refinement_id)
        return GenerationResultDTO(
            id=result.id,
            request_id=result.request_id,
            course_id=result.course_id,
            content_type=result.content_type,
            raw_output=result.raw_output,
            processed_content=result.processed_content,
            quality_score_id=result.quality_score_id,
            quality_level=result.quality_level,
            model_used=result.model_used,
            generation_method=result.generation_method,
            rag_context_used=result.rag_context_used,
            cached=result.cached,
            cache_key=result.cache_key,
            version=result.version,
            parent_result_id=result.parent_result_id,
            created_at=result.created_at,
            expires_at=result.expires_at
        )
    except ContentGenerationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BATCH ENDPOINTS
# ============================================================================

@router.post(
    "/batches",
    response_model=BatchDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create batch",
    description="Create a batch generation request"
)
async def create_batch(
    dto: CreateBatchDTO,
    service=Depends(get_service)
):
    """
    WHAT: Creates a new batch generation
    WHERE: POST /api/v2/generation/batches
    WHY: Enables bulk content generation
    """
    try:
        batch = await service.create_batch(
            name=dto.name,
            description=dto.description,
            course_id=dto.course_id,
            requester_id=dto.requester_id,
            content_types=dto.content_types,
            organization_id=dto.organization_id,
            target_modules=dto.target_modules,
            shared_parameters=dto.shared_parameters
        )
        return BatchDTO(
            id=batch.id,
            name=batch.name,
            description=batch.description,
            course_id=batch.course_id,
            requester_id=batch.requester_id,
            organization_id=batch.organization_id,
            shared_parameters=batch.shared_parameters,
            content_types=batch.content_types,
            target_modules=batch.target_modules,
            status=batch.status,
            total_items=batch.total_items,
            completed_items=batch.completed_items,
            failed_items=batch.failed_items,
            progress_percentage=batch.progress_percentage,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            estimated_completion=batch.estimated_completion,
            total_estimated_cost=float(batch.total_estimated_cost),
            actual_cost=float(batch.actual_cost),
            created_at=batch.created_at,
            updated_at=batch.updated_at
        )
    except BatchSizeLimitException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/batches/{batch_id}",
    response_model=BatchDTO,
    summary="Get batch",
    description="Retrieve a batch by ID"
)
async def get_batch(
    batch_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Retrieves a batch by ID
    WHERE: GET /api/v2/generation/batches/{batch_id}
    WHY: Provides batch status and details
    """
    batch = await service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    return BatchDTO(
        id=batch.id,
        name=batch.name,
        description=batch.description,
        course_id=batch.course_id,
        requester_id=batch.requester_id,
        organization_id=batch.organization_id,
        shared_parameters=batch.shared_parameters,
        content_types=batch.content_types,
        target_modules=batch.target_modules,
        status=batch.status,
        total_items=batch.total_items,
        completed_items=batch.completed_items,
        failed_items=batch.failed_items,
        progress_percentage=batch.progress_percentage,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        estimated_completion=batch.estimated_completion,
        total_estimated_cost=float(batch.total_estimated_cost),
        actual_cost=float(batch.actual_cost),
        created_at=batch.created_at,
        updated_at=batch.updated_at
    )


@router.post(
    "/batches/{batch_id}/process",
    response_model=BatchDTO,
    summary="Process batch",
    description="Process a batch to completion"
)
async def process_batch(
    batch_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Processes a batch to completion
    WHERE: POST /api/v2/generation/batches/{batch_id}/process
    WHY: Triggers batch generation workflow
    """
    try:
        batch = await service.process_batch(batch_id)
        return BatchDTO(
            id=batch.id,
            name=batch.name,
            description=batch.description,
            course_id=batch.course_id,
            requester_id=batch.requester_id,
            organization_id=batch.organization_id,
            shared_parameters=batch.shared_parameters,
            content_types=batch.content_types,
            target_modules=batch.target_modules,
            status=batch.status,
            total_items=batch.total_items,
            completed_items=batch.completed_items,
            failed_items=batch.failed_items,
            progress_percentage=batch.progress_percentage,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            estimated_completion=batch.estimated_completion,
            total_estimated_cost=float(batch.total_estimated_cost),
            actual_cost=float(batch.actual_cost),
            created_at=batch.created_at,
            updated_at=batch.updated_at
        )
    except ContentGenerationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/batches/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel batch",
    description="Cancel a batch generation"
)
async def cancel_batch(
    batch_id: UUID,
    service=Depends(get_service)
):
    """
    WHAT: Cancels a batch
    WHERE: DELETE /api/v2/generation/batches/{batch_id}
    WHY: Stops batch processing
    """
    success = await service.cancel_batch(batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Batch not found")


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get(
    "/analytics",
    response_model=List[AnalyticsDTO],
    summary="Get analytics history",
    description="Retrieve generation analytics for specified period"
)
async def get_analytics(
    organization_id: Optional[UUID] = Query(None),
    days: int = Query(30, ge=1, le=365),
    service=Depends(get_service)
):
    """
    WHAT: Retrieves analytics history
    WHERE: GET /api/v2/generation/analytics
    WHY: Provides performance insights
    """
    analytics_list = await service.get_analytics(
        organization_id=organization_id,
        days=days
    )
    return [
        AnalyticsDTO(
            id=a.id,
            organization_id=a.organization_id,
            period_start=a.period_start,
            period_end=a.period_end,
            total_requests=a.total_requests,
            completed_requests=a.completed_requests,
            failed_requests=a.failed_requests,
            cached_responses=a.cached_responses,
            avg_generation_time_seconds=a.avg_generation_time_seconds,
            total_input_tokens=a.total_input_tokens,
            total_output_tokens=a.total_output_tokens,
            total_cost=float(a.total_cost),
            avg_cost_per_request=float(a.avg_cost_per_request),
            cost_savings_from_cache=float(a.cost_savings_from_cache),
            avg_quality_score=a.avg_quality_score,
            excellent_count=a.excellent_count,
            good_count=a.good_count,
            acceptable_count=a.acceptable_count,
            needs_work_count=a.needs_work_count,
            poor_count=a.poor_count,
            content_type_counts=a.content_type_counts,
            total_refinements=a.total_refinements,
            successful_refinements=a.successful_refinements,
            avg_quality_improvement=a.avg_quality_improvement,
            created_at=a.created_at,
            updated_at=a.updated_at
        )
        for a in analytics_list
    ]


@router.get(
    "/analytics/current",
    response_model=AnalyticsDTO,
    summary="Get current analytics",
    description="Retrieve current day's generation analytics"
)
async def get_current_analytics(
    organization_id: Optional[UUID] = Query(None),
    service=Depends(get_service)
):
    """
    WHAT: Retrieves current analytics
    WHERE: GET /api/v2/generation/analytics/current
    WHY: Shows real-time performance
    """
    analytics = await service.get_current_analytics(organization_id)
    return AnalyticsDTO(
        id=analytics.id,
        organization_id=analytics.organization_id,
        period_start=analytics.period_start,
        period_end=analytics.period_end,
        total_requests=analytics.total_requests,
        completed_requests=analytics.completed_requests,
        failed_requests=analytics.failed_requests,
        cached_responses=analytics.cached_responses,
        avg_generation_time_seconds=analytics.avg_generation_time_seconds,
        total_input_tokens=analytics.total_input_tokens,
        total_output_tokens=analytics.total_output_tokens,
        total_cost=float(analytics.total_cost),
        avg_cost_per_request=float(analytics.avg_cost_per_request),
        cost_savings_from_cache=float(analytics.cost_savings_from_cache),
        avg_quality_score=analytics.avg_quality_score,
        excellent_count=analytics.excellent_count,
        good_count=analytics.good_count,
        acceptable_count=analytics.acceptable_count,
        needs_work_count=analytics.needs_work_count,
        poor_count=analytics.poor_count,
        content_type_counts=analytics.content_type_counts,
        total_refinements=analytics.total_refinements,
        successful_refinements=analytics.successful_refinements,
        avg_quality_improvement=analytics.avg_quality_improvement,
        created_at=analytics.created_at,
        updated_at=analytics.updated_at
    )
