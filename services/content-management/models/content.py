"""
Content models for Content Management Service.

This module defines all content-related models including
syllabus, slides, exercises, quizzes, and labs.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from models.common import (
    BaseContentModel, ContentType, DifficultyLevel, ExportFormat,
    ProcessingStatus
)


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


# Course Information Models
class CourseInfo(BaseModel):
    """Course information model"""
    course_code: Optional[str] = Field(None, max_length=20)
    course_title: str = Field(..., min_length=1, max_length=200)
    instructor: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    credits: Optional[int] = Field(None, ge=0, le=20)
    duration_weeks: Optional[int] = Field(None, ge=1, le=52)
    prerequisites: List[str] = Field(default_factory=list)


class LearningObjective(BaseModel):
    """Learning objective model"""
    id: Optional[str] = None
    objective: str = Field(..., min_length=1, max_length=500)
    bloom_level: Optional[str] = Field(None, max_length=50)
    assessment_method: Optional[str] = Field(None, max_length=100)
    module_id: Optional[str] = None


class CourseModule(BaseModel):
    """Course module model"""
    module_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    week_number: Optional[int] = Field(None, ge=1, le=52)
    duration_hours: Optional[float] = Field(None, ge=0, le=168)
    learning_objectives: List[LearningObjective] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    readings: List[str] = Field(default_factory=list)
    assignments: List[str] = Field(default_factory=list)


# Syllabus Models
class SyllabusContent(BaseContentModel):
    """Syllabus content model"""
    course_info: CourseInfo
    learning_objectives: List[LearningObjective] = Field(default_factory=list)
    modules: List[CourseModule] = Field(default_factory=list)
    assessment_methods: List[str] = Field(default_factory=list)
    grading_scheme: Optional[Dict[str, float]] = None
    policies: Optional[Dict[str, str]] = None
    schedule: List[Dict[str, Any]] = Field(default_factory=list)
    textbooks: List[str] = Field(default_factory=list)
    
    @field_validator('grading_scheme')
    @classmethod
    def validate_grading_scheme(cls, v):
        if v is not None:
            total = sum(v.values())
            if abs(total - 100.0) > 0.01:  # Allow for floating point precision
                raise ValueError('Grading scheme must sum to 100%')
        return v


class SyllabusCreate(BaseModel):
    """Model for creating syllabus"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    course_info: CourseInfo
    learning_objectives: List[LearningObjective] = Field(default_factory=list)
    modules: List[CourseModule] = Field(default_factory=list)
    assessment_methods: List[str] = Field(default_factory=list)
    grading_scheme: Optional[Dict[str, float]] = None
    policies: Optional[Dict[str, str]] = None
    schedule: List[Dict[str, Any]] = Field(default_factory=list)
    textbooks: List[str] = Field(default_factory=list)
    course_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SyllabusUpdate(BaseModel):
    """Model for updating syllabus"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    course_info: Optional[CourseInfo] = None
    learning_objectives: Optional[List[LearningObjective]] = None
    modules: Optional[List[CourseModule]] = None
    assessment_methods: Optional[List[str]] = None
    grading_scheme: Optional[Dict[str, float]] = None
    policies: Optional[Dict[str, str]] = None
    schedule: Optional[List[Dict[str, Any]]] = None
    textbooks: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class SyllabusResponse(BaseModel):
    """Model for syllabus response"""
    id: str
    title: str
    description: Optional[str]
    course_info: CourseInfo
    learning_objectives: List[LearningObjective]
    modules: List[CourseModule]
    assessment_methods: List[str]
    grading_scheme: Optional[Dict[str, float]]
    policies: Optional[Dict[str, str]]
    schedule: List[Dict[str, Any]]
    textbooks: List[str]
    course_id: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]


# Slide Models
class SlideContent(BaseContentModel):
    """Slide content model"""
    slide_number: int = Field(..., ge=1)
    slide_type: SlideType = SlideType.CONTENT
    content: str = Field(..., min_length=1)
    speaker_notes: Optional[str] = Field(None, max_length=2000)
    layout: Optional[str] = Field(None, max_length=50)
    background: Optional[str] = Field(None, max_length=100)
    animations: List[str] = Field(default_factory=list)
    duration_minutes: Optional[float] = Field(None, ge=0, le=60)


class SlidesCollection(BaseContentModel):
    """Collection of slides"""
    slides: List[SlideContent] = Field(..., min_items=1)
    total_duration_minutes: Optional[float] = Field(None, ge=0)
    presentation_style: Optional[str] = Field(None, max_length=50)
    theme: Optional[str] = Field(None, max_length=50)
    
    @field_validator('total_duration_minutes')
    @classmethod
    def validate_total_duration(cls, v, info):
        if v is not None and 'slides' in info.data:
            calculated_duration = sum(
                slide.duration_minutes or 0 for slide in info.data['slides']
            )
            if calculated_duration > 0 and abs(v - calculated_duration) > 1:
                raise ValueError('Total duration should match sum of slide durations')
        return v


class SlideCreate(BaseModel):
    """Model for creating slide"""
    title: str = Field(..., min_length=1, max_length=200)
    slide_number: int = Field(..., ge=1)
    slide_type: SlideType = SlideType.CONTENT
    content: str = Field(..., min_length=1)
    speaker_notes: Optional[str] = Field(None, max_length=2000)
    layout: Optional[str] = Field(None, max_length=50)
    background: Optional[str] = Field(None, max_length=100)
    animations: List[str] = Field(default_factory=list)
    duration_minutes: Optional[float] = Field(None, ge=0, le=60)
    course_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SlideUpdate(BaseModel):
    """Model for updating slide"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    slide_number: Optional[int] = Field(None, ge=1)
    slide_type: Optional[SlideType] = None
    content: Optional[str] = Field(None, min_length=1)
    speaker_notes: Optional[str] = Field(None, max_length=2000)
    layout: Optional[str] = Field(None, max_length=50)
    background: Optional[str] = Field(None, max_length=100)
    animations: Optional[List[str]] = None
    duration_minutes: Optional[float] = Field(None, ge=0, le=60)
    tags: Optional[List[str]] = None


