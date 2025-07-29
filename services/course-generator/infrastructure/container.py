"""
Dependency Injection Container for Course Generator Service
Single Responsibility: Wire up dependencies and manage service lifetimes
Dependency Inversion: Configure concrete implementations for abstract interfaces
"""
import asyncpg
from typing import Optional
from omegaconf import DictConfig

# Domain interfaces
from ..domain.interfaces.content_generation_service import (
    ISyllabusGenerationService, ISlideGenerationService, IExerciseGenerationService,
    IQuizGenerationService, ILabEnvironmentService, IChatService, 
    IProgressTrackingService, IJobManagementService, ILabSessionService
)
from ..domain.interfaces.ai_service import (
    IAIService, IPromptTemplateService, IAIFallbackService, 
    IContentValidationService, IAIConfigurationService
)
from ..domain.interfaces.content_repository import (
    ISyllabusRepository, ISlideRepository, IExerciseRepository, 
    IQuizRepository, IQuizAttemptRepository, ILabEnvironmentRepository,
    IStudentProgressRepository, IChatInteractionRepository, 
    ILabSessionRepository, IGenerationJobRepository
)

# Application services
from ..application.services.syllabus_generation_service import SyllabusGenerationService
from ..application.services.quiz_generation_service import QuizGenerationService

# Infrastructure implementations (these would need to be implemented)
# from ..infrastructure.ai.anthropic_ai_service import AnthropicAIService
# from ..infrastructure.ai.prompt_template_service import PromptTemplateService
# from ..infrastructure.repositories.postgresql_syllabus_repository import PostgreSQLSyllabusRepository
# etc.

