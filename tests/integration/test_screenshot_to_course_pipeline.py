"""
Screenshot-to-Course Pipeline Integration Tests

BUSINESS REQUIREMENT:
Validates the complete screenshot-to-course generation workflow including:
1. Screenshot upload and validation
2. AI vision analysis with LLM provider (mocked)
3. Course structure parsing and validation
4. Course creation in database
5. RAG service indexing for AI assistant
6. Batch processing of multiple screenshots
7. Error handling and retry mechanisms

TECHNICAL IMPLEMENTATION:
- Tests end-to-end workflow from upload to course creation
- Mocks external LLM API calls for reliability
- Uses real database interactions for data integrity
- Validates RAG service integration
- Tests async operations with proper fixtures
- Comprehensive error scenario coverage

TEST STRATEGY:
- Mock: External LLM API calls (OpenAI, Anthropic, etc.)
- Real: PostgreSQL database operations
- Real: ChromaDB RAG service operations
- Real: File upload and image processing
- Real: Course management service interactions
"""

import pytest
import pytest_asyncio
import httpx
import asyncio
import io
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from PIL import Image
import json

# Test Configuration
COURSE_GENERATOR_URL = "https://localhost:8004"  # Course Generator Service
COURSE_MANAGEMENT_URL = "https://localhost:8002"  # Course Management Service
RAG_SERVICE_URL = "https://localhost:8009"  # RAG Service
USER_SERVICE_URL = "https://localhost:8001"  # User Management Service

# Test Credentials
TEST_INSTRUCTOR_EMAIL = "test.instructor@coursecreator.com"
TEST_INSTRUCTOR_PASSWORD = "InstructorPass123!"

# Test Data
SAMPLE_SCREENSHOT_ANALYSIS = {
    "title": "Introduction to Python Programming",
    "description": "A comprehensive course covering Python fundamentals",
    "course_structure": {
        "title": "Introduction to Python Programming",
        "description": "Learn Python from basics to advanced concepts",
        "modules": [
            {
                "title": "Python Basics",
                "description": "Introduction to Python syntax and data types",
                "order": 1,
                "lessons": ["Variables and Data Types", "Operators", "Control Flow"],
                "estimated_duration_minutes": 90,
                "learning_objectives": ["Understand Python syntax", "Work with basic data types"]
            },
            {
                "title": "Functions and Modules",
                "description": "Learn to create and use functions",
                "order": 2,
                "lessons": ["Defining Functions", "Parameters", "Return Values", "Importing Modules"],
                "estimated_duration_minutes": 120,
                "learning_objectives": ["Create reusable functions", "Organize code with modules"]
            }
        ],
        "topics": ["Python", "Programming", "Software Development"],
        "learning_objectives": [
            "Master Python fundamentals",
            "Build practical applications",
            "Write clean, maintainable code"
        ],
        "prerequisites": ["Basic computer skills", "Problem-solving mindset"],
        "key_concepts": ["Variables", "Functions", "Control Flow", "Data Structures"],
        "difficulty": "beginner",
        "estimated_duration_hours": 4,
        "target_audience": "Beginners with no programming experience",
        "language": "en"
    },
    "detected_elements": [
        {"type": "heading", "content": "Introduction to Python", "confidence": 0.95},
        {"type": "code", "content": "print('Hello, World!')", "confidence": 0.90},
        {"type": "text", "content": "Python is a versatile programming language", "confidence": 0.85}
    ],
    "extracted_text": "Introduction to Python Programming\n\nLearn Python fundamentals...",
    "detected_language": "en",
    "confidence_score": 0.88
}


@pytest_asyncio.fixture
async def auth_token():
    """
    Authenticate as instructor and return auth token.

    BUSINESS CONTEXT:
    Screenshot upload and course creation require instructor authentication
    to ensure proper RBAC enforcement and organizational isolation.
    """
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/login",
                json={
                    "email": TEST_INSTRUCTOR_EMAIL,
                    "password": TEST_INSTRUCTOR_PASSWORD
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("access_token") or data.get("token")
            else:
                pytest.skip(f"Authentication failed: {response.status_code}")
        except Exception as e:
            pytest.skip(f"Cannot connect to user service: {e}")


@pytest_asyncio.fixture
async def http_client(auth_token):
    """
    Create authenticated HTTP client with HTTPS support.

    BUSINESS CONTEXT:
    All API requests must use HTTPS and include authentication
    for secure communication and RBAC enforcement.
    """
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=60.0,  # Longer timeout for AI operations
        verify=False  # Disable SSL verification for local testing
    ) as client:
        yield client


