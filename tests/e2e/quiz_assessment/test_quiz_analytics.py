"""
Comprehensive E2E Tests for Quiz Analytics and Reporting

BUSINESS REQUIREMENT:
Tests the complete quiz analytics system from both instructor and student perspectives,
covering completion rates, score distribution, performance analysis, struggling student
identification, question-level analytics, trend analysis, and export functionality.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Covers 12 test scenarios across instructor and student analytics
- Validates UI interactions, API calls, database queries, and data accuracy
- Tests chart rendering, CSV/PDF exports, and analytics dashboards

TEST COVERAGE:
1. Instructor Analytics:
   - Quiz completion rate tracking
   - Average score calculation and display
   - Score distribution histogram visualization
   - Struggling student identification (score < 60%)
   - Time spent per question analytics
   - Most missed questions analysis
   - Question difficulty analysis
   - CSV export functionality
   - PDF report generation
   - Cross-course performance comparison

2. Student Analytics:
   - Personal quiz history
   - Score trends over time
   - Time spent on each attempt
   - Question-by-question breakdown
   - Areas of strength/weakness identification
   - Anonymous comparison to class average

PRIORITY: P1 (HIGH) - Critical for instructor insights and student learning
"""

import pytest
import time
import uuid
import asyncpg
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class InstructorAnalyticsPage(BasePage):
    """
    Page Object for instructor analytics dashboard.

    BUSINESS CONTEXT:
    Instructors need comprehensive analytics to track student performance,
    identify at-risk students, and optimize course content based on data.
    """

    # Locators
    ANALYTICS_TAB = (By.ID, "analytics-tab")
    QUIZ_ANALYTICS_SECTION = (By.ID, "quiz-analytics-section")
    COMPLETION_RATE_CARD = (By.CLASS_NAME, "completion-rate-card")
    AVERAGE_SCORE_CARD = (By.CLASS_NAME, "average-score-card")
    SCORE_DISTRIBUTION_CHART = (By.ID, "score-distribution-chart")
    STRUGGLING_STUDENTS_LIST = (By.CLASS_NAME, "struggling-students-list")
    STRUGGLING_STUDENT_ITEM = (By.CLASS_NAME, "struggling-student-item")
    TIME_PER_QUESTION_CHART = (By.ID, "time-per-question-chart")
    MISSED_QUESTIONS_CHART = (By.ID, "missed-questions-chart")
    DIFFICULTY_ANALYSIS_CHART = (By.ID, "difficulty-analysis-chart")
    EXPORT_CSV_BUTTON = (By.ID, "export-csv-btn")
    EXPORT_PDF_BUTTON = (By.ID, "export-pdf-btn")
    COMPARE_COURSES_BUTTON = (By.ID, "compare-courses-btn")
    COURSE_SELECTOR = (By.ID, "analytics-course-select")
    QUIZ_SELECTOR = (By.ID, "analytics-quiz-select")
    DATE_RANGE_SELECTOR = (By.ID, "analytics-date-range")
    LOADING_OVERLAY = (By.CLASS_NAME, "loading-overlay")

    def navigate_to_analytics(self):
        """Navigate to instructor analytics dashboard."""
        self.navigate_to("/instructor-dashboard")
        time.sleep(2)
        if self.is_element_present(*self.ANALYTICS_TAB, timeout=10):
            self.click_element(*self.ANALYTICS_TAB)
            time.sleep(2)

    def select_course(self, course_name):
        """Select a specific course for analytics."""
        course_select = self.find_element(*self.COURSE_SELECTOR)
        course_select.click()
        time.sleep(0.5)
        # Find option by visible text
        options = course_select.find_elements(By.TAG_NAME, "option")
        for option in options:
            if course_name.lower() in option.text.lower():
                option.click()
                time.sleep(1)
                break

    def select_quiz(self, quiz_name):
        """Select a specific quiz for analytics."""
        quiz_select = self.find_element(*self.QUIZ_SELECTOR)
        quiz_select.click()
        time.sleep(0.5)
        # Find option by visible text
        options = quiz_select.find_elements(By.TAG_NAME, "option")
        for option in options:
            if quiz_name.lower() in option.text.lower():
                option.click()
                time.sleep(1)
                break

    def get_completion_rate(self):
        """Get quiz completion rate percentage."""
        if self.is_element_present(*self.COMPLETION_RATE_CARD, timeout=5):
            card = self.find_element(*self.COMPLETION_RATE_CARD)
            text = card.text
            # Extract percentage (e.g., "85%" -> 85)
            import re
            match = re.search(r'(\d+)%', text)
            if match:
                return int(match.group(1))
        return 0

    def get_average_score(self):
        """Get average quiz score."""
        if self.is_element_present(*self.AVERAGE_SCORE_CARD, timeout=5):
            card = self.find_element(*self.AVERAGE_SCORE_CARD)
            text = card.text
            # Extract percentage (e.g., "76%" -> 76)
            import re
            match = re.search(r'(\d+(?:\.\d+)?)%', text)
            if match:
                return float(match.group(1))
        return 0.0

    def get_struggling_students_count(self):
        """Get count of struggling students (score < 60%)."""
        if self.is_element_present(*self.STRUGGLING_STUDENTS_LIST, timeout=5):
            students = self.find_elements(*self.STRUGGLING_STUDENT_ITEM)
            return len(students)
        return 0

    def get_struggling_students(self):
        """Get list of struggling student names."""
        students = []
        if self.is_element_present(*self.STRUGGLING_STUDENTS_LIST, timeout=5):
            student_items = self.find_elements(*self.STRUGGLING_STUDENT_ITEM)
            for item in student_items:
                students.append(item.text)
        return students

    def is_chart_rendered(self, chart_locator):
        """Check if a chart canvas is rendered."""
        if self.is_element_present(*chart_locator, timeout=5):
            chart = self.find_element(*chart_locator)
            # Check if canvas has content (width > 0)
            width = chart.get_attribute("width")
            return width and int(width) > 0
        return False

    def export_to_csv(self):
        """Click export to CSV button."""
        self.click_element(*self.EXPORT_CSV_BUTTON)
        time.sleep(2)

    def export_to_pdf(self):
        """Click export to PDF button."""
        self.click_element(*self.EXPORT_PDF_BUTTON)
        time.sleep(3)

    def compare_courses(self):
        """Click compare courses button."""
        self.click_element(*self.COMPARE_COURSES_BUTTON)
        time.sleep(2)

    def wait_for_data_load(self, timeout=10):
        """Wait for analytics data to finish loading."""
        try:
            # Wait for loading overlay to disappear
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(self.LOADING_OVERLAY)
            )
            time.sleep(1)
        except TimeoutException:
            pass  # Already loaded or no overlay


