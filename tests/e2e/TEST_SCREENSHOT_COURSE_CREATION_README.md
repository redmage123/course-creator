# Screenshot-Based Course Creation E2E Tests

**Location**: `/home/bbrelin/course-creator/tests/e2e/test_screenshot_course_creation_e2e.py`
**Created**: 2025-12-13
**Test Count**: 12 tests (10 primary + 2 validation)
**Lines of Code**: 1,236

## Overview

Comprehensive end-to-end test suite validating the complete user journey for screenshot-based course creation, where instructors upload screenshots of existing educational content and AI automatically extracts content to generate complete course structures.

## Business Value

- **Rapid Course Creation**: Enables instructors to create courses from existing materials
- **AI-Powered Extraction**: Validates multi-provider LLM integration for content analysis
- **Quality Assurance**: Ensures generated course structures meet educational standards
- **Instructor Control**: Confirms instructors maintain oversight of AI-generated content

## Test Coverage

### 1. Instructor Authentication & Navigation (2 tests)

**test_01_instructor_login** (Priority: Critical)
- Validates instructor authentication workflow
- Verifies redirect to dashboard after login
- Ensures only authenticated instructors access course creation

**test_02_navigate_to_screenshot_creator** (Priority: Critical)
- Tests navigation to screenshot course creator
- Verifies UI component visibility
- Validates feature discoverability

### 2. Screenshot Upload & Validation (3 tests)

**test_03_upload_single_screenshot** (Priority: Critical)
- Tests single screenshot upload via file input
- Verifies preview display
- Validates upload button enablement

**test_04_upload_multiple_screenshots** (Priority: High)
- Tests batch upload of multiple screenshots
- Verifies all previews render correctly
- Tests preview removal functionality

**test_11_reject_invalid_file_type** (Priority: Medium)
- Validates file type restrictions (images only)
- Verifies error messaging for invalid files
- Documents validation pattern

**test_12_reject_oversized_file** (Priority: Medium)
- Validates file size limits (typically 10MB)
- Verifies error handling for large files
- Documents size restriction pattern

### 3. AI Analysis & Progress Tracking (3 tests)

**test_05_trigger_ai_analysis** (Priority: Critical)
- Tests AI analysis initiation
- Validates LLM provider selection
- Verifies analysis workflow starts

**test_06_monitor_analysis_progress** (Priority: Critical)
- Tests real-time progress tracking
- Monitors progress percentage updates
- Validates progress step descriptions
- Ensures completion detection (120s timeout)

**test_08_review_analysis_metadata** (Priority: High)
- Validates metadata extraction (subject, difficulty, confidence)
- Verifies confidence score >0.5 (reasonable threshold)
- Confirms LLM provider attribution

### 4. Course Structure Preview & Review (2 tests)

**test_07_review_generated_course_structure** (Priority: Critical)
- Validates course structure preview display
- Verifies course title generation
- Confirms module generation (at least 1 module)
- Validates description and learning objectives

### 5. Course Creation & Verification (2 tests)

**test_09_create_course_from_screenshots** (Priority: Critical)
- Tests final course creation from analyzed screenshots
- Verifies success message display
- Validates course creation confirmation

**test_10_verify_course_in_list** (Priority: Critical)
- Validates course persistence in database
- Verifies course appears in course list
- Includes cleanup of test data

## Page Object Models

### Core Page Objects

1. **InstructorLoginPage**
   - Handles instructor authentication
   - Locators: email, password, submit button
   - Methods: `navigate_to_login()`, `login_as_instructor()`

2. **CourseCreationNavigationPage**
   - Manages navigation to course creation features
   - Locators: courses menu, create buttons, screenshot creator
   - Methods: `navigate_to_screenshot_creator()`, `is_screenshot_creator_visible()`

3. **ScreenshotUploadPage**
   - Handles screenshot upload and validation
   - Features: drag-and-drop, file input, provider selection, preview grid
   - Locators: drop zone, file input, preview items, upload button, error banner
   - Methods:
     - `select_llm_provider(provider_name)`
     - `upload_screenshot_via_input(file_path)`
     - `upload_multiple_screenshots(file_paths)`
     - `get_preview_count()`, `remove_preview_at_index(index)`
     - `click_upload_button()`, `has_error()`, `get_error_message()`

4. **AnalysisProgressPage**
   - Monitors AI analysis progress in real-time
   - Locators: analyzing section, progress bar, progress percent, step text
   - Methods:
     - `is_analyzing()`, `get_progress_percent()`, `get_current_step()`
     - `wait_for_analysis_complete(timeout=120)`

