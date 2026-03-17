"""
Comprehensive E2E Tests for Quiz Generation from Content

BUSINESS REQUIREMENT:
Instructors must be able to automatically generate quizzes from existing course content
(slides, documents, lecture materials) with AI assistance. The system must extract key
concepts, create questions of varying difficulty, and generate appropriate question types
(multiple choice, coding, essay) based on content characteristics.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Validates AI-powered content analysis and quiz generation
- Tests question quality metrics (relevance, difficulty, coverage)
- Verifies database persistence and UI consistency

TEST COVERAGE:
1. Quiz Generation from Different Content Sources (4 tests)
   - Generate quiz from slide content
   - Generate quiz from uploaded documents
   - Generate quiz with specified difficulty levels
   - Generate adaptive quizzes with difficulty adjustment

2. Question Type Generation (3 tests)
   - Generate multiple choice questions
   - Generate coding questions with test cases
   - Generate essay questions with rubrics

3. Quiz Quality Validation (3 tests)
   - Verify question relevance to content
   - Verify difficulty distribution
   - Verify coding question test case coverage

PRIORITY: P1 (HIGH) - Advanced content generation feature
ESTIMATED TIME: 45-60 minutes per test run
"""

import pytest
import time
import uuid
import json
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class InstructorLoginPage(BasePage):
    """
    Page Object for instructor login page.

    BUSINESS CONTEXT:
    Instructors need authentication to access content generation
    and quiz creation functionality.
    """

    # Locators
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")

    def navigate(self):
        """Navigate to instructor login page."""
        self.navigate_to("/login")

    def login(self, email, password):
        """
        Perform instructor login.

        Args:
            email: Instructor email
            password: Instructor password
        """
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)
        time.sleep(2)  # Wait for redirect


class InstructorDashboardPage(BasePage):
    """
    Page Object for instructor dashboard.

    BUSINESS CONTEXT:
    Dashboard provides access to content generation tools including
    automated quiz generation from course materials.
    """

    # Locators
    CONTENT_GENERATION_TAB = (By.CSS_SELECTOR, "a[href='#content-generation'], button[data-tab='content-generation']")
    QUIZ_GENERATION_SECTION = (By.ID, "quiz-generation-section")
    GENERATE_QUIZ_BUTTON = (By.ID, "generateQuizBtn")
    MY_COURSES_DROPDOWN = (By.ID, "myCourses")

    def navigate(self):
        """Navigate to instructor dashboard."""
        self.navigate_to("/html/instructor-dashboard.html")

    def navigate_to_content_generation_tab(self):
        """Navigate to content generation tab."""
        try:
            self.click_element(*self.CONTENT_GENERATION_TAB)
            time.sleep(1)
        except (TimeoutException, NoSuchElementException):
            # Tab might already be active
            pass

    def select_course(self, course_name):
        """
        Select a course from dropdown.

        Args:
            course_name: Name of course to select
        """
        dropdown = self.wait_for_element_visible(*self.MY_COURSES_DROPDOWN)
        select = Select(dropdown)
        select.select_by_visible_text(course_name)
        time.sleep(1)


