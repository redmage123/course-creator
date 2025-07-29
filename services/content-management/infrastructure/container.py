"""
Content Management Dependency Injection Container
Single Responsibility: Wire up dependencies and manage service lifetimes
Dependency Inversion: Configure concrete implementations for abstract interfaces
"""
import asyncpg
from typing import Optional
from omegaconf import DictConfig

# Domain interfaces
from ..domain.interfaces.content_repository import (
    ISyllabusRepository, ISlideRepository, IQuizRepository,
    IExerciseRepository, ILabEnvironmentRepository, IContentSearchRepository
)
from ..domain.interfaces.content_service import (
    ISyllabusService, ISlideService, IQuizService, IExerciseService,
    ILabEnvironmentService, IContentSearchService, IContentValidationService,
    IContentAnalyticsService, IContentExportService
)

# Application services
from ..application.services.syllabus_service import SyllabusService
from ..application.services.content_validation_service import ContentValidationService
from ..application.services.content_search_service import ContentSearchService

# Infrastructure implementations (we'll create mock implementations for now)
from .repositories.postgresql_content_repository import (
    PostgreSQLSyllabusRepository, PostgreSQLSlideRepository,
    PostgreSQLQuizRepository, PostgreSQLExerciseRepository,
    PostgreSQLLabEnvironmentRepository, PostgreSQLContentSearchRepository
)


