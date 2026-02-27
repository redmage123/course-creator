# Screenshot-to-Course Pipeline Integration Tests

## Overview

Comprehensive integration test suite for the screenshot-to-course generation pipeline, validating the complete workflow from image upload through AI analysis to course creation and RAG indexing.

**Location**: `/home/bbrelin/course-creator/tests/integration/test_screenshot_to_course_pipeline.py`

**Test Count**: 12 comprehensive tests across 8 test classes

**Lines of Code**: 934

**Test Framework**: pytest with async support

## Test Coverage

### 1. TestScreenshotUpload (3 tests)
Tests the screenshot upload and validation phase.

- **test_upload_valid_screenshot**: Validates successful upload of PNG screenshot with metadata extraction
- **test_upload_invalid_format**: Verifies rejection of unsupported file formats (txt, doc, etc.)
- **test_upload_oversized_image**: Confirms 20MB file size limit enforcement

**Business Value**: Ensures only valid images are accepted, preventing processing errors and resource waste.

### 2. TestScreenshotAnalysis (2 tests)
Tests AI vision analysis with mocked LLM providers.

- **test_analyze_screenshot_with_llm**: Validates complete analysis workflow with mocked OpenAI/Anthropic API
- **test_get_analysis_status**: Verifies status polling for long-running analysis operations

**Business Value**: Confirms reliable analysis pipeline with proper status tracking for user feedback.

### 3. TestCourseGeneration (2 tests)
Tests course structure generation from analyzed screenshots.

- **test_generate_course_from_screenshot**: Validates complete course generation with modules and lessons
- **test_generate_course_without_analysis**: Ensures analysis prerequisite enforcement

**Business Value**: Guarantees high-quality course generation with proper validation gates.

### 4. TestDatabaseIntegration (1 test)
Tests PostgreSQL persistence of screenshot and course data.

- **test_screenshot_persisted_to_database**: Validates database storage and retrieval

**Business Value**: Ensures data durability, audit trail, and organization isolation.

### 5. TestRAGServiceIntegration (1 test)
Tests ChromaDB RAG service indexing of generated courses.

- **test_course_indexed_in_rag**: Validates semantic search indexing for AI assistant

**Business Value**: Enables AI-powered contextual help and content recommendations.

### 6. TestBatchProcessing (1 test)
Tests batch upload of multiple screenshots.

- **test_batch_upload_multiple_screenshots**: Validates processing of 3+ screenshots as a batch

**Business Value**: Supports bulk course creation from multi-slide presentations.

### 7. TestErrorHandling (2 tests)
Tests error scenarios and graceful degradation.

- **test_llm_provider_failure_handling**: Validates handling of AI service outages
- **test_missing_screenshot_404**: Confirms proper 404 responses for invalid IDs

**Business Value**: Ensures system resilience and clear user-facing error messages.

## Test Strategy

### Mocked Components
External dependencies mocked for reliability and speed:
- **LLM API Calls**: OpenAI/Anthropic vision API responses
- **Text Generation**: Course content generation responses

### Real Components
Critical infrastructure tested with actual services:
- **PostgreSQL**: Database persistence and queries
- **ChromaDB**: RAG vector database operations
- **File System**: Image upload and storage
- **FastAPI**: HTTP endpoints and routing
- **Image Processing**: PIL/Pillow metadata extraction

## Test Data

### Sample Screenshot Analysis
Realistic course structure returned by mocked LLM:
```json
{
  "title": "Introduction to Python Programming",
  "course_structure": {
    "modules": [
      {
        "title": "Python Basics",
        "lessons": ["Variables and Data Types", "Operators", "Control Flow"],
        "estimated_duration_minutes": 90
      },
      {
        "title": "Functions and Modules",
        "lessons": ["Defining Functions", "Parameters", "Return Values"],
        "estimated_duration_minutes": 120
      }
    ],
    "difficulty": "beginner",
    "estimated_duration_hours": 4
  },
  "confidence_score": 0.88
}
```

## Running Tests

### Run All Screenshot Pipeline Tests
```bash
cd /home/bbrelin/course-creator
pytest tests/integration/test_screenshot_to_course_pipeline.py -v
```

### Run Specific Test Class
```bash
pytest tests/integration/test_screenshot_to_course_pipeline.py::TestScreenshotUpload -v
```

### Run Single Test
```bash
pytest tests/integration/test_screenshot_to_course_pipeline.py::TestScreenshotUpload::test_upload_valid_screenshot -v
```

### Run with Coverage
```bash
pytest tests/integration/test_screenshot_to_course_pipeline.py --cov=services/course-generator --cov-report=html
```

## Prerequisites

### Services Required
These services must be running for full integration test coverage:

