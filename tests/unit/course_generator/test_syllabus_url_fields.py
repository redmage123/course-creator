"""
Unit Tests for Syllabus Model URL Fields (v3.3.2)

BUSINESS CONTEXT:
These tests verify the URL-based course generation fields added to the
SyllabusRequest model in v3.3.2. Tests cover:
- source_url field validation
- source_urls list validation
- external_sources configuration validation
- URL count limits
- has_external_sources property
- all_source_urls property

TESTING STRATEGY:
- Test Pydantic validation for all URL fields
- Verify edge cases and error messages
- Test property computations
- Ensure backwards compatibility with standard requests
"""

import pytest
import importlib.util
from pathlib import Path
from pydantic import ValidationError

# Use explicit path import to avoid collision with other services' models
_course_generator_root = Path(__file__).parent.parent.parent.parent / "services" / "course-generator"
_syllabus_path = _course_generator_root / "models" / "syllabus.py"
_spec = importlib.util.spec_from_file_location("cg_syllabus", _syllabus_path)
_syllabus_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_syllabus_module)

SyllabusRequest = _syllabus_module.SyllabusRequest
ContentSourceType = _syllabus_module.ContentSourceType
ExternalSourceConfig = _syllabus_module.ExternalSourceConfig
CourseLevel = _syllabus_module.CourseLevel


class TestContentSourceTypeEnum:
    """Test ContentSourceType enum for external sources."""

    def test_all_types_exist(self):
        """Test all expected source types exist."""
        expected = [
            "documentation",
            "tutorial",
            "api_reference",
            "knowledge_base",
            "blog",
            "wiki",
            "general",
        ]

        for type_val in expected:
            assert ContentSourceType(type_val)

    def test_documentation_type(self):
        """Test DOCUMENTATION type."""
        assert ContentSourceType.DOCUMENTATION == "documentation"

    def test_api_reference_type(self):
        """Test API_REFERENCE type."""
        assert ContentSourceType.API_REFERENCE == "api_reference"


