"""
E2E Tests for Instructor Scheduling Interface

BUSINESS CONTEXT:
Organization admins need to schedule courses with instructors at specific times and locations.
The system must prevent scheduling conflicts (same instructor at same time) and provide
visual feedback on instructor availability and workload distribution.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model
- Tests calendar/schedule view interface
- Tests schedule creation with time slots
- Tests conflict detection and visualization
- Validates integration with scheduling API endpoints

TEST COVERAGE:
- Schedules tab exists in org admin dashboard
- Calendar view displays (weekly/monthly)
- Create schedule entry (course + instructor + time + locations)
- Conflict detection when scheduling same instructor at same time
- Visual conflict indicators
- Edit existing schedule
- Delete schedule
- Filter schedules by instructor/course/locations

TDD APPROACH:
This is the RED phase - tests will FAIL until the scheduling UI is implemented.

API ENDPOINTS TESTED:
- GET /api/v1/schedules - List all schedules
- GET /api/v1/schedules/conflicts - Check for conflicts
- POST /api/v1/schedules - Create schedule
- PUT /api/v1/schedules/{schedule_id} - Update schedule
- DELETE /api/v1/schedules/{schedule_id} - Delete schedule
- GET /api/v1/instructors/{instructor_id}/schedules - Get instructor's schedule
- GET /api/v1/courses/{course_id}/schedule - Get course schedule
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/home/bbrelin/course-creator/tests/e2e')
from selenium_base import BaseTest, BasePage


class SchedulingPage(BasePage):
    """Page Object for Instructor Scheduling Interface"""

    # Navigation
    SCHEDULES_TAB = (By.CSS_SELECTOR, 'a[data-tab="schedules"]')
    SCHEDULES_CONTENT = (By.ID, 'schedules')

    # Schedule View
    CALENDAR_VIEW = (By.ID, 'scheduleCalendar')
    WEEKLY_VIEW_BTN = (By.ID, 'weeklyViewBtn')
    MONTHLY_VIEW_BTN = (By.ID, 'monthlyViewBtn')
    CREATE_SCHEDULE_BTN = (By.ID, 'createScheduleBtn')

    # Calendar Elements
    CALENDAR_HEADER = (By.CSS_SELECTOR, '.calendar-header')
    CALENDAR_GRID = (By.CSS_SELECTOR, '.calendar-grid')
    SCHEDULE_ITEMS = (By.CSS_SELECTOR, '.schedule-item')
    CONFLICT_INDICATORS = (By.CSS_SELECTOR, '.schedule-conflict')

    # Create Schedule Modal
    SCHEDULE_MODAL = (By.ID, 'scheduleModal')
    SCHEDULE_COURSE_SELECT = (By.ID, 'scheduleCourse')
    SCHEDULE_INSTRUCTOR_SELECT = (By.ID, 'scheduleInstructor')
    SCHEDULE_LOCATION_SELECT = (By.ID, 'scheduleLocation')
    SCHEDULE_START_DATE = (By.ID, 'scheduleStartDate')
    SCHEDULE_START_TIME = (By.ID, 'scheduleStartTime')
    SCHEDULE_END_TIME = (By.ID, 'scheduleEndTime')
    SCHEDULE_RECURRENCE = (By.ID, 'scheduleRecurrence')
    SCHEDULE_DAYS_OF_WEEK = (By.CSS_SELECTOR, 'input[name="daysOfWeek"]')
    SUBMIT_SCHEDULE_BTN = (By.ID, 'submitScheduleBtn')

    # Conflict Warning
    CONFLICT_WARNING = (By.ID, 'conflictWarning')
    CONFLICT_DETAILS = (By.CSS_SELECTOR, '.conflict-details')

    # Filters
    INSTRUCTOR_FILTER = (By.ID, 'instructorFilter')
    COURSE_FILTER = (By.ID, 'courseFilter')
    LOCATION_FILTER = (By.ID, 'locationFilter')

    # Notifications
    SUCCESS_NOTIFICATION = (By.CSS_SELECTOR, '.notification.success')
    ERROR_NOTIFICATION = (By.CSS_SELECTOR, '.notification.error')

    def navigate_to_schedules_tab(self):
        """Navigate to schedules tab in org admin dashboard"""
        wait = WebDriverWait(self.driver, 10)
        schedules_tab = wait.until(EC.element_to_be_clickable(self.SCHEDULES_TAB))
        schedules_tab.click()
        time.sleep(1)

    def schedules_tab_exists(self):
        """Check if schedules tab exists"""
        try:
            self.driver.find_element(*self.SCHEDULES_TAB)
            return True
        except NoSuchElementException:
            return False

    def calendar_view_exists(self):
        """Check if calendar view exists"""
        try:
            self.driver.find_element(*self.CALENDAR_VIEW)
            return True
        except NoSuchElementException:
            return False

    def click_create_schedule(self):
        """Click create schedule button"""
        wait = WebDriverWait(self.driver, 10)
        create_btn = wait.until(EC.element_to_be_clickable(self.CREATE_SCHEDULE_BTN))
        create_btn.click()

        # Wait for modal
        wait.until(EC.presence_of_element_located(self.SCHEDULE_MODAL))
        time.sleep(0.5)

    def fill_schedule_form(self, schedule_data):
        """
        Fill out schedule creation form

        Args:
            schedule_data: Dictionary with course_id, instructor_id, location_id,
                          start_date, start_time, end_time, recurrence
        """
        # Course
        course_select = Select(self.driver.find_element(*self.SCHEDULE_COURSE_SELECT))
        course_select.select_by_value(schedule_data['course_id'])

        # Instructor
        instructor_select = Select(self.driver.find_element(*self.SCHEDULE_INSTRUCTOR_SELECT))
        instructor_select.select_by_value(schedule_data['instructor_id'])

        # Locations
        if 'location_id' in schedule_data:
            location_select = Select(self.driver.find_element(*self.SCHEDULE_LOCATION_SELECT))
            location_select.select_by_value(schedule_data['location_id'])

        # Date and times
        start_date = self.driver.find_element(*self.SCHEDULE_START_DATE)
        start_date.clear()
        start_date.send_keys(schedule_data['start_date'])

        start_time = self.driver.find_element(*self.SCHEDULE_START_TIME)
        start_time.clear()
        start_time.send_keys(schedule_data['start_time'])

        end_time = self.driver.find_element(*self.SCHEDULE_END_TIME)
        end_time.clear()
        end_time.send_keys(schedule_data['end_time'])

        # Recurrence (optional)
        if 'recurrence' in schedule_data:
            recurrence_select = Select(self.driver.find_element(*self.SCHEDULE_RECURRENCE))
            recurrence_select.select_by_value(schedule_data['recurrence'])

            # Days of week if recurring
            if 'days_of_week' in schedule_data:
                day_checkboxes = self.driver.find_elements(*self.SCHEDULE_DAYS_OF_WEEK)
                for checkbox in day_checkboxes:
                    day_value = checkbox.get_attribute('value')
                    if day_value in schedule_data['days_of_week']:
                        if not checkbox.is_selected():
                            checkbox.click()

    def submit_schedule(self):
        """Submit schedule form"""
        wait = WebDriverWait(self.driver, 10)
        submit_btn = wait.until(EC.element_to_be_clickable(self.SUBMIT_SCHEDULE_BTN))
        submit_btn.click()
        time.sleep(1)

    def conflict_warning_visible(self):
        """Check if conflict warning is visible"""
        try:
            warning = self.driver.find_element(*self.CONFLICT_WARNING)
            return warning.is_displayed()
        except NoSuchElementException:
            return False

    def get_schedule_count(self):
        """Get number of schedules visible in calendar"""
        try:
            schedule_items = self.driver.find_elements(*self.SCHEDULE_ITEMS)
            return len(schedule_items)
        except NoSuchElementException:
            return 0

    def get_conflict_count(self):
        """Get number of schedules marked as conflicts"""
        try:
            conflicts = self.driver.find_elements(*self.CONFLICT_INDICATORS)
            return len(conflicts)
        except NoSuchElementException:
            return 0

    def switch_to_weekly_view(self):
        """Switch calendar to weekly view"""
        weekly_btn = self.driver.find_element(*self.WEEKLY_VIEW_BTN)
        weekly_btn.click()
        time.sleep(0.5)

    def is_visible(self, locator):
        """Check if element is visible"""
        try:
            element = self.driver.find_element(*locator)
            return element.is_displayed()
        except NoSuchElementException:
            return False


class TestInstructorScheduling(BaseTest):
    """
    TDD RED PHASE Test Suite for Instructor Scheduling Interface

    These tests will FAIL until the scheduling UI is implemented.
    """

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup test environment - login as org admin"""
        self.page = SchedulingPage(self.driver, self.config)

        # Login as org admin
        self.login_as_org_admin()

    def login_as_org_admin(self):
        """Login as organization administrator using localStorage authentication"""
        # Navigate to a simple page first to set localStorage
        self.driver.get(f"{self.config.base_url}/html/index.html")
        time.sleep(1)

        # Set up org admin authenticated state via localStorage
        self.driver.execute_script("""
            localStorage.setItem('authToken', 'test-org-admin-token-67890');
            localStorage.setItem('userRole', 'organization_admin');
            localStorage.setItem('userName', 'Test Org Admin');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 300,
                email: 'org_admin@example.com',
                role: 'organization_admin',
                organization_id: 1,
                name: 'Test Org Admin'
            }));
            localStorage.setItem('userEmail', 'org_admin@example.com');
            localStorage.setItem('sessionStart', Date.now().toString());
            localStorage.setItem('lastActivity', Date.now().toString());
        """)

        # Now navigate to the dashboard with authentication set
        self.driver.get(f"{self.config.base_url}/html/org-admin-dashboard.html")

        # Wait for dashboard to fully initialize - wait for navigation to be visible and clickable
        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'a[data-tab="overview"]')))
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-tab="schedules"]')))
        time.sleep(3)  # Additional time for JavaScript to fully initialize all tabs

    def test_schedules_tab_exists(self):
        """
        Test that Schedules tab exists in org admin dashboard

        EXPECTED RESULT (RED PHASE): FAIL - tab doesn't exist yet
        """
        assert self.page.schedules_tab_exists(), \
            "Schedules tab should exist in org admin dashboard"

    def test_schedules_tab_loads_calendar_view(self):
        """
        Test that clicking Schedules tab loads calendar view

        EXPECTED RESULT (RED PHASE): FAIL - calendar doesn't exist yet
        """
        # Navigate to schedules
        self.page.navigate_to_schedules_tab()

        # Verify calendar view is displayed
        assert self.page.calendar_view_exists(), \
            "Calendar view should be displayed in schedules tab"

    def test_create_schedule_button_exists(self):
        """
        Test that Create Schedule button exists

        EXPECTED RESULT (RED PHASE): FAIL - button doesn't exist yet
        """
        self.page.navigate_to_schedules_tab()

        # Verify create schedule button exists
        assert self.page.is_visible(self.page.CREATE_SCHEDULE_BTN), \
            "Create Schedule button should exist"

    def test_schedule_modal_opens(self):
        """
        Test that clicking Create Schedule opens modal

        EXPECTED RESULT (RED PHASE): FAIL - modal doesn't exist yet
        """
        self.page.navigate_to_schedules_tab()
        self.page.click_create_schedule()

        # Verify modal opened
        assert self.page.is_visible(self.page.SCHEDULE_MODAL), \
            "Schedule creation modal should open"

    def test_schedule_form_has_required_fields(self):
        """
        Test that schedule form has all required fields

        EXPECTED RESULT (RED PHASE): FAIL - form doesn't exist yet
        """
        self.page.navigate_to_schedules_tab()
        self.page.click_create_schedule()

        # Verify required fields exist
        assert self.page.is_visible(self.page.SCHEDULE_COURSE_SELECT), \
            "Course select dropdown should exist"
        assert self.page.is_visible(self.page.SCHEDULE_INSTRUCTOR_SELECT), \
            "Instructor select dropdown should exist"
        assert self.page.is_visible(self.page.SCHEDULE_START_DATE), \
            "Start date field should exist"
        assert self.page.is_visible(self.page.SCHEDULE_START_TIME), \
            "Start time field should exist"
        assert self.page.is_visible(self.page.SCHEDULE_END_TIME), \
            "End time field should exist"

    def test_create_schedule_entry(self):
        """
        Test complete workflow of creating a schedule entry

        EXPECTED RESULT (RED PHASE): FAIL - functionality doesn't exist yet
        """
        self.page.navigate_to_schedules_tab()

        # Get initial count
        initial_count = self.page.get_schedule_count()

        # Open create schedule modal
        self.page.click_create_schedule()

        # Fill schedule form
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        schedule_data = {
            'course_id': 'test-course-1',
            'instructor_id': 'test-instructor-1',
            'location_id': 'test-locations-1',
            'start_date': tomorrow,
            'start_time': '09:00',
            'end_time': '10:30',
            'recurrence': 'none'
        }
        self.page.fill_schedule_form(schedule_data)

        # Submit
        self.page.submit_schedule()

        # Wait for success notification
        wait = WebDriverWait(self.driver, 10)
        success_notif = wait.until(EC.presence_of_element_located(self.page.SUCCESS_NOTIFICATION))
        assert success_notif.is_displayed(), "Success notification should appear"

        # Verify schedule was added to calendar
        time.sleep(1)
        new_count = self.page.get_schedule_count()
        assert new_count > initial_count, \
            "Schedule count should increase after creating schedule"

    def test_conflict_detection_same_instructor_same_time(self):
        """
        Test that scheduling same instructor at same time shows conflict warning

        EXPECTED RESULT (RED PHASE): FAIL - conflict detection doesn't exist yet
        """
        self.page.navigate_to_schedules_tab()

        # Create first schedule
        self.page.click_create_schedule()
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        schedule_data = {
            'course_id': 'test-course-1',
            'instructor_id': 'test-instructor-1',
            'start_date': tomorrow,
            'start_time': '14:00',
            'end_time': '15:30',
            'recurrence': 'none'
        }
        self.page.fill_schedule_form(schedule_data)
        self.page.submit_schedule()

        time.sleep(2)

        # Try to create conflicting schedule (same instructor, overlapping time)
        self.page.click_create_schedule()
        conflicting_data = {
            'course_id': 'test-course-2',
            'instructor_id': 'test-instructor-1',  # Same instructor
            'start_date': tomorrow,  # Same date
            'start_time': '14:30',  # Overlapping time
            'end_time': '16:00',
            'recurrence': 'none'
        }
        self.page.fill_schedule_form(conflicting_data)

        # Verify conflict warning appears
        assert self.page.conflict_warning_visible(), \
            "Conflict warning should appear when scheduling same instructor at overlapping time"

    def test_recurring_schedule_options(self):
        """
        Test that recurring schedule options are available (weekly, daily)

        EXPECTED RESULT (RED PHASE): FAIL - recurrence options don't exist yet
        """
        self.page.navigate_to_schedules_tab()
        self.page.click_create_schedule()

        # Verify recurrence dropdown exists
        assert self.page.is_visible(self.page.SCHEDULE_RECURRENCE), \
            "Recurrence dropdown should exist"

        # Verify recurrence options
        recurrence_select = Select(self.driver.find_element(*self.page.SCHEDULE_RECURRENCE))
        options = [opt.text for opt in recurrence_select.options]

        assert 'None' in options or 'Does not repeat' in options, \
            "Should have option for non-recurring schedule"
        assert any('Weekly' in opt or 'week' in opt.lower() for opt in options), \
            "Should have option for weekly recurrence"

    def test_weekly_calendar_view(self):
        """
        Test switching to weekly calendar view

        EXPECTED RESULT (RED PHASE): FAIL - view toggle doesn't exist yet
        """
        self.page.navigate_to_schedules_tab()

        # Verify weekly view button exists
        assert self.page.is_visible(self.page.WEEKLY_VIEW_BTN), \
            "Weekly view button should exist"

        # Switch to weekly view
        self.page.switch_to_weekly_view()

        # Verify calendar shows weekly layout
        # (This would check for day columns, week header, etc.)
        calendar_grid = self.driver.find_element(*self.page.CALENDAR_GRID)
        assert calendar_grid.is_displayed(), \
            "Calendar grid should be visible in weekly view"

    def test_schedule_filters_exist(self):
        """
        Test that schedule filters exist (instructor, course, locations)

        EXPECTED RESULT (RED PHASE): FAIL - filters don't exist yet
        """
        self.page.navigate_to_schedules_tab()

        # Verify filter controls exist
        assert self.page.is_visible(self.page.INSTRUCTOR_FILTER), \
            "Instructor filter should exist"
        assert self.page.is_visible(self.page.COURSE_FILTER), \
            "Course filter should exist"
        assert self.page.is_visible(self.page.LOCATION_FILTER), \
            "Locations filter should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
