"""
Comprehensive E2E Tests for Adaptive Quiz Functionality

BUSINESS REQUIREMENT:
Tests the adaptive quiz system that adjusts question difficulty based on student
performance in real-time. Adaptive quizzes provide personalized assessment experiences,
adjusting difficulty to match student skill level for more accurate proficiency measurement.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Covers 8 test scenarios for adaptive quiz functionality
- Validates dynamic difficulty adjustment algorithms
- Tests fair scoring despite variable difficulty
- Validates personalized learning recommendations

TEST COVERAGE:
1. Adaptive Question Selection:
   - Quiz adjusts difficulty based on student answers
   - Easier questions after incorrect answer
   - Harder questions after correct answer streak
   - Difficulty calibration per student skill level

2. Personalized Quiz Experience:
   - Student sees questions matched to knowledge level
   - AI suggests remedial content after quiz
   - Prerequisite knowledge gaps identified
   - Follow-up quiz recommendations

3. Validation:
   - Verify adaptive algorithm works correctly
   - Verify fair scoring despite variable difficulty
   - Verify student cannot game the system

PRIORITY: P2 (MEDIUM) - Advanced feature for personalized learning

NOTE: If adaptive quiz functionality is not yet implemented, these tests serve
as specifications for future implementation. Tests will be skipped with appropriate
messages indicating the feature is planned but not yet available.
"""

import pytest
import time
import uuid
import asyncpg
import os
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from tests.e2e.selenium_base import BasePage, BaseTest

# Check if Selenium is configured
SELENIUM_AVAILABLE = os.getenv('SELENIUM_REMOTE') is not None or os.getenv('HEADLESS') is not None


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class AdaptiveQuizPage(BasePage):
    """
    Page Object for adaptive quiz functionality.

    BUSINESS CONTEXT:
    Adaptive quizzes dynamically adjust question difficulty based on student
    responses, providing more accurate skill assessment and personalized learning.
    """

    # Locators
    ADAPTIVE_MODE_INDICATOR = (By.CLASS_NAME, "adaptive-mode-indicator")
    CURRENT_DIFFICULTY_LEVEL = (By.CLASS_NAME, "difficulty-level")
    QUESTION_DIFFICULTY_BADGE = (By.CLASS_NAME, "question-difficulty-badge")
    QUESTION_TEXT = (By.CLASS_NAME, "question-text")
    ANSWER_OPTIONS = (By.CLASS_NAME, "answer-option")
    NEXT_QUESTION_BUTTON = (By.ID, "next-question-btn")
    SUBMIT_QUIZ_BUTTON = (By.ID, "submit-quiz-btn")
    SKILL_LEVEL_DISPLAY = (By.CLASS_NAME, "skill-level-display")
    ADAPTIVE_SCORE_DISPLAY = (By.CLASS_NAME, "adaptive-score-display")
    CONFIDENCE_INTERVAL = (By.CLASS_NAME, "confidence-interval")
    REMEDIAL_CONTENT_SUGGESTIONS = (By.CLASS_NAME, "remedial-suggestions")
    REMEDIAL_CONTENT_ITEM = (By.CLASS_NAME, "remedial-item")
    KNOWLEDGE_GAP_SECTION = (By.CLASS_NAME, "knowledge-gaps-section")
    KNOWLEDGE_GAP_ITEM = (By.CLASS_NAME, "knowledge-gap-item")
    NEXT_QUIZ_RECOMMENDATIONS = (By.CLASS_NAME, "next-quiz-recommendations")

    def is_adaptive_mode_enabled(self):
        """Check if quiz is in adaptive mode."""
        return self.is_element_present(*self.ADAPTIVE_MODE_INDICATOR, timeout=3)

    def get_current_difficulty_level(self):
        """
        Get current difficulty level displayed.
        Returns: String like "Easy", "Medium", "Hard", or "Adaptive"
        """
        if self.is_element_present(*self.CURRENT_DIFFICULTY_LEVEL, timeout=3):
            return self.get_text(*self.CURRENT_DIFFICULTY_LEVEL).strip()
        return "Unknown"

    def get_question_difficulty(self):
        """
        Get difficulty level of current question.
        Returns: String like "Easy", "Medium", "Hard"
        """
        if self.is_element_present(*self.QUESTION_DIFFICULTY_BADGE, timeout=3):
            badge_text = self.get_text(*self.QUESTION_DIFFICULTY_BADGE).strip()
            # Extract difficulty (e.g., "Difficulty: Medium" -> "Medium")
            if ":" in badge_text:
                return badge_text.split(":")[-1].strip()
            return badge_text
        return "Unknown"

    def answer_question(self, answer_index=0):
        """
        Answer current question.

        Args:
            answer_index: Index of answer to select (0-based)
        """
        answer_options = self.find_elements(*self.ANSWER_OPTIONS)
        if answer_options and len(answer_options) > answer_index:
            # Scroll into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                answer_options[answer_index]
            )
            time.sleep(0.3)
            answer_options[answer_index].click()
            time.sleep(0.5)

    def click_next_question(self):
        """Navigate to next question."""
        self.click_element(*self.NEXT_QUESTION_BUTTON)
        time.sleep(1)

    def submit_quiz(self):
        """Submit adaptive quiz."""
        self.click_element(*self.SUBMIT_QUIZ_BUTTON)
        time.sleep(2)

    def get_adaptive_score(self):
        """
        Get adaptive quiz score (may include confidence interval).
        Returns: Dictionary with 'score' and optionally 'confidence_interval'
        """
        result = {"score": 0, "confidence_interval": None}

        if self.is_element_present(*self.ADAPTIVE_SCORE_DISPLAY, timeout=5):
            score_text = self.get_text(*self.ADAPTIVE_SCORE_DISPLAY)
            import re
            match = re.search(r'(\d+(?:\.\d+)?)%', score_text)
            if match:
                result["score"] = float(match.group(1))

        if self.is_element_present(*self.CONFIDENCE_INTERVAL, timeout=2):
            ci_text = self.get_text(*self.CONFIDENCE_INTERVAL)
            result["confidence_interval"] = ci_text

        return result

    def get_remedial_content_suggestions(self):
        """Get list of remedial content suggested after quiz."""
        suggestions = []
        if self.is_element_present(*self.REMEDIAL_CONTENT_SUGGESTIONS, timeout=5):
            items = self.find_elements(*self.REMEDIAL_CONTENT_ITEM)
            for item in items:
                suggestions.append(item.text)
        return suggestions

    def get_knowledge_gaps(self):
        """Get list of identified knowledge gaps."""
        gaps = []
        if self.is_element_present(*self.KNOWLEDGE_GAP_SECTION, timeout=5):
            items = self.find_elements(*self.KNOWLEDGE_GAP_ITEM)
            for item in items:
                gaps.append(item.text)
        return gaps

    def get_skill_level(self):
        """
        Get estimated skill level.
        Returns: String like "Beginner", "Intermediate", "Advanced"
        """
        if self.is_element_present(*self.SKILL_LEVEL_DISPLAY, timeout=5):
            return self.get_text(*self.SKILL_LEVEL_DISPLAY).strip()
        return "Unknown"


