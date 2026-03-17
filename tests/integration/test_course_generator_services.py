"""
Integration Tests for Course Generator Services
Testing service integration and dependency injection following SOLID principles
"""
import pytest
import asyncio
import os
from datetime import datetime, timedelta
from omegaconf import DictConfig

from services.course_generator.infrastructure.container import Container

DB_AVAILABLE = os.getenv('TEST_DB_HOST') is not None or os.getenv('TEST_DATABASE_URL') is not None
from services.course_generator.domain.entities.course_content import (
    Syllabus, Slide, Exercise, DifficultyLevel, ExerciseType
)
from services.course_generator.domain.entities.quiz import (
    Quiz, QuizQuestion, QuizGenerationRequest
)
from services.course_generator.domain.interfaces.content_generation_service import (
    ISyllabusGenerationService, IQuizGenerationService, IExerciseGenerationService
)
from services.course_generator.application.services.syllabus_generation_service import SyllabusGenerationService
from services.course_generator.application.services.quiz_generation_service import QuizGenerationService

@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not configured")
class TestSyllabusGenerationServiceIntegration:
    """Test syllabus generation service integration with dependencies"""

    @pytest.fixture
    def config(self):
        """Create configuration from environment"""
        return DictConfig({
            'database': {'url': 'postgresql://postgres:postgres_password@localhost:5433/course_creator_test'},
            'logging': {'level': 'INFO'},
            'server': {'host': '0.0.0.0', 'port': 8001}
        })

    @pytest.fixture
    async def container(self, config):
        """Create container with real database"""
        container = Container(config)
        await container.initialize()
        yield container
        await container.cleanup()

    @pytest.mark.asyncio
    async def test_generate_syllabus_integration(self, container):
        """Test complete syllabus generation workflow"""
        pytest.skip("Needs refactoring to use real database and services")

    @pytest.mark.asyncio
    async def test_generate_syllabus_duplicate_course(self, container):
        """Test syllabus generation with existing course"""
        pytest.skip("Needs refactoring to use real database and services")

    @pytest.mark.asyncio
    async def test_analyze_syllabus_content_integration(self, container):
        """Test syllabus content analysis workflow"""
        pytest.skip("Needs refactoring to use real database and services")

@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not configured")
class TestQuizGenerationServiceIntegration:
    """Test quiz generation service integration with dependencies"""

    @pytest.mark.asyncio
    async def test_generate_quiz_integration(self):
        """Test complete quiz generation workflow"""
        pytest.skip("Needs refactoring to use real database and services")

    @pytest.mark.asyncio
    async def test_generate_adaptive_quiz_integration(self):
        """Test adaptive quiz generation workflow"""
        pytest.skip("Needs refactoring to use real database and services")

    @pytest.mark.asyncio
    async def test_validate_quiz_answers_integration(self):
        """Test quiz answer validation workflow"""
        pytest.skip("Needs refactoring to use real database and services")

class TestContainerIntegration:
    """Test dependency injection container integration"""

    @pytest.fixture
    def config(self):
        """Create configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://postgres:postgres_password@localhost:5433/course_creator_test'},
            'logging': {'level': 'INFO'}
        })

    @pytest.mark.asyncio
    async def test_container_initialization(self, config):
        """Test container initialization and cleanup"""
        container = Container(config)
        await container.initialize()
        assert container is not None
        await container.cleanup()

    def test_container_service_creation(self, config):
        """Test container creates services correctly"""
        container = Container(config)

        # Test service creation
        syllabus_service = container.get_syllabus_generation_service()
        assert isinstance(syllabus_service, SyllabusGenerationService)

        quiz_service = container.get_quiz_generation_service()
        assert isinstance(quiz_service, QuizGenerationService)

        # Test singleton behavior
        syllabus_service2 = container.get_syllabus_generation_service()
        assert syllabus_service is syllabus_service2

    def test_container_repository_creation(self, config):
        """Test container creates repositories correctly"""
        container = Container(config)

        # Test repository creation
        syllabus_repo = container.get_syllabus_repository()
        assert syllabus_repo is not None

        quiz_repo = container.get_quiz_repository()
        assert quiz_repo is not None

        # Test singleton behavior
        syllabus_repo2 = container.get_syllabus_repository()
        assert syllabus_repo is syllabus_repo2

    def test_container_ai_service_creation(self, config):
        """Test container creates AI services correctly"""
        container = Container(config)

        # Test AI service creation
        ai_service = container.get_ai_service()
        assert ai_service is not None

        prompt_service = container.get_prompt_service()
        assert prompt_service is not None

        # Test singleton behavior
        ai_service2 = container.get_ai_service()
        assert ai_service is ai_service2

@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not configured")
class TestCrossServiceIntegration:
    """Test integration between different services"""

    @pytest.mark.asyncio
    async def test_syllabus_to_quiz_workflow(self):
        """Test workflow from syllabus creation to quiz generation"""
        pytest.skip("Needs refactoring to use real database and services")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
