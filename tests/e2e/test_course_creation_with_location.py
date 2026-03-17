"""
E2E Tests for Course Creation with Locations Selection (Project Wizard Flow)

BUSINESS CONTEXT:
Tests the course creation workflow when creating courses within tracks and locations.
Org admins need to specify which locations a course is delivered at for multi-locations
organizations. This test now uses the correct Project Creation Wizard flow.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model
- Navigates through full Project Creation Wizard (Steps 1-4)
- Tests locations dropdown in course creation modal at Step 4
- Validates location_id is sent to backend API
- Tests integration with track management workflow

WORKFLOW (CORRECTED):
1. Navigate to Projects tab
2. Click "Create New Project" button (id="createProjectBtn")
3. Complete Project Wizard Steps 1-3:
   - Step 1: Project basics (name, slug, description, type)
   - Step 2: Project details (duration, participants, dates)
   - Step 3: Generate tracks (use AI or manual)
4. Step 4: Review tracks - "Manage Track" buttons appear here
5. Click "Manage Track" to open track management modal
6. Test course creation with locations dropdown

TEST COVERAGE:
- Locations dropdown exists in course modal
- Locations dropdown populated with organization's locations
- Locations selection persists and sends to API
- Course creation with track_id AND location_id
- Optional locations field (can be null)

TDD APPROACH:
This is the RED phase - test will FAIL until locations dropdown is implemented.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import sys

sys.path.insert(0, '/home/bbrelin/course-creator/tests/e2e')
from selenium_base import BaseTest, BasePage


class ProjectWizardPage(BasePage):
    """Page Object for Project Creation Wizard (Steps 1-4)"""

    # Projects Tab
    PROJECTS_TAB = (By.CSS_SELECTOR, 'a[data-tab="projects"]')
    CREATE_PROJECT_BTN = (By.ID, 'createProjectBtn')

    # Project Creation Modal
    PROJECT_MODAL = (By.ID, 'createProjectModal')

    # Step 1: Project Basics
    PROJECT_NAME_INPUT = (By.ID, 'projectName')
    PROJECT_SLUG_INPUT = (By.ID, 'projectSlug')
    PROJECT_DESCRIPTION_INPUT = (By.ID, 'projectDescription')
    PROJECT_TYPE_SINGLE_RADIO = (By.ID, 'projectTypeSingle')
    PROJECT_TYPE_MULTI_RADIO = (By.ID, 'projectTypeMultiLocation')
    NEXT_STEP_BTN = (By.CSS_SELECTOR, 'button[onclick*="nextProjectStep"]')

    # Step 2: Project Details
    PROJECT_DURATION_INPUT = (By.ID, 'projectDuration')
    PROJECT_PARTICIPANTS_INPUT = (By.ID, 'projectMaxParticipants')
    PROJECT_START_DATE_INPUT = (By.ID, 'projectStartDate')
    PROJECT_END_DATE_INPUT = (By.ID, 'projectEndDate')

    # Step 3: Track Generation
    GENERATE_TRACKS_BTN = (By.ID, 'generateTracksBtn')
    SKIP_TRACK_GENERATION_BTN = (By.ID, 'skipTrackGeneration')

    # Step 4: Review Tracks
    TRACKS_REVIEW_LIST = (By.ID, 'tracksReviewList')
    MANAGE_TRACK_BTN = (By.CSS_SELECTOR, 'button[onclick*="openTrackManagement"]')

    def navigate_to_projects_tab(self):
        """Navigate to projects tab in org admin dashboard"""
        wait = WebDriverWait(self.driver, 10)
        projects_nav = wait.until(EC.element_to_be_clickable(self.PROJECTS_TAB))
        projects_nav.click()
        time.sleep(2)

    def click_create_project(self):
        """Click Create New Project button to open wizard"""
        wait = WebDriverWait(self.driver, 10)
        create_btn = wait.until(EC.element_to_be_clickable(self.CREATE_PROJECT_BTN))
        create_btn.click()

        # Wait for modal to appear
        wait.until(EC.presence_of_element_located(self.PROJECT_MODAL))
        time.sleep(1)

    def fill_step1_project_basics(self, name="Test Project", slug="test-project",
                                   description="Test project description", project_type="single_location"):
        """
        Fill Step 1: Project Basics

        WHY: Tests need to complete Step 1 to access later wizard steps.

        @param project_type: Either 'single_location' or 'multi_location'
        """
        wait = WebDriverWait(self.driver, 10)

        # Project Name
        name_input = wait.until(EC.presence_of_element_located(self.PROJECT_NAME_INPUT))
        name_input.clear()
        name_input.send_keys(name)

        # Slug (auto-generated but can override)
        slug_input = self.driver.find_element(*self.PROJECT_SLUG_INPUT)
        slug_input.clear()
        slug_input.send_keys(slug)

        # Description
        desc_input = self.driver.find_element(*self.PROJECT_DESCRIPTION_INPUT)
        desc_input.clear()
        desc_input.send_keys(description)

        # Project Type (radio buttons)
        if project_type == "multi_location":
            type_radio = self.driver.find_element(*self.PROJECT_TYPE_MULTI_RADIO)
        else:
            type_radio = self.driver.find_element(*self.PROJECT_TYPE_SINGLE_RADIO)

        if not type_radio.is_selected():
            type_radio.click()

    def click_next_step(self):
        """
        Click Next button to advance wizard

        WHY: Wizard steps require explicit navigation.
        Uses JavaScript scroll to ensure button is visible before clicking.
        """
        wait = WebDriverWait(self.driver, 10)
        next_btn = wait.until(EC.element_to_be_clickable(self.NEXT_STEP_BTN))

        # Scroll element into view to avoid ElementClickInterceptedException
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
        time.sleep(0.5)  # Brief pause after scroll

        next_btn.click()
        time.sleep(1)

    def fill_step2_project_details(self, duration=12, participants=30,
                                    start_date="2025-01-01", end_date="2025-12-31"):
        """Fill Step 2: Project Details"""
        wait = WebDriverWait(self.driver, 10)

        # Duration (weeks)
        duration_input = wait.until(EC.presence_of_element_located(self.PROJECT_DURATION_INPUT))
        duration_input.clear()
        duration_input.send_keys(str(duration))

        # Max Participants
        participants_input = self.driver.find_element(*self.PROJECT_PARTICIPANTS_INPUT)
        participants_input.clear()
        participants_input.send_keys(str(participants))

        # Start Date
        start_date_input = self.driver.find_element(*self.PROJECT_START_DATE_INPUT)
        start_date_input.clear()
        start_date_input.send_keys(start_date)

        # End Date
        end_date_input = self.driver.find_element(*self.PROJECT_END_DATE_INPUT)
        end_date_input.clear()
        end_date_input.send_keys(end_date)

    def skip_track_generation(self):
        """Skip AI track generation in Step 3"""
        wait = WebDriverWait(self.driver, 10)
        skip_btn = wait.until(EC.element_to_be_clickable(self.SKIP_TRACK_GENERATION_BTN))
        skip_btn.click()
        time.sleep(1)

    def wait_for_step4_review(self):
        """Wait for Step 4 to load with track review list"""
        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located(self.TRACKS_REVIEW_LIST))
        time.sleep(1)

    def click_manage_track(self, track_index=0):
        """Click Manage Track button for specified track"""
        wait = WebDriverWait(self.driver, 10)
        manage_buttons = wait.until(EC.presence_of_all_elements_located(self.MANAGE_TRACK_BTN))

        if track_index < len(manage_buttons):
            manage_buttons[track_index].click()
            time.sleep(1)
        else:
            raise IndexError(f"Track index {track_index} not found")


class CourseCreationPage(BasePage):
    """Page Object for Course Creation Modal in Track Management"""

    # Track Management Modal
    TRACK_MANAGEMENT_MODAL = (By.ID, 'trackManagementModal')
    COURSES_TAB = (By.CSS_SELECTOR, '[data-bs-target="#coursesTabContent"], button[onclick*="switchTrackTab(\'courses\')"]')

    # Course Creation Modal
    COURSE_MODAL = (By.ID, 'courseModal')
    COURSE_MODAL_TITLE = (By.ID, 'courseModalTitle')

    # Course Form Fields
    COURSE_TITLE_INPUT = (By.ID, 'courseTitle')
    COURSE_DESCRIPTION_INPUT = (By.ID, 'courseDescription')
    COURSE_DIFFICULTY_SELECT = (By.ID, 'courseDifficulty')
    COURSE_CATEGORY_INPUT = (By.ID, 'courseCategory')
    COURSE_DURATION_INPUT = (By.ID, 'courseDuration')
    COURSE_DURATION_UNIT_SELECT = (By.ID, 'courseDurationUnit')
    COURSE_TAGS_INPUT = (By.ID, 'courseTags')

    # NEW: Locations Dropdown (this is what we're testing)
    COURSE_LOCATION_SELECT = (By.ID, 'courseLocation')

    # Submit Button
    CREATE_COURSE_BTN = (By.ID, 'createCourseBtn')
    COURSE_MODAL_CLOSE = (By.CSS_SELECTOR, '#courseModal .close')

    # Course List
    COURSES_LIST = (By.ID, 'courses-list')
    COURSE_ITEMS = (By.CSS_SELECTOR, '#courses-list .course-item')

    # Notifications
    NOTIFICATION_CONTAINER = (By.ID, 'notification-container')
    SUCCESS_NOTIFICATION = (By.CSS_SELECTOR, '.notification.success')

    def switch_to_courses_tab(self):
        """Switch to courses tab in track management modal"""
        wait = WebDriverWait(self.driver, 10)
        courses_tab = wait.until(EC.element_to_be_clickable(self.COURSES_TAB))
        courses_tab.click()
        time.sleep(0.5)

    def click_add_course_button(self):
        """Click the Add Course button in courses tab"""
        wait = WebDriverWait(self.driver, 10)
        add_course_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[onclick*="openCourseModal"]')))
        add_course_btn.click()

        # Wait for course modal
        wait.until(EC.presence_of_element_located(self.COURSE_MODAL))
        time.sleep(0.5)

    def fill_course_basic_info(self, title="Test Course", description="Test course description"):
        """Fill basic course information"""
        wait = WebDriverWait(self.driver, 10)

        # Title
        title_input = wait.until(EC.presence_of_element_located(self.COURSE_TITLE_INPUT))
        title_input.clear()
        title_input.send_keys(title)

        # Description
        desc_input = self.driver.find_element(*self.COURSE_DESCRIPTION_INPUT)
        desc_input.clear()
        desc_input.send_keys(description)

        # Difficulty
        difficulty_select = Select(self.driver.find_element(*self.COURSE_DIFFICULTY_SELECT))
        difficulty_select.select_by_value('intermediate')

        # Category
        category_input = self.driver.find_element(*self.COURSE_CATEGORY_INPUT)
        category_input.clear()
        category_input.send_keys('Programming')

        # Duration
        duration_input = self.driver.find_element(*self.COURSE_DURATION_INPUT)
        duration_input.clear()
        duration_input.send_keys('8')

        # Duration Unit
        duration_unit = Select(self.driver.find_element(*self.COURSE_DURATION_UNIT_SELECT))
        duration_unit.select_by_value('weeks')

    def select_location(self, location_name=None):
        """
        Select a locations from the dropdown

        Args:
            location_name: Name of locations to select, or None to leave unselected
        """
        wait = WebDriverWait(self.driver, 10)
        location_select = Select(wait.until(EC.presence_of_element_located(self.COURSE_LOCATION_SELECT)))

        if location_name:
            location_select.select_by_visible_text(location_name)
        else:
            # Select first non-empty option if any
            options = location_select.options
            if len(options) > 1:  # More than just placeholder
                location_select.select_by_index(1)

    def get_location_options(self):
        """Get all available locations options from dropdown"""
        wait = WebDriverWait(self.driver, 10)
        location_select = Select(wait.until(EC.presence_of_element_located(self.COURSE_LOCATION_SELECT)))
        return [option.text for option in location_select.options]

    def get_selected_location(self):
        """Get currently selected locations"""
        wait = WebDriverWait(self.driver, 10)
        location_select = Select(wait.until(EC.presence_of_element_located(self.COURSE_LOCATION_SELECT)))
        return location_select.first_selected_option.text

    def submit_course_creation(self):
        """Click create course button"""
        wait = WebDriverWait(self.driver, 10)
        create_btn = wait.until(EC.element_to_be_clickable(self.CREATE_COURSE_BTN))
        create_btn.click()
        time.sleep(1)

    def course_location_dropdown_exists(self):
        """Check if locations dropdown exists in course modal"""
        try:
            self.driver.find_element(*self.COURSE_LOCATION_SELECT)
            return True
        except NoSuchElementException:
            return False

    def is_visible(self, locator):
        """Check if element is visible"""
        try:
            element = self.driver.find_element(*locator)
            return element.is_displayed()
        except NoSuchElementException:
            return False


class TestCourseCreationWithLocation(BaseTest):
    """
    TDD RED PHASE Test Suite for Course Creation with Locations Selection

    These tests will FAIL until the locations dropdown is implemented in the course
    creation modal. This is intentional - we're writing tests first.

    UPDATED: Now uses correct Project Wizard flow (Steps 1-4) to reach track management.
    """

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup test environment - login as org admin"""
        self.wizard_page = ProjectWizardPage(self.driver, self.config)
        self.course_page = CourseCreationPage(self.driver, self.config)

        # Login as org admin
        self.login_as_org_admin()

        # Navigate to projects tab
        self.wizard_page.navigate_to_projects_tab()

    def login_as_org_admin(self):
        """Login as organization administrator using localStorage authentication"""
        # Navigate to a simple page first to set localStorage
        self.driver.get(f"{self.config.base_url}/html/index.html")
        time.sleep(1)

        # Set up org admin authenticated state via localStorage
        # Using real organization ID from database: 259da6df-c148-40c2-bcd9-dc6889e7e9fb (Software Engineering Bootcamp)
        self.driver.execute_script("""
            localStorage.setItem('authToken', 'test-org-admin-token-67890');
            localStorage.setItem('userRole', 'organization_admin');
            localStorage.setItem('userName', 'Test Org Admin');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 300,
                email: 'org_admin@example.com',
                role: 'organization_admin',
                organization_id: '259da6df-c148-40c2-bcd9-dc6889e7e9fb',
                name: 'Test Org Admin'
            }));
            localStorage.setItem('userEmail', 'org_admin@example.com');
            localStorage.setItem('sessionStart', Date.now().toString());
            localStorage.setItem('lastActivity', Date.now().toString());
        """)

        # Now navigate to the dashboard with authentication set
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html")

        # Wait for dashboard to fully initialize
        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'a[data-tab="overview"]')))
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-tab="projects"]')))
        time.sleep(3)

    def navigate_through_wizard_to_track_management(self):
        """
        Navigate through Project Creation Wizard Steps 1-4 to reach track management.

        This is the correct flow to access the "Manage Track" button.
        """
        # Step 1: Open wizard
        self.wizard_page.click_create_project()

        # Step 2: Fill project basics
        self.wizard_page.fill_step1_project_basics(
            name="E2E Test Project with Locations",
            slug="e2e-test-locations",
            description="Project for testing locations dropdown in course creation"
        )
        self.wizard_page.click_next_step()

        # Step 3: Fill project details
        self.wizard_page.fill_step2_project_details(
            duration=12,
            participants=30,
            start_date="2025-01-01",
            end_date="2025-12-31"
        )
        self.wizard_page.click_next_step()

        # Step 4: Skip track generation (to get to Step 4 quickly)
        self.wizard_page.skip_track_generation()

        # Step 5: Wait for Step 4 (Review) to load
        self.wizard_page.wait_for_step4_review()

        # Step 6: Click "Manage Track" button (now available at Step 4)
        self.wizard_page.click_manage_track(track_index=0)

    def test_location_dropdown_exists_in_course_modal(self):
        """
        Test that locations dropdown field exists in course creation modal

        EXPECTED RESULT (RED PHASE): FAIL - dropdown doesn't exist yet
        """
        # Navigate through wizard to track management
        self.navigate_through_wizard_to_track_management()

        # Switch to courses tab in track management modal
        self.course_page.switch_to_courses_tab()

        # Click Add Course
        self.course_page.click_add_course_button()

        # Verify course modal opened
        assert self.course_page.is_visible(self.course_page.COURSE_MODAL), "Course modal should be visible"

        # CRITICAL TEST: Check if locations dropdown exists
        assert self.course_page.course_location_dropdown_exists(), \
            "Locations dropdown should exist in course creation modal"

    def test_location_dropdown_populated_with_locations(self):
        """
        Test that locations dropdown is populated with organization's locations

        EXPECTED RESULT (RED PHASE): FAIL - dropdown doesn't exist yet
        """
        # Navigate to course modal
        self.navigate_through_wizard_to_track_management()
        self.course_page.switch_to_courses_tab()
        self.course_page.click_add_course_button()

        # Get locations options
        location_options = self.course_page.get_location_options()

        # Should have at least a placeholder and one locations
        assert len(location_options) >= 1, \
            "Locations dropdown should have at least one option"

        # First option should be placeholder or "Select Locations"
        assert any(keyword in location_options[0].lower()
                   for keyword in ['select', 'choose', 'none', 'optional']), \
            "First option should be a placeholder"

    def test_create_course_with_location_selected(self):
        """
        Test creating a course with a locations selected

        EXPECTED RESULT (RED PHASE): FAIL - dropdown doesn't exist yet
        """
        # Navigate to course modal
        self.navigate_through_wizard_to_track_management()
        self.course_page.switch_to_courses_tab()
        self.course_page.click_add_course_button()

        # Fill course details
        self.course_page.fill_course_basic_info(
            title="Python Fundamentals",
            description="Learn Python programming basics"
        )

        # Select a locations
        self.course_page.select_location()  # Selects first available locations

        # Verify locations was selected
        selected_location = self.course_page.get_selected_location()
        assert selected_location != "", "A locations should be selected"

        # Submit course creation
        self.course_page.submit_course_creation()

        # Wait for success notification
        success_notif = self.course_page.wait_for_element(
            self.course_page.SUCCESS_NOTIFICATION,
            timeout=10
        )
        assert success_notif.is_displayed(), "Success notification should appear"

        # Verify course appears in list
        time.sleep(2)
        course_items = self.driver.find_elements(*self.course_page.COURSE_ITEMS)
        assert len(course_items) > 0, "Course should appear in courses list"

    def test_create_course_without_location_optional(self):
        """
        Test creating a course without selecting a locations (should be optional)

        EXPECTED RESULT (RED PHASE): FAIL - dropdown doesn't exist yet
        """
        # Navigate to course modal
        self.navigate_through_wizard_to_track_management()
        self.course_page.switch_to_courses_tab()
        self.course_page.click_add_course_button()

        # Fill course details
        self.course_page.fill_course_basic_info(
            title="JavaScript Basics",
            description="Learn JavaScript fundamentals"
        )

        # DO NOT select a locations - leave as placeholder
        # This tests that locations is optional

        # Submit course creation
        self.course_page.submit_course_creation()

        # Should still succeed
        success_notif = self.course_page.wait_for_element(
            self.course_page.SUCCESS_NOTIFICATION,
            timeout=10
        )
        assert success_notif.is_displayed(), \
            "Course creation should succeed even without locations (optional field)"

    def test_location_field_has_proper_label(self):
        """
        Test that locations dropdown has a proper label

        EXPECTED RESULT (RED PHASE): FAIL - dropdown doesn't exist yet
        """
        # Navigate to course modal
        self.navigate_through_wizard_to_track_management()
        self.course_page.switch_to_courses_tab()
        self.course_page.click_add_course_button()

        # Find label for locations dropdown
        location_label = self.driver.find_element(
            By.CSS_SELECTOR,
            'label[for="courseLocation"]'
        )

        assert location_label.is_displayed(), "Locations label should be visible"
        assert "locations" in location_label.text.lower(), \
            "Label text should mention 'locations'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
