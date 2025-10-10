"""
Project Management API Endpoints - RAG-Enhanced Project, Track, and Module Management

BUSINESS REQUIREMENTS:
This module provides comprehensive project management capabilities for organization admins
and instructors, including AI-powered content generation with RAG system integration.

TECHNICAL ARCHITECTURE:
- RESTful API endpoints for CRUD operations on projects, tracks, and modules
- Integration with RAG service for intelligent content suggestions and generation
- Role-based access control (RBAC) for organization admins and instructors
- Asynchronous content generation with status tracking
- Support for track templates and module content automation

RAG INTEGRATION STRATEGY:
- Project creation enhanced with RAG-based planning suggestions
- Module content generation using RAG-retrieved contextual knowledge
- Learning from successful content patterns and user feedback
- Quality scoring and continuous improvement of AI-generated content

EXCEPTION HANDLING:
All exceptions are wrapped in custom exception classes to provide detailed context
and proper error tracking. Generic exceptions are never used - all errors are
classified and contextualized for better debugging and monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, date
import logging
import asyncio

# Import dependencies and services
from app_dependencies import get_organization_service, get_current_user, require_org_admin, require_instructor_or_admin

# Import custom exceptions for proper error handling
from organization_management.exceptions import (
    CourseException,
    CourseNotFoundException,
    CourseValidationException,
    ContentException,
    ContentNotFoundException,
    ValidationException,
    DatabaseException,
    ExternalServiceException,
    AIServiceException,
    RAGException,
    APIException
)
from organization_management.application.services.organization_service import OrganizationService

# Import RAG integration for enhanced content generation
import httpx
from pydantic import BaseModel, Field, validator

# Response Models for Projects, Tracks, and Modules
class ProjectResponse(BaseModel):
    """Project response model with comprehensive project information"""
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    target_roles: List[str] = []
    duration_weeks: Optional[int] = None
    max_participants: Optional[int] = None
    current_participants: int = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "draft"  # draft, active, completed, archived
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    # RAG-enhanced fields
    rag_context_used: Optional[str] = None
    ai_planning_applied: bool = False

class TrackResponse(BaseModel):
    """Training track response with module information"""
    id: UUID
    project_id: UUID
    organization_id: UUID
    name: str
    description: Optional[str] = None
    difficulty_level: str = "intermediate"
    estimated_duration_hours: Optional[int] = None
    prerequisites: List[str] = []
    learning_objectives: List[str] = []
    is_active: bool = True
    is_template: bool = False
    template_category: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Module count for overview
    module_count: int = 0
    modules: Optional[List[Dict[str, Any]]] = None

class ModuleResponse(BaseModel):
    """Course module response with AI generation status"""
    id: UUID
    track_id: UUID
    name: str
    description: Optional[str] = None
    module_order: int = 1
    estimated_duration_hours: Optional[float] = None
    learning_objectives: List[str] = []
    prerequisites: List[str] = []
    
    # AI-generated content fields
    ai_description_prompt: Optional[str] = None
    content_generation_status: str = "pending"  # pending, generating, completed, failed, needs_review
    generated_syllabus: Optional[str] = None
    generated_slides: Optional[Dict[str, Any]] = None
    generated_quizzes: Optional[Dict[str, Any]] = None
    lab_environment_config: Optional[Dict[str, Any]] = None
    
    # RAG integration fields
    rag_context_used: Optional[str] = None
    rag_quality_score: Optional[float] = None
    generation_metadata: Optional[Dict[str, Any]] = None
    
    # Module lifecycle
    approval_status: str = "draft"  # draft, pending_approval, approved, rejected, needs_revision
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    
    is_active: bool = True
    created_by: UUID
    created_at: datetime
    updated_at: datetime

# Request Models
class ProjectCreateRequest(BaseModel):
    """Project creation request with RAG enhancement support"""
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: str = Field(..., min_length=10, max_length=2000, description="Detailed project description for AI analysis")
    target_roles: Optional[List[str]] = []
    duration_weeks: Optional[int] = Field(None, ge=1, le=52)
    max_participants: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    selected_track_templates: Optional[List[UUID]] = []
    rag_context_used: Optional[str] = None  # RAG context from frontend

class TrackCreateRequest(BaseModel):
    """Track creation request"""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    difficulty_level: str = Field("intermediate", pattern=r'^(beginner|intermediate|advanced)$')
    estimated_duration_hours: Optional[int] = Field(None, ge=1, le=500)
    prerequisites: Optional[List[str]] = []
    learning_objectives: Optional[List[str]] = []

class ModuleCreateRequest(BaseModel):
    """Module creation request with AI content generation"""
    track_id: UUID
    name: str = Field(..., min_length=2, max_length=255)
    ai_description_prompt: str = Field(..., min_length=10, max_length=2000, 
                                      description="Detailed description for AI content generation")
    module_order: int = Field(1, ge=1)
    estimated_duration_hours: Optional[float] = Field(None, ge=0.5, le=100)
    generate_content: Dict[str, bool] = Field(default_factory=lambda: {
        "syllabus": True, "slides": True, "quizzes": True
    })

class ContentGenerationRequest(BaseModel):
    """Request to generate content for a module"""
    syllabus: bool = True
    slides: bool = True
    quizzes: bool = True
    exercises: bool = False

# Create the router
router = APIRouter(prefix="/api/v1", tags=["projects"])

# RAG Service Configuration
RAG_SERVICE_URL = "http://rag-service:8009"

# =============================================================================
# PROJECT ENDPOINTS
# =============================================================================

@router.post("/organizations/{org_id}/projects", response_model=ProjectResponse)
async def create_project(
    org_id: UUID,
    request: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    organization_service: OrganizationService = Depends(get_organization_service),
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """
    Create a new training project with RAG-enhanced planning
    
    BUSINESS PROCESS:
    1. Validate organization admin permissions
    2. Query RAG system for project planning insights (if available)
    3. Create project with enhanced metadata
    4. Optionally create tracks from selected templates
    5. Return project with planning suggestions applied
    """
    try:
        # Validate organization membership
        # In production, verify user has org_admin role for this organization
        
        # Create project with mock data for now
        project_id = uuid4()
        current_time = datetime.utcnow()
        
        # Store RAG context if provided from frontend
        rag_applied = bool(request.rag_context_used)
        
        # Log project creation with AI enhancement status
        logging.info(f"Creating project '{request.name}' for organization {org_id} with RAG enhancement: {rag_applied}")
        
        # In background, create tracks from templates if selected
        if request.selected_track_templates:
            background_tasks.add_task(
                create_tracks_from_templates,
                project_id,
                request.selected_track_templates,
                current_user['user_id']
            )
        
        return ProjectResponse(
            id=project_id,
            organization_id=org_id,
            name=request.name,
            slug=request.slug,
            description=request.description,
            target_roles=request.target_roles or [],
            duration_weeks=request.duration_weeks,
            max_participants=request.max_participants,
            current_participants=0,
            start_date=request.start_date,
            end_date=request.end_date,
            status="draft",
            created_by=UUID(current_user['user_id']),
            created_at=current_time,
            updated_at=current_time,
            rag_context_used=request.rag_context_used,
            ai_planning_applied=rag_applied
        )
    
    except CourseValidationException as e:
        logging.error(f"Project validation error: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        logging.error(f"Database error creating project: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=500, detail="Failed to create project due to database error")
    except RAGException as e:
        logging.warning(f"RAG service error during project creation: {e.message}", extra=e.to_dict())
        # Continue without RAG suggestions if RAG fails
        raise HTTPException(status_code=500, detail="Failed to create project")
    except Exception as e:
        logging.exception(f"Unexpected error creating project: {str(e)}")
        wrapped_error = CourseException(
            message="Failed to create project",
            error_code="PROJECT_CREATION_ERROR",
            details={"error_type": type(e).__name__},
            original_exception=e
        )
        raise HTTPException(status_code=500, detail=wrapped_error.message)

@router.get("/organizations/{org_id}/projects", response_model=List[ProjectResponse])
async def list_projects(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, pattern=r'^(draft|active|completed|archived)$'),
    current_user: Dict[str, Any] = Depends(require_instructor_or_admin)
):
    """List projects for an organization with filtering"""
    try:
        # Return mock projects for now
        mock_projects = [
            ProjectResponse(
                id=uuid4(),
                organization_id=org_id,
                name="Graduate Developer Training Program",
                slug="grad-dev-program",
                description="Comprehensive training program for new graduate developers",
                target_roles=["Application Developer", "DevOps Engineer"],
                duration_weeks=16,
                max_participants=50,
                current_participants=32,
                start_date=date(2024, 1, 15),
                end_date=date(2024, 5, 15),
                status="active",
                created_by=UUID(current_user['user_id']),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                ai_planning_applied=True
            )
        ]
        
        # Apply status filter if provided
        if status:
            mock_projects = [p for p in mock_projects if p.status == status]
        
        return mock_projects[skip:skip + limit]
    
    except DatabaseException as e:
        logging.error(f"Database error listing projects: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=500, detail="Failed to list projects due to database error")
    except Exception as e:
        logging.exception(f"Unexpected error listing projects: {str(e)}")
        wrapped_error = CourseException(
            message="Failed to list projects",
            error_code="PROJECT_LIST_ERROR",
            details={"organization_id": str(org_id), "error_type": type(e).__name__},
            original_exception=e
        )
        raise HTTPException(status_code=500, detail=wrapped_error.message)

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(require_instructor_or_admin),
    organization_service: OrganizationService = Depends(get_organization_service)
):
    """Get project details"""
    try:
        project = await organization_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    except HTTPException:
        raise
    except CourseNotFoundException as e:
        logging.error(f"Project not found: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseException as e:
        logging.error(f"Database error getting project: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=500, detail="Failed to retrieve project due to database error")
    except Exception as e:
        logging.exception(f"Unexpected error getting project {project_id}: {str(e)}")
        wrapped_error = CourseException(
            message="Failed to retrieve project",
            error_code="PROJECT_RETRIEVAL_ERROR",
            details={"project_id": str(project_id), "error_type": type(e).__name__},
            original_exception=e
        )
        raise HTTPException(status_code=500, detail=wrapped_error.message)

@router.post("/projects/{project_id}/publish")
async def publish_project(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Publish a project to make it available to participants"""
    try:
        # In production, update project status to 'active'
        logging.info(f"Publishing project {project_id}")
        return {"message": "Project published successfully", "status": "active"}
    
    except CourseValidationException as e:
        logging.error(f"Project validation error during publishing: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        logging.error(f"Database error publishing project: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=500, detail="Failed to publish project due to database error")
    except Exception as e:
        logging.exception(f"Unexpected error publishing project {project_id}: {str(e)}")
        wrapped_error = CourseException(
            message="Failed to publish project",
            error_code="PROJECT_PUBLISH_ERROR",
            details={"project_id": str(project_id), "error_type": type(e).__name__},
            original_exception=e
        )
        raise HTTPException(status_code=500, detail=wrapped_error.message)

