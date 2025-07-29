"""
Content Service Interfaces - Domain Layer
Single Responsibility: Define contracts for content business logic
Interface Segregation: Separate interfaces for different content operations
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from ..entities.base_content import ContentType, ContentStatus
from ..entities.syllabus import Syllabus
from ..entities.slide import Slide
from ..entities.quiz import Quiz
from ..entities.exercise import Exercise
from ..entities.lab_environment import LabEnvironment


class IContentValidationService(ABC):
    """Interface for content validation operations"""
    
    @abstractmethod
    async def validate_content(self, content) -> Dict[str, Any]:
        """Validate content entity"""
        pass
    
    @abstractmethod
    async def check_content_completeness(self, content) -> Dict[str, Any]:
        """Check if content is complete for publishing"""
        pass
    
    @abstractmethod
    async def validate_content_permissions(self, user_id: str, content_id: str, action: str) -> bool:
        """Validate user permissions for content action"""
        pass


class ISyllabusService(ABC):
    """Interface for syllabus business logic operations"""
    
    @abstractmethod
    async def create_syllabus(self, syllabus_data: Dict[str, Any], created_by: str) -> Syllabus:
        """Create new syllabus"""
        pass
    
    @abstractmethod
    async def get_syllabus(self, syllabus_id: str) -> Optional[Syllabus]:
        """Get syllabus by ID"""
        pass
    
    @abstractmethod
    async def update_syllabus(self, syllabus_id: str, updates: Dict[str, Any], updated_by: str) -> Optional[Syllabus]:
        """Update syllabus"""
        pass
    
    @abstractmethod
    async def delete_syllabus(self, syllabus_id: str, deleted_by: str) -> bool:
        """Delete syllabus"""
        pass
    
    @abstractmethod
    async def publish_syllabus(self, syllabus_id: str, published_by: str) -> Optional[Syllabus]:
        """Publish syllabus"""
        pass
    
    @abstractmethod
    async def archive_syllabus(self, syllabus_id: str, archived_by: str) -> Optional[Syllabus]:
        """Archive syllabus"""
        pass
    
    @abstractmethod
    async def get_course_syllabi(self, course_id: str, include_drafts: bool = False) -> List[Syllabus]:
        """Get all syllabi for a course"""
        pass
    
    @abstractmethod
    async def generate_syllabus_from_template(self, template_id: str, course_data: Dict[str, Any], created_by: str) -> Syllabus:
        """Generate syllabus from template"""
        pass


class ISlideService(ABC):
    """Interface for slide business logic operations"""
    
    @abstractmethod
    async def create_slide(self, slide_data: Dict[str, Any], created_by: str) -> Slide:
        """Create new slide"""
        pass
    
    @abstractmethod
    async def get_slide(self, slide_id: str) -> Optional[Slide]:
        """Get slide by ID"""
        pass
    
    @abstractmethod
    async def update_slide(self, slide_id: str, updates: Dict[str, Any], updated_by: str) -> Optional[Slide]:
        """Update slide"""
        pass
    
    @abstractmethod
    async def delete_slide(self, slide_id: str, deleted_by: str) -> bool:
        """Delete slide"""
        pass
    
    @abstractmethod
    async def reorder_slides(self, course_id: str, slide_orders: Dict[str, int], updated_by: str) -> bool:
        """Reorder slides in a course"""
        pass
    
    @abstractmethod
    async def duplicate_slide(self, slide_id: str, new_slide_number: int, created_by: str) -> Optional[Slide]:
        """Duplicate slide with new slide number"""
        pass
    
    @abstractmethod
    async def get_course_slides(self, course_id: str, ordered: bool = True) -> List[Slide]:
        """Get all slides for a course"""
        pass
    
    @abstractmethod
    async def generate_slides_from_content(self, content: str, course_id: str, created_by: str) -> List[Slide]:
        """Generate slides from content"""
        pass


class IQuizService(ABC):
    """Interface for quiz business logic operations"""
    
    @abstractmethod
    async def create_quiz(self, quiz_data: Dict[str, Any], created_by: str) -> Quiz:
        """Create new quiz"""
        pass
    
    @abstractmethod
    async def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID"""
        pass
    
    @abstractmethod
    async def update_quiz(self, quiz_id: str, updates: Dict[str, Any], updated_by: str) -> Optional[Quiz]:
        """Update quiz"""
        pass
    
    @abstractmethod
    async def delete_quiz(self, quiz_id: str, deleted_by: str) -> bool:
        """Delete quiz"""
        pass
    
    @abstractmethod
    async def publish_quiz(self, quiz_id: str, published_by: str) -> Optional[Quiz]:
        """Publish quiz"""
        pass
    
    @abstractmethod
    async def get_course_quizzes(self, course_id: str, include_drafts: bool = False) -> List[Quiz]:
        """Get all quizzes for a course"""
        pass
    
    @abstractmethod
    async def calculate_quiz_score(self, quiz_id: str, answers: Dict[int, str]) -> Dict[str, Any]:
        """Calculate quiz score based on answers"""
        pass
    
    @abstractmethod
    async def generate_quiz_from_content(self, content: str, course_id: str, created_by: str, question_count: int = 10) -> Quiz:
        """Generate quiz from content"""
        pass


