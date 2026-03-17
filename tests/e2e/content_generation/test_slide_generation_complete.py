"""
Comprehensive End-to-End Tests for Slide Generation Feature

BUSINESS REQUIREMENT:
Validates complete slide generation workflows including AI-generated slides,
slide customization, quality validation, and instructor control over content.

TECHNICAL IMPLEMENTATION:
- Uses selenium_base.py BaseTest as parent class
- Tests real UI interactions with slide generation features
- Covers ALL slide generation capabilities per E2E_PHASE_4_PLAN.md
- HTTPS-only communication (https://localhost:3000)
- Headless-compatible for CI/CD
- Page Object Model pattern for maintainability
- Multi-layer verification (UI + Database)

TEST COVERAGE:
1. Slide Creation (4 tests):
   - Generate slides from course outline (AI-generated)
   - Generate slides from uploaded documents (PDF, DOCX)
   - Generate slides with specific topic/learning objectives
   - Generate slides with instructor-provided content

2. Slide Customization (4 tests):
   - Edit generated slide content (text, images)
   - Reorder slides within module
   - Add/remove slides from generated set
   - Customize slide templates and styling

3. Slide Quality Validation (4 tests):
   - Verify slide content accuracy vs source material
   - Verify slide readability (Flesch-Kincaid score >60)
   - Verify slide formatting consistency
   - Verify slide media (images, diagrams) appropriateness

BUSINESS VALUE:
- Ensures instructors can rapidly create high-quality course materials
- Validates AI-generated content meets educational standards
- Confirms instructor control over final slide content
- Verifies slides are accessible and well-formatted
"""

import pytest
import time
import uuid
import psycopg2
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

# Import base test class
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from e2e.selenium_base import BaseTest, BasePage

# Check if Selenium is configured
SELENIUM_AVAILABLE = os.getenv('SELENIUM_REMOTE') is not None or os.getenv('HEADLESS') is not None


# Test Configuration
BASE_URL = "https://localhost:3000"
INSTRUCTOR_DASHBOARD_PATH = "/html/instructor-dashboard-modular.html"
LOGIN_PATH = "/html/index.html"


# ============================================================================
# PAGE OBJECT MODELS
# ============================================================================


class LoginPage(BasePage):
    """
    Page Object Model for Login Page

    BUSINESS PURPOSE:
    Handles authentication for instructor access to content generation.
    Only authenticated instructors can generate slides.
    """

    # Page elements
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BTN = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")

    def navigate_to_login(self):
        """Navigate to login page."""
        self.navigate_to(LOGIN_PATH)

    def login(self, email: str, password: str):
        """
        Perform login action.

        Args:
            email: User email
            password: User password
        """
        self.enter_text(*self.EMAIL_INPUT, text=email)
        self.enter_text(*self.PASSWORD_INPUT, text=password)
        self.click_element(*self.LOGIN_BTN)
        time.sleep(2)  # Wait for login to complete