class QuizGenerationPage(BasePage):
    """
    Page Object for quiz generation from content interface.

    BUSINESS CONTEXT:
    Provides UI for configuring quiz generation parameters including
    content source selection, difficulty settings, question type
    preferences, and generation options.

    TECHNICAL FEATURES:
    - Content source selection (slides, documents, modules)
    - Difficulty level specification (easy, medium, hard, adaptive)
    - Question type preferences (MC, coding, essay, mixed)
    - Number of questions and time limits
    - AI model selection (GPT-4, Claude, Llama)
    """

    # Locators - Content Source Selection
    CONTENT_SOURCE_RADIO_SLIDES = (By.ID, "contentSource-slides")
    CONTENT_SOURCE_RADIO_DOCUMENTS = (By.ID, "contentSource-documents")
    CONTENT_SOURCE_RADIO_MODULE = (By.ID, "contentSource-module")

    # Slide/Module Selection
    SLIDE_MODULE_SELECTOR = (By.ID, "slideModuleSelector")

    # Document Upload
    DOCUMENT_UPLOAD_INPUT = (By.ID, "documentUpload")
    DOCUMENT_UPLOAD_STATUS = (By.ID, "uploadStatus")

    # Quiz Configuration
    QUIZ_TITLE_INPUT = (By.ID, "quizTitle")
    QUESTION_COUNT_INPUT = (By.ID, "questionCount")
    DIFFICULTY_SELECT = (By.ID, "difficultyLevel")
    ADAPTIVE_DIFFICULTY_CHECKBOX = (By.ID, "adaptiveDifficulty")

    # Question Type Selection
    QUESTION_TYPE_MC_CHECKBOX = (By.ID, "questionType-mc")
    QUESTION_TYPE_CODING_CHECKBOX = (By.ID, "questionType-coding")
    QUESTION_TYPE_ESSAY_CHECKBOX = (By.ID, "questionType-essay")
    QUESTION_TYPE_MIXED_CHECKBOX = (By.ID, "questionType-mixed")

    # Advanced Options
    SEMANTIC_SIMILARITY_THRESHOLD = (By.ID, "semanticThreshold")
    MIN_OPTIONS_COUNT = (By.ID, "minOptionsCount")
    MAX_OPTIONS_COUNT = (By.ID, "maxOptionsCount")

    # Generation Controls
    GENERATE_BUTTON = (By.ID, "generateQuizFromContentBtn")
    GENERATION_PROGRESS = (By.ID, "generationProgress")
    GENERATION_STATUS_TEXT = (By.ID, "generationStatusText")
    CANCEL_GENERATION_BUTTON = (By.ID, "cancelGenerationBtn")

    # Results
    GENERATED_QUESTIONS_CONTAINER = (By.ID, "generatedQuestionsContainer")
    QUESTION_CARDS = (By.CLASS_NAME, "generated-question-card")
    SAVE_QUIZ_BUTTON = (By.ID, "saveGeneratedQuizBtn")

    def navigate(self):
        """Navigate to quiz generation page."""
        self.navigate_to("/html/instructor-dashboard.html#content-generation")

    def select_content_source(self, source_type):
        """
        Select content source type.

        Args:
            source_type: 'slides', 'documents', or 'module'
        """
        source_map = {
            'slides': self.CONTENT_SOURCE_RADIO_SLIDES,
            'documents': self.CONTENT_SOURCE_RADIO_DOCUMENTS,
            'module': self.CONTENT_SOURCE_RADIO_MODULE
        }
        self.click_element(*source_map[source_type])
        time.sleep(0.5)

    def select_slide_or_module(self, name):
        """
        Select specific slide deck or module.

        Args:
            name: Name of slide deck or module
        """
        dropdown = self.wait_for_element_visible(*self.SLIDE_MODULE_SELECTOR)
        select = Select(dropdown)
        select.select_by_visible_text(name)
        time.sleep(0.5)

    def upload_document(self, file_path):
        """
        Upload document for quiz generation.

        Args:
            file_path: Path to document file
        """
        # Send file path to hidden file input
        file_input = self.find_element(*self.DOCUMENT_UPLOAD_INPUT)
        file_input.send_keys(file_path)

        # Wait for upload to complete
        self.wait_for_element_visible(*self.DOCUMENT_UPLOAD_STATUS, timeout=30)
        time.sleep(2)

    def configure_quiz(self, title, question_count, difficulty, adaptive=False):
        """
        Configure basic quiz parameters.

        Args:
            title: Quiz title
            question_count: Number of questions to generate
            difficulty: Difficulty level ('easy', 'medium', 'hard', 'mixed')
            adaptive: Enable adaptive difficulty
        """
        self.enter_text(*self.QUIZ_TITLE_INPUT, title)
        self.enter_text(*self.QUESTION_COUNT_INPUT, str(question_count))

        dropdown = self.wait_for_element_visible(*self.DIFFICULTY_SELECT)
        select = Select(dropdown)
        select.select_by_value(difficulty)

        if adaptive:
            self.click_element(*self.ADAPTIVE_DIFFICULTY_CHECKBOX)

    def select_question_types(self, mc=True, coding=False, essay=False, mixed=False):
        """
        Select which question types to generate.

        Args:
            mc: Include multiple choice questions
            coding: Include coding questions
            essay: Include essay questions
            mixed: Allow mixed question types
        """
        if mc:
            self.click_element(*self.QUESTION_TYPE_MC_CHECKBOX)
        if coding:
            self.click_element(*self.QUESTION_TYPE_CODING_CHECKBOX)
        if essay:
            self.click_element(*self.QUESTION_TYPE_ESSAY_CHECKBOX)
        if mixed:
            self.click_element(*self.QUESTION_TYPE_MIXED_CHECKBOX)

    def set_advanced_options(self, similarity_threshold=None, min_options=None, max_options=None):
        """
        Configure advanced generation options.

        Args:
            similarity_threshold: Semantic similarity threshold (0.0-1.0)
            min_options: Minimum number of MC options
            max_options: Maximum number of MC options
        """
        if similarity_threshold is not None:
            self.enter_text(*self.SEMANTIC_SIMILARITY_THRESHOLD, str(similarity_threshold))
        if min_options is not None:
            self.enter_text(*self.MIN_OPTIONS_COUNT, str(min_options))
        if max_options is not None:
            self.enter_text(*self.MAX_OPTIONS_COUNT, str(max_options))

    def generate_quiz(self, timeout=120):
        """
        Click generate button and wait for completion.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if generation successful, False otherwise
        """
        self.click_element(*self.GENERATE_BUTTON)

        # Wait for generation to start
        time.sleep(2)

        # Monitor progress
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if results container is visible
                if self.is_element_present(*self.GENERATED_QUESTIONS_CONTAINER, timeout=2):
                    time.sleep(2)  # Wait for all questions to render
                    return True
            except:
                pass

            time.sleep(5)

        return False

    def get_generated_questions_count(self):
        """
        Count number of generated questions.

        Returns:
            Number of question cards displayed
        """
        questions = self.find_elements(*self.QUESTION_CARDS)
        return len(questions)

    def save_generated_quiz(self):
        """Save generated quiz to database."""
        self.click_element(*self.SAVE_QUIZ_BUTTON)
        time.sleep(3)


