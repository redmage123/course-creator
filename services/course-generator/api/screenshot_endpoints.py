"""
Screenshot-to-Course Generation API Endpoints

BUSINESS PURPOSE:
Provides REST API endpoints for uploading screenshots of course content
and generating complete courses using AI vision analysis. This enables
organizations to quickly create courses from existing materials like
presentation slides, documentation screenshots, or whiteboard photos.

TECHNICAL IMPLEMENTATION:
- FastAPI router with file upload handling
- Integration with multi-provider LLM vision services
- Background task processing for long-running operations
- Progress tracking and status updates

ENDPOINT SUMMARY:
- POST /upload - Upload screenshot for analysis
- POST /upload/batch - Upload multiple screenshots
- GET /{id}/status - Check analysis status
- GET /{id}/result - Get analysis result
- POST /{id}/generate-course - Generate course from analyzed screenshot
- GET /batch/{batch_id}/status - Check batch processing status
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    File,
    UploadFile,
    Form
)
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import logging
import hashlib
import os
import aiofiles
from PIL import Image
import io

# Pydantic models
from pydantic import BaseModel, Field

# Import services
from course_generator.application.services.screenshot_analysis_service import (
    ScreenshotAnalysisService,
    create_screenshot_analysis_service
)
from course_generator.application.services.screenshot_course_generator import (
    ScreenshotCourseGenerator,
    GenerationOptions,
    create_screenshot_course_generator
)
from course_generator.domain.entities.screenshot_analysis import (
    ScreenshotUpload,
    UploadStatus,
    ImageMetadata,
    DifficultyLevel
)

# Custom exceptions
from exceptions import (
    CourseCreatorBaseException,
    ValidationException,
    DatabaseException,
    APIException,
    VisionAnalysisException,
    ScreenshotUploadException,
    UnsupportedImageFormatException,
    CourseGenerationException,
    LLMProviderException,
)


logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances (lazy initialization)
_screenshot_service: Optional[ScreenshotAnalysisService] = None
_course_generator: Optional[ScreenshotCourseGenerator] = None

# In-memory storage for demo purposes (should use database in production)
_screenshot_storage: Dict[str, ScreenshotUpload] = {}
_batch_storage: Dict[str, Dict[str, Any]] = {}

# Upload configuration
UPLOAD_DIR = os.getenv("SCREENSHOT_UPLOAD_DIR", "/tmp/screenshots")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


# ================================================================
# PYDANTIC MODELS
# ================================================================

class ScreenshotUploadResponse(BaseModel):
    """Response from screenshot upload"""
    id: str
    status: str
    original_filename: str
    created_at: datetime
    message: str


class ScreenshotStatusResponse(BaseModel):
    """Screenshot processing status response"""
    id: str
    status: str
    progress_percent: float = 0.0
    error_message: Optional[str] = None
    has_analysis: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    analyzed_at: Optional[datetime] = None


class AnalysisResultResponse(BaseModel):
    """Screenshot analysis result response"""
    id: str
    screenshot_id: str
    extracted_text: str
    detected_language: str
    confidence_score: float
    has_course_structure: bool
    course_structure: Optional[Dict[str, Any]] = None
    provider_used: str
    model_used: str
    tokens_used: int
    processing_time_ms: int
    created_at: datetime


class CourseGenerationRequest(BaseModel):
    """Request to generate course from screenshot"""
    expand_modules: bool = Field(
        default=True,
        description="Expand modules with detailed lesson content"
    )
    generate_quizzes: bool = Field(
        default=True,
        description="Generate quiz questions for each module"
    )
    generate_exercises: bool = Field(
        default=True,
        description="Generate practical exercises"
    )
    difficulty_override: Optional[str] = Field(
        default=None,
        description="Override detected difficulty level"
    )
    language_override: Optional[str] = Field(
        default=None,
        description="Override detected language"
    )
    additional_context: Optional[str] = Field(
        default=None,
        description="Additional context for course generation"
    )


class GeneratedCourseResponse(BaseModel):
    """Response with generated course content"""
    id: str
    screenshot_id: str
    title: str
    description: str
    difficulty: str
    estimated_duration_hours: int
    target_audience: str
    language: str
    modules_count: int
    total_lessons_count: int
    created_at: datetime


class BatchUploadResponse(BaseModel):
    """Response from batch upload"""
    batch_id: str
    total_count: int
    status: str
    uploads: List[ScreenshotUploadResponse]


class BatchStatusResponse(BaseModel):
    """Batch processing status response"""
    batch_id: str
    status: str
    total_count: int
    completed_count: int
    failed_count: int
    progress_percent: float


# ================================================================
# SERVICE INITIALIZATION
# ================================================================

def get_screenshot_service() -> ScreenshotAnalysisService:
    """
    Get or create screenshot analysis service instance.

    Uses lazy initialization pattern to avoid circular import
    and startup timing issues.
    """
    global _screenshot_service
    if _screenshot_service is None:
        _screenshot_service = create_screenshot_analysis_service()
    return _screenshot_service


def get_course_generator() -> ScreenshotCourseGenerator:
    """Get or create course generator service instance."""
    global _course_generator
    if _course_generator is None:
        _course_generator = create_screenshot_course_generator()
    return _course_generator


# ================================================================
# HELPER FUNCTIONS
# ================================================================

async def save_upload_file(
    file: UploadFile,
    organization_id: UUID,
    user_id: UUID
) -> tuple[str, ImageMetadata]:
    """
    Save uploaded file and extract metadata.

    Args:
        file: Uploaded file
        organization_id: Organization UUID
        user_id: User UUID

    Returns:
        Tuple of (file_path, ImageMetadata)
    """
    # Validate file extension
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedImageFormatException(
            f"Unsupported file format: {ext}. "
            f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise ScreenshotUploadException(
            f"File size ({len(content) / (1024*1024):.1f}MB) "
            f"exceeds maximum ({MAX_FILE_SIZE / (1024*1024):.0f}MB)"
        )

    # Calculate hash for deduplication
    file_hash = hashlib.sha256(content).hexdigest()

    # Get image dimensions using PIL
    try:
        img = Image.open(io.BytesIO(content))
        width, height = img.size
        img_format = img.format or ext.upper()
    except IOError as e:
        raise ScreenshotUploadException(f"Invalid image file: {e}")

    # Create metadata
    metadata = ImageMetadata(
        width=width,
        height=height,
        format=img_format.lower(),
        size_bytes=len(content),
        file_hash=file_hash
    )

    # Ensure upload directory exists
    org_dir = os.path.join(UPLOAD_DIR, str(organization_id))
    os.makedirs(org_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(org_dir, f"{file_hash}.{ext}")
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    return file_path, metadata


# ================================================================
# API ENDPOINTS
# ================================================================

@router.post("/upload", response_model=ScreenshotUploadResponse)
async def upload_screenshot(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Screenshot image file"),
    organization_id: UUID = Form(..., description="Organization UUID"),
    user_id: UUID = Form(..., description="User UUID"),
    analyze_immediately: bool = Form(default=True, description="Start analysis immediately")
):
    """
    Upload a screenshot for course generation

    BUSINESS CONTEXT:
    Allows users to upload screenshots of course materials (slides,
    documentation, diagrams) to generate structured courses using AI.

    SUPPORTED FORMATS:
    - PNG, JPEG, WebP, GIF
    - Maximum file size: 20MB

    WORKFLOW:
    1. Upload and validate image
    2. Extract image metadata
    3. Optionally start AI analysis in background
    4. Return upload ID for status tracking
    """
    try:
        # Save file and get metadata
        file_path, metadata = await save_upload_file(file, organization_id, user_id)

        # Create upload record
        upload = ScreenshotUpload(
            id=uuid4(),
            organization_id=organization_id,
            user_id=user_id,
            file_path=file_path,
            original_filename=file.filename or "unknown",
            image_metadata=metadata,
            status=UploadStatus.PENDING
        )

        # Store in memory (use database in production)
        _screenshot_storage[str(upload.id)] = upload

        logger.info(
            f"Screenshot uploaded: {upload.id} by user {user_id} "
            f"for org {organization_id}"
        )

        # Start analysis in background if requested
        if analyze_immediately:
            background_tasks.add_task(
                analyze_screenshot_background,
                str(upload.id)
            )

        return ScreenshotUploadResponse(
            id=str(upload.id),
            status=upload.status.value,
            original_filename=upload.original_filename,
            created_at=upload.created_at,
            message="Screenshot uploaded successfully. Analysis will begin shortly."
                if analyze_immediately else "Screenshot uploaded. Use /analyze endpoint to start analysis."
        )

    except (UnsupportedImageFormatException, ScreenshotUploadException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_screenshot_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Multiple screenshot files"),
    organization_id: UUID = Form(..., description="Organization UUID"),
    user_id: UUID = Form(..., description="User UUID"),
):
    """
    Upload multiple screenshots for batch processing

    BUSINESS CONTEXT:
    Allows uploading multiple screenshots at once for combined
    course generation, useful for multi-slide presentations.

    LIMITS:
    - Maximum 10 files per batch
    - Maximum 20MB per file
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files per batch"
        )

    batch_id = str(uuid4())
    uploads = []
    errors = []

    for file in files:
        try:
            file_path, metadata = await save_upload_file(file, organization_id, user_id)

            upload = ScreenshotUpload(
                id=uuid4(),
                organization_id=organization_id,
                user_id=user_id,
                file_path=file_path,
                original_filename=file.filename or "unknown",
                image_metadata=metadata,
                status=UploadStatus.PENDING
            )

            _screenshot_storage[str(upload.id)] = upload
            uploads.append(ScreenshotUploadResponse(
                id=str(upload.id),
                status=upload.status.value,
                original_filename=upload.original_filename,
                created_at=upload.created_at,
                message="Queued for analysis"
            ))

        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    # Store batch info
    _batch_storage[batch_id] = {
        "upload_ids": [u.id for u in uploads],
        "total_count": len(files),
        "completed_count": 0,
        "failed_count": len(errors),
        "status": "processing",
        "errors": errors
    }

    # Start batch analysis in background
    background_tasks.add_task(
        analyze_batch_background,
        batch_id,
        [u.id for u in uploads]
    )

    logger.info(f"Batch {batch_id} created with {len(uploads)} screenshots")

    return BatchUploadResponse(
        batch_id=batch_id,
        total_count=len(files),
        status="processing",
        uploads=uploads
    )


