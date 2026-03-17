"""
Analytics API Endpoints for Course Material Tracking

BUSINESS REQUIREMENT:
REST API for querying materialized view analytics on file uploads/downloads

TDD: Endpoints created after DAO tests passed (GREEN phase complete)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from data_access.metadata_dao import MetadataDAO

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/uploads/course/{course_id}")
async def get_upload_analytics_by_course(
    course_id: int,
    dao: MetadataDAO = Depends()
) -> List[Dict[str, Any]]:
    """Get upload analytics for specific course"""
    return await dao.get_upload_analytics_by_course(course_id)


@router.get("/uploads/file-type/{file_type}")
async def get_upload_analytics_by_file_type(
    file_type: str,
    dao: MetadataDAO = Depends()
) -> List[Dict[str, Any]]:
    """Get upload analytics for specific file type"""
    return await dao.get_upload_analytics_by_file_type(file_type)


@router.get("/downloads/course/{course_id}")
async def get_download_analytics_by_course(
    course_id: int,
    dao: MetadataDAO = Depends()
) -> List[Dict[str, Any]]:
    """Get download analytics for specific course"""
    return await dao.get_download_analytics_by_course(course_id)


@router.get("/downloads/most-downloaded")
async def get_most_downloaded_files(
    limit: int = 10,
    dao: MetadataDAO = Depends()
) -> List[Dict[str, Any]]:
    """Get most downloaded files"""
    return await dao.get_most_downloaded_files(limit)


@router.get("/summary/course/{course_id}")
async def get_course_material_summary(
    course_id: int,
    dao: MetadataDAO = Depends()
) -> List[Dict[str, Any]]:
    """Get combined upload/download summary"""
    return await dao.get_course_material_summary(course_id)


@router.get("/engagement")
async def get_engagement_metrics(
    limit: int = 20,
    dao: MetadataDAO = Depends()
) -> List[Dict[str, Any]]:
    """Get engagement metrics (downloads per upload)"""
    return await dao.get_engagement_metrics(limit)


@router.post("/refresh")
async def refresh_analytics_views(
    dao: MetadataDAO = Depends()
) -> Dict[str, str]:
    """Refresh all analytics materialized views"""
    await dao.refresh_analytics_views()
    return {"status": "success", "message": "Analytics views refreshed"}


@router.get("/search")
async def search_course_materials(
    query: str,
    entity_type: str = None,
    course_id: int = None,
    limit: int = 50,
    dao: MetadataDAO = Depends()
) -> List[Dict[str, Any]]:
    """Full-text search for course materials"""
    return await dao.search_course_materials(query, entity_type, course_id, limit)


@router.get("/fuzzy-search")
async def fuzzy_search_course_materials(
    text: str,
    similarity: float = 0.3,
    limit: int = 50,
    dao: MetadataDAO = Depends()
) -> List[Dict[str, Any]]:
    """Fuzzy similarity search with typo tolerance"""
    return await dao.fuzzy_search_course_materials(text, similarity, limit)