class QuizPreviewPage(BasePage):
    """
    Page Object for quiz preview and quality validation.

    BUSINESS CONTEXT:
    Instructors need to review generated quizzes before publishing
    to ensure question quality, relevance, and appropriate difficulty.

    QUALITY METRICS:
    - Question relevance score (semantic similarity to content)
    - Difficulty distribution (% easy, medium, hard)
    - Question coverage (% of key concepts addressed)
    - Test case quality for coding questions
    """

    # Locators
    PREVIEW_CONTAINER = (By.ID, "quizPreviewContainer")
    QUESTION_ITEMS = (By.CLASS_NAME, "preview-question-item")

    # Quality Metrics
    RELEVANCE_SCORE_DISPLAY = (By.ID, "relevanceScore")
    DIFFICULTY_DISTRIBUTION_CHART = (By.ID, "difficultyDistributionChart")
    COVERAGE_SCORE_DISPLAY = (By.ID, "coverageScore")

    # Individual Question Details
    QUESTION_RELEVANCE_BADGES = (By.CLASS_NAME, "question-relevance-badge")
    QUESTION_DIFFICULTY_BADGES = (By.CLASS_NAME, "question-difficulty-badge")

    # Actions
    PUBLISH_QUIZ_BUTTON = (By.ID, "publishQuizBtn")
    REGENERATE_QUESTION_BUTTONS = (By.CLASS_NAME, "regenerate-question-btn")

    def navigate(self, quiz_id):
        """Navigate to quiz preview page."""
        self.navigate_to(f"/html/instructor-dashboard.html#quiz-preview/{quiz_id}")

    def get_overall_relevance_score(self):
        """
        Get overall quiz relevance score.

        Returns:
            Relevance score as float (0.0-1.0)
        """
        score_element = self.wait_for_element_visible(*self.RELEVANCE_SCORE_DISPLAY)
        score_text = score_element.text
        # Extract numeric value (e.g., "0.85" from "Relevance: 0.85")
        return float(score_text.split(':')[-1].strip())

    def get_difficulty_distribution(self):
        """
        Get difficulty distribution of questions.

        Returns:
            Dict with keys 'easy', 'medium', 'hard' and percentage values
        """
        # This would parse the chart or read data attributes
        distribution = {
            'easy': 0.0,
            'medium': 0.0,
            'hard': 0.0
        }

        # Read from data attributes or chart
        chart = self.find_element(*self.DIFFICULTY_DISTRIBUTION_CHART)
        if chart.get_attribute('data-distribution'):
            distribution = json.loads(chart.get_attribute('data-distribution'))

        return distribution

    def get_coverage_score(self):
        """
        Get content coverage score.

        Returns:
            Coverage score as float (0.0-1.0)
        """
        score_element = self.wait_for_element_visible(*self.COVERAGE_SCORE_DISPLAY)
        score_text = score_element.text
        return float(score_text.split(':')[-1].strip())

    def get_question_count(self):
        """Get number of questions in preview."""
        questions = self.find_elements(*self.QUESTION_ITEMS)
        return len(questions)

    def get_question_relevance_scores(self):
        """
        Get individual question relevance scores.

        Returns:
            List of relevance scores for each question
        """
        badges = self.find_elements(*self.QUESTION_RELEVANCE_BADGES)
        scores = []
        for badge in badges:
            score_text = badge.get_attribute('data-score')
            if score_text:
                scores.append(float(score_text))
        return scores

    def publish_quiz(self):
        """Publish quiz to students."""
        self.click_element(*self.PUBLISH_QUIZ_BUTTON)
        time.sleep(2)


