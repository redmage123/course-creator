"""
Data Models and Enums for Content Management Service
Defines data structures, enums, and validation models
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass


# ===================================
# ENUMS
# ===================================

class ContentType(str, Enum):
    """Content type enumeration"""
    SYLLABUS = "syllabus"
    SLIDES = "slides"
    MATERIALS = "materials"
    EXERCISES = "exercises"
    QUIZZES = "quizzes"
    LABS = "labs"
    EXPORTS = "exports"
    TEMP = "temp"


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(str, Enum):
    """Export format enumeration"""
    POWERPOINT = "powerpoint"
    JSON = "json"
    PDF = "pdf"
    EXCEL = "excel"
    ZIP = "zip"
    SCORM = "scorm"


class DifficultyLevel(str, Enum):
    """Difficulty level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class QuestionType(str, Enum):
    """Quiz question type enumeration"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_IN_BLANK = "fill_in_blank"
    MATCHING = "matching"


class ExerciseType(str, Enum):
    """Exercise type enumeration"""
    CODING = "coding"
    CONCEPTUAL = "conceptual"
    PROBLEM_SOLVING = "problem_solving"
    PRACTICAL = "practical"
    RESEARCH = "research"
    PRESENTATION = "presentation"


class SlideType(str, Enum):
    """Slide type enumeration"""
    TITLE = "title"
    CONTENT = "content"
    SECTION = "section"
    BULLET_POINTS = "bullet_points"
    IMAGE = "image"
    VIDEO = "video"
    EXERCISE = "exercise"
    QUIZ = "quiz"


# ===================================
# PYDANTIC MODELS
# ===================================

class BaseContentModel(BaseModel):
    """Base model for all content"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    course_id: Optional[str] = None
    tags: Optional[List[str]] = []
    
    class Config:
        use_enum_values = True


class CourseInfo(BaseModel):
    """Course information model"""
    course_code: Optional[str] = None
    course_title: str
    instructor: Optional[str] = None
    department: Optional[str] = None
    credits: Optional[int] = None
    duration_weeks: Optional[int] = None
    prerequisites: Optional[List[str]] = []
    
    @validator('duration_weeks')
    def validate_duration(cls, v):
        if v is not None and (v < 1 or v > 52):
            raise ValueError('Duration must be between 1 and 52 weeks')
        return v


class LearningObjective(BaseModel):
    """Learning objective model"""
    id: Optional[str] = None
    objective: str
    bloom_level: Optional[str] = None  # Knowledge, Comprehension, Application, etc.
    assessment_method: Optional[str] = None
    module_id: Optional[str] = None


class CourseModule(BaseModel):
    """Course module model"""
    module_id: str
    title: str
    description: Optional[str] = None
    week_number: Optional[int] = None
    duration_hours: Optional[float] = None
    learning_objectives: List[LearningObjective] = []
    topics: List[str] = []
    readings: Optional[List[str]] = []
    assignments: Optional[List[str]] = []
    
    @validator('duration_hours')
    def validate_duration_hours(cls, v):
        if v is not None and v < 0:
            raise ValueError('Duration hours must be non-negative')
        return v


class SyllabusContent(BaseContentModel):
    """Syllabus content model"""
    course_info: CourseInfo
    learning_objectives: List[LearningObjective] = []
    modules: List[CourseModule] = []
    assessment_methods: List[str] = []
    grading_scheme: Optional[Dict[str, float]] = None
    policies: Optional[Dict[str, str]] = None
    schedule: Optional[List[Dict[str, Any]]] = []
    textbooks: Optional[List[str]] = []


class SlideContent(BaseContentModel):
    """Slide content model"""
    slide_number: int
    slide_type: SlideType = SlideType.CONTENT
    content: str
    speaker_notes: Optional[str] = None
    layout: Optional[str] = None
    background: Optional[str] = None
    animations: Optional[List[str]] = []
    duration_minutes: Optional[float] = None
    
    @validator('slide_number')
    def validate_slide_number(cls, v):
        if v < 1:
            raise ValueError('Slide number must be positive')
        return v


class SlidesCollection(BaseContentModel):
    """Collection of slides"""
    slides: List[SlideContent]
    total_duration_minutes: Optional[float] = None
    presentation_style: Optional[str] = None
    theme: Optional[str] = None
    
    @validator('slides')
    def validate_slides(cls, v):
        if not v:
            raise ValueError('At least one slide is required')
        return v


class QuizQuestion(BaseModel):
    """Quiz question model"""
    question_id: str
    question: str
    question_type: QuestionType
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: Union[str, bool, List[str]]
    explanation: Optional[str] = None
    points: int = 1
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    tags: Optional[List[str]] = []
    
    @validator('points')
    def validate_points(cls, v):
        if v < 0:
            raise ValueError('Points must be non-negative')
        return v
    
    @validator('options')
    def validate_options(cls, v, values):
        if values.get('question_type') == QuestionType.MULTIPLE_CHOICE and not v:
            raise ValueError('Multiple choice questions must have options')
        return v


