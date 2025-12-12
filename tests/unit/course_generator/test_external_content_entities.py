"""
Unit Tests for External Content Domain Entities

BUSINESS CONTEXT:
These tests verify the domain entities used for URL-based course generation
from external third-party software documentation. Tests cover:
- Content source types and fetch status enums
- ExternalContentSource validation
- ContentFetchRequest construction
- ExternalContentMetadata handling
- ProcessedExternalContent data management
- URLBasedGenerationRequest parameter handling
- URLGenerationResult reporting

TESTING STRATEGY:
- Test all entity constructors and validators
- Verify enum values and transitions
- Test serialization/deserialization (to_dict methods)
- Ensure proper default values and optional fields
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from course_generator.domain.entities.external_content import (
    ContentSourceType,
    FetchStatus,
    ExternalContentSource,
    ContentFetchRequest,
    ExternalContentMetadata,
    ProcessedExternalContent,
    URLBasedGenerationRequest,
    URLGenerationResult,
)


class TestContentSourceType:
    """Test ContentSourceType enum."""

    def test_all_source_types_exist(self):
        """Test all expected source types are defined."""
        expected_types = [
            "documentation",
            "tutorial",
            "api_reference",
            "knowledge_base",
            "blog",
            "wiki",
            "general",
        ]

        for type_name in expected_types:
            assert hasattr(ContentSourceType, type_name.upper())

    def test_documentation_type(self):
        """Test DOCUMENTATION source type."""
        assert ContentSourceType.DOCUMENTATION.value == "documentation"

    def test_api_reference_type(self):
        """Test API_REFERENCE source type."""
        assert ContentSourceType.API_REFERENCE.value == "api_reference"

    def test_general_is_default(self):
        """Test GENERAL is the fallback type."""
        assert ContentSourceType.GENERAL.value == "general"


class TestFetchStatus:
    """Test FetchStatus enum."""

    def test_all_statuses_exist(self):
        """Test all expected fetch statuses are defined."""
        expected_statuses = [
            "pending",
            "fetching",
            "parsing",
            "processing",
            "completed",
            "failed",
            "cancelled",
        ]

        for status_name in expected_statuses:
            assert hasattr(FetchStatus, status_name.upper())

    def test_pending_is_initial_status(self):
        """Test PENDING is the initial status."""
        assert FetchStatus.PENDING.value == "pending"

    def test_completed_status(self):
        """Test COMPLETED status."""
        assert FetchStatus.COMPLETED.value == "completed"

    def test_failed_status(self):
        """Test FAILED status."""
        assert FetchStatus.FAILED.value == "failed"


class TestExternalContentSource:
    """Test ExternalContentSource dataclass."""

    def test_basic_creation(self):
        """Test basic source creation with URL only."""
        source = ExternalContentSource(url="https://example.com/docs")

        assert source.url == "https://example.com/docs"
        assert source.source_type == ContentSourceType.GENERAL
        assert source.description is None
        assert source.requires_auth is False
        assert source.priority == 1

    def test_source_with_type(self):
        """Test source with specific type."""
        source = ExternalContentSource(
            url="https://api.example.com/reference",
            source_type=ContentSourceType.API_REFERENCE,
        )

        assert source.source_type == ContentSourceType.API_REFERENCE

    def test_source_with_description(self):
        """Test source with description."""
        source = ExternalContentSource(
            url="https://docs.example.com",
            description="Main product documentation",
        )

        assert source.description == "Main product documentation"

    def test_source_with_priority(self):
        """Test source with custom priority."""
        source = ExternalContentSource(
            url="https://example.com/docs",
            priority=5,
        )

        assert source.priority == 5

    def test_url_normalization(self):
        """Test URL is trimmed of whitespace."""
        source = ExternalContentSource(url="  https://example.com/docs  ")

        assert source.url == "https://example.com/docs"

    def test_empty_url_raises_error(self):
        """Test empty URL raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ExternalContentSource(url="")

        assert "empty" in str(exc_info.value).lower()

    def test_whitespace_only_url_raises_error(self):
        """Test whitespace-only URL raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ExternalContentSource(url="   ")

        assert "empty" in str(exc_info.value).lower()

    def test_invalid_scheme_raises_error(self):
        """Test non-HTTP(S) scheme raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ExternalContentSource(url="ftp://example.com/file")

        assert "http" in str(exc_info.value).lower()


