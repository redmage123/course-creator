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

NOTE: These tests require real database connection.
Skipped until database fixtures are available in conftest.
"""

import pytest
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
    """
    Test suite for Graph Operations

    REFACTORING NOTES:
    - Remove all Mock/AsyncMock usage
    - Use real database connection from conftest fixtures
    - Replace mock_conn with actual asyncpg connection pool
    - Use test database with proper cleanup between tests
    """

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

    # All test methods need to be refactored to use real database
    # See conftest.py for database fixtures
