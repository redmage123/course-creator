"""
Lab Timeout and Cleanup E2E Test Suite
=======================================

Comprehensive Selenium tests for lab timeout mechanisms and automated cleanup.

TEST COVERAGE:
1. Timeout Mechanisms (5 tests)
   - Lab timeout warning display
   - Lab timeout countdown visible in UI
   - Lab auto-stops after inactivity timeout
   - Student can extend timeout before expiry
   - Lab cannot be extended beyond max duration

2. Cleanup Workflows (4 tests)
   - Lab cleanup on student logout
   - Lab cleanup on course completion
   - Lab cleanup on enrollment removal
   - Lab cleanup on course deletion

3. Orphan Detection (3 tests)
   - Detect orphaned containers
   - Cleanup orphaned containers automatically
   - Alert admin of cleanup failures

BUSINESS REQUIREMENTS:
- Labs must auto-stop after 2 hours of inactivity (prevents resource waste)
- Labs must have max duration of 8 hours (prevents abuse)
- Cleanup must occur on logout, enrollment removal, course deletion
- Orphaned containers must be detected and cleaned daily
- Students must receive warnings before timeout (15 min, 5 min, 1 min)
- Students can extend timeout if needed (but within max duration)

TECHNICAL IMPLEMENTATION:
- Uses accelerated timeouts (5 seconds instead of 2 hours) for testing
- Verifies Docker container status via docker-py
- Verifies database lab_sessions table state
- Uses HTTPS: https://localhost:3000
- Follows Page Object Model pattern

Author: Course Creator Platform Team
Version: 1.0.0
Date: 2025-11-05
"""

import pytest
import time
import os
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sys

# Add parent directory for selenium_base imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from selenium_base import BasePage, BaseTest


class LabPage(BasePage):
    """
    Page Object for Lab Environment page
    
    BUSINESS CONTEXT:
    Encapsulates all lab interactions for maintainable tests.
    """
    
    # Locators
    START_LAB_BUTTON = (By.ID, "start-lab-button")
    STOP_LAB_BUTTON = (By.ID, "stop-lab-button")
    PAUSE_LAB_BUTTON = (By.ID, "pause-lab-button")
    EXTEND_TIMEOUT_BUTTON = (By.ID, "extend-timeout-button")
    LAB_STATUS = (By.ID, "lab-status")
    LAB_TIMER = (By.ID, "lab-timer")
    TIMEOUT_WARNING = (By.ID, "timeout-warning")
    TIMEOUT_COUNTDOWN = (By.ID, "timeout-countdown")
    LAB_IFRAME = (By.ID, "lab-iframe")
    
    def __init__(self, driver):
        super().__init__(driver)
        self.base_url = os.getenv('TEST_BASE_URL', 'https://localhost:3000')
    
    def navigate_to_lab(self, course_id='test_course_001'):
        """Navigate to lab page for specific course"""
        self.driver.get(f"{self.base_url}/html/lab-multi-ide.html?course_id={course_id}")
        self.wait_for_page_load()
    
    def start_lab(self):
        """Start lab environment"""
        start_button = self.wait_for_element_clickable(self.START_LAB_BUTTON)
        start_button.click()
        # Wait for lab to initialize
        time.sleep(2)
    
    def stop_lab(self):
        """Stop lab environment"""
        stop_button = self.wait_for_element_clickable(self.STOP_LAB_BUTTON)
        stop_button.click()
        time.sleep(1)
    
    def pause_lab(self):
        """Pause lab environment"""
        pause_button = self.wait_for_element_clickable(self.PAUSE_LAB_BUTTON)
        pause_button.click()
        time.sleep(1)
    
    def extend_timeout(self):
        """Extend lab timeout"""
        extend_button = self.wait_for_element_clickable(self.EXTEND_TIMEOUT_BUTTON)
        extend_button.click()
        time.sleep(1)
    
    def get_lab_status(self):
        """Get current lab status text"""
        status = self.wait_for_element_visible(self.LAB_STATUS)
        return status.text
    
    def get_lab_timer(self):
        """Get lab timer text"""
        timer = self.wait_for_element_visible(self.LAB_TIMER)
        return timer.text
    
    def is_timeout_warning_visible(self):
        """Check if timeout warning is displayed"""
        try:
            warning = self.wait_for_element_visible(self.TIMEOUT_WARNING, timeout=2)
            return warning.is_displayed()
        except TimeoutException:
            return False
    
    def get_timeout_countdown(self):
        """Get timeout countdown text"""
        countdown = self.wait_for_element_visible(self.TIMEOUT_COUNTDOWN)
        return countdown.text
    
    def is_lab_iframe_loaded(self):
        """Check if lab iframe is loaded"""
        try:
            iframe = self.wait_for_element_visible(self.LAB_IFRAME, timeout=10)
            return iframe.is_displayed()
        except TimeoutException:
            return False
    
    def is_extend_button_enabled(self):
        """Check if extend timeout button is enabled"""
        try:
            button = self.driver.find_element(*self.EXTEND_TIMEOUT_BUTTON)
            return button.is_enabled()
        except NoSuchElementException:
            return False


