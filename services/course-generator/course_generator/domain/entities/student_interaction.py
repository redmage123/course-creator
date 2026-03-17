"""
Student Interaction Domain Entities
Single Responsibility: Represent student learning interactions and progress tracking
"""
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

class InteractionType(Enum):
    """
    Student Interaction Type Enumeration

    BUSINESS REQUIREMENT:
    Platform tracks different types of student interactions for personalized
    learning paths and AI assistant context.

    WHY: Enables analytics on which interaction types drive learning outcomes
    """
    CHAT = "chat"  # AI assistant conversations
    EXERCISE_SUBMISSION = "exercise_submission"  # Code or text exercise submissions
    QUIZ_ATTEMPT = "quiz_attempt"  # Quiz completion attempts
    LAB_SESSION = "lab_session"  # Docker container lab sessions
    PROGRESS_UPDATE = "progress_update"  # Manual progress checkpoints

class ProgressLevel(Enum):
    """
    Student Progress Level Enumeration

    BUSINESS REQUIREMENT:
    Students progress through levels based on completion rate and quiz scores.
    Levels determine content difficulty and AI assistant guidance style.

    TECHNICAL IMPLEMENTATION:
    - BEGINNER: <30% complete OR <60% avg quiz score
    - INTERMEDIATE: 30-60% complete AND 60-75% avg quiz score
    - ADVANCED: 60-80% complete AND 75-85% avg quiz score
    - EXPERT: 80%+ complete AND 85%+ avg quiz score

    WHY: Adaptive learning - adjusts content difficulty to student performance
    """
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class StudentProgress:
    """
    Student Progress Domain Entity - Tracks Learning Journey

    BUSINESS REQUIREMENT:
    Track student progress for adaptive learning, instructor analytics, and
    personalized AI assistant interactions. Progress includes completion rates,
    quiz scores, identified strengths/weaknesses, and time investment.

    TECHNICAL IMPLEMENTATION:
    - Auto-calculates progress level based on completion and quiz scores
    - Tracks knowledge areas for skill mapping
    - Identifies struggling students (needs_help) and high performers
    - Integrates with AI for personalized content recommendations

    WHY: Enables data-driven teaching and personalized learning experiences
    """
    course_id: str  # Course being tracked
    student_id: str  # Student whose progress is tracked
    completed_exercises: int  # Number of exercises completed
    total_exercises: int  # Total exercises in course
    quiz_scores: List[float]  # All quiz scores (0-100)
    knowledge_areas: List[str]  # Topics student has studied
    current_level: ProgressLevel  # Auto-calculated proficiency level
    last_activity: datetime  # Last interaction timestamp
    id: Optional[str] = None  # Auto-generated UUID
    strengths: List[str] = field(default_factory=list)  # Identified strong areas
    weaknesses: List[str] = field(default_factory=list)  # Identified weak areas
    learning_preferences: Dict[str, any] = field(default_factory=dict)  # Learning style data
    time_spent_minutes: int = 0  # Total time invested in course
    created_at: Optional[datetime] = None  # Enrollment timestamp
    updated_at: Optional[datetime] = None  # Last update timestamp
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules"""
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not self.student_id:
            raise ValueError("Student ID is required")
        
        if self.completed_exercises < 0:
            raise ValueError("Completed exercises cannot be negative")
        
        if self.total_exercises < 0:
            raise ValueError("Total exercises cannot be negative")
        
        if self.completed_exercises > self.total_exercises:
            raise ValueError("Completed exercises cannot exceed total exercises")
        
        # Validate quiz scores are between 0 and 100
        for score in self.quiz_scores:
            if not (0 <= score <= 100):
                raise ValueError("Quiz scores must be between 0 and 100")
        
        if self.time_spent_minutes < 0:
            raise ValueError("Time spent cannot be negative")
    
    def get_completion_percentage(self) -> float:
        """Get overall completion percentage"""
        if self.total_exercises == 0:
            return 0.0
        return (self.completed_exercises / self.total_exercises) * 100
    
    def get_average_quiz_score(self) -> float:
        """Get average quiz score"""
        if not self.quiz_scores:
            return 0.0
        return sum(self.quiz_scores) / len(self.quiz_scores)
    
    def add_quiz_score(self, score: float) -> None:
        """Add a new quiz score"""
        if not (0 <= score <= 100):
            raise ValueError("Quiz score must be between 0 and 100")
        
        self.quiz_scores.append(score)
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Update level based on performance
        self._update_level()
    
    def complete_exercise(self) -> None:
        """Mark an exercise as completed"""
        self.completed_exercises += 1
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Update level based on progress
        self._update_level()
    
    def add_knowledge_area(self, area: str) -> None:
        """Add a knowledge area"""
        if area and area.strip() and area not in self.knowledge_areas:
            self.knowledge_areas.append(area.strip())
            self.updated_at = datetime.utcnow()
    
    def add_strength(self, strength: str) -> None:
        """Add a strength"""
        if strength and strength.strip() and strength not in self.strengths:
            self.strengths.append(strength.strip())
            self.updated_at = datetime.utcnow()
    
    def add_weakness(self, weakness: str) -> None:
        """Add a weakness"""
        if weakness and weakness.strip() and weakness not in self.weaknesses:
            self.weaknesses.append(weakness.strip())
            self.updated_at = datetime.utcnow()
    
    def add_time_spent(self, minutes: int) -> None:
        """Add time spent studying"""
        if minutes <= 0:
            raise ValueError("Time spent must be positive")
        
        self.time_spent_minutes += minutes
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def _update_level(self) -> None:
        """
        Auto-calculate student proficiency level

        BUSINESS REQUIREMENT:
        Student level determines AI difficulty, content recommendations, and
        instructor intervention priorities.

        WHY: Adaptive learning - automatically adjusts to student performance
        """
        completion_rate = self.get_completion_percentage()
        avg_quiz_score = self.get_average_quiz_score()

        # Level calculation logic (see ProgressLevel enum for thresholds)
        if completion_rate >= 80 and avg_quiz_score >= 85:
            self.current_level = ProgressLevel.EXPERT
        elif completion_rate >= 60 and avg_quiz_score >= 75:
            self.current_level = ProgressLevel.ADVANCED
        elif completion_rate >= 30 and avg_quiz_score >= 60:
            self.current_level = ProgressLevel.INTERMEDIATE
        else:
            self.current_level = ProgressLevel.BEGINNER

    def needs_help(self) -> bool:
        """
        Identify students who need instructor intervention

        Returns:
            True if struggling (avg score <60% or <20% complete after 2+ quizzes)

        WHY: Proactive student support - alerts instructors to at-risk students
        """
        avg_score = self.get_average_quiz_score()
        completion_rate = self.get_completion_percentage()

        return avg_score < 60 or (completion_rate < 20 and len(self.quiz_scores) >= 2)

    def is_high_performer(self) -> bool:
        """
        Identify high-performing students for advanced content

        Returns:
            True if avg score ≥85% and completion ≥70%

        WHY: Enables accelerated tracks and peer mentorship opportunities
        """
        avg_score = self.get_average_quiz_score()
        completion_rate = self.get_completion_percentage()

        return avg_score >= 85 and completion_rate >= 70

@dataclass
class ChatInteraction:
    """
    Chat Interaction Domain Entity - RAG AI Assistant Conversations

    BUSINESS REQUIREMENT:
    Students interact with RAG-enhanced AI assistant for help with concepts,
    exercises, and quizzes. All interactions are logged for analytics and
    AI model improvement.

    TECHNICAL IMPLEMENTATION:
    - Stores full conversation context for RAG retrieval
    - Tracks confidence scores for answer quality monitoring
    - Auto-extracts topics for knowledge graph integration
    - Sentiment analysis for student satisfaction tracking

    WHY: Enables personalized AI assistance and tracks learning conversations
    """
    course_id: str  # Course context for RAG retrieval
    student_id: str  # Student having conversation
    user_message: str  # Student's question or input
    ai_response: str  # AI-generated response
    context: Dict  # RAG context, progress data, conversation history
    id: Optional[str] = None  # Auto-generated UUID
    topic: Optional[str] = None  # Auto-extracted topic (e.g., 'assessment', 'concept_explanation')
    sentiment: Optional[str] = None  # Student sentiment (positive, neutral, negative)
    confidence_score: Optional[float] = None  # AI confidence (0.0-1.0)
    created_at: Optional[datetime] = None  # Interaction timestamp
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules"""
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not self.student_id:
            raise ValueError("Student ID is required")
        
        if not self.user_message or len(self.user_message.strip()) == 0:
            raise ValueError("User message cannot be empty")
        
        if not self.ai_response or len(self.ai_response.strip()) == 0:
            raise ValueError("AI response cannot be empty")
        
        if not isinstance(self.context, dict):
            raise ValueError("Context must be a dictionary")
        
        if self.confidence_score is not None and not (0 <= self.confidence_score <= 1):
            raise ValueError("Confidence score must be between 0 and 1")
    
    def was_helpful(self) -> bool:
        """Check if the interaction was likely helpful based on confidence"""
        return self.confidence_score is not None and self.confidence_score >= 0.7
    
    def extract_topic(self) -> str:
        """Extract or return the topic of the conversation"""
        if self.topic:
            return self.topic
        
        # Simple topic extraction (could be enhanced with NLP)
        message_lower = self.user_message.lower()
        if any(word in message_lower for word in ['quiz', 'test', 'exam']):
            return 'assessment'
        elif any(word in message_lower for word in ['exercise', 'homework', 'practice']):
            return 'exercise'
        elif any(word in message_lower for word in ['concept', 'understand', 'explain']):
            return 'concept_explanation'
        else:
            return 'general'