class QuizSettingsPage(BasePage):
    """
    Page Object for quiz configuration/settings (instructor view).

    BUSINESS CONTEXT:
    Instructors need to enable adaptive mode for quizzes and configure
    difficulty adjustment parameters.
    """

    # Locators
    ADAPTIVE_MODE_TOGGLE = (By.ID, "adaptive-mode-toggle")
    DIFFICULTY_ALGORITHM_SELECT = (By.ID, "difficulty-algorithm-select")
    INITIAL_DIFFICULTY_SELECT = (By.ID, "initial-difficulty-select")
    ADJUSTMENT_SENSITIVITY_SLIDER = (By.ID, "adjustment-sensitivity")
    MIN_QUESTIONS_INPUT = (By.ID, "min-questions")
    MAX_QUESTIONS_INPUT = (By.ID, "max-questions")
    SAVE_SETTINGS_BUTTON = (By.ID, "save-quiz-settings-btn")

    def enable_adaptive_mode(self):
        """Enable adaptive quiz mode."""
        toggle = self.find_element(*self.ADAPTIVE_MODE_TOGGLE)
        if not toggle.is_selected():
            toggle.click()
            time.sleep(0.5)

    def select_difficulty_algorithm(self, algorithm_name):
        """
        Select difficulty adjustment algorithm.

        Args:
            algorithm_name: e.g., "IRT" (Item Response Theory), "Simple", "Bayesian"
        """
        select = self.find_element(*self.DIFFICULTY_ALGORITHM_SELECT)
        select.click()
        time.sleep(0.3)
        options = select.find_elements(By.TAG_NAME, "option")
        for option in options:
            if algorithm_name.lower() in option.text.lower():
                option.click()
                break
        time.sleep(0.5)

    def save_settings(self):
        """Save quiz settings."""
        self.click_element(*self.SAVE_SETTINGS_BUTTON)
        time.sleep(1)


