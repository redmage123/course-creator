"""
External Content Domain Entities for URL-Based Course Generation

BUSINESS REQUIREMENT:
Support course generation from external third-party software documentation by defining
the domain model for external content sources, fetch requests, and processed content.
This enables instructors to generate training materials from any documentation URL.

DOMAIN MODEL:
- ExternalContentSource: Represents a URL source for course content
- ContentFetchRequest: Request to fetch and process external content
- ProcessedExternalContent: Content after fetching and processing
- ExternalContentMetadata: Metadata about fetched content for tracking

INTEGRATION POINTS:
- Course Generator API: Receives external content in course generation requests
- RAG Service: Stores processed content for retrieval
- Course Management: Links generated courses to external sources
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class ContentSourceType(str, Enum):
    """
    Types of external content sources supported for course generation.

    Business Context:
    Different source types may require different processing strategies
    and have different characteristics for course generation.
    """
    DOCUMENTATION = "documentation"  # Technical documentation sites
    TUTORIAL = "tutorial"  # Tutorial/how-to content
    API_REFERENCE = "api_reference"  # API documentation
    KNOWLEDGE_BASE = "knowledge_base"  # Help/support content
    BLOG = "blog"  # Blog posts and articles
    WIKI = "wiki"  # Wiki pages
    GENERAL = "general"  # General web content


class FetchStatus(str, Enum):
    """
    Status of content fetch operations.

    Business Context:
    Tracks the lifecycle of content fetch requests for monitoring
    and error handling in the course generation pipeline.
    """
    PENDING = "pending"  # Request queued
    FETCHING = "fetching"  # Currently fetching
    PARSING = "parsing"  # Parsing content
    PROCESSING = "processing"  # Processing for RAG
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Fetch failed
    CANCELLED = "cancelled"  # Request cancelled


@dataclass
class ExternalContentSource:
    """
    Represents an external URL source for course content.

    Business Context:
    Defines a URL that will be used as a source for AI-powered course generation.
    Includes metadata about the source type and any access requirements.

    Technical Context:
    - url: The source URL to fetch content from
    - source_type: Classification for processing strategy
    - description: User-provided context about the source
    - requires_auth: Whether authentication is needed (not supported yet)
    """
    url: str
    source_type: ContentSourceType = ContentSourceType.GENERAL
    description: Optional[str] = None
    requires_auth: bool = False
    priority: int = 1  # For multi-URL requests, higher = more important

    def __post_init__(self):
        """Validate source configuration."""
        if not self.url or not self.url.strip():
            raise ValueError("URL cannot be empty")

        # Normalize URL
        self.url = self.url.strip()

        # Validate URL format (basic check)
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")


@dataclass
class ContentFetchRequest:
    """
    Request to fetch and process external content for course generation.

    Business Context:
    Encapsulates a complete request to fetch external documentation,
    including source URLs, processing preferences, and user context.

    Technical Context:
    - id: Unique request identifier for tracking
    - sources: List of URLs to fetch
    - course_context: Context about the course being generated
    - user_id: User making the request for attribution
    - options: Processing configuration
    """
    id: UUID = field(default_factory=uuid4)
    sources: List[ExternalContentSource] = field(default_factory=list)
    course_title: Optional[str] = None
    course_description: Optional[str] = None
    target_level: str = "beginner"  # beginner, intermediate, advanced
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    options: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: FetchStatus = FetchStatus.PENDING

    def add_source(self, url: str, source_type: ContentSourceType = ContentSourceType.GENERAL) -> None:
        """Add a content source to the request."""
        source = ExternalContentSource(url=url, source_type=source_type)
        self.sources.append(source)

    @property
    def source_count(self) -> int:
        """Number of sources in this request."""
        return len(self.sources)


@dataclass
class ExternalContentMetadata:
    """
    Metadata about fetched external content.

    Business Context:
    Tracks information about content sources for attribution,
    cache management, and content freshness checking.

    Technical Context:
    - source_url: Original URL
    - content_hash: Hash for change detection
    - fetch_timestamp: When content was fetched
    - word_count: Content size metrics
    """
    source_url: str
    content_hash: str
    fetch_timestamp: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    word_count: int = 0
    character_count: int = 0
    heading_count: int = 0
    code_block_count: int = 0
    source_type: ContentSourceType = ContentSourceType.GENERAL
    http_status: int = 200
    content_type: str = "text/html"
    last_modified: Optional[datetime] = None
    etag: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for storage."""
        return {
            "source_url": self.source_url,
            "content_hash": self.content_hash,
            "fetch_timestamp": self.fetch_timestamp.isoformat(),
            "title": self.title,
            "description": self.description,
            "word_count": self.word_count,
            "character_count": self.character_count,
            "heading_count": self.heading_count,
            "code_block_count": self.code_block_count,
            "source_type": self.source_type.value,
            "http_status": self.http_status,
            "content_type": self.content_type,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "etag": self.etag,
        }