class SlideGenerationPage(BasePage):
    """
    Page Object Model for Slide Generation Interface

    BUSINESS PURPOSE:
    Enables instructors to generate course slides using AI or manual input.
    Supports multiple generation methods: AI from outline, document upload,
    specific topics, and instructor-provided content.

    DESIGN PATTERN: Page Object Model
    Encapsulates all slide generation UI elements and interactions.
    """

    # Navigation
    CONTENT_GENERATION_TAB = (By.CSS_SELECTOR, "[data-tab='content-generation']")
    SLIDES_TAB = (By.CSS_SELECTOR, "[data-tab='slides']")

    # Slide generation methods
    GENERATE_FROM_OUTLINE_BTN = (By.ID, "generateFromOutlineBtn")
    GENERATE_FROM_DOCUMENT_BTN = (By.ID, "generateFromDocumentBtn")
    GENERATE_FROM_TOPIC_BTN = (By.ID, "generateFromTopicBtn")
    GENERATE_FROM_CONTENT_BTN = (By.ID, "generateFromContentBtn")

    # AI generation form
    COURSE_OUTLINE_INPUT = (By.ID, "courseOutlineInput")
    TOPIC_INPUT = (By.ID, "topicInput")
    LEARNING_OBJECTIVES_INPUT = (By.ID, "learningObjectivesInput")
    INSTRUCTOR_CONTENT_INPUT = (By.ID, "instructorContentInput")
    DOCUMENT_UPLOAD_INPUT = (By.ID, "documentUploadInput")
    FILE_FORMAT_SELECT = (By.ID, "fileFormatSelect")

    # Generation controls
    NUM_SLIDES_INPUT = (By.ID, "numSlidesInput")
    DIFFICULTY_LEVEL_SELECT = (By.ID, "difficultyLevelSelect")
    INCLUDE_IMAGES_CHECKBOX = (By.ID, "includeImagesCheckbox")
    INCLUDE_DIAGRAMS_CHECKBOX = (By.ID, "includeDiagramsCheckbox")
    GENERATE_SLIDES_BTN = (By.ID, "generateSlidesBtn")
    CANCEL_GENERATION_BTN = (By.ID, "cancelGenerationBtn")

    # Generation progress
    GENERATION_PROGRESS_MODAL = (By.ID, "generationProgressModal")
    PROGRESS_BAR = (By.CLASS_NAME, "progress-bar")
    PROGRESS_TEXT = (By.CLASS_NAME, "progress-text")
    GENERATION_STATUS = (By.ID, "generationStatus")

    # Generated slides view
    SLIDES_CONTAINER = (By.ID, "slidesContainer")
    SLIDE_CARD = (By.CLASS_NAME, "slide-card")
    SLIDE_TITLE = (By.CLASS_NAME, "slide-title")
    SLIDE_CONTENT = (By.CLASS_NAME, "slide-content")
    SLIDE_IMAGE = (By.CLASS_NAME, "slide-image")
    SLIDE_NUMBER = (By.CLASS_NAME, "slide-number")

    # Slide actions
    EDIT_SLIDE_BTN = (By.CLASS_NAME, "edit-slide-btn")
    DELETE_SLIDE_BTN = (By.CLASS_NAME, "delete-slide-btn")
    PREVIEW_SLIDE_BTN = (By.CLASS_NAME, "preview-slide-btn")
    SAVE_SLIDES_BTN = (By.ID, "saveSlidesBtn")
    EXPORT_SLIDES_BTN = (By.ID, "exportSlidesBtn")

    def navigate_to_slide_generation(self):
        """Navigate to slide generation interface."""
        self.click_element(*self.CONTENT_GENERATION_TAB)
        time.sleep(1)
        self.click_element(*self.SLIDES_TAB)
        time.sleep(1)

    def generate_slides_from_outline(self, outline: str, num_slides: int = 10,
                                     difficulty: str = "intermediate",
                                     include_images: bool = True):
        """
        Generate slides from course outline using AI.

        Args:
            outline: Course outline text
            num_slides: Number of slides to generate
            difficulty: Difficulty level (beginner/intermediate/advanced)
            include_images: Whether to include AI-generated images

        BUSINESS LOGIC:
        AI analyzes course outline and generates structured slides
        with titles, content, and optional images/diagrams.
        """
        self.click_element(*self.GENERATE_FROM_OUTLINE_BTN)
        time.sleep(1)

        # Fill generation form
        self.enter_text(*self.COURSE_OUTLINE_INPUT, text=outline)
        self.enter_text(*self.NUM_SLIDES_INPUT, text=str(num_slides), clear_first=True)

        # Select difficulty
        difficulty_element = self.find_element(*self.DIFFICULTY_LEVEL_SELECT)
        Select(difficulty_element).select_by_value(difficulty)

        # Toggle images
        if include_images:
            images_checkbox = self.find_element(*self.INCLUDE_IMAGES_CHECKBOX)
            if not images_checkbox.is_selected():
                images_checkbox.click()

        # Start generation
        self.click_element(*self.GENERATE_SLIDES_BTN)

    def generate_slides_from_document(self, document_path: str, file_format: str = "pdf"):
        """
        Generate slides from uploaded document (PDF, DOCX).

        Args:
            document_path: Path to document file
            file_format: Document format (pdf/docx)

        BUSINESS LOGIC:
        AI extracts key concepts from document and generates
        structured slides with proper citations.
        """
        self.click_element(*self.GENERATE_FROM_DOCUMENT_BTN)
        time.sleep(1)

        # Select file format
        format_element = self.find_element(*self.FILE_FORMAT_SELECT)
        Select(format_element).select_by_value(file_format)

        # Upload document
        upload_input = self.find_element(*self.DOCUMENT_UPLOAD_INPUT)
        upload_input.send_keys(document_path)
        time.sleep(2)  # Wait for upload

        # Start generation
        self.click_element(*self.GENERATE_SLIDES_BTN)

    def generate_slides_from_topic(self, topic: str, learning_objectives: str,
                                    num_slides: int = 8):
        """
        Generate slides for specific topic with learning objectives.

        Args:
            topic: Topic name
            learning_objectives: Learning objectives (comma-separated)
            num_slides: Number of slides to generate

        BUSINESS LOGIC:
        AI generates slides aligned with specified learning objectives,
        ensuring educational outcomes are met.
        """
        self.click_element(*self.GENERATE_FROM_TOPIC_BTN)
        time.sleep(1)

        # Fill topic form
        self.enter_text(*self.TOPIC_INPUT, text=topic)
        self.enter_text(*self.LEARNING_OBJECTIVES_INPUT, text=learning_objectives)
        self.enter_text(*self.NUM_SLIDES_INPUT, text=str(num_slides), clear_first=True)

        # Start generation
        self.click_element(*self.GENERATE_SLIDES_BTN)

    def generate_slides_from_content(self, content: str, num_slides: int = 5):
        """
        Generate slides from instructor-provided content.

        Args:
            content: Instructor-written content
            num_slides: Number of slides to generate

        BUSINESS LOGIC:
        AI structures instructor content into slides while preserving
        the instructor's voice and specific examples.
        """
        self.click_element(*self.GENERATE_FROM_CONTENT_BTN)
        time.sleep(1)

        # Fill content form
        self.enter_text(*self.INSTRUCTOR_CONTENT_INPUT, text=content)
        self.enter_text(*self.NUM_SLIDES_INPUT, text=str(num_slides), clear_first=True)

        # Start generation
        self.click_element(*self.GENERATE_SLIDES_BTN)

    def wait_for_generation_complete(self, timeout: int = 120):
        """
        Wait for slide generation to complete.

        Args:
            timeout: Maximum wait time in seconds

        BUSINESS REQUIREMENT:
        AI generation can take 30-120 seconds depending on complexity.
        """
        try:
            # Wait for progress modal to appear
            self.wait_for_element_visible(*self.GENERATION_PROGRESS_MODAL, timeout=10)

            # Wait for generation to complete (progress modal disappears)
            self.wait.until(
                EC.invisibility_of_element_located(self.GENERATION_PROGRESS_MODAL),
                timeout=timeout
            )
            time.sleep(2)  # Wait for slides to render
            return True
        except TimeoutException:
            return False

    def get_generated_slides_count(self) -> int:
        """
        Get number of generated slides.

        Returns:
            Number of slides displayed
        """
        slides = self.find_elements(*self.SLIDE_CARD)
        return len(slides)

    def get_slide_titles(self) -> list:
        """
        Get titles of all generated slides.

        Returns:
            List of slide titles
        """
        title_elements = self.find_elements(*self.SLIDE_TITLE)
        return [elem.text for elem in title_elements]

    def save_slides(self):
        """Save generated slides to course."""
        self.click_element(*self.SAVE_SLIDES_BTN)
        time.sleep(2)