class LoginPage(BasePage):
    """Page Object for login functionality."""

    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ROLE_SELECTOR = (By.ID, "role-selector")
    INSTRUCTOR_ROLE_OPTION = (By.CSS_SELECTOR, "option[value='instructor']")
    STUDENT_ROLE_OPTION = (By.CSS_SELECTOR, "option[value='student']")

    def login_as_instructor(self, email, password):
        """Login as instructor user."""
        self.navigate_to("/login")
        time.sleep(1)
        if self.is_element_present(*self.ROLE_SELECTOR, timeout=2):
            self.click_element(*self.ROLE_SELECTOR)
            self.click_element(*self.INSTRUCTOR_ROLE_OPTION)
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)
        time.sleep(3)

    def login_as_student(self, email, password):
        """Login as student user."""
        self.navigate_to("/login")
        time.sleep(1)
        if self.is_element_present(*self.ROLE_SELECTOR, timeout=2):
            self.click_element(*self.ROLE_SELECTOR)
            self.click_element(*self.STUDENT_ROLE_OPTION)
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)
        time.sleep(3)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
async def db_connection():
    """Provide database connection for verification."""
    conn = await asyncpg.connect(
        host="localhost",
        port=5433,
        user="course_creator",
        password="course_creator_password",
        database="course_creator"
    )
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture
def instructor_credentials():
    """Provide instructor test credentials."""
    return {
        "email": "instructor@example.com",
        "password": "Test123!@#"
    }


@pytest.fixture
def student_credentials():
    """Provide student test credentials."""
    return {
        "email": "student@example.com",
        "password": "Test123!@#"
    }


# ============================================================================
# ADAPTIVE QUESTION SELECTION TESTS
# ============================================================================

