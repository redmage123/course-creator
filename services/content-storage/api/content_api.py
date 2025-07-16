"""
Content API

FastAPI routes for content storage operations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Depends, status
from fastapi.responses import StreamingResponse
import io

from models.content import (
    ContentUpdate, ContentSearchRequest, ContentUploadResponse, 
    ContentListResponse, ContentResponse, ContentStats
)
from services.content_service import ContentService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_content_service() -> ContentService:
    """Dependency injection for content service."""
    # This would be replaced with actual dependency injection
    # For now, return None and handle in the endpoint
    return None


@router.post("/upload", response_model=ContentUploadResponse)
async def upload_content(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Query(None),
    content_service: ContentService = Depends(get_content_service)
):
    """Upload content file."""
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Upload content
        result = await content_service.upload_content(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by=uploaded_by
        )
        
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload content"
            )
            
    except Exception as e:
        logger.error(f"Error uploading content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    content_service: ContentService = Depends(get_content_service)
):
    """Get content metadata by ID."""
    try:
        result = await content_service.get_content(content_id)
        
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/content/{content_id}/download")
async def download_content(
    content_id: str,
    content_service: ContentService = Depends(get_content_service)
):
    """Download content file."""
    try:
        result = await content_service.get_content_file(content_id)
        
        if result:
            return StreamingResponse(
                io.BytesIO(result["content"]),
                media_type=result["content_type"],
                headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/content", response_model=ContentListResponse)
async def list_content(
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    uploaded_by: Optional[str] = Query(None),
    content_service: ContentService = Depends(get_content_service)
):
    """List content with pagination."""
    try:
        result = await content_service.list_content(
            page=page,
            per_page=per_page,
            uploaded_by=uploaded_by
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/content/search", response_model=ContentListResponse)
async def search_content(
    search_request: ContentSearchRequest,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    content_service: ContentService = Depends(get_content_service)
):
    """Search content with filters."""
    try:
        result = await content_service.search_content(
            search_request=search_request,
            page=page,
            per_page=per_page
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/content/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    update_data: ContentUpdate,
    content_service: ContentService = Depends(get_content_service)
):
    """Update content metadata."""
    try:
        result = await content_service.update_content(content_id, update_data)
        
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: str,
    permanent: bool = Query(False),
    content_service: ContentService = Depends(get_content_service)
):
    """Delete content (soft delete by default)."""
    try:
        if permanent:
            success = await content_service.permanently_delete_content(content_id)
        else:
            success = await content_service.delete_content(content_id)
        
        if success:
            return {"message": "Content deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stats", response_model=ContentStats)
async def get_content_stats(
    uploaded_by: Optional[str] = Query(None),
    content_service: ContentService = Depends(get_content_service)
):
    """Get content statistics."""
    try:
        result = await content_service.get_content_stats(uploaded_by)
        return result
        
    except Exception as e:
        logger.error(f"Error getting content stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/content/{content_id}/backup")
async def create_content_backup(
    content_id: str,
    backup_path: str = Query(..., description="Backup destination path"),
    content_service: ContentService = Depends(get_content_service)
):
    """Create backup of specific content."""
    try:
        success = await content_service.create_backup(content_id, backup_path)
        
        if success:
            return {"message": "Backup created successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )