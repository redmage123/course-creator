"""
Dependency Injection

Provides dependency injection for services, repositories, and AI components.
Handles proper initialization and lifecycle management of dependencies.
"""

from typing import Generator, Any
import logging
import asyncpg
from functools import lru_cache
from fastapi import Depends, HTTPException, status
from omegaconf import DictConfig
import hydra

from ai.client import AIClient
from repositories.base_repository import BaseRepository
from repositories.syllabus_repository import SyllabusRepository
from repositories.slide_repository import SlideRepository
from repositories.quiz_repository import QuizRepository
from repositories.lab_repository import LabRepository
from repositories.course_repository import CourseRepository
from services.course_service import CourseService
from services.slide_service import SlideService
from services.exercise_service import ExerciseService
from services.quiz_service import QuizService
from services.lab_service import LabService
from services.syllabus_service import SyllabusService
from services.content_service import ContentService
from services.ai_assistant_service import AIAssistantService

logger = logging.getLogger(__name__)

# Global database pool - will be initialized at startup
_db_pool: asyncpg.Pool = None
_config: DictConfig = None


async def init_database_pool() -> None:
    """Initialize the database connection pool."""
    global _db_pool, _config
    
    if _db_pool is not None:
        return
    
    try:
        # Initialize with hydra config
        with hydra.initialize(config_path="conf"):
            _config = hydra.compose(config_name="config")
        
        # Create database pool
        _db_pool = await asyncpg.create_pool(
            host=_config.database.host,
            port=_config.database.port,
            user=_config.database.user,
            password=_config.database.password,
            database=_config.database.database,
            min_size=_config.database.min_pool_size,
            max_size=_config.database.max_pool_size,
        )
        
        logger.info("Database pool initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


async def close_database_pool() -> None:
    """Close the database connection pool."""
    global _db_pool
    
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None
        logger.info("Database pool closed")


# Configuration Dependencies
def get_config() -> DictConfig:
    """Get application configuration."""
    global _config
    if _config is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration not initialized"
        )
    return _config


# Database Dependencies
def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool."""
    global _db_pool
    if _db_pool is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database pool not initialized"
        )
    return _db_pool


# AI Dependencies
@lru_cache()
def get_ai_client(config: DictConfig = Depends(get_config)) -> AIClient:
    """Get AI client instance."""
    return AIClient(config)


# Repository Dependencies
def get_base_repository(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> BaseRepository:
    """Get base repository instance."""
    return BaseRepository(db_pool)


def get_syllabus_repository(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> SyllabusRepository:
    """Get syllabus repository instance."""
    return SyllabusRepository(db_pool)


def get_slide_repository(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> SlideRepository:
    """Get slide repository instance."""
    return SlideRepository(db_pool)


def get_quiz_repository(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> QuizRepository:
    """Get quiz repository instance."""
    return QuizRepository(db_pool)


def get_lab_repository(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> LabRepository:
    """Get lab repository instance."""
    return LabRepository(db_pool)


def get_course_repository(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> CourseRepository:
    """Get course repository instance."""
    return CourseRepository(db_pool)


# Service Dependencies
def get_course_service(
    course_repo: CourseRepository = Depends(get_course_repository),
    ai_client: AIClient = Depends(get_ai_client)
) -> CourseService:
    """Get course service instance."""
    return CourseService(course_repo, ai_client)


def get_slide_service(
    slide_repo: SlideRepository = Depends(get_slide_repository),
    ai_client: AIClient = Depends(get_ai_client)
) -> SlideService:
    """Get slide service instance."""
    return SlideService(slide_repo, ai_client)


def get_exercise_service(
    ai_client: AIClient = Depends(get_ai_client)
) -> ExerciseService:
    """Get exercise service instance."""
    return ExerciseService(ai_client)


def get_quiz_service(
    quiz_repo: QuizRepository = Depends(get_quiz_repository),
    ai_client: AIClient = Depends(get_ai_client)
) -> QuizService:
    """Get quiz service instance."""
    return QuizService(quiz_repo, ai_client)


def get_lab_service(
    lab_repo: LabRepository = Depends(get_lab_repository),
    ai_client: AIClient = Depends(get_ai_client)
) -> LabService:
    """Get lab service instance."""
    return LabService(lab_repo, ai_client)


def get_syllabus_service(
    syllabus_repo: SyllabusRepository = Depends(get_syllabus_repository),
    ai_client: AIClient = Depends(get_ai_client)
) -> SyllabusService:
    """Get syllabus service instance."""
    return SyllabusService(syllabus_repo, ai_client)


def get_content_service(
    course_service: CourseService = Depends(get_course_service),
    slide_service: SlideService = Depends(get_slide_service),
    exercise_service: ExerciseService = Depends(get_exercise_service),
    quiz_service: QuizService = Depends(get_quiz_service),
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> ContentService:
    """Get content service instance."""
    return ContentService(
        course_service,
        slide_service,
        exercise_service,
        quiz_service,
        syllabus_service
    )


def get_ai_assistant_service(
    ai_client: AIClient = Depends(get_ai_client)
) -> AIAssistantService:
    """Get AI assistant service instance."""
    return AIAssistantService(ai_client)


# Error handler decorator
def handle_exceptions(func):
    """Decorator for consistent error handling."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    return wrapper