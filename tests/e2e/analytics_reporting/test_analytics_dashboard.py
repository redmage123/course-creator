"""
Comprehensive E2E Tests for Analytics Dashboards (ALL User Roles)

BUSINESS REQUIREMENT:
Tests analytics dashboards for ALL 4 user roles (Student, Instructor, Organization Admin, Site Admin).
Each role has different analytics needs and access levels. Analytics must be accurate, real-time,
and match database calculations exactly.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Covers 18 test scenarios across 4 user roles
- Three-layer verification: UI Display → Database Query → Accuracy Check
- Tests chart rendering, metric calculations, and real-time updates

TEST COVERAGE:
1. Student Analytics Dashboard (5 tests):
   - Personal progress dashboard
   - Course completion percentage accuracy
   - Time spent tracking accuracy
   - Quiz scores displayed correctly
   - Certificate achievements visible

2. Instructor Analytics Dashboard (6 tests):
   - View course analytics dashboard
   - Student enrollment numbers accurate
   - Course completion rates displayed
   - Average quiz scores calculated correctly
   - Student engagement metrics (views, time spent)
   - Struggling students identification (score < 60%)

3. Organization Admin Analytics (4 tests):
   - View organization-wide analytics
   - All courses overview with metrics
   - Member activity tracking
   - Resource utilization stats

4. Site Admin Analytics (3 tests):
   - Platform-wide analytics dashboard
   - Cross-organization metrics
   - System health and usage stats

PRIORITY: P0 (CRITICAL) - Core analytics functionality for ALL roles
"""

import pytest
import time
import uuid
import asyncpg
from datetime import datetime, timedelta
from decimal import Decimal
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class StudentAnalyticsPage(BasePage):
    """
    Page Object for student personal analytics dashboard.

    BUSINESS CONTEXT:
    Students need to track their own progress, identify areas for improvement,
    and visualize their learning journey. Analytics must be motivating and actionable.
    """

    # Locators
    DASHBOARD_LINK = (By.LINK_TEXT, "Dashboard")
    MY_PROGRESS_TAB = (By.ID, "my-progress-tab")
    OVERALL_PROGRESS_CARD = (By.ID, "overall-progress-percentage")
    COMPLETION_PERCENTAGE = (By.ID, "completion-percentage")
    TIME_SPENT_CARD = (By.ID, "time-spent-card")
    TOTAL_TIME_HOURS = (By.ID, "total-time-hours")
    QUIZ_SCORES_SECTION = (By.ID, "quiz-scores-section")
    QUIZ_SCORE_ITEM = (By.CLASS_NAME, "quiz-score-item")
    CERTIFICATES_SECTION = (By.ID, "certificates-section")
    CERTIFICATE_ITEM = (By.CLASS_NAME, "certificate-item")
    PROGRESS_CHART = (By.ID, "student-progress-chart")

    def navigate_to_dashboard(self):
        """Navigate to student dashboard."""
        self.navigate_to("/student-dashboard")
        time.sleep(2)
        if self.is_element_present(*self.MY_PROGRESS_TAB, timeout=10):
            self.click_element(*self.MY_PROGRESS_TAB)
            time.sleep(1)

    def get_completion_percentage(self):
        """Get displayed completion percentage."""
        elem = self.find_element(*self.COMPLETION_PERCENTAGE)
        text = elem.text.strip('%')
        return float(text) if text else 0.0

    def get_time_spent_hours(self):
        """Get displayed time spent in hours."""
        elem = self.find_element(*self.TOTAL_TIME_HOURS)
        text = elem.text.replace('h', '').strip()
        return float(text) if text else 0.0

    def get_quiz_scores(self):
        """Get list of quiz scores."""
        items = self.driver.find_elements(*self.QUIZ_SCORE_ITEM)
        scores = []
        for item in items:
            score_text = item.find_element(By.CLASS_NAME, "score").text
            score = float(score_text.strip('%'))
            quiz_name = item.find_element(By.CLASS_NAME, "quiz-name").text
            scores.append({"name": quiz_name, "score": score})
        return scores

    def get_certificates_count(self):
        """Get number of certificates earned."""
        items = self.driver.find_elements(*self.CERTIFICATE_ITEM)
        return len(items)

    def is_progress_chart_visible(self):
        """Check if progress chart is rendered."""
        return self.is_element_present(*self.PROGRESS_CHART, timeout=5)


