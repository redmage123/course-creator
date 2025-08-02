"""
Content Repository Interfaces - Domain Layer
Single Responsibility: Define contracts for data persistence
Interface Segregation: Separate interfaces for different content types
Dependency Inversion: Abstract interfaces for concrete implementations
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from domain.entities.base_content import ContentType
from domain.entities.syllabus import Syllabus
from domain.entities.slide import Slide
from domain.entities.quiz import Quiz
from domain.entities.exercise import Exercise
from domain.entities.lab_environment import LabEnvironment


class IBaseContentRepository(ABC):
    """Base repository interface for all content types"""
    
    @abstractmethod
    async def create(self, content) -> Any:
        """Create content"""
        pass
    
    @abstractmethod
    async def get_by_id(self, content_id: str) -> Optional[Any]:
        """Get content by ID"""
        pass
    
    @abstractmethod
    async def update(self, content_id: str, updates: Dict[str, Any]) -> Optional[Any]:
        """Update content"""
        pass
    
    @abstractmethod
    async def delete(self, content_id: str) -> bool:
        """Delete content"""
        pass
    
    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[Any]:
        """Get all content for a course"""
        pass
    
    @abstractmethod
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Any]:
        """List all content with pagination"""
        pass
    
    @abstractmethod
    async def count_by_course_id(self, course_id: str) -> int:
        """Count content items for a course"""
        pass
    
    @abstractmethod
    async def delete_by_course_id(self, course_id: str) -> int:
        """Delete all content for a course"""
        pass


class ISyllabusRepository(IBaseContentRepository):
    """Repository interface for syllabus content"""
    
    @abstractmethod
    async def create(self, syllabus: Syllabus) -> Syllabus:
        """Create syllabus"""
        pass
    
    @abstractmethod
    async def get_by_id(self, syllabus_id: str) -> Optional[Syllabus]:
        """Get syllabus by ID"""
        pass
    
    @abstractmethod
    async def update(self, syllabus_id: str, updates: Dict[str, Any]) -> Optional[Syllabus]:
        """Update syllabus"""
        pass
    
    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[Syllabus]:
        """Get all syllabi for a course"""
        pass
    
    @abstractmethod
    async def get_published_by_course_id(self, course_id: str) -> List[Syllabus]:
        """Get published syllabi for a course"""
        pass
    
    @abstractmethod
    async def search_by_title(self, title: str, limit: int = 50) -> List[Syllabus]:
        """Search syllabi by title"""
        pass


class ISlideRepository(IBaseContentRepository):
    """Repository interface for slide content"""
    
    @abstractmethod
    async def create(self, slide: Slide) -> Slide:
        """Create slide"""
        pass
    
    @abstractmethod
    async def get_by_id(self, slide_id: str) -> Optional[Slide]:
        """Get slide by ID"""
        pass
    
    @abstractmethod
    async def update(self, slide_id: str, updates: Dict[str, Any]) -> Optional[Slide]:
        """Update slide"""
        pass
    
    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[Slide]:
        """Get all slides for a course"""
        pass
    
    @abstractmethod
    async def get_ordered_slides(self, course_id: str) -> List[Slide]:
        """Get slides for a course ordered by slide number"""
        pass
    
    @abstractmethod
    async def get_by_slide_number(self, course_id: str, slide_number: int) -> Optional[Slide]:
        """Get slide by course and slide number"""
        pass
    
    @abstractmethod
    async def reorder_slides(self, course_id: str, slide_orders: Dict[str, int]) -> bool:
        """Reorder slides in a course"""
        pass


class IQuizRepository(IBaseContentRepository):
    """Repository interface for quiz content"""
    
    @abstractmethod
    async def create(self, quiz: Quiz) -> Quiz:
        """Create quiz"""
        pass
    
    @abstractmethod
    async def get_by_id(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID"""
        pass
    
    @abstractmethod
    async def update(self, quiz_id: str, updates: Dict[str, Any]) -> Optional[Quiz]:
        """Update quiz"""
        pass
    
    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[Quiz]:
        """Get all quizzes for a course"""
        pass
    
    @abstractmethod
    async def get_published_by_course_id(self, course_id: str) -> List[Quiz]:
        """Get published quizzes for a course"""
        pass
    
    @abstractmethod
    async def search_by_difficulty(self, difficulty: str, limit: int = 50) -> List[Quiz]:
        """Search quizzes by difficulty"""
        pass
    
    @abstractmethod
    async def get_timed_quizzes(self, course_id: str) -> List[Quiz]:
        """Get timed quizzes for a course"""
        pass