class TestContentFetchRequest:
    """Test ContentFetchRequest dataclass."""

    def test_basic_creation(self):
        """Test basic request creation with defaults."""
        request = ContentFetchRequest()

        assert isinstance(request.id, UUID)
        assert request.sources == []
        assert request.course_title is None
        assert request.target_level == "beginner"
        assert request.status == FetchStatus.PENDING
        assert request.created_at is not None

    def test_request_with_sources(self):
        """Test request with initial sources."""
        source = ExternalContentSource(url="https://example.com/docs")
        request = ContentFetchRequest(sources=[source])

        assert len(request.sources) == 1
        assert request.sources[0].url == "https://example.com/docs"

    def test_request_with_course_context(self):
        """Test request with course context."""
        request = ContentFetchRequest(
            course_title="Python Fundamentals",
            course_description="Learn Python basics",
            target_level="intermediate",
        )

        assert request.course_title == "Python Fundamentals"
        assert request.course_description == "Learn Python basics"
        assert request.target_level == "intermediate"

    def test_add_source_method(self):
        """Test add_source method."""
        request = ContentFetchRequest()
        request.add_source("https://example.com/docs")

        assert len(request.sources) == 1
        assert request.sources[0].url == "https://example.com/docs"
        assert request.sources[0].source_type == ContentSourceType.GENERAL

    def test_add_source_with_type(self):
        """Test add_source with specific type."""
        request = ContentFetchRequest()
        request.add_source(
            "https://api.example.com/ref",
            source_type=ContentSourceType.API_REFERENCE,
        )

        assert request.sources[0].source_type == ContentSourceType.API_REFERENCE

    def test_source_count_property(self):
        """Test source_count property."""
        request = ContentFetchRequest()
        assert request.source_count == 0

        request.add_source("https://example.com/docs1")
        request.add_source("https://example.com/docs2")

        assert request.source_count == 2


class TestExternalContentMetadata:
    """Test ExternalContentMetadata dataclass."""

    def test_basic_creation(self):
        """Test basic metadata creation."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com/docs",
            content_hash="abc123def456",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        assert metadata.source_url == "https://example.com/docs"
        assert metadata.content_hash == "abc123def456"
        assert metadata.word_count == 0
        assert metadata.source_type == ContentSourceType.GENERAL
        assert metadata.http_status == 200

    def test_full_metadata(self):
        """Test metadata with all fields."""
        timestamp = datetime.now(timezone.utc)
        metadata = ExternalContentMetadata(
            source_url="https://docs.example.com/guide",
            content_hash="hash123",
            fetch_timestamp=timestamp,
            title="Getting Started Guide",
            description="Learn the basics",
            word_count=5000,
            character_count=30000,
            heading_count=15,
            code_block_count=8,
            source_type=ContentSourceType.DOCUMENTATION,
            http_status=200,
            content_type="text/html",
            last_modified=timestamp,
            etag='"abc123"',
        )

        assert metadata.title == "Getting Started Guide"
        assert metadata.word_count == 5000
        assert metadata.heading_count == 15
        assert metadata.code_block_count == 8
        assert metadata.etag == '"abc123"'

    def test_to_dict_method(self):
        """Test to_dict serialization."""
        timestamp = datetime.now(timezone.utc)
        metadata = ExternalContentMetadata(
            source_url="https://example.com/docs",
            content_hash="hash123",
            fetch_timestamp=timestamp,
            title="Test Page",
            word_count=100,
        )

        result = metadata.to_dict()

        assert result["source_url"] == "https://example.com/docs"
        assert result["content_hash"] == "hash123"
        assert result["title"] == "Test Page"
        assert result["word_count"] == 100
        assert result["fetch_timestamp"] == timestamp.isoformat()
        assert result["source_type"] == "general"

    def test_to_dict_with_none_last_modified(self):
        """Test to_dict handles None last_modified."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com",
            content_hash="hash",
            fetch_timestamp=datetime.now(timezone.utc),
            last_modified=None,
        )

        result = metadata.to_dict()

        assert result["last_modified"] is None


