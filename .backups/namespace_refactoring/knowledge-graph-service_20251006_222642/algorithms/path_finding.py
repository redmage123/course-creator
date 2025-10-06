"""
Graph Path Finding Algorithms

BUSINESS REQUIREMENT:
Find optimal learning paths between courses considering
difficulty progression and prerequisite constraints.

ALGORITHMS:
- Dijkstra's algorithm for shortest weighted paths
- A* for goal-directed search
- Custom optimization for learning paths

WHY:
Students need optimal learning sequences that respect
prerequisites and minimize difficulty jumps.
"""

import heapq
from typing import List, Dict, Optional, Set, Tuple
from uuid import UUID
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(order=True)
class PriorityNode:
    """
    Priority queue node for path finding

    WHY: Heapq requires ordered items
    """
    priority: float
    node_id: UUID = field(compare=False)
    path: List[UUID] = field(default_factory=list, compare=False)
    cost: float = field(default=0.0, compare=False)


class PathFinder:
    """
    Path finding algorithms for knowledge graph

    BUSINESS VALUE:
    Finds optimal learning paths between courses
    """

    def __init__(self, graph_structure: Dict[UUID, List[Tuple[UUID, float, Dict]]]):
        """
        Initialize path finder with graph structure

        Args:
            graph_structure: Dict mapping node_id -> [(neighbor_id, weight, edge_properties)]
        """
        self.graph = graph_structure

    def dijkstra(
        self,
        start: UUID,
        end: UUID,
        max_depth: int = 10
    ) -> Optional[List[UUID]]:
        """
        Find shortest weighted path using Dijkstra's algorithm

        BUSINESS USE CASE:
        Find shortest learning path by number of courses

        Args:
            start: Starting course UUID
            end: Target course UUID
            max_depth: Maximum path length

        Returns:
            List of node UUIDs in path, or None if no path exists
        """
        if start == end:
            return [start]

        if start not in self.graph:
            return None

        # Priority queue: (cost, node_id, path)
        queue: List[PriorityNode] = [PriorityNode(0.0, start, [start], 0.0)]
        visited: Set[UUID] = set()
        costs: Dict[UUID, float] = {start: 0.0}

        while queue:
            current = heapq.heappop(queue)

            if current.node_id == end:
                return current.path

            if current.node_id in visited:
                continue

            if len(current.path) > max_depth:
                continue

            visited.add(current.node_id)

            # Explore neighbors
            if current.node_id not in self.graph:
                continue

            for neighbor_id, weight, edge_props in self.graph[current.node_id]:
                if neighbor_id in visited:
                    continue

                # Cost is path length + edge weight
                new_cost = current.cost + float(weight)

                if neighbor_id not in costs or new_cost < costs[neighbor_id]:
                    costs[neighbor_id] = new_cost
                    new_path = current.path + [neighbor_id]
                    heapq.heappush(
                        queue,
                        PriorityNode(new_cost, neighbor_id, new_path, new_cost)
                    )

        return None

    def a_star(
        self,
        start: UUID,
        end: UUID,
        heuristic_func,
        max_depth: int = 10
    ) -> Optional[List[UUID]]:
        """
        Find path using A* algorithm with heuristic

        BUSINESS USE CASE:
        Find optimal path with difficulty progression hints

        Args:
            start: Starting course UUID
            end: Target course UUID
            heuristic_func: Function(node_id, end_id) -> estimated_cost
            max_depth: Maximum path length

        Returns:
            List of node UUIDs in path, or None if no path exists
        """
        if start == end:
            return [start]

        if start not in self.graph:
            return None

        # Priority queue: (f_score, node_id, path, g_score)
        # f_score = g_score + heuristic
        h_start = heuristic_func(start, end)
        queue: List[PriorityNode] = [
            PriorityNode(h_start, start, [start], 0.0)
        ]

        visited: Set[UUID] = set()
        g_scores: Dict[UUID, float] = {start: 0.0}

        while queue:
            current = heapq.heappop(queue)

            if current.node_id == end:
                return current.path

            if current.node_id in visited:
                continue

            if len(current.path) > max_depth:
                continue

            visited.add(current.node_id)

            # Explore neighbors
            if current.node_id not in self.graph:
                continue

            for neighbor_id, weight, edge_props in self.graph[current.node_id]:
                if neighbor_id in visited:
                    continue

                # g_score = actual cost from start
                new_g_score = current.cost + float(weight)

                if neighbor_id not in g_scores or new_g_score < g_scores[neighbor_id]:
                    g_scores[neighbor_id] = new_g_score

                    # f_score = g_score + heuristic
                    h_score = heuristic_func(neighbor_id, end)
                    f_score = new_g_score + h_score

                    new_path = current.path + [neighbor_id]
                    heapq.heappush(
                        queue,
                        PriorityNode(f_score, neighbor_id, new_path, new_g_score)
                    )

        return None

    def find_learning_path(
        self,
        start: UUID,
        end: UUID,
        node_properties: Dict[UUID, Dict],
        optimization: str = 'shortest',
        max_depth: int = 10
    ) -> Optional[Dict]:
        """
        Find learning path with business logic

        BUSINESS USE CASE:
        Find optimal learning path considering:
        - Shortest path (fewest courses)
        - Easiest path (minimize difficulty jumps)
        - Fastest path (minimize total duration)

        Args:
            start: Starting course UUID
            end: Target course UUID
            node_properties: Dict of node_id -> properties
            optimization: 'shortest', 'easiest', or 'fastest'
            max_depth: Maximum path length

        Returns:
            Dict with path, metadata, and recommendations
        """
        if optimization == 'shortest':
            path = self.dijkstra(start, end, max_depth)
        elif optimization == 'easiest':
            path = self._find_easiest_path(start, end, node_properties, max_depth)
        elif optimization == 'fastest':
            path = self._find_fastest_path(start, end, node_properties, max_depth)
        else:
            path = self.dijkstra(start, end, max_depth)

        if not path:
            return None

        # Enrich path with metadata
        return self._enrich_path(path, node_properties)

    def _find_easiest_path(
        self,
        start: UUID,
        end: UUID,
        node_properties: Dict[UUID, Dict],
        max_depth: int
    ) -> Optional[List[UUID]]:
        """
        Find path that minimizes difficulty jumps

        BUSINESS LOGIC:
        Prefer gradual difficulty progression
        """
        difficulty_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}

        def difficulty_heuristic(node_id: UUID, target_id: UUID) -> float:
            """Heuristic based on difficulty difference"""
            node_diff = difficulty_map.get(
                node_properties.get(node_id, {}).get('difficulty', 'intermediate'),
                2
            )
            target_diff = difficulty_map.get(
                node_properties.get(target_id, {}).get('difficulty', 'intermediate'),
                2
            )
            return abs(target_diff - node_diff)

        return self.a_star(start, end, difficulty_heuristic, max_depth)

    def _find_fastest_path(
        self,
        start: UUID,
        end: UUID,
        node_properties: Dict[UUID, Dict],
        max_depth: int
    ) -> Optional[List[UUID]]:
        """
        Find path that minimizes total duration

        BUSINESS LOGIC:
        Consider course durations in path cost
        """
        # Rebuild graph with duration-based weights
        duration_graph = {}

        for node_id, neighbors in self.graph.items():
            duration_graph[node_id] = []
            for neighbor_id, weight, edge_props in neighbors:
                # Weight by duration instead of edge weight
                duration = node_properties.get(neighbor_id, {}).get('duration', 40)
                duration_graph[node_id].append((neighbor_id, duration, edge_props))

        # Use Dijkstra with duration weights
        temp_graph = self.graph
        self.graph = duration_graph
        result = self.dijkstra(start, end, max_depth)
        self.graph = temp_graph

        return result

    def _enrich_path(
        self,
        path: List[UUID],
        node_properties: Dict[UUID, Dict]
    ) -> Dict:
        """
        Enrich path with metadata

        BUSINESS VALUE:
        Provide useful information about the learning path
        """
        difficulty_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}

        total_duration = 0
        difficulties = []

        for node_id in path:
            props = node_properties.get(node_id, {})
            total_duration += props.get('duration', 0)
            difficulty = props.get('difficulty', 'intermediate')
            difficulties.append(difficulty)

        return {
            'path': [str(node_id) for node_id in path],
            'total_courses': len(path),
            'total_duration': total_duration,
            'difficulty_progression': difficulties,
            'start_difficulty': difficulties[0] if difficulties else None,
            'end_difficulty': difficulties[-1] if difficulties else None,
            'has_difficulty_jump': self._has_difficulty_jump(difficulties, difficulty_map)
        }

    def _has_difficulty_jump(
        self,
        difficulties: List[str],
        difficulty_map: Dict[str, int]
    ) -> bool:
        """Check if path has significant difficulty jumps"""
        if len(difficulties) < 2:
            return False

        for i in range(len(difficulties) - 1):
            current = difficulty_map.get(difficulties[i], 2)
            next_level = difficulty_map.get(difficulties[i + 1], 2)

            # Jump of more than 1 level
            if abs(next_level - current) > 1:
                return True

        return False

    def find_all_paths(
        self,
        start: UUID,
        end: UUID,
        max_depth: int = 5,
        max_paths: int = 3
    ) -> List[List[UUID]]:
        """
        Find multiple paths between nodes

        BUSINESS USE CASE:
        Show alternative learning paths

        Args:
            start: Starting node
            end: Target node
            max_depth: Maximum path length
            max_paths: Maximum number of paths to find

        Returns:
            List of paths (each path is a list of node UUIDs)
        """
        all_paths = []

        def dfs(current: UUID, path: List[UUID], visited: Set[UUID]):
            """Depth-first search to find all paths"""
            if len(all_paths) >= max_paths:
                return

            if current == end:
                all_paths.append(path.copy())
                return

            if len(path) >= max_depth:
                return

            if current not in self.graph:
                return

            for neighbor_id, weight, edge_props in self.graph[current]:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    path.append(neighbor_id)

                    dfs(neighbor_id, path, visited)

                    path.pop()
                    visited.remove(neighbor_id)

        visited_set = {start}
        dfs(start, [start], visited_set)

        return all_paths


def build_graph_structure(
    nodes: List[Dict],
    edges: List[Dict]
) -> Dict[UUID, List[Tuple[UUID, float, Dict]]]:
    """
    Build graph structure from nodes and edges

    HELPER FUNCTION:
    Convert database results to graph structure for algorithms

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries

    Returns:
        Dict mapping node_id -> [(neighbor_id, weight, edge_properties)]
    """
    graph = {}

    # Initialize all nodes
    for node in nodes:
        node_id = UUID(node['id']) if isinstance(node['id'], str) else node['id']
        graph[node_id] = []

    # Add edges
    for edge in edges:
        source_id = UUID(edge['source_node_id']) if isinstance(edge['source_node_id'], str) else edge['source_node_id']
        target_id = UUID(edge['target_node_id']) if isinstance(edge['target_node_id'], str) else edge['target_node_id']
        weight = float(edge.get('weight', 1.0))
        properties = edge.get('properties', {})

        if source_id in graph:
            graph[source_id].append((target_id, weight, properties))

    return graph