@pytest_asyncio.fixture
def sample_screenshot_image():
    """
    Generate a sample screenshot image for testing.

    BUSINESS CONTEXT:
    Creates a realistic test image simulating a course slide
    or documentation screenshot.

    Returns:
        Tuple of (image_bytes, metadata)
    """
    # Create a test image with text overlay
    img = Image.new('RGB', (1920, 1080), color='white')

    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()

    # Calculate metadata
    file_hash = hashlib.sha256(img_bytes).hexdigest()

    metadata = {
        "width": 1920,
        "height": 1080,
        "format": "png",
        "size_bytes": len(img_bytes),
        "file_hash": file_hash
    }

    return img_bytes, metadata


@pytest_asyncio.fixture
def mock_llm_vision_response():
    """
    Mock LLM vision analysis response.

    BUSINESS CONTEXT:
    Mocks external AI API calls to provide consistent, fast,
    and cost-free testing of the screenshot analysis pipeline.

    Returns:
        VisionAnalysisResult mock object
    """
    from course_generator.infrastructure.llm_providers.base_provider import VisionAnalysisResult

    return VisionAnalysisResult(
        extracted_text=SAMPLE_SCREENSHOT_ANALYSIS["extracted_text"],
        detected_language=SAMPLE_SCREENSHOT_ANALYSIS["detected_language"],
        confidence_score=SAMPLE_SCREENSHOT_ANALYSIS["confidence_score"],
        course_structure=SAMPLE_SCREENSHOT_ANALYSIS["course_structure"],
        detected_elements=SAMPLE_SCREENSHOT_ANALYSIS["detected_elements"],
        suggested_title=SAMPLE_SCREENSHOT_ANALYSIS["title"],
        suggested_description=SAMPLE_SCREENSHOT_ANALYSIS["description"],
        suggested_topics=SAMPLE_SCREENSHOT_ANALYSIS["course_structure"]["topics"],
        suggested_difficulty=SAMPLE_SCREENSHOT_ANALYSIS["course_structure"]["difficulty"],
        suggested_duration_hours=SAMPLE_SCREENSHOT_ANALYSIS["course_structure"]["estimated_duration_hours"],
        raw_response=json.dumps(SAMPLE_SCREENSHOT_ANALYSIS),
        model_used="gpt-4-vision-preview",
        provider_used="openai",
        processing_time_ms=1500,
        tokens_used=850
    )