@dataclass
class ProcessedExternalContent:
    """
    External content after fetching and processing.

    Business Context:
    Represents content that has been successfully fetched, parsed,
    and prepared for use in course generation. Includes both the
    extracted content and structural information.

    Technical Context:
    - request_id: Links to original fetch request
    - metadata: Source and processing metadata
    - content: Extracted text content
    - structured_content: Parsed structure (headings, sections)
    - code_examples: Extracted code blocks
    - chunks: Pre-chunked content for RAG
    """
    request_id: UUID
    metadata: ExternalContentMetadata
    content: str
    structured_content: Dict[str, Any] = field(default_factory=dict)
    code_examples: List[Dict[str, str]] = field(default_factory=list)
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    processing_time_ms: int = 0
    rag_document_ids: List[str] = field(default_factory=list)  # IDs in RAG storage

    @property
    def is_chunked(self) -> bool:
        """Whether content has been chunked for RAG."""
        return len(self.chunks) > 0

    @property
    def chunk_count(self) -> int:
        """Number of chunks created from this content."""
        return len(self.chunks)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of processed content for API responses."""
        return {
            "request_id": str(self.request_id),
            "source_url": self.metadata.source_url,
            "title": self.metadata.title,
            "word_count": self.metadata.word_count,
            "chunk_count": self.chunk_count,
            "code_example_count": len(self.code_examples),
            "processing_time_ms": self.processing_time_ms,
            "fetch_timestamp": self.metadata.fetch_timestamp.isoformat(),
        }


@dataclass
class URLBasedGenerationRequest:
    """
    Complete request for URL-based course generation.

    Business Context:
    Combines external content sources with course generation parameters
    to create a complete request for AI-powered course generation from
    third-party documentation URLs.

    Technical Context:
    - source_urls: URLs to fetch content from
    - course_params: Standard course generation parameters
    - processing_options: How to process fetched content
    """
    id: UUID = field(default_factory=uuid4)

    # Source URLs
    source_urls: List[str] = field(default_factory=list)
    primary_url: Optional[str] = None  # Main documentation URL

    # Course generation parameters
    course_title: Optional[str] = None
    course_description: Optional[str] = None
    target_level: str = "beginner"
    target_audience: Optional[str] = None
    objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None  # hours

    # Processing options
    include_code_examples: bool = True
    generate_quizzes: bool = True
    generate_exercises: bool = True
    max_modules: int = 10
    chunk_for_rag: bool = True

    # User context
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Set primary URL if not specified."""
        if self.source_urls and not self.primary_url:
            self.primary_url = self.source_urls[0]

    def add_url(self, url: str, is_primary: bool = False) -> None:
        """Add a source URL to the request."""
        if url not in self.source_urls:
            self.source_urls.append(url)

        if is_primary:
            self.primary_url = url

    @property
    def url_count(self) -> int:
        """Number of source URLs."""
        return len(self.source_urls)

    def to_syllabus_request_params(self) -> Dict[str, Any]:
        """
        Convert to parameters compatible with SyllabusRequest.

        Used to integrate with existing syllabus generation workflow.
        """
        return {
            "title": self.course_title or "Generated Course",
            "description": self.course_description or "",
            "level": self.target_level,
            "duration": self.estimated_duration,
            "objectives": self.objectives,
            "prerequisites": self.prerequisites,
            "target_audience": self.target_audience,
            "additional_requirements": f"Source documentation: {self.primary_url}",
        }


@dataclass
class URLGenerationResult:
    """
    Result of URL-based course generation.

    Business Context:
    Contains the generated course content along with metadata about
    the source URLs and processing that was performed.

    Technical Context:
    - request_id: Original request identifier
    - processed_content: All processed external content
    - generated_syllabus: The generated course syllabus
    - rag_enhanced: Whether RAG enhancement was used
    """
    request_id: UUID
    processed_content: List[ProcessedExternalContent] = field(default_factory=list)
    generated_syllabus: Optional[Dict[str, Any]] = None
    generation_method: str = "rag_enhanced"  # rag_enhanced, standard, fallback
    total_processing_time_ms: int = 0
    source_summary: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_successful(self) -> bool:
        """Whether generation completed successfully."""
        return self.generated_syllabus is not None and len(self.errors) == 0

    @property
    def total_source_words(self) -> int:
        """Total words across all processed sources."""
        return sum(pc.metadata.word_count for pc in self.processed_content)

    def get_summary(self) -> Dict[str, Any]:
        """Get generation result summary for API response."""
        return {
            "request_id": str(self.request_id),
            "success": self.is_successful,
            "source_count": len(self.processed_content),
            "total_source_words": self.total_source_words,
            "generation_method": self.generation_method,
            "processing_time_ms": self.total_processing_time_ms,
            "error_count": len(self.errors),
            "created_at": self.created_at.isoformat(),
        }


# Export all entities
__all__ = [
    "ContentSourceType",
    "FetchStatus",
    "ExternalContentSource",
    "ContentFetchRequest",
    "ExternalContentMetadata",
    "ProcessedExternalContent",
    "URLBasedGenerationRequest",
    "URLGenerationResult",
]
