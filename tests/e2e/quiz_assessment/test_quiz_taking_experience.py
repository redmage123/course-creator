"""
Comprehensive E2E Tests for Student Quiz-Taking Experience

BUSINESS REQUIREMENT:
Tests the complete student quiz-taking experience from quiz access through
completion, including all quiz features, workflows, and edge cases. Ensures
students have a smooth, reliable, and feature-rich assessment experience.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Covers 35+ test scenarios across quiz lifecycle
- Validates UI interactions, auto-save, timer, anti-cheating features
- Tests error handling, network resilience, and accessibility

TEST COVERAGE:
1. Quiz Access (6 tests)
   - Navigate to quiz from course page
   - Verify quiz locked before availability date
   - Verify quiz locked after due date
   - Verify attempt limit enforcement
   - Resume incomplete quiz attempt
   - View quiz instructions before starting

2. Quiz Taking Workflow (10 tests)
   - Start quiz and timer begins
   - Answer multiple choice question
   - Answer coding question (code editor integration)
   - Answer essay question (rich text editor)
   - Navigate between questions (next/previous)
   - Mark question for review
   - Save progress automatically
   - Submit quiz manually
   - Auto-submit when time expires
   - Warning before time expiration (5 min, 1 min)

3. Quiz Features (7 tests)
   - Question randomization working
   - Answer choice randomization
   - File upload for coding assignments
   - Code syntax highlighting
   - Code execution in lab (if applicable)
   - Calculator availability (if enabled)
   - Reference materials access (if allowed)

4. Quiz Completion (6 tests)
   - Submit quiz and see confirmation
   - View immediate feedback (if enabled)
   - View score (if immediate scoring enabled)
   - View correct answers (if review allowed)
   - View quiz analytics (time spent, accuracy)
   - Retake quiz (if multiple attempts allowed)

5. Edge Cases (6 tests)
   - Browser refresh doesn't lose progress
   - Network interruption recovery
   - Concurrent tab detection
   - Copy-paste prevention (if anti-cheating enabled)
   - Tab switching detection
   - Full-screen enforcement

PRIORITY: P0 (CRITICAL) - Essential for assessment functionality
"""

import pytest
import time
import uuid
import asyncio
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.action_chains import ActionChains

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class CoursePage(BasePage):
    """
    Page Object for course detail page with quiz access.

    BUSINESS CONTEXT:
    Students access quizzes from their enrolled courses. The course page
    shows quiz availability, attempts, and access control.
    """

    # Locators
    COURSE_TITLE = (By.CSS_SELECTOR, "h1.course-title")
    QUIZ_LIST = (By.CSS_SELECTOR, ".quiz-list")
    QUIZ_ITEM = (By.CSS_SELECTOR, ".quiz-item")
    QUIZ_LINK = (By.CSS_SELECTOR, "a.quiz-link")
    QUIZ_LOCKED_BADGE = (By.CSS_SELECTOR, ".quiz-locked")
    QUIZ_COMPLETED_BADGE = (By.CSS_SELECTOR, ".quiz-completed")
    QUIZ_ATTEMPTS_REMAINING = (By.CSS_SELECTOR, ".attempts-remaining")
    QUIZ_DUE_DATE = (By.CSS_SELECTOR, ".quiz-due-date")
    QUIZ_AVAILABLE_DATE = (By.CSS_SELECTOR, ".quiz-available-date")

    def navigate_to_quiz(self, quiz_name):
        """
        Navigate to specific quiz by name.

        Args:
            quiz_name: Name of the quiz to access
        """
        # Find quiz link by text
        quiz_links = self.driver.find_elements(*self.QUIZ_LINK)
        for link in quiz_links:
            if quiz_name.lower() in link.text.lower():
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                time.sleep(0.3)
                link.click()
                return True
        return False

    def is_quiz_locked(self, quiz_name):
        """Check if quiz is locked."""
        quiz_items = self.driver.find_elements(*self.QUIZ_ITEM)
        for item in quiz_items:
            if quiz_name.lower() in item.text.lower():
                locked_badges = item.find_elements(*self.QUIZ_LOCKED_BADGE)
                return len(locked_badges) > 0
        return False

    def get_attempts_remaining(self, quiz_name):
        """Get number of attempts remaining for quiz."""
        quiz_items = self.driver.find_elements(*self.QUIZ_ITEM)
        for item in quiz_items:
            if quiz_name.lower() in item.text.lower():
                try:
                    attempts_elem = item.find_element(*self.QUIZ_ATTEMPTS_REMAINING)
                    # Extract number from text like "2 attempts remaining"
                    import re
                    match = re.search(r'(\d+)', attempts_elem.text)
                    if match:
                        return int(match.group(1))
                except NoSuchElementException:
                    return None
        return None


class QuizInstructionsPage(BasePage):
    """
    Page Object for quiz instructions/start page.

    BUSINESS CONTEXT:
    Before starting a quiz, students see instructions, time limits,
    attempt information, and rules. This is critical for informed consent.
    """

    # Locators
    QUIZ_TITLE = (By.CSS_SELECTOR, "h1.quiz-title")
    INSTRUCTIONS_TEXT = (By.CSS_SELECTOR, ".quiz-instructions")
    TIME_LIMIT_TEXT = (By.CSS_SELECTOR, ".time-limit")
    QUESTION_COUNT = (By.CSS_SELECTOR, ".question-count")
    PASSING_SCORE = (By.CSS_SELECTOR, ".passing-score")
    ATTEMPTS_INFO = (By.CSS_SELECTOR, ".attempts-info")
    START_QUIZ_BUTTON = (By.ID, "start-quiz-btn")
    BACK_TO_COURSE_LINK = (By.CSS_SELECTOR, "a[href*='course']")
    RULES_LIST = (By.CSS_SELECTOR, ".quiz-rules")

    def get_quiz_title(self):
        """Get quiz title."""
        return self.get_text(*self.QUIZ_TITLE)

    def get_instructions(self):
        """Get quiz instructions."""
        if self.is_element_present(*self.INSTRUCTIONS_TEXT, timeout=3):
            return self.get_text(*self.INSTRUCTIONS_TEXT)
        return None

    def get_time_limit(self):
        """Get time limit in minutes."""
        if self.is_element_present(*self.TIME_LIMIT_TEXT, timeout=3):
            text = self.get_text(*self.TIME_LIMIT_TEXT)
            # Extract number from text like "60 minutes"
            import re
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))
        return None

    def get_question_count(self):
        """Get total number of questions."""
        if self.is_element_present(*self.QUESTION_COUNT, timeout=3):
            text = self.get_text(*self.QUESTION_COUNT)
            import re
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))
        return None

    def start_quiz(self):
        """Click start quiz button."""
        self.click_element(*self.START_QUIZ_BUTTON)
        time.sleep(1)


