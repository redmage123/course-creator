"""
Unit Tests for Path Finding Algorithms

BUSINESS CONTEXT:
Tests the path finding service that discovers learning paths between
courses, validates prerequisite chains, and recommends course sequences.

TECHNICAL VALIDATION:
- Shortest path algorithms (Dijkstra)
- All paths enumeration
- Learning path optimization
- Prerequisite chain validation
- Path cost calculation

TEST COVERAGE TARGETS:
- Line Coverage: 85%+
- Function Coverage: 80%+
- Branch Coverage: 75%+
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict
import sys
from pathlib import Path

# Add knowledge-graph-service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'knowledge-graph-service'))

from knowledge_graph_service.application.services.path_finding_service import (
    PathFindingService,
    LearningPath,
    PathNode
)
from knowledge_graph_service.domain.entities.node import Node, NodeType
from knowledge_graph_service.domain.entities.edge import Edge, EdgeType


class TestPathFinding:
    """Test suite for Path Finding Algorithms"""

    @pytest.fixture
    def path_service(self):
        """
        TEST FIXTURE: Path Finding Service instance

        BUSINESS SCENARIO: Student needs optimal learning sequence
        TECHNICAL SETUP: Initialize service with mock graph
        """
        with patch('knowledge_graph_service.infrastructure.database.get_database_pool'):
            service = PathFindingService()
            service.db_pool = AsyncMock()
            return service

    @pytest.fixture
    def sample_course_graph(self):
        """
        TEST FIXTURE: Sample course prerequisite graph

        GRAPH STRUCTURE:
        Programming Basics → Python 101 → Python 201 → Advanced Python
                                       ↘ Data Structures ↗
        """
        return {
            "nodes": [
                {"id": "course_1", "name": "Programming Basics", "difficulty": 1},
                {"id": "course_2", "name": "Python 101", "difficulty": 2},
                {"id": "course_3", "name": "Python 201", "difficulty": 3},
                {"id": "course_4", "name": "Data Structures", "difficulty": 3},
                {"id": "course_5", "name": "Advanced Python", "difficulty": 4}
            ],
            "edges": [
                {"source": "course_1", "target": "course_2", "type": "prerequisite_of"},
                {"source": "course_2", "target": "course_3", "type": "prerequisite_of"},
                {"source": "course_2", "target": "course_4", "type": "prerequisite_of"},
                {"source": "course_3", "target": "course_5", "type": "prerequisite_of"},
                {"source": "course_4", "target": "course_5", "type": "prerequisite_of"}
            ]
        }

    # ==========================================
    # SHORTEST PATH TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_shortest_path_direct(self, path_service):
        """
        TEST: Find shortest path between adjacent courses

        BUSINESS SCENARIO: Student asks path from Python 101 to Python 201
        TECHNICAL VALIDATION: Single-edge path returned
        EXPECTED OUTCOME: Direct path [Python 101 → Python 201]
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"course_id": "course_2", "course_name": "Python 101", "step": 0},
            {"course_id": "course_3", "course_name": "Python 201", "step": 1}
        ])
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        path = await path_service.find_shortest_path("course_2", "course_3")

        # Assert
        assert len(path) == 2
        assert path[0].id == "course_2"
        assert path[1].id == "course_3"

    @pytest.mark.asyncio
    async def test_shortest_path_multi_hop(self, path_service):
        """
        TEST: Find shortest path across multiple courses

        BUSINESS SCENARIO: Student asks path from Basics to Advanced
        TECHNICAL VALIDATION: Multi-edge path returned
        EXPECTED OUTCOME: Path with 4 courses
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"course_id": "course_1", "course_name": "Programming Basics", "step": 0},
            {"course_id": "course_2", "course_name": "Python 101", "step": 1},
            {"course_id": "course_3", "course_name": "Python 201", "step": 2},
            {"course_id": "course_5", "course_name": "Advanced Python", "step": 3}
        ])
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        path = await path_service.find_shortest_path("course_1", "course_5")

        # Assert
        assert len(path) == 4
        assert path[0].properties["name"] == "Programming Basics"
        assert path[-1].properties["name"] == "Advanced Python"

    @pytest.mark.asyncio
    async def test_shortest_path_no_path_exists(self, path_service):
        """
        TEST: Handle case where no path exists

        BUSINESS SCENARIO: Courses in different learning tracks
        TECHNICAL VALIDATION: Empty result or None returned
        EXPECTED OUTCOME: No path found
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        path = await path_service.find_shortest_path("course_1", "unconnected_course")

        # Assert
        assert path is None or len(path) == 0

    # ==========================================
    # ALL PATHS TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_find_all_paths(self, path_service):
        """
        TEST: Find all possible paths between courses

        BUSINESS SCENARIO: Student wants alternative learning routes
        TECHNICAL VALIDATION: Multiple valid paths returned
        EXPECTED OUTCOME: List of different paths
        """
        # Arrange - Two possible paths to Advanced Python
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            # Path 1: via Python 201
            [{"id": "course_2"}, {"id": "course_3"}, {"id": "course_5"}],
            # Path 2: via Data Structures
            [{"id": "course_2"}, {"id": "course_4"}, {"id": "course_5"}]
        ])
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        all_paths = await path_service.find_all_paths("course_2", "course_5", max_paths=10)

        # Assert
        assert len(all_paths) >= 2
        # Paths should be different
        assert set([p[1].id for p in all_paths]) == {"course_3", "course_4"}

    # ==========================================
    # LEARNING PATH OPTIMIZATION TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_optimize_learning_path_by_difficulty(self, path_service):
        """
        TEST: Optimize learning path considering difficulty

        BUSINESS SCENARIO: Student wants gradual difficulty increase
        TECHNICAL VALIDATION: Path ordered by difficulty
        EXPECTED OUTCOME: Difficulty increases progressively
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"course_id": "course_1", "difficulty": 1, "duration": 20},
            {"course_id": "course_2", "difficulty": 2, "duration": 30},
            {"course_id": "course_3", "difficulty": 3, "duration": 40},
            {"course_id": "course_5", "difficulty": 4, "duration": 50}
        ])
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        optimized_path = await path_service.optimize_learning_path(
            start="course_1",
            end="course_5",
            optimization_criteria="difficulty"
        )

        # Assert
        difficulties = [node.properties["difficulty"] for node in optimized_path]
        assert difficulties == sorted(difficulties)  # Ascending order

    @pytest.mark.asyncio
    async def test_optimize_learning_path_by_duration(self, path_service):
        """
        TEST: Optimize learning path for shortest total duration

        BUSINESS SCENARIO: Student wants quickest path to goal
        TECHNICAL VALIDATION: Minimum total duration path
        EXPECTED OUTCOME: Path with lowest sum of durations
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"course_id": "course_2", "duration": 30},
            {"course_id": "course_4", "duration": 35},  # Shorter than course_3
            {"course_id": "course_5", "duration": 50}
        ])
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        optimized_path = await path_service.optimize_learning_path(
            start="course_2",
            end="course_5",
            optimization_criteria="duration"
        )

        # Assert
        total_duration = sum(node.properties["duration"] for node in optimized_path)
        assert total_duration == 115  # 30 + 35 + 50

    # ==========================================
    # PREREQUISITE VALIDATION TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_validate_prerequisites_met(self, path_service):
        """
        TEST: Validate student has completed prerequisites

        BUSINESS SCENARIO: Check if student can enroll in course
        TECHNICAL VALIDATION: All prerequisites completed
        EXPECTED OUTCOME: Validation passes
        """
        # Arrange
        completed_courses = ["course_1", "course_2", "course_3"]
        target_course = "course_5"

        mock_conn = AsyncMock()
        # All prerequisites completed
        mock_conn.fetchval = AsyncMock(return_value=True)
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        is_ready = await path_service.validate_prerequisites(
            student_completed=completed_courses,
            target_course=target_course
        )

        # Assert
        assert is_ready is True

    @pytest.mark.asyncio
    async def test_validate_prerequisites_missing(self, path_service):
        """
        TEST: Detect missing prerequisites

        BUSINESS SCENARIO: Student tries to skip courses
        TECHNICAL VALIDATION: Missing prerequisites identified
        EXPECTED OUTCOME: Validation fails, missing courses listed
        """
        # Arrange
        completed_courses = ["course_1"]  # Missing course_2 and course_3
        target_course = "course_5"

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"course_id": "course_2", "course_name": "Python 101"},
            {"course_id": "course_3", "course_name": "Python 201"}
        ])
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        missing = await path_service.get_missing_prerequisites(
            student_completed=completed_courses,
            target_course=target_course
        )

        # Assert
        assert len(missing) == 2
        assert "course_2" in [c.id for c in missing]
        assert "course_3" in [c.id for c in missing]

    # ==========================================
    # COURSE RECOMMENDATION TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_recommend_next_courses(self, path_service):
        """
        TEST: Recommend next courses based on completed courses

        BUSINESS SCENARIO: Student finished Python 101, what's next?
        TECHNICAL VALIDATION: Eligible next courses identified
        EXPECTED OUTCOME: Python 201 and Data Structures recommended
        """
        # Arrange
        completed_courses = ["course_1", "course_2"]

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"course_id": "course_3", "course_name": "Python 201", "relevance_score": 0.95},
            {"course_id": "course_4", "course_name": "Data Structures", "relevance_score": 0.90}
        ])
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        recommendations = await path_service.recommend_next_courses(
            completed_courses=completed_courses,
            max_recommendations=5
        )

        # Assert
        assert len(recommendations) == 2
        assert recommendations[0].properties["relevance_score"] >= 0.90

    # ==========================================
    # PERFORMANCE TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_path_finding_large_graph(self, path_service):
        """
        TEST: Path finding performance on large graph

        BUSINESS SCENARIO: Platform with 1000+ courses
        TECHNICAL VALIDATION: Efficient algorithm execution
        EXPECTED OUTCOME: Path found within acceptable time
        """
        # Arrange
        mock_conn = AsyncMock()
        # Simulate path through many courses
        large_path = [
            {"course_id": f"course_{i}", "course_name": f"Course {i}", "step": i}
            for i in range(50)
        ]
        mock_conn.fetch = AsyncMock(return_value=large_path)
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        import time
        start = time.time()
        path = await path_service.find_shortest_path("course_0", "course_49")
        duration = time.time() - start

        # Assert
        assert len(path) == 50
        assert duration < 1.0  # Should complete in under 1 second

    # ==========================================
    # EDGE CASE TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_path_with_circular_prerequisites(self, path_service):
        """
        TEST: Handle circular prerequisite detection

        BUSINESS SCENARIO: Invalid course setup
        TECHNICAL VALIDATION: Cycle detected
        EXPECTED OUTCOME: Error or infinite loop prevention
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=Exception("Circular dependency detected"))
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(Exception, match="circular"):
            await path_service.find_shortest_path("course_A", "course_B")

    @pytest.mark.asyncio
    async def test_path_same_source_target(self, path_service):
        """
        TEST: Handle path from course to itself

        BUSINESS SCENARIO: Edge case input
        TECHNICAL VALIDATION: Single-node path returned
        EXPECTED OUTCOME: Path with only the source node
        """
        # Arrange
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"course_id": "course_1", "course_name": "Course 1", "step": 0}
        ])
        path_service.db_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        # Act
        path = await path_service.find_shortest_path("course_1", "course_1")

        # Assert
        assert len(path) == 1
        assert path[0].id == "course_1"
