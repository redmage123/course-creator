"""
Dependency injection setup following Dependency Inversion Principle.
"""
from fastapi import FastAPI
from omegaconf import DictConfig

from services.ai_service import AIService
from services.syllabus_service import SyllabusService
from services.exercise_generation_service import ExerciseGenerationService
from services.lab_environment_service import LabEnvironmentService
from services.job_service import JobService
from repositories.course_repository import CourseRepository

class DependencyContainer:
    """Container for managing service dependencies."""
    
    def __init__(self, config: DictConfig):
        self.config = config
        self._services = {}
        self._repositories = {}
        self._db_factory = None
    
    def get_course_repository(self) -> CourseRepository:
        """Get course repository instance."""
        if 'course_repository' not in self._repositories:
            # Simplified repository creation without database dependency for now
            self._repositories['course_repository'] = CourseRepository()
        return self._repositories['course_repository']
    
    def get_ai_service(self) -> AIService:
        """Get AI service instance."""
        if 'ai_service' not in self._services:
            self._services['ai_service'] = AIService(self.config.ai)
        return self._services['ai_service']
    
    def get_syllabus_service(self) -> SyllabusService:
        """Get syllabus service instance."""
        if 'syllabus_service' not in self._services:
            ai_service = self.get_ai_service()
            course_repo = self.get_course_repository()
            self._services['syllabus_service'] = SyllabusService(ai_service, course_repo)
        return self._services['syllabus_service']
    
    def get_exercise_service(self) -> ExerciseGenerationService:
        """Get exercise generation service instance."""
        if 'exercise_service' not in self._services:
            ai_service = self.get_ai_service()
            self._services['exercise_service'] = ExerciseGenerationService(ai_service)
        return self._services['exercise_service']
    
    def get_lab_service(self) -> LabEnvironmentService:
        """Get lab environment service instance."""
        if 'lab_service' not in self._services:
            ai_service = self.get_ai_service()
            self._services['lab_service'] = LabEnvironmentService(ai_service)
        return self._services['lab_service']
    
    def get_job_service(self) -> JobService:
        """Get job service instance."""
        if 'job_service' not in self._services:
            self._services['job_service'] = JobService()
        return self._services['job_service']

# Global container instance
_container: DependencyContainer = None

def setup_dependencies(app: FastAPI, config: DictConfig) -> None:
    """Setup dependency injection container."""
    global _container
    _container = DependencyContainer(config)
    
    # Store container in app state for access in routes
    app.state.container = _container

def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    if not _container:
        raise RuntimeError("Dependencies not initialized")
    return _container

def get_syllabus_service() -> SyllabusService:
    """Get syllabus service for FastAPI dependency injection."""
    return get_container().get_syllabus_service()

def get_exercise_service() -> ExerciseGenerationService:
    """Get exercise service for FastAPI dependency injection."""
    return get_container().get_exercise_service()

def get_lab_service() -> LabEnvironmentService:
    """Get lab service for FastAPI dependency injection."""
    return get_container().get_lab_service()

def get_job_service() -> JobService:
    """Get job service for FastAPI dependency injection."""
    return get_container().get_job_service()