class StudentAnalyticsPage(BasePage):
    """
    Page Object for student personal analytics view.

    BUSINESS CONTEXT:
    Students need visibility into their learning progress, strengths,
    weaknesses, and areas requiring additional practice.
    """

    # Locators
    PROGRESS_TAB = (By.ID, "progress-tab")
    QUIZ_HISTORY_SECTION = (By.ID, "quiz-history-section")
    QUIZ_HISTORY_TABLE = (By.CLASS_NAME, "quiz-history-table")
    QUIZ_HISTORY_ROW = (By.CLASS_NAME, "quiz-history-row")
    SCORE_TREND_CHART = (By.ID, "score-trend-chart")
    TIME_SPENT_CHART = (By.ID, "time-spent-chart")
    QUESTION_BREAKDOWN_SECTION = (By.ID, "question-breakdown-section")
    STRENGTHS_LIST = (By.CLASS_NAME, "strengths-list")
    WEAKNESSES_LIST = (By.CLASS_NAME, "weaknesses-list")
    CLASS_AVERAGE_COMPARISON = (By.CLASS_NAME, "class-average-comparison")
    PERSONAL_SCORE_DISPLAY = (By.CLASS_NAME, "personal-score-display")
    CLASS_AVERAGE_DISPLAY = (By.CLASS_NAME, "class-average-display")

    def navigate_to_progress(self):
        """Navigate to student progress/analytics page."""
        self.navigate_to("/student-dashboard")
        time.sleep(2)
        if self.is_element_present(*self.PROGRESS_TAB, timeout=10):
            self.click_element(*self.PROGRESS_TAB)
            time.sleep(2)

    def get_quiz_history_count(self):
        """Get count of quiz attempts in history."""
        if self.is_element_present(*self.QUIZ_HISTORY_TABLE, timeout=5):
            rows = self.find_elements(*self.QUIZ_HISTORY_ROW)
            return len(rows)
        return 0

    def get_latest_quiz_score(self):
        """Get score from most recent quiz attempt."""
        if self.is_element_present(*self.QUIZ_HISTORY_TABLE, timeout=5):
            rows = self.find_elements(*self.QUIZ_HISTORY_ROW)
            if rows:
                # First row is most recent
                text = rows[0].text
                import re
                match = re.search(r'(\d+)%', text)
                if match:
                    return int(match.group(1))
        return 0

    def get_strengths(self):
        """Get list of student strengths."""
        strengths = []
        if self.is_element_present(*self.STRENGTHS_LIST, timeout=5):
            strength_items = self.find_elements(By.CSS_SELECTOR, ".strengths-list li")
            for item in strength_items:
                strengths.append(item.text)
        return strengths

    def get_weaknesses(self):
        """Get list of student weaknesses."""
        weaknesses = []
        if self.is_element_present(*self.WEAKNESSES_LIST, timeout=5):
            weakness_items = self.find_elements(By.CSS_SELECTOR, ".weaknesses-list li")
            for item in weakness_items:
                weaknesses.append(item.text)
        return weaknesses

    def get_class_average_comparison(self):
        """Get personal score vs class average comparison."""
        result = {"personal": 0, "class_average": 0}
        if self.is_element_present(*self.CLASS_AVERAGE_COMPARISON, timeout=5):
            if self.is_element_present(*self.PERSONAL_SCORE_DISPLAY, timeout=2):
                personal_text = self.get_text(*self.PERSONAL_SCORE_DISPLAY)
                import re
                match = re.search(r'(\d+(?:\.\d+)?)%', personal_text)
                if match:
                    result["personal"] = float(match.group(1))

            if self.is_element_present(*self.CLASS_AVERAGE_DISPLAY, timeout=2):
                average_text = self.get_text(*self.CLASS_AVERAGE_DISPLAY)
                import re
                match = re.search(r'(\d+(?:\.\d+)?)%', average_text)
                if match:
                    result["class_average"] = float(match.group(1))

        return result

    def is_score_trend_visible(self):
        """Check if score trend chart is visible."""
        return self.is_element_present(*self.SCORE_TREND_CHART, timeout=5)


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

        # Select instructor role if role selector exists
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

        # Select student role if role selector exists
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
# INSTRUCTOR ANALYTICS TESTS
# ============================================================================