class IExerciseRepository(IBaseContentRepository):
    """Repository interface for exercise content"""
    
    @abstractmethod
    async def create(self, exercise: Exercise) -> Exercise:
        """Create exercise"""
        pass
    
    @abstractmethod
    async def get_by_id(self, exercise_id: str) -> Optional[Exercise]:
        """Get exercise by ID"""
        pass
    
    @abstractmethod
    async def update(self, exercise_id: str, updates: Dict[str, Any]) -> Optional[Exercise]:
        """Update exercise"""
        pass
    
    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[Exercise]:
        """Get all exercises for a course"""
        pass
    
    @abstractmethod
    async def get_by_difficulty(self, difficulty: str, course_id: Optional[str] = None) -> List[Exercise]:
        """Get exercises by difficulty level"""
        pass
    
    @abstractmethod
    async def get_by_type(self, exercise_type: str, course_id: Optional[str] = None) -> List[Exercise]:
        """Get exercises by type"""
        pass
    
    @abstractmethod
    async def search_by_objective(self, objective: str, limit: int = 50) -> List[Exercise]:
        """Search exercises by learning objective"""
        pass


class ILabEnvironmentRepository(IBaseContentRepository):
    """Repository interface for lab environment content"""
    
    @abstractmethod
    async def create(self, lab_environment: LabEnvironment) -> LabEnvironment:
        """Create lab environment"""
        pass
    
    @abstractmethod
    async def get_by_id(self, lab_id: str) -> Optional[LabEnvironment]:
        """Get lab environment by ID"""
        pass
    
    @abstractmethod
    async def update(self, lab_id: str, updates: Dict[str, Any]) -> Optional[LabEnvironment]:
        """Update lab environment"""
        pass
    
    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[LabEnvironment]:
        """Get all lab environments for a course"""
        pass
    
    @abstractmethod
    async def get_by_environment_type(self, env_type: str, course_id: Optional[str] = None) -> List[LabEnvironment]:
        """Get lab environments by type"""
        pass
    
    @abstractmethod
    async def get_by_base_image(self, base_image: str) -> List[LabEnvironment]:
        """Get lab environments using specific base image"""
        pass
    
    @abstractmethod
    async def get_gpu_required_environments(self, course_id: Optional[str] = None) -> List[LabEnvironment]:
        """Get lab environments that require GPU"""
        pass


class IContentSearchRepository(ABC):
    """Repository interface for content search operations"""
    
    @abstractmethod
    async def search_all_content(
        self, 
        query: str, 
        content_types: Optional[List[ContentType]] = None,
        course_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, List[Any]]:
        """Search across all content types"""
        pass
    
    @abstractmethod
    async def search_by_tags(
        self, 
        tags: List[str], 
        content_types: Optional[List[ContentType]] = None,
        course_id: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        """Search content by tags"""
        pass
    
    @abstractmethod
    async def get_content_statistics(self, course_id: Optional[str] = None) -> Dict[str, Any]:
        """Get content statistics"""
        pass
    
    @abstractmethod
    async def get_recent_content(
        self, 
        content_types: Optional[List[ContentType]] = None,
        days: int = 7,
        limit: int = 20
    ) -> List[Any]:
        """Get recently created/updated content"""
        pass