class IExerciseService(ABC):
    """Interface for exercise business logic operations"""
    
    @abstractmethod
    async def create_exercise(self, exercise_data: Dict[str, Any], created_by: str) -> Exercise:
        """Create new exercise"""
        pass
    
    @abstractmethod
    async def get_exercise(self, exercise_id: str) -> Optional[Exercise]:
        """Get exercise by ID"""
        pass
    
    @abstractmethod
    async def update_exercise(self, exercise_id: str, updates: Dict[str, Any], updated_by: str) -> Optional[Exercise]:
        """Update exercise"""
        pass
    
    @abstractmethod
    async def delete_exercise(self, exercise_id: str, deleted_by: str) -> bool:
        """Delete exercise"""
        pass
    
    @abstractmethod
    async def publish_exercise(self, exercise_id: str, published_by: str) -> Optional[Exercise]:
        """Publish exercise"""
        pass
    
    @abstractmethod
    async def get_course_exercises(self, course_id: str, include_drafts: bool = False) -> List[Exercise]:
        """Get all exercises for a course"""
        pass
    
    @abstractmethod
    async def get_exercises_by_difficulty(self, course_id: str, difficulty: str) -> List[Exercise]:
        """Get exercises by difficulty level"""
        pass
    
    @abstractmethod
    async def grade_exercise_submission(self, exercise_id: str, submission: Dict[str, Any]) -> Dict[str, Any]:
        """Grade exercise submission"""
        pass


class ILabEnvironmentService(ABC):
    """Interface for lab environment business logic operations"""
    
    @abstractmethod
    async def create_lab_environment(self, lab_data: Dict[str, Any], created_by: str) -> LabEnvironment:
        """Create new lab environment"""
        pass
    
    @abstractmethod
    async def get_lab_environment(self, lab_id: str) -> Optional[LabEnvironment]:
        """Get lab environment by ID"""
        pass
    
    @abstractmethod
    async def update_lab_environment(self, lab_id: str, updates: Dict[str, Any], updated_by: str) -> Optional[LabEnvironment]:
        """Update lab environment"""
        pass
    
    @abstractmethod
    async def delete_lab_environment(self, lab_id: str, deleted_by: str) -> bool:
        """Delete lab environment"""
        pass
    
    @abstractmethod
    async def get_course_lab_environments(self, course_id: str) -> List[LabEnvironment]:
        """Get all lab environments for a course"""
        pass
    
    @abstractmethod
    async def validate_lab_resources(self, lab_id: str, available_resources: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if lab can run with available resources"""
        pass
    
    @abstractmethod
    async def generate_lab_setup_script(self, lab_id: str) -> str:
        """Generate complete setup script for lab environment"""
        pass


class IContentSearchService(ABC):
    """Interface for content search operations"""
    
    @abstractmethod
    async def search_content(
        self, 
        query: str, 
        content_types: Optional[List[ContentType]] = None,
        course_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Any]]:
        """Search content across all types"""
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
    async def get_content_recommendations(self, content_id: str, limit: int = 5) -> List[Any]:
        """Get content recommendations based on existing content"""
        pass
    
    @abstractmethod
    async def get_trending_content(self, content_type: Optional[ContentType] = None, days: int = 7) -> List[Any]:
        """Get trending content"""
        pass


class IContentAnalyticsService(ABC):
    """Interface for content analytics operations"""
    
    @abstractmethod
    async def get_content_statistics(self, course_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive content statistics"""
        pass
    
    @abstractmethod
    async def get_content_usage_metrics(self, content_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage metrics for specific content"""
        pass
    
    @abstractmethod
    async def get_course_content_summary(self, course_id: str) -> Dict[str, Any]:
        """Get summary of all content for a course"""
        pass
    
    @abstractmethod
    async def analyze_content_quality(self, content_id: str) -> Dict[str, Any]:
        """Analyze content quality metrics"""
        pass
    
    @abstractmethod
    async def generate_content_report(self, course_id: str, report_type: str) -> Dict[str, Any]:
        """Generate content report"""
        pass


class IContentExportService(ABC):
    """Interface for content export operations"""
    
    @abstractmethod
    async def export_content(self, content_id: str, export_format: str) -> Dict[str, Any]:
        """Export single content item"""
        pass
    
    @abstractmethod
    async def export_course_content(self, course_id: str, export_format: str, content_types: Optional[List[ContentType]] = None) -> Dict[str, Any]:
        """Export all content for a course"""
        pass
    
    @abstractmethod
    async def create_content_package(self, content_ids: List[str], package_format: str) -> Dict[str, Any]:
        """Create downloadable content package"""
        pass
    
    @abstractmethod
    async def export_to_lms(self, course_id: str, lms_type: str, export_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Export content to LMS format"""
        pass