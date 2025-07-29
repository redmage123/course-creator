"""
Content Repository Interfaces
Single Responsibility: Define data access operations for content entities
Dependency Inversion: Abstract interfaces for data persistence
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..entities.course_content import Syllabus, Slide, Exercise, LabEnvironment, GenerationJob, ContentType
from ..entities.quiz import Quiz, QuizQuestion, QuizAttempt
from ..entities.student_interaction import StudentProgress, ChatInteraction, LabSession

class ISyllabusRepository(ABC):
    """Interface for syllabus data access operations"""

    @abstractmethod
    async def create(self, syllabus: Syllabus) -> Syllabus:
        """Create a new syllabus"""
        pass

    @abstractmethod
    async def get_by_id(self, syllabus_id: str) -> Optional[Syllabus]:
        """Get syllabus by ID"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> Optional[Syllabus]:
        """Get syllabus by course ID"""
        pass

    @abstractmethod
    async def update(self, syllabus: Syllabus) -> Syllabus:
        """Update an existing syllabus"""
        pass

    @abstractmethod
    async def delete(self, syllabus_id: str) -> bool:
        """Delete a syllabus"""
        pass

    @abstractmethod
    async def search(self, query: str, filters: Dict[str, Any] = None) -> List[Syllabus]:
        """Search syllabi by query and filters"""
        pass

class ISlideRepository(ABC):
    """Interface for slide data access operations"""

    @abstractmethod
    async def create(self, slide: Slide) -> Slide:
        """Create a new slide"""
        pass

    @abstractmethod
    async def get_by_id(self, slide_id: str) -> Optional[Slide]:
        """Get slide by ID"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str, order_by: str = "order") -> List[Slide]:
        """Get all slides for a course"""
        pass

    @abstractmethod
    async def update(self, slide: Slide) -> Slide:
        """Update an existing slide"""
        pass

    @abstractmethod
    async def delete(self, slide_id: str) -> bool:
        """Delete a slide"""
        pass

    @abstractmethod
    async def bulk_create(self, slides: List[Slide]) -> List[Slide]:
        """Create multiple slides in batch"""
        pass

    @abstractmethod
    async def reorder_slides(self, course_id: str, slide_orders: Dict[str, int]) -> bool:
        """Reorder slides for a course"""
        pass

    @abstractmethod
    async def get_slides_by_topic(self, course_id: str, topic: str) -> List[Slide]:
        """Get slides by topic"""
        pass

class IExerciseRepository(ABC):
    """Interface for exercise data access operations"""

    @abstractmethod
    async def create(self, exercise: Exercise) -> Exercise:
        """Create a new exercise"""
        pass

    @abstractmethod
    async def get_by_id(self, exercise_id: str) -> Optional[Exercise]:
        """Get exercise by ID"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[Exercise]:
        """Get all exercises for a course"""
        pass

    @abstractmethod
    async def get_by_topic(self, course_id: str, topic: str) -> List[Exercise]:
        """Get exercises by topic"""
        pass

    @abstractmethod
    async def get_by_difficulty(self, course_id: str, difficulty: str) -> List[Exercise]:
        """Get exercises by difficulty level"""
        pass

    @abstractmethod
    async def update(self, exercise: Exercise) -> Exercise:
        """Update an existing exercise"""
        pass

    @abstractmethod
    async def delete(self, exercise_id: str) -> bool:
        """Delete an exercise"""
        pass

    @abstractmethod
    async def bulk_create(self, exercises: List[Exercise]) -> List[Exercise]:
        """Create multiple exercises in batch"""
        pass

    @abstractmethod
    async def search(self, course_id: str, query: str, filters: Dict[str, Any] = None) -> List[Exercise]:
        """Search exercises by query and filters"""
        pass

class IQuizRepository(ABC):
    """Interface for quiz data access operations"""

    @abstractmethod
    async def create(self, quiz: Quiz) -> Quiz:
        """Create a new quiz"""
        pass

    @abstractmethod
    async def get_by_id(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[Quiz]:
        """Get all quizzes for a course"""
        pass

    @abstractmethod
    async def get_by_topic(self, course_id: str, topic: str) -> List[Quiz]:
        """Get quizzes by topic"""
        pass

    @abstractmethod
    async def update(self, quiz: Quiz) -> Quiz:
        """Update an existing quiz"""
        pass

    @abstractmethod
    async def delete(self, quiz_id: str) -> bool:
        """Delete a quiz"""
        pass

    @abstractmethod
    async def get_quiz_statistics(self, quiz_id: str) -> Dict[str, Any]:
        """Get statistics for a quiz"""
        pass

class IQuizAttemptRepository(ABC):
    """Interface for quiz attempt data access operations"""

    @abstractmethod
    async def create(self, attempt: QuizAttempt) -> QuizAttempt:
        """Create a new quiz attempt"""
        pass

    @abstractmethod
    async def get_by_id(self, attempt_id: str) -> Optional[QuizAttempt]:
        """Get quiz attempt by ID"""
        pass

    @abstractmethod
    async def get_by_student_and_quiz(self, student_id: str, quiz_id: str) -> List[QuizAttempt]:
        """Get all attempts by a student for a specific quiz"""
        pass

    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, course_id: str) -> List[QuizAttempt]:
        """Get all attempts by a student for a course"""
        pass

    @abstractmethod
    async def update(self, attempt: QuizAttempt) -> QuizAttempt:
        """Update a quiz attempt"""
        pass

    @abstractmethod
    async def get_attempt_statistics(self, quiz_id: str) -> Dict[str, Any]:
        """Get statistics for quiz attempts"""
        pass

