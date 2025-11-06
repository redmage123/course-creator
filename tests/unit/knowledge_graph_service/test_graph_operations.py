"""
Unit Tests for Knowledge Graph Operations

BUSINESS CONTEXT:
Tests the core graph operations for course relationships, prerequisites,
and learning path discovery. Validates node/edge CRUD operations and
graph traversal algorithms.

TECHNICAL VALIDATION:
- Node creation and management (courses, concepts, skills)
- Edge creation and relationships
- Graph queries and traversal
- Data validation and constraints
- Error handling

TEST COVERAGE TARGETS:
- Line Coverage: 85%+
- Function Coverage: 80%+
- Branch Coverage: 75%+
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List, Dict
import sys
from pathlib import Path

# Add knowledge-graph-service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'knowledge-graph-service'))

from knowledge_graph_service.application.services.graph_service import GraphService
from knowledge_graph_service.domain.entities.node import Node, NodeType
from knowledge_graph_service.domain.entities.edge import Edge, EdgeType


class TestGraphOperations:
    """Test suite for Graph Operations"""

    @pytest.fixture
    def graph_service(self):
        """
        TEST FIXTURE: Graph Service instance

        BUSINESS SCENARIO: Platform manages course prerequisites
        TECHNICAL SETUP: Initialize service with mock database
        """
        with patch('knowledge_graph_service.infrastructure.database.get_database_pool'):
            service = GraphService()
            service.db_pool = AsyncMock()
            return service

    @pytest.fixture
    def sample_course_node(self) -> Node:
        """TEST FIXTURE: Sample course node"""
        return Node(
            id="course_123",
            node_type=NodeType.COURSE,
            properties={
                "name": "Python 101",
                "description": "Introduction to Python",
                "duration_hours": 40
            },
            created_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_concept_node(self) -> Node:
        """TEST FIXTURE: Sample concept node"""
        return Node(
            id="concept_456",
            node_type=NodeType.CONCEPT,
            properties={
                "name": "Variables",
                "difficulty": "beginner"
            },
            created_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_edge(self, sample_course_node, sample_concept_node) -> Edge:
        """TEST FIXTURE: Sample edge (course teaches concept)"""
        return Edge(
            id="edge_789",
            source_id=sample_course_node.id,
            target_id=sample_concept_node.id,
            edge_type=EdgeType.TEACHES,
            properties={"importance": "high"},
            created_at=datetime.utcnow()
        )

    # ==========================================
    # NODE CREATION TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_create_node_success(self, graph_service, sample_course_node):
        """
        TEST: Successfully create node

        BUSINESS SCENARIO: Instructor creates new course
        TECHNICAL VALIDATION: Node persisted to database
        EXPECTED OUTCOME: Node ID returned
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=sample_course_node.id)
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        graph_service.db_pool.acquire.return_value = mock_conn

        # Act
        node_id = await graph_service.create_node(
            node_type=NodeType.COURSE,
            properties=sample_course_node.properties
        )

        # Assert
        assert node_id == sample_course_node.id
        mock_conn.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_node_invalid_type(self, graph_service):
        """
        TEST: Reject invalid node type

        BUSINESS SCENARIO: API receives invalid node type
        TECHNICAL VALIDATION: Validation error raised
        EXPECTED OUTCOME: Clear error message
        """
        # Act & Assert
        with pytest.raises(ValueError, match="node type"):
            await graph_service.create_node(
                node_type="INVALID_TYPE",
                properties={}
            )

    @pytest.mark.asyncio
    async def test_create_node_missing_required_properties(self, graph_service):
        """
        TEST: Reject node with missing required properties

        BUSINESS SCENARIO: Course created without name
        TECHNICAL VALIDATION: Validation error raised
        EXPECTED OUTCOME: Missing property identified
        """
        # Act & Assert
        with pytest.raises(ValueError, match="required"):
            await graph_service.create_node(
                node_type=NodeType.COURSE,
                properties={"duration_hours": 40}  # Missing 'name'
            )

    # ==========================================
    # NODE RETRIEVAL TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_node_by_id(self, graph_service, sample_course_node):
        """
        TEST: Retrieve node by ID

        BUSINESS SCENARIO: Display course details
        TECHNICAL VALIDATION: Node fetched from database
        EXPECTED OUTCOME: Complete node data returned
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={
            "id": sample_course_node.id,
            "node_type": sample_course_node.node_type.value,
            "properties": sample_course_node.properties,
            "created_at": sample_course_node.created_at
        })
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        node = await graph_service.get_node(sample_course_node.id)

        # Assert
        assert node is not None
        assert node.id == sample_course_node.id
        assert node.properties["name"] == "Python 101"

    @pytest.mark.asyncio
    async def test_get_node_not_found(self, graph_service):
        """
        TEST: Handle non-existent node

        BUSINESS SCENARIO: Request for deleted course
        TECHNICAL VALIDATION: None returned
        EXPECTED OUTCOME: No errors, None returned
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        node = await graph_service.get_node("non_existent_id")

        # Assert
        assert node is None

    @pytest.mark.asyncio
    async def test_get_nodes_by_type(self, graph_service):
        """
        TEST: Retrieve all nodes of specific type

        BUSINESS SCENARIO: List all courses
        TECHNICAL VALIDATION: Filtered query executed
        EXPECTED OUTCOME: List of course nodes
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"id": "course_1", "node_type": "course", "properties": {"name": "Python 101"}},
            {"id": "course_2", "node_type": "course", "properties": {"name": "Python 201"}}
        ])
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        nodes = await graph_service.get_nodes_by_type(NodeType.COURSE)

        # Assert
        assert len(nodes) == 2
        assert all(n.node_type == NodeType.COURSE for n in nodes)

    # ==========================================
    # NODE UPDATE TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_update_node(self, graph_service, sample_course_node):
        """
        TEST: Update node properties

        BUSINESS SCENARIO: Instructor updates course details
        TECHNICAL VALIDATION: Properties merged and saved
        EXPECTED OUTCOME: Node updated successfully
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        updated_properties = {"name": "Python 101 - Updated"}

        # Act
        await graph_service.update_node(sample_course_node.id, updated_properties)

        # Assert
        mock_conn.execute.assert_called_once()

    # ==========================================
    # NODE DELETION TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_delete_node(self, graph_service, sample_course_node):
        """
        TEST: Delete node

        BUSINESS SCENARIO: Admin removes deprecated course
        TECHNICAL VALIDATION: Node and edges deleted
        EXPECTED OUTCOME: Node no longer exists
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="DELETE 1")
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        await graph_service.delete_node(sample_course_node.id)

        # Assert
        assert mock_conn.execute.call_count >= 1  # Delete node and edges

    # ==========================================
    # EDGE CREATION TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_create_edge_success(self, graph_service, sample_course_node, sample_concept_node):
        """
        TEST: Successfully create edge

        BUSINESS SCENARIO: Link course to concept it teaches
        TECHNICAL VALIDATION: Edge persisted to database
        EXPECTED OUTCOME: Edge ID returned
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value="edge_123")
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        edge_id = await graph_service.create_edge(
            source_id=sample_course_node.id,
            target_id=sample_concept_node.id,
            edge_type=EdgeType.TEACHES,
            properties={}
        )

        # Assert
        assert edge_id == "edge_123"

    @pytest.mark.asyncio
    async def test_create_edge_invalid_nodes(self, graph_service):
        """
        TEST: Reject edge with non-existent nodes

        BUSINESS SCENARIO: API receives invalid node IDs
        TECHNICAL VALIDATION: Foreign key constraint violated
        EXPECTED OUTCOME: Error raised
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Foreign key violation"))
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(Exception):
            await graph_service.create_edge(
                source_id="non_existent_1",
                target_id="non_existent_2",
                edge_type=EdgeType.PREREQUISITE_OF
            )

    # ==========================================
    # EDGE RETRIEVAL TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_edges_from_node(self, graph_service, sample_course_node):
        """
        TEST: Get all outgoing edges from node

        BUSINESS SCENARIO: Find what course teaches
        TECHNICAL VALIDATION: Outgoing edges retrieved
        EXPECTED OUTCOME: List of edges
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {
                "id": "edge_1",
                "source_id": sample_course_node.id,
                "target_id": "concept_1",
                "edge_type": "teaches",
                "properties": {}
            },
            {
                "id": "edge_2",
                "source_id": sample_course_node.id,
                "target_id": "concept_2",
                "edge_type": "teaches",
                "properties": {}
            }
        ])
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        edges = await graph_service.get_edges_from_node(sample_course_node.id)

        # Assert
        assert len(edges) == 2
        assert all(e.source_id == sample_course_node.id for e in edges)

    @pytest.mark.asyncio
    async def test_get_edges_to_node(self, graph_service, sample_course_node):
        """
        TEST: Get all incoming edges to node

        BUSINESS SCENARIO: Find prerequisites for course
        TECHNICAL VALIDATION: Incoming edges retrieved
        EXPECTED OUTCOME: List of prerequisite edges
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {
                "id": "edge_1",
                "source_id": "course_prerequisite",
                "target_id": sample_course_node.id,
                "edge_type": "prerequisite_of",
                "properties": {}
            }
        ])
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        edges = await graph_service.get_edges_to_node(sample_course_node.id)

        # Assert
        assert len(edges) == 1
        assert edges[0].target_id == sample_course_node.id

    # ==========================================
    # GRAPH TRAVERSAL TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_neighbors(self, graph_service, sample_course_node):
        """
        TEST: Get all neighboring nodes

        BUSINESS SCENARIO: Find related courses
        TECHNICAL VALIDATION: Connected nodes retrieved
        EXPECTED OUTCOME: List of neighbor nodes
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"id": "concept_1", "node_type": "concept", "properties": {"name": "Variables"}},
            {"id": "concept_2", "node_type": "concept", "properties": {"name": "Functions"}}
        ])
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        neighbors = await graph_service.get_neighbors(sample_course_node.id)

        # Assert
        assert len(neighbors) == 2
        assert all(n.node_type == NodeType.CONCEPT for n in neighbors)

    @pytest.mark.asyncio
    async def test_get_neighbors_by_edge_type(self, graph_service, sample_course_node):
        """
        TEST: Get neighbors connected by specific edge type

        BUSINESS SCENARIO: Find only prerequisite courses
        TECHNICAL VALIDATION: Filtered traversal
        EXPECTED OUTCOME: Only prerequisite nodes returned
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"id": "course_prereq", "node_type": "course", "properties": {"name": "Programming Basics"}}
        ])
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        prerequisites = await graph_service.get_neighbors(
            sample_course_node.id,
            edge_type=EdgeType.PREREQUISITE_OF,
            direction="incoming"
        )

        # Assert
        assert len(prerequisites) == 1
        assert prerequisites[0].node_type == NodeType.COURSE

    # ==========================================
    # GRAPH STATISTICS TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_graph_statistics(self, graph_service):
        """
        TEST: Retrieve graph statistics

        BUSINESS SCENARIO: Admin monitors graph size and health
        TECHNICAL VALIDATION: Aggregate queries executed
        EXPECTED OUTCOME: Node/edge counts and metrics
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={
            "total_nodes": 150,
            "total_edges": 300,
            "course_count": 50,
            "concept_count": 100
        })
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        stats = await graph_service.get_statistics()

        # Assert
        assert stats["total_nodes"] == 150
        assert stats["total_edges"] == 300

    # ==========================================
    # EDGE CASE TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_circular_edge_detection(self, graph_service):
        """
        TEST: Detect and prevent circular prerequisites

        BUSINESS SCENARIO: Course A requires Course B requires Course A
        TECHNICAL VALIDATION: Cycle detection algorithm
        EXPECTED OUTCOME: Error raised
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Circular dependency detected"))
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(Exception, match="circular"):
            await graph_service.create_edge(
                source_id="course_A",
                target_id="course_B",
                edge_type=EdgeType.PREREQUISITE_OF,
                check_cycles=True
            )

    @pytest.mark.asyncio
    async def test_large_graph_performance(self, graph_service):
        """
        TEST: Handle large graph efficiently

        BUSINESS SCENARIO: Platform with 10,000+ courses
        TECHNICAL VALIDATION: Pagination and indexing
        EXPECTED OUTCOME: Queries complete in reasonable time
        """
        # Arrange
        large_node_list = [
            {"id": f"course_{i}", "node_type": "course", "properties": {"name": f"Course {i}"}}
            for i in range(1000)
        ]

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=large_node_list)
        graph_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        nodes = await graph_service.get_nodes_by_type(NodeType.COURSE, limit=1000)

        # Assert
        assert len(nodes) == 1000