@router.get("/{screenshot_id}/status", response_model=ScreenshotStatusResponse)
async def get_screenshot_status(screenshot_id: UUID):
    """
    Get screenshot processing status

    BUSINESS CONTEXT:
    Allows checking the progress of screenshot analysis,
    which may take 5-30 seconds depending on image complexity.
    """
    upload = _screenshot_storage.get(str(screenshot_id))

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screenshot {screenshot_id} not found"
        )

    # Calculate progress based on status
    progress_map = {
        UploadStatus.PENDING: 0.0,
        UploadStatus.VALIDATING: 10.0,
        UploadStatus.QUEUED: 20.0,
        UploadStatus.ANALYZING: 50.0,
        UploadStatus.ANALYZED: 80.0,
        UploadStatus.GENERATING: 90.0,
        UploadStatus.COMPLETED: 100.0,
        UploadStatus.FAILED: 0.0,
        UploadStatus.EXPIRED: 0.0,
    }

    return ScreenshotStatusResponse(
        id=str(upload.id),
        status=upload.status.value,
        progress_percent=progress_map.get(upload.status, 0.0),
        error_message=upload.error_message,
        has_analysis=upload.analysis_result is not None,
        created_at=upload.created_at,
        updated_at=upload.updated_at,
        analyzed_at=upload.analyzed_at
    )