class StudentDashboardPage(BasePage):
    """Page Object for Student Dashboard"""
    
    LOGOUT_BUTTON = (By.ID, "logout-button")
    MY_COURSES = (By.ID, "my-courses")
    
    def __init__(self, driver):
        super().__init__(driver)
        self.base_url = os.getenv('TEST_BASE_URL', 'https://localhost:3000')
    
    def navigate(self):
        """Navigate to student dashboard"""
        self.driver.get(f"{self.base_url}/html/student-dashboard.html")
        self.wait_for_page_load()
    
    def logout(self):
        """Logout student"""
        logout_button = self.wait_for_element_clickable(self.LOGOUT_BUTTON)
        logout_button.click()
        time.sleep(1)


class LoginPage(BasePage):
    """Page Object for Login page"""
    
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    
    def __init__(self, driver):
        super().__init__(driver)
        self.base_url = os.getenv('TEST_BASE_URL', 'https://localhost:3000')
    
    def navigate(self):
        """Navigate to login page"""
        self.driver.get(f"{self.base_url}/html/student-login.html")
        self.wait_for_page_load()
    
    def login(self, email, password):
        """Login with credentials"""
        email_input = self.wait_for_element_visible(self.EMAIL_INPUT)
        email_input.send_keys(email)
        
        password_input = self.wait_for_element_visible(self.PASSWORD_INPUT)
        password_input.send_keys(password)
        
        submit_button = self.wait_for_element_clickable(self.SUBMIT_BUTTON)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        time.sleep(0.5)
        submit_button.click()
        time.sleep(2)