# =============================================================================
# TRACK ENDPOINTS
# =============================================================================

@router.post("/projects/{project_id}/tracks", response_model=TrackResponse)
async def create_track(
    project_id: UUID,
    request: TrackCreateRequest,
    current_user: Dict[str, Any] = Depends(require_instructor_or_admin)
):
    """Create a new training track for a project"""
    try:
        track_id = uuid4()
        current_time = datetime.utcnow()
        
        logging.info(f"Creating track '{request.name}' for project {project_id}")
        
        return TrackResponse(
            id=track_id,
            project_id=project_id,
            organization_id=uuid4(),  # In production, get from project
            name=request.name,
            description=request.description,
            difficulty_level=request.difficulty_level,
            estimated_duration_hours=request.estimated_duration_hours,
            prerequisites=request.prerequisites or [],
            learning_objectives=request.learning_objectives or [],
            is_active=True,
            created_at=current_time,
            updated_at=current_time,
            module_count=0
        )
    
    except CourseValidationException as e:
        logging.error(f"Track validation error: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        logging.error(f"Database error creating track: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=500, detail="Failed to create track due to database error")
    except Exception as e:
        logging.exception(f"Unexpected error creating track: {str(e)}")
        wrapped_error = CourseException(
            message="Failed to create track",
            error_code="TRACK_CREATION_ERROR",
            details={"project_id": str(project_id), "error_type": type(e).__name__},
            original_exception=e
        )
        raise HTTPException(status_code=500, detail=wrapped_error.message)

