"""
E2E Tests for Authentication Workflows

BUSINESS REQUIREMENT:
Tests complete user authentication flows including login, logout,
session management, and role-based access control.

TECHNICAL IMPLEMENTATION:
- Uses Selenium with Chrome WebDriver
- Tests all user roles (student, instructor, org admin)
- Tests session persistence and timeout
- Uses Page Object Model pattern
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.selenium_base import BasePage, BaseTest


class LoginPage(BasePage):
    """Page Object for login page."""

    # Locators
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")

    def navigate(self):
        """Navigate to login page."""
        self.navigate_to("/login")

    def login(self, email, password):
        """
        Perform login operation.

        Args:
            email: User email
            password: User password
        """
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)

    def get_error_message(self):
        """Get error message text if present."""
        if self.is_element_present(*self.ERROR_MESSAGE, timeout=3):
            return self.get_text(*self.ERROR_MESSAGE)
        return None


class DashboardPage(BasePage):
    """Page Object for dashboard (after login)."""

    # Locators
    USER_MENU = (By.ID, "user-menu")
    LOGOUT_BUTTON = (By.ID, "logout-btn")
    DASHBOARD_TITLE = (By.TAG_NAME, "h1")

    def is_loaded(self):
        """Check if dashboard page is loaded."""
        return self.is_element_present(*self.DASHBOARD_TITLE, timeout=10)

    def get_dashboard_title(self):
        """Get dashboard title text."""
        return self.get_text(*self.DASHBOARD_TITLE)

    def logout(self):
        """Perform logout operation."""
        self.click_element(*self.USER_MENU)
        time.sleep(0.5)  # Wait for menu animation
        self.click_element(*self.LOGOUT_BUTTON)


@pytest.mark.e2e
class TestStudentLogin(BaseTest):
    """Test student authentication flows."""

    def test_student_successful_login(self):
        """
        Test student can login with valid credentials.

        WORKFLOW:
        1. Navigate to login page
        2. Enter valid student credentials
        3. Click login
        4. Verify redirected to student dashboard
        """
        login_page = LoginPage(self.driver, self.config)
        dashboard = DashboardPage(self.driver, self.config)

        # Step 1: Navigate
        login_page.navigate()

        # Step 2-3: Login
        login_page.login("student@example.com", "student-password-123")

        # Step 4: Verify dashboard
        assert dashboard.is_loaded(), "Dashboard did not load after login"
        assert "Student Dashboard" in dashboard.get_dashboard_title()

    def test_student_invalid_credentials(self):
        """
        Test login fails with invalid credentials.

        WORKFLOW:
        1. Navigate to login page
        2. Enter invalid credentials
        3. Click login
        4. Verify error message displayed
        """
        login_page = LoginPage(self.driver, self.config)

        login_page.navigate()
        login_page.login("student@example.com", "wrong-password")

        error = login_page.get_error_message()
        assert error is not None, "No error message displayed"
        assert "invalid" in error.lower() or "incorrect" in error.lower()

    def test_student_empty_credentials(self):
        """Test form validation for empty credentials."""
        login_page = LoginPage(self.driver, self.config)

        login_page.navigate()
        login_page.login("", "")

        # HTML5 validation should prevent submission
        # Or server returns error
        time.sleep(1)
        current_url = login_page.get_current_url()
        assert "/login" in current_url, "Should stay on login page"


@pytest.mark.e2e
class TestInstructorLogin(BaseTest):
    """Test instructor authentication flows."""

    def test_instructor_successful_login(self):
        """
        Test instructor can login and access instructor dashboard.

        WORKFLOW:
        1. Navigate to login
        2. Login as instructor
        3. Verify instructor dashboard loaded
        4. Verify instructor-specific features visible
        """
        login_page = LoginPage(self.driver, self.config)
        dashboard = DashboardPage(self.driver, self.config)

        login_page.navigate()
        login_page.login("instructor@example.com", "instructor-password-123")

        assert dashboard.is_loaded()
        assert "Instructor Dashboard" in dashboard.get_dashboard_title()

        # Verify instructor features
        assert dashboard.is_element_present(By.ID, "create-course-btn", timeout=5)


@pytest.mark.e2e
class TestOrgAdminLogin(BaseTest):
    """Test organization admin authentication flows."""

    def test_org_admin_successful_login(self):
        """
        Test org admin can login and access org dashboard.

        WORKFLOW:
        1. Navigate to login
        2. Login as org admin
        3. Verify org admin dashboard loaded
        4. Verify admin features visible
        """
        login_page = LoginPage(self.driver, self.config)
        dashboard = DashboardPage(self.driver, self.config)

        login_page.navigate()
        login_page.login("admin@example.com", "admin-password-123")

        assert dashboard.is_loaded()
        assert "Organization Dashboard" in dashboard.get_dashboard_title()

        # Verify admin features
        assert dashboard.is_element_present(By.ID, "create-project-btn", timeout=5)


@pytest.mark.e2e
class TestSessionManagement(BaseTest):
    """Test session persistence and timeout."""

    def test_session_persists_across_pages(self):
        """
        Test user session persists when navigating between pages.

        WORKFLOW:
        1. Login
        2. Navigate to different page
        3. Verify still logged in
        4. Return to dashboard
        5. Verify session maintained
        """
        login_page = LoginPage(self.driver, self.config)
        dashboard = DashboardPage(self.driver, self.config)

        # Login
        login_page.navigate()
        login_page.login("student@example.com", "student-password-123")
        assert dashboard.is_loaded()

        # Navigate to courses page
        dashboard.navigate_to("/courses")
        time.sleep(1)

        # Return to dashboard
        dashboard.navigate_to("/dashboard")

        # Verify still logged in
        assert dashboard.is_element_present(*dashboard.DASHBOARD_TITLE, timeout=5)

    def test_logout_clears_session(self):
        """
        Test logout properly clears session.

        WORKFLOW:
        1. Login
        2. Logout
        3. Verify redirected to login
        4. Try to access dashboard
        5. Verify redirected back to login
        """
        login_page = LoginPage(self.driver, self.config)
        dashboard = DashboardPage(self.driver, self.config)

        # Login
        login_page.navigate()
        login_page.login("student@example.com", "student-password-123")
        assert dashboard.is_loaded()

        # Logout
        dashboard.logout()

        # Verify on login page
        time.sleep(1)
        assert "/login" in login_page.get_current_url()

        # Try to access dashboard directly
        dashboard.navigate_to("/dashboard")
        time.sleep(1)

        # Should be redirected to login
        assert "/login" in login_page.get_current_url()


@pytest.mark.e2e
class TestPasswordReset(BaseTest):
    """Test password reset workflow."""

    def test_password_reset_request(self):
        """
        Test user can request password reset.

        WORKFLOW:
        1. Navigate to login
        2. Click forgot password
        3. Enter email
        4. Submit request
        5. Verify confirmation message
        """
        login_page = LoginPage(self.driver, self.config)

        login_page.navigate()

        # Click forgot password link
        forgot_link = (By.LINK_TEXT, "Forgot Password?")
        if login_page.is_element_present(*forgot_link, timeout=3):
            login_page.click_element(*forgot_link)

            # Enter email
            email_input = (By.ID, "reset-email")
            login_page.enter_text(*email_input, "student@example.com")

            # Submit
            submit_btn = (By.CSS_SELECTOR, "button[type='submit']")
            login_page.click_element(*submit_btn)

            # Verify confirmation
            success_msg = (By.CLASS_NAME, "success-message")
            assert login_page.is_element_present(*success_msg, timeout=5)


@pytest.mark.e2e
class TestRoleBasedAccess(BaseTest):
    """Test role-based access control."""

    def test_student_cannot_access_instructor_features(self):
        """
        Test student cannot access instructor-only features.

        WORKFLOW:
        1. Login as student
        2. Try to access /instructor/courses
        3. Verify access denied or redirected
        """
        login_page = LoginPage(self.driver, self.config)

        login_page.navigate()
        login_page.login("student@example.com", "student-password-123")

        # Try to access instructor page
        login_page.navigate_to("/instructor/courses")
        time.sleep(2)

        # Should see error or be redirected
        current_url = login_page.get_current_url()
        assert "/instructor/courses" not in current_url or \
               login_page.is_element_present(By.CLASS_NAME, "access-denied", timeout=3)

    def test_instructor_cannot_access_admin_features(self):
        """Test instructor cannot access admin-only features."""
        login_page = LoginPage(self.driver, self.config)

        login_page.navigate()
        login_page.login("instructor@example.com", "instructor-password-123")

        # Try to access admin page
        login_page.navigate_to("/admin/organizations")
        time.sleep(2)

        # Should see error or be redirected
        current_url = login_page.get_current_url()
        assert "/admin/organizations" not in current_url or \
               login_page.is_element_present(By.CLASS_NAME, "access-denied", timeout=3)


# Run with: HEADLESS=true pytest tests/e2e/test_auth_selenium.py -v -m e2e