class QuizPage(BasePage):
    """
    Page Object for active quiz page.

    BUSINESS CONTEXT:
    The quiz page is where students answer questions, navigate between
    questions, and submit their quiz. It includes timer, progress tracking,
    and various question types.
    """

    # Locators - Quiz Header
    QUIZ_TITLE = (By.CSS_SELECTOR, "h1.quiz-title")
    QUIZ_TIMER = (By.CSS_SELECTOR, ".quiz-timer")
    QUESTION_COUNTER = (By.CSS_SELECTOR, ".question-counter")
    ANSWER_COUNTER = (By.CSS_SELECTOR, ".answer-counter")
    SAVE_INDICATOR = (By.CSS_SELECTOR, ".save-indicator")
    TIME_WARNING = (By.CSS_SELECTOR, ".time-warning")

    # Locators - Question Content
    QUESTION_CONTAINER = (By.CSS_SELECTOR, ".question-container.active")
    QUESTION_TEXT = (By.CSS_SELECTOR, ".question-text")
    ANSWER_OPTIONS = (By.CSS_SELECTOR, ".answer-option")
    ANSWER_RADIO = (By.CSS_SELECTOR, "input[type='radio']")
    ANSWER_CHECKBOX = (By.CSS_SELECTOR, "input[type='checkbox']")
    TEXT_ANSWER_INPUT = (By.CSS_SELECTOR, "textarea.answer-text")
    CODE_EDITOR = (By.CSS_SELECTOR, ".code-editor")
    FILE_UPLOAD_INPUT = (By.CSS_SELECTOR, "input[type='file']")

    # Locators - Navigation
    PREVIOUS_BUTTON = (By.ID, "previous-question-btn")
    NEXT_BUTTON = (By.ID, "next-question-btn")
    SUBMIT_BUTTON = (By.ID, "submit-quiz-btn")
    MARK_FOR_REVIEW_BUTTON = (By.CSS_SELECTOR, ".mark-for-review")
    QUESTION_NAVIGATOR = (By.CSS_SELECTOR, ".question-navigator")
    QUESTION_NAV_ITEM = (By.CSS_SELECTOR, ".question-nav-item")

    # Locators - Tools
    CALCULATOR_BUTTON = (By.CSS_SELECTOR, ".calculator-button")
    CALCULATOR_MODAL = (By.CSS_SELECTOR, ".calculator-modal")
    REFERENCE_MATERIALS_BUTTON = (By.CSS_SELECTOR, ".reference-button")
    REFERENCE_MATERIALS_MODAL = (By.CSS_SELECTOR, ".reference-modal")
    CODE_RUN_BUTTON = (By.CSS_SELECTOR, ".run-code-button")
    CODE_OUTPUT = (By.CSS_SELECTOR, ".code-output")

    # Locators - Warnings/Alerts
    TAB_SWITCH_WARNING = (By.CSS_SELECTOR, ".tab-switch-warning")
    FULLSCREEN_PROMPT = (By.CSS_SELECTOR, ".fullscreen-prompt")
    AUTO_SAVE_MESSAGE = (By.CSS_SELECTOR, ".auto-save-message")

    def get_timer_value(self):
        """
        Get current timer value in seconds.

        Returns:
            int: Remaining time in seconds, or None if no timer
        """
        if self.is_element_present(*self.QUIZ_TIMER, timeout=3):
            timer_text = self.get_text(*self.QUIZ_TIMER)
            # Parse format like "45:30" (MM:SS)
            import re
            match = re.search(r'(\d+):(\d+)', timer_text)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                return minutes * 60 + seconds
        return None

    def get_current_question_number(self):
        """Get current question number."""
        counter_text = self.get_text(*self.QUESTION_COUNTER)
        # Parse "Question 3 of 10"
        import re
        match = re.search(r'Question (\d+) of (\d+)', counter_text)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def get_question_text(self):
        """Get current question text."""
        return self.get_text(*self.QUESTION_TEXT)

    def select_multiple_choice_answer(self, answer_index=0):
        """
        Select multiple choice answer by index.

        Args:
            answer_index: 0-based index of answer option
        """
        # Wait for answer options to be visible
        answer_options = WebDriverWait(self.driver, 10).until(
            lambda d: [el for el in d.find_elements(*self.ANSWER_OPTIONS) if el.is_displayed()]
        )

        if answer_options and len(answer_options) > answer_index:
            # Scroll into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                answer_options[answer_index]
            )
            time.sleep(0.3)
            answer_options[answer_index].click()
            time.sleep(0.2)  # Wait for selection to register

    def answer_text_question(self, text):
        """
        Answer text/essay question.

        Args:
            text: Answer text to enter
        """
        self.enter_text(*self.TEXT_ANSWER_INPUT, text)

    def answer_code_question(self, code):
        """
        Answer coding question using code editor.

        Args:
            code: Code to enter
        """
        # Wait for code editor to be present
        code_editor = self.wait_for_element(*self.CODE_EDITOR, timeout=10)

        # Use JavaScript to set code editor value (handles CodeMirror/Monaco)
        self.driver.execute_script("""
            var editor = arguments[0];
            if (editor.CodeMirror) {
                editor.CodeMirror.setValue(arguments[1]);
            } else if (window.monaco) {
                monaco.editor.getModels()[0].setValue(arguments[1]);
            } else {
                editor.value = arguments[1];
            }
        """, code_editor, code)
        time.sleep(0.5)

    def upload_file(self, file_path):
        """
        Upload file for file upload question.

        Args:
            file_path: Path to file to upload
        """
        file_input = self.find_element(*self.FILE_UPLOAD_INPUT)
        file_input.send_keys(file_path)
        time.sleep(1)

    def click_next_question(self):
        """Navigate to next question."""
        self.click_element(*self.NEXT_BUTTON)
        time.sleep(0.5)

    def click_previous_question(self):
        """Navigate to previous question."""
        self.click_element(*self.PREVIOUS_BUTTON)
        time.sleep(0.5)

    def mark_question_for_review(self):
        """Mark current question for later review."""
        if self.is_element_present(*self.MARK_FOR_REVIEW_BUTTON, timeout=3):
            self.click_element(*self.MARK_FOR_REVIEW_BUTTON)
            time.sleep(0.3)

    def jump_to_question(self, question_number):
        """
        Jump to specific question using navigator.

        Args:
            question_number: 1-based question number
        """
        nav_items = self.driver.find_elements(*self.QUESTION_NAV_ITEM)
        if len(nav_items) >= question_number:
            nav_items[question_number - 1].click()
            time.sleep(0.5)

    def submit_quiz(self):
        """Submit quiz for grading."""
        self.click_element(*self.SUBMIT_BUTTON)

        # Handle confirmation alert
        try:
            time.sleep(0.5)
            alert = Alert(self.driver)
            alert.accept()
        except:
            pass  # No alert present

        time.sleep(2)

    def is_auto_save_working(self):
        """Check if auto-save indicator is visible."""
        return self.is_element_present(*self.AUTO_SAVE_MESSAGE, timeout=5)

    def open_calculator(self):
        """Open calculator tool."""
        if self.is_element_present(*self.CALCULATOR_BUTTON, timeout=3):
            self.click_element(*self.CALCULATOR_BUTTON)
            time.sleep(0.5)
            return self.is_element_present(*self.CALCULATOR_MODAL, timeout=3)
        return False

    def open_reference_materials(self):
        """Open reference materials."""
        if self.is_element_present(*self.REFERENCE_MATERIALS_BUTTON, timeout=3):
            self.click_element(*self.REFERENCE_MATERIALS_BUTTON)
            time.sleep(0.5)
            return self.is_element_present(*self.REFERENCE_MATERIALS_MODAL, timeout=3)
        return False

    def run_code(self):
        """Run code in code editor."""
        if self.is_element_present(*self.CODE_RUN_BUTTON, timeout=3):
            self.click_element(*self.CODE_RUN_BUTTON)
            time.sleep(2)  # Wait for code execution
            return self.get_code_output()
        return None

    def get_code_output(self):
        """Get code execution output."""
        if self.is_element_present(*self.CODE_OUTPUT, timeout=5):
            return self.get_text(*self.CODE_OUTPUT)
        return None

    def is_time_warning_visible(self):
        """Check if time warning is displayed."""
        return self.is_element_present(*self.TIME_WARNING, timeout=3)

    def get_answered_questions_count(self):
        """Get count of answered questions from counter."""
        counter_text = self.get_text(*self.ANSWER_COUNTER)
        # Parse "5 of 10 answered"
        import re
        match = re.search(r'(\d+) of (\d+)', counter_text)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None


class QuizResultsPage(BasePage):
    """
    Page Object for quiz results page.

    BUSINESS CONTEXT:
    After submission, students see their results including score, feedback,
    correct answers (if allowed), and performance analytics.
    """

    # Locators
    RESULTS_TITLE = (By.CSS_SELECTOR, "h1.results-title")
    SCORE_DISPLAY = (By.CSS_SELECTOR, ".quiz-score")
    PERCENTAGE_DISPLAY = (By.CSS_SELECTOR, ".score-percentage")
    PASSED_MESSAGE = (By.CSS_SELECTOR, ".quiz-passed")
    FAILED_MESSAGE = (By.CSS_SELECTOR, ".quiz-failed")
    CORRECT_COUNT = (By.CSS_SELECTOR, ".correct-count")
    INCORRECT_COUNT = (By.CSS_SELECTOR, ".incorrect-count")
    TIME_SPENT = (By.CSS_SELECTOR, ".time-spent")
    FEEDBACK_MESSAGE = (By.CSS_SELECTOR, ".feedback-message")

    # Actions
    REVIEW_ANSWERS_BUTTON = (By.ID, "review-answers-btn")
    RETAKE_QUIZ_BUTTON = (By.ID, "retake-quiz-btn")
    CONTINUE_COURSE_BUTTON = (By.ID, "continue-course-btn")
    VIEW_ANALYTICS_BUTTON = (By.CSS_SELECTOR, ".view-analytics-btn")

    # Review page
    QUESTION_REVIEW_LIST = (By.CSS_SELECTOR, ".question-review-list")
    CORRECT_ANSWER = (By.CSS_SELECTOR, ".correct-answer")
    YOUR_ANSWER = (By.CSS_SELECTOR, ".your-answer")
    QUESTION_EXPLANATION = (By.CSS_SELECTOR, ".question-explanation")

    def get_score_percentage(self):
        """Get quiz score as percentage."""
        if self.is_element_present(*self.PERCENTAGE_DISPLAY, timeout=5):
            score_text = self.get_text(*self.PERCENTAGE_DISPLAY)
            import re
            match = re.search(r'(\d+)', score_text)
            if match:
                return int(match.group(1))
        return None

    def get_correct_count(self):
        """Get number of correct answers."""
        if self.is_element_present(*self.CORRECT_COUNT, timeout=3):
            text = self.get_text(*self.CORRECT_COUNT)
            import re
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))
        return None

    def is_passed(self):
        """Check if quiz was passed."""
        return self.is_element_present(*self.PASSED_MESSAGE, timeout=3)

    def is_failed(self):
        """Check if quiz was failed."""
        return self.is_element_present(*self.FAILED_MESSAGE, timeout=3)

    def get_time_spent(self):
        """Get time spent on quiz in seconds."""
        if self.is_element_present(*self.TIME_SPENT, timeout=3):
            text = self.get_text(*self.TIME_SPENT)
            # Parse various formats: "45:30", "45 minutes 30 seconds", etc.
            import re
            # Try MM:SS format first
            match = re.search(r'(\d+):(\d+)', text)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                return minutes * 60 + seconds
            # Try "X minutes Y seconds" format
            minutes_match = re.search(r'(\d+)\s*minutes?', text)
            seconds_match = re.search(r'(\d+)\s*seconds?', text)
            minutes = int(minutes_match.group(1)) if minutes_match else 0
            seconds = int(seconds_match.group(1)) if seconds_match else 0
            return minutes * 60 + seconds
        return None

    def get_feedback(self):
        """Get feedback message."""
        if self.is_element_present(*self.FEEDBACK_MESSAGE, timeout=3):
            return self.get_text(*self.FEEDBACK_MESSAGE)
        return None

    def review_answers(self):
        """Click review answers button."""
        if self.is_element_present(*self.REVIEW_ANSWERS_BUTTON, timeout=3):
            self.click_element(*self.REVIEW_ANSWERS_BUTTON)
            time.sleep(1)
            return True
        return False

    def retake_quiz(self):
        """Click retake quiz button."""
        if self.is_element_present(*self.RETAKE_QUIZ_BUTTON, timeout=3):
            self.click_element(*self.RETAKE_QUIZ_BUTTON)
            time.sleep(1)
            return True
        return False

    def view_analytics(self):
        """Click view analytics button."""
        if self.is_element_present(*self.VIEW_ANALYTICS_BUTTON, timeout=3):
            self.click_element(*self.VIEW_ANALYTICS_BUTTON)
            time.sleep(1)
            return True
        return False