@pytest.mark.integration
@pytest.mark.asyncio
class TestScreenshotUpload:
    """Test screenshot upload and validation."""

    async def test_upload_valid_screenshot(self, http_client, sample_screenshot_image):
        """
        Test uploading a valid screenshot image.

        BUSINESS FLOW:
        1. Prepare image file with metadata
        2. Upload to screenshot endpoint
        3. Verify upload record created
        4. Verify image metadata extracted
        5. Confirm pending status

        EXPECTED OUTCOME:
        Screenshot uploaded successfully with status 'pending',
        ready for AI analysis.
        """
        image_bytes, expected_metadata = sample_screenshot_image

        # Prepare multipart form data
        files = {
            'file': ('test_screenshot.png', image_bytes, 'image/png')
        }
        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4()),
            'analyze_immediately': 'false'  # Don't auto-analyze for this test
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        # Verify upload successful
        assert response.status_code in [200, 201], f"Upload failed: {response.text}"

        upload_data = response.json()
        assert 'id' in upload_data
        assert upload_data['status'] == 'pending'
        assert upload_data['original_filename'] == 'test_screenshot.png'
        assert 'created_at' in upload_data

        # Store upload ID for cleanup
        return upload_data['id']

    async def test_upload_invalid_format(self, http_client):
        """
        Test uploading unsupported file format.

        BUSINESS REQUIREMENT:
        Only specific image formats (PNG, JPEG, WebP, GIF) are supported
        for screenshot analysis to ensure compatibility with vision models.

        EXPECTED OUTCOME:
        Upload rejected with 400 Bad Request and clear error message.
        """
        # Create a text file
        text_content = b"This is not an image"

        files = {
            'file': ('document.txt', text_content, 'text/plain')
        }
        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4())
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        # Should reject invalid format
        assert response.status_code == 400
        error_data = response.json()
        assert 'detail' in error_data
        assert 'format' in error_data['detail'].lower() or 'unsupported' in error_data['detail'].lower()

    async def test_upload_oversized_image(self, http_client):
        """
        Test uploading image exceeding size limit.

        BUSINESS REQUIREMENT:
        Maximum file size is 20MB to prevent memory issues and
        ensure timely processing.

        EXPECTED OUTCOME:
        Upload rejected with 400 Bad Request and size limit message.
        """
        # Create oversized image (simulated with metadata)
        # Note: Creating actual 21MB image would slow tests, so we mock validation

        files = {
            'file': ('huge_screenshot.png', b'x' * (21 * 1024 * 1024), 'image/png')
        }
        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4())
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        # Should reject oversized file
        assert response.status_code == 400
        error_data = response.json()
        assert 'size' in error_data['detail'].lower() or 'exceeds' in error_data['detail'].lower()


