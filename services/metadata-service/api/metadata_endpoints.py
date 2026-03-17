"""
Metadata API Endpoints

BUSINESS REQUIREMENT:
REST API for metadata management operations including CRUD,
search, bulk operations, and enrichment.

DESIGN PATTERN:
RESTful API with FastAPI following OpenAPI standards
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from metadata_service.application.services.metadata_service import (
    MetadataService,
    MetadataServiceError,
    MetadataValidationError,
    BulkOperationError
)
from metadata_service.domain.entities.metadata import Metadata as MetadataEntity
from data_access.metadata_dao import MetadataDAO


# Pydantic Models for Request/Response
class MetadataCreate(BaseModel):
    """Request model for creating metadata"""
    entity_id: UUID
    entity_type: str = Field(..., description="Type of entity (course, content, user, etc.)")
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    auto_extract_tags: bool = Field(default=False, description="Auto-extract tags from title/description")


class MetadataUpdate(BaseModel):
    """Request model for updating metadata"""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class MetadataResponse(BaseModel):
    """Response model for metadata"""
    id: UUID
    entity_id: UUID
    entity_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str]
    keywords: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Request model for metadata search"""
    query: str
    entity_types: Optional[List[str]] = None
    required_tags: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)


class FuzzySearchRequest(BaseModel):
    """
    Request model for fuzzy search with typo tolerance

    BUSINESS VALUE:
    Enables students to find courses even with typos or partial search terms
    """
    query: str = Field(..., description="Search query (typos allowed!)")
    entity_types: Optional[List[str]] = Field(None, description="Filter by entity types")
    similarity_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0.0-1.0). Lower = more forgiving"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")


class FuzzySearchResult(BaseModel):
    """
    Response model for fuzzy search results with similarity scores

    BUSINESS VALUE:
    Shows match quality to users so they understand result relevance
    """
    id: UUID
    entity_id: UUID
    entity_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str]
    keywords: List[str]
    metadata: Dict[str, Any]
    similarity_score: float = Field(..., description="Match quality (0.0-1.0)")
    created_at: str
    updated_at: str
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class BulkCreateRequest(BaseModel):
    """Request model for bulk metadata creation"""
    metadata_list: List[MetadataCreate]
    stop_on_error: bool = Field(default=False)


# Router
router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])


# Dependency injection
async def get_metadata_service() -> MetadataService:
    """
    Dependency to provide MetadataService instance

    TODO: Replace with proper dependency injection container
    """
    from infrastructure.database import get_database_pool
    pool = await get_database_pool()
    dao = MetadataDAO(pool)
    return MetadataService(dao)


