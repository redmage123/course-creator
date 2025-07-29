"""
Integration Tests for Course Generator Services
Testing service integration and dependency injection following SOLID principles
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from omegaconf import DictConfig

from services.course_generator.infrastructure.container import Container
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

class TestSyllabusGenerationServiceIntegration:
    """Test syllabus generation service integration with dependencies"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'},
            'server': {'host': '0.0.0.0', 'port': 8001}
        })
    
    @pytest.fixture
    def mock_container(self, mock_config):
        """Create container with mocked dependencies"""
        container = Container(mock_config)
        
        # Mock the repositories and services
        container._syllabus_repository = AsyncMock()
        container._ai_service = AsyncMock()
        container._prompt_service = Mock()
        
        return container
    
    @pytest.fixture
    def syllabus_service(self, mock_container):
        """Create syllabus service with mocked dependencies"""
        return mock_container.get_syllabus_generation_service()
    
    @pytest.mark.asyncio
    async def test_generate_syllabus_integration(self, syllabus_service, mock_container):
        """Test complete syllabus generation workflow"""
        # Setup mocks
        mock_container._syllabus_repository.get_by_course_id.return_value = None  # No existing syllabus
        mock_container._prompt_service.get_prompt_template.return_value = "Generate syllabus for {title}"
        mock_container._prompt_service.render_prompt.return_value = "Generate syllabus for Test Course"
        
        # Mock AI service response
        mock_ai_response = {
            'learning_objectives': [
                'Understand basic concepts',
                'Apply knowledge practically'
            ],
            'topics': [
                {
                    'name': 'Introduction',
                    'duration_hours': 2,
                    'subtopics': ['Overview', 'Setup']
                }
            ],
            'prerequisites': ['Basic knowledge'],
            'resources': [
                {
                    'title': 'Textbook',
                    'type': 'book',
                    'description': 'Main reference'
                }
            ],
            'assessment_methods': ['Quiz', 'Project']
        }
        mock_container._ai_service.generate_structured_content.return_value = mock_ai_response
        
        # Mock repository save
        saved_syllabus = Syllabus(
            course_id="course_123",
            title="Test Course",
            description="Test Description",
            category="Programming",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_duration=40
        )
        saved_syllabus.learning_objectives = mock_ai_response['learning_objectives']
        saved_syllabus.topics = mock_ai_response['topics']
        mock_container._syllabus_repository.create.return_value = saved_syllabus
        
        # Execute service method
        result = await syllabus_service.generate_syllabus(
            course_id="course_123",
            title="Test Course",
            description="Test Description",
            category="Programming",
            difficulty_level="beginner",
            estimated_duration=40
        )
        
        # Verify results
        assert result.course_id == "course_123"
        assert result.title == "Test Course"
        assert result.difficulty_level == DifficultyLevel.BEGINNER
        assert len(result.learning_objectives) == 2
        assert len(result.topics) == 1
        
        # Verify mock interactions
        mock_container._syllabus_repository.get_by_course_id.assert_called_once_with("course_123")
        mock_container._ai_service.generate_structured_content.assert_called_once()
        mock_container._syllabus_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_syllabus_duplicate_course(self, syllabus_service, mock_container):
        """Test syllabus generation with existing course"""
        # Setup existing syllabus
        existing_syllabus = Syllabus(
            course_id="course_123",
            title="Existing Course",
            description="Existing Description",
            category="Programming",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_duration=40
        )
        mock_container._syllabus_repository.get_by_course_id.return_value = existing_syllabus
        
        # Should raise ValueError for duplicate
        with pytest.raises(ValueError, match="Syllabus already exists for course course_123"):
            await syllabus_service.generate_syllabus(
                course_id="course_123",
                title="Test Course",
                description="Test Description",
                category="Programming",
                difficulty_level="beginner",
                estimated_duration=40
            )
    
    @pytest.mark.asyncio
    async def test_analyze_syllabus_content_integration(self, syllabus_service, mock_container):
        """Test syllabus content analysis workflow"""
        # Setup mocks
        mock_container._prompt_service.get_prompt_template.return_value = "Analyze content: {content}"
        mock_container._prompt_service.render_prompt.return_value = "Analyze content: Course syllabus text"
        
        # Mock AI analysis response
        mock_analysis_response = {
            'extracted_title': 'Advanced Python Programming',
            'extracted_description': 'Learn advanced Python concepts',
            'estimated_difficulty': 'advanced',
            'estimated_duration': 60,
            'learning_objectives': [
                'Master advanced Python features',
                'Build complex applications'
            ],
            'topics': [
                {'name': 'Decorators', 'duration_hours': 8},
                {'name': 'Metaclasses', 'duration_hours': 6}
            ],
            'prerequisites': ['Intermediate Python'],
            'subject_category': 'Programming',
            'quality_score': 0.85
        }
        mock_container._ai_service.generate_structured_content.return_value = mock_analysis_response
        
        # Execute analysis
        result = await syllabus_service.analyze_syllabus_content("Course syllabus text content")
        
        # Verify results
        assert result['extracted_title'] == 'Advanced Python Programming'
        assert result['estimated_difficulty'] == 'advanced'
        assert result['quality_score'] == 0.85
        assert len(result['learning_objectives']) == 2
        
        # Verify mock interactions
        mock_container._prompt_service.get_prompt_template.assert_called_once()
        mock_container._ai_service.generate_structured_content.assert_called_once()