class ILabEnvironmentRepository(ABC):
    """Interface for lab environment data access operations"""

    @abstractmethod
    async def create(self, lab_environment: LabEnvironment) -> LabEnvironment:
        """Create a new lab environment"""
        pass

    @abstractmethod
    async def get_by_id(self, lab_id: str) -> Optional[LabEnvironment]:
        """Get lab environment by ID"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[LabEnvironment]:
        """Get all lab environments for a course"""
        pass

    @abstractmethod
    async def get_by_environment_type(self, environment_type: str) -> List[LabEnvironment]:
        """Get lab environments by type"""
        pass

    @abstractmethod
    async def update(self, lab_environment: LabEnvironment) -> LabEnvironment:
        """Update an existing lab environment"""
        pass

    @abstractmethod
    async def delete(self, lab_id: str) -> bool:
        """Delete a lab environment"""
        pass

class IStudentProgressRepository(ABC):
    """Interface for student progress data access operations"""

    @abstractmethod
    async def create(self, progress: StudentProgress) -> StudentProgress:
        """Create new student progress record"""
        pass

    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, course_id: str) -> Optional[StudentProgress]:
        """Get progress for a student in a specific course"""
        pass

    @abstractmethod
    async def get_by_student_id(self, student_id: str) -> List[StudentProgress]:
        """Get all progress records for a student"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[StudentProgress]:
        """Get all progress records for a course"""
        pass

    @abstractmethod
    async def update(self, progress: StudentProgress) -> StudentProgress:
        """Update student progress"""
        pass

    @abstractmethod
    async def delete(self, progress_id: str) -> bool:
        """Delete a progress record"""
        pass

    @abstractmethod
    async def get_course_analytics(self, course_id: str) -> Dict[str, Any]:
        """Get analytics for all students in a course"""
        pass

class IChatInteractionRepository(ABC):
    """Interface for chat interaction data access operations"""

    @abstractmethod
    async def create(self, interaction: ChatInteraction) -> ChatInteraction:
        """Create a new chat interaction"""
        pass

    @abstractmethod
    async def get_by_id(self, interaction_id: str) -> Optional[ChatInteraction]:
        """Get chat interaction by ID"""
        pass

    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, course_id: str, 
                                       limit: int = 50) -> List[ChatInteraction]:
        """Get chat history for a student in a course"""
        pass

    @abstractmethod
    async def get_recent_interactions(self, course_id: str, limit: int = 100) -> List[ChatInteraction]:
        """Get recent chat interactions for a course"""
        pass

    @abstractmethod
    async def update(self, interaction: ChatInteraction) -> ChatInteraction:
        """Update a chat interaction"""
        pass

    @abstractmethod
    async def delete_old_interactions(self, days_old: int = 90) -> int:
        """Delete old chat interactions"""
        pass

    @abstractmethod
    async def get_interaction_analytics(self, course_id: str, time_period_days: int = 30) -> Dict[str, Any]:
        """Get analytics for chat interactions"""
        pass

class ILabSessionRepository(ABC):
    """Interface for lab session data access operations"""

    @abstractmethod
    async def create(self, session: LabSession) -> LabSession:
        """Create a new lab session"""
        pass

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[LabSession]:
        """Get lab session by ID"""
        pass

    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, course_id: str) -> List[LabSession]:
        """Get all lab sessions for a student in a course"""
        pass

    @abstractmethod
    async def get_active_session(self, student_id: str, course_id: str) -> Optional[LabSession]:
        """Get active lab session for a student"""
        pass

    @abstractmethod
    async def update(self, session: LabSession) -> LabSession:
        """Update a lab session"""
        pass

    @abstractmethod
    async def end_session(self, session_id: str) -> LabSession:
        """End a lab session"""
        pass

    @abstractmethod
    async def delete_old_sessions(self, days_old: int = 30) -> int:
        """Delete old lab sessions"""
        pass

    @abstractmethod
    async def get_session_analytics(self, course_id: str) -> Dict[str, Any]:
        """Get analytics for lab sessions"""
        pass

class IGenerationJobRepository(ABC):
    """Interface for generation job data access operations"""

    @abstractmethod
    async def create(self, job: GenerationJob) -> GenerationJob:
        """Create a new generation job"""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[GenerationJob]:
        """Get generation job by ID"""
        pass

    @abstractmethod
    async def get_pending_jobs(self, content_type: Optional[ContentType] = None, 
                              limit: int = 10) -> List[GenerationJob]:
        """Get pending jobs for processing"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[GenerationJob]:
        """Get all jobs for a course"""
        pass

    @abstractmethod
    async def update(self, job: GenerationJob) -> GenerationJob:
        """Update a generation job"""
        pass

    @abstractmethod
    async def delete(self, job_id: str) -> bool:
        """Delete a generation job"""
        pass

    @abstractmethod
    async def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Clean up old completed jobs"""
        pass

    @abstractmethod
    async def get_job_statistics(self, time_period_days: int = 30) -> Dict[str, Any]:
        """Get statistics for generation jobs"""
        pass