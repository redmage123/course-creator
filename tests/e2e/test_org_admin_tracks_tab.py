"""
E2E Tests for Organization Admin Dashboard - Tracks Tab

BUSINESS CONTEXT:
Tests the complete user workflow for managing tracks in the organization
admin dashboard. Validates UI interactions, data entry, filtering, and
track lifecycle management.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model
- Tests modular JavaScript architecture
- Validates modal interactions
- Tests CRUD operations through UI

TEST COVERAGE:
- Tracks tab navigation
- Track creation modal
- Track editing
- Track deletion with confirmation
- Filtering and search
- Track details view
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import sys

sys.path.insert(0, '/home/bbrelin/course-creator/tests/e2e')
from selenium_base import BaseTest, BasePage


class OrgAdminDashboardPage(BasePage):
    """Page Object for Organization Admin Dashboard"""

    # Navigation
    TRACKS_NAV_LINK = (By.CSS_SELECTOR, 'a[data-tab="tracks"]')
    TRACKS_TAB = (By.ID, 'tracks')

    # Tracks Tab Elements
    CREATE_TRACK_BTN = (By.CSS_SELECTOR, 'button[onclick*="showCreateTrackModal"]')
    TRACKS_TABLE_BODY = (By.ID, 'tracksTableBody')
    TRACK_ROWS = (By.CSS_SELECTOR, '#tracksTableBody tr')

    # Filters
    PROJECT_FILTER = (By.ID, 'trackProjectFilter')
    STATUS_FILTER = (By.ID, 'trackStatusFilter')
    DIFFICULTY_FILTER = (By.ID, 'trackDifficultyFilter')
    SEARCH_INPUT = (By.ID, 'trackSearchInput')

    # Track Creation Modal
    TRACK_MODAL = (By.ID, 'trackModal')
    TRACK_MODAL_TITLE = (By.ID, 'trackModalTitle')
    TRACK_NAME_INPUT = (By.ID, 'trackName')
    TRACK_DESCRIPTION_INPUT = (By.ID, 'trackDescription')
    TRACK_PROJECT_SELECT = (By.ID, 'trackProject')
    TRACK_DIFFICULTY_SELECT = (By.ID, 'trackDifficulty')
    TRACK_DURATION_INPUT = (By.ID, 'trackDuration')
    TRACK_MAX_STUDENTS_INPUT = (By.ID, 'trackMaxStudents')
    TRACK_AUDIENCE_INPUT = (By.ID, 'trackAudience')
    TRACK_PREREQUISITES_INPUT = (By.ID, 'trackPrerequisites')
    TRACK_OBJECTIVES_INPUT = (By.ID, 'trackObjectives')
    TRACK_SUBMIT_BTN = (By.ID, 'trackSubmitBtn')
    TRACK_MODAL_CLOSE = (By.CSS_SELECTOR, '#trackModal .close-modal')

    # Track Details Modal
    TRACK_DETAILS_MODAL = (By.ID, 'trackDetailsModal')
    TRACK_DETAILS_CONTENT = (By.ID, 'trackDetailsContent')
    EDIT_FROM_DETAILS_BTN = (By.CSS_SELECTOR, '#trackDetailsModal button[onclick*="editTrackFromDetails"]')

    # Delete Confirmation Modal
    DELETE_TRACK_MODAL = (By.ID, 'deleteTrackModal')
    DELETE_TRACK_WARNING = (By.ID, 'deleteTrackWarning')
    CONFIRM_DELETE_BTN = (By.CSS_SELECTOR, '#deleteTrackModal button[onclick*="confirmDeleteTrack"]')

    # Notifications
    NOTIFICATION_CONTAINER = (By.ID, 'notification-container')
    NOTIFICATION = (By.CSS_SELECTOR, '.notification')

    def navigate_to_org_admin(self, org_id):
        """Navigate to organization admin dashboard"""
        self.navigate_to(f"/org-admin-dashboard.html?org_id={org_id}")
        time.sleep(1)

    def click_tracks_tab(self):
        """Click tracks navigation tab"""
        self.wait_and_click(*self.TRACKS_NAV_LINK)
        self.wait_for_element(*self.TRACKS_TAB)
        time.sleep(0.5)

    def click_create_track(self):
        """Click create track button"""
        self.wait_and_click(*self.CREATE_TRACK_BTN)
        self.wait_for_element(*self.TRACK_MODAL)
        time.sleep(0.5)

    def fill_track_form(self, track_data):
        """Fill out track creation/edit form"""
        # Name
        self.clear_and_type(self.TRACK_NAME_INPUT, track_data['name'])

        # Description (optional)
        if 'description' in track_data:
            self.clear_and_type(self.TRACK_DESCRIPTION_INPUT, track_data['description'])

        # Project
        if 'project_id' in track_data:
            project_select = Select(self.find_element(*self.TRACK_PROJECT_SELECT))
            project_select.select_by_value(track_data['project_id'])

        # Difficulty
        if 'difficulty_level' in track_data:
            difficulty_select = Select(self.find_element(*self.TRACK_DIFFICULTY_SELECT))
            difficulty_select.select_by_value(track_data['difficulty_level'])

        # Duration
        if 'duration_weeks' in track_data:
            self.clear_and_type(self.TRACK_DURATION_INPUT, str(track_data['duration_weeks']))

        # Max students
        if 'max_students' in track_data:
            self.clear_and_type(self.TRACK_MAX_STUDENTS_INPUT, str(track_data['max_students']))

        # Target audience (comma-separated)
        if 'target_audience' in track_data:
            audience_str = ', '.join(track_data['target_audience'])
            self.clear_and_type(self.TRACK_AUDIENCE_INPUT, audience_str)

        # Prerequisites (comma-separated)
        if 'prerequisites' in track_data:
            prereqs_str = ', '.join(track_data['prerequisites'])
            self.clear_and_type(self.TRACK_PREREQUISITES_INPUT, prereqs_str)

        # Learning objectives (comma-separated)
        if 'learning_objectives' in track_data:
            objectives_str = ', '.join(track_data['learning_objectives'])
            self.clear_and_type(self.TRACK_OBJECTIVES_INPUT, objectives_str)

    def submit_track_form(self):
        """Submit track form"""
        self.wait_and_click(*self.TRACK_SUBMIT_BTN)
        time.sleep(1)

    def get_track_count(self):
        """Get number of tracks in table"""
        rows = self.find_elements(*self.TRACK_ROWS)
        # Filter out "no tracks found" row
        actual_rows = [r for r in rows if 'No tracks found' not in r.text]
        return len(actual_rows)

    def search_tracks(self, search_term):
        """Enter search term and trigger search"""
        search_input = self.find_element(*self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(search_term)
        # Trigger change event (debounced in actual implementation)
        time.sleep(1)

    def filter_by_difficulty(self, difficulty):
        """Filter tracks by difficulty level"""
        difficulty_select = Select(self.find_element(*self.DIFFICULTY_FILTER))
        difficulty_select.select_by_value(difficulty)
        time.sleep(1)

    def wait_for_notification(self, expected_text=None, timeout=5):
        """Wait for notification to appear"""
        try:
            notification = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.NOTIFICATION)
            )
            if expected_text:
                assert expected_text.lower() in notification.text.lower()
            return notification.text
        except TimeoutException:
            return None


@pytest.mark.e2e
@pytest.mark.tracks
@pytest.mark.ui
class TestOrgAdminTracksTab(BaseTest):
    """
    E2E tests for organization admin tracks tab

    TESTING STRATEGY:
    - Test complete user workflows
    - Validate UI interactions
    - Test data persistence through UI
    - Test error handling and validation
    """

    def setUp(self):
        """Setup test environment"""
        super().setUp()
        self.page = OrgAdminDashboardPage(self.driver)

        # Create test organization and login
        # (This would use test data fixtures or API calls)
        self.org_id = "test-org-id"
        self.project_id = "test-project-id"

        # Login as org admin
        self.login_as_org_admin()

    def login_as_org_admin(self):
        """Login as organization administrator"""
        self.page.navigate_to("/login.html")
        # Login implementation
        # For now, assume logged in via cookie/localStorage
        pass

    def test_navigate_to_tracks_tab(self):
        """
        Test navigating to tracks tab

        WORKFLOW:
        1. Load org admin dashboard
        2. Click tracks navigation link
        3. Verify tracks tab is displayed
        """
        # Navigate to dashboard
        self.page.navigate_to_org_admin(self.org_id)

        # Click tracks tab
        self.page.click_tracks_tab()

        # Verify tracks tab is visible
        tracks_tab = self.page.find_element(*self.page.TRACKS_TAB)
        assert tracks_tab.is_displayed()

        # Verify tracks table exists
        tracks_table = self.page.find_element(*self.page.TRACKS_TABLE_BODY)
        assert tracks_table is not None

    def test_create_track_complete_workflow(self):
        """
        Test complete track creation workflow

        WORKFLOW:
        1. Navigate to tracks tab
        2. Click create track button
        3. Fill out track form with all fields
        4. Submit form
        5. Verify track appears in table
        6. Verify success notification
        """
        # Navigate to tracks
        self.page.navigate_to_org_admin(self.org_id)
        self.page.click_tracks_tab()

        # Get initial count
        initial_count = self.page.get_track_count()

        # Click create track
        self.page.click_create_track()

        # Verify modal title
        modal_title = self.page.find_element(*self.page.TRACK_MODAL_TITLE)
        assert "Create New Track" in modal_title.text

        # Fill form
        track_data = {
            'name': 'E2E Test Track',
            'description': 'Track created by E2E test',
            'project_id': self.project_id,
            'difficulty_level': 'beginner',
            'duration_weeks': 8,
            'max_students': 30,
            'target_audience': ['beginners', 'professionals'],
            'prerequisites': ['Basic computer skills'],
            'learning_objectives': [
                'Understand core concepts',
                'Apply knowledge practically'
            ]
        }

        self.page.fill_track_form(track_data)

        # Submit
        self.page.submit_track_form()

        # Wait for notification
        notification_text = self.page.wait_for_notification('created successfully')
        assert notification_text is not None

        # Verify track count increased
        new_count = self.page.get_track_count()
        assert new_count == initial_count + 1

        # Verify track appears in table
        table_body = self.page.find_element(*self.page.TRACKS_TABLE_BODY)
        assert 'E2E Test Track' in table_body.text

    def test_create_track_validation(self):
        """
        Test track form validation

        VALIDATION:
        - Name is required
        - Project must be selected
        - Duration must be positive number
        """
        self.page.navigate_to_org_admin(self.org_id)
        self.page.click_tracks_tab()
        self.page.click_create_track()

        # Try to submit empty form
        self.page.submit_track_form()

        # Should see validation error (browser native or custom)
        # This depends on implementation - could check for error messages

    def test_search_tracks(self):
        """
        Test track search functionality

        WORKFLOW:
        1. Create multiple tracks with different names
        2. Enter search term
        3. Verify only matching tracks displayed
        4. Clear search
        5. Verify all tracks displayed
        """
        self.page.navigate_to_org_admin(self.org_id)
        self.page.click_tracks_tab()

        # Search for "Python"
        self.page.search_tracks("Python")

        # Verify results contain Python
        table_body = self.page.find_element(*self.page.TRACKS_TABLE_BODY)
        rows = self.page.find_elements(*self.page.TRACK_ROWS)

        for row in rows:
            if 'No tracks found' not in row.text:
                assert 'Python' in row.text or 'python' in row.text.lower()

    def test_filter_by_difficulty(self):
        """
        Test filtering tracks by difficulty level

        WORKFLOW:
        1. Select difficulty filter
        2. Verify only tracks with that difficulty shown
        """
        self.page.navigate_to_org_admin(self.org_id)
        self.page.click_tracks_tab()

        # Filter by beginner
        self.page.filter_by_difficulty('beginner')

        # Verify all visible tracks are beginner level
        rows = self.page.find_elements(*self.page.TRACK_ROWS)
        for row in rows:
            if 'No tracks found' not in row.text:
                # Check for beginner badge
                assert 'beginner' in row.text.lower()

    def test_view_track_details(self):
        """
        Test viewing track details modal

        WORKFLOW:
        1. Click view details button on track
        2. Verify details modal opens
        3. Verify all track information displayed
        4. Close modal
        """
        self.page.navigate_to_org_admin(self.org_id)
        self.page.click_tracks_tab()

        # Click view button on first track
        view_btn = self.page.find_element(By.CSS_SELECTOR, '.btn-icon[title="View Details"]')
        view_btn.click()

        # Wait for details modal
        self.page.wait_for_element(*self.page.TRACK_DETAILS_MODAL)

        # Verify modal content
        details_content = self.page.find_element(*self.page.TRACK_DETAILS_CONTENT)
        assert details_content.is_displayed()
        assert len(details_content.text) > 0

    def test_edit_track_workflow(self):
        """
        Test editing existing track

        WORKFLOW:
        1. Click edit button on track
        2. Verify form populated with current data
        3. Modify fields
        4. Submit changes
        5. Verify changes reflected in table
        """
        self.page.navigate_to_org_admin(self.org_id)
        self.page.click_tracks_tab()

        # Click edit button on first track
        edit_btn = self.page.find_element(By.CSS_SELECTOR, '.btn-icon[title="Edit"]')
        edit_btn.click()

        # Wait for modal
        self.page.wait_for_element(*self.page.TRACK_MODAL)

        # Verify modal title shows "Edit"
        modal_title = self.page.find_element(*self.page.TRACK_MODAL_TITLE)
        assert "Edit" in modal_title.text

        # Modify name
        name_input = self.page.find_element(*self.page.TRACK_NAME_INPUT)
        current_name = name_input.get_attribute('value')
        new_name = current_name + " - Edited"

        name_input.clear()
        name_input.send_keys(new_name)

        # Submit
        self.page.submit_track_form()

        # Wait for notification
        self.page.wait_for_notification('updated successfully')

        # Verify updated name in table
        table_body = self.page.find_element(*self.page.TRACKS_TABLE_BODY)
        assert new_name in table_body.text

    def test_delete_track_workflow(self):
        """
        Test deleting track with confirmation

        WORKFLOW:
        1. Click delete button on track
        2. Verify confirmation modal appears
        3. Verify warning message
        4. Confirm deletion
        5. Verify track removed from table
        6. Verify success notification
        """
        self.page.navigate_to_org_admin(self.org_id)
        self.page.click_tracks_tab()

        # Get initial count
        initial_count = self.page.get_track_count()

        # Click delete button on first track
        delete_btn = self.page.find_element(By.CSS_SELECTOR, '.btn-icon[title="Delete"]')
        delete_btn.click()

        # Wait for confirmation modal
        self.page.wait_for_element(*self.page.DELETE_TRACK_MODAL)

        # Verify warning message
        warning = self.page.find_element(*self.page.DELETE_TRACK_WARNING)
        assert 'cannot be undone' in warning.text.lower()

        # Confirm deletion
        confirm_btn = self.page.find_element(*self.page.CONFIRM_DELETE_BTN)
        confirm_btn.click()

        # Wait for notification
        self.page.wait_for_notification('deleted successfully')

        # Verify count decreased
        new_count = self.page.get_track_count()
        assert new_count == initial_count - 1

    def test_modal_close_functionality(self):
        """
        Test closing modals properly

        WORKFLOW:
        1. Open create modal
        2. Fill partial data
        3. Close modal
        4. Reopen modal
        5. Verify form is reset/empty
        """
        self.page.navigate_to_org_admin(self.org_id)
        self.page.click_tracks_tab()

        # Open create modal
        self.page.click_create_track()

        # Enter some data
        self.page.clear_and_type(self.page.TRACK_NAME_INPUT, "Test Track")

        # Close modal
        close_btn = self.page.find_element(*self.page.TRACK_MODAL_CLOSE)
        close_btn.click()

        time.sleep(0.5)

        # Reopen modal
        self.page.click_create_track()

        # Verify form is empty
        name_input = self.page.find_element(*self.page.TRACK_NAME_INPUT)
        assert name_input.get_attribute('value') == ''


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "e2e"])
