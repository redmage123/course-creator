"""
Unit Tests for Path Finding Algorithms

Tests Dijkstra, A*, and learning path algorithms.
"""

import pytest
from uuid import uuid4, UUID

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/knowledge-graph-service'))

from algorithms.path_finding import (
    PathFinder,
    build_graph_structure,
    PriorityNode
)


class TestPathFindingAlgorithms:
    """Test suite for path finding algorithms"""

    @pytest.fixture
    def simple_graph(self):
        """Create a simple test graph"""
        # A -> B -> C -> D
        node_a = uuid4()
        node_b = uuid4()
        node_c = uuid4()
        node_d = uuid4()

        graph = {
            node_a: [(node_b, 1.0, {})],
            node_b: [(node_c, 1.0, {})],
            node_c: [(node_d, 1.0, {})],
            node_d: []
        }

        return graph, (node_a, node_b, node_c, node_d)

    @pytest.fixture
    def branching_graph(self):
        """Create a graph with multiple paths"""
        #     B (weight 2)
        #    / \
        #   A   D
        #    \ /
        #     C (weight 1)
        node_a = uuid4()
        node_b = uuid4()
        node_c = uuid4()
        node_d = uuid4()

        graph = {
            node_a: [
                (node_b, 2.0, {}),
                (node_c, 1.0, {})
            ],
            node_b: [(node_d, 2.0, {})],
            node_c: [(node_d, 1.0, {})],
            node_d: []
        }

        return graph, (node_a, node_b, node_c, node_d)

    def test_dijkstra_simple_path(self, simple_graph):
        """Test Dijkstra on simple linear path"""
        graph, (node_a, node_b, node_c, node_d) = simple_graph

        finder = PathFinder(graph)
        path = finder.dijkstra(node_a, node_d)

        assert path == [node_a, node_b, node_c, node_d]

    def test_dijkstra_same_start_end(self, simple_graph):
        """Test Dijkstra when start equals end"""
        graph, (node_a, _, _, _) = simple_graph

        finder = PathFinder(graph)
        path = finder.dijkstra(node_a, node_a)

        assert path == [node_a]

    def test_dijkstra_no_path_exists(self, simple_graph):
        """Test Dijkstra when no path exists"""
        graph, (node_a, _, _, node_d) = simple_graph

        finder = PathFinder(graph)
        # Try to go backwards (impossible in directed graph)
        path = finder.dijkstra(node_d, node_a)

        assert path is None

    def test_dijkstra_shortest_weighted_path(self, branching_graph):
        """Test Dijkstra finds shortest weighted path"""
        graph, (node_a, node_b, node_c, node_d) = branching_graph

        finder = PathFinder(graph)
        path = finder.dijkstra(node_a, node_d)

        # Should take path through C (weight 1+1=2) not B (weight 2+2=4)
        assert path == [node_a, node_c, node_d]

    def test_dijkstra_max_depth_limit(self, simple_graph):
        """Test Dijkstra respects max depth limit"""
        graph, (node_a, _, _, node_d) = simple_graph

        finder = PathFinder(graph)
        path = finder.dijkstra(node_a, node_d, max_depth=2)

        # Path needs 4 nodes but max_depth=2, so no path found
        assert path is None

    def test_a_star_with_heuristic(self, branching_graph):
        """Test A* algorithm with heuristic function"""
        graph, (node_a, node_b, node_c, node_d) = branching_graph

        # Simple heuristic: always return 0 (equivalent to Dijkstra)
        def zero_heuristic(node_id, target_id):
            return 0.0

        finder = PathFinder(graph)
        path = finder.a_star(node_a, node_d, zero_heuristic)

        assert path == [node_a, node_c, node_d]

    def test_a_star_same_start_end(self, simple_graph):
        """Test A* when start equals end"""
        graph, (node_a, _, _, _) = simple_graph

        def zero_heuristic(node_id, target_id):
            return 0.0

        finder = PathFinder(graph)
        path = finder.a_star(node_a, node_a, zero_heuristic)

        assert path == [node_a]

    def test_find_all_paths(self, branching_graph):
        """Test finding multiple paths"""
        graph, (node_a, node_b, node_c, node_d) = branching_graph

        finder = PathFinder(graph)
        paths = finder.find_all_paths(node_a, node_d, max_depth=5, max_paths=10)

        # Should find 2 paths: A->B->D and A->C->D
        assert len(paths) == 2
        assert [node_a, node_b, node_d] in paths
        assert [node_a, node_c, node_d] in paths

    def test_find_all_paths_max_paths_limit(self, branching_graph):
        """Test that max_paths limit is respected"""
        graph, (node_a, _, _, node_d) = branching_graph

        finder = PathFinder(graph)
        paths = finder.find_all_paths(node_a, node_d, max_depth=5, max_paths=1)

        # Should stop after finding 1 path
        assert len(paths) == 1

    def test_priority_node_ordering(self):
        """Test that PriorityNode orders correctly"""
        node1 = PriorityNode(1.0, uuid4(), [], 1.0)
        node2 = PriorityNode(2.0, uuid4(), [], 2.0)
        node3 = PriorityNode(0.5, uuid4(), [], 0.5)

        nodes = sorted([node1, node2, node3])

        assert nodes[0].priority == 0.5
        assert nodes[1].priority == 1.0
        assert nodes[2].priority == 2.0


