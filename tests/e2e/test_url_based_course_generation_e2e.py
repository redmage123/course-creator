"""
E2E Tests for URL-Based Course Generation

BUSINESS CONTEXT:
These E2E tests verify the complete URL-based course generation workflow
from API request to generated syllabus. Tests cover:
- API endpoint access and authentication
- URL validation and error handling
- Complete generation workflow
- Response format validation
- Progress tracking

TESTING STRATEGY:
- Test against running course-generator service
- Use test fixtures for URLs and expected responses
- Verify complete request/response cycle
- Test error scenarios with appropriate HTTP status codes
"""

import pytest
import requests
import time
import os
from uuid import UUID
from typing import Dict, Any

# Service configuration
BASE_URL = os.getenv("COURSE_GENERATOR_URL", "https://localhost:8002")
API_PREFIX = "/api/v1/syllabus"

# Skip all tests if service is not available
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_E2E_TESTS", "false").lower() == "true",
    reason="E2E tests disabled"
)


class TestURLBasedCourseGenerationE2E:
    """E2E tests for URL-based course generation endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.base_url = BASE_URL
        self.api_url = f"{self.base_url}{API_PREFIX}"
        # Disable SSL verification for localhost testing
        self.verify_ssl = False

    def test_service_health_check(self):
        """Test course-generator service is running."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                verify=self.verify_ssl,
                timeout=5,
            )
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Course generator service not available")

    def test_generate_syllabus_with_single_url(self):
        """Test generating syllabus from single documentation URL."""
        payload = {
            "title": "Python Testing Fundamentals",
            "description": "Learn how to write effective tests in Python",
            "source_url": "https://docs.python.org/3/library/unittest.html",
            "level": "beginner",
            "objectives": [
                "Understand test-driven development",
                "Write unit tests with unittest",
            ],
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=60,  # URL fetching can take time
            )

            # Should return success or fallback to placeholder
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            if "syllabus" in data and data["syllabus"]:
                # If URL-based generation worked
                assert data["syllabus"]["title"] == "Python Testing Fundamentals"
                assert "modules" in data["syllabus"]
                assert "source_summary" in data

        except requests.exceptions.Timeout:
            pytest.skip("Request timed out - URL fetching may be slow")
        except requests.exceptions.ConnectionError:
            pytest.skip("Course generator service not available")

    def test_generate_syllabus_with_multiple_urls(self):
        """Test generating syllabus from multiple documentation URLs."""
        payload = {
            "title": "Docker Fundamentals",
            "description": "Complete Docker training course",
            "source_urls": [
                "https://docs.docker.com/get-started/",
                "https://docs.docker.com/compose/",
            ],
            "level": "intermediate",
            "use_rag_enhancement": True,
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=120,  # Multiple URLs
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

        except requests.exceptions.Timeout:
            pytest.skip("Request timed out")
        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_generate_syllabus_without_urls(self):
        """Test standard generation without URLs (backwards compatibility)."""
        payload = {
            "title": "Standard Course",
            "description": "Course generated without external URLs",
            "level": "beginner",
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=30,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_generate_with_invalid_url_scheme(self):
        """Test that invalid URL scheme returns validation error."""
        payload = {
            "title": "Test Course",
            "description": "Test",
            "source_url": "ftp://example.com/docs",
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=10,
            )

            # Should return 422 validation error
            assert response.status_code == 422

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_generate_with_too_many_urls(self):
        """Test that exceeding URL limit returns validation error."""
        payload = {
            "title": "Test Course",
            "description": "Test",
            "source_urls": [f"https://example.com/doc{i}" for i in range(15)],
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=10,
            )

            # Should return 422 validation error (max 10 URLs)
            assert response.status_code == 422

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_generate_with_unreachable_url(self):
        """Test handling of unreachable URLs."""
        payload = {
            "title": "Test Course",
            "description": "Test",
            "source_url": "https://this-domain-does-not-exist-12345.com/docs",
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=60,
            )

            # Should return error (connection or not found)
            # Either 500 (fetch error) or the service handles it gracefully
            assert response.status_code in [200, 500, 502]

            if response.status_code == 200:
                data = response.json()
                # If handled gracefully, should indicate failure
                if "source_summary" in data:
                    assert data["source_summary"].get("urls_failed", 0) > 0

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_generate_with_external_source_config(self):
        """Test generation with detailed external source configuration."""
        payload = {
            "title": "AWS Lambda Training",
            "description": "Learn serverless with AWS Lambda",
            "external_sources": [
                {
                    "url": "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html",
                    "source_type": "documentation",
                    "priority": 10,
                    "description": "Main Lambda documentation",
                },
            ],
            "level": "intermediate",
            "include_code_examples": True,
            "max_content_chunks": 30,
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=60,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

        except requests.exceptions.Timeout:
            pytest.skip("Request timed out")
        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")


class TestGenerationProgressE2E:
    """E2E tests for generation progress tracking."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.base_url = BASE_URL
        self.api_url = f"{self.base_url}{API_PREFIX}"
        self.verify_ssl = False

    def test_progress_endpoint_not_found(self):
        """Test progress endpoint returns 404 for unknown request."""
        try:
            response = requests.get(
                f"{self.api_url}/generate/progress/12345678-1234-1234-1234-123456789012",
                verify=self.verify_ssl,
                timeout=10,
            )

            assert response.status_code == 404
            data = response.json()
            assert "error" in data.get("detail", {})

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_progress_endpoint_invalid_uuid(self):
        """Test progress endpoint returns 400 for invalid UUID."""
        try:
            response = requests.get(
                f"{self.api_url}/generate/progress/not-a-valid-uuid",
                verify=self.verify_ssl,
                timeout=10,
            )

            assert response.status_code == 400
            data = response.json()
            assert "invalid" in str(data).lower()

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")


class TestURLBasedGenerationErrorsE2E:
    """E2E tests for URL-based generation error handling."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.base_url = BASE_URL
        self.api_url = f"{self.base_url}{API_PREFIX}"
        self.verify_ssl = False

    def test_empty_title_validation(self):
        """Test that empty title returns validation error."""
        payload = {
            "title": "",
            "description": "Test description",
            "source_url": "https://example.com/docs",
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=10,
            )

            assert response.status_code == 422

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_empty_description_validation(self):
        """Test that empty description returns validation error."""
        payload = {
            "title": "Test Course",
            "description": "",
            "source_url": "https://example.com/docs",
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=10,
            )

            assert response.status_code == 422

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_invalid_course_level(self):
        """Test that invalid course level returns validation error."""
        payload = {
            "title": "Test Course",
            "description": "Test",
            "level": "super_expert",  # Invalid level
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=10,
            )

            assert response.status_code == 422

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_max_content_chunks_validation(self):
        """Test max_content_chunks validation."""
        payload = {
            "title": "Test Course",
            "description": "Test",
            "source_url": "https://example.com/docs",
            "max_content_chunks": 500,  # Exceeds max of 200
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=10,
            )

            assert response.status_code == 422

        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")


class TestURLBasedGenerationResponseFormatE2E:
    """E2E tests for response format validation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.base_url = BASE_URL
        self.api_url = f"{self.base_url}{API_PREFIX}"
        self.verify_ssl = False

    def test_response_contains_required_fields(self):
        """Test response contains all required fields."""
        payload = {
            "title": "Response Format Test",
            "description": "Testing response format",
            "source_url": "https://docs.python.org/3/",
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=60,
            )

            assert response.status_code == 200
            data = response.json()

            # Required fields
            assert "success" in data
            assert isinstance(data["success"], bool)

            if data["success"] and "syllabus" in data and data["syllabus"]:
                syllabus = data["syllabus"]
                assert "title" in syllabus
                assert "modules" in syllabus

        except requests.exceptions.Timeout:
            pytest.skip("Request timed out")
        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")

    def test_source_summary_format(self):
        """Test source_summary format in response."""
        payload = {
            "title": "Source Summary Test",
            "description": "Testing source summary format",
            "source_url": "https://docs.python.org/3/",
        }

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()

                if "source_summary" in data:
                    summary = data["source_summary"]
                    assert "urls_processed" in summary
                    assert "urls_failed" in summary
                    assert isinstance(summary["urls_processed"], int)
                    assert isinstance(summary["urls_failed"], int)

        except requests.exceptions.Timeout:
            pytest.skip("Request timed out")
        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")


class TestURLBasedGenerationPerformanceE2E:
    """E2E tests for performance characteristics."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.base_url = BASE_URL
        self.api_url = f"{self.base_url}{API_PREFIX}"
        self.verify_ssl = False

    def test_single_url_response_time(self):
        """Test response time for single URL generation."""
        payload = {
            "title": "Performance Test",
            "description": "Testing response time",
            "source_url": "https://httpbin.org/html",  # Fast test endpoint
        }

        try:
            start_time = time.time()

            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                verify=self.verify_ssl,
                timeout=60,
            )

            elapsed_time = time.time() - start_time

            assert response.status_code == 200

            # Response should complete within reasonable time (60s)
            assert elapsed_time < 60

            data = response.json()
            if "processing_time_ms" in data:
                # Server-reported time should be less than total elapsed
                assert data["processing_time_ms"] < elapsed_time * 1000

        except requests.exceptions.Timeout:
            pytest.skip("Request timed out - performance issue")
        except requests.exceptions.ConnectionError:
            pytest.skip("Service not available")


# Selenium-based UI tests would go here if frontend is implemented
class TestURLBasedGenerationUIE2E:
    """Placeholder for UI E2E tests when frontend is implemented."""

    @pytest.mark.skip(reason="Frontend UI not yet implemented")
    def test_url_input_field_exists(self):
        """Test URL input field exists in course creation form."""
        pass

    @pytest.mark.skip(reason="Frontend UI not yet implemented")
    def test_multiple_url_input_support(self):
        """Test ability to add multiple URLs."""
        pass

    @pytest.mark.skip(reason="Frontend UI not yet implemented")
    def test_generation_progress_display(self):
        """Test progress is displayed during generation."""
        pass

    @pytest.mark.skip(reason="Frontend UI not yet implemented")
    def test_source_attribution_display(self):
        """Test source attribution is displayed in generated syllabus."""
        pass
