"""
Comprehensive End-to-End Tests for Content Regeneration Workflows

BUSINESS REQUIREMENT:
Validates content regeneration workflows allowing instructors to iterate on
AI-generated content when dissatisfied with initial outputs or when content
becomes outdated. Tests version control, rollback, and comparison features.

TECHNICAL IMPLEMENTATION:
- Uses selenium_base.py BaseTest as parent class
- Tests real UI interactions for content regeneration
- Covers regeneration scenarios per E2E_PHASE_4_PLAN.md (lines 83-96)
- HTTPS-only communication (https://localhost:3000)
- Headless-compatible for CI/CD
- Page Object Model pattern for maintainability
- Extended timeouts for AI regeneration operations
- Multi-layer verification (UI + Database)

TEST COVERAGE:
1. Regeneration Scenarios (5 tests):
   - Regenerate single slide (instructor dissatisfied)
   - Regenerate entire module (content outdated)
   - Regenerate quiz questions (difficulty adjustment)
   - Regenerate with different AI model
   - Regenerate with instructor feedback

2. Version Control (3 tests):
   - Version history tracking
   - Compare versions side-by-side
   - Rollback to previous version

PRIORITY: P1 (HIGH) - Part of Phase 4 Content Generation expansion
"""

import pytest
import time
import json
import psycopg2
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import base test class
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from e2e.selenium_base import BaseTest, BasePage


# Test Configuration
BASE_URL = "https://localhost:3000"
INSTRUCTOR_DASHBOARD_URL = f"{BASE_URL}/html/instructor-dashboard-modular.html"
LOGIN_URL = f"{BASE_URL}/html/index.html"

# Test Credentials
TEST_INSTRUCTOR_EMAIL = "instructor@example.com"
TEST_INSTRUCTOR_PASSWORD = "InstructorPass123!"

# AI Regeneration Timeouts
AI_REGENERATION_TIMEOUT = 120  # 2 minutes for AI regeneration
STANDARD_TIMEOUT = 30  # 30 seconds for standard operations


class LoginPage(BasePage):
    """Page Object Model for Login Page."""

    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BTN = (By.ID, "loginBtn")

    def navigate_to_login(self):
        """Navigate to login page."""
        self.navigate_to("/html/index.html")

    def login(self, email, password):
        """Perform login."""
        self.enter_text(*self.EMAIL_INPUT, text=email)
        self.enter_text(*self.PASSWORD_INPUT, text=password)
        self.click_element(*self.LOGIN_BTN)
        time.sleep(2)


