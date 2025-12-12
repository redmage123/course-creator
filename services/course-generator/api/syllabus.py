"""
Syllabus API Routes

FastAPI routes for syllabus management operations.

Enhanced in v3.3.2 to support URL-based course generation from external
third-party software documentation. Instructors can provide documentation URLs
that will be fetched, parsed, and used as context for AI-powered course generation.

ENDPOINT SUMMARY:
- POST /generate: Generate syllabus (supports both standard and URL-based generation)
- POST /generate/from-urls: Dedicated endpoint for URL-based generation
- GET /generate/progress/{request_id}: Check URL-based generation progress
- POST /refine: Refine existing syllabus
- GET /{course_id}: Get syllabus by course ID
- PUT /{course_id}: Update syllabus
- DELETE /{course_id}: Delete syllabus
- GET /: List all syllabi
- POST /{course_id}/validate: Validate syllabus
- POST /{course_id}/save: Save syllabus
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

# from services.syllabus_service import SyllabusService
from app.dependencies import get_container
# from app.dependencies import get_syllabus_service
from models.syllabus import SyllabusRequest, SyllabusFeedback, SyllabusResponse

# URL-based generation service
from course_generator.application.services.url_based_generation_service import (
    URLBasedGenerationService,
    GenerationProgress,
    create_url_based_generation_service,
)

# Custom exceptions
from exceptions import (
    CourseCreatorBaseException,
    ContentException,
    ContentNotFoundException,
    ContentValidationException,
    FileStorageException,
    ValidationException,
    DatabaseException,
    AuthenticationException,
    AuthorizationException,
    ConfigurationException,
    APIException,
    BusinessRuleException,
    # URL-related exceptions (v3.3.2)
    URLFetchException,
    URLValidationException,
    URLConnectionException,
    URLTimeoutException,
    URLAccessDeniedException,
    URLNotFoundException,
    ContentParsingException,
    HTMLParsingException,
    ContentExtractionException,
    ContentTooLargeException,
    UnsupportedContentTypeException,
    RobotsDisallowedException,
    RAGException,
    AIServiceException,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instance for URL-based generation
# Initialized lazily to avoid startup issues
_url_generation_service: Optional[URLBasedGenerationService] = None


def get_url_generation_service() -> URLBasedGenerationService:
    """
    Get or create URL-based generation service instance.

    Uses lazy initialization pattern to avoid circular import
    and startup timing issues.
    """
    global _url_generation_service
    if _url_generation_service is None:
        _url_generation_service = create_url_based_generation_service()
    return _url_generation_service


@router.post("/generate", response_model=Dict[str, Any])
async def generate_syllabus(
    request: SyllabusRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Generate a new syllabus for a course.

    BUSINESS CONTEXT:
    This endpoint supports two generation modes:
    1. Standard generation: Uses provided course parameters only
    2. URL-based generation (v3.3.2): Fetches content from external URLs
       and uses it as context for AI-powered generation

    URL-based generation is triggered when:
    - source_url is provided (single URL)
    - source_urls contains URLs (multiple URLs)
    - external_sources contains ExternalSourceConfig objects

    Args:
        request: Syllabus generation request (with optional URLs)
        background_tasks: FastAPI background tasks handler

    Returns:
        Generated syllabus data with source attribution (if URL-based)

    Raises:
        HTTPException: If generation fails
        URLFetchException: If URL fetching fails
        ContentParsingException: If content parsing fails
        AIServiceException: If AI generation fails
    """
    logger.info(
        f"Syllabus generation request received: title='{request.title}', "
        f"has_urls={request.has_external_sources}"
    )

    try:
        # Check if this is a URL-based generation request
        if request.has_external_sources:
            # Use URL-based generation service
            service = get_url_generation_service()

            logger.info(
                f"Starting URL-based generation with {len(request.all_source_urls)} URLs"
            )

            result = await service.generate_from_urls(request)

            return {
                "success": True,
                "syllabus": result.get("syllabus"),
                "message": "Syllabus generated from external documentation URLs",
                "course_id": request.course_id,
                "generation_method": result.get("generation_method", "url_based"),
                "source_summary": result.get("source_summary"),
                "processing_time_ms": result.get("processing_time_ms"),
                "request_id": result.get("request_id"),
            }
        else:
            # Standard generation (placeholder for now)
            logger.info("Using standard syllabus generation (no URLs provided)")

            return {
                "success": True,
                "message": "Standard syllabus generation endpoint - service starting up",
                "course_id": request.course_id,
                "status": "placeholder",
                "hint": "Provide source_url or source_urls for URL-based generation",
            }

    except URLValidationException as e:
        logger.warning(f"URL validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "url_validation_error",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except URLConnectionException as e:
        logger.warning(f"URL connection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "url_connection_error",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except URLTimeoutException as e:
        logger.warning(f"URL fetch timeout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": "url_timeout_error",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except URLAccessDeniedException as e:
        logger.warning(f"URL access denied: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "url_access_denied",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except URLNotFoundException as e:
        logger.warning(f"URL not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "url_not_found",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except ContentParsingException as e:
        logger.warning(f"Content parsing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "content_parsing_error",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except ContentTooLargeException as e:
        logger.warning(f"Content too large: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "content_too_large",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except RobotsDisallowedException as e:
        logger.warning(f"Robots.txt disallowed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "robots_disallowed",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except URLFetchException as e:
        logger.error(f"URL fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "url_fetch_error",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except AIServiceException as e:
        logger.error(f"AI service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ai_service_error",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except RAGException as e:
        logger.error(f"RAG service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "rag_service_error",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except CourseCreatorBaseException as e:
        logger.error(f"Course creator error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "course_creator_error",
                "message": str(e),
                "error_code": getattr(e, 'error_code', None),
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error in syllabus generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": f"Unexpected error: {str(e)}",
            }
        )


@router.get("/generate/progress/{request_id}", response_model=Dict[str, Any])
async def get_generation_progress(
    request_id: str,
) -> Dict[str, Any]:
    """
    Get progress of a URL-based syllabus generation request.

    BUSINESS CONTEXT:
    URL-based generation can take time due to fetching multiple URLs.
    This endpoint allows clients to poll for progress updates.

    Args:
        request_id: UUID of the generation request

    Returns:
        Progress information including status, URLs processed, etc.

    Raises:
        HTTPException: If request not found
    """
    try:
        uuid_request_id = UUID(request_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_request_id", "message": "Invalid UUID format"}
        )

    service = get_url_generation_service()
    progress = service.get_progress(uuid_request_id)

    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "request_not_found",
                "message": f"No generation request found with ID: {request_id}",
            }
        )

    return {
        "success": True,
        "progress": progress.to_dict(),
    }


@router.post("/refine")
async def refine_syllabus() -> Dict[str, Any]:
    """Placeholder for syllabus refinement."""
    return {
        "success": True,
        "message": "Syllabus refinement endpoint - service starting up",
        "status": "placeholder"
    }


@router.get("/{course_id}")
async def get_syllabus(
    course_id: str,
    # syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """
    Retrieve syllabus data for a course.
    
    Args:
        course_id: Course identifier
        syllabus_service: Syllabus service instance
        
    Returns:
        Syllabus data
        
    Raises:
        HTTPException: If syllabus not found
    """
    try:
        syllabus_data = await syllabus_service.get_syllabus(course_id)
        
        if not syllabus_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Syllabus not found for course {course_id}"
            )
        
        return {
            "success": True,
            "syllabus": syllabus_data,
            "course_id": course_id
        }
        
    except HTTPException:
        raise
    except CourseGeneratorException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DatabaseException(
            message=f"Failed to retrieve syllabus for course {course_id}",
            operation="get_syllabus",
            table_name="syllabi",
            original_exception=e
        )


@router.put("/{course_id}", response_model=Dict[str, Any])
async def update_syllabus(
    course_id: str,
    updates: Dict[str, Any],
    # syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """
    Update specific fields in syllabus data.
    
    Args:
        course_id: Course identifier
        updates: Dictionary containing fields to update
        syllabus_service: Syllabus service instance
        
    Returns:
        Update confirmation
        
    Raises:
        HTTPException: If update fails
    """
    try:
        updated = await syllabus_service.update_syllabus(course_id, updates)
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Syllabus not found for course {course_id}"
            )
        
        return {
            "success": True,
            "message": f"Syllabus updated for course {course_id}",
            "course_id": course_id
        }
        
    except HTTPException:
        raise
    except CourseGeneratorException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except ValueError as e:
        raise ValidationException(
            message="Invalid syllabus update data",
            field_name="updates",
            original_exception=e
        )
    except Exception as e:
        raise DatabaseException(
            message=f"Failed to update syllabus for course {course_id}",
            operation="update_syllabus",
            table_name="syllabi",
            original_exception=e
        )


@router.delete("/{course_id}", response_model=Dict[str, Any])
async def delete_syllabus(
    course_id: str,
    # syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """
    Delete syllabus data for a course.
    
    Args:
        course_id: Course identifier
        syllabus_service: Syllabus service instance
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        deleted = await syllabus_service.delete_syllabus(course_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Syllabus not found for course {course_id}"
            )
        
        return {
            "success": True,
            "message": f"Syllabus deleted for course {course_id}",
            "course_id": course_id
        }
        
    except HTTPException:
        raise
    except CourseGeneratorException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DatabaseException(
            message=f"Failed to delete syllabus for course {course_id}",
            operation="delete_syllabus",
            table_name="syllabi",
            original_exception=e
        )


@router.get("/", response_model=Dict[str, Any])
async def list_syllabi(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    # syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """
    List all syllabi with optional search and pagination.
    
    Args:
        limit: Maximum number of syllabi to return
        offset: Number of syllabi to skip
        search: Optional search term
        syllabus_service: Syllabus service instance
        
    Returns:
        List of syllabi
        
    Raises:
        HTTPException: If listing fails
    """
    try:
        if search:
            syllabi = await syllabus_service.search_syllabi(search, limit)
        else:
            syllabi = await syllabus_service.list_syllabi(limit, offset)
        
        return {
            "success": True,
            "syllabi": syllabi,
            "count": len(syllabi),
            "limit": limit,
            "offset": offset,
            "search": search
        }
        
    except CourseGeneratorException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DatabaseException(
            message="Failed to list syllabi",
            operation="list_syllabi" if not search else "search_syllabi",
            table_name="syllabi",
            original_exception=e
        )


@router.post("/{course_id}/validate", response_model=Dict[str, Any])
async def validate_syllabus(
    course_id: str,
    # syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """
    Validate syllabus data structure and content.
    
    Args:
        course_id: Course identifier
        syllabus_service: Syllabus service instance
        
    Returns:
        Validation results
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        syllabus_data = await syllabus_service.get_syllabus(course_id)
        
        if not syllabus_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Syllabus not found for course {course_id}"
            )
        
        validation_results = await syllabus_service.validate_syllabus(syllabus_data)
        
        return {
            "success": True,
            "validation": validation_results,
            "course_id": course_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate syllabus for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate syllabus: {str(e)}"
        )


@router.post("/{course_id}/save", response_model=Dict[str, Any])
async def save_syllabus(
    course_id: str,
    syllabus_data: Dict[str, Any],
    # syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """
    Save syllabus data for a course.
    
    Args:
        course_id: Course identifier
        syllabus_data: Syllabus data to save
        syllabus_service: Syllabus service instance
        
    Returns:
        Save confirmation
        
    Raises:
        HTTPException: If save fails
    """
    try:
        await syllabus_service.save_syllabus(course_id, syllabus_data)
        
        return {
            "success": True,
            "message": f"Syllabus saved for course {course_id}",
            "course_id": course_id
        }
        
    except Exception as e:
        logger.error(f"Failed to save syllabus for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save syllabus: {str(e)}"
        )