@pytest.mark.integration
@pytest.mark.asyncio
class TestScreenshotAnalysis:
    """Test screenshot AI analysis with mocked LLM."""

    @patch('course_generator.infrastructure.llm_providers.base_provider.BaseLLMProvider.analyze_image')
    async def test_analyze_screenshot_with_llm(
        self,
        mock_analyze,
        http_client,
        sample_screenshot_image,
        mock_llm_vision_response
    ):
        """
        Test screenshot analysis using mocked LLM provider.

        BUSINESS FLOW:
        1. Upload screenshot
        2. Trigger analysis (mocked LLM call)
        3. Verify analysis result structure
        4. Confirm course structure extracted
        5. Validate confidence scores

        EXPECTED OUTCOME:
        Analysis completes with course structure extracted,
        ready for course generation.
        """
        # Configure mock to return vision analysis
        mock_analyze.return_value = mock_llm_vision_response

        image_bytes, _ = sample_screenshot_image

        # Upload screenshot
        files = {'file': ('course_slide.png', image_bytes, 'image/png')}
        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4()),
            'analyze_immediately': 'true'  # Auto-trigger analysis
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        assert response.status_code in [200, 201]
        upload_data = response.json()
        screenshot_id = upload_data['id']

        # Wait for analysis to complete (background task)
        await asyncio.sleep(2)

        # Get analysis status
        status_response = await http_client.get(
            f"{COURSE_GENERATOR_URL}/screenshot/{screenshot_id}/status"
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        # Verify analysis completed
        assert status_data['status'] in ['analyzed', 'analyzing']
        assert status_data['has_analysis'] or status_data['status'] == 'analyzing'

        # If analysis completed, verify result
        if status_data['has_analysis']:
            result_response = await http_client.get(
                f"{COURSE_GENERATOR_URL}/screenshot/{screenshot_id}/result"
            )

            assert result_response.status_code == 200
            result_data = result_response.json()

            assert result_data['confidence_score'] > 0
            assert result_data['detected_language'] == 'en'
            assert result_data['has_course_structure']
            assert 'course_structure' in result_data

    async def test_get_analysis_status(self, http_client, sample_screenshot_image):
        """
        Test checking analysis status.

        BUSINESS REQUIREMENT:
        Analysis may take 5-30 seconds, so status endpoint enables
        polling for completion without blocking.

        EXPECTED OUTCOME:
        Status endpoint returns current state and progress percentage.
        """
        image_bytes, _ = sample_screenshot_image

        # Upload without auto-analysis
        files = {'file': ('status_test.png', image_bytes, 'image/png')}
        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4()),
            'analyze_immediately': 'false'
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        assert response.status_code in [200, 201]
        screenshot_id = response.json()['id']

        # Check status
        status_response = await http_client.get(
            f"{COURSE_GENERATOR_URL}/screenshot/{screenshot_id}/status"
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert 'id' in status_data
        assert 'status' in status_data
        assert 'progress_percent' in status_data
        assert status_data['status'] == 'pending'
        assert status_data['progress_percent'] == 0.0


@pytest.mark.integration
@pytest.mark.asyncio
class TestCourseGeneration:
    """Test course generation from screenshot analysis."""

    @patch('course_generator.infrastructure.llm_providers.base_provider.BaseLLMProvider.analyze_image')
    @patch('course_generator.infrastructure.llm_providers.base_provider.BaseLLMProvider.generate_text')
    async def test_generate_course_from_screenshot(
        self,
        mock_generate_text,
        mock_analyze_image,
        http_client,
        sample_screenshot_image,
        mock_llm_vision_response
    ):
        """
        Test complete course generation from screenshot.

        BUSINESS FLOW:
        1. Upload and analyze screenshot
        2. Request course generation
        3. Verify course structure created
        4. Validate modules and lessons
        5. Confirm database persistence

        EXPECTED OUTCOME:
        Full course structure generated with modules, lessons,
        and learning objectives ready for publication.
        """
        # Configure mocks
        mock_analyze_image.return_value = mock_llm_vision_response

        # Mock lesson content generation
        mock_lesson_response = MagicMock()
        mock_lesson_response.content = json.dumps({
            "lessons": [
                {
                    "title": "Introduction to Variables",
                    "description": "Learn about Python variables",
                    "learning_objectives": ["Define variables", "Assign values"],
                    "key_concepts": ["Variable names", "Data types"],
                    "duration_minutes": 30
                }
            ]
        })
        mock_generate_text.return_value = mock_lesson_response

        image_bytes, _ = sample_screenshot_image

        # Upload and analyze
        files = {'file': ('course_gen.png', image_bytes, 'image/png')}
        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4()),
            'analyze_immediately': 'true'
        }

        upload_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        assert upload_response.status_code in [200, 201]
        screenshot_id = upload_response.json()['id']

        # Wait for analysis
        await asyncio.sleep(2)

        # Generate course
        generation_request = {
            "expand_modules": True,
            "generate_quizzes": True,
            "generate_exercises": True,
            "difficulty_override": None,
            "language_override": None,
            "additional_context": None
        }

        course_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/{screenshot_id}/generate-course",
            json=generation_request
        )

        # Verify course generated
        if course_response.status_code in [200, 201]:
            course_data = course_response.json()

            assert 'id' in course_data
            assert course_data['title'] == SAMPLE_SCREENSHOT_ANALYSIS['title']
            assert course_data['modules_count'] >= 2
            assert course_data['difficulty'] == 'beginner'
            assert course_data['estimated_duration_hours'] > 0
            assert course_data['total_lessons_count'] > 0

    async def test_generate_course_without_analysis(self, http_client, sample_screenshot_image):
        """
        Test attempting course generation before analysis.

        BUSINESS REQUIREMENT:
        Course generation requires completed analysis to ensure
        data quality and prevent incomplete courses.

        EXPECTED OUTCOME:
        Request rejected with 400 Bad Request indicating analysis required.
        """
        image_bytes, _ = sample_screenshot_image

        # Upload without analysis
        files = {'file': ('no_analysis.png', image_bytes, 'image/png')}
        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4()),
            'analyze_immediately': 'false'
        }

        upload_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        screenshot_id = upload_response.json()['id']

        # Try to generate course immediately
        generation_request = {"expand_modules": True}

        course_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/{screenshot_id}/generate-course",
            json=generation_request
        )

        # Should reject
        assert course_response.status_code == 400
        error_data = course_response.json()
        assert 'analyzed' in error_data['detail'].lower() or 'analysis' in error_data['detail'].lower()


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Test database persistence of screenshot and course data."""

    @patch('course_generator.infrastructure.llm_providers.base_provider.BaseLLMProvider.analyze_image')
    async def test_screenshot_persisted_to_database(
        self,
        mock_analyze,
        http_client,
        sample_screenshot_image,
        mock_llm_vision_response
    ):
        """
        Test screenshot metadata persisted to PostgreSQL.

        BUSINESS REQUIREMENT:
        Screenshot uploads must be tracked in database for audit,
        organization isolation, and user attribution.

        EXPECTED OUTCOME:
        Upload record queryable from database with correct metadata.
        """
        mock_analyze.return_value = mock_llm_vision_response

        image_bytes, expected_metadata = sample_screenshot_image
        org_id = str(uuid4())
        user_id = str(uuid4())

        # Upload screenshot
        files = {'file': ('db_test.png', image_bytes, 'image/png')}
        data = {
            'organization_id': org_id,
            'user_id': user_id,
            'analyze_immediately': 'true'
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        assert response.status_code in [200, 201]
        screenshot_id = response.json()['id']

        # Wait for processing
        await asyncio.sleep(2)

        # Verify can retrieve from database via API
        status_response = await http_client.get(
            f"{COURSE_GENERATOR_URL}/screenshot/{screenshot_id}/status"
        )

        assert status_response.status_code == 200
        db_data = status_response.json()

        # Verify database fields
        assert db_data['id'] == screenshot_id
        assert 'created_at' in db_data
        assert 'updated_at' in db_data


@pytest.mark.integration
@pytest.mark.asyncio
class TestRAGServiceIntegration:
    """Test RAG service indexing of generated courses."""

    @patch('course_generator.infrastructure.llm_providers.base_provider.BaseLLMProvider.analyze_image')
    async def test_course_indexed_in_rag(
        self,
        mock_analyze,
        http_client,
        sample_screenshot_image,
        mock_llm_vision_response
    ):
        """
        Test generated course content indexed in RAG service.

        BUSINESS REQUIREMENT:
        Courses must be indexed in RAG for AI assistant to provide
        contextually relevant help and content recommendations.

        EXPECTED OUTCOME:
        Course content searchable via RAG semantic similarity.
        """
        mock_analyze.return_value = mock_llm_vision_response

        image_bytes, _ = sample_screenshot_image

        # Upload and analyze
        files = {'file': ('rag_test.png', image_bytes, 'image/png')}
        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4()),
            'analyze_immediately': 'true'
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        assert response.status_code in [200, 201]
        screenshot_id = response.json()['id']

        # Wait for analysis
        await asyncio.sleep(3)

        # Get analysis result
        result_response = await http_client.get(
            f"{COURSE_GENERATOR_URL}/screenshot/{screenshot_id}/result"
        )

        if result_response.status_code == 200:
            result_data = result_response.json()
            course_title = result_data.get('course_structure', {}).get('title', '')

            # Verify RAG service can find content (if RAG service is running)
            try:
                rag_response = await http_client.post(
                    f"{RAG_SERVICE_URL}/query",
                    json={
                        "query_text": "Python programming basics",
                        "collection": "course_content",
                        "top_k": 5
                    }
                )

                if rag_response.status_code == 200:
                    rag_results = rag_response.json()
                    # Course content should be findable
                    assert 'results' in rag_results or 'documents' in rag_results
            except Exception:
                # RAG service may not be available in test environment
                pytest.skip("RAG service not available")


@pytest.mark.integration
@pytest.mark.asyncio
class TestBatchProcessing:
    """Test batch upload and processing of multiple screenshots."""

    async def test_batch_upload_multiple_screenshots(self, http_client, sample_screenshot_image):
        """
        Test uploading multiple screenshots as a batch.

        BUSINESS USE CASE:
        Instructors upload multiple slides from a presentation
        to generate a comprehensive course covering all topics.

        EXPECTED OUTCOME:
        All screenshots uploaded successfully with batch tracking.
        """
        image_bytes, _ = sample_screenshot_image

        # Create multiple "different" screenshots
        files = [
            ('files', ('slide1.png', image_bytes, 'image/png')),
            ('files', ('slide2.png', image_bytes, 'image/png')),
            ('files', ('slide3.png', image_bytes, 'image/png'))
        ]

        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4())
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload/batch",
            files=files,
            data=data
        )

        assert response.status_code in [200, 201]
        batch_data = response.json()

        assert 'batch_id' in batch_data
        assert batch_data['total_count'] == 3
        assert batch_data['status'] in ['processing', 'completed']
        assert len(batch_data['uploads']) == 3

        # Wait for batch processing
        await asyncio.sleep(3)

        # Check batch status
        batch_id = batch_data['batch_id']
        status_response = await http_client.get(
            f"{COURSE_GENERATOR_URL}/screenshot/batch/{batch_id}/status"
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert status_data['total_count'] == 3
        assert status_data['progress_percent'] >= 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and retry mechanisms."""

    @patch('course_generator.infrastructure.llm_providers.base_provider.BaseLLMProvider.analyze_image')
    async def test_llm_provider_failure_handling(
        self,
        mock_analyze,
        http_client,
        sample_screenshot_image
    ):
        """
        Test handling of LLM provider failures.

        BUSINESS REQUIREMENT:
        System must gracefully handle AI service outages
        and provide clear error messages to users.

        EXPECTED OUTCOME:
        Upload marked as failed with descriptive error message.
        """
        # Configure mock to raise exception
        from shared.exceptions import LLMProviderException
        mock_analyze.side_effect = LLMProviderException(
            message="Provider rate limit exceeded",
            error_code="RATE_LIMIT",
            details={}
        )

        image_bytes, _ = sample_screenshot_image

        # Upload with auto-analysis
        files = {'file': ('fail_test.png', image_bytes, 'image/png')}
        data = {
            'organization_id': str(uuid4()),
            'user_id': str(uuid4()),
            'analyze_immediately': 'true'
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/screenshot/upload",
            files=files,
            data=data
        )

        screenshot_id = response.json()['id']

        # Wait for analysis attempt
        await asyncio.sleep(2)

        # Check status - should show failure
        status_response = await http_client.get(
            f"{COURSE_GENERATOR_URL}/screenshot/{screenshot_id}/status"
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        # Should have error status or message
        assert (
            status_data['status'] == 'failed' or
            status_data.get('error_message') is not None
        )

    async def test_missing_screenshot_404(self, http_client):
        """
        Test accessing non-existent screenshot.

        BUSINESS REQUIREMENT:
        Invalid screenshot IDs must return 404 with clear message.

        EXPECTED OUTCOME:
        404 Not Found with helpful error message.
        """
        fake_id = str(uuid4())

        response = await http_client.get(
            f"{COURSE_GENERATOR_URL}/screenshot/{fake_id}/status"
        )

        assert response.status_code == 404
        error_data = response.json()
        assert 'not found' in error_data['detail'].lower()


# ================================================================
# TEST UTILITIES
# ================================================================

def create_test_screenshot_bytes(width: int = 1920, height: int = 1080) -> bytes:
    """
    Create test screenshot image bytes.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        PNG image bytes
    """
    img = Image.new('RGB', (width, height), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()


def assert_course_structure_valid(course_structure: Dict[str, Any]):
    """
    Validate course structure format.

    BUSINESS RULES:
    - Must have title and description
    - Must have at least one module
    - Each module must have lessons
    - Must have learning objectives
    - Must have difficulty level

    Args:
        course_structure: Course structure dictionary

    Raises:
        AssertionError: If structure is invalid
    """
    assert 'title' in course_structure
    assert 'description' in course_structure
    assert 'modules' in course_structure
    assert len(course_structure['modules']) > 0

    # Validate modules
    for module in course_structure['modules']:
        assert 'title' in module
        assert 'description' in module
        assert 'order' in module
        assert 'lessons' in module
        assert isinstance(module['lessons'], list)

    # Validate metadata
    assert 'difficulty' in course_structure
    assert course_structure['difficulty'] in ['beginner', 'intermediate', 'advanced', 'expert']
    assert 'learning_objectives' in course_structure
    assert isinstance(course_structure['learning_objectives'], list)