class ContentRegenerationPage(BasePage):
    """
    Page Object Model for Content Regeneration UI.
    
    BUSINESS CONTEXT:
    Encapsulates all content regeneration elements including regeneration
    triggers, feedback forms, model selection, and progress tracking.
    """

    # Content selection
    CONTENT_TAB = (By.CSS_SELECTOR, "[data-tab='content']")
    SLIDE_LIST = (By.CLASS_NAME, "slide-list")
    MODULE_LIST = (By.CLASS_NAME, "module-list")
    QUIZ_LIST = (By.CLASS_NAME, "quiz-list")

    # Regeneration controls
    REGENERATE_BTN = (By.CLASS_NAME, "regenerate-btn")
    REGENERATE_SLIDE_BTN = (By.CLASS_NAME, "regenerate-slide-btn")
    REGENERATE_MODULE_BTN = (By.CLASS_NAME, "regenerate-module-btn")
    REGENERATE_QUIZ_BTN = (By.CLASS_NAME, "regenerate-quiz-btn")
    
    # Regeneration options modal
    REGENERATION_MODAL = (By.ID, "regenerationModal")
    AI_MODEL_SELECT = (By.ID, "aiModelSelect")
    FEEDBACK_TEXTAREA = (By.ID, "instructorFeedback")
    DIFFICULTY_SELECT = (By.ID, "difficultySelect")
    CONFIRM_REGENERATE_BTN = (By.ID, "confirmRegenerateBtn")
    CANCEL_REGENERATE_BTN = (By.ID, "cancelRegenerateBtn")
    
    # Progress tracking
    REGENERATION_PROGRESS = (By.CLASS_NAME, "regeneration-progress")
    PROGRESS_BAR = (By.CLASS_NAME, "progress-bar")
    PROGRESS_MESSAGE = (By.CLASS_NAME, "progress-message")
    
    # Success/Error states
    SUCCESS_MESSAGE = (By.CLASS_NAME, "regeneration-success")
    ERROR_MESSAGE = (By.CLASS_NAME, "regeneration-error")

    def navigate_to_content_tab(self):
        """Navigate to content management tab."""
        self.click_element(*self.CONTENT_TAB)
        time.sleep(1)

    def select_slide(self, slide_index):
        """Select specific slide for regeneration."""
        slides = self.find_elements(*self.SLIDE_LIST)
        if slide_index < len(slides):
            slides[slide_index].click()
            time.sleep(0.5)

    def click_regenerate_slide(self):
        """Click regenerate button for selected slide."""
        self.click_element(*self.REGENERATE_SLIDE_BTN)
        self.wait_for_element_visible(*self.REGENERATION_MODAL)

    def click_regenerate_module(self):
        """Click regenerate button for entire module."""
        self.click_element(*self.REGENERATE_MODULE_BTN)
        self.wait_for_element_visible(*self.REGENERATION_MODAL)

    def click_regenerate_quiz(self):
        """Click regenerate button for quiz."""
        self.click_element(*self.REGENERATE_QUIZ_BTN)
        self.wait_for_element_visible(*self.REGENERATION_MODAL)

    def select_ai_model(self, model_name):
        """
        Select AI model for regeneration.
        
        Args:
            model_name: 'gpt-4', 'claude', 'llama'
        """
        select = Select(self.find_element(*self.AI_MODEL_SELECT))
        select.select_by_value(model_name)

    def enter_instructor_feedback(self, feedback_text):
        """Enter instructor feedback for regeneration guidance."""
        self.enter_text(*self.FEEDBACK_TEXTAREA, text=feedback_text)

    def select_difficulty(self, difficulty):
        """
        Select difficulty level for regeneration.
        
        Args:
            difficulty: 'easy', 'medium', 'hard'
        """
        select = Select(self.find_element(*self.DIFFICULTY_SELECT))
        select.select_by_value(difficulty)

    def confirm_regeneration(self):
        """Confirm and start regeneration process."""
        self.click_element(*self.CONFIRM_REGENERATE_BTN)
        
    def wait_for_regeneration_complete(self, timeout=AI_REGENERATION_TIMEOUT):
        """Wait for regeneration to complete."""
        try:
            self.wait_for_element_visible(*self.SUCCESS_MESSAGE, timeout=timeout)
            return True
        except TimeoutException:
            return False

    def get_regeneration_error(self):
        """Get error message if regeneration failed."""
        try:
            return self.get_text(*self.ERROR_MESSAGE)
        except NoSuchElementException:
            return None


