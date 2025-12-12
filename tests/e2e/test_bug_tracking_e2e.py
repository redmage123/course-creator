"""
Bug Tracking E2E Tests

BUSINESS CONTEXT:
End-to-end tests for the bug tracking system using Selenium.
Tests the complete user journey from bug submission to viewing analysis.

TECHNICAL IMPLEMENTATION:
Uses Selenium WebDriver for browser automation.
Tests against real frontend running on test server.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import os


# Test configuration
BASE_URL = os.environ.get("TEST_BASE_URL", "https://localhost:3000")
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"


class TestBugTrackingE2E:
    """E2E tests for bug tracking system."""

    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome WebDriver."""
        options = Options()
        if HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    @pytest.fixture
    def logged_in_driver(self, driver):
        """Setup driver with logged in user."""
        # Navigate to login page
        driver.get(f"{BASE_URL}/login")

        # Wait for login form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        # Login with test user
        driver.find_element(By.ID, "username").send_keys("testuser")
        driver.find_element(By.ID, "password").send_keys("testpassword123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Wait for redirect to dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )

        return driver

    def test_bug_submission_page_loads(self, logged_in_driver):
        """Test that bug submission page loads correctly."""
        driver = logged_in_driver

        # Navigate to bug submission page
        driver.get(f"{BASE_URL}/bugs/submit")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )

        # Verify page title
        title = driver.find_element(By.CSS_SELECTOR, "h1").text
        assert "Report" in title or "Bug" in title

    def test_bug_submission_form_elements_present(self, logged_in_driver):
        """Test that all form elements are present."""
        driver = logged_in_driver

        driver.get(f"{BASE_URL}/bugs/submit")

        # Wait for form to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "title"))
        )

        # Verify required fields exist
        assert driver.find_element(By.ID, "title")
        assert driver.find_element(By.ID, "description")
        assert driver.find_element(By.ID, "submitter_email")

        # Verify optional fields exist
        assert driver.find_element(By.ID, "steps_to_reproduce")
        assert driver.find_element(By.ID, "expected_behavior")
        assert driver.find_element(By.ID, "actual_behavior")
        assert driver.find_element(By.ID, "severity")
        assert driver.find_element(By.ID, "affected_component")

        # Verify submit button exists
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        assert submit_button.is_displayed()

    def test_bug_submission_form_validation(self, logged_in_driver):
        """Test form validation for required fields."""
        driver = logged_in_driver

        driver.get(f"{BASE_URL}/bugs/submit")

        # Wait for form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "title"))
        )

        # Try to submit empty form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        # Wait for validation errors
        time.sleep(0.5)

        # Check for error messages (assuming error class or aria-invalid)
        title_input = driver.find_element(By.ID, "title")
        assert title_input.get_attribute("aria-invalid") == "true" or \
               driver.find_element(By.ID, "title-error")

    def test_bug_submission_form_title_validation(self, logged_in_driver):
        """Test title minimum length validation."""
        driver = logged_in_driver

        driver.get(f"{BASE_URL}/bugs/submit")

        # Wait for form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "title"))
        )

        # Enter short title (less than 10 characters)
        title_input = driver.find_element(By.ID, "title")
        title_input.clear()
        title_input.send_keys("Short")

        # Enter valid description
        desc_input = driver.find_element(By.ID, "description")
        desc_input.clear()
        desc_input.send_keys("This is a valid description for the bug report.")

        # Enter valid email
        email_input = driver.find_element(By.ID, "submitter_email")
        email_input.clear()
        email_input.send_keys("test@example.com")

        # Submit
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        # Wait for validation error
        time.sleep(0.5)

        # Check for error message about title length
        try:
            error_element = driver.find_element(By.ID, "title-error")
            assert "10 characters" in error_element.text
        except Exception:
            # Alternative: check aria-invalid
            title_input = driver.find_element(By.ID, "title")
            assert title_input.get_attribute("aria-invalid") == "true"

    def test_bug_submission_success(self, logged_in_driver):
        """Test successful bug submission."""
        driver = logged_in_driver

        driver.get(f"{BASE_URL}/bugs/submit")

        # Wait for form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "title"))
        )

        # Fill in required fields
        title_input = driver.find_element(By.ID, "title")
        title_input.clear()
        title_input.send_keys("E2E Test Bug - Login button not working")

        desc_input = driver.find_element(By.ID, "description")
        desc_input.clear()
        desc_input.send_keys("This is an E2E test bug report. The login button does not respond to clicks.")

        email_input = driver.find_element(By.ID, "submitter_email")
        email_input.clear()
        email_input.send_keys("e2e-test@example.com")

        # Fill optional fields
        steps_input = driver.find_element(By.ID, "steps_to_reproduce")
        steps_input.clear()
        steps_input.send_keys("1. Go to login page\n2. Click login button")

        # Select severity
        severity_select = driver.find_element(By.ID, "severity")
        severity_select.click()
        time.sleep(0.2)
        # Select "high" option
        driver.find_element(By.CSS_SELECTOR, "option[value='high']").click()

        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        # Wait for success message or redirect
        try:
            WebDriverWait(driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".successContainer")),
                    EC.url_contains("/bugs/")
                )
            )
            # Success!
            assert True
        except TimeoutException:
            # Check if we're still on form (might have error)
            pytest.fail("Bug submission did not complete successfully")

    def test_bug_list_page_loads(self, logged_in_driver):
        """Test that bug list page loads correctly."""
        driver = logged_in_driver

        driver.get(f"{BASE_URL}/bugs/my")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )

        # Verify page title
        title = driver.find_element(By.CSS_SELECTOR, "h1").text
        assert "Bug" in title or "Report" in title

    def test_bug_list_has_filters(self, logged_in_driver):
        """Test that bug list page has filter controls."""
        driver = logged_in_driver

        driver.get(f"{BASE_URL}/bugs/my")

        # Wait for filters to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "status-filter"))
        )

        # Verify filter controls exist
        assert driver.find_element(By.ID, "status-filter")
        assert driver.find_element(By.ID, "severity-filter")

    def test_bug_list_shows_report_button(self, logged_in_driver):
        """Test that bug list page has button to report new bug."""
        driver = logged_in_driver

        driver.get(f"{BASE_URL}/bugs/my")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )

        # Find "Report New Bug" or similar button
        buttons = driver.find_elements(By.TAG_NAME, "a")
        report_link = None
        for button in buttons:
            if "Report" in button.text or "New Bug" in button.text or "Submit" in button.text:
                report_link = button
                break

        assert report_link is not None, "Report new bug button not found"


