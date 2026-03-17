"""
End-to-End Tests for Knowledge Graph Service

Tests the complete knowledge graph system including:
- Database operations
- Graph algorithms
- Prerequisites checking
- Learning path generation
"""

import pytest
import pytest_asyncio
import asyncio
import asyncpg
from uuid import uuid4, UUID
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/knowledge-graph-service'))

from knowledge_graph_service.domain.entities.node import Node, NodeType, create_course_node
from knowledge_graph_service.domain.entities.edge import Edge, EdgeType, create_prerequisite_edge
from data_access.graph_dao import GraphDAO
from knowledge_graph_service.application.services.graph_service import GraphService
from knowledge_graph_service.application.services.path_finding_service import PathFindingService
from knowledge_graph_service.application.services.prerequisite_service import PrerequisiteService


@pytest_asyncio.fixture(scope="function")
async def db_pool():
    """Create database connection pool for tests"""
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres_password',
        database='course_creator',
        min_size=1,
        max_size=5
    )
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def dao(db_pool):
    """Create GraphDAO instance"""
    return GraphDAO(db_pool)


@pytest_asyncio.fixture
async def graph_service(dao):
    """Create GraphService instance"""
    return GraphService(dao)


@pytest_asyncio.fixture
async def path_service(dao):
    """Create PathFindingService instance"""
    return PathFindingService(dao)


@pytest_asyncio.fixture
async def prereq_service(dao):
    """Create PrerequisiteService instance"""
    return PrerequisiteService(dao)


@pytest_asyncio.fixture
async def cleanup_test_nodes(db_pool):
    """Clean up test nodes after each test"""
    test_node_ids = []

    yield test_node_ids

    # Cleanup
    if test_node_ids:
        async with db_pool.acquire() as conn:
            for node_id in test_node_ids:
                await conn.execute(
                    "DELETE FROM knowledge_graph_nodes WHERE id = $1",
                    node_id
                )


class TestGraphDAOE2E:
    """E2E tests for GraphDAO with real database"""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_node(self, dao, cleanup_test_nodes):
        """Test creating and retrieving a node from database"""
        entity_id = uuid4()
        node = Node(
            node_type=NodeType.COURSE,
            entity_id=entity_id,
            label="E2E Test Course",
            properties={'difficulty': 'beginner', 'duration': 30}
        )

        # Create node
        created_node = await dao.create_node(node)
        cleanup_test_nodes.append(created_node.id)

        assert created_node.id is not None
        assert created_node.created_at is not None
        assert created_node.updated_at is not None

        # Retrieve node
        retrieved_node = await dao.get_node_by_id(created_node.id)

        assert retrieved_node is not None
        assert retrieved_node.label == "E2E Test Course"
        assert retrieved_node.properties['difficulty'] == 'beginner'
        assert retrieved_node.properties['duration'] == 30

    @pytest.mark.asyncio
    async def test_create_and_retrieve_edge(self, dao, cleanup_test_nodes):
        """Test creating edge between nodes"""
        # Create source node
        source_node = Node(NodeType.COURSE, uuid4(), "Source Course")
        source = await dao.create_node(source_node)
        cleanup_test_nodes.append(source.id)

        # Create target node
        target_node = Node(NodeType.COURSE, uuid4(), "Target Course")
        target = await dao.create_node(target_node)
        cleanup_test_nodes.append(target.id)

        # Create edge
        edge = Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=source.id,
            target_node_id=target.id,
            weight=Decimal('0.9')
        )
        created_edge = await dao.create_edge(edge)

        assert created_edge.id is not None

        # Retrieve edge
        retrieved_edge = await dao.get_edge_by_id(created_edge.id)

        assert retrieved_edge is not None
        assert retrieved_edge.edge_type == EdgeType.PREREQUISITE_OF
        assert retrieved_edge.source_node_id == source.id
        assert retrieved_edge.target_node_id == target.id
        assert retrieved_edge.weight == Decimal('0.9')

    @pytest.mark.asyncio
    async def test_get_neighbors(self, dao, cleanup_test_nodes):
        """Test getting neighbors of a node"""
        # Create nodes
        center_node = await dao.create_node(Node(NodeType.COURSE, uuid4(), "Center"))
        cleanup_test_nodes.append(center_node.id)

        neighbor1 = await dao.create_node(Node(NodeType.COURSE, uuid4(), "Neighbor 1"))
        cleanup_test_nodes.append(neighbor1.id)

        neighbor2 = await dao.create_node(Node(NodeType.COURSE, uuid4(), "Neighbor 2"))
        cleanup_test_nodes.append(neighbor2.id)

        # Create edges
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=center_node.id,
            target_node_id=neighbor1.id,
            weight=Decimal('1.0')
        ))
        await dao.create_edge(Edge(
            edge_type=EdgeType.RELATES_TO,
            source_node_id=center_node.id,
            target_node_id=neighbor2.id,
            weight=Decimal('0.5')
        ))

        # Get neighbors
        neighbors = await dao.get_neighbors(center_node.id, direction='outgoing')

        assert len(neighbors) == 2
        neighbor_labels = [n['label'] for n in neighbors]
        assert "Neighbor 1" in neighbor_labels
        assert "Neighbor 2" in neighbor_labels

    @pytest.mark.asyncio
    async def test_search_nodes(self, dao, cleanup_test_nodes):
        """Test full-text search on nodes"""
        # Create searchable nodes
        node1 = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Python Programming Basics")
        )
        cleanup_test_nodes.append(node1.id)

        node2 = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Advanced Python Development")
        )
        cleanup_test_nodes.append(node2.id)

        node3 = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "JavaScript Fundamentals")
        )
        cleanup_test_nodes.append(node3.id)

        # Search for "Python"
        results = await dao.search_nodes("Python", limit=10)

        assert len(results) >= 2
        python_courses = [n for n in results if 'Python' in n.label]
        assert len(python_courses) >= 2


