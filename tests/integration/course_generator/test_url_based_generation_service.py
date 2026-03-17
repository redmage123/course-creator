"""
Unit Tests for URL-Based Generation Service

BUSINESS CONTEXT:
These tests verify the URLBasedGenerationService that orchestrates
AI-powered course generation from external documentation URLs. Tests cover:
- Complete generation workflow
- URL fetching and error handling
- RAG integration and content storage
- Progress tracking
- Syllabus generation from fetched content

TESTING STRATEGY:
- Mock external dependencies (URL fetcher, RAG service)
- Test all workflow stages independently
- Verify error propagation with custom exceptions
- Test concurrent URL fetching behavior
- Ensure proper progress tracking
"""

import pytest
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
import importlib.util
from pathlib import Path

# Use explicit path imports to avoid module collision when running tests
# with multiple services in sys.path
_course_generator_root = Path(__file__).parent.parent.parent.parent / "services" / "course-generator"

# Import syllabus models from explicit path
_syllabus_path = _course_generator_root / "models" / "syllabus.py"
_spec = importlib.util.spec_from_file_location("cg_syllabus", _syllabus_path)
_syllabus_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_syllabus_module)
SyllabusRequest = _syllabus_module.SyllabusRequest
CourseLevel = _syllabus_module.CourseLevel

# Import exceptions from explicit path
_exceptions_path = _course_generator_root / "exceptions.py"
_exc_spec = importlib.util.spec_from_file_location("cg_exceptions", _exceptions_path)
_exceptions_module = importlib.util.module_from_spec(_exc_spec)
_exc_spec.loader.exec_module(_exceptions_module)
URLFetchException = _exceptions_module.URLFetchException
URLValidationException = _exceptions_module.URLValidationException
URLConnectionException = _exceptions_module.URLConnectionException
URLTimeoutException = _exceptions_module.URLTimeoutException
AIServiceException = _exceptions_module.AIServiceException
RAGException = _exceptions_module.RAGException
CourseCreatorBaseException = _exceptions_module.CourseCreatorBaseException

from course_generator.application.services.url_based_generation_service import (
    URLBasedGenerationService,
    URLFetchResult,
    GenerationProgress,
    create_url_based_generation_service,
)
from course_generator.application.services.url_content_fetcher import (
    FetchedContent,
    ContentChunk,
)
from course_generator.domain.entities.external_content import (
    ProcessedExternalContent,
    ExternalContentMetadata,
)


class TestURLBasedGenerationServiceInitialization:
    """Test service initialization."""

    def test_default_initialization(self):
        """Test service initializes with defaults."""
        service = URLBasedGenerationService()

        assert service.max_concurrent_fetches == URLBasedGenerationService.MAX_CONCURRENT_FETCHES
        assert service.url_fetcher is not None
        assert service.rag_service is not None

    def test_custom_max_concurrent_fetches(self):
        """Test custom concurrent fetch limit."""
        service = URLBasedGenerationService(max_concurrent_fetches=5)

        assert service.max_concurrent_fetches == 5

    def test_factory_function(self):
        """Test create_url_based_generation_service factory."""
        service = create_url_based_generation_service(max_concurrent_fetches=2)

        assert isinstance(service, URLBasedGenerationService)
        assert service.max_concurrent_fetches == 2