class Container:
    """
    Dependency injection container following SOLID principles
    """
    
    def __init__(self, config: DictConfig):
        self._config = config
        self._connection_pool: Optional[asyncpg.Pool] = None
        
        # Service instances (singletons)
        self._ai_service: Optional[IAIService] = None
        self._prompt_service: Optional[IPromptTemplateService] = None
        
        # Repository instances
        self._syllabus_repository: Optional[ISyllabusRepository] = None
        self._quiz_repository: Optional[IQuizRepository] = None
        self._quiz_attempt_repository: Optional[IQuizAttemptRepository] = None
        self._slide_repository: Optional[ISlideRepository] = None
        self._exercise_repository: Optional[IExerciseRepository] = None
        self._lab_environment_repository: Optional[ILabEnvironmentRepository] = None
        self._student_progress_repository: Optional[IStudentProgressRepository] = None
        self._chat_interaction_repository: Optional[IChatInteractionRepository] = None
        self._lab_session_repository: Optional[ILabSessionRepository] = None
        self._generation_job_repository: Optional[IGenerationJobRepository] = None
        
        # Application service instances
        self._syllabus_generation_service: Optional[ISyllabusGenerationService] = None
        self._quiz_generation_service: Optional[IQuizGenerationService] = None
        self._slide_generation_service: Optional[ISlideGenerationService] = None
        self._exercise_generation_service: Optional[IExerciseGenerationService] = None
        self._lab_environment_service: Optional[ILabEnvironmentService] = None
        self._chat_service: Optional[IChatService] = None
        self._progress_tracking_service: Optional[IProgressTrackingService] = None
        self._job_management_service: Optional[IJobManagementService] = None
        self._lab_session_service: Optional[ILabSessionService] = None
    
    async def initialize(self) -> None:
        """Initialize the container and create database connections"""
        # Create database connection pool
        self._connection_pool = await asyncpg.create_pool(
            self._config.database.url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._connection_pool:
            await self._connection_pool.close()
    
    # AI Service factories
    def get_ai_service(self) -> IAIService:
        """Get AI service instance"""
        if not self._ai_service:
            # For now, return a mock implementation
            # In production, this would be:
            # self._ai_service = AnthropicAIService(self._config.ai)
            self._ai_service = MockAIService()
        
        return self._ai_service
    
    def get_prompt_service(self) -> IPromptTemplateService:
        """Get prompt template service instance"""
        if not self._prompt_service:
            # For now, return a mock implementation
            # In production, this would be:
            # self._prompt_service = PromptTemplateService(self._config.prompts)
            self._prompt_service = MockPromptTemplateService()
        
        return self._prompt_service
    
    # Repository factories
    def get_syllabus_repository(self) -> ISyllabusRepository:
        """Get syllabus repository instance"""
        if not self._syllabus_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            # For now, return a mock implementation
            # In production, this would be:
            # self._syllabus_repository = PostgreSQLSyllabusRepository(self._connection_pool)
            self._syllabus_repository = MockSyllabusRepository()
        
        return self._syllabus_repository
    
    def get_quiz_repository(self) -> IQuizRepository:
        """Get quiz repository instance"""
        if not self._quiz_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            # For now, return a mock implementation
            self._quiz_repository = MockQuizRepository()
        
        return self._quiz_repository
    
    def get_quiz_attempt_repository(self) -> IQuizAttemptRepository:
        """Get quiz attempt repository instance"""
        if not self._quiz_attempt_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            # For now, return a mock implementation
            self._quiz_attempt_repository = MockQuizAttemptRepository()
        
        return self._quiz_attempt_repository
    
    # Application service factories
    def get_syllabus_generation_service(self) -> ISyllabusGenerationService:
        """Get syllabus generation service instance"""
        if not self._syllabus_generation_service:
            self._syllabus_generation_service = SyllabusGenerationService(
                syllabus_repository=self.get_syllabus_repository(),
                ai_service=self.get_ai_service(),
                prompt_service=self.get_prompt_service()
            )
        
        return self._syllabus_generation_service
    
    def get_quiz_generation_service(self) -> IQuizGenerationService:
        """Get quiz generation service instance"""
        if not self._quiz_generation_service:
            self._quiz_generation_service = QuizGenerationService(
                quiz_repository=self.get_quiz_repository(),
                quiz_attempt_repository=self.get_quiz_attempt_repository(),
                ai_service=self.get_ai_service(),
                prompt_service=self.get_prompt_service()
            )
        
        return self._quiz_generation_service


# Mock implementations for demonstration (would be replaced with real implementations)
from ..domain.interfaces.ai_service import IAIService, IPromptTemplateService, ContentGenerationType
from ..domain.interfaces.content_repository import ISyllabusRepository, IQuizRepository, IQuizAttemptRepository

class MockAIService(IAIService):
    """Mock AI service for demonstration"""
    
    async def generate_content(self, content_type, prompt, context=None, model=None):
        return f"Mock AI generated content for {content_type.value}"
    
    async def generate_structured_content(self, content_type, prompt, schema, context=None, model=None):
        if content_type == ContentGenerationType.SYLLABUS:
            return {
                "learning_objectives": ["Understand basic concepts", "Apply knowledge practically"],
                "topics": [
                    {"name": "Introduction", "duration_hours": 2, "subtopics": ["Overview", "Setup"]},
                    {"name": "Advanced Topics", "duration_hours": 4, "subtopics": ["Deep dive", "Examples"]}
                ],
                "prerequisites": ["Basic knowledge"],
                "resources": [{"title": "Textbook", "type": "book", "description": "Main reference"}],
                "assessment_methods": ["Quiz", "Project"]
            }
        elif content_type == ContentGenerationType.QUIZ:
            return {
                "questions": [
                    {
                        "question": "What is the main concept?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": 0,
                        "explanation": "Option A is correct because...",
                        "points": 1
                    }
                ]
            }
        return {}
    
    async def chat_completion(self, messages, context=None, model=None):
        return "Mock AI chat response"
    
    async def analyze_text(self, text, analysis_type, context=None):
        return {"sentiment": "positive", "topics": ["education", "learning"]}
    
    async def validate_content(self, content, content_type, validation_criteria=None):
        return {"is_valid": True, "quality_score": 0.8}
    
    def get_available_models(self):
        from ..domain.interfaces.ai_service import AIModel
        return [AIModel.MOCK_MODEL]
    
    def get_provider_info(self):
        return {"provider": "mock", "version": "1.0"}
    
    async def test_connection(self):
        return True


class MockPromptTemplateService(IPromptTemplateService):
    """Mock prompt template service for demonstration"""
    
    def get_prompt_template(self, content_type, template_name="default"):
        templates = {
            ContentGenerationType.SYLLABUS: "Generate a comprehensive syllabus for {title} with {description}",
            ContentGenerationType.QUIZ: "Generate {question_count} questions about {topic} at {difficulty} level"
        }
        return templates.get(content_type, "Generate content for {content_type}")
    
    def render_prompt(self, template, variables):
        for key, value in variables.items():
            if isinstance(value, dict):
                continue  # Skip complex objects
            template = template.replace(f"{{{key}}}", str(value))
        return template
    
    def validate_template_variables(self, template, variables):
        return True
    
    def get_available_templates(self, content_type):
        return ["default", "comprehensive", "basic"]


class MockSyllabusRepository(ISyllabusRepository):
    """Mock syllabus repository for demonstration"""
    
    def __init__(self):
        self._syllabi = {}
    
    async def create(self, syllabus):
        self._syllabi[syllabus.id] = syllabus
        return syllabus
    
    async def get_by_id(self, syllabus_id):
        return self._syllabi.get(syllabus_id)
    
    async def get_by_course_id(self, course_id):
        for syllabus in self._syllabi.values():
            if syllabus.course_id == course_id:
                return syllabus
        return None
    
    async def update(self, syllabus):
        self._syllabi[syllabus.id] = syllabus
        return syllabus
    
    async def delete(self, syllabus_id):
        return self._syllabi.pop(syllabus_id, None) is not None
    
    async def search(self, query, filters=None):
        return list(self._syllabi.values())


class MockQuizRepository(IQuizRepository):
    """Mock quiz repository for demonstration"""
    
    def __init__(self):
        self._quizzes = {}
    
    async def create(self, quiz):
        self._quizzes[quiz.id] = quiz
        return quiz
    
    async def get_by_id(self, quiz_id):
        return self._quizzes.get(quiz_id)
    
    async def get_by_course_id(self, course_id):
        return [q for q in self._quizzes.values() if q.course_id == course_id]
    
    async def get_by_topic(self, course_id, topic):
        return [q for q in self._quizzes.values() if q.course_id == course_id and q.topic == topic]
    
    async def update(self, quiz):
        self._quizzes[quiz.id] = quiz
        return quiz
    
    async def delete(self, quiz_id):
        return self._quizzes.pop(quiz_id, None) is not None
    
    async def get_quiz_statistics(self, quiz_id):
        return {"total_attempts": 0, "average_score": 0.0}


class MockQuizAttemptRepository(IQuizAttemptRepository):
    """Mock quiz attempt repository for demonstration"""
    
    def __init__(self):
        self._attempts = {}
    
    async def create(self, attempt):
        self._attempts[attempt.id] = attempt
        return attempt
    
    async def get_by_id(self, attempt_id):
        return self._attempts.get(attempt_id)
    
    async def get_by_student_and_quiz(self, student_id, quiz_id):
        return [a for a in self._attempts.values() if a.student_id == student_id and a.quiz_id == quiz_id]
    
    async def get_by_student_and_course(self, student_id, course_id):
        return [a for a in self._attempts.values() if a.student_id == student_id and a.course_id == course_id]
    
    async def update(self, attempt):
        self._attempts[attempt.id] = attempt
        return attempt
    
    async def get_attempt_statistics(self, quiz_id):
        return {"total_attempts": 0, "average_score": 0.0}