@dataclass
class LabSession:
    """
    Lab Session Domain Entity - Docker Container Coding Sessions

    BUSINESS REQUIREMENT:
    Students work in isolated Docker container environments with multiple IDEs
    (VSCode, Jupyter, RStudio). Sessions persist code files, track AI assistant
    interactions, and monitor progress on lab exercises.

    TECHNICAL IMPLEMENTATION:
    - Each session maps to a Docker container instance
    - Code files stored as key-value pairs (filename -> content)
    - AI conversation history for context-aware assistance
    - Environment state tracks installed packages, config changes
    - Session duration monitoring for resource management

    WHY: Enables hands-on coding practice with AI guidance in isolated environments
    """
    course_id: str  # Course context
    student_id: str  # Student owning this session
    session_data: Dict  # Container metadata, IDE preferences
    code_files: Dict[str, str]  # Filename -> file content mapping
    id: Optional[str] = None  # Auto-generated UUID
    current_exercise: Optional[str] = None  # Active exercise ID
    progress_data: Dict = field(default_factory=dict)  # Exercise completion states
    ai_conversation_history: List[Dict] = field(default_factory=list)  # In-lab AI chat
    environment_state: Dict = field(default_factory=dict)  # Docker env state
    started_at: Optional[datetime] = None  # Session start time
    last_activity: Optional[datetime] = None  # Last interaction time
    ended_at: Optional[datetime] = None  # Session end time (container stopped)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.started_at:
            self.started_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules"""
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not self.student_id:
            raise ValueError("Student ID is required")
        
        if not isinstance(self.session_data, dict):
            raise ValueError("Session data must be a dictionary")
        
        if not isinstance(self.code_files, dict):
            raise ValueError("Code files must be a dictionary")
        
        if not isinstance(self.progress_data, dict):
            raise ValueError("Progress data must be a dictionary")
        
        if not isinstance(self.ai_conversation_history, list):
            raise ValueError("AI conversation history must be a list")
    
    def add_code_file(self, filename: str, content: str) -> None:
        """Add or update a code file"""
        if not filename or len(filename.strip()) == 0:
            raise ValueError("Filename cannot be empty")
        
        self.code_files[filename.strip()] = content
        self.last_activity = datetime.utcnow()
    
    def remove_code_file(self, filename: str) -> bool:
        """Remove a code file"""
        if filename in self.code_files:
            del self.code_files[filename]
            self.last_activity = datetime.utcnow()
            return True
        return False
    
    def add_ai_conversation(self, user_message: str, ai_response: str, context: Dict = None) -> None:
        """Add an AI conversation to the history"""
        conversation = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'context': context or {}
        }
        
        self.ai_conversation_history.append(conversation)
        self.last_activity = datetime.utcnow()
    
    def update_progress(self, exercise_id: str, progress_data: Dict) -> None:
        """Update progress for a specific exercise"""
        if not exercise_id:
            raise ValueError("Exercise ID is required")
        
        self.progress_data[exercise_id] = {
            'data': progress_data,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        self.current_exercise = exercise_id
        self.last_activity = datetime.utcnow()
    
    def end_session(self) -> None:
        """End the lab session"""
        if self.ended_at:
            raise ValueError("Session is already ended")
        
        self.ended_at = datetime.utcnow()
    
    def get_session_duration_minutes(self) -> Optional[int]:
        """Get session duration in minutes"""
        if not self.started_at:
            return None
        
        end_time = self.ended_at or datetime.utcnow()
        duration = end_time - self.started_at
        return int(duration.total_seconds() / 60)
    
    def is_active(self) -> bool:
        """Check if session is still active"""
        return self.ended_at is None
    
    def get_files_count(self) -> int:
        """Get number of code files in session"""
        return len(self.code_files)
    
    def has_code_in_language(self, language: str) -> bool:
        """Check if session has code files in specific language"""
        extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cc', '.cxx'],
            'c': ['.c'],
            'html': ['.html', '.htm'],
            'css': ['.css']
        }
        
        lang_extensions = extensions.get(language.lower(), [])
        
        return any(
            any(filename.lower().endswith(ext) for ext in lang_extensions)
            for filename in self.code_files.keys()
        )

@dataclass
class DynamicContentRequest:
    """
    Dynamic Content Generation Request Value Object

    BUSINESS REQUIREMENT:
    AI generates personalized content (exercises, quizzes, explanations, hints)
    based on student progress, weaknesses, and learning style.

    TECHNICAL IMPLEMENTATION:
    - Includes full student progress context for AI personalization
    - Supports 4 content types: exercise, quiz, explanation, hint
    - Validates all parameters before expensive AI generation
    - Extracts key metrics for RAG context

    WHY: Enables adaptive learning with AI-generated personalized content
    """
    course_id: str  # Course context
    student_progress: Dict  # StudentProgress entity serialized
    context: Dict  # Additional context (current topic, recent errors, etc.)
    content_type: str  # Type to generate: exercise, quiz, explanation, hint

    def validate(self) -> None:
        """
        Validate content generation request

        Raises:
            ValueError: If any parameter is invalid

        WHY: Prevents invalid AI requests that waste tokens and time
        """
        if not self.course_id:
            raise ValueError("Course ID is required")

        if not isinstance(self.student_progress, dict):
            raise ValueError("Student progress must be a dictionary")

        if not isinstance(self.context, dict):
            raise ValueError("Context must be a dictionary")

        valid_content_types = ["exercise", "quiz", "explanation", "hint"]
        if self.content_type not in valid_content_types:
            raise ValueError(f"Content type must be one of: {', '.join(valid_content_types)}")

    def get_student_level(self) -> str:
        """Extract student proficiency level for content difficulty"""
        return self.student_progress.get('current_level', 'beginner')

    def get_completion_rate(self) -> float:
        """Calculate student completion percentage for adaptive pacing"""
        completed = self.student_progress.get('completed_exercises', 0)
        total = self.student_progress.get('total_exercises', 1)
        return (completed / total) * 100 if total > 0 else 0.0

    def get_average_score(self) -> float:
        """Calculate average quiz score for difficulty calibration"""
        scores = self.student_progress.get('quiz_scores', [])
        return sum(scores) / len(scores) if scores else 0.0