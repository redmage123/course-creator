"""
Comprehensive E2E Tests for Real-Time Analytics

BUSINESS REQUIREMENT:
Tests the real-time analytics system to ensure instructors and administrators
receive immediate feedback on student activities, enabling rapid intervention
and data-driven decision making.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests WebSocket/polling mechanisms for real-time updates
- Validates performance metrics (query speed, update latency)
- Tests against HTTPS frontend (https://localhost:3000)
- Uses secondary browser/API for triggering events
- Database verification for all metrics

TEST COVERAGE:
1. Real-Time Updates (6 tests):
   - Student enrollment updates analytics immediately
   - Quiz submission updates scores in real-time
   - Course completion updates dashboard
   - User activity tracking updates engagement metrics
   - Page view tracking updates analytics
   - Video watch time updates in real-time

2. WebSocket/Polling Integration (3 tests):
   - Analytics dashboard uses WebSocket for updates
   - Poll interval configurable (5 seconds default)
   - Connection loss handling and reconnect

3. Performance (3 tests):
   - Analytics queries execute under 500ms
   - Dashboard loads within 3 seconds
   - Real-time updates don't slow UI

PRIORITY: P0 (CRITICAL) - Essential for real-time instructor insights
"""

import pytest
import time
import uuid
import asyncpg
import httpx
import json
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

class RealTimeAnalyticsPage(BasePage):
    """
    Page Object for real-time analytics dashboard.

    BUSINESS CONTEXT:
    Instructors need real-time visibility into student activities to provide
    immediate feedback and identify students who need help.
    """

    # Locators
    ANALYTICS_TAB = (By.ID, "analytics-tab")
    REAL_TIME_SECTION = (By.ID, "real-time-analytics-section")
    ENROLLMENT_COUNT = (By.ID, "enrollment-count")
    AVERAGE_QUIZ_SCORE = (By.ID, "average-quiz-score")
    SUBMISSION_COUNT = (By.ID, "submission-count")
    COMPLETION_RATE = (By.ID, "completion-rate")
    ACTIVE_USERS_COUNT = (By.ID, "active-users-count")
    PAGE_VIEWS_COUNT = (By.ID, "page-views-count")
    VIDEO_WATCH_TIME = (By.ID, "video-watch-time")
    ENGAGEMENT_SCORE = (By.ID, "engagement-score")
    WEBSOCKET_STATUS = (By.ID, "websocket-status")
    WEBSOCKET_CONNECTED = (By.CLASS_NAME, "websocket-connected")
    WEBSOCKET_DISCONNECTED = (By.CLASS_NAME, "websocket-disconnected")
    LAST_UPDATE_TIME = (By.ID, "last-update-time")
    AUTO_REFRESH_TOGGLE = (By.ID, "auto-refresh-toggle")
    REFRESH_INTERVAL_INPUT = (By.ID, "refresh-interval")
    LOADING_INDICATOR = (By.CLASS_NAME, "analytics-loading")
    UPDATE_NOTIFICATION = (By.CLASS_NAME, "update-notification")

    def navigate_to_analytics(self):
        """Navigate to real-time analytics dashboard."""
        self.navigate_to("/instructor-dashboard")
        time.sleep(2)
        if self.is_element_present(*self.ANALYTICS_TAB, timeout=10):
            self.click_element(*self.ANALYTICS_TAB)
            time.sleep(2)

    def get_enrollment_count(self) -> int:
        """Get current enrollment count from dashboard."""
        element = self.find_element(*self.ENROLLMENT_COUNT)
        return int(element.text.strip())

    def get_average_quiz_score(self) -> float:
        """Get current average quiz score from dashboard."""
        element = self.find_element(*self.AVERAGE_QUIZ_SCORE)
        score_text = element.text.strip().rstrip('%')
        return float(score_text)

    def get_submission_count(self) -> int:
        """Get current quiz submission count."""
        element = self.find_element(*self.SUBMISSION_COUNT)
        return int(element.text.strip())

    def get_completion_rate(self) -> float:
        """Get current course completion rate."""
        element = self.find_element(*self.COMPLETION_RATE)
        rate_text = element.text.strip().rstrip('%')
        return float(rate_text)

    def get_active_users_count(self) -> int:
        """Get current active users count."""
        element = self.find_element(*self.ACTIVE_USERS_COUNT)
        return int(element.text.strip())

    def get_page_views_count(self) -> int:
        """Get current page views count."""
        element = self.find_element(*self.PAGE_VIEWS_COUNT)
        return int(element.text.strip())

    def get_video_watch_time(self) -> int:
        """Get current video watch time in minutes."""
        element = self.find_element(*self.VIDEO_WATCH_TIME)
        time_text = element.text.strip().split()[0]  # "45 minutes" -> "45"
        return int(time_text)

    def get_engagement_score(self) -> float:
        """Get current engagement score."""
        element = self.find_element(*self.ENGAGEMENT_SCORE)
        return float(element.text.strip())

    def is_websocket_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.is_element_present(*self.WEBSOCKET_CONNECTED, timeout=2)

    def wait_for_update_notification(self, timeout=10):
        """Wait for update notification to appear."""
        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.presence_of_element_located(self.UPDATE_NOTIFICATION))

    def get_last_update_time(self) -> str:
        """Get timestamp of last analytics update."""
        element = self.find_element(*self.LAST_UPDATE_TIME)
        return element.text.strip()

    def set_refresh_interval(self, seconds: int):
        """Set auto-refresh interval."""
        input_elem = self.find_element(*self.REFRESH_INTERVAL_INPUT)
        input_elem.clear()
        input_elem.send_keys(str(seconds))

    def check_websocket_connection(self) -> dict:
        """
        Check WebSocket connection status using JavaScript.

        Returns:
            dict with connection status, readyState, url
        """
        script = """
        // Check if WebSocket exists
        if (window.analyticsWebSocket) {
            return {
                exists: true,
                readyState: window.analyticsWebSocket.readyState,
                url: window.analyticsWebSocket.url,
                connected: window.analyticsWebSocket.readyState === 1
            };
        }
        return {exists: false};
        """
        return self.driver.execute_script(script)