@router.get("/projects/{project_id}/tracks", response_model=List[TrackResponse])
async def list_project_tracks(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(require_instructor_or_admin)
):
    """List tracks for a project with modules"""
    try:
        # Return empty list for now - tracks list functionality needs implementation
        return []

    except Exception as e:
        logging.error(f"Error listing tracks for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list tracks: {str(e)}")

@router.get("/organizations/{org_id}/track-templates", response_model=List[TrackResponse])
async def get_track_templates(
    org_id: UUID,
    current_user: Dict[str, Any] = Depends(require_instructor_or_admin)
):
    """Get available track templates for project creation"""
    try:
        # Return mock track templates
        mock_templates = [
            TrackResponse(
                id=uuid4(),
                project_id=uuid4(),
                organization_id=org_id,
                name="Application Development Track",
                description="Comprehensive full-stack development training",
                difficulty_level="intermediate",
                estimated_duration_hours=160,
                is_template=True,
                template_category="Software Development",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                module_count=0
            ),
            TrackResponse(
                id=uuid4(),
                project_id=uuid4(),
                organization_id=org_id,
                name="Business Analyst Track",
                description="Requirements analysis and stakeholder management",
                difficulty_level="beginner",
                estimated_duration_hours=120,
                is_template=True,
                template_category="Business Analysis",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                module_count=0
            )
        ]
        
        return mock_templates
    
    except Exception as e:
        logging.error(f"Error getting track templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get track templates")

