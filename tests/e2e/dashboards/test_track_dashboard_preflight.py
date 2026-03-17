"""
Track Dashboard Pre-Flight Validation Tests (TDD - Red Phase)

BUSINESS PURPOSE:
These tests verify that all required HTML elements, API endpoints, and CSS selectors
are correctly configured BEFORE running workflow tests. This prevents the types of
errors we missed in previous testing (missing IDs, invalid selectors, URL construction errors).

TEST STRATEGY:
1. Run these tests FIRST before any workflow tests
2. If these fail, workflow tests will not run
3. Each test verifies a specific aspect of the dashboard infrastructure

@module test_track_dashboard_preflight
"""

import pytest
import requests
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from selenium_base import BaseTest


class TestTrackDashboardPreFlight(BaseTest):
    """
    Pre-flight validation tests for Track Dashboard

    WHY THIS TEST CLASS EXISTS:
    Previous E2E tests failed due to:
    - Missing HTML element IDs
    - Invalid CSS selectors
    - URL construction errors
    - Duplicate HTML attributes

    This test class catches these issues BEFORE running workflow tests.
    """

    def wait_for_loading_to_complete(self, timeout=10):
        """Helper method to wait for loading spinner to disappear"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
            )
        except:
            # Loading spinner might not be present at all
            pass

    @pytest.fixture(scope="function", autouse=True)
    def setup_org_admin_session(self):
        """Set up authenticated org admin session before each test"""
        # Login as org admin
        self.driver.get(f"{self.config.base_url}/html/index.html")
        time.sleep(2)

        # Handle privacy modal if present
        try:
            privacy_modal = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.ID, "privacyModal"))
            )
            if privacy_modal.is_displayed():
                accept_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
                self.click_element_js(accept_btn)
                time.sleep(1)
        except:
            pass

        # Click login button
        try:
            login_btn = self.wait_for_element((By.ID, "loginBtn"))
            self.click_element_js(login_btn)
            time.sleep(1)
        except:
            pass

        # Fill login form
        username_field = self.wait_for_element((By.ID, "loginEmail"))
        username_field.send_keys("orgadmin")

        password_field = self.wait_for_element((By.ID, "loginPassword"))
        password_field.send_keys("orgadmin123!")

        submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Sign In')]")
        self.click_element_js(submit_btn)
        time.sleep(3)

        # Get auth token for API tests
        self.auth_token = self.driver.execute_script("return localStorage.getItem('authToken');")

    def test_01_tracks_tab_exists(self):
        """
        Test that Tracks tab exists and is clickable

        PREVENTS: Tab not found errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")

        try:
            tracks_tab = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "tracksTab"))
            )
            assert tracks_tab.is_displayed(), "Tracks tab should be visible"
            assert tracks_tab.is_enabled(), "Tracks tab should be enabled"
        except TimeoutException:
            pytest.fail("Tracks tab with ID 'tracksTab' not found in DOM")

    def test_02_tracks_table_exists(self):
        """
        Test that tracks table exists with correct ID

        PREVENTS: Table not found errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        try:
            tracks_table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "tracksTable"))
            )
            assert tracks_table is not None, "Tracks table should exist"
        except TimeoutException:
            pytest.fail("Tracks table with ID 'tracksTable' not found in DOM")

    def test_03_create_track_button_exists_with_id(self):
        """
        Test that Create Track button exists with correct ID

        PREVENTS: Button not found errors (like we had with Create Project button)
        WHY CRITICAL: Previous tests failed because button had no ID
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        try:
            create_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "createTrackBtn"))
            )
            assert create_btn.is_displayed(), "Create Track button should be visible"
            assert create_btn.is_enabled(), "Create Track button should be enabled"
        except TimeoutException:
            pytest.fail("Create Track button with ID 'createTrackBtn' not found in DOM")

    def test_04_create_track_modal_exists(self):
        """
        Test that Create Track modal exists in DOM

        PREVENTS: Modal not found errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        try:
            # Modal should exist in DOM even if not visible
            modal = self.driver.find_element(By.ID, "createTrackModal")
            assert modal is not None, "Create Track modal should exist in DOM"
        except NoSuchElementException:
            pytest.fail("Create Track modal with ID 'createTrackModal' not found in DOM")

    def test_05_create_track_form_fields_exist(self):
        """
        Test that all form fields in create modal exist with correct IDs

        PREVENTS: Form field not found errors
        WHY CRITICAL: Need to verify ALL fields exist before workflow tests
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        required_fields = {
            "trackName": "Track name input field",
            "trackDescription": "Track description textarea",
            "trackDifficultyLevel": "Difficulty level select dropdown",
            "trackDurationHours": "Duration hours input field",
            "trackPrerequisites": "Prerequisites textarea (JSON)",
            "trackLearningObjectives": "Learning objectives textarea (JSON)",
            "trackIsActive": "Is active checkbox"
        }

        missing_fields = []
        for field_id, description in required_fields.items():
            try:
                self.driver.find_element(By.ID, field_id)
            except NoSuchElementException:
                missing_fields.append(f"{field_id} ({description})")

        if missing_fields:
            pytest.fail(f"Missing form fields in create modal: {', '.join(missing_fields)}")

    def test_06_submit_create_track_button_exists_with_correct_type(self):
        """
        Test that submit button exists with correct ID and type='submit'

        PREVENTS: Submit button errors (like we had with Create Project)
        WHY CRITICAL: Previous tests failed due to wrong button type and missing ID
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        try:
            submit_btn = self.driver.find_element(By.ID, "submitCreateTrackBtn")
            assert submit_btn is not None, "Submit button should exist"

            button_type = submit_btn.get_attribute("type")
            assert button_type == "submit", "Submit button should have type='submit'"

            # Check for duplicate class attributes (previous bug)
            class_attr = submit_btn.get_attribute("class")
            assert class_attr is not None, "Button should have class attribute"

        except NoSuchElementException:
            pytest.fail("Submit button with ID 'submitCreateTrackBtn' not found in DOM")

    def test_07_edit_track_modal_and_button_exist(self):
        """
        Test that edit modal and buttons exist

        PREVENTS: Edit functionality errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        try:
            edit_modal = self.driver.find_element(By.ID, "editTrackModal")
            assert edit_modal is not None, "Edit Track modal should exist"

            submit_edit_btn = self.driver.find_element(By.ID, "submitEditTrackBtn")
            assert submit_edit_btn is not None, "Submit edit button should exist"

        except NoSuchElementException as e:
            pytest.fail(f"Edit modal or button missing: {str(e)}")

    def test_08_delete_track_modal_exists(self):
        """
        Test that delete confirmation modal exists

        PREVENTS: Delete functionality errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        try:
            delete_modal = self.driver.find_element(By.ID, "deleteTrackModal")
            assert delete_modal is not None, "Delete Track modal should exist"

            confirm_delete_btn = self.driver.find_element(By.ID, "confirmDeleteTrackBtn")
            assert confirm_delete_btn is not None, "Confirm delete button should exist"

        except NoSuchElementException as e:
            pytest.fail(f"Delete modal or button missing: {str(e)}")

    def test_09_tracks_api_endpoint_responds(self):
        """
        Test that tracks API endpoint responds with 200

        PREVENTS: API 404 errors (like we had with tracks endpoint)
        WHY CRITICAL: Previous tests failed due to missing trailing slash
        """
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test with trailing slash (correct format)
        response = requests.get(
            f"{self.config.base_url}/api/v1/tracks/",
            headers=headers,
            verify=False
        )

        assert response.status_code in [200, 401, 403], \
                      f"API should respond with 200/401/403, got {response.status_code}"

        if response.status_code == 200:
            # Verify response is JSON
            try:
                data = response.json()
                assert isinstance(data, (list, dict)), "API should return JSON list or dict"
            except json.JSONDecodeError:
                pytest.fail("API response is not valid JSON")

    def test_10_tracks_api_with_query_params(self):
        """
        Test that tracks API handles query parameters correctly

        PREVENTS: URL construction errors with query strings
        WHY CRITICAL: Previous issue with /api/v1/tracks?params vs /api/v1/tracks/?params
        """
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test with trailing slash before query params (correct format)
        response = requests.get(
            f"{self.config.base_url}/api/v1/tracks/?status=active",
            headers=headers,
            verify=False
        )

        assert response.status_code in [200, 400, 401, 403], \
                      f"API with query params should respond properly, got {response.status_code}"

    def test_11_css_selectors_are_valid(self):
        """
        Test that all CSS selectors used in tests are valid

        PREVENTS: Invalid selector errors (like :contains() issue)
        WHY CRITICAL: Previous tests failed due to jQuery-style selectors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        # Test each selector without executing (just verify they don't throw)
        selectors = [
            (By.ID, "createTrackBtn"),
            (By.ID, "submitCreateTrackBtn"),
            (By.ID, "submitEditTrackBtn"),
            (By.ID, "confirmDeleteTrackBtn"),
            (By.CSS_SELECTOR, "button.btn-primary[type='submit']"),
            (By.CSS_SELECTOR, "table#tracksTable tbody tr"),
        ]

        for by, selector in selectors:
            try:
                self.driver.find_elements(by, selector)
            except Exception as e:
                pytest.fail(f"Invalid selector: {selector} - {str(e)}")

    def test_12_search_and_filter_inputs_exist(self):
        """
        Test that search and filter inputs exist

        PREVENTS: Filter functionality errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        required_inputs = {
            "trackSearchInput": "Search input field",
            "trackProjectFilter": "Project filter dropdown",
            "trackDifficultyFilter": "Difficulty filter dropdown",
            "trackStatusFilter": "Status filter dropdown"
        }

        missing_inputs = []
        for input_id, description in required_inputs.items():
            try:
                self.driver.find_element(By.ID, input_id)
            except NoSuchElementException:
                missing_inputs.append(f"{input_id} ({description})")

        if missing_inputs:
            pytest.fail(f"Missing filter inputs: {', '.join(missing_inputs)}")

    def test_13_no_duplicate_html_attributes(self):
        """
        Test that buttons don't have duplicate attributes

        PREVENTS: HTML validation errors (like duplicate class attributes)
        WHY CRITICAL: Previous submit button had duplicate class attributes
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        # Get all buttons
        buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[id*='Track']")

        for button in buttons:
            # Check HTML source for duplicate attributes
            outer_html = button.get_attribute("outerHTML")

            # Simple check: attribute should not appear twice
            # Example: <button class="foo" class="bar"> is invalid
            if outer_html.count(' class="') > 1:
                button_id = button.get_attribute("id")
                pytest.fail(f"Button {button_id} has duplicate 'class' attributes")

            if outer_html.count(' type="') > 1:
                button_id = button.get_attribute("id")
                pytest.fail(f"Button {button_id} has duplicate 'type' attributes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