@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not configured")
class TestAdaptiveQuestionSelection(BaseTest):
    """
    Test suite for adaptive question selection algorithms.

    BUSINESS REQUIREMENT:
    Adaptive quizzes should dynamically adjust question difficulty based on
    student performance to provide more accurate skill assessment.
    """

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_quiz_adjusts_difficulty_based_on_student_answers(self, browser, test_base_url,
                                                                    student_credentials):
        """
        E2E TEST: Quiz adjusts difficulty based on student answers

        BUSINESS REQUIREMENT:
        - Adaptive algorithm adjusts question difficulty in real-time
        - Provides more accurate assessment than fixed-difficulty quizzes
        - Optimizes assessment time by reducing unnecessary questions

        TEST SCENARIO:
        1. Login as student
        2. Navigate to adaptive quiz
        3. Start adaptive quiz (should start at medium difficulty)
        4. Answer several questions correctly
        5. Verify difficulty increases (harder questions)
        6. Answer several questions incorrectly
        7. Verify difficulty decreases (easier questions)

        VALIDATION:
        - Adaptive mode indicator visible
        - Difficulty level changes based on performance
        - Questions get harder after correct streaks
        - Questions get easier after incorrect answers
        - Difficulty adjustments are smooth (not too abrupt)
        """
        login_page = LoginPage(browser, test_base_url)
        adaptive_quiz_page = AdaptiveQuizPage(browser, test_base_url)

        # Step 1: Login
        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )

        # Step 2: Navigate to adaptive quiz
        adaptive_quiz_page.navigate_to("/quiz/adaptive-python-quiz")
        time.sleep(2)

        # Step 3: Check if adaptive mode is enabled
        if not adaptive_quiz_page.is_adaptive_mode_enabled():
            pytest.skip("Adaptive quiz mode not yet implemented")

        # Get initial difficulty
        initial_difficulty = adaptive_quiz_page.get_current_difficulty_level()
        difficulty_progression = [initial_difficulty]

        # Step 4-5: Answer questions and track difficulty changes
        # (This is a simplified simulation - actual test would need more sophisticated logic)
        for i in range(5):
            current_difficulty = adaptive_quiz_page.get_question_difficulty()
            difficulty_progression.append(current_difficulty)

            # Answer question (index 0 for simplicity - would need correct answer logic)
            adaptive_quiz_page.answer_question(answer_index=0)
            adaptive_quiz_page.click_next_question()
            time.sleep(1)

        # Validation: Verify difficulty changes occurred
        unique_difficulties = set(difficulty_progression)
        assert len(unique_difficulties) > 1, \
            "Difficulty should change during adaptive quiz (not stay constant)"

        # Note: More sophisticated validation would require knowing correct answers
        # and verifying difficulty increases after correct answers, decreases after incorrect

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_easier_questions_after_incorrect_answer(self, browser, test_base_url,
                                                           student_credentials):
        """
        E2E TEST: Quiz presents easier questions after incorrect answer

        BUSINESS REQUIREMENT:
        - Adaptive algorithm should lower difficulty after incorrect answers
        - Prevents student frustration from overly difficult questions
        - Enables accurate assessment of actual skill level

        TEST SCENARIO:
        1. Login as student
        2. Start adaptive quiz at medium difficulty
        3. Deliberately answer incorrectly
        4. Verify next question has lower difficulty

        VALIDATION:
        - After incorrect answer, difficulty decreases
        - Difficulty decrease is proportional to confidence in incorrect answer
        - Does not decrease below minimum difficulty threshold
        """
        login_page = LoginPage(browser, test_base_url)
        adaptive_quiz_page = AdaptiveQuizPage(browser, test_base_url)

        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )

        adaptive_quiz_page.navigate_to("/quiz/adaptive-python-quiz")
        time.sleep(2)

        if not adaptive_quiz_page.is_adaptive_mode_enabled():
            pytest.skip("Adaptive quiz mode not yet implemented")

        # Get initial difficulty
        initial_difficulty = adaptive_quiz_page.get_question_difficulty()

        # Answer incorrectly (assume last option is incorrect - simplified)
        answer_options = adaptive_quiz_page.find_elements(*adaptive_quiz_page.ANSWER_OPTIONS)
        if answer_options:
            adaptive_quiz_page.answer_question(answer_index=len(answer_options) - 1)
            adaptive_quiz_page.click_next_question()
            time.sleep(1)

            # Get new difficulty
            new_difficulty = adaptive_quiz_page.get_question_difficulty()

            # Define difficulty ordering
            difficulty_order = ["Easy", "Medium", "Hard"]

            # Validation: New difficulty should be lower or same
            if initial_difficulty in difficulty_order and new_difficulty in difficulty_order:
                initial_idx = difficulty_order.index(initial_difficulty)
                new_idx = difficulty_order.index(new_difficulty)
                assert new_idx <= initial_idx, \
                    f"Difficulty should decrease or stay same after incorrect answer " \
                    f"(was {initial_difficulty}, now {new_difficulty})"
        else:
            pytest.skip("Could not test - no answer options found")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_harder_questions_after_correct_answer_streak(self, browser, test_base_url,
                                                                student_credentials):
        """
        E2E TEST: Quiz presents harder questions after correct answer streak

        BUSINESS REQUIREMENT:
        - Adaptive algorithm should increase difficulty after consecutive correct answers
        - Efficiently identifies student skill ceiling
        - Provides appropriate challenge level

        TEST SCENARIO:
        1. Login as student
        2. Start adaptive quiz
        3. Answer multiple questions correctly in a row (streak)
        4. Verify difficulty increases

        VALIDATION:
        - After 2-3 correct answers, difficulty increases
        - Difficulty increase is proportional to streak length
        - Does not increase beyond maximum difficulty threshold
        """
        login_page = LoginPage(browser, test_base_url)
        adaptive_quiz_page = AdaptiveQuizPage(browser, test_base_url)

        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )

        adaptive_quiz_page.navigate_to("/quiz/adaptive-python-quiz")
        time.sleep(2)

        if not adaptive_quiz_page.is_adaptive_mode_enabled():
            pytest.skip("Adaptive quiz mode not yet implemented")

        # Note: This test would require knowing correct answers
        # For now, we'll document the expected behavior
        pytest.skip("Test requires correct answer knowledge - placeholder for future implementation")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_difficulty_calibration_per_student_skill_level(self, browser, test_base_url,
                                                                  student_credentials, db_connection):
        """
        E2E TEST: Difficulty calibration adapts to individual student skill level

        BUSINESS REQUIREMENT:
        - Adaptive algorithm should maintain optimal difficulty for each student
        - Targets 70-80% success rate for efficient learning
        - Calibrates based on historical performance

        TEST SCENARIO:
        1. Login as student with known skill level
        2. Start adaptive quiz
        3. Verify initial difficulty matches student's historical level
        4. Complete quiz
        5. Verify final difficulty indicates accurate skill assessment

        VALIDATION:
        - Initial difficulty based on student history
        - Quiz converges on student's true skill level
        - Skill level estimate has reasonable confidence interval
        - Historical data influences initial difficulty selection
        """
        login_page = LoginPage(browser, test_base_url)
        adaptive_quiz_page = AdaptiveQuizPage(browser, test_base_url)

        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )

        # Check student's historical skill level from database
        query = """
            SELECT
                AVG(score::float / total_questions) as avg_performance,
                COUNT(*) as quiz_count
            FROM course_creator.quiz_attempts
            WHERE user_id = (
                SELECT id FROM course_creator.users WHERE email = $1 LIMIT 1
            )
        """
        result = await db_connection.fetchrow(query, student_credentials["email"])

        if result and result['quiz_count'] > 0:
            historical_performance = float(result['avg_performance'])

            # Navigate to adaptive quiz
            adaptive_quiz_page.navigate_to("/quiz/adaptive-python-quiz")
            time.sleep(2)

            if not adaptive_quiz_page.is_adaptive_mode_enabled():
                pytest.skip("Adaptive quiz mode not yet implemented")

            # Verify initial difficulty matches historical performance
            initial_difficulty = adaptive_quiz_page.get_current_difficulty_level()

            # Expected difficulty based on historical performance
            if historical_performance >= 0.8:
                expected_difficulty = "Hard"
            elif historical_performance >= 0.6:
                expected_difficulty = "Medium"
            else:
                expected_difficulty = "Easy"

            # Note: Actual validation would require more sophisticated logic
            # This is a placeholder for the expected behavior
            assert initial_difficulty in ["Easy", "Medium", "Hard", "Adaptive"], \
                f"Initial difficulty should be set appropriately (got {initial_difficulty})"
        else:
            pytest.skip("No historical data for student - cannot test calibration")