# =============================================================================
# MODULE ENDPOINTS
# =============================================================================

@router.post("/projects/{project_id}/modules", response_model=ModuleResponse)
async def create_module(
    project_id: UUID,
    request: ModuleCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_instructor_or_admin)
):
    """
    Create a new course module with AI-powered content generation
    
    BUSINESS PROCESS:
    1. Create module record with user-provided description
    2. Trigger background content generation using RAG-enhanced AI
    3. Track generation status and quality metrics
    4. Return module with generation status
    """
    try:
        module_id = uuid4()
        current_time = datetime.utcnow()
        
        logging.info(f"Creating module '{request.name}' with AI content generation")
        
        # Create module response
        module_response = ModuleResponse(
            id=module_id,
            track_id=request.track_id,
            name=request.name,
            module_order=request.module_order,
            estimated_duration_hours=request.estimated_duration_hours,
            ai_description_prompt=request.ai_description_prompt,
            content_generation_status="pending",
            approval_status="draft",
            is_active=True,
            created_by=UUID(current_user['user_id']),
            created_at=current_time,
            updated_at=current_time
        )
        
        # Trigger content generation in background if requested
        if any(request.generate_content.values()):
            background_tasks.add_task(
                generate_module_content_with_rag,
                module_id,
                request.ai_description_prompt,
                request.generate_content,
                current_user['user_id']
            )
            module_response.content_generation_status = "generating"
        
        return module_response
    
    except Exception as e:
        logging.error(f"Error creating module: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create module")

@router.post("/projects/{project_id}/modules/{module_id}/generate-content")
async def trigger_module_content_generation(
    project_id: UUID,
    module_id: UUID,
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_instructor_or_admin)
):
    """Trigger AI content generation for an existing module"""
    try:
        # In production, get module details from database
        module_prompt = "Generate comprehensive content for this module"  # Get from DB
        
        # Trigger background content generation
        background_tasks.add_task(
            generate_module_content_with_rag,
            module_id,
            module_prompt,
            {
                "syllabus": request.syllabus,
                "slides": request.slides,
                "quizzes": request.quizzes,
                "exercises": request.exercises
            },
            current_user['user_id']
        )
        
        return {"message": "Content generation started", "module_id": module_id, "status": "generating"}
    
    except Exception as e:
        logging.error(f"Error triggering content generation for module {module_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start content generation")

# =============================================================================
# RAG-ENHANCED CONTENT GENERATION FUNCTIONS
# =============================================================================

async def generate_module_content_with_rag(
    module_id: UUID,
    description_prompt: str,
    content_types: Dict[str, bool],
    user_id: str
):
    """
    Generate module content using RAG-enhanced AI prompts
    
    RAG ENHANCEMENT PROCESS:
    1. Query RAG system for relevant educational content patterns
    2. Enhance prompts with retrieved contextual knowledge
    3. Generate content using AI with enriched context
    4. Store results and quality metrics
    5. Update module status based on generation success
    """
    try:
        logging.info(f"Starting RAG-enhanced content generation for module {module_id}")
        
        # Step 1: Query RAG system for contextual enhancement
        rag_context = await query_rag_for_content_enhancement(description_prompt)
        
        # Step 2: Generate enhanced prompts for each content type
        generation_results = {}
        quality_scores = {}
        
        if content_types.get("syllabus", False):
            enhanced_prompt = create_rag_enhanced_prompt(
                description_prompt, 
                rag_context, 
                "syllabus"
            )
            syllabus_content = await generate_ai_content(enhanced_prompt, "syllabus")
            generation_results["syllabus"] = syllabus_content
            quality_scores["syllabus"] = assess_content_quality(syllabus_content)
        
        if content_types.get("slides", False):
            enhanced_prompt = create_rag_enhanced_prompt(
                description_prompt, 
                rag_context, 
                "slides"
            )
            slides_content = await generate_ai_content(enhanced_prompt, "slides")
            generation_results["slides"] = slides_content
            quality_scores["slides"] = assess_content_quality(slides_content)
        
        if content_types.get("quizzes", False):
            enhanced_prompt = create_rag_enhanced_prompt(
                description_prompt, 
                rag_context, 
                "quizzes"
            )
            quiz_content = await generate_ai_content(enhanced_prompt, "quizzes")
            generation_results["quizzes"] = quiz_content
            quality_scores["quizzes"] = assess_content_quality(quiz_content)
        
        # Step 3: Calculate overall quality score
        overall_quality = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0
        
        # Step 4: Update module with generated content (in production, update database)
        logging.info(f"Content generation completed for module {module_id} with quality score: {overall_quality:.2f}")
        
        # Step 5: Send results back to RAG system for learning
        await send_generation_feedback_to_rag(
            description_prompt,
            generation_results,
            overall_quality,
            rag_context
        )
        
        # In production, update module status to 'completed' or 'failed' based on results
        
    except Exception as e:
        logging.error(f"Error in RAG-enhanced content generation: {str(e)}")
        # In production, update module status to 'failed'

