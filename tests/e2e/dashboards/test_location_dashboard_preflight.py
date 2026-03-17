"""
Locations Dashboard Pre-Flight Validation Tests (TDD - Red Phase)

BUSINESS PURPOSE:
These tests verify that all required HTML elements, API endpoints, and CSS selectors
are correctly configured for the Locations dashboard BEFORE running workflow tests.

The Locations dashboard supports TWO levels of CRUD:
1. Locations CRUD - Create, read, update, delete locations instances
2. Track CRUD at locations level - Create custom tracks for specific locations

USER REQUIREMENT:
"While tracks are created at the project level, the locations dashboard should be
able to add or delete tracks as well, including creating custom tracks.
This should all be part of the tests."

TEST STRATEGY:
1. Run these tests FIRST before any workflow tests
2. If these fail, workflow tests will not run
3. Each test verifies a specific aspect of the dashboard infrastructure

@module test_location_dashboard_preflight
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


class TestLocationDashboardPreFlight(BaseTest):
    """
    Pre-flight validation tests for Locations Dashboard

    WHY THIS TEST CLASS EXISTS:
    The locations dashboard has TWO levels of CRUD operations:
    1. Locations CRUD - Managing locations instances
    2. Track CRUD - Creating custom tracks at locations level

    This test class validates both levels are properly implemented.
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

    # =============================================================================
    # SECTION 1: LOCATIONS CRUD - Tab and Table Tests
    # =============================================================================

    def test_01_locations_tab_exists(self):
        """
        Test that Locations tab exists and is clickable

        PREVENTS: Tab not found errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")

        try:
            locations_tab = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "locationsTab"))
            )
            assert locations_tab.is_displayed(), "Locations tab should be visible"
            assert locations_tab.is_enabled(), "Locations tab should be enabled"
        except TimeoutException:
            pytest.fail("Locations tab with ID 'locationsTab' not found in DOM")

    def test_02_locations_table_exists(self):
        """
        Test that locations table exists with correct ID

        PREVENTS: Table not found errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            locations_table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "locationsTable"))
            )
            assert locations_table is not None, "Locations table should exist"
        except TimeoutException:
            pytest.fail("Locations table with ID 'locationsTable' not found in DOM")

    # =============================================================================
    # SECTION 2: LOCATIONS CRUD - Create Modal and Form Tests
    # =============================================================================

    def test_03_create_location_button_exists(self):
        """
        Test that Create Locations button exists with correct ID

        PREVENTS: Button not found errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            create_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "createLocationBtn"))
            )
            assert create_btn.is_displayed(), "Create Locations button should be visible"
            assert create_btn.is_enabled(), "Create Locations button should be enabled"
        except TimeoutException:
            pytest.fail("Create Locations button with ID 'createLocationBtn' not found in DOM")

    def test_04_create_location_modal_exists(self):
        """
        Test that Create Locations modal exists in DOM

        PREVENTS: Modal not found errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            # Modal should exist in DOM even if not visible
            modal = self.driver.find_element(By.ID, "createLocationModal")
            assert modal is not None, "Create Locations modal should exist in DOM"
        except NoSuchElementException:
            pytest.fail("Create Locations modal with ID 'createLocationModal' not found in DOM")

    def test_05_create_location_form_fields_exist(self):
        """
        Test that all form fields in create locations modal exist with correct IDs

        PREVENTS: Form field not found errors
        WHY CRITICAL: Need to verify ALL fields exist before workflow tests
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        required_fields = {
            "locationName": "Locations name input field",
            "locationSlug": "Locations slug input field",
            "locationDescription": "Locations description textarea",
            "locationCountry": "Country input field",
            "locationRegion": "Region input field",
            "locationCity": "City input field",
            "locationTimezone": "Timezone select dropdown",
            "locationStartDate": "Start date input field",
            "locationEndDate": "End date input field",
            "locationMaxParticipants": "Max participants input field"
        }

        missing_fields = []
        for field_id, description in required_fields.items():
            try:
                self.driver.find_element(By.ID, field_id)
            except NoSuchElementException:
                missing_fields.append(f"{field_id} ({description})")

        if missing_fields:
            pytest.fail(f"Missing form fields in create locations modal: {', '.join(missing_fields)}")

    def test_06_submit_create_location_button_exists(self):
        """
        Test that submit button exists with correct ID and type='submit'

        PREVENTS: Submit button errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            submit_btn = self.driver.find_element(By.ID, "submitCreateLocationBtn")
            assert submit_btn is not None, "Submit button should exist"

            button_type = submit_btn.get_attribute("type")
            assert button_type == "submit", "Submit button should have type='submit'"
        except NoSuchElementException:
            pytest.fail("Submit button with ID 'submitCreateLocationBtn' not found in DOM")

    # =============================================================================
    # SECTION 3: LOCATIONS CRUD - Edit and Delete Modal Tests
    # =============================================================================

    def test_07_edit_location_modal_exists(self):
        """
        Test that edit modal and buttons exist

        PREVENTS: Edit functionality errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            edit_modal = self.driver.find_element(By.ID, "editLocationModal")
            assert edit_modal is not None, "Edit Locations modal should exist"

            submit_edit_btn = self.driver.find_element(By.ID, "submitEditLocationBtn")
            assert submit_edit_btn is not None, "Submit edit button should exist"
        except NoSuchElementException as e:
            pytest.fail(f"Edit modal or button missing: {str(e)}")

    def test_08_delete_location_modal_exists(self):
        """
        Test that delete confirmation modal exists

        PREVENTS: Delete functionality errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            delete_modal = self.driver.find_element(By.ID, "deleteLocationModal")
            assert delete_modal is not None, "Delete Locations modal should exist"

            confirm_delete_btn = self.driver.find_element(By.ID, "confirmDeleteLocationBtn")
            assert confirm_delete_btn is not None, "Confirm delete button should exist"
        except NoSuchElementException as e:
            pytest.fail(f"Delete modal or button missing: {str(e)}")

    # =============================================================================
    # SECTION 4: TRACK CRUD AT LOCATIONS LEVEL - Track Management Section Tests
    # =============================================================================

    def test_09_location_tracks_section_exists(self):
        """
        Test that locations tracks section exists when viewing a locations

        PREVENTS: Track management section not found errors
        WHY CRITICAL: User requirement - locations dashboard must support track CRUD
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            # Section should exist for viewing/managing tracks at locations level
            tracks_section = self.driver.find_element(By.ID, "locationTracksSection")
            assert tracks_section is not None, "Locations tracks section should exist"
        except NoSuchElementException:
            pytest.fail("Locations tracks section with ID 'locationTracksSection' not found in DOM")

    def test_10_create_track_at_location_button_exists(self):
        """
        Test that Create Track button exists in locations tracks section

        PREVENTS: Button not found errors
        WHY CRITICAL: User requirement - "locations dashboard should be able to add tracks"
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            create_track_btn = self.driver.find_element(By.ID, "createTrackAtLocationBtn")
            assert create_track_btn is not None, "Create Track at Locations button should exist"
        except NoSuchElementException:
            pytest.fail("Create Track at Locations button with ID 'createTrackAtLocationBtn' not found in DOM")

    def test_11_create_track_at_location_modal_exists(self):
        """
        Test that Create Track at Locations modal exists

        PREVENTS: Modal not found errors
        WHY CRITICAL: User requirement - "including creating custom tracks"
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            modal = self.driver.find_element(By.ID, "createTrackAtLocationModal")
            assert modal is not None, "Create Track at Locations modal should exist"
        except NoSuchElementException:
            pytest.fail("Create Track at Locations modal with ID 'createTrackAtLocationModal' not found in DOM")

    def test_12_create_track_at_location_form_fields_exist(self):
        """
        Test that track creation form fields exist in locations context

        PREVENTS: Form field not found errors
        WHY CRITICAL: Custom tracks need all standard track fields
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        required_fields = {
            "locationTrackName": "Track name input field",
            "locationTrackDescription": "Track description textarea",
            "locationTrackType": "Track type select dropdown",
            "locationTrackDifficultyLevel": "Difficulty level select dropdown",
            "locationTrackDurationWeeks": "Duration weeks input field",
            "locationTrackMaxStudents": "Max students input field"
        }

        missing_fields = []
        for field_id, description in required_fields.items():
            try:
                self.driver.find_element(By.ID, field_id)
            except NoSuchElementException:
                missing_fields.append(f"{field_id} ({description})")

        if missing_fields:
            pytest.fail(f"Missing form fields in create track at locations modal: {', '.join(missing_fields)}")

    def test_13_edit_track_at_location_modal_exists(self):
        """
        Test that edit track modal exists for locations-level tracks

        PREVENTS: Edit functionality errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            edit_modal = self.driver.find_element(By.ID, "editTrackAtLocationModal")
            assert edit_modal is not None, "Edit Track at Locations modal should exist"

            submit_btn = self.driver.find_element(By.ID, "submitEditTrackAtLocationBtn")
            assert submit_btn is not None, "Submit edit track button should exist"
        except NoSuchElementException as e:
            pytest.fail(f"Edit track modal or button missing: {str(e)}")

    def test_14_delete_track_at_location_modal_exists(self):
        """
        Test that delete track confirmation modal exists

        PREVENTS: Delete functionality errors
        WHY CRITICAL: User requirement - "locations dashboard should be able to delete tracks"
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        try:
            delete_modal = self.driver.find_element(By.ID, "deleteTrackAtLocationModal")
            assert delete_modal is not None, "Delete Track at Locations modal should exist"

            confirm_btn = self.driver.find_element(By.ID, "confirmDeleteTrackAtLocationBtn")
            assert confirm_btn is not None, "Confirm delete track button should exist"
        except NoSuchElementException as e:
            pytest.fail(f"Delete track modal or button missing: {str(e)}")

    # =============================================================================
    # SECTION 5: API ENDPOINT TESTS
    # =============================================================================

    def test_15_locations_api_endpoint_responds(self):
        """
        Test that locations API endpoint responds with 200

        PREVENTS: API 404 errors
        """
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test with trailing slash (correct format)
        response = requests.get(
            f"{self.config.base_url}/api/v1/locations/",
            headers=headers,
            verify=False
        )

        assert response.status_code in [200, 400, 401, 403], \
            f"API should respond with 200/400/401/403, got {response.status_code}"

        if response.status_code == 200:
            # Verify response is JSON
            try:
                data = response.json()
                assert isinstance(data, (list, dict)), "API should return JSON list or dict"
            except json.JSONDecodeError:
                pytest.fail("API response is not valid JSON")

    def test_16_location_tracks_api_endpoint_responds(self):
        """
        Test that locations-specific tracks API endpoint responds

        PREVENTS: API routing errors for locations tracks
        WHY CRITICAL: Need to verify tracks can be queried by location_id
        """
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test tracks filtered by location_id query parameter
        response = requests.get(
            f"{self.config.base_url}/api/v1/tracks/?location_id=550e8400-e29b-41d4-a716-446655440000",
            headers=headers,
            verify=False
        )

        assert response.status_code in [200, 400, 401, 403], \
            f"API with location_id filter should respond properly, got {response.status_code}"

    def test_17_css_selectors_are_valid(self):
        """
        Test that all CSS selectors used in tests are valid

        PREVENTS: Invalid selector errors
        """
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html?org_id=550e8400-e29b-41d4-a716-446655440000")
        self.wait_for_loading_to_complete()

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()

        # Test each selector without executing (just verify they don't throw)
        selectors = [
            (By.ID, "createLocationBtn"),
            (By.ID, "submitCreateLocationBtn"),
            (By.ID, "submitEditLocationBtn"),
            (By.ID, "confirmDeleteLocationBtn"),
            (By.ID, "createTrackAtLocationBtn"),
            (By.ID, "submitEditTrackAtLocationBtn"),
            (By.ID, "confirmDeleteTrackAtLocationBtn"),
            (By.CSS_SELECTOR, "table#locationsTable tbody tr"),
        ]

        for by, selector in selectors:
            try:
                self.driver.find_elements(by, selector)
            except Exception as e:
                pytest.fail(f"Invalid selector: {selector} - {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