@router.get("/{screenshot_id}/result", response_model=AnalysisResultResponse)
async def get_analysis_result(screenshot_id: UUID):
    """
    Get screenshot analysis result

    BUSINESS CONTEXT:
    Returns the AI-extracted content and course structure
    from the analyzed screenshot.

    PRECONDITION:
    Screenshot must have status 'analyzed' or later.
    """
    upload = _screenshot_storage.get(str(screenshot_id))

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screenshot {screenshot_id} not found"
        )

    if not upload.analysis_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Screenshot {screenshot_id} has not been analyzed yet. "
                   f"Current status: {upload.status.value}"
        )

    result = upload.analysis_result

    return AnalysisResultResponse(
        id=str(result.id),
        screenshot_id=str(result.screenshot_id),
        extracted_text=result.extracted_text[:1000] + "..." if len(result.extracted_text) > 1000 else result.extracted_text,
        detected_language=result.detected_language,
        confidence_score=result.confidence_score,
        has_course_structure=result.has_course_structure,
        course_structure=result.course_structure.to_dict() if result.course_structure else None,
        provider_used=result.provider_used,
        model_used=result.model_used,
        tokens_used=result.tokens_used,
        processing_time_ms=result.processing_time_ms,
        created_at=result.created_at
    )


@router.post("/{screenshot_id}/generate-course", response_model=GeneratedCourseResponse)
async def generate_course_from_screenshot(
    screenshot_id: UUID,
    request: CourseGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a complete course from analyzed screenshot

    BUSINESS CONTEXT:
    Takes the analyzed screenshot content and generates a full
    course with modules, lessons, and optionally quizzes/exercises.

    PRECONDITION:
    Screenshot must have been analyzed (status 'analyzed' or later).
    """
    upload = _screenshot_storage.get(str(screenshot_id))

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screenshot {screenshot_id} not found"
        )

    if not upload.analysis_result or not upload.analysis_result.course_structure:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Screenshot has no course structure. Please analyze first."
        )

    try:
        # Get course generator
        generator = get_course_generator()

        # Build generation options
        difficulty = None
        if request.difficulty_override:
            try:
                difficulty = DifficultyLevel(request.difficulty_override.lower())
            except ValueError:
                pass

        options = GenerationOptions(
            expand_modules=request.expand_modules,
            generate_quizzes=request.generate_quizzes,
            generate_exercises=request.generate_exercises,
            difficulty_override=difficulty,
            language_override=request.language_override,
            additional_context=request.additional_context
        )

        # Generate course
        generated = await generator.generate_course(
            upload.analysis_result,
            options
        )

        # Update upload status
        upload.mark_completed(generated.id)

        logger.info(f"Generated course {generated.id} from screenshot {screenshot_id}")

        # Count total lessons
        total_lessons = sum(len(m.lessons) for m in generated.modules)

        return GeneratedCourseResponse(
            id=str(generated.id),
            screenshot_id=str(screenshot_id),
            title=generated.title,
            description=generated.description,
            difficulty=generated.difficulty.value,
            estimated_duration_hours=generated.estimated_duration_hours,
            target_audience=generated.target_audience,
            language=generated.language,
            modules_count=len(generated.modules),
            total_lessons_count=total_lessons,
            created_at=generated.created_at
        )

    except LLMProviderException as e:
        logger.error(f"LLM provider error during generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )
    except CourseGenerationException as e:
        logger.error(f"Course generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{screenshot_id}/analyze")
async def analyze_screenshot(
    screenshot_id: UUID,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger analysis for a screenshot

    BUSINESS CONTEXT:
    Use this if auto-analysis was disabled during upload
    or if re-analysis is needed.
    """
    upload = _screenshot_storage.get(str(screenshot_id))

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screenshot {screenshot_id} not found"
        )

    if upload.status == UploadStatus.ANALYZING:
        return {"message": "Analysis already in progress", "status": upload.status.value}

    # Start analysis in background
    background_tasks.add_task(
        analyze_screenshot_background,
        str(screenshot_id)
    )

    return {"message": "Analysis started", "status": "analyzing"}


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """
    Get batch processing status

    BUSINESS CONTEXT:
    Track progress of multiple screenshot uploads being
    processed together.
    """
    batch = _batch_storage.get(batch_id)

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found"
        )

    # Calculate current status
    completed = 0
    failed = 0
    for upload_id in batch.get("upload_ids", []):
        upload = _screenshot_storage.get(upload_id)
        if upload:
            if upload.status == UploadStatus.COMPLETED:
                completed += 1
            elif upload.status == UploadStatus.FAILED:
                failed += 1

    total = batch.get("total_count", 0)
    progress = (completed + failed) / total * 100 if total > 0 else 0

    status_str = "completed" if completed + failed >= total else "processing"

    return BatchStatusResponse(
        batch_id=batch_id,
        status=status_str,
        total_count=total,
        completed_count=completed,
        failed_count=failed,
        progress_percent=progress
    )


