"""
Graph Service - Core Knowledge Graph Operations

BUSINESS REQUIREMENT:
Provide high-level graph operations for course relationships,
prerequisites, and learning path management.

BUSINESS VALUE:
- Enables intelligent course discovery
- Manages prerequisite relationships
- Supports curriculum visualization
- Provides graph-based recommendations

TECHNICAL IMPLEMENTATION:
- Orchestrates DAO layer operations
- Integrates with path finding algorithms
- Handles business logic validation
- Manages transactions

WHY:
Separates business logic from data access for better maintainability
and testability. Provides clean API for controller layer.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from knowledge_graph_service.domain.entities.node import Node, NodeType, create_course_node
from knowledge_graph_service.domain.entities.edge import Edge, EdgeType, create_prerequisite_edge
from data_access.graph_dao import GraphDAO
from algorithms.path_finding import PathFinder, build_graph_structure

logger = logging.getLogger(__name__)


class GraphServiceError(Exception):
    """Base exception for graph service errors"""
    pass


class NodeNotFoundError(GraphServiceError):
    """Raised when a node is not found"""
    pass


class EdgeNotFoundError(GraphServiceError):
    """Raised when an edge is not found"""
    pass


class DuplicateNodeError(GraphServiceError):
    """Raised when attempting to create duplicate node"""
    pass


class GraphService:
    """
    Core Knowledge Graph Service

    BUSINESS VALUE:
    Provides unified interface for graph operations
    """

    def __init__(self, dao: GraphDAO):
        """
        Initialize graph service

        Args:
            dao: GraphDAO instance for data access
        """
        self.dao = dao

    # ========================================
    # NODE OPERATIONS
    # ========================================

    async def create_node(
        self,
        node_type: NodeType,
        entity_id: UUID,
        label: str,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> Node:
        """
        Create a new graph node

        BUSINESS USE CASE:
        When a course/concept/skill is created, add it to the knowledge graph

        Args:
            node_type: Type of node (course, concept, etc.)
            entity_id: Reference to the actual entity (e.g., course UUID)
            label: Display name for the node
            properties: Node-specific properties
            metadata: Additional metadata
            user_id: User creating the node

        Returns:
            Created node

        Raises:
            DuplicateNodeError: If node for this entity already exists
        """
        # Check if node already exists for this entity
        existing = await self.dao.get_node_by_entity(entity_id, node_type)
        if existing:
            raise DuplicateNodeError(
                f"Node already exists for {node_type.value} {entity_id}"
            )

        # Create node entity
        node = Node(
            node_type=node_type,
            entity_id=entity_id,
            label=label,
            properties=properties or {},
            metadata=metadata or {},
            created_by=user_id,
            updated_by=user_id
        )

        # Persist to database
        created_node = await self.dao.create_node(node)

        logger.info(
            f"Created graph node: {node_type.value} '{label}' (id={created_node.id})"
        )

        return created_node

    async def get_node(self, node_id: UUID) -> Node:
        """
        Get node by ID

        Args:
            node_id: Node UUID

        Returns:
            Node

        Raises:
            NodeNotFoundError: If node doesn't exist
        """
        node = await self.dao.get_node_by_id(node_id)
        if not node:
            raise NodeNotFoundError(f"Node {node_id} not found")
        return node

    async def get_node_by_entity(
        self,
        entity_id: UUID,
        node_type: NodeType
    ) -> Optional[Node]:
        """
        Get node by entity reference

        BUSINESS USE CASE:
        Find the graph node representing a specific course

        Args:
            entity_id: Entity UUID (e.g., course UUID)
            node_type: Type of node

        Returns:
            Node or None if not found
        """
        return await self.dao.get_node_by_entity(entity_id, node_type)

    async def update_node(
        self,
        node_id: UUID,
        label: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> Node:
        """
        Update existing node

        Args:
            node_id: Node UUID
            label: New label (optional)
            properties: Updated properties (optional)
            metadata: Updated metadata (optional)
            user_id: User updating the node

        Returns:
            Updated node

        Raises:
            NodeNotFoundError: If node doesn't exist
        """
        node = await self.get_node(node_id)

        if label:
            node.label = label
        if properties is not None:
            node.properties = properties
        if metadata is not None:
            node.metadata = metadata
        if user_id:
            node.updated_by = user_id

        updated_node = await self.dao.update_node(node)

        logger.info(f"Updated graph node: {node_id}")

        return updated_node

    async def delete_node(self, node_id: UUID) -> bool:
        """
        Delete node and all connected edges

        BUSINESS LOGIC:
        Deleting a node removes all its relationships

        Args:
            node_id: Node UUID

        Returns:
            True if deleted, False if not found
        """
        deleted = await self.dao.delete_node(node_id)

        if deleted:
            logger.info(f"Deleted graph node: {node_id}")

        return deleted

    async def search_nodes(
        self,
        query: str,
        node_types: Optional[List[NodeType]] = None,
        limit: int = 20
    ) -> List[Node]:
        """
        Full-text search on nodes

        BUSINESS USE CASE:
        Search for courses/concepts by name

        Args:
            query: Search text
            node_types: Filter by node types
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        return await self.dao.search_nodes(query, node_types, limit)

    # ========================================
    # EDGE OPERATIONS
    # ========================================

    async def create_edge(
        self,
        edge_type: EdgeType,
        source_node_id: UUID,
        target_node_id: UUID,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> Edge:
        """
        Create a new graph edge (relationship)

        BUSINESS USE CASE:
        Define relationships like "Course A is prerequisite for Course B"

        Args:
            edge_type: Type of relationship
            source_node_id: Source node UUID
            target_node_id: Target node UUID
            weight: Relationship strength (0.0-1.0)
            properties: Edge-specific properties
            metadata: Additional metadata
            user_id: User creating the edge

        Returns:
            Created edge

        Raises:
            NodeNotFoundError: If source or target node doesn't exist
        """
        # Validate nodes exist
        await self.get_node(source_node_id)
        await self.get_node(target_node_id)

        # Create edge entity
        edge = Edge(
            edge_type=edge_type,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            weight=weight,
            properties=properties or {},
            metadata=metadata or {},
            created_by=user_id,
            updated_by=user_id
        )

        # Persist to database
        created_edge = await self.dao.create_edge(edge)

        logger.info(
            f"Created graph edge: {edge_type.value} "
            f"from {source_node_id} to {target_node_id}"
        )

        return created_edge

    async def get_edge(self, edge_id: UUID) -> Edge:
        """
        Get edge by ID

        Args:
            edge_id: Edge UUID

        Returns:
            Edge

        Raises:
            EdgeNotFoundError: If edge doesn't exist
        """
        edge = await self.dao.get_edge_by_id(edge_id)
        if not edge:
            raise EdgeNotFoundError(f"Edge {edge_id} not found")
        return edge

    async def delete_edge(self, edge_id: UUID) -> bool:
        """
        Delete edge

        Args:
            edge_id: Edge UUID

        Returns:
            True if deleted, False if not found
        """
        deleted = await self.dao.delete_edge(edge_id)

        if deleted:
            logger.info(f"Deleted graph edge: {edge_id}")

        return deleted

    # ========================================
    # GRAPH QUERIES
    # ========================================

    async def get_neighbors(
        self,
        node_id: UUID,
        edge_types: Optional[List[str]] = None,
        direction: str = 'both'
    ) -> List[Dict[str, Any]]:
        """
        Get neighboring nodes

        BUSINESS USE CASE:
        Find all courses related to a specific course

        Args:
            node_id: Node UUID
            edge_types: Filter by edge types
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            List of neighbor nodes with relationship info
        """
        return await self.dao.get_neighbors(node_id, edge_types, direction)

    async def get_related_courses(
        self,
        course_node_id: UUID,
        relationship_types: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get courses related to a given course

        BUSINESS USE CASE:
        "Students who took this course also took..."

        Args:
            course_node_id: Course node UUID
            relationship_types: Types of relationships to consider
            max_results: Maximum number of results

        Returns:
            List of related courses with relationship info
        """
        neighbors = await self.get_neighbors(
            course_node_id,
            edge_types=relationship_types,
            direction='both'
        )

        # Filter to only course nodes
        courses = [
            n for n in neighbors
            if n.get('node_type') == 'course'
        ]

        return courses[:max_results]

    # ========================================
    # BULK OPERATIONS
    # ========================================

    async def bulk_import_graph(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Bulk import graph data

        BUSINESS USE CASE:
        Import entire curriculum graph from external system

        Args:
            nodes: List of node data dictionaries
            edges: List of edge data dictionaries
            user_id: User performing the import

        Returns:
            Import summary with counts
        """
        # Convert to entities
        node_entities = []
        for node_data in nodes:
            node = Node(
                node_type=NodeType(node_data['node_type']),
                entity_id=UUID(node_data['entity_id']),
                label=node_data['label'],
                properties=node_data.get('properties', {}),
                metadata=node_data.get('metadata', {}),
                created_by=user_id,
                updated_by=user_id
            )
            node_entities.append(node)

        # Create nodes
        created_nodes = await self.dao.bulk_create_nodes(node_entities)

        # Build node ID mapping (entity_id -> node_id)
        node_id_map = {
            str(node.entity_id): node.id
            for node in created_nodes
        }

        # Convert edges to entities
        edge_entities = []
        for edge_data in edges:
            source_id = node_id_map.get(edge_data['source_entity_id'])
            target_id = node_id_map.get(edge_data['target_entity_id'])

            if not source_id or not target_id:
                logger.warning(
                    f"Skipping edge: missing node for "
                    f"{edge_data['source_entity_id']} -> {edge_data['target_entity_id']}"
                )
                continue

            edge = Edge(
                edge_type=EdgeType(edge_data['edge_type']),
                source_node_id=source_id,
                target_node_id=target_id,
                weight=edge_data.get('weight', 1.0),
                properties=edge_data.get('properties', {}),
                metadata=edge_data.get('metadata', {}),
                created_by=user_id,
                updated_by=user_id
            )
            edge_entities.append(edge)

        # Create edges
        created_edges = await self.dao.bulk_create_edges(edge_entities)

        summary = {
            'nodes_created': len(created_nodes),
            'edges_created': len(created_edges),
            'nodes_skipped': len(nodes) - len(created_nodes),
            'edges_skipped': len(edges) - len(created_edges)
        }

        logger.info(
            f"Bulk import completed: {summary['nodes_created']} nodes, "
            f"{summary['edges_created']} edges"
        )

        return summary

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get graph statistics

        BUSINESS VALUE:
        Provides insights into curriculum structure

        Returns:
            Statistics including node counts, edge counts, etc.
        """
        # Get node counts by type
        node_counts = {}
        for node_type in NodeType:
            nodes = await self.dao.list_nodes_by_type(node_type, limit=100000)
            node_counts[node_type.value] = len(nodes)

        # Get all edges to count by type
        edge_counts = {}
        # Note: Would need to add a method to DAO to get all edges efficiently

        return {
            'total_nodes': sum(node_counts.values()),
            'node_counts': node_counts,
            'total_edges': sum(edge_counts.values()) if edge_counts else 0,
            'edge_counts': edge_counts
        }