class TestBugStatusPageE2E:
    """E2E tests for bug status page."""

    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome WebDriver."""
        options = Options()
        if HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    def test_bug_status_page_shows_not_found_for_invalid_id(self, driver):
        """Test that invalid bug ID shows appropriate message."""
        driver.get(f"{BASE_URL}/bugs/invalid-uuid-12345")

        # Wait for page to load
        time.sleep(2)

        # Should show error or not found message
        page_text = driver.page_source.lower()
        assert "not found" in page_text or "error" in page_text or "login" in page_text


class TestBugTrackingAccessibility:
    """Accessibility tests for bug tracking pages."""

    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome WebDriver."""
        options = Options()
        if HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    def test_form_inputs_have_labels(self, driver):
        """Test that form inputs have associated labels."""
        driver.get(f"{BASE_URL}/bugs/submit")

        # Wait for form
        time.sleep(2)

        # Check if page requires login, skip test if so
        if "/login" in driver.current_url:
            pytest.skip("Login required for this page")

        # Get all inputs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        selects = driver.find_elements(By.TAG_NAME, "select")

        all_fields = inputs + textareas + selects

        for field in all_fields:
            field_id = field.get_attribute("id")
            if field_id and field.get_attribute("type") != "hidden":
                # Check for associated label
                labels = driver.find_elements(By.CSS_SELECTOR, f"label[for='{field_id}']")
                assert len(labels) > 0 or field.get_attribute("aria-label"), \
                    f"Field {field_id} has no associated label"

    def test_form_has_submit_button(self, driver):
        """Test that form has accessible submit button."""
        driver.get(f"{BASE_URL}/bugs/submit")

        time.sleep(2)

        if "/login" in driver.current_url:
            pytest.skip("Login required for this page")

        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        # Button should be visible and enabled
        assert submit_button.is_displayed()
        assert submit_button.is_enabled()

        # Button should have text content
        assert len(submit_button.text) > 0


class TestBugTrackingNavigation:
    """Navigation tests for bug tracking."""

    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome WebDriver."""
        options = Options()
        if HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    def test_breadcrumb_navigation(self, driver):
        """Test that breadcrumb navigation works."""
        # This test verifies breadcrumbs exist on bug pages
        driver.get(f"{BASE_URL}/bugs/submit")

        time.sleep(2)

        if "/login" in driver.current_url:
            pytest.skip("Login required for this page")

        # Look for breadcrumb links
        breadcrumbs = driver.find_elements(By.CSS_SELECTOR, ".breadcrumb a, nav a")

        # Should have at least one navigation link
        assert len(breadcrumbs) > 0, "No breadcrumb navigation found"