5. **CourseStructurePreviewPage**
   - Displays AI-generated course structure for review
   - Locators: preview section, analysis info, course structure, modules, objectives
   - Methods:
     - `get_analysis_metadata()` → dict with content_type, subject, difficulty, confidence
     - `get_course_title()`, `get_course_description()`
     - `get_learning_objectives()`, `get_module_count()`, `get_module_titles()`
     - `get_similar_courses_count()`
     - `click_create_course()`, `click_start_over()`

6. **CourseCreationSuccessPage**
   - Confirms successful course creation
   - Locators: success section, success icon, success message
   - Methods: `is_success_visible()`, `get_success_message()`, `click_create_another()`

### Database Helper

**ScreenshotCourseDatabase**
- Provides database verification for course creation
- Methods:
  - `get_course_by_title(title, org_id)` → course data dict
  - `get_screenshot_analysis(screenshot_id)` → analysis data dict
  - `cleanup_test_course(course_id)` → deletes test data

## Test Data

### Screenshot Fixtures

**test_screenshots** fixture (scope: class)
- Location: `tests/e2e/test_data/screenshots/`
- Creates test screenshot images if not present
- Uses PIL (Pillow) to generate simple test images
- Provides 3 test screenshots (1920x1080 PNG)
- Returns list of absolute file paths

### Database Connection

Uses standard `db_connection` fixture from conftest.py:
- Host: localhost
- Port: 5433 (Docker PostgreSQL)
- Database: course_creator
- User: postgres
- Password: postgres_password

## Configuration

### Pytest Markers

```bash
# Run all screenshot course creation tests
pytest -m screenshot_course_creation

# Run critical priority tests only
pytest -m "screenshot_course_creation and priority_critical"

# Run with specific markers
pytest -m "e2e and screenshot_course_creation"
```

### Environment Variables

