"""
Path Finding Service - Learning Path Generation

BUSINESS REQUIREMENT:
Generate optimal learning paths between courses considering
student progress, difficulty progression, and prerequisites.

BUSINESS VALUE:
- Helps students plan their learning journey
- Suggests optimal course sequences
- Minimizes difficulty jumps
- Reduces time to skill mastery

TECHNICAL IMPLEMENTATION:
- Uses graph algorithms (Dijkstra, A*)
- Integrates with student progress data
- Enriches paths with metadata
- Provides multiple optimization strategies

WHY:
Students need guidance on what courses to take and in what order.
Optimal learning paths improve completion rates and learning outcomes.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from knowledge_graph_service.domain.entities.node import Node, NodeType
from knowledge_graph_service.domain.entities.edge import Edge, EdgeType
from data_access.graph_dao import GraphDAO
from algorithms.path_finding import PathFinder, build_graph_structure

logger = logging.getLogger(__name__)


class PathNotFoundError(Exception):
    """Raised when no path exists between nodes"""
    pass


class InvalidOptimizationError(Exception):
    """Raised when invalid optimization type is specified"""
    pass


class PathFindingService:
    """
    Learning Path Generation Service

    BUSINESS VALUE:
    Provides intelligent course sequencing recommendations
    """

    def __init__(self, dao: GraphDAO):
        """
        Initialize path finding service

        Args:
            dao: GraphDAO instance for data access
        """
        self.dao = dao

    async def find_learning_path(
        self,
        start_course_id: UUID,
        end_course_id: UUID,
        optimization: str = 'shortest',
        student_id: Optional[UUID] = None,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Find optimal learning path between two courses

        BUSINESS USE CASE:
        Student wants to learn Advanced Python but is currently at Beginner level.
        Find the optimal sequence of courses to get there.

        Args:
            start_course_id: Starting course UUID
            end_course_id: Target course UUID
            optimization: 'shortest', 'easiest', or 'fastest'
            student_id: Optional student UUID for personalization
            max_depth: Maximum path length

        Returns:
            Dict with path, metadata, and recommendations

        Raises:
            PathNotFoundError: If no path exists
            InvalidOptimizationError: If optimization type is invalid
        """
        # Validate optimization type
        valid_optimizations = {'shortest', 'easiest', 'fastest'}
        if optimization not in valid_optimizations:
            raise InvalidOptimizationError(
                f"Optimization must be one of {valid_optimizations}, got '{optimization}'"
            )

        # Get graph nodes for courses
        start_node = await self.dao.get_node_by_entity(
            start_course_id,
            NodeType.COURSE
        )
        end_node = await self.dao.get_node_by_entity(
            end_course_id,
            NodeType.COURSE
        )

        if not start_node or not end_node:
            raise PathNotFoundError(
                f"Could not find graph nodes for courses: "
                f"start={start_course_id}, end={end_course_id}"
            )

        # Build graph structure
        graph_data = await self._build_graph_structure()

        # Get node properties for all nodes
        node_properties = await self._get_node_properties()

        # Create path finder
        path_finder = PathFinder(graph_data)

        # Find path using selected optimization
        path_result = path_finder.find_learning_path(
            start=start_node.id,
            end=end_node.id,
            node_properties=node_properties,
            optimization=optimization,
            max_depth=max_depth
        )

        if not path_result:
            raise PathNotFoundError(
                f"No path found from {start_course_id} to {end_course_id} "
                f"within {max_depth} steps"
            )

        # Enrich with course details
        enriched_path = await self._enrich_with_course_details(
            path_result,
            student_id
        )

        logger.info(
            f"Found learning path: {start_course_id} -> {end_course_id} "
            f"({len(path_result['path'])} courses, optimization={optimization})"
        )

        return enriched_path

    async def find_alternative_paths(
        self,
        start_course_id: UUID,
        end_course_id: UUID,
        max_paths: int = 3,
        max_depth: int = 5
    ) -> List[List[UUID]]:
        """
        Find multiple alternative paths

        BUSINESS USE CASE:
        Show students different learning routes to the same destination

        Args:
            start_course_id: Starting course UUID
            end_course_id: Target course UUID
            max_paths: Maximum number of paths to find
            max_depth: Maximum path length

        Returns:
            List of paths (each path is a list of course UUIDs)
        """
        # Get graph nodes
        start_node = await self.dao.get_node_by_entity(
            start_course_id,
            NodeType.COURSE
        )
        end_node = await self.dao.get_node_by_entity(
            end_course_id,
            NodeType.COURSE
        )

        if not start_node or not end_node:
            return []

        # Build graph structure
        graph_data = await self._build_graph_structure()

        # Create path finder
        path_finder = PathFinder(graph_data)

        # Find all paths
        paths = path_finder.find_all_paths(
            start=start_node.id,
            end=end_node.id,
            max_depth=max_depth,
            max_paths=max_paths
        )

        # Convert node UUIDs to course UUIDs
        course_paths = []
        for path in paths:
            course_path = []
            for node_id in path:
                node = await self.dao.get_node_by_id(node_id)
                if node:
                    course_path.append(node.entity_id)
            course_paths.append(course_path)

        return course_paths

    async def get_recommended_next_courses(
        self,
        current_course_id: UUID,
        student_id: Optional[UUID] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recommended next courses after completing current course

        BUSINESS USE CASE:
        Student completes "Introduction to Python", what should they take next?

        Args:
            current_course_id: Just completed course UUID
            student_id: Optional student UUID for personalization
            limit: Maximum number of recommendations

        Returns:
            List of recommended courses with metadata
        """
        # Get graph node for course
        course_node = await self.dao.get_node_by_entity(
            current_course_id,
            NodeType.COURSE
        )

        if not course_node:
            return []

        # Get outgoing edges (this course is prerequisite for...)
        outgoing_edges = await self.dao.get_edges_from_node(
            course_node.id,
            edge_types=[EdgeType.PREREQUISITE_OF]
        )

        # Get related courses
        related_edges = await self.dao.get_edges_from_node(
            course_node.id,
            edge_types=[
                EdgeType.RELATES_TO,
                EdgeType.BUILDS_ON,
                EdgeType.SIMILAR_TO
            ]
        )

        # Combine and prioritize
        recommendations = []

        # Priority 1: Direct next courses (this is prerequisite for)
        for edge in outgoing_edges[:limit]:
            target_node = await self.dao.get_node_by_id(edge.target_node_id)
            if target_node and target_node.node_type == NodeType.COURSE:
                recommendations.append({
                    'course_id': target_node.entity_id,
                    'course_name': target_node.label,
                    'reason': 'natural_progression',
                    'relationship': 'prerequisite_for',
                    'weight': float(edge.weight),
                    'priority': 1
                })

        # Priority 2: Related courses
        for edge in related_edges[:limit - len(recommendations)]:
            target_node = await self.dao.get_node_by_id(edge.target_node_id)
            if target_node and target_node.node_type == NodeType.COURSE:
                recommendations.append({
                    'course_id': target_node.entity_id,
                    'course_name': target_node.label,
                    'reason': 'related_content',
                    'relationship': edge.edge_type.value,
                    'weight': float(edge.weight),
                    'priority': 2
                })

        # Sort by priority and weight
        recommendations.sort(
            key=lambda x: (x['priority'], -x['weight'])
        )

        return recommendations[:limit]

    async def get_skill_progression_path(
        self,
        target_skills: List[str],
        student_id: Optional[UUID] = None,
        max_courses: int = 10
    ) -> Dict[str, Any]:
        """
        Generate learning path to acquire specific skills

        BUSINESS USE CASE:
        Student wants to learn "Machine Learning" and "Data Visualization".
        Find the optimal course sequence to acquire these skills.

        Args:
            target_skills: List of skill names
            student_id: Optional student UUID
            max_courses: Maximum courses in path

        Returns:
            Dict with course sequence and skill coverage
        """
        # Find skill nodes
        skill_nodes = []
        for skill_name in target_skills:
            nodes = await self.dao.search_nodes(
                skill_name,
                node_types=[NodeType.SKILL],
                limit=1
            )
            if nodes:
                skill_nodes.append(nodes[0])

        if not skill_nodes:
            return {
                'path': [],
                'skills_covered': [],
                'message': 'No matching skills found'
            }

        # Find courses that teach these skills
        course_skill_map = {}
        for skill_node in skill_nodes:
            # Get edges: courses that develop this skill
            incoming_edges = await self.dao.get_edges_to_node(
                skill_node.id,
                edge_types=[EdgeType.DEVELOPS]
            )

            for edge in incoming_edges:
                source_node = await self.dao.get_node_by_id(edge.source_node_id)
                if source_node and source_node.node_type == NodeType.COURSE:
                    if source_node.entity_id not in course_skill_map:
                        course_skill_map[source_node.entity_id] = {
                            'node': source_node,
                            'skills': []
                        }
                    course_skill_map[source_node.entity_id]['skills'].append({
                        'skill': skill_node.label,
                        'weight': float(edge.weight)
                    })

        # Sort courses by number of target skills they teach
        sorted_courses = sorted(
            course_skill_map.values(),
            key=lambda x: len(x['skills']),
            reverse=True
        )

        # Build optimal path considering prerequisites
        path = []
        covered_skills = set()

        for course_data in sorted_courses[:max_courses]:
            course_node = course_data['node']

            # Check if this course adds new skills
            new_skills = [
                s['skill'] for s in course_data['skills']
                if s['skill'] not in covered_skills
            ]

            if new_skills or len(path) == 0:
                path.append({
                    'course_id': course_node.entity_id,
                    'course_name': course_node.label,
                    'skills': course_data['skills'],
                    'new_skills': new_skills
                })
                covered_skills.update(new_skills)

            # Stop if all skills are covered
            if len(covered_skills) >= len(target_skills):
                break

        return {
            'path': path,
            'skills_covered': list(covered_skills),
            'target_skills': target_skills,
            'coverage': len(covered_skills) / len(target_skills) if target_skills else 0
        }

    # ========================================
    # HELPER METHODS
    # ========================================

    async def _build_graph_structure(self) -> Dict[UUID, List[tuple]]:
        """
        Build graph structure from database

        Returns:
            Dict mapping node_id -> [(neighbor_id, weight, edge_properties)]
        """
        # Get all nodes (limit to courses and related entities)
        all_nodes = []
        for node_type in [NodeType.COURSE, NodeType.CONCEPT, NodeType.SKILL]:
            nodes = await self.dao.list_nodes_by_type(
                node_type,
                limit=10000  # High limit for complete graph
            )
            all_nodes.extend(nodes)

        # Initialize graph structure
        graph = {node.id: [] for node in all_nodes}

        # Get all edges for these nodes
        for node in all_nodes:
            edges = await self.dao.get_edges_from_node(node.id)

            for edge in edges:
                graph[node.id].append((
                    edge.target_node_id,
                    float(edge.weight),
                    edge.properties
                ))

        return graph

    async def _get_node_properties(self) -> Dict[UUID, Dict[str, Any]]:
        """
        Get properties for all nodes

        Returns:
            Dict mapping node_id -> properties
        """
        node_properties = {}

        # Get all nodes
        all_nodes = []
        for node_type in [NodeType.COURSE, NodeType.CONCEPT, NodeType.SKILL]:
            nodes = await self.dao.list_nodes_by_type(node_type, limit=10000)
            all_nodes.extend(nodes)

        # Build property map
        for node in all_nodes:
            node_properties[node.id] = {
                'label': node.label,
                'node_type': node.node_type.value,
                **node.properties
            }

        return node_properties

    async def _enrich_with_course_details(
        self,
        path_result: Dict[str, Any],
        student_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Enrich path with detailed course information

        Args:
            path_result: Path from PathFinder
            student_id: Optional student UUID

        Returns:
            Enriched path with course details
        """
        # Convert node UUIDs to course details
        course_details = []

        for node_id_str in path_result['path']:
            node_id = UUID(node_id_str)
            node = await self.dao.get_node_by_id(node_id)

            if node:
                detail = {
                    'course_id': str(node.entity_id),
                    'course_name': node.label,
                    'difficulty': node.properties.get('difficulty', 'intermediate'),
                    'duration': node.properties.get('duration', 0),
                    'node_id': str(node.id)
                }

                # Add student-specific data if available
                if student_id:
                    # TODO: Check if student has completed this course
                    # This would integrate with student progress service
                    detail['completed'] = False
                    detail['in_progress'] = False

                course_details.append(detail)

        return {
            **path_result,
            'course_details': course_details,
            'path': [d['course_id'] for d in course_details]  # Use course UUIDs
        }