class TestGraphServiceE2E:
    """E2E tests for GraphService"""

    @pytest.mark.asyncio
    async def test_create_course_with_service(self, graph_service, cleanup_test_nodes):
        """Test creating course through service layer"""
        entity_id = uuid4()

        node = await graph_service.create_node(
            node_type=NodeType.COURSE,
            entity_id=entity_id,
            label="Service Test Course",
            properties={'difficulty': 'intermediate'},
            user_id=uuid4()
        )
        cleanup_test_nodes.append(node.id)

        assert node.id is not None
        assert node.label == "Service Test Course"
        assert node.properties['difficulty'] == 'intermediate'

    @pytest.mark.asyncio
    async def test_bulk_import_graph(self, graph_service, cleanup_test_nodes):
        """Test bulk importing graph data"""
        course1_id = uuid4()
        course2_id = uuid4()

        nodes_data = [
            {
                'node_type': 'course',
                'entity_id': str(course1_id),
                'label': 'Bulk Course 1',
                'properties': {'difficulty': 'beginner'}
            },
            {
                'node_type': 'course',
                'entity_id': str(course2_id),
                'label': 'Bulk Course 2',
                'properties': {'difficulty': 'intermediate'}
            }
        ]

        edges_data = [
            {
                'edge_type': 'prerequisite_of',
                'source_entity_id': str(course1_id),
                'target_entity_id': str(course2_id),
                'weight': 1.0
            }
        ]

        summary = await graph_service.bulk_import_graph(nodes_data, edges_data)

        # Track for cleanup
        for node in await graph_service.dao.list_nodes_by_type(NodeType.COURSE, limit=100):
            if 'Bulk Course' in node.label:
                cleanup_test_nodes.append(node.id)

        assert summary['nodes_created'] == 2
        assert summary['edges_created'] == 1