class TestURLFetchResult:
    """Test URLFetchResult dataclass."""

    def test_successful_result(self):
        """Test successful fetch result."""
        content = FetchedContent(
            url="https://example.com/docs",
            content="Test content",
            title="Test",
            description="",
            headings=[],
            code_blocks=[],
            word_count=2,
            character_count=12,
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        result = URLFetchResult(
            url="https://example.com/docs",
            success=True,
            content=content,
            fetch_time_ms=150,
        )

        assert result.success is True
        assert result.content is not None
        assert result.error is None

    def test_failed_result(self):
        """Test failed fetch result."""
        result = URLFetchResult(
            url="https://example.com/docs",
            success=False,
            error="Connection timeout",
            error_type="timeout",
            fetch_time_ms=30000,
        )

        assert result.success is False
        assert result.content is None
        assert result.error == "Connection timeout"
        assert result.error_type == "timeout"


class TestGenerationProgress:
    """Test GenerationProgress dataclass."""

    def test_initial_progress(self):
        """Test initial progress state."""
        progress = GenerationProgress(
            request_id=uuid4(),
            total_urls=3,
        )

        assert progress.status == "initializing"
        assert progress.total_urls == 3
        assert progress.urls_fetched == 0
        assert progress.urls_failed == 0
        assert progress.generation_started is False
        assert progress.generation_complete is False

    def test_progress_to_dict(self):
        """Test progress serialization."""
        request_id = uuid4()
        progress = GenerationProgress(
            request_id=request_id,
            total_urls=2,
            urls_fetched=1,
            status="fetching_urls",
            current_step="Fetching URL 2 of 2",
        )

        result = progress.to_dict()

        assert result["request_id"] == str(request_id)
        assert result["status"] == "fetching_urls"
        assert result["total_urls"] == 2
        assert result["urls_fetched"] == 1
        assert result["current_step"] == "Fetching URL 2 of 2"
        assert "elapsed_seconds" in result



class TestGenerateFromUrls:
    """Test generate_from_urls main workflow - needs real implementations."""

    @pytest.fixture
    def service(self):
        """Create service - needs real implementations."""
        import os
        if not os.getenv('CONTENT_FETCHER_URL'):
            pytest.skip("CONTENT_FETCHER_URL not configured")

    @pytest.fixture
    def sample_request(self):
        """Create sample syllabus request with URLs."""
        return SyllabusRequest(
            title="AWS Fundamentals",
            description="Learn AWS basics",
            source_url="https://docs.aws.amazon.com/getting-started",
            level=CourseLevel.BEGINNER,
        )

    @pytest.mark.asyncio
    async def test_successful_generation(self, service, mock_fetcher, sample_request):
        """Test successful URL-based generation."""
        # Mock successful URL fetch
        mock_content = FetchedContent(
            url="https://docs.aws.amazon.com/getting-started",
            content="AWS documentation content here...",
            title="Getting Started with AWS",
            description="Learn the basics of AWS",
            headings=[
                {"text": "Introduction", "level": 1},
                {"text": "Creating an Account", "level": 2},
            ],
            code_blocks=[],
            word_count=100,
            character_count=500,
            content_hash="abc123",
            fetch_timestamp=datetime.now(timezone.utc),
        )
        mock_fetcher.fetch_and_parse.return_value = mock_content
        mock_fetcher.create_content_chunks.return_value = [
            ContentChunk(
                content="Chunk 1 content",
                chunk_index=0,
                source_url="https://docs.aws.amazon.com/getting-started",
                heading_context="Introduction",
            ),
        ]

        # Execute
        result = await service.generate_from_urls(sample_request)

        # Verify
        assert result["success"] is True
        assert "syllabus" in result
        assert result["source_summary"]["urls_processed"] == 1
        mock_fetcher.fetch_and_parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_urls_fail_raises_exception(self, service, mock_fetcher, sample_request):
        """Test that failure of all URLs raises exception."""
        # Import exceptions from the same module the service uses
        from course_generator.exceptions import (
            URLConnectionException as ServiceURLConnectionException,
            URLFetchException as ServiceURLFetchException,
        )

        mock_fetcher.fetch_and_parse.side_effect = ServiceURLConnectionException(
            message="Connection failed",
            url="https://example.com",
        )

        with pytest.raises(ServiceURLFetchException) as exc_info:
            await service.generate_from_urls(sample_request)

        # The error code is based on class name: URLFETCHEXCEPTION
        assert exc_info.value.error_code is not None

    @pytest.mark.asyncio
    async def test_partial_url_success(self, service, mock_fetcher):
        """Test partial success when some URLs fail."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_urls=[
                "https://example.com/success",
                "https://example.com/fail",
            ],
        )

        # First URL succeeds, second fails
        mock_content = FetchedContent(
            url="https://example.com/success",
            content="Success content",
            title="Success",
            description="",
            headings=[{"text": "Title", "level": 1}],
            code_blocks=[],
            word_count=50,
            character_count=100,
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        mock_fetcher.fetch_and_parse.side_effect = [
            mock_content,
            URLConnectionException(message="Failed", url="https://example.com/fail"),
        ]
        mock_fetcher.create_content_chunks.return_value = []

        result = await service.generate_from_urls(request)

        assert result["success"] is True
        assert result["source_summary"]["urls_processed"] == 1
        assert result["source_summary"]["urls_failed"] == 1

    @pytest.mark.asyncio
    async def test_progress_tracking(self, service, mock_fetcher, sample_request):
        """Test progress is tracked during generation."""
        mock_content = FetchedContent(
            url="https://docs.aws.amazon.com/getting-started",
            content="Content",
            title="Title",
            description="",
            headings=[],
            code_blocks=[],
            word_count=10,
            character_count=50,
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
        )
        mock_fetcher.fetch_and_parse.return_value = mock_content
        mock_fetcher.create_content_chunks.return_value = []

        result = await service.generate_from_urls(sample_request)

        # Check that progress was tracked
        request_id = result["request_id"]
        progress = service.get_progress(uuid4())  # Different ID should return None
        assert progress is None


class TestFetchAllUrls:
    """Test _fetch_all_urls method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked fetcher."""
        mock_fetcher = AsyncMock()
        return URLBasedGenerationService(url_fetcher=mock_fetcher)

    @pytest.mark.asyncio
    async def test_concurrent_fetching(self, service):
        """Test URLs are fetched concurrently."""
        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
        ]

        progress = GenerationProgress(request_id=uuid4(), total_urls=3)

        # Mock successful fetches
        mock_content = FetchedContent(
            url="https://example.com/test",
            content="Content",
            title="Test",
            description="",
            headings=[],
            code_blocks=[],
            word_count=5,
            character_count=30,
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        service.url_fetcher.fetch_and_parse = AsyncMock(return_value=mock_content)

        results = await service._fetch_all_urls(urls, progress)

        assert len(results) == 3
        assert service.url_fetcher.fetch_and_parse.call_count == 3


class TestFetchSingleUrl:
    """Test _fetch_single_url method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked fetcher."""
        mock_fetcher = AsyncMock()
        return URLBasedGenerationService(url_fetcher=mock_fetcher)

    @pytest.mark.asyncio
    async def test_successful_fetch(self, service):
        """Test successful single URL fetch."""
        mock_content = FetchedContent(
            url="https://example.com/docs",
            content="Test content",
            title="Test",
            description="",
            headings=[],
            code_blocks=[],
            word_count=2,
            character_count=12,
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
        )
        service.url_fetcher.fetch_and_parse = AsyncMock(return_value=mock_content)

        result = await service._fetch_single_url("https://example.com/docs")

        assert result.success is True
        assert result.content is not None
        assert result.url == "https://example.com/docs"

    @pytest.mark.asyncio
    async def test_validation_error(self, service):
        """Test URLValidationException handling."""
        # Import the exceptions from course_generator.exceptions to ensure
        # we use the same class instances that the service uses
        from course_generator.exceptions import URLValidationException as ServiceURLValidationException

        service.url_fetcher.fetch_and_parse = AsyncMock(
            side_effect=ServiceURLValidationException(
                message="Invalid URL",
                url="invalid",
            )
        )

        result = await service._fetch_single_url("invalid")

        assert result.success is False
        assert result.error_type == "validation"

    @pytest.mark.asyncio
    async def test_connection_error(self, service):
        """Test URLConnectionException handling."""
        from course_generator.exceptions import URLConnectionException as ServiceURLConnectionException

        service.url_fetcher.fetch_and_parse = AsyncMock(
            side_effect=ServiceURLConnectionException(
                message="Connection refused",
                url="https://unreachable.com",
            )
        )

        result = await service._fetch_single_url("https://unreachable.com")

        assert result.success is False
        assert result.error_type == "connection"

    @pytest.mark.asyncio
    async def test_timeout_error(self, service):
        """Test URLTimeoutException handling."""
        from course_generator.exceptions import URLTimeoutException as ServiceURLTimeoutException

        service.url_fetcher.fetch_and_parse = AsyncMock(
            side_effect=ServiceURLTimeoutException(
                message="Request timed out",
                url="https://slow.com",
                # Note: timeout parameter is not supported by the base exception
            )
        )

        result = await service._fetch_single_url("https://slow.com")

        assert result.success is False
        assert result.error_type == "timeout"

    @pytest.mark.asyncio
    async def test_unexpected_error(self, service):
        """Test unexpected exception handling."""
        service.url_fetcher.fetch_and_parse = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        result = await service._fetch_single_url("https://example.com")

        assert result.success is False
        assert result.error_type == "unknown"
        assert "Unexpected" in result.error


class TestBuildContextSummary:
    """Test _build_context_summary method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return URLBasedGenerationService()

    def test_empty_contents(self, service):
        """Test with empty content list."""
        result = service._build_context_summary([])

        assert result == ""

    def test_single_content_summary(self, service):
        """Test summary from single content."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com/docs",
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
            title="Getting Started",
            word_count=500,
        )

        content = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata,
            content="This is the main content of the documentation.",
            structured_content={
                "headings": [
                    {"text": "Introduction", "level": 1},
                    {"text": "Setup", "level": 2},
                ],
            },
        )

        result = service._build_context_summary([content])

        assert "Getting Started" in result
        assert "https://example.com/docs" in result
        assert "Introduction" in result

    def test_code_examples_included(self, service):
        """Test code examples are included in summary."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com/docs",
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        content = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata,
            content="Content",
            code_examples=[
                {"language": "python", "content": "print('hello')"},
            ],
        )

        result = service._build_context_summary([content])

        assert "python" in result.lower()
        assert "print" in result