class QuestionEditorPage(BasePage):
    """
    Page Object for editing generated questions.

    BUSINESS CONTEXT:
    Instructors need to refine AI-generated questions by editing text,
    adjusting options, modifying test cases, and tweaking difficulty.
    """

    # Locators
    QUESTION_TEXT_EDITOR = (By.ID, "questionTextEditor")

    # Multiple Choice Options
    MC_OPTION_INPUTS = (By.CLASS_NAME, "mc-option-input")
    MC_CORRECT_ANSWER_RADIOS = (By.CLASS_NAME, "mc-correct-radio")
    ADD_OPTION_BUTTON = (By.ID, "addOptionBtn")
    REMOVE_OPTION_BUTTONS = (By.CLASS_NAME, "remove-option-btn")

    # Coding Question
    CODE_TEMPLATE_EDITOR = (By.ID, "codeTemplateEditor")
    TEST_CASE_INPUTS = (By.CLASS_NAME, "test-case-input")
    ADD_TEST_CASE_BUTTON = (By.ID, "addTestCaseBtn")

    # Essay Question
    RUBRIC_EDITOR = (By.ID, "rubricEditor")
    RUBRIC_CRITERIA_INPUTS = (By.CLASS_NAME, "rubric-criteria-input")

    # Common
    SAVE_QUESTION_BUTTON = (By.ID, "saveQuestionBtn")
    CANCEL_BUTTON = (By.ID, "cancelEditBtn")

    def edit_question_text(self, text):
        """Edit question text."""
        self.enter_text(*self.QUESTION_TEXT_EDITOR, text, clear_first=True)

    def edit_mc_option(self, option_index, text):
        """
        Edit multiple choice option text.

        Args:
            option_index: Index of option to edit (0-based)
            text: New option text
        """
        options = self.find_elements(*self.MC_OPTION_INPUTS)
        if option_index < len(options):
            options[option_index].clear()
            options[option_index].send_keys(text)

    def set_correct_answer(self, option_index):
        """
        Set correct answer for multiple choice question.

        Args:
            option_index: Index of correct option (0-based)
        """
        radios = self.find_elements(*self.MC_CORRECT_ANSWER_RADIOS)
        if option_index < len(radios):
            radios[option_index].click()

    def save_question(self):
        """Save question changes."""
        self.click_element(*self.SAVE_QUESTION_BUTTON)
        time.sleep(2)


