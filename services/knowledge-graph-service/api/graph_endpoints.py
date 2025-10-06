"""
Knowledge Graph API Endpoints

BUSINESS REQUIREMENT:
Expose RESTful API for knowledge graph operations including
node/edge management, graph queries, and visualization data.

BUSINESS VALUE:
- Enables frontend integration
- Provides programmatic access to graph
- Supports real-time graph updates
- Powers visualization components

TECHNICAL IMPLEMENTATION:
- FastAPI REST endpoints
- Pydantic request/response models
- Async database operations
- Error handling and validation

WHY:
Frontend and external systems need HTTP API to interact with
the knowledge graph. Clean REST API ensures easy integration.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from knowledge_graph_service.application.services.graph_service import (
    GraphService,
    NodeNotFoundError,
    EdgeNotFoundError,
    DuplicateNodeError
)
from knowledge_graph_service.domain.entities.node import NodeType
from knowledge_graph_service.domain.entities.edge import EdgeType


router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


# ========================================
# REQUEST/RESPONSE MODELS
# ========================================

class CreateNodeRequest(BaseModel):
    """Request model for creating a node"""
    node_type: str = Field(..., description="Type of node (course, concept, skill, etc.)")
    entity_id: str = Field(..., description="UUID of the entity this node represents")
    label: str = Field(..., description="Display name for the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class NodeResponse(BaseModel):
    """Response model for a node"""
    id: str
    node_type: str
    entity_id: str
    label: str
    properties: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class CreateEdgeRequest(BaseModel):
    """Request model for creating an edge"""
    edge_type: str = Field(..., description="Type of relationship")
    source_node_id: str = Field(..., description="Source node UUID")
    target_node_id: str = Field(..., description="Target node UUID")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Relationship strength (0.0-1.0)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EdgeResponse(BaseModel):
    """Response model for an edge"""
    id: str
    edge_type: str
    source_node_id: str
    target_node_id: str
    weight: float
    properties: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class BulkImportRequest(BaseModel):
    """Request model for bulk graph import"""
    nodes: List[Dict[str, Any]] = Field(..., description="List of nodes to create")
    edges: List[Dict[str, Any]] = Field(..., description="List of edges to create")


class GraphStatisticsResponse(BaseModel):
    """Response model for graph statistics"""
    total_nodes: int
    node_counts: Dict[str, int]
    total_edges: int
    edge_counts: Dict[str, int]


class NeighborResponse(BaseModel):
    """Response model for neighbor query"""
    node_id: str
    node_type: str
    label: str
    relationship: str
    weight: float
    direction: str  # 'incoming' or 'outgoing'


# ========================================
# DEPENDENCY INJECTION
# ========================================

async def get_graph_service() -> GraphService:
    """
    Dependency injection for GraphService

    TODO: Initialize with actual database connection pool
    """
    from infrastructure.database import get_database_pool
    from data_access.graph_dao import GraphDAO

    pool = await get_database_pool()
    dao = GraphDAO(pool)
    return GraphService(dao)


# ========================================
# NODE ENDPOINTS
# ========================================

@router.post("/nodes", response_model=NodeResponse, status_code=201)
async def create_node(
    request: CreateNodeRequest,
    user_id: Optional[str] = None,
    service: GraphService = Depends(get_graph_service)
):
    """
    Create a new graph node

    BUSINESS USE CASE:
    When a course is created, add it to the knowledge graph
    """
    try:
        node = await service.create_node(
            node_type=NodeType(request.node_type),
            entity_id=UUID(request.entity_id),
            label=request.label,
            properties=request.properties,
            metadata=request.metadata,
            user_id=UUID(user_id) if user_id else None
        )

        return NodeResponse(
            id=str(node.id),
            node_type=node.node_type.value,
            entity_id=str(node.entity_id),
            label=node.label,
            properties=node.properties,
            metadata=node.metadata,
            created_at=node.created_at.isoformat(),
            updated_at=node.updated_at.isoformat()
        )

    except DuplicateNodeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    service: GraphService = Depends(get_graph_service)
):
    """
    Get node by ID
    """
    try:
        node = await service.get_node(UUID(node_id))

        return NodeResponse(
            id=str(node.id),
            node_type=node.node_type.value,
            entity_id=str(node.entity_id),
            label=node.label,
            properties=node.properties,
            metadata=node.metadata,
            created_at=node.created_at.isoformat(),
            updated_at=node.updated_at.isoformat()
        )

    except NodeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/nodes/entity/{entity_id}", response_model=NodeResponse)
async def get_node_by_entity(
    entity_id: str,
    node_type: str = Query(..., description="Node type"),
    service: GraphService = Depends(get_graph_service)
):
    """
    Get node by entity reference

    BUSINESS USE CASE:
    Find graph node for a specific course
    """
    node = await service.get_node_by_entity(
        UUID(entity_id),
        NodeType(node_type)
    )

    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"No {node_type} node found for entity {entity_id}"
        )

    return NodeResponse(
        id=str(node.id),
        node_type=node.node_type.value,
        entity_id=str(node.entity_id),
        label=node.label,
        properties=node.properties,
        metadata=node.metadata,
        created_at=node.created_at.isoformat(),
        updated_at=node.updated_at.isoformat()
    )


@router.delete("/nodes/{node_id}", status_code=204)
async def delete_node(
    node_id: str,
    service: GraphService = Depends(get_graph_service)
):
    """
    Delete node and all connected edges
    """
    deleted = await service.delete_node(UUID(node_id))

    if not deleted:
        raise HTTPException(status_code=404, detail="Node not found")


@router.get("/nodes/search", response_model=List[NodeResponse])
async def search_nodes(
    q: str = Query(..., description="Search query"),
    node_types: Optional[List[str]] = Query(None, description="Filter by node types"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    service: GraphService = Depends(get_graph_service)
):
    """
    Full-text search on nodes

    BUSINESS USE CASE:
    Search for courses or concepts by name
    """
    types = [NodeType(t) for t in node_types] if node_types else None
    nodes = await service.search_nodes(q, types, limit)

    return [
        NodeResponse(
            id=str(node.id),
            node_type=node.node_type.value,
            entity_id=str(node.entity_id),
            label=node.label,
            properties=node.properties,
            metadata=node.metadata,
            created_at=node.created_at.isoformat(),
            updated_at=node.updated_at.isoformat()
        )
        for node in nodes
    ]


# ========================================
# EDGE ENDPOINTS
# ========================================

@router.post("/edges", response_model=EdgeResponse, status_code=201)
async def create_edge(
    request: CreateEdgeRequest,
    user_id: Optional[str] = None,
    service: GraphService = Depends(get_graph_service)
):
    """
    Create a new graph edge (relationship)

    BUSINESS USE CASE:
    Define that "Course A is prerequisite for Course B"
    """
    try:
        edge = await service.create_edge(
            edge_type=EdgeType(request.edge_type),
            source_node_id=UUID(request.source_node_id),
            target_node_id=UUID(request.target_node_id),
            weight=request.weight,
            properties=request.properties,
            metadata=request.metadata,
            user_id=UUID(user_id) if user_id else None
        )

        return EdgeResponse(
            id=str(edge.id),
            edge_type=edge.edge_type.value,
            source_node_id=str(edge.source_node_id),
            target_node_id=str(edge.target_node_id),
            weight=float(edge.weight),
            properties=edge.properties,
            metadata=edge.metadata,
            created_at=edge.created_at.isoformat(),
            updated_at=edge.updated_at.isoformat()
        )

    except NodeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/edges/{edge_id}", response_model=EdgeResponse)
async def get_edge(
    edge_id: str,
    service: GraphService = Depends(get_graph_service)
):
    """
    Get edge by ID
    """
    try:
        edge = await service.get_edge(UUID(edge_id))

        return EdgeResponse(
            id=str(edge.id),
            edge_type=edge.edge_type.value,
            source_node_id=str(edge.source_node_id),
            target_node_id=str(edge.target_node_id),
            weight=float(edge.weight),
            properties=edge.properties,
            metadata=edge.metadata,
            created_at=edge.created_at.isoformat(),
            updated_at=edge.updated_at.isoformat()
        )

    except EdgeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/edges/{edge_id}", status_code=204)
async def delete_edge(
    edge_id: str,
    service: GraphService = Depends(get_graph_service)
):
    """
    Delete edge
    """
    deleted = await service.delete_edge(UUID(edge_id))

    if not deleted:
        raise HTTPException(status_code=404, detail="Edge not found")


# ========================================
# GRAPH QUERY ENDPOINTS
# ========================================

@router.get("/nodes/{node_id}/neighbors", response_model=List[NeighborResponse])
async def get_neighbors(
    node_id: str,
    edge_types: Optional[List[str]] = Query(None, description="Filter by edge types"),
    direction: str = Query("both", regex="^(outgoing|incoming|both)$"),
    service: GraphService = Depends(get_graph_service)
):
    """
    Get neighboring nodes

    BUSINESS USE CASE:
    Find all courses related to a specific course
    """
    neighbors = await service.get_neighbors(
        UUID(node_id),
        edge_types=edge_types,
        direction=direction
    )

    return [
        NeighborResponse(
            node_id=n['neighbor_id'],
            node_type=n['node_type'],
            label=n['label'],
            relationship=n['edge_type'],
            weight=n['weight'],
            direction=n['direction']
        )
        for n in neighbors
    ]


@router.get("/courses/{course_id}/related", response_model=List[Dict[str, Any]])
async def get_related_courses(
    course_id: str,
    relationship_types: Optional[List[str]] = Query(None, description="Relationship types"),
    limit: int = Query(10, ge=1, le=50),
    service: GraphService = Depends(get_graph_service)
):
    """
    Get courses related to a given course

    BUSINESS USE CASE:
    "Students who took this course also took..."
    """
    # Get course node
    course_node = await service.get_node_by_entity(
        UUID(course_id),
        NodeType.COURSE
    )

    if not course_node:
        raise HTTPException(status_code=404, detail="Course not found in graph")

    related = await service.get_related_courses(
        course_node.id,
        relationship_types=relationship_types,
        max_results=limit
    )

    return related


# ========================================
# BULK OPERATIONS
# ========================================

@router.post("/bulk-import")
async def bulk_import_graph(
    request: BulkImportRequest,
    user_id: Optional[str] = None,
    service: GraphService = Depends(get_graph_service)
):
    """
    Bulk import graph data

    BUSINESS USE CASE:
    Import entire curriculum graph from external system
    """
    summary = await service.bulk_import_graph(
        nodes=request.nodes,
        edges=request.edges,
        user_id=UUID(user_id) if user_id else None
    )

    return summary


@router.get("/statistics", response_model=GraphStatisticsResponse)
async def get_graph_statistics(
    service: GraphService = Depends(get_graph_service)
):
    """
    Get graph statistics

    BUSINESS VALUE:
    Provides insights into curriculum structure
    """
    stats = await service.get_graph_statistics()

    return GraphStatisticsResponse(
        total_nodes=stats['total_nodes'],
        node_counts=stats['node_counts'],
        total_edges=stats['total_edges'],
        edge_counts=stats['edge_counts']
    )