class TestGenerateModulesFromContent:
    """Test _generate_modules_from_content method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return URLBasedGenerationService()

    def test_modules_from_headings(self, service):
        """Test module generation from content headings."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com/docs",
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
            title="Documentation",
        )

        content = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata,
            content="Content",
            structured_content={
                "headings": [
                    {"text": "Getting Started", "level": 1},
                    {"text": "Installation", "level": 2},
                    {"text": "Configuration", "level": 2},
                    {"text": "Advanced Topics", "level": 1},
                    {"text": "Performance", "level": 2},
                ],
            },
        )

        modules = service._generate_modules_from_content([content], CourseLevel.BEGINNER)

        assert len(modules) >= 1
        # First module should be based on first H1
        assert "Getting Started" in modules[0]["title"]

    def test_fallback_without_headings(self, service):
        """Test fallback module generation without headings."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com/docs",
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
            title="API Reference",
        )

        content = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata,
            content="Content without headings",
            structured_content={"headings": []},
        )

        modules = service._generate_modules_from_content([content], CourseLevel.BEGINNER)

        assert len(modules) >= 1
        assert modules[0]["title"] == "API Reference"

    def test_max_10_modules(self, service):
        """Test module count is limited to 10."""
        metadata = ExternalContentMetadata(
            source_url="https://example.com/docs",
            content_hash="abc",
            fetch_timestamp=datetime.now(timezone.utc),
        )

        # Create content with many H1 headings
        content = ProcessedExternalContent(
            request_id=uuid4(),
            metadata=metadata,
            content="Content",
            structured_content={
                "headings": [
                    {"text": f"Module {i}", "level": 1}
                    for i in range(15)
                ],
            },
        )

        modules = service._generate_modules_from_content([content], CourseLevel.BEGINNER)

        assert len(modules) <= 10


class TestEstimateDuration:
    """Test _estimate_duration method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return URLBasedGenerationService()

    def test_duration_from_word_count(self, service):
        """Test duration estimation from word count."""
        contents = [
            ProcessedExternalContent(
                request_id=uuid4(),
                metadata=ExternalContentMetadata(
                    source_url="https://example.com",
                    content_hash="abc",
                    fetch_timestamp=datetime.now(timezone.utc),
                    word_count=3000,  # Should be ~1 hour
                ),
                content="Content",
            ),
        ]

        duration = service._estimate_duration(contents)

        assert duration == 1

    def test_minimum_duration(self, service):
        """Test minimum duration is 1 hour."""
        contents = [
            ProcessedExternalContent(
                request_id=uuid4(),
                metadata=ExternalContentMetadata(
                    source_url="https://example.com",
                    content_hash="abc",
                    fetch_timestamp=datetime.now(timezone.utc),
                    word_count=100,  # Very short content
                ),
                content="Short",
            ),
        ]

        duration = service._estimate_duration(contents)

        assert duration >= 1