class TestExternalSourceConfig:
    """Test ExternalSourceConfig model for URL configuration."""

    def test_basic_creation(self):
        """Test basic source config creation."""
        config = ExternalSourceConfig(url="https://example.com/docs")

        assert config.url == "https://example.com/docs"
        assert config.source_type == ContentSourceType.GENERAL
        assert config.priority == 1
        assert config.description is None

    def test_full_configuration(self):
        """Test full source configuration."""
        config = ExternalSourceConfig(
            url="https://api.example.com/reference",
            source_type=ContentSourceType.API_REFERENCE,
            priority=5,
            description="Main API documentation",
        )

        assert config.source_type == ContentSourceType.API_REFERENCE
        assert config.priority == 5
        assert config.description == "Main API documentation"

    def test_url_trimmed(self):
        """Test URL whitespace is trimmed."""
        config = ExternalSourceConfig(url="  https://example.com/docs  ")

        assert config.url == "https://example.com/docs"

    def test_empty_url_raises_error(self):
        """Test empty URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExternalSourceConfig(url="")

        assert "empty" in str(exc_info.value).lower()

    def test_whitespace_url_raises_error(self):
        """Test whitespace-only URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExternalSourceConfig(url="   ")

        assert "empty" in str(exc_info.value).lower()

    def test_invalid_scheme_raises_error(self):
        """Test non-HTTP URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExternalSourceConfig(url="ftp://example.com/file")

        assert "http" in str(exc_info.value).lower()

    def test_url_too_long_raises_error(self):
        """Test URL exceeding max length raises ValidationError."""
        long_url = "https://example.com/" + "a" * 2100

        with pytest.raises(ValidationError) as exc_info:
            ExternalSourceConfig(url=long_url)

        assert "length" in str(exc_info.value).lower()

    def test_priority_minimum(self):
        """Test priority minimum constraint."""
        with pytest.raises(ValidationError):
            ExternalSourceConfig(url="https://example.com", priority=0)

    def test_priority_maximum(self):
        """Test priority maximum constraint."""
        with pytest.raises(ValidationError):
            ExternalSourceConfig(url="https://example.com", priority=11)

    def test_valid_priority_range(self):
        """Test valid priority values."""
        for priority in range(1, 11):
            config = ExternalSourceConfig(
                url="https://example.com",
                priority=priority,
            )
            assert config.priority == priority


class TestSyllabusRequestSourceUrl:
    """Test SyllabusRequest source_url field."""

    def test_request_without_source_url(self):
        """Test request without source_url (backwards compatibility)."""
        request = SyllabusRequest(
            title="Test Course",
            description="Test description",
        )

        assert request.source_url is None
        assert request.has_external_sources is False

    def test_request_with_source_url(self):
        """Test request with single source_url."""
        request = SyllabusRequest(
            title="Test Course",
            description="Test description",
            source_url="https://docs.example.com/guide",
        )

        assert request.source_url == "https://docs.example.com/guide"
        assert request.has_external_sources is True

    def test_source_url_trimmed(self):
        """Test source_url whitespace is trimmed."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_url="  https://example.com/docs  ",
        )

        assert request.source_url == "https://example.com/docs"

    def test_empty_source_url_becomes_none(self):
        """Test empty source_url becomes None."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_url="",
        )

        assert request.source_url is None

    def test_whitespace_source_url_becomes_none(self):
        """Test whitespace-only source_url becomes None."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_url="   ",
        )

        assert request.source_url is None

    def test_invalid_source_url_scheme(self):
        """Test invalid URL scheme raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SyllabusRequest(
                title="Test",
                description="Test",
                source_url="ftp://example.com/docs",
            )

        assert "http" in str(exc_info.value).lower()

    def test_source_url_too_long(self):
        """Test source_url exceeding max length raises error."""
        long_url = "https://example.com/" + "x" * 2100

        with pytest.raises(ValidationError) as exc_info:
            SyllabusRequest(
                title="Test",
                description="Test",
                source_url=long_url,
            )

        assert "length" in str(exc_info.value).lower()


class TestSyllabusRequestSourceUrls:
    """Test SyllabusRequest source_urls field."""

    def test_request_with_empty_source_urls(self):
        """Test request with empty source_urls list."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_urls=[],
        )

        assert request.source_urls == []
        assert request.has_external_sources is False

    def test_request_with_single_source_url_in_list(self):
        """Test request with single URL in source_urls."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_urls=["https://example.com/docs"],
        )

        assert len(request.source_urls) == 1
        assert request.has_external_sources is True

    def test_request_with_multiple_source_urls(self):
        """Test request with multiple URLs in source_urls."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_urls=[
                "https://example.com/docs",
                "https://api.example.com/reference",
                "https://blog.example.com/tutorial",
            ],
        )

        assert len(request.source_urls) == 3

    def test_source_urls_items_trimmed(self):
        """Test source_urls items are trimmed."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_urls=["  https://example.com/docs  "],
        )

        assert request.source_urls[0] == "https://example.com/docs"

    def test_empty_item_in_source_urls_raises_error(self):
        """Test empty URL in source_urls raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SyllabusRequest(
                title="Test",
                description="Test",
                source_urls=["https://example.com", ""],
            )

        assert "empty" in str(exc_info.value).lower()

    def test_invalid_scheme_in_source_urls(self):
        """Test invalid URL scheme in source_urls raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SyllabusRequest(
                title="Test",
                description="Test",
                source_urls=["https://example.com", "ftp://example.com/file"],
            )

        assert "http" in str(exc_info.value).lower()


class TestSyllabusRequestExternalSources:
    """Test SyllabusRequest external_sources field."""

    def test_request_with_external_sources(self):
        """Test request with external_sources configuration."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            external_sources=[
                ExternalSourceConfig(
                    url="https://docs.example.com",
                    source_type=ContentSourceType.DOCUMENTATION,
                ),
            ],
        )

        assert len(request.external_sources) == 1
        assert request.has_external_sources is True

    def test_request_with_multiple_external_sources(self):
        """Test request with multiple external sources."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            external_sources=[
                ExternalSourceConfig(
                    url="https://docs.example.com",
                    source_type=ContentSourceType.DOCUMENTATION,
                    priority=10,
                ),
                ExternalSourceConfig(
                    url="https://api.example.com",
                    source_type=ContentSourceType.API_REFERENCE,
                    priority=5,
                ),
            ],
        )

        assert len(request.external_sources) == 2


class TestSyllabusRequestUrlCountLimit:
    """Test SyllabusRequest URL count validation."""

    def test_max_10_urls_from_source_url_and_source_urls(self):
        """Test max 10 URLs across source_url and source_urls."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_url="https://example.com/main",
            source_urls=[f"https://example.com/doc{i}" for i in range(9)],
        )

        assert len(request.all_source_urls) == 10

    def test_exceeding_10_urls_raises_error(self):
        """Test exceeding 10 URLs raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SyllabusRequest(
                title="Test",
                description="Test",
                source_urls=[f"https://example.com/doc{i}" for i in range(11)],
            )

        assert "10" in str(exc_info.value)

    def test_combined_urls_exceed_limit(self):
        """Test combined URLs from all fields exceeding limit."""
        with pytest.raises(ValidationError) as exc_info:
            SyllabusRequest(
                title="Test",
                description="Test",
                source_url="https://example.com/main",
                source_urls=[f"https://example.com/doc{i}" for i in range(5)],
                external_sources=[
                    ExternalSourceConfig(url=f"https://ext.example.com/doc{i}")
                    for i in range(6)
                ],
            )

        assert "Too many" in str(exc_info.value) or "10" in str(exc_info.value)


class TestSyllabusRequestHasExternalSources:
    """Test has_external_sources property."""

    def test_false_without_urls(self):
        """Test has_external_sources is False without URLs."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
        )

        assert request.has_external_sources is False

    def test_true_with_source_url(self):
        """Test has_external_sources is True with source_url."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_url="https://example.com/docs",
        )

        assert request.has_external_sources is True

    def test_true_with_source_urls(self):
        """Test has_external_sources is True with source_urls."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_urls=["https://example.com/docs"],
        )

        assert request.has_external_sources is True

    def test_true_with_external_sources(self):
        """Test has_external_sources is True with external_sources."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            external_sources=[
                ExternalSourceConfig(url="https://example.com/docs"),
            ],
        )

        assert request.has_external_sources is True


class TestSyllabusRequestAllSourceUrls:
    """Test all_source_urls property."""

    def test_empty_when_no_urls(self):
        """Test all_source_urls is empty without URLs."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
        )

        assert request.all_source_urls == []

    def test_includes_source_url(self):
        """Test all_source_urls includes source_url."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_url="https://example.com/main",
        )

        assert "https://example.com/main" in request.all_source_urls

    def test_includes_source_urls(self):
        """Test all_source_urls includes source_urls."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_urls=["https://example.com/1", "https://example.com/2"],
        )

        assert "https://example.com/1" in request.all_source_urls
        assert "https://example.com/2" in request.all_source_urls

    def test_includes_external_sources(self):
        """Test all_source_urls includes external_sources URLs."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            external_sources=[
                ExternalSourceConfig(url="https://ext.example.com/docs"),
            ],
        )

        assert "https://ext.example.com/docs" in request.all_source_urls

    def test_combines_all_url_sources(self):
        """Test all_source_urls combines all URL sources."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_url="https://example.com/main",
            source_urls=["https://example.com/docs"],
            external_sources=[
                ExternalSourceConfig(url="https://ext.example.com/api"),
            ],
        )

        urls = request.all_source_urls

        assert len(urls) == 3
        assert "https://example.com/main" in urls
        assert "https://example.com/docs" in urls
        assert "https://ext.example.com/api" in urls

    def test_no_duplicate_urls(self):
        """Test all_source_urls deduplicates external_sources against existing URLs.

        Note: The implementation only deduplicates external_sources URLs against
        URLs already in the list. It doesn't deduplicate between source_url and
        source_urls as these should be validated at input time.
        """
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_url="https://example.com/docs",
            source_urls=["https://example.com/extra"],
            external_sources=[
                # This URL is already in source_url, so it should not be added again
                ExternalSourceConfig(url="https://example.com/docs"),
            ],
        )

        urls = request.all_source_urls

        # external_sources URL that matches source_url should not appear twice
        assert urls.count("https://example.com/docs") == 1
        # But there should be 2 URLs total (source_url + source_urls[0])
        assert len(urls) == 2

    def test_source_url_first(self):
        """Test source_url is first in all_source_urls."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            source_url="https://example.com/main",
            source_urls=["https://example.com/other"],
        )

        assert request.all_source_urls[0] == "https://example.com/main"


class TestSyllabusRequestUrlProcessingOptions:
    """Test URL processing option fields."""

    def test_default_use_rag_enhancement(self):
        """Test use_rag_enhancement defaults to True."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
        )

        assert request.use_rag_enhancement is True

    def test_default_include_code_examples(self):
        """Test include_code_examples defaults to True."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
        )

        assert request.include_code_examples is True

    def test_default_max_content_chunks(self):
        """Test max_content_chunks default value."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
        )

        assert request.max_content_chunks == 50

    def test_custom_processing_options(self):
        """Test custom processing options."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            use_rag_enhancement=False,
            include_code_examples=False,
            max_content_chunks=100,
        )

        assert request.use_rag_enhancement is False
        assert request.include_code_examples is False
        assert request.max_content_chunks == 100

    def test_max_content_chunks_minimum(self):
        """Test max_content_chunks minimum constraint."""
        with pytest.raises(ValidationError):
            SyllabusRequest(
                title="Test",
                description="Test",
                max_content_chunks=0,
            )

    def test_max_content_chunks_maximum(self):
        """Test max_content_chunks maximum constraint."""
        with pytest.raises(ValidationError):
            SyllabusRequest(
                title="Test",
                description="Test",
                max_content_chunks=201,
            )


class TestSyllabusRequestBackwardsCompatibility:
    """Test backwards compatibility with standard requests."""

    def test_standard_request_still_works(self):
        """Test standard request without URLs works."""
        request = SyllabusRequest(
            title="Python Fundamentals",
            description="Learn Python programming basics",
            level=CourseLevel.BEGINNER,
            duration=20,
            objectives=["Understand variables", "Write functions"],
            prerequisites=["Basic computer skills"],
            target_audience="Beginners",
        )

        assert request.title == "Python Fundamentals"
        assert request.level == CourseLevel.BEGINNER
        assert request.has_external_sources is False

    def test_standard_request_ignores_url_options(self):
        """Test URL options don't affect standard requests."""
        request = SyllabusRequest(
            title="Test",
            description="Test",
            use_rag_enhancement=False,  # Still valid option
        )

        assert request.use_rag_enhancement is False
        assert request.has_external_sources is False
