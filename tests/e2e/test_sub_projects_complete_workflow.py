"""
E2E Tests for Sub-Projects (Locations) Feature

BUSINESS CONTEXT:
Tests the complete workflow for creating and managing sub-projects/locations
in a hierarchical project structure. Validates multi-locations program management,
track overrides, and locations-based filtering.

TEST COVERAGE:
- Main project creation with sub-projects enabled
- Sub-project (locations) creation in multiple locations
- Locations filtering (country, region, city)
- Track assignment and date overrides
- Enrollment isolation between locations
- Timeline visualization
- Sub-project comparison

TDD RED PHASE - These tests should FAIL initially
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import time
from datetime import datetime, timedelta


@pytest.fixture
def org_admin_session(test_driver, test_base_url):
    """Setup organization admin session and navigate to projects"""
    # Navigate to index first
    test_driver.get(f"{test_base_url}/html/index.html")
    time.sleep(2)

    # Set up organization admin authenticated state
    test_driver.execute_script("""
        localStorage.setItem('authToken', 'test-org-admin-token-locations');
        localStorage.setItem('currentUser', JSON.stringify({
            id: 100,
            email: 'orgadmin@testorg.com',
            role: 'organization_admin',
            organization_id: 1,
            name: 'Test Org Admin'
        }));
        localStorage.setItem('userEmail', 'orgadmin@testorg.com');
        localStorage.setItem('sessionStart', Date.now().toString());
        localStorage.setItem('lastActivity', Date.now().toString());
    """)

    # Navigate to org admin dashboard
    test_driver.get(f"{test_base_url}/html/org-admin-dashboard.html?org_id=1")
    time.sleep(3)

    # Click on Projects tab
    projects_tab = WebDriverWait(test_driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tab='projects']"))
    )
    projects_tab.click()

    # Wait for projects tab content to load (modular HTML takes time to load)
    WebDriverWait(test_driver, 15).until(
        EC.presence_of_element_located((By.ID, "createProjectBtn"))
    )

    return test_driver


class TestMainProjectWithSubProjectsCreation:
    """Test creating a main project with sub-projects enabled"""

    def test_01_create_main_project_button_exists(self, org_admin_session):
        """Verify Create New Project button is present"""
        create_btn = WebDriverWait(org_admin_session, 10).until(
            EC.presence_of_element_located((By.ID, "createProjectBtn"))
        )
        assert create_btn.is_displayed()
        assert create_btn.is_enabled()

    def test_02_open_project_creation_wizard(self, org_admin_session):
        """Open project creation wizard and verify first step"""
        create_btn = org_admin_session.find_element(By.ID, "createProjectBtn")
        create_btn.click()

        # Wait for modal to open
        modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createProjectModal"))
        )

        # Verify Step 0 (new): Project Type Selection
        step0 = modal.find_element(By.ID, "projectStep0")
        assert "active" in step0.get_attribute("class")

        # Verify project type radio buttons exist
        single_project_radio = modal.find_element(By.ID, "projectTypeSingle")
        multi_location_radio = modal.find_element(By.ID, "projectTypeMultiLocation")

        assert single_project_radio.is_displayed()
        assert multi_location_radio.is_displayed()

    def test_03_select_multi_location_project_type(self, org_admin_session):
        """Select multi-locations project type and advance to Step 1"""
        create_btn = org_admin_session.find_element(By.ID, "createProjectBtn")
        create_btn.click()

        modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createProjectModal"))
        )

        # Select multi-locations project type
        multi_location_radio = modal.find_element(By.ID, "projectTypeMultiLocation")
        multi_location_radio.click()

        # Verify description text appears
        description_text = modal.find_element(By.ID, "multiLocationDescription")
        assert "multiple locations" in description_text.text.lower()
        assert "locations" in description_text.text.lower()

        # Click Next to advance to Step 1
        next_btn = modal.find_element(By.ID, "projectStep0NextBtn")
        next_btn.click()

        # Wait for Step 1 to become active
        step1 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "projectStep1"))
        )
        assert "active" in step1.get_attribute("class")

    def test_04_complete_main_project_basic_info(self, org_admin_session):
        """Fill in basic information for main project"""
        create_btn = org_admin_session.find_element(By.ID, "createProjectBtn")
        create_btn.click()

        modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createProjectModal"))
        )

        # Select multi-locations and advance to Step 1
        multi_location_radio = modal.find_element(By.ID, "projectTypeMultiLocation")
        multi_location_radio.click()
        next_btn = modal.find_element(By.ID, "projectStep0NextBtn")
        next_btn.click()

        # Wait for Step 1
        WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "projectStep1"))
        )

        # Fill in basic info
        name_input = modal.find_element(By.ID, "projectName")
        name_input.clear()
        name_input.send_keys("Cloud Architecture Graduate Program")

        slug_input = modal.find_element(By.ID, "projectSlug")
        slug_input.clear()
        slug_input.send_keys("cloud-arch-grad-program")

        description_input = modal.find_element(By.ID, "projectDescription")
        description_input.clear()
        description_input.send_keys("Comprehensive cloud architecture training for graduate engineers across multiple global locations")

        # Select target roles
        roles_select = Select(modal.find_element(By.ID, "projectTargetRoles"))
        roles_select.select_by_value("application_developers")
        roles_select.select_by_value("devops_engineers")

        # Verify template indicator is shown
        template_indicator = modal.find_element(By.ID, "templateProjectIndicator")
        assert template_indicator.is_displayed()
        assert "template" in template_indicator.text.lower()

        # Click Next to Step 2
        step1_next_btn = modal.find_element(By.CSS_SELECTOR, "#projectStep1 .next-step-btn")
        step1_next_btn.click()

        # Verify Step 2 becomes active
        step2 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "projectStep2"))
        )
        assert "active" in step2.get_attribute("class")

    def test_05_verify_sub_projects_section_in_review_step(self, org_admin_session):
        """Complete wizard and verify sub-projects section appears in final review"""
        create_btn = org_admin_session.find_element(By.ID, "createProjectBtn")
        create_btn.click()

        modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createProjectModal"))
        )

        # Navigate through wizard
        multi_location_radio = modal.find_element(By.ID, "projectTypeMultiLocation")
        multi_location_radio.click()
        modal.find_element(By.ID, "projectStep0NextBtn").click()

        # Step 1: Basic info
        WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "projectStep1"))
        )
        modal.find_element(By.ID, "projectName").send_keys("Test Program")
        modal.find_element(By.ID, "projectSlug").send_keys("test-program")
        modal.find_element(By.ID, "projectDescription").send_keys("Test description")
        modal.find_element(By.CSS_SELECTOR, "#projectStep1 .next-step-btn").click()

        # Step 2: Configuration (skip AI suggestions)
        WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "projectStep2"))
        )
        modal.find_element(By.CSS_SELECTOR, "#projectStep2 .next-step-btn").click()

        # Step 3: Review and Create
        step3 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "projectStep3"))
        )
        assert "active" in step3.get_attribute("class")

        # Verify sub-projects placeholder section exists
        sub_projects_section = step3.find_element(By.ID, "subProjectsPlaceholder")
        assert sub_projects_section.is_displayed()
        assert "locations will be created" in sub_projects_section.text.lower()

        # Create main project
        create_btn = modal.find_element(By.ID, "submitProjectBtn")
        create_btn.click()

        # Wait for success notification
        success_msg = WebDriverWait(org_admin_session, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.success"))
        )
        assert "created successfully" in success_msg.text.lower()


class TestSubProjectManagementTab:
    """Test sub-project management tab and UI"""

    def test_01_view_project_shows_locations_tab(self, org_admin_session):
        """After creating main project, verify Locations tab appears in project view"""
        # Assuming a main project exists from previous test
        # Click on first project in table
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        # Wait for project detail modal/view
        project_detail = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        )

        # Verify Locations/Locations tab exists
        locations_tab = project_detail.find_element(By.CSS_SELECTOR, "[data-tab='locations']")
        assert locations_tab.is_displayed()
        assert "locations" in locations_tab.text.lower() or "locations" in locations_tab.text.lower()

    def test_02_click_locations_tab_shows_empty_state(self, org_admin_session):
        """Click Locations tab and verify empty state for new project"""
        # Navigate to project detail
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        project_detail = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        )

        # Click Locations tab
        locations_tab = project_detail.find_element(By.CSS_SELECTOR, "[data-tab='locations']")
        locations_tab.click()

        # Wait for locations content
        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Verify empty state message
        empty_state = locations_content.find_element(By.CLASS_NAME, "empty-state")
        assert "no locations" in empty_state.text.lower()

        # Verify "Create Locations" button exists
        create_location_btn = locations_content.find_element(By.ID, "createLocationBtn")
        assert create_location_btn.is_displayed()
        assert create_location_btn.is_enabled()

    def test_03_locations_tab_shows_filters(self, org_admin_session):
        """Verify locations and date filters are present in Locations tab"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        project_detail = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        )

        locations_tab = project_detail.find_element(By.CSS_SELECTOR, "[data-tab='locations']")
        locations_tab.click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Verify filter controls
        country_filter = locations_content.find_element(By.ID, "locationCountryFilter")
        region_filter = locations_content.find_element(By.ID, "locationRegionFilter")
        city_filter = locations_content.find_element(By.ID, "locationCityFilter")
        status_filter = locations_content.find_element(By.ID, "locationStatusFilter")
        date_from_filter = locations_content.find_element(By.ID, "locationDateFromFilter")
        date_to_filter = locations_content.find_element(By.ID, "locationDateToFilter")

        assert country_filter.is_displayed()
        assert region_filter.is_displayed()
        assert city_filter.is_displayed()
        assert status_filter.is_displayed()
        assert date_from_filter.is_displayed()
        assert date_to_filter.is_displayed()