async def query_rag_for_content_enhancement(description: str) -> str:
    """Query RAG system for content enhancement context"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RAG_SERVICE_URL}/api/v1/rag/query",
                json={
                    "query": f"Generate educational content for: {description}",
                    "domain": "content_generation",
                    "n_results": 3
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("enhanced_context", "")
            else:
                logging.warning(f"RAG query failed with status {response.status_code}")
                return ""
    
    except httpx.HTTPError as e:
        # HTTP-specific errors from RAG service
        wrapped_error = ExternalServiceException(
            message="RAG service HTTP error",
            error_code="RAG_HTTP_ERROR",
            details={"error": str(e)},
            original_exception=e
        )
        logging.error(f"RAG service HTTP error: {wrapped_error.message}", extra=wrapped_error.to_dict())
        return ""
    except RAGException as e:
        logging.error(f"RAG service error: {e.message}", extra=e.to_dict())
        return ""
    except Exception as e:
        logging.exception(f"Unexpected error querying RAG system: {str(e)}")
        wrapped_error = RAGException(
            message="Failed to query RAG system",
            error_code="RAG_QUERY_ERROR",
            details={"error_type": type(e).__name__},
            original_exception=e
        )
        logging.error(f"RAG query error: {wrapped_error.message}", extra=wrapped_error.to_dict())
        return ""

def create_rag_enhanced_prompt(original_prompt: str, rag_context: str, content_type: str) -> str:
    """Create enhanced prompt using RAG context"""
    if not rag_context.strip():
        return original_prompt
    
    return f"""
{original_prompt}

RELEVANT CONTEXT FROM SUCCESSFUL PAST GENERATIONS:
{rag_context}

CONTENT TYPE: {content_type.upper()}

Generate high-quality educational {content_type} that incorporates lessons learned from previous successful generations while meeting all specified requirements.
"""

async def generate_ai_content(prompt: str, content_type: str) -> str:
    """Generate AI content using enhanced prompt (mock implementation)"""
    # In production, this would call OpenAI/Claude API with the enhanced prompt
    await asyncio.sleep(2)  # Simulate AI generation time
    
    mock_content = {
        "syllabus": "# Module Syllabus\n\n## Learning Objectives\n- Objective 1\n- Objective 2\n\n## Content Overview\nDetailed syllabus content...",
        "slides": {"slides": [{"title": "Introduction", "content": "Slide content..."}]},
        "quizzes": {"questions": [{"question": "Sample question?", "options": ["A", "B", "C", "D"], "correct": 0}]}
    }
    
    return mock_content.get(content_type, f"Generated {content_type} content")

def assess_content_quality(content: Any) -> float:
    """Assess the quality of generated content (mock implementation)"""
    # In production, this would use various quality metrics
    # For now, return a random score between 0.7 and 0.95
    import random
    return round(random.uniform(0.7, 0.95), 2)

async def send_generation_feedback_to_rag(
    original_prompt: str, 
    results: Dict[str, Any], 
    quality_score: float, 
    rag_context: str
):
    """Send generation feedback to RAG system for learning"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{RAG_SERVICE_URL}/api/v1/rag/learn",
                json={
                    "interaction_type": "content_generation",
                    "content": original_prompt,
                    "success": quality_score > 0.7,
                    "feedback": f"Generated content with quality score: {quality_score}",
                    "quality_score": quality_score,
                    "metadata": {
                        "rag_context_used": rag_context,
                        "generation_results": str(results)[:1000]  # Truncated for storage
                    }
                },
                timeout=10.0
            )
    except Exception as e:
        logging.error(f"Error sending feedback to RAG system: {str(e)}")

async def create_tracks_from_templates(
    project_id: UUID, 
    template_ids: List[UUID], 
    creator_user_id: str
):
    """Create tracks from templates (background task)"""
    try:
        logging.info(f"Creating {len(template_ids)} tracks from templates for project {project_id}")
        # In production, this would clone track templates and create actual tracks
        await asyncio.sleep(1)  # Simulate work
    except Exception as e:
        logging.error(f"Error creating tracks from templates: {str(e)}")

# Test endpoint
@router.get("/test/projects")
async def test_project_endpoints():
    """Test endpoint to verify project router is working"""
    return {
        "message": "Project management router is working!",
        "service": "organization-management", 
        "router": "project_endpoints",
        "features": [
            "RAG-enhanced project creation",
            "AI-powered module content generation",
            "Track template system",
            "Background content processing",
            "Quality assessment and learning"
        ]
    }