class SlideResponse(BaseModel):
    """Model for slide response"""
    id: str
    title: str
    slide_number: int
    slide_type: SlideType
    content: str
    speaker_notes: Optional[str]
    layout: Optional[str]
    background: Optional[str]
    animations: List[str]
    duration_minutes: Optional[float]
    course_id: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]


# Quiz Models
class QuizQuestion(BaseModel):
    """Quiz question model"""
    question_id: str
    question: str = Field(..., min_length=1, max_length=1000)
    question_type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: Union[str, bool, List[str]]
    explanation: Optional[str] = Field(None, max_length=1000)
    points: int = Field(1, ge=0, le=100)
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    tags: List[str] = Field(default_factory=list)
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        if info.data.get('question_type') == QuestionType.MULTIPLE_CHOICE and not v:
            raise ValueError('Multiple choice questions must have options')
        return v


class Quiz(BaseContentModel):
    """Quiz model"""
    questions: List[QuizQuestion] = Field(..., min_items=1)
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=600)
    attempts_allowed: int = Field(1, ge=1, le=10)
    shuffle_questions: bool = False
    shuffle_options: bool = False
    show_correct_answers: bool = True
    passing_score: Optional[float] = Field(None, ge=0, le=100)


class QuizCreate(BaseModel):
    """Model for creating quiz"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    questions: List[QuizQuestion] = Field(..., min_items=1)
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=600)
    attempts_allowed: int = Field(1, ge=1, le=10)
    shuffle_questions: bool = False
    shuffle_options: bool = False
    show_correct_answers: bool = True
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    course_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class QuizUpdate(BaseModel):
    """Model for updating quiz"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    questions: Optional[List[QuizQuestion]] = None
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=600)
    attempts_allowed: Optional[int] = Field(None, ge=1, le=10)
    shuffle_questions: Optional[bool] = None
    shuffle_options: Optional[bool] = None
    show_correct_answers: Optional[bool] = None
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    tags: Optional[List[str]] = None


class QuizResponse(BaseModel):
    """Model for quiz response"""
    id: str
    title: str
    description: Optional[str]
    questions: List[QuizQuestion]
    time_limit_minutes: Optional[int]
    attempts_allowed: int
    shuffle_questions: bool
    shuffle_options: bool
    show_correct_answers: bool
    passing_score: Optional[float]
    course_id: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]


# Exercise Models
class ExerciseStep(BaseModel):
    """Exercise step model"""
    step_number: int = Field(..., ge=1)
    instruction: str = Field(..., min_length=1, max_length=2000)
    expected_output: Optional[str] = Field(None, max_length=1000)
    hints: List[str] = Field(default_factory=list)
    code_template: Optional[str] = Field(None, max_length=5000)


class Exercise(BaseContentModel):
    """Exercise model"""
    exercise_type: ExerciseType
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    estimated_time_minutes: Optional[int] = Field(None, ge=1, le=480)
    learning_objectives: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    steps: List[ExerciseStep] = Field(default_factory=list)
    solution: Optional[str] = Field(None, max_length=10000)
    grading_rubric: Optional[Dict[str, Any]] = None
    resources: List[str] = Field(default_factory=list)