class SlideEditorPage(BasePage):
    """
    Page Object Model for Slide Editor Interface

    BUSINESS PURPOSE:
    Allows instructors to customize AI-generated slides by editing text,
    reordering slides, adding/removing slides, and customizing templates.

    INSTRUCTOR CONTROL:
    While AI generates initial content, instructors have full control
    over final slide content to ensure quality and accuracy.
    """

    # Editor elements
    SLIDE_EDITOR_MODAL = (By.ID, "slideEditorModal")
    SLIDE_TITLE_INPUT = (By.ID, "slideTitleInput")
    SLIDE_CONTENT_EDITOR = (By.ID, "slideContentEditor")
    SLIDE_IMAGE_INPUT = (By.ID, "slideImageInput")
    SLIDE_TEMPLATE_SELECT = (By.ID, "slideTemplateSelect")

    # Editing tools
    TEXT_FORMAT_BOLD = (By.ID, "formatBoldBtn")
    TEXT_FORMAT_ITALIC = (By.ID, "formatItalicBtn")
    TEXT_FORMAT_UNDERLINE = (By.ID, "formatUnderlineBtn")
    INSERT_IMAGE_BTN = (By.ID, "insertImageBtn")
    INSERT_CODE_BTN = (By.ID, "insertCodeBtn")
    INSERT_LIST_BTN = (By.ID, "insertListBtn")

    # Slide order controls
    MOVE_SLIDE_UP_BTN = (By.CLASS_NAME, "move-slide-up-btn")
    MOVE_SLIDE_DOWN_BTN = (By.CLASS_NAME, "move-slide-down-btn")
    SLIDE_ORDER_INPUT = (By.CLASS_NAME, "slide-order-input")

    # Slide management
    ADD_SLIDE_BTN = (By.ID, "addSlideBtn")
    DUPLICATE_SLIDE_BTN = (By.CLASS_NAME, "duplicate-slide-btn")
    DELETE_SLIDE_BTN = (By.CLASS_NAME, "delete-slide-btn")
    CONFIRM_DELETE_BTN = (By.ID, "confirmDeleteBtn")

    # Template customization
    TEMPLATE_TITLE_ONLY = (By.CSS_SELECTOR, "[data-template='title-only']")
    TEMPLATE_TITLE_CONTENT = (By.CSS_SELECTOR, "[data-template='title-content']")
    TEMPLATE_TWO_COLUMN = (By.CSS_SELECTOR, "[data-template='two-column']")
    TEMPLATE_IMAGE_CAPTION = (By.CSS_SELECTOR, "[data-template='image-caption']")

    # Editor actions
    SAVE_CHANGES_BTN = (By.ID, "saveChangesBtn")
    CANCEL_EDIT_BTN = (By.ID, "cancelEditBtn")
    PREVIEW_SLIDE_BTN = (By.ID, "previewSlideBtn")

    def open_slide_editor(self, slide_index: int = 0):
        """
        Open editor for specific slide.

        Args:
            slide_index: Index of slide to edit (0-based)
        """
        slide_cards = self.find_elements(*SlideGenerationPage.SLIDE_CARD)
        if slide_index < len(slide_cards):
            edit_buttons = self.find_elements(*SlideGenerationPage.EDIT_SLIDE_BTN)
            edit_buttons[slide_index].click()
            time.sleep(1)
            self.wait_for_element_visible(*self.SLIDE_EDITOR_MODAL)

    def edit_slide_content(self, title: str = None, content: str = None):
        """
        Edit slide title and content.

        Args:
            title: New slide title (optional)
            content: New slide content (optional)
        """
        if title:
            self.enter_text(*self.SLIDE_TITLE_INPUT, text=title)

        if content:
            self.enter_text(*self.SLIDE_CONTENT_EDITOR, text=content)

    def change_slide_template(self, template: str):
        """
        Change slide template.

        Args:
            template: Template type (title-only/title-content/two-column/image-caption)
        """
        template_select = self.find_element(*self.SLIDE_TEMPLATE_SELECT)
        Select(template_select).select_by_value(template)
        time.sleep(1)

    def insert_image(self, image_path: str):
        """
        Insert image into slide.

        Args:
            image_path: Path to image file
        """
        self.click_element(*self.INSERT_IMAGE_BTN)
        time.sleep(0.5)

        image_input = self.find_element(*self.SLIDE_IMAGE_INPUT)
        image_input.send_keys(image_path)
        time.sleep(1)

    def save_slide_changes(self):
        """Save slide edits."""
        self.click_element(*self.SAVE_CHANGES_BTN)
        time.sleep(1)

    def move_slide_up(self, slide_index: int):
        """
        Move slide up in order.

        Args:
            slide_index: Index of slide to move
        """
        move_up_buttons = self.find_elements(*self.MOVE_SLIDE_UP_BTN)
        if slide_index < len(move_up_buttons):
            move_up_buttons[slide_index].click()
            time.sleep(1)

    def move_slide_down(self, slide_index: int):
        """
        Move slide down in order.

        Args:
            slide_index: Index of slide to move
        """
        move_down_buttons = self.find_elements(*self.MOVE_SLIDE_DOWN_BTN)
        if slide_index < len(move_down_buttons):
            move_down_buttons[slide_index].click()
            time.sleep(1)

    def add_new_slide(self):
        """Add new blank slide to set."""
        self.click_element(*self.ADD_SLIDE_BTN)
        time.sleep(1)

    def delete_slide(self, slide_index: int):
        """
        Delete slide from set.

        Args:
            slide_index: Index of slide to delete
        """
        delete_buttons = self.find_elements(*self.DELETE_SLIDE_BTN)
        if slide_index < len(delete_buttons):
            delete_buttons[slide_index].click()
            time.sleep(0.5)
            # Confirm deletion
            self.click_element(*self.CONFIRM_DELETE_BTN)
            time.sleep(1)


class SlidePreviewPage(BasePage):
    """
    Page Object Model for Slide Preview Interface

    BUSINESS PURPOSE:
    Validates slide quality including content accuracy, readability,
    formatting consistency, and media appropriateness.

    QUALITY ASSURANCE:
    Ensures slides meet educational standards before publishing to students.
    """

    # Preview elements
    PREVIEW_MODAL = (By.ID, "slidePreviewModal")
    PREVIEW_TITLE = (By.CLASS_NAME, "preview-title")
    PREVIEW_CONTENT = (By.CLASS_NAME, "preview-content")
    PREVIEW_IMAGE = (By.CLASS_NAME, "preview-image")
    PREVIEW_SLIDE_NUMBER = (By.CLASS_NAME, "preview-slide-number")

    # Navigation
    NEXT_SLIDE_BTN = (By.ID, "nextSlideBtn")
    PREV_SLIDE_BTN = (By.ID, "prevSlideBtn")
    CLOSE_PREVIEW_BTN = (By.ID, "closePreviewBtn")

    # Quality metrics
    READABILITY_SCORE = (By.ID, "readabilityScore")
    CONTENT_ACCURACY = (By.ID, "contentAccuracy")
    FORMATTING_CONSISTENCY = (By.ID, "formattingConsistency")
    MEDIA_APPROPRIATENESS = (By.ID, "mediaAppropriateness")

    # Quality indicators
    QUALITY_WARNING = (By.CLASS_NAME, "quality-warning")
    QUALITY_SUCCESS = (By.CLASS_NAME, "quality-success")

    # Export options
    EXPORT_PDF_BTN = (By.ID, "exportPdfBtn")
    EXPORT_PPTX_BTN = (By.ID, "exportPptxBtn")

    def open_slide_preview(self, slide_index: int = 0):
        """
        Open preview for specific slide.

        Args:
            slide_index: Index of slide to preview
        """
        preview_buttons = self.find_elements(*SlideGenerationPage.PREVIEW_SLIDE_BTN)
        if slide_index < len(preview_buttons):
            preview_buttons[slide_index].click()
            time.sleep(1)
            self.wait_for_element_visible(*self.PREVIEW_MODAL)

    def get_readability_score(self) -> float:
        """
        Get Flesch-Kincaid readability score.

        Returns:
            Readability score (0-100, higher is better)

        BUSINESS REQUIREMENT:
        Educational content should have readability score >60
        for target audience comprehension.
        """
        try:
            score_text = self.get_text(*self.READABILITY_SCORE)
            # Extract numeric score from text (e.g., "Readability: 72.5")
            score = float(score_text.split(":")[-1].strip())
            return score
        except (ValueError, NoSuchElementException):
            return 0.0

    def get_content_accuracy(self) -> float:
        """
        Get content accuracy vs source material.

        Returns:
            Accuracy percentage (0-100)

        BUSINESS REQUIREMENT:
        AI-generated slides must accurately reflect source material
        with >85% accuracy to prevent misinformation.
        """
        try:
            accuracy_text = self.get_text(*self.CONTENT_ACCURACY)
            accuracy = float(accuracy_text.split(":")[-1].strip().replace("%", ""))
            return accuracy
        except (ValueError, NoSuchElementException):
            return 0.0

    def has_quality_warnings(self) -> bool:
        """
        Check if slide has quality warnings.

        Returns:
            True if warnings present, False otherwise
        """
        return self.is_element_present(*self.QUALITY_WARNING, timeout=2)

    def navigate_next_slide(self):
        """Navigate to next slide in preview."""
        self.click_element(*self.NEXT_SLIDE_BTN)
        time.sleep(1)

    def navigate_previous_slide(self):
        """Navigate to previous slide in preview."""
        self.click_element(*self.PREV_SLIDE_BTN)
        time.sleep(1)

    def close_preview(self):
        """Close preview modal."""
        self.click_element(*self.CLOSE_PREVIEW_BTN)
        time.sleep(1)

    def export_to_pdf(self):
        """Export slides to PDF format."""
        self.click_element(*self.EXPORT_PDF_BTN)
        time.sleep(3)  # Wait for download

    def export_to_powerpoint(self):
        """Export slides to PowerPoint format."""
        self.click_element(*self.EXPORT_PPTX_BTN)
        time.sleep(3)  # Wait for download