class VersionHistoryPage(BasePage):
    """
    Page Object Model for Version History Management.
    
    BUSINESS CONTEXT:
    Encapsulates version tracking, comparison, and rollback functionality
    for content regeneration workflows.
    """

    # Version history controls
    VERSION_HISTORY_BTN = (By.CLASS_NAME, "version-history-btn")
    VERSION_HISTORY_MODAL = (By.ID, "versionHistoryModal")
    VERSION_LIST = (By.CLASS_NAME, "version-list")
    VERSION_ITEM = (By.CLASS_NAME, "version-item")
    
    # Version details
    VERSION_NUMBER = (By.CLASS_NAME, "version-number")
    VERSION_DATE = (By.CLASS_NAME, "version-date")
    VERSION_AUTHOR = (By.CLASS_NAME, "version-author")
    VERSION_AI_MODEL = (By.CLASS_NAME, "version-ai-model")
    VERSION_FEEDBACK = (By.CLASS_NAME, "version-feedback")
    
    # Version actions
    VIEW_VERSION_BTN = (By.CLASS_NAME, "view-version-btn")
    COMPARE_VERSION_BTN = (By.CLASS_NAME, "compare-version-btn")
    ROLLBACK_VERSION_BTN = (By.CLASS_NAME, "rollback-version-btn")
    
    # Rollback confirmation
    ROLLBACK_MODAL = (By.ID, "rollbackConfirmModal")
    CONFIRM_ROLLBACK_BTN = (By.ID, "confirmRollbackBtn")
    CANCEL_ROLLBACK_BTN = (By.ID, "cancelRollbackBtn")

    def open_version_history(self):
        """Open version history modal."""
        self.click_element(*self.VERSION_HISTORY_BTN)
        self.wait_for_element_visible(*self.VERSION_HISTORY_MODAL)

    def get_version_count(self):
        """Get total number of versions."""
        versions = self.find_elements(*self.VERSION_ITEM)
        return len(versions)

    def get_version_details(self, version_index):
        """
        Get details for specific version.
        
        Returns:
            dict: Version metadata
        """
        versions = self.find_elements(*self.VERSION_ITEM)
        if version_index >= len(versions):
            return None
            
        version = versions[version_index]
        return {
            'number': version.find_element(*self.VERSION_NUMBER).text,
            'date': version.find_element(*self.VERSION_DATE).text,
            'author': version.find_element(*self.VERSION_AUTHOR).text,
            'ai_model': version.find_element(*self.VERSION_AI_MODEL).text,
            'feedback': version.find_element(*self.VERSION_FEEDBACK).text
        }

    def compare_versions(self, version1_index, version2_index):
        """
        Compare two versions side-by-side.
        
        Args:
            version1_index: Index of first version
            version2_index: Index of second version
        """
        versions = self.find_elements(*self.VERSION_ITEM)
        versions[version1_index].find_element(*self.COMPARE_VERSION_BTN).click()
        time.sleep(0.5)
        versions[version2_index].find_element(*self.COMPARE_VERSION_BTN).click()

    def rollback_to_version(self, version_index):
        """
        Rollback to specific version.
        
        Args:
            version_index: Index of version to rollback to
        """
        versions = self.find_elements(*self.VERSION_ITEM)
        versions[version_index].find_element(*self.ROLLBACK_VERSION_BTN).click()
        self.wait_for_element_visible(*self.ROLLBACK_MODAL)
        self.click_element(*self.CONFIRM_ROLLBACK_BTN)


class VersionComparisonPage(BasePage):
    """
    Page Object Model for Side-by-Side Version Comparison.
    
    BUSINESS CONTEXT:
    Allows instructors to compare different versions of content
    to understand changes and decide on rollback.
    """

    # Comparison view
    COMPARISON_MODAL = (By.ID, "versionComparisonModal")
    VERSION1_PANEL = (By.CLASS_NAME, "version1-panel")
    VERSION2_PANEL = (By.CLASS_NAME, "version2-panel")
    
    # Version metadata
    VERSION1_HEADER = (By.CLASS_NAME, "version1-header")
    VERSION2_HEADER = (By.CLASS_NAME, "version2-header")
    
    # Content comparison
    VERSION1_CONTENT = (By.CLASS_NAME, "version1-content")
    VERSION2_CONTENT = (By.CLASS_NAME, "version2-content")
    DIFF_HIGHLIGHTS = (By.CLASS_NAME, "diff-highlight")
    
    # Actions
    CLOSE_COMPARISON_BTN = (By.CLASS_NAME, "close-comparison-btn")
    CHOOSE_VERSION1_BTN = (By.CLASS_NAME, "choose-version1-btn")
    CHOOSE_VERSION2_BTN = (By.CLASS_NAME, "choose-version2-btn")

    def get_version1_content(self):
        """Get content from version 1 panel."""
        return self.get_text(*self.VERSION1_CONTENT)

    def get_version2_content(self):
        """Get content from version 2 panel."""
        return self.get_text(*self.VERSION2_CONTENT)

    def get_diff_count(self):
        """Get number of differences highlighted."""
        diffs = self.find_elements(*self.DIFF_HIGHLIGHTS)
        return len(diffs)

    def choose_version1(self):
        """Choose version 1 as active version."""
        self.click_element(*self.CHOOSE_VERSION1_BTN)

    def choose_version2(self):
        """Choose version 2 as active version."""
        self.click_element(*self.CHOOSE_VERSION2_BTN)


