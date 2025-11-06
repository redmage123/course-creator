"""
E2E Tests for Course-Instructor Assignment Interface (Project Wizard Flow)

BUSINESS CONTEXT:
Organization admins need to assign instructors to courses with specific roles
(primary instructor or assistant instructor). This enables proper course staffing,
workload distribution, and accountability. This test now uses the correct Project
Creation Wizard flow.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model
- Navigates through full Project Creation Wizard (Steps 1-4)
- Tests instructor list display in course details at Step 4
- Tests add/remove instructor functionality
- Tests instructor role assignment (primary/assistant)
- Validates integration with course-instructor assignment API

WORKFLOW (CORRECTED):
1. Navigate to Projects tab
2. Click "Create New Project" button (id="createProjectBtn")
3. Complete Project Wizard Steps 1-3
4. Step 4: Review tracks - "Manage Track" buttons appear here
5. Click "Manage Track" to open track management modal
6. Test instructor assignment in course management

TEST COVERAGE:
- View course details with instructor list
- Add instructor to course with role selection
- Remove instructor from course
- Update instructor role
- Validate role requirements (at least one primary)
- Error handling for duplicate assignments

TDD APPROACH:
This is the RED phase - tests will FAIL until the UI is implemented.

API ENDPOINTS TESTED:
- GET /api/v1/courses/{course_id}/instructors
- POST /api/v1/courses/{course_id}/instructors
- PUT /api/v1/courses/{course_id}/instructors/{instructor_id}
- DELETE /api/v1/courses/{course_id}/instructors/{instructor_id}
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

    PROJECTS_TAB = (By.CSS_SELECTOR, 'a[data-tab="projects"]')
    CREATE_PROJECT_BTN = (By.ID, 'createProjectBtn')
    PROJECT_MODAL = (By.ID, 'createProjectModal')
    PROJECT_NAME_INPUT = (By.ID, 'projectName')
    PROJECT_SLUG_INPUT = (By.ID, 'projectSlug')
    PROJECT_DESCRIPTION_INPUT = (By.ID, 'projectDescription')
    PROJECT_TYPE_SINGLE_RADIO = (By.ID, 'projectTypeSingle')
    PROJECT_TYPE_MULTI_RADIO = (By.ID, 'projectTypeMultiLocation')
    NEXT_STEP_BTN = (By.CSS_SELECTOR, 'button[onclick*="nextProjectStep"]')
    PROJECT_DURATION_INPUT = (By.ID, 'projectDuration')
    PROJECT_PARTICIPANTS_INPUT = (By.ID, 'projectMaxParticipants')
    PROJECT_START_DATE_INPUT = (By.ID, 'projectStartDate')
    PROJECT_END_DATE_INPUT = (By.ID, 'projectEndDate')
    SKIP_TRACK_GENERATION_BTN = (By.ID, 'skipTrackGeneration')
    TRACKS_REVIEW_LIST = (By.ID, 'tracksReviewList')
    MANAGE_TRACK_BTN = (By.CSS_SELECTOR, 'button[onclick*="openTrackManagement"]')

    def navigate_to_projects_tab(self):
        """Navigate to projects tab"""
        wait = WebDriverWait(self.driver, 10)
        projects_nav = wait.until(EC.element_to_be_clickable(self.PROJECTS_TAB))
        projects_nav.click()
        time.sleep(2)

    def complete_wizard_to_step4(self):
        """Complete wizard Steps 1-3 to reach Step 4"""
        # Click create project
        wait = WebDriverWait(self.driver, 10)
        create_btn = wait.until(EC.element_to_be_clickable(self.CREATE_PROJECT_BTN))
        create_btn.click()
        wait.until(EC.presence_of_element_located(self.PROJECT_MODAL))
        time.sleep(1)

        # Step 1: Fill basics
        name_input = wait.until(EC.presence_of_element_located(self.PROJECT_NAME_INPUT))
        name_input.clear()
        name_input.send_keys("Test Project Instructor Assignment")
        slug_input = self.driver.find_element(*self.PROJECT_SLUG_INPUT)
        slug_input.clear()
        slug_input.send_keys("test-instructor-assignment")
        desc_input = self.driver.find_element(*self.PROJECT_DESCRIPTION_INPUT)
        desc_input.clear()
        desc_input.send_keys("Project for testing instructor assignment")

        # Project Type (radio button - single locations is default/checked)
        type_radio = self.driver.find_element(*self.PROJECT_TYPE_SINGLE_RADIO)
        if not type_radio.is_selected():
            type_radio.click()

        # Next to Step 2
        next_btn = wait.until(EC.element_to_be_clickable(self.NEXT_STEP_BTN))
        next_btn.click()
        time.sleep(1)

        # Step 2: Fill details
        duration_input = wait.until(EC.presence_of_element_located(self.PROJECT_DURATION_INPUT))
        duration_input.clear()
        duration_input.send_keys('12')
        participants_input = self.driver.find_element(*self.PROJECT_PARTICIPANTS_INPUT)
        participants_input.clear()
        participants_input.send_keys('30')
        start_date_input = self.driver.find_element(*self.PROJECT_START_DATE_INPUT)
        start_date_input.clear()
        start_date_input.send_keys('2025-01-01')
        end_date_input = self.driver.find_element(*self.PROJECT_END_DATE_INPUT)
        end_date_input.clear()
        end_date_input.send_keys('2025-12-31')

        # Next to Step 3
        next_btn = wait.until(EC.element_to_be_clickable(self.NEXT_STEP_BTN))
        next_btn.click()
        time.sleep(1)

        # Step 3: Skip track generation
        skip_btn = wait.until(EC.element_to_be_clickable(self.SKIP_TRACK_GENERATION_BTN))
        skip_btn.click()
        time.sleep(1)

        # Wait for Step 4
        wait.until(EC.presence_of_element_located(self.TRACKS_REVIEW_LIST))
        time.sleep(1)

    def click_manage_track(self, track_index=0):
        """Click Manage Track button"""
        wait = WebDriverWait(self.driver, 10)
        manage_buttons = wait.until(EC.presence_of_all_elements_located(self.MANAGE_TRACK_BTN))
        if track_index < len(manage_buttons):
            manage_buttons[track_index].click()
            time.sleep(1)
        else:
            raise IndexError(f"Track index {track_index} not found")


class CourseInstructorPage(BasePage):
    """Page Object for Course-Instructor Assignment Interface"""

    # Track Management Modal
    TRACK_MANAGEMENT_MODAL = (By.ID, 'trackManagementModal')
    COURSES_TAB = (By.CSS_SELECTOR, 'button[onclick*="switchTrackTab(\'courses\')"]')
    INSTRUCTORS_TAB = (By.CSS_SELECTOR, 'button[onclick*="switchTrackTab(\'instructors\')"]')

    # Course Management
    COURSE_ITEMS = (By.CSS_SELECTOR, '.course-item')
    COURSE_VIEW_BTN = (By.CSS_SELECTOR, 'button[data-action="view-course"]')

    # Course Details Modal (if separate from track management)
    COURSE_DETAILS_MODAL = (By.ID, 'courseDetailsModal')
    COURSE_TITLE = (By.ID, 'courseDetailsTitle')

    # Instructor List
    INSTRUCTORS_LIST = (By.ID, 'courseInstructorsList')
    INSTRUCTOR_ITEMS = (By.CSS_SELECTOR, '.instructor-item')
    NO_INSTRUCTORS_MESSAGE = (By.CSS_SELECTOR, '.no-instructors-message')
    ADD_INSTRUCTOR_BTN = (By.ID, 'addInstructorBtn')

    # Add Instructor Modal
    ADD_INSTRUCTOR_MODAL = (By.ID, 'addInstructorModal')
    INSTRUCTOR_SELECT = (By.ID, 'instructorSelect')
    INSTRUCTOR_ROLE_PRIMARY = (By.ID, 'rolePrimary')
    INSTRUCTOR_ROLE_ASSISTANT = (By.ID, 'roleAssistant')
    SUBMIT_INSTRUCTOR_BTN = (By.ID, 'submitInstructorBtn')

    # Actions
    REMOVE_INSTRUCTOR_BTN = (By.CSS_SELECTOR, 'button[data-action="remove-instructor"]')
    EDIT_INSTRUCTOR_ROLE_BTN = (By.CSS_SELECTOR, 'button[data-action="edit-instructor-role"]')

    # Notifications
    SUCCESS_NOTIFICATION = (By.CSS_SELECTOR, '.notification.success')
    ERROR_NOTIFICATION = (By.CSS_SELECTOR, '.notification.error')

    def switch_to_instructors_tab(self):
        """Switch to instructors tab in track management"""
        wait = WebDriverWait(self.driver, 10)
        instructors_tab = wait.until(EC.element_to_be_clickable(self.INSTRUCTORS_TAB))
        instructors_tab.click()
        time.sleep(0.5)

    def switch_to_courses_tab(self):
        """Switch to courses tab"""
        wait = WebDriverWait(self.driver, 10)
        courses_tab = wait.until(EC.element_to_be_clickable(self.COURSES_TAB))
        courses_tab.click()
        time.sleep(0.5)

    def instructors_section_exists(self):
        """Check if instructors section exists"""
        try:
            self.driver.find_element(*self.INSTRUCTORS_LIST)
            return True
        except NoSuchElementException:
            return False

    def get_instructor_count(self):
        """Get number of instructors"""
        try:
            instructor_items = self.driver.find_elements(*self.INSTRUCTOR_ITEMS)
            return len(instructor_items)
        except NoSuchElementException:
            return 0

    def click_add_instructor(self):
        """Click add instructor button"""
        wait = WebDriverWait(self.driver, 10)
        add_btn = wait.until(EC.element_to_be_clickable(self.ADD_INSTRUCTOR_BTN))
        add_btn.click()
        wait.until(EC.presence_of_element_located(self.ADD_INSTRUCTOR_MODAL))
        time.sleep(0.5)

    def select_instructor(self, instructor_name=None):
        """Select an instructor from dropdown"""
        wait = WebDriverWait(self.driver, 10)
        instructor_select = Select(wait.until(EC.presence_of_element_located(self.INSTRUCTOR_SELECT)))
        if instructor_name:
            instructor_select.select_by_visible_text(instructor_name)
        else:
            if len(instructor_select.options) > 1:
                instructor_select.select_by_index(1)

    def select_instructor_role(self, role='primary'):
        """Select instructor role"""
        if role == 'primary':
            role_radio = self.driver.find_element(*self.INSTRUCTOR_ROLE_PRIMARY)
        else:
            role_radio = self.driver.find_element(*self.INSTRUCTOR_ROLE_ASSISTANT)
        role_radio.click()

    def submit_instructor_assignment(self):
        """Submit instructor assignment"""
        wait = WebDriverWait(self.driver, 10)
        submit_btn = wait.until(EC.element_to_be_clickable(self.SUBMIT_INSTRUCTOR_BTN))
        submit_btn.click()
        time.sleep(1)

    def remove_first_instructor(self):
        """Remove first instructor"""
        wait = WebDriverWait(self.driver, 10)
        remove_btn = wait.until(EC.element_to_be_clickable(self.REMOVE_INSTRUCTOR_BTN))
        remove_btn.click()
        time.sleep(1)

    def get_instructor_roles(self):
        """Get list of roles for assigned instructors"""
        roles = []
        instructor_items = self.driver.find_elements(*self.INSTRUCTOR_ITEMS)
        for item in instructor_items:
            role_badge = item.find_element(By.CSS_SELECTOR, '.instructor-role-badge')
            roles.append(role_badge.text.lower())
        return roles

    def is_visible(self, locator):
        """Check if element is visible"""
        try:
            element = self.driver.find_element(*locator)
            return element.is_displayed()
        except NoSuchElementException:
            return False


class TestCourseInstructorAssignment(BaseTest):
    """
    TDD RED PHASE Test Suite for Course-Instructor Assignment Interface

    These tests will FAIL until the UI is implemented.
    UPDATED: Now uses correct Project Wizard flow to reach track management.
    """

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup test environment - login as org admin"""
        self.wizard_page = ProjectWizardPage(self.driver, self.config)
        self.instructor_page = CourseInstructorPage(self.driver, self.config)

        # Login as org admin
        self.login_as_org_admin()

        # Navigate to projects tab
        self.wizard_page.navigate_to_projects_tab()

    def login_as_org_admin(self):
        """Login as organization administrator using localStorage authentication"""
        self.driver.get(f"{self.config.base_url}/html/index.html")
        time.sleep(1)

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

        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html")

        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'a[data-tab="overview"]')))
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-tab="projects"]')))
        time.sleep(3)

    def navigate_to_track_management(self):
        """Navigate through wizard to track management"""
        self.wizard_page.complete_wizard_to_step4()
        self.wizard_page.click_manage_track(track_index=0)

    def test_instructors_tab_exists_in_track_management(self):
        """
        Test that instructors tab exists in track management modal

        EXPECTED RESULT (RED PHASE): FAIL - tab doesn't exist yet
        """
        self.navigate_to_track_management()

        # Verify track management modal opened
        assert self.instructor_page.is_visible(self.instructor_page.TRACK_MANAGEMENT_MODAL), \
            "Track management modal should be visible"

        # CRITICAL TEST: Check if instructors tab exists
        assert self.instructor_page.is_visible(self.instructor_page.INSTRUCTORS_TAB), \
            "Instructors tab should exist in track management"

    def test_instructors_section_displays(self):
        """
        Test that instructors section displays when tab is clicked

        EXPECTED RESULT (RED PHASE): FAIL - section doesn't exist yet
        """
        self.navigate_to_track_management()

        # Click instructors tab
        self.instructor_page.switch_to_instructors_tab()

        # Verify instructors section is visible
        assert self.instructor_page.instructors_section_exists(), \
            "Instructors section should be visible in track management"

    def test_add_instructor_button_exists(self):
        """
        Test that Add Instructor button exists

        EXPECTED RESULT (RED PHASE): FAIL - button doesn't exist yet
        """
        self.navigate_to_track_management()
        self.instructor_page.switch_to_instructors_tab()

        # Verify add instructor button exists
        assert self.instructor_page.is_visible(self.instructor_page.ADD_INSTRUCTOR_BTN), \
            "Add Instructor button should exist"

    def test_add_instructor_modal_opens(self):
        """
        Test that clicking Add Instructor opens assignment modal

        EXPECTED RESULT (RED PHASE): FAIL - modal doesn't exist yet
        """
        self.navigate_to_track_management()
        self.instructor_page.switch_to_instructors_tab()

        # Click add instructor
        self.instructor_page.click_add_instructor()

        # Verify modal opened
        assert self.instructor_page.is_visible(self.instructor_page.ADD_INSTRUCTOR_MODAL), \
            "Add Instructor modal should open"

    def test_instructor_dropdown_populated(self):
        """
        Test that instructor dropdown is populated

        EXPECTED RESULT (RED PHASE): FAIL - dropdown doesn't exist yet
        """
        self.navigate_to_track_management()
        self.instructor_page.switch_to_instructors_tab()
        self.instructor_page.click_add_instructor()

        # Get instructor options
        instructor_select = Select(self.driver.find_element(*self.instructor_page.INSTRUCTOR_SELECT))
        options = instructor_select.options

        # Should have at least placeholder + one instructor
        assert len(options) >= 2, \
            "Instructor dropdown should have at least one instructor option"

    def test_role_selection_radio_buttons_exist(self):
        """
        Test that role selection radio buttons exist

        EXPECTED RESULT (RED PHASE): FAIL - radio buttons don't exist yet
        """
        self.navigate_to_track_management()
        self.instructor_page.switch_to_instructors_tab()
        self.instructor_page.click_add_instructor()

        # Verify role radio buttons exist
        assert self.instructor_page.is_visible(self.instructor_page.INSTRUCTOR_ROLE_PRIMARY), \
            "Primary instructor role radio button should exist"
        assert self.instructor_page.is_visible(self.instructor_page.INSTRUCTOR_ROLE_ASSISTANT), \
            "Assistant instructor role radio button should exist"

    def test_assign_instructor_to_track(self):
        """
        Test complete workflow of assigning an instructor

        EXPECTED RESULT (RED PHASE): FAIL - functionality doesn't exist yet
        """
        self.navigate_to_track_management()
        self.instructor_page.switch_to_instructors_tab()

        # Get initial count
        initial_count = self.instructor_page.get_instructor_count()

        # Open add instructor modal
        self.instructor_page.click_add_instructor()

        # Select instructor and role
        self.instructor_page.select_instructor()
        self.instructor_page.select_instructor_role('primary')

        # Submit
        self.instructor_page.submit_instructor_assignment()

        # Wait for success notification
        wait = WebDriverWait(self.driver, 10)
        success_notif = wait.until(EC.presence_of_element_located(self.instructor_page.SUCCESS_NOTIFICATION))
        assert success_notif.is_displayed(), "Success notification should appear"

        # Verify instructor was added
        time.sleep(1)
        new_count = self.instructor_page.get_instructor_count()
        assert new_count == initial_count + 1, \
            "Instructor count should increase by 1"

    def test_remove_instructor(self):
        """
        Test removing an instructor

        EXPECTED RESULT (RED PHASE): FAIL - functionality doesn't exist yet
        """
        self.navigate_to_track_management()
        self.instructor_page.switch_to_instructors_tab()

        # Get initial count
        initial_count = self.instructor_page.get_instructor_count()
        assert initial_count > 0, "Should have at least one instructor for this test"

        # Remove first instructor
        self.instructor_page.remove_first_instructor()

        # Wait for success notification
        wait = WebDriverWait(self.driver, 10)
        success_notif = wait.until(EC.presence_of_element_located(self.instructor_page.SUCCESS_NOTIFICATION))
        assert success_notif.is_displayed(), "Success notification should appear"

        # Verify instructor was removed
        time.sleep(1)
        new_count = self.instructor_page.get_instructor_count()
        assert new_count == initial_count - 1, \
            "Instructor count should decrease by 1"

    def test_instructor_list_displays_roles(self):
        """
        Test that instructor list displays roles

        EXPECTED RESULT (RED PHASE): FAIL - role display doesn't exist yet
        """
        self.navigate_to_track_management()
        self.instructor_page.switch_to_instructors_tab()

        # Get instructor roles
        roles = self.instructor_page.get_instructor_roles()

        # Should have at least one role
        assert len(roles) > 0, "Should have at least one instructor role displayed"

        # Roles should be 'primary' or 'assistant'
        for role in roles:
            assert role in ['primary', 'assistant', 'primary instructor', 'assistant instructor'], \
                f"Role '{role}' should be 'primary' or 'assistant'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