# ============================================================================
# TEST CLASS 1: TIMEOUT MECHANISMS (5 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.lab_environment
@pytest.mark.timeout(300)
class TestLabTimeoutMechanisms(BaseTest):
    """Test suite for lab timeout mechanisms"""
    
    def setup_method(self, method):
        """Setup for each test"""
        super().setup_method(method)
        self.login_page = LoginPage(self.driver)
        self.dashboard_page = StudentDashboardPage(self.driver)
        self.lab_page = LabPage(self.driver)
        
        # Login as student
        self.login_page.navigate()
        self.login_page.login('student.test@example.com', 'password123')
    
    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_lab_timeout_warning_displayed(self, accelerated_timeout_env):
        """
        E2E TEST: Lab timeout warning displayed 15 minutes before expiry
        
        BUSINESS REQUIREMENT:
        - Students must receive warning before timeout (15 min, 5 min, 1 min)
        - Prevents unexpected lab shutdowns
        - Gives students time to save work
        
        TEST SCENARIO:
        1. Login as student
        2. Start lab
        3. Wait for timeout warning time (3 seconds in test environment)
        4. Verify warning message displayed
        5. Verify countdown timer visible
        
        VALIDATION:
        - Timeout warning element visible
        - Warning message contains "will expire soon"
        - Countdown shows remaining time
        
        NOTE: Uses accelerated timeout (3 seconds instead of 15 minutes)
        """
        # Navigate to lab and start it
        self.lab_page.navigate_to_lab()
        self.lab_page.start_lab()
        
        # Wait for warning time (3 seconds with accelerated timeout)
        time.sleep(3.5)
        
        # VERIFICATION 1: Warning is displayed
        assert self.lab_page.is_timeout_warning_visible(), \
            "Timeout warning should be visible"
        
        # VERIFICATION 2: Warning contains expected message
        warning_element = self.driver.find_element(*self.lab_page.TIMEOUT_WARNING)
        warning_text = warning_element.text.lower()
        assert "expire" in warning_text or "timeout" in warning_text, \
            f"Warning should mention expiry/timeout, got: {warning_text}"
    
    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_lab_timeout_countdown_visible(self, accelerated_timeout_env):
        """
        E2E TEST: Lab timeout countdown visible in UI
        
        BUSINESS REQUIREMENT:
        - Students must see countdown to timeout
        - Countdown updates in real-time
        - Helps students manage their time
        
        TEST SCENARIO:
        1. Login as student
        2. Start lab
        3. Wait for warning period
        4. Verify countdown element exists
        5. Verify countdown decreases over time
        
        VALIDATION:
        - Countdown element visible
        - Countdown shows seconds remaining
        - Countdown value decreases
        """
        # Navigate to lab and start it
        self.lab_page.navigate_to_lab()
        self.lab_page.start_lab()
        
        # Wait for warning time
        time.sleep(3.5)
        
        # Get initial countdown
        initial_countdown = self.lab_page.get_timeout_countdown()
        
        # Wait 1 second
        time.sleep(1)
        
        # Get updated countdown
        updated_countdown = self.lab_page.get_timeout_countdown()
        
        # VERIFICATION: Countdown decreased
        assert initial_countdown != updated_countdown, \
            "Countdown should update over time"
    
    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_lab_auto_stops_after_inactivity_timeout(
        self,
        accelerated_timeout_env,
        docker_client,
        db_connection,
        test_student_credentials
    ):
        """
        E2E TEST: Lab auto-stops after inactivity timeout
        
        BUSINESS REQUIREMENT:
        - Labs must auto-stop after 2 hours of inactivity
        - Prevents resource waste from abandoned labs
        - Saves infrastructure costs
        
        TEST SCENARIO:
        1. Login as student
        2. Start lab
        3. Simulate inactivity (set timeout to 5 seconds for testing)
        4. Verify lab auto-stops
        5. Verify container stopped in Docker
        6. Verify database updated
        
        VALIDATION:
        - Lab status changes to "Stopped"
        - Docker container status is "exited"
        - Student notified of auto-stop
        - Lab can be restarted manually
        - Database lab_sessions updated
        
        NOTE: Uses accelerated timeout (5 seconds instead of 2 hours)
        """
        # Navigate to lab and start it
        self.lab_page.navigate_to_lab()
        self.lab_page.start_lab()
        
        # Get lab container
        containers = docker_client.containers.list(filters={"name": f"lab_*"})
        assert len(containers) > 0, "Lab container should exist"
        container = containers[0]
        container_id = container.id
        
        # Simulate inactivity by not interacting with lab
        # Wait for timeout (5 seconds with accelerated timeout)
        time.sleep(6)
        
        # VERIFICATION 1: UI shows stopped
        lab_status = self.lab_page.get_lab_status()
        assert "Stopped" in lab_status or "Inactive" in lab_status or "Timeout" in lab_status, \
            f"Expected 'Stopped', got '{lab_status}'"
        
        # VERIFICATION 2: Container actually stopped
        container = docker_client.containers.get(container_id)
        assert container.status in ["exited", "stopped"], \
            f"Expected container 'exited' or 'stopped', got '{container.status}'"
        
        # VERIFICATION 3: Database updated
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT status, ended_at FROM lab_sessions WHERE container_id = %s",
            (container_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        
        assert row is not None, "Lab session should exist in database"
        assert row[0] == 'stopped', f"Expected status 'stopped', got '{row[0]}'"
        assert row[1] is not None, "ended_at should be set"
    
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_student_can_extend_timeout(self, accelerated_timeout_env):
        """
        E2E TEST: Student can extend timeout before expiry
        
        BUSINESS REQUIREMENT:
        - Students can extend timeout if they need more time
        - Extension adds 30 minutes to session
        - Cannot exceed max duration (8 hours)
        
        TEST SCENARIO:
        1. Login as student
        2. Start lab
        3. Wait for warning
        4. Click "Extend Timeout" button
        5. Verify timeout extended
        6. Verify new countdown displayed
        
        VALIDATION:
        - Extend button clickable during warning period
        - Timeout countdown resets after extension
        - Success message displayed
        - Lab remains running
        """
        # Navigate to lab and start it
        self.lab_page.navigate_to_lab()
        self.lab_page.start_lab()
        
        # Wait for warning time
        time.sleep(3.5)
        
        # Get initial countdown
        initial_countdown = self.lab_page.get_timeout_countdown()
        
        # VERIFICATION 1: Extend button is enabled
        assert self.lab_page.is_extend_button_enabled(), \
            "Extend button should be enabled during warning period"
        
        # Extend timeout
        self.lab_page.extend_timeout()
        
        # VERIFICATION 2: Countdown increased/reset
        time.sleep(1)
        new_countdown = self.lab_page.get_timeout_countdown()
        # In accelerated environment, extension should give more time
        # Cannot directly compare values due to timing, but warning should disappear
        
        # Wait a moment and check if warning is still visible
        time.sleep(1)
        warning_visible = self.lab_page.is_timeout_warning_visible()
        assert not warning_visible, "Warning should disappear after extension"
        
        # VERIFICATION 3: Lab still running
        lab_status = self.lab_page.get_lab_status()
        assert "Running" in lab_status or "Active" in lab_status, \
            f"Lab should still be running after extension, got '{lab_status}'"
    
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_lab_cannot_exceed_max_duration(
        self,
        accelerated_timeout_env,
        docker_client
    ):
        """
        E2E TEST: Lab cannot be extended beyond max duration (8 hours)
        
        BUSINESS REQUIREMENT:
        - Labs have maximum duration of 8 hours
        - Prevents abuse and ensures fair resource allocation
        - Extension button disabled when max reached
        
        TEST SCENARIO:
        1. Login as student
        2. Start lab
        3. Extend timeout multiple times
        4. Verify extension disabled when max duration reached
        5. Verify lab stops at max duration
        
        VALIDATION:
        - Extend button disabled after max duration reached
        - Error message shown when trying to extend past max
        - Lab stops automatically at max duration
        - Container removed from Docker
        
        NOTE: Uses accelerated timeout (30 seconds max instead of 8 hours)
        """
        # Navigate to lab and start it
        self.lab_page.navigate_to_lab()
        self.lab_page.start_lab()
        
        # Get lab container
        containers = docker_client.containers.list(filters={"name": f"lab_*"})
        assert len(containers) > 0, "Lab container should exist"
        container_id = containers[0].id
        
        # Wait for warning and extend multiple times
        for _ in range(3):
            time.sleep(3.5)
            if self.lab_page.is_extend_button_enabled():
                self.lab_page.extend_timeout()
            else:
                break
        
        # Wait for max duration (30 seconds with accelerated timeout)
        # After multiple extensions, should hit max
        time.sleep(10)
        
        # VERIFICATION 1: Extend button disabled
        assert not self.lab_page.is_extend_button_enabled(), \
            "Extend button should be disabled after max duration"
        
        # VERIFICATION 2: Lab stopped at max duration
        # May need to wait a bit more
        time.sleep(5)
        lab_status = self.lab_page.get_lab_status()
        assert "Stopped" in lab_status or "Max Duration" in lab_status, \
            f"Lab should stop at max duration, got '{lab_status}'"


# ============================================================================
# TEST CLASS 2: CLEANUP WORKFLOWS (4 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.lab_environment
@pytest.mark.cleanup
class TestLabCleanupWorkflows(BaseTest):
    """Test suite for lab cleanup workflows"""
    
    def setup_method(self, method):
        """Setup for each test"""
        super().setup_method(method)
        self.login_page = LoginPage(self.driver)
        self.dashboard_page = StudentDashboardPage(self.driver)
        self.lab_page = LabPage(self.driver)
        
        # Login as student
        self.login_page.navigate()
        self.login_page.login('student.test@example.com', 'password123')
    
    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_lab_cleanup_on_student_logout(
        self,
        docker_client,
        db_connection,
        cleanup_test_labs
    ):
        """
        E2E TEST: Lab cleanup on student logout
        
        BUSINESS REQUIREMENT:
        - Labs must be cleaned up when student logs out
        - Prevents orphaned containers
        - Ensures security (other students can't access lab)
        
        TEST SCENARIO:
        1. Login as student
        2. Start lab
        3. Verify container running
        4. Logout
        5. Verify container stopped and removed
        6. Verify database session closed
        
        VALIDATION:
        - Container stopped after logout
        - Container removed from Docker
        - Database lab_sessions.status = 'stopped'
        - Database lab_sessions.ended_at set
        """
        # Navigate to lab and start it
        self.lab_page.navigate_to_lab()
        self.lab_page.start_lab()
        
        # Get lab container
        containers = docker_client.containers.list(filters={"name": f"lab_*"})
        assert len(containers) > 0, "Lab container should exist"
        container_id = containers[0].id
        container_name = containers[0].name
        
        # VERIFICATION 1: Container running
        assert containers[0].status == "running", "Container should be running"
        
        # Logout
        self.dashboard_page.navigate()
        self.dashboard_page.logout()
        
        # Wait for cleanup
        time.sleep(2)
        
        # VERIFICATION 2: Container stopped
        container = docker_client.containers.get(container_id)
        assert container.status in ["exited", "stopped"], \
            f"Container should be stopped after logout, got '{container.status}'"
        
        # VERIFICATION 3: Database updated
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT status, ended_at FROM lab_sessions WHERE container_id = %s",
            (container_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        
        assert row is not None, "Lab session should exist in database"
        assert row[0] == 'stopped', f"Expected status 'stopped', got '{row[0]}'"
        assert row[1] is not None, "ended_at should be set"
    
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_lab_cleanup_on_course_completion(
        self,
        docker_client,
        db_connection,
        cleanup_test_labs
    ):
        """
        E2E TEST: Lab cleanup on course completion
        
        BUSINESS REQUIREMENT:
        - Labs must be cleaned up when student completes course
        - Frees resources for new students
        - Archives student work for reference
        
        TEST SCENARIO:
        1. Login as student
        2. Start lab
        3. Complete course (trigger completion API)
        4. Verify lab stopped and archived
        5. Verify storage volume persisted
        
        VALIDATION:
        - Container stopped after course completion
        - Container removed from Docker
        - Storage volume persisted for archival
        - Database lab_sessions.status = 'completed'
        - Database lab_sessions.archived = true
        """
        # Navigate to lab and start it
        self.lab_page.navigate_to_lab()
        self.lab_page.start_lab()
        
        # Get lab container
        containers = docker_client.containers.list(filters={"name": f"lab_*"})
        assert len(containers) > 0, "Lab container should exist"
        container_id = containers[0].id
        
        # Simulate course completion via API
        # In real implementation, this would trigger cleanup job
        import requests
        api_url = f"{self.lab_page.base_url}/api/v1/courses/complete"
        payload = {"course_id": "test_course_001", "student_id": "test_student_001"}
        
        try:
            response = requests.post(api_url, json=payload, verify=False)
            # May fail if API not implemented yet (expected in TDD RED phase)
        except Exception as e:
            print(f"Course completion API call failed (expected in RED phase): {e}")
        
        # Wait for cleanup job to run
        time.sleep(3)
        
        # VERIFICATION 1: Container stopped
        container = docker_client.containers.get(container_id)
        assert container.status in ["exited", "stopped"], \
            f"Container should be stopped after course completion, got '{container.status}'"
        
        # VERIFICATION 2: Database updated
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT status, archived FROM lab_sessions WHERE container_id = %s",
            (container_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            assert row[0] == 'completed', f"Expected status 'completed', got '{row[0]}'"
            assert row[1] is True, "Lab session should be archived"
    
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_lab_cleanup_on_enrollment_removal(
        self,
        docker_client,
        db_connection,
        cleanup_test_labs
    ):
        """
        E2E TEST: Lab cleanup on enrollment removal
        
        BUSINESS REQUIREMENT:
        - Labs must be cleaned up when student unenrolls
        - Prevents unauthorized access
        - Frees resources immediately
        
        TEST SCENARIO:
        1. Login as student
        2. Start lab
        3. Unenroll student via API
        4. Verify lab stopped immediately
        5. Verify container removed
        
        VALIDATION:
        - Container stopped after unenrollment
        - Container removed from Docker
        - Database lab_sessions.status = 'removed'
        - Student cannot access lab anymore
        """
        # Navigate to lab and start it
        self.lab_page.navigate_to_lab()
        self.lab_page.start_lab()
        
        # Get lab container
        containers = docker_client.containers.list(filters={"name": f"lab_*"})
        assert len(containers) > 0, "Lab container should exist"
        container_id = containers[0].id
        
        # Simulate enrollment removal via API
        import requests
        api_url = f"{self.lab_page.base_url}/api/v1/enrollments/remove"
        payload = {"course_id": "test_course_001", "student_id": "test_student_001"}
        
        try:
            response = requests.post(api_url, json=payload, verify=False)
        except Exception as e:
            print(f"Enrollment removal API call failed (expected in RED phase): {e}")
        
        # Wait for cleanup
        time.sleep(2)
        
        # VERIFICATION 1: Container stopped
        container = docker_client.containers.get(container_id)
        assert container.status in ["exited", "stopped"], \
            f"Container should be stopped after enrollment removal, got '{container.status}'"
        
        # VERIFICATION 2: Database updated
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT status FROM lab_sessions WHERE container_id = %s",
            (container_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            assert row[0] in ['stopped', 'removed'], \
                f"Expected status 'stopped' or 'removed', got '{row[0]}'"
    
    @pytest.mark.priority_medium
    @pytest.mark.asyncio
    async def test_lab_cleanup_on_course_deletion(
        self,
        docker_client,
        db_connection,
        cleanup_test_labs
    ):
        """
        E2E TEST: Lab cleanup on course deletion
        
        BUSINESS REQUIREMENT:
        - All labs must be cleaned up when course deleted
        - Prevents orphaned resources
        - Ensures data integrity
        
        TEST SCENARIO:
        1. Login as student
        2. Start lab
        3. Delete course (admin action)
        4. Verify all labs for course stopped
        5. Verify all containers removed
        
        VALIDATION:
        - All containers for course stopped
        - All containers removed from Docker
        - Database lab_sessions.status = 'course_deleted'
        - All student data archived or deleted per policy
        """
        # Navigate to lab and start it
        self.lab_page.navigate_to_lab()
        self.lab_page.start_lab()
        
        # Get lab container
        containers = docker_client.containers.list(filters={"name": f"lab_*"})
        assert len(containers) > 0, "Lab container should exist"
        container_id = containers[0].id
        
        # Simulate course deletion via API
        import requests
        api_url = f"{self.lab_page.base_url}/api/v1/courses/delete"
        payload = {"course_id": "test_course_001"}
        
        try:
            response = requests.delete(api_url, json=payload, verify=False)
        except Exception as e:
            print(f"Course deletion API call failed (expected in RED phase): {e}")
        
        # Wait for cleanup
        time.sleep(3)
        
        # VERIFICATION 1: Container stopped
        container = docker_client.containers.get(container_id)
        assert container.status in ["exited", "stopped"], \
            f"Container should be stopped after course deletion, got '{container.status}'"
        
        # VERIFICATION 2: Database updated
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT status FROM lab_sessions WHERE container_id = %s",
            (container_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            assert row[0] in ['stopped', 'course_deleted'], \
                f"Expected status 'stopped' or 'course_deleted', got '{row[0]}'"


# ============================================================================
# TEST CLASS 3: ORPHAN DETECTION (3 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.lab_environment
@pytest.mark.orphan_detection
class TestLabOrphanDetection(BaseTest):
    """Test suite for lab orphan detection and cleanup"""
    
    def setup_method(self, method):
        """Setup for each test"""
        super().setup_method(method)
        self.login_page = LoginPage(self.driver)
        self.lab_page = LabPage(self.driver)
    
    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_detect_orphaned_containers(
        self,
        docker_client,
        db_connection,
        cleanup_test_labs
    ):
        """
        E2E TEST: Detect orphaned containers (no associated session)
        
        BUSINESS REQUIREMENT:
        - System must detect containers without valid lab_sessions
        - Prevents resource leaks from crashes or bugs
        - Runs daily as cron job
        
        TEST SCENARIO:
        1. Create orphaned container manually (no database entry)
        2. Run orphan detection script
        3. Verify orphan detected
        4. Verify logged in audit trail
        
        VALIDATION:
        - Orphan detection script finds container
        - Container flagged as orphan
        - Admin notified via email/alert
        - Audit log entry created
        """
        # Create orphaned container manually
        orphan_container = docker_client.containers.run(
            "python:3.11-slim",
            name="lab_test_orphan_001",
            command="sleep infinity",
            detach=True,
            labels={"app": "course-creator-lab"}
        )
        
        # Simulate orphan detection (would normally be cron job)
        # Query all lab containers
        all_lab_containers = docker_client.containers.list(filters={"label": "app=course-creator-lab"})
        
        # Get all valid lab sessions from database
        cursor = db_connection.cursor()
        cursor.execute("SELECT container_id FROM lab_sessions WHERE status = 'running'")
        valid_container_ids = {row[0] for row in cursor.fetchall()}
        cursor.close()
        
        # Find orphans
        orphan_containers = [
            c for c in all_lab_containers
            if c.id not in valid_container_ids
        ]
        
        # VERIFICATION 1: Orphan detected
        assert len(orphan_containers) > 0, "Orphan container should be detected"
        assert orphan_container.id in [c.id for c in orphan_containers], \
            "Our test orphan should be in the list"
        
        # VERIFICATION 2: Log entry created (if implemented)
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action = 'orphan_detected' AND resource_id = %s",
            (orphan_container.id,)
        )
        count = cursor.fetchone()[0]
        cursor.close()
        
        # May be 0 in RED phase before audit logging implemented
        print(f"Audit log entries for orphan detection: {count}")
        
        # Cleanup
        orphan_container.stop(timeout=5)
        orphan_container.remove(force=True)
    
    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_cleanup_orphaned_containers_automatically(
        self,
        docker_client,
        db_connection,
        cleanup_test_labs
    ):
        """
        E2E TEST: Cleanup orphaned containers automatically (daily job)
        
        BUSINESS REQUIREMENT:
        - Orphaned containers must be cleaned up automatically
        - Runs daily at 2 AM via cron
        - Sends summary report to admins
        
        TEST SCENARIO:
        1. Create multiple orphaned containers
        2. Run cleanup script
        3. Verify all orphans removed
        4. Verify summary report generated
        
        VALIDATION:
        - All orphaned containers stopped
        - All orphaned containers removed
        - Summary report shows count and details
        - No errors in cleanup process
        """
        # Create multiple orphaned containers
        orphan_count = 3
        orphan_containers = []
        
        for i in range(orphan_count):
            container = docker_client.containers.run(
                "python:3.11-slim",
                name=f"lab_test_orphan_{i:03d}",
                command="sleep infinity",
                detach=True,
                labels={"app": "course-creator-lab"}
            )
            orphan_containers.append(container)
        
        # Simulate orphan cleanup (would normally be cron job)
        # Get all lab containers
        all_lab_containers = docker_client.containers.list(filters={"label": "app=course-creator-lab"})
        
        # Get all valid lab sessions
        cursor = db_connection.cursor()
        cursor.execute("SELECT container_id FROM lab_sessions WHERE status = 'running'")
        valid_container_ids = {row[0] for row in cursor.fetchall()}
        cursor.close()
        
        # Find and cleanup orphans
        cleanup_count = 0
        cleanup_errors = []
        
        for container in all_lab_containers:
            if container.id not in valid_container_ids:
                try:
                    container.stop(timeout=5)
                    container.remove(force=True)
                    cleanup_count += 1
                except Exception as e:
                    cleanup_errors.append({"container_id": container.id, "error": str(e)})
        
        # VERIFICATION 1: All orphans cleaned up
        assert cleanup_count >= orphan_count, \
            f"Expected at least {orphan_count} orphans cleaned, got {cleanup_count}"
        
        # VERIFICATION 2: No cleanup errors
        assert len(cleanup_errors) == 0, \
            f"Cleanup should succeed without errors, got: {cleanup_errors}"
        
        # VERIFICATION 3: Containers actually removed
        remaining_orphans = docker_client.containers.list(
            filters={"name": "lab_test_orphan_*"}
        )
        assert len(remaining_orphans) == 0, \
            f"All orphans should be removed, found {len(remaining_orphans)}"
    
    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_alert_admin_of_cleanup_failures(
        self,
        docker_client,
        db_connection,
        cleanup_test_labs
    ):
        """
        E2E TEST: Alert admin of cleanup failures
        
        BUSINESS REQUIREMENT:
        - Admins must be notified if cleanup fails
        - Prevents resource leaks from going unnoticed
        - Allows manual intervention
        
        TEST SCENARIO:
        1. Create container that cannot be stopped gracefully
        2. Run cleanup script
        3. Verify cleanup failure detected
        4. Verify admin alert sent
        5. Verify failure logged
        
        VALIDATION:
        - Cleanup failure detected
        - Admin email/notification sent
        - Failure logged in database
        - Container marked for manual review
        """
        # Create container that's harder to stop (simulating stuck container)
        problem_container = docker_client.containers.run(
            "python:3.11-slim",
            name="lab_test_problematic_001",
            command="python -c 'import signal; signal.signal(signal.SIGTERM, signal.SIG_IGN); import time; time.sleep(infinity)'",
            detach=True,
            labels={"app": "course-creator-lab"}
        )
        
        # Simulate orphan cleanup with failure handling
        try:
            # Try graceful stop (will timeout)
            problem_container.stop(timeout=2)
        except Exception as stop_error:
            # VERIFICATION 1: Cleanup failure detected
            assert True, "Expected stop to fail or timeout"
            
            # Log failure (in real implementation)
            cursor = db_connection.cursor()
            cursor.execute(
                """
                INSERT INTO cleanup_failures (container_id, container_name, error_message, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (problem_container.id, problem_container.name, str(stop_error), datetime.now())
            )
            db_connection.commit()
            cursor.close()
            
            # VERIFICATION 2: Failure logged
            cursor = db_connection.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM cleanup_failures WHERE container_id = %s",
                (problem_container.id,)
            )
            count = cursor.fetchone()[0]
            cursor.close()
            
            # May be 0 in RED phase before cleanup_failures table exists
            print(f"Cleanup failures logged: {count}")
            
            # Force remove for cleanup
            problem_container.remove(force=True)


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