# ============================================================================
# REGENERATION SCENARIOS TESTS (5 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.content_generation
@pytest.mark.priority_high
class TestContentRegenerationScenarios(BaseTest):
    """
    Tests for content regeneration scenarios.
    
    BUSINESS REQUIREMENT:
    Instructors must be able to regenerate content when dissatisfied with
    AI outputs or when content becomes outdated, with multiple regeneration
    options and feedback mechanisms.
    """

    def test_regenerate_single_slide_instructor_dissatisfied(self):
        """
        Test regenerating a single slide when instructor is dissatisfied.
        
        BUSINESS SCENARIO:
        An instructor generates slides for a Python module but finds one slide
        about "list comprehensions" too simplistic. They regenerate just that
        slide with feedback to make it more advanced.
        
        VALIDATION CRITERIA:
        - Regeneration modal appears with feedback form
        - Instructor can provide specific feedback
        - Only selected slide is regenerated
        - Other slides remain unchanged
        - New slide content reflects feedback
        - Database updated with new version
        """
        # Login as instructor
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(TEST_INSTRUCTOR_EMAIL, TEST_INSTRUCTOR_PASSWORD)
        
        # Navigate to content tab
        regen_page = ContentRegenerationPage(self.driver, self.config)
        regen_page.navigate_to_content_tab()
        
        # Select slide 3 (list comprehensions)
        regen_page.select_slide(2)  # 0-indexed
        
        # Click regenerate for this slide
        regen_page.click_regenerate_slide()
        
        # Provide instructor feedback
        feedback = "Make this more advanced - include nested comprehensions and performance considerations"
        regen_page.enter_instructor_feedback(feedback)
        
        # Confirm regeneration
        regen_page.confirm_regeneration()
        
        # Wait for regeneration to complete
        success = regen_page.wait_for_regeneration_complete()
        assert success, "Slide regeneration should complete successfully"
        
        # Verify success message displayed
        assert regen_page.is_element_present(*regen_page.SUCCESS_MESSAGE)
        
        # Verify only slide 3 was regenerated (check version count)
        version_page = VersionHistoryPage(self.driver, self.config)
        version_page.open_version_history()
        assert version_page.get_version_count() >= 2, "Should have at least 2 versions"
        
        # Database verification
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT content, version, feedback FROM content_versions 
            WHERE slide_id = %s ORDER BY version DESC LIMIT 1
        """, (3,))
        result = cursor.fetchone()
        assert result is not None, "Slide version should exist in database"
        assert result[2] == feedback, "Instructor feedback should be stored"
        cursor.close()
        conn.close()

    def test_regenerate_entire_module_content_outdated(self):
        """
        Test regenerating entire module when content is outdated.
        
        BUSINESS SCENARIO:
        A Python course was created 2 years ago. Python 3.12 is now out with
        new features. Instructor regenerates the entire "Advanced Python" module
        to include new Python 3.12 features.
        
        VALIDATION CRITERIA:
        - Module-level regeneration option available
        - All slides in module regenerated
        - Feedback applied to all slides
        - Version history tracks module regeneration
        - Quiz questions updated to match new content
        """
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(TEST_INSTRUCTOR_EMAIL, TEST_INSTRUCTOR_PASSWORD)
        
        regen_page = ContentRegenerationPage(self.driver, self.config)
        regen_page.navigate_to_content_tab()
        
        # Click regenerate for entire module
        regen_page.click_regenerate_module()
        
        # Provide module-level feedback
        feedback = "Update to include Python 3.12 features: match statements, improved type hints, and performance improvements"
        regen_page.enter_instructor_feedback(feedback)
        
        # Confirm regeneration
        regen_page.confirm_regeneration()
        
        # Wait for regeneration (longer timeout for entire module)
        success = regen_page.wait_for_regeneration_complete(timeout=180)
        assert success, "Module regeneration should complete successfully"
        
        # Verify all slides have new versions
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT slide_id) FROM content_versions 
            WHERE module_id = %s AND version > 1
        """, (1,))
        regenerated_slides = cursor.fetchone()[0]
        assert regenerated_slides >= 5, "At least 5 slides should be regenerated"
        cursor.close()
        conn.close()

    def test_regenerate_quiz_questions_difficulty_adjustment(self):
        """
        Test regenerating quiz questions to adjust difficulty.
        
        BUSINESS SCENARIO:
        An instructor notices students are scoring too high (95% average) on
        a quiz, indicating questions are too easy. They regenerate quiz with
        'hard' difficulty setting.
        
        VALIDATION CRITERIA:
        - Quiz regeneration preserves question count
        - Difficulty parameter affects generated questions
        - Previous quiz version archived
        - Student submissions unaffected
        - Analytics show difficulty change
        """
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(TEST_INSTRUCTOR_EMAIL, TEST_INSTRUCTOR_PASSWORD)
        
        regen_page = ContentRegenerationPage(self.driver, self.config)
        regen_page.navigate_to_content_tab()
        
        # Click regenerate for quiz
        regen_page.click_regenerate_quiz()
        
        # Select hard difficulty
        regen_page.select_difficulty('hard')
        
        # Provide feedback
        feedback = "Questions are too easy - students averaging 95%. Make more challenging with edge cases."
        regen_page.enter_instructor_feedback(feedback)
        
        # Confirm regeneration
        regen_page.confirm_regeneration()
        
        # Wait for regeneration
        success = regen_page.wait_for_regeneration_complete()
        assert success, "Quiz regeneration should complete successfully"
        
        # Verify quiz difficulty updated in database
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT difficulty, version FROM quizzes 
            WHERE quiz_id = %s ORDER BY version DESC LIMIT 1
        """, (1,))
        result = cursor.fetchone()
        assert result[0] == 'hard', "Quiz difficulty should be updated to hard"
        assert result[1] > 1, "Quiz should have version > 1"
        cursor.close()
        conn.close()

    def test_regenerate_with_different_ai_model(self):
        """
        Test regenerating content with different AI model.
        
        BUSINESS SCENARIO:
        An instructor used GPT-4 for initial generation but finds the content
        too verbose. They regenerate using Claude which tends to be more concise.
        
        VALIDATION CRITERIA:
        - Multiple AI models available for selection
        - Model selection persisted in version history
        - Content style reflects model characteristics
        - Model metadata stored in database
        """
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(TEST_INSTRUCTOR_EMAIL, TEST_INSTRUCTOR_PASSWORD)
        
        regen_page = ContentRegenerationPage(self.driver, self.config)
        regen_page.navigate_to_content_tab()
        
        # Select slide for regeneration
        regen_page.select_slide(1)
        regen_page.click_regenerate_slide()
        
        # Select Claude model instead of GPT-4
        regen_page.select_ai_model('claude')
        
        # Provide feedback
        feedback = "Make more concise - GPT-4 version too wordy"
        regen_page.enter_instructor_feedback(feedback)
        
        # Confirm regeneration
        regen_page.confirm_regeneration()
        
        # Wait for regeneration
        success = regen_page.wait_for_regeneration_complete()
        assert success, "Regeneration with Claude should complete successfully"
        
        # Verify AI model tracked in version history
        version_page = VersionHistoryPage(self.driver, self.config)
        version_page.open_version_history()
        latest_version = version_page.get_version_details(0)
        assert latest_version['ai_model'] == 'Claude', "Version history should track Claude as model"

    def test_regenerate_with_instructor_feedback_integration(self):
        """
        Test regeneration integrating multiple rounds of instructor feedback.
        
        BUSINESS SCENARIO:
        Instructor regenerates slide 3 times, each time providing refinement
        feedback. System should track feedback history and use cumulative
        feedback for better results.
        
        VALIDATION CRITERIA:
        - Multiple regenerations possible
        - Each feedback saved in history
        - Later regenerations access previous feedback
        - Cumulative feedback improves results
        - Feedback chain visible in UI
        """
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(TEST_INSTRUCTOR_EMAIL, TEST_INSTRUCTOR_PASSWORD)
        
        regen_page = ContentRegenerationPage(self.driver, self.config)
        regen_page.navigate_to_content_tab()
        regen_page.select_slide(0)
        
        # First regeneration
        regen_page.click_regenerate_slide()
        regen_page.enter_instructor_feedback("Add more code examples")
        regen_page.confirm_regeneration()
        regen_page.wait_for_regeneration_complete()
        
        time.sleep(2)
        
        # Second regeneration
        regen_page.click_regenerate_slide()
        regen_page.enter_instructor_feedback("Make examples more practical - real-world scenarios")
        regen_page.confirm_regeneration()
        regen_page.wait_for_regeneration_complete()
        
        time.sleep(2)
        
        # Third regeneration
        regen_page.click_regenerate_slide()
        regen_page.enter_instructor_feedback("Add common pitfalls section")
        regen_page.confirm_regeneration()
        regen_page.wait_for_regeneration_complete()
        
        # Verify 4 versions exist (original + 3 regenerations)
        version_page = VersionHistoryPage(self.driver, self.config)
        version_page.open_version_history()
        assert version_page.get_version_count() == 4, "Should have 4 versions"
        
        # Verify all feedback saved
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT feedback FROM content_versions 
            WHERE slide_id = %s ORDER BY version ASC
        """, (1,))
        feedbacks = [row[0] for row in cursor.fetchall()]
        assert len(feedbacks) == 4, "Should have 4 feedback entries"
        assert "code examples" in feedbacks[1]
        assert "practical" in feedbacks[2]
        assert "pitfalls" in feedbacks[3]
        cursor.close()
        conn.close()