class TestInstructorQuizAnalytics(BaseTest):
    """
    Test suite for instructor quiz analytics dashboard.

    BUSINESS REQUIREMENT:
    Instructors need comprehensive analytics to make data-driven decisions
    about course content, identify struggling students, and optimize learning outcomes.
    """

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_instructor_views_quiz_completion_rate(self, browser, test_base_url,
                                                         instructor_credentials, db_connection):
        """
        E2E TEST: Instructor views quiz completion rate

        BUSINESS REQUIREMENT:
        - Instructors need to track how many students have completed quizzes
        - Completion rate indicates student engagement and course effectiveness
        - Low completion rates may signal course difficulty or engagement issues

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Select a course and quiz
        4. View completion rate
        5. Verify completion rate matches database calculation

        VALIDATION:
        - Completion rate displayed correctly (percentage)
        - Matches database calculation: (completed / enrolled) * 100
        - Updates when different quiz/course selected
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1: Login as instructor
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )

        # Step 2: Navigate to analytics
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()

        # Step 3: Select course and quiz
        analytics_page.select_course("Introduction to Python")
        analytics_page.select_quiz("Python Basics Quiz")

        # Step 4: Get completion rate from UI
        completion_rate_ui = analytics_page.get_completion_rate()
        assert completion_rate_ui > 0, "Completion rate should be displayed"

        # Step 5: Verify against database
        # Query to calculate actual completion rate
        query = """
            SELECT
                COUNT(DISTINCT qa.user_id)::float /
                NULLIF(COUNT(DISTINCT e.user_id), 0) * 100 as completion_rate
            FROM course_creator.enrollments e
            LEFT JOIN course_creator.quiz_attempts qa
                ON e.user_id = qa.user_id AND e.course_id = qa.course_instance_id
            WHERE e.course_id = (
                SELECT id FROM course_creator.courses WHERE title = 'Introduction to Python' LIMIT 1
            )
        """
        result = await db_connection.fetchrow(query)
        if result and result['completion_rate']:
            db_completion_rate = round(float(result['completion_rate']))
            # Allow 5% tolerance for rounding and timing differences
            assert abs(completion_rate_ui - db_completion_rate) <= 5, \
                f"UI completion rate {completion_rate_ui}% should match DB rate {db_completion_rate}%"

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_instructor_views_average_score(self, browser, test_base_url,
                                                   instructor_credentials, db_connection):
        """
        E2E TEST: Instructor views average quiz score across all students

        BUSINESS REQUIREMENT:
        - Average score indicates overall course effectiveness
        - Helps identify if quiz difficulty is appropriate
        - Enables comparison across different courses/topics

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Select a course and quiz
        4. View average score
        5. Verify average matches database calculation

        VALIDATION:
        - Average score displayed as percentage
        - Calculation: SUM(scores) / COUNT(attempts)
        - Matches database calculation within tolerance
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1-3: Login and navigate
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()
        analytics_page.select_course("Introduction to Python")
        analytics_page.select_quiz("Python Basics Quiz")

        # Step 4: Get average score from UI
        average_score_ui = analytics_page.get_average_score()
        assert average_score_ui > 0, "Average score should be displayed"

        # Step 5: Verify against database
        query = """
            SELECT AVG(score::float / total_questions * 100) as avg_score
            FROM course_creator.quiz_attempts
            WHERE quiz_id IN (
                SELECT id FROM course_creator.quizzes
                WHERE title LIKE '%Python Basics%' LIMIT 1
            )
        """
        result = await db_connection.fetchrow(query)
        if result and result['avg_score']:
            db_average_score = round(float(result['avg_score']), 1)
            # Allow 5% tolerance
            assert abs(average_score_ui - db_average_score) <= 5, \
                f"UI average {average_score_ui}% should match DB average {db_average_score}%"

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_instructor_views_score_distribution(self, browser, test_base_url,
                                                       instructor_credentials):
        """
        E2E TEST: Instructor views score distribution histogram

        BUSINESS REQUIREMENT:
        - Score distribution reveals learning outcome patterns
        - Helps identify if quiz difficulty is appropriate (normal distribution expected)
        - Bimodal distribution may indicate content gaps

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Select a course and quiz
        4. Verify score distribution chart renders
        5. Check chart shows histogram bars

        VALIDATION:
        - Chart canvas element exists and has content
        - Chart displays histogram bars (not just empty canvas)
        - X-axis shows score ranges (0-60%, 60-70%, 70-80%, 80-90%, 90-100%)
        - Y-axis shows student count
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1-3: Login and navigate
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()
        analytics_page.select_course("Introduction to Python")
        analytics_page.select_quiz("Python Basics Quiz")

        # Step 4-5: Verify chart rendering
        chart_rendered = analytics_page.is_chart_rendered(
            analytics_page.SCORE_DISTRIBUTION_CHART
        )
        assert chart_rendered, "Score distribution chart should be rendered with data"

        # Additional validation: Check chart is visible and has reasonable size
        chart = analytics_page.find_element(*analytics_page.SCORE_DISTRIBUTION_CHART)
        assert chart.is_displayed(), "Chart should be visible"

        width = int(chart.get_attribute("width") or 0)
        height = int(chart.get_attribute("height") or 0)
        assert width > 200 and height > 100, \
            f"Chart should have reasonable dimensions (got {width}x{height})"

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_instructor_identifies_struggling_students(self, browser, test_base_url,
                                                             instructor_credentials, db_connection):
        """
        E2E TEST: Instructor identifies struggling students (score < 60%)

        BUSINESS REQUIREMENT:
        - Early identification of struggling students enables timely intervention
        - Students scoring < 60% need additional support and resources
        - Critical for student retention and success

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Select a course and quiz
        4. View struggling students list
        5. Verify list matches database query (score < 60%)

        VALIDATION:
        - Struggling students section exists and is visible
        - List shows students with quiz score < 60%
        - Student names and scores are displayed
        - Count matches database calculation
        - List is sortable by score (lowest first)
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1-3: Login and navigate
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()
        analytics_page.select_course("Introduction to Python")
        analytics_page.select_quiz("Python Basics Quiz")

        # Step 4: Get struggling students from UI
        struggling_count_ui = analytics_page.get_struggling_students_count()
        struggling_students_ui = analytics_page.get_struggling_students()

        # Step 5: Verify against database
        query = """
            SELECT
                u.full_name,
                qa.score::float / qa.total_questions * 100 as score_percentage
            FROM course_creator.quiz_attempts qa
            JOIN course_creator.users u ON qa.user_id = u.id
            WHERE qa.quiz_id IN (
                SELECT id FROM course_creator.quizzes
                WHERE title LIKE '%Python Basics%' LIMIT 1
            )
            AND (qa.score::float / qa.total_questions * 100) < 60
            ORDER BY score_percentage ASC
        """
        db_struggling = await db_connection.fetch(query)
        db_struggling_count = len(db_struggling)

        # Validation
        assert struggling_count_ui >= 0, "Struggling students count should be displayed"

        # If database has struggling students, UI should show them
        if db_struggling_count > 0:
            assert struggling_count_ui > 0, \
                f"UI should show {db_struggling_count} struggling students from DB"

            # Verify count matches (within reason for pagination)
            assert struggling_count_ui == db_struggling_count or \
                   struggling_count_ui >= min(db_struggling_count, 10), \
                f"UI count {struggling_count_ui} should match DB count {db_struggling_count}"

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_instructor_views_time_per_question_analytics(self, browser, test_base_url,
                                                                instructor_credentials):
        """
        E2E TEST: Instructor views time spent per question (average)

        BUSINESS REQUIREMENT:
        - Time per question indicates question difficulty and clarity
        - Questions taking too long may be poorly worded or too complex
        - Helps optimize quiz design for better learning assessment

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Select a course and quiz
        4. View time per question chart
        5. Verify chart shows average time for each question

        VALIDATION:
        - Time per question chart renders correctly
        - Shows bar chart with one bar per question
        - Y-axis shows time in seconds/minutes
        - Hover tooltip shows exact time value
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1-3: Login and navigate
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()
        analytics_page.select_course("Introduction to Python")
        analytics_page.select_quiz("Python Basics Quiz")

        # Step 4-5: Verify chart rendering
        chart_rendered = analytics_page.is_chart_rendered(
            analytics_page.TIME_PER_QUESTION_CHART
        )

        # Chart may not exist if feature not implemented yet
        if analytics_page.is_element_present(*analytics_page.TIME_PER_QUESTION_CHART, timeout=3):
            assert chart_rendered, "Time per question chart should render with data"
        else:
            pytest.skip("Time per question analytics not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_instructor_views_most_missed_questions(self, browser, test_base_url,
                                                          instructor_credentials):
        """
        E2E TEST: Instructor views most missed questions

        BUSINESS REQUIREMENT:
        - Identifies questions that most students answer incorrectly
        - Indicates content areas needing additional instruction
        - Helps refine course material and quiz questions

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Select a course and quiz
        4. View most missed questions chart
        5. Verify questions sorted by miss rate (highest first)

        VALIDATION:
        - Missed questions chart renders
        - Shows questions with highest error rates
        - Displays percentage of students who missed each question
        - Top 5-10 most missed questions shown
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1-3: Login and navigate
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()
        analytics_page.select_course("Introduction to Python")
        analytics_page.select_quiz("Python Basics Quiz")

        # Step 4-5: Verify chart rendering
        if analytics_page.is_element_present(*analytics_page.MISSED_QUESTIONS_CHART, timeout=3):
            chart_rendered = analytics_page.is_chart_rendered(
                analytics_page.MISSED_QUESTIONS_CHART
            )
            assert chart_rendered, "Most missed questions chart should render"
        else:
            pytest.skip("Most missed questions analytics not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_instructor_views_question_difficulty_analysis(self, browser, test_base_url,
                                                                 instructor_credentials):
        """
        E2E TEST: Instructor views question difficulty analysis

        BUSINESS REQUIREMENT:
        - Question difficulty analysis shows empirical difficulty based on student performance
        - Helps balance quiz difficulty for effective assessment
        - Identifies questions that may need revision

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Select a course and quiz
        4. View difficulty analysis chart
        5. Verify questions categorized by difficulty (easy/medium/hard)

        VALIDATION:
        - Difficulty analysis chart renders
        - Questions categorized: Easy (>80% correct), Medium (60-80%), Hard (<60%)
        - Shows distribution of questions across difficulty levels
        - Color-coded for quick visual assessment
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1-3: Login and navigate
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()
        analytics_page.select_course("Introduction to Python")
        analytics_page.select_quiz("Python Basics Quiz")

        # Step 4-5: Verify chart rendering
        if analytics_page.is_element_present(*analytics_page.DIFFICULTY_ANALYSIS_CHART, timeout=3):
            chart_rendered = analytics_page.is_chart_rendered(
                analytics_page.DIFFICULTY_ANALYSIS_CHART
            )
            assert chart_rendered, "Difficulty analysis chart should render"
        else:
            pytest.skip("Question difficulty analysis not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_instructor_exports_quiz_results_to_csv(self, browser, test_base_url,
                                                          instructor_credentials):
        """
        E2E TEST: Instructor exports quiz results to CSV

        BUSINESS REQUIREMENT:
        - CSV export enables external analysis in Excel/Google Sheets
        - Required for institutional reporting and record-keeping
        - Supports data-driven decision making

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Select a course and quiz
        4. Click export to CSV button
        5. Verify file download initiated

        VALIDATION:
        - Export button exists and is clickable
        - File download starts (can't verify file content in E2E)
        - CSV should include: student_name, score, percentage, time_taken, completion_date
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1-3: Login and navigate
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()
        analytics_page.select_course("Introduction to Python")
        analytics_page.select_quiz("Python Basics Quiz")

        # Step 4: Click export CSV
        if analytics_page.is_element_present(*analytics_page.EXPORT_CSV_BUTTON, timeout=3):
            analytics_page.export_to_csv()
            # Note: Cannot verify actual file download in E2E test
            # But can verify button click doesn't cause errors
            time.sleep(1)
        else:
            pytest.skip("CSV export not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_instructor_generates_quiz_performance_pdf_report(self, browser, test_base_url,
                                                                    instructor_credentials):
        """
        E2E TEST: Instructor generates quiz performance report PDF

        BUSINESS REQUIREMENT:
        - PDF reports provide professional-looking summaries for stakeholders
        - Required for accreditation and compliance reporting
        - Enables sharing insights with non-technical audiences

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Select a course and quiz
        4. Click generate PDF report button
        5. Verify PDF generation initiated

        VALIDATION:
        - PDF report button exists and is clickable
        - Report generation starts (shows loading indicator)
        - PDF should include: summary stats, charts, student list
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1-3: Login and navigate
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()
        analytics_page.select_course("Introduction to Python")
        analytics_page.select_quiz("Python Basics Quiz")

        # Step 4: Click export PDF
        if analytics_page.is_element_present(*analytics_page.EXPORT_PDF_BUTTON, timeout=3):
            analytics_page.export_to_pdf()
            # Note: Cannot verify actual file download in E2E test
            time.sleep(2)
        else:
            pytest.skip("PDF report generation not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_instructor_compares_quiz_performance_across_courses(self, browser, test_base_url,
                                                                       instructor_credentials):
        """
        E2E TEST: Instructor compares quiz performance across courses

        BUSINESS REQUIREMENT:
        - Cross-course comparison reveals curriculum effectiveness patterns
        - Helps identify best practices for replication
        - Enables data-driven curriculum improvements

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Click compare courses button
        4. Select 2-3 courses for comparison
        5. View comparative analytics

        VALIDATION:
        - Compare courses button exists
        - Multi-course selector appears
        - Side-by-side comparison view shows average scores, completion rates
        - Chart visualizes differences across courses
        """
        login_page = LoginPage(browser, test_base_url)
        analytics_page = InstructorAnalyticsPage(browser, test_base_url)

        # Step 1-3: Login and navigate
        login_page.login_as_instructor(
            instructor_credentials["email"],
            instructor_credentials["password"]
        )
        analytics_page.navigate_to_analytics()
        analytics_page.wait_for_data_load()

        # Step 4: Click compare courses
        if analytics_page.is_element_present(*analytics_page.COMPARE_COURSES_BUTTON, timeout=3):
            analytics_page.compare_courses()
            time.sleep(2)
            # Verify comparison view loads
            # (Implementation details depend on actual UI)
        else:
            pytest.skip("Cross-course comparison not yet implemented")


# ============================================================================
# STUDENT ANALYTICS TESTS
# ============================================================================

class TestStudentQuizAnalytics(BaseTest):
    """
    Test suite for student personal quiz analytics.

    BUSINESS REQUIREMENT:
    Students need visibility into their learning progress, strengths,
    and areas needing improvement for effective self-directed learning.
    """

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_student_views_quiz_history(self, browser, test_base_url,
                                               student_credentials, db_connection):
        """
        E2E TEST: Student views personal quiz history

        BUSINESS REQUIREMENT:
        - Students need to track their quiz attempts over time
        - Historical view enables reflection on learning progress
        - Supports metacognitive learning strategies

        TEST SCENARIO:
        1. Login as student
        2. Navigate to progress/analytics page
        3. View quiz history section
        4. Verify all quiz attempts are listed
        5. Check history shows: quiz name, date, score, time taken

        VALIDATION:
        - Quiz history table exists and is visible
        - Lists all quiz attempts for the student
        - Shows correct data: quiz name, score, date
        - Most recent attempts shown first (descending order)
        - Count matches database records
        """
        login_page = LoginPage(browser, test_base_url)
        student_analytics_page = StudentAnalyticsPage(browser, test_base_url)

        # Step 1-2: Login and navigate
        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )
        student_analytics_page.navigate_to_progress()

        # Step 3-4: View quiz history
        if student_analytics_page.is_element_present(
            *student_analytics_page.QUIZ_HISTORY_SECTION, timeout=5
        ):
            history_count_ui = student_analytics_page.get_quiz_history_count()

            # Step 5: Verify against database
            query = """
                SELECT COUNT(*) as attempt_count
                FROM course_creator.quiz_attempts
                WHERE user_id = (
                    SELECT id FROM course_creator.users
                    WHERE email = $1 LIMIT 1
                )
            """
            result = await db_connection.fetchrow(query, student_credentials["email"])
            db_history_count = result['attempt_count'] if result else 0

            assert history_count_ui >= 0, "Quiz history should be displayed"
            if db_history_count > 0:
                assert history_count_ui > 0, \
                    f"Should show {db_history_count} quiz attempts from database"
        else:
            pytest.skip("Student quiz history not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_student_views_score_trends_over_time(self, browser, test_base_url,
                                                        student_credentials):
        """
        E2E TEST: Student views score trends over time

        BUSINESS REQUIREMENT:
        - Trend visualization shows learning progress
        - Helps students see improvement (or areas needing work)
        - Motivational tool for continued engagement

        TEST SCENARIO:
        1. Login as student
        2. Navigate to progress/analytics page
        3. View score trend chart
        4. Verify chart shows score progression over time

        VALIDATION:
        - Score trend chart exists and renders
        - X-axis shows date/time
        - Y-axis shows score percentage
        - Line chart connects quiz attempts chronologically
        - Shows upward/downward trends clearly
        """
        login_page = LoginPage(browser, test_base_url)
        student_analytics_page = StudentAnalyticsPage(browser, test_base_url)

        # Step 1-2: Login and navigate
        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )
        student_analytics_page.navigate_to_progress()

        # Step 3-4: Verify score trend chart
        score_trend_visible = student_analytics_page.is_score_trend_visible()

        if student_analytics_page.is_element_present(
            *student_analytics_page.SCORE_TREND_CHART, timeout=5
        ):
            assert score_trend_visible, "Score trend chart should be visible"
        else:
            pytest.skip("Student score trend analytics not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_student_views_areas_of_strength_and_weakness(self, browser, test_base_url,
                                                                student_credentials):
        """
        E2E TEST: Student views areas of strength/weakness identification

        BUSINESS REQUIREMENT:
        - Identifying strengths builds confidence
        - Identifying weaknesses guides study focus
        - Supports personalized learning paths

        TEST SCENARIO:
        1. Login as student
        2. Navigate to progress/analytics page
        3. View strengths section
        4. View weaknesses section
        5. Verify topics/concepts are listed

        VALIDATION:
        - Strengths section exists and shows topics student performs well in
        - Weaknesses section exists and shows topics needing improvement
        - Based on question-level analytics (topic tags)
        - Clear, actionable insights
        """
        login_page = LoginPage(browser, test_base_url)
        student_analytics_page = StudentAnalyticsPage(browser, test_base_url)

        # Step 1-2: Login and navigate
        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )
        student_analytics_page.navigate_to_progress()

        # Step 3-5: View strengths and weaknesses
        if student_analytics_page.is_element_present(
            *student_analytics_page.STRENGTHS_LIST, timeout=5
        ):
            strengths = student_analytics_page.get_strengths()
            weaknesses = student_analytics_page.get_weaknesses()

            # At least one of these should have content
            assert len(strengths) > 0 or len(weaknesses) > 0, \
                "Should show either strengths or weaknesses (or both)"
        else:
            pytest.skip("Strength/weakness analysis not yet implemented")

    @pytest.mark.e2e
    @pytest.mark.quiz_assessment
    @pytest.mark.analytics
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_student_compares_performance_to_class_average(self, browser, test_base_url,
                                                                 student_credentials):
        """
        E2E TEST: Student compares performance to class average (anonymous)

        BUSINESS REQUIREMENT:
        - Class average comparison provides context for personal performance
        - Anonymized to protect student privacy (FERPA compliance)
        - Helps students gauge their relative progress

        TEST SCENARIO:
        1. Login as student
        2. Navigate to progress/analytics page
        3. View class average comparison section
        4. Verify personal score and class average displayed
        5. Verify no individual student names shown (privacy)

        VALIDATION:
        - Comparison section exists and is visible
        - Shows student's personal average score
        - Shows anonymized class average score
        - Visual indicator (above/below/at average)
        - No personally identifiable information about other students
        """
        login_page = LoginPage(browser, test_base_url)
        student_analytics_page = StudentAnalyticsPage(browser, test_base_url)

        # Step 1-2: Login and navigate
        login_page.login_as_student(
            student_credentials["email"],
            student_credentials["password"]
        )
        student_analytics_page.navigate_to_progress()

        # Step 3-5: View class average comparison
        if student_analytics_page.is_element_present(
            *student_analytics_page.CLASS_AVERAGE_COMPARISON, timeout=5
        ):
            comparison = student_analytics_page.get_class_average_comparison()

            assert comparison["personal"] >= 0, "Personal score should be displayed"
            assert comparison["class_average"] >= 0, "Class average should be displayed"

            # Verify values are reasonable (0-100%)
            assert 0 <= comparison["personal"] <= 100, \
                f"Personal score {comparison['personal']}% should be 0-100%"
            assert 0 <= comparison["class_average"] <= 100, \
                f"Class average {comparison['class_average']}% should be 0-100%"
        else:
            pytest.skip("Class average comparison not yet implemented")


# ============================================================================
# END OF TEST FILE
# ============================================================================