class ContentManagementContainer:
    """
    Dependency injection container following SOLID principles
    """
    
    def __init__(self, config: DictConfig):
        self._config = config
        self._connection_pool: Optional[asyncpg.Pool] = None
        
        # Repository instances (singletons)
        self._syllabus_repository: Optional[ISyllabusRepository] = None
        self._slide_repository: Optional[ISlideRepository] = None
        self._quiz_repository: Optional[IQuizRepository] = None
        self._exercise_repository: Optional[IExerciseRepository] = None
        self._lab_environment_repository: Optional[ILabEnvironmentRepository] = None
        self._content_search_repository: Optional[IContentSearchRepository] = None
        
        # Service instances (singletons)
        self._syllabus_service: Optional[ISyllabusService] = None
        self._slide_service: Optional[ISlideService] = None
        self._quiz_service: Optional[IQuizService] = None
        self._exercise_service: Optional[IExerciseService] = None
        self._lab_environment_service: Optional[ILabEnvironmentService] = None
        self._content_search_service: Optional[IContentSearchService] = None
        self._content_validation_service: Optional[IContentValidationService] = None
        self._content_analytics_service: Optional[IContentAnalyticsService] = None
        self._content_export_service: Optional[IContentExportService] = None
    
    async def initialize(self) -> None:
        """Initialize the container and create database connections"""
        # Create database connection pool
        database_url = getattr(self._config, 'database_url', 
                             "postgresql://course_user:c0urs3:atao12e@localhost:5433/course_creator")
        
        self._connection_pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._connection_pool:
            await self._connection_pool.close()
    
    # Repository factories (following Dependency Inversion)
    def get_syllabus_repository(self) -> ISyllabusRepository:
        """Get syllabus repository instance"""
        if not self._syllabus_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            self._syllabus_repository = PostgreSQLSyllabusRepository(self._connection_pool)
        
        return self._syllabus_repository
    
    def get_slide_repository(self) -> ISlideRepository:
        """Get slide repository instance"""
        if not self._slide_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            self._slide_repository = PostgreSQLSlideRepository(self._connection_pool)
        
        return self._slide_repository
    
    def get_quiz_repository(self) -> IQuizRepository:
        """Get quiz repository instance"""
        if not self._quiz_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            self._quiz_repository = PostgreSQLQuizRepository(self._connection_pool)
        
        return self._quiz_repository
    
    def get_exercise_repository(self) -> IExerciseRepository:
        """Get exercise repository instance"""
        if not self._exercise_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            self._exercise_repository = PostgreSQLExerciseRepository(self._connection_pool)
        
        return self._exercise_repository
    
    def get_lab_environment_repository(self) -> ILabEnvironmentRepository:
        """Get lab environment repository instance"""
        if not self._lab_environment_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            self._lab_environment_repository = PostgreSQLLabEnvironmentRepository(self._connection_pool)
        
        return self._lab_environment_repository
    
    def get_content_search_repository(self) -> IContentSearchRepository:
        """Get content search repository instance"""
        if not self._content_search_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            self._content_search_repository = PostgreSQLContentSearchRepository(self._connection_pool)
        
        return self._content_search_repository
    
    # Service factories (following Dependency Inversion)
    def get_content_validation_service(self) -> IContentValidationService:
        """Get content validation service instance"""
        if not self._content_validation_service:
            self._content_validation_service = ContentValidationService()
        
        return self._content_validation_service
    
    def get_syllabus_service(self) -> ISyllabusService:
        """Get syllabus service instance"""
        if not self._syllabus_service:
            self._syllabus_service = SyllabusService(
                syllabus_repository=self.get_syllabus_repository(),
                validation_service=self.get_content_validation_service()
            )
        
        return self._syllabus_service
    
    def get_slide_service(self) -> ISlideService:
        """Get slide service instance"""
        if not self._slide_service:
            # For now, return a mock implementation
            # In a complete implementation, this would be:
            # self._slide_service = SlideService(
            #     slide_repository=self.get_slide_repository(),
            #     validation_service=self.get_content_validation_service()
            # )
            self._slide_service = MockSlideService()
        
        return self._slide_service
    
    def get_quiz_service(self) -> IQuizService:
        """Get quiz service instance"""
        if not self._quiz_service:
            # For now, return a mock implementation
            self._quiz_service = MockQuizService()
        
        return self._quiz_service
    
    def get_exercise_service(self) -> IExerciseService:
        """Get exercise service instance"""
        if not self._exercise_service:
            # For now, return a mock implementation
            self._exercise_service = MockExerciseService()
        
        return self._exercise_service
    
    def get_lab_environment_service(self) -> ILabEnvironmentService:
        """Get lab environment service instance"""
        if not self._lab_environment_service:
            # For now, return a mock implementation
            self._lab_environment_service = MockLabEnvironmentService()
        
        return self._lab_environment_service
    
    def get_content_search_service(self) -> IContentSearchService:
        """Get content search service instance"""
        if not self._content_search_service:
            self._content_search_service = ContentSearchService(
                search_repository=self.get_content_search_repository()
            )
        
        return self._content_search_service
    
    def get_content_analytics_service(self) -> IContentAnalyticsService:
        """Get content analytics service instance"""
        if not self._content_analytics_service:
            # For now, return a mock implementation
            self._content_analytics_service = MockContentAnalyticsService()
        
        return self._content_analytics_service
    
    def get_content_export_service(self) -> IContentExportService:
        """Get content export service instance"""
        if not self._content_export_service:
            # For now, return a mock implementation
            self._content_export_service = MockContentExportService()
        
        return self._content_export_service


# Mock implementations for services not yet fully implemented
class MockSlideService:
    """Mock slide service for demonstration"""
    
    async def create_slide(self, slide_data, created_by):
        return {"id": "mock_slide_id", "title": slide_data.get("title", "Mock Slide")}
    
    async def get_slide(self, slide_id):
        return {"id": slide_id, "title": "Mock Slide"}
    
    async def update_slide(self, slide_id, updates, updated_by):
        return {"id": slide_id, "title": updates.get("title", "Updated Mock Slide")}
    
    async def delete_slide(self, slide_id, deleted_by):
        return True
    
    async def get_course_slides(self, course_id, ordered=True):
        return []
    
    async def reorder_slides(self, course_id, slide_orders, updated_by):
        return True
    
    async def duplicate_slide(self, slide_id, new_slide_number, created_by):
        return {"id": "new_mock_slide_id", "slide_number": new_slide_number}
    
    async def generate_slides_from_content(self, content, course_id, created_by):
        return []