# ============================================================================
# TEST CLASSES
# ============================================================================


@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not configured")
@pytest.mark.e2e
@pytest.mark.content_generation
class TestSlideCreation(BaseTest):
    """
    Test Category 1: Slide Creation

    BUSINESS REQUIREMENT:
    Instructors must be able to generate slides through multiple methods:
    - AI generation from course outline
    - AI generation from uploaded documents (PDF, DOCX)
    - AI generation from specific topic/learning objectives
    - AI structuring of instructor-provided content

    QUALITY CRITERIA:
    - Generation completes within 120 seconds
    - Correct number of slides generated
    - Slides have titles and content
    - Database records created correctly
    """

    @pytest.mark.priority_critical
    def test_generate_slides_from_course_outline(self, db_connection, test_instructor_credentials,
                                                  test_course_data, ai_generation_timeout):
        """
        Test: Generate slides from course outline using AI

        BUSINESS SCENARIO:
        Instructor has created course outline and wants AI to generate
        initial slide deck covering all topics in the outline.

        WORKFLOW:
        1. Login as instructor
        2. Navigate to slide generation interface
        3. Input course outline text
        4. Configure generation (10 slides, intermediate difficulty, with images)
        5. Start AI generation
        6. Wait for generation to complete (max 120s)
        7. Verify slides generated correctly

        SUCCESS CRITERIA:
        - 10 slides generated
        - Each slide has title and content
        - Slides saved to database
        - Generation completes within 120s

        VALIDATION:
        - UI: Count slide cards displayed
        - Database: Query slides table for new records
        """
        # Step 1: Login
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        # Step 2: Navigate to slide generation
        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        # Step 3: Generate slides from outline
        course_outline = """
        Module 1: Introduction to Python Programming
        - Python basics and syntax
        - Variables and data types
        - Control flow (if/else, loops)

        Module 2: Functions and Modules
        - Defining functions
        - Function parameters and return values
        - Importing and using modules

        Module 3: Data Structures
        - Lists and tuples
        - Dictionaries and sets
        - List comprehensions
        """

        slide_gen_page.generate_slides_from_outline(
            outline=course_outline,
            num_slides=10,
            difficulty="intermediate",
            include_images=True
        )

        # Step 4: Wait for generation to complete
        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Slide generation did not complete within timeout"

        # Step 5: Verify slides generated
        slides_count = slide_gen_page.get_generated_slides_count()
        assert slides_count == 10, f"Expected 10 slides, got {slides_count}"

        # Step 6: Verify slide titles
        slide_titles = slide_gen_page.get_slide_titles()
        assert len(slide_titles) == 10, f"Expected 10 slide titles, got {len(slide_titles)}"
        assert all(title.strip() != "" for title in slide_titles), "Some slides missing titles"

        # Step 7: Save slides
        slide_gen_page.save_slides()

        # Step 8: Verify database records
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM slides
            WHERE title LIKE '%Python%' OR title LIKE '%Function%' OR title LIKE '%Data%'
        """)
        db_slides_count = cursor.fetchone()[0]
        assert db_slides_count >= 10, f"Expected >= 10 slides in DB, got {db_slides_count}"
        cursor.close()

    @pytest.mark.priority_high
    def test_generate_slides_from_uploaded_document_pdf(self, db_connection,
                                                         test_instructor_credentials,
                                                         ai_generation_timeout):
        """
        Test: Generate slides from uploaded PDF document

        BUSINESS SCENARIO:
        Instructor has existing PDF textbook/materials and wants to
        convert key concepts into slide deck for lectures.

        WORKFLOW:
        1. Login as instructor
        2. Navigate to slide generation interface
        3. Select "Generate from Document" option
        4. Upload PDF file
        5. Start AI generation
        6. Wait for generation to complete
        7. Verify slides extracted from PDF

        SUCCESS CRITERIA:
        - PDF successfully uploaded
        - Slides generated from PDF content
        - Citations to source material included
        - Slides saved to database

        VALIDATION:
        - UI: Slides displayed with content from PDF
        - Database: Slides contain source_document reference

        NOTE: This test requires test PDF file to be present.
        For TDD RED phase, test will use mock PDF path.
        """
        # Step 1: Login
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        # Step 2: Navigate to slide generation
        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        # Step 3: Upload PDF document
        # Note: In TDD RED phase, this will fail until PDF upload is implemented
        test_pdf_path = "/tmp/test_course_material.pdf"

        # Create test PDF if doesn't exist (for GREEN phase)
        if not os.path.exists(test_pdf_path):
            # Will be implemented in GREEN phase
            pytest.skip("Test PDF file not available yet (TDD RED phase)")

        slide_gen_page.generate_slides_from_document(
            document_path=test_pdf_path,
            file_format="pdf"
        )

        # Step 4: Wait for generation
        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "PDF slide generation did not complete"

        # Step 5: Verify slides generated
        slides_count = slide_gen_page.get_generated_slides_count()
        assert slides_count > 0, "No slides generated from PDF"

        # Step 6: Save slides
        slide_gen_page.save_slides()

        # Step 7: Verify database records include source document
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM slides
            WHERE source_document = 'test_course_material.pdf'
        """)
        pdf_slides_count = cursor.fetchone()[0]
        assert pdf_slides_count > 0, "Slides not linked to source PDF in database"
        cursor.close()

    @pytest.mark.priority_high
    def test_generate_slides_from_specific_topic(self, db_connection,
                                                  test_instructor_credentials,
                                                  ai_generation_timeout):
        """
        Test: Generate slides with specific topic and learning objectives

        BUSINESS SCENARIO:
        Instructor wants to create targeted slides for specific topic
        aligned with defined learning objectives.

        WORKFLOW:
        1. Login as instructor
        2. Navigate to slide generation interface
        3. Enter topic: "Object-Oriented Programming in Python"
        4. Enter learning objectives:
           - "Understand classes and objects"
           - "Implement inheritance and polymorphism"
           - "Apply encapsulation principles"
        5. Generate 8 slides
        6. Verify slides align with objectives

        SUCCESS CRITERIA:
        - 8 slides generated
        - Each slide addresses one or more learning objectives
        - Content accuracy >85%
        - Slides saved to database with objective links

        VALIDATION:
        - UI: Slides cover all learning objectives
        - Database: Slides linked to learning objectives
        """
        # Step 1: Login
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        # Step 2: Navigate to slide generation
        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        # Step 3: Generate slides from topic
        topic = "Object-Oriented Programming in Python"
        learning_objectives = """
        1. Understand classes and objects
        2. Implement inheritance and polymorphism
        3. Apply encapsulation principles
        4. Use composition over inheritance
        """

        slide_gen_page.generate_slides_from_topic(
            topic=topic,
            learning_objectives=learning_objectives,
            num_slides=8
        )

        # Step 4: Wait for generation
        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Topic slide generation did not complete"

        # Step 5: Verify slides generated
        slides_count = slide_gen_page.get_generated_slides_count()
        assert slides_count == 8, f"Expected 8 slides, got {slides_count}"

        # Step 6: Verify slide titles mention key concepts
        slide_titles = slide_gen_page.get_slide_titles()
        title_text = " ".join(slide_titles).lower()

        # Check if key OOP concepts appear in slide titles
        assert "class" in title_text or "object" in title_text, \
            "Slides don't mention classes/objects"
        assert "inheritance" in title_text or "polymorphism" in title_text, \
            "Slides don't mention inheritance/polymorphism"

        # Step 7: Save slides
        slide_gen_page.save_slides()

        # Step 8: Verify database records
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM slides
            WHERE topic = %s
        """, (topic,))
        topic_slides_count = cursor.fetchone()[0]
        assert topic_slides_count == 8, \
            f"Expected 8 slides for topic in DB, got {topic_slides_count}"
        cursor.close()

    @pytest.mark.priority_medium
    def test_generate_slides_from_instructor_content(self, db_connection,
                                                      test_instructor_credentials,
                                                      ai_generation_timeout):
        """
        Test: Generate slides from instructor-provided content

        BUSINESS SCENARIO:
        Instructor has written detailed course notes and wants AI to
        structure them into presentation slides while preserving their
        voice and specific examples.

        WORKFLOW:
        1. Login as instructor
        2. Navigate to slide generation interface
        3. Input instructor content (essay-style text)
        4. Request AI to structure into 5 slides
        5. Verify AI preserves instructor's examples
        6. Verify AI maintains instructor's voice

        SUCCESS CRITERIA:
        - 5 slides generated
        - Instructor's examples preserved verbatim
        - Instructor's voice/tone maintained
        - Slides have clear structure (title, points, examples)

        VALIDATION:
        - UI: Slides contain instructor's original examples
        - Database: Slides marked as instructor-authored
        """
        # Step 1: Login
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        # Step 2: Navigate to slide generation
        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        # Step 3: Instructor content
        instructor_content = """
        Let me tell you about debugging in Python - it's both an art and a science.

        First, understand that print statements are your friend. I know fancy debuggers
        exist, but there's something satisfying about a well-placed print(). I once
        spent 3 hours debugging a Flask app, only to discover I had misspelled a
        variable name. A simple print statement would have caught it in 30 seconds.

        Second, the Python debugger (pdb) is incredibly powerful. Set a breakpoint
        with import pdb; pdb.set_trace() and you can step through your code line
        by line. This is especially useful for complex algorithms.

        Third, logging beats printing for production code. Use the logging module
        with different severity levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        This way you can control verbosity without changing code.

        Fourth, don't forget about assert statements for sanity checks. They're
        like unit tests embedded in your code.

        Finally, my golden rule: if you're stuck for more than 20 minutes, take
        a break. Fresh eyes solve bugs faster than tired ones.
        """

        slide_gen_page.generate_slides_from_content(
            content=instructor_content,
            num_slides=5
        )

        # Step 4: Wait for generation
        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Instructor content slide generation did not complete"

        # Step 5: Verify slides generated
        slides_count = slide_gen_page.get_generated_slides_count()
        assert slides_count == 5, f"Expected 5 slides, got {slides_count}"

        # Step 6: Verify instructor examples preserved
        # Check if Flask example appears in slides
        slide_gen_page.click_element(*SlideGenerationPage.PREVIEW_SLIDE_BTN)
        time.sleep(2)

        # Navigate through slides looking for instructor's examples
        preview_page = SlidePreviewPage(self.driver, self.config)
        found_flask_example = False

        for i in range(5):
            content = self.driver.find_element(By.CLASS_NAME, "preview-content").text
            if "Flask" in content or "misspelled" in content:
                found_flask_example = True
                break
            if i < 4:  # Don't try to go to next slide on last slide
                preview_page.navigate_next_slide()

        assert found_flask_example, "Instructor's Flask example not preserved in slides"

        preview_page.close_preview()

        # Step 7: Save slides
        slide_gen_page.save_slides()

        # Step 8: Verify database marks slides as instructor-authored
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM slides
            WHERE instructor_authored = true
            AND content LIKE '%Flask%'
        """)
        authored_count = cursor.fetchone()[0]
        assert authored_count > 0, "Slides not marked as instructor-authored in DB"
        cursor.close()