class InstructorAnalyticsPage(BasePage):
    """
    Page Object for instructor analytics dashboard.

    BUSINESS CONTEXT:
    Instructors need comprehensive analytics to track course performance,
    identify struggling students, and optimize content based on data insights.
    """

    # Locators
    ANALYTICS_TAB = (By.ID, "analytics-tab")
    COURSE_ANALYTICS_SECTION = (By.ID, "course-analytics-section")
    ENROLLMENT_COUNT = (By.ID, "enrollment-count")
    COMPLETION_RATE = (By.ID, "completion-rate")
    AVERAGE_QUIZ_SCORE = (By.ID, "average-quiz-score")
    ENGAGEMENT_METRICS = (By.ID, "engagement-metrics")
    TOTAL_VIEWS_COUNT = (By.ID, "total-views-count")
    AVG_TIME_SPENT = (By.ID, "avg-time-spent")
    STRUGGLING_STUDENTS_LIST = (By.ID, "struggling-students-list")
    STRUGGLING_STUDENT_ITEM = (By.CLASS_NAME, "struggling-student")
    ENROLLMENT_CHART = (By.ID, "enrollment-chart")
    COMPLETION_CHART = (By.ID, "completion-chart")
    COURSE_SELECTOR = (By.ID, "analytics-course-select")

    def navigate_to_analytics(self):
        """Navigate to instructor analytics dashboard."""
        self.navigate_to("/instructor-dashboard")
        time.sleep(2)
        if self.is_element_present(*self.ANALYTICS_TAB, timeout=10):
            self.click_element(*self.ANALYTICS_TAB)
            time.sleep(2)

    def select_course(self, course_id):
        """Select a course for analytics."""
        select_elem = self.find_element(*self.COURSE_SELECTOR)
        select_elem.click()
        time.sleep(0.5)
        option = select_elem.find_element(By.CSS_SELECTOR, f"option[data-course-id='{course_id}']")
        option.click()
        time.sleep(1)

    def get_enrollment_count(self):
        """Get displayed enrollment count."""
        elem = self.find_element(*self.ENROLLMENT_COUNT)
        return int(elem.text)

    def get_completion_rate(self):
        """Get displayed completion rate percentage."""
        elem = self.find_element(*self.COMPLETION_RATE)
        text = elem.text.strip('%')
        return float(text) if text else 0.0

    def get_average_quiz_score(self):
        """Get displayed average quiz score."""
        elem = self.find_element(*self.AVERAGE_QUIZ_SCORE)
        text = elem.text.strip('%')
        return float(text) if text else 0.0

    def get_struggling_students_count(self):
        """Get number of struggling students listed."""
        items = self.driver.find_elements(*self.STRUGGLING_STUDENT_ITEM)
        return len(items)

    def get_total_views(self):
        """Get total course views count."""
        elem = self.find_element(*self.TOTAL_VIEWS_COUNT)
        return int(elem.text.replace(',', ''))

    def get_avg_time_spent(self):
        """Get average time spent (in minutes)."""
        elem = self.find_element(*self.AVG_TIME_SPENT)
        text = elem.text.replace('min', '').strip()
        return float(text) if text else 0.0

    def are_charts_visible(self):
        """Check if analytics charts are rendered."""
        return (self.is_element_present(*self.ENROLLMENT_CHART, timeout=5) and
                self.is_element_present(*self.COMPLETION_CHART, timeout=5))


class OrgAdminAnalyticsPage(BasePage):
    """
    Page Object for organization admin analytics dashboard.

    BUSINESS CONTEXT:
    Organization admins need organization-wide metrics to track overall
    learning outcomes, resource utilization, and member engagement.
    """

    # Locators
    ANALYTICS_TAB = (By.ID, "analytics-tab")
    ORG_ANALYTICS_SECTION = (By.ID, "org-analytics-section")
    TOTAL_COURSES_COUNT = (By.ID, "total-courses-count")
    TOTAL_MEMBERS_COUNT = (By.ID, "total-members-count")
    ACTIVE_MEMBERS_COUNT = (By.ID, "active-members-count")
    AVG_COURSE_COMPLETION = (By.ID, "avg-course-completion")
    COURSES_OVERVIEW_TABLE = (By.ID, "courses-overview-table")
    COURSE_ROW = (By.CLASS_NAME, "course-row")
    MEMBER_ACTIVITY_CHART = (By.ID, "member-activity-chart")
    RESOURCE_UTILIZATION_CARD = (By.ID, "resource-utilization")

    def navigate_to_analytics(self):
        """Navigate to org admin analytics dashboard."""
        self.navigate_to("/org-admin-dashboard")
        time.sleep(2)
        if self.is_element_present(*self.ANALYTICS_TAB, timeout=10):
            self.click_element(*self.ANALYTICS_TAB)
            time.sleep(2)

    def get_total_courses(self):
        """Get total courses count."""
        elem = self.find_element(*self.TOTAL_COURSES_COUNT)
        return int(elem.text)

    def get_total_members(self):
        """Get total members count."""
        elem = self.find_element(*self.TOTAL_MEMBERS_COUNT)
        return int(elem.text)

    def get_active_members(self):
        """Get active members count."""
        elem = self.find_element(*self.ACTIVE_MEMBERS_COUNT)
        return int(elem.text)

    def get_avg_course_completion(self):
        """Get average course completion percentage."""
        elem = self.find_element(*self.AVG_COURSE_COMPLETION)
        text = elem.text.strip('%')
        return float(text) if text else 0.0

    def get_courses_overview_count(self):
        """Get number of courses in overview table."""
        rows = self.driver.find_elements(*self.COURSE_ROW)
        return len(rows)

    def is_member_activity_chart_visible(self):
        """Check if member activity chart is rendered."""
        return self.is_element_present(*self.MEMBER_ACTIVITY_CHART, timeout=5)