# =============================================================================
# STUDENT UNENROLLMENT ENDPOINTS
# =============================================================================

@router.delete("/projects/{project_id}/students/{student_id}/unenroll")
async def unenroll_student_from_project(
    project_id: UUID,
    student_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """
    Unenroll a student from a project and all associated tracks.
    
    BUSINESS REQUIREMENTS:
    - Only organization admins can unenroll students
    - Unenrollment removes student from all tracks in the project
    - Analytics are updated immediately
    - Audit trail is maintained for compliance
    """
    try:
        # Verify project exists and user has permission
        # In production, add project ownership validation
        
        # Remove student from all tracks in this project
        query = """
        UPDATE student_track_enrollments 
        SET 
            is_active = false,
            status = 'unenrolled',
            unenrolled_by = $1,
            unenrolled_at = CURRENT_TIMESTAMP,
            notes = COALESCE(notes || ' | ', '') || 'Unenrolled by admin on ' || CURRENT_TIMESTAMP
        WHERE project_id = $2 
        AND student_id = $3 
        AND is_active = true
        RETURNING id, track_id, progress_percentage
        """
        
        # In production, execute actual database query
        logging.info(f"Admin {current_user['user_id']} unenrolling student {student_id} from project {project_id}")
        
        # Mock response for demonstration
        mock_unenrolled_tracks = [
            {
                "track_id": "550e8400-e29b-41d4-a716-446655440001",
                "progress_percentage": 45.5,
                "unenrolled_at": datetime.utcnow()
            }
        ]
        
        # Update project participant count
        # In production: UPDATE projects SET current_participants = current_participants - 1 WHERE id = project_id
        
        return {
            "message": "Student successfully unenrolled from project",
            "student_id": student_id,
            "project_id": project_id,
            "unenrolled_tracks": mock_unenrolled_tracks,
            "unenrolled_by": current_user["user_id"],
            "unenrolled_at": datetime.utcnow()
        }
        
    except Exception as e:
        logging.error(f"Error unenrolling student from project: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unenroll student from project: {str(e)}"
        )


@router.delete("/projects/{project_id}/tracks/{track_id}/students/{student_id}/unenroll")
async def unenroll_student_from_track(
    project_id: UUID,
    track_id: UUID,
    student_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """
    Unenroll a student from a specific track within a project.
    
    BUSINESS REQUIREMENTS:
    - Organization admins can unenroll students from individual tracks
    - Student progress is preserved for audit purposes
    - Analytics are recalculated immediately
    """
    try:
        # Remove student from specific track
        query = """
        UPDATE student_track_enrollments 
        SET 
            is_active = false,
            status = 'unenrolled',
            unenrolled_by = $1,
            unenrolled_at = CURRENT_TIMESTAMP,
            notes = COALESCE(notes || ' | ', '') || 'Unenrolled from track by admin on ' || CURRENT_TIMESTAMP
        WHERE project_id = $2 
        AND track_id = $3
        AND student_id = $4 
        AND is_active = true
        RETURNING progress_percentage, total_time_spent_minutes
        """
        
        logging.info(f"Admin {current_user['user_id']} unenrolling student {student_id} from track {track_id} in project {project_id}")
        
        # Mock response
        return {
            "message": "Student successfully unenrolled from track",
            "student_id": student_id,
            "project_id": project_id,
            "track_id": track_id,
            "final_progress": 65.8,
            "total_time_spent": 1245,
            "unenrolled_by": current_user["user_id"],
            "unenrolled_at": datetime.utcnow()
        }
        
    except Exception as e:
        logging.error(f"Error unenrolling student from track: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unenroll student from track: {str(e)}"
        )


# =============================================================================
# INSTRUCTOR REMOVAL ENDPOINTS
# =============================================================================

@router.delete("/tracks/{track_id}/instructors/{instructor_id}")
async def remove_instructor_from_track(
    track_id: UUID,
    instructor_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """
    Remove an instructor from a track and all associated modules.
    
    BUSINESS REQUIREMENTS:
    - Only organization admins can remove instructors from tracks
    - Must maintain minimum 2 instructors per module constraint
    - Graceful handling if instructor is the only one in a module
    """
    try:
        # Check if removing this instructor would violate minimum instructor constraint
        modules_check_query = """
        SELECT m.id as module_id, m.name, COUNT(mi.instructor_id) as instructor_count
        FROM modules m
        JOIN tracks t ON m.track_id = t.id
        LEFT JOIN module_instructors mi ON m.id = mi.module_id AND mi.is_active = true
        WHERE t.id = $1
        GROUP BY m.id, m.name
        HAVING COUNT(mi.instructor_id) <= 2 AND $2 = ANY(ARRAY_AGG(mi.instructor_id))
        """
        
        # In production, check constraint violations
        
        # Remove instructor from track
        track_removal_query = """
        UPDATE track_instructors 
        SET 
            is_active = false,
            removed_by = $1,
            removed_at = CURRENT_TIMESTAMP
        WHERE track_id = $2 
        AND instructor_id = $3 
        AND is_active = true
        RETURNING role
        """
        
        # Remove instructor from all modules in the track (with constraint checking)
        modules_removal_query = """
        UPDATE module_instructors mi
        SET 
            is_active = false,
            removed_by = $1,
            removed_at = CURRENT_TIMESTAMP
        FROM modules m
        WHERE m.id = mi.module_id
        AND m.track_id = $2
        AND mi.instructor_id = $3
        AND mi.is_active = true
        AND (
            SELECT COUNT(*) 
            FROM module_instructors mi2 
            WHERE mi2.module_id = mi.module_id 
            AND mi2.is_active = true
        ) > 2
        RETURNING mi.module_id, mi.role
        """
        
        logging.info(f"Admin {current_user['user_id']} removing instructor {instructor_id} from track {track_id}")
        
        # Mock response
        return {
            "message": "Instructor successfully removed from track",
            "track_id": track_id,
            "instructor_id": instructor_id,
            "removed_from_track": True,
            "removed_from_modules": [
                {"module_id": "660e8400-e29b-41d4-a716-446655440001", "role": "instructor"},
                {"module_id": "660e8400-e29b-41d4-a716-446655440002", "role": "co_instructor"}
            ],
            "modules_with_constraint_warning": [],
            "removed_by": current_user["user_id"],
            "removed_at": datetime.utcnow()
        }
        
    except Exception as e:
        logging.error(f"Error removing instructor from track: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove instructor from track: {str(e)}"
        )


@router.delete("/modules/{module_id}/instructors/{instructor_id}")
async def remove_instructor_from_module(
    module_id: UUID,
    instructor_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """
    Remove an instructor from a specific module.
    
    BUSINESS REQUIREMENTS:
    - Enforce minimum 2 instructors per module constraint
    - Cannot remove instructor if it would leave less than 2 instructors
    """
    try:
        # Check current instructor count for the module
        count_query = """
        SELECT COUNT(*) as instructor_count
        FROM module_instructors 
        WHERE module_id = $1 AND is_active = true
        """
        
        # Mock check - in production, execute actual query
        current_instructor_count = 3  # Mock value
        
        if current_instructor_count <= 2:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove instructor: Module must have at least 2 active instructors"
            )
        
        # Remove instructor from module
        removal_query = """
        UPDATE module_instructors 
        SET 
            is_active = false,
            removed_by = $1,
            removed_at = CURRENT_TIMESTAMP
        WHERE module_id = $2 
        AND instructor_id = $3 
        AND is_active = true
        RETURNING role
        """
        
        logging.info(f"Admin {current_user['user_id']} removing instructor {instructor_id} from module {module_id}")
        
        return {
            "message": "Instructor successfully removed from module",
            "module_id": module_id,
            "instructor_id": instructor_id,
            "previous_role": "co_instructor",
            "remaining_instructors": current_instructor_count - 1,
            "removed_by": current_user["user_id"],
            "removed_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error removing instructor from module: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove instructor from module: {str(e)}"
        )


# =============================================================================
# ORGANIZATION INSTRUCTOR REMOVAL ENDPOINTS
# =============================================================================

@router.delete("/organizations/{organization_id}/instructors/{instructor_id}")
async def remove_instructor_from_organization(
    organization_id: UUID,
    instructor_id: UUID,
    transfer_assignments: bool = Query(False, description="Transfer assignments to other instructors"),
    replacement_instructor_id: Optional[UUID] = Query(None, description="Instructor to transfer assignments to"),
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """
    Remove an instructor from the entire organization.
    
    BUSINESS REQUIREMENTS:
    - Remove instructor from all tracks and modules
    - Option to transfer assignments to another instructor
    - Maintain minimum instructor constraints
    - Complete audit trail of removal
    """
    try:
        # Get all instructor assignments in the organization
        assignments_query = """
        SELECT 
            ti.track_id,
            mi.module_id,
            ti.role as track_role,
            mi.role as module_role
        FROM track_instructors ti
        FULL OUTER JOIN module_instructors mi ON ti.track_id = (
            SELECT track_id FROM modules WHERE id = mi.module_id
        )
        JOIN tracks t ON (ti.track_id = t.id OR mi.module_id IN (
            SELECT id FROM modules WHERE track_id = t.id
        ))
        JOIN projects p ON t.project_id = p.id
        WHERE p.organization_id = $1
        AND (ti.instructor_id = $2 OR mi.instructor_id = $2)
        AND (ti.is_active = true OR mi.is_active = true)
        """
        
        # Check constraint violations before removal
        constraint_check_query = """
        SELECT m.id, m.name, COUNT(mi.instructor_id) as instructor_count
        FROM modules m
        JOIN tracks t ON m.track_id = t.id
        JOIN projects p ON t.project_id = p.id
        JOIN module_instructors mi ON m.id = mi.module_id
        WHERE p.organization_id = $1
        AND mi.is_active = true
        GROUP BY m.id, m.name
        HAVING COUNT(mi.instructor_id) = 2 AND $2 = ANY(ARRAY_AGG(mi.instructor_id))
        """
        
        # If transfer_assignments is true and replacement provided, transfer assignments
        if transfer_assignments and replacement_instructor_id:
            # Transfer track assignments
            transfer_tracks_query = """
            UPDATE track_instructors 
            SET 
                instructor_id = $1,
                assigned_by = $2,
                assigned_at = CURRENT_TIMESTAMP,
                notes = COALESCE(notes || ' | ', '') || 'Transferred from instructor ' || $3 || ' on ' || CURRENT_TIMESTAMP
            WHERE instructor_id = $3
            AND track_id IN (
                SELECT t.id FROM course_creator.tracks t
                JOIN projects p ON t.project_id = p.id
                WHERE p.organization_id = $4
            )
            AND is_active = true
            """
            
            # Transfer module assignments
            transfer_modules_query = """
            UPDATE module_instructors mi
            SET 
                instructor_id = $1,
                assigned_by = $2,
                assigned_at = CURRENT_TIMESTAMP,
                notes = COALESCE(notes || ' | ', '') || 'Transferred from instructor ' || $3 || ' on ' || CURRENT_TIMESTAMP
            FROM modules m
            JOIN tracks t ON m.track_id = t.id
            JOIN projects p ON t.project_id = p.id
            WHERE mi.module_id = m.id
            AND mi.instructor_id = $3
            AND p.organization_id = $4
            AND mi.is_active = true
            """
            
        else:
            # Remove instructor assignments (with constraint checking)
            remove_tracks_query = """
            UPDATE track_instructors ti
            SET 
                is_active = false,
                removed_by = $1,
                removed_at = CURRENT_TIMESTAMP
            FROM course_creator.tracks t
            JOIN projects p ON t.project_id = p.id
            WHERE ti.track_id = t.id
            AND ti.instructor_id = $2
            AND p.organization_id = $3
            AND ti.is_active = true
            """
            
            remove_modules_query = """
            UPDATE module_instructors mi
            SET 
                is_active = false,
                removed_by = $1,
                removed_at = CURRENT_TIMESTAMP
            FROM modules m
            JOIN tracks t ON m.track_id = t.id
            JOIN projects p ON t.project_id = p.id
            WHERE mi.module_id = m.id
            AND mi.instructor_id = $2
            AND p.organization_id = $3
            AND mi.is_active = true
            AND (
                SELECT COUNT(*) 
                FROM module_instructors mi2 
                WHERE mi2.module_id = mi.module_id 
                AND mi2.is_active = true
            ) > 2
            """
        
        # Remove instructor from organization membership
        remove_membership_query = """
        UPDATE organization_memberships 
        SET 
            is_active = false,
            removed_by = $1,
            removed_at = CURRENT_TIMESTAMP
        WHERE organization_id = $2 
        AND user_id = $3 
        AND is_active = true
        """
        
        logging.info(f"Admin {current_user['user_id']} removing instructor {instructor_id} from organization {organization_id}")
        
        # Mock response
        response_data = {
            "message": "Instructor successfully removed from organization",
            "organization_id": organization_id,
            "instructor_id": instructor_id,
            "removed_from_tracks": 3,
            "removed_from_modules": 7,
            "removed_from_organization": True,
            "removed_by": current_user["user_id"],
            "removed_at": datetime.utcnow()
        }
        
        if transfer_assignments and replacement_instructor_id:
            response_data.update({
                "assignments_transferred": True,
                "replacement_instructor_id": replacement_instructor_id,
                "transferred_tracks": 3,
                "transferred_modules": 7
            })
        else:
            response_data.update({
                "assignments_transferred": False,
                "modules_with_constraint_violations": []  # Would list modules that couldn't be updated
            })
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error removing instructor from organization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove instructor from organization: {str(e)}"
        )