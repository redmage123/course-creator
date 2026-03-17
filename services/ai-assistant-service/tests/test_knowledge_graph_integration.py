"""
TDD RED Phase: Knowledge Graph Service Integration Tests

BUSINESS PURPOSE:
Tests integration between AI Assistant and Knowledge Graph Service.
Ensures course relationships, prerequisites, and learning paths enhance AI responses.

TECHNICAL IMPLEMENTATION:
Tests knowledge graph client, path generation, and prerequisite validation.
"""

import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock

from ai_assistant_service.application.services.knowledge_graph_service import KnowledgeGraphService


@pytest.mark.asyncio
class TestKnowledgeGraphIntegration:
    """Test Knowledge Graph Service integration"""

    @pytest.fixture
    def kg_service(self):
        """Create Knowledge Graph service instance"""
        return KnowledgeGraphService(base_url="https://localhost:8012")

    @pytest.fixture
    def sample_course_id(self):
        """Sample course ID"""
        return 1

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID"""
        return 123

    async def test_service_initialization(self, kg_service):
        """Test Knowledge Graph service initializes correctly"""
        assert kg_service is not None
        assert kg_service.base_url == "https://localhost:8012"
        assert kg_service.client is not None

    async def test_health_check(self, kg_service):
        """Test Knowledge Graph service health check"""
        is_healthy = await kg_service.health_check()
        assert isinstance(is_healthy, bool)

    async def test_get_course_node(self, kg_service, sample_course_id):
        """Test retrieving course node from knowledge graph"""
        node = await kg_service.get_node(
            node_id=sample_course_id,
            node_type="course"
        )

        assert node is not None
        assert "id" in node
        assert "node_type" in node
        assert "properties" in node
        assert node["node_type"] == "course"

    async def test_get_prerequisites(self, kg_service, sample_course_id):
        """Test getting course prerequisites"""
        prerequisites = await kg_service.get_prerequisites(sample_course_id)

        assert isinstance(prerequisites, list)
        for prereq in prerequisites:
            assert "course_id" in prereq
            assert "title" in prereq
            assert "relationship_type" in prereq

    async def test_get_learning_path(self, kg_service, sample_user_id):
        """Test generating learning path for user"""
        target_skill = "Python Programming"

        path = await kg_service.get_learning_path(
            user_id=sample_user_id,
            target_skill=target_skill
        )

        assert path is not None
        assert "courses" in path
        assert "total_duration" in path
        assert "difficulty_progression" in path
        assert isinstance(path["courses"], list)

    async def test_find_related_courses(self, kg_service, sample_course_id):
        """Test finding related courses"""
        related = await kg_service.find_related_courses(
            course_id=sample_course_id,
            max_results=5
        )

        assert isinstance(related, list)
        assert len(related) <= 5
        for course in related:
            assert "course_id" in course
            assert "title" in course
            assert "similarity_score" in course
            assert 0.0 <= course["similarity_score"] <= 1.0

    async def test_check_prerequisites_met(self, kg_service, sample_course_id, sample_user_id):
        """Test checking if user meets course prerequisites"""
        result = await kg_service.check_prerequisites_met(
            user_id=sample_user_id,
            course_id=sample_course_id
        )

        assert isinstance(result, dict)
        assert "prerequisites_met" in result
        assert "missing_prerequisites" in result
        assert isinstance(result["prerequisites_met"], bool)
        assert isinstance(result["missing_prerequisites"], list)

    async def test_get_course_sequence(self, kg_service):
        """Test getting optimal course sequence for a track"""
        track_id = 1

        sequence = await kg_service.get_course_sequence(track_id)

        assert isinstance(sequence, list)
        for item in sequence:
            assert "course_id" in item
            assert "order" in item
            assert "prerequisites_satisfied" in item

    async def test_recommend_next_course(self, kg_service, sample_user_id):
        """Test recommending next course based on progress"""
        recommendations = await kg_service.recommend_next_course(
            user_id=sample_user_id,
            max_recommendations=3
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        for rec in recommendations:
            assert "course_id" in rec
            assert "title" in rec
            assert "relevance_score" in rec
            assert "reason" in rec

    async def test_get_skill_progression(self, kg_service, sample_user_id):
        """Test getting skill progression for user"""
        skill_progression = await kg_service.get_skill_progression(sample_user_id)

        assert isinstance(skill_progression, dict)
        assert "skills" in skill_progression
        assert "completed_courses" in skill_progression
        assert "recommended_paths" in skill_progression

    async def test_validate_course_sequence(self, kg_service):
        """Test validating if course sequence is valid"""
        course_ids = [1, 2, 3]

        validation = await kg_service.validate_course_sequence(course_ids)

        assert isinstance(validation, dict)
        assert "is_valid" in validation
        assert "issues" in validation
        assert isinstance(validation["is_valid"], bool)

    async def test_get_graph_statistics(self, kg_service):
        """Test getting graph statistics"""
        stats = await kg_service.get_statistics()

        assert isinstance(stats, dict)
        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "node_types" in stats
        assert "edge_types" in stats

    async def test_search_courses_by_topic(self, kg_service):
        """Test searching courses by topic using graph"""
        topic = "Machine Learning"

        courses = await kg_service.search_by_topic(
            topic=topic,
            max_results=10
        )

        assert isinstance(courses, list)
        assert len(courses) <= 10
        for course in courses:
            assert "course_id" in course
            assert "title" in course
            assert "relevance_score" in course

    async def test_get_course_dependencies(self, kg_service, sample_course_id):
        """Test getting all course dependencies (deep)"""
        dependencies = await kg_service.get_dependencies(
            course_id=sample_course_id,
            depth=3
        )

        assert isinstance(dependencies, dict)
        assert "prerequisites" in dependencies
        assert "postrequisites" in dependencies
        assert "depth" in dependencies

    async def test_find_shortest_path_to_skill(self, kg_service, sample_user_id):
        """Test finding shortest learning path to target skill"""
        target_skill = "Data Science"

        path = await kg_service.find_shortest_path(
            user_id=sample_user_id,
            target_skill=target_skill
        )

        assert isinstance(path, dict)
        assert "courses" in path
        assert "total_duration" in path
        assert "path_length" in path

    async def test_get_popular_learning_paths(self, kg_service):
        """Test getting popular learning paths"""
        paths = await kg_service.get_popular_paths(max_results=5)

        assert isinstance(paths, list)
        assert len(paths) <= 5
        for path in paths:
            assert "path_id" in path
            assert "title" in path
            assert "courses" in path
            assert "enrollment_count" in path

    async def test_suggest_prerequisites_for_course(self, kg_service):
        """Test suggesting prerequisites for a new course"""
        course_title = "Advanced Deep Learning"
        course_topics = ["neural networks", "tensorflow", "optimization"]

        suggestions = await kg_service.suggest_prerequisites(
            course_title=course_title,
            topics=course_topics
        )

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert "course_id" in suggestion
            assert "title" in suggestion
            assert "relevance_score" in suggestion

    async def test_get_course_impact_analysis(self, kg_service, sample_course_id):
        """Test analyzing impact of removing a course"""
        impact = await kg_service.analyze_course_impact(sample_course_id)

        assert isinstance(impact, dict)
        assert "affected_courses" in impact
        assert "affected_users" in impact
        assert "impact_severity" in impact

    async def test_cache_graph_queries(self, kg_service, sample_course_id):
        """Test caching improves graph query performance"""
        # First call
        result1 = await kg_service.get_node(sample_course_id, "course")

        # Second call (should use cache)
        result2 = await kg_service.get_node(sample_course_id, "course")

        assert result1 == result2

    async def test_error_handling_invalid_node(self, kg_service):
        """Test error handling for non-existent node"""
        with pytest.raises(Exception):
            await kg_service.get_node(node_id=999999, node_type="course")

    async def test_error_handling_service_unavailable(self):
        """Test error handling when service is unavailable"""
        kg_service = KnowledgeGraphService(base_url="https://invalid-url:9999")

        with pytest.raises(httpx.HTTPError):
            await kg_service.health_check()

    async def test_close_client(self, kg_service):
        """Test client closes gracefully"""
        await kg_service.close()
        assert kg_service.client.is_closed