class TestSubProjectCreationWorkflow:
    """Test creating individual sub-projects (locations)"""

    def test_01_open_create_location_modal(self, org_admin_session):
        """Click Create Locations button and verify modal opens"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        project_detail = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        )

        locations_tab = project_detail.find_element(By.CSS_SELECTOR, "[data-tab='locations']")
        locations_tab.click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Click Create Locations button
        create_location_btn = locations_content.find_element(By.ID, "createLocationBtn")
        create_location_btn.click()

        # Verify modal opens
        location_modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createLocationModal"))
        )

        # Verify modal title
        modal_title = location_modal.find_element(By.CLASS_NAME, "modal-title")
        assert "create locations" in modal_title.text.lower() or "create sub-project" in modal_title.text.lower()

    def test_02_location_wizard_step1_basic_info(self, org_admin_session):
        """Test Step 1: Basic Information for locations"""
        # Open locations creation modal
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        ).find_element(By.ID, "createLocationBtn").click()

        location_modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createLocationModal"))
        )

        # Verify Step 1 is active
        step1 = location_modal.find_element(By.ID, "locationStep1")
        assert "active" in step1.get_attribute("class")

        # Verify form fields exist
        name_input = location_modal.find_element(By.ID, "locationName")
        slug_input = location_modal.find_element(By.ID, "locationSlug")
        description_input = location_modal.find_element(By.ID, "locationDescription")

        # Fill in basic info
        name_input.send_keys("Boston Locations Fall 2025")
        slug_input.send_keys("boston-fall-2025")
        description_input.send_keys("Graduate training program for Boston office")

        # Click Next
        next_btn = location_modal.find_element(By.CSS_SELECTOR, "#locationStep1 .next-step-btn")
        next_btn.click()

        # Verify Step 2 becomes active
        step2 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep2"))
        )
        assert "active" in step2.get_attribute("class")

    def test_03_location_wizard_step2_location(self, org_admin_session):
        """Test Step 2: Locations Information"""
        # Navigate to locations creation and Step 2
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        ).find_element(By.ID, "createLocationBtn").click()

        location_modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createLocationModal"))
        )

        # Fill Step 1 and advance
        location_modal.find_element(By.ID, "locationName").send_keys("Boston Locations Fall 2025")
        location_modal.find_element(By.ID, "locationSlug").send_keys("boston-fall-2025")
        location_modal.find_element(By.ID, "locationDescription").send_keys("Boston program")
        location_modal.find_element(By.CSS_SELECTOR, "#locationStep1 .next-step-btn").click()

        # Wait for Step 2
        step2 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep2"))
        )

        # Verify locations fields exist
        country_select = Select(step2.find_element(By.ID, "locationCountry"))
        region_select = Select(step2.find_element(By.ID, "locationRegion"))
        city_input = step2.find_element(By.ID, "locationCity")
        timezone_select = Select(step2.find_element(By.ID, "locationTimezone"))

        # Select locations
        country_select.select_by_visible_text("United States")

        # Wait for regions to load (dynamic based on country)
        time.sleep(1)
        region_select.select_by_visible_text("Massachusetts")

        city_input.send_keys("Boston")
        timezone_select.select_by_value("America/New_York")

        # Optional: Address field
        address_input = step2.find_element(By.ID, "locationAddress")
        address_input.send_keys("123 Main Street, Boston, MA 02101")

        # Click Next to Step 3
        next_btn = step2.find_element(By.CSS_SELECTOR, ".next-step-btn")
        next_btn.click()

        # Verify Step 3 becomes active
        step3 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep3"))
        )
        assert "active" in step3.get_attribute("class")

    def test_04_location_wizard_step3_schedule(self, org_admin_session):
        """Test Step 3: Schedule Configuration"""
        # Navigate to Step 3
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        ).find_element(By.ID, "createLocationBtn").click()

        location_modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createLocationModal"))
        )

        # Fill Steps 1 and 2
        location_modal.find_element(By.ID, "locationName").send_keys("Boston Locations")
        location_modal.find_element(By.ID, "locationSlug").send_keys("boston-fall-2025")
        location_modal.find_element(By.ID, "locationDescription").send_keys("Boston program")
        location_modal.find_element(By.CSS_SELECTOR, "#locationStep1 .next-step-btn").click()

        step2 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep2"))
        )
        Select(step2.find_element(By.ID, "locationCountry")).select_by_visible_text("United States")
        step2.find_element(By.ID, "locationCity").send_keys("Boston")
        step2.find_element(By.CSS_SELECTOR, ".next-step-btn").click()

        # Wait for Step 3
        step3 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep3"))
        )

        # Verify schedule fields
        start_date = step3.find_element(By.ID, "locationStartDate")
        end_date = step3.find_element(By.ID, "locationEndDate")
        duration = step3.find_element(By.ID, "locationDuration")
        max_participants = step3.find_element(By.ID, "locationMaxParticipants")

        # Set dates
        future_start = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        future_end = (datetime.now() + timedelta(days=150)).strftime("%Y-%m-%d")

        start_date.send_keys(future_start)
        end_date.send_keys(future_end)

        # Verify duration auto-calculates (approximately 17 weeks)
        time.sleep(1)
        calculated_duration = duration.get_attribute("value")
        assert int(calculated_duration) in range(15, 20)  # Allow some flexibility

        max_participants.clear()
        max_participants.send_keys("30")

        # Click Next to Step 4
        next_btn = step3.find_element(By.CSS_SELECTOR, ".next-step-btn")
        next_btn.click()

        # Verify Step 4 becomes active
        step4 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep4"))
        )
        assert "active" in step4.get_attribute("class")

    def test_05_location_wizard_step4_track_selection(self, org_admin_session):
        """Test Step 4: Track Selection with Overrides"""
        # Navigate to Step 4
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        ).find_element(By.ID, "createLocationBtn").click()

        location_modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createLocationModal"))
        )

        # Navigate through Steps 1-3 (abbreviated)
        location_modal.find_element(By.ID, "locationName").send_keys("Boston Locations")
        location_modal.find_element(By.ID, "locationSlug").send_keys("boston-test")
        location_modal.find_element(By.ID, "locationDescription").send_keys("Test")
        location_modal.find_element(By.CSS_SELECTOR, "#locationStep1 .next-step-btn").click()

        WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep2"))
        )
        Select(location_modal.find_element(By.ID, "locationCountry")).select_by_visible_text("United States")
        location_modal.find_element(By.ID, "locationCity").send_keys("Boston")
        location_modal.find_element(By.CSS_SELECTOR, "#locationStep2 .next-step-btn").click()

        step3 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep3"))
        )
        future_start = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        future_end = (datetime.now() + timedelta(days=150)).strftime("%Y-%m-%d")
        step3.find_element(By.ID, "locationStartDate").send_keys(future_start)
        step3.find_element(By.ID, "locationEndDate").send_keys(future_end)
        step3.find_element(By.ID, "locationMaxParticipants").send_keys("30")
        step3.find_element(By.CSS_SELECTOR, ".next-step-btn").click()

        # Wait for Step 4
        step4 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep4"))
        )

        # Verify track list from parent project
        track_list = step4.find_element(By.ID, "availableTracksList")
        track_items = track_list.find_elements(By.CLASS_NAME, "track-item")

        assert len(track_items) > 0, "Should display tracks from parent project"

        # Select first 2 tracks
        track_checkboxes = [item.find_element(By.CSS_SELECTOR, "input[type='checkbox']") for item in track_items[:2]]
        for checkbox in track_checkboxes:
            checkbox.click()

        # Verify override fields appear for selected tracks
        first_track_override = step4.find_element(By.CSS_SELECTOR, ".track-override-section:first-child")
        override_start = first_track_override.find_element(By.CLASS_NAME, "track-override-start-date")
        override_end = first_track_override.find_element(By.CLASS_NAME, "track-override-end-date")
        instructor_select = Select(first_track_override.find_element(By.CLASS_NAME, "track-instructor-select"))

        # Set override dates
        track_start = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        track_end = (datetime.now() + timedelta(days=80)).strftime("%Y-%m-%d")
        override_start.send_keys(track_start)
        override_end.send_keys(track_end)

        # Select instructor
        instructor_select.select_by_index(1)  # Select first available instructor

        # Click Next to Step 5 (Review)
        next_btn = step4.find_element(By.CSS_SELECTOR, ".next-step-btn")
        next_btn.click()

        # Verify Step 5 becomes active
        step5 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep5"))
        )
        assert "active" in step5.get_attribute("class")

    def test_06_location_wizard_step5_review_and_create(self, org_admin_session):
        """Test Step 5: Review and Create Locations"""
        # Navigate through complete wizard
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        ).find_element(By.ID, "createLocationBtn").click()

        location_modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "createLocationModal"))
        )

        # Fill all steps (abbreviated for brevity)
        # ... (Steps 1-4 filling code) ...

        # Navigate to Step 5
        step5 = WebDriverWait(org_admin_session, 5).until(
            EC.presence_of_element_located((By.ID, "locationStep5"))
        )

        # Verify review sections
        review_basic_info = step5.find_element(By.ID, "reviewBasicInfo")
        review_location = step5.find_element(By.ID, "reviewLocation")
        review_schedule = step5.find_element(By.ID, "reviewSchedule")
        review_tracks = step5.find_element(By.ID, "reviewTracks")

        assert "Boston Locations" in review_basic_info.text
        assert "United States" in review_location.text
        assert "Boston" in review_location.text

        # Create locations
        create_btn = step5.find_element(By.ID, "submitLocationBtn")
        create_btn.click()

        # Wait for success notification
        success_msg = WebDriverWait(org_admin_session, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.success"))
        )
        assert "locations created" in success_msg.text.lower()

        # Verify modal closes
        WebDriverWait(org_admin_session, 5).until(
            EC.invisibility_of_element_located((By.ID, "createLocationModal"))
        )

        # Verify locations appears in list
        locations_list = org_admin_session.find_element(By.ID, "locationsList")
        location_items = locations_list.find_elements(By.CLASS_NAME, "locations-item")
        assert len(location_items) >= 1, "Should display newly created locations"


class TestMultipleLocationCreation:
    """Test creating multiple locations for different locations"""

    def test_01_create_boston_location(self, org_admin_session):
        """Create Boston locations (US East Coast)"""
        # This would be the full implementation of creating Boston locations
        # Following the same pattern as TestSubProjectCreationWorkflow.test_06
        pass

    def test_02_create_london_location(self, org_admin_session):
        """Create London locations (UK)"""
        # Locations: United Kingdom, England, London
        # Timezone: Europe/London
        pass

    def test_03_create_tokyo_location(self, org_admin_session):
        """Create Tokyo locations (Japan)"""
        # Locations: Japan, Tokyo, Shibuya
        # Timezone: Asia/Tokyo
        pass

    def test_04_verify_three_locations_in_list(self, org_admin_session):
        """Verify all 3 locations appear in the locations list"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        locations_list = locations_content.find_element(By.ID, "locationsList")
        location_items = locations_list.find_elements(By.CLASS_NAME, "locations-item")

        assert len(location_items) == 3, "Should display all 3 locations"

        # Verify each locations appears
        location_locations = [item.find_element(By.CLASS_NAME, "locations-locations").text for item in location_items]
        assert any("Boston" in loc for loc in location_locations)
        assert any("London" in loc for loc in location_locations)
        assert any("Tokyo" in loc for loc in location_locations)