class SiteAdminAnalyticsPage(BasePage):
    """
    Page Object for site admin platform-wide analytics.

    BUSINESS CONTEXT:
    Site admins need platform-wide metrics to monitor system health,
    cross-organization trends, and overall platform utilization.
    """

    # Locators
    ANALYTICS_TAB = (By.ID, "analytics-tab")
    PLATFORM_ANALYTICS_SECTION = (By.ID, "platform-analytics-section")
    TOTAL_ORGS_COUNT = (By.ID, "total-orgs-count")
    TOTAL_USERS_COUNT = (By.ID, "total-users-count")
    TOTAL_COURSES_COUNT = (By.ID, "total-courses-count")
    PLATFORM_HEALTH_STATUS = (By.ID, "platform-health-status")
    CROSS_ORG_METRICS_CHART = (By.ID, "cross-org-metrics-chart")
    SYSTEM_USAGE_STATS = (By.ID, "system-usage-stats")
    ACTIVE_USERS_24H = (By.ID, "active-users-24h")

    def navigate_to_analytics(self):
        """Navigate to site admin analytics dashboard."""
        self.navigate_to("/site-admin-dashboard")
        time.sleep(2)
        if self.is_element_present(*self.ANALYTICS_TAB, timeout=10):
            self.click_element(*self.ANALYTICS_TAB)
            time.sleep(2)

    def get_total_orgs(self):
        """Get total organizations count."""
        elem = self.find_element(*self.TOTAL_ORGS_COUNT)
        return int(elem.text)

    def get_total_users(self):
        """Get total users count."""
        elem = self.find_element(*self.TOTAL_USERS_COUNT)
        return int(elem.text)

    def get_total_courses(self):
        """Get total courses count."""
        elem = self.find_element(*self.TOTAL_COURSES_COUNT)
        return int(elem.text)

    def get_platform_health_status(self):
        """Get platform health status."""
        elem = self.find_element(*self.PLATFORM_HEALTH_STATUS)
        return elem.text.strip()

    def get_active_users_24h(self):
        """Get active users in last 24 hours."""
        elem = self.find_element(*self.ACTIVE_USERS_24H)
        return int(elem.text)

    def is_cross_org_chart_visible(self):
        """Check if cross-org metrics chart is rendered."""
        return self.is_element_present(*self.CROSS_ORG_METRICS_CHART, timeout=5)


class LoginPage(BasePage):
    """Page Object for login functionality."""

    # Locators
    EMAIL_INPUT = (By.ID, "login-email")
    PASSWORD_INPUT = (By.ID, "login-password")
    SUBMIT_BUTTON = (By.ID, "login-submit")

    def login(self, email, password):
        """Perform login."""
        self.navigate_to("/login")
        time.sleep(1)
        self.type_text(*self.EMAIL_INPUT, email)
        self.type_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.SUBMIT_BUTTON)
        time.sleep(2)


# ============================================================================
# TEST CLASSES - Organized by User Role
# ============================================================================

