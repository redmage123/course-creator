"""
Screenshot Analysis Domain Entities

BUSINESS PURPOSE:
Defines the core domain entities for screenshot-to-course generation.
These entities represent the business concepts of uploading screenshots,
analyzing them with AI, and generating course structures.

TECHNICAL IMPLEMENTATION:
- Dataclasses for immutable value objects
- Enums for status tracking
- Entity classes with validation
- Rich domain methods

WHY:
Clean separation of domain logic from infrastructure concerns.
These entities are provider-agnostic and contain pure business rules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class UploadStatus(str, Enum):
    """
    Status of a screenshot upload

    BUSINESS CONTEXT:
    Tracks the lifecycle of a screenshot from upload through
    analysis to course generation.
    """
    PENDING = "pending"           # Just uploaded, waiting for processing
    VALIDATING = "validating"     # Being validated (format, size)
    QUEUED = "queued"             # In processing queue
    ANALYZING = "analyzing"       # Vision AI is analyzing
    ANALYZED = "analyzed"         # Analysis complete
    GENERATING = "generating"     # Course being generated
    COMPLETED = "completed"       # Course generated successfully
    FAILED = "failed"             # Processing failed
    EXPIRED = "expired"           # Upload expired (not processed in time)


class DifficultyLevel(str, Enum):
    """Course difficulty level"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass(frozen=True)