# ================================================================
# BACKGROUND TASKS
# ================================================================

async def analyze_screenshot_background(screenshot_id: str):
    """
    Background task to analyze a screenshot.

    Called automatically after upload or manually via analyze endpoint.
    """
    upload = _screenshot_storage.get(screenshot_id)
    if not upload:
        logger.error(f"Screenshot {screenshot_id} not found for analysis")
        return

    try:
        service = get_screenshot_service()

        # Read image data
        async with aiofiles.open(upload.file_path, "rb") as f:
            image_data = await f.read()

        # Perform analysis
        analyzed_upload = await service.analyze_screenshot(
            image_data=image_data,
            filename=upload.original_filename,
            organization_id=upload.organization_id,
            user_id=upload.user_id
        )

        # Update stored upload
        upload.analysis_result = analyzed_upload.analysis_result
        upload.status = analyzed_upload.status
        upload.analyzed_at = analyzed_upload.analyzed_at
        upload.updated_at = datetime.utcnow()

        logger.info(f"Screenshot {screenshot_id} analyzed successfully")

    except Exception as e:
        logger.error(f"Analysis failed for {screenshot_id}: {e}")
        upload.mark_failed(str(e))


async def analyze_batch_background(batch_id: str, upload_ids: List[str]):
    """
    Background task to analyze a batch of screenshots.
    """
    for upload_id in upload_ids:
        await analyze_screenshot_background(upload_id)

    # Update batch status
    batch = _batch_storage.get(batch_id)
    if batch:
        batch["status"] = "completed"
        logger.info(f"Batch {batch_id} analysis completed")