class TestProcessedExternalContent:
    """Test ProcessedExternalContent dataclass."""

    def test_basic_creation(self):
        """Test basic processed content creation."""
        request_id = uuid4()
        metadata = ExternalContentMetadata(
            source_url="https://example.com",
            content_hash="hash",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        content = ProcessedExternalContent(
            request_id=request_id,
            metadata=metadata,
            content="Extracted content here",
        )

        assert content.request_id == request_id
        assert content.content == "Extracted content here"
        assert content.structured_content == {}
        assert content.code_examples == []
        assert content.chunks == []

    def test_with_structured_content(self):
        """Test processed content with structure."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com",
            content_hash="hash",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        content = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata,
            content="Content",
            structured_content={
                "headings": [
                    {"text": "Introduction", "level": 1},
                    {"text": "Setup", "level": 2},
                ],
            },
            code_examples=[
                {"language": "python", "content": "print('hello')"},
            ],
        )

        assert len(content.structured_content["headings"]) == 2
        assert len(content.code_examples) == 1

    def test_is_chunked_property(self):
        """Test is_chunked property."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com",
            content_hash="hash",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        # Without chunks
        content = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata,
            content="Content",
        )
        assert content.is_chunked is False

        # With chunks
        content.chunks = [{"index": 0, "content": "chunk"}]
        assert content.is_chunked is True

    def test_chunk_count_property(self):
        """Test chunk_count property."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com",
            content_hash="hash",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        content = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata,
            content="Content",
            chunks=[
                {"index": 0, "content": "chunk1"},
                {"index": 1, "content": "chunk2"},
                {"index": 2, "content": "chunk3"},
            ],
        )

        assert content.chunk_count == 3

    def test_get_summary_method(self):
        """Test get_summary method."""
        timestamp = datetime.now(timezone.utc)
        metadata = ExternalContentMetadata(
            source_url="https://example.com/docs",
            content_hash="hash",
            fetch_timestamp=timestamp,
            title="Test Doc",
            word_count=500,
        )

        content = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata,
            content="Content",
            chunks=[{"index": 0, "content": "chunk"}],
            code_examples=[{"language": "python", "content": "code"}],
            processing_time_ms=150,
        )

        summary = content.get_summary()

        assert summary["source_url"] == "https://example.com/docs"
        assert summary["title"] == "Test Doc"
        assert summary["word_count"] == 500
        assert summary["chunk_count"] == 1
        assert summary["code_example_count"] == 1
        assert summary["processing_time_ms"] == 150


class TestURLBasedGenerationRequest:
    """Test URLBasedGenerationRequest dataclass."""

    def test_basic_creation(self):
        """Test basic request creation."""
        request = URLBasedGenerationRequest()

        assert isinstance(request.id, UUID)
        assert request.source_urls == []
        assert request.primary_url is None
        assert request.target_level == "beginner"
        assert request.max_modules == 10
        assert request.chunk_for_rag is True

    def test_request_with_urls(self):
        """Test request with source URLs."""
        request = URLBasedGenerationRequest(
            source_urls=[
                "https://example.com/docs",
                "https://example.com/api",
            ],
        )

        assert len(request.source_urls) == 2
        # Primary URL should be set to first URL
        assert request.primary_url == "https://example.com/docs"

    def test_explicit_primary_url(self):
        """Test explicit primary URL setting."""
        request = URLBasedGenerationRequest(
            source_urls=["https://example.com/docs"],
            primary_url="https://example.com/main",
        )

        assert request.primary_url == "https://example.com/main"

    def test_course_parameters(self):
        """Test course generation parameters."""
        request = URLBasedGenerationRequest(
            course_title="AWS Fundamentals",
            course_description="Learn AWS basics",
            target_level="intermediate",
            target_audience="DevOps engineers",
            objectives=["Understand EC2", "Deploy to S3"],
            prerequisites=["Basic Linux", "Networking basics"],
            estimated_duration=40,
        )

        assert request.course_title == "AWS Fundamentals"
        assert request.target_level == "intermediate"
        assert len(request.objectives) == 2
        assert request.estimated_duration == 40

    def test_processing_options(self):
        """Test processing options."""
        request = URLBasedGenerationRequest(
            include_code_examples=False,
            generate_quizzes=False,
            generate_exercises=True,
            max_modules=5,
            chunk_for_rag=False,
        )

        assert request.include_code_examples is False
        assert request.generate_quizzes is False
        assert request.generate_exercises is True
        assert request.max_modules == 5
        assert request.chunk_for_rag is False

    def test_add_url_method(self):
        """Test add_url method."""
        request = URLBasedGenerationRequest()
        request.add_url("https://example.com/docs")

        assert "https://example.com/docs" in request.source_urls

    def test_add_url_as_primary(self):
        """Test add_url with is_primary flag."""
        request = URLBasedGenerationRequest()
        request.add_url("https://example.com/docs")
        request.add_url("https://example.com/main", is_primary=True)

        assert request.primary_url == "https://example.com/main"

    def test_add_url_no_duplicates(self):
        """Test add_url doesn't add duplicates."""
        request = URLBasedGenerationRequest()
        request.add_url("https://example.com/docs")
        request.add_url("https://example.com/docs")

        assert request.url_count == 1

    def test_url_count_property(self):
        """Test url_count property."""
        request = URLBasedGenerationRequest(
            source_urls=[
                "https://example.com/docs1",
                "https://example.com/docs2",
            ]
        )

        assert request.url_count == 2

    def test_to_syllabus_request_params(self):
        """Test to_syllabus_request_params method."""
        request = URLBasedGenerationRequest(
            course_title="Test Course",
            course_description="Description",
            target_level="advanced",
            target_audience="Developers",
            objectives=["Obj 1"],
            prerequisites=["Prereq 1"],
            estimated_duration=10,
            primary_url="https://example.com/docs",
        )

        params = request.to_syllabus_request_params()

        assert params["title"] == "Test Course"
        assert params["description"] == "Description"
        assert params["level"] == "advanced"
        assert params["duration"] == 10
        assert "objectives" in params
        assert "https://example.com/docs" in params["additional_requirements"]