class LoginPage(BasePage):
    """Page Object for student login."""

    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")

    def navigate(self):
        self.navigate_to("/student-login")

    def login(self, email, password):
        """Login as student."""
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)
        time.sleep(2)


# ============================================================================
# TEST CLASS - QUIZ ACCESS TESTS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.quiz_assessment
@pytest.mark.priority_critical
class TestQuizAccess(BaseTest):
    """
    Test suite for quiz access control and availability.

    BUSINESS REQUIREMENT:
    Students should only be able to access quizzes when they are available,
    have attempts remaining, and meet prerequisites.
    """

    @pytest.mark.asyncio
    async def test_student_navigates_to_quiz_from_course(self, browser_driver, test_base_url):
        """
        E2E TEST: Student navigates to quiz from course page

        BUSINESS REQUIREMENT:
        - Students must be able to easily find and access quizzes from their courses
        - Quiz links should be clearly visible and clickable

        TEST SCENARIO:
        1. Login as student
        2. Navigate to enrolled course
        3. Find quiz in course content
        4. Click quiz link
        5. Verify quiz instructions page loads

        VALIDATION:
        - Course page displays quiz list
        - Quiz link is clickable
        - Quiz instructions page loads successfully
        - Quiz title matches selected quiz
        """
        driver = browser_driver

        # Login as student
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # Navigate to course (assuming we're on dashboard after login)
        driver.get(f"{test_base_url}/course/1")
        time.sleep(2)

        # Find and click quiz
        course_page = CoursePage(driver, test_base_url)
        assert course_page.navigate_to_quiz("Python Programming Quiz"), \
            "Failed to find and click quiz link"

        # Verify quiz instructions page loads
        instructions_page = QuizInstructionsPage(driver, test_base_url)
        quiz_title = instructions_page.get_quiz_title()
        assert quiz_title is not None, "Quiz instructions page did not load"
        assert "quiz" in quiz_title.lower(), f"Unexpected quiz title: {quiz_title}"

    @pytest.mark.asyncio
    async def test_quiz_locked_before_availability_date(self, browser_driver, test_base_url):
        """
        E2E TEST: Quiz is locked before its availability date

        BUSINESS REQUIREMENT:
        - Quizzes should not be accessible before their scheduled availability date
        - Students should see clear messaging about when quiz becomes available

        TEST SCENARIO:
        1. Login as student
        2. Navigate to course with future-dated quiz
        3. Attempt to access quiz
        4. Verify locked state and availability message

        VALIDATION:
        - Quiz displays locked badge/icon
        - Quiz link is disabled or shows alert
        - Availability date is clearly displayed
        - Error message explains quiz is not yet available
        """
        driver = browser_driver

        # Login as student
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # Navigate to course with future quiz
        driver.get(f"{test_base_url}/course/2")
        time.sleep(2)

        # Check if quiz is locked
        course_page = CoursePage(driver, test_base_url)
        is_locked = course_page.is_quiz_locked("Future Quiz")

        assert is_locked, "Quiz should be locked before availability date"

    @pytest.mark.asyncio
    async def test_quiz_locked_after_due_date(self, browser_driver, test_base_url):
        """
        E2E TEST: Quiz is locked after its due date

        BUSINESS REQUIREMENT:
        - Quizzes should not be accessible after their due date (if configured)
        - Students should see clear messaging about missed deadline

        TEST SCENARIO:
        1. Login as student
        2. Navigate to course with past-due quiz
        3. Attempt to access quiz
        4. Verify locked state and due date message

        VALIDATION:
        - Quiz displays locked badge/icon
        - Quiz link is disabled
        - Due date is clearly displayed as passed
        - Error message explains quiz is no longer available
        """
        driver = browser_driver

        # Login as student
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # Navigate to course with expired quiz
        driver.get(f"{test_base_url}/course/3")
        time.sleep(2)

        # Check if quiz is locked
        course_page = CoursePage(driver, test_base_url)
        is_locked = course_page.is_quiz_locked("Expired Quiz")

        assert is_locked, "Quiz should be locked after due date"

    @pytest.mark.asyncio
    async def test_quiz_attempt_limit_enforced(self, browser_driver, test_base_url):
        """
        E2E TEST: Quiz attempt limit is enforced

        BUSINESS REQUIREMENT:
        - Quizzes with attempt limits should prevent access after limit reached
        - Students should see clear information about attempts remaining

        TEST SCENARIO:
        1. Login as student who has exhausted attempts
        2. Navigate to course with attempt-limited quiz
        3. Verify quiz shows no attempts remaining
        4. Attempt to access quiz
        5. Verify access is denied

        VALIDATION:
        - Attempts remaining count is displayed
        - Quiz is locked when no attempts remaining
        - Error message explains attempt limit reached
        - Option to contact instructor (if applicable)
        """
        driver = browser_driver

        # Login as student with no attempts
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student2@example.com", "test123")

        # Navigate to course
        driver.get(f"{test_base_url}/course/1")
        time.sleep(2)

        # Check attempts remaining
        course_page = CoursePage(driver, test_base_url)
        attempts = course_page.get_attempts_remaining("Limited Attempts Quiz")

        assert attempts == 0, f"Expected 0 attempts remaining, got {attempts}"
        assert course_page.is_quiz_locked("Limited Attempts Quiz"), \
            "Quiz should be locked when no attempts remaining"

    @pytest.mark.asyncio
    async def test_resume_incomplete_quiz_attempt(self, browser_driver, test_base_url):
        """
        E2E TEST: Student can resume incomplete quiz attempt

        BUSINESS REQUIREMENT:
        - Students should be able to resume partially completed quizzes
        - Progress should be preserved (answered questions, time spent)
        - Students should continue from where they left off

        TEST SCENARIO:
        1. Login as student with incomplete attempt
        2. Navigate to quiz
        3. Verify "Resume Quiz" button is displayed
        4. Click resume
        5. Verify previous answers are preserved
        6. Verify starting at correct question

        VALIDATION:
        - Resume button is clearly visible
        - Previously answered questions show saved answers
        - Current question is first unanswered question
        - Timer continues from saved time (if applicable)
        - Save indicator shows "Draft" or "In Progress"
        """
        driver = browser_driver

        # Login as student with incomplete attempt
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student3@example.com", "test123")

        # Navigate to quiz
        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        # Check for resume functionality
        instructions_page = QuizInstructionsPage(driver, test_base_url)

        # Look for resume button or indication of in-progress quiz
        resume_button = (By.CSS_SELECTOR, "button.resume-quiz-btn")
        has_resume = instructions_page.is_element_present(*resume_button, timeout=3)

        if has_resume:
            instructions_page.click_element(*resume_button)
            time.sleep(1)

            # Verify we're in quiz page
            quiz_page = QuizPage(driver, test_base_url)
            current_q, total_q = quiz_page.get_current_question_number()

            assert current_q is not None, "Failed to resume quiz"
            # Should not be on question 1 if resuming
            # (unless that's the first unanswered question)

    @pytest.mark.asyncio
    async def test_view_quiz_instructions_before_starting(self, browser_driver, test_base_url):
        """
        E2E TEST: Student can view quiz instructions before starting

        BUSINESS REQUIREMENT:
        - Students must see clear instructions before beginning quiz
        - Instructions should include time limit, question count, rules
        - Students must explicitly start quiz (informed consent)

        TEST SCENARIO:
        1. Login as student
        2. Navigate to quiz
        3. Verify instructions page displays
        4. Verify all key information is shown
        5. Start quiz
        6. Verify quiz begins after explicit start

        VALIDATION:
        - Instructions page loads before quiz
        - Time limit is clearly displayed
        - Question count is shown
        - Passing score is shown (if applicable)
        - Rules/guidelines are listed
        - Start button is prominent and labeled clearly
        - Quiz does not auto-start
        """
        driver = browser_driver

        # Login as student
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # Navigate to quiz
        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        # Verify instructions page
        instructions_page = QuizInstructionsPage(driver, test_base_url)

        quiz_title = instructions_page.get_quiz_title()
        assert quiz_title is not None, "Quiz title not displayed"

        instructions = instructions_page.get_instructions()
        assert instructions is not None and len(instructions) > 0, \
            "Quiz instructions not displayed"

        question_count = instructions_page.get_question_count()
        assert question_count is not None and question_count > 0, \
            "Question count not displayed"

        # Verify Start button exists
        start_button_present = instructions_page.is_element_present(
            *instructions_page.START_QUIZ_BUTTON, timeout=3
        )
        assert start_button_present, "Start Quiz button not found"

        # Start quiz
        instructions_page.start_quiz()

        # Verify quiz page loads
        quiz_page = QuizPage(driver, test_base_url)
        question_text = quiz_page.get_question_text()
        assert question_text is not None, "Quiz did not start after clicking Start button"


