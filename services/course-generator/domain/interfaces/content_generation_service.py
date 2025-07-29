"""
Content Generation Service Interfaces
Single Responsibility: Define content generation operations
Interface Segregation: Focused interfaces for different generation types
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.course_content import Syllabus, Slide, Exercise, LabEnvironment, GenerationJob
from ..entities.quiz import Quiz, QuizQuestion, QuizGenerationRequest
from ..entities.student_interaction import StudentProgress, ChatInteraction, LabSession

class ISyllabusGenerationService(ABC):
    """Interface for syllabus generation operations"""

    @abstractmethod
    async def generate_syllabus(self, course_id: str, title: str, description: str, 
                               category: str, difficulty_level: str, 
                               estimated_duration: int, context: Dict[str, Any] = None) -> Syllabus:
        """Generate a course syllabus"""
        pass

    @abstractmethod
    async def update_syllabus(self, syllabus: Syllabus, updates: Dict[str, Any]) -> Syllabus:
        """Update an existing syllabus"""
        pass

    @abstractmethod
    async def analyze_syllabus_content(self, content: str) -> Dict[str, Any]:
        """Analyze uploaded syllabus content and extract structured data"""
        pass

class ISlideGenerationService(ABC):
    """Interface for slide generation operations"""

    @abstractmethod
    async def generate_slides(self, course_id: str, title: str, description: str, 
                             topic: str, slide_count: int = 10, 
                             use_custom_template: bool = False) -> List[Slide]:
        """Generate slides for a course topic"""
        pass

    @abstractmethod
    async def generate_single_slide(self, course_id: str, topic: str, 
                                   slide_type: str, content_hints: List[str] = None) -> Slide:
        """Generate a single slide"""
        pass

    @abstractmethod
    async def update_slide_content(self, slide: Slide, new_content: Dict[str, Any]) -> Slide:
        """Update slide content"""
        pass

class IExerciseGenerationService(ABC):
    """Interface for exercise generation operations"""

    @abstractmethod
    async def generate_exercise(self, course_id: str, topic: str, difficulty: str, 
                               exercise_type: str = "coding", context: Dict[str, Any] = None) -> Exercise:
        """Generate a single exercise"""
        pass

    @abstractmethod
    async def generate_exercises_batch(self, course_id: str, topic: str, difficulty: str, 
                                      count: int = 5, exercise_type: str = "coding") -> List[Exercise]:
        """Generate multiple exercises"""
        pass

    @abstractmethod
    async def generate_dynamic_exercise(self, course_id: str, student_progress: Dict[str, Any], 
                                       context: Dict[str, Any]) -> Exercise:
        """Generate personalized exercise based on student progress"""
        pass

    @abstractmethod
    async def validate_exercise_solution(self, exercise: Exercise, solution: str) -> Dict[str, Any]:
        """Validate a student's exercise solution"""
        pass

class IQuizGenerationService(ABC):
    """Interface for quiz generation operations"""

    @abstractmethod
    async def generate_quiz(self, request: QuizGenerationRequest) -> Quiz:
        """Generate a complete quiz"""
        pass

    @abstractmethod
    async def generate_quiz_questions(self, topic: str, difficulty: str, 
                                     question_count: int, context: Dict[str, Any] = None) -> List[QuizQuestion]:
        """Generate quiz questions for a topic"""
        pass

    @abstractmethod
    async def generate_adaptive_quiz(self, course_id: str, student_progress: Dict[str, Any], 
                                    context: Dict[str, Any]) -> Quiz:
        """Generate an adaptive quiz based on student performance"""
        pass

    @abstractmethod
    async def validate_quiz_answers(self, quiz: Quiz, answers: List[int]) -> Dict[str, Any]:
        """Validate quiz answers and calculate score"""
        pass