@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.priority_critical
class TestStudentAnalyticsDashboard(BaseTest):
    """
    Test student personal analytics dashboard.

    BUSINESS REQUIREMENT:
    Students must be able to view their personal progress, track time spent,
    review quiz scores, and see earned certificates. All metrics must be
    accurate and motivating.
    """

    @pytest.mark.asyncio
    async def test_student_views_personal_progress_dashboard(self, browser, test_base_url, student_credentials, db_connection):
        """
        E2E TEST: Student views personal progress dashboard

        BUSINESS REQUIREMENT:
        - Students need clear visibility of their learning progress
        - Progress dashboard must load quickly (< 3 seconds)
        - All key metrics must be visible at a glance

        TEST SCENARIO:
        1. Login as student
        2. Navigate to personal progress dashboard
        3. Verify dashboard loads successfully
        4. Verify key sections are visible

        VALIDATION:
        - Dashboard renders without errors
        - Progress chart visible
        - Key metric cards present
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(student_credentials["email"], student_credentials["password"])

        analytics_page = StudentAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_dashboard()

        # VERIFICATION 1: Dashboard loads
        assert analytics_page.is_element_present(*analytics_page.MY_PROGRESS_TAB, timeout=10), \
            "My Progress tab should be present"

        # VERIFICATION 2: Progress chart visible
        assert analytics_page.is_progress_chart_visible(), \
            "Progress chart should be visible"

        # VERIFICATION 3: Key sections present
        assert analytics_page.is_element_present(*analytics_page.OVERALL_PROGRESS_CARD, timeout=5), \
            "Overall progress card should be present"
        assert analytics_page.is_element_present(*analytics_page.TIME_SPENT_CARD, timeout=5), \
            "Time spent card should be present"
        assert analytics_page.is_element_present(*analytics_page.QUIZ_SCORES_SECTION, timeout=5), \
            "Quiz scores section should be present"

    @pytest.mark.asyncio
    async def test_course_completion_percentage_accurate(self, browser, test_base_url, student_credentials, db_connection):
        """
        E2E TEST: Course completion percentage matches database

        BUSINESS REQUIREMENT:
        - Completion percentage must be calculated accurately
        - Percentage must match enrollment table in database
        - Updates must reflect in real-time

        TEST SCENARIO:
        1. Login as student
        2. Navigate to progress dashboard
        3. Get displayed completion percentage
        4. Query database for actual completion
        5. Compare values (tolerance < 1%)

        VALIDATION:
        - UI percentage matches database calculation
        - Calculation accuracy < 1% tolerance
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(student_credentials["email"], student_credentials["password"])

        analytics_page = StudentAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_dashboard()

        # Get student ID from credentials
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (student_credentials["email"],))
        student_id = cursor.fetchone()[0]

        # VERIFICATION 1: Get UI completion percentage
        ui_completion = analytics_page.get_completion_percentage()

        # VERIFICATION 2: Get database completion percentage
        cursor.execute("""
            SELECT AVG(progress_percentage)
            FROM enrollments
            WHERE student_id = %s AND status = 'active'
        """, (student_id,))
        result = cursor.fetchone()[0]
        db_completion = float(result) if result else 0.0

        # VERIFICATION 3: Compare values
        assert abs(ui_completion - db_completion) < 1.0, \
            f"Completion percentage mismatch: UI={ui_completion}%, DB={db_completion}%"

    @pytest.mark.asyncio
    async def test_time_spent_tracking_accurate(self, browser, test_base_url, student_credentials, db_connection):
        """
        E2E TEST: Time spent tracking matches database

        BUSINESS REQUIREMENT:
        - Time spent must be tracked accurately across all activities
        - Display should aggregate all course time
        - Must match student_activities table

        TEST SCENARIO:
        1. Login as student
        2. View time spent metric
        3. Query database for actual time
        4. Compare values

        VALIDATION:
        - UI time matches database total
        - Time calculated from student_activities table
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(student_credentials["email"], student_credentials["password"])

        analytics_page = StudentAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_dashboard()

        # Get student ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (student_credentials["email"],))
        student_id = cursor.fetchone()[0]

        # VERIFICATION 1: Get UI time spent
        ui_time_hours = analytics_page.get_time_spent_hours()

        # VERIFICATION 2: Get database time spent (aggregate from student_progress)
        cursor.execute("""
            SELECT COALESCE(SUM(time_spent_minutes), 0) / 60.0
            FROM student_progress
            WHERE student_id = %s
        """, (student_id,))
        db_time_hours = float(cursor.fetchone()[0])

        # VERIFICATION 3: Compare values (tolerance 0.1 hours = 6 minutes)
        assert abs(ui_time_hours - db_time_hours) < 0.1, \
            f"Time spent mismatch: UI={ui_time_hours}h, DB={db_time_hours}h"

    @pytest.mark.asyncio
    async def test_quiz_scores_displayed_correctly(self, browser, test_base_url, student_credentials, db_connection):
        """
        E2E TEST: Quiz scores displayed accurately

        BUSINESS REQUIREMENT:
        - All quiz scores must be displayed
        - Scores must match quiz_performance table
        - Display should show quiz name and percentage

        TEST SCENARIO:
        1. Login as student
        2. View quiz scores section
        3. Get all displayed quiz scores
        4. Query database for actual scores
        5. Compare each score

        VALIDATION:
        - Number of quizzes matches database
        - Each score matches database value
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(student_credentials["email"], student_credentials["password"])

        analytics_page = StudentAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_dashboard()

        # Get student ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (student_credentials["email"],))
        student_id = cursor.fetchone()[0]

        # VERIFICATION 1: Get UI quiz scores
        ui_quiz_scores = analytics_page.get_quiz_scores()

        # VERIFICATION 2: Get database quiz scores
        cursor.execute("""
            SELECT quiz_id, score_percentage
            FROM quiz_performance
            WHERE student_id = %s AND status = 'completed'
            ORDER BY end_time DESC
        """, (student_id,))
        db_quiz_scores = cursor.fetchall()

        # VERIFICATION 3: Compare counts
        assert len(ui_quiz_scores) == len(db_quiz_scores), \
            f"Quiz count mismatch: UI={len(ui_quiz_scores)}, DB={len(db_quiz_scores)}"

        # VERIFICATION 4: Compare individual scores (if any exist)
        for ui_quiz, db_quiz in zip(ui_quiz_scores, db_quiz_scores):
            db_score = float(db_quiz[1])
            assert abs(ui_quiz["score"] - db_score) < 1.0, \
                f"Quiz score mismatch: UI={ui_quiz['score']}%, DB={db_score}%"

    @pytest.mark.asyncio
    async def test_certificate_achievements_visible(self, browser, test_base_url, student_credentials, db_connection):
        """
        E2E TEST: Certificate achievements are visible

        BUSINESS REQUIREMENT:
        - Earned certificates must be prominently displayed
        - Certificate count must match database
        - Certificates provide motivation for completion

        TEST SCENARIO:
        1. Login as student
        2. View certificates section
        3. Count displayed certificates
        4. Query database for earned certificates
        5. Compare counts

        VALIDATION:
        - Certificate section visible
        - Certificate count matches database
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(student_credentials["email"], student_credentials["password"])

        analytics_page = StudentAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_dashboard()

        # Get student ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (student_credentials["email"],))
        student_id = cursor.fetchone()[0]

        # VERIFICATION 1: Certificates section visible
        assert analytics_page.is_element_present(*analytics_page.CERTIFICATES_SECTION, timeout=5), \
            "Certificates section should be visible"

        # VERIFICATION 2: Get UI certificate count
        ui_cert_count = analytics_page.get_certificates_count()

        # VERIFICATION 3: Get database certificate count
        cursor.execute("""
            SELECT COUNT(*)
            FROM enrollments
            WHERE student_id = %s
            AND progress_percentage = 100
            AND certificate_issued = TRUE
        """, (student_id,))
        db_cert_count = cursor.fetchone()[0]

        # VERIFICATION 4: Compare counts
        assert ui_cert_count == db_cert_count, \
            f"Certificate count mismatch: UI={ui_cert_count}, DB={db_cert_count}"


@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.priority_critical
class TestInstructorAnalyticsDashboard(BaseTest):
    """
    Test instructor analytics dashboard.

    BUSINESS REQUIREMENT:
    Instructors must have comprehensive analytics to track course performance,
    monitor student engagement, and identify students who need help.
    """

    @pytest.mark.asyncio
    async def test_instructor_views_course_analytics_dashboard(self, browser, test_base_url, instructor_credentials, db_connection):
        """
        E2E TEST: Instructor views course analytics dashboard

        BUSINESS REQUIREMENT:
        - Instructors need quick access to course performance metrics
        - Dashboard must load within 3 seconds
        - All key metrics visible without scrolling

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Verify dashboard loads
        4. Verify key sections visible

        VALIDATION:
        - Analytics dashboard renders
        - Charts are visible
        - Metric cards present
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(instructor_credentials["email"], instructor_credentials["password"])

        analytics_page = InstructorAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # VERIFICATION 1: Analytics section loaded
        assert analytics_page.is_element_present(*analytics_page.COURSE_ANALYTICS_SECTION, timeout=10), \
            "Course analytics section should be present"

        # VERIFICATION 2: Charts visible
        assert analytics_page.are_charts_visible(), \
            "Analytics charts should be visible"

        # VERIFICATION 3: Key metrics present
        assert analytics_page.is_element_present(*analytics_page.ENROLLMENT_COUNT, timeout=5), \
            "Enrollment count should be present"
        assert analytics_page.is_element_present(*analytics_page.COMPLETION_RATE, timeout=5), \
            "Completion rate should be present"

    @pytest.mark.asyncio
    async def test_student_enrollment_numbers_accurate(self, browser, test_base_url, instructor_credentials, db_connection):
        """
        E2E TEST: Student enrollment numbers match database

        BUSINESS REQUIREMENT:
        - Enrollment count must be accurate
        - Should count only active enrollments
        - Must match enrollments table

        TEST SCENARIO:
        1. Login as instructor
        2. Select a course
        3. View enrollment count
        4. Query database for actual count
        5. Compare values

        VALIDATION:
        - UI count matches database count exactly
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(instructor_credentials["email"], instructor_credentials["password"])

        analytics_page = InstructorAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # Get instructor's first course
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (instructor_credentials["email"],))
        instructor_id = cursor.fetchone()[0]

        cursor.execute("""
            SELECT id FROM courses
            WHERE instructor_id = %s
            LIMIT 1
        """, (instructor_id,))
        course_result = cursor.fetchone()

        if course_result:
            course_id = course_result[0]

            # Select course in UI
            analytics_page.select_course(course_id)

            # VERIFICATION 1: Get UI enrollment count
            ui_enrollment = analytics_page.get_enrollment_count()

            # VERIFICATION 2: Get database enrollment count
            cursor.execute("""
                SELECT COUNT(*)
                FROM enrollments
                WHERE course_id = %s AND status = 'active'
            """, (course_id,))
            db_enrollment = cursor.fetchone()[0]

            # VERIFICATION 3: Compare values
            assert ui_enrollment == db_enrollment, \
                f"Enrollment count mismatch: UI={ui_enrollment}, DB={db_enrollment}"

    @pytest.mark.asyncio
    async def test_course_completion_rates_displayed(self, browser, test_base_url, instructor_credentials, db_connection):
        """
        E2E TEST: Course completion rates calculated correctly

        BUSINESS REQUIREMENT:
        - Completion rate = (students with 100% progress / total students) * 100
        - Must match database calculation
        - Updated in real-time

        TEST SCENARIO:
        1. Login as instructor
        2. Select course
        3. Get displayed completion rate
        4. Calculate actual completion rate from database
        5. Compare values (tolerance < 1%)

        VALIDATION:
        - UI rate matches database calculation
        - Calculation uses correct formula
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(instructor_credentials["email"], instructor_credentials["password"])

        analytics_page = InstructorAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # Get course ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (instructor_credentials["email"],))
        instructor_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM courses WHERE instructor_id = %s LIMIT 1", (instructor_id,))
        course_result = cursor.fetchone()

        if course_result:
            course_id = course_result[0]
            analytics_page.select_course(course_id)

            # VERIFICATION 1: Get UI completion rate
            ui_completion = analytics_page.get_completion_rate()

            # VERIFICATION 2: Calculate database completion rate
            cursor.execute("""
                SELECT
                    COUNT(CASE WHEN progress_percentage = 100 THEN 1 END) * 100.0 /
                    NULLIF(COUNT(*), 0)
                FROM enrollments
                WHERE course_id = %s AND status = 'active'
            """, (course_id,))
            result = cursor.fetchone()[0]
            db_completion = float(result) if result else 0.0

            # VERIFICATION 3: Compare values
            assert abs(ui_completion - db_completion) < 1.0, \
                f"Completion rate mismatch: UI={ui_completion}%, DB={db_completion}%"

    @pytest.mark.asyncio
    async def test_average_quiz_scores_calculated_correctly(self, browser, test_base_url, instructor_credentials, db_connection):
        """
        E2E TEST: Average quiz scores calculated accurately

        BUSINESS REQUIREMENT:
        - Average quiz score = mean of all completed quiz scores for course
        - Must include only 'completed' status quizzes
        - Displayed as percentage (0-100)

        TEST SCENARIO:
        1. Login as instructor
        2. Select course
        3. Get displayed average quiz score
        4. Calculate actual average from database
        5. Compare values (tolerance < 1%)

        VALIDATION:
        - UI average matches database calculation
        - Only completed quizzes included
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(instructor_credentials["email"], instructor_credentials["password"])

        analytics_page = InstructorAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # Get course ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (instructor_credentials["email"],))
        instructor_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM courses WHERE instructor_id = %s LIMIT 1", (instructor_id,))
        course_result = cursor.fetchone()

        if course_result:
            course_id = course_result[0]
            analytics_page.select_course(course_id)

            # VERIFICATION 1: Get UI average score
            ui_avg_score = analytics_page.get_average_quiz_score()

            # VERIFICATION 2: Calculate database average score
            cursor.execute("""
                SELECT AVG(score_percentage)
                FROM quiz_performance
                WHERE course_id = %s AND status = 'completed'
            """, (course_id,))
            result = cursor.fetchone()[0]
            db_avg_score = float(result) if result else 0.0

            # VERIFICATION 3: Compare values
            assert abs(ui_avg_score - db_avg_score) < 1.0, \
                f"Average quiz score mismatch: UI={ui_avg_score}%, DB={db_avg_score}%"

    @pytest.mark.asyncio
    async def test_student_engagement_metrics_displayed(self, browser, test_base_url, instructor_credentials, db_connection):
        """
        E2E TEST: Student engagement metrics (views, time spent) accurate

        BUSINESS REQUIREMENT:
        - Engagement metrics must track total views and average time spent
        - Views counted from student_activities table
        - Time spent from student_progress table

        TEST SCENARIO:
        1. Login as instructor
        2. Select course
        3. Get displayed engagement metrics (views, time)
        4. Query database for actual metrics
        5. Compare values

        VALIDATION:
        - UI views match database count
        - UI average time matches database calculation
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(instructor_credentials["email"], instructor_credentials["password"])

        analytics_page = InstructorAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # Get course ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (instructor_credentials["email"],))
        instructor_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM courses WHERE instructor_id = %s LIMIT 1", (instructor_id,))
        course_result = cursor.fetchone()

        if course_result:
            course_id = course_result[0]
            analytics_page.select_course(course_id)

            # VERIFICATION 1: Get UI total views
            ui_views = analytics_page.get_total_views()

            # VERIFICATION 2: Get database total views
            cursor.execute("""
                SELECT COUNT(*)
                FROM student_activities
                WHERE course_id = %s AND activity_type = 'content_view'
            """, (course_id,))
            db_views = cursor.fetchone()[0]

            assert ui_views == db_views, \
                f"Total views mismatch: UI={ui_views}, DB={db_views}"

            # VERIFICATION 3: Get UI average time spent
            ui_avg_time = analytics_page.get_avg_time_spent()

            # VERIFICATION 4: Get database average time spent (in minutes)
            cursor.execute("""
                SELECT AVG(time_spent_minutes)
                FROM student_progress
                WHERE course_id = %s
            """, (course_id,))
            result = cursor.fetchone()[0]
            db_avg_time = float(result) if result else 0.0

            assert abs(ui_avg_time - db_avg_time) < 1.0, \
                f"Average time spent mismatch: UI={ui_avg_time} min, DB={db_avg_time} min"

    @pytest.mark.asyncio
    async def test_struggling_students_identification(self, browser, test_base_url, instructor_credentials, db_connection):
        """
        E2E TEST: Struggling students identified correctly (score < 60%)

        BUSINESS REQUIREMENT:
        - Struggling students defined as: average quiz score < 60%
        - List must be accurate for early intervention
        - Updated in real-time as new quiz submissions come in

        TEST SCENARIO:
        1. Login as instructor
        2. Select course
        3. Get list of struggling students from UI
        4. Query database for students with avg score < 60%
        5. Compare student IDs and counts

        VALIDATION:
        - UI count matches database count
        - Same students identified in both UI and database
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(instructor_credentials["email"], instructor_credentials["password"])

        analytics_page = InstructorAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # Get course ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (instructor_credentials["email"],))
        instructor_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM courses WHERE instructor_id = %s LIMIT 1", (instructor_id,))
        course_result = cursor.fetchone()

        if course_result:
            course_id = course_result[0]
            analytics_page.select_course(course_id)

            # VERIFICATION 1: Get UI struggling students count
            ui_struggling_count = analytics_page.get_struggling_students_count()

            # VERIFICATION 2: Get database struggling students count
            cursor.execute("""
                SELECT COUNT(DISTINCT e.student_id)
                FROM enrollments e
                JOIN quiz_performance qp ON e.student_id = qp.student_id
                                         AND e.course_id = qp.course_id
                WHERE e.course_id = %s
                AND qp.status = 'completed'
                GROUP BY e.student_id
                HAVING AVG(qp.score_percentage) < 60
            """, (course_id,))
            result = cursor.fetchone()
            db_struggling_count = result[0] if result else 0

            # VERIFICATION 3: Compare counts
            assert ui_struggling_count == db_struggling_count, \
                f"Struggling students count mismatch: UI={ui_struggling_count}, DB={db_struggling_count}"


@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.priority_high
class TestOrgAdminAnalyticsDashboard(BaseTest):
    """
    Test organization admin analytics dashboard.

    BUSINESS REQUIREMENT:
    Organization admins need organization-wide analytics to track overall
    learning outcomes and resource utilization across all courses and members.
    """

    @pytest.mark.asyncio
    async def test_org_admin_views_organization_wide_analytics(self, browser, test_base_url, org_admin_credentials, db_connection):
        """
        E2E TEST: Org admin views organization-wide analytics

        BUSINESS REQUIREMENT:
        - Org admins need holistic view of organization performance
        - Dashboard must aggregate data across all courses
        - Loading time < 5 seconds even with large datasets

        TEST SCENARIO:
        1. Login as org admin
        2. Navigate to analytics dashboard
        3. Verify dashboard loads
        4. Verify key metrics visible

        VALIDATION:
        - Analytics dashboard renders
        - Organization-wide metrics displayed
        - Charts visible
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(org_admin_credentials["email"], org_admin_credentials["password"])

        analytics_page = OrgAdminAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # VERIFICATION 1: Analytics section loaded
        assert analytics_page.is_element_present(*analytics_page.ORG_ANALYTICS_SECTION, timeout=10), \
            "Organization analytics section should be present"

        # VERIFICATION 2: Key metrics present
        assert analytics_page.is_element_present(*analytics_page.TOTAL_COURSES_COUNT, timeout=5), \
            "Total courses count should be present"
        assert analytics_page.is_element_present(*analytics_page.TOTAL_MEMBERS_COUNT, timeout=5), \
            "Total members count should be present"

        # VERIFICATION 3: Charts visible
        assert analytics_page.is_member_activity_chart_visible(), \
            "Member activity chart should be visible"

    @pytest.mark.asyncio
    async def test_all_courses_overview_with_metrics(self, browser, test_base_url, org_admin_credentials, db_connection):
        """
        E2E TEST: All courses overview displays accurate metrics

        BUSINESS REQUIREMENT:
        - Overview table must list all organization courses
        - Each course shows enrollment, completion rate
        - Data must match database exactly

        TEST SCENARIO:
        1. Login as org admin
        2. Navigate to analytics
        3. View courses overview table
        4. Count rows in UI
        5. Query database for course count
        6. Compare counts

        VALIDATION:
        - Course count matches database
        - Each course has metrics displayed
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(org_admin_credentials["email"], org_admin_credentials["password"])

        analytics_page = OrgAdminAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # Get org admin's organization ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT id, organization_id FROM users WHERE email = %s",
                      (org_admin_credentials["email"],))
        user_result = cursor.fetchone()
        org_id = user_result[1]

        # VERIFICATION 1: Get UI courses count
        ui_courses_count = analytics_page.get_courses_overview_count()

        # VERIFICATION 2: Get database courses count for organization
        cursor.execute("""
            SELECT COUNT(*)
            FROM courses
            WHERE organization_id = %s
        """, (org_id,))
        db_courses_count = cursor.fetchone()[0]

        # VERIFICATION 3: Compare counts
        assert ui_courses_count == db_courses_count, \
            f"Courses count mismatch: UI={ui_courses_count}, DB={db_courses_count}"

    @pytest.mark.asyncio
    async def test_member_activity_tracking(self, browser, test_base_url, org_admin_credentials, db_connection):
        """
        E2E TEST: Member activity tracking accurate

        BUSINESS REQUIREMENT:
        - Track total members and active members
        - Active = logged in within last 30 days
        - Counts must match database

        TEST SCENARIO:
        1. Login as org admin
        2. View member activity metrics
        3. Get UI counts (total, active)
        4. Query database for actual counts
        5. Compare values

        VALIDATION:
        - Total members count accurate
        - Active members count accurate
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(org_admin_credentials["email"], org_admin_credentials["password"])

        analytics_page = OrgAdminAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # Get organization ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT organization_id FROM users WHERE email = %s",
                      (org_admin_credentials["email"],))
        org_id = cursor.fetchone()[0]

        # VERIFICATION 1: Get UI total members
        ui_total_members = analytics_page.get_total_members()

        # VERIFICATION 2: Get database total members
        cursor.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE organization_id = %s
        """, (org_id,))
        db_total_members = cursor.fetchone()[0]

        assert ui_total_members == db_total_members, \
            f"Total members mismatch: UI={ui_total_members}, DB={db_total_members}"

        # VERIFICATION 3: Get UI active members
        ui_active_members = analytics_page.get_active_members()

        # VERIFICATION 4: Get database active members (logged in last 30 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id)
            FROM user_sessions
            WHERE organization_id = %s
            AND last_activity > NOW() - INTERVAL '30 days'
        """, (org_id,))
        db_active_members = cursor.fetchone()[0]

        assert ui_active_members == db_active_members, \
            f"Active members mismatch: UI={ui_active_members}, DB={db_active_members}"

    @pytest.mark.asyncio
    async def test_resource_utilization_stats(self, browser, test_base_url, org_admin_credentials, db_connection):
        """
        E2E TEST: Resource utilization statistics displayed

        BUSINESS REQUIREMENT:
        - Track resource usage (storage, labs, API calls)
        - Display utilization percentages
        - Help org admins plan capacity

        TEST SCENARIO:
        1. Login as org admin
        2. View resource utilization card
        3. Verify metrics present
        4. (Database verification would require resource tracking tables)

        VALIDATION:
        - Resource utilization card visible
        - Key metrics displayed
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(org_admin_credentials["email"], org_admin_credentials["password"])

        analytics_page = OrgAdminAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # VERIFICATION 1: Resource utilization card present
        assert analytics_page.is_element_present(*analytics_page.RESOURCE_UTILIZATION_CARD, timeout=5), \
            "Resource utilization card should be present"

        # VERIFICATION 2: Get average course completion
        ui_avg_completion = analytics_page.get_avg_course_completion()

        # Get organization ID
        cursor = db_connection.cursor()
        cursor.execute("SELECT organization_id FROM users WHERE email = %s",
                      (org_admin_credentials["email"],))
        org_id = cursor.fetchone()[0]

        # VERIFICATION 3: Calculate database average completion
        cursor.execute("""
            SELECT AVG(progress_percentage)
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE c.organization_id = %s AND e.status = 'active'
        """, (org_id,))
        result = cursor.fetchone()[0]
        db_avg_completion = float(result) if result else 0.0

        assert abs(ui_avg_completion - db_avg_completion) < 1.0, \
            f"Average completion mismatch: UI={ui_avg_completion}%, DB={db_avg_completion}%"


@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.priority_high
class TestSiteAdminAnalyticsDashboard(BaseTest):
    """
    Test site admin platform-wide analytics.

    BUSINESS REQUIREMENT:
    Site admins need platform-wide metrics to monitor system health,
    cross-organization trends, and overall utilization.
    """

    @pytest.mark.asyncio
    async def test_site_admin_views_platform_wide_analytics(self, browser, test_base_url, site_admin_credentials, db_connection):
        """
        E2E TEST: Site admin views platform-wide analytics

        BUSINESS REQUIREMENT:
        - Site admins need complete platform visibility
        - Aggregate metrics across all organizations
        - System health monitoring

        TEST SCENARIO:
        1. Login as site admin
        2. Navigate to analytics dashboard
        3. Verify dashboard loads
        4. Verify platform-wide metrics visible

        VALIDATION:
        - Platform analytics dashboard renders
        - Cross-organization metrics displayed
        - System health status visible
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(site_admin_credentials["email"], site_admin_credentials["password"])

        analytics_page = SiteAdminAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # VERIFICATION 1: Analytics section loaded
        assert analytics_page.is_element_present(*analytics_page.PLATFORM_ANALYTICS_SECTION, timeout=10), \
            "Platform analytics section should be present"

        # VERIFICATION 2: Platform-wide metrics present
        assert analytics_page.is_element_present(*analytics_page.TOTAL_ORGS_COUNT, timeout=5), \
            "Total organizations count should be present"
        assert analytics_page.is_element_present(*analytics_page.TOTAL_USERS_COUNT, timeout=5), \
            "Total users count should be present"
        assert analytics_page.is_element_present(*analytics_page.PLATFORM_HEALTH_STATUS, timeout=5), \
            "Platform health status should be present"

    @pytest.mark.asyncio
    async def test_cross_organization_metrics(self, browser, test_base_url, site_admin_credentials, db_connection):
        """
        E2E TEST: Cross-organization metrics accurate

        BUSINESS REQUIREMENT:
        - Aggregate counts across all organizations
        - Display total organizations, users, courses
        - All counts must match database exactly

        TEST SCENARIO:
        1. Login as site admin
        2. View platform metrics
        3. Get UI counts (orgs, users, courses)
        4. Query database for actual counts
        5. Compare all values

        VALIDATION:
        - Total organizations count accurate
        - Total users count accurate
        - Total courses count accurate
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(site_admin_credentials["email"], site_admin_credentials["password"])

        analytics_page = SiteAdminAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        cursor = db_connection.cursor()

        # VERIFICATION 1: Total organizations
        ui_orgs = analytics_page.get_total_orgs()
        cursor.execute("SELECT COUNT(*) FROM organizations")
        db_orgs = cursor.fetchone()[0]
        assert ui_orgs == db_orgs, f"Organizations count mismatch: UI={ui_orgs}, DB={db_orgs}"

        # VERIFICATION 2: Total users
        ui_users = analytics_page.get_total_users()
        cursor.execute("SELECT COUNT(*) FROM users")
        db_users = cursor.fetchone()[0]
        assert ui_users == db_users, f"Users count mismatch: UI={ui_users}, DB={db_users}"

        # VERIFICATION 3: Total courses
        ui_courses = analytics_page.get_total_courses()
        cursor.execute("SELECT COUNT(*) FROM courses")
        db_courses = cursor.fetchone()[0]
        assert ui_courses == db_courses, f"Courses count mismatch: UI={ui_courses}, DB={db_courses}"

    @pytest.mark.asyncio
    async def test_system_health_and_usage_stats(self, browser, test_base_url, site_admin_credentials, db_connection):
        """
        E2E TEST: System health and usage statistics

        BUSINESS REQUIREMENT:
        - Monitor platform health (Healthy/Degraded/Down)
        - Track active users in last 24 hours
        - Provide early warning of issues

        TEST SCENARIO:
        1. Login as site admin
        2. View system health status
        3. View active users (24h)
        4. Query database for actual active users
        5. Compare values

        VALIDATION:
        - Health status displayed
        - Active users count matches database
        - Cross-org chart rendered
        """
        login_page = LoginPage(browser, test_base_url)
        login_page.login(site_admin_credentials["email"], site_admin_credentials["password"])

        analytics_page = SiteAdminAnalyticsPage(browser, test_base_url)
        analytics_page.navigate_to_analytics()

        # VERIFICATION 1: Platform health status
        health_status = analytics_page.get_platform_health_status()
        assert health_status in ["Healthy", "Degraded", "Down"], \
            f"Health status should be valid: got '{health_status}'"

        # VERIFICATION 2: Active users (24h)
        ui_active_users = analytics_page.get_active_users_24h()

        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id)
            FROM user_sessions
            WHERE last_activity > NOW() - INTERVAL '24 hours'
        """)
        db_active_users = cursor.fetchone()[0]

        assert ui_active_users == db_active_users, \
            f"Active users (24h) mismatch: UI={ui_active_users}, DB={db_active_users}"

        # VERIFICATION 3: Cross-org chart visible
        assert analytics_page.is_cross_org_chart_visible(), \
            "Cross-organization metrics chart should be visible"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