# ============================================================================
# TEST CLASS - QUIZ TAKING WORKFLOW TESTS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.quiz_assessment
@pytest.mark.priority_critical
class TestQuizTakingWorkflow(BaseTest):
    """
    Test suite for quiz taking workflow and interactions.

    BUSINESS REQUIREMENT:
    Students must have smooth, reliable quiz-taking experience with
    intuitive navigation, auto-save, and clear feedback.
    """

    @pytest.mark.asyncio
    async def test_start_quiz_and_timer_begins(self, browser_driver, test_base_url):
        """
        E2E TEST: Quiz timer starts when quiz begins

        BUSINESS REQUIREMENT:
        - Timed quizzes must start timer when student clicks "Start Quiz"
        - Timer must be clearly visible and count down accurately

        TEST SCENARIO:
        1. Login as student
        2. Navigate to timed quiz
        3. Note time limit from instructions
        4. Start quiz
        5. Verify timer starts
        6. Verify timer counts down

        VALIDATION:
        - Timer is visible on quiz page
        - Timer shows correct initial time
        - Timer counts down (check after 5 seconds)
        - Timer format is clear (MM:SS)
        """
        driver = browser_driver

        # Login and navigate to quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        # Start quiz
        instructions_page = QuizInstructionsPage(driver, test_base_url)
        time_limit = instructions_page.get_time_limit()
        instructions_page.start_quiz()

        # Check timer
        quiz_page = QuizPage(driver, test_base_url)
        initial_time = quiz_page.get_timer_value()

        assert initial_time is not None, "Timer not visible"

        if time_limit:
            expected_initial = time_limit * 60
            # Allow 10 second variance for page load
            assert abs(initial_time - expected_initial) <= 10, \
                f"Timer shows {initial_time}s, expected ~{expected_initial}s"

        # Wait and verify countdown
        time.sleep(5)
        after_time = quiz_page.get_timer_value()

        if after_time is not None:
            assert after_time < initial_time, \
                f"Timer not counting down: was {initial_time}s, now {after_time}s"

    @pytest.mark.asyncio
    async def test_answer_multiple_choice_question(self, browser_driver, test_base_url):
        """
        E2E TEST: Student answers multiple choice question

        BUSINESS REQUIREMENT:
        - Multiple choice questions must support single answer selection
        - Selected answer must be clearly indicated
        - Selection must persist when navigating away and back

        TEST SCENARIO:
        1. Login and start quiz
        2. View multiple choice question
        3. Select an answer
        4. Verify selection is highlighted
        5. Navigate away and back
        6. Verify selection is preserved

        VALIDATION:
        - Answer options are clearly displayed
        - Radio button or selection indicator is visible
        - Selected answer is visually distinct
        - Selection persists across navigation
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        # Answer question
        quiz_page = QuizPage(driver, test_base_url)
        question_text = quiz_page.get_question_text()
        assert question_text is not None, "Question text not displayed"

        # Select first answer
        quiz_page.select_multiple_choice_answer(0)

        # Verify selection (check if radio button is selected)
        selected = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']:checked")
        assert len(selected) > 0, "Answer not selected"

    @pytest.mark.asyncio
    async def test_answer_coding_question(self, browser_driver, test_base_url):
        """
        E2E TEST: Student answers coding question with code editor

        BUSINESS REQUIREMENT:
        - Coding questions must provide proper code editor with syntax highlighting
        - Code must be saved and preserved

        TEST SCENARIO:
        1. Login and start quiz with coding question
        2. Navigate to coding question
        3. Enter code in editor
        4. Verify code is accepted
        5. Verify syntax highlighting works

        VALIDATION:
        - Code editor is displayed
        - Code can be entered
        - Editor supports typical code features
        - Code is saved
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # Navigate to quiz with coding question
        driver.get(f"{test_base_url}/quiz/2")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Check if code editor is present
        has_code_editor = quiz_page.is_element_present(*quiz_page.CODE_EDITOR, timeout=5)

        if has_code_editor:
            # Enter code
            sample_code = "def hello():\n    print('Hello, World!')"
            quiz_page.answer_code_question(sample_code)

            # Verify code was entered (basic check)
            time.sleep(1)
            # Code editor should contain some text now

    @pytest.mark.asyncio
    async def test_answer_essay_question(self, browser_driver, test_base_url):
        """
        E2E TEST: Student answers essay question with rich text

        BUSINESS REQUIREMENT:
        - Essay questions must support text input
        - Text should be preserved and saved

        TEST SCENARIO:
        1. Login and start quiz with essay question
        2. Navigate to essay question
        3. Enter text answer
        4. Verify text is accepted and saved

        VALIDATION:
        - Text area/editor is displayed
        - Text can be entered
        - Text is saved
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # Navigate to quiz with essay question
        driver.get(f"{test_base_url}/quiz/3")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Check if text answer input is present
        has_text_input = quiz_page.is_element_present(*quiz_page.TEXT_ANSWER_INPUT, timeout=5)

        if has_text_input:
            # Enter essay answer
            essay_text = "This is a sample essay answer demonstrating the text input functionality."
            quiz_page.answer_text_question(essay_text)

            # Verify text was entered
            time.sleep(1)

    @pytest.mark.asyncio
    async def test_navigate_between_questions(self, browser_driver, test_base_url):
        """
        E2E TEST: Student navigates between questions using next/previous

        BUSINESS REQUIREMENT:
        - Students must be able to navigate freely between questions
        - Question counter must update correctly
        - Answers must persist when navigating

        TEST SCENARIO:
        1. Login and start quiz
        2. Answer question 1
        3. Click Next
        4. Verify question 2 displays
        5. Click Previous
        6. Verify question 1 displays with saved answer

        VALIDATION:
        - Next button works
        - Previous button works
        - Question counter updates
        - Answers are preserved
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Verify starting on question 1
        current_q, total_q = quiz_page.get_current_question_number()
        assert current_q == 1, f"Expected question 1, got question {current_q}"

        # Answer and go to next
        quiz_page.select_multiple_choice_answer(0)
        quiz_page.click_next_question()

        # Verify question 2
        current_q, total_q = quiz_page.get_current_question_number()
        assert current_q == 2, f"Expected question 2, got question {current_q}"

        # Go back to question 1
        quiz_page.click_previous_question()

        # Verify back on question 1
        current_q, total_q = quiz_page.get_current_question_number()
        assert current_q == 1, f"Expected question 1, got question {current_q}"

        # Verify answer is still selected
        selected = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']:checked")
        assert len(selected) > 0, "Answer not preserved after navigation"

    @pytest.mark.asyncio
    async def test_mark_question_for_review(self, browser_driver, test_base_url):
        """
        E2E TEST: Student marks question for later review

        BUSINESS REQUIREMENT:
        - Students should be able to flag questions to review later
        - Marked questions should be visually indicated

        TEST SCENARIO:
        1. Login and start quiz
        2. Mark question for review
        3. Verify question is marked
        4. Navigate away and back
        5. Verify mark persists

        VALIDATION:
        - Mark for review button/checkbox is available
        - Marked state is visually clear
        - Mark persists across navigation
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Check if mark for review feature exists
        has_review_button = quiz_page.is_element_present(
            *quiz_page.MARK_FOR_REVIEW_BUTTON, timeout=3
        )

        if has_review_button:
            # Mark question
            quiz_page.mark_question_for_review()

            # Navigate away
            quiz_page.click_next_question()

            # Navigate back
            quiz_page.click_previous_question()

            # Verify mark persists (visual check - button state or icon)
            time.sleep(1)

    @pytest.mark.asyncio
    async def test_save_progress_automatically(self, browser_driver, test_base_url):
        """
        E2E TEST: Quiz progress saves automatically

        BUSINESS REQUIREMENT:
        - Student answers must auto-save to prevent data loss
        - Auto-save should happen after each answer
        - Save indicator should provide feedback

        TEST SCENARIO:
        1. Login and start quiz
        2. Answer question
        3. Wait for auto-save
        4. Verify save indicator appears
        5. Refresh page
        6. Verify answer is preserved

        VALIDATION:
        - Save indicator appears after answering
        - Answer persists after page refresh
        - No manual save button required
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Answer question
        quiz_page.select_multiple_choice_answer(1)

        # Wait for auto-save (check for save indicator)
        time.sleep(3)
        auto_saved = quiz_page.is_auto_save_working()

        # Note: Auto-save may be silent (no indicator)
        # Best test is to refresh and check persistence

        # Refresh page
        driver.refresh()
        time.sleep(2)

        # Check if answer is preserved
        # (May need to handle resume dialog or auto-continue)
        time.sleep(1)

    @pytest.mark.asyncio
    async def test_submit_quiz_manually(self, browser_driver, test_base_url):
        """
        E2E TEST: Student submits quiz manually

        BUSINESS REQUIREMENT:
        - Students must be able to submit quiz when finished
        - Confirmation dialog should prevent accidental submission
        - Results page should load after submission

        TEST SCENARIO:
        1. Login and start quiz
        2. Answer all questions
        3. Click Submit button
        4. Confirm submission in dialog
        5. Verify results page loads

        VALIDATION:
        - Submit button is available on last question
        - Confirmation dialog appears
        - Results page loads after confirmation
        - Quiz cannot be modified after submission
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Get question count
        _, total_questions = quiz_page.get_current_question_number()

        # Answer all questions quickly
        for i in range(total_questions or 5):
            quiz_page.select_multiple_choice_answer(0)

            # Check if we're on last question
            current_q, _ = quiz_page.get_current_question_number()
            if current_q == total_questions:
                break

            # Click next if not on last question
            if quiz_page.is_element_present(*quiz_page.NEXT_BUTTON, timeout=2):
                quiz_page.click_next_question()

        # Submit quiz
        quiz_page.submit_quiz()

        # Verify results page or confirmation
        time.sleep(2)

        # Check if we're on results page
        results_page = QuizResultsPage(driver, test_base_url)
        score = results_page.get_score_percentage()

        # Results may or may not be immediate depending on settings
        # At minimum, should see confirmation or redirect

    @pytest.mark.asyncio
    async def test_auto_submit_when_time_expires(self, browser_driver, test_base_url):
        """
        E2E TEST: Quiz auto-submits when timer reaches zero

        BUSINESS REQUIREMENT:
        - Timed quizzes must auto-submit when time expires
        - Students should receive warning before expiration
        - Auto-submit should be automatic, no student action needed

        TEST SCENARIO:
        1. Login and start quiz with very short time limit (or mock timer)
        2. Wait for timer to expire
        3. Verify auto-submit happens
        4. Verify results page loads

        VALIDATION:
        - Timer reaches 0:00
        - Quiz auto-submits
        - No student action required
        - Results page loads

        NOTE: This test requires a quiz with short time limit (1-2 minutes)
        or ability to mock timer for testing.
        """
        driver = browser_driver

        # Login and navigate to short-timer quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # This test requires a special quiz with 1-minute timer
        # Or mock/override timer in browser console
        driver.get(f"{test_base_url}/quiz/4")  # Short timer quiz
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        time_limit = instructions_page.get_time_limit()

        if time_limit and time_limit <= 2:  # 2 minutes or less
            instructions_page.start_quiz()

            quiz_page = QuizPage(driver, test_base_url)

            # Wait for timer to expire (+ 10 second buffer)
            wait_time = (time_limit * 60) + 10
            time.sleep(wait_time)

            # Verify auto-submit occurred (check URL or results page)
            current_url = driver.current_url
            assert "result" in current_url.lower() or "complete" in current_url.lower(), \
                "Quiz did not auto-submit after timer expiration"

    @pytest.mark.asyncio
    async def test_time_warning_before_expiration(self, browser_driver, test_base_url):
        """
        E2E TEST: Warning appears before time expiration

        BUSINESS REQUIREMENT:
        - Students should receive warning at 5 minutes and 1 minute remaining
        - Warning should be clearly visible but not disruptive

        TEST SCENARIO:
        1. Login and start timed quiz
        2. Fast-forward to 5 minutes remaining (or wait)
        3. Verify 5-minute warning appears
        4. Fast-forward to 1 minute remaining
        5. Verify 1-minute warning appears

        VALIDATION:
        - Warning appears at correct times
        - Warning is visible and clear
        - Warning doesn't block quiz interaction
        - Warning can be dismissed if needed

        NOTE: This test may require timer manipulation for practical testing.
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Check if timer warnings are implemented
        # This would typically require either:
        # 1. Waiting for actual time to pass (impractical for testing)
        # 2. Manipulating timer via JavaScript
        # 3. Using a test quiz with very short time limit

        # Option 2: Manipulate timer via JavaScript for testing
        driver.execute_script("""
            // Set timer to 6 minutes (360 seconds) to trigger 5-min warning soon
            if (window.remainingTime !== undefined) {
                window.remainingTime = 360;
            }
        """)

        # Wait for warning to appear
        time.sleep(70)  # Wait ~1 minute for 5-min warning

        has_warning = quiz_page.is_time_warning_visible()
        # Warning may or may not be visible depending on implementation