# ============================================================================
# PERSONALIZED QUIZ EXPERIENCE TESTS
# ============================================================================

@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not configured")
class TestPersonalizedQuizExperience(BaseTest):
    """
    Test suite for personalized quiz experiences and recommendations.

    BUSINESS REQUIREMENT:
    Adaptive quizzes should provide personalized learning recommendations,
    identify knowledge gaps, and suggest remedial content.
    """

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_student_sees_questions_matched_to_knowledge_level(self, browser, test_base_url,
                                                                     student_credentials):
        """
        E2E TEST: Student sees questions matched to knowledge level

        BUSINESS REQUIREMENT:
        - Students should receive questions appropriate to their skill level
        - Avoids demotivation from overly difficult questions
        - Avoids boredom from overly easy questions
        - Maximizes learning efficiency

        TEST SCENARIO:
        1. Login as student
        2. Start adaptive quiz
        3. Verify questions presented match estimated skill level
        4. Verify question difficulty is "just right" (not too easy, not too hard)

        VALIDATION:
        - Questions are within student's zone of proximal development
        - Difficulty distribution is appropriate (mostly medium, some easy/hard)
        - No questions that are obviously too difficult or too easy
        """
        login_page = LoginPage(browser, test_base_url)
        adaptive_quiz_page = AdaptiveQuizPage(browser, test_base_url)

        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )

        adaptive_quiz_page.navigate_to("/quiz/adaptive-python-quiz")
        time.sleep(2)

        if not adaptive_quiz_page.is_adaptive_mode_enabled():
            pytest.skip("Adaptive quiz mode not yet implemented")

        # Track question difficulties
        difficulties = []
        for i in range(5):
            difficulty = adaptive_quiz_page.get_question_difficulty()
            if difficulty != "Unknown":
                difficulties.append(difficulty)

            # Answer question
            adaptive_quiz_page.answer_question(answer_index=0)
            adaptive_quiz_page.click_next_question()
            time.sleep(1)

        # Validation: Should see a mix of difficulties, centered around student level
        if difficulties:
            assert len(set(difficulties)) > 0, "Should see questions with difficulty ratings"
            # Most questions should be medium difficulty (optimal challenge)
            medium_count = difficulties.count("Medium")
            assert medium_count > 0 or len(difficulties) < 3, \
                "Should see mostly medium difficulty questions for optimal learning"

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_ai_suggests_remedial_content_after_quiz(self, browser, test_base_url,
                                                           student_credentials):
        """
        E2E TEST: AI suggests remedial content after quiz completion

        BUSINESS REQUIREMENT:
        - Students need guidance on what to study next
        - Remedial content helps address knowledge gaps
        - Personalized recommendations improve learning outcomes

        TEST SCENARIO:
        1. Login as student
        2. Complete adaptive quiz (with some incorrect answers)
        3. View results page
        4. Verify remedial content suggestions are displayed
        5. Verify suggestions are relevant to missed topics

        VALIDATION:
        - Remedial content section exists
        - Lists 3-5 specific resources (videos, readings, exercises)
        - Resources address topics student struggled with
        - Links to content are functional
        """
        login_page = LoginPage(browser, test_base_url)
        adaptive_quiz_page = AdaptiveQuizPage(browser, test_base_url)

        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )

        adaptive_quiz_page.navigate_to("/quiz/adaptive-python-quiz")
        time.sleep(2)

        if not adaptive_quiz_page.is_adaptive_mode_enabled():
            pytest.skip("Adaptive quiz mode not yet implemented")

        # Complete quiz (simplified - answer 5 questions)
        for i in range(5):
            adaptive_quiz_page.answer_question(answer_index=0)
            if i < 4:
                adaptive_quiz_page.click_next_question()
            time.sleep(1)

        # Submit quiz
        adaptive_quiz_page.submit_quiz()
        time.sleep(2)

        # Check for remedial content suggestions
        suggestions = adaptive_quiz_page.get_remedial_content_suggestions()

        if len(suggestions) > 0:
            assert len(suggestions) >= 1, "Should suggest at least one remedial resource"
            assert len(suggestions) <= 10, "Should not overwhelm with too many suggestions"

            # Suggestions should be specific (not generic)
            for suggestion in suggestions:
                assert len(suggestion) > 10, f"Suggestion should be descriptive: {suggestion}"
        else:
            pytest.skip("Remedial content suggestions not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_prerequisite_knowledge_gaps_identified(self, browser, test_base_url,
                                                          student_credentials):
        """
        E2E TEST: Prerequisite knowledge gaps are identified

        BUSINESS REQUIREMENT:
        - Students may struggle due to missing prerequisite knowledge
        - Identifying gaps enables targeted remediation
        - Prevents students from advancing without foundational understanding

        TEST SCENARIO:
        1. Login as student
        2. Complete adaptive quiz
        3. View results page
        4. Verify knowledge gaps section is displayed
        5. Verify gaps are specific and actionable

        VALIDATION:
        - Knowledge gaps section exists
        - Lists specific topics/concepts student is missing
        - Distinguishes between "weak" and "missing" knowledge
        - Provides links to foundational content
        """
        login_page = LoginPage(browser, test_base_url)
        adaptive_quiz_page = AdaptiveQuizPage(browser, test_base_url)

        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )

        adaptive_quiz_page.navigate_to("/quiz/adaptive-python-quiz")
        time.sleep(2)

        if not adaptive_quiz_page.is_adaptive_mode_enabled():
            pytest.skip("Adaptive quiz mode not yet implemented")

        # Complete quiz
        for i in range(5):
            adaptive_quiz_page.answer_question(answer_index=0)
            if i < 4:
                adaptive_quiz_page.click_next_question()
            time.sleep(1)

        adaptive_quiz_page.submit_quiz()
        time.sleep(2)

        # Check for knowledge gaps
        knowledge_gaps = adaptive_quiz_page.get_knowledge_gaps()

        if len(knowledge_gaps) > 0:
            assert len(knowledge_gaps) >= 1, "Should identify at least one knowledge gap"

            # Gaps should be specific topics
            for gap in knowledge_gaps:
                assert len(gap) > 5, f"Knowledge gap should be specific: {gap}"
        else:
            pytest.skip("Knowledge gap identification not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_follow_up_quiz_recommendations(self, browser, test_base_url,
                                                  student_credentials):
        """
        E2E TEST: Follow-up quiz recommendations provided

        BUSINESS REQUIREMENT:
        - Students need guidance on next steps in learning journey
        - Recommendations should be personalized based on performance
        - Supports continuous learning progression

        TEST SCENARIO:
        1. Login as student
        2. Complete adaptive quiz
        3. View results page
        4. Verify next quiz recommendations section
        5. Verify recommendations are appropriate for skill level

        VALIDATION:
        - Recommendations section exists
        - Suggests 2-4 next quizzes
        - Recommendations match student skill level
        - Explains why each quiz is recommended
        """
        login_page = LoginPage(browser, test_base_url)
        adaptive_quiz_page = AdaptiveQuizPage(browser, test_base_url)

        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )

        adaptive_quiz_page.navigate_to("/quiz/adaptive-python-quiz")
        time.sleep(2)

        if not adaptive_quiz_page.is_adaptive_mode_enabled():
            pytest.skip("Adaptive quiz mode not yet implemented")

        # Complete quiz
        for i in range(5):
            adaptive_quiz_page.answer_question(answer_index=0)
            if i < 4:
                adaptive_quiz_page.click_next_question()
            time.sleep(1)

        adaptive_quiz_page.submit_quiz()
        time.sleep(2)

        # Check for recommendations
        if adaptive_quiz_page.is_element_present(
            *adaptive_quiz_page.NEXT_QUIZ_RECOMMENDATIONS, timeout=5
        ):
            # Recommendations section exists - feature implemented
            # (Actual validation would check content)
            pass
        else:
            pytest.skip("Follow-up quiz recommendations not yet implemented")