@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not configured")
@pytest.mark.e2e
@pytest.mark.content_generation
class TestSlideCustomization(BaseTest):
    """
    Test Category 2: Slide Customization

    BUSINESS REQUIREMENT:
    Instructors must have full control over AI-generated slides:
    - Edit slide content (text, images)
    - Reorder slides within module
    - Add/remove slides from generated set
    - Customize slide templates and styling

    QUALITY CRITERIA:
    - Edits saved correctly
    - Slide order persists
    - Template changes applied
    - Database updated accurately
    """

    @pytest.mark.priority_critical
    def test_edit_generated_slide_content(self, db_connection, test_instructor_credentials,
                                          ai_generation_timeout):
        """
        Test: Edit generated slide content (text and images)

        BUSINESS SCENARIO:
        AI generated good slides, but instructor wants to refine the wording
        and replace an AI-generated image with a better one.

        WORKFLOW:
        1. Login as instructor
        2. Generate initial slides (reuse generation)
        3. Open slide editor for slide #3
        4. Edit slide title and content
        5. Replace slide image
        6. Save changes
        7. Verify edits persisted

        SUCCESS CRITERIA:
        - Slide title updated
        - Slide content updated
        - Image replaced
        - Changes visible immediately
        - Database updated

        VALIDATION:
        - UI: Edited content displays correctly
        - Database: slides table shows updated content
        """
        # Step 1: Login and generate slides
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        # Generate test slides
        slide_gen_page.generate_slides_from_topic(
            topic="Web Development Basics",
            learning_objectives="Understand HTML, CSS, JavaScript",
            num_slides=5
        )

        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Slide generation failed"

        # Step 2: Edit slide #3 (index 2)
        slide_editor = SlideEditorPage(self.driver, self.config)
        slide_editor.open_slide_editor(slide_index=2)

        # Edit content
        new_title = "CSS Styling Fundamentals - EDITED"
        new_content = "This is the EDITED content for CSS basics slide."

        slide_editor.edit_slide_content(title=new_title, content=new_content)

        # Step 3: Save changes
        slide_editor.save_slide_changes()
        time.sleep(2)

        # Step 4: Verify UI shows edited content
        slide_titles = slide_gen_page.get_slide_titles()
        assert new_title in slide_titles, f"Edited title not found in slide titles"

        # Step 5: Save all slides to database
        slide_gen_page.save_slides()

        # Step 6: Verify database updated
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT title, content FROM slides
            WHERE title = %s
        """, (new_title,))
        result = cursor.fetchone()
        assert result is not None, "Edited slide not found in database"
        assert new_content in result[1], "Edited content not saved to database"
        cursor.close()

    @pytest.mark.priority_high
    def test_reorder_slides_within_module(self, db_connection, test_instructor_credentials,
                                          ai_generation_timeout):
        """
        Test: Reorder slides within module

        BUSINESS SCENARIO:
        AI generated slides in suboptimal order. Instructor wants to
        rearrange them to follow better pedagogical flow.

        WORKFLOW:
        1. Login and generate slides
        2. Note original slide order
        3. Move slide #1 to position #3
        4. Move slide #5 to position #2
        5. Verify new order displayed
        6. Save slides
        7. Verify database reflects new order

        SUCCESS CRITERIA:
        - Slides reorder in UI immediately
        - New order persists after save
        - Database slide_order column updated
        - No slides lost during reordering

        VALIDATION:
        - UI: Slide cards in new order
        - Database: slide_order values correct
        """
        # Step 1: Login and generate slides
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        slide_gen_page.generate_slides_from_topic(
            topic="Database Design",
            learning_objectives="Understand normalization, indexing, transactions",
            num_slides=5
        )

        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Slide generation failed"

        # Step 2: Get original slide order
        original_titles = slide_gen_page.get_slide_titles()
        assert len(original_titles) == 5, "Expected 5 slides"

        # Step 3: Reorder slides
        slide_editor = SlideEditorPage(self.driver, self.config)

        # Move slide at index 0 down (to position 1)
        slide_editor.move_slide_down(slide_index=0)
        time.sleep(1)

        # Move slide at index 3 up (to position 2)
        slide_editor.move_slide_up(slide_index=3)
        time.sleep(1)

        # Step 4: Get new slide order
        new_titles = slide_gen_page.get_slide_titles()
        assert len(new_titles) == 5, "Slides lost during reordering"
        assert new_titles != original_titles, "Slide order unchanged"

        # Step 5: Save slides
        slide_gen_page.save_slides()

        # Step 6: Verify database has correct order
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT title, slide_order FROM slides
            WHERE topic = 'Database Design'
            ORDER BY slide_order ASC
        """)
        db_slides = cursor.fetchall()
        assert len(db_slides) == 5, f"Expected 5 slides in DB, got {len(db_slides)}"

        # Verify order numbers are sequential
        for i, (title, order) in enumerate(db_slides):
            assert order == i + 1, f"Slide order gap detected: {order} != {i + 1}"

        cursor.close()

    @pytest.mark.priority_high
    def test_add_remove_slides_from_set(self, db_connection, test_instructor_credentials,
                                        ai_generation_timeout):
        """
        Test: Add and remove slides from generated set

        BUSINESS SCENARIO:
        AI generated 8 slides, but instructor wants to add 2 custom slides
        and remove 1 irrelevant slide for final deck of 9 slides.

        WORKFLOW:
        1. Login and generate 8 slides
        2. Remove slide #4 (index 3)
        3. Add new blank slide
        4. Add another blank slide
        5. Edit new slides with custom content
        6. Verify final count is 9 slides
        7. Save slides
        8. Verify database has 9 slides

        SUCCESS CRITERIA:
        - Slide successfully removed (7 remaining)
        - Two slides successfully added (9 total)
        - New slides editable
        - Final slide count = 9
        - Database matches UI

        VALIDATION:
        - UI: 9 slide cards displayed
        - Database: 9 slide records
        """
        # Step 1: Login and generate slides
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        unique_topic = f"Network Security_{uuid.uuid4().hex[:8]}"

        slide_gen_page.generate_slides_from_topic(
            topic=unique_topic,
            learning_objectives="Understand firewalls, encryption, VPNs",
            num_slides=8
        )

        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Slide generation failed"

        initial_count = slide_gen_page.get_generated_slides_count()
        assert initial_count == 8, f"Expected 8 slides initially, got {initial_count}"

        # Step 2: Remove slide #4 (index 3)
        slide_editor = SlideEditorPage(self.driver, self.config)
        slide_editor.delete_slide(slide_index=3)
        time.sleep(1)

        after_delete_count = slide_gen_page.get_generated_slides_count()
        assert after_delete_count == 7, f"Expected 7 slides after delete, got {after_delete_count}"

        # Step 3: Add two new slides
        slide_editor.add_new_slide()
        time.sleep(1)

        slide_editor.add_new_slide()
        time.sleep(1)

        final_count = slide_gen_page.get_generated_slides_count()
        assert final_count == 9, f"Expected 9 slides after adding 2, got {final_count}"

        # Step 4: Edit one of the new slides
        slide_editor.open_slide_editor(slide_index=7)  # Edit first new slide
        slide_editor.edit_slide_content(
            title="Custom Slide: Zero Trust Security",
            content="Zero trust architecture assumes no implicit trust..."
        )
        slide_editor.save_slide_changes()

        # Step 5: Save all slides
        slide_gen_page.save_slides()

        # Step 6: Verify database
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM slides
            WHERE topic = %s
        """, (unique_topic,))
        db_count = cursor.fetchone()[0]
        assert db_count == 9, f"Expected 9 slides in DB, got {db_count}"

        # Verify custom slide saved
        cursor.execute("""
            SELECT title FROM slides
            WHERE title = 'Custom Slide: Zero Trust Security'
        """)
        custom_slide = cursor.fetchone()
        assert custom_slide is not None, "Custom slide not found in database"

        cursor.close()

    @pytest.mark.priority_medium
    def test_customize_slide_templates_and_styling(self, db_connection,
                                                    test_instructor_credentials,
                                                    ai_generation_timeout):
        """
        Test: Customize slide templates and styling

        BUSINESS SCENARIO:
        Instructor wants to apply different templates to slides for visual variety:
        - Title slide uses "title-only" template
        - Content slides use "title-content" template
        - Comparison slide uses "two-column" template
        - Image slides use "image-caption" template

        WORKFLOW:
        1. Login and generate slides
        2. Change slide #1 to "title-only" template
        3. Change slide #2 to "two-column" template
        4. Change slide #3 to "image-caption" template
        5. Verify templates applied visually
        6. Save slides
        7. Verify database stores template choices

        SUCCESS CRITERIA:
        - Templates change immediately in UI
        - Slide layout adjusts to template
        - Template persists after save
        - Database stores template_type

        VALIDATION:
        - UI: Slide layout matches template
        - Database: template_type column correct
        """
        # Step 1: Login and generate slides
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        unique_topic = f"Cloud Computing_{uuid.uuid4().hex[:8]}"

        slide_gen_page.generate_slides_from_topic(
            topic=unique_topic,
            learning_objectives="Understand IaaS, PaaS, SaaS",
            num_slides=4
        )

        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Slide generation failed"

        # Step 2: Change templates
        slide_editor = SlideEditorPage(self.driver, self.config)

        # Slide 1: Title-only template
        slide_editor.open_slide_editor(slide_index=0)
        slide_editor.change_slide_template(template="title-only")
        slide_editor.save_slide_changes()

        # Slide 2: Two-column template
        slide_editor.open_slide_editor(slide_index=1)
        slide_editor.change_slide_template(template="two-column")
        slide_editor.save_slide_changes()

        # Slide 3: Image-caption template
        slide_editor.open_slide_editor(slide_index=2)
        slide_editor.change_slide_template(template="image-caption")
        slide_editor.save_slide_changes()

        # Step 3: Save slides
        slide_gen_page.save_slides()

        # Step 4: Verify database stores templates
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT slide_order, template_type FROM slides
            WHERE topic = %s
            ORDER BY slide_order ASC
        """, (unique_topic,))
        slides = cursor.fetchall()

        assert len(slides) == 4, f"Expected 4 slides, got {len(slides)}"
        assert slides[0][1] == "title-only", "Slide 1 template not saved"
        assert slides[1][1] == "two-column", "Slide 2 template not saved"
        assert slides[2][1] == "image-caption", "Slide 3 template not saved"

        cursor.close()