class TestPathFindingE2E:
    """E2E tests for learning path finding"""

    @pytest.mark.asyncio
    async def test_find_learning_path_shortest(self, dao, path_service, cleanup_test_nodes):
        """Test finding shortest learning path"""
        # Create a simple path: A -> B -> C
        node_a = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Course A", properties={'difficulty': 'beginner', 'duration': 20})
        )
        cleanup_test_nodes.append(node_a.id)

        node_b = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Course B", properties={'difficulty': 'intermediate', 'duration': 30})
        )
        cleanup_test_nodes.append(node_b.id)

        node_c = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Course C", properties={'difficulty': 'advanced', 'duration': 40})
        )
        cleanup_test_nodes.append(node_c.id)

        # Create edges
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=node_a.id,
            target_node_id=node_b.id,
            weight=Decimal('1.0')
        ))
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=node_b.id,
            target_node_id=node_c.id,
            weight=Decimal('1.0')
        ))

        # Find learning path
        path_result = await path_service.find_learning_path(
            start_course_id=node_a.entity_id,
            end_course_id=node_c.entity_id,
            optimization='shortest'
        )

        assert path_result is not None
        assert path_result['total_courses'] == 3
        assert path_result['total_duration'] == 90
        assert path_result['difficulty_progression'] == ['beginner', 'intermediate', 'advanced']

    @pytest.mark.asyncio
    async def test_recommended_next_courses(self, dao, path_service, cleanup_test_nodes):
        """Test getting recommended next courses"""
        # Create current course
        current = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Current Course")
        )
        cleanup_test_nodes.append(current.id)

        # Create next courses
        next1 = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Next Course 1")
        )
        cleanup_test_nodes.append(next1.id)

        next2 = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Next Course 2")
        )
        cleanup_test_nodes.append(next2.id)

        # Create prerequisite edges
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=current.id,
            target_node_id=next1.id,
            weight=Decimal('0.9')
        ))
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=current.id,
            target_node_id=next2.id,
            weight=Decimal('0.8')
        ))

        # Get recommendations
        recommendations = await path_service.get_recommended_next_courses(
            current_course_id=current.entity_id,
            limit=5
        )

        assert len(recommendations) >= 2
        course_names = [rec['course_name'] for rec in recommendations]
        assert "Next Course 1" in course_names
        assert "Next Course 2" in course_names


class TestPrerequisitesE2E:
    """E2E tests for prerequisite checking"""

    @pytest.mark.asyncio
    async def test_check_prerequisites_ready(self, dao, prereq_service, cleanup_test_nodes):
        """Test checking prerequisites when student is ready"""
        # Create prerequisite course
        prereq = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Prerequisite Course")
        )
        cleanup_test_nodes.append(prereq.id)

        # Create target course
        target = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Target Course")
        )
        cleanup_test_nodes.append(target.id)

        # Create prerequisite relationship
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=prereq.id,
            target_node_id=target.id,
            weight=Decimal('1.0'),
            properties={'mandatory': True}
        ))

        # Check prerequisites (student completed prerequisite)
        result = await prereq_service.check_prerequisites(
            course_id=target.entity_id,
            student_id=uuid4(),
            completed_course_ids=[prereq.entity_id]
        )

        assert result['ready'] is True
        assert len(result['missing_prerequisites']) == 0

    @pytest.mark.asyncio
    async def test_check_prerequisites_not_ready(self, dao, prereq_service, cleanup_test_nodes):
        """Test checking prerequisites when student is not ready"""
        # Create prerequisite course
        prereq = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Required Prerequisite")
        )
        cleanup_test_nodes.append(prereq.id)

        # Create target course
        target = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Advanced Course")
        )
        cleanup_test_nodes.append(target.id)

        # Create prerequisite relationship
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=prereq.id,
            target_node_id=target.id,
            weight=Decimal('1.0'),
            properties={'mandatory': True}
        ))

        # Check prerequisites (student has NOT completed prerequisite)
        result = await prereq_service.check_prerequisites(
            course_id=target.entity_id,
            student_id=uuid4(),
            completed_course_ids=[]  # Empty - no courses completed
        )

        assert result['ready'] is False
        assert len(result['missing_prerequisites']) == 1
        assert result['missing_prerequisites'][0]['course_name'] == "Required Prerequisite"

    @pytest.mark.asyncio
    async def test_validate_course_sequence(self, dao, prereq_service, cleanup_test_nodes):
        """Test validating a course sequence"""
        # Create courses in sequence
        course1 = await dao.create_node(Node(NodeType.COURSE, uuid4(), "Course 1"))
        cleanup_test_nodes.append(course1.id)

        course2 = await dao.create_node(Node(NodeType.COURSE, uuid4(), "Course 2"))
        cleanup_test_nodes.append(course2.id)

        course3 = await dao.create_node(Node(NodeType.COURSE, uuid4(), "Course 3"))
        cleanup_test_nodes.append(course3.id)

        # Create prerequisite chain: 1 -> 2 -> 3
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=course1.id,
            target_node_id=course2.id,
            weight=Decimal('1.0')
        ))
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=course2.id,
            target_node_id=course3.id,
            weight=Decimal('1.0')
        ))

        # Validate correct sequence
        valid_result = await prereq_service.validate_course_sequence(
            course_sequence=[course1.entity_id, course2.entity_id, course3.entity_id]
        )
        assert valid_result['valid'] is True

        # Validate incorrect sequence (reversed)
        invalid_result = await prereq_service.validate_course_sequence(
            course_sequence=[course3.entity_id, course2.entity_id, course1.entity_id]
        )
        assert invalid_result['valid'] is False
        assert len(invalid_result['issues']) > 0