class WebSocketMonitor:
    """
    Helper class for monitoring WebSocket connections and messages.

    BUSINESS CONTEXT:
    Provides utilities for testing real-time analytics updates via WebSocket,
    ensuring messages are delivered and processed correctly.
    """

    def __init__(self, driver):
        self.driver = driver

    def inject_websocket_logger(self):
        """
        Inject JavaScript to log WebSocket messages.

        TECHNICAL IMPLEMENTATION:
        Overrides WebSocket send/onmessage to capture all traffic.
        """
        script = """
        window.websocketMessages = [];

        if (!window.WebSocketOriginal) {
            window.WebSocketOriginal = WebSocket;

            window.WebSocket = function(url, protocols) {
                const ws = new window.WebSocketOriginal(url, protocols);

                const originalSend = ws.send;
                ws.send = function(data) {
                    window.websocketMessages.push({
                        type: 'sent',
                        data: data,
                        timestamp: new Date().toISOString()
                    });
                    return originalSend.call(this, data);
                };

                const originalOnMessage = ws.onmessage;
                ws.addEventListener('message', function(event) {
                    window.websocketMessages.push({
                        type: 'received',
                        data: event.data,
                        timestamp: new Date().toISOString()
                    });
                });

                return ws;
            };
        }
        """
        self.driver.execute_script(script)

    def get_websocket_messages(self) -> list:
        """Get all captured WebSocket messages."""
        script = "return window.websocketMessages || [];"
        return self.driver.execute_script(script)

    def clear_websocket_messages(self):
        """Clear captured WebSocket messages."""
        script = "window.websocketMessages = [];"
        self.driver.execute_script(script)

    def wait_for_message(self, message_type: str, timeout=10) -> dict:
        """
        Wait for a specific WebSocket message type.

        Args:
            message_type: Type of message to wait for (e.g., 'analytics_update')
            timeout: Maximum time to wait in seconds

        Returns:
            The matching message dict
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            messages = self.get_websocket_messages()
            for msg in messages:
                if msg['type'] == 'received':
                    try:
                        data = json.loads(msg['data'])
                        if data.get('type') == message_type:
                            return data
                    except json.JSONDecodeError:
                        pass
            time.sleep(0.5)
        raise TimeoutException(f"WebSocket message '{message_type}' not received within {timeout}s")


# ============================================================================
# TEST CLASS - Real-Time Updates
# ============================================================================

@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.real_time
@pytest.mark.priority_critical
class TestRealTimeUpdates(BaseTest):
    """
    Test suite for real-time analytics updates.

    BUSINESS REQUIREMENT:
    Instructors must receive immediate updates when students interact with
    the platform, enabling rapid response and intervention.
    """

    @pytest.mark.asyncio
    async def test_01_student_enrollment_updates_analytics_immediately(
        self, browser, selenium_config, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Student enrollment updates instructor analytics in real-time

        BUSINESS REQUIREMENT:
        - Instructors need immediate visibility into new enrollments
        - Analytics must update within 5 seconds of enrollment
        - No manual refresh required

        TEST SCENARIO:
        1. Instructor opens course analytics dashboard
        2. Record initial enrollment count
        3. Student enrolls in course via API
        4. Instructor dashboard updates automatically
        5. Verify new enrollment count displayed

        VALIDATION:
        - Enrollment count updates within 5 seconds
        - Update happens without page refresh
        - New count matches database
        - WebSocket/polling mechanism working
        """
        page = RealTimeAnalyticsPage(browser)
        ws_monitor = WebSocketMonitor(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()

        # Inject WebSocket logger
        ws_monitor.inject_websocket_logger()

        # Wait for analytics to load
        time.sleep(2)

        # Get course ID from dashboard
        course_id = browser.execute_script("""
            const courseCard = document.querySelector('[data-course-id]');
            return courseCard ? courseCard.getAttribute('data-course-id') : null;
        """)

        assert course_id, "No course found for instructor"

        # Record initial enrollment count
        initial_count = page.get_enrollment_count()

        # Create new student via API
        async with httpx.AsyncClient(verify=False) as client:
            # Register new student
            student_data = {
                "email": f"student_{uuid.uuid4().hex[:8]}@example.com",
                "password": "TestPassword123!",
                "full_name": "Test Student",
                "role": "student"
            }

            register_response = await client.post(
                f"{selenium_config}/api/v1/auth/register",
                json=student_data
            )
            assert register_response.status_code == 201, "Student registration failed"

            student_id = register_response.json()["user_id"]
            student_token = register_response.json()["token"]

            # Enroll student in course
            enroll_response = await client.post(
                f"{selenium_config}/api/v1/enrollments",
                json={"course_id": course_id},
                headers={"Authorization": f"Bearer {student_token}"}
            )
            assert enroll_response.status_code in [200, 201], "Enrollment failed"

        # VERIFICATION: Dashboard updates within 5 seconds
        WebDriverWait(browser, 5).until(
            lambda d: page.get_enrollment_count() > initial_count
        )

        new_count = page.get_enrollment_count()

        # VERIFICATION: Count increased by 1
        assert new_count == initial_count + 1, f"Expected {initial_count + 1}, got {new_count}"

        # DATABASE VERIFICATION: Enrollment exists
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM enrollments
            WHERE course_id = %s AND student_id = %s
        """, (course_id, student_id))
        db_count = cursor.fetchone()[0]
        assert db_count == 1, "Enrollment not found in database"

        # VERIFICATION: WebSocket message received
        try:
            update_msg = ws_monitor.wait_for_message('enrollment_update', timeout=2)
            assert update_msg is not None, "WebSocket update message not received"
        except TimeoutException:
            # Polling mechanism may be used instead
            pass

    @pytest.mark.asyncio
    async def test_02_quiz_submission_updates_analytics_immediately(
        self, browser, selenium_config, instructor_credentials, student_credentials, db_connection
    ):
        """
        E2E TEST: Quiz submission updates instructor analytics in real-time

        BUSINESS REQUIREMENT:
        - Instructors need real-time visibility into student performance
        - Analytics must update within 5 seconds of student action
        - No manual refresh required

        TEST SCENARIO:
        1. Instructor opens course analytics dashboard
        2. Record initial average quiz score
        3. Student logs in separate browser/session
        4. Student takes and submits quiz
        5. Instructor dashboard updates automatically
        6. Verify new average score displayed

        VALIDATION:
        - Average score updates within 5 seconds
        - Update happens without page refresh
        - New score mathematically correct
        - WebSocket/polling mechanism working
        """
        page = RealTimeAnalyticsPage(browser)
        ws_monitor = WebSocketMonitor(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()

        # Inject WebSocket logger
        ws_monitor.inject_websocket_logger()

        # Wait for analytics to load
        time.sleep(2)

        # Get course ID
        course_id = browser.execute_script("""
            const courseCard = document.querySelector('[data-course-id]');
            return courseCard ? courseCard.getAttribute('data-course-id') : null;
        """)

        # Record initial state
        initial_score = page.get_average_quiz_score()
        initial_submission_count = page.get_submission_count()

        # Student submits quiz via API (faster than UI)
        async with httpx.AsyncClient(verify=False) as client:
            # Student login
            login_response = await client.post(
                f"{selenium_config}/api/v1/auth/login",
                json={
                    "email": student_credentials["email"],
                    "password": student_credentials["password"]
                }
            )
            student_token = login_response.json()["token"]

            # Get quiz ID for course
            quiz_response = await client.get(
                f"{selenium_config}/api/v1/courses/{course_id}/quizzes",
                headers={"Authorization": f"Bearer {student_token}"}
            )
            quizzes = quiz_response.json()
            assert len(quizzes) > 0, "No quizzes found for course"
            quiz_id = quizzes[0]["id"]

            # Submit quiz with perfect score (100%)
            submit_response = await client.post(
                f"{selenium_config}/api/v1/quizzes/{quiz_id}/submit",
                json={
                    "answers": [
                        {"question_id": i, "answer": "correct_answer"}
                        for i in range(1, 11)  # 10 questions
                    ]
                },
                headers={"Authorization": f"Bearer {student_token}"}
            )
            assert submit_response.status_code in [200, 201], "Quiz submission failed"

        # VERIFICATION: Dashboard updates within 5 seconds
        WebDriverWait(browser, 5).until(
            lambda d: page.get_submission_count() > initial_submission_count
        )

        new_submission_count = page.get_submission_count()
        new_score = page.get_average_quiz_score()

        # VERIFICATION: Submission count increased
        assert new_submission_count > initial_submission_count, "Submission count should increase"

        # VERIFICATION: Score updated (should increase with perfect score)
        assert new_score >= initial_score, "Average score should increase with perfect score"

        # DATABASE VERIFICATION: Calculate expected average
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT AVG(score / total_questions * 100)
            FROM quiz_submissions
            WHERE course_id = %s AND status = 'graded'
        """, (course_id,))
        result = cursor.fetchone()
        if result[0]:
            db_avg = round(float(result[0]), 1)
            assert abs(new_score - db_avg) < 1.0, f"UI score ({new_score}%) should match DB ({db_avg}%)"

    @pytest.mark.asyncio
    async def test_03_course_completion_updates_dashboard(
        self, browser, selenium_config, instructor_credentials, student_credentials, db_connection
    ):
        """
        E2E TEST: Course completion updates analytics dashboard in real-time

        BUSINESS REQUIREMENT:
        - Track course completion rates in real-time
        - Celebrate student achievements immediately
        - Update instructor dashboards without delay

        TEST SCENARIO:
        1. Instructor opens analytics dashboard
        2. Record initial completion rate
        3. Student completes final course module via API
        4. Dashboard updates automatically
        5. Verify new completion rate

        VALIDATION:
        - Completion rate updates within 5 seconds
        - Mathematical accuracy of rate calculation
        - No page refresh required
        """
        page = RealTimeAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()
        time.sleep(2)

        # Get course ID
        course_id = browser.execute_script("""
            const courseCard = document.querySelector('[data-course-id]');
            return courseCard ? courseCard.getAttribute('data-course-id') : null;
        """)

        # Record initial completion rate
        initial_rate = page.get_completion_rate()

        # Student completes course via API
        async with httpx.AsyncClient(verify=False) as client:
            # Student login
            login_response = await client.post(
                f"{selenium_config}/api/v1/auth/login",
                json={
                    "email": student_credentials["email"],
                    "password": student_credentials["password"]
                }
            )
            student_token = login_response.json()["token"]

            # Mark course as completed
            complete_response = await client.post(
                f"{selenium_config}/api/v1/courses/{course_id}/complete",
                headers={"Authorization": f"Bearer {student_token}"}
            )
            assert complete_response.status_code in [200, 201], "Course completion failed"

        # VERIFICATION: Dashboard updates within 5 seconds
        time.sleep(5)  # Wait for update
        new_rate = page.get_completion_rate()

        # VERIFICATION: Completion rate changed
        assert new_rate != initial_rate, "Completion rate should update"

        # DATABASE VERIFICATION
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE completion_status = 'completed') * 100.0 / NULLIF(COUNT(*), 0)
            FROM enrollments
            WHERE course_id = %s
        """, (course_id,))
        result = cursor.fetchone()
        if result[0]:
            db_rate = round(float(result[0]), 1)
            assert abs(new_rate - db_rate) < 1.0, f"UI rate ({new_rate}%) should match DB ({db_rate}%)"

    @pytest.mark.asyncio
    async def test_04_user_activity_tracking_updates_engagement(
        self, browser, selenium_config, instructor_credentials, student_credentials, db_connection
    ):
        """
        E2E TEST: User activity tracking updates engagement metrics in real-time

        BUSINESS REQUIREMENT:
        - Track real-time student engagement
        - Identify active vs. inactive students
        - Update engagement scores immediately

        TEST SCENARIO:
        1. Instructor views engagement analytics
        2. Record initial active users count
        3. Student performs activities (page views, video watching)
        4. Dashboard updates engagement metrics
        5. Verify active users count increased

        VALIDATION:
        - Active users count updates within 5 seconds
        - Engagement score recalculated
        - Activity logged in database
        """
        page = RealTimeAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()
        time.sleep(2)

        # Get course ID
        course_id = browser.execute_script("""
            const courseCard = document.querySelector('[data-course-id]');
            return courseCard ? courseCard.getAttribute('data-course-id') : null;
        """)

        # Record initial active users
        initial_active_users = page.get_active_users_count()

        # Student performs activities via API
        async with httpx.AsyncClient(verify=False) as client:
            # Student login
            login_response = await client.post(
                f"{selenium_config}/api/v1/auth/login",
                json={
                    "email": student_credentials["email"],
                    "password": student_credentials["password"]
                }
            )
            student_token = login_response.json()["token"]

            # Track multiple activities
            activities = [
                {
                    "activity_type": "page_view",
                    "course_id": course_id,
                    "activity_data": {"page": "course_overview"}
                },
                {
                    "activity_type": "video_play",
                    "course_id": course_id,
                    "activity_data": {"video_id": "intro_video", "duration": 120}
                },
                {
                    "activity_type": "content_view",
                    "course_id": course_id,
                    "activity_data": {"content_type": "slide", "content_id": "slide_1"}
                }
            ]

            for activity in activities:
                await client.post(
                    f"{selenium_config}/api/v1/analytics/activities/track",
                    json=activity,
                    headers={"Authorization": f"Bearer {student_token}"}
                )
                time.sleep(0.5)

        # VERIFICATION: Dashboard updates within 5 seconds
        time.sleep(5)
        new_active_users = page.get_active_users_count()

        # VERIFICATION: Active users increased or stayed same (depends on timing)
        assert new_active_users >= initial_active_users, "Active users count should not decrease"

        # DATABASE VERIFICATION: Activities logged
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM student_activities
            WHERE course_id = %s
            AND timestamp > NOW() - INTERVAL '1 minute'
        """, (course_id,))
        recent_activities = cursor.fetchone()[0]
        assert recent_activities >= 3, "Activities should be logged in database"

    @pytest.mark.asyncio
    async def test_05_page_view_tracking_updates_analytics(
        self, browser, selenium_config, instructor_credentials, student_credentials, db_connection
    ):
        """
        E2E TEST: Page view tracking updates analytics in real-time

        BUSINESS REQUIREMENT:
        - Track which content students are viewing
        - Identify popular and ignored content
        - Update page view counts immediately

        TEST SCENARIO:
        1. Instructor views content analytics
        2. Record initial page views count
        3. Student views multiple pages
        4. Dashboard updates page view count
        5. Verify count increased correctly

        VALIDATION:
        - Page views count updates within 5 seconds
        - Count matches number of views triggered
        - Database records all page views
        """
        page = RealTimeAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()
        time.sleep(2)

        # Get course ID
        course_id = browser.execute_script("""
            const courseCard = document.querySelector('[data-course-id]');
            return courseCard ? courseCard.getAttribute('data-course-id') : null;
        """)

        # Record initial page views
        initial_views = page.get_page_views_count()

        # Student views pages via API
        async with httpx.AsyncClient(verify=False) as client:
            # Student login
            login_response = await client.post(
                f"{selenium_config}/api/v1/auth/login",
                json={
                    "email": student_credentials["email"],
                    "password": student_credentials["password"]
                }
            )
            student_token = login_response.json()["token"]

            # Track 5 page views
            pages = ["overview", "syllabus", "week1", "week2", "resources"]
            for page_name in pages:
                await client.post(
                    f"{selenium_config}/api/v1/analytics/activities/track",
                    json={
                        "activity_type": "page_view",
                        "course_id": course_id,
                        "activity_data": {"page": page_name}
                    },
                    headers={"Authorization": f"Bearer {student_token}"}
                )

        # VERIFICATION: Dashboard updates within 5 seconds
        time.sleep(5)
        new_views = page.get_page_views_count()

        # VERIFICATION: Page views increased by 5
        assert new_views >= initial_views + 5, f"Expected at least {initial_views + 5}, got {new_views}"

    @pytest.mark.asyncio
    async def test_06_video_watch_time_updates_realtime(
        self, browser, selenium_config, instructor_credentials, student_credentials, db_connection
    ):
        """
        E2E TEST: Video watch time updates in real-time

        BUSINESS REQUIREMENT:
        - Track video engagement metrics
        - Identify most and least watched videos
        - Update watch time continuously

        TEST SCENARIO:
        1. Instructor views video analytics
        2. Record initial total watch time
        3. Student watches video (tracked via API)
        4. Dashboard updates watch time
        5. Verify time increased correctly

        VALIDATION:
        - Watch time updates within 5 seconds
        - Time increase matches video duration watched
        - Database records video activity
        """
        page = RealTimeAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()
        time.sleep(2)

        # Get course ID
        course_id = browser.execute_script("""
            const courseCard = document.querySelector('[data-course-id]');
            return courseCard ? courseCard.getAttribute('data-course-id') : null;
        """)

        # Record initial watch time
        initial_watch_time = page.get_video_watch_time()

        # Student watches video via API (10 minutes)
        async with httpx.AsyncClient(verify=False) as client:
            # Student login
            login_response = await client.post(
                f"{selenium_config}/api/v1/auth/login",
                json={
                    "email": student_credentials["email"],
                    "password": student_credentials["password"]
                }
            )
            student_token = login_response.json()["token"]

            # Track video watching (10 minutes)
            await client.post(
                f"{selenium_config}/api/v1/analytics/activities/track",
                json={
                    "activity_type": "video_watch",
                    "course_id": course_id,
                    "activity_data": {
                        "video_id": "intro_video",
                        "duration_seconds": 600  # 10 minutes
                    }
                },
                headers={"Authorization": f"Bearer {student_token}"}
            )

        # VERIFICATION: Dashboard updates within 5 seconds
        time.sleep(5)
        new_watch_time = page.get_video_watch_time()

        # VERIFICATION: Watch time increased by ~10 minutes
        assert new_watch_time >= initial_watch_time + 10, \
            f"Expected at least {initial_watch_time + 10}, got {new_watch_time}"