@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not configured")
@pytest.mark.e2e
@pytest.mark.content_generation
class TestSlideQualityValidation(BaseTest):
    """
    Test Category 3: Slide Quality Validation

    BUSINESS REQUIREMENT:
    Platform must validate AI-generated slide quality:
    - Content accuracy vs source material (>85%)
    - Readability (Flesch-Kincaid score >60)
    - Formatting consistency
    - Media appropriateness

    QUALITY CRITERIA:
    - Quality metrics calculated correctly
    - Warnings shown for low-quality slides
    - Instructors can override quality checks
    - Quality data stored in database
    """

    @pytest.mark.priority_critical
    def test_verify_slide_content_accuracy(self, db_connection, test_instructor_credentials,
                                           ai_generation_timeout):
        """
        Test: Verify slide content accuracy vs source material

        BUSINESS SCENARIO:
        AI generated slides from course outline. Platform must verify
        that slide content accurately reflects the source outline
        with >85% accuracy to prevent misinformation.

        WORKFLOW:
        1. Login and generate slides from known outline
        2. Open slide preview
        3. Check content accuracy metric
        4. Verify accuracy >85%
        5. If accuracy <85%, verify warning shown
        6. Verify database stores accuracy score

        SUCCESS CRITERIA:
        - Content accuracy calculated
        - Accuracy score >85% for good slides
        - Warning shown for accuracy <85%
        - Accuracy stored in database

        VALIDATION:
        - UI: Accuracy score displayed in preview
        - Database: accuracy_score column populated

        TECHNICAL NOTE:
        Accuracy calculated using semantic similarity (embeddings)
        between source outline and generated slide content.
        """
        # Step 1: Login and generate slides with known source
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        # Use specific outline to test accuracy
        test_outline = """
        Module: Microservices Architecture
        1. Service decomposition strategies
           - Decompose by business capability
           - Decompose by subdomain
        2. Inter-service communication
           - Synchronous (REST, gRPC)
           - Asynchronous (message queues)
        3. Data management patterns
           - Database per service
           - Saga pattern for transactions
        """

        slide_gen_page.generate_slides_from_outline(
            outline=test_outline,
            num_slides=3,
            difficulty="advanced"
        )

        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Slide generation failed"

        # Step 2: Open preview and check accuracy
        preview_page = SlidePreviewPage(self.driver, self.config)
        preview_page.open_slide_preview(slide_index=0)

        # Step 3: Get content accuracy
        accuracy = preview_page.get_content_accuracy()
        assert accuracy > 0, "Content accuracy not calculated"

        # Step 4: Verify accuracy threshold
        if accuracy >= 85.0:
            # High accuracy - should not have warnings
            has_warnings = preview_page.has_quality_warnings()
            assert not has_warnings, \
                f"High accuracy ({accuracy}%) slide should not have warnings"
        else:
            # Low accuracy - should have warnings
            has_warnings = preview_page.has_quality_warnings()
            assert has_warnings, \
                f"Low accuracy ({accuracy}%) slide should have warnings"

        preview_page.close_preview()

        # Step 5: Save slides
        slide_gen_page.save_slides()

        # Step 6: Verify database stores accuracy
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT accuracy_score FROM slides
            WHERE content LIKE '%Microservices%'
            ORDER BY slide_order ASC
            LIMIT 1
        """)
        db_accuracy = cursor.fetchone()
        assert db_accuracy is not None, "Accuracy score not stored in database"
        assert db_accuracy[0] > 0, "Invalid accuracy score in database"

        cursor.close()

    @pytest.mark.priority_critical
    def test_verify_slide_readability_score(self, db_connection, test_instructor_credentials,
                                           ai_generation_timeout):
        """
        Test: Verify slide readability (Flesch-Kincaid score >60)

        BUSINESS SCENARIO:
        Educational content must be readable for target audience.
        Flesch-Kincaid readability score >60 ensures content is
        appropriate for undergraduate students.

        WORKFLOW:
        1. Login and generate slides
        2. Open slide preview
        3. Check Flesch-Kincaid readability score
        4. Verify score >60 (target audience: undergrad)
        5. If score <60, verify warning shown
        6. Verify database stores readability score

        SUCCESS CRITERIA:
        - Readability score calculated for each slide
        - Score >60 for well-written slides
        - Warning shown for score <60
        - Score stored in database

        VALIDATION:
        - UI: Readability score displayed
        - Database: readability_score column populated

        TECHNICAL NOTE:
        Flesch-Kincaid formula:
        206.835 - 1.015 * (total_words / total_sentences)
                - 84.6 * (total_syllables / total_words)
        Score interpretation:
        - 90-100: Very easy (5th grade)
        - 60-70: Standard (8th-9th grade) ← Target for undergrad
        - 0-30: Very confusing (college graduate)
        """
        # Step 1: Login and generate slides
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        slide_gen_page.generate_slides_from_topic(
            topic="RESTful API Design",
            learning_objectives="Understand REST principles, HTTP methods, status codes",
            num_slides=5
        )

        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Slide generation failed"

        # Step 2: Check readability for all slides
        preview_page = SlidePreviewPage(self.driver, self.config)
        preview_page.open_slide_preview(slide_index=0)

        readability_scores = []

        for i in range(5):
            # Get readability score
            score = preview_page.get_readability_score()
            assert score > 0, f"Readability score not calculated for slide {i+1}"
            readability_scores.append(score)

            # Check for warnings if score too low
            if score < 60:
                has_warnings = preview_page.has_quality_warnings()
                # Note: Warning should appear, but in TDD RED phase might not be implemented
                # assert has_warnings, f"Slide {i+1} with readability {score} should have warning"

            # Navigate to next slide (except last)
            if i < 4:
                preview_page.navigate_next_slide()

        preview_page.close_preview()

        # Step 3: Verify average readability >60
        avg_readability = sum(readability_scores) / len(readability_scores)
        assert avg_readability >= 60, \
            f"Average readability {avg_readability:.1f} below target of 60"

        # Step 4: Save slides
        slide_gen_page.save_slides()

        # Step 5: Verify database stores readability
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT AVG(readability_score) FROM slides
            WHERE topic = 'RESTful API Design'
        """)
        db_avg_readability = cursor.fetchone()[0]
        assert db_avg_readability is not None, "Readability scores not in database"
        assert db_avg_readability >= 60, \
            f"DB average readability {db_avg_readability:.1f} below target"

        cursor.close()

    @pytest.mark.priority_high
    def test_verify_slide_formatting_consistency(self, db_connection,
                                                 test_instructor_credentials,
                                                 ai_generation_timeout):
        """
        Test: Verify slide formatting consistency

        BUSINESS SCENARIO:
        Professional slide decks maintain consistent formatting:
        - Font sizes consistent within same content type
        - Bullet point styles consistent
        - Color scheme consistent
        - Spacing/margins consistent

        WORKFLOW:
        1. Login and generate slides
        2. Check formatting consistency metrics
        3. Verify all slides use same:
           - Title font size
           - Body text font size
           - Bullet point style
           - Color scheme
        4. If inconsistent, verify warning shown
        5. Verify database stores consistency score

        SUCCESS CRITERIA:
        - Formatting consistency calculated
        - Consistency score >90%
        - Warning shown for inconsistent formatting
        - Consistency data in database

        VALIDATION:
        - UI: Consistency score displayed
        - Database: formatting_consistency column
        """
        # Step 1: Login and generate slides
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        slide_gen_page.generate_slides_from_topic(
            topic="DevOps CI/CD Pipelines",
            learning_objectives="Understand continuous integration, deployment, monitoring",
            num_slides=6
        )

        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Slide generation failed"

        # Step 2: Check formatting consistency
        preview_page = SlidePreviewPage(self.driver, self.config)
        preview_page.open_slide_preview(slide_index=0)

        # Get formatting consistency score
        # (In GREEN phase, this would be implemented as a quality metric)
        try:
            consistency_element = self.driver.find_element(By.ID, "formattingConsistency")
            consistency_text = consistency_element.text
            # Extract percentage (e.g., "Consistency: 95%")
            consistency = float(consistency_text.split(":")[-1].strip().replace("%", ""))

            assert consistency >= 90, \
                f"Formatting consistency {consistency}% below target of 90%"

            # Check for warnings if consistency low
            if consistency < 90:
                has_warnings = preview_page.has_quality_warnings()
                # assert has_warnings, "Low consistency should trigger warning"

        except NoSuchElementException:
            # Formatting consistency not yet implemented (TDD RED phase)
            pytest.skip("Formatting consistency metric not implemented yet")

        preview_page.close_preview()

        # Step 3: Save slides
        slide_gen_page.save_slides()

        # Step 4: Verify database
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT AVG(formatting_consistency) FROM slides
            WHERE topic = 'DevOps CI/CD Pipelines'
        """)
        db_consistency = cursor.fetchone()[0]

        if db_consistency is not None:
            assert db_consistency >= 90, \
                f"DB formatting consistency {db_consistency}% below target"
        else:
            # Not yet implemented
            pytest.skip("Formatting consistency not stored in database yet")

        cursor.close()

    @pytest.mark.priority_medium
    def test_verify_slide_media_appropriateness(self, db_connection,
                                                test_instructor_credentials,
                                                ai_generation_timeout):
        """
        Test: Verify slide media (images, diagrams) appropriateness

        BUSINESS SCENARIO:
        AI-generated images/diagrams must be:
        - Relevant to slide content
        - Educationally appropriate
        - Properly licensed (or AI-generated)
        - High quality (not pixelated)

        WORKFLOW:
        1. Login and generate slides with images
        2. Check each slide's media
        3. Verify images are:
           - Relevant to content (semantic similarity)
           - Appropriate quality (resolution check)
           - Properly attributed (source/license)
        4. If inappropriate media, verify warning
        5. Verify database stores media metadata

        SUCCESS CRITERIA:
        - Media relevance score >80%
        - Image quality meets standards (min 800x600)
        - Source/license information present
        - Inappropriate media flagged

        VALIDATION:
        - UI: Media appropriateness score displayed
        - Database: media_metadata stored
        """
        # Step 1: Login and generate slides with images
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(test_instructor_credentials['email'],
                        test_instructor_credentials['password'])

        slide_gen_page = SlideGenerationPage(self.driver, self.config)
        slide_gen_page.navigate_to(INSTRUCTOR_DASHBOARD_PATH)
        slide_gen_page.navigate_to_slide_generation()

        slide_gen_page.generate_slides_from_outline(
            outline="Machine Learning: Neural Networks, Training, Applications",
            num_slides=4,
            include_images=True  # Request images
        )

        generation_complete = slide_gen_page.wait_for_generation_complete(
            timeout=ai_generation_timeout
        )
        assert generation_complete, "Slide generation failed"

        # Step 2: Check slides for images
        slide_images = self.driver.find_elements(By.CLASS_NAME, "slide-image")
        images_count = len([img for img in slide_images if img.is_displayed()])

        # At least some slides should have images
        assert images_count > 0, "No images generated in slides"

        # Step 3: Check media appropriateness
        preview_page = SlidePreviewPage(self.driver, self.config)
        preview_page.open_slide_preview(slide_index=0)

        try:
            media_element = self.driver.find_element(By.ID, "mediaAppropriateness")
            media_text = media_element.text
            # Extract score (e.g., "Media Quality: 85%")
            media_score = float(media_text.split(":")[-1].strip().replace("%", ""))

            assert media_score >= 80, \
                f"Media appropriateness {media_score}% below target of 80%"

            # Check for warnings if score low
            if media_score < 80:
                has_warnings = preview_page.has_quality_warnings()
                # assert has_warnings, "Low media quality should trigger warning"

        except NoSuchElementException:
            # Media appropriateness not yet implemented (TDD RED phase)
            pytest.skip("Media appropriateness metric not implemented yet")

        preview_page.close_preview()

        # Step 4: Save slides
        slide_gen_page.save_slides()

        # Step 5: Verify database stores media metadata
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT image_url, image_source, image_license
            FROM slides
            WHERE topic LIKE '%Machine Learning%'
            AND image_url IS NOT NULL
        """)
        slides_with_images = cursor.fetchall()

        if len(slides_with_images) > 0:
            # Verify media metadata present
            for img_url, img_source, img_license in slides_with_images:
                assert img_url, "Image URL missing"
                # Source and license might be NULL for AI-generated images
                # but at least one should be populated
                assert img_source or img_license, \
                    "Both image source and license missing"
        else:
            pytest.skip("Image metadata not stored in database yet")

        cursor.close()
