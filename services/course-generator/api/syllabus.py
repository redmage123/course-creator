"""
Syllabus API Routes

FastAPI routes for syllabus management operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
import logging

from ..services.syllabus_service import SyllabusService
from ..dependencies_new import get_syllabus_service, handle_exceptions
from ..models.syllabus import SyllabusRequest, SyllabusFeedback, SyllabusResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=SyllabusResponse)
@handle_exceptions
async def generate_syllabus(
    request: SyllabusRequest,
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """
    Generate a new syllabus for a course.
    
    Args:
        request: Syllabus generation request
        syllabus_service: Syllabus service instance
        
    Returns:
        Generated syllabus data
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        course_info = request.dict()
        syllabus_data = await syllabus_service.generate_syllabus(course_info)
        
        # Save the generated syllabus if course_id is provided
        if hasattr(request, 'course_id') and request.course_id:
            await syllabus_service.save_syllabus(request.course_id, syllabus_data)
        
        return {
            "success": True,
            "syllabus": syllabus_data,
            "message": "Syllabus generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate syllabus: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate syllabus: {str(e)}"
        )


@router.post("/refine", response_model=SyllabusResponse)
@handle_exceptions
async def refine_syllabus(
    course_id: str,
    feedback: SyllabusFeedback,
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """
    Refine an existing syllabus based on feedback.
    
    Args:
        course_id: Course identifier
        feedback: Refinement feedback
        syllabus_service: Syllabus service instance
        
    Returns:
        Refined syllabus data
        
    Raises:
        HTTPException: If refinement fails
    """
    try:
        feedback_data = feedback.dict()
        refined_syllabus = await syllabus_service.refine_syllabus(course_id, feedback_data)
        
        return {
            "success": True,
            "syllabus": refined_syllabus,
            "message": "Syllabus refined successfully"
        }
        
    except ValueError as e:
        logger.warning(f"Syllabus not found for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Syllabus not found for course {course_id}"
        )
    except Exception as e:
        logger.error(f"Failed to refine syllabus for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine syllabus: {str(e)}"
        )


@router.get("/{course_id}", response_model=Dict[str, Any])
@handle_exceptions
async def get_syllabus(
    course_id: str,
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
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
    except Exception as e:
        logger.error(f"Failed to retrieve syllabus for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve syllabus: {str(e)}"
        )


@router.put("/{course_id}", response_model=Dict[str, Any])
@handle_exceptions
async def update_syllabus(
    course_id: str,
    updates: Dict[str, Any],
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
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
    except Exception as e:
        logger.error(f"Failed to update syllabus for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update syllabus: {str(e)}"
        )


@router.delete("/{course_id}", response_model=Dict[str, Any])
@handle_exceptions
async def delete_syllabus(
    course_id: str,
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
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
    except Exception as e:
        logger.error(f"Failed to delete syllabus for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete syllabus: {str(e)}"
        )


@router.get("/", response_model=Dict[str, Any])
@handle_exceptions
async def list_syllabi(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
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
        
    except Exception as e:
        logger.error(f"Failed to list syllabi: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list syllabi: {str(e)}"
        )


@router.post("/{course_id}/validate", response_model=Dict[str, Any])
@handle_exceptions
async def validate_syllabus(
    course_id: str,
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
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
@handle_exceptions
async def save_syllabus(
    course_id: str,
    syllabus_data: Dict[str, Any],
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
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