class ILabEnvironmentService(ABC):
    """Interface for lab environment management operations"""

    @abstractmethod
    async def create_lab_environment(self, course_id: str, name: str, description: str, 
                                    environment_type: str, config: Dict[str, Any]) -> LabEnvironment:
        """Create a new lab environment"""
        pass

    @abstractmethod
    async def generate_lab_exercises(self, lab_environment: LabEnvironment, 
                                    topic: str, difficulty: str, count: int = 3) -> List[Exercise]:
        """Generate exercises for a lab environment"""
        pass

    @abstractmethod
    async def customize_lab_for_student(self, lab_environment: LabEnvironment, 
                                       student_progress: StudentProgress) -> LabEnvironment:
        """Customize lab environment based on student progress"""
        pass

    @abstractmethod
    async def validate_lab_setup(self, lab_environment: LabEnvironment) -> Dict[str, Any]:
        """Validate lab environment configuration"""
        pass

class IChatService(ABC):
    """Interface for AI chat interactions"""

    @abstractmethod
    async def process_chat_message(self, course_id: str, student_id: str, 
                                  user_message: str, context: Dict[str, Any]) -> ChatInteraction:
        """Process a student's chat message and generate AI response"""
        pass

    @abstractmethod
    async def get_conversation_history(self, course_id: str, student_id: str, 
                                      limit: int = 10) -> List[ChatInteraction]:
        """Get conversation history for a student"""
        pass

    @abstractmethod
    async def analyze_conversation_sentiment(self, interactions: List[ChatInteraction]) -> Dict[str, Any]:
        """Analyze sentiment and learning patterns from conversations"""
        pass

class IProgressTrackingService(ABC):
    """Interface for student progress tracking operations"""

    @abstractmethod
    async def update_student_progress(self, course_id: str, student_id: str, 
                                     progress_updates: Dict[str, Any]) -> StudentProgress:
        """Update student progress data"""
        pass

    @abstractmethod
    async def get_student_progress(self, course_id: str, student_id: str) -> Optional[StudentProgress]:
        """Get current student progress"""
        pass

    @abstractmethod
    async def analyze_learning_patterns(self, student_progress: StudentProgress) -> Dict[str, Any]:
        """Analyze student learning patterns and provide insights"""
        pass

    @abstractmethod
    async def generate_personalized_recommendations(self, student_progress: StudentProgress) -> List[Dict[str, Any]]:
        """Generate personalized learning recommendations"""
        pass

class IJobManagementService(ABC):
    """Interface for content generation job management"""

    @abstractmethod
    async def create_generation_job(self, job: GenerationJob) -> GenerationJob:
        """Create a new content generation job"""
        pass

    @abstractmethod
    async def get_job_status(self, job_id: str) -> Optional[GenerationJob]:
        """Get job status by ID"""
        pass

    @abstractmethod
    async def update_job_progress(self, job_id: str, status: str, 
                                 result: Optional[Dict[str, Any]] = None, 
                                 error_message: Optional[str] = None) -> GenerationJob:
        """Update job progress"""
        pass

    @abstractmethod
    async def get_pending_jobs(self, limit: int = 10) -> List[GenerationJob]:
        """Get pending jobs for processing"""
        pass

    @abstractmethod
    async def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Clean up old completed jobs"""
        pass

class ILabSessionService(ABC):
    """Interface for lab session management"""

    @abstractmethod
    async def create_lab_session(self, course_id: str, student_id: str, 
                                session_data: Dict[str, Any]) -> LabSession:
        """Create a new lab session"""
        pass

    @abstractmethod
    async def save_lab_state(self, session_id: str, session_data: Dict[str, Any], 
                            code_files: Dict[str, str], progress_data: Dict[str, Any] = None) -> LabSession:
        """Save lab session state"""
        pass

    @abstractmethod
    async def restore_lab_session(self, course_id: str, student_id: str) -> Optional[LabSession]:
        """Restore the most recent lab session for a student"""
        pass

    @abstractmethod
    async def end_lab_session(self, session_id: str) -> LabSession:
        """End a lab session"""
        pass

    @abstractmethod
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a lab session"""
        pass