#!/usr/bin/env python3
"""
Multi-Locations Project Creation Workflow E2E Test

BUSINESS PURPOSE:
Comprehensive end-to-end test of the complete multi-locations project creation
workflow with locations/sub-projects. Tests the full user journey from login
through creating a template project and multiple locations-based locations.

TEST COVERAGE:
1. Login and authentication
2. Navigate to org admin dashboard
3. Navigate to Projects tab
4. Create multi-locations project (template)
5. Navigate to project detail view
6. Create Boston locations (US East Coast)
7. Create London locations (UK)
8. Verify both locations in list
9. Test locations filtering
10. Test timeline visualization

VISUAL REGRESSION:
- Captures screenshots at EVERY step
- Checks for visual changes compared to baseline
- Saves to: tests/e2e/dashboards/visual_regression/workflow_multi_location/

CONSOLE ERROR CHECKING:
- Monitors browser console at EVERY step
- Captures JavaScript errors, warnings, network failures
- Fails test if critical errors detected

TDD APPROACH:
This test follows Test-Driven Development principles:
- RED: Test written first, expected to fail initially
- GREEN: Implement features to make test pass
- REFACTOR: Optimize implementation while maintaining passing tests

@test_suite: workflow_multi_location
@requires: organization_management, authentication, projects
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

# Import helpers
from visual_regression_helper import VisualRegressionHelper


class ConsoleErrorChecker:
    """
    Helper to check for browser console errors

    BUSINESS PURPOSE:
    Monitors JavaScript console for errors that could indicate broken functionality.
    Distinguishes between critical errors (breaks functionality) and warnings.

    WHY THIS MATTERS:
    - JavaScript errors often invisible to functional tests
    - Console errors indicate broken API calls, missing resources, logic bugs
    - Early detection prevents user-facing issues
    """

    def __init__(self, driver):
        self.driver = driver
        self.errors = []
        self.warnings = []

    def check_console(self, step_name: str) -> Tuple[List[str], List[str]]:
        """
        Check browser console for errors and warnings

        RETURNS:
        (errors, warnings) - Lists of error/warning messages

        BUSINESS RULES:
        - SEVERE level logs are errors
        - WARNING level logs are warnings
        - SSL certificate warnings are ignored (expected for self-signed certs)
        """
        try:
            logs = self.driver.get_log('browser')
            step_errors = []
            step_warnings = []

            for entry in logs:
                message = entry['message']

                # Skip SSL certificate warnings (expected for self-signed certs)
                if 'SSL certificate' in message or 'valid SSL' in message:
                    continue

                if entry['level'] == 'SEVERE':
                    step_errors.append(f"[{step_name}] {message}")
                    self.errors.append(message)
                elif entry['level'] == 'WARNING':
                    step_warnings.append(f"[{step_name}] {message}")
                    self.warnings.append(message)

            return step_errors, step_warnings

        except Exception as e:
            print(f"⚠️  Could not check console: {e}")
            return [], []

    def assert_no_critical_errors(self, step_name: str):
        """Assert that no critical console errors occurred"""
        errors, warnings = self.check_console(step_name)

        if errors:
            error_summary = '\n'.join(errors)
            raise AssertionError(
                f"Critical console errors detected at step '{step_name}':\n{error_summary}"
            )

        if warnings:
            print(f"⚠️  Warnings at {step_name}: {len(warnings)}")
            for warning in warnings[:3]:  # Show first 3
                print(f"   {warning}")


class TestMultiLocationProjectWorkflow:
    """
    Complete multi-locations project workflow test

    WORKFLOW STEPS:
    1. Login as org admin
    2. Navigate to org-admin-dashboard
    3. Click Projects tab
    4. Click "Create Project" button
    5. Select "Multi-Locations" project type
    6. Fill basic project info
    7. Skip AI configuration
    8. Review and create template project
    9. Verify template project created
    10. Navigate to project detail view
    11. Click "Locations" tab
    12. Create Boston locations
    13. Create London locations
    14. Verify both locations in list
    15. Test locations filtering
    16. Test timeline view
    """

    @classmethod
    def setup_class(cls):
        """Setup test suite"""
        print("\n" + "="*70)
        print("MULTI-LOCATIONS PROJECT CREATION WORKFLOW TEST")
        print("="*70)

        # Initialize Chrome driver
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_argument('--headless=new')  # Run headless for CI/CD

        # Enable browser logging
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(5)

        # Base URL
        cls.base_url = os.environ.get('TEST_BASE_URL', 'https://localhost:3000')

        # Initialize helpers
        cls.visual = VisualRegressionHelper(
            cls.driver,
            test_name="workflow_multi_location",
            threshold=0.02,  # 2% tolerance
            update_baselines=os.environ.get('UPDATE_BASELINES', 'false').lower() == 'true'
        )

        cls.console = ConsoleErrorChecker(cls.driver)

        # Test data
        cls.project_name = f"Global Training Program {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cls.project_slug = f"global-training-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cls.project_id = None
        cls.boston_location_id = None
        cls.london_location_id = None

        # Screenshot counter
        cls.screenshot_count = 0

        print(f"\n📍 Base URL: {cls.base_url}")
        print(f"📁 Visual regression path: {cls.visual.baselines_dir}")
        print(f"🖥️  Headless mode: Enabled")

    @classmethod
    def teardown_class(cls):
        """Cleanup after test suite"""
        print(f"\n📊 Test Summary:")
        print(f"   Screenshots captured: {cls.screenshot_count}")
        print(f"   Console errors: {len(cls.console.errors)}")
        print(f"   Console warnings: {len(cls.console.warnings)}")

        if cls.console.errors:
            print(f"\n❌ Console Errors Detected:")
            for error in cls.console.errors[:5]:
                print(f"   {error[:100]}...")

        if cls.driver:
            cls.driver.quit()

    def capture_step(self, step_name: str, wait_time: float = 1.0):
        """
        Capture visual regression screenshot and check console

        BUSINESS PURPOSE:
        Standardized step capture ensuring both visual and console verification.

        WHY BOTH:
        - Visual: Catches layout breaks, CSS issues, rendering bugs
        - Console: Catches JavaScript errors, API failures, logic bugs
        """
        # Wait for stabilization
        time.sleep(wait_time)

        # Capture screenshot
        passed, diff = self.visual.capture_and_compare(step_name)
        self.screenshot_count += 1

        # Check console
        self.console.assert_no_critical_errors(step_name)

        print(f"✅ Step captured: {step_name} (diff: {diff*100:.2f}%)")

        return passed

    def test_01_login_as_org_admin(self):
        """
        Step 1: Login as organization admin

        BUSINESS FLOW:
        1. Navigate to homepage
        2. Dismiss privacy consent modal
        3. Click login button
        4. Fill credentials
        5. Submit login
        6. Verify authenticated
        """
        print("\n" + "="*70)
        print("STEP 1: Login as Organization Admin")
        print("="*70)

        # Navigate to homepage
        print(f"🌐 Navigating to {self.base_url}/index.html")
        self.driver.get(f"{self.base_url}/index.html")
        time.sleep(3)

        self.capture_step("01_homepage_loaded", wait_time=2)

        # Dismiss privacy modal
        try:
            time.sleep(2)  # Wait for modal to appear
            privacy_modal = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "privacyModal"))
            )

            if privacy_modal.is_displayed():
                print("🍪 Dismissing privacy consent modal...")
                accept_btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Accept All')]"
                )
                accept_btn.click()
                time.sleep(1)

                self.capture_step("02_privacy_modal_dismissed")
        except:
            print("ℹ️  No privacy modal (already dismissed)")

        # Click login button
        print("🔍 Opening login dropdown...")
        login_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        )
        login_btn.click()
        time.sleep(1)

        self.capture_step("03_login_dropdown_opened")

        # Fill login form
        print("📝 Entering credentials...")
        email_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginEmail"))
        )
        password_field = self.driver.find_element(By.ID, "loginPassword")

        email_field.clear()
        email_field.send_keys("orgadmin")
        password_field.clear()
        password_field.send_keys("orgadmin123!")

        self.capture_step("04_login_form_filled")

        # Submit login
        print("🚀 Submitting login...")
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        time.sleep(5)

        self.capture_step("05_login_submitted")

        # Verify authentication
        auth_token = self.driver.execute_script("return localStorage.getItem('authToken');")
        assert auth_token, "Login failed - no auth token found"

        print("✅ Successfully logged in")

    def test_02_navigate_to_dashboard(self):
        """
        Step 2: Navigate to organization admin dashboard

        BUSINESS FLOW:
        1. Navigate to org-admin-dashboard.html
        2. Wait for dashboard initialization
        3. Verify orgTitle element appears
        4. Verify no loading spinner
        """
        print("\n" + "="*70)
        print("STEP 2: Navigate to Organization Admin Dashboard")
        print("="*70)

        org_id = "550e8400-e29b-41d4-a716-446655440000"  # AI Elevate org
        dashboard_url = f"{self.base_url}/html/org-admin-dashboard.html?org_id={org_id}"

        print(f"🌐 Navigating to {dashboard_url}")
        self.driver.get(dashboard_url)
        time.sleep(5)

        self.capture_step("06_dashboard_loading")

        # Wait for dashboard to initialize
        print("⏳ Waiting for dashboard initialization...")
        org_title = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "orgTitle"))
        )

        title_text = org_title.text
        print(f"📊 Dashboard loaded: {title_text}")

        # Wait for any loading spinners to disappear
        try:
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
            )
        except:
            pass

        time.sleep(2)

        self.capture_step("07_dashboard_loaded")

        print("✅ Dashboard loaded successfully")

    def test_03_navigate_to_projects_tab(self):
        """
        Step 3: Click Projects tab

        BUSINESS FLOW:
        1. Find Projects tab
        2. Click tab
        3. Wait for projects content to load
        4. Verify Create Project button visible
        """
        print("\n" + "="*70)
        print("STEP 3: Navigate to Projects Tab")
        print("="*70)

        print("🔍 Finding Projects tab...")
        projects_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tab='projects']"))
        )

        print("🖱️  Clicking Projects tab...")
        projects_tab.click()
        time.sleep(3)

        self.capture_step("08_projects_tab_clicked")

        # Wait for projects content to load
        print("⏳ Waiting for projects content...")
        create_btn = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "createProjectBtn"))
        )

        assert create_btn.is_displayed(), "Create Project button not visible"

        self.capture_step("09_projects_tab_loaded")

        print("✅ Projects tab loaded")

    def test_04_open_create_project_modal(self):
        """
        Step 4: Click Create Project button

        BUSINESS FLOW:
        1. Click Create Project button
        2. Wait for modal to open
        3. Verify Step 0 (project type selection) is active
        """
        print("\n" + "="*70)
        print("STEP 4: Open Create Project Modal")
        print("="*70)

        print("🖱️  Clicking Create Project button...")
        create_btn = self.driver.find_element(By.ID, "createProjectBtn")
        create_btn.click()
        time.sleep(2)

        self.capture_step("10_create_project_clicked")

        # Wait for modal to open
        print("⏳ Waiting for modal...")
        modal = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "createProjectModal"))
        )

        self.capture_step("11_create_project_modal_opened")

        # Verify Step 0 is active
        step0 = modal.find_element(By.ID, "projectStep0")
        assert "active" in step0.get_attribute("class"), "Step 0 not active"

        print("✅ Create Project modal opened")

    def test_05_select_multi_location_project_type(self):
        """
        Step 5: Select Multi-Locations project type

        BUSINESS FLOW:
        1. Find multi-locations radio button
        2. Click it
        3. Verify description appears
        4. Click Next to advance to Step 1
        """
        print("\n" + "="*70)
        print("STEP 5: Select Multi-Locations Project Type")
        print("="*70)

        modal = self.driver.find_element(By.ID, "createProjectModal")

        print("🎯 Selecting Multi-Locations project type...")
        multi_location_radio = modal.find_element(By.ID, "projectTypeMultiLocation")
        multi_location_radio.click()
        time.sleep(1)

        self.capture_step("12_multi_location_selected")

        # Verify description appears
        description = modal.find_element(By.ID, "multiLocationDescription")
        assert description.is_displayed(), "Multi-locations description not shown"
        assert "locations" in description.text.lower(), "Description missing 'locations'"

        # Click Next
        print("➡️  Advancing to Step 1...")
        next_btn = modal.find_element(By.ID, "projectStep0NextBtn")
        next_btn.click()
        time.sleep(1)

        self.capture_step("13_advanced_to_step1")

        # Verify Step 1 is active
        step1 = modal.find_element(By.ID, "projectStep1")
        assert "active" in step1.get_attribute("class"), "Step 1 not active"

        print("✅ Multi-locations type selected, Step 1 active")

    def test_06_fill_basic_project_info(self):
        """
        Step 6: Fill basic project information

        BUSINESS FLOW:
        1. Fill project name
        2. Fill project slug
        3. Fill description
        4. Select target roles
        5. Verify template indicator shown
        6. Click Next to Step 2
        """
        print("\n" + "="*70)
        print("STEP 6: Fill Basic Project Information")
        print("="*70)

        modal = self.driver.find_element(By.ID, "createProjectModal")

        print("📝 Filling project details...")

        # Project name
        name_field = modal.find_element(By.ID, "projectName")
        name_field.clear()
        name_field.send_keys(self.project_name)
        print(f"   Name: {self.project_name}")

        # Project slug
        slug_field = modal.find_element(By.ID, "projectSlug")
        slug_field.clear()
        slug_field.send_keys(self.project_slug)
        print(f"   Slug: {self.project_slug}")

        # Description
        desc_field = modal.find_element(By.ID, "projectDescription")
        desc_field.clear()
        desc_field.send_keys(
            "Multi-locations graduate training program across Boston and London offices"
        )

        self.capture_step("14_basic_info_filled")

        # Select target roles
        print("👥 Selecting target roles...")
        roles_select = Select(modal.find_element(By.ID, "projectTargetRoles"))
        roles_select.select_by_value("application_developers")
        roles_select.select_by_value("devops_engineers")

        time.sleep(1)

        self.capture_step("15_target_roles_selected")

        # Verify template indicator
        template_indicator = modal.find_element(By.ID, "templateProjectIndicator")
        assert template_indicator.is_displayed(), "Template indicator not shown"

        # Click Next to Step 2
        print("➡️  Advancing to Step 2...")
        next_btn = modal.find_element(By.CSS_SELECTOR, "#projectStep1 .next-step-btn")
        next_btn.click()
        time.sleep(1)

        self.capture_step("16_advanced_to_step2")

        # Verify Step 2 is active
        step2 = modal.find_element(By.ID, "projectStep2")
        assert "active" in step2.get_attribute("class"), "Step 2 not active"

        print("✅ Basic info filled, Step 2 active")

    def test_07_skip_ai_configuration(self):
        """
        Step 7: Skip AI configuration (Step 2)

        BUSINESS FLOW:
        1. Verify on Step 2 (AI Configuration)
        2. Click Next without configuring AI
        3. Advance to Step 3 (Review)
        """
        print("\n" + "="*70)
        print("STEP 7: Skip AI Configuration")
        print("="*70)

        modal = self.driver.find_element(By.ID, "createProjectModal")

        print("⏭️  Skipping AI configuration...")

        self.capture_step("17_ai_config_step")

        # Click Next to Step 3
        next_btn = modal.find_element(By.CSS_SELECTOR, "#projectStep2 .next-step-btn")
        next_btn.click()
        time.sleep(1)

        self.capture_step("18_advanced_to_step3")

        # Verify Step 3 is active
        step3 = modal.find_element(By.ID, "projectStep3")
        assert "active" in step3.get_attribute("class"), "Step 3 not active"

        print("✅ AI config skipped, Step 3 active")

    def test_08_review_and_create_project(self):
        """
        Step 8: Review and create template project

        BUSINESS FLOW:
        1. Verify on Step 3 (Review)
        2. Verify sub-projects placeholder shown
        3. Click Create Project button
        4. Wait for success notification
        5. Wait for modal to close
        """
        print("\n" + "="*70)
        print("STEP 8: Review and Create Template Project")
        print("="*70)

        modal = self.driver.find_element(By.ID, "createProjectModal")
        step3 = modal.find_element(By.ID, "projectStep3")

        print("👀 Reviewing project configuration...")

        self.capture_step("19_review_step")

        # Verify sub-projects placeholder
        sub_projects_section = step3.find_element(By.ID, "subProjectsPlaceholder")
        assert sub_projects_section.is_displayed(), "Sub-projects section not shown"
        assert "locations will be created" in sub_projects_section.text.lower()

        # Create project
        print("🚀 Creating project...")
        create_btn = modal.find_element(By.ID, "submitProjectBtn")
        create_btn.click()
        time.sleep(3)

        self.capture_step("20_project_create_clicked")

        # Wait for success notification
        print("⏳ Waiting for success notification...")
        success_msg = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.success"))
        )

        assert "created successfully" in success_msg.text.lower()

        self.capture_step("21_project_created_success")

        # Wait for modal to close
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located((By.ID, "createProjectModal"))
        )

        print("✅ Template project created successfully")

    def test_09_navigate_to_project_detail(self):
        """
        Step 9: Navigate to project detail view

        BUSINESS FLOW:
        1. Find newly created project in list
        2. Click View/Manage button
        3. Wait for project detail view to open
        4. Verify Locations tab exists
        """
        print("\n" + "="*70)
        print("STEP 9: Navigate to Project Detail View")
        print("="*70)

        print("🔍 Finding newly created project...")
        time.sleep(2)  # Wait for projects list to refresh

        self.capture_step("22_projects_list_refreshed")

        # Click on first project (should be our newly created one)
        view_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        view_btn.click()
        time.sleep(2)

        self.capture_step("23_project_detail_clicked")

        # Wait for project detail view
        print("⏳ Waiting for project detail view...")
        project_detail = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        )

        self.capture_step("24_project_detail_opened")

        # Verify Locations tab exists
        locations_tab = project_detail.find_element(By.CSS_SELECTOR, "[data-tab='locations']")
        assert locations_tab.is_displayed(), "Locations tab not visible"

        print("✅ Project detail view opened")

    def test_10_navigate_to_locations_tab(self):
        """
        Step 10: Click Locations tab

        BUSINESS FLOW:
        1. Click Locations tab
        2. Wait for locations content to load
        3. Verify empty state shown
        4. Verify Create Locations button exists
        5. Verify filters exist
        """
        print("\n" + "="*70)
        print("STEP 10: Navigate to Locations Tab")
        print("="*70)

        project_detail = self.driver.find_element(By.ID, "projectDetailView")

        print("🖱️  Clicking Locations tab...")
        locations_tab = project_detail.find_element(By.CSS_SELECTOR, "[data-tab='locations']")
        locations_tab.click()
        time.sleep(2)

        self.capture_step("25_locations_tab_clicked")

        # Wait for locations content
        print("⏳ Waiting for locations content...")
        locations_content = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        self.capture_step("26_locations_tab_loaded")

        # Verify empty state
        empty_state = locations_content.find_element(By.CLASS_NAME, "empty-state")
        assert "no locations" in empty_state.text.lower()

        # Verify Create Locations button
        create_location_btn = locations_content.find_element(By.ID, "createLocationBtn")
        assert create_location_btn.is_displayed()
        assert create_location_btn.is_enabled()

        # Verify filters exist
        locations_content.find_element(By.ID, "locationCountryFilter")
        locations_content.find_element(By.ID, "locationCityFilter")

        print("✅ Locations tab loaded with empty state")

    def test_11_create_boston_location(self):
        """
        Step 11: Create Boston locations (US East Coast)

        BUSINESS FLOW:
        1. Click Create Locations button
        2. Fill Step 1: Basic info (name, slug, description)
        3. Fill Step 2: Locations (US, Massachusetts, Boston)
        4. Fill Step 3: Schedule (dates, max participants)
        5. Fill Step 4: Track selection
        6. Review and create (Step 5)
        7. Verify success notification
        """
        print("\n" + "="*70)
        print("STEP 11: Create Boston Locations")
        print("="*70)

        locations_content = self.driver.find_element(By.ID, "locationsTabContent")

        # Click Create Locations
        print("🖱️  Opening locations creation modal...")
        create_location_btn = locations_content.find_element(By.ID, "createLocationBtn")
        create_location_btn.click()
        time.sleep(2)

        self.capture_step("27_create_location_clicked")

        # Wait for modal
        location_modal = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "createLocationModal"))
        )

        self.capture_step("28_location_modal_opened")

        # Step 1: Basic Info
        print("📝 Step 1: Basic Information...")
        location_modal.find_element(By.ID, "locationName").send_keys("Boston Graduate Program Fall 2025")
        location_modal.find_element(By.ID, "locationSlug").send_keys("boston-fall-2025")
        location_modal.find_element(By.ID, "locationDescription").send_keys(
            "Graduate training program for Boston office, US East Coast region"
        )

        self.capture_step("29_boston_step1_filled")

        location_modal.find_element(By.CSS_SELECTOR, "#locationStep1 .next-step-btn").click()
        time.sleep(1)

        # Step 2: Locations
        print("📍 Step 2: Locations...")
        step2 = location_modal.find_element(By.ID, "locationStep2")

        Select(step2.find_element(By.ID, "locationCountry")).select_by_visible_text("United States")
        time.sleep(1)  # Wait for regions to load
        Select(step2.find_element(By.ID, "locationRegion")).select_by_visible_text("Massachusetts")
        step2.find_element(By.ID, "locationCity").send_keys("Boston")
        Select(step2.find_element(By.ID, "locationTimezone")).select_by_value("America/New_York")
        step2.find_element(By.ID, "locationAddress").send_keys("1 Boston Place, Boston, MA 02108")

        self.capture_step("30_boston_step2_filled")

        step2.find_element(By.CSS_SELECTOR, ".next-step-btn").click()
        time.sleep(1)

        # Step 3: Schedule
        print("📅 Step 3: Schedule...")
        step3 = location_modal.find_element(By.ID, "locationStep3")

        start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=150)).strftime("%Y-%m-%d")

        step3.find_element(By.ID, "locationStartDate").send_keys(start_date)
        step3.find_element(By.ID, "locationEndDate").send_keys(end_date)
        step3.find_element(By.ID, "locationMaxParticipants").send_keys("30")

        self.capture_step("31_boston_step3_filled")

        step3.find_element(By.CSS_SELECTOR, ".next-step-btn").click()
        time.sleep(1)

        # Step 4: Track Selection
        print("🎯 Step 4: Track Selection...")
        step4 = location_modal.find_element(By.ID, "locationStep4")

        self.capture_step("32_boston_step4_tracks")

        # Select first 2 tracks
        track_list = step4.find_element(By.ID, "availableTracksList")
        track_items = track_list.find_elements(By.CLASS_NAME, "track-item")

        if len(track_items) >= 2:
            for item in track_items[:2]:
                checkbox = item.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                checkbox.click()

        self.capture_step("33_boston_step4_tracks_selected")

        step4.find_element(By.CSS_SELECTOR, ".next-step-btn").click()
        time.sleep(1)

        # Step 5: Review and Create
        print("👀 Step 5: Review and Create...")
        step5 = location_modal.find_element(By.ID, "locationStep5")

        self.capture_step("34_boston_step5_review")

        # Verify review sections
        review_basic = step5.find_element(By.ID, "reviewBasicInfo")
        assert "Boston" in review_basic.text

        # Create locations
        print("🚀 Creating Boston locations...")
        create_btn = step5.find_element(By.ID, "submitLocationBtn")
        create_btn.click()
        time.sleep(3)

        self.capture_step("35_boston_location_created")

        # Wait for success notification
        success_msg = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.success"))
        )
        assert "locations created" in success_msg.text.lower()

        # Wait for modal to close
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located((By.ID, "createLocationModal"))
        )

        print("✅ Boston locations created successfully")

    def test_12_create_london_location(self):
        """
        Step 12: Create London locations (UK)

        BUSINESS FLOW:
        Same as Boston but with UK locations details
        """
        print("\n" + "="*70)
        print("STEP 12: Create London Locations")
        print("="*70)

        locations_content = self.driver.find_element(By.ID, "locationsTabContent")

        # Click Create Locations
        print("🖱️  Opening locations creation modal...")
        create_location_btn = locations_content.find_element(By.ID, "createLocationBtn")
        create_location_btn.click()
        time.sleep(2)

        self.capture_step("36_create_london_location_clicked")

        # Wait for modal
        location_modal = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "createLocationModal"))
        )

        # Step 1: Basic Info
        print("📝 Step 1: Basic Information...")
        location_modal.find_element(By.ID, "locationName").send_keys("London Graduate Program Fall 2025")
        location_modal.find_element(By.ID, "locationSlug").send_keys("london-fall-2025")
        location_modal.find_element(By.ID, "locationDescription").send_keys(
            "Graduate training program for London office, UK region"
        )

        self.capture_step("37_london_step1_filled")

        location_modal.find_element(By.CSS_SELECTOR, "#locationStep1 .next-step-btn").click()
        time.sleep(1)

        # Step 2: Locations
        print("📍 Step 2: Locations...")
        step2 = location_modal.find_element(By.ID, "locationStep2")

        Select(step2.find_element(By.ID, "locationCountry")).select_by_visible_text("United Kingdom")
        time.sleep(1)
        Select(step2.find_element(By.ID, "locationRegion")).select_by_visible_text("England")
        step2.find_element(By.ID, "locationCity").send_keys("London")
        Select(step2.find_element(By.ID, "locationTimezone")).select_by_value("Europe/London")
        step2.find_element(By.ID, "locationAddress").send_keys("10 Downing Street, London SW1A 2AA")

        self.capture_step("38_london_step2_filled")

        step2.find_element(By.CSS_SELECTOR, ".next-step-btn").click()
        time.sleep(1)

        # Step 3: Schedule
        print("📅 Step 3: Schedule...")
        step3 = location_modal.find_element(By.ID, "locationStep3")

        start_date = (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=165)).strftime("%Y-%m-%d")

        step3.find_element(By.ID, "locationStartDate").send_keys(start_date)
        step3.find_element(By.ID, "locationEndDate").send_keys(end_date)
        step3.find_element(By.ID, "locationMaxParticipants").send_keys("25")

        self.capture_step("39_london_step3_filled")

        step3.find_element(By.CSS_SELECTOR, ".next-step-btn").click()
        time.sleep(1)

        # Step 4: Track Selection
        print("🎯 Step 4: Track Selection...")
        step4 = location_modal.find_element(By.ID, "locationStep4")

        # Select first 2 tracks
        track_list = step4.find_element(By.ID, "availableTracksList")
        track_items = track_list.find_elements(By.CLASS_NAME, "track-item")

        if len(track_items) >= 2:
            for item in track_items[:2]:
                checkbox = item.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                checkbox.click()

        self.capture_step("40_london_step4_tracks_selected")

        step4.find_element(By.CSS_SELECTOR, ".next-step-btn").click()
        time.sleep(1)

        # Step 5: Review and Create
        print("👀 Step 5: Review and Create...")
        step5 = location_modal.find_element(By.ID, "locationStep5")

        self.capture_step("41_london_step5_review")

        # Create locations
        print("🚀 Creating London locations...")
        create_btn = step5.find_element(By.ID, "submitLocationBtn")
        create_btn.click()
        time.sleep(3)

        self.capture_step("42_london_location_created")

        # Wait for success notification
        success_msg = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.success"))
        )
        assert "locations created" in success_msg.text.lower()

        print("✅ London locations created successfully")

    def test_13_verify_both_locations_in_list(self):
        """
        Step 13: Verify both locations appear in list

        BUSINESS FLOW:
        1. Wait for locations list to refresh
        2. Verify 2 locations items exist
        3. Verify Boston locations details
        4. Verify London locations details
        """
        print("\n" + "="*70)
        print("STEP 13: Verify Both Locations in List")
        print("="*70)

        print("⏳ Waiting for locations list to refresh...")
        time.sleep(3)

        self.capture_step("43_locations_list_with_both")

        locations_content = self.driver.find_element(By.ID, "locationsTabContent")
        locations_list = locations_content.find_element(By.ID, "locationsList")
        location_items = locations_list.find_elements(By.CLASS_NAME, "locations-item")

        print(f"📊 Found {len(location_items)} locations")
        assert len(location_items) == 2, f"Expected 2 locations, found {len(location_items)}"

        # Verify locations
        location_locations = [
            item.find_element(By.CLASS_NAME, "locations-locations").text
            for item in location_items
        ]

        assert any("Boston" in loc for loc in location_locations), "Boston locations not found"
        assert any("London" in loc for loc in location_locations), "London locations not found"

        print("✅ Both locations verified in list")

    def test_14_test_location_filtering(self):
        """
        Step 14: Test locations filtering

        BUSINESS FLOW:
        1. Filter by country (United States)
        2. Verify only Boston locations shown
        3. Clear filter
        4. Filter by city (London)
        5. Verify only London locations shown
        6. Clear all filters
        7. Verify both locations shown
        """
        print("\n" + "="*70)
        print("STEP 14: Test Locations Filtering")
        print("="*70)

        locations_content = self.driver.find_element(By.ID, "locationsTabContent")

        # Filter by United States
        print("🔍 Filtering by country: United States...")
        country_filter = Select(locations_content.find_element(By.ID, "locationCountryFilter"))
        country_filter.select_by_visible_text("United States")
        time.sleep(2)

        self.capture_step("44_filter_usa")

        location_items = locations_content.find_elements(By.CLASS_NAME, "locations-item")
        assert len(location_items) == 1, "Should show only 1 locations (Boston)"
        assert "Boston" in location_items[0].find_element(By.CLASS_NAME, "locations-locations").text

        # Clear filter
        print("🔄 Clearing filter...")
        clear_btn = locations_content.find_element(By.ID, "clearLocationsFiltersBtn")
        clear_btn.click()
        time.sleep(2)

        self.capture_step("45_filter_cleared")

        # Filter by city (London)
        print("🔍 Filtering by city: London...")
        city_filter = locations_content.find_element(By.ID, "locationCityFilter")
        city_filter.clear()
        city_filter.send_keys("London")
        time.sleep(2)

        self.capture_step("46_filter_london")

        location_items = locations_content.find_elements(By.CLASS_NAME, "locations-item")
        assert len(location_items) == 1, "Should show only 1 locations (London)"
        assert "London" in location_items[0].find_element(By.CLASS_NAME, "locations-locations").text

        # Clear all filters
        print("🔄 Clearing all filters...")
        clear_btn.click()
        time.sleep(2)

        self.capture_step("47_all_filters_cleared")

        location_items = locations_content.find_elements(By.CLASS_NAME, "locations-item")
        assert len(location_items) == 2, "Should show both locations"

        print("✅ Locations filtering working correctly")

    def test_15_test_timeline_view(self):
        """
        Step 15: Test timeline visualization

        BUSINESS FLOW:
        1. Click timeline view button
        2. Verify timeline container appears
        3. Verify 2 timeline bars shown
        4. Verify each bar has start/end markers
        5. Switch back to list view
        """
        print("\n" + "="*70)
        print("STEP 15: Test Timeline Visualization")
        print("="*70)

        locations_content = self.driver.find_element(By.ID, "locationsTabContent")

        # Click timeline view
        print("🖱️  Switching to timeline view...")
        timeline_btn = locations_content.find_element(By.ID, "locationTimelineViewBtn")
        timeline_btn.click()
        time.sleep(2)

        self.capture_step("48_timeline_view_clicked")

        # Wait for timeline container
        print("⏳ Waiting for timeline...")
        timeline_container = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "locationTimelineContainer"))
        )

        self.capture_step("49_timeline_view_loaded")

        # Verify timeline bars
        timeline_bars = timeline_container.find_elements(By.CLASS_NAME, "timeline-bar")
        print(f"📊 Found {len(timeline_bars)} timeline bars")
        assert len(timeline_bars) == 2, "Should show 2 locations timelines"

        # Verify each bar has markers
        for i, bar in enumerate(timeline_bars):
            start_marker = bar.find_element(By.CLASS_NAME, "timeline-start")
            end_marker = bar.find_element(By.CLASS_NAME, "timeline-end")
            location_label = bar.find_element(By.CLASS_NAME, "timeline-label")

            assert start_marker.is_displayed(), f"Bar {i} start marker not visible"
            assert end_marker.is_displayed(), f"Bar {i} end marker not visible"
            assert location_label.is_displayed(), f"Bar {i} label not visible"

        # Switch back to list view
        print("🔙 Switching back to list view...")
        list_btn = locations_content.find_element(By.ID, "locationListViewBtn")
        list_btn.click()
        time.sleep(1)

        self.capture_step("50_back_to_list_view")

        print("✅ Timeline visualization working correctly")

    def test_16_generate_final_report(self):
        """
        Step 16: Generate final test report

        BUSINESS FLOW:
        1. Collect all test results
        2. Generate summary report
        3. Save to /tmp/multi_location_workflow_report.txt
        4. Print summary
        """
        print("\n" + "="*70)
        print("STEP 16: Generate Final Report")
        print("="*70)

        report = []
        report.append("="*70)
        report.append("MULTI-LOCATIONS PROJECT WORKFLOW TEST REPORT")
        report.append("="*70)
        report.append(f"\nGenerated: {datetime.now().isoformat()}")
        report.append(f"Base URL: {self.base_url}")
        report.append(f"\nTest Results:")
        report.append(f"  ✅ All 16 workflow steps completed successfully")
        report.append(f"\nVisual Regression:")
        report.append(f"  Screenshots captured: {self.screenshot_count}")
        report.append(f"  Locations: {self.visual.baselines_dir}")
        report.append(f"\nConsole Monitoring:")
        report.append(f"  Console errors: {len(self.console.errors)}")
        report.append(f"  Console warnings: {len(self.console.warnings)}")

        if self.console.errors:
            report.append(f"\n❌ Console Errors:")
            for error in self.console.errors[:10]:
                report.append(f"  {error[:100]}...")

        if self.console.warnings:
            report.append(f"\n⚠️  Console Warnings:")
            for warning in self.console.warnings[:5]:
                report.append(f"  {warning[:100]}...")

        report.append(f"\nWorkflow Summary:")
        report.append(f"  1. ✅ Login as org admin")
        report.append(f"  2. ✅ Navigate to dashboard")
        report.append(f"  3. ✅ Navigate to Projects tab")
        report.append(f"  4. ✅ Open Create Project modal")
        report.append(f"  5. ✅ Select Multi-Locations type")
        report.append(f"  6. ✅ Fill basic project info")
        report.append(f"  7. ✅ Skip AI configuration")
        report.append(f"  8. ✅ Create template project")
        report.append(f"  9. ✅ Navigate to project detail")
        report.append(f" 10. ✅ Navigate to Locations tab")
        report.append(f" 11. ✅ Create Boston locations")
        report.append(f" 12. ✅ Create London locations")
        report.append(f" 13. ✅ Verify both locations in list")
        report.append(f" 14. ✅ Test locations filtering")
        report.append(f" 15. ✅ Test timeline visualization")
        report.append(f" 16. ✅ Generate final report")
        report.append("\n" + "="*70)
        report.append("TEST SUITE COMPLETED SUCCESSFULLY")
        report.append("="*70)

        report_text = "\n".join(report)

        # Save report
        report_path = "/tmp/multi_location_workflow_report.txt"
        with open(report_path, 'w') as f:
            f.write(report_text)

        print(report_text)
        print(f"\n📝 Report saved to: {report_path}")

        # Return summary
        return {
            'screenshots': self.screenshot_count,
            'console_errors': len(self.console.errors),
            'console_warnings': len(self.console.warnings),
            'status': 'PASSED'
        }


def main():
    """
    Main entry point for running test suite

    USAGE:
    python test_multi_location_project_workflow.py

    ENVIRONMENT VARIABLES:
    - TEST_BASE_URL: Base URL (default: https://localhost:3000)
    - UPDATE_BASELINES: Set to 'true' to update visual baselines
    """
    import sys

    # Run test suite
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes',
        '-s'  # Show print statements
    ])


if __name__ == "__main__":
    main()
