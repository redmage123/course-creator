"""
Knowledge Graph Service Client

BUSINESS PURPOSE:
Provides intelligent course recommendations and learning path generation using
graph-based relationships between courses, skills, and prerequisites.
Enables personalized learning journeys and optimal course sequencing.

TECHNICAL IMPLEMENTATION:
HTTP client for Knowledge Graph Service (port 8012).
Handles course relationships, prerequisite checking, learning path generation,
and skill progression tracking using graph algorithms.
"""

import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


@dataclass
class CourseNode:
    """Course node in knowledge graph"""
    course_id: int
    title: str
    properties: Dict[str, Any]


@dataclass
class LearningPath:
    """Learning path recommendation"""
    courses: List[Dict[str, Any]]
    total_duration: int
    difficulty_progression: List[str]


@dataclass
class PrerequisiteCheck:
    """Prerequisite validation result"""
    prerequisites_met: bool
    missing_prerequisites: List[Dict[str, Any]]


class KnowledgeGraphService:
    """
    Knowledge Graph Service Client

    Provides intelligent course recommendations and learning paths using
    graph-based analysis of course relationships, prerequisites, and skills.

    Key Features:
    - Course relationship mapping (prerequisites, related courses)
    - Learning path generation (skill-based, shortest path)
    - Prerequisite validation and checking
    - Course sequence optimization
    - Skill progression tracking
    """

    def __init__(self, base_url: str = "https://localhost:8012"):
        """
        Initialize Knowledge Graph service client

        Args:
            base_url: Base URL of knowledge graph service
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            verify=False,  # SSL verification disabled for local dev
            timeout=30.0
        )
        logger.info(f"Knowledge Graph Service initialized: {self.base_url}")

    async def health_check(self) -> bool:
        """
        Check if Knowledge Graph service is healthy

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/health"
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Knowledge Graph service health check failed: {e}")
            return False

    async def get_node(
        self,
        node_id: int,
        node_type: str
    ) -> Dict[str, Any]:
        """
        Get a node from the knowledge graph

        Args:
            node_id: ID of the node (e.g., course_id)
            node_type: Type of node (e.g., "course", "skill", "track")

        Returns:
            Node data with id, type, and properties

        Raises:
            httpx.HTTPError: If node not found or API call fails
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/nodes/{node_type}/{node_id}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get node {node_type}/{node_id}: {e}")
            raise

    async def get_prerequisites(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Get prerequisites for a course

        Args:
            course_id: ID of the course

        Returns:
            List of prerequisite courses with course_id, title, and relationship_type
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/courses/{course_id}/prerequisites"
            )
            response.raise_for_status()
            return response.json().get("prerequisites", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to get prerequisites for course {course_id}: {e}")
            return []

    async def get_learning_path(
        self,
        user_id: int,
        target_skill: str
    ) -> Dict[str, Any]:
        """
        Generate a learning path to acquire a target skill

        Uses user's current progress and skill level to create personalized
        learning path with optimal course sequence and difficulty progression.

        Args:
            user_id: ID of the user
            target_skill: Target skill to learn (e.g., "Python Programming")

        Returns:
            Dictionary with courses, total_duration, and difficulty_progression
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/knowledge-graph/learning-paths",
                json={
                    "user_id": user_id,
                    "target_skill": target_skill
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to generate learning path for user {user_id}: {e}")
            return {
                "courses": [],
                "total_duration": 0,
                "difficulty_progression": []
            }

    async def find_related_courses(
        self,
        course_id: int,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find courses related to a given course

        Uses graph relationships and content similarity to find related courses.
        Useful for "You might also like" recommendations.

        Args:
            course_id: ID of the course
            max_results: Maximum number of results to return

        Returns:
            List of related courses with course_id, title, and similarity_score
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/courses/{course_id}/related",
                params={"max_results": max_results}
            )
            response.raise_for_status()
            return response.json().get("related_courses", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to find related courses for {course_id}: {e}")
            return []

    async def check_prerequisites_met(
        self,
        user_id: int,
        course_id: int
    ) -> Dict[str, Any]:
        """
        Check if user meets prerequisites for a course

        Validates user's completed courses against course prerequisites.
        Returns list of missing prerequisites if any.

        Args:
            user_id: ID of the user
            course_id: ID of the course

        Returns:
            Dictionary with prerequisites_met (bool) and missing_prerequisites (list)
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/knowledge-graph/prerequisites/check",
                json={
                    "user_id": user_id,
                    "course_id": course_id
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to check prerequisites for user {user_id}, course {course_id}: {e}")
            return {
                "prerequisites_met": False,
                "missing_prerequisites": []
            }

    async def get_course_sequence(self, track_id: int) -> List[Dict[str, Any]]:
        """
        Get optimal course sequence for a track

        Orders courses based on prerequisites and difficulty progression.
        Ensures prerequisites are satisfied at each step.

        Args:
            track_id: ID of the track

        Returns:
            List of courses in optimal order with course_id, order, and prerequisites_satisfied
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/tracks/{track_id}/sequence"
            )
            response.raise_for_status()
            return response.json().get("sequence", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to get course sequence for track {track_id}: {e}")
            return []

    async def recommend_next_course(
        self,
        user_id: int,
        max_recommendations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Recommend next courses based on user progress

        Analyzes user's completed courses, current skills, and learning goals
        to recommend optimal next courses.

        Args:
            user_id: ID of the user
            max_recommendations: Maximum number of recommendations

        Returns:
            List of recommended courses with course_id, title, relevance_score, and reason
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/users/{user_id}/recommendations",
                params={"max_recommendations": max_recommendations}
            )
            response.raise_for_status()
            return response.json().get("recommendations", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to get recommendations for user {user_id}: {e}")
            return []

    async def get_skill_progression(self, user_id: int) -> Dict[str, Any]:
        """
        Get skill progression for user

        Tracks user's skill development based on completed courses
        and suggests next skills to learn.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary with skills, completed_courses, and recommended_paths
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/users/{user_id}/skills"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get skill progression for user {user_id}: {e}")
            return {
                "skills": [],
                "completed_courses": [],
                "recommended_paths": []
            }

    async def validate_course_sequence(
        self,
        course_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Validate if a course sequence is valid

        Checks if prerequisites are satisfied at each step
        and identifies any ordering issues.

        Args:
            course_ids: List of course IDs in sequence

        Returns:
            Dictionary with is_valid (bool) and issues (list)
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/knowledge-graph/sequences/validate",
                json={"course_ids": course_ids}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to validate course sequence: {e}")
            return {
                "is_valid": False,
                "issues": []
            }

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get knowledge graph statistics

        Returns:
            Dictionary with total_nodes, total_edges, node_types, and edge_types
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/statistics"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "node_types": {},
                "edge_types": {}
            }

    async def search_by_topic(
        self,
        topic: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search courses by topic using graph

        Uses graph relationships and content similarity to find
        courses related to a topic.

        Args:
            topic: Topic to search for (e.g., "Machine Learning")
            max_results: Maximum number of results

        Returns:
            List of courses with course_id, title, and relevance_score
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/search",
                params={
                    "topic": topic,
                    "max_results": max_results
                }
            )
            response.raise_for_status()
            return response.json().get("courses", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to search by topic '{topic}': {e}")
            return []

    async def get_dependencies(
        self,
        course_id: int,
        depth: int = 3
    ) -> Dict[str, Any]:
        """
        Get all course dependencies (deep)

        Traverses graph to find all prerequisites and postrequisites
        up to specified depth.

        Args:
            course_id: ID of the course
            depth: Maximum depth to traverse (default: 3)

        Returns:
            Dictionary with prerequisites, postrequisites, and depth
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/courses/{course_id}/dependencies",
                params={"depth": depth}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get dependencies for course {course_id}: {e}")
            return {
                "prerequisites": [],
                "postrequisites": [],
                "depth": depth
            }

    async def find_shortest_path(
        self,
        user_id: int,
        target_skill: str
    ) -> Dict[str, Any]:
        """
        Find shortest learning path to target skill

        Uses graph algorithms to find minimal course sequence
        to acquire target skill.

        Args:
            user_id: ID of the user
            target_skill: Target skill to learn

        Returns:
            Dictionary with courses, total_duration, and path_length
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/knowledge-graph/paths/shortest",
                json={
                    "user_id": user_id,
                    "target_skill": target_skill
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to find shortest path for user {user_id}: {e}")
            return {
                "courses": [],
                "total_duration": 0,
                "path_length": 0
            }

    async def get_popular_paths(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Get popular learning paths

        Returns most popular learning paths based on enrollment counts.

        Args:
            max_results: Maximum number of paths to return

        Returns:
            List of paths with path_id, title, courses, and enrollment_count
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/knowledge-graph/paths/popular",
                params={"max_results": max_results}
            )
            response.raise_for_status()
            return response.json().get("paths", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to get popular paths: {e}")
            return []

    async def suggest_prerequisites(
        self,
        course_title: str,
        topics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Suggest prerequisites for a new course

        Analyzes course title and topics to recommend appropriate
        prerequisite courses from existing graph.

        Args:
            course_title: Title of new course
            topics: List of topics covered in course

        Returns:
            List of suggested prerequisites with course_id, title, and relevance_score
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/knowledge-graph/prerequisites/suggest",
                json={
                    "course_title": course_title,
                    "topics": topics
                }
            )
            response.raise_for_status()
            return response.json().get("suggestions", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to suggest prerequisites: {e}")
            return []

    async def analyze_course_impact(self, course_id: int) -> Dict[str, Any]:
        """
        Analyze impact of removing a course

        Identifies which courses and users would be affected if
        a course is removed from the catalog.

        Args:
            course_id: ID of the course

        Returns:
            Dictionary with affected_courses, affected_users, and impact_severity
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/knowledge-graph/courses/{course_id}/impact"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to analyze impact for course {course_id}: {e}")
            return {
                "affected_courses": [],
                "affected_users": 0,
                "impact_severity": "unknown"
            }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("Knowledge Graph Service client closed")