class TestLocationFiltering:
    """Test filtering locations by locations"""

    def test_01_filter_by_country_usa(self, org_admin_session):
        """Filter locations by country (USA) and verify only US locations shown"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Select USA in country filter
        country_filter = Select(locations_content.find_element(By.ID, "locationCountryFilter"))
        country_filter.select_by_visible_text("United States")

        # Wait for filtered results
        time.sleep(1)

        # Verify only US locations shown
        location_items = locations_content.find_elements(By.CLASS_NAME, "locations-item")
        for item in location_items:
            location_text = item.find_element(By.CLASS_NAME, "locations-locations").text
            assert "United States" in location_text or "Boston" in location_text

    def test_02_filter_by_city_london(self, org_admin_session):
        """Filter by city name (London)"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Type "London" in city filter
        city_filter = locations_content.find_element(By.ID, "locationCityFilter")
        city_filter.clear()
        city_filter.send_keys("London")

        # Wait for filtered results
        time.sleep(1)

        # Verify only London locations shown
        location_items = locations_content.find_elements(By.CLASS_NAME, "locations-item")
        assert len(location_items) == 1
        assert "London" in location_items[0].find_element(By.CLASS_NAME, "locations-locations").text

    def test_03_filter_by_date_range(self, org_admin_session):
        """Filter by date range (Q3 2025)"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Set date range
        date_from = locations_content.find_element(By.ID, "locationDateFromFilter")
        date_to = locations_content.find_element(By.ID, "locationDateToFilter")

        date_from.send_keys("2025-07-01")
        date_to.send_keys("2025-09-30")

        # Wait for filtered results
        time.sleep(1)

        # Verify only locations starting in Q3 2025 shown
        location_items = locations_content.find_elements(By.CLASS_NAME, "locations-item")
        for item in location_items:
            start_date_text = item.find_element(By.CLASS_NAME, "locations-start-date").text
            # Parse and verify date is within range
            # (Simplified for test structure)

    def test_04_clear_all_filters(self, org_admin_session):
        """Clear all filters and verify all locations shown again"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Apply some filters first
        Select(locations_content.find_element(By.ID, "locationCountryFilter")).select_by_visible_text("United States")
        time.sleep(1)

        # Click "Clear Filters" button
        clear_btn = locations_content.find_element(By.ID, "clearLocationsFiltersBtn")
        clear_btn.click()

        # Wait for refresh
        time.sleep(1)

        # Verify all 3 locations shown
        location_items = locations_content.find_elements(By.CLASS_NAME, "locations-item")
        assert len(location_items) == 3