class MockQuizService:
    """Mock quiz service for demonstration"""
    
    async def create_quiz(self, quiz_data, created_by):
        return {"id": "mock_quiz_id", "title": quiz_data.get("title", "Mock Quiz")}
    
    async def get_quiz(self, quiz_id):
        return {"id": quiz_id, "title": "Mock Quiz"}
    
    async def update_quiz(self, quiz_id, updates, updated_by):
        return {"id": quiz_id, "title": updates.get("title", "Updated Mock Quiz")}
    
    async def delete_quiz(self, quiz_id, deleted_by):
        return True
    
    async def publish_quiz(self, quiz_id, published_by):
        return {"id": quiz_id, "status": "published"}
    
    async def get_course_quizzes(self, course_id, include_drafts=False):
        return []
    
    async def calculate_quiz_score(self, quiz_id, answers):
        return {"score": 85, "total": 100}
    
    async def generate_quiz_from_content(self, content, course_id, created_by, question_count=10):
        return {"id": "generated_quiz_id", "questions": []}


class MockExerciseService:
    """Mock exercise service for demonstration"""
    
    async def create_exercise(self, exercise_data, created_by):
        return {"id": "mock_exercise_id", "title": exercise_data.get("title", "Mock Exercise")}
    
    async def get_exercise(self, exercise_id):
        return {"id": exercise_id, "title": "Mock Exercise"}
    
    async def update_exercise(self, exercise_id, updates, updated_by):
        return {"id": exercise_id, "title": updates.get("title", "Updated Mock Exercise")}
    
    async def delete_exercise(self, exercise_id, deleted_by):
        return True
    
    async def publish_exercise(self, exercise_id, published_by):
        return {"id": exercise_id, "status": "published"}
    
    async def get_course_exercises(self, course_id, include_drafts=False):
        return []
    
    async def get_exercises_by_difficulty(self, course_id, difficulty):
        return []
    
    async def grade_exercise_submission(self, exercise_id, submission):
        return {"grade": "B+", "score": 87}


class MockLabEnvironmentService:
    """Mock lab environment service for demonstration"""
    
    async def create_lab_environment(self, lab_data, created_by):
        return {"id": "mock_lab_id", "title": lab_data.get("title", "Mock Lab")}
    
    async def get_lab_environment(self, lab_id):
        return {"id": lab_id, "title": "Mock Lab Environment"}
    
    async def update_lab_environment(self, lab_id, updates, updated_by):
        return {"id": lab_id, "title": updates.get("title", "Updated Mock Lab")}
    
    async def delete_lab_environment(self, lab_id, deleted_by):
        return True
    
    async def get_course_lab_environments(self, course_id):
        return []
    
    async def validate_lab_resources(self, lab_id, available_resources):
        return {"valid": True, "requirements_met": True}
    
    async def generate_lab_setup_script(self, lab_id):
        return "#!/bin/bash\necho 'Mock setup script'"


class MockContentAnalyticsService:
    """Mock content analytics service for demonstration"""
    
    async def get_content_statistics(self, course_id=None):
        return {
            "total_content": 25,
            "syllabi": 2,
            "slides": 12,
            "quizzes": 5,
            "exercises": 4,
            "lab_environments": 2
        }
    
    async def get_content_usage_metrics(self, content_id, days=30):
        return {"views": 45, "engagements": 12, "completion_rate": 78.5}
    
    async def get_course_content_summary(self, course_id):
        return {"content_count": 15, "completion_percentage": 85}
    
    async def analyze_content_quality(self, content_id):
        return {"quality_score": 8.5, "recommendations": []}
    
    async def generate_content_report(self, course_id, report_type):
        return {"report_id": "mock_report", "status": "generated"}


class MockContentExportService:
    """Mock content export service for demonstration"""
    
    async def export_content(self, content_id, export_format):
        return {"export_id": "mock_export", "download_url": "/exports/mock_export.zip"}
    
    async def export_course_content(self, course_id, export_format, content_types=None):
        return {"export_id": "course_export", "download_url": "/exports/course_export.zip"}
    
    async def create_content_package(self, content_ids, package_format):
        return {"package_id": "mock_package", "download_url": "/packages/mock_package.zip"}
    
    async def export_to_lms(self, course_id, lms_type, export_settings):
        return {"export_id": "lms_export", "status": "completed"}