class TestCompleteWorkflowE2E:
    """E2E tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_complete_learning_journey(self, dao, path_service, prereq_service, cleanup_test_nodes):
        """Test complete student learning journey"""
        # Create learning path: Beginner -> Intermediate -> Advanced
        beginner = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Python Beginner",
                 properties={'difficulty': 'beginner', 'duration': 20})
        )
        cleanup_test_nodes.append(beginner.id)

        intermediate = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Python Intermediate",
                 properties={'difficulty': 'intermediate', 'duration': 30})
        )
        cleanup_test_nodes.append(intermediate.id)

        advanced = await dao.create_node(
            Node(NodeType.COURSE, uuid4(), "Python Advanced",
                 properties={'difficulty': 'advanced', 'duration': 40})
        )
        cleanup_test_nodes.append(advanced.id)

        # Create prerequisite relationships
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=beginner.id,
            target_node_id=intermediate.id,
            weight=Decimal('1.0')
        ))
        await dao.create_edge(Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=intermediate.id,
            target_node_id=advanced.id,
            weight=Decimal('1.0')
        ))

        # Step 1: Student wants to reach advanced course
        path = await path_service.find_learning_path(
            start_course_id=beginner.entity_id,
            end_course_id=advanced.entity_id,
            optimization='shortest'
        )

        assert path['total_courses'] == 3
        assert not path['has_difficulty_jump']

        # Step 2: Check prerequisites for intermediate (completed beginner)
        prereq_check_ready = await prereq_service.check_prerequisites(
            course_id=intermediate.entity_id,
            student_id=uuid4(),
            completed_course_ids=[beginner.entity_id]
        )
        assert prereq_check_ready['ready'] is True

        # Step 3: Check prerequisites for advanced (NOT completed intermediate)
        prereq_check_not_ready = await prereq_service.check_prerequisites(
            course_id=advanced.entity_id,
            student_id=uuid4(),
            completed_course_ids=[beginner.entity_id]
        )
        assert prereq_check_not_ready['ready'] is False

        # Step 4: Get recommended next course after beginner
        recommendations = await path_service.get_recommended_next_courses(
            current_course_id=beginner.entity_id,
            limit=5
        )
        assert len(recommendations) > 0
        assert recommendations[0]['course_name'] == "Python Intermediate"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