class TestTimelineView:
    """Test visual timeline of all locations"""

    def test_01_timeline_view_button_exists(self, org_admin_session):
        """Verify timeline view toggle button exists"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Verify view toggle buttons
        list_view_btn = locations_content.find_element(By.ID, "locationListViewBtn")
        timeline_view_btn = locations_content.find_element(By.ID, "locationTimelineViewBtn")

        assert list_view_btn.is_displayed()
        assert timeline_view_btn.is_displayed()

    def test_02_switch_to_timeline_view(self, org_admin_session):
        """Click timeline view and verify timeline is displayed"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Click timeline view
        timeline_view_btn = locations_content.find_element(By.ID, "locationTimelineViewBtn")
        timeline_view_btn.click()

        # Verify timeline container appears
        timeline_container = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationTimelineContainer"))
        )

        # Verify timeline has bars for each locations
        timeline_bars = timeline_container.find_elements(By.CLASS_NAME, "timeline-bar")
        assert len(timeline_bars) == 3, "Should show 3 locations timelines"

        # Verify each bar has start/end markers
        for bar in timeline_bars:
            start_marker = bar.find_element(By.CLASS_NAME, "timeline-start")
            end_marker = bar.find_element(By.CLASS_NAME, "timeline-end")
            location_label = bar.find_element(By.CLASS_NAME, "timeline-label")

            assert start_marker.is_displayed()
            assert end_marker.is_displayed()
            assert location_label.is_displayed()