class Quiz(BaseContentModel):
    """Quiz model"""
    questions: List[QuizQuestion]
    time_limit_minutes: Optional[int] = None
    attempts_allowed: int = 1
    shuffle_questions: bool = False
    shuffle_options: bool = False
    show_correct_answers: bool = True
    passing_score: Optional[float] = None
    
    @validator('time_limit_minutes')
    def validate_time_limit(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Time limit must be positive')
        return v
    
    @validator('attempts_allowed')
    def validate_attempts(cls, v):
        if v < 1:
            raise ValueError('At least one attempt must be allowed')
        return v
    
    @validator('passing_score')
    def validate_passing_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Passing score must be between 0 and 100')
        return v


class ExerciseStep(BaseModel):
    """Exercise step model"""
    step_number: int
    instruction: str
    expected_output: Optional[str] = None
    hints: Optional[List[str]] = []
    code_template: Optional[str] = None
    
    @validator('step_number')
    def validate_step_number(cls, v):
        if v < 1:
            raise ValueError('Step number must be positive')
        return v


class Exercise(BaseContentModel):
    """Exercise model"""
    exercise_type: ExerciseType
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    estimated_time_minutes: Optional[int] = None
    learning_objectives: List[str] = []
    prerequisites: Optional[List[str]] = []
    steps: List[ExerciseStep] = []
    solution: Optional[str] = None
    grading_rubric: Optional[Dict[str, Any]] = None
    resources: Optional[List[str]] = []
    
    @validator('estimated_time_minutes')
    def validate_time(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Estimated time must be positive')
        return v


class LabEnvironment(BaseContentModel):
    """Lab environment model"""
    environment_type: str = "docker"
    base_image: Optional[str] = None
    tools: List[Dict[str, Any]] = []
    datasets: List[Dict[str, Any]] = []
    setup_scripts: List[str] = []
    access_instructions: Optional[str] = None
    estimated_setup_time_minutes: Optional[int] = None
    resource_requirements: Optional[Dict[str, Any]] = None
    
    @validator('estimated_setup_time_minutes')
    def validate_setup_time(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Setup time must be positive')
        return v


class AIGenerationRequest(BaseModel):
    """AI content generation request model"""
    content_type: ContentType
    source_content: Optional[Dict[str, Any]] = None
    custom_prompt: Optional[str] = None
    parameters: Dict[str, Any] = {}
    user_preferences: Optional[Dict[str, Any]] = {}
    
    @validator('content_type')
    def validate_content_type(cls, v):
        valid_types = [ContentType.SLIDES, ContentType.EXERCISES, ContentType.QUIZZES, ContentType.LABS]
        if v not in valid_types:
            raise ValueError(f'Content type must be one of: {[t.value for t in valid_types]}')
        return v


class ProcessingTask(BaseModel):
    """Processing task model"""
    task_id: str
    task_type: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress_percentage: int = 0
    message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    
    @validator('progress_percentage')
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Progress must be between 0 and 100')
        return v


class ExportRequest(BaseModel):
    """Export request model"""
    content_id: str
    format: ExportFormat
    options: Optional[Dict[str, Any]] = {}
    include_metadata: bool = True
    
    @validator('format')
    def validate_format(cls, v):
        return v


class FileUploadRequest(BaseModel):
    """File upload request model"""
    content_type: ContentType
    filename: str
    file_size: int
    mime_type: Optional[str] = None
    process_with_ai: bool = False
    course_id: Optional[str] = None
    
    @validator('file_size')
    def validate_file_size(cls, v):
        max_size = 100 * 1024 * 1024  # 100MB
        if v <= 0:
            raise ValueError('File size must be positive')
        if v > max_size:
            raise ValueError(f'File size exceeds maximum limit of {max_size} bytes')
        return v


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    content_types: Optional[List[ContentType]] = None
    filters: Optional[Dict[str, Any]] = {}
    sort_by: Optional[str] = "created_at"
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v.lower()
    
    @validator('limit')
    def validate_limit(cls, v):
        if v <= 0 or v > 1000:
            raise ValueError('Limit must be between 1 and 1000')
        return v


class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any]
    total_count: int
    page_size: int
    current_page: int
    total_pages: int
    has_next: bool
    has_previous: bool


# ===================================
# UTILITY FUNCTIONS
# ===================================

def create_api_response(success: bool, message: str, data: Any = None, 
                       error_code: str = None) -> APIResponse:
    """Create standardized API response"""
    return APIResponse(
        success=success,
        message=message,
        data=data,
        error_code=error_code
    )


def create_paginated_response(items: List[Any], total_count: int, 
                            page_size: int, current_page: int) -> PaginatedResponse:
    """Create paginated response"""
    total_pages = (total_count + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=items,
        total_count=total_count,
        page_size=page_size,
        current_page=current_page,
        total_pages=total_pages,
        has_next=current_page < total_pages,
        has_previous=current_page > 1
    )


def validate_content_type_format(content_type: str, file_extension: str) -> bool:
    """Validate file format for content type"""
    format_mapping = {
        ContentType.SYLLABUS: ['.pdf', '.doc', '.docx', '.txt'],
        ContentType.SLIDES: ['.ppt', '.pptx', '.pdf', '.json'],
        ContentType.MATERIALS: ['.pdf', '.doc', '.docx', '.zip', '.jpg', '.png', '.mp4', '.mp3']
    }
    
    allowed_formats = format_mapping.get(ContentType(content_type), [])
    return file_extension.lower() in allowed_formats


# ===================================
# DATACLASSES FOR INTERNAL USE
# ===================================

@dataclass
class ProcessingMetrics:
    """Metrics for processing operations"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_processing_time_seconds: float = 0.0
    peak_concurrent_requests: int = 0


@dataclass
class SystemHealth:
    """System health status"""
    status: str = "healthy"
    version: str = "1.0.0"
    uptime_seconds: int = 0
    total_files_processed: int = 0
    storage_usage_bytes: int = 0
    active_processing_tasks: int = 0
    last_health_check: Optional[datetime] = None