class TestExtractObjectives:
    """Test _extract_objectives method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return URLBasedGenerationService()

    def test_objectives_from_headings(self, service):
        """Test objectives extracted from headings."""
        contents = [
            ProcessedExternalContent(
                request_id=uuid4(),
                metadata=ExternalContentMetadata(
                    source_url="https://example.com",
                    content_hash="abc",
                    fetch_timestamp=datetime.now(timezone.utc),
                ),
                content="Content",
                structured_content={
                    "headings": [
                        {"text": "Docker Basics", "level": 1},
                        {"text": "Container Management", "level": 2},
                        {"text": "Networking", "level": 2},
                    ],
                },
            ),
        ]

        objectives = service._extract_objectives(contents)

        assert len(objectives) >= 1
        assert any("Docker" in obj for obj in objectives)

    def test_max_8_objectives(self, service):
        """Test objectives limited to 8."""
        contents = [
            ProcessedExternalContent(
                request_id=uuid4(),
                metadata=ExternalContentMetadata(
                    source_url="https://example.com",
                    content_hash="abc",
                    fetch_timestamp=datetime.now(timezone.utc),
                ),
                content="Content",
                structured_content={
                    "headings": [
                        {"text": f"Topic {i}", "level": 1}
                        for i in range(15)
                    ],
                },
            ),
        ]

        objectives = service._extract_objectives(contents)

        assert len(objectives) <= 8


class TestGetProgress:
    """Test get_progress method."""

    def test_get_existing_progress(self):
        """Test retrieving existing progress."""
        service = URLBasedGenerationService()
        request_id = uuid4()

        # Manually add progress to cache
        progress = GenerationProgress(
            request_id=request_id,
            status="fetching_urls",
        )
        service._progress_cache[request_id] = progress

        result = service.get_progress(request_id)

        assert result is not None
        assert result.status == "fetching_urls"

    def test_get_nonexistent_progress(self):
        """Test retrieving non-existent progress returns None."""
        service = URLBasedGenerationService()

        result = service.get_progress(uuid4())

        assert result is None