class TestQuizGenerationServiceIntegration:
    """Test quiz generation service integration with dependencies"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.fixture
    def mock_container(self, mock_config):
        """Create container with mocked dependencies"""
        container = Container(mock_config)
        
        # Mock the repositories and services
        container._quiz_repository = AsyncMock()
        container._quiz_attempt_repository = AsyncMock()
        container._ai_service = AsyncMock()
        container._prompt_service = Mock()
        
        return container
    
    @pytest.fixture
    def quiz_service(self, mock_container):
        """Create quiz service with mocked dependencies"""
        return mock_container.get_quiz_generation_service()
    
    @pytest.mark.asyncio
    async def test_generate_quiz_integration(self, quiz_service, mock_container):
        """Test complete quiz generation workflow"""
        # Setup mocks
        mock_container._prompt_service.get_prompt_template.return_value = "Generate {question_count} questions about {topic}"
        mock_container._prompt_service.render_prompt.return_value = "Generate 5 questions about Python basics"
        
        # Mock AI service response
        mock_ai_response = {
            'questions': [
                {
                    'question': 'What is Python?',
                    'options': ['Programming Language', 'Snake', 'Tool', 'Framework'],
                    'correct_answer': 0,
                    'explanation': 'Python is a programming language',
                    'points': 1
                },
                {
                    'question': 'What is a variable?',
                    'options': ['Container', 'Function', 'Loop', 'Class'],
                    'correct_answer': 0,
                    'explanation': 'A variable is a container for data',
                    'points': 1
                }
            ]
        }
        mock_container._ai_service.generate_structured_content.return_value = mock_ai_response
        
        # Mock repository save
        saved_quiz = Quiz(
            course_id="course_123",
            title="Python Basics Quiz",
            topic="Python basics",
            difficulty="beginner",
            questions=[]  # Will be populated by service
        )
        mock_container._quiz_repository.create.return_value = saved_quiz
        
        # Create quiz generation request
        request = QuizGenerationRequest(
            course_id="course_123",
            topic="Python basics",
            difficulty="beginner",
            question_count=5,
            difficulty_level="beginner",
            instructor_context={},
            student_tracking={}
        )
        
        # Execute service method
        result = await quiz_service.generate_quiz(request)
        
        # Verify results
        assert result.course_id == "course_123"
        assert result.topic == "Python basics"
        assert result.difficulty == "beginner"
        
        # Verify mock interactions
        mock_container._ai_service.generate_structured_content.assert_called_once()
        mock_container._quiz_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_adaptive_quiz_integration(self, quiz_service, mock_container):
        """Test adaptive quiz generation workflow"""
        # Setup student progress data
        student_progress = {
            'completed_exercises': 8,
            'total_exercises': 10,
            'quiz_scores': [85.0, 90.0, 78.0],
            'current_level': 'intermediate',
            'knowledge_areas': ['variables', 'functions']
        }
        
        context = {
            'instructor_context': {'focus_areas': ['advanced_topics']}
        }
        
        # Setup mocks
        mock_container._prompt_service.get_prompt_template.return_value = "Generate adaptive quiz for {topic}"
        mock_container._prompt_service.render_prompt.return_value = "Generate adaptive quiz for functions"
        
        # Mock AI response for adaptive quiz
        mock_ai_response = {
            'questions': [
                {
                    'question': 'What is a lambda function?',
                    'options': ['Anonymous function', 'Named function', 'Class method', 'Variable'],
                    'correct_answer': 0,
                    'explanation': 'Lambda functions are anonymous functions',
                    'points': 2
                }
            ]
        }
        mock_container._ai_service.generate_structured_content.return_value = mock_ai_response
        
        # Mock repository save
        adaptive_quiz = Quiz(
            course_id="course_123",
            title="Adaptive Quiz - functions",
            topic="functions",
            difficulty="intermediate",
            questions=[]
        )
        mock_container._quiz_repository.create.return_value = adaptive_quiz
        
        # Execute adaptive quiz generation
        result = await quiz_service.generate_adaptive_quiz("course_123", student_progress, context)
        
        # Verify adaptive parameters were used
        assert result.course_id == "course_123"
        assert result.difficulty == "intermediate"  # Should adapt based on performance
        
        # Verify mock interactions
        mock_container._quiz_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_quiz_answers_integration(self, quiz_service):
        """Test quiz answer validation workflow"""
        # Create quiz with questions
        questions = [
            QuizQuestion(
                question="What is 2+2?",
                options=["3", "4", "5", "6"],
                correct_answer=1,
                points=2
            ),
            QuizQuestion(
                question="What is 3*3?",
                options=["6", "9", "12", "15"],
                correct_answer=1,
                points=3
            )
        ]
        
        quiz = Quiz(
            course_id="course_123",
            title="Math Quiz",
            topic="Arithmetic",
            difficulty="beginner",
            questions=questions,
            passing_score=60
        )
        
        # Test validation with correct answers
        answers = [1, 1]  # Both correct
        result = await quiz_service.validate_quiz_answers(quiz, answers)
        
        # Verify results
        assert result['total_questions'] == 2
        assert result['correct_answers'] == 2
        assert result['score_percentage'] == 100.0
        assert result['passed'] == True
        assert len(result['detailed_results']) == 2
        
        # Test validation with partial correct answers
        answers = [1, 0]  # First correct, second wrong
        result = await quiz_service.validate_quiz_answers(quiz, answers)
        
        assert result['correct_answers'] == 1
        assert result['score_percentage'] == 40.0  # 2 out of 5 points
        assert result['passed'] == False  # Below 60% passing score

class TestContainerIntegration:
    """Test dependency injection container integration"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.mark.asyncio
    async def test_container_initialization(self, mock_config):
        """Test container initialization and cleanup"""
        container = Container(mock_config)
        
        # Mock the database connection
        container._connection_pool = AsyncMock()
        
        await container.initialize()
        assert container._connection_pool is not None
        
        await container.cleanup()
    
    def test_container_service_creation(self, mock_config):
        """Test container creates services correctly"""
        container = Container(mock_config)
        
        # Test service creation
        syllabus_service = container.get_syllabus_generation_service()
        assert isinstance(syllabus_service, SyllabusGenerationService)
        
        quiz_service = container.get_quiz_generation_service()
        assert isinstance(quiz_service, QuizGenerationService)
        
        # Test singleton behavior
        syllabus_service2 = container.get_syllabus_generation_service()
        assert syllabus_service is syllabus_service2
    
    def test_container_repository_creation(self, mock_config):
        """Test container creates repositories correctly"""
        container = Container(mock_config)
        
        # Test repository creation
        syllabus_repo = container.get_syllabus_repository()
        assert syllabus_repo is not None
        
        quiz_repo = container.get_quiz_repository()
        assert quiz_repo is not None
        
        # Test singleton behavior
        syllabus_repo2 = container.get_syllabus_repository()
        assert syllabus_repo is syllabus_repo2
    
    def test_container_ai_service_creation(self, mock_config):
        """Test container creates AI services correctly"""
        container = Container(mock_config)
        
        # Test AI service creation
        ai_service = container.get_ai_service()
        assert ai_service is not None
        
        prompt_service = container.get_prompt_service()
        assert prompt_service is not None
        
        # Test singleton behavior
        ai_service2 = container.get_ai_service()
        assert ai_service is ai_service2