1. **PostgreSQL** (port 5434): Course and upload metadata storage
2. **Course Generator Service** (port 8004): Screenshot upload and analysis endpoints
3. **User Management Service** (port 8001): Authentication for RBAC
4. **RAG Service** (port 8009): Optional - semantic indexing tests will skip if unavailable

### Environment Variables
```bash
# PostgreSQL
DATABASE_URL=postgresql://test_user:test_password@localhost:5434/course_creator_test

# ChromaDB (embedded)
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# JWT Authentication
JWT_SECRET=test-secret-key-for-testing

# Screenshot Storage
SCREENSHOT_UPLOAD_DIR=/tmp/screenshots
```

### Test User Setup
Instructor account required:
```sql
INSERT INTO users (email, password_hash, role)
VALUES ('test.instructor@coursecreator.com', '<hashed>', 'instructor');
```

## Async Test Support

All tests use `pytest-asyncio` for proper async/await support:

```python
@pytest.mark.asyncio
async def test_upload_valid_screenshot(self, http_client, sample_screenshot_image):
    """Test with async HTTP client"""
    response = await http_client.post(...)
    assert response.status_code == 200
```

## Fixtures

### auth_token
Authenticates as test instructor and returns JWT token.

### http_client
Provides authenticated `httpx.AsyncClient` with HTTPS support.

### sample_screenshot_image
Generates 1920x1080 PNG test image with metadata.

### mock_llm_vision_response
Returns realistic `VisionAnalysisResult` for mocked AI calls.

## Test Execution Flow

### Typical Test Sequence
1. **Authenticate**: Obtain JWT token for instructor
2. **Upload**: POST screenshot to `/screenshot/upload`
3. **Analyze**: Background task processes with mocked LLM
4. **Poll Status**: GET `/screenshot/{id}/status` until complete
5. **Generate Course**: POST `/screenshot/{id}/generate-course`
6. **Verify Database**: Confirm persistence
7. **Verify RAG**: Check semantic indexing (optional)
8. **Cleanup**: Tests are idempotent, no explicit cleanup needed

## Expected Test Results

### All Tests Passing
```
tests/integration/test_screenshot_to_course_pipeline.py::TestScreenshotUpload::test_upload_valid_screenshot PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestScreenshotUpload::test_upload_invalid_format PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestScreenshotUpload::test_upload_oversized_image PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestScreenshotAnalysis::test_analyze_screenshot_with_llm PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestScreenshotAnalysis::test_get_analysis_status PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestCourseGeneration::test_generate_course_from_screenshot PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestCourseGeneration::test_generate_course_without_analysis PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestDatabaseIntegration::test_screenshot_persisted_to_database PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestRAGServiceIntegration::test_course_indexed_in_rag PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestBatchProcessing::test_batch_upload_multiple_screenshots PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestErrorHandling::test_llm_provider_failure_handling PASSED
tests/integration/test_screenshot_to_course_pipeline.py::TestErrorHandling::test_missing_screenshot_404 PASSED

========================= 12 passed in 15.23s =========================
```

## Troubleshooting

### Common Issues

#### Authentication Fails
```
pytest.skip(f"Authentication failed: {response.status_code}")
```
**Solution**: Ensure test instructor account exists and user-management service is running.

#### Connection Refused
```
Cannot connect to user service: Connection refused
```
**Solution**: Start required services:
```bash
docker-compose up -d postgres redis
cd services/user-management && python main.py &
cd services/course-generator && python main.py &
```

#### RAG Tests Skip
```
pytest.skip("RAG service not available")
```
**Solution**: This is expected if RAG service isn't running. Test will skip gracefully.

#### Mock Import Errors
```
ModuleNotFoundError: No module named 'course_generator.infrastructure'
```
**Solution**: Ensure course-generator service is in Python path:
```bash
export PYTHONPATH=/home/bbrelin/course-creator/services/course-generator:$PYTHONPATH
```

## Maintenance

### Updating Mock Data
To reflect changes in AI response format, update `SAMPLE_SCREENSHOT_ANALYSIS` dictionary.

### Adding New Tests
Follow existing patterns:
1. Add to appropriate `Test*` class
2. Use `@pytest.mark.asyncio` decorator
3. Document business context in docstring
4. Mock external APIs, use real database
5. Include cleanup if needed

### Deprecation Notes
- Direct database access deprecated in favor of API calls
- Synchronous tests being migrated to async

## Related Documentation
- [Course Generator Service Documentation](../../services/course-generator/README.md)
- [RAG Service Documentation](../../services/rag-service/README.md)
- [Integration Test Guidelines](../INTEGRATION_TEST_GUIDELINES.md)
- [Screenshot Analysis API](../../docs/SCREENSHOT_ANALYSIS_API.md)

## Contact
For questions about these tests, contact the platform team or refer to `CLAUDE.md` for AI-assisted guidance.