class ImageMetadata:
    """
    Metadata extracted from uploaded image

    BUSINESS CONTEXT:
    Stores technical details about the uploaded image
    for validation and processing.
    """
    width: int
    height: int
    format: str  # png, jpeg, webp
    size_bytes: int
    file_hash: str  # SHA-256 for deduplication

    @property
    def size_mb(self) -> float:
        """Get size in megabytes"""
        return self.size_bytes / (1024 * 1024)

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio (width/height)"""
        return self.width / self.height if self.height > 0 else 0


@dataclass
class DetectedElement:
    """
    Element detected in screenshot by vision AI

    BUSINESS CONTEXT:
    Represents a discrete piece of content detected in the
    screenshot such as text blocks, images, code snippets, etc.
    """
    element_type: str  # text, image, code, diagram, table, etc.
    content: str
    confidence: float
    bounding_box: Optional[Dict[str, int]] = None  # x, y, width, height
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CourseModule:
    """
    A module/section within a course structure

    BUSINESS CONTEXT:
    Represents a logical grouping of lessons within
    a course, extracted from screenshot content.
    """
    title: str
    description: str
    order: int
    lessons: List[str] = field(default_factory=list)
    estimated_duration_minutes: int = 0
    learning_objectives: List[str] = field(default_factory=list)


@dataclass
class CourseStructure:
    """
    Complete course structure extracted from screenshot

    BUSINESS CONTEXT:
    The full course outline generated from screenshot analysis,
    ready to be used for course creation.
    """
    title: str
    description: str
    modules: List[CourseModule] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    estimated_duration_hours: int = 0
    target_audience: str = ""
    language: str = "en"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "title": self.title,
            "description": self.description,
            "modules": [
                {
                    "title": m.title,
                    "description": m.description,
                    "order": m.order,
                    "lessons": m.lessons,
                    "estimated_duration_minutes": m.estimated_duration_minutes,
                    "learning_objectives": m.learning_objectives
                }
                for m in self.modules
            ],
            "topics": self.topics,
            "learning_objectives": self.learning_objectives,
            "prerequisites": self.prerequisites,
            "key_concepts": self.key_concepts,
            "difficulty": self.difficulty.value,
            "estimated_duration_hours": self.estimated_duration_hours,
            "target_audience": self.target_audience,
            "language": self.language
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CourseStructure":
        """Create from dictionary"""
        modules = [
            CourseModule(
                title=m.get("title", ""),
                description=m.get("description", ""),
                order=m.get("order", i),
                lessons=m.get("lessons", []),
                estimated_duration_minutes=m.get("estimated_duration_minutes", 0),
                learning_objectives=m.get("learning_objectives", [])
            )
            for i, m in enumerate(data.get("modules", []))
        ]

        difficulty_str = data.get("difficulty", "intermediate")
        try:
            difficulty = DifficultyLevel(difficulty_str.lower())
        except ValueError:
            difficulty = DifficultyLevel.INTERMEDIATE

        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            modules=modules,
            topics=data.get("topics", []),
            learning_objectives=data.get("learning_objectives", []),
            prerequisites=data.get("prerequisites", []),
            key_concepts=data.get("key_concepts", []),
            difficulty=difficulty,
            estimated_duration_hours=int(data.get("estimated_duration_hours", 0)),
            target_audience=data.get("target_audience", ""),
            language=data.get("language", "en")
        )


@dataclass
class AnalysisResult:
    """
    Result of screenshot analysis by vision AI

    BUSINESS CONTEXT:
    Contains all information extracted from a screenshot
    by the vision LLM, ready for course generation.
    """
    id: UUID = field(default_factory=uuid4)
    screenshot_id: UUID = field(default_factory=uuid4)
    extracted_text: str = ""
    detected_language: str = "en"
    confidence_score: float = 0.0
    detected_elements: List[DetectedElement] = field(default_factory=list)
    course_structure: Optional[CourseStructure] = None
    raw_response: str = ""
    provider_used: str = ""
    model_used: str = ""
    tokens_used: int = 0
    processing_time_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_course_structure(self) -> bool:
        """Check if course structure was extracted"""
        return self.course_structure is not None

    @property
    def is_high_confidence(self) -> bool:
        """Check if analysis has high confidence (>= 0.8)"""
        return self.confidence_score >= 0.8


@dataclass
class ScreenshotUpload:
    """
    Domain entity for an uploaded screenshot

    BUSINESS CONTEXT:
    Represents a screenshot uploaded by a user for course generation.
    Tracks the full lifecycle from upload through analysis to course creation.
    """
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    original_filename: str = ""
    image_metadata: Optional[ImageMetadata] = None
    status: UploadStatus = UploadStatus.PENDING
    analysis_result: Optional[AnalysisResult] = None
    generated_course_id: Optional[UUID] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    analyzed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Business rules
    MAX_FILE_SIZE_MB = 20.0
    ALLOWED_FORMATS = {"png", "jpeg", "jpg", "webp", "gif"}
    EXPIRY_HOURS = 24

    def validate_image(self) -> bool:
        """
        Validate uploaded image meets requirements

        Returns:
            True if valid, raises exception otherwise
        """
        if not self.image_metadata:
            return False

        # Check size
        if self.image_metadata.size_mb > self.MAX_FILE_SIZE_MB:
            self.error_message = (
                f"Image size ({self.image_metadata.size_mb:.1f}MB) "
                f"exceeds maximum ({self.MAX_FILE_SIZE_MB}MB)"
            )
            self.status = UploadStatus.FAILED
            return False

        # Check format
        if self.image_metadata.format.lower() not in self.ALLOWED_FORMATS:
            self.error_message = (
                f"Format '{self.image_metadata.format}' not allowed. "
                f"Supported: {', '.join(self.ALLOWED_FORMATS)}"
            )
            self.status = UploadStatus.FAILED
            return False

        return True

    def can_retry(self) -> bool:
        """Check if processing can be retried"""
        return (
            self.status == UploadStatus.FAILED and
            self.retry_count < self.max_retries
        )

    def mark_analyzing(self):
        """Mark upload as being analyzed"""
        self.status = UploadStatus.ANALYZING
        self.updated_at = datetime.utcnow()

    def mark_analyzed(self, result: AnalysisResult):
        """Mark upload as analyzed with result"""
        self.status = UploadStatus.ANALYZED
        self.analysis_result = result
        self.analyzed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_generating(self):
        """Mark upload as generating course"""
        self.status = UploadStatus.GENERATING
        self.updated_at = datetime.utcnow()

    def mark_completed(self, course_id: UUID):
        """Mark upload as completed with generated course"""
        self.status = UploadStatus.COMPLETED
        self.generated_course_id = course_id
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str):
        """Mark upload as failed"""
        self.status = UploadStatus.FAILED
        self.error_message = error
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if upload has expired"""
        if self.status == UploadStatus.COMPLETED:
            return False
        elapsed = datetime.utcnow() - self.created_at
        return elapsed.total_seconds() > (self.EXPIRY_HOURS * 3600)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "user_id": str(self.user_id),
            "original_filename": self.original_filename,
            "status": self.status.value,
            "has_analysis": self.analysis_result is not None,
            "generated_course_id": str(self.generated_course_id) if self.generated_course_id else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "image_metadata": {
                "width": self.image_metadata.width,
                "height": self.image_metadata.height,
                "format": self.image_metadata.format,
                "size_mb": self.image_metadata.size_mb
            } if self.image_metadata else None
        }


@dataclass
class ScreenshotBatch:
    """
    A batch of screenshots for bulk processing

    BUSINESS CONTEXT:
    Allows users to upload multiple screenshots at once
    for combined course generation.
    """
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    screenshots: List[ScreenshotUpload] = field(default_factory=list)
    combined_analysis: Optional[AnalysisResult] = None
    status: UploadStatus = UploadStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_screenshot(self, upload: ScreenshotUpload):
        """Add screenshot to batch"""
        self.screenshots.append(upload)

    @property
    def total_count(self) -> int:
        """Total number of screenshots"""
        return len(self.screenshots)

    @property
    def completed_count(self) -> int:
        """Number of analyzed screenshots"""
        return sum(
            1 for s in self.screenshots
            if s.status in (UploadStatus.ANALYZED, UploadStatus.COMPLETED)
        )

    @property
    def failed_count(self) -> int:
        """Number of failed screenshots"""
        return sum(
            1 for s in self.screenshots
            if s.status == UploadStatus.FAILED
        )

    @property
    def progress_percent(self) -> float:
        """Processing progress percentage"""
        if self.total_count == 0:
            return 0.0
        return (self.completed_count / self.total_count) * 100