class TestURLGenerationResult:
    """Test URLGenerationResult dataclass."""

    def test_basic_creation(self):
        """Test basic result creation."""
        request_id = uuid4()
        result = URLGenerationResult(request_id=request_id)

        assert result.request_id == request_id
        assert result.processed_content == []
        assert result.generated_syllabus is None
        assert result.generation_method == "rag_enhanced"
        assert result.errors == []

    def test_successful_result(self):
        """Test successful generation result."""
        request_id = uuid4()
        syllabus = {
            "title": "Generated Course",
            "modules": [{"title": "Module 1"}],
        }

        result = URLGenerationResult(
            request_id=request_id,
            generated_syllabus=syllabus,
            generation_method="rag_enhanced",
            total_processing_time_ms=5000,
        )

        assert result.is_successful is True
        assert result.generated_syllabus is not None

    def test_failed_result(self):
        """Test failed generation result."""
        result = URLGenerationResult(
            request_id=uuid4(),
            errors=[{"url": "https://example.com", "error": "Timeout"}],
        )

        assert result.is_successful is False

    def test_total_source_words(self):
        """Test total_source_words property."""
        metadata1 = ExternalContentMetadata(
            source_url="https://example.com/1",
            content_hash="hash1",
            fetch_timestamp=datetime.now(timezone.utc),
            word_count=1000,
        )
        metadata2 = ExternalContentMetadata(
            source_url="https://example.com/2",
            content_hash="hash2",
            fetch_timestamp=datetime.now(timezone.utc),
            word_count=2000,
        )

        content1 = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata1,
            content="Content 1",
        )
        content2 = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata2,
            content="Content 2",
        )

        result = URLGenerationResult(
            request_id=uuid4(),
            processed_content=[content1, content2],
        )

        assert result.total_source_words == 3000

    def test_get_summary_method(self):
        """Test get_summary method."""
        request_id = uuid4()
        result = URLGenerationResult(
            request_id=request_id,
            generated_syllabus={"title": "Course"},
            generation_method="rag_enhanced",
            total_processing_time_ms=3000,
        )

        summary = result.get_summary()

        assert summary["request_id"] == str(request_id)
        assert summary["success"] is True
        assert summary["generation_method"] == "rag_enhanced"
        assert summary["processing_time_ms"] == 3000
        assert summary["error_count"] == 0


class TestEntityExports:
    """Test __all__ exports."""

    def test_all_entities_exported(self):
        """Test all entities are in __all__."""
        from course_generator.domain.entities import external_content

        expected_exports = [
            "ContentSourceType",
            "FetchStatus",
            "ExternalContentSource",
            "ContentFetchRequest",
            "ExternalContentMetadata",
            "ProcessedExternalContent",
            "URLBasedGenerationRequest",
            "URLGenerationResult",
        ]

        for name in expected_exports:
            assert name in external_content.__all__