class ExerciseCreate(BaseModel):
    """Model for creating exercise"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    exercise_type: ExerciseType
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    estimated_time_minutes: Optional[int] = Field(None, ge=1, le=480)
    learning_objectives: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    steps: List[ExerciseStep] = Field(default_factory=list)
    solution: Optional[str] = Field(None, max_length=10000)
    grading_rubric: Optional[Dict[str, Any]] = None
    resources: List[str] = Field(default_factory=list)
    course_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ExerciseUpdate(BaseModel):
    """Model for updating exercise"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    exercise_type: Optional[ExerciseType] = None
    difficulty: Optional[DifficultyLevel] = None
    estimated_time_minutes: Optional[int] = Field(None, ge=1, le=480)
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    steps: Optional[List[ExerciseStep]] = None
    solution: Optional[str] = Field(None, max_length=10000)
    grading_rubric: Optional[Dict[str, Any]] = None
    resources: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ExerciseResponse(BaseModel):
    """Model for exercise response"""
    id: str
    title: str
    description: Optional[str]
    exercise_type: ExerciseType
    difficulty: DifficultyLevel
    estimated_time_minutes: Optional[int]
    learning_objectives: List[str]
    prerequisites: List[str]
    steps: List[ExerciseStep]
    solution: Optional[str]
    grading_rubric: Optional[Dict[str, Any]]
    resources: List[str]
    course_id: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]


# Lab Environment Models
class LabEnvironment(BaseContentModel):
    """Lab environment model"""
    environment_type: str = Field("docker", max_length=50)
    base_image: Optional[str] = Field(None, max_length=200)
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    datasets: List[Dict[str, Any]] = Field(default_factory=list)
    setup_scripts: List[str] = Field(default_factory=list)
    access_instructions: Optional[str] = Field(None, max_length=2000)
    estimated_setup_time_minutes: Optional[int] = Field(None, ge=1, le=120)
    resource_requirements: Optional[Dict[str, Any]] = None


class LabEnvironmentCreate(BaseModel):
    """Model for creating lab environment"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    environment_type: str = Field("docker", max_length=50)
    base_image: Optional[str] = Field(None, max_length=200)
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    datasets: List[Dict[str, Any]] = Field(default_factory=list)
    setup_scripts: List[str] = Field(default_factory=list)
    access_instructions: Optional[str] = Field(None, max_length=2000)
    estimated_setup_time_minutes: Optional[int] = Field(None, ge=1, le=120)
    resource_requirements: Optional[Dict[str, Any]] = None
    course_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class LabEnvironmentUpdate(BaseModel):
    """Model for updating lab environment"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    environment_type: Optional[str] = Field(None, max_length=50)
    base_image: Optional[str] = Field(None, max_length=200)
    tools: Optional[List[Dict[str, Any]]] = None
    datasets: Optional[List[Dict[str, Any]]] = None
    setup_scripts: Optional[List[str]] = None
    access_instructions: Optional[str] = Field(None, max_length=2000)
    estimated_setup_time_minutes: Optional[int] = Field(None, ge=1, le=120)
    resource_requirements: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class LabEnvironmentResponse(BaseModel):
    """Model for lab environment response"""
    id: str
    title: str
    description: Optional[str]
    environment_type: str
    base_image: Optional[str]
    tools: List[Dict[str, Any]]
    datasets: List[Dict[str, Any]]
    setup_scripts: List[str]
    access_instructions: Optional[str]
    estimated_setup_time_minutes: Optional[int]
    resource_requirements: Optional[Dict[str, Any]]
    course_id: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]


# AI Generation Models
class AIGenerationRequest(BaseModel):
    """AI content generation request model"""
    content_type: ContentType
    source_content: Optional[Dict[str, Any]] = None
    custom_prompt: Optional[str] = Field(None, max_length=2000)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v):
        valid_types = [ContentType.SLIDES, ContentType.EXERCISES, ContentType.QUIZZES, ContentType.LABS]
        if v not in valid_types:
            raise ValueError(f'Content type must be one of: {[t.value for t in valid_types]}')
        return v


class ContentGenerationRequest(BaseModel):
    """Content generation request model"""
    generate_slides: bool = True
    generate_exercises: bool = True
    generate_quizzes: bool = True
    generate_labs: bool = True
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)


class CustomGenerationRequest(BaseModel):
    """Custom content generation request model"""
    prompt: str = Field(..., min_length=1, max_length=2000)
    content_type: str = Field(..., min_length=1, max_length=50)
    parameters: Dict[str, Any] = Field(default_factory=dict)