"""
Knowledge Graph Data Access Object

BUSINESS REQUIREMENT:
Provide CRUD operations for nodes and edges in the knowledge graph

TECHNICAL IMPLEMENTATION:
- asyncpg for async database operations
- Transaction support
- Bulk operations
- Query optimization

WHY:
Separates data access from business logic for better testing and maintenance
"""

import asyncpg
import json
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from domain.entities.node import Node, NodeType
from domain.entities.edge import Edge, EdgeType


class GraphDAO:
    """
    Data Access Object for Knowledge Graph

    BUSINESS VALUE:
    Provides efficient database operations for graph data
    """

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    # ========================================
    # NODE OPERATIONS
    # ========================================

    async def create_node(self, node: Node, connection: Optional[asyncpg.Connection] = None) -> Node:
        """
        Create a new node in the graph

        Args:
            node: Node entity to create
            connection: Optional database connection (for transactions)

        Returns:
            Node: Created node with database-generated fields

        Raises:
            asyncpg.UniqueViolationError: If node already exists
        """
        query = """
            INSERT INTO knowledge_graph_nodes (
                id, node_type, entity_id, label, properties, metadata,
                created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING created_at, updated_at
        """

        if connection:
            # Reuse existing connection (already in transaction)
            row = await connection.fetchrow(
                query,
                node.id,
                node.node_type.value,
                node.entity_id,
                node.label,
                json.dumps(node.properties),
                json.dumps(node.metadata),
                node.created_at,
                node.updated_at,
                node.created_by,
                node.updated_by
            )
        else:
            # Acquire new connection from pool
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    row = await conn.fetchrow(
                        query,
                        node.id,
                        node.node_type.value,
                        node.entity_id,
                        node.label,
                        json.dumps(node.properties),
                        json.dumps(node.metadata),
                        node.created_at,
                        node.updated_at,
                        node.created_by,
                        node.updated_by
                    )

        node.created_at = row['created_at']
        node.updated_at = row['updated_at']

        return node

    async def get_node_by_id(self, node_id: UUID) -> Optional[Node]:
        """
        Get node by ID

        Args:
            node_id: Node UUID

        Returns:
            Node or None if not found
        """
        query = """
            SELECT id, node_type, entity_id, label, properties, metadata,
                   created_at, updated_at, created_by, updated_by
            FROM knowledge_graph_nodes
            WHERE id = $1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, node_id)

            if not row:
                return None

            return self._row_to_node(row)

    async def get_node_by_entity(self, entity_id: UUID, node_type: NodeType) -> Optional[Node]:
        """
        Get node by entity reference

        BUSINESS USE CASE:
        Find node representing a specific course/concept/skill

        Args:
            entity_id: Entity UUID
            node_type: Type of node

        Returns:
            Node or None if not found
        """
        query = """
            SELECT id, node_type, entity_id, label, properties, metadata,
                   created_at, updated_at, created_by, updated_by
            FROM knowledge_graph_nodes
            WHERE entity_id = $1 AND node_type = $2
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, entity_id, node_type.value)

            if not row:
                return None

            return self._row_to_node(row)

    async def list_nodes_by_type(
        self,
        node_type: NodeType,
        limit: int = 100,
        offset: int = 0
    ) -> List[Node]:
        """
        List nodes by type

        Args:
            node_type: Type of nodes to retrieve
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of nodes
        """
        query = """
            SELECT id, node_type, entity_id, label, properties, metadata,
                   created_at, updated_at, created_by, updated_by
            FROM knowledge_graph_nodes
            WHERE node_type = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, node_type.value, limit, offset)
            return [self._row_to_node(row) for row in rows]

    async def update_node(self, node: Node) -> Node:
        """
        Update existing node

        Args:
            node: Node with updated data

        Returns:
            Updated node

        Raises:
            ValueError: If node doesn't exist
        """
        query = """
            UPDATE knowledge_graph_nodes
            SET label = $2,
                properties = $3,
                metadata = $4,
                updated_at = $5,
                updated_by = $6
            WHERE id = $1
            RETURNING updated_at
        """

        node.updated_at = datetime.now()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    query,
                    node.id,
                    node.label,
                    json.dumps(node.properties),
                    json.dumps(node.metadata),
                    node.updated_at,
                    node.updated_by
                )

                if not row:
                    raise ValueError(f"Node {node.id} not found")

                node.updated_at = row['updated_at']
                return node

    async def delete_node(self, node_id: UUID) -> bool:
        """
        Delete node (and all connected edges via CASCADE)

        Args:
            node_id: Node UUID

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM knowledge_graph_nodes WHERE id = $1"

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.execute(query, node_id)
                return result != 'DELETE 0'

    async def search_nodes(
        self,
        search_query: str,
        node_types: Optional[List[NodeType]] = None,
        limit: int = 20
    ) -> List[Node]:
        """
        Full-text search on nodes

        BUSINESS USE CASE:
        Find courses/concepts by name or description

        Args:
            search_query: Search text
            node_types: Filter by node types
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        if node_types:
            type_filter = "AND node_type = ANY($2)"
            params = [search_query, [t.value for t in node_types], limit]
        else:
            type_filter = ""
            params = [search_query, limit]

        query = f"""
            SELECT id, node_type, entity_id, label, properties, metadata,
                   created_at, updated_at, created_by, updated_by
            FROM knowledge_graph_nodes
            WHERE to_tsvector('english', label) @@ plainto_tsquery('english', $1)
            {type_filter}
            ORDER BY ts_rank(to_tsvector('english', label), plainto_tsquery('english', $1)) DESC
            LIMIT ${len(params)}
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_node(row) for row in rows]

    # ========================================
    # EDGE OPERATIONS
    # ========================================

    async def create_edge(self, edge: Edge, connection: Optional[asyncpg.Connection] = None) -> Edge:
        """
        Create a new edge in the graph

        Args:
            edge: Edge entity to create
            connection: Optional database connection (for transactions)

        Returns:
            Edge: Created edge with database-generated fields

        Raises:
            asyncpg.UniqueViolationError: If edge already exists
            asyncpg.ForeignKeyViolationError: If nodes don't exist
        """
        query = """
            INSERT INTO knowledge_graph_edges (
                id, edge_type, source_node_id, target_node_id, weight,
                properties, metadata, created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING created_at, updated_at
        """

        if connection:
            # Reuse existing connection (already in transaction)
            row = await connection.fetchrow(
                query,
                edge.id,
                edge.edge_type.value,
                edge.source_node_id,
                edge.target_node_id,
                float(edge.weight),
                json.dumps(edge.properties),
                json.dumps(edge.metadata),
                edge.created_at,
                edge.updated_at,
                edge.created_by,
                edge.updated_by
            )
        else:
            # Acquire new connection from pool
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    row = await conn.fetchrow(
                        query,
                        edge.id,
                        edge.edge_type.value,
                        edge.source_node_id,
                        edge.target_node_id,
                        float(edge.weight),
                        json.dumps(edge.properties),
                        json.dumps(edge.metadata),
                        edge.created_at,
                        edge.updated_at,
                        edge.created_by,
                        edge.updated_by
                    )

        edge.created_at = row['created_at']
        edge.updated_at = row['updated_at']

        return edge

    async def get_edge_by_id(self, edge_id: UUID) -> Optional[Edge]:
        """Get edge by ID"""
        query = """
            SELECT id, edge_type, source_node_id, target_node_id, weight,
                   properties, metadata, created_at, updated_at, created_by, updated_by
            FROM knowledge_graph_edges
            WHERE id = $1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, edge_id)

            if not row:
                return None

            return self._row_to_edge(row)

    async def get_edges_from_node(
        self,
        node_id: UUID,
        edge_types: Optional[List[EdgeType]] = None
    ) -> List[Edge]:
        """
        Get all outgoing edges from a node

        BUSINESS USE CASE:
        Find all courses that have a specific course as prerequisite

        Args:
            node_id: Source node ID
            edge_types: Filter by edge types

        Returns:
            List of edges
        """
        if edge_types:
            type_filter = "AND edge_type = ANY($2)"
            params = [node_id, [t.value for t in edge_types]]
        else:
            type_filter = ""
            params = [node_id]

        query = f"""
            SELECT id, edge_type, source_node_id, target_node_id, weight,
                   properties, metadata, created_at, updated_at, created_by, updated_by
            FROM knowledge_graph_edges
            WHERE source_node_id = $1
            {type_filter}
            ORDER BY weight DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_edge(row) for row in rows]

    async def get_edges_to_node(
        self,
        node_id: UUID,
        edge_types: Optional[List[EdgeType]] = None
    ) -> List[Edge]:
        """
        Get all incoming edges to a node

        BUSINESS USE CASE:
        Find all prerequisites for a course

        Args:
            node_id: Target node ID
            edge_types: Filter by edge types

        Returns:
            List of edges
        """
        if edge_types:
            type_filter = "AND edge_type = ANY($2)"
            params = [node_id, [t.value for t in edge_types]]
        else:
            type_filter = ""
            params = [node_id]

        query = f"""
            SELECT id, edge_type, source_node_id, target_node_id, weight,
                   properties, metadata, created_at, updated_at, created_by, updated_by
            FROM knowledge_graph_edges
            WHERE target_node_id = $1
            {type_filter}
            ORDER BY weight DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_edge(row) for row in rows]

    async def delete_edge(self, edge_id: UUID) -> bool:
        """Delete edge"""
        query = "DELETE FROM knowledge_graph_edges WHERE id = $1"

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.execute(query, edge_id)
                return result != 'DELETE 0'

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
        Get neighbors of a node using database function

        Args:
            node_id: Node UUID
            edge_types: Filter by edge types
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            List of neighbor nodes with relationship info
        """
        edge_types_array = edge_types if edge_types else None

        query = """
            SELECT * FROM kg_get_neighbors($1, $2::VARCHAR[], $3)
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, node_id, edge_types_array, direction)
            return [dict(row) for row in rows]

    async def find_shortest_path(
        self,
        start_node_id: UUID,
        end_node_id: UUID,
        max_depth: int = 10
    ) -> Optional[List[UUID]]:
        """
        Find shortest path using database function

        Args:
            start_node_id: Starting node
            end_node_id: Target node
            max_depth: Maximum path length

        Returns:
            List of node UUIDs in path, or None if no path exists
        """
        query = """
            SELECT kg_find_shortest_path($1, $2, $3) AS path
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, start_node_id, end_node_id, max_depth)
            return row['path'] if row and row['path'] else None

    async def get_all_prerequisites(
        self,
        course_node_id: UUID,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get all prerequisites using database function

        Args:
            course_node_id: Course node UUID
            max_depth: Maximum prerequisite chain depth

        Returns:
            List of prerequisite nodes with depth info
        """
        query = """
            SELECT * FROM kg_get_all_prerequisites($1, $2)
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, course_node_id, max_depth)
            return [dict(row) for row in rows]

    # ========================================
    # BULK OPERATIONS
    # ========================================

    async def bulk_create_nodes(self, nodes: List[Node]) -> List[Node]:
        """
        Bulk create nodes

        BUSINESS USE CASE:
        Import entire curriculum graph

        Args:
            nodes: List of nodes to create

        Returns:
            List of created nodes
        """
        if not nodes:
            return []

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                created = []
                for node in nodes:
                    created_node = await self.create_node(node, connection=conn)
                    created.append(created_node)

                return created

    async def bulk_create_edges(self, edges: List[Edge]) -> List[Edge]:
        """
        Bulk create edges

        Args:
            edges: List of edges to create

        Returns:
            List of created edges
        """
        if not edges:
            return []

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                created = []
                for edge in edges:
                    created_edge = await self.create_edge(edge, connection=conn)
                    created.append(created_edge)

                return created

    # ========================================
    # HELPER METHODS
    # ========================================

    def _row_to_node(self, row: asyncpg.Record) -> Node:
        """Convert database row to Node entity"""
        # Parse JSON fields if they're strings
        properties = row['properties'] if isinstance(row['properties'], dict) else json.loads(row['properties'])
        metadata = row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])

        return Node.from_dict({
            'id': str(row['id']),
            'node_type': row['node_type'],
            'entity_id': str(row['entity_id']),
            'label': row['label'],
            'properties': properties,
            'metadata': metadata,
            'created_at': row['created_at'].isoformat(),
            'updated_at': row['updated_at'].isoformat(),
            'created_by': str(row['created_by']) if row['created_by'] else None,
            'updated_by': str(row['updated_by']) if row['updated_by'] else None
        })

    def _row_to_edge(self, row: asyncpg.Record) -> Edge:
        """Convert database row to Edge entity"""
        # Parse JSON fields if they're strings
        properties = row['properties'] if isinstance(row['properties'], dict) else json.loads(row['properties'])
        metadata = row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])

        return Edge.from_dict({
            'id': str(row['id']),
            'edge_type': row['edge_type'],
            'source_node_id': str(row['source_node_id']),
            'target_node_id': str(row['target_node_id']),
            'weight': float(row['weight']),
            'properties': properties,
            'metadata': metadata,
            'created_at': row['created_at'].isoformat(),
            'updated_at': row['updated_at'].isoformat(),
            'created_by': str(row['created_by']) if row['created_by'] else None,
            'updated_by': str(row['updated_by']) if row['updated_by'] else None
        })