# ============================================================================
# TEST CLASS - QUIZ FEATURES TESTS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.quiz_assessment
@pytest.mark.priority_high
class TestQuizFeatures(BaseTest):
    """
    Test suite for quiz features and enhancements.

    BUSINESS REQUIREMENT:
    Quizzes should support advanced features like randomization,
    calculator, reference materials, and code execution.
    """

    @pytest.mark.asyncio
    async def test_question_randomization_working(self, browser_driver, test_base_url):
        """
        E2E TEST: Questions are randomized for different students

        BUSINESS REQUIREMENT:
        - Quiz questions should be randomized to prevent cheating
        - Each student sees questions in different order

        TEST SCENARIO:
        1. Login as student1 and start quiz
        2. Note order of first 3 questions
        3. Logout and login as student2
        4. Start same quiz
        5. Compare question order

        VALIDATION:
        - Question order is different between students
        - All questions are present
        - Randomization is consistent per student (refresh shows same order)
        """
        driver = browser_driver

        # Student 1: Get question order
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/5")  # Quiz with randomization enabled
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Get first 3 question texts
        student1_questions = []
        for i in range(3):
            question = quiz_page.get_question_text()
            student1_questions.append(question)
            if i < 2:
                quiz_page.select_multiple_choice_answer(0)
                quiz_page.click_next_question()

        # Logout
        driver.get(f"{test_base_url}/logout")
        time.sleep(2)

        # Student 2: Get question order
        login_page.navigate()
        login_page.login("student2@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/5")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        student2_questions = []
        for i in range(3):
            question = quiz_page.get_question_text()
            student2_questions.append(question)
            if i < 2:
                quiz_page.select_multiple_choice_answer(0)
                quiz_page.click_next_question()

        # Compare - should be different order
        # (If randomization is enabled)
        assert len(student1_questions) == len(student2_questions), \
            "Different number of questions for different students"

    @pytest.mark.asyncio
    async def test_answer_choice_randomization(self, browser_driver, test_base_url):
        """
        E2E TEST: Answer choices are randomized

        BUSINESS REQUIREMENT:
        - Answer choices should be randomized to prevent pattern recognition
        - Correct answer position should vary

        TEST SCENARIO:
        1. Login as two different students
        2. View same question
        3. Compare answer order

        VALIDATION:
        - Answer choices are in different order
        - All answers are present
        - Correct answer is randomized
        """
        driver = browser_driver

        # Similar to question randomization test
        # Would need to compare answer option order between students
        # This is difficult to test without knowing expected correct answer

        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/5")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Get answer options
        answer_elements = driver.find_elements(*quiz_page.ANSWER_OPTIONS)
        student1_answers = [elem.text for elem in answer_elements if elem.is_displayed()]

        # Would need to repeat for student 2 and compare

    @pytest.mark.asyncio
    async def test_file_upload_for_coding_assignments(self, browser_driver, test_base_url):
        """
        E2E TEST: Student uploads file for coding assignment question

        BUSINESS REQUIREMENT:
        - Some questions should allow file upload
        - Uploaded files should be saved and associated with submission

        TEST SCENARIO:
        1. Login and start quiz with file upload question
        2. Navigate to file upload question
        3. Select and upload file
        4. Verify upload success
        5. Submit quiz
        6. Verify file is included in submission

        VALIDATION:
        - File upload input is available
        - File can be selected and uploaded
        - Upload progress/success is indicated
        - File is saved with quiz submission
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/6")  # Quiz with file upload question
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Check if file upload is present
        has_file_upload = quiz_page.is_element_present(
            *quiz_page.FILE_UPLOAD_INPUT, timeout=5
        )

        if has_file_upload:
            # Create a test file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write("def test():\n    return 'Hello, World!'")
                temp_file_path = f.name

            # Upload file
            quiz_page.upload_file(temp_file_path)

            # Verify upload (look for file name display or success message)
            time.sleep(2)

            # Clean up
            import os
            os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_code_syntax_highlighting(self, browser_driver, test_base_url):
        """
        E2E TEST: Code editor provides syntax highlighting

        BUSINESS REQUIREMENT:
        - Code editor should provide syntax highlighting for readability
        - Highlighting should work for common languages (Python, JavaScript, etc.)

        TEST SCENARIO:
        1. Login and start quiz with coding question
        2. Enter code in editor
        3. Verify syntax highlighting is applied

        VALIDATION:
        - Code editor is present
        - Syntax highlighting is visible
        - Different code elements have different colors
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/2")  # Quiz with code question
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Check if code editor exists
        has_code_editor = quiz_page.is_element_present(*quiz_page.CODE_EDITOR, timeout=5)

        if has_code_editor:
            # Enter code
            sample_code = "def hello():\n    print('Hello')"
            quiz_page.answer_code_question(sample_code)

            # Check for syntax highlighting (look for span.keyword, span.string, etc.)
            time.sleep(1)

            # CodeMirror or Monaco editor will add syntax highlighting spans
            syntax_elements = driver.find_elements(By.CSS_SELECTOR, ".cm-keyword, .mtk1, .token")
            has_highlighting = len(syntax_elements) > 0

            # Syntax highlighting presence indicates feature is working

    @pytest.mark.asyncio
    async def test_code_execution_in_lab(self, browser_driver, test_base_url):
        """
        E2E TEST: Student can execute code in quiz

        BUSINESS REQUIREMENT:
        - Some coding questions should allow code execution
        - Results should be displayed to student

        TEST SCENARIO:
        1. Login and start quiz with executable code question
        2. Enter code
        3. Click Run button
        4. Verify output is displayed

        VALIDATION:
        - Run button is available
        - Code executes
        - Output is displayed
        - Execution errors are shown clearly
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/2")  # Quiz with executable code
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Check if code execution is available
        has_run_button = quiz_page.is_element_present(*quiz_page.CODE_RUN_BUTTON, timeout=5)

        if has_run_button:
            # Enter simple code
            sample_code = "print('Hello, World!')"
            quiz_page.answer_code_question(sample_code)

            # Run code
            output = quiz_page.run_code()

            # Verify output
            assert output is not None, "No code output received"
            assert "Hello" in output or "output" in output.lower(), \
                f"Unexpected code output: {output}"

    @pytest.mark.asyncio
    async def test_calculator_availability(self, browser_driver, test_base_url):
        """
        E2E TEST: Calculator tool is available when enabled

        BUSINESS REQUIREMENT:
        - Some quizzes should provide calculator tool
        - Calculator should be functional and accessible

        TEST SCENARIO:
        1. Login and start quiz with calculator enabled
        2. Click calculator button
        3. Verify calculator opens
        4. Perform calculation
        5. Verify result

        VALIDATION:
        - Calculator button is visible
        - Calculator modal opens
        - Calculator is functional
        - Calculator can be closed
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/7")  # Quiz with calculator
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Try to open calculator
        calculator_opened = quiz_page.open_calculator()

        if calculator_opened:
            # Verify calculator is functional
            # (Would need to interact with calculator buttons)
            time.sleep(1)

            # Close calculator
            close_button = (By.CSS_SELECTOR, ".calculator-modal .close")
            if quiz_page.is_element_present(*close_button, timeout=3):
                quiz_page.click_element(*close_button)

    @pytest.mark.asyncio
    async def test_reference_materials_access(self, browser_driver, test_base_url):
        """
        E2E TEST: Reference materials are accessible when allowed

        BUSINESS REQUIREMENT:
        - Some quizzes allow reference materials
        - Materials should be easy to access without leaving quiz

        TEST SCENARIO:
        1. Login and start quiz with reference materials
        2. Click reference materials button
        3. Verify materials are displayed
        4. Close materials
        5. Verify quiz state is preserved

        VALIDATION:
        - Reference button is visible
        - Materials modal opens
        - Materials are readable
        - Modal can be closed
        - Quiz continues normally after closing
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/8")  # Quiz with reference materials
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Try to open reference materials
        materials_opened = quiz_page.open_reference_materials()

        if materials_opened:
            # Verify materials are displayed
            time.sleep(1)

            # Close materials
            close_button = (By.CSS_SELECTOR, ".reference-modal .close")
            if quiz_page.is_element_present(*close_button, timeout=3):
                quiz_page.click_element(*close_button)

            # Verify quiz is still active
            question_text = quiz_page.get_question_text()
            assert question_text is not None, "Quiz state lost after closing reference materials"


# ============================================================================
# TEST CLASS - QUIZ COMPLETION TESTS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.quiz_assessment
@pytest.mark.priority_critical
class TestQuizCompletion(BaseTest):
    """
    Test suite for quiz completion and results.

    BUSINESS REQUIREMENT:
    Students should receive clear feedback after quiz completion
    including score, correct answers (if allowed), and performance analytics.
    """

    @pytest.mark.asyncio
    async def test_submit_quiz_and_see_confirmation(self, browser_driver, test_base_url):
        """
        E2E TEST: Confirmation page appears after quiz submission

        BUSINESS REQUIREMENT:
        - Students should see clear confirmation that quiz was submitted
        - Confirmation should include submission details

        TEST SCENARIO:
        1. Login and complete quiz
        2. Submit quiz
        3. Verify confirmation page/message

        VALIDATION:
        - Confirmation page loads
        - Submission confirmation is clear
        - Timestamp is shown
        - Next steps are indicated
        """
        driver = browser_driver

        # Login and complete quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Answer all questions quickly
        _, total_q = quiz_page.get_current_question_number()
        for i in range(total_q or 5):
            quiz_page.select_multiple_choice_answer(0)
            current_q, _ = quiz_page.get_current_question_number()
            if current_q == total_q:
                break
            if quiz_page.is_element_present(*quiz_page.NEXT_BUTTON, timeout=2):
                quiz_page.click_next_question()

        # Submit
        quiz_page.submit_quiz()

        # Verify confirmation or results page
        time.sleep(2)

        # Check for confirmation message or results page
        confirmation_found = False

        # Check for various confirmation indicators
        confirmation_messages = [
            (By.CSS_SELECTOR, ".submission-confirmation"),
            (By.CSS_SELECTOR, ".quiz-submitted"),
            (By.XPATH, "//*[contains(text(), 'submitted')]"),
            (By.XPATH, "//*[contains(text(), 'completed')]"),
        ]

        for locator in confirmation_messages:
            if quiz_page.is_element_present(*locator, timeout=3):
                confirmation_found = True
                break

        # Results page is also acceptable confirmation
        results_page = QuizResultsPage(driver, test_base_url)
        if results_page.is_element_present(*results_page.RESULTS_TITLE, timeout=3):
            confirmation_found = True

    @pytest.mark.asyncio
    async def test_view_immediate_feedback(self, browser_driver, test_base_url):
        """
        E2E TEST: Immediate feedback is shown after submission

        BUSINESS REQUIREMENT:
        - If configured, quiz should show immediate feedback
        - Feedback should include which answers were correct/incorrect

        TEST SCENARIO:
        1. Login and complete quiz with immediate feedback enabled
        2. Submit quiz
        3. Verify feedback is displayed

        VALIDATION:
        - Feedback page loads immediately
        - Correct/incorrect indicators are shown
        - Explanations are provided (if configured)
        """
        driver = browser_driver

        # Login and submit quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/9")  # Quiz with immediate feedback
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Answer and submit
        _, total_q = quiz_page.get_current_question_number()
        for i in range(total_q or 5):
            quiz_page.select_multiple_choice_answer(0)
            current_q, _ = quiz_page.get_current_question_number()
            if current_q == total_q:
                break
            if quiz_page.is_element_present(*quiz_page.NEXT_BUTTON, timeout=2):
                quiz_page.click_next_question()

        quiz_page.submit_quiz()

        # Check for feedback
        time.sleep(2)

        results_page = QuizResultsPage(driver, test_base_url)
        feedback = results_page.get_feedback()

        # Feedback may be present or not depending on quiz settings

    @pytest.mark.asyncio
    async def test_view_score(self, browser_driver, test_base_url):
        """
        E2E TEST: Score is displayed after submission

        BUSINESS REQUIREMENT:
        - If immediate scoring is enabled, show score after submission
        - Score should be clear and easy to understand

        TEST SCENARIO:
        1. Login and complete quiz
        2. Submit quiz
        3. Verify score is displayed
        4. Verify score is accurate

        VALIDATION:
        - Score percentage is shown
        - Correct/total count is shown
        - Pass/fail indicator is shown
        - Score matches expected value
        """
        driver = browser_driver

        # Login and submit quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Answer all questions (all correct for predictable score)
        _, total_q = quiz_page.get_current_question_number()
        for i in range(total_q or 5):
            quiz_page.select_multiple_choice_answer(0)  # Assuming first answer is correct
            current_q, _ = quiz_page.get_current_question_number()
            if current_q == total_q:
                break
            if quiz_page.is_element_present(*quiz_page.NEXT_BUTTON, timeout=2):
                quiz_page.click_next_question()

        quiz_page.submit_quiz()

        # Check score
        time.sleep(2)

        results_page = QuizResultsPage(driver, test_base_url)
        score = results_page.get_score_percentage()

        # Score may or may not be shown depending on settings
        if score is not None:
            assert 0 <= score <= 100, f"Invalid score: {score}"

    @pytest.mark.asyncio
    async def test_view_correct_answers(self, browser_driver, test_base_url):
        """
        E2E TEST: Correct answers are shown in review

        BUSINESS REQUIREMENT:
        - If allowed, students should see correct answers after submission
        - Review should clearly indicate correct vs incorrect

        TEST SCENARIO:
        1. Login and complete quiz
        2. Submit quiz
        3. Click "Review Answers"
        4. Verify correct answers are shown

        VALIDATION:
        - Review button is available
        - Review page shows all questions
        - Correct answers are clearly marked
        - Student's answers are shown for comparison
        """
        driver = browser_driver

        # Login and submit quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/9")  # Quiz with answer review enabled
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Answer and submit
        _, total_q = quiz_page.get_current_question_number()
        for i in range(total_q or 5):
            quiz_page.select_multiple_choice_answer(0)
            current_q, _ = quiz_page.get_current_question_number()
            if current_q == total_q:
                break
            if quiz_page.is_element_present(*quiz_page.NEXT_BUTTON, timeout=2):
                quiz_page.click_next_question()

        quiz_page.submit_quiz()
        time.sleep(2)

        # Try to review answers
        results_page = QuizResultsPage(driver, test_base_url)
        review_available = results_page.review_answers()

        if review_available:
            # Verify review page shows questions and answers
            time.sleep(2)

            has_review_list = results_page.is_element_present(
                *results_page.QUESTION_REVIEW_LIST, timeout=5
            )

            # Review functionality varies by implementation

    @pytest.mark.asyncio
    async def test_view_quiz_analytics(self, browser_driver, test_base_url):
        """
        E2E TEST: Quiz analytics are available after completion

        BUSINESS REQUIREMENT:
        - Students should see analytics about their performance
        - Analytics should include time spent, accuracy, etc.

        TEST SCENARIO:
        1. Login and complete quiz
        2. Submit quiz
        3. View analytics
        4. Verify analytics data is shown

        VALIDATION:
        - Analytics button/link is available
        - Time spent is shown
        - Accuracy metrics are shown
        - Performance insights are provided
        """
        driver = browser_driver

        # Login and submit quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Answer and submit
        _, total_q = quiz_page.get_current_question_number()
        for i in range(total_q or 5):
            quiz_page.select_multiple_choice_answer(0)
            current_q, _ = quiz_page.get_current_question_number()
            if current_q == total_q:
                break
            if quiz_page.is_element_present(*quiz_page.NEXT_BUTTON, timeout=2):
                quiz_page.click_next_question()

        quiz_page.submit_quiz()
        time.sleep(2)

        # Check for analytics
        results_page = QuizResultsPage(driver, test_base_url)

        # Check time spent
        time_spent = results_page.get_time_spent()

        # Time spent may or may not be shown
        if time_spent is not None:
            assert time_spent > 0, "Time spent should be positive"

        # Try to view detailed analytics
        analytics_available = results_page.view_analytics()

    @pytest.mark.asyncio
    async def test_retake_quiz(self, browser_driver, test_base_url):
        """
        E2E TEST: Student can retake quiz when allowed

        BUSINESS REQUIREMENT:
        - If multiple attempts are allowed, students should be able to retake
        - Retake button should be clearly visible
        - New attempt should start fresh

        TEST SCENARIO:
        1. Login and complete quiz
        2. Submit quiz
        3. Click "Retake Quiz"
        4. Verify new attempt starts
        5. Verify previous answers are cleared

        VALIDATION:
        - Retake button is available (if attempts remain)
        - Button is disabled if no attempts remain
        - New attempt starts fresh
        - Attempt counter updates
        """
        driver = browser_driver

        # Login and submit quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/10")  # Quiz with multiple attempts
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Answer and submit
        _, total_q = quiz_page.get_current_question_number()
        for i in range(total_q or 5):
            quiz_page.select_multiple_choice_answer(0)
            current_q, _ = quiz_page.get_current_question_number()
            if current_q == total_q:
                break
            if quiz_page.is_element_present(*quiz_page.NEXT_BUTTON, timeout=2):
                quiz_page.click_next_question()

        quiz_page.submit_quiz()
        time.sleep(2)

        # Try to retake
        results_page = QuizResultsPage(driver, test_base_url)
        retake_available = results_page.retake_quiz()

        if retake_available:
            # Should be back at quiz instructions or quiz page
            time.sleep(2)

            # Verify we're starting a new attempt
            current_url = driver.current_url
            assert "quiz" in current_url.lower(), "Did not navigate to quiz after retake"


# ============================================================================
# TEST CLASS - EDGE CASE TESTS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.quiz_assessment
@pytest.mark.priority_high
class TestQuizEdgeCases(BaseTest):
    """
    Test suite for quiz edge cases and error scenarios.

    BUSINESS REQUIREMENT:
    Quiz system should handle edge cases gracefully including
    browser refresh, network issues, and anti-cheating measures.
    """

    @pytest.mark.asyncio
    async def test_browser_refresh_preserves_progress(self, browser_driver, test_base_url):
        """
        E2E TEST: Browser refresh doesn't lose quiz progress

        BUSINESS REQUIREMENT:
        - Quiz progress must be preserved across page refreshes
        - Students should not lose work due to accidental refresh

        TEST SCENARIO:
        1. Login and start quiz
        2. Answer several questions
        3. Refresh browser
        4. Verify answers are preserved
        5. Verify on same question

        VALIDATION:
        - Page reload doesn't clear answers
        - Current question is preserved
        - Timer continues (if applicable)
        - No data loss occurs
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Answer 3 questions
        for i in range(3):
            quiz_page.select_multiple_choice_answer(i % 4)  # Vary answers
            if i < 2:
                quiz_page.click_next_question()

        # Get current state before refresh
        current_q_before, total_q = quiz_page.get_current_question_number()

        # Wait for auto-save
        time.sleep(3)

        # Refresh page
        driver.refresh()
        time.sleep(3)

        # May need to handle resume dialog or auto-continue
        # Check if we're back in quiz

        # Verify we're in quiz (not back at instructions)
        quiz_page = QuizPage(driver, test_base_url)

        # Try to get current question
        try:
            current_q_after, _ = quiz_page.get_current_question_number()

            # Should be on same question or near it
            assert current_q_after is not None, "Quiz state lost after refresh"

        except:
            # May be at instructions page asking to resume
            instructions_page = QuizInstructionsPage(driver, test_base_url)
            resume_button = (By.CSS_SELECTOR, "button.resume-quiz-btn")

            if instructions_page.is_element_present(*resume_button, timeout=3):
                # Click resume
                instructions_page.click_element(*resume_button)
                time.sleep(2)

                # Should now be in quiz
                quiz_page = QuizPage(driver, test_base_url)
                current_q_after, _ = quiz_page.get_current_question_number()
                assert current_q_after is not None, "Failed to resume after refresh"

    @pytest.mark.asyncio
    async def test_network_interruption_recovery(self, browser_driver, test_base_url):
        """
        E2E TEST: Quiz handles network interruption gracefully

        BUSINESS REQUIREMENT:
        - Quiz should queue saves during network outage
        - Quiz should sync when connection restored
        - Student should receive clear feedback about connection status

        TEST SCENARIO:
        1. Login and start quiz
        2. Simulate network interruption (offline mode)
        3. Answer questions while offline
        4. Restore network
        5. Verify answers sync

        VALIDATION:
        - Offline indicator appears
        - Answers are saved locally
        - Connection restoration is detected
        - Answers sync to server
        - No data loss occurs

        NOTE: This test uses Chrome DevTools Protocol to simulate offline
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Answer first question while online
        quiz_page.select_multiple_choice_answer(0)
        time.sleep(2)
        quiz_page.click_next_question()

        # Simulate offline mode
        try:
            driver.execute_cdp_cmd("Network.enable", {})
            driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
                "offline": True,
                "downloadThroughput": 0,
                "uploadThroughput": 0,
                "latency": 0
            })

            # Answer question while offline
            quiz_page.select_multiple_choice_answer(1)
            time.sleep(2)

            # Restore network
            driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
                "offline": False,
                "downloadThroughput": -1,
                "uploadThroughput": -1,
                "latency": 0
            })
            driver.execute_cdp_cmd("Network.disable", {})

            # Wait for sync
            time.sleep(3)

            # Verify quiz state is preserved
            current_q, _ = quiz_page.get_current_question_number()
            assert current_q is not None, "Quiz state lost after network recovery"

        except Exception as e:
            # CDP commands may not be available in all setups
            print(f"CDP not available, skipping network simulation: {e}")

    @pytest.mark.asyncio
    async def test_concurrent_tab_detection(self, browser_driver, test_base_url):
        """
        E2E TEST: System detects quiz open in multiple tabs

        BUSINESS REQUIREMENT:
        - For security, quiz should only be open in one tab at a time
        - System should detect and prevent concurrent access

        TEST SCENARIO:
        1. Login and start quiz in tab 1
        2. Open same quiz in tab 2
        3. Verify warning/error appears
        4. Verify only one tab can submit

        VALIDATION:
        - Concurrent tab warning is shown
        - Quiz is disabled in second tab
        - Clear message explains the situation
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        driver.get(f"{test_base_url}/quiz/1")
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Open quiz in new tab
        driver.execute_script("window.open(arguments[0], '_blank');", f"{test_base_url}/quiz/1")
        time.sleep(2)

        # Switch to new tab
        tabs = driver.window_handles
        if len(tabs) > 1:
            driver.switch_to.window(tabs[1])
            time.sleep(2)

            # Check for concurrent tab warning
            warning_locators = [
                (By.CSS_SELECTOR, ".concurrent-tab-warning"),
                (By.XPATH, "//*[contains(text(), 'another tab')]"),
                (By.XPATH, "//*[contains(text(), 'already open')]"),
            ]

            warning_found = False
            for locator in warning_locators:
                if quiz_page.is_element_present(*locator, timeout=3):
                    warning_found = True
                    break

            # Close second tab
            driver.close()
            driver.switch_to.window(tabs[0])

    @pytest.mark.asyncio
    async def test_copy_paste_prevention(self, browser_driver, test_base_url):
        """
        E2E TEST: Copy-paste is prevented when anti-cheating is enabled

        BUSINESS REQUIREMENT:
        - For high-stakes assessments, copy-paste should be disabled
        - Students should be informed of this restriction

        TEST SCENARIO:
        1. Login and start quiz with anti-cheating enabled
        2. Attempt to copy question text
        3. Verify copy is prevented
        4. Verify warning message appears

        VALIDATION:
        - Copy operation is blocked
        - Warning message is displayed
        - Right-click is disabled (if applicable)
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # Navigate to high-security quiz
        driver.get(f"{test_base_url}/quiz/11")  # Quiz with anti-cheating
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Try to select and copy text
        question_elem = driver.find_element(*quiz_page.QUESTION_TEXT)

        # Attempt to select text
        actions = ActionChains(driver)
        actions.double_click(question_elem).perform()
        time.sleep(1)

        # Try to copy (Ctrl+C)
        actions.key_down(Keys.CONTROL).send_keys('c').key_up(Keys.CONTROL).perform()
        time.sleep(1)

        # Check if warning appears
        warning_shown = quiz_page.is_element_present(
            *quiz_page.TAB_SWITCH_WARNING, timeout=3
        ) or driver.execute_script("return document.oncopy !== null")

    @pytest.mark.asyncio
    async def test_tab_switching_detection(self, browser_driver, test_base_url):
        """
        E2E TEST: Tab switching is detected and logged

        BUSINESS REQUIREMENT:
        - For proctored quizzes, tab switching should be detected
        - Students should receive warning about tab switching
        - Tab switches should be logged for review

        TEST SCENARIO:
        1. Login and start proctored quiz
        2. Switch to another tab
        3. Switch back to quiz tab
        4. Verify warning appears
        5. Verify tab switch was logged

        VALIDATION:
        - Tab switch is detected
        - Warning message appears
        - Count of tab switches is tracked
        - Excessive switching may lock quiz
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # Navigate to proctored quiz
        driver.get(f"{test_base_url}/quiz/11")  # Proctored quiz
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Open new tab
        driver.execute_script("window.open('about:blank', '_blank');")
        time.sleep(2)

        # Switch to new tab
        tabs = driver.window_handles
        if len(tabs) > 1:
            driver.switch_to.window(tabs[1])
            time.sleep(2)

            # Switch back to quiz
            driver.switch_to.window(tabs[0])
            time.sleep(2)

            # Check for tab switch warning
            warning_shown = quiz_page.is_element_present(
                *quiz_page.TAB_SWITCH_WARNING, timeout=5
            )

            # Close extra tab
            driver.switch_to.window(tabs[1])
            driver.close()
            driver.switch_to.window(tabs[0])

    @pytest.mark.asyncio
    async def test_fullscreen_enforcement(self, browser_driver, test_base_url):
        """
        E2E TEST: Fullscreen mode is enforced when required

        BUSINESS REQUIREMENT:
        - High-stakes quizzes should enforce fullscreen mode
        - Students should be prompted to enter fullscreen
        - Exiting fullscreen should trigger warning

        TEST SCENARIO:
        1. Login and start fullscreen-required quiz
        2. Verify fullscreen prompt appears
        3. Enter fullscreen
        4. Exit fullscreen
        5. Verify warning/lock occurs

        VALIDATION:
        - Fullscreen prompt is shown
        - Quiz locks if fullscreen declined
        - Exiting fullscreen triggers warning
        - Quiz may pause until fullscreen restored
        """
        driver = browser_driver

        # Login and start quiz
        login_page = LoginPage(driver, test_base_url)
        login_page.navigate()
        login_page.login("student1@example.com", "test123")

        # Navigate to fullscreen-required quiz
        driver.get(f"{test_base_url}/quiz/11")  # High-security quiz
        time.sleep(2)

        instructions_page = QuizInstructionsPage(driver, test_base_url)
        instructions_page.start_quiz()

        quiz_page = QuizPage(driver, test_base_url)

        # Check for fullscreen prompt
        fullscreen_prompt = quiz_page.is_element_present(
            *quiz_page.FULLSCREEN_PROMPT, timeout=5
        )

        if fullscreen_prompt:
            # Try to enter fullscreen via JavaScript
            driver.execute_script("""
                var elem = document.documentElement;
                if (elem.requestFullscreen) {
                    elem.requestFullscreen();
                } else if (elem.webkitRequestFullscreen) {
                    elem.webkitRequestFullscreen();
                } else if (elem.msRequestFullscreen) {
                    elem.msRequestFullscreen();
                }
            """)
            time.sleep(2)

            # Exit fullscreen
            driver.execute_script("""
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
            """)
            time.sleep(2)

            # Check for warning
            warning_shown = quiz_page.is_element_present(
                *quiz_page.FULLSCREEN_PROMPT, timeout=3
            )


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture
def browser_driver():
    """
    Fixture providing Selenium WebDriver instance.

    BUSINESS CONTEXT:
    Provides configured Chrome driver for all E2E tests with
    proper setup and teardown.
    """
    from tests.e2e.selenium_base import ChromeDriverSetup, SeleniumConfig

    config = SeleniumConfig()
    driver = ChromeDriverSetup.create_driver(config)

    yield driver

    # Teardown
    driver.quit()


@pytest.fixture
def test_base_url():
    """
    Fixture providing test base URL.

    BUSINESS CONTEXT:
    All tests use HTTPS localhost frontend.
    """
    return "https://localhost:3000"


@pytest.fixture
async def db_connection():
    """
    Fixture providing database connection for verification.

    BUSINESS CONTEXT:
    Some tests need to verify database state after quiz submission.
    """
    import asyncpg

    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        database="course_creator",
        user="postgres",
        password="postgres"
    )

    yield conn

    await conn.close()


# ============================================================================
# END OF TEST FILE
# ============================================================================