class TestCrossServiceIntegration:
    """Test integration between different services"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.fixture
    def container_with_mocks(self, mock_config):
        """Create container with mocked external dependencies"""
        container = Container(mock_config)
        
        # Mock all repositories
        container._syllabus_repository = AsyncMock()
        container._quiz_repository = AsyncMock()
        container._exercise_repository = AsyncMock()
        container._ai_service = AsyncMock()
        container._prompt_service = Mock()
        
        return container
    
    @pytest.mark.asyncio
    async def test_syllabus_to_quiz_workflow(self, container_with_mocks):
        """Test workflow from syllabus creation to quiz generation"""
        # Step 1: Create syllabus
        syllabus_service = container_with_mocks.get_syllabus_generation_service()
        
        # Mock syllabus creation
        container_with_mocks._syllabus_repository.get_by_course_id.return_value = None
        container_with_mocks._prompt_service.get_prompt_template.return_value = "Generate syllabus"
        container_with_mocks._prompt_service.render_prompt.return_value = "Generate syllabus for course"
        
        syllabus_ai_response = {
            'learning_objectives': ['Learn Python basics'],
            'topics': [{'name': 'Variables', 'duration_hours': 4}],
            'prerequisites': [],
            'resources': [],
            'assessment_methods': ['Quiz']
        }
        container_with_mocks._ai_service.generate_structured_content.return_value = syllabus_ai_response
        
        created_syllabus = Syllabus(
            course_id="course_123",
            title="Python Basics",
            description="Learn Python fundamentals",
            category="Programming",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_duration=40
        )
        container_with_mocks._syllabus_repository.create.return_value = created_syllabus
        
        syllabus = await syllabus_service.generate_syllabus(
            course_id="course_123",
            title="Python Basics",
            description="Learn Python fundamentals",
            category="Programming",
            difficulty_level="beginner",
            estimated_duration=40
        )
        
        # Step 2: Generate quiz based on syllabus
        quiz_service = container_with_mocks.get_quiz_generation_service()
        
        # Mock quiz generation
        quiz_ai_response = {
            'questions': [
                {
                    'question': 'What is a Python variable?',
                    'options': ['Container', 'Function', 'Loop', 'Class'],
                    'correct_answer': 0,
                    'explanation': 'Variables store data',
                    'points': 1
                }
            ]
        }
        container_with_mocks._ai_service.generate_structured_content.return_value = quiz_ai_response
        
        created_quiz = Quiz(
            course_id="course_123",
            title="Variables Quiz",
            topic="Variables",
            difficulty="beginner",
            questions=[]
        )
        container_with_mocks._quiz_repository.create.return_value = created_quiz
        
        quiz_request = QuizGenerationRequest(
            course_id="course_123",
            topic="Variables",  # From syllabus topic
            difficulty="beginner",
            question_count=5,
            difficulty_level="beginner",
            instructor_context={'syllabus_context': syllabus.learning_objectives},
            student_tracking={}
        )
        
        quiz = await quiz_service.generate_quiz(quiz_request)
        
        # Verify the workflow worked
        assert syllabus.course_id == quiz.course_id
        assert syllabus.difficulty_level.value == quiz.difficulty
        
        # Both services should have been called
        container_with_mocks._syllabus_repository.create.assert_called_once()
        container_with_mocks._quiz_repository.create.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])