- `TEST_BASE_URL`: Base URL for tests (default: https://localhost:3000)
- `HEADLESS`: Run in headless mode (default: true)
- `SELENIUM_REMOTE`: Selenium Grid URL (optional)
- `SCREENSHOT_DIR`: Screenshot output directory
- `VIDEO_DIR`: Video recording directory (if enabled)

### Base URL

All tests use **HTTPS-only**: `https://localhost:3000`

## Running the Tests

### Prerequisites

1. **Services Running**:
   ```bash
   docker-compose up -d
   # Ensure all 16 services are healthy
   ./scripts/app-control.sh status
   ```

2. **Frontend Running**:
   ```bash
   cd frontend-react
   npm run dev
   # Should serve on https://localhost:3000
   ```

3. **Test Screenshots**:
   - Either place test images in `tests/e2e/test_data/screenshots/`
   - Or install PIL/Pillow for automatic generation: `pip install Pillow`

### Run Full Suite

```bash
# All screenshot course creation tests
pytest tests/e2e/test_screenshot_course_creation_e2e.py -v

# With HTML report
pytest tests/e2e/test_screenshot_course_creation_e2e.py -v \
  --html=reports/screenshot_course_creation.html

# Headless mode (default)
HEADLESS=true pytest tests/e2e/test_screenshot_course_creation_e2e.py -v

# Headed mode (visible browser)
HEADLESS=false pytest tests/e2e/test_screenshot_course_creation_e2e.py -v
```

### Run Specific Tests

```bash
# Single test
pytest tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_01_instructor_login -v

# Critical tests only
pytest tests/e2e/test_screenshot_course_creation_e2e.py -m priority_critical -v

# Primary journey (tests 1-10)
pytest tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney -v

# Validation tests only (tests 11-12)
pytest tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotUploadValidation -v
```

### Run with Selenium Grid (Docker)

```bash
# Start Selenium Grid
docker-compose -f docker-compose.selenium.yml up -d

# Run tests against grid
SELENIUM_REMOTE=http://localhost:4444 \
TEST_BASE_URL_DOCKER=https://frontend:3000 \
pytest tests/e2e/test_screenshot_course_creation_e2e.py -v
```

## Expected Results

### Successful Test Run

```
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_01_instructor_login PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_02_navigate_to_screenshot_creator PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_03_upload_single_screenshot PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_04_upload_multiple_screenshots PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_05_trigger_ai_analysis PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_06_monitor_analysis_progress PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_07_review_generated_course_structure PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_08_review_analysis_metadata PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_09_create_course_from_screenshots PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotCourseCreationJourney::test_10_verify_course_in_list PASSED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotUploadValidation::test_11_reject_invalid_file_type SKIPPED
tests/e2e/test_screenshot_course_creation_e2e.py::TestScreenshotUploadValidation::test_12_reject_oversized_file SKIPPED

12 tests: 10 passed, 2 skipped
```

### Common Issues

1. **Analysis Timeout**: If AI analysis takes >120s, tests may skip
   - Solution: Check course-generator service health
   - Solution: Verify LLM provider configuration

2. **Component Not Found**: If ScreenshotCourseCreator not visible
   - Solution: Verify feature is enabled in frontend
   - Solution: Check if component requires feature flag

3. **Test Screenshot Missing**: If test images not available
   - Solution: Install Pillow: `pip install Pillow`
   - Solution: Manually place test PNGs in `tests/e2e/test_data/screenshots/`

4. **Database Verification Fails**: Organization ID extraction issue
   - Solution: Update test to extract actual org_id from authenticated session
   - Solution: Create test organization in fixture

## Integration Points

### Frontend Components

- **ScreenshotCourseCreator.tsx**: Main React component
  - Location: `frontend-react/src/features/courses/components/`
  - Features: drag-drop, provider selection, progress tracking, preview

### Backend Services

- **screenshotService.ts**: Frontend service layer
  - Endpoints: `/api/v1/screenshots/upload`, `/api/v1/screenshots/analyze`
  - Functions: `uploadScreenshot()`, `analyzeScreenshot()`, `pollUntilComplete()`

- **course-generator service**: Backend microservice
  - Port: 8002
  - Handles: screenshot upload, AI analysis, course generation
  - Multi-provider LLM support: OpenAI, Anthropic, Deepseek, Qwen, Ollama, Gemini, Mistral

### Database Tables

- **courses**: Created course records
- **screenshot_analysis**: Analysis results and metadata
- **modules**: Generated course modules
- **lessons**: Generated lessons within modules

## Maintenance

### Updating Tests

When frontend changes occur:

1. **Component Refactoring**: Update Page Object locators
2. **New Features**: Add new test methods
3. **API Changes**: Update service call expectations
4. **UI Changes**: Update CSS selector patterns

### Adding New Tests

Follow the established pattern:

```python
@pytest.mark.priority_high
def test_13_new_screenshot_feature(self, test_screenshots):
    """
    Test: Description of new feature

    BUSINESS REQUIREMENT:
    Explain the business value

    Steps:
    1. Step one
    2. Step two
    3. Step three
    """
    # Login and setup
    login_page = InstructorLoginPage(self.driver, self.config)
    login_page.login_as_instructor()

    # Test implementation
    # ...

    print("✓ New feature tested successfully")
```

## Documentation

### Architecture Documentation

- **CLAUDE.md**: Project-wide testing requirements
- **E2E_PHASE_4_PLAN.md**: E2E test expansion plan
- **selenium_base.py**: Base classes and utilities

### Related Tests

- `test_slide_generation_complete.py`: Slide generation E2E tests
- `test_quiz_generation_from_content.py`: Quiz generation E2E tests
- `test_rag_enhanced_generation.py`: RAG-enhanced content tests

## Compliance

### Test Standards

- **TDD Methodology**: Follow Red-Green-Refactor cycle
- **Page Object Model**: All UI interactions through page objects
- **Multi-layer Verification**: UI + Database validation
- **HTTPS-Only**: All requests use secure protocol
- **Comprehensive Documentation**: Business context in all test docstrings

### Code Quality

- **Python Syntax**: Valid Python 3.12+
- **Type Hints**: Used where applicable
- **Error Handling**: Try/except with appropriate exceptions
- **Clean Code**: PEP 8 compliant, clear variable names
- **Comments**: Explain WHY, not WHAT

## Future Enhancements

### Planned Tests

1. **Cross-browser Testing**: Firefox, Safari, Edge compatibility
2. **Mobile Responsive**: Test on mobile viewport sizes
3. **Accessibility**: WCAG 2.1 AA compliance validation
4. **Performance**: Analysis completion time benchmarks
5. **Error Recovery**: Network failure and retry handling
6. **Batch Processing**: Large batch upload (10+ screenshots)
7. **Edit Generated Structure**: Modify course before creation
8. **Template Selection**: Choose from course templates

### Feature Improvements

1. **Screenshot Annotation**: Highlight regions of interest
2. **Multi-language Support**: Non-English content extraction
3. **Quality Metrics**: Automated quality scoring
4. **Comparison Mode**: Compare multiple screenshot analyses
5. **Export Preview**: Download course structure before creation

## Contact & Support

For questions or issues with these tests:

1. Review test output logs for detailed error messages
2. Check `reports/screenshots/` for failure screenshots
3. Verify all services are healthy: `./scripts/app-control.sh status`
4. Consult memory system: `python3 .claude/query_memory.py search "screenshot"`

---

**Last Updated**: 2025-12-13
**Test Suite Version**: 1.0.0
**Maintainer**: Claude Code (AI-assisted development)