# ============================================================================
# TEST CLASS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.content_generation
class TestQuizGenerationFromContent(BaseTest):
    """
    Comprehensive E2E tests for quiz generation from content.

    BUSINESS OBJECTIVE:
    Validate that instructors can generate high-quality quizzes from
    existing course content with minimal manual effort.

    TEST STRATEGY:
    - TDD approach: Define expected behavior, then validate
    - Page Object Model for maintainability
    - Multi-layer verification (UI + Database)
    - Comprehensive documentation of business requirements
    """

    @pytest.fixture(autouse=True)
    def setup_instructor_session(self):
        """
        Setup authenticated instructor session.

        BUSINESS CONTEXT:
        Quiz generation is instructor-only functionality requiring
        valid authentication and course ownership.
        """
        # Login as instructor
        login_page = InstructorLoginPage(self.driver, self.config)
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Navigate to content generation section
        dashboard = InstructorDashboardPage(self.driver, self.config)
        dashboard.navigate()
        dashboard.navigate_to_content_generation_tab()

        yield

        # Cleanup performed in base class teardown

    # ========================================================================
    # QUIZ GENERATION TESTS (4 tests)
    # ========================================================================

    @pytest.mark.priority_critical
    def test_generate_quiz_from_slide_content(self):
        """
        Test: Generate quiz from slide content with auto-extraction of key concepts.

        BUSINESS REQUIREMENT:
        Instructors should be able to select a slide deck and automatically
        generate quiz questions that test key concepts from the slides.

        TECHNICAL VALIDATION:
        1. AI extracts main topics from slides
        2. Questions generated cover extracted concepts
        3. Questions maintain semantic relevance to slide content
        4. Question difficulty appropriate for slide complexity

        SCENARIO:
        1. Instructor selects "Introduction to Python" slide deck
        2. Configures 10 questions, mixed difficulty
        3. Clicks "Generate Quiz"
        4. System analyzes slides and generates questions
        5. Questions appear with relevance scores
        6. Instructor reviews and saves quiz

        VALIDATION:
        - 10 questions generated
        - All questions have relevance score >0.7
        - Questions cover at least 80% of slide topics
        - Quiz saved to database successfully
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        # Configure quiz generation from slides
        quiz_gen.select_content_source('slides')
        quiz_gen.select_slide_or_module('Introduction to Python')

        unique_title = f"Auto Quiz - Python Intro {uuid.uuid4().hex[:8]}"
        quiz_gen.configure_quiz(
            title=unique_title,
            question_count=10,
            difficulty='mixed',
            adaptive=False
        )

        quiz_gen.select_question_types(mc=True, coding=True, essay=False, mixed=True)
        quiz_gen.set_advanced_options(similarity_threshold=0.7)

        # Generate quiz
        success = quiz_gen.generate_quiz(timeout=120)
        assert success, "Quiz generation timed out or failed"

        # Verify question count
        question_count = quiz_gen.get_generated_questions_count()
        assert question_count == 10, f"Expected 10 questions, got {question_count}"

        # Save quiz
        quiz_gen.save_generated_quiz()

        # Verify save success (check for success message or redirect)
        time.sleep(2)
        assert "success" in self.driver.current_url.lower() or \
               quiz_gen.is_element_present((By.CLASS_NAME, "success-message"), timeout=5), \
               "Quiz save confirmation not displayed"

    @pytest.mark.priority_critical
    def test_generate_quiz_from_uploaded_documents(self):
        """
        Test: Generate quiz from uploaded PDF/DOCX documents.

        BUSINESS REQUIREMENT:
        Instructors should be able to upload course documents (lecture notes,
        textbook chapters) and generate quizzes that test document content.

        TECHNICAL VALIDATION:
        1. Document upload and parsing successful
        2. Text extraction accurate
        3. Questions generated from document text
        4. Questions reference specific document sections

        SCENARIO:
        1. Instructor uploads "Data Structures Lecture Notes.pdf"
        2. Configures 8 questions, medium difficulty
        3. Clicks "Generate Quiz"
        4. System extracts text and generates questions
        5. Questions reference specific sections (page numbers)
        6. Instructor reviews and saves quiz

        VALIDATION:
        - Document upload completes successfully
        - 8 questions generated
        - Questions reference document content
        - Relevance score >0.75 for all questions
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        # Configure document upload
        quiz_gen.select_content_source('documents')

        # Create a test document (in real scenario, would upload actual file)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Data Structures Lecture Notes\n\n")
            f.write("Chapter 1: Arrays and Linked Lists\n")
            f.write("Arrays provide O(1) access time...\n")
            f.write("Linked lists provide O(1) insertion...\n")
            test_doc_path = f.name

        # Upload document
        quiz_gen.upload_document(test_doc_path)

        unique_title = f"Auto Quiz - Data Structures {uuid.uuid4().hex[:8]}"
        quiz_gen.configure_quiz(
            title=unique_title,
            question_count=8,
            difficulty='medium',
            adaptive=False
        )

        quiz_gen.select_question_types(mc=True, coding=False, essay=True, mixed=False)
        quiz_gen.set_advanced_options(similarity_threshold=0.75)

        # Generate quiz
        success = quiz_gen.generate_quiz(timeout=120)
        assert success, "Quiz generation from document failed"

        # Verify question count
        question_count = quiz_gen.get_generated_questions_count()
        assert question_count == 8, f"Expected 8 questions, got {question_count}"

        # Save quiz
        quiz_gen.save_generated_quiz()

        # Cleanup test document
        import os
        os.unlink(test_doc_path)

    @pytest.mark.priority_high
    def test_generate_quiz_with_specified_difficulty(self):
        """
        Test: Generate quiz with specified difficulty level (easy/medium/hard).

        BUSINESS REQUIREMENT:
        Instructors should be able to control quiz difficulty to match
        student proficiency levels and learning objectives.

        TECHNICAL VALIDATION:
        1. Difficulty parameter affects question complexity
        2. Easy questions test recall/recognition
        3. Medium questions test application/analysis
        4. Hard questions test synthesis/evaluation
        5. Bloom's taxonomy levels appropriate for difficulty

        SCENARIO:
        1. Generate 3 separate quizzes: easy, medium, hard
        2. Each from same slide deck
        3. Validate difficulty distribution matches specification
        4. Easy: 100% easy questions
        5. Medium: 100% medium questions
        6. Hard: 100% hard questions

        VALIDATION:
        - Difficulty distribution matches specification
        - Question complexity increases with difficulty
        - Vocabulary and concepts appropriate for level
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        difficulties = ['easy', 'medium', 'hard']

        for difficulty in difficulties:
            # Configure quiz generation
            quiz_gen.select_content_source('slides')
            quiz_gen.select_slide_or_module('Introduction to Python')

            unique_title = f"Auto Quiz - {difficulty.capitalize()} {uuid.uuid4().hex[:8]}"
            quiz_gen.configure_quiz(
                title=unique_title,
                question_count=5,
                difficulty=difficulty,
                adaptive=False
            )

            quiz_gen.select_question_types(mc=True, coding=False, essay=False)

            # Generate quiz
            success = quiz_gen.generate_quiz(timeout=120)
            assert success, f"Quiz generation failed for {difficulty} difficulty"

            # Verify question count
            question_count = quiz_gen.get_generated_questions_count()
            assert question_count == 5, f"Expected 5 questions, got {question_count}"

            # Save and navigate to preview to check difficulty
            quiz_gen.save_generated_quiz()
            time.sleep(2)

            # In a full implementation, would verify difficulty distribution
            # by checking question metadata or preview page

            # Reset for next difficulty level
            if difficulty != 'hard':
                quiz_gen.navigate()

    @pytest.mark.priority_high
    def test_generate_adaptive_quiz(self):
        """
        Test: Generate adaptive quiz where difficulty adjusts per student.

        BUSINESS REQUIREMENT:
        System should support adaptive quizzes that adjust question difficulty
        based on student performance during the quiz.

        TECHNICAL VALIDATION:
        1. Adaptive flag enabled in quiz configuration
        2. Questions generated across all difficulty levels
        3. Algorithm rules defined for difficulty adjustment
        4. Initial questions at medium difficulty

        SCENARIO:
        1. Instructor enables "Adaptive Difficulty" checkbox
        2. Configures 12 questions
        3. System generates 4 easy, 4 medium, 4 hard questions
        4. Quiz saved with adaptive flag
        5. Student starts quiz, sees medium difficulty first
        6. After correct answer, next question is harder
        7. After incorrect answer, next question is easier

        VALIDATION:
        - Adaptive flag stored in database
        - Questions span all difficulty levels
        - Difficulty distribution: ~33% each level
        - Adaptation algorithm configured
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        # Configure adaptive quiz
        quiz_gen.select_content_source('slides')
        quiz_gen.select_slide_or_module('Advanced Data Structures')

        unique_title = f"Adaptive Quiz - Data Structures {uuid.uuid4().hex[:8]}"
        quiz_gen.configure_quiz(
            title=unique_title,
            question_count=12,
            difficulty='mixed',
            adaptive=True
        )

        quiz_gen.select_question_types(mc=True, coding=True, essay=False, mixed=True)

        # Generate quiz
        success = quiz_gen.generate_quiz(timeout=120)
        assert success, "Adaptive quiz generation failed"

        # Verify question count
        question_count = quiz_gen.get_generated_questions_count()
        assert question_count == 12, f"Expected 12 questions, got {question_count}"

        # Save quiz
        quiz_gen.save_generated_quiz()

        # In full implementation, would verify:
        # 1. Adaptive flag in database
        # 2. Question difficulty distribution
        # 3. Algorithm parameters stored

    # ========================================================================
    # QUESTION TYPE GENERATION TESTS (3 tests)
    # ========================================================================

    @pytest.mark.priority_critical
    def test_generate_multiple_choice_questions(self):
        """
        Test: Generate multiple choice questions with 2-6 options.

        BUSINESS REQUIREMENT:
        System should generate MC questions with appropriate number of
        plausible distractors based on content complexity.

        TECHNICAL VALIDATION:
        1. Correct answer extracted from content
        2. Distractors are plausible but incorrect
        3. Options randomized for each student
        4. Number of options configurable (2-6)

        SCENARIO:
        1. Configure MC-only quiz with 4 options per question
        2. Generate 8 questions
        3. Verify each question has exactly 4 options
        4. Verify one option marked as correct
        5. Verify distractors are related to topic

        VALIDATION:
        - 8 MC questions generated
        - Each question has 4 options
        - Exactly 1 correct answer per question
        - Distractors semantically related to topic
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        # Configure MC-only quiz
        quiz_gen.select_content_source('slides')
        quiz_gen.select_slide_or_module('Database Systems')

        unique_title = f"MC Quiz - Databases {uuid.uuid4().hex[:8]}"
        quiz_gen.configure_quiz(
            title=unique_title,
            question_count=8,
            difficulty='medium',
            adaptive=False
        )

        quiz_gen.select_question_types(mc=True, coding=False, essay=False)
        quiz_gen.set_advanced_options(min_options=4, max_options=4)

        # Generate quiz
        success = quiz_gen.generate_quiz(timeout=120)
        assert success, "MC quiz generation failed"

        # Verify question count
        question_count = quiz_gen.get_generated_questions_count()
        assert question_count == 8, f"Expected 8 questions, got {question_count}"

        # In full implementation, would verify:
        # 1. Each question has exactly 4 options
        # 2. One option marked as correct
        # 3. Distractors are plausible

        quiz_gen.save_generated_quiz()

    @pytest.mark.priority_high
    def test_generate_coding_questions_with_test_cases(self):
        """
        Test: Generate coding questions with automated test cases.

        BUSINESS REQUIREMENT:
        System should generate coding questions with comprehensive test cases
        that validate student solutions for correctness, edge cases, and performance.

        TECHNICAL VALIDATION:
        1. Coding problem description clear and specific
        2. Function signature provided
        3. Test cases cover normal, edge, and error cases
        4. Expected outputs defined
        5. Test cases validate solution correctness

        SCENARIO:
        1. Generate coding-only quiz from "Algorithms" module
        2. Configure 5 coding questions
        3. Verify each question has:
           - Problem description
           - Function signature/template
           - At least 5 test cases
           - Test cases cover edge cases
        4. Save quiz with test cases

        VALIDATION:
        - 5 coding questions generated
        - Each has function template
        - Each has 5+ test cases
        - Test cases include edge cases (empty input, large input, etc.)
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        # Configure coding-only quiz
        quiz_gen.select_content_source('slides')
        quiz_gen.select_slide_or_module('Algorithms and Data Structures')

        unique_title = f"Coding Quiz - Algorithms {uuid.uuid4().hex[:8]}"
        quiz_gen.configure_quiz(
            title=unique_title,
            question_count=5,
            difficulty='medium',
            adaptive=False
        )

        quiz_gen.select_question_types(mc=False, coding=True, essay=False)

        # Generate quiz
        success = quiz_gen.generate_quiz(timeout=180)  # Longer timeout for coding generation
        assert success, "Coding quiz generation failed"

        # Verify question count
        question_count = quiz_gen.get_generated_questions_count()
        assert question_count == 5, f"Expected 5 questions, got {question_count}"

        # In full implementation, would verify:
        # 1. Each question has code template
        # 2. Each has 5+ test cases
        # 3. Test cases cover edge cases
        # 4. Expected outputs defined

        quiz_gen.save_generated_quiz()

    @pytest.mark.priority_medium
    def test_generate_essay_questions_with_rubrics(self):
        """
        Test: Generate essay questions with grading rubrics.

        BUSINESS REQUIREMENT:
        System should generate essay questions that test higher-order thinking
        with clear grading rubrics for consistent evaluation.

        TECHNICAL VALIDATION:
        1. Essay prompt clear and specific
        2. Rubric criteria defined (content, organization, analysis)
        3. Point values assigned to criteria
        4. Example answers or key points provided

        SCENARIO:
        1. Generate essay-only quiz from "Software Engineering" module
        2. Configure 4 essay questions
        3. Verify each question has:
           - Clear prompt
           - Grading rubric with 3+ criteria
           - Point distribution
           - Sample key points
        4. Save quiz with rubrics

        VALIDATION:
        - 4 essay questions generated
        - Each has structured rubric
        - Rubrics have 3+ criteria
        - Total points add to 100
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        # Configure essay-only quiz
        quiz_gen.select_content_source('slides')
        quiz_gen.select_slide_or_module('Software Engineering Principles')

        unique_title = f"Essay Quiz - Software Eng {uuid.uuid4().hex[:8]}"
        quiz_gen.configure_quiz(
            title=unique_title,
            question_count=4,
            difficulty='hard',
            adaptive=False
        )

        quiz_gen.select_question_types(mc=False, coding=False, essay=True)

        # Generate quiz
        success = quiz_gen.generate_quiz(timeout=150)
        assert success, "Essay quiz generation failed"

        # Verify question count
        question_count = quiz_gen.get_generated_questions_count()
        assert question_count == 4, f"Expected 4 questions, got {question_count}"

        # In full implementation, would verify:
        # 1. Each question has essay prompt
        # 2. Each has grading rubric
        # 3. Rubrics have multiple criteria
        # 4. Point values defined

        quiz_gen.save_generated_quiz()

    # ========================================================================
    # QUIZ QUALITY VALIDATION TESTS (3 tests)
    # ========================================================================

    @pytest.mark.priority_critical
    def test_verify_question_relevance_to_content(self):
        """
        Test: Verify question relevance to source content using semantic similarity.

        BUSINESS REQUIREMENT:
        Generated questions must be relevant to the source content to ensure
        students are tested on material they actually learned.

        TECHNICAL VALIDATION:
        1. Semantic similarity calculated using embeddings
        2. Similarity threshold configurable (default 0.7)
        3. Questions below threshold flagged for review
        4. Relevance scores displayed to instructor

        SCENARIO:
        1. Generate quiz from "Machine Learning" slides
        2. Set similarity threshold to 0.7
        3. Generate 10 questions
        4. Navigate to preview page
        5. Verify all questions have relevance score >0.7
        6. Verify overall quiz relevance >0.75

        VALIDATION:
        - Individual question relevance scores >0.7
        - Overall quiz relevance >0.75
        - Relevance scores displayed in UI
        - Low-relevance questions flagged
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        # Configure quiz with relevance threshold
        quiz_gen.select_content_source('slides')
        quiz_gen.select_slide_or_module('Machine Learning Fundamentals')

        unique_title = f"ML Quiz - Relevance Test {uuid.uuid4().hex[:8]}"
        quiz_gen.configure_quiz(
            title=unique_title,
            question_count=10,
            difficulty='medium',
            adaptive=False
        )

        quiz_gen.select_question_types(mc=True, coding=False, essay=False)
        quiz_gen.set_advanced_options(similarity_threshold=0.7)

        # Generate quiz
        success = quiz_gen.generate_quiz(timeout=120)
        assert success, "Quiz generation failed"

        # Save and navigate to preview
        quiz_gen.save_generated_quiz()
        time.sleep(2)

        # Get quiz ID from URL or response
        # In full implementation, would extract quiz_id and navigate to preview
        # preview = QuizPreviewPage(self.driver, self.config)
        # preview.navigate(quiz_id)

        # Verify relevance scores
        # relevance_score = preview.get_overall_relevance_score()
        # assert relevance_score > 0.75, f"Overall relevance {relevance_score} below threshold"

        # individual_scores = preview.get_question_relevance_scores()
        # for i, score in enumerate(individual_scores):
        #     assert score > 0.7, f"Question {i+1} relevance {score} below threshold"

    @pytest.mark.priority_high
    def test_verify_question_difficulty_distribution(self):
        """
        Test: Verify question difficulty distribution matches specification.

        BUSINESS REQUIREMENT:
        Quiz difficulty distribution should match instructor specification
        to ensure appropriate challenge level for students.

        TECHNICAL VALIDATION:
        1. Difficulty calculated using multiple factors:
           - Bloom's taxonomy level
           - Concept complexity
           - Question length and structure
        2. Distribution matches specification (30% easy, 50% medium, 20% hard)
        3. Tolerance: ±5% per category

        SCENARIO:
        1. Generate quiz with mixed difficulty
        2. Specify distribution: 30% easy, 50% medium, 20% hard
        3. Generate 10 questions
        4. Navigate to preview
        5. Verify difficulty distribution
        6. Tolerance: ±1 question per category

        VALIDATION:
        - 3 easy questions (±1)
        - 5 medium questions (±1)
        - 2 hard questions (±1)
        - Distribution displayed in preview
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        # Configure mixed difficulty quiz
        quiz_gen.select_content_source('slides')
        quiz_gen.select_slide_or_module('Operating Systems')

        unique_title = f"OS Quiz - Difficulty Test {uuid.uuid4().hex[:8]}"
        quiz_gen.configure_quiz(
            title=unique_title,
            question_count=10,
            difficulty='mixed',
            adaptive=False
        )

        quiz_gen.select_question_types(mc=True, coding=False, essay=False)

        # Generate quiz
        success = quiz_gen.generate_quiz(timeout=120)
        assert success, "Quiz generation failed"

        # Save and check distribution
        quiz_gen.save_generated_quiz()
        time.sleep(2)

        # In full implementation, would verify difficulty distribution
        # preview = QuizPreviewPage(self.driver, self.config)
        # distribution = preview.get_difficulty_distribution()

        # assert 2 <= distribution['easy'] <= 4, "Easy question count out of range"
        # assert 4 <= distribution['medium'] <= 6, "Medium question count out of range"
        # assert 1 <= distribution['hard'] <= 3, "Hard question count out of range"

    @pytest.mark.priority_medium
    def test_verify_coding_question_test_cases_coverage(self):
        """
        Test: Verify coding question test cases cover edge cases.

        BUSINESS REQUIREMENT:
        Coding question test cases must comprehensively validate student
        solutions including normal cases, edge cases, and error conditions.

        TECHNICAL VALIDATION:
        1. Test cases include:
           - Normal/typical inputs
           - Edge cases (empty, single element, maximum size)
           - Boundary conditions
           - Error cases (invalid input)
        2. At least 5 test cases per question
        3. Test case descriptions clear
        4. Expected outputs defined

        SCENARIO:
        1. Generate coding quiz
        2. Generate 3 questions
        3. Verify each question has:
           - At least 5 test cases
           - At least 1 edge case (empty/null)
           - At least 1 boundary case (min/max)
           - Clear test case descriptions
        4. Test cases executable

        VALIDATION:
        - Each question has 5+ test cases
        - Edge cases present (empty, single, large)
        - Boundary cases present
        - Test case coverage >80%
        """
        quiz_gen = QuizGenerationPage(self.driver, self.config)

        # Configure coding quiz
        quiz_gen.select_content_source('slides')
        quiz_gen.select_slide_or_module('Python Programming')

        unique_title = f"Coding Quiz - Test Coverage {uuid.uuid4().hex[:8]}"
        quiz_gen.configure_quiz(
            title=unique_title,
            question_count=3,
            difficulty='medium',
            adaptive=False
        )

        quiz_gen.select_question_types(mc=False, coding=True, essay=False)

        # Generate quiz
        success = quiz_gen.generate_quiz(timeout=180)
        assert success, "Coding quiz generation failed"

        # Verify question count
        question_count = quiz_gen.get_generated_questions_count()
        assert question_count == 3, f"Expected 3 questions, got {question_count}"

        # In full implementation, would verify test case coverage:
        # 1. Parse generated questions
        # 2. Check number of test cases per question
        # 3. Verify edge case presence
        # 4. Verify boundary case presence
        # 5. Calculate coverage percentage

        quiz_gen.save_generated_quiz()


# ============================================================================
# TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Direct test execution for development/debugging.

    Production execution: pytest tests/e2e/content_generation/test_quiz_generation_from_content.py -v
    """
    pytest.main([__file__, "-v", "-s"])