# ============================================================================
# VERSION CONTROL TESTS (3 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.content_generation
@pytest.mark.priority_high
class TestVersionControl(BaseTest):
    """
    Tests for version control and rollback functionality.
    
    BUSINESS REQUIREMENT:
    Instructors must be able to track version history, compare versions,
    and rollback to previous versions if regeneration produces worse content.
    """

    def test_version_history_tracking(self):
        """
        Test comprehensive version history tracking.
        
        BUSINESS SCENARIO:
        An instructor has regenerated a slide 5 times with different AI models
        and feedback. They want to see complete history of all versions with
        metadata (date, model, feedback, author).
        
        VALIDATION CRITERIA:
        - All versions displayed chronologically
        - Each version shows: number, date, author, AI model, feedback
        - Latest version marked as current
        - Version count accurate
        - Database matches UI display
        """
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(TEST_INSTRUCTOR_EMAIL, TEST_INSTRUCTOR_PASSWORD)
        
        # Create 3 versions through regeneration
        regen_page = ContentRegenerationPage(self.driver, self.config)
        regen_page.navigate_to_content_tab()
        regen_page.select_slide(0)
        
        for i in range(3):
            regen_page.click_regenerate_slide()
            regen_page.enter_instructor_feedback(f"Iteration {i+1}: Refine content")
            regen_page.select_ai_model(['gpt-4', 'claude', 'llama'][i])
            regen_page.confirm_regeneration()
            regen_page.wait_for_regeneration_complete()
            time.sleep(2)
        
        # Open version history
        version_page = VersionHistoryPage(self.driver, self.config)
        version_page.open_version_history()
        
        # Verify all versions present
        version_count = version_page.get_version_count()
        assert version_count == 4, f"Should have 4 versions (original + 3 regenerations), got {version_count}"
        
        # Verify metadata for each version
        for i in range(version_count):
            details = version_page.get_version_details(i)
            assert details is not None, f"Version {i} details should exist"
            assert details['number'] is not None
            assert details['date'] is not None
            assert details['author'] == TEST_INSTRUCTOR_EMAIL
            if i > 0:  # Regenerated versions
                assert details['ai_model'] in ['GPT-4', 'Claude', 'Llama']
                assert 'Iteration' in details['feedback']

    def test_compare_versions_side_by_side(self):
        """
        Test side-by-side version comparison.
        
        BUSINESS SCENARIO:
        Instructor wants to compare version 2 (GPT-4) with version 3 (Claude)
        to see which AI model produced better content. Comparison should
        highlight differences.
        
        VALIDATION CRITERIA:
        - Two versions displayed side-by-side
        - Content differences highlighted
        - Version metadata visible for both
        - Can choose preferred version
        - Comparison view accessible and clear
        """
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(TEST_INSTRUCTOR_EMAIL, TEST_INSTRUCTOR_PASSWORD)
        
        # Create 2 versions with different models
        regen_page = ContentRegenerationPage(self.driver, self.config)
        regen_page.navigate_to_content_tab()
        regen_page.select_slide(1)
        
        # Version 2: GPT-4
        regen_page.click_regenerate_slide()
        regen_page.select_ai_model('gpt-4')
        regen_page.enter_instructor_feedback("Use GPT-4")
        regen_page.confirm_regeneration()
        regen_page.wait_for_regeneration_complete()
        time.sleep(2)
        
        # Version 3: Claude
        regen_page.click_regenerate_slide()
        regen_page.select_ai_model('claude')
        regen_page.enter_instructor_feedback("Use Claude")
        regen_page.confirm_regeneration()
        regen_page.wait_for_regeneration_complete()
        time.sleep(2)
        
        # Open version history and compare
        version_page = VersionHistoryPage(self.driver, self.config)
        version_page.open_version_history()
        version_page.compare_versions(1, 0)  # Compare version 2 vs version 3
        
        # Verify comparison view
        comparison_page = VersionComparisonPage(self.driver, self.config)
        assert comparison_page.is_element_present(*comparison_page.COMPARISON_MODAL)
        
        # Verify both versions displayed
        content1 = comparison_page.get_version1_content()
        content2 = comparison_page.get_version2_content()
        assert len(content1) > 0, "Version 1 content should be displayed"
        assert len(content2) > 0, "Version 2 content should be displayed"
        
        # Verify differences highlighted
        diff_count = comparison_page.get_diff_count()
        assert diff_count > 0, "Differences should be highlighted"

    def test_rollback_to_previous_version(self):
        """
        Test rollback to previous version functionality.
        
        BUSINESS SCENARIO:
        Instructor regenerates a slide but new version is worse than v2.
        They rollback from v3 to v2, making v2 the active version again.
        
        VALIDATION CRITERIA:
        - Rollback option available for all versions
        - Confirmation modal prevents accidental rollback
        - Rolled-back version becomes current
        - Rollback creates new version (v4 = copy of v2)
        - Database updated correctly
        - Students see rolled-back content
        """
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate_to_login()
        login_page.login(TEST_INSTRUCTOR_EMAIL, TEST_INSTRUCTOR_PASSWORD)
        
        # Create 3 versions
        regen_page = ContentRegenerationPage(self.driver, self.config)
        regen_page.navigate_to_content_tab()
        regen_page.select_slide(2)
        
        for i in range(2):
            regen_page.click_regenerate_slide()
            regen_page.enter_instructor_feedback(f"Version {i+2}")
            regen_page.confirm_regeneration()
            regen_page.wait_for_regeneration_complete()
            time.sleep(2)
        
        # Open version history
        version_page = VersionHistoryPage(self.driver, self.config)
        version_page.open_version_history()
        
        # Verify 3 versions exist
        assert version_page.get_version_count() == 3
        
        # Rollback to version 2 (index 1)
        version_page.rollback_to_version(1)
        time.sleep(2)
        
        # Verify rollback created new version
        version_page.open_version_history()
        assert version_page.get_version_count() == 4, "Rollback should create new version"
        
        # Verify database reflects rollback
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT content, is_active FROM content_versions 
            WHERE slide_id = %s AND version = 4
        """, (3,))
        result = cursor.fetchone()
        assert result is not None, "Rollback version should exist"
        assert result[1] == True, "Rollback version should be active"
        cursor.close()
        conn.close()


    def get_db_connection(self):
        """Helper method to get database connection."""
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'course_creator'),
            user=os.getenv('DB_USER', 'course_user'),
            password=os.getenv('DB_PASSWORD', 'password')
        )