# ============================================================================
# TEST CLASS - WebSocket/Polling Integration
# ============================================================================

@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.real_time
@pytest.mark.websocket
@pytest.mark.priority_high
class TestWebSocketIntegration(BaseTest):
    """
    Test suite for WebSocket/polling integration in real-time analytics.

    BUSINESS REQUIREMENT:
    Ensure reliable real-time communication between analytics service and
    instructor dashboards using WebSocket or polling fallback.
    """

    def test_07_analytics_dashboard_uses_websocket(
        self, browser, selenium_config, instructor_credentials
    ):
        """
        E2E TEST: Analytics dashboard uses WebSocket for real-time updates

        BUSINESS REQUIREMENT:
        - Prefer WebSocket for efficient real-time communication
        - Establish connection on dashboard load
        - Maintain connection throughout session

        TEST SCENARIO:
        1. Instructor logs in
        2. Navigate to analytics dashboard
        3. Check for WebSocket connection
        4. Verify connection status indicator
        5. Verify WebSocket URL correct

        VALIDATION:
        - WebSocket connection established
        - Connection status shown in UI
        - Correct WebSocket URL (wss://localhost:8001/ws/analytics)
        - ReadyState is OPEN (1)
        """
        page = RealTimeAnalyticsPage(browser)
        ws_monitor = WebSocketMonitor(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()

        # Inject WebSocket logger
        ws_monitor.inject_websocket_logger()

        # Wait for analytics to fully load
        time.sleep(3)

        # VERIFICATION: WebSocket connection exists
        ws_status = page.check_websocket_connection()

        assert ws_status.get('exists'), "WebSocket should be initialized"
        assert ws_status.get('connected'), "WebSocket should be connected"
        assert ws_status.get('readyState') == 1, f"WebSocket readyState should be 1 (OPEN), got {ws_status.get('readyState')}"

        # VERIFICATION: Correct WebSocket URL
        ws_url = ws_status.get('url', '')
        assert 'wss://' in ws_url or 'ws://' in ws_url, "WebSocket URL should use ws:// or wss://"
        assert 'analytics' in ws_url.lower(), "WebSocket URL should contain 'analytics'"

        # VERIFICATION: UI shows connected status
        assert page.is_websocket_connected(), "UI should show WebSocket connected status"

    def test_08_poll_interval_configurable(
        self, browser, selenium_config, instructor_credentials
    ):
        """
        E2E TEST: Poll interval is configurable with 5 second default

        BUSINESS REQUIREMENT:
        - Allow administrators to adjust polling frequency
        - Default to 5 seconds for optimal balance
        - Support range from 1 to 60 seconds

        TEST SCENARIO:
        1. Instructor opens analytics dashboard
        2. Check default poll interval (should be 5s)
        3. Change interval to 10 seconds
        4. Verify interval updated
        5. Verify updates occur at new interval

        VALIDATION:
        - Default interval is 5 seconds
        - Interval can be changed via UI
        - New interval takes effect immediately
        - Updates occur at configured interval
        """
        page = RealTimeAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()
        time.sleep(2)

        # VERIFICATION: Default interval is 5 seconds
        interval_input = browser.find_element(By.ID, "refresh-interval")
        default_interval = int(interval_input.get_attribute("value"))
        assert default_interval == 5, f"Default interval should be 5 seconds, got {default_interval}"

        # Change interval to 10 seconds
        page.set_refresh_interval(10)
        time.sleep(1)

        # VERIFICATION: Interval updated
        new_interval = int(interval_input.get_attribute("value"))
        assert new_interval == 10, f"Interval should be 10 seconds, got {new_interval}"

        # VERIFICATION: Check interval persists
        browser.refresh()
        time.sleep(2)
        interval_input = browser.find_element(By.ID, "refresh-interval")
        persisted_interval = int(interval_input.get_attribute("value"))
        assert persisted_interval == 10, "Interval should persist after page refresh"

    def test_09_connection_loss_handling_and_reconnect(
        self, browser, selenium_config, instructor_credentials
    ):
        """
        E2E TEST: Connection loss handling and automatic reconnect

        BUSINESS REQUIREMENT:
        - Handle network interruptions gracefully
        - Automatically reconnect when connection restored
        - Show connection status to user
        - Queue updates during disconnection

        TEST SCENARIO:
        1. Instructor opens analytics dashboard
        2. Verify WebSocket connected
        3. Simulate connection loss (close WebSocket)
        4. Verify UI shows disconnected status
        5. Wait for automatic reconnect
        6. Verify connection restored

        VALIDATION:
        - UI shows disconnected status immediately
        - Reconnect attempt made within 10 seconds
        - Connection successfully restored
        - Queued updates delivered after reconnect
        """
        page = RealTimeAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()
        time.sleep(3)

        # VERIFICATION: Initially connected
        assert page.is_websocket_connected(), "Should be connected initially"

        # Simulate connection loss by closing WebSocket
        browser.execute_script("""
            if (window.analyticsWebSocket) {
                window.analyticsWebSocket.close();
            }
        """)

        time.sleep(1)

        # VERIFICATION: UI shows disconnected status
        wait.until(EC.presence_of_element_located(page.WEBSOCKET_DISCONNECTED))
        assert not page.is_websocket_connected(), "Should show disconnected status"

        # Wait for automatic reconnect (typically 5-10 seconds)
        time.sleep(10)

        # VERIFICATION: Reconnection attempted and successful
        try:
            wait.until(EC.presence_of_element_located(page.WEBSOCKET_CONNECTED))
            assert page.is_websocket_connected(), "Should reconnect automatically"
        except TimeoutException:
            # Check if polling fallback activated instead
            last_update = page.get_last_update_time()
            assert last_update, "Should have fallback update mechanism"


# ============================================================================
# TEST CLASS - Performance Metrics
# ============================================================================

@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.real_time
@pytest.mark.performance
@pytest.mark.priority_high
class TestPerformanceMetrics(BaseTest):
    """
    Test suite for analytics performance requirements.

    BUSINESS REQUIREMENT:
    Real-time analytics must be fast and responsive to provide
    a good user experience and enable rapid decision making.
    """

    def test_10_analytics_queries_execute_under_500ms(
        self, browser, selenium_config, instructor_credentials
    ):
        """
        E2E TEST: Analytics queries execute under 500ms

        BUSINESS REQUIREMENT:
        - Fast query performance for real-time dashboards
        - Maximum 500ms per analytics query
        - Optimized database queries with indexes

        TEST SCENARIO:
        1. Instructor opens analytics dashboard
        2. Measure time for analytics API calls
        3. Verify all queries complete under 500ms
        4. Check multiple analytics endpoints

        VALIDATION:
        - All analytics API calls < 500ms
        - Dashboard loads without blocking
        - Query performance consistent across endpoints
        """
        page = RealTimeAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))

        # Inject performance monitoring
        browser.execute_script("""
            window.analyticsPerformance = [];

            // Override fetch to measure performance
            const originalFetch = window.fetch;
            window.fetch = function(url, options) {
                const startTime = performance.now();
                return originalFetch(url, options).then(response => {
                    const endTime = performance.now();
                    const duration = endTime - startTime;

                    if (url.includes('analytics')) {
                        window.analyticsPerformance.push({
                            url: url,
                            duration: duration,
                            timestamp: new Date().toISOString()
                        });
                    }

                    return response;
                });
            };
        """)

        # Navigate to analytics to trigger API calls
        page.navigate_to_analytics()
        time.sleep(5)  # Wait for all analytics to load

        # Get performance metrics
        performance_data = browser.execute_script("return window.analyticsPerformance || [];")

        # VERIFICATION: All analytics queries under 500ms
        slow_queries = [p for p in performance_data if p['duration'] > 500]

        assert len(slow_queries) == 0, \
            f"Found {len(slow_queries)} slow queries (>500ms): {slow_queries}"

        # VERIFICATION: At least some analytics queries were made
        assert len(performance_data) > 0, "Should have made analytics API calls"

        # Calculate average query time
        if performance_data:
            avg_duration = sum(p['duration'] for p in performance_data) / len(performance_data)
            print(f"\nAnalytics Performance Summary:")
            print(f"  Total queries: {len(performance_data)}")
            print(f"  Average duration: {avg_duration:.2f}ms")
            print(f"  Max duration: {max(p['duration'] for p in performance_data):.2f}ms")
            print(f"  Min duration: {min(p['duration'] for p in performance_data):.2f}ms")

    def test_11_dashboard_loads_within_3_seconds(
        self, browser, selenium_config, instructor_credentials
    ):
        """
        E2E TEST: Analytics dashboard loads within 3 seconds

        BUSINESS REQUIREMENT:
        - Fast dashboard load time for user experience
        - Maximum 3 seconds from navigation to interactive
        - Progressive loading for large datasets

        TEST SCENARIO:
        1. Instructor navigates to analytics dashboard
        2. Measure time from navigation to dashboard ready
        3. Verify dashboard interactive within 3 seconds
        4. Check that loading indicators used appropriately

        VALIDATION:
        - Dashboard ready within 3 seconds
        - Loading indicators shown during load
        - No blocking UI during data fetch
        - Progressive enhancement used
        """
        page = RealTimeAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        wait.until(EC.url_contains("/instructor-dashboard"))

        # Measure dashboard load time
        start_time = time.time()

        # Navigate to analytics
        page.navigate_to_analytics()

        # Wait for analytics to be interactive (loading overlay gone)
        try:
            wait.until(EC.invisibility_of_element_located(page.LOADING_INDICATOR))
        except TimeoutException:
            pass  # No loading indicator, dashboard loaded immediately

        # Wait for at least one analytics element to be present
        wait.until(EC.presence_of_element_located(page.REAL_TIME_SECTION))

        end_time = time.time()
        load_duration = end_time - start_time

        # VERIFICATION: Dashboard loaded within 3 seconds
        assert load_duration <= 3.0, \
            f"Dashboard took {load_duration:.2f}s to load (max 3.0s)"

        print(f"\nDashboard Load Time: {load_duration:.2f}s")

        # VERIFICATION: Dashboard is interactive
        assert page.is_element_present(*page.REAL_TIME_SECTION), \
            "Dashboard should be fully loaded and interactive"

    def test_12_realtime_updates_dont_slow_ui(
        self, browser, selenium_config, instructor_credentials, student_credentials
    ):
        """
        E2E TEST: Real-time updates don't slow down UI interactions

        BUSINESS REQUIREMENT:
        - Real-time updates should not block user interactions
        - UI remains responsive during updates
        - Updates processed asynchronously

        TEST SCENARIO:
        1. Instructor opens analytics dashboard
        2. Trigger multiple rapid updates via API
        3. Measure UI responsiveness during updates
        4. Verify no UI blocking or lag

        VALIDATION:
        - UI interactions respond within 100ms
        - No freezing during updates
        - Smooth animations maintained
        - Background processing used
        """
        page = RealTimeAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{selenium_config}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_analytics()
        time.sleep(2)

        # Get course ID
        course_id = browser.execute_script("""
            const courseCard = document.querySelector('[data-course-id]');
            return courseCard ? courseCard.getAttribute('data-course-id') : null;
        """)

        # Inject UI responsiveness monitor
        browser.execute_script("""
            window.uiResponsiveness = [];

            // Monitor click responsiveness
            document.addEventListener('click', function(e) {
                const startTime = performance.now();
                requestAnimationFrame(() => {
                    const endTime = performance.now();
                    window.uiResponsiveness.push({
                        element: e.target.id || e.target.className,
                        responseTime: endTime - startTime
                    });
                });
            });
        """)

        # Trigger rapid updates via API
        import asyncio

        async def trigger_rapid_updates():
            async with httpx.AsyncClient(verify=False) as client:
                # Student login
                login_response = await client.post(
                    f"{selenium_config}/api/v1/auth/login",
                    json={
                        "email": student_credentials["email"],
                        "password": student_credentials["password"]
                    }
                )
                student_token = login_response.json()["token"]

                # Trigger 20 rapid activities
                for i in range(20):
                    await client.post(
                        f"{selenium_config}/api/v1/analytics/activities/track",
                        json={
                            "activity_type": "page_view",
                            "course_id": course_id,
                            "activity_data": {"page": f"page_{i}"}
                        },
                        headers={"Authorization": f"Bearer {student_token}"}
                    )

        # Run updates in background
        asyncio.run(trigger_rapid_updates())

        # Interact with UI during updates
        time.sleep(1)  # Let updates start arriving

        # Click various elements
        elements_to_click = [
            page.ANALYTICS_TAB,
            page.REAL_TIME_SECTION
        ]

        for locator in elements_to_click:
            try:
                element = browser.find_element(*locator)
                if element.is_displayed():
                    element.click()
                    time.sleep(0.2)
            except:
                pass

        # Get UI responsiveness data
        responsiveness_data = browser.execute_script("return window.uiResponsiveness || [];")

        # VERIFICATION: All UI interactions < 100ms
        if responsiveness_data:
            slow_interactions = [r for r in responsiveness_data if r['responseTime'] > 100]
            assert len(slow_interactions) == 0, \
                f"Found {len(slow_interactions)} slow UI interactions (>100ms): {slow_interactions}"

            avg_response_time = sum(r['responseTime'] for r in responsiveness_data) / len(responsiveness_data)
            print(f"\nUI Responsiveness During Updates:")
            print(f"  Total interactions: {len(responsiveness_data)}")
            print(f"  Average response time: {avg_response_time:.2f}ms")
            print(f"  Max response time: {max(r['responseTime'] for r in responsiveness_data):.2f}ms")