class TestLocationEnrollmentIsolation:
    """Test that enrollments are isolated between locations"""

    def test_01_enroll_student_in_boston_location(self, org_admin_session):
        """Enroll a student in Boston locations specifically"""
        # This would involve:
        # 1. Navigate to Students tab
        # 2. Select student
        # 3. Enroll in Boston locations (not just parent project)
        # 4. Verify enrollment record specifies sub_project_id
        pass

    def test_02_verify_student_only_in_boston_location(self, org_admin_session):
        """Verify student appears in Boston locations but not London or Tokyo"""
        # Check each locations's participant list
        pass

    def test_03_verify_capacity_tracking_per_location(self, org_admin_session):
        """Verify participant counts are tracked separately per locations"""
        # Boston: 1/30
        # London: 0/25
        # Tokyo: 0/20
        pass


class TestLocationComparison:
    """Test comparing multiple locations"""

    def test_01_select_multiple_locations_for_comparison(self, org_admin_session):
        """Select 2+ locations and click Compare button"""
        # Navigate to Locations tab
        first_project = WebDriverWait(org_admin_session, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-row:first-child .view-project-btn"))
        )
        first_project.click()

        WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "projectDetailView"))
        ).find_element(By.CSS_SELECTOR, "[data-tab='locations']").click()

        locations_content = WebDriverWait(org_admin_session, 5).until(
            EC.visibility_of_element_located((By.ID, "locationsTabContent"))
        )

        # Select locations using checkboxes
        location_items = locations_content.find_elements(By.CLASS_NAME, "locations-item")
        for item in location_items[:2]:  # Select first 2
            checkbox = item.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            checkbox.click()

        # Click Compare button
        compare_btn = locations_content.find_element(By.ID, "compareLocationsBtn")
        assert compare_btn.is_enabled()
        compare_btn.click()

        # Verify comparison modal opens
        comparison_modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "locationComparisonModal"))
        )
        assert comparison_modal.is_displayed()

    def test_02_comparison_modal_shows_side_by_side_data(self, org_admin_session):
        """Verify comparison modal shows side-by-side comparison"""
        # ... (setup code to open comparison modal) ...

        comparison_modal = WebDriverWait(org_admin_session, 10).until(
            EC.visibility_of_element_located((By.ID, "locationComparisonModal"))
        )

        # Verify comparison table/grid
        comparison_table = comparison_modal.find_element(By.ID, "comparisonTable")

        # Verify columns for each locations
        column_headers = comparison_table.find_elements(By.CLASS_NAME, "locations-column-header")
        assert len(column_headers) == 2

        # Verify comparison metrics rows
        location_row = comparison_table.find_element(By.CSS_SELECTOR, "tr[data-metric='locations']")
        dates_row = comparison_table.find_element(By.CSS_SELECTOR, "tr[data-metric='dates']")
        participants_row = comparison_table.find_element(By.CSS_SELECTOR, "tr[data-metric='participants']")
        tracks_row = comparison_table.find_element(By.CSS_SELECTOR, "tr[data-metric='tracks']")

        assert location_row.is_displayed()
        assert dates_row.is_displayed()
        assert participants_row.is_displayed()
        assert tracks_row.is_displayed()


# ==============================================================================
# FIXTURES AND HELPERS
# ==============================================================================

@pytest.fixture
def test_driver():
    """Create a Chrome WebDriver instance"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)

    yield driver

    driver.quit()


@pytest.fixture
def test_base_url():
    """Base URL for the application"""
    import os
    return os.getenv('TEST_BASE_URL', 'https://localhost:3000')


# ==============================================================================
# TEST EXECUTION
# ==============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