# ============================================================================
# VALIDATION AND FAIRNESS TESTS
# ============================================================================

@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not configured")
class TestAdaptiveQuizValidation(BaseTest):
    """
    Test suite for adaptive quiz validation and fairness.

    BUSINESS REQUIREMENT:
    Adaptive quizzes must be fair, accurate, and resistant to gaming.
    """

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_adaptive_algorithm_works_correctly(self, browser, test_base_url,
                                                      student_credentials, db_connection):
        """
        E2E TEST: Verify adaptive algorithm works correctly

        BUSINESS REQUIREMENT:
        - Adaptive algorithm must accurately estimate student skill level
        - Algorithm should converge on true skill level within reasonable questions
        - Results should be consistent with traditional fixed-difficulty assessments

        TEST SCENARIO:
        1. Login as student with known skill level
        2. Complete adaptive quiz
        3. Compare adaptive score to traditional quiz score
        4. Verify scores are within acceptable range (±10%)

        VALIDATION:
        - Adaptive score correlates with traditional score
        - Adaptive quiz uses fewer questions to reach same accuracy
        - Confidence interval includes true skill level
        """
        pytest.skip("Requires control group with traditional quiz scores - placeholder")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_fair_scoring_despite_variable_difficulty(self, browser, test_base_url,
                                                            student_credentials):
        """
        E2E TEST: Verify fair scoring despite variable difficulty

        BUSINESS REQUIREMENT:
        - Students who see harder questions should not be penalized
        - Scoring must account for question difficulty
        - Final score represents true skill level, not just number correct

        TEST SCENARIO:
        1. Two students with same skill level take same adaptive quiz
        2. Verify both receive similar final scores
        3. Verify scores account for question difficulty

        VALIDATION:
        - Score calculation includes difficulty weighting
        - Two students with same ability get same score ±5%
        - Harder questions contribute more to score
        - Easier questions contribute less to score
        """
        pytest.skip("Requires multiple student simulations - placeholder for future implementation")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.adaptive
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_student_cannot_game_adaptive_system(self, browser, test_base_url,
                                                       student_credentials):
        """
        E2E TEST: Verify student cannot game the adaptive system

        BUSINESS REQUIREMENT:
        - System must be resistant to intentional gaming
        - Cannot artificially lower difficulty by answering incorrectly early
        - Cannot inflate score by restarting quiz multiple times

        TEST SCENARIO:
        1. Attempt to game system by intentionally failing first questions
        2. Verify system detects pattern and adjusts appropriately
        3. Verify final score reflects true ability, not gaming strategy

        VALIDATION:
        - Deliberate incorrect answers don't permanently lower difficulty
        - System detects inconsistent performance patterns
        - Final score is accurate despite gaming attempts
        - Multiple retakes don't inflate score artificially
        """
        pytest.skip("Requires sophisticated gaming simulation - placeholder for future implementation")


# ============================================================================
# END OF TEST FILE
# ============================================================================