class TestLearningPathAlgorithms:
    """Test suite for learning path specific algorithms"""

    @pytest.fixture
    def difficulty_graph(self):
        """Create a graph with difficulty properties"""
        node_beginner = uuid4()
        node_intermediate = uuid4()
        node_advanced = uuid4()

        graph = {
            node_beginner: [(node_intermediate, 1.0, {})],
            node_intermediate: [(node_advanced, 1.0, {})],
            node_advanced: []
        }

        properties = {
            node_beginner: {
                'difficulty': 'beginner',
                'duration': 20
            },
            node_intermediate: {
                'difficulty': 'intermediate',
                'duration': 30
            },
            node_advanced: {
                'difficulty': 'advanced',
                'duration': 40
            }
        }

        return graph, properties, (node_beginner, node_intermediate, node_advanced)

    def test_find_learning_path_shortest(self, difficulty_graph):
        """Test finding shortest learning path"""
        graph, properties, (start, mid, end) = difficulty_graph

        finder = PathFinder(graph)
        result = finder.find_learning_path(
            start, end, properties, optimization='shortest'
        )

        assert result is not None
        assert len(result['path']) == 3
        assert result['total_courses'] == 3
        assert result['total_duration'] == 90  # 20 + 30 + 40

    def test_find_learning_path_easiest(self, difficulty_graph):
        """Test finding easiest learning path (minimal difficulty jumps)"""
        graph, properties, (start, mid, end) = difficulty_graph

        finder = PathFinder(graph)
        result = finder.find_learning_path(
            start, end, properties, optimization='easiest'
        )

        assert result is not None
        assert result['difficulty_progression'] == ['beginner', 'intermediate', 'advanced']
        assert result['start_difficulty'] == 'beginner'
        assert result['end_difficulty'] == 'advanced'

    def test_find_learning_path_fastest(self, difficulty_graph):
        """Test finding fastest learning path (minimal duration)"""
        graph, properties, (start, mid, end) = difficulty_graph

        finder = PathFinder(graph)
        result = finder.find_learning_path(
            start, end, properties, optimization='fastest'
        )

        assert result is not None
        assert result['total_duration'] == 90

    def test_difficulty_jump_detection(self, difficulty_graph):
        """Test detecting significant difficulty jumps"""
        graph, properties, (start, _, end) = difficulty_graph

        # Add direct edge from beginner to advanced (big jump)
        graph[start].append((end, 1.0, {}))

        finder = PathFinder(graph)
        result = finder.find_learning_path(
            start, end, properties, optimization='shortest'
        )

        if result and len(result['path']) == 2:  # Direct path
            # Beginner -> Advanced is a jump of 2 levels
            assert result.get('has_difficulty_jump') is True

    def test_path_enrichment_with_metadata(self, difficulty_graph):
        """Test that paths are enriched with metadata"""
        graph, properties, (start, _, end) = difficulty_graph

        finder = PathFinder(graph)
        result = finder.find_learning_path(
            start, end, properties, optimization='shortest'
        )

        assert 'total_duration' in result
        assert 'difficulty_progression' in result
        assert 'start_difficulty' in result
        assert 'end_difficulty' in result
        assert 'has_difficulty_jump' in result


class TestGraphStructureBuilder:
    """Test suite for graph structure building"""

    def test_build_graph_structure_empty(self):
        """Test building graph from empty lists"""
        nodes = []
        edges = []

        graph = build_graph_structure(nodes, edges)

        assert graph == {}

    def test_build_graph_structure_nodes_only(self):
        """Test building graph with nodes but no edges"""
        node1_id = uuid4()
        node2_id = uuid4()

        nodes = [
            {'id': str(node1_id)},
            {'id': str(node2_id)}
        ]
        edges = []

        graph = build_graph_structure(nodes, edges)

        assert node1_id in graph
        assert node2_id in graph
        assert graph[node1_id] == []
        assert graph[node2_id] == []

    def test_build_graph_structure_with_edges(self):
        """Test building graph with nodes and edges"""
        node1_id = uuid4()
        node2_id = uuid4()

        nodes = [
            {'id': str(node1_id)},
            {'id': str(node2_id)}
        ]
        edges = [
            {
                'source_node_id': str(node1_id),
                'target_node_id': str(node2_id),
                'weight': 0.8,
                'properties': {'test': 'value'}
            }
        ]

        graph = build_graph_structure(nodes, edges)

        assert len(graph[node1_id]) == 1
        assert graph[node1_id][0][0] == node2_id  # target
        assert graph[node1_id][0][1] == 0.8  # weight
        assert graph[node1_id][0][2] == {'test': 'value'}  # properties

    def test_build_graph_structure_uuid_conversion(self):
        """Test that string UUIDs are converted correctly"""
        node_id = uuid4()

        nodes = [{'id': str(node_id)}]
        edges = []

        graph = build_graph_structure(nodes, edges)

        # Should have UUID key, not string
        assert node_id in graph
        assert isinstance(list(graph.keys())[0], UUID)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
