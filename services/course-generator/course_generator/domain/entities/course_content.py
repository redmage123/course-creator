"""
Course Content Domain Entities
Single Responsibility: Represent course content generation domain concepts
"""
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

class DifficultyLevel(Enum):
    """
    Content Difficulty Level - Aligns with Student Progress Levels

    WHY: Ensures content difficulty matches student proficiency for optimal learning
    """
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ContentType(Enum):
    """
    Course Content Type - Types of AI-Generatable Content

    WHY: Categorizes content for generation pipelines and storage organization
    """
    SYLLABUS = "syllabus"  # Course outline and learning objectives
    SLIDE = "slide"  # Presentation slide content
    EXERCISE = "exercise"  # Practice exercises and coding challenges
    QUIZ = "quiz"  # Assessment questions
    LAB = "lab"  # Docker container lab environments

class JobStatus(Enum):
    """
    Content Generation Job Status

    WHY: Tracks async AI content generation jobs for progress monitoring
    """
    PENDING = "pending"  # Job queued, not started
    RUNNING = "running"  # AI generation in progress
    COMPLETED = "completed"  # Successfully generated
    FAILED = "failed"  # Generation error occurred
    CANCELLED = "cancelled"  # User cancelled job

class SlideType(Enum):
    """
    Slide Type for Course Presentations

    WHY: Different slide types have different layouts and content structures
    """
    TITLE = "title"  # Course/module title slide
    CONTENT = "content"  # Main content slide
    EXERCISE = "exercise"  # Embedded exercise slide
    SUMMARY = "summary"  # Module summary slide

@dataclass
class CourseTemplate:
    """Domain entity representing a course generation template"""
    name: str
    description: str
    parameters: Dict
    id: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules"""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Template name cannot be empty")
        
        if not self.description or len(self.description.strip()) == 0:
            raise ValueError("Template description cannot be empty")
        
        if not isinstance(self.parameters, dict):
            raise ValueError("Template parameters must be a dictionary")

@dataclass
class Syllabus:
    """Domain entity representing a course syllabus"""
    course_id: str
    title: str
    description: str
    category: str
    difficulty_level: DifficultyLevel
    estimated_duration: int
    id: Optional[str] = None
    learning_objectives: List[str] = field(default_factory=list)
    topics: List[Dict] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    resources: List[Dict] = field(default_factory=list)
    assessment_methods: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
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
        
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Syllabus title cannot be empty")
        
        if not self.description or len(self.description.strip()) == 0:
            raise ValueError("Syllabus description cannot be empty")
        
        if self.estimated_duration <= 0:
            raise ValueError("Estimated duration must be positive")
    
    def add_learning_objective(self, objective: str) -> None:
        """Add a learning objective"""
        if objective and objective.strip():
            self.learning_objectives.append(objective.strip())
            self.updated_at = datetime.utcnow()
    
    def add_topic(self, topic_name: str, duration_hours: int, subtopics: List[str] = None) -> None:
        """Add a topic to the syllabus"""
        if not topic_name or len(topic_name.strip()) == 0:
            raise ValueError("Topic name cannot be empty")
        
        if duration_hours <= 0:
            raise ValueError("Topic duration must be positive")
        
        topic = {
            'name': topic_name.strip(),
            'duration_hours': duration_hours,
            'subtopics': subtopics or []
        }
        
        self.topics.append(topic)
        self.updated_at = datetime.utcnow()
    
    def get_total_duration(self) -> int:
        """Get total duration from all topics"""
        return sum(topic.get('duration_hours', 0) for topic in self.topics)

@dataclass
class Slide:
    """Domain entity representing a course slide"""
    title: str
    content: str
    slide_type: SlideType
    order: int
    course_id: str
    id: Optional[str] = None
    topic: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules"""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Slide title cannot be empty")
        
        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Slide content cannot be empty")
        
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if self.order < 0:
            raise ValueError("Slide order must be non-negative")
    
    def update_content(self, title: Optional[str] = None, content: Optional[str] = None, 
                      notes: Optional[str] = None) -> None:
        """Update slide content"""
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        if notes is not None:
            self.notes = notes
        
        self.updated_at = datetime.utcnow()
        self.validate()

@dataclass
class Exercise:
    """Domain entity representing a course exercise"""
    course_id: str
    topic: str
    difficulty: DifficultyLevel
    title: str
    description: str
    instructions: str
    id: Optional[str] = None
    solution: Optional[str] = None
    hints: List[str] = field(default_factory=list)
    test_cases: List[Dict] = field(default_factory=list)
    expected_time_minutes: Optional[int] = None
    language: Optional[str] = None
    starter_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
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
        
        if not self.topic or len(self.topic.strip()) == 0:
            raise ValueError("Exercise topic cannot be empty")
        
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Exercise title cannot be empty")
        
        if not self.description or len(self.description.strip()) == 0:
            raise ValueError("Exercise description cannot be empty")
        
        if not self.instructions or len(self.instructions.strip()) == 0:
            raise ValueError("Exercise instructions cannot be empty")
        
        if self.expected_time_minutes is not None and self.expected_time_minutes <= 0:
            raise ValueError("Expected time must be positive")
    
    def add_hint(self, hint: str) -> None:
        """Add a hint to the exercise"""
        if hint and hint.strip():
            self.hints.append(hint.strip())
            self.updated_at = datetime.utcnow()
    
    def add_test_case(self, input_data: str, expected_output: str, description: Optional[str] = None) -> None:
        """Add a test case to the exercise"""
        test_case = {
            'input': input_data,
            'expected_output': expected_output,
            'description': description or f"Test case {len(self.test_cases) + 1}"
        }
        
        self.test_cases.append(test_case)
        self.updated_at = datetime.utcnow()
    
    def is_programming_exercise(self) -> bool:
        """Check if this is a programming exercise"""
        return self.language is not None or self.starter_code is not None