@router.post("/", response_model=MetadataResponse, status_code=status.HTTP_201_CREATED)
async def create_metadata(
    request: MetadataCreate,
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Create new metadata record

    BUSINESS LOGIC:
    - Creates metadata for an entity
    - Optionally auto-extracts tags from title/description
    - Returns created metadata with generated ID

    Args:
        request: Metadata creation request
        service: Injected MetadataService

    Returns:
        Created metadata

    Raises:
        400: Validation error
        409: Metadata already exists
    """
    try:
        # Convert request to entity
        metadata = MetadataEntity(
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            title=request.title,
            description=request.description,
            tags=request.tags,
            keywords=request.keywords,
            metadata=request.metadata
        )

        # Create via service
        created = await service.create_metadata(
            metadata,
            auto_extract_tags=request.auto_extract_tags
        )

        # Convert to response
        return MetadataResponse(**created.to_dict())

    except MetadataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except MetadataServiceError as e:
        if "already exists" in str(e).lower():
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{metadata_id}", response_model=MetadataResponse)
async def get_metadata_by_id(
    metadata_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Retrieve metadata by ID

    Args:
        metadata_id: Metadata UUID
        service: Injected MetadataService

    Returns:
        Metadata entity

    Raises:
        404: Metadata not found
    """
    metadata = await service.get_metadata_by_id(metadata_id)

    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")

    return MetadataResponse(**metadata.to_dict())


@router.get("/entity/{entity_id}", response_model=MetadataResponse)
async def get_metadata_by_entity(
    entity_id: UUID,
    entity_type: str = Query(..., description="Entity type"),
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Retrieve metadata by entity_id and entity_type

    PRIMARY USE CASE:
    Get metadata for a specific entity (e.g., course, content)

    Args:
        entity_id: Entity UUID
        entity_type: Entity type
        service: Injected MetadataService

    Returns:
        Metadata entity

    Raises:
        404: Metadata not found
    """
    metadata = await service.get_metadata_by_entity(entity_id, entity_type)

    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")

    return MetadataResponse(**metadata.to_dict())


@router.get("/type/{entity_type}", response_model=List[MetadataResponse])
async def list_metadata_by_type(
    entity_type: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: MetadataService = Depends(get_metadata_service)
):
    """
    List all metadata for entity type

    Args:
        entity_type: Entity type to filter by
        limit: Maximum results (1-1000)
        offset: Pagination offset
        service: Injected MetadataService

    Returns:
        List of metadata entities
    """
    metadata_list = await service.list_metadata_by_type(
        entity_type,
        limit=limit,
        offset=offset
    )

    return [MetadataResponse(**m.to_dict()) for m in metadata_list]


@router.put("/{metadata_id}", response_model=MetadataResponse)
async def update_metadata(
    metadata_id: UUID,
    request: MetadataUpdate,
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Update metadata (partial update)

    BUSINESS LOGIC:
    - Updates only specified fields
    - Preserves other fields
    - Automatically updates updated_at timestamp

    Args:
        metadata_id: Metadata UUID
        request: Update request
        service: Injected MetadataService

    Returns:
        Updated metadata

    Raises:
        404: Metadata not found
        400: Validation error
    """
    try:
        # Build update dict (only non-None values)
        updates = {}
        if request.title is not None:
            updates['title'] = request.title
        if request.description is not None:
            updates['description'] = request.description
        if request.tags is not None:
            updates['tags'] = request.tags
        if request.keywords is not None:
            updates['keywords'] = request.keywords
        if request.metadata is not None:
            updates['metadata'] = request.metadata

        # Perform partial update
        updated = await service.partial_update_metadata(metadata_id, updates)

        return MetadataResponse(**updated.to_dict())

    except MetadataServiceError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{metadata_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metadata(
    metadata_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Delete metadata by ID

    Args:
        metadata_id: Metadata UUID
        service: Injected MetadataService

    Returns:
        204 No Content

    Raises:
        404: Metadata not found
    """
    deleted = await service.delete_metadata(metadata_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Metadata not found")

    return None


@router.post("/search", response_model=List[MetadataResponse])
async def search_metadata(
    request: SearchRequest,
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Full-text search on metadata

    SEARCH FEATURES:
    - Full-text search across title, description, tags, keywords
    - Filter by entity types
    - Filter by required tags
    - Results ranked by relevance

    Args:
        request: Search request
        service: Injected MetadataService

    Returns:
        List of matching metadata ranked by relevance
    """
    results = await service.search_metadata(
        request.query,
        entity_types=request.entity_types,
        required_tags=request.required_tags,
        limit=request.limit
    )

    return [MetadataResponse(**m.to_dict()) for m in results]


@router.post("/search/fuzzy")
async def fuzzy_search_metadata(
    request: FuzzySearchRequest,
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Fuzzy search with typo tolerance and partial matching

    BUSINESS USE CASE:
    Students can find courses even when they make typos or use incomplete search terms.
    For example, searching for "pyton" will find "Python" courses.

    TECHNICAL IMPLEMENTATION:
    - Uses PostgreSQL pg_trgm trigram similarity
    - Checks each tag/keyword individually for better accuracy
    - Returns similarity scores (0.0-1.0) for match quality
    - Results sorted by relevance (highest similarity first)

    SIMILARITY THRESHOLD GUIDE:
    - 0.1-0.2: Very forgiving (good for student searches with typos)
    - 0.3-0.4: Balanced (default)
    - 0.5-0.7: Strict (closer matches only)
    - 0.8-1.0: Very strict (almost exact matches)

    Args:
        request: Fuzzy search request with query and options
        service: Injected MetadataService

    Returns:
        JSON with results array containing metadata + similarity scores

    Example Request:
        POST /api/v1/metadata/search/fuzzy
        {
            "query": "pyton",
            "entity_types": ["course"],
            "similarity_threshold": 0.2,
            "limit": 20
        }

    Example Response:
        {
            "results": [
                {
                    "id": "...",
                    "entity_id": "...",
                    "entity_type": "course",
                    "title": "Python Programming Fundamentals",
                    "description": "Learn Python from scratch",
                    "tags": ["python", "programming", "beginner"],
                    "keywords": ["python", "coding"],
                    "metadata": {"difficulty": "beginner"},
                    "similarity_score": 0.44,
                    "created_at": "...",
                    "updated_at": "..."
                }
            ]
        }
    """
    # Get DAO directly for fuzzy search (bypass service layer for now)
    from infrastructure.database import get_database_pool
    pool = await get_database_pool()
    dao = MetadataDAO(pool)

    # Call DAO fuzzy search method
    results_with_scores = await dao.search_fuzzy(
        search_query=request.query,
        entity_types=request.entity_types,
        similarity_threshold=request.similarity_threshold,
        limit=request.limit
    )

    # Format results with similarity scores
    formatted_results = []
    for metadata, similarity_score in results_with_scores:
        result_dict = metadata.to_dict()
        result_dict['similarity_score'] = similarity_score
        formatted_results.append(FuzzySearchResult(**result_dict))

    return {"results": formatted_results}


@router.get("/tags/{tags}", response_model=List[MetadataResponse])
async def get_by_tags(
    tags: str,  # Path parameter, not Query
    entity_type: Optional[str] = Query(None),
    limit: int = Query(default=100, ge=1, le=1000),
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Retrieve metadata by tags

    Args:
        tags: Comma-separated tags (must have all) - path parameter
        entity_type: Optional entity type filter
        limit: Maximum results
        service: Injected MetadataService

    Returns:
        List of metadata with matching tags
    """
    tag_list = [tag.strip() for tag in tags.split(',')]

    results = await service.get_by_tags(
        tag_list,
        entity_type=entity_type,
        limit=limit
    )

    return [MetadataResponse(**m.to_dict()) for m in results]


@router.post("/bulk", response_model=Dict[str, Any])
async def bulk_create_metadata(
    request: BulkCreateRequest,
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Create multiple metadata records

    BULK OPERATION:
    - Efficient batch creation
    - Optional stop-on-error mode
    - Returns success/failure counts

    Args:
        request: Bulk create request
        service: Injected MetadataService

    Returns:
        Summary of created metadata

    Raises:
        207: Partial success (some failed)
        400: All failed or validation error
    """
    try:
        # Convert requests to entities
        metadata_list = [
            MetadataEntity(
                entity_id=m.entity_id,
                entity_type=m.entity_type,
                title=m.title,
                description=m.description,
                tags=m.tags,
                keywords=m.keywords,
                metadata=m.metadata
            )
            for m in request.metadata_list
        ]

        # Bulk create
        created = await service.bulk_create_metadata(
            metadata_list,
            stop_on_error=request.stop_on_error
        )

        return {
            "created_count": len(created),
            "total_count": len(request.metadata_list),
            "created": [MetadataResponse(**m.to_dict()) for m in created]
        }

    except BulkOperationError as e:
        # Partial success
        if e.successful_count > 0:
            raise HTTPException(
                status_code=207,
                detail={
                    "message": str(e),
                    "successful_count": e.successful_count,
                    "total_count": e.total_count
                }
            )
        # All failed
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{metadata_id}/enrich", response_model=MetadataResponse)
async def enrich_metadata(
    metadata_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    """
    Enrich metadata with auto-extracted information

    ENRICHMENT:
    - Auto-extract tags from title/description
    - Extract topics and keywords
    - Updates metadata in database

    Args:
        metadata_id: Metadata UUID
        service: Injected MetadataService

    Returns:
        Enriched metadata

    Raises:
        404: Metadata not found
    """
    # Get existing metadata
    metadata = await service.get_metadata_by_id(metadata_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")

    # Enrich
    enriched = await service.enrich_metadata(metadata)

    return MetadataResponse(**enriched.to_dict())


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint

    Returns:
        Service health status
    """
    return {"status": "healthy", "service": "metadata-service"}