@dataclass
class LabEnvironment:
    """Domain entity representing a lab environment"""
    course_id: str
    name: str
    description: str
    environment_type: str
    config: Dict
    exercises: List[Dict]
    id: Optional[str] = None
    docker_image: Optional[str] = None
    ports: List[int] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    setup_scripts: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
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
        
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Lab environment name cannot be empty")
        
        if not self.description or len(self.description.strip()) == 0:
            raise ValueError("Lab environment description cannot be empty")
        
        if not self.environment_type or len(self.environment_type.strip()) == 0:
            raise ValueError("Environment type is required")
        
        if not isinstance(self.config, dict):
            raise ValueError("Configuration must be a dictionary")
        
        if not isinstance(self.exercises, list):
            raise ValueError("Exercises must be a list")
    
    def add_exercise(self, exercise_id: str, exercise_config: Dict) -> None:
        """Add an exercise to the lab environment"""
        if not exercise_id:
            raise ValueError("Exercise ID is required")
        
        exercise_entry = {
            'exercise_id': exercise_id,
            'config': exercise_config,
            'added_at': datetime.utcnow().isoformat()
        }
        
        self.exercises.append(exercise_entry)
        self.updated_at = datetime.utcnow()
    
    def add_port(self, port: int) -> None:
        """Add a port to the lab environment"""
        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ValueError("Port must be a valid integer between 1 and 65535")
        
        if port not in self.ports:
            self.ports.append(port)
            self.updated_at = datetime.utcnow()
    
    def set_environment_variable(self, key: str, value: str) -> None:
        """Set an environment variable"""
        if not key or len(key.strip()) == 0:
            raise ValueError("Environment variable key cannot be empty")
        
        self.environment_variables[key.strip()] = value
        self.updated_at = datetime.utcnow()

@dataclass
class GenerationJob:
    """
    Content Generation Job Domain Entity - Async AI Content Generation

    BUSINESS REQUIREMENT:
    Instructors request AI-generated content (syllabi, quizzes, exercises, labs).
    Generation is async (10-60 seconds) so jobs are queued, tracked, and provide
    progress feedback to avoid UI blocking.

    TECHNICAL IMPLEMENTATION:
    - Tracks job lifecycle: PENDING → RUNNING → COMPLETED/FAILED/CANCELLED
    - Stores generation parameters for retry/debugging
    - Records timing metrics for performance monitoring
    - Supports scheduled generation for batch operations
    - Progress percentage for real-time UI updates

    WHY: Enables responsive UI for expensive AI operations and provides audit trail
    """
    content_type: ContentType  # Type of content being generated
    course_id: str  # Course context for generation
    parameters: Dict  # Generation parameters (topic, difficulty, count, etc.)
    status: JobStatus = JobStatus.PENDING  # Current job state
    id: Optional[str] = None  # Auto-generated UUID
    result: Optional[Dict] = None  # Generated content (set on COMPLETED)
    error_message: Optional[str] = None  # Error details (set on FAILED)
    created_at: Optional[datetime] = None  # Job created timestamp
    started_at: Optional[datetime] = None  # Generation started timestamp
    completed_at: Optional[datetime] = None  # Job finished timestamp
    progress_percentage: int = 0  # Progress indicator (0-100)
    scheduled_time: Optional[datetime] = None  # For batch/scheduled generation
    metadata: Dict = field(default_factory=dict)  # Additional tracking data
    
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
        
        if not isinstance(self.parameters, dict):
            raise ValueError("Parameters must be a dictionary")
        
        if not isinstance(self.status, JobStatus):
            raise ValueError(f"Status must be a JobStatus enum value")
    
    def start(self) -> None:
        """
        Start AI content generation

        Raises:
            ValueError: If job is not in PENDING state

        WHY: Transitions job to RUNNING state and records start time for metrics
        """
        if self.status != JobStatus.PENDING:
            raise ValueError("Can only start pending jobs")

        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete(self, result: Dict) -> None:
        """
        Mark job as successfully completed with generated content

        Args:
            result: The generated content (syllabus, quiz, exercise, etc.)

        Raises:
            ValueError: If job is not RUNNING

        WHY: Stores generated content and marks job complete for instructor review
        """
        if self.status != JobStatus.RUNNING:
            raise ValueError("Can only complete running jobs")

        self.status = JobStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100

    def fail(self, error_message: str) -> None:
        """
        Mark job as failed with error details

        Args:
            error_message: Description of what went wrong

        WHY: Records failures for debugging and instructor notification
        """
        if self.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise ValueError("Can only fail pending or running jobs")

        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def cancel(self) -> None:
        """
        Cancel job (user-initiated)

        WHY: Allows instructors to cancel long-running or incorrect generation requests
        """
        if self.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise ValueError("Can only cancel pending or running jobs")

        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """Check if job completed successfully"""
        return self.status == JobStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if job failed"""
        return self.status == JobStatus.FAILED

    def get_duration_seconds(self) -> Optional[int]:
        """
        Calculate job duration for performance monitoring

        Returns:
            Duration in seconds, or None if not completed

        WHY: Tracks AI generation performance for optimization
        """
        if not self.started_at or not self.completed_at:
            return None

        duration = self.completed_at - self.started_at
        return int(duration.total_seconds())